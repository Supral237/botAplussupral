import os
import time
import threading
import logging
import requests
import schedule
from flask import Flask
import telebot

# --- CONFIGURATION ---
TOKEN = os.getenv("8404423366:AAELzmHapklGgYTa_nHCRzVzYaEjWDSBeQA") or "TON_TOKEN_ICI"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# --- STOCKAGE DES UTILISATEURS ---
USERS_FILE = "users.txt"


def save_user(chat_id):
    """Enregistre l'utilisateur dans un fichier s'il n'existe pas déjà."""
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(str(chat_id) + "\n")
        logger.info(f"Nouvel utilisateur ajouté : {chat_id}")


def get_all_users():
    """Récupère la liste des utilisateurs enregistrés."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return [u.strip() for u in f if u.strip()]


# --- ANALYSE COMBINÉE ---
def analyse_combinee():
    """
    Combine les données de rumeurs et de smart money.
    (Ici on simule, mais tu peux connecter ton API ou tes scripts d'analyse réels)
    """
    logger.info("Début de l’analyse combinée (rumeurs + smart money)...")

    try:
        # Exemple de récupération des données simulées
        rumeurs = "Les rumeurs indiquent une forte activité sur $OP et $INJ."
        smart_money = "Les portefeuilles smart money accumulent massivement du $INJ."

        resultat = f"🔥 **Analyse combinée** 🔥\n\n📈 {rumeurs}\n💰 {smart_money}\n\nConclusion : $INJ montre un fort potentiel de pump."
        logger.info("Analyse combinée terminée avec succès.")
        return resultat

    except Exception as e:
        logger.error(f"Erreur pendant l’analyse combinée : {e}")
        return "⚠️ Erreur pendant l’analyse combinée."


# --- ENVOI AUTOMATIQUE ---
def envoyer_analyse_auto():
    """Envoie automatiquement l’analyse combinée à tous les utilisateurs."""
    logger.info("Démarrage de l’envoi automatique de l’analyse...")
    try:
        users = get_all_users()
        if not users:
            logger.warning("Aucun utilisateur enregistré. Aucun envoi effectué.")
            return

        message = analyse_combinee()
        for user in users:
            try:
                bot.send_message(user, message, parse_mode="Markdown")
                logger.info(f"Analyse envoyée à {user}")
            except Exception as e:
                logger.error(f"Erreur lors de l’envoi à {user}: {e}")
    except Exception as e:
        logger.error(f"Erreur globale dans l’envoi automatique : {e}")


# Planifie l’envoi toutes les 6 heures
schedule.every(6).hours.do(envoyer_analyse_auto)


def scheduler_thread():
    """Thread pour exécuter le scheduler sans bloquer le bot."""
    while True:
        schedule.run_pending()
        time.sleep(30)


# --- HANDLERS TELEGRAM ---
@bot.message_handler(commands=["start"])
def start_command(message):
    save_user(message.chat.id)
    bot.reply_to(
        message,
        "👋 Salut ! Tu recevras désormais automatiquement les analyses crypto toutes les 6h 🚀",
    )
    logger.info(f"Commande /start reçue de {message.chat.id}")


@bot.message_handler(commands=["analyse"])
def manual_analyse(message):
    logger.info(f"Commande /analyse demandée par {message.chat.id}")
    resultat = analyse_combinee()
    bot.reply_to(message, resultat, parse_mode="Markdown")


# --- FLASK KEEP-ALIVE ---
@app.route("/")
def home():
    return "Bot actif ✅"


# --- LANCEMENT GLOBAL ---
if __name__ == "__main__":
    logger.info("Démarrage du bot Telegram...")

    # Thread 1 : bot Telegram
    bot_thread = threading.Thread(target=bot.infinity_polling, name="TelegramBot")
    bot_thread.start()

    # Thread 2 : scheduler (envoi toutes les 6h)
    schedule_thread = threading.Thread(target=scheduler_thread, name="Scheduler")
    schedule_thread.start()

    # Serveur Flask pour Render
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Lancement du serveur Flask sur le port {port}...")
    app.run(host="0.0.0.0", port=port)
