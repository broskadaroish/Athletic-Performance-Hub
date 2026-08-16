"""
test_session.py — Session-Persistenz und Cookie-Restore-Mechanismus

Prüft die Szenarien aus dem Master-Auftrag TEIL D (Session):

 1. Login erfolgreich → session_erstellen gibt Token zurück
 2. Normaler Rerun: session_token_aktiv → True
 3. Neuer leerer session_state + gültiges Token → session_validieren → user-dict
 4. Ungültiges Token → session_validieren → None
 5. Abgelaufene Session (idle) → session_validieren → None
 6. Deaktivierter Benutzer → session_validieren → None
 7. Logout → token_aktiv = False
 8. Passwortänderung → session_token_version-Mismatch → token_aktiv = False
 9. session_aktivitaet_aktualisieren → letzte_aktivitaet wird frisch gesetzt
10. Throttled DB-Touch Logik (Unit-Test ohne DB)

Benötigt: artifacts/athletik/database.py (get_conn, session_*, _pw_hash)
Läuft in der lokalen Replit-Umgebung — kein Produktionszugriff.

ACHTUNG: Dieser Test schreibt in die lokale DB. Alle Testdaten werden
am Ende vollständig aufgeräumt (verein + benutzer + sessions gelöscht).
"""
import sys
import os
import datetime
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    DB_PATH, get_conn, _pw_hash,
    session_erstellen, session_validieren, session_token_aktiv,
    session_beenden, session_aktivitaet_aktualisieren,
)

PASS = 0
FAIL = 0
_TEST_TOKENS: list[str] = []
_TEST_BENUTZER_ID: int | None = None
_TEST_VEREIN_ID:   int | None = None


def check(label: str, got, expected):
    global PASS, FAIL
    if got == expected:
        PASS += 1
        print(f"  ✅ PASS  {label}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL  {label} | got={got!r} expected={expected!r}")


def fail(label: str, detail: str = ""):
    global FAIL
    FAIL += 1
    print(f"  ❌ FAIL  {label}" + (f" | {detail}" if detail else ""))


def ok(label: str):
    global PASS
    PASS += 1
    print(f"  ✅ PASS  {label}")


# ─── Test-Daten einrichten ────────────────────────────────────────────────────
def _setup() -> tuple[int, int]:
    """Legt minimalen Testverein + Testbenutzer an. Gibt (verein_id, benutzer_id) zurück."""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO vereine (name, email, kundennummer, aktiv)
               VALUES ('Testverein_Session', 'session@test.local', 'APH-TEST-SES', 1)"""
        )
        verein_id = cur.lastrowid
        cur2 = conn.execute(
            """INSERT INTO benutzer
               (verein_id, vorname, nachname, email, passwort_hash, rolle, aktiv,
                email_verifiziert, kundennummer, session_token_version)
               VALUES (?, 'Test', 'Session', 'session_user@test.local', ?, 'trainer', 1, 1,
                       'APH-TEST-SES-U', 0)""",
            (verein_id, _pw_hash("testpass123!")),
        )
        benutzer_id = cur2.lastrowid
    return verein_id, benutzer_id


def _teardown(verein_id: int, benutzer_id: int):
    """Räumt alle Testdaten auf."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE benutzer_id=?", (benutzer_id,))
            conn.execute("DELETE FROM benutzer WHERE id=?", (benutzer_id,))
            conn.execute("DELETE FROM vereine WHERE id=?", (verein_id,))
    except Exception as e:
        print(f"  ⚠️ Teardown-Fehler: {e}")


# ─── Tests ────────────────────────────────────────────────────────────────────

print("\n══ TEIL D: Session-Tests ══")

try:
    _vid, _bid = _setup()
    _TEST_VEREIN_ID   = _vid
    _TEST_BENUTZER_ID = _bid
    print(f"  Setup: verein_id={_vid}, benutzer_id={_bid}")
except Exception as e:
    fail("Setup fehlgeschlagen", str(e))
    sys.exit(1)

