from datetime import datetime
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


def fetch_kline(symbol="BTCUSDT", interval="4h", output_dir="data"):
    """抓取 Binance K線資料，清理後輸出至 CSV"""
    os.makedirs(output_dir, exist_ok=True)
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 500}

    print(f"\n📡 從 Binance 抓取 {symbol} ({interval}) K線資料中...")
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
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.rename(columns={'open_time': 'Date'}, inplace=True)
    df.drop(columns=["close_time", "ignore"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # === 輸出結果 ===
    raw_path = os.path.join(output_dir, f"{symbol.replace('/', '_')}.csv")
    clean_path = os.path.join(output_dir, "cleaned.csv")

    df.to_csv(raw_path, index=False)
    df.to_csv(clean_path, index=False)

    print(f"✅ 原始資料已儲存：{raw_path}")
    print(f"✅ 清理後資料已儲存：{clean_path}")
    print(f"📈 最新資料時間：{df['Date'].iloc[-1]}")

    return df


def main():
    """主程式入口，可直接執行"""
    fetch_kline(symbol="BTCUSDT", interval="4h", output_dir="data")


if __name__ == "__main__":
    main()
