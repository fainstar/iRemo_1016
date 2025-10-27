import time
import hmac
import hashlib
import requests
import os
import ast
from pathlib import Path

# === API 金鑰 / 設定讀取 ===
BASE_URL = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"


def load_api_config(path: str):
    """從簡單的 python-like config 檔中擷取 API_KEY 與 SECRET_KEY（安全解析，不執行）。
    預期格式類似於：
      API_KEY = "..."
      SECRET_KEY = "..."
    """
    cfg = {}
    try:
        p = Path(path)
        if not p.exists():
            return cfg
        src = p.read_text(encoding='utf-8')
        tree = ast.parse(src, mode='exec')
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ('API_KEY', 'SECRET_KEY', 'BASE_URL', 'SYMBOL'):
                        val = node.value
                        if isinstance(val, ast.Constant) and isinstance(val.value, str):
                            cfg[target.id] = val.value
    except Exception:
        # 若解析失敗，回傳空 dict（呼叫方可使用 env 或其它備援）
        return {}
    return cfg


# 嘗試載入預設位置的 config（repository 相對路徑 user/api.config）
default_cfg_path = Path(__file__).parent.joinpath('user', 'api.config')
_cfg = load_api_config(str(default_cfg_path))

# 以環境變數為備援
API_KEY = _cfg.get('API_KEY') or os.getenv('API_KEY') or ''
SECRET_KEY = _cfg.get('SECRET_KEY') or os.getenv('SECRET_KEY') or ''

if _cfg.get('BASE_URL'):
    BASE_URL = _cfg.get('BASE_URL')
if _cfg.get('SYMBOL'):
    SYMBOL = _cfg.get('SYMBOL')

# === 通用函式 ===
def _sign(params):
    q = "&".join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(SECRET_KEY.encode(), q.encode(), hashlib.sha256).hexdigest()

