"""
Tests für den Brute-Force-Schutz beim Login.
Alle Zeitvergleiche laufen vollständig in SQLite (UTC) — kein Python-datetime-Vergleich.
Deckt ab:
  - Serielle Fehlversuche führen zur Sperre nach MAX_LOGIN_VERSUCHE
  - Parallele Fehlversuche führen ebenfalls zur Sperre (atomarer SQL-UPDATE, kein Race)
  - Korrekte Zurücksetzung nach erfolgreichem Login (via auth.login())
  - login() gibt {'gesperrt': True, ...} zurück wenn das Konto gesperrt ist
  - Automatische Entsperrung nach Ablauf der Sperrzeit (timezone-neutral via SQLite)
"""

import os
import sys
import tempfile
import threading

# Athletik-Paket im Pfad
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Temporäre Test-Datenbank anlegen (muss vor dem Import von database gesetzt werden)
_tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmpfile.close()
os.environ["ATHLETIK_DB_PATH"] = _tmpfile.name
# Kleines Limit damit Tests schnell laufen
os.environ["MAX_LOGIN_VERSUCHE"] = "5"
os.environ["LOGIN_SPERRE_MINUTEN"] = "15"

import database
import auth
from config import MAX_LOGIN_VERSUCHE as MAX, LOGIN_SPERRE_MINUTEN as SPERRE_MIN

# DB-Schema sicherstellen
database.init_db()

_COUNTER = 0  # eindeutige E-Mails pro Test


def _unique_email() -> str:
    global _COUNTER
    _COUNTER += 1
    return f"testuser{_COUNTER}@brute.local"


def _setup_user(passwort: str = "richtig123") -> tuple[str, int]:
    """Legt einen frischen Testbenutzer an; gibt (email, id) zurück."""
    email = _unique_email()
    pw_hash = database._pw_hash(passwort)
    with database.get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO benutzer (email, passwort_hash, rolle, aktiv) VALUES (?,?,?,1)",
            (email, pw_hash, "Trainer"),
        )
        bid = cur.lastrowid
    return email, bid


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_seriell_sperre():
    """Nach MAX Fehlversuchen (via auth.login()) wird das Konto gesperrt."""
    email, _ = _setup_user()

    # MAX - 1 Fehlversuche → noch nicht gesperrt
    for _ in range(MAX - 1):
        result = auth.login(email, "falsch")
        assert result is None, "Kein gesperrtes-Dict erwartet vor MAX Versuchen"

    status = database.benutzer_sperre_pruefen(email)
    assert not status["gesperrt"], f"Nach {MAX-1} Versuchen noch keine Sperre erwartet"

    # Letzter (MAX.) Fehlversuch → Sperre
    result = auth.login(email, "falsch")
    assert isinstance(result, dict) and result.get("gesperrt"), (
        "login() muss {'gesperrt': True, ...} zurückgeben"
    )
    assert result.get("verbleibend_sek", 0) > 0, "verbleibend_sek muss > 0 sein"

    status = database.benutzer_sperre_pruefen(email)
    assert status["gesperrt"], "DB muss Sperre widerspiegeln"

    print("✓ test_seriell_sperre")


def test_parallel_sperre():
    """5 gleichzeitige Fehlversuche sperren das Konto (atomic UPDATE, kein Race)."""
    email, bid = _setup_user()
    errors: list[Exception] = []

    def fehlversuch():
        try:
            database.benutzer_login_fehlversuch(bid, MAX, SPERRE_MIN)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=fehlversuch) for _ in range(MAX)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Ausnahmen in Threads: {errors}"

    status = database.benutzer_sperre_pruefen(email)
    assert status["gesperrt"], (
        f"Konto muss nach {MAX} parallelen Fehlversuchen gesperrt sein; "
        f"login_versuche={status['login_versuche']}"
    )
    assert status["verbleibend_sek"] > 0

    print("✓ test_parallel_sperre")


def test_reset_nach_erfolg():
    """Nach erfolgreichem Login (auth.login()) werden Zähler und Sperre zurückgesetzt."""
    passwort = "richtig123"
    email, _ = _setup_user(passwort)

    # Einige Fehlversuche (nicht genug für Sperre)
    for _ in range(MAX - 2):
        auth.login(email, "falsch")

    # Erfolgreicher Login
    user = auth.login(email, passwort)
    assert isinstance(user, dict) and not user.get("gesperrt"), (
        "Erfolgreicher Login muss User-Dict ohne 'gesperrt' zurückgeben"
    )

    status = database.benutzer_sperre_pruefen(email)
    assert status["login_versuche"] == 0, "Zähler muss nach Erfolg auf 0 stehen"
    assert not status["gesperrt"]

    print("✓ test_reset_nach_erfolg")


