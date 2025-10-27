import subprocess
import schedule
import time
from datetime import datetime


def run_job():
    """執行整個交易流程（fetch → feature → analysis → decision）"""
    steps = [
        ("📥 獲取 4H K 線數據", ["python3", "fetch_data.py"]),
        ("🧮 特徵工程", ["python3", "add_features.py"]),
        ("📊 特徵分箱", ["python3", "binned_features.py"]),
        ("🔍 箱子分析", ["python3", "feature_bin_analysis.py"]),
        ("📈 計算交易分數", ["python3", "calculate_trading_scores.py"]),
        ("🧾 生成評估報告", ["python3", "generate_latest_assessment.py"]),
        ("📨 發送到 Discord", ["python3", "send_to_discord.py"]),
        ("🤖 執行交易建議", ["python3", "go_again.py", "--live"]),
    ]

    print("\n────────────────────────────────────────")
    print(f"🚀 開始執行任務時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for desc, cmd in steps:
        print(f"\n▶️ {desc}...")
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                print(f"✅ {desc} 完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ {desc} 執行失敗: {e}")
        except Exception as e:
            print(f"⚠️ {desc} 發生未知錯誤: {e}")

    print(f"🎯 任務結束時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("────────────────────────────────────────\n")


def schedule_c4h_jobs():
    """設定每 4 小時執行一次"""
    times = ["03:56", "07:56", "11:56", "15:56", "19:56", "23:56"]
    for t in times:
        schedule.every().day.at(t).do(run_job)
        print(f"🕒 已排程：每日 {t} 執行")

    print("\n✅ 排程啟動成功，等待下一個觸發時間...\n")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # True = 定期自動執行
    # False = 立即執行一次
    AUTO_MODE = True

    if AUTO_MODE:
        schedule_c4h_jobs()
    else:
        run_job()
