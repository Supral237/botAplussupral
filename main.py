from flask import Flask, request
import requests
import os
import random
import threading
import time
import schedule

# --- 🔧 Variables d'environnement ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Ton ID Telegram personnel

app = Flask(__name__)

# --- 🧠 Fonction d'envoi de message Telegram ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("❌ Erreur d'envoi :", e)

# --- 🧠 Analyse des tendances ---
def get_crypto_trend():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        data = requests.get(url).json()
        trending = [coin["item"]["name"] for coin in data["coins"][:5]]
        names = "\n".join([f"• {name}" for name in trending])
        return f"🚀 **Tendances du marché :**\n\n{names}\n\n📊 Ces tokens attirent actuellement beaucoup d’attention."
    except Exception as e:
        return f"⚠️ Impossible d’obtenir les tendances : {e}"

# --- 🧠 Rumeurs et signaux simulés ---
def get_rumors_and_signals():
    rumors = [
        "🐳 Plusieurs portefeuilles ‘smart money’ accumulent du PEPE depuis 48h.",
        "🚨 Rumeur de partenariat entre Coinbase et un projet Layer-2 confidentiel.",
        "📈 Fort intérêt institutionnel observé sur Celestia (TIA).",
        "🧠 Les données on-chain montrent une accumulation rapide de tokens AI.",
        "🔥 Hausse du volume social autour de la crypto ORDI sur X/Twitter."
    ]
    return random.choice(rumors)

# --- 💹 Vérification des pumps ---
def check_for_pumps():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false"
        data = requests.get(url).json()

        for coin in data:
            if coin.get("price_change_percentage_24h", 0) >= 10:
                name = coin["name"]
                price = coin["current_price"]
                change = round(coin["price_change_percentage_24h"], 2)
                alert = f"🚨 *Alerte Pump !*\n\n{name} a augmenté de *{change}%* ces dernières 24h 💥\nPrix actuel : *${price}*\n\n👀 Surveille ce token !"
                send_message(ADMIN_CHAT_ID, alert)
                print(f"⚡ Alerte envoyée pour {name}")
    except Exception as e:
        print("Erreur de détection de pump :", e)

# --- 🧩 Envoi d'analyse complète ---
def send_daily_analysis():
    if not ADMIN_CHAT_ID:
        print("⚠️ Aucun ID admin défini dans les variables d'environnement.")
        return

    trend = get_crypto_trend()
    rumor = get_rumors_and_signals()
    message = f"{trend}\n\n💬 **Rumeur / Signal Smart Money :**\n{rumor}"
    send_message(ADMIN_CHAT_ID, message)
    print("📤 Analyse quotidienne envoyée avec succès.")

# --- 🧩 Planification automatique ---
def scheduler_thread():
    schedule.every().day.at("08:00").do(send_daily_analysis)
    schedule.every(10).minutes.do(check_for_pumps)
    while True:
        schedule.run_pending()
        time.sleep(30)

# --- 🔁 Webhook Telegram ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip().lower()

        if text == "/start":
            send_message(chat_id, "🤖 Salut ! Je suis Bot A+. Envoie /analyse pour obtenir une analyse crypto complète 🧠")

        elif text == "/analyse":
            send_message(chat_id, "⏳ Analyse en cours, collecte des signaux de marché...")
            trend = get_crypto_trend()
            rumor = get_rumors_and_signals()
            message = f"{trend}\n\n💬 **Rumeur / Signal Smart Money :**\n{rumor}"
            send_message(chat_id, message)

        else:
            send_message(chat_id, "❓ Commande inconnue. Utilise /start ou /analyse.")

    return "ok", 200

# --- 🌍 Page d'accueil Render ---
@app.route("/")
def home():
    return "✅ Bot A+ opérationnel avec alertes automatiques."

# --- 🚀 Lancement du bot ---
if __name__ == "__main__":
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")
        print("🔗 Webhook configuré :", res.text)

    threading.Thread(target=scheduler_thread, daemon=True).start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
