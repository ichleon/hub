### link [hub](https://a57970-77e1.a.jrnm.app)


## NEO-HUB — Setup


## Installation

```bash
cd hub
pip install -r requirements.txt
python server.py
```

Dann im Browser öffnen: **http://localhost:5000** (oder `http://<pi-ip>:5000`,
wenn der Server z.B. auf deinem Raspberry Pi 5 läuft).

Wichtig: `hub.html` NICHT direkt als Datei doppelklicken — sie muss über
`http://localhost:5000/` vom Server ausgeliefert werden, sonst fehlen die
`/api/...`-Endpunkte und der WebSocket (same-origin).

## Was macht jede Kachel?

| Kachel | Funktion |
|---|---|
| **Portal A** | Holt einen zufälligen Fakt/Spruch von einer externen API (`api.adviceslip.com`); fällt ohne Internet auf eine lokale Liste zurück. |
| **Daten-Knoten** | Zeigt echte CPU-, RAM- und Speicherauslastung deines Rechners (via `psutil`), aktualisiert alle 2 Sekunden. |
| **Komm-Raum** | Echter Live-Chat über WebSocket (`/ws/chat`). Öffne den Hub in zwei Tabs, um es zu testen — Nachrichten werden an alle verbundenen Clients gesendet. |
| **System-Log** | Zeigt die letzten 50 Zeilen aus `hub.log`, dem echten Log-File des Servers (jede Anfrage wird geloggt). |
| **Standort** | Nutzt die Geolocation-API deines Browsers (fragt um Erlaubnis) und zeigt Koordinaten + eine echte OpenStreetMap-Karte. Braucht keinen Server. |
| **Zeit-Sync** | Holt die Serverzeit über `/api/time`, berechnet den Offset zur lokalen Uhr und zeigt eine live tickende Uhr plus Weltzeiten (Berlin/UTC/New York/Tokio). |

## Dateien

- `hub.html` — Frontend (Design unverändert, jetzt mit echten Modal-Funktionen)
- `server.py` — Flask-Backend mit allen API-Routen + WebSocket-Chat
- `requirements.txt` — `flask`, `flask-sock`, `psutil`, `requests`
- `hub.log` — wird beim ersten Start automatisch angelegt


