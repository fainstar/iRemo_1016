#!/usr/bin/env python3
"""save_results_sql.py

Read latest assessment JSON and the last row from cleaned_features.csv, compute 30/90 MA on close,
and store a record into an SQLite database at data/trading_results.db.

Usage: python save_results_sql.py
"""
from pathlib import Path
import csv
import json
import os
from datetime import datetime
from statistics import mean
import sys

# Try to import mysql connector for MySQL support. If not available, we'll fall back to SQLite.
try:
    import mysql.connector
    from mysql.connector import errorcode
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
JSON_PATH = DATA_DIR / "latest_trading_assessment.json"
CSV_PATH = DATA_DIR / "cleaned_features.csv"
DB_PATH = DATA_DIR / "trading_results.db"

# Hard-coded MySQL credentials (as requested)
MYSQL_HOST = "49.213.238.86"
MYSQL_PORT = 2306
MYSQL_USER = "remo0811"
MYSQL_PASSWORD = "Oomayb1oO"
MYSQL_DB = "trading_results"


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def read_assessment(json_path):
    if not json_path.exists():
        raise FileNotFoundError(f"assessment file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract buy/sell scores from common nested locations
    buy_score = None
    sell_score = None

    # Common location: trading_signals
    ts = data.get("trading_signals") or {}
    if isinstance(ts, dict):
        buy_score = ts.get("buy_score")
        sell_score = ts.get("sell_score")

    # fallback to top-level keys
    if buy_score is None:
        buy_score = data.get("buy_score")
    if sell_score is None:
        sell_score = data.get("sell_score")

    recommendation = data.get("recommendation")
    assessment_time = data.get("assessment_time")
    return buy_score, sell_score, recommendation, assessment_time


def read_cleaned_csv(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"csv file not found: {csv_path}")

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        raise ValueError("CSV contains no rows")

    # Convert numeric fields for last row
    last = rows[-1]
    numeric_last = {
        "open": safe_float(last.get("open") or last.get("Open") or last.get("o")),
        "high": safe_float(last.get("high") or last.get("High") or last.get("h")),
        "low": safe_float(last.get("low") or last.get("Low") or last.get("l")),
        "close": safe_float(last.get("close") or last.get("Close") or last.get("c")),
        "volume": safe_float(last.get("volume") or last.get("Volume") or last.get("v")),
    }

    # Gather closes for MA
    closes = []
    for r in rows:
        c = safe_float(r.get("close") or r.get("Close") or r.get("c"))
        if c is not None:
            closes.append(c)

    return numeric_last, closes, last


def compute_ma(closes, window):
    if not closes:
        return None
    if len(closes) < window:
        # compute mean of available if not enough data
        return mean(closes)
    return mean(closes[-window:])


def ensure_table_mysql(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_assessments (
            id INT PRIMARY KEY AUTO_INCREMENT,
            ts VARCHAR(64),
            `open` DOUBLE,
            `high` DOUBLE,
            `low` DOUBLE,
            `close` DOUBLE,
            volume DOUBLE,
            ma30 DOUBLE,
            ma90 DOUBLE,
            buy_score DOUBLE,
            sell_score DOUBLE,
            recommendation TEXT,
            created_at DATETIME,
            UNIQUE KEY uq_ts (ts)
        )
        """
    )
    conn.commit()


def insert_record_mysql(conn, rec):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO trading_assessments
        (ts, `open`, `high`, `low`, `close`, volume, ma30, ma90, buy_score, sell_score, recommendation, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            rec.get("ts"),
            rec.get("open"),
            rec.get("high"),
            rec.get("low"),
            rec.get("close"),
            rec.get("volume"),
            rec.get("ma30"),
            rec.get("ma90"),
            rec.get("buy_score"),
            rec.get("sell_score"),
            rec.get("recommendation"),
            rec.get("created_at"),
        ),
    )
    conn.commit()
    return cur.lastrowid


def main():
    try:
        buy_score, sell_score, recommendation, assessment_time = read_assessment(JSON_PATH)
    except Exception as e:
        print(f"Failed to read assessment: {e}")
        sys.exit(1)

    try:
        numeric_last, closes, raw_last = read_cleaned_csv(CSV_PATH)
    except Exception as e:
        print(f"Failed to read CSV: {e}")
        sys.exit(1)

    ma30 = round(compute_ma(closes, 30), 2)
    ma90 = round(compute_ma(closes, 90), 2)

    # Use assessment_time from JSON if available, else fall back to CSV timestamp, else now
    ts = assessment_time or raw_last.get("timestamp") or raw_last.get("time") or raw_last.get("date")
    if not ts:
        ts = datetime.utcnow().isoformat()

    record = {
        "ts": ts,
        "open": numeric_last.get("open"),
        "high": numeric_last.get("high"),
        "low": numeric_last.get("low"),
        "close": numeric_last.get("close"),
        "volume": numeric_last.get("volume"),
        "ma30": ma30,
        "ma90": ma90,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "recommendation": recommendation,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Ensure data dir exists (kept for SQLite fallback)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Require mysql-connector to be available and use MySQL only (no SQLite fallback)
    if not MYSQL_AVAILABLE:
        print("mysql-connector not installed. Please install via: pip install mysql-connector-python")
        sys.exit(1)

    # connect without database to ensure database exists
    tmp = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        connection_timeout=10,
    )
    tmp.autocommit = True
    tmp_cur = tmp.cursor()
    tmp_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`")
    tmp_cur.close()
    tmp.close()

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        connection_timeout=10,
    )
    try:
        ensure_table_mysql(conn)
        # Check for duplicate by ts
        cur = conn.cursor()
        cur.execute("SELECT id FROM trading_assessments WHERE ts = %s LIMIT 1", (record.get("ts"),))
        found = cur.fetchone()
        if found:
            print(f"Record with ts={record.get('ts')} already exists (id={found[0]}). Skipping insert.")
        else:
            rowid = insert_record_mysql(conn, record)
    finally:
        conn.close()

    print("Inserted record id:", rowid)
    print("Wrote to MySQL at %s:%s DB=%s" % (MYSQL_HOST, MYSQL_PORT, MYSQL_DB))
    print("Summary:")
    for k in ["ts", "open", "high", "low", "close", "volume", "ma30", "ma90", "buy_score", "sell_score", "recommendation"]:
        print(f"  {k}: {record.get(k)}")


if __name__ == "__main__":
    main()
