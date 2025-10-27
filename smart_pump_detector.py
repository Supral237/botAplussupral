import os
import time
import requests
import threading
from datetime import datetime, UTC
from dotenv import load_dotenv
from flask import Flask, request

# ============================
# 🔧 Configuration
# ============================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("[ERREUR] ⚠️ Clés Telegram manquantes dans .env")
    TELEGRAM_TOKEN = None
    CHAT_ID = None

TOKENS = ["SOL", "PEPE", "WIF", "TIA", "ASTR"]

# ============================
# 🧠 Fonctions utilitaires
# ============================
def log(msg: str):
    print(f"[{datetime.now(UTC).strftime('%H:%M:%S')}] {msg}")

def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("⚠️ Impossible d’envoyer le message : clés Telegram absentes")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        log(f"Erreur Telegram : {e}")

# ============================
# 📊 Analyse intelligente
# ============================
def get_price(symbol: str):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT", timeout=10)
        return float(r.json()["price"])
    except Exception:
        return None

def get_volume(symbol: str):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT", timeout=10)
        return float(r.json()["quoteVolume"])
    except Exception:
        return 0.0

def fake_social_score(symbol: str):
    """Simule un score social (remplacer par API Twitter plus tard)"""
    return hash(symbol + str(datetime.now().minute)) % 100

def fake_whale_activity(symbol: str):
    """Simule activité baleine (futur : API whale-alert.io)"""
    return hash(symbol + "whale") % 50

def fake_news_alert(symbol: str):
    """Simule détection d'annonce (futur : API CoinMarketCal)"""
    return symbol in ["SOL", "TIA"]

def analyze_token(symbol: str):
    """Analyse globale avec 4 critères"""
    price = get_price(symbol)
    volume = get_volume(symbol)
    if not price or volume == 0:
        return None

    # Calcul des conditions
    cond_volume = volume > 5_000_000  # volume élevé
    cond_social = fake_social_score(symbol) > 70
    cond_whale = fake_whale_activity(symbol) > 30
    cond_news = fake_news_alert(symbol)

    score = sum([cond_volume, cond_social, cond_whale, cond_news])
    return {
        "symbol": symbol,
        "price": price,
        "volume": volume,
        "conditions": (cond_volume, cond_social, cond_whale, cond_news),
        "score": score
    }

# ============================
# 🔍 Détection des pumps
# ============================
def detect_pumps():
    log("🚀 SmartPump lancé (Render, mode intelligent)")
    send_telegram_message("🤖 Bot SmartPump connecté et opérationnel ✅")

    while True:
        for token in TOKENS:
            log(f"Analyse de {token}...")
            result = analyze_token(token)
            if not result:
                continue

            score = result["score"]
            if score >= 3:
                msg = (
                    f"🚨 PUMP détecté sur {token} !\n"
                    f"💰 Prix : {result['price']:.4f} USDT\n"
                    f"📊 Volume : {result['volume']:.0f}\n"
                    f"🔥 Score : {score}/4 conditions\n"
                    f"🧠 Critères :\n"
                    f" - Volume élevé ✅ {result['conditions'][0]}\n"
                    f" - Activité sociale ✅ {result['conditions'][1]}\n"
                    f" - Baleines actives ✅ {result['conditions'][2]}\n"
                    f" - Annonce/rumeur ✅ {result['conditions'][3]}"
                )
                log(msg)
                send_telegram_message(msg)
            else:
                log(f"Aucune anomalie détectée sur {token} (score={score})")

            time.sleep(5)

        log("⏳ Nouvelle analyse dans 3 minutes...")
        time.sleep(180)

# ============================
# 🌐 Serveur Flask (Render)
# ============================
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 SmartPump Detector opérationnel sur Render"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Webhook Telegram pour /start"""
    data = request.get_json()
    if "message" in data and data["message"].get("text") == "/start":
        send_telegram_message("🤖 Bot SmartPump connecté et opérationnel ✅")
    return "ok"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ============================
# 🚀 Lancement global
# ============================
if __name__ == "__main__":
    threading.Thread(target=detect_pumps).start()
    run_flask()