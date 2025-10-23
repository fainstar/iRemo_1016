#!/usr/bin/env python3
"""
Discord Webhook 發送器 - 發送交易評估報告到Discord
"""

import json
import requests
from datetime import datetime
import sys

def load_assessment_data():
    """載入最新的評估數據"""
    try:
        with open('data/latest_trading_assessment.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 找不到評估文件，請先運行: python3 generate_latest_assessment.py")
        return None
    except json.JSONDecodeError:
        print("❌ JSON文件格式錯誤")
        return None

def get_embed_color(recommendation):
    """根據推薦返回Discord embed顏色"""
    color_map = {
        "強烈買入": 0x00FF00,  # 鮮綠色
        "買入": 0x90EE90,      # 淺綠色
        "觀望": 0xFFFF00,      # 黃色
        "賣出": 0xFFA500,      # 橙色
        "強烈賣出": 0xFF0000   # 紅色
    }
    return color_map.get(recommendation, 0x808080)  # 默認灰色

def create_discord_embed(assessment_data):
    """創建Discord embed"""
    embed = {
        "title": "🎯 BTC/USDT 交易評估報告",
        "description": "最新市場分析與交易建議 | 4小時K線",
        "color": get_embed_color(assessment_data['recommendation']),
        "fields": [
            {
                "name": "📅 評估時間 (+8時區)",
                "value": f"```{assessment_data['assessment_time']}```",
                "inline": False
            },
            {
                "name": "💰 K線資訊",
                "value": f"```css\n開盤: {assessment_data['candlestick_data']['open']:,.2f}\n最高: {assessment_data['candlestick_data']['high']:,.2f}\n最低: {assessment_data['candlestick_data']['low']:,.2f}\n收盤: {assessment_data['candlestick_data']['close']:,.2f}```",
                "inline": True
            },
            {
                "name": "📊 技術分析",
                "value": f"```diff\n{'+' if assessment_data['analysis']['price_change'] >= 0 else ''}{assessment_data['analysis']['price_change']:+,.2f} (變化)\n{assessment_data['analysis']['price_range']:,.2f} (區間)\n{assessment_data['analysis']['body_size']:,.2f} (實體)```",
                "inline": True
            },
            {
                "name": "🎖️ 交易評分",
                "value": f"```yaml\n買入: {assessment_data['trading_signals']['buy_score']:.3f}\n賣出: {assessment_data['trading_signals']['sell_score']:.3f}```",
                "inline": True
            },
            {
                "name": "💡 交易建議",
                "value": f"```fix\n{assessment_data['recommendation']}```",
                "inline": True
            },
            {
                "name": "📈 市場狀態",
                "value": get_market_status(assessment_data),
                "inline": False
            }
        ],
        "footer": {
            "text": "AI量化交易系統 • 基於特徵箱子分析",
            "icon_url": "https://i.imgur.com/4M34hi2.png"
        },
        "timestamp": datetime.now().isoformat(),
        "thumbnail": {
            "url": "https://www.binance.com/favicon.ico"
        }
    }

    return embed

def get_market_status(assessment_data):
    """根據數據判斷市場狀態"""
    buy_score = assessment_data['trading_signals']['buy_score']
    sell_score = assessment_data['trading_signals']['sell_score']
    price_change = assessment_data['analysis']['price_change']

    if buy_score >= 0.75:
        status = "🚀 強勢上漲趨勢"
    elif buy_score >= 0.5:
        status = "📈 溫和上漲趨勢"
    elif sell_score >= 0.75:
        status = "📉 強勢下跌趨勢"
    elif sell_score >= 0.5:
        status = "📊 溫和下跌趨勢"
    else:
        status = "⚖️ 市場震盪整理"

    # 添加價格變化描述
    if abs(price_change) < 100:
        volatility = "低波動"
    elif abs(price_change) < 500:
        volatility = "中波動"
    else:
        volatility = "高波動"

    return f"```{status} | {volatility}```"

def send_to_discord(webhook_url, embed):
    """發送embed到Discord"""
    payload = {
        "embeds": [embed],
        "username": "BTC交易助手 🤖",
        "avatar_url": "https://i.imgur.com/4M34hi2.png"
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        if response.status_code == 204:
            print("✅ Discord webhook 發送成功!")
            print(f"📊 評估時間: {embed['fields'][0]['value'].strip('```')}")
            print(f"💡 交易建議: {embed['fields'][3]['value'].strip('```').split(':')[1].strip()}")
            return True
        else:
            print(f"❌ 發送失敗，狀態碼: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 請求超時，請檢查網路連接")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🎯 Discord Webhook 交易評估發送器")
    print("=" * 50)

    # 載入評估數據
    assessment_data = load_assessment_data()
    if not assessment_data:
        return

    # 獲取webhook URL
    webhook_url = "https://discord.com/api/webhooks/1428770104023322748/G5mnhSn9AgxvNhBtR9Ld5Tc7jhtf8ksdElWkpIzGjgX9fZjf_nH9lmwke7tUHDN86Ind"
  

    # 創建embed
    embed = create_discord_embed(assessment_data)

    # 發送到Discord
    print(f"\n🚀 正在發送到Discord...")
    success = send_to_discord(webhook_url, embed)

    if success:
        print("\n" + "=" * 50)
        print("🎉 交易評估報告已成功發送到Discord!")
        print("💡 提示: 您可以設定定時任務自動發送最新評估")
    else:
        print("\n❌ 發送失敗，請檢查:")
        print("   - Webhook URL是否正確")
        print("   - 網路連接是否正常")
        print("   - Discord伺服器權限設定")

if __name__ == "__main__":
    main()