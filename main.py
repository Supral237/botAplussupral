import telebot
from flask import Flask, request

# === CONFIGURATION ===
TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"  # Remplace par ton vrai token Telegram
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === ROUTE WEBHOOK ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Mauvais format', 403

# === MESSAGE DE TEST / PAGE RACINE ===
@app.route('/')
def index():
    return "🤖 Bot Telegram opérationnel sur Render !"

# === HANDLERS ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Salut ! Je suis ton bot crypto. Je t’enverrai bientôt des signaux 💹")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "Message reçu ✅")

# === DÉMARRAGE ===
if __name__ == "__main__":
    import requests

    # URL Render (remplace par la tienne)
    WEBHOOK_URL = "https://botaplussupral-2.onrender.com/webhook"  # ⚠️ à modifier

    # Supprime l'ancien webhook puis configure le nouveau
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")

    print("🚀 Webhook configuré sur :", WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
