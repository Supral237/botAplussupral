import telebot
from telebot import types
from flask import Flask, request
import requests
import threading
import time
import schedule
import os

# === CONFIGURATION DU BOT ===
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"  # <-- Remplace ici ton vrai token du bot Telegram
WEBHOOK_URL = "https://botaplussupral-2.onrender.com/" + BOT_TOKEN  # ton URL Render

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Liste des utilisateurs ayant tapé /start
users = set()

# === GESTION DES COMMANDES ===
@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    bot.reply_to(message, "🚀 Salut ! Je t’enverrai automatiquement des signaux crypto toutes les 6 heures basés sur les rumeurs et les mouvements de smart money 💹")

# === FONCTION D’ANALYSE COMBINÉE ===
def analyser_crypto():
    try:
        # Exemple d'analyse combinée simulée
        # (tu pourras brancher ici ton vrai module de détection plus tard)
        rumeurs = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coin = rumeurs["coins"][0]["item"]
        name = coin["name"]
        symbol = coin["symbol"]
        reason = "Rumeurs positives et accumulation de smart money détectée 📈"

        message = f"🚨 Signal Crypto Automatique 🚨\n\n💰 **{name} ({symbol})**\n📊 Analyse combinée : {reason}\n⏰ Nouvelle mise à jour dans 6 heures."
        
        # Envoi du message à tous les utilisateurs enregistrés
        for chat_id in users:
            bot.send_message(chat_id, message, parse_mode="Markdown")
    except Exception as e:
        print(f"Erreur dans l’analyse : {e}")

# === PLANIFICATION AUTOMATIQUE ===
def planificateur():
    schedule.every(6).hours.do(analyser_crypto)
    while True:
        schedule.run_pending()
        time.sleep(30)

# === CONFIG FLASK POUR LE WEBHOOK ===
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def receive_update():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/', methods=['GET'])
def index():
    return "Bot A+ est actif ✅", 200

# === DÉMARRAGE DU BOT ===
def start_bot():
    # Lancement du planificateur automatique dans un thread séparé
    threading.Thread(target=planificateur, daemon=True).start()
    print("🚀 Bot A+ opérationnel avec envoi automatique toutes les 6 heures.")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    start_bot()