def _req(method, endpoint, params=None):
    if params is None: params = {}
    params["timestamp"] = int(time.time() * 1000)
    params["signature"] = _sign(params)
    headers = {"X-MBX-APIKEY": API_KEY}
    url = BASE_URL + endpoint
    try:
        res = requests.request(method, url, params=params, headers=headers, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# === 初始化（明確檢查） ===
def setup():
    print("🛠️ 初始化 Binance Futures 設定中...")
    print("────────────────────────────────────────")

    # Step 1: 測試 API 連線
    ping = _req("GET", "/fapi/v1/ping")
    if ping == {}:
        print("✅ API 連線成功")
    else:
        print("❌ API 連線失敗:", ping)
        return False

    # Step 2: 檢查帳戶權限
    account = _req("GET", "/fapi/v2/account")
    if "availableBalance" in account:
        print(f"✅ 帳戶驗證成功，可用餘額：{account['availableBalance']} USDT")
    else:
        print("❌ 帳戶驗證失敗，請檢查 API Key 權限")
        print("回傳內容:", account)
        return False

    # Step 3: 設定全倉模式
    print("\n⚙️ 嘗試設定全倉模式...")
    resp_margin = _req("POST", "/fapi/v1/marginType", {"symbol": SYMBOL, "marginType": "CROSSED"})
    if resp_margin == {} or resp_margin.get("code") == -4046:
        print("✅ 全倉模式設定成功（或已是全倉）")
    else:
        print("❌ 全倉模式設定失敗:", resp_margin)
        return False

    # Step 4: 設定槓桿 20x
    print("\n⚙️ 嘗試設定槓桿倍數 (20x)...")
    resp_lev = _req("POST", "/fapi/v1/leverage", {"symbol": SYMBOL, "leverage": 20})
    if "leverage" in resp_lev:
        print(f"✅ 槓桿設定成功：{resp_lev['leverage']}x")
    else:
        print("❌ 槓桿設定失敗:", resp_lev)
        return False

    print("\n🎯 初始化完成！你的環境設定如下：")
    print(f"  模式：全倉")
    print(f"  槓桿：20x")
    print(f"  交易對：{SYMBOL}")
    print("────────────────────────────────────────\n")
    return True


# === 查倉位 ===
def get_position(symbol=SYMBOL):
    for pos in _req("GET", "/fapi/v2/positionRisk"):
        if pos["symbol"] == symbol:
            amt = float(pos["positionAmt"])
            entry = float(pos["entryPrice"])
            upnl = float(pos["unRealizedProfit"])
            return amt, entry, upnl
    return 0, 0, 0

# === 查現價與安全開倉量 ===
def get_capacity(leverage=20):
    acc = _req("GET", "/fapi/v2/account")
    if "availableBalance" not in acc:
        print("🚫 無法取得帳戶資訊:", acc); return 0
    bal = float(acc["availableBalance"])
    price = float(_req("GET", "/fapi/v1/ticker/price", {"symbol": SYMBOL})["price"])
    safe = (bal * leverage / price) * 0.9
    print(f"💰 可用資金:{bal:.2f}USDT｜槓桿:{leverage}x｜現價:{price:.2f}｜建議開倉:{safe:.4f}BTC")
    return round(safe, 3)

# === 市價開多（無倉才開） ===
def buy_market(qty):
    amt, entry, _ = get_position()
    if amt > 0:
        print(f"⚠️ 已有多單 {amt} BTC（均價 {entry}），不再開倉。"); return
    elif amt < 0:
        print("⚠️ 偵測到空單（理論上不應存在），請手動檢查帳戶。"); return
    print(f"➡️ 市價開多 {qty} BTC ...")
    res = _req("POST", "/fapi/v1/order", {"symbol": SYMBOL, "side": "BUY", "type": "MARKET", "quantity": qty})
    print("✅ 開倉結果:", res)

# === 市價平倉（僅平多單） ===
def sell_close():
    amt, entry, upnl = get_position()
    if amt <= 0:
        print("ℹ️ 沒有多單，不執行平倉。"); return
    print(f"📊 平倉 {amt} BTC，均價 {entry}，浮盈虧 {upnl:.2f} USDT")
    res = _req("POST", "/fapi/v1/order", {"symbol": SYMBOL, "side": "SELL", "type": "MARKET", "quantity": round(amt, 3)})
    print("✅ 平倉結果:", res)

# === 主程式 ===
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='根據 latest_trading_assessment.json 的 recommendation 決定開倉/平倉操作')
    parser.add_argument('--json', '-j', default='data/latest_trading_assessment.json', help='assessment JSON 檔案路徑')
    parser.add_argument('--config', '-c', default='user/api.config', help='API config 檔案路徑（預設 user/api.config）')
    parser.add_argument('--live', action='store_true', help='若帶此參數，會嘗試連 API 並執行下單（小心）')
    args = parser.parse_args()

    # 若指定了 config 路徑，嘗試讀取並覆寫全域 API_KEY / SECRET_KEY / BASE_URL / SYMBOL
    cfg_from_cli = load_api_config(args.config)
    if cfg_from_cli:
        if cfg_from_cli.get('API_KEY'):
            API_KEY = cfg_from_cli.get('API_KEY')
        if cfg_from_cli.get('SECRET_KEY'):
            SECRET_KEY = cfg_from_cli.get('SECRET_KEY')
        if cfg_from_cli.get('BASE_URL'):
            BASE_URL = cfg_from_cli.get('BASE_URL')
        if cfg_from_cli.get('SYMBOL'):
            SYMBOL = cfg_from_cli.get('SYMBOL')

    def process_recommendation(json_path: str, live: bool = False):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 無法讀取 JSON 檔案 {json_path}: {e}")
            return

        rec = data.get('recommendation') or data.get('trading_signals', {}).get('recommendation')
        # 有些檔案會把買賣分數放在 trading_signals，例如示範檔案
        print(f"Assessment recommendation: {rec}")

        if not rec:
            print("⚠️ recommendation 欄位不存在，無法決定操作。")
            return

        rec = str(rec).strip().lower()

        # 判斷文字
        if rec in ['買入', 'buy', 'long']:
            print("🔔 建議：買入 (Long)")
            if live:
                if setup():
                    qty = get_capacity()
                    if qty > 0:
                        buy_market(qty)
                    else:
                        print("⚠️ 無可用建倉量")
            else:
                print("[DRY RUN] 不會下單。若要執行請加上 --live。")
        elif rec in ['賣出', 'sell', 'short', '平倉', 'sell exit', 'exit']:
            print("🔔 建議：賣出 / 平倉 (Close Long)")
            if live:
                if setup():
                    sell_close()
            else:
                print("[DRY RUN] 不會下單。若要執行請加上 --live。")
        elif rec in ['持有', 'hold', 'hold position', '觀望']:
            print("🔒 建議：持有/觀望，暫不執行任何操作")
        else:
            # 嘗試簡單關鍵字辨識
            if 'buy' in rec or '買' in rec:
                print("🔔 建議（關鍵字偵測）：買入 (Long)")
            elif 'sell' in rec or '賣' in rec or '平' in rec:
                print("🔔 建議（關鍵字偵測）：賣出 / 平倉")
            else:
                print("⚠️ 無法辨識的 recommendation 字串，請檢查 JSON 檔案內容。")

    # 預設為 dry-run
    process_recommendation(args.json, live=args.live)
