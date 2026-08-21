"""
NEO-HUB Backend
================
Liefert hub.html aus und stellt die Endpunkte bereit, die das Frontend braucht:

  GET  /                -> liefert hub.html
  GET  /api/time         -> Serverzeit (fuer Zeit-Sync)
  GET  /api/system       -> CPU/RAM/Speicher/Uptime (fuer Daten-Knoten)
  GET  /api/log          -> letzte Zeilen aus hub.log (fuer System-Log)
  GET  /api/portal       -> zufaelliger Fakt (fuer Portal A), inkl. Fallback ohne Internet
  WS   /ws/chat          -> einfacher Broadcast-Chat (fuer Komm-Raum)

Installation:
    pip install -r requirements.txt

Start:
    python server.py

Standardmaessig laeuft der Server auf http://0.0.0.0:5000 -- einfach im
Browser auf dem Pi oder im lokalen Netz oeffnen (http://<pi-ip>:5000).
"""

import json
import logging
import os
import platform
import random
import socket
import threading
import time
from datetime import datetime, timezone

import psutil
import requests
from flask import Flask, jsonify, send_from_directory
from flask_sock import Sock

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "hub.log")

app = Flask(__name__, static_folder=None)
sock = Sock(app)

# ---------------------------------------------------------------------------
# Logging: alles landet in hub.log, damit /api/log echte Zeilen anzeigen kann
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("neo-hub")

# Werkzeugs eigene (bunte) Request-Logs sollen nicht in hub.log landen,
# damit /api/log nur unsere eigenen, sauberen Eintraege zeigt.
logging.getLogger("werkzeug").propagate = False


def boot_log_entry():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()
    logger.info("NEO-HUB Server gestartet auf Host %s", socket.gethostname())


boot_log_entry()

START_TIME = time.time()


# ---------------------------------------------------------------------------
# Statische Auslieferung von hub.html
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    logger.info("Hub-Seite aufgerufen")
    return send_from_directory(APP_DIR, "hub.html")


# ---------------------------------------------------------------------------
# Zeit-Sync
# ---------------------------------------------------------------------------
@app.route("/api/time")
def api_time():
    now = datetime.now(timezone.utc)
    return jsonify({
        "iso": now.isoformat(),
        "unix": now.timestamp(),
    })


# ---------------------------------------------------------------------------
# Daten-Knoten: echte System-Stats via psutil
# ---------------------------------------------------------------------------
def format_uptime(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


@app.route("/api/system")
def api_system():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot = psutil.boot_time()
    uptime_seconds = time.time() - boot

    logger.info("System-Stats abgefragt (CPU %.1f%%, RAM %.1f%%)",
                psutil.cpu_percent(interval=0.2), mem.percent)

    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / (1024 ** 3), 1),
        "memory_total_gb": round(mem.total / (1024 ** 3), 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "hostname": socket.gethostname(),
        "platform": f"{platform.system()} {platform.release()}",
        "uptime": format_uptime(uptime_seconds),
    })


# ---------------------------------------------------------------------------
# System-Log: letzte Zeilen aus hub.log
# ---------------------------------------------------------------------------
@app.route("/api/log")
def api_log():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
        return jsonify({"lines": [l.rstrip("\n") for l in lines]})
    except FileNotFoundError:
        return jsonify({"lines": ["Noch keine Log-Eintraege vorhanden."]})


# ---------------------------------------------------------------------------
# Portal A: zufaelliger Fakt, mit Offline-Fallback-Liste
# ---------------------------------------------------------------------------
FALLBACK_FACTS = [
    "Ein Raspberry Pi 5 hat einen eigenen RP1-Chip fuer I/O, getrennt vom Haupt-SoC.",
    "Der erste Computerbug war 1947 buchstaeblich ein Bug: eine Motte in einem Relais.",
    "ComputerCraft-Turtles in Minecraft koennen sich selbst mit Lua-Code neu programmieren.",
    "I2C wurde von Philips in den 1980ern entwickelt, urspruenglich fuer Fernseher.",
    "WebSockets erlauben bidirektionale Kommunikation ueber eine einzige TCP-Verbindung.",
    "GPIO steht fuer General Purpose Input/Output.",
]


@app.route("/api/portal")
def api_portal():
    try:
        resp = requests.get("https://api.adviceslip.com/advice", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        fact = data["slip"]["advice"]
        logger.info("Portal-Fakt von externer API geladen")
        return jsonify({"fact": fact, "source": "adviceslip.com"})
    except Exception as e:
        logger.warning("Portal-API nicht erreichbar (%s), nutze Fallback", e)
        return jsonify({"fact": random.choice(FALLBACK_FACTS), "source": "lokal"})


# ---------------------------------------------------------------------------
# Komm-Raum: einfacher Broadcast-Chat ueber WebSocket
# ---------------------------------------------------------------------------
clients = set()
clients_lock = threading.Lock()


def broadcast(payload, exclude=None):
    dead = []
    with clients_lock:
        for c in clients:
            if c is exclude:
                continue
            try:
                c.send(json.dumps(payload))
            except Exception:
                dead.append(c)
        for d in dead:
            clients.discard(d)


@sock.route("/ws/chat")
def ws_chat(ws):
    with clients_lock:
        clients.add(ws)
    logger.info("Neuer Chat-Client verbunden (aktiv: %d)", len(clients))
    try:
        while True:
            raw = ws.receive()
            if raw is None:
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "join":
                broadcast({"type": "system", "text": f"{msg.get('user', 'Jemand')} ist dem Raum beigetreten."}, exclude=ws)
            elif msg.get("type") == "message":
                text = str(msg.get("text", ""))[:300]
                user = str(msg.get("user", "Anonym"))[:32]
                logger.info("Chat: %s: %s", user, text)
                broadcast({"type": "chat", "user": user, "text": text})
    finally:
        with clients_lock:
            clients.discard(ws)
        logger.info("Chat-Client getrennt (aktiv: %d)", len(clients))


if __name__ == "__main__":
    # debug=False + threaded, damit mehrere WebSocket-Clients gleichzeitig funktionieren
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
