import pandas as pd
import json
from typing import Dict, Any

# 假設與設計說明：
# - 使用 feature_analysis_report.json 中每個 feature 的 prediction_score 作為該 feature 的權重。
# - 對於 buy_score：使用 high_point_analysis 中對應箱子的 up_probability（代表向上機率），
#   以 prediction_score 加權後做正規化（加權平均），結果介於 0~1。
# - 對於 sell_score：使用 low_point_analysis 中對應箱子的向下機率 (1 - up_probability)，
#   以 prediction_score 加權後做正規化，結果介於 0~1。
# - 若某 feature 在資料列中缺值或當前箱子在分析報告中未出現，則忽略該 feature（權重不計入分母）。
# - 這些假設若需調整，請告知要改用 avg_change_pct、或把 prediction_score 正規化等策略。


# 讀取JSON分析結果
with open('data/feature_analysis_report.json', 'r', encoding='utf-8') as f:
    analysis_data = json.load(f)

# 讀取分箱特徵數據
df = pd.read_csv('data/binned_features.csv')

# 建立 feature -> analysis map 方便查詢
feature_map: Dict[str, Dict[str, Any]] = {}
for feature in analysis_data.get('top_features', []):
    feature_name = feature.get('feature_name')
    if feature_name:
        feature_map[feature_name] = feature


def safe_bin_key(val) -> str:
    """把資料列中的箱子值轉成與 JSON key 相符的字串表示。"""
    # 把 NaN 或 None 視為空字串，使其不會匹配到任何分析箱
    try:
        if pd.isna(val):
            return ''
    except Exception:
        pass
    # 常見的箱子會是數字或字串，直接轉成 str
    return str(val)


def calculate_buy_score(row) -> float:
    """計算買入分數：以 prediction_score 為權重，加權 high_point_analysis[bin].up_probability 的加權平均。"""
    weighted_sum = 0.0
    total_weight = 0.0

    for feature_name, meta in feature_map.items():
        if feature_name not in row.index:
            continue
        pred_score = float(meta.get('prediction_score', 0) or 0)
        if pred_score <= 0:
            continue

        bin_key = safe_bin_key(row[feature_name])
        if not bin_key:
            continue

        high_analysis = meta.get('high_point_analysis', {})
        bin_entry = high_analysis.get(bin_key)
        if not bin_entry:
            # 若該箱子不在分析報告中，則跳過此 feature
            continue

        up_prob = float(bin_entry.get('up_probability', 0) or 0)
        weighted_sum += pred_score * up_prob
        total_weight += pred_score

    return (weighted_sum / total_weight) if total_weight > 0 else 0.0


def calculate_sell_score(row) -> float:
    """計算賣出分數：以 prediction_score 為權重，加權 (1 - low_point_analysis[bin].up_probability) 的加權平均。
    這代表對低點分析中向下（下跌）的機率做加權。
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for feature_name, meta in feature_map.items():
        if feature_name not in row.index:
            continue
        pred_score = float(meta.get('prediction_score', 0) or 0)
        if pred_score <= 0:
            continue

        bin_key = safe_bin_key(row[feature_name])
        if not bin_key:
            continue

        low_analysis = meta.get('low_point_analysis', {})
        bin_entry = low_analysis.get(bin_key)
        if not bin_entry:
            continue

        up_prob = float(bin_entry.get('up_probability', 0) or 0)
        down_prob = 1.0 - up_prob
        weighted_sum += pred_score * down_prob
        total_weight += pred_score

    return (weighted_sum / total_weight) if total_weight > 0 else 0.0


print("開始計算買入與賣出分數（依據 feature_analysis_report.json）...")
df['buy_score'] = df.apply(calculate_buy_score, axis=1)
df['sell_score'] = df.apply(calculate_sell_score, axis=1)

# 可選：算一個綜合分數（買 - 賣），供後續排序或過濾使用
df['signal_score'] = df['buy_score'] - df['sell_score']

# 保存結果
output_cols = ['Date', 'open', 'high', 'low', 'close', 'buy_score', 'sell_score', 'signal_score']
available_cols = [c for c in output_cols if c in df.columns]
output_df = df[available_cols]
output_df.to_csv('data/trading_signals_with_scores.csv', index=False)

print("完成！結果已保存到 data/trading_signals_with_scores.csv")
print(f"數據行數: {len(output_df)}")