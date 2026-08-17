#!/usr/bin/env python3
"""
Trainer-Mandanten-Tests (Task #248)
Mehrfachmandanten-Architektur: trainer_mandanten-Tabelle, DB-Funktionen, Schutzregeln.
Läuft direkt als: python3 test_trainer_mandanten.py
"""

import sys
import os
import sqlite3
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")

# ── Temporäre Test-DB ──────────────────────────────────────────────────────────
_TMP_DIR = tempfile.mkdtemp(prefix="aph_test_mandanten_")
_TEST_DB = os.path.join(_TMP_DIR, "test_mandanten.db")

import database as db
_ORIG_DB_PATH = db.DB_PATH
db.DB_PATH = _TEST_DB

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

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
    c = sqlite3.connect(_TEST_DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def _verein(name: str = "Testverein") -> int:
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO vereine (name, aktiv, lizenz_status) VALUES (?, 1, 'trial')",
            (name,),
        )
        return cur.lastrowid


def _benutzer(verein_id, email: str = "trainer@test.de", rolle: str = "Trainer") -> int:
    from auth import hash_password
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO benutzer "
            "(verein_id, vorname, nachname, email, passwort_hash, rolle, aktiv, email_verifiziert) "
            "VALUES (?, 'T', 'Test', ?, ?, ?, 1, 1)",
            (verein_id, email, hash_password("pw123"), rolle),
        )
        return cur.lastrowid


def _mandant_direct(benutzer_id: int, verein_id: int, rolle: str = "Trainer") -> None:
    """Fügt trainer_mandanten-Eintrag direkt per SQL ein (kein get_conn Wrapper)."""
    with db.get_conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO trainer_mandanten "
            "(benutzer_id, verein_id, rolle_im_verein, aktiv) VALUES (?, ?, ?, 1)",
            (benutzer_id, verein_id, rolle),
        )


# ── Test-Gruppen ───────────────────────────────────────────────────────────────

def test_tabelle():
    print("\n── Tabelle ──────────────────────────────────────────")

    # Init DB first
    db.init_db()

    with _raw() as c:
        row = c.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='trainer_mandanten'"
        ).fetchone()
    check("trainer_mandanten-Tabelle existiert", row is not None)

    # UNIQUE constraint
    vid = _verein("UniqueTest")
    bid = _benutzer(vid, "unique@t.de")
    _mandant_direct(bid, vid)
    try:
        # Zweiter identischer INSERT muss fehlschlagen
        failed = False
        try:
            with _raw() as c:
                c.execute(
                    "INSERT INTO trainer_mandanten (benutzer_id, verein_id) VALUES (?, ?)",
                    (bid, vid),
                )
        except sqlite3.IntegrityError:
            failed = True
        check("UNIQUE(benutzer_id, verein_id) verhindert Duplikate", failed)
    except Exception as e:
        fail("UNIQUE-Constraint-Test", str(e))


def test_migration():
    print("\n── Idempotente Migration ────────────────────────────")

    # Benutzer anlegen VOR init_db()
    vid = _verein("MigVerein")
    bid = _benutzer(vid, "mig@test.de")

    # Migration auslösen
    db.init_db()

    with _raw() as c:
        row = c.execute(
            "SELECT 1 FROM trainer_mandanten WHERE benutzer_id=? AND verein_id=?",
            (bid, vid),
        ).fetchone()
    check("benutzer.verein_id → trainer_mandanten migriert", row is not None)

    # Idempotenz: erneutes init_db() erzeugt kein Duplikat
    db.init_db()
    with _raw() as c:
        cnt = c.execute(
            "SELECT COUNT(*) FROM trainer_mandanten WHERE benutzer_id=? AND verein_id=?",
            (bid, vid),
        ).fetchone()[0]
    check("Erneutes init_db() erzeugt keine Duplikate", cnt == 1, f"cnt={cnt}")

    # Superadmin wird NICHT migriert
    sa_vid = _verein("SAVerein")
    sa_bid = _benutzer(sa_vid, "sa_mig@test.de", rolle="Superadmin")
    db.init_db()
    with _raw() as c:
        row = c.execute(
            "SELECT 1 FROM trainer_mandanten WHERE benutzer_id=?", (sa_bid,)
        ).fetchone()
    check("Superadmin wird NICHT in trainer_mandanten migriert", row is None)

    # NULL verein_id wird NICHT migriert
    null_bid = _benutzer(None, "null@test.de")
    db.init_db()
    with _raw() as c:
        row = c.execute(
            "SELECT 1 FROM trainer_mandanten WHERE benutzer_id=?", (null_bid,)
        ).fetchone()
    check("NULL verein_id wird NICHT migriert", row is None)


