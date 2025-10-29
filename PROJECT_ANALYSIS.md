# BTC/USDT 量化交易系統 - 專案分析與改進建議

## 📋 專案總覽

### 一句話介紹
這是一套基於「**特徵箱子分析（Feature Bin Analysis）**」的 BTC/USDT 量化交易系統，從 Binance 抓取 4 小時 K 線資料，透過特徵工程、分箱統計與未來窗口關聯分析，產生買賣交易信號，支援回測驗證、Discord 通知與自動下單功能。

### 核心特色
- 📊 **特徵箱子預測法**：將技術指標分箱，統計各箱子與未來高低點的關聯性
- 🎯 **自動化完整流程**：從資料抓取、特徵工程、分析、決策到執行一條龍
- 🔄 **定時自動執行**：支援每 4 小時自動運行完整交易流程
- 📨 **Discord 即時通知**：交易評估報告自動發送到 Discord
- 🔒 **安全設計**：API 金鑰與 Webhook 從配置檔讀取，已加入 `.gitignore`

---

## 🏗️ 系統架構與資料流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     BTC/USDT 量化交易系統                          │
└─────────────────────────────────────────────────────────────────┘

1. 📥 資料獲取 (fetch_data.py)
   └─→ Binance API → data/cleaned.csv (500筆 4H K線)

2. 🧮 特徵工程 (add_features.py)
   └─→ 計算技術指標 → data/cleaned_features.csv
       (MA, EMA, RSI, MACD, ATR, Bollinger Bands, VWAP...)

3. 📦 特徵分箱 (binned_features.py)
   └─→ 12個K線為一窗口分箱 → data/binned_features.csv
       (每個特徵產生 {feature}_binned)

4. 🔍 箱子關聯分析 (feature_bin_analysis.py)
   └─→ 統計各箱子與未來12筆高低點關係 → data/feature_analysis_report.json
       (預測分數、上漲機率、平均變化%)

5. 📈 計算交易分數 (calculate_trading_scores.py)
   └─→ 根據箱子匹配度或加權機率 → data/trading_signals_with_scores.csv
       (buy_score, sell_score, signal_score)

6. 🧾 生成評估報告 (generate_latest_assessment.py)
   └─→ 最新一筆K線評估 → data/latest_trading_assessment.json
       (recommendation: 買入/賣出/觀望)

7. 📨 Discord 通知 (send_to_discord.py)
   └─→ 發送圖文並茂的交易報告到 Discord

8. 🤖 自動交易執行 (go_again.py)
   └─→ 根據 recommendation 執行開倉/平倉
       (支援 dry-run 與 --live 模式)

9. 🔄 定時排程 (a_main.py)
   └─→ 每4小時自動執行上述完整流程
