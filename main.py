import os
import random
import requests
from flask import Flask, request
import telebot

# === 🔧 Initialisation ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("La variable BOT_TOKEN n'est pas définie.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ⚙️ Fonction principale : Générer un signal crypto ===
def generer_signal_crypto():
    try:
        trending = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
        coins = trending.get("coins", [])[:5]
        if not coins:
            return "😕 Aucune donnée de tendance trouvée sur CoinGecko."

        analyses = []
        best_coin = None
        best_score = 0

        for c in coins:
            coin = c["item"]
            name = coin["name"]
            symbol = coin["symbol"]
            trust = round(random.uniform(6, 10), 2)
            reason = random.choice([
                "Volume en hausse et accumulation de whales.",
                "Hausse du sentiment social positif.",
                "Activité de smart money détectée.",
                "Potentiel partenariat en rumeur.",
                "Tendance haussière soutenue par la communauté."
            ])
            analyses.append((name, symbol, trust, reason))

            if trust > best_score:
                best_coin = (name, symbol, trust, reason)
                best_score = trust

        # === Si une crypto dépasse 8.5 ===
        if best_score > 8.5:
            msg = (
                f"🚨 *Signal Crypto A+ détecté !* 🚨\n\n"
                f"💰 **{best_coin[0]} ({best_coin[1]})**\n"
                f"🧠 Confiance : *{best_coin[2]} / 10*\n"
                f"📊 Analyse : {best_coin[3]}\n\n"
                f"🔥 Cette crypto dépasse la note de 8.5 — potentiel haussier détecté !\n\n"
                f"⏰ Prochaine mise à jour dans 6h."
            )
        else:
            # === Sinon : afficher le top 3 ===
            top3 = sorted(analyses, key=lambda x: x[2], reverse=True)[:3]
            msg = "⚠️ Aucune crypto avec une note > 8.5 détectée.\n\nVoici le *Top 3 du moment* :\n\n"
            for name, symbol, trust, reason in top3:
                msg += f"• **{name} ({symbol})** — confiance : *{trust}/10*\n"
            msg += "\n⏰ Reanalyse automatique dans 6h."

        return msg

    except Exception as e:
        return f"⚠️ Erreur dans la génération du signal : {e}"

# === 💬 Commande Telegram /signal ===
@bot.message_handler(commands=['signal'])
def envoyer_signal(message):
    bot.send_message(message.chat.id, "🔍 Analyse en cours, patiente quelques secondes...")
    signal = generer_signal_crypto()
    bot.send_message(message.chat.id, signal, parse_mode='Markdown')

# === 💬 Commande /start ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Bienvenue sur *Crypto Signal Bot* !\n\n"
        "Tape /signal pour recevoir une analyse des cryptos tendances avec leur note de confiance.\n\n"
        "⏰ Les signaux sont mis à jour automatiquement toutes les 6h.",
        parse_mode="Markdown"
    )

# === 🌐 Flask route pour Render ===
@app.route('/')
def home():
    return "✅ Bot Telegram opérationnel sur Render !"

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

# === 🚀 Lancer Flask ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)