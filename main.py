from flask import Flask, request
import requests
import os

app = Flask(__name__)

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Ton token Telegram dans les variables d'environnement Render
WEBHOOK_URL = f"https://botaplussupral-2.onrender.com/{BOT_TOKEN}"

# === SET WEBHOOK ===
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {"url": WEBHOOK_URL}
    response = requests.post(url, json=data)
    print("🔗 Webhook setup response:", response.text)

# === TRAITEMENT DES MESSAGES ===
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, json=data)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if update and "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text.lower() == "/start":
            send_message(chat_id, "👋 Bienvenue ! Tu recevras bientôt des signaux crypto 🔥")
        else:
            send_message(chat_id, f"Message reçu : {text}")

    return {"ok": True}

@app.route("/", methods=["GET"])
def home():
    return "Bot A+ est en ligne 🚀"

if __name__ == "__main__":
    print("🚀 Bot A+ démarré avec succès sur Render !")
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
