import os
import requests
from flask import Flask, request
import schedule
import time
import threading

# ===== CONFIGURATION =====
TOKEN = os.getenv("TELEGRAM_TOKEN")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
WEBHOOK_URL = f"https://botaplussupral-2.onrender.com/{TOKEN}"
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# ===== FONCTIONS UTILITAIRES =====

def send_message(chat_id, text):
    url = f"{BOT_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erreur envoi message: {e}")

# ===== RUMEURS / NEWS (via Twitter) =====
def get_crypto_news():
    if not BEARER_TOKEN:
        return "⚠️ Aucune clé Twitter configurée."
    try:
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
        query = "crypto (partnership OR listing OR announcement OR upgrade) -is:retweet lang:fr"
        url = f"https://api.x.com/2/tweets/search/recent?query={query}&max_results=5&tweet.fields=created_at"
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json().get("data", [])
        if not data:
            return "Aucune rumeur trouvée récemment."
        news = [f"📰 {n['text']}" for n in data]
        return "\n\n".join(news)
    except Exception as e:
        return f"Erreur récupération news : {e}"

# ===== SMART MONEY (via Covalent) =====
def get_smart_money():
    if not COVALENT_API_KEY:
        return "⚠️ Clé Covalent manquante."
    try:
        # Exemple : un portefeuille souvent actif sur Ethereum
        wallet = "0xb1b2d032AA2F52347fbcfd08E5C3Cc55216E8404"
        url = f"https://api.covalenthq.com/v1/1/address/{wallet}/transactions_v3/?key={COVALENT_API_KEY}"
        res = requests.get(url, timeout=10).json()
        txs = res.get("data", {}).get("items", [])
        if not txs:
            return "Aucune activité détectée sur le portefeuille."
        latest = txs[:3]
        out = []
        for tx in latest:
            value = tx.get("value_quote", 0)
            to_addr = tx.get("to_address", "")
            symbol = tx.get("tx_hash", "")[:10]
            out.append(f"💰 Tx {symbol} → {to_addr}\nValeur estimée : ${round(value,2)}")
        return "\n\n".join(out)
    except Exception as e:
        return f"Erreur Covalent : {e}"

# ===== TRAITEMENT DES COMMANDES =====
@app.route(f"/{TOKEN}", methods=["POST"])
def handle_message():
    update = request.get_json()
    if not update:
        return "ok"
    
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").lower()

    if text == "/start":
        send_message(chat_id, "👋 Bienvenue sur le bot A+ ! Je t’enverrai bientôt des signaux crypto 🔥")
    elif text == "/rumeurs":
        send_message(chat_id, "🔍 Recherche des rumeurs crypto en cours…")
        send_message(chat_id, get_crypto_news())
    elif text == "/smart":
        send_message(chat_id, "💼 Analyse des portefeuilles Smart Money…")
        send_message(chat_id, get_smart_money())
    else:
        send_message(chat_id, "❓ Commandes disponibles :\n/start\n/rumeurs\n/smart")

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot A+ actif sur Render !"

# ===== PLANIFICATION (optionnelle) =====
def job_auto_message():
    print("⏰ Envoi automatique en cours…")

schedule.every(6).hours.do(job_auto_message)

def scheduler_thread():
    while True:
        schedule.run_pending()
        time.sleep(60)

# ===== DÉMARRAGE DU BOT =====
def set_webhook():
    print("🔗 Configuration du Webhook…")
    res = requests.get(f"{BOT_URL}/setWebhook?url={WEBHOOK_URL}")
    print("Réponse Webhook:", res.text)

if __name__ == "__main__":
    set_webhook()
    threading.Thread(target=scheduler_thread, daemon=True).start()
    print("🚀 Bot A+ démarré avec succès sur Render !")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
