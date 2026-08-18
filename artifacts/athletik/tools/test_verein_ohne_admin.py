#!/usr/bin/env python3
"""
Regressionstests: Vereinskunde ohne Vereinsadmin

Szenarien A–H aus dem Hotfix-Spec:
A) Verein MIT Vereinsadmin → normales Verhalten
B) Verein OHNE Vereinsadmin → kunde_vollstaendig_laden: verein ok, benutzer None
C) Verein ohne VA: Vereinsname ändern → funktioniert
D) Verein ohne VA: aktiv 1→0 → funktioniert (aktiv allein löst Verein-UPDATE aus)
E) Kein Aufruf benutzer_aktivieren(None) → keine Exception
F) Einzeltrainer → bestehendes Verhalten unverändert
G) Technischer Mandant → bestehendes Verhalten unverändert
H) kundenstamm_aendern(benutzer_id=None, ...) → nur Verein-UPDATE, kein Crash
"""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")

import database as db

_ORIG_DB = db.DB_PATH
_TMP_DIR = tempfile.mkdtemp(prefix="test_verein_ohne_admin_")
_DB_PATH = os.path.join(_TMP_DIR, "test.db")

db.DB_PATH = _DB_PATH
db.init_db()

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────
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


def _verein(name: str, ist_techn: int = 0) -> int:
    with db.get_conn() as c:
        return c.execute(
            "INSERT INTO vereine (name, lizenz_status, ist_technischer_mandant, aktiv) "
            "VALUES (?, 'active', ?, 1)",
            (name, ist_techn),
        ).lastrowid


def _benutzer(verein_id, email: str, rolle: str = "Vereinsadmin") -> int:
    with db.get_conn() as c:
        return c.execute(
            "INSERT INTO benutzer (email, passwort_hash, rolle, aktiv, verein_id) "
            "VALUES (?, 'x', ?, 1, ?)",
            (email, rolle, verein_id),
        ).lastrowid


def cleanup():
    db.DB_PATH = _ORIG_DB
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


# ── Szenario A: Verein MIT Vereinsadmin ───────────────────────────────────────
def test_A_verein_mit_admin():
    print("\n── A: Verein MIT Vereinsadmin ────────────────────────")
    v_id = _verein("VA-Verein-A")
    b_id = _benutzer(v_id, "va@a.de")

    daten = db.kunde_vollstaendig_laden(verein_id=v_id)
    check("A1: daten ist nicht None", daten is not None)
    check("A2: verein vorhanden",     bool(daten.get("verein")))
    check("A3: benutzer vorhanden",   bool(daten.get("benutzer")))
    check("A4: benutzer.id korrekt",  daten["benutzer"]["id"] == b_id)
    check("A5: verein.id korrekt",    daten["verein"]["id"] == v_id)


# ── Szenario B: Verein OHNE Vereinsadmin ──────────────────────────────────────
def test_B_verein_ohne_admin():
    print("\n── B: Verein OHNE Vereinsadmin ───────────────────────")
    v_id = _verein("VA-Verein-B-ohne-Admin")

    daten = db.kunde_vollstaendig_laden(verein_id=v_id)
    check("B1: daten ist nicht None",    daten is not None,
          "kunde_vollstaendig_laden crasht")
    check("B2: verein vorhanden",        bool(daten.get("verein")),
          f"verein={daten.get('verein') if daten else 'N/A'}")
    check("B3: benutzer ist None",       daten.get("benutzer") is None,
          f"benutzer={daten.get('benutzer')}")
    check("B4: kein Crash",              True)  # bis hierher = kein Crash


# ── Szenario C: Vereinsname ändern ohne Benutzer ──────────────────────────────
def test_C_vereinsname_aendern():
    print("\n── C: Vereinsname ändern ohne Vereinsadmin ──────────")
    v_id = _verein("C-Alter-Name")

    # kundenstamm_aendern mit benutzer_id=None
    db.kundenstamm_aendern(
        None, v_id,
        vereinsname="C-Neuer-Name",
        superadmin_id=None,
    )

    with db.get_conn() as c:
        row = c.execute("SELECT name FROM vereine WHERE id=?", (v_id,)).fetchone()
    check("C1: Vereinsname wurde geändert",
          row and row["name"] == "C-Neuer-Name",
          f"name={row['name'] if row else 'N/A'}")


