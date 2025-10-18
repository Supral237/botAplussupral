import os
import time
import logging
import requests
from flask import Flask, request
import telebot
from threading import Thread

# === CONFIGURATION LOGGING ===
logging.basicConfig(level=logging.INFO, format='[LOG] %(message)s')

# === VARIABLES D'ENVIRONNEMENT ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
HOSTNAME = os.getenv("HOSTNAME")

if not BOT_TOKEN:
    logging.error("❌ ERREUR : La variable BOT_TOKEN n'est pas définie.")
    raise ValueError("La variable BOT_TOKEN n'est pas définie.")
if not HOSTNAME:
    logging.warning("⚠️ Avertissement : HOSTNAME non défini, utilisation par défaut Render.")
    HOSTNAME = "botaplussupral-2.onrender.com"

# === INITIALISATION ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
users = {}  # user_id : fréquence d'analyse (en heures)
watchlist = {}  # user_id : [liste de cryptos à surveiller]

# === CONFIGURATION DU WEBHOOK ===
WEBHOOK_URL = f"https://{HOSTNAME}/webhook"

def setup_webhook():
    logging.info(f"🌐 Configuration du webhook sur : {WEBHOOK_URL}")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)

# === ROUTE FLASK ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_data().decode("utf-8")
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

# === COMMANDE /start ===
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    users[user_id] = 6  # fréquence par défaut
    watchlist[user_id] = []
    bot.reply_to(message, "👋 Salut ! Je suis ton bot crypto A+ Supral 📊\n"
                          "👉 `/signal` pour une analyse instantanée\n"
                          "👉 `/settime X` pour recevoir des signaux automatiques toutes les X heures\n"
                          "👉 `/watch <SYMBOL>` pour surveiller une crypto (ex : /watch OM)")
    logging.info(f"✅ Utilisateur {user_id} initialisé avec fréquence 6h et aucune crypto surveillée.")

# === COMMANDE /settime ===
@bot.message_handler(commands=["settime"])
def set_time(message):
    user_id = message.chat.id
    text = message.text.split()
    if len(text) != 2 or not text[1].isdigit():
        bot.reply_to(message, "⏰ Utilisation : `/settime X` (X = heures)\nEx : `/settime 4` pour toutes les 4h", parse_mode="Markdown")
        return
    hours = int(text[1])
    if hours < 1 or hours > 24:
        bot.reply_to(message, "⚠️ Choisis une fréquence entre 1h et 24h.")
        return
    users[user_id] = hours
    bot.reply_to(message, f"✅ Fréquence mise à jour : toutes les {hours} heures.")
    logging.info(f"🔁 Fréquence de {user_id} mise à {hours}h")

# === COMMANDE /watch ===
@bot.message_handler(commands=["watch"])
def add_watch(message):
    user_id = message.chat.id
    text = message.text.split()
    if len(text) != 2:
        bot.reply_to(message, "⚠️ Utilisation : `/watch SYMBOL`\nEx : `/watch OM`", parse_mode="Markdown")
        return
    symbol = text[1].upper()
    watchlist.setdefault(user_id, [])
    if symbol in watchlist[user_id]:
        bot.reply_to(message, f"👀 Tu surveilles déjà {symbol}.")
        return
    watchlist[user_id].append(symbol)
    bot.reply_to(message, f"✅ Tu surveilles maintenant {symbol}. Je t’enverrai une alerte si elle bouge fort 📈📉")
    logging.info(f"👁️ {user_id} surveille maintenant {symbol}")

# === FONCTION D'ANALYSE DEXSCREENER ===
def get_top_crypto():
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/tokens")
        data = response.json()
        pairs = data.get("pairs", [])
        sorted_pairs = sorted(pairs, key=lambda x: x.get("volume", 0), reverse=True)[:3]
        results = []
        for p in sorted_pairs:
            name = p.get("baseToken", {}).get("symbol", "N/A")
            price = p.get("priceUsd", "?")
            vol = p.get("volume", 0)
            change = p.get("priceChange", {}).get("h24", 0)
            note = "🔥 Fort potentiel" if change > 5 else "⚠️ Surveillance"
            results.append(f"{name} — ${price}\nVolume: {vol:,}\nVariation 24h: {change}%\nNote: {note}")
        return results
    except Exception as e:
        logging.error(f"Erreur DexScreener : {e}")
        return None

# === ANALYSE SPÉCIFIQUE POUR /watch ===
def check_watchlist():
    for user_id, symbols in watchlist.items():
        for symbol in symbols:
            try:
                url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
                data = requests.get(url).json()
                pairs = data.get("pairs", [])
                if not pairs:
                    continue
                pair = pairs[0]
                name = pair["baseToken"]["symbol"]
                price = pair["priceUsd"]
                change = pair["priceChange"]["h24"]
                if abs(change) >= 5:
                    msg = f"🚨 *ALERTE {name}* 🚨\nPrix: ${price}\nVariation 24h: {change}%\nNote: {'🔥 Pump détecté' if change > 0 else '⚠️ Dump détecté'}"
                    bot.send_message(user_id, msg, parse_mode="Markdown")
                    logging.info(f"📢 Alerte envoyée à {user_id} pour {name}")
            except Exception as e:
                logging.error(f"Erreur analyse {symbol}: {e}")

# === ENVOI DES SIGNAUX AUTOMATIQUES ===
def envoyer_signaux(user_id):
    cryptos = get_top_crypto()
    if not cryptos:
        bot.send_message(user_id, "⚠️ Aucune donnée trouvée.")
        return
    message = "📊 *Signal crypto automatique*\n\n" + "\n\n".join(cryptos)
    bot.send_message(user_id, message, parse_mode="Markdown")

# === COMMANDE /signal ===
@bot.message_handler(commands=["signal"])
def signal_manuel(message):
    user_id = message.chat.id
    bot.reply_to(message, "🔎 Analyse du marché en cours...")
    cryptos = get_top_crypto()
    if not cryptos:
        bot.send_message(user_id, "⚠️ Aucune donnée trouvée pour le moment.")
        return
    msg = "📈 *Signal instantané*\n\n" + "\n\n".join(cryptos)
    bot.send_message(user_id, msg, parse_mode="Markdown")

# === SCHEDULER PRINCIPAL ===
def scheduler_loop():
    last_sent = {}
    while True:
        current_time = time.time()
        for user_id, hours in users.items():
            if user_id not in last_sent or current_time - last_sent[user_id] >= hours * 3600:
                envoyer_signaux(user_id)
                last_sent[user_id] = current_time
        check_watchlist()
        time.sleep(1800)  # vérifie toutes les 30 minutes

# === LANCEMENT ===
if __name__ == "__main__":
    logging.info(f"✅ BOT_TOKEN détecté : {BOT_TOKEN[:8]}********")
    logging.info(f"✅ HOSTNAME utilisé : {HOSTNAME}")
    logging.info("🚀 Démarrage du bot A+ Supral avec surveillance personnalisée...")
    setup_webhook()
    Thread(target=scheduler_loop).start()
    app.run(host="0.0.0.0", port=10000)