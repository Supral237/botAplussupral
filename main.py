# main.py
import os
import requests
import threading
import time
import schedule
import json
from flask import Flask, request, jsonify
from datetime import datetime, timezone

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ex. https://botaplussupral-2.onrender.com
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # ton chat id
PUMP_THRESHOLD = float(os.getenv("PUMP_THRESHOLD", "10"))  # % en 24h pour alerter
REDDIT_SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "CryptoCurrency,CryptoMoonShots,CryptoMarkets").split(",")
REDDIT_KEYWORDS = [k.strip().lower() for k in os.getenv("REDDIT_KEYWORDS", "partnership,listing,airdrop,partenariat,listing,collab").split(",")]

STATE_FILE = "state.json"  # stockage simple des derniers ids vus (persistant tant que Render instance vivante)

# ---------- INIT ----------
app = Flask(__name__)

if not BOT_TOKEN or not WEBHOOK_URL or not ADMIN_CHAT_ID:
    raise RuntimeError("BOT_TOKEN, WEBHOOK_URL et ADMIN_CHAT_ID doivent être définis dans l'environnement.")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------- Helpers ----------
def send_message(chat_id, text, parse_mode="Markdown"):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }, timeout=10)
    except Exception as e:
        print("Erreur send_message:", e)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # état initial
    return {"seen_reddit": {}, "last_pumps": {}}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print("Erreur save_state:", e)

state = load_state()

# ---------- CoinGecko pump detector ----------
def check_for_pumps():
    try:
        print(f"[{datetime.now().isoformat()}] Vérification pumps...")
        # top 100 marchés (page=1, per_page=100)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1, "sparkline": "false", "price_change_percentage": "24h"}
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        alerts = []
        for coin in data:
            change = coin.get("price_change_percentage_24h")  # float
            if change is None:
                continue
            if change >= PUMP_THRESHOLD:
                coin_id = coin.get("id")
                last_alert = state.get("last_pumps", {}).get(coin_id)
                # éviter doublons fréquents : n'alerter qu'une fois par fenêtre de 6h par coin
                now = time.time()
                if not last_alert or now - last_alert > 6*3600:
                    alerts.append({
                        "name": coin.get("name"),
                        "symbol": coin.get("symbol"),
                        "price": coin.get("current_price"),
                        "change": round(change,2),
                        "id": coin_id
                    })
                    state.setdefault("last_pumps", {})[coin_id] = now

        if alerts:
            for a in alerts:
                msg = f"🚨 *Alerte Pump* : {a['name']} ({a['symbol'].upper()})\n24h: *{a['change']}%*\nPrix: `${a['price']}`\nhttps://www.coingecko.com/fr/pi%C3%A8ces/{a['id']}"
                send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
                print("Alerte envoyée pour", a['name'])
            save_state(state)
        else:
            print("Aucun pump détecté.")
    except Exception as e:
        print("Erreur check_for_pumps:", e)

# ---------- Reddit scanner (public JSON) ----------
USER_AGENT = "botAplus:monitor:v1 (by /u/yourname)"

def scan_reddit():
    try:
        print(f"[{datetime.now().isoformat()}] Scan Reddit...")
        headers = {"User-Agent": USER_AGENT}
        for subreddit in REDDIT_SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                print("Reddit status", resp.status_code, "for", subreddit)
                continue
            j = resp.json()
            posts = j.get("data", {}).get("children", [])
            for p in posts:
                pid = p["data"]["id"]
                title = p["data"].get("title", "")
                url_post = "https://reddit.com" + p["data"].get("permalink", "")
                # seen?
                seen_for_sub = state.setdefault("seen_reddit", {}).setdefault(subreddit, [])
                if pid in seen_for_sub:
                    continue
                # mark seen
                seen_for_sub.append(pid)
                # keep seen list small
                if len(seen_for_sub) > 200:
                    state["seen_reddit"][subreddit] = seen_for_sub[-200:]
                # check keywords
                title_lower = title.lower()
                for kw in REDDIT_KEYWORDS:
                    if kw and kw in title_lower:
                        msg = f"💬 *Rumeur/Annonce détectée* dans r/{subreddit} :\n\n*{title}*\n\n{url_post}\n\nMot-clé: `{kw}`"
                        send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
                        print("Rumeur détectée:", title)
                        break
        save_state(state)
    except Exception as e:
        print("Erreur scan_reddit:", e)

# ---------- Scheduler thread ----------
def scheduler_loop():
    # checks
    schedule.every(10).minutes.do(check_for_pumps)     # marché
    schedule.every(5).minutes.do(scan_reddit)         # rumeurs
    # daily summary at 08:00 (server time — Render uses UTC; tu peux ajuster)
    # schedule.every().day.at("08:00").do(send_daily_summary)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print("Erreur schedule.run_pending:", e)
        time.sleep(1)

# ---------- Telegram webhook handler ----------
@app.route("/", methods=["POST","GET"])
def webhook():
    if request.method == "GET":
        return "Bot A+ en ligne", 200
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok":False}), 400
    # simple logging
    print("Update reçu:", data.keys())
    message = data.get("message") or data.get("edited_message")
    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text","").strip()
        # commands
        if text.startswith("/start"):
            send_message(chat_id, "🤖 Bot A+ actif. /analyse, /monitor_on, /monitor_off, /set_threshold <n>, /status")
        elif text.startswith("/analyse"):
            send_message(chat_id, "🔎 Lancement d'une analyse instantanée...")
            # instant run checks
            try:
                check_for_pumps()
                scan_reddit()
                send_message(chat_id, "✅ Analyse terminée. Vérifie les alertes envoyées.")
            except Exception as e:
                send_message(chat_id, f"Erreur analyse: {e}")
        elif text.startswith("/monitor_on"):
            # start scheduler thread if not running (we run it at startup anyway)
            send_message(chat_id, "✅ Monitoring activé (déjà en cours sur le serveur).")
        elif text.startswith("/monitor_off"):
            send_message(chat_id, "⚠️ Pour arrêter le monitoring, stoppe le service sur Render.")
        elif text.startswith("/set_threshold"):
            parts = text.split()
            if len(parts) >= 2:
                try:
                    val = float(parts[1])
                    global PUMP_THRESHOLD
                    PUMP_THRESHOLD = val
                    send_message(chat_id, f"✅ Seuil de pump mis à {PUMP_THRESHOLD}%")
                except:
                    send_message(chat_id, "Usage: /set_threshold 10")
            else:
                send_message(chat_id, "Usage: /set_threshold 10")
        elif text.startswith("/status"):
            send_message(chat_id, f"Status: pump_threshold={PUMP_THRESHOLD}%. Subreddits={','.join(REDDIT_SUBREDDITS)}")
        else:
            send_message(chat_id, "Commande inconnue. Voir /start")
    return jsonify({"ok":True})

# ---------- Auto set webhook on startup ----------
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}"  # Telegram posts POST to this URL root
    try:
        r = requests.get(f"{TELEGRAM_API}/setWebhook?url={webhook_url}", timeout=10)
        print("Webhook set:", r.text)
    except Exception as e:
        print("Erreur set_webhook:", e)

# ---------- Entrypoint ----------
if __name__ == "__main__":
    # start scheduler thread
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    # set webhook
    set_webhook()
    # run flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
