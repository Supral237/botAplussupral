from flask import Flask, request
import requests
import json
import schedule
import time
import threading

# --- CONFIG ---
BOT_TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
ADMIN_ID = "7457254381"  # ton ID Telegram pour recevoir les alertes perso

app = Flask(__name__)

# --- UTILITAIRES ---
def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_crypto_trending():
    """Exemple de fonction de détection de tendances crypto (via API publique)."""
    try:
        data = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coins = data.get("coins", [])
        top = []
        for c in coins[:5]:
            coin = c["item"]
            top.append(f"🚀 <b>{coin['name']}</b> ({coin['symbol']})\n🔗 https://www.coingecko.com/en/coins/{coin['id']}")
        return "\n\n".join(top)
    except Exception as e:
        return f"Erreur API : {e}"

def detect_smart_money():
    """Simulation d’analyse onchain (simplifiée pour l’exemple)."""
    # En version avancée : tu peux brancher une vraie API (comme Nansen, Arkham, etc.)
    wallets = ["0x1234...", "0xABCD...", "0x9999..."]
    coin = "ZKSync (ZK)"
    reason = "Accumulation par plusieurs portefeuilles smart money cette semaine 🔥"
    return f"💼 <b>Smart Money Alert</b>\nCrypto : {coin}\nRaison : {reason}\nPortefeuilles : {', '.join(wallets)}"

def crypto_news_summary():
    """Résumé d'actualités crypto (simplifié pour démo)."""
    try:
        res = requests.get("https://cryptopanic.com/api/v1/posts/?auth_token=demo&filter=rising")
        data = res.json().get("results", [])
        news = []
        for n in data[:3]:
            news.append(f"📰 <b>{n['title']}</b>\n🔗 {n['url']}")
        return "\n\n".join(news)
    except:
        return "Impossible de charger les actualités."

# --- LOGIQUE DU BOT ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "ok", 200

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "").lower()

    if text in ["/start", "start"]:
        send_message(chat_id, "👋 Bienvenue ! Je t’enverrai bientôt des signaux crypto 🔥")
    elif "rumeur" in text or "signal" in text:
        send_message(chat_id, f"📈 Voici les cryptos en tendance :\n\n{get_crypto_trending()}")
    elif "smart" in text:
        send_message(chat_id, detect_smart_money())
    elif "news" in text or "actu" in text:
        send_message(chat_id, crypto_news_summary())
    else:
        send_message(chat_id, "🤖 Commandes disponibles :\n- rumeurs / signal\n- smart\n- news / actu")

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot crypto en ligne 🚀", 200

# --- AUTOMATISATION ---
def job_auto_send():
    """Tâche planifiée qui envoie automatiquement des infos au créateur."""
    trending = get_crypto_trending()
    smart = detect_smart_money()
    send_message(ADMIN_ID, f"🔔 <b>Veille quotidienne</b>\n\n{trending}\n\n{smart}")

def run_schedule():
    schedule.every(6).hours.do(job_auto_send)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=10000)
