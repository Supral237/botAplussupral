import os
import requests
from flask import Flask, request
import logging

# === Configuration principale ===
TOKEN = os.getenv("BOT_TOKEN", "TON_TOKEN_TELEGRAM_ICI")  # à remplacer si tu veux le tester en local
CHAT_ID = os.getenv("CHAT_ID", "TON_CHAT_ID_ICI")  # optionnel
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "https://botaplussupral-2.onrender.com")

# === Initialisation Flask ===
app = Flask(__name__)

# === Logs utiles pour Render ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Fonction pour envoyer un message Telegram ===
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    return response.json()


# === Webhook Telegram (reçoit les messages) ===
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    logger.info(f"📩 Update reçu : {update}")

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"].lower()

        if text == "/start":
            send_message(chat_id, "🤖 <b>Bot A+</b> est bien en ligne sur Render !\n\nPrêt à surveiller les opportunités crypto 🚀")
        elif "bonjour" in text:
            send_message(chat_id, "👋 Salut ! Content de te revoir Thierry 😎")
        else:
            send_message(chat_id, "📡 Message reçu ! (bientôt, je t’enverrai des signaux crypto 😉)")

    return {"ok": True}


# === Page d'accueil (GET) ===
@app.route("/", methods=["GET"])
def index():
    return "✅ Bot A+ en ligne sur Render.", 200


# === Configuration automatique du webhook ===
def set_webhook():
    set_hook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    res = requests.get(set_hook_url)
    if res.status_code == 200:
        logger.info("✅ Webhook configuré avec succès.")
    else:
        logger.error(f"⚠️ Erreur configuration webhook : {res.text}")


# === Démarrage ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    set_webhook()
    logger.info(f"🚀 Démarrage du bot A+ sur le port {port}")
    app.run(host="0.0.0.0", port=port)