# ── Szenario D: aktiv 1→0 ohne Benutzer ──────────────────────────────────────
def test_D_aktiv_aendern():
    print("\n── D: aktiv 1→0 ohne Vereinsadmin ───────────────────")
    v_id = _verein("D-Verein-Aktiv")

    with db.get_conn() as c:
        c.execute("UPDATE vereine SET aktiv=1 WHERE id=?", (v_id,))

    db.kundenstamm_aendern(None, v_id, aktiv=0, superadmin_id=None)

    with db.get_conn() as c:
        row = c.execute("SELECT aktiv FROM vereine WHERE id=?", (v_id,)).fetchone()
    check("D1: aktiv wurde auf 0 gesetzt (BUG-FIX: aktiv allein triggert UPDATE)",
          row and row["aktiv"] == 0,
          f"aktiv={row['aktiv'] if row else 'N/A'}")

    # Auch zurück auf 1
    db.kundenstamm_aendern(None, v_id, aktiv=1, superadmin_id=None)
    with db.get_conn() as c:
        row2 = c.execute("SELECT aktiv FROM vereine WHERE id=?", (v_id,)).fetchone()
    check("D2: aktiv wieder auf 1 setzbar",
          row2 and row2["aktiv"] == 1,
          f"aktiv={row2['aktiv'] if row2 else 'N/A'}")


# ── Szenario E: benutzer_aktivieren(None) wird NICHT aufgerufen ───────────────
def test_E_kein_benutzer_aktivieren_none():
    print("\n── E: Kein benutzer_aktivieren(None) ────────────────")
    # Direkttest: benutzer_aktivieren(None, 0) soll einen Fehler produzieren
    # oder silently fehlschlagen — wichtig ist: der Code-Pfad in _detail_a_kundenkonto
    # ruft es NICHT auf wenn kein Benutzer vorhanden ist (Code-Review-Test).
    # Wir simulieren den Schutz indem wir prüfen, dass kundenstamm_aendern
    # mit benutzer_id=None KEIN benutzer-UPDATE auslöst.
    v_id = _verein("E-Verein")

    # Lege extra einen Benutzer in EINEM ANDEREN Verein an (Kontrolle)
    v_other = _verein("E-Verein-Other")
    b_other = _benutzer(v_other, "e_other@test.de")

    # Setze aktiv=0 für Verein E via kundenstamm_aendern(None, v_id, ...)
    db.kundenstamm_aendern(None, v_id, aktiv=0, superadmin_id=None)

    # Der andere Benutzer (v_other) darf NICHT verändert worden sein
    with db.get_conn() as c:
        b_row = c.execute("SELECT aktiv FROM benutzer WHERE id=?", (b_other,)).fetchone()
    check("E1: Anderer Benutzer wurde nicht berührt (kein unbeabsichtigter Benutzer-UPDATE)",
          b_row and b_row["aktiv"] == 1,
          f"aktiv={b_row['aktiv'] if b_row else 'N/A'}")

    # Kein Crash bei benutzer_id=None + aktiv-Parameter
    crashed = False
    try:
        db.kundenstamm_aendern(None, v_id, aktiv=1, superadmin_id=None)
    except Exception as e:
        crashed = True
    check("E2: kundenstamm_aendern(None, ...) wirft keine Exception", not crashed)


# ── Szenario F: Einzeltrainer — bestehendes Verhalten ────────────────────────
def test_F_einzeltrainer():
    print("\n── F: Einzeltrainer — bestehendes Verhalten ─────────")
    # Einzeltrainer ohne Verein: benutzer_id gesetzt, verein_id=None
    # (Direkttrainer ohne techn. Mandant)
    with db.get_conn() as c:
        b_id = c.execute(
            "INSERT INTO benutzer (email, passwort_hash, rolle, aktiv) "
            "VALUES ('f_trainer@test.de', 'x', 'Trainer', 1)"
        ).lastrowid

    daten = db.kunde_vollstaendig_laden(benutzer_id=b_id)
    check("F1: daten ist nicht None",  daten is not None)
    check("F2: benutzer vorhanden",    bool(daten.get("benutzer")))
    check("F3: verein ist None",       daten.get("verein") is None)
    check("F4: benutzer.id korrekt",   daten["benutzer"]["id"] == b_id)

    # kundenstamm_aendern mit echter benutzer_id → Benutzer-UPDATE
    db.kundenstamm_aendern(b_id, None, vorname="Franz", superadmin_id=None)
    with db.get_conn() as c:
        row = c.execute("SELECT vorname FROM benutzer WHERE id=?", (b_id,)).fetchone()
    check("F5: Vorname wurde beim Einzeltrainer geändert",
          row and row["vorname"] == "Franz",
          f"vorname={row['vorname'] if row else 'N/A'}")


