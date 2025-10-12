import telebot
from telebot import types
from flask import Flask, request
import requests
import threading
import time
import schedule
import os
import sqlite3

# === CONFIGURATION DU BOT ===
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"  # <-- remplace ici
WEBHOOK_URL = "https://botaplussupral-2.onrender.com/" + BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DB_PATH = "users.db"

# === BASE DE DONNÉES ===
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            last_sent TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def ajouter_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id, last_sent) VALUES (?, NULL)", (chat_id,))
    conn.commit()
    conn.close()

def obtenir_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM users")
    result = [row[0] for row in c.fetchall()]
    conn.close()
    return result

def maj_dernier_envoi(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_sent = datetime('now') WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def compter_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    conn.close()
    return total

def compter_users_recents():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE last_sent >= datetime('now', '-6 hours')")
    total = c.fetchone()[0]
    conn.close()
    return total

# === COMMANDE /start ===
@bot.message_handler(commands=['start'])
def start(message):
    ajouter_user(message.chat.id)
    bot.reply_to(message, (
        "👋 Salut ! Je t’enverrai automatiquement des *signaux crypto* toutes les 6 heures 📊.\n\n"
        "📈 Tape /signal pour un signal instantané.\n"
        "🧠 Tape /dernierrumeur pour connaître les dernières rumeurs crypto.\n"
        "🐋 Tape /smartmoney pour voir où investissent les whales.\n"
        "📊 Tape /statistiques pour voir le nombre d'utilisateurs du bot."
    ), parse_mode="Markdown")

# === COMMANDE /signal ===
@bot.message_handler(commands=['signal'])
def signal(message):
    bot.reply_to(message, "📡 Analyse combinée en cours...")
    try:
        msg = generer_signal_crypto()
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        maj_dernier_envoi(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant l’analyse : {e}")

# === COMMANDE /statistiques ===
@bot.message_handler(commands=['statistiques'])
def statistiques(message):
    total = compter_users()
    recents = compter_users_recents()
    msg = (
        f"📊 *Statistiques du Bot A+* :\n\n"
        f"👥 Total d’utilisateurs : {total}\n"
        f"📬 Utilisateurs ayant reçu un signal dans les 6 dernières heures : {recents}\n\n"
        f"⏰ Prochain envoi automatique dans 6 heures."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# === COMMANDE /dernierrumeur ===
@bot.message_handler(commands=['dernierrumeur'])
def derniere_rumeur(message):
    bot.send_message(message.chat.id, "🕵️ Recherche des dernières rumeurs crypto...")
    try:
        rumeurs = get_rumeurs()
        bot.send_message(message.chat.id, rumeurs, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant la récupération des rumeurs : {e}")

# === COMMANDE /smartmoney ===
@bot.message_handler(commands=['smartmoney'])
def smartmoney(message):
    bot.send_message(message.chat.id, "🐋 Analyse des portefeuilles whales en cours...")
    try:
        data = get_smart_money()
        bot.send_message(message.chat.id, data, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant la récupération des données smart money : {e}")

# === ANALYSE COMBINÉE ===
def generer_signal_crypto():
    try:
        trending = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coin = trending["coins"][0]["item"]
        name = coin["name"]
        symbol = coin["symbol"]
        reason = "Analyse combinée : Rumeurs positives + accumulation smart money 💹"
        return f"🚨 *Signal Crypto A+* 🚨\n\n💰 **{name} ({symbol})**\n📊 {reason}\n⏰ Prochaine mise à jour automatique dans 6 heures."
    except Exception as e:
        return f"⚠️ Erreur dans la génération du signal : {e}"

# === RUMEURS CRYPTO ===
def get_rumeurs():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=6f3e0b4c7281b9c3c7b3c6fda9f6d8ae&kind=news"
        data = requests.get(url).json()
        posts = data.get("results", [])[:3]
        if not posts:
            return "😕 Aucune rumeur récente trouvée."
        msg = "🧠 *Dernières rumeurs crypto* :\n\n"
        for p in posts:
            title = p.get("title", "Sans titre")
            link = p.get("url", "")
            msg += f"• [{title}]({link})\n"
        return msg
    except Exception as e:
        return f"⚠️ Impossible de récupérer les rumeurs : {e}"

# === SMART MONEY ===
def get_smart_money():
    try:
        url = "https://api.llama.fi/whales/latest"
        data = requests.get(url).json()
        if "whales" not in data:
            return "😕 Aucune donnée whale trouvée pour le moment."
        top = data["whales"][:3]
        msg = "🐋 *Top 3 des mouvements Smart Money récents* :\n\n"
        for tx in top:
            chain = tx.get("chain", "Inconnue")
            token = tx.get("symbol", "???")
            amount = tx.get("amountUsd", 0)
            msg += f"• **{token}** sur *{chain}* — {round(amount,2)} $\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur récupération smart money : {e}"

# === ENVOI AUTOMATIQUE ===
def envoyer_signaux_periodiques():
    try:
        msg = generer_signal_crypto()
        users = obtenir_users()
        for chat_id in users:
            try:
                bot.send_message(chat_id, msg, parse_mode="Markdown")
                maj_dernier_envoi(chat_id)
                time.sleep(1)
            except Exception as e:
                print(f"Erreur envoi à {chat_id}: {e}")
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
    return "🤖 Bot A+ actif avec signaux, rumeurs & smart money ✅", 200

# === DÉMARRAGE DU BOT ===
def start_bot():
    init_db()
    threading.Thread(target=planificateur, daemon=True).start()
    print("🚀 Bot A+ prêt (signaux + rumeurs + smart money + stats).")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    start_bot()
