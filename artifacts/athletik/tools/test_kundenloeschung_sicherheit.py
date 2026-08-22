#!/usr/bin/env python3
"""Regressionen für Vertragsidentität und fail-closed Kundenlöschung.

Die Tests laufen ausschließlich gegen eine temporäre SQLite-Datenbank.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database as db


TMP_DIR = Path(tempfile.mkdtemp(prefix="aph-kundenloeschung-"))
TEST_DB = TMP_DIR / "kundenloeschung.db"
ORIGINAL_DB = db.DB_PATH
db.DB_PATH = str(TEST_DB)
db.init_db()

PASS = 0
FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS  {label}")
    else:
        FAIL += 1
        print(f"FAIL  {label}")


def erwartet_value_error(label: str, callback) -> None:
    try:
        callback()
    except ValueError:
        check(label, True)
    else:
        check(label, False)


def verein(
    verein_id: int,
    name: str,
    kundennummer: str,
    *,
    technisch: bool = False,
) -> None:
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO vereine
               (id, name, kundennummer, aktiv, lizenztyp, lizenz_status,
                ist_technischer_mandant)
               VALUES (?, ?, ?, 1, 'TRAINER_BASIC', 'active', ?)""",
            (verein_id, name, kundennummer, int(technisch)),
        )


def benutzer(
    benutzer_id: int,
    email: str,
    *,
    verein_id: int | None,
    kundennummer: str | None,
    rolle: str = "Trainer",
) -> None:
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO benutzer
               (id, verein_id, vorname, nachname, email, passwort_hash, rolle,
                aktiv, kundennummer)
               VALUES (?, ?, 'Test', 'Person', ?, 'hash', ?, 1, ?)""",
            (benutzer_id, verein_id, email, rolle, kundennummer),
        )


def mitgliedschaft(benutzer_id: int, verein_id: int) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO trainer_mandanten (benutzer_id, verein_id) VALUES (?, ?)",
            (benutzer_id, verein_id),
        )


def spieler(spieler_id: int, verein_id: int, trainer_id: int) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO spieler (id, name, verein_id, trainer_id) VALUES (?, 'Testspieler', ?, ?)",
            (spieler_id, verein_id, trainer_id),
        )


def setup() -> None:
    benutzer(1, "superadmin@test.invalid", verein_id=None, kundennummer=None, rolle="Superadmin")

    # Technischer Einzeltrainer: Vertragskonto APH-A, Benutzerkonto APH-B.
    verein(100, "Technischer Trainerbereich", "APH-000100", technisch=True)
    benutzer(101, "trainer@test.invalid", verein_id=100, kundennummer="APH-000101")
    mitgliedschaft(101, 100)
    spieler(110, 100, 101)
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO rechnungen (verein_id, rechnungsnummer, betrag_eur)
               VALUES (100, 'R-100', 19.90)"""
        )
        conn.execute(
            """INSERT INTO audit_log (benutzer_id, aktion, details, superadmin_id)
               VALUES (101, 'test_vor_loeschung', 'Nachweis', 1)"""
        )

    # Eigenständiger Vereinskunde zum Vergleich.
    verein(300, "FC Test", "APH-000300")
    benutzer(301, "admin@fc-test.invalid", verein_id=300, kundennummer="APH-000301", rolle="Vereinsadmin")
    mitgliedschaft(301, 300)
    spieler(310, 300, 301)

    # Fremder Mandant für Mehrfachmandanten- und Fremdtrainerfälle.
    verein(200, "Fremdverein", "APH-000200")
    benutzer(201, "fremd@verein.invalid", verein_id=200, kundennummer="APH-000201")
    mitgliedschaft(201, 200)


