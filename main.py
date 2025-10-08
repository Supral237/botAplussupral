from flask import Flask, request
import requests
import json
import schedule
import time
import threading

# --- CONFIG ---
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
ADMIN_ID = "7457254381"  # ton chat ID

app = Flask(__name__)

# --- OUTILS ---
def send_message(chat_id, text):
    """Envoi d’un message Telegram"""
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# --- MODULE RUMEURS & VEILLE ---
def get_trending_coins():
    """Top cryptos en tendance sur CoinGecko"""
    try:
        data = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coins = data.get("coins", [])
        msg = "🚀 <b>Top cryptos en tendance :</b>\n\n"
        for c in coins[:5]:
            coin = c["item"]
            msg += f"• <b>{coin['name']}</b> ({coin['symbol']})\n🔗 https://www.coingecko.com/en/coins/{coin['id']}\n\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur CoinGecko : {e}"

def get_hot_news():
    """Rumeurs / annonces montantes via CryptoPanic"""
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&filter=rising"
        data = requests.get(url).json().get("results", [])
        news = []
        for n in data[:3]:
            news.append(f"📰 <b>{n['title']}</b>\n🔗 {n['url']}")
        return "🔥 <b>Rumeurs & Actualités brûlantes :</b>\n\n" + "\n\n".join(news)
    except:
        return "⚠️ Impossible de charger les rumeurs CryptoPanic."

def get_upcoming_events():
    """Événements à venir sur CoinMarketCal"""
    try:
        url = "https://developers.coinmarketcal.com/v1/events"
        headers = {"x-api-key": "DEMO_KEY"}  # tu pourras mettre ta clé plus tard
        data = requests.get(url, headers=headers).json()
        events = data.get("body", [])
        msg = "📅 <b>Événements à venir :</b>\n\n"
        for e in events[:3]:
            msg += f"• {e['title']} ({e['coin']['symbol']})\n🗓️ {e['date_event']}\n🔗 {e['source']}\n\n"
        return msg
    except:
        return "⚠️ Erreur CoinMarketCal."

def smart_money_alert():
    """Exemple d'alerte Smart Money"""
    coin = "ZKSync (ZK)"
    reason = "Accumulation détectée sur plusieurs portefeuilles smart money 🧠"
    return f"💼 <b>Smart Money Alert</b>\nCrypto : {coin}\nRaison : {reason}"

# --- BOT COMMANDES ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "ok", 200

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "").lower()

    if text in ["/start", "start"]:
        send_message(chat_id, "👋 Bienvenue ! Je t’enverrai des <b>signaux et rumeurs crypto</b> en temps réel 🔥")
    elif "rumeur" in text or "signal" in text:
        send_message(chat_id, get_hot_news())
    elif "smart" in text:
        send_message(chat_id, smart_money_alert())
    elif "event" in text or "cal" in text:
        send_message(chat_id, get_upcoming_events())
    elif "tendance" in text or "trend" in text:
        send_message(chat_id, get_trending_coins())
    else:
        send_message(chat_id, "🤖 Commandes disponibles :\n- rumeur / signal\n- tendance / trend\n- smart\n- event / cal")

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot crypto actif 🚀", 200

# --- AUTOMATISATION ---
def auto_veille():
    """Routine automatique d’envoi de rumeurs + tendances"""
    rumors = get_hot_news()
    trends = get_trending_coins()
    send_message(ADMIN_ID, f"📡 <b>Veille Auto</b>\n\n{rumors}\n\n{trends}")

def run_schedule():
    schedule.every(3).hours.do(auto_veille)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=10000)
