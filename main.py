import os
import requests
from flask import Flask, request

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

app = Flask(__name__)

# --- FONCTIONS UTILITAIRES ---

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ Erreur Telegram : {e}")


def get_crypto_signal():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        data = requests.get(url).json()
        coins = data.get("coins", [])
        if not coins:
            return "😕 Aucun signal fort détecté pour le moment."
        msg = "🚀 <b>Signaux Crypto (Top tendances Coingecko)</b>\n\n"
        for c in coins:
            item = c["item"]
            msg += f"• {item['name']} ({item['symbol'].upper()}) — Rang {item['market_cap_rank']}\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur API Coingecko : {e}"


def get_twitter_rumors():
    try:
        if not TWITTER_BEARER_TOKEN:
            return "⚠️ Clé Twitter API manquante."

        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        query = "(crypto OR partnership OR listing OR launch OR rumor) (binance OR coinbase OR okx OR solana OR ethereum OR base OR layerzero) lang:en -is:retweet"
        url = f"https://api.x.com/2/tweets/search/recent?query={query}&max_results=5&tweet.fields=created_at,author_id,text"

        response = requests.get(url, headers=headers).json()
        tweets = response.get("data", [])

        if not tweets:
            return "😶 Aucune rumeur récente détectée sur Twitter."

        msg = "🐦 <b>Rumeurs Twitter détectées :</b>\n\n"
        for t in tweets:
            text = t['text'][:250].replace("\n", " ")
            msg += f"🕒 {t['created_at']}\n{text}\n\n"
        return msg
    except Exception as e:
        return f"⚠️ Erreur Twitter API : {e}"

# --- ROUTE DYNAMIQUE POUR WEBHOOK ---

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot A+ en ligne et opérationnel !"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").lower()

        if text == "/start":
            send_message(chat_id, "👋 Salut ! Je suis ton bot A+. Tape 'signal' pour les tendances ou 'twitter' pour les rumeurs crypto.")
        elif "signal" in text:
            send_message(chat_id, get_crypto_signal())
        elif "twitter" in text or "x" in text:
            send_message(chat_id, get_twitter_rumors())
        else:
            send_message(chat_id, "🤖 Commande inconnue. Essaye 'signal' ou 'twitter'.")

    return {"ok": True}

# --- DÉMARRAGE DU WEBHOOK ---

if __name__ == "__main__":
    webhook_url = f"https://botaplussupral-2.onrender.com/webhook"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    response = requests.get(url, params={"url": webhook_url})
    print("🔗 Configuration du Webhook :", response.text)

    print("🚀 Bot A+ démarré avec succès sur Render !")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
