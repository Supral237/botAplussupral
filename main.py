from flask import Flask, request
import requests
import os
import schedule
import time
import threading

# === Configuration de base ===
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
URL = "https://botaplussupral.onrender.com"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# === Fonction d'envoi de message Telegram ===
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erreur d'envoi :", e)

# === Configuration automatique du webhook ===
def set_webhook():
    webhook_url = f"{URL}/webhook"
    response = requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    print("Webhook setup:", response.text)

# === Route principale (pour tester Render) ===
@app.route('/')
def home():
    return "🤖 Bot A+ est en ligne sur Render !"

# === Route du webhook (pour recevoir les messages Telegram) ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text.lower() in ["/start", "start"]:
            send_message(chat_id, "✅ Bot A+ connecté avec succès ! Enchanté 😎")
        else:
            send_message(chat_id, f"Message reçu : {text}")
    return "ok"

# === Exemple de tâche planifiée ===
def job():
    print("⏰ Tâche planifiée exécutée...")
    # Tu peux y mettre une tâche automatique ici

# === Thread pour le planificateur ===
def run_schedule():
    schedule.every(10).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Démarre le planificateur en parallèle
    threading.Thread(target=run_schedule, daemon=True).start()

    print("🔍 Démarrage du bot A+...")
    print("✅ Planificateur activé (toutes les 10 minutes)")

    # Configure le webhook à chaque démarrage
    set_webhook()

    # Lance le serveur Flask
    app.run(host="0.0.0.0", port=10000)
