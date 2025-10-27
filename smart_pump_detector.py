# smart_pump_detector_4signaux.py
# Detecteur PRE-PUMP basé sur 4 signaux :
# 1) Volume spike (Binance klines)
# 2) Social buzz (LunarCrush, optionnel)
# 3) Whale trades (gros trades sur Binance aggTrades)
# 4) News events (CoinMarketCal, optionnel)
#
# Envoi d'alerte Telegram si >= 3 signaux.
#
# Conçu pour Pydroid 3 (Android). Dépendances : requests, python-dotenv

import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
# Chemin du .env : adapte si besoin
ENV_PATH = os.getenv("SMARTPUMP_ENV_PATH", "/storage/emulated/0/Analyze/.env")
load_dotenv(ENV_PATH)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Optionnels (mettre dans .env si disponibles)
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")       # optional
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY") # optional

# Liste des symbols (Binance format) à surveiller
TARGETS = os.getenv("SMARTPUMP_TARGETS", "ASTRUSDT,PEPEUSDT,WIFUSDT,SOLUSDT,TIAUSDT").split(",")

# Paramètres de détection
CHECK_INTERVAL = int(os.getenv("SMARTPUMP_INTERVAL", 180))          # secondes entre cycles
VOLUME_MULTIPLIER_THRESHOLD = float(os.getenv("SMARTPUMP_VOL_MULT", 2.0))  # vol_last / vol_avg >= threshold
WHale_TRADE_USD = float(os.getenv("SMARTPUMP_WHALE_USD", 50000))    # trade >= this USD counts as whale trade
SOCIAL_SCORE_THRESHOLD = float(os.getenv("SMARTPUMP_SOCIAL", 200))  # lunarcrush social_volume threshold
SCORE_THRESHOLD = int(os.getenv("SMARTPUMP_SCORE_THRESHOLD", 3))    # signals required to alert

ENTRY_BUFFER_PCT = float(os.getenv("SMARTPUMP_ENTRY_BUFFER", 0.002)) # entry = best_bid * (1 + buffer)
TP_PCT = float(os.getenv("SMARTPUMP_TP_PCT", 0.05))                 # take profit +5%
SL_PCT = float(os.getenv("SMARTPUMP_SL_PCT", 0.02))                 # stop loss -2%

# -------------------------
# UTIL
# -------------------------
def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def log(msg: str):
    print(f"[{now_utc()}] {msg}")

def send_telegram(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ Telegram credentials missing (TELEGRAM_TOKEN/TELEGRAM_CHAT_ID in .env)")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=8)
        if r.status_code == 200:
            return True
        else:
            log(f"Telegram API returned {r.status_code}: {r.text}")
            return False
    except Exception as e:
        log(f"Telegram send error: {e}")
        return False

# -------------------------
# BINANCE DATA HELPERS
# -------------------------
BINANCE_REST = "https://api.binance.com"

def get_klines(symbol: str, interval: str = "15m", limit: int = 12):
    """Return list of klines arrays or None"""
    try:
        url = f"{BINANCE_REST}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"Error get_klines({symbol}): {e}")
        return None

def get_order_book(symbol: str, limit: int = 5):
    try:
        url = f"{BINANCE_REST}/api/v3/depth"
        params = {"symbol": symbol, "limit": limit}
        r = requests.get(url, params=params, timeout=6)
        r.raise_for_status()
        data = r.json()
        bids = [(float(p[0]), float(p[1])) for p in data.get("bids", [])]
        asks = [(float(p[0]), float(p[1])) for p in data.get("asks", [])]
        return {"bids": bids, "asks": asks}
    except Exception as e:
        log(f"Error order_book({symbol}): {e}")
        return {"bids": [], "asks": []}

def get_recent_agg_trades(symbol: str, limit: int = 100):
    """AggTrades (recent trades) - used to detect large trades"""
    try:
        url = f"{BINANCE_REST}/api/v3/aggTrades"
        params = {"symbol": symbol, "limit": limit}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"Error aggTrades({symbol}): {e}")
        return []

def get_price(symbol: str):
    try:
        url = f"{BINANCE_REST}/api/v3/ticker/price"
        r = requests.get(url, params={"symbol": symbol}, timeout=6)
        r.raise_for_status()
        return float(r.json().get("price", 0))
    except Exception:
        return None

# -------------------------
# SOCIAL (LunarCrush) - optional
# -------------------------
def get_social_volume_lunar(symbol_short: str):
    """Return social_volume numeric or 0 if unavailable"""
    if not LUNARCRUSH_API_KEY:
        return 0
    try:
        # symbol_short expected like "PEPE" (without USDT)
        url = f"https://api.lunarcrush.com/v2?data=assets&key={LUNARCRUSH_API_KEY}&symbol={symbol_short}"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        j = r.json()
        data = j.get("data") or []
        if not data:
            return 0
        return float(data[0].get("social_volume", 0) or 0)
    except Exception as e:
        log(f"LunarCrush error ({symbol_short}): {e}")
        return 0

# -------------------------
# NEWS (CoinMarketCal) - optional
# -------------------------
def check_coinmarketcal_events(symbol_short: str):
    if not COINMARKETCAL_API_KEY:
        return False
    try:
        url = "https://developers.coinmarketcal.com/v1/events"
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        params = {"coins": symbol_short.lower()}
        r = requests.get(url, headers=headers, params=params, timeout=8)
        r.raise_for_status()
        body = r.json().get("body", [])
        # If there is at least one event, return True
        return len(body) > 0
    except Exception as e:
        log(f"CoinMarketCal error ({symbol_short}): {e}")
        return False

