import os
import time
import requests
import threading
from datetime import datetime, UTC
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# ============================
# 🔧 Configuration
# ============================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("[ERREUR] ⚠️ Les clés Telegram sont manquantes dans .env")
    TELEGRAM_TOKEN = None
    CHAT_ID = None

TOKENS = ["ASTR", "PEPE", "WIF", "SOL", "TIA"]

# ============================
# ⚙️ Fonctions principales
# ============================
def log(message: str):
    print(f"[{datetime.now(UTC).strftime('%H:%M:%S')}] {message}")

def send_telegram_message(msg: str):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            log(f"Erreur Telegram : {e}")
    else:
        log("⚠️ Impossible d’envoyer le message : clés Telegram absentes")

def get_price(symbol: str):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        r = requests.get(url, timeout=10).json()
        return float(r["price"])
    except Exception:
        return None

def analyze_token(symbol: str):
    price = get_price(symbol)
    if not price:
        return None
    score = 0
    if price > 1:
        score += 1
    if "PEPE" in symbol:
        score += 1
    if price > 10:
        score += 1
    return score

def detect_pumps():
    log("🚀 Smart Pump Detector lancé (Render)")
    while True:
        for token in TOKENS:
            log(f"Analyse de {token}...")
            score = analyze_token(token)
            if score and score >= 3:
                message = f"🚨 PUMP détecté sur {token} (score={score})"
                log(message)
                send_telegram_message(message)
            else:
                log(f"Rien de spécial sur {token} (score={score})")
            time.sleep(5)
        log("⏳ Nouvelle vérification dans 3 min...")
        time.sleep(180)

# ============================
# 🌐 Flask pour Webhook
# ============================
app = Flask(__name__)

@app.route('/')
def home():
    return "Smart Pump Detector est en ligne 🚀"

@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Recevoir les messages Telegram via Webhook"""
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        log(f"Message reçu de {chat_id}: {text}")
        # Réponse automatique simple
        if text.lower() == "/start":
            send_telegram_message("Bot SmartPump connecté et opérationnel ✅")
    return jsonify(ok=True)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============================
# 🚀 Lancement
# ============================
if __name__ == "__main__":
    thread_bot = threading.Thread(target=detect_pumps)
    thread_bot.start()
    run_flask()