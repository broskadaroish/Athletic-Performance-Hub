"""
Logging-Konfiguration für Athletik App.
Wird einmalig beim Import ausgeführt (Streamlit-Module werden nur einmal geladen).

Features:
- Konsolen-Ausgabe (stdout) → wird von Cloud-Diensten (Render, Railway, VPS) erfasst
- In Produktion: rotierende Logdatei (5 MB × 10 = max 50 MB) + error.log
- Streamlit- und Bibliotheks-Logger auf WARNING gedrosselt
"""

import logging
import logging.handlers
import sys

import config  # importiert ensure_dirs() → Verzeichnisse existieren


_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> logging.Logger:
    """Konfiguriert Root-Logger. Gibt den App-Logger zurück."""
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.WARNING)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    if config.APP_ENV == "production":
        # Rotierende Logdatei
        log_file = config.LOG_DIR / "athletik.log"
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=10,
            encoding="utf-8",
        )
        fh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        handlers.append(fh)

        # Separate Fehlerdatei (nur ERROR+)
        err_file = config.LOG_DIR / "error.log"
        eh = logging.handlers.RotatingFileHandler(
            err_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        eh.setLevel(logging.ERROR)
        eh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        handlers.append(eh)

    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )

    # Bibliotheks-Logger auf WARNING drosseln (Streamlit ist gesprächig)
    for noisy in ("streamlit", "watchdog", "urllib3", "PIL", "matplotlib", "fpdf"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return logging.getLogger("athletik")


# Einmalig beim Import ausführen
logger = setup_logging()
logger.info("Athletik App gestartet — Umgebung: %s", config.APP_ENV)