# -------------------------
# SIGNAL COMPUTATION
# -------------------------
def check_volume_spike(symbol: str):
    """Compare last 15m volume to average of previous N 15m candles"""
    klines = get_klines(symbol, interval="15m", limit=8)  # ~2h of 15m candles
    if not klines or len(klines) < 3:
        return False, {}
    # last closed candle is klines[-2] (because klines[-1] may be current open)
    # We'll compare last closed (idx -2) to average of previous 4 closed candles (-6..-3)
    try:
        last_closed = klines[-2]
        prev_closed_slice = klines[-6:-2]  # 4 candles
        last_vol = float(last_closed[5])
        prev_vols = [float(k[5]) for k in prev_closed_slice if k]
        avg_prev = sum(prev_vols) / len(prev_vols) if prev_vols else 0.0
        vol_mult = (last_vol / avg_prev) if avg_prev > 0 else 1.0
        diag = {"last_vol": last_vol, "avg_prev": avg_prev, "vol_mult": vol_mult}
        is_spike = vol_mult >= VOLUME_MULTIPLIER_THRESHOLD
        return is_spike, diag
    except Exception as e:
        log(f"Volume spike calc error {symbol}: {e}")
        return False, {}

def check_whale_trades(symbol: str):
    """Detect large individual trades in recent aggTrades >= WHale_TRADE_USD"""
    trades = get_recent_agg_trades(symbol, limit=200)
    if not trades:
        return False, {}
    price = get_price(symbol) or 0.0
    large_count = 0
    large_trades = []
    for t in trades:
        try:
            qty = float(t.get("q") or t.get("quantity") or 0)  # aggTrades uses 'q' in some responses
            # Calculate USD value step-by-step:
            # qty * price = usd_val
            usd_val = qty * price
            if usd_val >= WHale_TRADE_USD:
                large_count += 1
                large_trades.append({"qty": qty, "usd": usd_val, "id": t.get("a")})
        except Exception:
            continue
    diag = {"large_count": large_count, "sample": large_trades[:3]}
    return (large_count >= 1), diag

def check_social_hype(symbol: str):
    short = symbol.replace("USDT", "")
    val = get_social_volume_lunar(short)
    return (val >= SOCIAL_SCORE_THRESHOLD), {"social_volume": val}

def check_news(symbol: str):
    short = symbol.replace("USDT", "")
    has_event = check_coinmarketcal_events(short)
    return has_event, {}

# -------------------------
# ENTRY SUGGESTION
# -------------------------
def suggest_entry(symbol: str):
    ob = get_order_book(symbol, limit=5)
    price = get_price(symbol) or 0.0
    best_bid = ob["bids"][0][0] if ob["bids"] else price
    # step-by-step arithmetic to avoid mistakes:
    # entry = best_bid * (1 + ENTRY_BUFFER_PCT)
    entry = best_bid * (1.0 + ENTRY_BUFFER_PCT)
    tp = entry * (1.0 + TP_PCT)
    sl = entry * (1.0 - SL_PCT)
    # rounding
    if price >= 1:
        entry = round(entry, 4)
        tp = round(tp, 4)
        sl = round(sl, 4)
    else:
        entry = round(entry, 6)
        tp = round(tp, 6)
        sl = round(sl, 6)
    return {"price": price, "best_bid": best_bid, "entry": entry, "tp": tp, "sl": sl}

# -------------------------
# MAIN ANALYSIS
# -------------------------
def analyze_and_alert(symbol: str):
    sigs = []
    diags = {}

    vol_ok, vol_diag = check_volume_spike(symbol)
    if vol_ok:
        sigs.append("volume_spike")
    diags["volume"] = vol_diag

    whale_ok, whale_diag = check_whale_trades(symbol)
    if whale_ok:
        sigs.append("whale_trades")
    diags["whales"] = whale_diag

    social_ok, social_diag = check_social_hype(symbol)
    if social_ok:
        sigs.append("social_buzz")
    diags["social"] = social_diag

    news_ok, news_diag = check_news(symbol)
    if news_ok:
        sigs.append("news_event")
    diags["news"] = news_diag

    score = len(sigs)
    return score, sigs, diags

# -------------------------
# RUN LOOP
# -------------------------
def main_loop():
    log("Smart Pump Detector (4 signaux) démarré")
    # startup message
    send_telegram(f"🚀 Smart Pump Detector lancé at {now_utc()}")
    while True:
        for sym in TARGETS:
            try:
                log(f"Analyse {sym} ...")
                score, sigs, diags = analyze_and_alert(sym)
                log(f"{sym} signals={sigs} score={score}")
                if score >= SCORE_THRESHOLD:
                    sug = suggest_entry(sym)
                    reasons = ", ".join(sigs)
                    msg = (
                        f"🚨 <b>PRE-PUMP SIGNAL</b>\n"
                        f"Pair: <b>{sym}</b>\n"
                        f"Score: {score}/{4}\n"
                        f"Signals: {reasons}\n\n"
                        f"Current price: {sug['price']}\n"
                        f"Best bid: {sug['best_bid']}\n"
                        f"Suggested entry (limit): {sug['entry']}\n"
                        f"TP: {sug['tp']} (+{int(TP_PCT*100)}%)\n"
                        f"SL: {sug['sl']} (-{int(SL_PCT*100)}%)\n\n"
                        f"Diagnostics: {diags}\n"
                        f"Time: {now_utc()}\n\n"
                        f"_Suggestion: place a LIMIT BUY at entry price. Adjust size & slippage accordingly._"
                    )
                    send_telegram(msg)
                    log(f"ALERTE ENVOYÉE pour {sym} -> {reasons}")
                else:
                    log(f"Aucun pre-pump sur {sym} (score={score})")
            except Exception as e:
                log(f"Erreur analyse {sym}: {e}")
            time.sleep(1)
        log(f"Pause {CHECK_INTERVAL}s avant prochain cycle\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()