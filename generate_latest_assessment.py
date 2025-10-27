import pandas as pd
from datetime import datetime, timedelta
import json

def generate_latest_assessment():
    """
    生成最新一筆交易評估報告
    步驟：
    1. 從 CSV 讀取交易信號資料
    2. 抓取最新一筆記錄（最新 K 線）
    3. 計算K線結構（實體、上下影線、漲跌幅）
    4. 根據買賣分數給出交易建議
    """
    # 讀取交易信號數據（含 buy_score、sell_score）
    df = pd.read_csv('data/trading_signals_with_scores.csv')

    # 取最後一筆（最新時間）
    latest_data = df.iloc[-1]

    # 將 UTC 時間轉成 +8（台灣時間）
    utc_time = pd.to_datetime(latest_data['Date'])
    local_time = utc_time + timedelta(hours=8)

    # 建立報告結構
    assessment = {
        "assessment_time": local_time.strftime('%Y-%m-%d %H:%M:%S +08'),
        "original_utc_time": utc_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        
        # 當前K線數據
        "candlestick_data": {
            "open": round(latest_data['open'], 2),
            "high": round(latest_data['high'], 2),
            "low": round(latest_data['low'], 2),
            "close": round(latest_data['close'], 2)
        },
        
        # 模型或策略的買賣分數
        "trading_signals": {
            "buy_score": round(latest_data['buy_score'], 3),
            "sell_score": round(latest_data['sell_score'], 3)
        },
        
        # K線結構分析（幫助判斷市場情緒）
        "analysis": {
            "price_change": round(latest_data['close'] - latest_data['open'], 2),  # 漲跌
            "price_range": round(latest_data['high'] - latest_data['low'], 2),     # 高低價差
            "body_size": round(abs(latest_data['close'] - latest_data['open']), 2), # 實體大小
            "upper_shadow": round(latest_data['high'] - max(latest_data['open'], latest_data['close']), 2),  # 上影線
            "lower_shadow": round(min(latest_data['open'], latest_data['close']) - latest_data['low'], 2)    # 下影線
        },

        # 綜合建議（強烈買入 / 買入 / 賣出 / 觀望）
        "recommendation": get_recommendation(latest_data['buy_score'], latest_data['sell_score'])
    }

    return assessment

def get_recommendation(buy_score, sell_score):
    """
    根據買賣分數給出交易建議。
    規則：
      - 若買入分數明顯高於賣出分數（差距 ≥ 0.25）：
          * buy_score ≥ 0.75 → 強烈買入
          * buy_score > 0.5 → 買入
      - 若賣出分數明顯高於買入分數（差距 ≥ 0.25）：
          * sell_score ≥ 0.75 → 強烈賣出
          * sell_score > 0.5 → 賣出
      - 其餘情況 → 觀望
    """
    # 買入信號顯著高於賣出信號
    if buy_score > sell_score + 0.25:
        if buy_score >= 0.75:
            return "強烈買入"
        elif buy_score >= 0.5:
            return "買入"
    
    # 賣出信號顯著高於買入信號
    elif sell_score > buy_score + 0.25:
        if sell_score >= 0.75:
            return "強烈賣出"
        elif sell_score >= 0.5:
            return "賣出"
    
    # 其他（分數接近或信號不明確）
    return "觀望"


def format_assessment_report(assessment):
    """
    將評估報告格式化成可讀文字版本
    方便直接輸出在終端或存成TXT
    """
    report = f"""
{'='*60}
🎯 最新交易評估報告 (+8時區)
{'='*60}

📅 評估時間: {assessment['assessment_time']}
   (UTC時間: {assessment['original_utc_time']})

💰 K線資訊:
   開盤價: {assessment['candlestick_data']['open']:,.2f}
   最高價: {assessment['candlestick_data']['high']:,.2f}
   最低價: {assessment['candlestick_data']['low']:,.2f}
   收盤價: {assessment['candlestick_data']['close']:,.2f}

📊 技術分析:
   價格變化: {assessment['analysis']['price_change']:+,.2f}
   價格區間: {assessment['analysis']['price_range']:,.2f}
   實體大小: {assessment['analysis']['body_size']:,.2f}
   上影線: {assessment['analysis']['upper_shadow']:,.2f}
   下影線: {assessment['analysis']['lower_shadow']:,.2f}

🎖️ 交易信號評分:
   買入評分: {assessment['trading_signals']['buy_score']:.3f}
   賣出評分: {assessment['trading_signals']['sell_score']:.3f}

💡 交易建議: {assessment['recommendation']}

{'='*60}
"""
    return report


def save_assessment_report():
    """
    主流程：
    1. 生成最新交易評估
    2. 保存 JSON 與 TXT 檔案
    3. 在終端印出結果
    """
    # 生成分析結果
    assessment = generate_latest_assessment()

    # 儲存 JSON 格式（結構化數據，供系統使用）
    with open('data/latest_trading_assessment.json', 'w', encoding='utf-8') as f:
        json.dump(assessment, f, ensure_ascii=False, indent=2)

    # 螢幕輸出提示與報告預覽
    print("✅ 最新交易評估報告已生成:")
    print("   📄 JSON格式: latest_trading_assessment.json")


# 主程式進入點
if __name__ == "__main__":
    save_assessment_report()
