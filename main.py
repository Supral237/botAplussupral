import os
import time
import logging
import requests
import telebot
from flask import Flask, request

# === CONFIGURATION DU LOGGING ===
logging.basicConfig(level=logging.INFO, format="[LOG] %(message)s")

# === LECTURE DES VARIABLES D'ENVIRONNEMENT ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if not BOT_TOKEN:
    logging.error("❌ ERREUR : La variable BOT_TOKEN n'est pas définie dans Render.")
    raise ValueError("La variable BOT_TOKEN n'est pas définie.")

if not RENDER_EXTERNAL_HOSTNAME:
    logging.warning("⚠️ Variable RENDER_EXTERNAL_HOSTNAME absente, utilisation du fallback localhost.")
    RENDER_EXTERNAL_HOSTNAME = "localhost"

logging.info(f"✅ BOT_TOKEN détecté : {BOT_TOKEN[:10]}********")
logging.info(f"✅ HOSTNAME utilisé : {RENDER_EXTERNAL_HOSTNAME}")

# === INITIALISATION DU BOT ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ROUTE DU WEBHOOK ===
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = request.stream.read().decode("utf-8")
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

# === COMMANDE START ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "👋 Salut ! Je t’enverrai bientôt des signaux crypto basés sur DexScreener 📊")

# === TEST DE DEXSCREENER ===
def get_top_token():
    try:
        url = "https://api.dexscreener.com/latest/dex/tokens"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "pairs" in data and data["pairs"]:
            pair = data["pairs"][0]
            return f"Token : {pair['baseToken']['symbol']} | Volume : {pair['volume']['h24']}$"
        return "Aucun token trouvé."
    except Exception as e:
        logging.error(f"Erreur DexScreener : {e}")
        return "Erreur lors de l'analyse DexScreener."

# === ROUTE TEST SIMPLE ===
@app.route("/", methods=['GET'])
def index():
    return "Bot A+ Supral actif ✅"

# === CONFIGURATION DU WEBHOOK ===
def setup_webhook():
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"
    bot.remove_webhook()
    time.sleep(1)
    success = bot.set_webhook(url=webhook_url)
    if success:
        logging.info(f"✅ Webhook configuré avec succès : {webhook_url}")
    else:
        logging.error(f"❌ Échec de configuration du webhook vers : {webhook_url}")

# === POINT D'ENTRÉE ===
if __name__ == "__main__":
    logging.info("🚀 Démarrage du bot A+ Supral avec DexScreener...")
    setup_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
