"""
Tests für Lizenz-Ablauf-Scheduler und Kandidaten-Auswahl.

Deckt ab:
- SMTP-Fehler verhindert dass warn_log beschrieben wird (retry-Sicherheit)
- Nur 'active' + 'trial' Vereine werden gewarnt (andere Status ausgeschlossen)
- Trial-Ablauf via testphase_bis, nicht lizenz_bis
- Deduplizierung unterdrückt Wiederholung innerhalb 7 Tage
"""

import os
import sys
import tempfile
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Temporäre Test-DB damit kein echter Datenbestand verändert wird
_tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmpfile.close()
os.environ["ATHLETIK_DB_PATH"] = _tmpfile.name

# Sicherstellen dass das athletik-Verzeichnis im Pfad ist
_athletik_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _athletik_dir not in sys.path:
    sys.path.insert(0, _athletik_dir)

import database as db

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _setup():
    """Frische DB für jeden Test."""
    db.init_db()


def _verein_anlegen(conn, name, lizenz_status, lizenz_bis=None, testphase_bis=None,
                    aktiv=1, gesperrt=0):
    cur = conn.execute(
        "INSERT INTO vereine (name, aktiv, lizenz_status, lizenztyp, lizenz_bis, testphase_bis, gesperrt) "
        "VALUES (?, ?, ?, 'BASIC', ?, ?, ?)",
        (name, aktiv, lizenz_status, lizenz_bis, testphase_bis, gesperrt),
    )
    return cur.lastrowid


# ── Tests: Kandidaten-Auswahl ─────────────────────────────────────────────────

def test_active_lizenz_innerhalb_30_tage_wird_erkannt():
    """Active-Verein mit lizenz_bis in 15 Tagen soll gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=15)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Active", "active", lizenz_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Active" in namen, f"Erwartet TestVerein-Active in {namen}"
    eintrag = next(v for v in kandidaten if v["name"] == "TestVerein-Active")
    assert 14 <= eintrag["tage_bis_ablauf"] <= 15


def test_trial_ablauf_via_testphase_bis_erkannt():
    """Trial-Verein mit testphase_bis in 7 Tagen soll erkannt werden (lizenz_bis ignoriert)."""
    _setup()
    ablauf = (date.today() + timedelta(days=7)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Trial", "trial", testphase_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Trial" in namen, f"Erwartet TestVerein-Trial in {namen}"
    eintrag = next(v for v in kandidaten if v["name"] == "TestVerein-Trial")
    assert 6 <= eintrag["tage_bis_ablauf"] <= 7


def test_expired_verein_wird_nicht_gewarnt():
    """Bereits abgelaufene (expired) Vereine sollen NICHT in der Kandidatenliste erscheinen."""
    _setup()
    ablauf = (date.today() + timedelta(days=15)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Expired", "expired", lizenz_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Expired" not in namen, "Expired-Verein darf nicht gewarnt werden"


def test_suspended_verein_wird_nicht_gewarnt():
    """Gesperrte (suspended) Vereine sollen nicht gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Suspended", "suspended", lizenz_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Suspended" not in namen, "Suspended-Verein darf nicht gewarnt werden"


def test_cancelled_verein_wird_nicht_gewarnt():
    """Gekündigte (cancelled) Vereine sollen nicht gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=5)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Cancelled", "cancelled", lizenz_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Cancelled" not in namen, "Cancelled-Verein darf nicht gewarnt werden"


def test_deaktivierter_verein_wird_nicht_gewarnt():
    """Inaktiver (aktiv=0) Verein soll nicht gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Inaktiv", "active", lizenz_bis=ablauf, aktiv=0)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Inaktiv" not in namen


def test_gesperrter_verein_wird_nicht_gewarnt():
    """Gesperrter (gesperrt=1) Verein soll nicht gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Gesperrt", "active", lizenz_bis=ablauf, gesperrt=1)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Gesperrt" not in namen


def test_ablauf_nach_30_tagen_nicht_gewarnt():
    """Verein dessen Lizenz erst in 45 Tagen abläuft soll noch nicht gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=45)).isoformat()
    with db.get_conn() as conn:
        _verein_anlegen(conn, "TestVerein-Fernablauf", "active", lizenz_bis=ablauf)

    kandidaten = db.lizenz_ablauf_vereine(30)
    namen = [v["name"] for v in kandidaten]
    assert "TestVerein-Fernablauf" not in namen


