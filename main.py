import os
import telebot
from flask import Flask, request
import requests
import random

# === CONFIGURATION ===
TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"  # <-- Remplace ici par ton token Telegram
BASE_URL = "https://botaplussupral.onrender.com"  # <-- adapte si ton URL Render est différente
WEBHOOK_URL = f"{BASE_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === ROUTE PRINCIPALE ===
@app.route('/')
def index():
    return "🚀 Bot A+ est en ligne et opérationnel !", 200

# === WEBHOOK TELEGRAM ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
    except Exception as e:
        print("❌ Erreur webhook:", e)
    return "OK", 200

# === COMMANDES DE BASE ===
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 Bienvenue sur le bot A+ !\n\n"
        "Voici les commandes disponibles :\n"
        "📡 /rumeurs → Suivre les rumeurs crypto du moment\n"
        "📰 /news → Actualités et annonces importantes\n"
        "💼 /smart → Analyse des portefeuilles Smart Money\n"
        "📈 /signal → Obtenir un signal crypto potentiel\n\n"
        "Je travaille 24h/24 pour détecter les meilleures opportunités 💪"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "Utilise /rumeurs, /news, /smart ou /signal pour obtenir des infos crypto.")

# === FONCTIONNALITÉ : RUMEURS CRYPTO ===
@bot.message_handler(commands=['rumeurs'])
def rumeurs(message):
    bot.reply_to(message, "🔍 Recherche des rumeurs crypto en cours...")
    try:
        data = [
            "🚀 Rumeur : Binance pourrait lister $ZRO bientôt.",
            "💥 Des discussions entre Ripple et Amazon refont surface.",
            "🔥 Des insiders parlent d’un partenariat entre Avalanche et Google Cloud."
        ]
        result = "\n\n".join(data)
        bot.send_message(message.chat.id, f"📡 Rumeurs du marché :\n\n{result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Erreur lors de l'analyse des rumeurs : {e}")

# === FONCTIONNALITÉ : ACTUALITÉS ===
@bot.message_handler(commands=['news'])
def news(message):
    bot.reply_to(message, "📰 Analyse des dernières actualités crypto...")
    try:
        news_list = [
            "🔔 Bitcoin franchit les 70 000 $ suite à une annonce de la SEC.",
            "💼 BlackRock ajoute un ETF Ethereum à sa plateforme.",
            "🌍 L’Union Européenne valide une régulation favorable aux stablecoins."
        ]
        bot.send_message(message.chat.id, "\n\n".join(news_list))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Erreur lors de la récupération des actualités : {e}")

# === FONCTIONNALITÉ : SMART MONEY ===
@bot.message_handler(commands=['smart'])
def smart(message):
    bot.reply_to(message, "💼 Analyse des portefeuilles smart money...")
    try:
        smart_data = [
            "🐋 Portefeuille 0xabc... a accumulé massivement du $SOL avant le pump.",
            "💰 Smart wallet 0xdef... a acheté 250 000 $ de $INJ hier.",
            "⚡ Adresse 0xghi... accumule du $TAO depuis 3 jours."
        ]
        bot.send_message(message.chat.id, "📊 Smart Money :\n\n" + "\n\n".join(smart_data))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Erreur dans l'analyse on-chain : {e}")

# === NOUVELLE FONCTIONNALITÉ : SIGNALS CRYPTO ===
@bot.message_handler(commands=['signal'])
def signal(message):
    bot.reply_to(message, "📈 Analyse du marché en cours...")
    try:
        # Exemples de signaux
        signaux = [
            {
                "token": "SOL",
                "raison": "Hausse du volume de 120% et accumulation par des whales",
                "cible": "Target : +15% dans 48h",
                "confiance": "🟢 Confiance : Élevée"
            },
            {
                "token": "INJ",
                "raison": "Annonce prochaine de partenariat avec Binance Labs (rumeur forte)",
                "cible": "Target : +20% dans 3 jours",
                "confiance": "🟠 Confiance : Moyenne"
            },
            {
                "token": "TAO",
                "raison": "Smart money en accumulation constante depuis 5 jours",
                "cible": "Target : +25% sous 72h",
                "confiance": "🟢 Confiance : Forte"
            },
            {
                "token": "ZRO",
                "raison": "Hausse soudaine du volume + rumeurs de listing Binance",
                "cible": "Target : +30% rapide",
                "confiance": "🟡 Confiance : Modérée"
            }
        ]
        signal_choisi = random.choice(signaux)
        msg = (
            f"🚀 **Signal détecté !**\n\n"
            f"💎 Token : ${signal_choisi['token']}\n"
            f"📊 Raison : {signal_choisi['raison']}\n"
            f"🎯 {signal_choisi['cible']}\n"
            f"{signal_choisi['confiance']}\n\n"
            f"⚠️ Ce signal est indicatif, fais toujours ta propre analyse."
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Erreur lors de la génération du signal : {e}")

# === CONFIGURATION AUTOMATIQUE DU WEBHOOK ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    try:
        print("🧹 Suppression de tout ancien webhook...")
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

        print(f"🔗 Configuration du nouveau webhook sur {WEBHOOK_URL} ...")
        set_hook = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
        print("📬 Réponse de Telegram :", set_hook.json())
    except Exception as e:
        print("⚠️ Erreur pendant la configuration du webhook:", e)

    print(f"🚀 Bot A+ prêt et en écoute sur le port {port}")
    app.run(host="0.0.0.0", port=port)
