import os
import requests
from flask import Flask, request
import logging

# ==============================
# CONFIGURATION DU BOT
# ==============================
TOKEN = "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
WEBHOOK_URL = f"https://botaplussupral-2.onrender.com/{TOKEN}"
ADMIN_CHAT_ID = "XXXX"  # <-- Mets ici ton ID Telegram (pour les notifications d’état)

# ==============================
# INITIALISATION
# ==============================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ==============================
# ROUTE PRINCIPALE
# ==============================
@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot A+ opérationnel ✅", 200


# ==============================
# ROUTE DU WEBHOOK
# ==============================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        logging.info(f"📩 Nouvelle mise à jour reçue : {update}")

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")

            if text.lower() == "/start" or text.lower() == "start":
                send_message(chat_id, "👋 Salut ! Je suis Bot A+. Je t’enverrai des signaux crypto 🔥")
            elif "rumeur" in text.lower():
                send_message(chat_id, "🔍 Recherche des dernières rumeurs crypto... (bientôt disponible)")
            elif "news" in text.lower():
                send_message(chat_id, "📰 Analyse des dernières actualités du marché... (bientôt disponible)")
            elif "smart" in text.lower():
                send_message(chat_id, "💼 Détection des mouvements de Smart Money... (bientôt disponible)")
            else:
                send_message(chat_id, "✅ Message reçu ! Tape 'rumeur', 'news' ou 'smart' pour tester mes fonctions.")
        return "ok", 200

    except Exception as e:
        logging.error(f"Erreur dans le webhook : {e}")
        return "error", 500


# ==============================
# ENVOI DE MESSAGE
# ==============================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


# ==============================
# CONFIGURATION AUTOMATIQUE DU WEBHOOK
# ==============================
def setup_webhook():
    logging.info("🔗 Configuration du Webhook...")
    delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"

    # Supprimer l’ancien Webhook
    requests.get(delete_url)
    # Ajouter le nouveau
    response = requests.get(set_url)
    logging.info(f"Résultat du webhook : {response.text}")

    # Notification à l’admin (si défini)
    if ADMIN_CHAT_ID != "XXXX":
        send_message(ADMIN_CHAT_ID, "🚀 Bot A+ redémarré et webhook configuré avec succès !")


# ==============================
# DÉMARRAGE DU BOT
# ==============================
if __name__ == "__main__":
    setup_webhook()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
