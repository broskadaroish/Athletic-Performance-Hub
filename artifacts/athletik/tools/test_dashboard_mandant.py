"""
Mandantenscharfe Dashboard-KPI-Tests

Sicherstellt, dass dashboard_trainer_* Funktionen bei gesetztem verein_id
ausschliesslich Daten des aktiven Mandanten liefern.

Szenarien:
  - Trainer in Verein A + B: aktiv A → nur A-Werte
  - Trainer in Verein A + B: aktiv B → nur B-Werte
  - Superadmin (keine verein_id-Filterung) → globale Werte
  - Einzelmandant ohne verein_id → Legacy-Pfad gibt alle Spieler zurück
"""

import os
import sys
import shutil
import tempfile
import contextlib

# ---------------------------------------------------------------------------
# Pfad-Setup
# ---------------------------------------------------------------------------
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT      = os.path.dirname(_TOOLS_DIR)
sys.path.insert(0, _ROOT)

import database as db

_ORIG_DB_PATH = db.DB_PATH
_TMP_DIR      = tempfile.mkdtemp(prefix="test_dash_mandant_")
_DB           = os.path.join(_TMP_DIR, "test.db")

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
_pass = _fail = 0

def check(label: str, condition: bool, detail: str = ""):
    global _pass, _fail
    if condition:
        print(f"  ✅ PASS  {label}")
        _pass += 1
    else:
        msg = f"  ❌ FAIL  {label}"
        if detail:
            msg += f"\n           → {detail}"
        print(msg)
        _fail += 1


@contextlib.contextmanager
def _raw():
    import sqlite3
    con = sqlite3.connect(_DB)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _verein(name: str) -> int:
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO vereine (name, lizenz_status, ist_technischer_mandant) "
            "VALUES (?, 'active', 0)",
            (name,),
        )
        return cur.lastrowid


def _benutzer(verein_id: int, email: str, rolle: str = "Trainer") -> int:
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO benutzer (email, passwort_hash, rolle, aktiv, verein_id) "
            "VALUES (?, 'x', ?, 1, ?)",
            (email, rolle, verein_id),
        )
        return cur.lastrowid


def _mandant(benutzer_id: int, verein_id: int):
    with db.get_conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO trainer_mandanten (benutzer_id, verein_id, aktiv) "
            "VALUES (?, ?, 1)",
            (benutzer_id, verein_id),
        )


def _spieler(name: str, trainer_id: int, verein_id: int) -> int:
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO spieler (name, trainer_id, verein_id) VALUES (?, ?, ?)",
            (name, trainer_id, verein_id),
        )
        return cur.lastrowid


def _verletzung(spieler_id: int, datum: str = "2026-08-15"):
    with db.get_conn() as c:
        c.execute(
            "INSERT INTO verletzung (spieler_id, datum, art, koerperteil, schwere) "
            "VALUES (?, ?, 'Zerrung', 'Oberschenkel', 'leicht')",
            (spieler_id, datum),
        )


def _fms_test(spieler_id: int, datum: str = "2026-06-01"):
    """Fügt einen FMS-Testeintrag ein → Spieler gilt als 'getestet'."""
    with db.get_conn() as c:
        c.execute(
            "INSERT INTO fms_test (spieler_id, datum, deep_squat, hurdle_links, "
            "hurdle_rechts, inline_links, inline_rechts, shoulder_links, shoulder_rechts, score) "
            "VALUES (?, ?, 2, 2, 2, 2, 2, 2, 2, 14)",
            (spieler_id, datum),
        )


