# save_results_sql.py

這個專案新增了一個簡單的腳本 `save_results_sql.py`，用途是:

- 從 `data/latest_trading_assessment.json` 讀取 `buy_score`, `sell_score`, `recommendation`。
- 從 `data/cleaned_features.csv` 讀取最後一筆（open, high, low, close, volume），並計算 close 的 30MA 與 90MA。
- 把上述資料寫入 SQLite 資料庫 `data/trading_results.db` 的 `trading_assessments` 表。

使用方式
```
python save_results_sql.py
```

輸出
- 在 `data/trading_results.db` 中新增一筆資料。
- 腳本會在終端印出插入的 row id、資料庫路徑與欄位摘要。

注意事項
- 腳本使用純標準庫（不依賴 pandas），以降低環境相依性。
- 如果 `latest_trading_assessment.json` 中沒有 `buy_score` 或 `sell_score` 欄位，對應值會儲存為 NULL。
- 若 CSV 行數少於 30 或 90，MA 會用可用的所有 close 值平均作為退而求其次的結果。

後續改進建議
- 若要寫入 PostgreSQL / MySQL，請把 `sqlite3` 部分換成對應 DB 的 client (psycopg2 / mysql-connector)，並使用連線池/交易管理。
- 可加入單元測試以驗證 CSV/JSON 解析邏輯與插入結果。
