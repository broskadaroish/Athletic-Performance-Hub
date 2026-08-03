"""
Zentrale Konfiguration — Bruce Football Performance Diagnostics.
Alle Einstellungen aus Umgebungsvariablen.
"""

import os
from pathlib import Path

# ── Allgemeines ───────────────────────────────────────────────────────────────
APP_ENV   = os.environ.get("APP_ENV", "development")   # development | production
DEBUG     = APP_ENV != "production"
PORT      = int(os.environ.get("PORT", "8082"))

# ── Daten-Verzeichnis ─────────────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("ATHLETIK_DATA_DIR", os.path.dirname(__file__)))

SQLITE_PATH = os.environ.get(
    "ATHLETIK_DB_PATH",
    str(DATA_DIR / "athletik.db"),
)

# ── Upload-Limits ─────────────────────────────────────────────────────────────
MAX_UPLOAD_MB    = int(os.environ.get("MAX_UPLOAD_MB",    "10"))
MAX_LOGO_MB      = int(os.environ.get("MAX_LOGO_MB",       "2"))
MAX_SPIELERBILD_MB = int(os.environ.get("MAX_SPIELERBILD_MB", "5"))
MAX_DOC_MB       = int(os.environ.get("MAX_DOC_MB",       "10"))

# ── Upload-Verzeichnisse ──────────────────────────────────────────────────────
LOGOS_DIR      = DATA_DIR / "uploads" / "logos"
SPIELERBILDER_DIR = DATA_DIR / "uploads" / "spielerbilder"
PDF_DIR        = DATA_DIR / "uploads" / "pdf"
EXPORTS_DIR    = DATA_DIR / "uploads" / "exports"
BACKUPS_DIR    = DATA_DIR / "uploads" / "backups"
DOCS_DIR       = DATA_DIR / "uploads" / "docs"
LOGS_DIR       = DATA_DIR / "logs"

for _d in [LOGOS_DIR, SPIELERBILDER_DIR, PDF_DIR, EXPORTS_DIR, BACKUPS_DIR, DOCS_DIR, LOGS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Sicherheit ────────────────────────────────────────────────────────────────
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
SECRET_KEY     = os.environ.get("SECRET_KEY",     "dev-key-change-in-production")

# ── Proxy-Konfiguration ───────────────────────────────────────────────────────
BEHIND_PROXY     = os.environ.get("BEHIND_PROXY", "false").lower() == "true"
TRUSTED_PROXIES  = os.environ.get("TRUSTED_PROXIES", "127.0.0.1")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING" if APP_ENV == "production" else "INFO")

# ── Backup ───────────────────────────────────────────────────────────────────
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
# S3-kompatibler Speicher für externes Backup (leer = deaktiviert)
S3_BUCKET        = os.environ.get("S3_BUCKET", "")
S3_ENDPOINT_URL  = os.environ.get("S3_ENDPOINT_URL", "")

# ── Session-Timeout ───────────────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "60"))

# ── Brute-Force-Schutz ────────────────────────────────────────────────────────
MAX_LOGIN_VERSUCHE    = int(os.environ.get("MAX_LOGIN_VERSUCHE",    "5"))
LOGIN_SPERRE_MINUTEN  = int(os.environ.get("LOGIN_SPERRE_MINUTEN", "15"))

# ── Wartungsmodus ─────────────────────────────────────────────────────────────
MAINTENANCE_MODE    = os.environ.get("MAINTENANCE_MODE", "0") == "1"
MAINTENANCE_MESSAGE = os.environ.get("MAINTENANCE_MESSAGE", "")

# ── Stripe ────────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY",     "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

# Stripe Price-IDs (werden nach der Stripe-Produkt-Anlage befüllt)
STRIPE_PRICE_BASIC_MONAT = os.environ.get("STRIPE_PRICE_BASIC_MONAT", "")
STRIPE_PRICE_BASIC_JAHR  = os.environ.get("STRIPE_PRICE_BASIC_JAHR",  "")
STRIPE_PRICE_PRO_MONAT   = os.environ.get("STRIPE_PRICE_PRO_MONAT",   "")
STRIPE_PRICE_PRO_JAHR    = os.environ.get("STRIPE_PRICE_PRO_JAHR",    "")

# Öffentliche App-URL (für Stripe Redirect-URLs)
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8082")