def test_fuer_benutzer():
    print("\n── trainer_mandanten_fuer_benutzer() ───────────────")
    from database import trainer_mandanten_fuer_benutzer

    # Trainer ohne Mandanten (kein verein_id)
    no_vid_bid = _benutzer(None, "solo2@test.de")
    result = trainer_mandanten_fuer_benutzer(no_vid_bid)
    check("Leere Liste ohne Mandanten", result == [])

    # Trainer mit aktivem Mandanten
    vid = _verein("FuerBenVerein")
    bid = _benutzer(vid, "fuerben@test.de")
    _mandant_direct(bid, vid)
    result = trainer_mandanten_fuer_benutzer(bid)
    check("Gibt aktive Mandanten zurück", len(result) >= 1)
    if result:
        check("Verein-ID stimmt überein", result[0]["verein_id"] == vid)
    else:
        fail("Verein-ID stimmt überein", "Keine Ergebnisse")

    # Inaktive ausblenden
    with _raw() as c:
        c.execute("UPDATE trainer_mandanten SET aktiv=0 WHERE benutzer_id=?", (bid,))
    result = trainer_mandanten_fuer_benutzer(bid)
    check("Inaktive Mandanten ausgeblendet", result == [])


def test_hinzufuegen():
    print("\n── trainer_mandant_hinzufuegen() ────────────────────")
    from database import trainer_mandant_hinzufuegen, trainer_mandanten_fuer_benutzer

    v1 = _verein("Add-Verein-A")
    v2 = _verein("Add-Verein-B")
    bid = _benutzer(v1, "add@test.de")
    _mandant_direct(bid, v1)  # Ersteintrag simulieren

    trainer_mandant_hinzufuegen(bid, v2, "Trainer")
    result = trainer_mandanten_fuer_benutzer(bid)
    vids = {r["verein_id"] for r in result}
    check("Zweiten Mandanten hinzufügen", v2 in vids)
    check("Erster Mandant bleibt erhalten", v1 in vids)

    # Reaktivierung
    with _raw() as c:
        c.execute(
            "UPDATE trainer_mandanten SET aktiv=0 WHERE benutzer_id=? AND verein_id=?",
            (bid, v2),
        )
    trainer_mandant_hinzufuegen(bid, v2, "Vereinsadmin")
    result = trainer_mandanten_fuer_benutzer(bid)
    v2_entry = next((r for r in result if r["verein_id"] == v2), None)
    check("Inaktiver Eintrag reaktiviert", v2_entry is not None and v2_entry["aktiv"] == 1)
    check(
        "Rolle wird bei Reaktivierung aktualisiert",
        v2_entry is not None and v2_entry["rolle_im_verein"] == "Vereinsadmin",
    )


def test_entfernen():
    print("\n── trainer_mandant_entfernen() ──────────────────────")
    from database import trainer_mandant_entfernen, trainer_mandanten_fuer_benutzer

    vid = _verein("EntfVerein")
    bid = _benutzer(vid, "entf@test.de")
    _mandant_direct(bid, vid)

    trainer_mandant_entfernen(bid, vid)
    result = trainer_mandanten_fuer_benutzer(bid)
    check("Entfernen deaktiviert Eintrag", result == [])

    # benutzer.verein_id bleibt erhalten (Schutzregel!)
    with _raw() as c:
        row = c.execute("SELECT verein_id FROM benutzer WHERE id=?", (bid,)).fetchone()
    check(
        "benutzer.verein_id bleibt nach Austritt erhalten",
        row is not None and row["verein_id"] == vid,
    )

    # Nicht vorhandener Eintrag wirft keinen Fehler
    try:
        trainer_mandant_entfernen(99999, 99999)
        check("Entfernen nicht-vorhandener Eintrag — kein Fehler", True)
    except Exception as e:
        fail("Entfernen nicht-vorhandener Eintrag", str(e))