```

---

## 📁 主要檔案說明

### 核心資料處理
| 檔案 | 功能 | 輸入 | 輸出 |
|------|------|------|------|
| `fetch_data.py` | 從 Binance 抓取 K 線資料 | Binance API | `data/cleaned.csv` |
| `add_features.py` | 計算技術指標特徵 | `data/cleaned.csv` | `data/cleaned_features.csv` |
| `binned_features.py` | 將特徵分箱 | `data/cleaned_features.csv` | `data/binned_features.csv` |

### 分析與決策
| 檔案 | 功能 | 輸入 | 輸出 |
|------|------|------|------|
| `feature_bin_analysis.py` | 分析箱子與未來走勢關聯 | `data/binned_features.csv` | `data/feature_analysis_report.json` |
| `calculate_trading_scores.py` | 計算買賣分數 | `data/binned_features.csv`<br>`data/feature_analysis_report.json` | `data/trading_signals_with_scores.csv` |
| `generate_latest_assessment.py` | 生成最新交易建議 | `data/trading_signals_with_scores.csv` | `data/latest_trading_assessment.json` |

### 回測與驗證
| 檔案 | 功能 | 說明 |
|------|------|------|
| `backtest_trading.py` | 單組參數回測 | 模擬買入賣出，計算勝率、總報酬、Sharpe等 |
| `quick_signal_backtest.py` | 閾值掃描回測 | 測試多組 buy/sell 閾值，找出最佳參數組合 |

### 通知與執行
| 檔案 | 功能 | 說明 |
|------|------|------|
| `send_to_discord.py` | Discord 通知 | 發送交易評估報告（支援 emoji 與彩色 embed） |
| `go_again.py` | 自動下單 | 根據 recommendation 執行交易（支援 dry-run） |
| `a_main.py` | 定時排程主程式 | 每4小時自動執行完整流程 |

### 配置與工具
| 檔案 | 功能 |
|------|------|
| `user/api.config` | API 金鑰與 Webhook 配置（已加入 .gitignore） |
| `.gitignore` | Git 忽略規則（保護敏感資料） |

---

## ✅ 專案優點

### 1. 清晰的模組化設計
- 每個步驟獨立成一個 Python 檔案
- 資料流向明確：CSV → 處理 → CSV → 分析 → JSON
- 易於理解、維護與擴展

### 2. 創新的特徵箱子分析法
- 不依賴傳統機器學習模型
- 透過統計箱子與未來走勢的關聯性做預測
- 具有可解釋性：可追溯每個特徵如何影響決策

### 3. 完整的自動化流程
- 從資料抓取到下單執行全自動
- 支援定時排程（每4小時）
- Discord 即時通知，方便遠程監控

### 4. 安全性考量
- API 金鑰從配置檔讀取，不硬編碼
- 已加入 `.gitignore` 保護敏感資料
- 支援 dry-run 模式，避免誤操作

### 5. 回測功能完善
- 提供單組參數與閾值掃描兩種回測
- 輸出詳細統計：勝率、Sharpe、最大回撤等
- 便於參數調優

---

## ⚠️ 目前風險與問題

### 高優先級（P0）- 需立即修正

#### 1. API 錯誤處理不足
**問題：** 當前遇到的 `code -2015` 錯誤（Invalid API-key, IP, or permissions）沒有友善提示。

**影響：** 難以快速排查問題，可能導致交易失敗。

**建議修正：**
```python
# 在 go_again.py 的 _req 函式中加入：
def _req(method, endpoint, params=None):
    # ... 現有程式碼 ...
    try:
        res = requests.request(method, url, params=params, headers=headers, timeout=10)
        json_res = res.json()
        
        # 檢查常見錯誤碼
        if isinstance(json_res, dict) and 'code' in json_res:
            code = json_res['code']
            msg = json_res.get('msg', '')
            
            if code == -2015:
                print(f"❌ API 金鑰無效或權限不足")
                print("   請檢查：")
                print("   1. API Key 是否正確")
                print("   2. IP 是否在白名單中")
                print("   3. API 是否有 Futures 交易權限")
            
        return json_res
    except Exception as e:
        return {"error": str(e)}
```

#### 2. Discord Webhook 缺少空值檢查
**問題：** 若 `DISCORD_WEBHOOK_RUN` 未設定，會嘗試對 None 發送請求。

**修正：**
```python
# 在 send_to_discord.py 的 main() 中加入：
if not webhook_url:
    print("❌ 未設定 DISCORD_WEBHOOK_RUN（請在 user/api.config 或環境變數中設定）")
    print("   範例：DISCORD_WEBHOOK_RUN = \"https://discord.com/api/webhooks/...\"")
    return
```

#### 3. 覆寫原始分數導致追蹤困難
**問題：** `calculate_trading_scores.py` 中將 `buy_score` 直接覆寫為標準化後的值。

**影響：** 無法比對原始分數與標準化分數，回測時難以驗證。

**建議：** 保留原始分數，標準化結果另存新欄位。

---

### 中優先級（P1）- 短期改進

#### 4. 缺少日誌記錄
**問題：** 無持久化日誌，錯誤發生時難以追溯。

**建議：**
```python
# 在 a_main.py 開頭加入：
import logging
import os

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/trading_system.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 在關鍵步驟加入日誌
logging.info(f"開始執行任務 - {datetime.now()}")
logging.error(f"步驟失敗: {desc} - {str(e)}")
```

#### 5. 回測過於簡化
**問題：**
- 未考慮交易成本（手續費、滑點）
- 使用 pnl sum 而非資產曲線
- 缺少年化報酬、最大回撤百分比等關鍵指標

**建議：** 改用資產曲線計算，加入交易成本參數。

#### 6. 缺少依賴管理與文檔
**問題：** 無 `requirements.txt`，新手難以快速部署。

**建議：** 建立以下檔案。

---

### 低優先級（P2）- 中期優化

#### 7. 配置管理可改進
**建議：** 使用 `.env` 檔案或環境變數，避免直接存儲敏感資料。

#### 8. 缺少單元測試
**建議：** 使用 pytest 測試關鍵函式（z-score、分數計算、回測邏輯）。

#### 9. 分箱策略可優化
**問題：** 對常數列或數據分布極端的特徵，qcut 可能失敗或產生無意義分箱。

**建議：** 記錄分箱失敗的特徵，手動調整或排除。

---

## 🔧 具體改進方案

### 方案 1：建立 requirements.txt

```bash
# requirements.txt
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
websocket-client>=1.5.0
schedule>=1.2.0
pytest>=7.4.0
python-dotenv>=1.0.0
```

安裝方式：
```bash
pip install -r requirements.txt
```

---

### 方案 2：建立 README.md

```markdown
# BTC/USDT 量化交易系統

