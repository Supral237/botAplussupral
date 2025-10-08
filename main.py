import os
import requests
from flask import Flask, request
import schedule
import time
import threading

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN") or "8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") or "https://botaplussupral-2.onrender.com"

app = Flask(__name__)

# --- Envoi de message Telegram ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Erreur envoi message :", e)

# --- Gestion des messages entrants ---
def handle_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return

    print(f"📩 Message reçu : {text}")

    if text.lower() in ["/start", "start"]:
        send_message(chat_id, "👋 Bienvenue sur le bot A+ 🚀\nJe suis prêt à t'aider à atteindre ton objectif 💰")
    elif "bonjour" in text.lower():
        send_message(chat_id, "Salut 👋, comment vas-tu aujourd’hui ?")
    else:
        send_message(chat_id, f"Tu as dit : {text}")

# --- Route principale : webhook ---
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = request.get_json()
        handle_update(update)
        return "OK", 200
    else:
        return "🤖 Bot A+ est en ligne sur Render 🚀", 200

# --- Planificateur de tâches ---
def job():
    print("🕒 Tâche planifiée exécutée (toutes les 10 minutes)")
    # Ici, tu pourras ajouter plus tard la logique crypto / veille / trading

def run_scheduler():
    schedule.every(10).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- Lancement du bot ---
def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    data = {"url": WEBHOOK_URL}
    response = requests.post(url, data=data)
    print("🔗 Configuration du webhook :", response.text)

if __name__ == '__main__':
    print("🔍 Démarrage du bot A+...")
    threading.Thread(target=run_scheduler, daemon=True).start()
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