def test_fuer_verein():
    print("\n── trainer_mandanten_fuer_verein() ──────────────────")
    from database import trainer_mandanten_fuer_verein, trainer_mandant_entfernen

    vid = _verein("FuerVerein")
    bid = _benutzer(vid, "fv@test.de")
    _mandant_direct(bid, vid)

    result = trainer_mandanten_fuer_verein(vid)
    bid_list = [r["benutzer_id"] for r in result]
    check("Trainer im Verein enthalten", bid in bid_list)

    # Inaktive nicht enthalten
    trainer_mandant_entfernen(bid, vid)
    result = trainer_mandanten_fuer_verein(vid)
    bid_list = [r["benutzer_id"] for r in result]
    check("Entfernter Trainer nicht mehr enthalten", bid not in bid_list)


def test_alle_mit_mandanten():
    print("\n── alle_trainer_mit_mandanten() ─────────────────────")
    from database import alle_trainer_mit_mandanten

    vid = _verein("AlleMitVerein")
    bid = _benutzer(vid, "alle@test.de")
    sa_bid = _benutzer(vid, "sa_alle@test.de", rolle="Superadmin")
    result = alle_trainer_mit_mandanten()
    ids = [r["id"] for r in result]
    check("Trainer in Ergebnismenge", bid in ids)
    check("Superadmin nicht in Ergebnismenge", sa_bid not in ids)


def test_email_existiert():
    print("\n── benutzer_email_existiert() ───────────────────────")
    from database import benutzer_email_existiert

    vid = _verein("EmailVerein")
    _benutzer(vid, "exist@test.de")
    check("Existierende E-Mail erkannt", benutzer_email_existiert("exist@test.de"))
    check("Nicht-existierende E-Mail korrekt", not benutzer_email_existiert("never@test.de"))
    check("Case-insensitiv", benutzer_email_existiert("EXIST@TEST.DE"))


def test_beitreten():
    print("\n── trainer_verein_beitreten() + Mandanten ───────────")
    from database import trainer_verein_beitreten, trainer_mandanten_fuer_benutzer

    vid = _verein("BeitrittsVerein")
    with db.get_conn() as c:
        c.execute("UPDATE vereine SET max_trainer=100 WHERE id=?", (vid,))
    try:
        bid = trainer_verein_beitreten(
            vid, "Max", "Muster", "bj2@test.de", "password123"
        )
        mandanten = trainer_mandanten_fuer_benutzer(bid)
        vids = [m["verein_id"] for m in mandanten]
        check("trainer_verein_beitreten() legt mandanten-Eintrag an", vid in vids)

        # Idempotenz nach erneutem init_db()
        db.init_db()
        mandanten2 = trainer_mandanten_fuer_benutzer(bid)
        vids2 = [m["verein_id"] for m in mandanten2 if m["verein_id"] == vid]
        check("Kein Duplikat nach erneutem init_db()", len(vids2) == 1, f"Gefunden: {len(vids2)}")
    except Exception as e:
        fail("trainer_verein_beitreten()", str(e))


