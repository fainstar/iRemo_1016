from datetime import datetime, timedelta
import time
import requests
import pandas as pd
from tqdm import tqdm
import json
import os

# === 基本設定 ===
symbol = "BTCUSDT"       # 幣種：BTC/USDT
interval = "4h"           # K線時間間隔：4小時
output_dir = "data"       # 資料儲存資料夾
os.makedirs(output_dir, exist_ok=True)

# Binance 回傳的 K 線欄位結構
cols = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'num_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
]

# === 帶重試機制的請求函式 ===
def fetch_with_retry(url, params, max_attempts=5, backoff_factor=1.5):
    """
    從指定 URL 抓取資料，若失敗會自動重試。
    max_attempts：最大嘗試次數
    backoff_factor：重試等待時間的指數倍率
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            attempt += 1
            wait = backoff_factor ** attempt
            print(f"第 {attempt} 次嘗試失敗：{e}，{wait:.1f} 秒後重試...")
            time.sleep(wait)
    raise RuntimeError(f"多次重試後仍無法成功取得資料（共 {max_attempts} 次）")

# === 向 Binance 抓取 K 線資料 ===
url = "https://api.binance.com/api/v3/klines"
params = {"symbol": symbol, "interval": interval, "limit": 500}

try:
    data = fetch_with_retry(url, params)
except Exception as e:
    print("❌ 抓取資料時發生致命錯誤：", e)
    data = []

# === 處理與清理資料 ===
if data:
    # 將回傳資料轉成 DataFrame
    df = pd.DataFrame(data, columns=cols)

    # 將開盤時間轉為日期格式
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")

    # 將欄位 open_time 改名為 Date
    df.rename(columns={'open_time': 'Date'}, inplace=True)

    # 移除不必要欄位
    cols_to_drop = ['close_time', 'ignore']
    df.drop(columns=cols_to_drop, inplace=True)

    # 重置索引
    df.reset_index(drop=True, inplace=True)

    # === 輸出檔案 ===
    raw_path = os.path.join(output_dir, "BTC_USDT.csv")      # 原始資料
    clean_path = os.path.join(output_dir, "cleaned.csv")     # 清理後資料

    df.to_csv(raw_path, index=False)
    df.to_csv(clean_path, index=False)

    print(f"✅ 原始資料已儲存：{raw_path}")
    print(f"✅ 清理後資料已儲存：{clean_path}")
else:
    print("⚠️ 未能成功從 Binance 取得資料。")
