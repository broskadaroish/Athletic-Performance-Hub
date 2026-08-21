"""Regressionen für den sicheren CSV-/XLSX-Spielerimport."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest

from openpyxl import Workbook

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from spieler_import import (
    auto_mapping,
    build_preview,
    read_upload,
    revalidate_preview,
    validate_mapping,
)


POSITIONS = ["Torwart", "Zentrales Mittelfeld"]
LEVELS = ["Breitensport", "Leistungssport"]
STATUSES = ["Uneingeschränktes Mannschaftstraining", "Trainingspause"]


def _trainer_im_verein() -> tuple[int, int]:
    with database.get_conn() as conn:
        verein_id = conn.execute(
            "INSERT INTO vereine (name, aktiv, lizenztyp) VALUES (?, ?, ?)",
            ("Importverein", 1, "TRAINER_BASIC"),
        ).lastrowid
        trainer_id = conn.execute(
            """INSERT INTO benutzer
               (verein_id, vorname, nachname, email, passwort_hash, rolle, aktiv)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (verein_id, "Tina", "Trainer", "tina@test.de", "hash", "Trainer", 1),
        ).lastrowid
        conn.execute(
            """INSERT INTO trainer_mandanten
               (benutzer_id, verein_id, rolle_im_verein, aktiv)
               VALUES (?, ?, ?, ?)""",
            (trainer_id, verein_id, "Trainer", 1),
        )
    return verein_id, trainer_id


def _preview(rows, existing=None):
    return build_preview(
        rows,
        {
            "vorname": "Vorname",
            "nachname": "Nachname",
            "geburtsdatum": "Geburtsdatum",
            "geschlecht": "Geschlecht",
            "hauptposition": "Position",
            "nebenposition": None,
            "spielbein": None,
            "leistungsniveau": None,
            "mannschaft": None,
            "trainingsstatus": None,
        },
        existing or set(),
        positionen=POSITIONS,
        leistungsniveaus=LEVELS,
        trainingsstatus=STATUSES,
    )


