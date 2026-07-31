"""
PyInstaller Runtime Hook — Bruce Football Performance Diagnostics
Setzt Umgebungsvariablen für den Offline-Betrieb und den korrekten
Streamlit-Startup ohne Browser-Öffnung.
"""
import os
import sys

# Streamlit ohne automatischen Browser-Start
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")

# Datenbank-Pfad relativ zum Executable (AppData)
import pathlib
_appdata = pathlib.Path(os.environ.get("APPDATA", ".")) / "BruceFootball"
_appdata.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("BRUCE_DB_PATH", str(_appdata / "athletik.db"))
