import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

class FeatureBinAnalyzer:
    """
    特徵分箱與未來走勢關聯分析器
    用來分析每個分箱特徵（如 RSI_binned、MA_binned）與未來 12 筆價格變化的關係，
    例如：某特徵值較高時，未來是否更容易上漲。
    """
    
    def __init__(self, binned_data_path, original_data_path):
        """
        初始化分析器
        - binned_data_path: 已完成分箱的特徵資料 CSV
        - original_data_path: 原始數據 CSV（可用於比對或擴充）
        """
        self.binned_df = pd.read_csv(binned_data_path)
        self.original_df = pd.read_csv(original_data_path)
        
        # 篩選出所有以「_binned」結尾的特徵欄位
        self.binned_features = [col for col in self.binned_df.columns if col.endswith('_binned')]
        
        # 預先計算未來 12 筆的高低點變化
        self._calculate_future_returns()

    def _calculate_future_returns(self):
        """
        計算未來 12 筆資料內的高點 / 低點變化百分比與方向
        """
        # 計算未來 12 筆中的最高價與最低價
        self.binned_df['future_high_12'] = self.binned_df['high'].shift(-12).rolling(window=12).max()
        self.binned_df['future_low_12'] = self.binned_df['low'].shift(-12).rolling(window=12).min()

        # 計算相對於目前 close 的漲跌百分比
        self.binned_df['future_high_pct'] = (self.binned_df['future_high_12'] - self.binned_df['close']) / self.binned_df['close']
        self.binned_df['future_low_pct'] = (self.binned_df['future_low_12'] - self.binned_df['close']) / self.binned_df['close']

        # 轉成二元方向標籤：高點漲 → 1、低點跌 → 1
        self.binned_df['future_high_direction'] = (self.binned_df['future_high_pct'] > 0).astype(int)
        self.binned_df['future_low_direction'] = (self.binned_df['future_low_pct'] < 0).astype(int)

    def analyze_single_feature(self, feature_name, targets=['high', 'low']):
        """
        分析單一特徵與未來高/低點的關係
        回傳每個箱子（bin）的樣本數、平均變化、上漲機率等統計結果
        """
        results = {}
        for target in targets:
            # 根據目標類型設定對應欄位與標籤
            if target == 'high':
                pct_col, direction_col, label = 'future_high_pct', 'future_high_direction', '高點'
            else:
                pct_col, direction_col, label = 'future_low_pct', 'future_low_direction', '低點'
            
            # 以箱子分組，計算每個箱子的統計資料
            group_stats = self.binned_df.groupby(feature_name).agg({
                pct_col: ['count', 'mean', 'std'],
                direction_col: ['sum', 'mean']
            }).round(4)
            
            # 重命名欄位
            group_stats.columns = [
                f'{label}_樣本數', f'{label}_平均變化%', f'{label}_變化標準差',
                f'{label}_上漲次數', f'{label}_上漲機率'
            ]
            results[f'{label}預測'] = group_stats
        return results

    def analyze_all_features(self, targets=['high', 'low'], top_n=8):
        """
        分析所有特徵的「預測能力」
        預測能力衡量方式：各箱子的上漲機率差異（標準差）
        越大表示該特徵越能分出漲跌差異。
        """
        feature_scores = {}
        for feature in self.binned_features:
            scores = []
            for target in targets:
                # 根據高/低點選擇對應方向欄位
                direction_col = 'future_high_direction' if target == 'high' else 'future_low_direction'
                # 計算每個箱子的上漲機率
                bin_probs = self.binned_df.groupby(feature)[direction_col].mean()
                # 使用標準差衡量箱子間的差異
                scores.append(bin_probs.std() if len(bin_probs) > 1 else 0)
            # 平均作為該特徵的總體預測分數
            feature_scores[feature] = np.mean(scores)
        
        # 排序後取出前 N 名
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_features[:top_n]

    def generate_json_report(self, top_features=8):
        """
        生成 JSON 格式的分析報告
        包含：
          - 數據概要
          - 預測能力最強的前 N 個特徵
          - 每個特徵的箱子統計細節
        """
        top_predictive_features = self.analyze_all_features(top_n=top_features)

        report = {
            "analysis_type": "特徵箱子與未來窗口高點、低點關係分析",
            "data_overview": {
                "total_samples": len(self.binned_df),
                "binned_features_count": len(self.binned_features),
                "analysis_period": {
                    "start": str(self.binned_df['Date'].min()),
                    "end": str(self.binned_df['Date'].max())
                }
            },
            "top_features": []
        }

        # 對每個排名前 N 的特徵進行詳細分析
        for i, (feature_name, score) in enumerate(top_predictive_features, 1):
            feature_data = {
                "rank": i,
                "feature_name": feature_name,
                "prediction_score": round(score, 4),
                "high_point_analysis": {},
                "low_point_analysis": {}
            }

            # 單特徵詳細統計
            results = self.analyze_single_feature(feature_name)
            if results:
                # 高點統計
                if '高點預測' in results:
                    high_stats = results['高點預測']
                    for bin_value in high_stats.index:
                        feature_data["high_point_analysis"][str(bin_value)] = {
                            "sample_count": int(high_stats.loc[bin_value, '高點_樣本數']),
                            "avg_change_pct": round(float(high_stats.loc[bin_value, '高點_平均變化%']), 4),
                            "change_std": round(float(high_stats.loc[bin_value, '高點_變化標準差']), 4),
                            "up_count": int(high_stats.loc[bin_value, '高點_上漲次數']),
                            "up_probability": round(float(high_stats.loc[bin_value, '高點_上漲機率']), 4)
                        }
                # 低點統計
                if '低點預測' in results:
                    low_stats = results['低點預測']
                    for bin_value in low_stats.index:
                        feature_data["low_point_analysis"][str(bin_value)] = {
                            "sample_count": int(low_stats.loc[bin_value, '低點_樣本數']),
                            "avg_change_pct": round(float(low_stats.loc[bin_value, '低點_平均變化%']), 4),
                            "change_std": round(float(low_stats.loc[bin_value, '低點_變化標準差']), 4),
                            "up_count": int(low_stats.loc[bin_value, '低點_上漲次數']),
                            "up_probability": round(float(low_stats.loc[bin_value, '低點_上漲機率']), 4)
                        }
            report["top_features"].append(feature_data)

        return report


# ========== 主程式執行區 ========== #
if __name__ == "__main__":
    # 建立分析器實例（讀取CSV資料）
    analyzer = FeatureBinAnalyzer('data/binned_features.csv', 'data/cleaned_features.csv')
    
    # 生成 JSON 報告
    json_report = analyzer.generate_json_report(top_features=8)
    
    # 儲存結果至檔案
    with open('data/feature_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    
    print("✅ JSON報告已保存到: data/feature_analysis_report.json")