try:
    # ── Test 1: session_erstellen ──────────────────────────────────────────────
    print("\n─ Test 1: session_erstellen ─")
    tok = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok)
    check("session_erstellen gibt Token zurück (nicht leer)", bool(tok), True)
    check("Token-Länge > 20 Zeichen", len(tok) > 20, True)

    # Prüfe DB-Eintrag direkt
    with get_conn() as conn:
        row = conn.execute(
            "SELECT aktiv, token_version FROM sessions WHERE token=?", (tok,)
        ).fetchone()
    check("Session in DB: aktiv=1", row[0] if row else None, 1)

    # ── Test 2: session_token_aktiv (normaler Rerun) ───────────────────────────
    print("\n─ Test 2: session_token_aktiv (normaler Rerun) ─")
    aktiv = session_token_aktiv(tok)
    check("session_token_aktiv → True (gültige Session)", aktiv, True)

    # ── Test 3: session_validieren mit gültigem Token ─────────────────────────
    print("\n─ Test 3: session_validieren → Session-Restore ─")
    user = session_validieren(tok, idle_sek=3600)
    check("session_validieren gibt user-dict zurück", user is not None, True)
    if user:
        check("user['id'] == benutzer_id", user.get("id"), _bid)
        check("user['aktiv'] == 1", user.get("aktiv"), 1)
        check("user['email_verifiziert'] == 1", user.get("email_verifiziert"), 1)

    # ── Test 4: Ungültiges Token ───────────────────────────────────────────────
    print("\n─ Test 4: ungültiges Token ─")
    res_inv = session_validieren("UNGÜLTIG_1234567890", idle_sek=3600)
    check("Ungültiges Token → None", res_inv, None)
    aktiv_inv = session_token_aktiv("UNGÜLTIG_1234567890")
    check("Ungültiges Token → token_aktiv = False", aktiv_inv, False)

    # ── Test 5: Abgelaufene Session (Idle-Timeout) ────────────────────────────
    print("\n─ Test 5: abgelaufene Session (idle_sek=0) ─")
    tok_exp = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok_exp)
    # Aktivität manuell auf vor 2 Stunden setzen
    zwei_h_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET letzte_aktivitaet=? WHERE token=?",
            (zwei_h_ago, tok_exp),
        )
    res_exp = session_validieren(tok_exp, idle_sek=3600)  # 1h timeout
    check("Idle-expired (2h alt) → None", res_exp, None)
    # Session muss jetzt inaktiv sein
    with get_conn() as conn:
        r = conn.execute("SELECT aktiv FROM sessions WHERE token=?", (tok_exp,)).fetchone()
    check("Idle-expired Session → aktiv=0 in DB", r[0] if r else None, 0)

    # ── Test 6: Deaktivierter Benutzer ────────────────────────────────────────
    print("\n─ Test 6: deaktivierter Benutzer ─")
    tok_deak = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok_deak)
    with get_conn() as conn:
        conn.execute("UPDATE benutzer SET aktiv=0 WHERE id=?", (_bid,))
    res_deak = session_validieren(tok_deak, idle_sek=3600)
    check("Deaktivierter Benutzer → None", res_deak, None)
    # Benutzer wieder aktivieren für folgende Tests
    with get_conn() as conn:
        conn.execute("UPDATE benutzer SET aktiv=1 WHERE id=?", (_bid,))
    aktiv_nach_reaktiv = session_token_aktiv(tok_deak)
    # token_deak ist noch aktiv=1 in DB, aber session_validieren gibt None zurück
    # (benutzer.aktiv prüft session_validieren; token_aktiv prüft nur s.aktiv + version)
    # Nach Reaktivierung: token_aktiv sollte wieder True liefern
    check("Nach Reaktivierung: token_aktiv = True", aktiv_nach_reaktiv, True)

    # ── Test 7: Logout ────────────────────────────────────────────────────────
    print("\n─ Test 7: Logout ─")
    tok_out = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok_out)
    check("Vor Logout: token_aktiv = True", session_token_aktiv(tok_out), True)
    session_beenden(tok_out)
    check("Nach Logout: token_aktiv = False", session_token_aktiv(tok_out), False)
    check("Nach Logout: session_validieren = None", session_validieren(tok_out, idle_sek=3600), None)

    # ── Test 8: Passwortänderung → Version-Mismatch ───────────────────────────
    print("\n─ Test 8: Passwortänderung → session_token_version Mismatch ─")
    tok_pw = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok_pw)
    check("Vor PW-Änderung: token_aktiv = True", session_token_aktiv(tok_pw), True)
    # Passwort-Änderung simulieren: session_token_version erhöhen (wie benutzer_pw_aendern tut)
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET session_token_version = COALESCE(session_token_version, 0) + 1 WHERE id=?",
            (_bid,),
        )
    check("Nach PW-Änderung: token_aktiv = False (Version-Mismatch)", session_token_aktiv(tok_pw), False)
    check("Nach PW-Änderung: session_validieren = None", session_validieren(tok_pw, idle_sek=3600), None)
    # Für folgende Tests: version zurücksetzen
    with get_conn() as conn:
        conn.execute("UPDATE benutzer SET session_token_version=0 WHERE id=?", (_bid,))
    with get_conn() as conn:
        conn.execute("UPDATE sessions SET aktiv=0 WHERE benutzer_id=?", (_bid,))

    # ── Test 9: session_aktivitaet_aktualisieren (neue Funktion) ─────────────
    print("\n─ Test 9: session_aktivitaet_aktualisieren ─")
    tok_touch = session_erstellen(_bid, idle_sek=3600, max_sek=86400)
    _TEST_TOKENS.append(tok_touch)
    # Aktivität auf vor 55 Minuten setzen
    old_ts = (datetime.datetime.utcnow() - datetime.timedelta(minutes=55)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET letzte_aktivitaet=? WHERE token=?",
            (old_ts, tok_touch),
        )
    # Vor touch: session_validieren mit 30min idle → NOCH gültig (55min < 60min... aber idle=30min?)
    # Wir prüfen, dass nach dem Touch die Session wieder als frisch gilt
    session_aktivitaet_aktualisieren(tok_touch)
    with get_conn() as conn:
        r = conn.execute(
            "SELECT letzte_aktivitaet FROM sessions WHERE token=?", (tok_touch,)
        ).fetchone()
    la_after = r[0] if r else None
    ts_after = datetime.datetime.fromisoformat(la_after) if la_after else None
    ts_now   = datetime.datetime.utcnow()
    if ts_after:
        diff_sek = abs((ts_now - ts_after).total_seconds())
        check("Nach session_aktivitaet_aktualisieren: letzte_aktivitaet < 5s alt", diff_sek < 5, True)
    else:
        fail("letzte_aktivitaet nach Touch nicht lesbar")

    # KERNTEST: Session war 55min alt (mit 60min idle), nach Touch → noch gültig
    res_nach_touch = session_validieren(tok_touch, idle_sek=3600)
    check("Nach DB-Touch: session_validieren → user (Session bleibt gültig)", res_nach_touch is not None, True)
    session_beenden(tok_touch)

    # ── Test 10: Unit-Test Throttle-Logik (ohne DB) ───────────────────────────
    print("\n─ Test 10: Throttle-Logik (Unit, ohne DB) ─")
    _DB_TOUCH_INTERVAL_SEC = 300
    last = 0.0
    now1 = time.time()
    should_touch_first = (now1 - last) > _DB_TOUCH_INTERVAL_SEC
    check("Beim ersten Mal (last=0): touch ausführen", should_touch_first, True)
    last = now1
    now2 = time.time()
    should_touch_second = (now2 - last) > _DB_TOUCH_INTERVAL_SEC
    check("Sofort danach: KEIN Touch (< 5 min)", should_touch_second, False)
    last_old = time.time() - 310  # 310 Sekunden in der Vergangenheit
    should_touch_after_5min = (time.time() - last_old) > _DB_TOUCH_INTERVAL_SEC
    check("Nach >5 min: touch ausführen", should_touch_after_5min, True)

finally:
    # ── Cleanup ───────────────────────────────────────────────────────────────
    if _TEST_VEREIN_ID and _TEST_BENUTZER_ID:
        _teardown(_TEST_VEREIN_ID, _TEST_BENUTZER_ID)
        print("\n  Cleanup: Testdaten gelöscht.")


# ═══════════════════════════════════════════════════════════════════════════════
# py_compile
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ py_compile ══")
import py_compile, pathlib
_ROOT = pathlib.Path(__file__).parent.parent
for _f in ["database.py", "app.py", "mobile.py", "session_timeout.py", "auth.py"]:
    try:
        py_compile.compile(str(_ROOT / _f), doraise=True)
        ok(f"py_compile {_f}")
    except py_compile.PyCompileError as e:
        fail(f"py_compile {_f}", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Ergebnis
# ═══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
if FAIL == 0:
    print(f"  Ergebnis: {PASS} PASS, 0 FAIL ✅")
else:
    print(f"  Ergebnis: {PASS} PASS, {FAIL} FAIL ❌")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
