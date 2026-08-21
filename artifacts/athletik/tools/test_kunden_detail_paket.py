#!/usr/bin/env python3
"""Regressionen für Legacy-Pakete in der Kunden-Detailansicht."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["ATHLETIK_DB_PATH"] = _db_file.name

import database
database.init_db()

from license import LIZENZ_TYPEN
from modules.kundenverwaltung import _detail_kundennummer, _detail_paket_key


class TestKundenDetailLegacyPakete(unittest.TestCase):
    def test_legacy_paketwerte_werden_im_richtigen_vertragspartner_kontext_aufgeloest(self):
        cases = [
            ("PRO", False, "VEREIN_PRO"),
            ("BASIC", False, "VEREIN_BASIC"),
            ("PRO", True, "TRAINER_PRO"),
            ("BASIC", True, "TRAINER_BASIC"),
        ]
        for raw, technisch, expected in cases:
            with self.subTest(raw=raw, technisch=technisch):
                key = _detail_paket_key(raw, technisch)
                self.assertEqual(key, expected)

        self.assertEqual(LIZENZ_TYPEN["VEREIN_PRO"]["preis_monat"], 39.99)
        self.assertEqual(LIZENZ_TYPEN["VEREIN_PRO"]["preis_jahr"], 399.0)

    def test_unbekanntes_paket_bleibt_nicht_zugeordnet(self):
        self.assertIsNone(_detail_paket_key("ALT_UNBEKANNT", False))
        self.assertIsNone(_detail_paket_key(None, True))

    def test_vereinsvertrag_und_kundennummer_werden_nicht_vom_benutzer_ueberschrieben(self):
        with database.get_conn() as conn:
            verein_id = conn.execute(
                """INSERT INTO vereine
                   (name, kundennummer, lizenztyp, lizenz_status, aktiv)
                   VALUES ('FC Vertragsquelle', 'APH-VEREIN-001', 'PRO', 'active', 1)"""
            ).lastrowid
            conn.execute(
                """INSERT INTO benutzer
                   (verein_id, vorname, nachname, email, passwort_hash, rolle,
                    kundennummer, lizenztyp, lizenz_status, aktiv)
                   VALUES (?, 'Alt', 'Trainer', 'alt@test.invalid', 'hash', 'Vereinsadmin',
                           'APH-BENUTZER-ALT', 'TRAINER_BASIC', 'trial', 1)""",
                (verein_id,),
            )

        daten = database.kunde_vollstaendig_laden(verein_id=verein_id)
        verein = daten["verein"]
        benutzer = daten["benutzer"]

        self.assertEqual(_detail_paket_key(verein["lizenztyp"], False), "VEREIN_PRO")
        self.assertEqual(_detail_kundennummer(verein, benutzer), "APH-VEREIN-001")
        self.assertNotEqual(_detail_kundennummer(verein, benutzer), benutzer["kundennummer"])


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    finally:
        Path(_db_file.name).unlink(missing_ok=True)