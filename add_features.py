import pandas as pd
import numpy as np

def generate_features(input_path: str, output_path: str) -> pd.DataFrame:
    """
    從輸入 CSV 檔讀取 K 線資料，計算多種技術指標（MA、EMA、布林帶、RSI、MACD、ATR、VWAP等），
    並輸出到新的 CSV 檔案，回傳完整的特徵 DataFrame。
    """
    # 讀取數據
    df = pd.read_csv(input_path)

    # === 基本技術指標 ===
    df['MA_20'] = df['close'].rolling(window=20).mean()

    def ema(series, span):
        return series.ewm(span=span).mean()
    df['EMA_20'] = ema(df['close'], 20)

    # === 布林通道 (Bollinger Bands) ===
    bb_period = 20
    bb_std = 2
    df['BB_middle'] = df['close'].rolling(window=bb_period).mean()
    bb_std_dev = df['close'].rolling(window=bb_period).std()
    df['BBL_20_2.0'] = df['BB_middle'] - (bb_std_dev * bb_std)
    df['BBM_20_2.0'] = df['BB_middle']
    df['BBU_20_2.0'] = df['BB_middle'] + (bb_std_dev * bb_std)
    df['BBB_20_2.0'] = (df['close'] - df['BBL_20_2.0']) / (df['BBU_20_2.0'] - df['BBL_20_2.0'])
    df['BBP_20_2.0'] = df['BBB_20_2.0']
    df.drop(columns=['BB_middle'], inplace=True)

    # === RSI (相對強弱指標) ===
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    df['RSI_14'] = calculate_rsi(df['close'], 14)

    # === MACD (指數平滑異同移動平均線) ===
    def calculate_macd(series, fast=12, slow=26, signal=9):
        ema_fast = ema(series, fast)
        ema_slow = ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    macd_line, signal_line, histogram = calculate_macd(df['close'])
    df['MACD_12_26_9'] = macd_line
    df['MACDs_12_26_9'] = signal_line
    df['MACDh_12_26_9'] = histogram

    # === ATR (平均真實波幅) ===
    def calculate_atr(high, low, close, period=14):
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    df['ATR_14'] = calculate_atr(df['high'], df['low'], df['close'], 14)

    # === 價格變化類特徵 ===
    df['Return'] = df['close'].pct_change()
    df['High_Low'] = df['high'] - df['low']
    df['Open_Close'] = df['close'] - df['open']
    df['UpperShadow'] = df['high'] - df[['close', 'open']].max(axis=1)
    df['LowerShadow'] = df[['close', 'open']].min(axis=1) - df['low']

    # === 時間特徵 ===
    df['Datetime'] = pd.to_datetime(df['Date'])
    df['Hour'] = df['Datetime'].dt.hour
    df['Weekday'] = df['Datetime'].dt.weekday

    # === 成交量特徵 ===
    df['Volume_MA20'] = df['volume'].rolling(window=20).mean()
    df['Volume_Change'] = df['volume'].pct_change()

    # === VWAP (成交量加權平均價) ===
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap_numerator'] = (df['typical_price'] * df['volume']).cumsum()
    df['vwap_denominator'] = df['volume'].cumsum()
    df['VWAP'] = df['vwap_numerator'] / df['vwap_denominator']

    # 20 期移動 VWAP
    window = 20
    df['VWAP_20_numerator'] = (df['typical_price'] * df['volume']).rolling(window=window).sum()
    df['VWAP_20_denominator'] = df['volume'].rolling(window=window).sum()
    df['VWAP_20'] = df['VWAP_20_numerator'] / df['VWAP_20_denominator']

    # 清除中間計算欄位
    df.drop(columns=[
        'typical_price', 'vwap_numerator', 'vwap_denominator',
        'VWAP_20_numerator', 'VWAP_20_denominator', 'Datetime'
    ], inplace=True)

    # === 儲存結果 ===
    df.to_csv(output_path, index=False)

    print("✅ 成功產生技術特徵並儲存：", output_path)
    print("資料形狀：", df.shape)

    vwap_cols = [col for col in df.columns if 'VWAP' in col]
    print("\nVWAP 相關欄位：", vwap_cols)
    print("\nVWAP 統計資訊：")
    print(df[vwap_cols].describe())

    return df


# === 主程式執行區 ===
if __name__ == "__main__":
    input_path = "data/cleaned.csv"
    output_path = "data/cleaned_features.csv"
    generate_features(input_path, output_path)
