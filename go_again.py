import time, hmac, hashlib, requests, os, ast, json
from pathlib import Path
import argparse

# === API 基本設定 ===
BASE_URL = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"
API_KEY = ""
SECRET_KEY = ""


# === 載入設定檔 ===
def load_api_config(path: str):
    """安全地從簡單 Python-like config 檔載入 API_KEY、SECRET_KEY、BASE_URL、SYMBOL"""
    cfg = {}
    try:
        p = Path(path)
        if not p.exists():
            return cfg
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src, mode="exec")
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in ("API_KEY", "SECRET_KEY", "BASE_URL", "SYMBOL"):
                        v = node.value
                        if isinstance(v, ast.Constant) and isinstance(v.value, str):
                            cfg[t.id] = v.value
    except Exception:
        return {}
    return cfg


# === 通用 API 請求 ===
def _sign(params):
    q = "&".join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(SECRET_KEY.encode(), q.encode(), hashlib.sha256).hexdigest()


def _req(method, endpoint, params=None):
    if params is None:
        params = {}
    params["timestamp"] = int(time.time() * 1000)
    params["signature"] = _sign(params)
    headers = {"X-MBX-APIKEY": API_KEY}
    url = BASE_URL + endpoint
    try:
        res = requests.request(method, url, params=params, headers=headers, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}


# === 初始化 ===
def setup():
    print("🛠️ 初始化 Binance Futures 設定中...")
    print("────────────────────────────────────────")

    if _req("GET", "/fapi/v1/ping") == {}:
        print("✅ API 連線成功")
    else:
        print("❌ API 連線失敗"); return False

    acc = _req("GET", "/fapi/v2/account")
    if "availableBalance" in acc:
        print(f"✅ 帳戶驗證成功，可用餘額：{acc['availableBalance']} USDT")
    else:
        print("❌ 帳戶驗證失敗:", acc); return False

    print("\n⚙️ 嘗試設定全倉模式...")
    m = _req("POST", "/fapi/v1/marginType", {"symbol": SYMBOL, "marginType": "CROSSED"})
    if m == {} or m.get("code") == -4046:
        print("✅ 全倉模式設定成功（或已是全倉）")
    else:
        print("❌ 全倉模式設定失敗:", m); return False

    print("\n⚙️ 嘗試設定槓桿 20x...")
    l = _req("POST", "/fapi/v1/leverage", {"symbol": SYMBOL, "leverage": 20})
    if "leverage" in l:
        print(f"✅ 槓桿設定成功：{l['leverage']}x")
    else:
        print("❌ 槓桿設定失敗:", l); return False

    print("\n🎯 初始化完成：全倉、20x、交易對", SYMBOL)
    print("────────────────────────────────────────\n")
    return True


# === 基本查詢與操作 ===
def get_position(symbol=SYMBOL):
    for pos in _req("GET", "/fapi/v2/positionRisk"):
        if pos["symbol"] == symbol:
            return float(pos["positionAmt"]), float(pos["entryPrice"]), float(pos["unRealizedProfit"])
    return 0, 0, 0


def get_capacity(leverage=20):
    acc = _req("GET", "/fapi/v2/account")
    if "availableBalance" not in acc:
        print("🚫 無法取得帳戶資訊:", acc); return 0
    bal = float(acc["availableBalance"])
    price = float(_req("GET", "/fapi/v1/ticker/price", {"symbol": SYMBOL})["price"])
    safe = (bal * leverage / price) * 0.9
    print(f"💰 可用:{bal:.2f}USDT｜槓桿:{leverage}x｜現價:{price:.2f}｜建議開倉:{safe:.4f}BTC")
    return round(safe, 3)


def buy_market(qty):
    amt, entry, _ = get_position()
    if amt > 0:
        print(f"⚠️ 已有多單 {amt} BTC（均價 {entry}），不再開倉。"); return
    print(f"➡️ 市價開多 {qty} BTC ...")
    print("✅ 開倉結果:", _req("POST", "/fapi/v1/order",
                         {"symbol": SYMBOL, "side": "BUY", "type": "MARKET", "quantity": qty}))


def sell_close():
    amt, entry, upnl = get_position()
    if amt <= 0:
        print("ℹ️ 無多單，不執行平倉。"); return
    print(f"📊 平倉 {amt} BTC，均價 {entry}，浮盈虧 {upnl:.2f} USDT")
    print("✅ 平倉結果:",
          _req("POST", "/fapi/v1/order",
               {"symbol": SYMBOL, "side": "SELL", "type": "MARKET", "quantity": round(amt, 3)}))


# === 根據 JSON recommendation 操作 ===
def process_recommendation(json_path: str, live: bool = False):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 無法讀取 JSON 檔 {json_path}: {e}")
        return

    rec = data.get("recommendation") or data.get("trading_signals", {}).get("recommendation")
    print(f"📄 Assessment recommendation: {rec}")

    if not rec:
        print("⚠️ recommendation 欄位不存在，無法決定操作。"); return

    rec = str(rec).strip().lower()

    if rec in ["買入", "buy", "long"]:
        print("🔔 建議：買入 (Long)")
        if not live:
            print("[DRY RUN] 不會下單。加上 --live 以執行。"); return
        if setup():
            qty = get_capacity()
            if qty > 0:
                buy_market(qty)
    elif rec in ["賣出", "sell", "平倉", "exit"]:
        print("🔔 建議：賣出 / 平倉 (Close Long)")
        if not live:
            print("[DRY RUN] 不會下單。加上 --live 以執行。"); return
        if setup():
            sell_close()
    elif rec in ["持有", "hold", "觀望"]:
        print("🔒 建議：持有/觀望，不執行操作。")
    else:
        if "buy" in rec or "買" in rec:
            print("🔔 關鍵字偵測：買入 (Long)")
        elif "sell" in rec or "賣" in rec or "平" in rec:
            print("🔔 關鍵字偵測：賣出 / 平倉")
        else:
            print("⚠️ 無法辨識 recommendation 字串。")


# === 主入口 ===
def main():
    parser = argparse.ArgumentParser(description="根據 latest_trading_assessment.json 決定開倉/平倉")
    parser.add_argument("--json", "-j", default="data/latest_trading_assessment.json", help="assessment JSON 檔路徑")
    parser.add_argument("--config", "-c", default="user/api.config", help="API config 檔（預設 user/api.config）")
    parser.add_argument("--live", action="store_true", help="帶此參數會真的執行下單（否則 dry-run）")
    args = parser.parse_args()

    # 載入 config
    cfg = load_api_config(args.config)
    global API_KEY, SECRET_KEY, BASE_URL, SYMBOL
    if cfg:
        API_KEY = cfg.get("API_KEY", API_KEY)
        SECRET_KEY = cfg.get("SECRET_KEY", SECRET_KEY)
        BASE_URL = cfg.get("BASE_URL", BASE_URL)
        SYMBOL = cfg.get("SYMBOL", SYMBOL)

    process_recommendation(args.json, live=args.live)


if __name__ == "__main__":
    main()
