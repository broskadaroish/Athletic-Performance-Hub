"""
Bruce Football Performance Diagnostics — Windows Launcher
Startpunkt für die PyInstaller-gebundene Streamlit-Anwendung.
"""

import os
import sys
import socket
import threading
import time
import webbrowser

# ── Pfade ─────────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # PyInstaller: alle App-Dateien liegen in sys._MEIPASS
    APP_DIR = sys._MEIPASS
else:
    # Entwicklung: launcher.py liegt in installer/, App-Dateien eine Ebene höher
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_PY = os.path.join(APP_DIR, "app.py")

# ── Benutzerdaten-Verzeichnis (APPDATA) ───────────────────────────────────────
APPDATA = os.environ.get("APPDATA") or os.path.expanduser("~")
DATA_DIR = os.path.join(APPDATA, "BruceFootballDiagnostics")
os.makedirs(DATA_DIR, exist_ok=True)

# Unterordner anlegen
for sub in ("Berichte", "Trainingspläne", "Backups", "Logs"):
    os.makedirs(os.path.join(DATA_DIR, sub), exist_ok=True)

# CWD auf Datenverzeichnis setzen → athletik.db und Backups landen in APPDATA
os.chdir(DATA_DIR)

# Damit Assets (assets/, tests/-SVGs …) via os.path.dirname(__file__) gefunden werden
# wird APP_DIR in sys.path eingetragen (PyInstaller macht das für _MEIPASS ohnehin)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# ── Freien Port finden ────────────────────────────────────────────────────────
def _freier_port(start: int = 8501) -> int:
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return start


PORT = _freier_port()


# ── Browser nach Verzögerung öffnen ──────────────────────────────────────────
def _oeffne_browser():
    time.sleep(4)
    webbrowser.open(f"http://localhost:{PORT}")


threading.Thread(target=_oeffne_browser, daemon=True).start()

# ── Streamlit starten ─────────────────────────────────────────────────────────
from streamlit.web import bootstrap  # noqa: E402

flag_options = {
    "server.port": PORT,
    "server.address": "localhost",
    "server.headless": True,
    "browser.gatherUsageStats": False,
    "global.developmentMode": False,
    "server.maxUploadSize": 50,
}

bootstrap.run(APP_PY, "", [], flag_options)
