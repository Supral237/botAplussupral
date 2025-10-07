import os
import requests
import schedule
import time

# Lire les variables d'environnement (depuis Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"⚠️ Erreur Telegram : {response.text}")
    else:
        print("✅ Message envoyé avec succès.")

def job():
    print("⏱️ Exécution de la tâche programmée...")
    send_message("🤖 Le bot A+ est toujours en ligne sur Render !")

if __name__ == "__main__":
    print("🔍 Démarrage du bot A+ (Render)...")
    send_message("🚀 Bot A+ démarré avec succès sur Render !")

    schedule.every(10).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(10)
