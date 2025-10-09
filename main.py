import os
import requests
from flask import Flask, request
import threading
import time
import logging

# ==============================
# CONFIGURATION DU BOT
# ==============================
TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
WEBHOOK_URL = f"https://botaplussupral-2.onrender.com/{TOKEN}"
ADMIN_CHAT_ID = "7457254381"  # <-- Remplace par ton ID Telegram

# ==============================
# INITIALISATION
# ==============================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ==============================
# ENVOI DE MESSAGE
# ==============================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi du message : {e}")


# ==============================
# ROUTES FLASK
# ==============================
@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot A+ opérationnel ✅", 200


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        logging.info(f"📩 Nouvelle mise à jour : {update}")

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "").lower()

            if text in ["/start", "start"]:
                send_message(chat_id, "👋 Salut ! Je suis Bot A+. Je t’enverrai des signaux crypto 🔥")

            elif "rumeur" in text:
                send_message(chat_id, "🔍 Recherche des dernières rumeurs crypto...")
                rumeurs = get_crypto_rumeurs()
                send_message(chat_id, rumeurs)

            elif "smart" in text:
                send_message(chat_id, "💼 Détection des mouvements de Smart Money...")
                smart = get_smart_money()
                send_message(chat_id, smart)

            elif "news" in text:
                send_message(chat_id, "📰 Analyse des dernières actualités du marché crypto...")
                news = get_crypto_news()
                send_message(chat_id, news)

            else:
                send_message(chat_id, "✅ Commande reçue ! Essaie 'rumeur', 'smart' ou 'news'.")

        return "ok", 200
    except Exception as e:
        logging.error(f"Erreur dans le webhook : {e}")
        return "error", 500


# ==============================
# MODULE RUMEURS (FAUX EXEMPLE)
# ==============================
def get_crypto_rumeurs():
    try:
        # Ici tu pourras remplacer par un appel API réel
        rumeurs = [
            "🚀 Rumeur : Binance préparerait une intégration avec TON Network.",
            "💎 Rumeur : Coinbase envisagerait de lister un nouveau projet basé sur Solana.",
        ]
        return "\n\n".join(rumeurs)
    except Exception as e:
        return f"Erreur lors de la récupération des rumeurs : {e}"


# ==============================
# MODULE SMART MONEY (FAUX EXEMPLE)
# ==============================
def get_smart_money():
    try:
        smart = [
            "💼 Une baleine a acheté 1.2M $ de $LINK sur Binance.",
            "🧠 Portefeuille 0xABC vient d'accumuler massivement du $PYTH avant une annonce.",
        ]
        return "\n\n".join(smart)
    except Exception as e:
        return f"Erreur lors de la récupération des données Smart Money : {e}"


# ==============================
# MODULE NEWS (FAUX EXEMPLE)
# ==============================
def get_crypto_news():
    try:
        news = [
            "📰 Bitcoin franchit 72 000 $ pour la première fois depuis avril.",
            "🔥 Ethereum annonce une nouvelle mise à jour centrée sur la scalabilité.",
        ]
        return "\n\n".join(news)
    except Exception as e:
        return f"Erreur lors de la récupération des actualités : {e}"


# ==============================
# FONCTION AUTOMATIQUE (veille horaire)
# ==============================
def veille_automatique():
    while True:
        try:
            logging.info("⏰ Lancement de la veille automatique...")
            rumeurs = get_crypto_rumeurs()
            smart = get_smart_money()

            message = f"🕓 **Veille automatique crypto (toutes les heures)**\n\n{rumeurs}\n\n{smart}"
            send_message(ADMIN_CHAT_ID, message)
        except Exception as e:
            logging.error(f"Erreur dans la veille automatique : {e}")
        time.sleep(3600)  # toutes les heures


# ==============================
# CONFIGURATION DU WEBHOOK
# ==============================
def setup_webhook():
    logging.info("🔗 Configuration du Webhook...")
    delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"

    requests.get(delete_url)
    response = requests.get(set_url)
    logging.info(f"Résultat du webhook : {response.text}")

    if ADMIN_CHAT_ID != "XXXX":
        send_message(ADMIN_CHAT_ID, "🚀 Bot A+ prêt et webhook configuré avec succès !")


# ==============================
# DÉMARRAGE DU BOT
# ==============================
if __name__ == "__main__":
    setup_webhook()

    # Démarrer le thread de veille automatique
    if ADMIN_CHAT_ID != "XXXX":
        threading.Thread(target=veille_automatique, daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
