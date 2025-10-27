import subprocess
import schedule
import time

# Define the job to be scheduled
def scheduled_job():
    #獲取 4小時K線數據
    subprocess.run(["python3", "fetch_data.py"])
    # 特徵工程
    subprocess.run(["python3", "add_features.py"])
    # 特徵分箱
    subprocess.run(["python3", "binned_features.py"])
    # 箱子分析
    subprocess.run(["python3", "feature_bin_analysis.py"])
    # 計算交易分數
    subprocess.run(["python3", "calculate_trading_scores.py"])
    # 生成最新評估報告
    subprocess.run(["python3", "generate_latest_assessment.py"])
    # 發送到 Discord
    subprocess.run(["python3", "send_to_discord.py"])

def C4h_run():
    # Schedule the job at the specified times
    schedule.every().day.at("23:55").do(scheduled_job)
    schedule.every().day.at("19:55").do(scheduled_job)
    schedule.every().day.at("15:55").do(scheduled_job)
    schedule.every().day.at("11:55").do(scheduled_job)
    schedule.every().day.at("07:55").do(scheduled_job)
    schedule.every().day.at("03:55").do(scheduled_job)
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    flag = False
    if flag:
        C4h_run()
    else:
        scheduled_job()   