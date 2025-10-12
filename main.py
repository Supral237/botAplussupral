import os
import telebot
import requests
import schedule
import time
import threading
from flask import Flask, request

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA")
HOSTNAME = os.getenv("botaplussupral-2.onrender.com")
WEBHOOK_URL = f"https://{HOSTNAME}/webhook"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Liste des utilisateurs /start
users = set()

# === FONCTION D'ANALYSE DEXSCREENER ===
def get_crypto_analysis(symbol="BTC"):
    try:
        print(f"[LOG] Récupération de l'analyse pour {symbol}")
        url = f"https://api.dexscreener.com/latest/dex/search/?q={symbol}"
        r = requests.get(url)
        data = r.json()

        if "pairs" not in data or len(data["pairs"]) == 0:
            return f"❌ Aucune donnée trouvée pour {symbol}"

        pair = data["pairs"][0]
        price_usd = float(pair.get("priceUsd", 0))
        volume_24h = float(pair.get("volume", 0))
        price_change = float(pair.get("priceChange", {}).get("h24", 0))

        # Calcul de la note de confiance
        score = 5
        if price_change > 10:
            score += 2
        elif price_change < -10:
            score -= 2
        if volume_24h > 1_000_000:
            score += 2

        score = max(0, min(score, 10))  # borne 0-10
        tendance = "📈 En forte hausse" if price_change > 5 else "📉 En baisse" if price_change < -5 else "➡️ Stable"

        message = (
            f"💎 **Signal crypto automatique**\n\n"
            f"🔹 **Token :** {symbol}\n"
            f"💰 **Prix actuel :** {round(price_usd, 4)} $\n"
            f"📊 **Variation 24h :** {price_change:.2f} %\n"
            f"💵 **Volume (24h) :** {volume_24h:,.0f} $\n"
            f"🧭 **Note de confiance : {score}/10**\n\n"
            f"{tendance}\n"
            f"⏰ Analyse mise à jour automatiquement toutes les 6h."
        )
        return message

    except Exception as e:
        print(f"[ERREUR ANALYSE] {e}")
        return "❌ Erreur lors de l'analyse."

# === ENVOI AUTOMATIQUE ===
def send_auto_signal():
    print("[LOG] Envoi automatique des signaux...")
    cryptos = ["BTC", "ETH", "SOL", "AVAX"]
    for symbol in cryptos:
        msg = get_crypto_analysis(symbol)
        for user in users:
            try:
                bot.send_message(user, msg, parse_mode="Markdown")
                print(f"[OK] Signal envoyé à {user} pour {symbol}")
            except Exception as e:
                print(f"[ERREUR ENVOI] {e}")

# === PLANIFICATION (toutes les 6h) ===
def schedule_jobs():
    schedule.every(6).hours.do(send_auto_signal)
    while True:
        schedule.run_pending()
        time.sleep(60)

# === WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# === COMMANDES TELEGRAM ===
@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.chat.id)
    bot.reply_to(
        message,
        "👋 Salut ! Je t’enverrai automatiquement des signaux crypto toutes les 6h.\n"
        "Tu recevras les analyses des tokens les plus prometteurs avec une note de confiance."
    )

@bot.message_handler(commands=["signal"])
def manual_signal(message):
    bot.reply_to(message, "📡 Génération d’un signal en cours...")
    msg = get_crypto_analysis("BTC")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# === LANCEMENT ===
if __name__ == "__main__":
    print("[LOG] Démarrage du bot A+ Supral avec DexScreener")
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"[OK] Webhook configuré sur {WEBHOOK_URL}")

    threading.Thread(target=schedule_jobs, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
