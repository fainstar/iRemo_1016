import pandas as pd
from datetime import datetime, timedelta
import json

def generate_latest_assessment():
    """
    生成最新一筆交易評估報告
    """
    # 讀取交易信號數據
    df = pd.read_csv('data/trading_signals_with_scores.csv')

    # 獲取最新一筆數據
    latest_data = df.iloc[-1]

    # 解析時間並轉換為+8時區
    utc_time = pd.to_datetime(latest_data['Date'])
    # 假設原始時間是UTC，轉換為+8時區
    local_time = utc_time + timedelta(hours=8)

    # 構建評估報告
    assessment = {
        "assessment_time": local_time.strftime('%Y-%m-%d %H:%M:%S +08'),
        "original_utc_time": utc_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        "candlestick_data": {
            "open": round(latest_data['open'], 2),
            "high": round(latest_data['high'], 2),
            "low": round(latest_data['low'], 2),
            "close": round(latest_data['close'], 2)
        },
        "trading_signals": {
            "buy_score": round(latest_data['buy_score'], 3),
            "sell_score": round(latest_data['sell_score'], 3)
        },
        "analysis": {
            "price_change": round(latest_data['close'] - latest_data['open'], 2),
            "price_range": round(latest_data['high'] - latest_data['low'], 2),
            "body_size": round(abs(latest_data['close'] - latest_data['open']), 2),
            "upper_shadow": round(latest_data['high'] - max(latest_data['open'], latest_data['close']), 2),
            "lower_shadow": round(min(latest_data['open'], latest_data['close']) - latest_data['low'], 2)
        },
        "recommendation": get_recommendation(latest_data['buy_score'], latest_data['sell_score'])
    }

    return assessment

def get_recommendation(buy_score, sell_score):
    """
    根據買賣分數給出推薦
    """
    if buy_score >= 0.75:
        return "強烈買入"
    elif buy_score >= 0.5:
        return "買入"
    elif sell_score >= 0.75:
        return "強烈賣出"
    elif sell_score >= 0.5:
        return "賣出"
    else:
        return "觀望"

def format_assessment_report(assessment):
    """
    格式化評估報告為可讀文本
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
    生成並保存評估報告
    """
    # 生成評估數據
    assessment = generate_latest_assessment()

    # 保存JSON格式
    with open('data/latest_trading_assessment.json', 'w', encoding='utf-8') as f:
        json.dump(assessment, f, ensure_ascii=False, indent=2)

    # 保存文本格式
    report_text = format_assessment_report(assessment)
    with open('data/latest_trading_assessment.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)

    print("✅ 最新交易評估報告已生成:")
    print("   📄 JSON格式: latest_trading_assessment.json")
    print("   📄 文本格式: latest_trading_assessment.txt")
    print("\n" + "="*60)
    print(report_text)

if __name__ == "__main__":
    save_assessment_report()