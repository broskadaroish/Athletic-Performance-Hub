"""
Lizenz-Ablauf-Scheduler — läuft einmal täglich im Hintergrund.

Prüft alle aktiven Vereine auf ablaufende Lizenzen (≤ 30 Tage) und sendet
dem Superadmin eine zusammengefasste Warn-E-Mail.  Doppelte Warnungen für
denselben Verein innerhalb von 7 Tagen werden unterdrückt.

Verwendung:
    from lizenz_scheduler import start_lizenz_scheduler
    start_lizenz_scheduler()   # einmalig beim App-Start aufrufen
"""

import logging
import threading
import time
from datetime import date

_log = logging.getLogger(__name__)

# Warnschwelle: Vereine mit weniger als X Tagen bis Ablauf
WARN_TAGE = 30
# Deduplizierungs-Fenster: keine erneute Warnung für denselben Verein innerhalb X Tage
DEDUPLIZIERUNG_TAGE = 7
# Wie oft der Check läuft (Sekunden) — 24 Stunden
CHECK_INTERVALL_SEK = 86_400

_scheduler_gestartet = False
_scheduler_lock = threading.Lock()


def _superadmin_zieladressen() -> list[str]:
    """
    Ermittelt die E-Mail-Adressen für Warnungen.

    1. Alle Superadmins aus der Datenbank.
    2. Falls kein Superadmin in der DB → SUPERADMIN_EMAIL aus config als Fallback.
    """
    import config
    from database import superadmin_emails

    adressen = superadmin_emails()
    # Fallback: SUPERADMIN_EMAIL aus Umgebungsvariable
    if not adressen and config.SUPERADMIN_EMAIL:
        adressen = [config.SUPERADMIN_EMAIL]
    return adressen


def lizenz_check_ausfuehren() -> None:
    """
    Hauptlogik: Vereine ermitteln → Deduplizierung → E-Mail versenden → Protokollieren.
    """
    from database import (
        lizenz_ablauf_vereine,
        lizenz_warn_bereits_gesendet,
        lizenz_warn_protokollieren,
    )
    from email_service import send_lizenz_ablauf_warnung

    _log.info("[LizenzScheduler] Starte täglichen Lizenz-Ablauf-Check (%s)", date.today().isoformat())

    try:
        kandidaten = lizenz_ablauf_vereine(tage=WARN_TAGE)
    except Exception as exc:
        _log.error("[LizenzScheduler] Fehler beim Abrufen ablaufender Lizenzen: %s", exc)
        return

    if not kandidaten:
        _log.info("[LizenzScheduler] Keine ablaufenden Lizenzen gefunden.")
        return

    # Deduplizierung: nur Vereine, für die noch keine Warnung in den letzten 7 Tagen gesendet wurde
    neu = [v for v in kandidaten if not lizenz_warn_bereits_gesendet(v["id"], DEDUPLIZIERUNG_TAGE)]

    if not neu:
        _log.info(
            "[LizenzScheduler] %d ablaufende Lizenz(en) gefunden, aber alle bereits gewarnt "
            "(innerhalb %d Tage). Keine E-Mail versendet.",
            len(kandidaten), DEDUPLIZIERUNG_TAGE,
        )
        return

    empfaenger = _superadmin_zieladressen()
    if not empfaenger:
        _log.warning(
            "[LizenzScheduler] %d Verein(e) mit ablaufender Lizenz, aber keine "
            "Superadmin-E-Mail konfiguriert. Kein Versand möglich.", len(neu)
        )
        return

    _log.info(
        "[LizenzScheduler] %d neue Warn-E-Mail(s) nötig, Empfänger: %s",
        len(neu), empfaenger,
    )

    mindestens_eine_erfolgreich = False
    for to in empfaenger:
        ok = send_lizenz_ablauf_warnung(to, neu)
        if ok:
            _log.info("[LizenzScheduler] Warn-E-Mail erfolgreich an %s gesendet.", to)
            mindestens_eine_erfolgreich = True
        else:
            _log.warning("[LizenzScheduler] Warn-E-Mail an %s fehlgeschlagen.", to)

    # Nur in warn_log eintragen wenn mindestens eine E-Mail erfolgreich versendet wurde.
    # Andernfalls bleibt der Verein unprotokolliert und wird beim nächsten Check erneut versucht.
    if mindestens_eine_erfolgreich:
        for v in neu:
            lizenz_warn_protokollieren(v["id"])
            _log.debug("[LizenzScheduler] Verein %d (%s) in warn_log eingetragen.", v["id"], v["name"])
    else:
        _log.warning(
            "[LizenzScheduler] Kein Versand erfolgreich — warn_log bleibt unverändert. "
            "Nächster Versuch in %d Stunden.", CHECK_INTERVALL_SEK // 3600
        )


def _backup_ausfuehren() -> None:
    """
    Tägliches Datenbank-Backup (SCHRITT 9 §23–24).
    Fehler werden geloggt aber nicht weitergeworfen — Scheduler läuft weiter.
    """
    try:
        from database import db_backup_erstellen
        ok, msg = db_backup_erstellen()
        if ok:
            _log.info("[LizenzScheduler] Tägliches Backup erfolgreich: %s", msg)
        else:
            _log.warning("[LizenzScheduler] Tägliches Backup fehlgeschlagen: %s", msg)
    except Exception as exc:
        _log.error("[LizenzScheduler] Backup-Fehler: %s", exc)


def _scheduler_loop() -> None:
    """Endlosschleife: Check sofort beim Start, dann alle 24 Stunden."""
    # Kurze Startpause damit die App vollständig initialisiert ist
    time.sleep(10)
    while True:
        try:
            lizenz_check_ausfuehren()
        except Exception as exc:
            _log.exception("[LizenzScheduler] Unerwarteter Fehler im Scheduler-Loop: %s", exc)
        # Tägliches Backup nach dem Lizenz-Check (SCHRITT 9 §23–24)
        _backup_ausfuehren()
        time.sleep(CHECK_INTERVALL_SEK)


def start_lizenz_scheduler() -> None:
    """
    Startet den Hintergrund-Scheduler (einmalig — idempotent).

    Darf mehrfach aufgerufen werden; der Thread wird nur einmal gestartet
    (relevant bei Streamlit's mehrfachen Skript-Rerun-Zyklen).
    """
    global _scheduler_gestartet
    with _scheduler_lock:
        if _scheduler_gestartet:
            return
        t = threading.Thread(
            target=_scheduler_loop,
            name="LizenzAblaufScheduler",
            daemon=True,
        )
        t.start()
        _scheduler_gestartet = True
        _log.info("[LizenzScheduler] Hintergrund-Scheduler gestartet.")
