from datetime import datetime, timedelta, timezone
import time
import requests
import pandas as pd
import os

# === Binance K線結構 ===
BINANCE_KLINE_COLS = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'num_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
]

# 轉換 interval -> 毫秒
INTERVAL_MS = {
    "1s": 1000,
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
    "3d": 3 * 24 * 60 * 60_000,
    "1w": 7 * 24 * 60 * 60_000,
    "1M": 30 * 24 * 60 * 60_000,   # Binance 月線長度不定，這裡僅做近似
}

def fetch_with_retry(url, params, max_attempts=5, backoff_factor=1.5):
    """從 Binance API 抓資料（具重試機制）"""
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            wait = backoff_factor ** attempt
            print(f"第 {attempt} 次嘗試失敗：{e}，{wait:.1f} 秒後重試...")
            time.sleep(wait)
    raise RuntimeError(f"❌ 多次重試後仍無法成功取得資料（共 {max_attempts} 次）")

def get_latest_closed_kline_close_time(symbol: str, interval: str) -> int:
    """
    取最新一根「已收盤」K線的 close_time（毫秒）。
    用 limit=1 直接問 klines，比自己算時間對齊安全。
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 1}
    data = fetch_with_retry(url, params)
    if not data:
        raise RuntimeError("⚠️ 取最新K線失敗")
    # 回傳的格式第7欄為 close_time（毫秒）
    latest_close_time_ms = data[0][6]
    return latest_close_time_ms

def fetch_kline_window(symbol="BTCUSDT",
                       interval="4h",
                       offset_bars=0,
                       window_size=500,
                       output_dir="data",
                       prefix="backtest"):
    """
    回測用窗口抓取：
    以最新K線為0，往回 offset_bars 當作「結尾」，
    一次取 window_size 根（最大1000，建議<=500）。

    會將結果輸出兩份 CSV：
    - {prefix}_{symbol}_{interval}_off{offset}_win{window}.csv
    - {prefix}_cleaned.csv（覆蓋式，方便下游固定讀取檔名）
    """
    if interval not in INTERVAL_MS:
        raise ValueError(f"不支援的 interval: {interval}")

    if window_size < 1 or window_size > 1000:
        raise ValueError("window_size 必須介於 1~1000（Binance 單次上限 1000）")

    os.makedirs(output_dir, exist_ok=True)
    url = "https://api.binance.com/api/v3/klines"

    # 先拿「最新一根已收盤K」的 close_time 當基準
    latest_close_time_ms = get_latest_closed_kline_close_time(symbol, interval)
    step = INTERVAL_MS[interval]

    # 設定「結尾」：往回 offset_bars 根
    # endTime 的定義：回傳的最後一根K線的 close_time 不會超過 endTime
    end_time_ms = latest_close_time_ms - offset_bars * step

    # 用 endTime + limit 抓取 window_size 連續資料（結尾對齊 end_time_ms）
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": window_size,
        "endTime": end_time_ms
    }

    print(f"\n📡 抓取 {symbol} ({interval}) 回測窗口：offset_bars={offset_bars}, window_size={window_size}")
    print(f"   以 close_time={end_time_ms}（UTC毫秒）為結尾")

    try:
        raw_data = fetch_with_retry(url, params)
    except Exception as e:
        print("❌ 抓取資料時發生致命錯誤：", e)
        return None

    if not raw_data:
        print("⚠️ 未能成功取得資料。")
        return None

    # === 處理資料 ===
    df = pd.DataFrame(raw_data, columns=BINANCE_KLINE_COLS)
    df["open_time"]  = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df.rename(columns={'open_time': 'Date'}, inplace=True)
    df.drop(columns=["ignore"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 檢查長度是否符合 window_size（太早期幣對可能不夠長）
    if len(df) < window_size:
        print(f"⚠️ 實際取得 {len(df)} 根，小於要求的 {window_size} 根（歷史不足或幣對歷史較短）。")

    # === 輸出結果 ===
    file_tag = f"{prefix}_{symbol.replace('/', '_')}_{interval}_off{offset_bars}_win{window_size}.csv"
    raw_path = os.path.join(output_dir, file_tag)
    clean_path = os.path.join(output_dir, f"{prefix}_cleaned.csv")

    df.to_csv(raw_path, index=False)
    df.to_csv(clean_path, index=False)

    print(f"✅ 視窗資料已儲存：{raw_path}")
    print(f"✅ 便利讀取檔（覆蓋式）：{clean_path}")
    print(f"📈 視窗起訖：{df['Date'].iloc[0]} ~ {df['Date'].iloc[-1]}（UTC）")
    return df

def main():
    # 例1：最新往回 500 根（與你原本邏輯等價）
    fetch_kline_window(symbol="BTCUSDT", interval="4h", offset_bars=0, window_size=500, output_dir="data")

    # 例2：把「120 根之前」那根當結尾，往前取 500 根（回測滑窗）
    # fetch_kline_window(symbol="BTCUSDT", interval="4h", offset_bars=120, window_size=500, output_dir="data")

if __name__ == "__main__":
    main()