# ---------------------------------------------------------------------------
# Einmaliges Setup
# ---------------------------------------------------------------------------
def setup():
    db.DB_PATH = _DB
    db.init_db()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_ohne_test_mandant_isolation():
    print("\n── dashboard_trainer_ohne_test: Mandant-Isolation ───")
    from database import dashboard_trainer_ohne_test

    va  = _verein("DT-OT-VA")
    vb  = _verein("DT-OT-VB")
    bid = _benutzer(va, "dt_ot@test.de")
    _mandant(bid, va)
    _mandant(bid, vb)

    sp_a = _spieler("OT-A", bid, va)   # A → getestet
    sp_b = _spieler("OT-B", bid, vb)   # B → NICHT getestet

    _fms_test(sp_a, "2026-08-17")      # Frischer Test → nicht fällig

    # Aktiver Mandant A: 0 fällige (Spieler A hat Test)
    n_a = dashboard_trainer_ohne_test(bid, verein_id=va)
    check("Aktiver Mandant A → 0 fällige (Spieler A hat Test)",
          n_a == 0, f"Erhalten: {n_a}")

    # Aktiver Mandant B: 1 fällig (Spieler B kein Test)
    n_b = dashboard_trainer_ohne_test(bid, verein_id=vb)
    check("Aktiver Mandant B → 1 fällig (Spieler B ohne Test)",
          n_b == 1, f"Erhalten: {n_b}")

    # Ohne verein_id (Legacy): beide Spieler → 1 fällig gesamt
    n_all = dashboard_trainer_ohne_test(bid, verein_id=None)
    check("Ohne verein_id → Spieler beider Vereine (Sp-A getestet, Sp-B nicht → 1)",
          n_all == 1, f"Erhalten: {n_all}")

    # Kein Mix: A-Wert != B-Wert (unterschiedliche Realität)
    check("A-Wert ≠ B-Wert — keine Vermischung",
          n_a != n_b)


def test_verletzungen_mandant_isolation():
    print("\n── dashboard_trainer_neue_verletzungen: Mandant-Isolation")
    from database import dashboard_trainer_neue_verletzungen

    va  = _verein("DT-VL-VA")
    vb  = _verein("DT-VL-VB")
    bid = _benutzer(va, "dt_vl@test.de")
    _mandant(bid, va)
    _mandant(bid, vb)

    sp_a = _spieler("VL-A", bid, va)   # A → Verletzung
    _spieler("VL-B", bid, vb)          # B → keine Verletzung

    _verletzung(sp_a, "2026-08-16")    # Innerhalb 14 Tage

    v_a = dashboard_trainer_neue_verletzungen(bid, verein_id=va)
    check("Aktiver Mandant A → 1 Verletzung",
          v_a == 1, f"Erhalten: {v_a}")

    v_b = dashboard_trainer_neue_verletzungen(bid, verein_id=vb)
    check("Aktiver Mandant B → 0 Verletzungen",
          v_b == 0, f"Erhalten: {v_b}")

    v_all = dashboard_trainer_neue_verletzungen(bid, verein_id=None)
    check("Ohne verein_id → 1 (globale Zählung über beide Mandanten)",
          v_all == 1, f"Erhalten: {v_all}")


def test_diagnostiken_mandant_isolation():
    print("\n── dashboard_trainer_diagnostiken_monat: Mandant-Isolation")
    from database import dashboard_trainer_diagnostiken_monat

    va  = _verein("DT-DM-VA")
    vb  = _verein("DT-DM-VB")
    bid = _benutzer(va, "dt_dm@test.de")
    _mandant(bid, va)
    _mandant(bid, vb)

    sp_a = _spieler("DM-A", bid, va)
    _spieler("DM-B", bid, vb)

    _fms_test(sp_a, "2026-08-01")   # In Monat August 2026

    d_a = dashboard_trainer_diagnostiken_monat(bid, verein_id=va)
    check("Aktiver Mandant A → ≥1 Diagnostik diesen Monat",
          d_a >= 1, f"Erhalten: {d_a}")

    d_b = dashboard_trainer_diagnostiken_monat(bid, verein_id=vb)
    check("Aktiver Mandant B → 0 Diagnostiken",
          d_b == 0, f"Erhalten: {d_b}")

    d_all = dashboard_trainer_diagnostiken_monat(bid, verein_id=None)
    check("Ohne verein_id → ≥1 (beide Mandanten)",
          d_all >= 1, f"Erhalten: {d_all}")

    check("B-Wert strikter als globaler Wert: 0 < global",
          d_b < d_all)


