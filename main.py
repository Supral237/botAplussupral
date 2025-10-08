import os
import requests
from flask import Flask, request

# Initialisation de l’application Flask
app = Flask(__name__)

# Ton token Telegram doit être dans les variables d’environnement Render
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN non défini dans les variables d'environnement Render")

# ✅ Fonction pour configurer automatiquement le webhook
def set_webhook():
    url = f"https://botaplussupral.onrender.com/{TOKEN}"  # Remplace l’URL si besoin
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={url}"
    response = requests.get(webhook_url)
    print("Configuration du webhook :", response.text)

# ✅ Route principale — juste pour test
@app.route('/')
def home():
    return "Bot A+ en ligne ✅"

# ✅ Route qui reçoit les mises à jour Telegram
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = request.get_json()
    print(update)  # Pour voir les messages reçus dans les logs Render

    if not update or "message" not in update:
        return "no update", 200

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").lower()

    # Réponse simple au /start
    if text == "/start":
        send_message(chat_id, "👋 Bonjour ! Je suis ton bot A+ prêt à fonctionner 🚀")
    elif "bonjour" in text:
        send_message(chat_id, "Salut 👋 ! Comment vas-tu ?")
    else:
        send_message(chat_id, "Je suis bien en ligne ✅")

    return "ok", 200

# ✅ Fonction d’envoi de message
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": chat_id, "text": text})

# ✅ Lancement de l’application Flask
if __name__ == '__main__':
    print("🔍 Démarrage du bot A+...")
    set_webhook()
    app.run(host='0.0.0.0', port=10000)