def test_mehrere_vereine():
    print("\n── Mehrere Vereine (Kern-Szenario) ──────────────────")
    from database import (
        trainer_mandant_hinzufuegen,
        trainer_mandant_entfernen,
        trainer_mandanten_fuer_benutzer,
    )

    v1 = _verein("Multi-A")
    v2 = _verein("Multi-B")
    v3 = _verein("Multi-C")
    bid = _benutzer(v1, "multi2@test.de")
    _mandant_direct(bid, v1)
    trainer_mandant_hinzufuegen(bid, v2)
    trainer_mandant_hinzufuegen(bid, v3)

    result = trainer_mandanten_fuer_benutzer(bid)
    vids = {r["verein_id"] for r in result}
    check("Trainer in drei Vereinen", vids == {v1, v2, v3})

    # Aus einem austreten (Superadmin darf alles)
    trainer_mandant_entfernen(bid, v2, caller_rolle="Superadmin")
    result2 = trainer_mandanten_fuer_benutzer(bid)
    vids2 = {r["verein_id"] for r in result2}
    check("Austritt aus einem — andere bleiben", vids2 == {v1, v3})

    # benutzer.verein_id (Legacy) unverändert
    with _raw() as c:
        row = c.execute("SELECT verein_id FROM benutzer WHERE id=?", (bid,)).fetchone()
    check("Legacy benutzer.verein_id bleibt unverändert", row["verein_id"] == v1)


def test_autorisierung_entfernen():
    print("\n── Autorisierung: trainer_mandant_entfernen() ───────")
    from database import trainer_mandant_entfernen, trainer_mandanten_fuer_benutzer

    v1 = _verein("Auth-Verein-A")
    v2 = _verein("Auth-Verein-B")
    bid = _benutzer(v1, "auth@test.de")
    _mandant_direct(bid, v1)
    _mandant_direct(bid, v2)

    # Vereinsadmin von v1 darf NUR v1-Mitgliedschaft entfernen
    try:
        trainer_mandant_entfernen(bid, v1, caller_rolle="Vereinsadmin", caller_verein_id=v1)
        result_v1 = trainer_mandanten_fuer_benutzer(bid)
        v1_remaining = any(r["verein_id"] == v1 for r in result_v1)
        check("Vereinsadmin entfernt eigene Vereinsmitgliedschaft", not v1_remaining)
    except Exception as e:
        fail("Vereinsadmin entfernt eigene Vereinsmitgliedschaft", str(e))

    # Vereinsadmin von v1 darf NICHT Mitgliedschaft in v2 entfernen
    perm_error_raised = False
    try:
        trainer_mandant_entfernen(bid, v2, caller_rolle="Vereinsadmin", caller_verein_id=v1)
    except PermissionError:
        perm_error_raised = True
    except Exception as e:
        fail("Cross-Tenant-Entfernung wirft PermissionError", str(e))
    check("Cross-Tenant-Entfernung wirft PermissionError", perm_error_raised)

    # v2-Mitgliedschaft ist noch aktiv
    result_after = trainer_mandanten_fuer_benutzer(bid)
    v2_still = any(r["verein_id"] == v2 for r in result_after)
    check("Fremde Mitgliedschaft bleibt nach fehlgeschlagenem Entfernen aktiv", v2_still)

    # Superadmin darf v2 trotzdem entfernen
    try:
        trainer_mandant_entfernen(bid, v2, caller_rolle="Superadmin")
        result_sa = trainer_mandanten_fuer_benutzer(bid)
        v2_gone = not any(r["verein_id"] == v2 for r in result_sa)
        check("Superadmin darf fremde Vereinsmitgliedschaft entfernen", v2_gone)
    except Exception as e:
        fail("Superadmin entfernt fremde Mitgliedschaft", str(e))

    # caller_verein_id=None ohne Superadmin → PermissionError
    v3 = _verein("Auth-Verein-C")
    bid3 = _benutzer(v3, "auth3@test.de")
    _mandant_direct(bid3, v3)
    pe2 = False
    try:
        trainer_mandant_entfernen(bid3, v3, caller_rolle="Vereinsadmin", caller_verein_id=None)
    except PermissionError:
        pe2 = True
    check("caller_verein_id=None mit Vereinsadmin wirft PermissionError", pe2)


