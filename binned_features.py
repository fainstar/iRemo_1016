import pandas as pd
import numpy as np

# 讀取數據
df = pd.read_csv('data/cleaned_features.csv')

# 保留基本欄位（若存在），但不要只限制為這些欄位——我們會在輸出時把這些欄位放到最前面
base_cols = ['Date', 'open', 'high', 'low', 'close']
present_base_cols = [c for c in base_cols if c in df.columns]

# 其餘欄位也會參與分箱
all_cols_for_binning = [c for c in df.columns]

# 定義窗口大小
window_size = 12

# 初始化分箱結果
binned_data = []

# 遍歷窗口並為每個欄位產生一個分箱後的新欄位："{col}_binned"
for i in range(0, len(df), window_size):
    window = df.iloc[i:i + window_size]
    
    # 對每個特徵進行分箱，存到 binned_window 並以 col_binned 命名
    binned_window = {}
    for col in all_cols_for_binning:
        if col not in window.columns:
            continue
        # 不對 Date 欄位做分箱（我們要保留原始 Date）
        if col == 'Date':
            continue
        out_col = f"{col}_binned"
        if col == 'Weekday':
            # Weekday 分7箱
            binned_window[out_col] = pd.cut(window[col], bins=7, labels=False)
        elif window[col].dtype in ['float64', 'int64']:
            # 數值型特徵分4箱（使用 qcut，若重複分位數則 drop duplicates）
            try:
                binned_window[out_col] = pd.qcut(window[col], q=5, labels=False, duplicates='drop')
            except Exception:
                # 若 qcut 失敗（例如常數列），退回到 cut
                binned_window[out_col] = pd.cut(window[col], bins=4, labels=False)
        else:
            # 非數值型特徵保持原值作為分箱（分類標籤）
            binned_window[out_col] = window[col].astype(str)
    
    # 將分箱結果加入列表
    binned_data.append(pd.DataFrame(binned_window))

# 合併所有窗口的分箱結果
binned_df = pd.concat(binned_data, ignore_index=True)

# 如果存在基本欄位，將原始基本欄位加入到最前面
final_cols = []
for c in present_base_cols:
    final_cols.append(c)

# 接著加入所有分箱欄位（維持 binned_df 目前的欄位順序）
binned_cols = [c for c in binned_df.columns if c.endswith('_binned')]
final_cols.extend(binned_cols)

# 合併原始基本欄位（從原始 df）與分箱結果（binned_df）
output_df = pd.DataFrame()
if len(present_base_cols) > 0:
    # 將原始基本欄位對齊到 output_df（注意索引長度應相同）
    # 若原始 df 比 binned_df 長，先取相同長度的前面部份
    n = len(binned_df)
    output_df = df[present_base_cols].reset_index(drop=True).iloc[:n].copy()
else:
    output_df = pd.DataFrame(index=range(len(binned_df)))

# 將分箱欄位加入
output_df = pd.concat([output_df.reset_index(drop=True), binned_df.reset_index(drop=True)], axis=1)


# 儲存包含基本欄位與所有分箱欄位的數據
output_df.to_csv('data/binned_features.csv', index=False)