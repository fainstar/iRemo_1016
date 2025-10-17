import json
import requests
from datetime import datetime

def send_discord_webhook(webhook_url, assessment_data):
    """
    發送Discord webhook with embed
    """
    # 構建embed
    embed = {
        "title": "🎯 BTC/USDT 交易評估報告",
        "description": f"最新市場分析與交易建議",
        "color": get_embed_color(assessment_data['recommendation']),
        "fields": [
            {
                "name": "📅 評估時間",
                "value": f"{assessment_data['assessment_time']}\n*(UTC: {assessment_data['original_utc_time']})*",
                "inline": False
            },
            {
                "name": "💰 K線資訊",
                "value": f"```開盤: {assessment_data['candlestick_data']['open']:,.2f}\n最高: {assessment_data['candlestick_data']['high']:,.2f}\n最低: {assessment_data['candlestick_data']['low']:,.2f}\n收盤: {assessment_data['candlestick_data']['close']:,.2f}```",
                "inline": True
            },
            {
                "name": "📊 技術指標",
                "value": f"```變化: {assessment_data['analysis']['price_change']:+,.2f}\n區間: {assessment_data['analysis']['price_range']:,.2f}\n實體: {assessment_data['analysis']['body_size']:,.2f}```",
                "inline": True
            },
            {
                "name": "🎖️ 交易評分",
                "value": f"**買入**: `{assessment_data['trading_signals']['buy_score']:.3f}`\n**賣出**: `{assessment_data['trading_signals']['sell_score']:.3f}`",
                "inline": True
            },
            {
                "name": "💡 交易建議",
                "value": f"**{assessment_data['recommendation']}**",
                "inline": True
            }
        ],
        "footer": {
            "text": f"AI量化交易系統 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        },
        "timestamp": datetime.now().isoformat()
    }

    # 構建webhook payload
    payload = {
        "embeds": [embed],
        "username": "BTC交易助手",
        "avatar_url": "https://i.imgur.com/4M34hi2.png"  # 可以更換為自定義頭像
    }

    # 發送webhook
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("✅ Discord webhook 發送成功!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Discord webhook 發送失敗: {e}")
        return False

def get_embed_color(recommendation):
    """
    根據推薦返回對應的顏色
    """
    color_map = {
        "強烈買入": 0x00FF00,  # 綠色
        "買入": 0x90EE90,      # 淺綠色
        "觀望": 0xFFFF00,      # 黃色
        "賣出": 0xFFA500,      # 橙色
        "強烈賣出": 0xFF0000   # 紅色
    }
    return color_map.get(recommendation, 0x808080)  # 默認灰色

def send_latest_assessment_to_discord(webhook_url):
    """
    發送最新評估到Discord
    """
    try:
        # 讀取最新評估數據
        with open('data/latest_trading_assessment.json', 'r', encoding='utf-8') as f:
            assessment_data = json.load(f)

        # 發送webhook
        success = send_discord_webhook(webhook_url, assessment_data)

        if success:
            print("🎉 交易評估報告已成功發送到Discord!")
        else:
            print("❌ 發送失敗，請檢查webhook URL")

    except FileNotFoundError:
        print("❌ 找不到評估文件，請先運行 generate_latest_assessment.py")
    except json.JSONDecodeError:
        print("❌ JSON文件格式錯誤")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

def create_discord_webhook_example():
    """
    創建Discord webhook使用範例
    """
    example_code = '''
# Discord Webhook 使用範例

# 1. 在Discord中創建webhook:
#   - 進入Discord伺服器設定
#   - 選擇 "Integrations" > "Webhooks"
#   - 點擊 "New Webhook"
#   - 設定名稱和頻道
#   - 複製Webhook URL

# 2. 使用範例:
from discord_webhook_sender import send_latest_assessment_to_discord

# 替換為您的webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# 發送最新評估
send_latest_assessment_to_discord(WEBHOOK_URL)

# 3. 設定定時任務 (Linux/Mac):
# crontab -e
# 添加: */30 * * * * cd /path/to/your/project && python3 discord_webhook_sender.py

# 4. 設定定時任務 (Windows):
# 使用任務排程器設定每30分鐘運行一次
'''
    return example_code

if __name__ == "__main__":
    # 範例webhook URL - 用戶需要替換為自己的
    WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

    if WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("❌ 請先設定您的Discord Webhook URL")
        print("\n" + "="*60)
        print("📖 Discord Webhook 設定指南:")
        print("="*60)
        print("1. 進入您的Discord伺服器")
        print("2. 右鍵點擊頻道 > 編輯頻道 > Integrations > Webhooks")
        print("3. 點擊 'New Webhook' 創建新的webhook")
        print("4. 設定名稱和選擇頻道")
        print("5. 複製 'Webhook URL'")
        print("6. 將下面的 WEBHOOK_URL 替換為您的URL")
        print("\n範例:")
        print('WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdef..."')
        print("="*60)

        # 顯示使用範例
        print("\n" + create_discord_webhook_example())
    else:
        send_latest_assessment_to_discord(WEBHOOK_URL)