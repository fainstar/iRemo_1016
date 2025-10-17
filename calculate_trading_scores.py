import pandas as pd
import json

# 讀取JSON分析結果
with open('data/feature_analysis_report.json', 'r', encoding='utf-8') as f:
    analysis_data = json.load(f)

# 讀取分箱特徵數據
df = pd.read_csv('data/binned_features.csv')

# 定義高點和低點的最佳箱子規則
high_point_best_bins = {}
low_point_best_bins = {}

for feature in analysis_data['top_features']:
    feature_name = feature['feature_name']

    # 高點最佳箱子（平均變化%最高的箱子）
    high_analysis = feature['high_point_analysis']
    best_high_bin = max(high_analysis.keys(), key=lambda x: high_analysis[x]['avg_change_pct'])
    high_point_best_bins[feature_name] = best_high_bin

    # 低點最佳箱子（平均變化%最低的箱子）
    low_analysis = feature['low_point_analysis']
    best_low_bin = min(low_analysis.keys(), key=lambda x: low_analysis[x]['avg_change_pct'])
    low_point_best_bins[feature_name] = best_low_bin

print("高點最佳箱子規則:")
for feature, bin_val in high_point_best_bins.items():
    print(f"  {feature}: 箱子{bin_val}")

print("\n低點最佳箱子規則:")
for feature, bin_val in low_point_best_bins.items():
    print(f"  {feature}: 箱子{bin_val}")

# 計算買入和賣出分數
def calculate_buy_score(row):
    """計算買入分數：高點特徵處於最佳箱子的比例"""
    total_features = len(high_point_best_bins)
    matching_features = 0

    for feature, best_bin in high_point_best_bins.items():
        if feature in row.index:
            # 將最佳箱子轉換為相同類型進行比較
            try:
                current_bin = str(row[feature])
                if current_bin == str(best_bin):
                    matching_features += 1
            except:
                continue

    return matching_features / total_features if total_features > 0 else 0

def calculate_sell_score(row):
    """計算賣出分數：低點特徵處於最佳箱子的比例"""
    total_features = len(low_point_best_bins)
    matching_features = 0

    for feature, best_bin in low_point_best_bins.items():
        if feature in row.index:
            try:
                current_bin = str(row[feature])
                if current_bin == str(best_bin):
                    matching_features += 1
            except:
                continue

    return matching_features / total_features if total_features > 0 else 0

# 應用分數計算
print("\n計算買入和賣出分數...")
df['buy_score'] = df.apply(calculate_buy_score, axis=1)
df['sell_score'] = df.apply(calculate_sell_score, axis=1)

# 保存結果
output_df = df[['Date', 'open', 'high', 'low', 'close', 'buy_score', 'sell_score']]
output_df.to_csv('data/trading_signals_with_scores.csv', index=False)

print("完成！結果已保存到 trading_signals_with_scores.csv")
print(f"數據行數: {len(output_df)}")
print(".2f")
print(".2f")