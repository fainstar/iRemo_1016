from datetime import datetime, timedelta
import time
import requests
import pandas as pd
from tqdm import tqdm
import json
import os

symbol = "BTCUSDT"
interval = "4h"

# Binance kline API returns arrays with these columns:
# [open_time, open, high, low, close, volume, close_time, quote_asset_volume,
#  number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore]
cols = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'num_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
]

df_all = pd.DataFrame()

def fetch_with_retry(url, params, max_attempts=5, backoff_factor=1.5):
    attempt = 0
    while attempt < max_attempts:
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            attempt += 1
            wait = backoff_factor ** attempt
            print(f'Fetch attempt {attempt} failed: {e}; retrying in {wait:.1f}s')
            time.sleep(wait)
    raise RuntimeError(f'Failed to fetch after {max_attempts} attempts')

# Fetch the latest 500 klines
url = f"https://api.binance.com/api/v3/klines"
params = {"symbol": symbol, "interval": interval, "limit": 500}
try:
    data = fetch_with_retry(url, params)
except Exception as e:
    print('Fatal fetch error:', e)
    data = []

if data:
    df = pd.DataFrame(data, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df_all = df

df_all.reset_index(drop=True, inplace=True)
df_all.to_csv("data/BTC_USDT.csv", index=False)