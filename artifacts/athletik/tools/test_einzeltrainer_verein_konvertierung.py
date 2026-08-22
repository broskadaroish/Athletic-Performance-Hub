#!/usr/bin/env python3
"""Regressionen für die sichere Einzeltrainer-zu-Verein-Konvertierung.

Ausführen:
    cd artifacts/athletik && python tools/test_einzeltrainer_verein_konvertierung.py

Die Suite nutzt ausschließlich eine temporäre SQLite-Datenbank. Sie verändert
keine lokale Entwicklungs- oder Produktionsdatenbank.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DB = Path(tempfile.mkdtemp(prefix="aph-konvertierung-")) / "test.db"
os.environ["ATHLETIK_DB_PATH"] = str(TEST_DB)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from license import get_lizenz_info


database.DB_PATH = str(TEST_DB)
database.init_db()


class TestEinzeltrainerZuVereinKonvertierung(unittest.TestCase):
    _nummer = 0

    @classmethod
    def setUpClass(cls) -> None:
        with database.get_conn() as conn:
            cls.superadmin_id = conn.execute(
                """INSERT INTO benutzer
                   (email, passwort_hash, rolle, aktiv, vorname, nachname)
                   VALUES ('superadmin-konvertierung@test.invalid', 'hash',
                           'Superadmin', 1, 'Super', 'Admin')"""
            ).lastrowid

    @classmethod
    def _next(cls) -> int:
        cls._nummer += 1
        return cls._nummer

    def _technischer_trainer(
        self,
        *,
        paket: str,
        status: str = "trial",
        zweiter_direkter_benutzer: bool = False,
        inhaber_aktiv: int = 1,
    ) -> tuple[int, int, dict]:
        nummer = self._next()
        original = {
            "kundennummer": f"APH-MANDANT-{nummer}",
            "testphase_bis": "2031-07-15",
            "lizenz_bis": "2031-12-31",
            "stripe_customer_id": f"cus_konvertierung_{nummer}",
            "stripe_subscription_id": None,
            "lizenz_status": status,
        }
        with database.get_conn() as conn:
            verein_id = conn.execute(
                """INSERT INTO vereine
                   (name, aktiv, ist_technischer_mandant, kundennummer,
                    lizenztyp, lizenz_status, testphase_bis, lizenz_bis,
                    stripe_customer_id, stripe_subscription_id)
                   VALUES (?, 1, 1, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"Technischer Mandant {nummer}",
                    original["kundennummer"],
                    paket,
                    original["lizenz_status"],
                    original["testphase_bis"],
                    original["lizenz_bis"],
                    original["stripe_customer_id"],
                    original["stripe_subscription_id"],
                ),
            ).lastrowid
            benutzer_id = conn.execute(
                """INSERT INTO benutzer
                   (verein_id, email, passwort_hash, rolle, aktiv, kundennummer,
                    lizenztyp, lizenz_status, testphase_bis)
                   VALUES (?, ?, 'hash', 'Trainer', 1, ?, 'TRAINER_BASIC',
                           'active', '2029-01-01')""",
                (
                    verein_id,
                    f"trainer-konvertierung-{nummer}@test.invalid",
                    f"APH-BENUTZER-{nummer}",
                ),
            ).lastrowid
            conn.execute(
                "INSERT INTO spieler (name, verein_id, trainer_id) VALUES (?, ?, ?)",
                (f"Spieler {nummer}", verein_id, benutzer_id),
            )
            if zweiter_direkter_benutzer:
                conn.execute(
                    """INSERT INTO benutzer
                       (verein_id, email, passwort_hash, rolle, aktiv)
                       VALUES (?, ?, 'hash', 'Trainer', 1)""",
                    (verein_id, f"zweiter-trainer-{nummer}@test.invalid"),
                )
            if not inhaber_aktiv:
                conn.execute(
                    "UPDATE benutzer SET aktiv=0 WHERE id=?",
                    (benutzer_id,),
                )
        database.trainer_mandant_hinzufuegen(benutzer_id, verein_id, "Trainer")
        return verein_id, benutzer_id, original

    def _konvertieren_und_pruefen(self, ausgangspaket: str, zielpaket: str) -> None:
        verein_id, benutzer_id, original = self._technischer_trainer(paket=ausgangspaket)
        with database.get_conn() as conn:
            vorher_vereine = conn.execute("SELECT COUNT(*) FROM vereine").fetchone()[0]
            vorher_spieler = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (verein_id,)
            ).fetchone()[0]

        ergebnis = database.einzeltrainer_zu_verein_konvertieren(
            verein_id,
            benutzer_id,
            zielpaket,
            superadmin_id=self.superadmin_id,
        )

        self.assertEqual(ergebnis["verein_id"], verein_id)
        self.assertEqual(ergebnis["benutzer_id"], benutzer_id)
        self.assertEqual(ergebnis["kundennummer"], original["kundennummer"])
        self.assertEqual(ergebnis["stripe_customer_id"], original["stripe_customer_id"])

        with database.get_conn() as conn:
            verein = dict(
                conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone()
            )
            benutzer = dict(
                conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone()
            )
            mitgliedschaft = dict(
                conn.execute(
                    """SELECT rolle_im_verein, aktiv FROM trainer_mandanten
                       WHERE benutzer_id=? AND verein_id=?""",
                    (benutzer_id, verein_id),
                ).fetchone()
            )
            nachher_vereine = conn.execute("SELECT COUNT(*) FROM vereine").fetchone()[0]
            nachher_spieler = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (verein_id,)
            ).fetchone()[0]
            audit = conn.execute(
                """SELECT COUNT(*) FROM audit_log
                   WHERE benutzer_id=? AND aktion='einzeltrainer_zu_verein_konvertiert'""",
                (benutzer_id,),
            ).fetchone()[0]

        self.assertEqual(nachher_vereine, vorher_vereine, "Es wurde ein zweiter Verein angelegt")
        self.assertEqual(nachher_spieler, vorher_spieler, "Spieler wurden verschoben oder gelöscht")
        self.assertEqual(verein["ist_technischer_mandant"], 0)
        self.assertEqual(verein["lizenztyp"], zielpaket)
        self.assertEqual(verein["kundennummer"], original["kundennummer"])
        self.assertEqual(verein["lizenz_status"], original["lizenz_status"])
        self.assertEqual(verein["testphase_bis"], original["testphase_bis"])
        self.assertEqual(verein["lizenz_bis"], original["lizenz_bis"])
        self.assertEqual(verein["stripe_customer_id"], original["stripe_customer_id"])
        self.assertIsNone(verein["stripe_subscription_id"])
        self.assertEqual(benutzer["rolle"], "Vereinsadmin")
        self.assertEqual(benutzer["kundennummer"], original["kundennummer"].replace("MANDANT", "BENUTZER"))
        self.assertEqual(benutzer["lizenztyp"], "TRAINER_BASIC", "Legacy-Benutzerlizenz darf nicht überschrieben werden")
        self.assertEqual(mitgliedschaft, {"rolle_im_verein": "Vereinsadmin", "aktiv": 1})
        self.assertEqual(audit, 1)

        lizenzinfo = get_lizenz_info(verein)
        self.assertEqual(lizenzinfo["lizenz_typ"], zielpaket)
        self.assertEqual(lizenzinfo["testphase_bis"], original["testphase_bis"])
        self.assertEqual(lizenzinfo["lizenz_status"], original["lizenz_status"])

        kunden = [k for k in database.kunden_liste_laden() if k.get("verein_id") == verein_id]
        self.assertEqual(len(kunden), 1, "Der konvertierte Vertragspartner muss genau einmal erscheinen")
        self.assertEqual(kunden[0]["kundentyp"], "Verein")
        self.assertEqual(kunden[0]["kundennummer"], original["kundennummer"])
        self.assertEqual(kunden[0]["benutzer_id"], benutzer_id)
        self.assertNotIn(
            benutzer_id,
            [k["benutzer_id"] for k in database.kunden_liste_laden() if k["kundentyp"] == "Einzeltrainer"],
        )
        self.assertIn(verein_id, [v["id"] for v in database.alle_vereine_lizenz()])
        self.assertNotIn(benutzer_id, [b["id"] for b in database.alle_trainer_lizenz()])
        self.assertIn(verein_id, [v["id"] for v in database.vereine_laden()])

        detail = database.kunde_vollstaendig_laden(verein_id, benutzer_id)
        self.assertEqual(detail["verein"]["id"], verein_id)
        self.assertFalse(detail["verein"]["ist_technischer_mandant"])
        self.assertEqual(detail["benutzer"]["rolle"], "Vereinsadmin")

    def test_alle_trainer_zu_verein_kombinationen(self) -> None:
        for ausgangspaket, zielpaket in (
            ("TRAINER_BASIC", "VEREIN_BASIC"),
            ("TRAINER_BASIC", "VEREIN_PRO"),
            ("TRAINER_PRO", "VEREIN_BASIC"),
            ("TRAINER_PRO", "VEREIN_PRO"),
        ):
            with self.subTest(ausgangspaket=ausgangspaket, zielpaket=zielpaket):
                self._konvertieren_und_pruefen(ausgangspaket, zielpaket)

    def test_inkonsistenter_technischer_mandant_mit_vereinspaket_wird_bereinigt(self) -> None:
        self._konvertieren_und_pruefen("VEREIN_PRO", "VEREIN_PRO")

    def test_historisches_vereinspaket_ist_als_reparierbarer_trainer_erreichbar(self) -> None:
        verein_id, benutzer_id, original = self._technischer_trainer(paket="VEREIN_PRO")
        kunden = [
            kunde for kunde in database.kunden_liste_laden()
            if kunde.get("vertrag_verein_id") == verein_id
        ]
        trainer = [
            konto for konto in database.alle_trainer_lizenz()
            if konto["id"] == benutzer_id
        ]
        from modules import lizenz_page
        dialog_zeilen = lizenz_page._sa_normalize([], trainer)

        self.assertEqual(len(kunden), 1)
        self.assertEqual(kunden[0]["kundentyp"], "Einzeltrainer")
        self.assertEqual(kunden[0]["kundennummer"], original["kundennummer"])
        self.assertEqual(len(trainer), 1)
        self.assertEqual(trainer[0]["vertrag_verein_id"], verein_id)
        self.assertEqual(trainer[0]["lizenztyp"], "VEREIN_PRO")
        self.assertEqual(len(dialog_zeilen), 1)
        self.assertEqual(dialog_zeilen[0]["_typ"], "trainer")
        self.assertEqual(dialog_zeilen[0]["_vertrag_verein_id"], verein_id)
        self.assertEqual(dialog_zeilen[0]["_paket_key"], "VEREIN_PRO")
        self.assertNotIn(verein_id, [verein["id"] for verein in database.alle_vereine_lizenz()])

    def test_falsche_berechtigung_aendert_nichts(self) -> None:
        verein_id, benutzer_id, original = self._technischer_trainer(paket="TRAINER_BASIC")
        with self.assertRaises(PermissionError):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_PRO", superadmin_id=benutzer_id
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(verein["kundennummer"], original["kundennummer"])
        self.assertEqual(benutzer["rolle"], "Trainer")

    def test_mehrere_direkte_benutzer_blockieren_ohne_teilzustand(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(
            paket="TRAINER_PRO", zweiter_direkter_benutzer=True
        )
        with self.assertRaisesRegex(ValueError, "genau ein direkt"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_BASIC", superadmin_id=self.superadmin_id
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_PRO")
        self.assertEqual(benutzer["rolle"], "Trainer")

    def test_inaktiver_inhaber_wird_ohne_teilzustand_abgelehnt(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(
            paket="TRAINER_BASIC", inhaber_aktiv=0
        )
        with self.assertRaisesRegex(ValueError, "aktives Inhaberkonto"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_PRO", superadmin_id=self.superadmin_id
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["aktiv"], 0)
        self.assertEqual(benutzer["rolle"], "Trainer")

    def test_weitere_aktive_mandantschaft_blockiert_ohne_rechteausweitung(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(paket="TRAINER_BASIC")
        with database.get_conn() as conn:
            fremdverein_id = conn.execute(
                """INSERT INTO vereine (name, aktiv, ist_technischer_mandant)
                   VALUES (?, 1, 0)""",
                (f"Nebenverein {self._next()}",),
            ).lastrowid
        database.trainer_mandant_hinzufuegen(benutzer_id, fremdverein_id, "Trainer")

        with self.assertRaisesRegex(ValueError, "weiteren aktiven Mandantenmitgliedschaften"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_PRO", superadmin_id=self.superadmin_id
            )

        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
            mitgliedschaften = [
                dict(row) for row in conn.execute(
                    """SELECT verein_id, rolle_im_verein, aktiv
                         FROM trainer_mandanten
                        WHERE benutzer_id=?
                        ORDER BY verein_id""",
                    (benutzer_id,),
                ).fetchall()
            ]
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["rolle"], "Trainer")
        self.assertEqual(
            mitgliedschaften,
            [
                {"verein_id": verein_id, "rolle_im_verein": "Trainer", "aktiv": 1},
                {"verein_id": fremdverein_id, "rolle_im_verein": "Trainer", "aktiv": 1},
            ],
        )

    def test_fehlende_zielmitgliedschaft_blockiert_ohne_teilzustand(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(paket="TRAINER_BASIC")
        with database.get_conn() as conn:
            conn.execute(
                "DELETE FROM trainer_mandanten WHERE benutzer_id=? AND verein_id=?",
                (benutzer_id, verein_id),
            )
        with self.assertRaisesRegex(ValueError, "bestehende aktive Mandantenmitgliedschaft"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_PRO", superadmin_id=self.superadmin_id
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
            mitgliedschaft = conn.execute(
                "SELECT 1 FROM trainer_mandanten WHERE benutzer_id=? AND verein_id=?",
                (benutzer_id, verein_id),
            ).fetchone()
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["rolle"], "Trainer")
        self.assertIsNone(mitgliedschaft)

    def test_inaktive_zielmitgliedschaft_blockiert_ohne_reaktivierung(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(paket="TRAINER_BASIC")
        with database.get_conn() as conn:
            conn.execute(
                """UPDATE trainer_mandanten SET aktiv=0
                    WHERE benutzer_id=? AND verein_id=?""",
                (benutzer_id, verein_id),
            )
        with self.assertRaisesRegex(ValueError, "bestehende aktive Mandantenmitgliedschaft"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "VEREIN_PRO", superadmin_id=self.superadmin_id
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
            mitgliedschaft = dict(conn.execute(
                """SELECT rolle_im_verein, aktiv FROM trainer_mandanten
                    WHERE benutzer_id=? AND verein_id=?""",
                (benutzer_id, verein_id),
            ).fetchone())
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["rolle"], "Trainer")
        self.assertEqual(mitgliedschaft, {"rolle_im_verein": "Trainer", "aktiv": 0})

    def test_unerlaubtes_zielpaket_wird_vor_transaktion_abgelehnt(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(paket="TRAINER_BASIC")
        with self.assertRaisesRegex(ValueError, "nur VEREIN_BASIC oder VEREIN_PRO"):
            database.einzeltrainer_zu_verein_konvertieren(
                verein_id, benutzer_id, "TRAINER_PRO", superadmin_id=self.superadmin_id
            )

    def test_benutzerlizenz_ist_bei_technischem_mandanten_serverseitig_blockiert(self) -> None:
        verein_id, benutzer_id, _ = self._technischer_trainer(paket="TRAINER_BASIC")
        with self.assertRaisesRegex(ValueError, "nur Einzeltrainer-Pakete"):
            database.trainer_lizenz_setzen(
                benutzer_id,
                "VEREIN_PRO",
                "active",
                "2032-01-01",
            )
        with self.assertRaisesRegex(ValueError, "mit Mandant"):
            database.trainer_lizenz_setzen(
                benutzer_id,
                "TRAINER_PRO",
                "active",
                "2032-01-01",
            )
        with database.get_conn() as conn:
            verein = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            benutzer = dict(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
        self.assertEqual(verein["ist_technischer_mandant"], 1)
        self.assertEqual(verein["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["lizenztyp"], "TRAINER_BASIC")
        self.assertEqual(benutzer["lizenz_status"], "active")

    def test_lizenzdialog_rendert_standalone_und_technischen_mandanten(self) -> None:
        """Fängt lokale Dialogfehler vor dem Speichern der Lizenz ab."""
        from contextlib import nullcontext
        from unittest.mock import patch
        from modules import lizenz_page

        technische_zeile = {
            "_typ": "trainer",
            "_name": "Technischer Trainer",
            "_display_status": "Aktiv",
            "_paket_key": "TRAINER_BASIC",
            "lizenz_status": "active",
            "lizenz_bis": "2031-12-31",
            "_vertrag_verein_id": 42,
            "gesperrt": False,
        }
        historische_standalone_zeile = {
            **technische_zeile,
            "_name": "Standalone Trainer",
            # Ein historisch fehlerhaftes Vereinspaket muss auf die sichere
            # Trainer-Auswahl zurückfallen statt den Dialog abstürzen zu lassen.
            "_paket_key": "VEREIN_PRO",
            "_vertrag_verein_id": None,
        }

        def selectbox(_label, optionen, index=0, **_kwargs):
            return optionen[index]

        with (
            patch.object(lizenz_page.st, "markdown"),
            patch.object(lizenz_page.st, "columns", return_value=(nullcontext(), nullcontext())),
            patch.object(lizenz_page.st, "selectbox", side_effect=selectbox),
            patch.object(lizenz_page.st, "date_input"),
            patch.object(lizenz_page.st, "number_input", return_value=0),
            patch.object(lizenz_page.st, "button", return_value=False),
        ):
            for row in (technische_zeile, historische_standalone_zeile):
                with self.subTest(name=row["_name"]):
                    lizenz_page._sa_edit_dialog.__wrapped__(row)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False).result
    try:
        TEST_DB.unlink(missing_ok=True)
        TEST_DB.parent.rmdir()
    except OSError:
        pass
    raise SystemExit(0 if result.wasSuccessful() else 1)