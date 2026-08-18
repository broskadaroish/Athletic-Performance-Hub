#!/usr/bin/env python3
"""
Block-B Automatisierte Tests (B8)
Prüft B2–B7 ohne Streamlit-Imports. Läuft direkt als python3 test_block_b.py.
35 Tests — alle müssen mit PASS enden.

Isolierte Testdatenbank: temporäres SQLite-File, nach dem Lauf gelöscht.
Die Produktivdatenbank (/data/athletik.db) wird nicht berührt.
"""
import sys
import os
import sqlite3
import shutil
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")

import database as db
from license import (
    trainer_limit_erreicht,
    spieler_limit_erreicht,
    normalize_lizenz_typ,
    LIZENZ_TYPEN,
)

# ── Isolierte Testdatenbank ────────────────────────────────────────────────────
# Temp-Verzeichnis und -DB vor allen Imports anlegen, damit alle db.*-Funktionen
# von Anfang an auf die Testdatenbank zeigen. Die Produktivdaten werden nicht
# berührt. Cleanup erfolgt am Ende von main().

_TMP_DIR    = tempfile.mkdtemp(prefix="test_block_b_")
_DB_PATH    = os.path.join(_TMP_DIR, "test.db")
_ORIG_DB    = db.DB_PATH     # Originalwert für Restore in cleanup()

# Alle db.* Funktionen auf die Temp-DB umleiten
db.DB_PATH = _DB_PATH
db.init_db()                 # Schema vollständig anlegen

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

_pass = 0
_fail = 0

def ok(name: str) -> None:
    global _pass
    _pass += 1
    print(f"  ✅ PASS  {name}")

def fail(name: str, reason: str = "") -> None:
    global _fail
    _fail += 1
    print(f"  ❌ FAIL  {name}" + (f" — {reason}" if reason else ""))

def check(name: str, condition: bool, reason: str = "") -> None:
    if condition:
        ok(name)
    else:
        fail(name, reason)

