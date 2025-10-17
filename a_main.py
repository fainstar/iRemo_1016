import subprocess
import schedule
import time

# Define the job to be scheduled
def scheduled_job():
    subprocess.run(["python3", "btc_4h.py"])
    subprocess.run(["python3", "preprocess.py"])
    subprocess.run(["python3", "features_no_ta.py"])
    subprocess.run(["python3", "binned_features.py"])
    subprocess.run(["python3", "feature_bin_analysis.py"])
    subprocess.run(["python3", "calculate_trading_scores.py"])
    subprocess.run(["python3", "generate_latest_assessment.py"])
    subprocess.run(["python3", "send_to_discord.py"])

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