def test_benutzer_speichern_erstellt_mandanten():
    print("\n── benutzer_speichern() erstellt trainer_mandanten ─")
    from database import benutzer_speichern, trainer_mandanten_fuer_benutzer

    vid = _verein("Portal-Verein")
    # Trainer über benutzer_speichern() anlegen (wie im Trainerportal)
    bid = benutzer_speichern(
        vid, "Portal", "Trainer", "portal@test.de", "pw1234", "Trainer"
    )
    mandanten = trainer_mandanten_fuer_benutzer(bid)
    vids = [m["verein_id"] for m in mandanten]
    check("benutzer_speichern(Trainer) erstellt mandanten-Eintrag", vid in vids)

    # Vereinsadmin ebenfalls
    vid2 = _verein("Portal-Verein-VA")
    va_bid = benutzer_speichern(
        vid2, "Portal", "Admin", "portal_va@test.de", "pw1234", "Vereinsadmin"
    )
    va_mandanten = trainer_mandanten_fuer_benutzer(va_bid)
    va_vids = [m["verein_id"] for m in va_mandanten]
    check("benutzer_speichern(Vereinsadmin) erstellt mandanten-Eintrag", vid2 in va_vids)

    # Superadmin bekommt KEINEN mandanten-Eintrag
    sa_vid = _verein("Portal-SA-Verein")
    sa_bid = benutzer_speichern(
        sa_vid, "Super", "Admin", "portal_sa@test.de", "pw1234", "Superadmin"
    )
    sa_mandanten = trainer_mandanten_fuer_benutzer(sa_bid)
    check("benutzer_speichern(Superadmin) erstellt KEINEN mandanten-Eintrag",
          not any(m["verein_id"] == sa_vid for m in sa_mandanten))

    # ohne verein_id: kein Eintrag
    bid_no_vid = benutzer_speichern(
        None, "Kein", "Verein", "no_vid_portal@test.de", "pw1234", "Trainer"
    )
    no_mandanten = trainer_mandanten_fuer_benutzer(bid_no_vid)
    check("benutzer_speichern(verein_id=None) erstellt KEINEN mandanten-Eintrag",
          len(no_mandanten) == 0)


# ── Zusammenfassung ────────────────────────────────────────────────────────────

def test_spieler_laden_multi_mandant():
    print("\n── spieler_laden() Multi-Mandant-Filterung ──────────")
    from database import spieler_laden

    v1 = _verein("SL-Verein-A")
    v2 = _verein("SL-Verein-B")
    bid = _benutzer(v1, "sl_trainer@test.de")
    _mandant_direct(bid, v1)
    _mandant_direct(bid, v2)  # Trainer ist jetzt in beiden Vereinen

    # Spieler in Verein A, zugeordnet diesem Trainer
    with db.get_conn() as c:
        c.execute(
            "INSERT INTO spieler (name, trainer_id, verein_id) VALUES ('Spieler-A', ?, ?)",
            (bid, v1),
        )
        c.execute(
            "INSERT INTO spieler (name, trainer_id, verein_id) VALUES ('Spieler-B', ?, ?)",
            (bid, v2),
        )

    # Trainer im aktiven Mandanten Verein A sieht nur Spieler in Verein A
    v1_spieler = spieler_laden(bid, "Trainer", v1)
    v1_names = [s["name"] for s in v1_spieler]
    check("Trainer sieht Spieler im aktiven Mandanten Verein A", "Spieler-A" in v1_names)
    check("Trainer sieht NICHT Spieler aus Verein B wenn V1 aktiv", "Spieler-B" not in v1_names)

    # Trainer im aktiven Mandanten Verein B sieht nur Spieler in Verein B
    v2_spieler = spieler_laden(bid, "Trainer", v2)
    v2_names = [s["name"] for s in v2_spieler]
    check("Trainer sieht Spieler im aktiven Mandanten Verein B", "Spieler-B" in v2_names)
    check("Trainer sieht NICHT Spieler aus Verein A wenn V2 aktiv", "Spieler-A" not in v2_names)

    # Trainer ohne aktive Mitgliedschaft in einem Verein sieht dort nichts
    v3 = _verein("SL-Verein-C")
    v3_spieler = spieler_laden(bid, "Trainer", v3)
    check("Trainer ohne Mandant in Verein C sieht keine Spieler", len(v3_spieler) == 0)

    # Ohne verein_id: alle eigenen Spieler (Legacy-Verhalten)
    all_spieler = spieler_laden(bid, "Trainer", None)
    all_names = [s["name"] for s in all_spieler]
    check("Ohne verein_id: alle eigenen Spieler", "Spieler-A" in all_names and "Spieler-B" in all_names)