# ── Tests: Deduplizierung ─────────────────────────────────────────────────────

def test_deduplizierung_innerhalb_7_tage():
    """Nach Protokollierung soll derselbe Verein nicht nochmal gewarnt werden."""
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        vid = _verein_anlegen(conn, "TestVerein-Dedup", "active", lizenz_bis=ablauf)

    assert not db.lizenz_warn_bereits_gesendet(vid, 7), "Noch kein Eintrag erwartet"
    db.lizenz_warn_protokollieren(vid)
    assert db.lizenz_warn_bereits_gesendet(vid, 7), "Nach Protokollierung erwartet"


def test_deduplizierung_unbekannter_verein_false():
    """Für einen nicht protokollierten Verein soll bereits_gesendet False sein."""
    _setup()
    assert not db.lizenz_warn_bereits_gesendet(99999, 7)


# ── Tests: SMTP-Fehler verhindert warn_log-Eintrag ───────────────────────────

def test_smtp_fehler_verhindert_warn_log_eintrag():
    """
    Wenn ALLE E-Mail-Sendes fehlschlagen, darf kein warn_log-Eintrag angelegt werden
    (damit der nächste Check es erneut versucht).
    """
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        vid = _verein_anlegen(conn, "TestVerein-SMTPFail", "active", lizenz_bis=ablauf)

    # Superadmin-Email patchen
    with patch("database.superadmin_emails", return_value=["admin@example.com"]):
        # send_lizenz_ablauf_warnung gibt False zurück (SMTP-Fehler)
        with patch("email_service.send_lizenz_ablauf_warnung", return_value=False):
            from lizenz_scheduler import lizenz_check_ausfuehren
            lizenz_check_ausfuehren()

    # warn_log darf KEINEN Eintrag haben
    assert not db.lizenz_warn_bereits_gesendet(vid, 7), \
        "Nach SMTP-Fehler darf kein warn_log-Eintrag vorhanden sein"


def test_smtp_erfolg_schreibt_warn_log_eintrag():
    """
    Wenn mindestens eine E-Mail erfolgreich versendet wurde, MUSS ein warn_log-Eintrag
    angelegt werden (damit innerhalb von 7 Tagen nicht erneut gewarnt wird).
    """
    _setup()
    ablauf = (date.today() + timedelta(days=10)).isoformat()
    with db.get_conn() as conn:
        vid = _verein_anlegen(conn, "TestVerein-SMTPOk", "active", lizenz_bis=ablauf)

    with patch("database.superadmin_emails", return_value=["admin@example.com"]):
        with patch("email_service.send_lizenz_ablauf_warnung", return_value=True):
            from lizenz_scheduler import lizenz_check_ausfuehren
            lizenz_check_ausfuehren()

    assert db.lizenz_warn_bereits_gesendet(vid, 7), \
        "Nach erfolgreichem Versand muss warn_log-Eintrag vorhanden sein"


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_active_lizenz_innerhalb_30_tage_wird_erkannt,
        test_trial_ablauf_via_testphase_bis_erkannt,
        test_expired_verein_wird_nicht_gewarnt,
        test_suspended_verein_wird_nicht_gewarnt,
        test_cancelled_verein_wird_nicht_gewarnt,
        test_deaktivierter_verein_wird_nicht_gewarnt,
        test_gesperrter_verein_wird_nicht_gewarnt,
        test_ablauf_nach_30_tagen_nicht_gewarnt,
        test_deduplizierung_innerhalb_7_tage,
        test_deduplizierung_unbekannter_verein_false,
        test_smtp_fehler_verhindert_warn_log_eintrag,
        test_smtp_erfolg_schreibt_warn_log_eintrag,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1

    print(f"\n{'PASSED' if not failed else 'FAILED'}: {len(tests)-failed}/{len(tests)} Tests bestanden")
    sys.exit(1 if failed else 0)
