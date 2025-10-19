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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA")
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

# === COMMANDES DE BASE ===
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

@bot.message_handler(commands=['statistiques'])
def statistiques(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE last_sent >= datetime('now', '-6 hours')")
    recents = c.fetchone()[0]
    conn.close()
    msg = (
        f"📊 *Statistiques du Bot A+* :\n\n"
        f"👥 Total d’utilisateurs : {total}\n"
        f"📬 Utilisateurs actifs (6h) : {recents}\n\n"
        f"⏰ Prochain envoi automatique dans 6 heures."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# === SIGNALS AVEC NOTE ===
def generer_signal_crypto(alerte=False):
    try:
        data = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coins = data.get("coins", [])
        if not coins:
            return None

        signaux = []
        alertes = []

        for c in coins:
            item = c["item"]
            coin_id = item["id"]
            name = item["name"]
            symbol = item["symbol"]

            m = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}").json()
            md = m.get("market_data", {})
            price = md.get("current_price", {}).get("usd", 0)
            change = md.get("price_change_percentage_24h", 0)
            vol = md.get("total_volume", {}).get("usd", 0)
            cap = md.get("market_cap", {}).get("usd", 0)

            # Calcul de la note
            note = 0
            if change > 0: note += 2
            if 3 <= change <= 15: note += 2
            if vol > 1_000_000: note += 2
            if cap > 10_000_000: note += 2
            if vol / max(cap, 1) > 0.1: note += 2
            note = round(min(note, 10), 1)

            analyse = ""
            if note >= 8.5:
                if change > 10:
                    analyse = "🚀 Forte dynamique haussière, attention au FOMO."
                elif 3 <= change <= 10:
                    analyse = "📈 Montée régulière soutenue par le volume."
                else:
                    analyse = "🧠 Mouvement calme mais accumulation détectée."

                signaux.append({
                    "name": name,
                    "symbol": symbol,
                    "price": price,
                    "change": change,
                    "note": note,
                    "analyse": analyse
                })

            # Alerte spéciale
            if note >= 9.5:
                alertes.append(f"🔔 *ALERTE ULTRA SIGNAL !*\n💰 **{name} ({symbol})**\n"
                               f"Prix: ${price}\nVariation 24h: {change}%\n"
                               f"Note: *{note}/10*\n{analyse}")

        if alerte:
            return alertes if alertes else None

        if not signaux:
            return "⚠️ Aucune crypto avec une note > 8.5 détectée pour l’instant."

        msg = "🚨 *Signaux Crypto A+ (note > 8.5)* 🚨\n\n"
        for s in signaux:
            msg += (f"💰 **{s['name']} ({s['symbol']})**\n"
                    f"💵 Prix : ${s['price']}\n"
                    f"📈 Variation 24h : {s['change']}%\n"
                    f"🧠 Note : *{s['note']} / 10*\n"
                    f"{s['analyse']}\n—\n")

        msg += "\n⏰ Prochaine mise à jour dans 6h."
        return msg

    except Exception as e:
        return f"⚠️ Erreur dans la génération du signal : {e}"

# === RUMEURS & SMART MONEY ===
def get_rumeurs():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=6f3e0b4c7281b9c3c7b3c6fda9f6d8ae&kind=news"
        data = requests.get(url).json()
        posts = data.get("results", [])[:3]
        if not posts:
            return "😕 Aucune rumeur récente trouvée."
        msg = "🧠 *Dernières rumeurs crypto* :\n\n"
        for p in posts:
            msg += f"• [{p.get('title','Sans titre')}]({p.get('url','')})\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur rumeurs : {e}"

def get_smart_money():
    try:
        url = "https://api.llama.fi/whales/latest"
        data = requests.get(url).json()
        if "whales" not in data:
            return "😕 Aucune donnée whale trouvée."
        msg = "🐋 *Top mouvements Smart Money récents* :\n\n"
        for tx in data["whales"][:3]:
            msg += f"• **{tx.get('symbol','???')}** sur *{tx.get('chain','Inconnue')}* — {round(tx.get('amountUsd',0),2)} $\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur smart money : {e}"

# === COMMANDES ===
@bot.message_handler(commands=['signal'])
def signal(message):
    bot.reply_to(message, "📡 Analyse combinée en cours...")
    msg = generer_signal_crypto()
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    maj_dernier_envoi(message.chat.id)

@bot.message_handler(commands=['dernierrumeur'])
def derniere_rumeur(message):
    bot.send_message(message.chat.id, get_rumeurs(), parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['smartmoney'])
def smartmoney(message):
    bot.send_message(message.chat.id, get_smart_money(), parse_mode="Markdown", disable_web_page_preview=True)

# === ENVOIS AUTOMATIQUES ===
def envoyer_signaux_periodiques():
    msg = generer_signal_crypto()
    users = obtenir_users()
    for chat_id in users:
        try:
            bot.send_message(chat_id, msg, parse_mode="Markdown")
            maj_dernier_envoi(chat_id)
            time.sleep(1)
        except Exception as e:
            print(f"Erreur envoi {chat_id}: {e}")

# === ALERTE TEMPS RÉEL (toutes les 30 min) ===
def surveiller_alertes():
    while True:
        try:
            alertes = generer_signal_crypto(alerte=True)
            if alertes:
                for a in alertes:
                    for user_id in obtenir_users():
                        bot.send_message(user_id, a, parse_mode="Markdown")
                        time.sleep(1)
        except Exception as e:
            print(f"Erreur alerte : {e}")
        time.sleep(1800)  # vérifie toutes les 30 min

# === PLANIFICATEUR ===
def planificateur():
    schedule.every(6).hours.do(envoyer_signaux_periodiques)
    while True:
        schedule.run_pending()
        time.sleep(30)

# === FLASK / WEBHOOK ===
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('UTF-8'))
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def index():
    return "🤖 Bot A+ prêt avec alertes instantanées ✅", 200

# === LANCEMENT ===
def start_bot():
    init_db()
    threading.Thread(target=planificateur, daemon=True).start()
    threading.Thread(target=surveiller_alertes, daemon=True).start()
    print("🚀 Bot A+ prêt (signaux + rumeurs + smart money + alertes temps réel).")
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    start_bot()