def test_identity_and_confirmation() -> None:
    kunden = db.kunden_liste_laden()
    trainer = next(row for row in kunden if row.get("benutzer_id") == 101)
    check(
        "Technischer Einzeltrainer führt den technischen Mandanten als Kundenkonto",
        trainer["vertrag_verein_id"] == 100 and trainer["kundennummer"] == "APH-000100",
    )

    detail = db.kunde_vollstaendig_laden(verein_id=100, benutzer_id=101)
    check(
        "Detailansicht trennt Vertrags- und Benutzerkundennummer",
        detail
        and detail["verein"]["kundennummer"] == "APH-000100"
        and detail["benutzer"]["kundennummer"] == "APH-000101",
    )

    ziel = db.kunde_loeschziel_pruefen(
        100,
        101,
        erwartete_kundennummer="APH-000100",
        superadmin_id=1,
    )
    check(
        "Löschziel verwendet APH-A und nicht die Benutzerkundennummer APH-B",
        ziel["kundennummer"] == "APH-000100" and ziel["benutzer_ids"] == [101],
    )
    erwartet_value_error(
        "Falsche Benutzerkundennummer blockiert die Löschfreigabe",
        lambda: db.kunde_loeschziel_pruefen(
            100,
            101,
            erwartete_kundennummer="APH-000101",
            superadmin_id=1,
        ),
    )

    zusammenfassung = db.kunde_zusammenfassung_laden(
        100,
        101,
        erwartete_kundennummer="APH-000100",
        superadmin_id=1,
    )
    check(
        "Zusammenfassung zählt ausschließlich Daten des technischen Kundenkontos",
        zusammenfassung["n_spieler"] == 1
        and zusammenfassung["n_benutzerkonten"] == 1
        and zusammenfassung["n_mandantenzuordnungen"] == 1,
    )

    verein_ziel = db.kunde_loeschziel_pruefen(
        300,
        301,
        erwartete_kundennummer="APH-000300",
        superadmin_id=1,
    )
    check(
        "Vereinskunde bestätigt mit der Vereins-Kundennummer",
        verein_ziel["kundennummer"] == "APH-000300",
    )