def test_spieler_zuweisen_mandant_autorisierung():
    print("\n── spieler_trainer_zuweisen() Mandant-Autorisierung ─")
    from database import spieler_trainer_zuweisen

    v1 = _verein("ZW-Verein-A")
    v2 = _verein("ZW-Verein-B")
    bid = _benutzer(v1, "zw_trainer@test.de")
    _mandant_direct(bid, v1)
    _mandant_direct(bid, v2)  # Aktive Mitgliedschaft in beiden Vereinen

    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO spieler (name, verein_id) VALUES ('ZW-Spieler', ?)", (v2,)
        )
        spieler_id = cur.lastrowid

    # Zuweisung in Verein B soll klappen, auch wenn benutzer.verein_id = V1
    try:
        spieler_trainer_zuweisen(spieler_id, bid, v2)
        # Prüfe ob Zuweisung gespeichert
        with _raw() as c:
            row = c.execute(
                "SELECT trainer_id, verein_id FROM spieler WHERE id=?", (spieler_id,)
            ).fetchone()
        check("Zuweisung über Mandant klappt trotz Legacy-verein_id in anderem Verein",
              row["trainer_id"] == bid and row["verein_id"] == v2)
    except ValueError as e:
        fail("Zuweisung über Mandant", str(e))

    # Zuweisung in Verein C (keine Mitgliedschaft) muss scheitern
    v3 = _verein("ZW-Verein-C")
    with db.get_conn() as c:
        cur = c.execute(
            "INSERT INTO spieler (name, verein_id) VALUES ('ZW-Spieler-C', ?)", (v3,)
        )
        sp_c = cur.lastrowid
    val_error = False
    try:
        spieler_trainer_zuweisen(sp_c, bid, v3)
    except ValueError:
        val_error = True
    check("Zuweisung ohne Mandant-Mitgliedschaft in Verein C scheitert", val_error)


def test_session_invalidierung_bei_austritt():
    print("\n── Session-Invalidierung bei Mandant-Austritt ───────")
    from database import trainer_mandant_entfernen

    v1 = _verein("SI-Verein")
    bid = _benutzer(v1, "si_trainer@test.de")
    _mandant_direct(bid, v1)

    # session_token_version vor Austritt lesen
    with _raw() as c:
        row = c.execute(
            "SELECT COALESCE(session_token_version, 0) AS ver FROM benutzer WHERE id=?",
            (bid,),
        ).fetchone()
    version_vorher = row["ver"] if row else 0

    # Mitgliedschaft entfernen (Superadmin darf das immer)
    trainer_mandant_entfernen(bid, v1, caller_rolle="Superadmin")

    # session_token_version muss erhöht worden sein
    with _raw() as c:
        row2 = c.execute(
            "SELECT COALESCE(session_token_version, 0) AS ver FROM benutzer WHERE id=?",
            (bid,),
        ).fetchone()
    version_nachher = row2["ver"] if row2 else 0

    check(
        "session_token_version wird bei Mandant-Austritt erhöht",
        version_nachher > version_vorher,
        f"vorher={version_vorher}, nachher={version_nachher}",
    )

    # Mitgliedschaft ist inaktiv
    with _raw() as c:
        row3 = c.execute(
            "SELECT aktiv FROM trainer_mandanten WHERE benutzer_id=? AND verein_id=?",
            (bid, v1),
        ).fetchone()
    check("Mitgliedschaft nach Austritt inaktiv", row3 is not None and row3["aktiv"] == 0)