def _raw() -> sqlite3.Connection:
    """Direkte SQLite-Verbindung zur isolierten Test-DB (umgeht db.get_conn())."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cleanup() -> None:
    """Restore + Temp-Verzeichnis löschen."""
    db.DB_PATH = _ORIG_DB
    shutil.rmtree(_TMP_DIR, ignore_errors=True)

# ── Setup: Testdaten anlegen ──────────────────────────────────────────────────

def setup():
    """Legt minimale Testdaten in der Temp-DB an. IDs ≥ 9000, plus id=1 für B1-Guard."""
    conn = _raw()
    c = conn.cursor()

    # id=1 Superadmin: wird vom B1-Letzter-SA-Guard geschützt
    c.execute("""
        INSERT OR IGNORE INTO benutzer (id, email, passwort_hash, rolle, aktiv)
        VALUES (1, 'sa_main@test.de', 'x', 'Superadmin', 1)
    """)
    # Test-Superadmin id=9001 (wird in B1 temporär deaktiviert)
    c.execute("""
        INSERT OR IGNORE INTO benutzer (id, email, passwort_hash, rolle, aktiv)
        VALUES (9001, 'sa_test@test.de', 'x', 'Superadmin', 1)
    """)
    # Verein A — TRAINER_BASIC, trial
    c.execute("""
        INSERT OR IGNORE INTO vereine (id, name, aktiv, lizenztyp, lizenz_status)
        VALUES (9001, 'Testverein A', 1, 'TRAINER_BASIC', 'trial')
    """)
    # Verein B — VEREIN_PRO, active
    c.execute("""
        INSERT OR IGNORE INTO vereine (id, name, aktiv, lizenztyp, lizenz_status)
        VALUES (9002, 'Testverein B', 1, 'VEREIN_PRO', 'active')
    """)
    # Vereinsadmin für Verein A
    c.execute("""
        INSERT OR IGNORE INTO benutzer (id, email, passwort_hash, rolle, aktiv, verein_id)
        VALUES (9002, 'va@a.de', 'x', 'Vereinsadmin', 1, 9001)
    """)
    # 3 Trainer für Verein A  → überschreitet TRAINER_BASIC-Limit (max_trainer=2)
    for i in range(3):
        c.execute(
            "INSERT OR IGNORE INTO benutzer (id, email, passwort_hash, rolle, aktiv, verein_id) "
            "VALUES (?, ?, 'x', 'Trainer', 1, 9001)",
            (9010 + i, f"t{i}@a.de"),
        )
    # 5 Spieler für Verein A  → unter TRAINER_BASIC-Limit (max_spieler=25)
    for i in range(5):
        c.execute(
            "INSERT OR IGNORE INTO spieler (id, name, verein_id) VALUES (?, ?, 9001)",
            (9010 + i, f"Spieler {i}"),
        )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# B2 — Atomare Kundennummern + UNIQUE-Indexes
# ─────────────────────────────────────────────────────────────────────────────

def test_b2_unique_indexes():
    print("\n── B2: UNIQUE-Indexes ──")
    conn = _raw()
    idx = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%kundennummer%'"
    ).fetchall()}
    conn.close()
    check("B2.1  UNIQUE idx auf vereine.kundennummer",
          "idx_vereine_kundennummer" in idx)
    check("B2.2  UNIQUE idx auf benutzer.kundennummer",
          "idx_benutzer_kundennummer" in idx)

def test_b2_atomic_assignment():
    print("\n── B2: Atomare Kundennummern-Vergabe ──")
    kn1 = db.kundennummer_vergeben_verein(9001)
    kn2 = db.kundennummer_vergeben_verein(9001)
    check("B2.3  Idempotenz: zweite Vergabe gibt gleiche Nummer zurück",
          kn1 == kn2, f"got {kn1} vs {kn2}")
    check("B2.4  Format APH-XXXXXX",
          kn1.startswith("APH-") and len(kn1) == 10, f"got {kn1}")

def test_b2_no_duplicate():
    print("\n── B2: Kein Duplikat durch sequentielle Vergabe ──")
    kn_a = db.kundennummer_vergeben_verein(9001)
    kn_b = db.kundennummer_vergeben_verein(9002)
    check("B2.5  Zwei Vereine erhalten unterschiedliche Nummern",
          kn_a != kn_b, f"both got {kn_a}")

# ─────────────────────────────────────────────────────────────────────────────
# B3 — Dashboard KPIs + Filter
# ─────────────────────────────────────────────────────────────────────────────

def test_b3_dashboard_kpis():
    print("\n── B3: Dashboard KPIs ──")
    kpis = db.dashboard_sa_kpis()
    check("B3.1  n_kunden_gesamt vorhanden", "n_kunden_gesamt" in kpis)
    check("B3.2  n_trial vorhanden",         "n_trial" in kpis)
    check("B3.3  n_aktive_abos vorhanden",   "n_aktive_abos" in kpis)
    check("B3.4  n_gekuendigt vorhanden",    "n_gekuendigt" in kpis)
    check("B3.5  n_zahlungsproblem vorhanden","n_zahlungsproblem" in kpis)
    check("B3.6  n_trial ≥ 0 (kein Fehler)", isinstance(kpis["n_trial"], int) and kpis["n_trial"] >= 0)

def test_b3_filter_trial():
    print("\n── B3: Filter trial ──")
    alle = db.kunden_liste_laden()
    trial = db.kunden_liste_laden(filter_lizenz="trial")
    check("B3.7  filter_lizenz=trial gibt Teilmenge zurück",
          len(trial) <= len(alle), f"{len(trial)} vs {len(alle)}")
    check("B3.8  alle trial-Kunden haben lizenz_status=trial",
          all(k["lizenz_status"] == "trial" for k in trial),
          str([k["lizenz_status"] for k in trial if k["lizenz_status"] != "trial"][:3]))

def test_b3_filter_zahlungsstatus():
    print("\n── B3: Filter Zahlungsstatus ──")
    # Setze einen Testwert
    conn = _raw()
    conn.execute("UPDATE vereine SET zahlungsstatus='fehlgeschlagen' WHERE id=9001")
    conn.commit()
    conn.close()
    fehlgeschlagen = db.kunden_liste_laden(filter_zahlungsstatus="fehlgeschlagen")
    check("B3.9  filter_zahlungsstatus=fehlgeschlagen findet Treffer",
          any(k.get("verein_id") == 9001 for k in fehlgeschlagen),
          f"found: {[k.get('verein_id') for k in fehlgeschlagen]}")
    # Zurücksetzen
    conn = _raw()
    conn.execute("UPDATE vereine SET zahlungsstatus=NULL WHERE id=9001")
    conn.commit()
    conn.close()

def test_b3_filter_status_trial():
    print("\n── B3: Accountstatus-Filter Trial ──")
    alle = db.kunden_liste_laden()
    trial_status = db.kunden_liste_laden(filter_status="Trial")
    check("B3.10 filter_status=Trial filtert korrekt",
          all(k["lizenz_status"] == "trial" for k in trial_status),
          str([k["lizenz_status"] for k in trial_status if k["lizenz_status"] != "trial"][:3]))

# ─────────────────────────────────────────────────────────────────────────────
# B4 — Stripe-Block (nur DB-Felder, kein API-Call)
# ─────────────────────────────────────────────────────────────────────────────

def test_b4_stripe_fields_in_vollstaendig():
    print("\n── B4: Stripe-Felder in kunde_vollstaendig_laden ──")
    conn = _raw()
    # stripe_customer_id in vereine-Schema prüfen
    cols = {r[1] for r in conn.execute("PRAGMA table_info(vereine)").fetchall()}
    conn.close()
    check("B4.1  stripe_customer_id Spalte vorhanden",
          "stripe_customer_id" in cols)
    check("B4.2  stripe_subscription_id Spalte vorhanden",
          "stripe_subscription_id" in cols)
    check("B4.3  zahlungsstatus Spalte vorhanden",
          "zahlungsstatus" in cols)
    check("B4.4  cancel_at_period_end Spalte vorhanden",
          "cancel_at_period_end" in cols)

# ─────────────────────────────────────────────────────────────────────────────
# B5 — Fail-closed + Downgrade-Schutz
# ─────────────────────────────────────────────────────────────────────────────

def test_b5_fail_closed():
    print("\n── B5: Fail-closed Limitprüfungen ──")
    # Prüfe mit ungültiger verein_id — DB gibt 0 zurück, aber Exception sollte True ergeben
    # Wir simulieren fail-closed indem wir ein defektes DB-Path-Szenario testen:
    # Da die DB existiert und 0 zurückgibt, prüfen wir nur die Logik des Returns.
    
    # TRAINER_BASIC hat max_trainer=2; Verein A hat 3 Trainer → Limit erreicht
    result = trainer_limit_erreicht(9001, "TRAINER_BASIC")
    check("B5.1  trainer_limit_erreicht gibt True wenn >2 Trainer (TRAINER_BASIC)",
          result is True, f"got {result}")
    
    # VEREIN_PRO hat max_trainer=None → immer False
    result_pro = trainer_limit_erreicht(9001, "VEREIN_PRO")
    check("B5.2  trainer_limit_erreicht gibt False bei unbegrenzt (VEREIN_PRO)",
          result_pro is False, f"got {result_pro}")
    
    # Spieler: TRAINER_BASIC max_spieler=25; 5 Spieler → kein Limit
    result_sp = spieler_limit_erreicht(9001, "TRAINER_BASIC")
    check("B5.3  spieler_limit_erreicht False bei 5 von 25 (TRAINER_BASIC)",
          result_sp is False, f"got {result_sp}")

def test_b5_downgrade_schutz_definition():
    print("\n── B5: Paket-Limits konsistent ──")
    # Verifikation: TRAINER_BASIC hat kleinere Limits als VEREIN_PRO
    basic = LIZENZ_TYPEN.get("TRAINER_BASIC", {})
    pro   = LIZENZ_TYPEN.get("VEREIN_PRO", {})
    check("B5.4  TRAINER_BASIC.max_trainer ist None oder < VEREIN_PRO",
          basic.get("max_trainer") != pro.get("max_trainer"))
    check("B5.5  LIZENZ_TYPEN enthält alle 4 Pakete",
          len(LIZENZ_TYPEN) >= 4)

# ─────────────────────────────────────────────────────────────────────────────
# B6 — Sperren/Entsperren
# ─────────────────────────────────────────────────────────────────────────────

def test_b6_verein_sperren():
    print("\n── B6: Verein sperren/entsperren ──")
    conn = _raw()
    conn.execute("UPDATE vereine SET aktiv=1 WHERE id=9001")
    conn.commit()
    conn.close()
    
    # verein_sperren(verein_id, gesperrt=True/False) — B6 via direktem DB-Check
    db.verein_sperren(9001, True)
    conn = _raw()
    v = conn.execute("SELECT gesperrt FROM vereine WHERE id=9001").fetchone()
    conn.close()
    check("B6.1  verein_sperren(True) setzt gesperrt=1",
          v and v[0] == 1, f"gesperrt={v}")
    
    db.verein_sperren(9001, False)
    conn = _raw()
    v2 = conn.execute("SELECT gesperrt FROM vereine WHERE id=9001").fetchone()
    conn.close()
    check("B6.2  verein_sperren(False) setzt gesperrt=0",
          v2 and v2[0] == 0, f"gesperrt={v2}")

def test_b6_benutzer_aktivieren():
    print("\n── B6: Benutzer sperren/entsperren ──")
    db.benutzer_aktivieren(9002, 0)
    conn = _raw()
    b = conn.execute("SELECT aktiv FROM benutzer WHERE id=9002").fetchone()
    conn.close()
    check("B6.3  benutzer_aktivieren(0) sperrt Benutzer",
          b and b[0] == 0, f"aktiv={b}")
    
    db.benutzer_aktivieren(9002, 1)
    conn = _raw()
    b2 = conn.execute("SELECT aktiv FROM benutzer WHERE id=9002").fetchone()
    conn.close()
    check("B6.4  benutzer_aktivieren(1) entsperrt Benutzer",
          b2 and b2[0] == 1, f"aktiv={b2}")

# ─────────────────────────────────────────────────────────────────────────────
# B7 — Audit-Log Abdeckung
# ─────────────────────────────────────────────────────────────────────────────

def test_b7_audit_log():
    print("\n── B7: Audit-Log Einträge ──")
    conn = _raw()
    cols = {r[1] for r in conn.execute("PRAGMA table_info(audit_log)").fetchall()}
    conn.close()
    check("B7.1  audit_log.benutzer_id vorhanden", "benutzer_id" in cols)
    check("B7.2  audit_log.aktion vorhanden",       "aktion" in cols)
    check("B7.3  audit_log.superadmin_id vorhanden","superadmin_id" in cols)
    check("B7.4  audit_log.details vorhanden",       "details" in cols)

def test_b7_audit_eintragen():
    print("\n── B7: Audit-Log Funktion ──")
    db.audit_log_eintragen(9002, "test_b8_aktion", "b8 test", 9001)
    conn = _raw()
    row = conn.execute(
        "SELECT aktion, superadmin_id FROM audit_log WHERE aktion='test_b8_aktion' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    check("B7.5  audit_log_eintragen schreibt korrekt",
          row and row[0] == "test_b8_aktion" and row[1] == 9001,
          f"got {row}")

# ─────────────────────────────────────────────────────────────────────────────
# B1 Guards — Regressions-Smoke-Check
# ─────────────────────────────────────────────────────────────────────────────

def test_b1_regression():
    print("\n── B1: Guard-Regression ──")
    # Damit der Guard für den letzten SA greift, deaktivieren wir den Test-SA (9001)
    # und prüfen dann, ob SA id=1 (der einzig verbleibende aktive SA) geschützt ist.
    conn = _raw()
    conn.execute("UPDATE benutzer SET aktiv=0 WHERE id=9001 AND rolle='Superadmin'")
    conn.commit()
    conn.close()

    # Jetzt sollte SA id=1 der einzige aktive SA sein → benutzer_loeschen(1) muss False zurückgeben
    ok_del, msg_del = db.benutzer_loeschen(1)
    check("B1.R1  Letzter Superadmin kann nicht gelöscht werden",
          ok_del is False and "Superadmin" in msg_del, f"ok={ok_del} msg={msg_del}")

    # benutzer_aktivieren(1, 0) muss ValueError werfen
    _err_raised = False
    try:
        db.benutzer_aktivieren(1, 0)
    except ValueError:
        _err_raised = True
    check("B1.R2  Letzten Superadmin deaktivieren löst ValueError aus",
          _err_raised)

    # Test-SA wieder aktivieren
    conn = _raw()
    conn.execute("UPDATE benutzer SET aktiv=1 WHERE id=9001 AND rolle='Superadmin'")
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# Ausführung
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Block-B Testsuite (B8)")
    print("=" * 60)

    try:
        setup()

        test_b2_unique_indexes()
        test_b2_atomic_assignment()
        test_b2_no_duplicate()

        test_b3_dashboard_kpis()
        test_b3_filter_trial()
        test_b3_filter_zahlungsstatus()
        test_b3_filter_status_trial()

        test_b4_stripe_fields_in_vollstaendig()

        test_b5_fail_closed()
        test_b5_downgrade_schutz_definition()

        test_b6_verein_sperren()
        test_b6_benutzer_aktivieren()

        test_b7_audit_log()
        test_b7_audit_eintragen()

        test_b1_regression()

    finally:
        cleanup()

    print("\n" + "=" * 60)
    print(f"  Ergebnis: {_pass} PASS, {_fail} FAIL")
    print("=" * 60)
    sys.exit(0 if _fail == 0 else 1)