def test_letzte_spieler_mandant_isolation():
    print("\n── dashboard_trainer_letzte_spieler: Mandant-Isolation")
    from database import dashboard_trainer_letzte_spieler

    va  = _verein("DT-LS-VA")
    vb  = _verein("DT-LS-VB")
    bid = _benutzer(va, "dt_ls@test.de")
    _mandant(bid, va)
    _mandant(bid, vb)

    sp_a = _spieler("LS-A", bid, va)
    sp_b = _spieler("LS-B", bid, vb)

    _fms_test(sp_a, "2026-08-17")
    _fms_test(sp_b, "2026-08-10")

    r_a = dashboard_trainer_letzte_spieler(bid, limit=10, verein_id=va)
    ids_a = [r["id"] for r in r_a]
    check("Aktiver Mandant A → nur A-Spieler",
          sp_a in ids_a and sp_b not in ids_a,
          f"ids={ids_a}")

    r_b = dashboard_trainer_letzte_spieler(bid, limit=10, verein_id=vb)
    ids_b = [r["id"] for r in r_b]
    check("Aktiver Mandant B → nur B-Spieler",
          sp_b in ids_b and sp_a not in ids_b,
          f"ids={ids_b}")

    r_all = dashboard_trainer_letzte_spieler(bid, limit=10, verein_id=None)
    ids_all = [r["id"] for r in r_all]
    check("Ohne verein_id (Legacy) → beide Spieler sichtbar",
          sp_a in ids_all and sp_b in ids_all,
          f"ids={ids_all}")


def test_superadmin_global():
    """Superadmin-Auswertungen in spieler_laden() bleiben global (kein verein_id-Filter)."""
    print("\n── Superadmin: globale Auswertung unberührt ──────────")
    from database import spieler_laden

    va  = _verein("DT-SA-VA")
    vb  = _verein("DT-SA-VB")
    bid_sa = _benutzer(va, "dt_sa@test.de", rolle="Superadmin")

    _spieler("SA-Spieler-A", None, va)
    _spieler("SA-Spieler-B", None, vb)

    alle = spieler_laden(bid_sa, "Superadmin", verein_id=None)
    namen = [s["name"] for s in alle]
    check("Superadmin sieht alle Spieler (global, kein verein_id-Filter)",
          "SA-Spieler-A" in namen and "SA-Spieler-B" in namen)


def test_einzel_mandant_legacy():
    """Einzelmandant-Trainer ohne verein_id: Legacy-Pfad liefert alle eigenen Spieler."""
    print("\n── Einzelmandant ohne verein_id: Legacy-Pfad ────────")
    from database import dashboard_trainer_letzte_spieler

    v  = _verein("DT-EM-V")
    bid = _benutzer(v, "dt_em@test.de")
    _mandant(bid, v)

    sp = _spieler("EM-Spieler", bid, v)
    _fms_test(sp, "2026-08-15")

    r = dashboard_trainer_letzte_spieler(bid, limit=10, verein_id=None)
    ids = [x["id"] for x in r]
    check("Einzelmandant ohne verein_id → Spieler im Legacy-Pfad sichtbar",
          sp in ids, f"ids={ids}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def cleanup():
    db.DB_PATH = _ORIG_DB_PATH
    try:
        shutil.rmtree(_TMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    setup()
    try:
        test_ohne_test_mandant_isolation()
        test_verletzungen_mandant_isolation()
        test_diagnostiken_mandant_isolation()
        test_letzte_spieler_mandant_isolation()
        test_superadmin_global()
        test_einzel_mandant_legacy()
    finally:
        cleanup()

    print()
    print("=" * 60)
    print(f"  Ergebnis: {_pass}/{_pass + _fail} PASS  |  {_fail} FAIL")
    print("=" * 60)
    if _fail:
        sys.exit(1)
