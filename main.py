import os
import time
import requests
from flask import Flask, request
from telebot import TeleBot, types

# =======================
# 🔧 Configuration de base
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if not BOT_TOKEN:
    raise ValueError("❌ La variable BOT_TOKEN n'est pas définie dans Render.")

if not HOSTNAME:
    raise ValueError("❌ La variable RENDER_EXTERNAL_HOSTNAME n'est pas définie dans Render.")

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

print(f"[LOG] ✅ BOT_TOKEN détecté : {BOT_TOKEN[:6]}********")
print(f"[LOG] ✅ HOSTNAME utilisé : {HOSTNAME}")
print("[LOG] 🚀 Démarrage du bot A+ Supral avec DexScreener...")

# ============================
# ⚙️ Configuration du webhook
# ============================
def setup_webhook():
    webhook_url = f"https://{HOSTNAME}/webhook"
    print(f"[LOG] 🌐 Tentative de configuration du webhook : {webhook_url}")

    # Attendre que Render démarre bien
    for i in range(5):
        try:
            response = requests.get(f"https://{HOSTNAME}/")
            if response.status_code == 200:
                print("[LOG] ✅ Render est accessible, configuration du webhook...")
                break
        except Exception as e:
            print(f"[LOG] ⚠️ Render pas encore prêt ({e}), nouvelle tentative...")
        time.sleep(3)

    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)

    if success:
        print("[LOG] ✅ Webhook configuré avec succès !")
    else:
        print("[LOG] ❌ Échec de la configuration du webhook.")

# ============================
# 🔎 Fonction de surveillance
# ============================
def fetch_dexscreener_data():
    """Récupère les nouvelles paires détectées sur DexScreener"""
    url = "https://api.dexscreener.com/latest/dex/tokens"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("pairs", [])[:5]
    except Exception as e:
        print(f"[LOG] ⚠️ Erreur DexScreener : {e}")
    return []

def format_pair(pair):
    """Formate les infos DexScreener en message lisible"""
    name = pair.get("baseToken", {}).get("name", "Unknown")
    symbol = pair.get("baseToken", {}).get("symbol", "N/A")
    price = pair.get("priceUsd", "N/A")
    chain = pair.get("chainId", "N/A")
    liquidity = pair.get("liquidity", {}).get("usd", "N/A")
    url = pair.get("url", "https://dexscreener.com")

    return (
        f"💎 *Nouveau Token repéré !*\n\n"
        f"🪙 Nom : *{name}* ({symbol})\n"
        f"💰 Prix : ${price}\n"
        f"🌐 Réseau : {chain}\n"
        f"💦 Liquidité : ${liquidity}\n"
        f"🔗 [Voir sur DexScreener]({url})"
    )

# ============================
# 🧠 Commande Telegram
# ============================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Bienvenue sur *A+ Supral Bot* !\n"
                          "Je t’enverrai des signaux DexScreener 🚀")

@bot.message_handler(commands=['scan'])
def manual_scan(message):
    pairs = fetch_dexscreener_data()
    if not pairs:
        bot.send_message(message.chat.id, "⚠️ Aucune nouvelle paire trouvée.")
        return

    for pair in pairs:
        msg = format_pair(pair)
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", disable_web_page_preview=False)

# ============================
# 🌐 Routes Flask
# ============================
@app.route('/webhook', methods=['POST'])
def webhook():
    """Reçoit les updates Telegram via Render"""
    update = request.stream.read().decode("utf-8")
    bot.process_new_updates([TeleBot.types.Update.de_json(update)])
    return "OK", 200

@app.route('/')
def home():
    return "✅ Bot A+ Supral en ligne avec Webhook actif", 200

# ============================
# 🚀 Lancement principal
# ============================
if __name__ == '__main__':
    setup_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