def test_fail_closed_consistency_guards() -> None:
    # Ein zweites direktes Benutzerkonto im technischen Mandanten ist nie ein
    # zulässiges Einzeltrainer-Kundenobjekt.
    benutzer(102, "fremd-im-tech@test.invalid", verein_id=100, kundennummer="APH-000102")
    erwartet_value_error(
        "Fremder Benutzer im technischen Mandanten blockiert fail-closed",
        lambda: db.kunde_loeschziel_pruefen(
            100, 101, erwartete_kundennummer="APH-000100", superadmin_id=1
        ),
    )
    with db.get_conn() as conn:
        conn.execute("DELETE FROM benutzer WHERE id=102")

    # Ein Benutzer mit weiterem Mandanten darf durch die Kundenlöschung nicht
    # samt seiner Mitgliedschaft beim Fremdverein verschwinden.
    mitgliedschaft(101, 200)
    erwartet_value_error(
        "Mehrfachmandanten-Trainer blockiert die Löschung statt Fremdmandant zu treffen",
        lambda: db.kunde_loeschziel_pruefen(
            100, 101, erwartete_kundennummer="APH-000100", superadmin_id=1
        ),
    )
    with db.get_conn() as conn:
        fremdverein_vorhanden = conn.execute(
            "SELECT 1 FROM vereine WHERE id=200"
        ).fetchone()
        trainer_vorhanden = conn.execute(
            "SELECT 1 FROM benutzer WHERE id=101"
        ).fetchone()
        conn.execute("DELETE FROM trainer_mandanten WHERE benutzer_id=101 AND verein_id=200")
    check(
        "Geblockte Mehrfachmandanten-Löschung verändert keine Fremddaten",
        bool(fremdverein_vorhanden) and bool(trainer_vorhanden),
    )

    # Ein Spieler darf nicht einem Trainer ohne Zugehörigkeit zum Kundenmandanten
    # zugeordnet sein.
    spieler(111, 100, 201)
    erwartet_value_error(
        "Fremde Spielerzuordnung blockiert die Löschung fail-closed",
        lambda: db.kunde_loeschziel_pruefen(
            100, 101, erwartete_kundennummer="APH-000100", superadmin_id=1
        ),
    )
    with db.get_conn() as conn:
        conn.execute("DELETE FROM spieler WHERE id=111")

    # Ein Standalone-Trainer hat keine Mandanten-ID. SQL-NULL darf seine
    # Fremdzuordnung nicht als sichere Zielzuordnung durchwinken.
    benutzer(202, "standalone@test.invalid", verein_id=None, kundennummer="APH-000202")
    spieler(112, 100, 202)
    erwartet_value_error(
        "Standalone-Fremdtrainer mit NULL-Mandant blockiert die Löschung",
        lambda: db.kunde_loeschziel_pruefen(
            100, 101, erwartete_kundennummer="APH-000100", superadmin_id=1
        ),
    )
    with db.get_conn() as conn:
        conn.execute("DELETE FROM spieler WHERE id=112")

    # Eine widerrufene Mitgliedschaft ist keine Berechtigung, weiterhin
    # Spieler eines Kundenmandanten zu verwalten oder mitzulöschen.
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO trainer_mandanten (benutzer_id, verein_id, aktiv)
               VALUES (201, 100, 0)"""
        )
    spieler(113, 100, 201)
    erwartet_value_error(
        "Deaktivierte Mandantenzuordnung blockiert die Löschung",
        lambda: db.kunde_loeschziel_pruefen(
            100, 101, erwartete_kundennummer="APH-000100", superadmin_id=1
        ),
    )
    with db.get_conn() as conn:
        conn.execute("DELETE FROM spieler WHERE id=113")
        conn.execute("DELETE FROM trainer_mandanten WHERE benutzer_id=201 AND verein_id=100")


def test_atomic_delete_and_retention() -> None:
    result = db.kunde_loeschen(
        100,
        101,
        1,
        erwartete_kundennummer="APH-000100",
    )
    check(
        "Richtige Vertragskundennummer erlaubt die gemeinsame Löschung",
        result["n_spieler"] == 1 and result["n_benutzer"] == 1,
    )
    with db.get_conn() as conn:
        trainer = conn.execute("SELECT 1 FROM benutzer WHERE id=101").fetchone()
        spieler_row = conn.execute("SELECT 1 FROM spieler WHERE id=110").fetchone()
        mandant = conn.execute(
            "SELECT kundennummer, lizenz_status FROM vereine WHERE id=100"
        ).fetchone()
        rechnung = conn.execute(
            "SELECT verein_id FROM rechnungen WHERE rechnungsnummer='R-100'"
        ).fetchone()
        audit = conn.execute(
            "SELECT benutzer_id FROM audit_log WHERE aktion='test_vor_loeschung'"
        ).fetchone()
        loeschaudit = conn.execute(
            """SELECT superadmin_id FROM audit_log
                 WHERE aktion='kunde_endgueltig_geloescht'"""
        ).fetchone()
        zuordnung = conn.execute(
            "SELECT 1 FROM trainer_mandanten WHERE verein_id=100"
        ).fetchone()
    check(
        "Technischer Mandant, Benutzer, Spieler und Mandantenzuordnung werden gemeinsam bereinigt",
        trainer is None
        and spieler_row is None
        and mandant["kundennummer"] == "[gelöscht]"
        and mandant["lizenz_status"] == "geloescht"
        and zuordnung is None,
    )
    check(
        "Rechnungen und Audit-Nachweis bleiben anonymisiert erhalten",
        rechnung
        and rechnung["verein_id"] == 100
        and audit
        and audit["benutzer_id"] is None
        and loeschaudit
        and loeschaudit["superadmin_id"] == 1,
    )


if __name__ == "__main__":
    try:
        setup()
        test_identity_and_confirmation()
        test_fail_closed_consistency_guards()
        test_atomic_delete_and_retention()
    finally:
        db.DB_PATH = ORIGINAL_DB
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    print(f"\nErgebnis: {PASS} PASS, {FAIL} FAIL")
    sys.exit(0 if FAIL == 0 else 1)