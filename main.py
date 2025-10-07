import requests
import schedule
import time
import json
import os

def load_config():
    """Charge les paramètres depuis config.json"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Erreur de chargement du fichier config.json : {e}")
        return None


def send_telegram_message(token, chat_id, message):
    """Envoie un message Telegram via l’API Bot"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)

    if response.status_code != 200:
        print(f"⚠️ Erreur Telegram : {response.text}")
    else:
        print("✅ Message envoyé avec succès.")


def job():
    """Tâche principale exécutée à chaque intervalle"""
    config = load_config()
    if not config:
        print("⚠️ Impossible de charger la configuration.")
        return

    token = config.get("telegram_token")
    chat_id = config.get("chat_id")

    # Exemple : message d’état
    message = "🤖 Bot A+ : tout fonctionne correctement ! ✅"
    send_telegram_message(token, chat_id, message)


if __name__ == "__main__":
    print("🔍 Démarrage du bot A+...")

    config = load_config()
    if not config:
        print("⚠️ Impossible de continuer sans config.json.")
        exit(1)

    token = config.get("telegram_token")
    chat_id = config.get("chat_id")

    # Envoi d’un message de démarrage
    send_telegram_message(token, chat_id, "🚀 Bot A+ démarré avec succès sur Render !")

    # Planifie l’envoi d’un message toutes les 10 minutes
    schedule.every(10).minutes.do(job)

    print("⏱️ Mises à jour prévues toutes les 10 minutes.")
    while True:
        schedule.run_pending()
        time.sleep(1)
