import requests
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# 🔧 Charger le fichier .env depuis ton dossier Android
load_dotenv("/storage/emulated/0/Analyze/.env")

# 🧩 Récupération des clés API depuis le fichier .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔔 Fonction pour envoyer un message Telegram
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERREUR] Clés Telegram manquantes dans .env")
        print(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}")
        print(f"TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ✅ Message envoyé à Telegram")
        else:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ❌ Erreur Telegram : {response.text}")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ⚠️ Erreur lors de l’envoi Telegram : {e}")

# 🧮 Fonction de calcul du score de pump
def pump_score(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
        r = requests.get(url, timeout=10)
        data = r.json()

        price_change = float(data["priceChangePercent"])
        volume = float(data["quoteVolume"])

        score = 0
        if price_change > 5:
            score += 2
        if price_change > 10:
            score += 3
        if volume > 10000000:
            score += 2
        if volume > 50000000:
            score += 3

        return score, price_change, volume
    except Exception as e:
        print(f"Erreur lors du calcul pour {symbol}: {e}")
        return 0, 0, 0

# 🔍 Liste des cryptos à surveiller
TOKENS = ["ASTR", "PEPE", "WIF", "SOL", "TIA", "DOGE", "BTC", "ETH"]

# 🕒 Fonction principale
def main():
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 🚀 Smart Pump Detector lancé (Android - Pydroid 3)")

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_message("🚀 Smart Pump Detector vient d’être lancé ✅")

    while True:
        for token in TOKENS:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Analyse de {token}...")
            score, change, volume = pump_score(token)
            if score >= 5:
                alert = f"🚨 {token} semble PUMPER !\n💹 Variation : {change:.2f}%\n💰 Volume : {volume/1_000_000:.2f}M USDT\nScore : {score}/10"
                print(alert)
                send_telegram_message(alert)
            else:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Rien de spécial sur {token} (score={score})")

        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ⏳ Nouvelle vérification dans 3 min...")
        time.sleep(180)

# 🏁 Lancement du programme
if __name__ == "__main__":
    main()