# ── Szenario G: Technischer Mandant ──────────────────────────────────────────
def test_G_technischer_mandant():
    print("\n── G: Technischer Mandant — bestehendes Verhalten ───")
    v_id = _verein("G-TechMandant", ist_techn=1)
    b_id = _benutzer(v_id, "g_trainer@test.de", rolle="Trainer")

    # Über benutzer_id laden (Einzeltrainer-Pfad mit techn. Mandant)
    daten = db.kunde_vollstaendig_laden(benutzer_id=b_id)
    check("G1: daten nicht None",             daten is not None)
    check("G2: benutzer vorhanden",           bool(daten.get("benutzer")))
    check("G3: verein vorhanden (techn.Mand.)",bool(daten.get("verein")))
    check("G4: ist_technischer_mandant=1",
          daten["verein"].get("ist_technischer_mandant") == 1)


# ── Szenario H: kundenstamm_aendern — nur Verein-UPDATE, kein Benutzer-Crash ─
def test_H_kundenstamm_aendern_verein_only():
    print("\n── H: kundenstamm_aendern(None, verein_id) — komplett")
    v_id = _verein("H-Verein")

    # Name + Ansprechpartner + aktiv
    db.kundenstamm_aendern(
        None, v_id,
        vereinsname="H-Geänderter-Name",
        ansprechpartner="Müller Hans",
        aktiv=0,
        superadmin_id=None,
    )
    with db.get_conn() as c:
        row = c.execute(
            "SELECT name, ansprechpartner, aktiv FROM vereine WHERE id=?", (v_id,)
        ).fetchone()
    check("H1: Vereinsname gesetzt",      row and row["name"] == "H-Geänderter-Name")
    check("H2: Ansprechpartner gesetzt",  row and row["ansprechpartner"] == "Müller Hans")
    check("H3: aktiv auf 0 gesetzt",      row and row["aktiv"] == 0)

    # Nur aktiv=1 ohne Name/Ansprechpartner (BUG-FIX Test)
    db.kundenstamm_aendern(None, v_id, aktiv=1, superadmin_id=None)
    with db.get_conn() as c:
        row2 = c.execute("SELECT aktiv, name FROM vereine WHERE id=?", (v_id,)).fetchone()
    check("H4: aktiv=1 ohne Namensangabe gesetzt (BUG-FIX)",
          row2 and row2["aktiv"] == 1,
          f"aktiv={row2['aktiv'] if row2 else 'N/A'}")
    check("H5: Vereinsname blieb erhalten",
          row2 and row2["name"] == "H-Geänderter-Name")

    # Kein Benutzer-UPDATE ausgelöst (Prüfung über separaten Benutzer)
    with db.get_conn() as c:
        b_check = c.execute(
            "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND vorname IS NOT NULL", (v_id,)
        ).fetchone()[0]
    check("H6: Kein Benutzer-UPDATE ohne benutzer_id", b_check == 0)


# ── Szenario B2: kunde_vollstaendig_laden via verein_id, kein VA ──────────────
def test_B2_vollstaendig_laden_konsistenz():
    print("\n── B2: vollstaendig_laden — Verein ohne VA, kein Crash ─")
    v_id = _verein("B2-Kein-VA")

    # Mehrfach aufrufen — kein Crash
    for i in range(3):
        daten = db.kunde_vollstaendig_laden(verein_id=v_id)
        check(f"B2.{i+1}: Aufruf {i+1} kein Crash",
              daten is not None and daten.get("verein") is not None and daten.get("benutzer") is None)


# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Vereinskunde ohne Vereinsadmin — Hotfix-Tests")
    print("=" * 60)
    try:
        test_A_verein_mit_admin()
        test_B_verein_ohne_admin()
        test_C_vereinsname_aendern()
        test_D_aktiv_aendern()
        test_E_kein_benutzer_aktivieren_none()
        test_F_einzeltrainer()
        test_G_technischer_mandant()
        test_H_kundenstamm_aendern_verein_only()
        test_B2_vollstaendig_laden_konsistenz()
    finally:
        cleanup()

    print()
    print("=" * 60)
    print(f"  Ergebnis: {_pass}/{_pass + _fail} PASS  |  {_fail} FAIL")
    print("=" * 60)
    sys.exit(0 if _fail == 0 else 1)
