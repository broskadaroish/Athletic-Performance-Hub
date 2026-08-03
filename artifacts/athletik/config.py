"""
Zentrale Anwendungskonfiguration — alle Env-Variablen werden hier gelesen.
Kein anderes Modul soll direkt os.environ befragen.

Einbinden:
    import config
    config.ensure_dirs()   # einmalig beim Start
"""

import os
from pathlib import Path

# ── Verzeichnisse ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# DATA_DIR: für Cloud-Betrieb auf ein persistentes Volume zeigen lassen.
# Beispiel Render: ATHLETIK_DATA_DIR=/data
# Beispiel Railway: ATHLETIK_DATA_DIR=/mnt/data
DATA_DIR = Path(os.environ.get("ATHLETIK_DATA_DIR", str(BASE_DIR)))

UPLOAD_DIR      = DATA_DIR / "uploads"
LOGO_DIR        = UPLOAD_DIR / "logos"
SPIELERBILD_DIR = UPLOAD_DIR / "spielerbilder"
PDF_DIR         = UPLOAD_DIR / "pdf"
EXPORT_DIR      = UPLOAD_DIR / "exports"
BACKUP_DIR      = UPLOAD_DIR / "backups"
DOCS_DIR        = UPLOAD_DIR / "docs"      # eigene Protokolle / Anleitungen
LOG_DIR         = DATA_DIR / "logs"

# ── Datenbank ────────────────────────────────────────────────────────────────
# Wenn DATABASE_URL gesetzt ist → PostgreSQL-Adapter nutzen.
# Wenn nicht → SQLite (Standard für Entwicklung und kleinen Livebetrieb).
DATABASE_URL = os.environ.get("DATABASE_URL", "")           # Standard Render/Railway
SQLITE_PATH  = os.environ.get(
    "ATHLETIK_DB_PATH",
    str(DATA_DIR / "athletik.db"),
)

USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))

# Railway/Render setzen DATABASE_URL manchmal mit "postgres://" — psycopg2 braucht "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

# ── Sicherheit ───────────────────────────────────────────────────────────────
SESSION_SECRET = os.environ.get("SESSION_SECRET", "CHANGE-ME-IN-PRODUCTION-please-set-SESSION_SECRET")
SECRET_KEY     = os.environ.get("SECRET_KEY", SESSION_SECRET)

# ── Anwendung ────────────────────────────────────────────────────────────────
APP_ENV   = os.environ.get("APP_ENV", "development")   # development | production
DEBUG     = APP_ENV != "production"
PORT      = int(os.environ.get("PORT", 8082))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING" if not DEBUG else "DEBUG")

# ── Upload-Limits ─────────────────────────────────────────────────────────────
MAX_UPLOAD_MB      = int(os.environ.get("MAX_UPLOAD_MB", 10))
MAX_LOGO_MB        = int(os.environ.get("MAX_LOGO_MB", 2))
MAX_SPIELERBILD_MB = int(os.environ.get("MAX_SPIELERBILD_MB", 5))
MAX_DOC_MB         = int(os.environ.get("MAX_DOC_MB", 20))

# ── HTTPS / Proxy ─────────────────────────────────────────────────────────────
BEHIND_PROXY      = os.environ.get("BEHIND_PROXY", "1") == "1"  # Standard: ja (Render, Railway, VPS)
TRUSTED_PROXIES   = os.environ.get("TRUSTED_PROXIES", "127.0.0.1,::1")


def ensure_dirs() -> None:
    """Stellt sicher, dass alle Upload- und Log-Verzeichnisse existieren.
    Idempotent — kann mehrfach aufgerufen werden.
    """
    for d in [
        UPLOAD_DIR, LOGO_DIR, SPIELERBILD_DIR,
        PDF_DIR, EXPORT_DIR, BACKUP_DIR, DOCS_DIR, LOG_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# ── Beim Import sofort ausführen ─────────────────────────────────────────────
ensure_dirs()
