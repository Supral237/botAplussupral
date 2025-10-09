import telebot
from telebot import types
from flask import Flask, request
import requests
import threading
import time
import schedule
import os

# === CONFIGURATION DU BOT ===
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"  # <-- Remplace ici ton token réel
WEBHOOK_URL = "https://botaplussupral-2.onrender.com/" + BOT_TOKEN  # ton URL Render

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === BASE UTILISATEURS ===
users = set()

# === COMMANDE /start ===
@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    bot.reply_to(message, "👋 Salut ! Je t’enverrai automatiquement des signaux crypto toutes les 6 heures.\n"
                          "Tu peux aussi taper /signal pour recevoir une analyse immédiate 💹")

# === COMMANDE /signal ===
@bot.message_handler(commands=['signal'])
def signal(message):
    bot.reply_to(message, "📡 Analyse en cours, patiente quelques secondes...")
    try:
        msg = generer_signal_crypto()
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant l’analyse : {e}")

# === FONCTION D’ANALYSE COMBINÉE ===
def generer_signal_crypto():
    try:
        # Exemple de base combinée : trending + accumulation fictive
        rumeurs = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coin = rumeurs["coins"][0]["item"]
        name = coin["name"]
        symbol = coin["symbol"]

        # Ici tu peux plus tard brancher une vraie analyse on-chain ou Twitter
        reason = "Rumeurs haussières + accumulation par smart money détectées 📈"
        return f"🚨 *Signal Crypto A+* 🚨\n\n💰 **{name} ({symbol})**\n📊 {reason}\n⏰ Prochaine mise à jour automatique dans 6 heures."
    except Exception as e:
        return f"⚠️ Erreur dans la génération du signal : {e}"

# === FONCTION AUTOMATIQUE (toutes les 6 heures) ===
def envoyer_signaux_periodiques():
    try:
        msg = generer_signal_crypto()
        for chat_id in users:
            bot.send_message(chat_id, msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Erreur lors de l’envoi automatique : {e}")

# === PLANIFICATION ===
def planificateur():
    schedule.every(6).hours.do(envoyer_signaux_periodiques)
    while True:
        schedule.run_pending()
        time.sleep(30)

# === FLASK / WEBHOOK ===
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/', methods=['GET'])
def index():
    return "🤖 Bot A+ actif sur Render ✅", 200

# === LANCEMENT ===
def start_bot():
    threading.Thread(target=planificateur, daemon=True).start()
    print("🚀 Bot A+ prêt : envoi automatique + commande /signal active.")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    start_bot()