def test_vereinsadmin_zugriffsschutz_nach_austritt():
    print("\n── Vereinsadmin Zugriffsschutz nach Mandant-Austritt ─")
    from database import spieler_laden, trainer_mandant_entfernen

    v1 = _verein("VA-Schutz-Verein")
    va_bid = _benutzer(v1, "va_schutz@test.de", rolle="Vereinsadmin")
    _mandant_direct(va_bid, v1)

    # Spieler im Verein anlegen
    with db.get_conn() as c:
        c.execute(
            "INSERT INTO spieler (name, verein_id) VALUES ('Schutz-Spieler', ?)", (v1,)
        )

    # Vereinsadmin hat aktive Mitgliedschaft → kann Spieler sehen
    spieler_vorher = spieler_laden(va_bid, "Vereinsadmin", v1)
    check(
        "Vereinsadmin mit aktiver Mitgliedschaft sieht Spieler",
        any(s["name"] == "Schutz-Spieler" for s in spieler_vorher),
    )

    # Mitgliedschaft entfernen (Superadmin darf das)
    trainer_mandant_entfernen(va_bid, v1, caller_rolle="Superadmin")

    # Vereinsadmin hat KEINE aktive Mitgliedschaft mehr → kein Zugriff
    spieler_nachher = spieler_laden(va_bid, "Vereinsadmin", v1)
    check(
        "Vereinsadmin ohne aktive Mitgliedschaft sieht KEINE Spieler mehr",
        len(spieler_nachher) == 0,
    )


def test_trainer_pool_per_mandant():
    print("\n── trainer_mandanten_fuer_verein() als Trainer-Pool ─")
    from database import trainer_mandanten_fuer_verein

    v1 = _verein("Pool-Verein-A")
    v2 = _verein("Pool-Verein-B")

    # Trainer mit benutzer.verein_id = v1, aber aktiver Mandant auch in v2
    bid = _benutzer(v1, "pool_trainer@test.de")
    _mandant_direct(bid, v1)
    _mandant_direct(bid, v2)

    # Trainer mit benutzer.verein_id = v1, KEINE Mitgliedschaft in v2
    bid_nur_v1 = _benutzer(v1, "pool_nur_v1@test.de")
    _mandant_direct(bid_nur_v1, v1)

    # trainer_mandanten_fuer_verein(v2) zeigt den Trainer mit Mandant in v2
    pool_v2 = trainer_mandanten_fuer_verein(v2)
    bids_v2 = {t["benutzer_id"] for t in pool_v2}
    check(
        "Trainer mit Mandant in V2 erscheint im Pool für V2",
        bid in bids_v2,
    )
    check(
        "Trainer OHNE Mandant in V2 erscheint NICHT im Pool für V2",
        bid_nur_v1 not in bids_v2,
    )

    # trainer_mandanten_fuer_verein(v1) zeigt beide Trainer
    pool_v1 = trainer_mandanten_fuer_verein(v1)
    bids_v1 = {t["benutzer_id"] for t in pool_v1}
    check("Beide Trainer erscheinen im Pool für V1", bid in bids_v1 and bid_nur_v1 in bids_v1)


def cleanup():
    db.DB_PATH = _ORIG_DB_PATH
    try:
        shutil.rmtree(_TMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("  Trainer-Mandanten Tests (Task #248)")
    print("=" * 60)

    try:
        test_tabelle()
        test_migration()
        test_fuer_benutzer()
        test_hinzufuegen()
        test_entfernen()
        test_fuer_verein()
        test_alle_mit_mandanten()
        test_email_existiert()
        test_beitreten()
        test_mehrere_vereine()
        test_autorisierung_entfernen()
        test_benutzer_speichern_erstellt_mandanten()
        test_spieler_laden_multi_mandant()
        test_spieler_zuweisen_mandant_autorisierung()
        test_session_invalidierung_bei_austritt()
        test_vereinsadmin_zugriffsschutz_nach_austritt()
        test_trainer_pool_per_mandant()
    finally:
        cleanup()

    print("\n" + "=" * 60)
    total = _pass + _fail
    print(f"  Ergebnis: {_pass}/{total} PASS  |  {_fail} FAIL")
    print("=" * 60)
    if _fail:
        sys.exit(1)
