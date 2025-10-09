import os
import requests
import schedule
import time
from flask import Flask, request

# === CONFIGURATION ===
TOKEN = os.getenv("TELEGRAM_TOKEN", "TON_TOKEN_TELEGRAM_ICI")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "TON_CHAT_ID_ICI")
X_BEARER = os.getenv("X_BEARER_TOKEN", "TON_BEARER_TOKEN_X_ICI")

app = Flask(__name__)

# === ENVOI MESSAGE TELEGRAM ===
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur d’envoi Telegram : {e}")

# === MODULE NEWS ===
def get_crypto_news():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?kind=news&filter=rising"
        response = requests.get(url)
        data = response.json().get("results", [])
        news = [f"📰 {n['title']}" for n in data[:3]]
        return "\n\n".join(news) if news else "Aucune actualité trouvée pour le moment."
    except Exception as e:
        return f"Erreur lors de la récupération des actualités : {e}"

# === MODULE RUMEURS ===
def get_crypto_rumors():
    try:
        headers = {"Authorization": f"Bearer {X_BEARER}"}
        query = "crypto OR bitcoin OR altcoin OR partnership OR listing lang:fr"
        url = f"https://api.x.com/2/tweets/search/recent?query={query}&max_results=5"
        resp = requests.get(url, headers=headers)
        tweets = resp.json().get("data", [])
        rumors = [f"💬 {t['text']}" for t in tweets]
        return "\n\n".join(rumors) if rumors else "Aucune rumeur détectée récemment."
    except Exception as e:
        return f"Erreur lors de l’analyse des rumeurs : {e}"

# === MODULE SMART MONEY ===
def get_smart_money_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc"
        response = requests.get(url)
        coins = response.json()
        picks = coins[:3]
        msg = "\n".join([f"💰 {c['name']} ({c['symbol'].upper()}) - ${c['current_price']}" for c in picks])
        return f"Voici les tokens les plus accumulés par les whales 👇\n\n{msg}"
    except Exception as e:
        return f"Erreur lors de la récupération des données smart money : {e}"

# === MODULE SIGNAL AUTOMATIQUE ===
def get_crypto_signal():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        data = requests.get(url).json()
        coin = data['coins'][0]['item']
        return f"🚀 Signal du moment : {coin['name']} ({coin['symbol'].upper()})\nRang : {coin['market_cap_rank']}\nTendance forte détectée 🔥"
    except Exception as e:
        return f"Erreur lors de la génération du signal : {e}"

# === RECEPTION WEBHOOK ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "").lower()

        if "/start" in text:
            send_message(chat_id, "👋 Bienvenue sur Bot A+ !\nJe t’enverrai des signaux crypto 🔥")
        elif "/news" in text:
            send_message(chat_id, get_crypto_news())
        elif "/rumors" in text:
            send_message(chat_id, get_crypto_rumors())
        elif "/smart" in text:
            send_message(chat_id, get_smart_money_data())
        elif "/signal" in text:
            send_message(chat_id, get_crypto_signal())
        else:
            send_message(chat_id, "Commande inconnue. Essaie /news, /rumors, /smart ou /signal.")

    return {"ok": True}

@app.route("/")
def home():
    return "Bot A+ opérationnel ✅"

# === TÂCHE PLANIFIÉE AUTOMATIQUE ===
def auto_signal():
    msg = get_crypto_signal()
    send_message(CHAT_ID, msg)
    print("Signal automatique envoyé ✅")

schedule.every(6).hours.do(auto_signal)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # CONFIGURATION WEBHOOK
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'botaplussupral-2.onrender.com')}/{TOKEN}"
    r = requests.get(url, params={"url": webhook_url})
    print("🔗 Webhook configuré :", r.text)

    send_message(CHAT_ID, "🚀 Bot A+ redémarré avec succès sur Render !")
    from threading import Thread
    Thread(target=run_scheduler).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