class TestSpielerImport(unittest.TestCase):
    def setUp(self):
        self.old_db_path = database.DB_PATH
        file_descriptor, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(file_descriptor)
        database.DB_PATH = self.db_path
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.old_db_path
        os.unlink(self.db_path)

    def test_csv_mapping_und_sichere_normalisierung(self):
        headers, rows = read_upload(
            "Vorname;Nachname;Geburtsdatum;Geschlecht;Position\n"
            "Max;Mustermann;2008-03-15;m;Zentrales Mittelfeld\n".encode(),
            "kader.csv",
        )
        mapping = auto_mapping(headers)
        self.assertEqual(mapping["vorname"], "Vorname")
        self.assertEqual(mapping["nachname"], "Nachname")
        self.assertEqual(mapping["geburtsdatum"], "Geburtsdatum")
        self.assertFalse(validate_mapping(headers, mapping))

        preview = _preview(rows)
        self.assertEqual(preview[0]["status"], "🟡 Hinweis")
        self.assertEqual(preview[0]["geburtsdatum"], "15.03.2008")
        self.assertEqual(preview[0]["geschlecht"], "Männlich")
        self.assertTrue(preview[0]["altersklasse"])

    def test_formel_und_fehlende_pflichtfelder_sind_nicht_importierbar(self):
        preview = _preview([{
            "Vorname": "=HYPERLINK(\"https://example.test\")",
            "Nachname": "",
            "Geburtsdatum": "31.02.2020",
            "Geschlecht": "Männlich",
            "Position": "Torwart",
        }])
        self.assertEqual(preview[0]["status"], "🔴 Fehler")
        self.assertIn("keine erlaubte Eingabe", preview[0]["hinweis"])
        self.assertIn("fehlt", preview[0]["hinweis"])

    def test_dubletten_sind_nur_hinweis_und_nicht_aktualisierung(self):
        rows = [{
            "Vorname": "Max",
            "Nachname": "Mustermann",
            "Geburtsdatum": "15.03.2008",
            "Geschlecht": "Männlich",
            "Position": "Torwart",
        }]
        preview = _preview(rows, {("max", "mustermann", "15.03.2008")})
        self.assertEqual(preview[0]["status"], "🟡 Hinweis")
        self.assertIn("aktiven Mandanten", preview[0]["hinweis"])

    def test_xlsx_mit_formel_wird_abgelehnt(self):
        book = Workbook()
        sheet = book.active
        sheet.append(["Vorname", "Nachname", "Geburtsdatum"])
        sheet.append(["=NOW()", "Mustermann", "15.03.2008"])
        buffer = io.BytesIO()
        book.save(buffer)

        with self.assertRaisesRegex(ValueError, "Formeln sind nicht erlaubt"):
            read_upload(buffer.getvalue(), "kader.xlsx")

    def test_import_prueft_mandant_erneut(self):
        verein_id, trainer_id = _trainer_im_verein()
        with self.assertRaises(PermissionError):
            database.spieler_importieren(
                [{"vorname": "Max", "nachname": "Muster", "geburtsdatum": "15.03.2008"}],
                benutzer_id=trainer_id,
                rolle="Trainer",
                verein_id=verein_id + 100,
            )
        with database.get_conn() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM spieler").fetchone()[0], 0)

    def test_import_dublette_und_limit_werden_im_schreibvorgang_geprueft(self):
        verein_id, trainer_id = _trainer_im_verein()
        with database.get_conn() as conn:
            for number in range(19):
                conn.execute(
                    """INSERT INTO spieler
                       (name, vorname, nachname, geburtsdatum, trainer_id, verein_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (f"Vorname{number} Muster", f"Vorname{number}", "Muster",
                     f"01.01.{2000 + number}", trainer_id, verein_id),
                )
            conn.execute(
                """INSERT INTO spieler
                   (name, vorname, nachname, geburtsdatum, trainer_id, verein_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("Max Muster", "Max", "Muster", "15.03.2008", trainer_id, verein_id),
            )

        result = database.spieler_importieren(
            [
                {"vorname": "Max", "nachname": "Muster", "geburtsdatum": "15.03.2008"},
                {"vorname": "Neu", "nachname": "Spieler", "geburtsdatum": "15.03.2009"},
            ],
            benutzer_id=trainer_id,
            rolle="Trainer",
            verein_id=verein_id,
        )
        self.assertEqual(result, {"angelegt": 0, "uebersprungen": 1, "limit_blockiert": 1})

    def test_import_schreibpfad_lehnt_ungueltige_stammdaten_ab(self):
        verein_id, trainer_id = _trainer_im_verein()
        result = database.spieler_importieren(
            [
                {
                    "vorname": "Max", "nachname": "Muster", "geburtsdatum": "15.03.1899",
                    "hauptposition": "Zentrales Mittelfeld",
                },
                {
                    "vorname": "Lea", "nachname": "Muster", "geburtsdatum": "15.03.2009",
                    "hauptposition": "Unbekannte Position",
                },
                {
                    "vorname": "Mia", "nachname": "Muster", "geburtsdatum": "15.03.2009",
                    "hauptposition": "Torwart", "mannschaft": "=FORMULA()",
                },
            ],
            benutzer_id=trainer_id,
            rolle="Trainer",
            verein_id=verein_id,
        )
        self.assertEqual(result, {"angelegt": 0, "uebersprungen": 3, "limit_blockiert": 0})
        with database.get_conn() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM spieler").fetchone()[0], 0)

    def test_bearbeitete_vorschau_wird_serverseitig_neu_geprueft(self):
        preview = _preview([{
            "Vorname": "Max",
            "Nachname": "Muster",
            "Geburtsdatum": "15.03.2008",
            "Geschlecht": "Männlich",
            "Position": "Torwart",
        }])
        preview[0]["hauptposition"] = "Nicht vorhanden"
        checked = revalidate_preview(
            preview,
            set(),
            positionen=POSITIONS,
            leistungsniveaus=LEVELS,
            trainingsstatus=STATUSES,
        )
        self.assertEqual(checked[0]["status"], "🔴 Fehler")


if __name__ == "__main__":
    unittest.main()