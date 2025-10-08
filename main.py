import requests
import schedule
import time
import threading
from flask import Flask

# ==========================================================
# 🔧 CONFIGURATION DU BOT
# ==========================================================
BOT_TOKEN = "TON_TOKEN_TELEGRAM_ICI"  # <-- Mets ici ton token
CHAT_ID = "TON_CHAT_ID_ICI"           # <-- Mets ici ton ID Telegram

# ==========================================================
# 🧠 FONCTIONS DU BOT
# ==========================================================
def envoyer_message(message):
    """Envoie un message sur Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("⚠️ Erreur d’envoi Telegram :", e)

def bot_tache_principale():
    """Ici tu peux mettre ton code de veille crypto, par exemple."""
    print("🔍 Exécution de la tâche principale...")
    envoyer_message("🤖 Bot A+ exécute la veille automatique crypto...")

# ==========================================================
# 🕒 PLANIFICATION AUTOMATIQUE
# ==========================================================
def demarrer_schedule():
    """Démarre la planification (exécute la tâche toutes les 10 minutes)."""
    schedule.every(10).minutes.do(bot_tache_principale)
    print("✅ Planificateur activé (toutes les 10 minutes)")
    while True:
        schedule.run_pending()
        time.sleep(5)

# ==========================================================
# 🌐 SERVEUR FLASK POUR RENDER (garde le bot en ligne)
# ==========================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Bot A+ est en ligne et fonctionne parfaitement sur Render !"

def run_flask():
    """Lance Flask sur un port pour Render."""
    app.run(host='0.0.0.0', port=10000)

# ==========================================================
# 🚀 DÉMARRAGE DU BOT
# ==========================================================
if __name__ == "__main__":
    print("🔍 Démarrage du bot A+...")

    # Envoie un message Telegram au lancement
    envoyer_message("✅ Bot A+ démarré avec succès sur Render !")

    # Lancer Flask dans un thread parallèle
    threading.Thread(target=run_flask).start()

    # Lancer le planificateur
    demarrer_schedule()