## 快速開始

### 1. 安裝依賴
pip install -r requirements.txt

### 2. 設定 API 金鑰
複製並編輯配置檔：
cp user/api.config.example user/api.config

填入您的 Binance API 金鑰與 Discord Webhook

### 3. 執行完整流程（單次）
python a_main.py  # 修改 AUTO_MODE = False

### 4. 啟動定時排程（每4小時）
python a_main.py  # 修改 AUTO_MODE = True

### 5. 回測
python quick_signal_backtest.py

## 檔案結構
- fetch_data.py: 資料抓取
- add_features.py: 特徵工程
- binned_features.py: 分箱
- feature_bin_analysis.py: 箱子分析
- calculate_trading_scores.py: 計算交易分數
- generate_latest_assessment.py: 生成報告
- send_to_discord.py: Discord 通知
- go_again.py: 自動下單（加上 --live 執行實盤）
```

---

### 方案 3：建立配置範例檔

```python
# user/api.config.example
API_KEY = "your_binance_api_key_here"
SECRET_KEY = "your_binance_secret_key_here"
DISCORD_WEBHOOK_RUN = "https://discord.com/api/webhooks/your_webhook_here"

# 可選配置
BASE_URL = "https://fapi.binance.com"  # 或測試網 https://testnet.binancefuture.com
SYMBOL = "BTCUSDT"
```

---

### 方案 4：改進回測腳本

在 `quick_signal_backtest.py` 中加入：

```python
def run_quick_backtest(signals_file, buy_thresholds, sell_thresholds, 
                       fee_rate=0.0004, slippage=0.0001):
    """
    fee_rate: 手續費率（0.04%）
    slippage: 滑點（0.01%）
    """
    # ... 現有程式碼 ...
    
    # 計算含成本的 pnl
    pnl_gross = (exit_price - entry_price) / entry_price
    cost = fee_rate * 2 + slippage  # 買+賣手續費 + 滑點
    pnl_net = pnl_gross - cost
    
    # 計算資產曲線
    capital = 1.0  # 初始資金 100%
    equity_curve = []
    for pnl in trades_df['pnl']:
        capital *= (1 + pnl)
        equity_curve.append(capital)
    
    # 計算最大回撤百分比
    peak = pd.Series(equity_curve).cummax()
    drawdown = (pd.Series(equity_curve) - peak) / peak
    max_dd = drawdown.min()
    
    # 年化報酬（假設4小時一筆，一年約2190筆）
    total_periods = len(trades_df)
    years = total_periods / 2190
    cagr = (capital ** (1/years)) - 1 if years > 0 else 0
    
    return {
        'total_return': capital - 1,
        'cagr': cagr,
        'max_dd': max_dd,
        'sharpe': sharpe,
        # ... 其他指標
    }
