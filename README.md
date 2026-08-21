# NEO-HUB — Setup

Alle 6 Kacheln sind jetzt echt funktional. Damit alles läuft (WebSocket-Chat,
System-Stats, Log, Zeit-Sync), brauchst du den kleinen Python-Server. Ohne
ihn öffnet sich `hub.html` zwar weiterhin, aber Standort ist der einzige
Punkt, der auch rein im Browser (ohne Server) funktioniert.

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

## Erweiterungsideen für dein Pi-5-Setup

Da du sowieso schon einen Webhook-zu-WebSocket-Gateway für deine
OLED/LCD-Displays baust: `server.py` lässt sich leicht erweitern, damit
z.B. die Daten-Knoten-Kachel echte Sensordaten deines Pi anzeigt
(Temperatur über `vcgencmd measure_temp`, GPIO-Status über `pinctrl`, etc.)
statt nur CPU/RAM. Sag Bescheid, wenn ich das einbauen soll.
