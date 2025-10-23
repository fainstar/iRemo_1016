import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class FeatureBinAnalyzer:
    def __init__(self, binned_data_path, original_data_path):
        """
        初始化分析器
        """
        self.binned_df = pd.read_csv(binned_data_path)
        self.original_df = pd.read_csv(original_data_path)
        
        # 獲取所有分箱特徵名稱
        self.binned_features = [col for col in self.binned_df.columns if col.endswith('_binned')]
        
        # 計算未來收益率
        self._calculate_future_returns()
        
    def _calculate_future_returns(self):
        """
        計算未來12筆窗口內的高點和低點
        """
        # 未來12筆窗口內的最高價
        self.binned_df['future_high_12'] = self.binned_df['high'].shift(-12).rolling(window=12).max()
        # 未來12筆窗口內的最低價
        self.binned_df['future_low_12'] = self.binned_df['low'].shift(-12).rolling(window=12).min()
        
        # 計算相對於當前close的變化百分比
        self.binned_df['future_high_pct'] = (self.binned_df['future_high_12'] - self.binned_df['close']) / self.binned_df['close']
        self.binned_df['future_low_pct'] = (self.binned_df['future_low_12'] - self.binned_df['close']) / self.binned_df['close']
        
        # 未來趨勢方向 (高點上漲=1, 低點下跌=0)
        self.binned_df['future_high_direction'] = (self.binned_df['future_high_pct'] > 0).astype(int)
        self.binned_df['future_low_direction'] = (self.binned_df['future_low_pct'] < 0).astype(int)
        
    def analyze_single_feature(self, feature_name, targets=['high', 'low']):
        """
        分析單個特徵與未來窗口高點、低點的關係
        """
        if feature_name not in self.binned_features:
            print(f"特徵 {feature_name} 不在分箱特徵列表中")
            return None
            
        results = {}
        
        for target in targets:
            if target == 'high':
                pct_col = 'future_high_pct'
                direction_col = 'future_high_direction'
                label = '高點'
            else:
                pct_col = 'future_low_pct'
                direction_col = 'future_low_direction'
                label = '低點'
            
            # 按箱子分組統計
            group_stats = self.binned_df.groupby(feature_name).agg({
                pct_col: ['count', 'mean', 'std'],
                direction_col: ['sum', 'mean']
            }).round(4)
            
            # 重新命名列
            group_stats.columns = [f'{label}_樣本數', f'{label}_平均變化%', f'{label}_變化標準差', 
                                 f'{label}_上漲次數', f'{label}_上漲機率']
            
            results[f'{label}預測'] = group_stats
            
        return results
    
    def analyze_all_features(self, targets=['high', 'low'], top_n=10):
        """
        分析所有特徵，找出與未來窗口高點、低點關係最強的特徵
        """
        feature_scores = {}
        
        for feature in self.binned_features:
            scores = []
            
            for target in targets:
                if target == 'high':
                    direction_col = 'future_high_direction'
                else:
                    direction_col = 'future_low_direction'
                
                # 計算不同箱子間上漲機率的差異（作為預測能力指標）
                bin_probs = self.binned_df.groupby(feature)[direction_col].mean()
                
                if len(bin_probs) > 1:
                    # 使用標準差衡量箱子間差異
                    prob_std = bin_probs.std()
                    scores.append(prob_std)
                else:
                    scores.append(0)
            
            # 取平均作為該特徵的總體得分
            feature_scores[feature] = np.mean(scores)
        
        # 排序並取前N個
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        
        print("=" * 60)
        print(f"預測能力排名前 {top_n} 的特徵:")
        print("=" * 60)
        
        for i, (feature, score) in enumerate(sorted_features[:top_n], 1):
            print(f"{i:2d}. {feature:<25} 預測得分: {score:.4f}")
            
        return sorted_features[:top_n]
    
    def plot_feature_analysis(self, feature_name, targets=['high', 'low']):
        """
        繪製特徵分析圖表
        """
        if feature_name not in self.binned_features:
            print(f"特徵 {feature_name} 不在分箱特徵列表中")
            return
            
        fig, axes = plt.subplots(2, len(targets), figsize=(5*len(targets), 10))
        if len(targets) == 1:
            axes = axes.reshape(2, 1)
            
        for i, target in enumerate(targets):
            if target == 'high':
                pct_col = 'future_high_pct'
                direction_col = 'future_high_direction'
                label = '高點'
                color_return = 'red'
                color_prob = 'darkred'
            else:
                pct_col = 'future_low_pct'
                direction_col = 'future_low_direction'
                label = '低點'
                color_return = 'blue'
                color_prob = 'darkblue'
            
            # 上方圖：平均變化百分比
            data_pct = self.binned_df.groupby(feature_name)[pct_col].mean()
            axes[0, i].bar(data_pct.index, data_pct.values, alpha=0.7, color=color_return)
            axes[0, i].set_title(f'{feature_name}\n未來12筆{label}平均變化%')
            axes[0, i].set_xlabel('箱子')
            axes[0, i].set_ylabel('平均變化%')
            axes[0, i].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            
            # 下方圖：方向機率
            data_prob = self.binned_df.groupby(feature_name)[direction_col].mean()
            axes[1, i].bar(data_prob.index, data_prob.values, alpha=0.7, color=color_prob)
            axes[1, i].set_title(f'未來12筆{label}方向機率')
            axes[1, i].set_xlabel('箱子')
            axes[1, i].set_ylabel('方向機率')
            axes[1, i].axhline(y=0.5, color='black', linestyle='--', alpha=0.5)
            axes[1, i].set_ylim(0, 1)
            
        plt.tight_layout()
        plt.show()
        
    def generate_comprehensive_report(self, top_features=5):
        """
        生成綜合分析報告
        """
        print("=" * 80)
        print("特徵箱子與未來窗口高點、低點關係分析報告")
        print("=" * 80)
        
        # 1. 整體統計
        print(f"\n📊 數據概覽:")
        print(f"   總樣本數: {len(self.binned_df)}")
        print(f"   分箱特徵數: {len(self.binned_features)}")
        print(f"   分析期間: {self.binned_df['Date'].min()} 至 {self.binned_df['Date'].max()}")
        
        # 2. 找出預測能力最強的特徵
        top_predictive_features = self.analyze_all_features(top_n=top_features)
        
        print(f"\n📈 詳細分析前 {top_features} 個特徵:")
        print("=" * 80)
        
        # 3. 詳細分析每個頂級特徵
        for i, (feature_name, score) in enumerate(top_predictive_features, 1):
            print(f"\n{i}. {feature_name} (預測得分: {score:.4f})")
            print("-" * 60)
            
            # 分析結果
            results = self.analyze_single_feature(feature_name)
            
            if results:
                for target, stats in results.items():
                    print(f"\n  {target}預測結果:")
                    print(stats.to_string())
        
        return top_predictive_features
    
    def generate_json_report(self, top_features=8):
        """
        生成JSON格式的分析報告
        """
        import json
        
        # 獲取前N個特徵
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
        
        for i, (feature_name, score) in enumerate(top_predictive_features, 1):
            feature_data = {
                "rank": i,
                "feature_name": feature_name,
                "prediction_score": round(score, 4),
                "high_point_analysis": {},
                "low_point_analysis": {}
            }
            
            # 分析結果
            results = self.analyze_single_feature(feature_name)
            
            if results:
                # 高點分析
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
                
                # 低點分析
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

# 創建分析器實例
analyzer = FeatureBinAnalyzer('data/binned_features.csv', 'data/cleaned_features.csv')

# 生成綜合報告
print("正在生成特徵箱子與未來窗口高點、低點關係分析報告...")
top_features = analyzer.generate_comprehensive_report(top_features=8)

# 生成JSON報告
print("\n正在生成JSON格式報告...")
import json
json_report = analyzer.generate_json_report(top_features=8)

# 保存到文件
with open('data/feature_analysis_report.json', 'w', encoding='utf-8') as f:
    json.dump(json_report, f, ensure_ascii=False, indent=2)

print("JSON報告已保存到: feature_analysis_report.json")