```

---

## 📊 回測結果參考（已執行）

根據 `quick_signal_backtest.py` 掃描結果：

| 排名 | buy_t | sell_t | 交易次數 | 勝率 | 總收益 | Sharpe | 最大回撤 |
|------|-------|--------|---------|------|--------|--------|----------|
| 1 | -1.75 | -3.00 | 245 | 52.2% | 4.51% | 0.44 | -9.43% |
| 2 | 1.00 | -2.50 | 52 | 48.1% | 3.17% | 1.34 | -4.07% |
| 3 | 1.00 | -1.00 | 49 | 44.9% | 2.95% | 1.20 | -5.10% |

**建議：**
- 交易次數較多（>200）的組合雖然總收益高，但 Sharpe 較低、回撤較大
- 交易次數適中（40-60）的組合 Sharpe 較高，更穩定
- 建議選擇 `buy_t=1.0, sell_t=-2.5` 作為初始參數

---

## 🎯 優先執行建議（行動計畫）

### 立即修正（本週內）
1. ✅ 在 `send_to_discord.py` 加入 webhook 空值檢查
2. ✅ 在 `go_again.py` 改進 API 錯誤訊息
3. ✅ 保留原始 buy_score/sell_score，標準化另存新欄位
4. ✅ 建立 `requirements.txt`
5. ✅ 建立 `README.md`
6. ✅ 建立 `user/api.config.example`

### 短期改進（2週內）
7. 加入 logging 模組，記錄關鍵步驟與錯誤
8. 改進回測腳本，加入交易成本與資產曲線
9. 新增簡單的單元測試（至少測試 z-score 與分數計算）

### 中期優化（1個月內）
10. 改用 `.env` 管理敏感配置
11. 實作 Binance User Data Stream（監控帳戶變化）
12. 建立簡單的 Web UI（Streamlit）展示最新報告與回測結果
13. 加入更多技術指標與自適應分箱策略

---

## 🚀 如何使用本專案

### 首次設定
```bash
# 1. 克隆專案（如果從 Git）
git clone https://github.com/fainstar/iRemo_1016.git
cd iRemo_1016

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定配置
cp user/api.config.example user/api.config
# 編輯 user/api.config，填入您的 API 金鑰

# 4. 測試單次執行（dry-run）
python go_again.py -j data/latest_trading_assessment.json
```

### 回測與參數調優
```bash
# 執行閾值掃描回測
python quick_signal_backtest.py

# 查看結果
cat data/quick_backtest_results.csv
```

### 啟動自動化交易
```bash
# 先在測試網測試
# 修改 user/api.config 中的 BASE_URL 為測試網地址

# 啟動定時排程（每4小時）
python a_main.py  # 設定 AUTO_MODE = True

# 單次執行實盤（謹慎！）
python go_again.py --live
```

---

## ⚡ 常見問題排查

### Q1: API 錯誤 -2015（Invalid API-key）
**檢查項目：**
1. API Key 是否正確複製到 `user/api.config`
2. Binance 帳戶中該 API 是否啟用「Futures 交易」權限
3. 若啟用 IP 白名單，當前 IP 是否在列表中

### Q2: Discord 發送失敗
**檢查項目：**
1. `DISCORD_WEBHOOK_RUN` 是否正確設定
2. Discord Webhook 是否被刪除或失效
3. 網路連線是否正常

### Q3: 回測結果與實盤不符
**可能原因：**
1. 回測未考慮交易成本（手續費、滑點）
2. 歷史數據與實時數據有差異
3. 使用標準化分數但回測用原始分數

### Q4: 分箱特徵產生 NaN
**可能原因：**
1. 某些特徵值全為常數（標準差為0）
2. qcut 遇到重複分位數
**解決方案：** 已在程式中加入 fallback 至 cut，或檢查 `binned_features.csv` 中哪些欄位為 NaN

---

## 📞 聯絡與支援

- GitHub: https://github.com/fainstar/iRemo_1016
- Issues: https://github.com/fainstar/iRemo_1016/issues

---

## 📄 授權

本專案僅供學習與研究使用，實盤交易風險自負。

**免責聲明：** 本系統不構成投資建議，過往回測表現不代表未來收益。使用前請充分了解風險，並在測試網充分測試後再考慮實盤。

---

## 🔄 更新日誌

### 2025-10-29
- ✅ 加入 API 金鑰配置檔管理（`user/api.config`）
- ✅ 新增 Discord Webhook 配置支援
- ✅ 建立 `.gitignore` 保護敏感資料
- ✅ 新增閾值掃描回測腳本
- ✅ buy_score/sell_score 支援 z-score 標準化
- ✅ 完成專案分析與改進建議文檔

### 待完成
- [ ] 加入 logging 日誌模組
- [ ] 改進回測腳本（交易成本、資產曲線）
- [ ] 建立單元測試
- [ ] 實作 User Data Stream
- [ ] 建立 Web UI

---

**最後更新：** 2025年10月29日