def test_gesperrtes_konto_blockiert_auch_richtiges_passwort():
    """Auch mit richtigem Passwort kommt man auf ein gesperrtes Konto nicht rein."""
    passwort = "richtig123"
    email, _ = _setup_user(passwort)

    for _ in range(MAX):
        auth.login(email, "falsch")

    result = auth.login(email, passwort)
    assert isinstance(result, dict) and result.get("gesperrt"), (
        "Gesperrtes Konto darf nicht mit richtigem Passwort einloggen"
    )

    print("✓ test_gesperrtes_konto_blockiert_auch_richtiges_passwort")


def test_automatische_entsperrung():
    """Nach Ablauf der Sperrzeit wird das Konto automatisch entsperrt (SQLite-UTC, timezone-neutral)."""
    email, bid = _setup_user()

    # Sperre manuell in der Vergangenheit setzen (SQLite UTC, 2 Sekunden abgelaufen)
    with database.get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET login_versuche=?, gesperrt_bis=datetime('now', '-2 seconds') WHERE id=?",
            (MAX, bid),
        )

    status = database.benutzer_sperre_pruefen(email)
    assert not status["gesperrt"], "Abgelaufene Sperre muss automatisch aufgehoben werden"
    assert status["login_versuche"] == 0, "Zähler muss nach Entsperrung zurückgesetzt sein"

    # Jetzt muss Login mit richtigem Passwort wieder klappen
    user = auth.login(email, "richtig123")
    assert isinstance(user, dict) and not user.get("gesperrt"), (
        "Login nach Entsperrung muss klappen"
    )

    print("✓ test_automatische_entsperrung")


def test_unbekannte_email_kein_fehler():
    """Unbekannte E-Mail gibt None zurück, kein Crash."""
    result = auth.login("ghost@nirgends.local", "egal")
    assert result is None, "Unbekannte E-Mail muss None liefern"

    status = database.benutzer_sperre_pruefen("ghost@nirgends.local")
    assert status == {"gesperrt": False, "verbleibend_sek": 0, "benutzer_id": None, "login_versuche": 0}

    print("✓ test_unbekannte_email_kein_fehler")


def test_stale_reset_loescht_keine_frische_sperre():
    """Race: abgelaufene Sperre + simultane Fehlversuche → neue Sperre bleibt erhalten.

    Szenario:
    1. Konto hat eine bereits abgelaufene Sperre (gesperrt_bis in der Vergangenheit).
    2. Gleichzeitig werden MAX Fehlversuche ausgeführt, die eine neue Sperre setzen.
    3. Das bedingte Reset-UPDATE in benutzer_sperre_pruefen darf die neue Sperre NICHT löschen.
    """
    email, bid = _setup_user()

    # Abgelaufene Sperre manuell setzen
    with database.get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET login_versuche=0, gesperrt_bis=datetime('now', '-2 seconds') WHERE id=?",
            (bid,),
        )

    errors: list[Exception] = []
    results: list[dict | None] = []
    lock = threading.Lock()

    def fehlversuch():
        try:
            database.benutzer_login_fehlversuch(bid, MAX, SPERRE_MIN)
            # Danach Sperr-Status lesen und sammeln
            s = database.benutzer_sperre_pruefen(email)
            with lock:
                results.append(s)
        except Exception as exc:
            with lock:
                errors.append(exc)

    # MAX parallele Fehlversuche während die abgelaufene Sperre noch im DB steht
    threads = [threading.Thread(target=fehlversuch) for _ in range(MAX)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread-Ausnahmen: {errors}"

    # Abschließender Status: Konto muss nun gesperrt sein (MAX neue Fehlversuche)
    final = database.benutzer_sperre_pruefen(email)
    # Das bedingte UPDATE schützt die neue Sperre; login_versuche >= MAX
    assert final["gesperrt"] or final["login_versuche"] >= MAX, (
        f"Neue Sperre darf nicht durch stale reset gelöscht worden sein; "
        f"gesperrt={final['gesperrt']}, login_versuche={final['login_versuche']}"
    )

    print("✓ test_stale_reset_loescht_keine_frische_sperre")


if __name__ == "__main__":
    try:
        test_seriell_sperre()
        test_parallel_sperre()
        test_reset_nach_erfolg()
        test_gesperrtes_konto_blockiert_auch_richtiges_passwort()
        test_automatische_entsperrung()
        test_unbekannte_email_kein_fehler()
        test_stale_reset_loescht_keine_frische_sperre()
        print("\n✅ Alle Tests bestanden.")
    finally:
        try:
            os.unlink(_tmpfile.name)
        except Exception:
            pass
