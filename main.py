import telebot
from telebot import types
from flask import Flask, request
import requests
import threading
import time
import schedule
import os
import sqlite3
import json

# === CONFIGURATION DU BOT ===
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
WEBHOOK_URL = "https://botaplussupral-2.onrender.com/" + BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DB_PATH = "users.db"
PERF_REAL_FILE = "performances_reelles.json"

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

# === OUTILS SUPPLÉMENTAIRES ===
def recuperer_prix_actuel(crypto):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto.lower()}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data[crypto.lower()]["usd"]
    except Exception as e:
        print(f"Erreur récupération prix {crypto} : {e}")
        return None

def enregistrer_signal(crypto, prix_depart):
    data = []
    if os.path.exists(PERF_REAL_FILE):
        try:
            data = json.load(open(PERF_REAL_FILE))
        except:
            pass
    data.append({
        "crypto": crypto,
        "prix_depart": prix_depart,
        "timestamp": time.time(),
        "verifie": False
    })
    with open(PERF_REAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def verifier_performances_reelles():
    if not os.path.exists(PERF_REAL_FILE):
        return
    try:
        data = json.load(open(PERF_REAL_FILE))
    except:
        data = []
    maintenant = time.time()
    nouvelle_data = []
    for signal in data:
        if signal.get("verifie"):
            nouvelle_data.append(signal)
            continue
        if maintenant - signal["timestamp"] >= 24 * 3600:
            prix_actuel = recuperer_prix_actuel(signal["crypto"])
            if prix_actuel:
                variation = ((prix_actuel - signal["prix_depart"]) / signal["prix_depart"]) * 100
                signal["variation_24h"] = round(variation, 2)
                signal["verifie"] = True
                envoyer_message_tous_utilisateurs(
                    f"📈 *Mise à jour 24h :* {signal['crypto']} a varié de {signal['variation_24h']}% depuis le dernier signal."
                )
        nouvelle_data.append(signal)
    with open(PERF_REAL_FILE, "w") as f:
        json.dump(nouvelle_data, f, indent=2)

def envoyer_message_tous_utilisateurs(msg):
    users = obtenir_users()
    for chat_id in users:
        try:
            bot.send_message(chat_id, msg, parse_mode="Markdown")
            maj_dernier_envoi(chat_id)
            time.sleep(1)
        except Exception as e:
            print(f"Erreur envoi à {chat_id}: {e}")

# === COMMANDES BOT ===
@bot.message_handler(commands=['start'])
def start(message):
    ajouter_user(message.chat.id)
    bot.reply_to(message, (
        "👋 Salut ! Je t’enverrai automatiquement des *signaux crypto* toutes les 6 heures 📊.\n\n"
        "📈 Tape /signal pour un signal instantané.\n"
        "🧠 Tape /dernierrumeur pour connaître les dernières rumeurs crypto.\n"
        "🐋 Tape /smartmoney pour voir où investissent les whales.\n"
        "📊 Tape /statistiques pour voir les stats du bot."
    ), parse_mode="Markdown")

@bot.message_handler(commands=['signal'])
def signal(message):
    bot.reply_to(message, "📡 Analyse combinée en cours...")
    try:
        msg = generer_signal_crypto()
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        maj_dernier_envoi(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant l’analyse : {e}")

@bot.message_handler(commands=['statistiques'])
def statistiques(message):
    total = compter_users()
    recents = compter_users_recents()
    msg = (
        f"📊 *Statistiques du Bot A+* :\n\n"
        f"👥 Total d’utilisateurs : {total}\n"
        f"📬 Utilisateurs actifs (6 dernières heures) : {recents}\n"
        f"⏰ Prochain envoi automatique dans 6 heures."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['dernierrumeur'])
def derniere_rumeur(message):
    bot.send_message(message.chat.id, "🕵️ Recherche des dernières rumeurs crypto...")
    try:
        rumeurs = get_rumeurs()
        bot.send_message(message.chat.id, rumeurs, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant la récupération des rumeurs : {e}")

@bot.message_handler(commands=['smartmoney'])
def smartmoney(message):
    bot.send_message(message.chat.id, "🐋 Analyse des portefeuilles whales en cours...")
    try:
        data = get_smart_money()
        bot.send_message(message.chat.id, data, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erreur pendant la récupération : {e}")

# === SOURCES DE DONNÉ
