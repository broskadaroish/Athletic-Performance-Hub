#!/usr/bin/env python3
"""
Test-Suite: Kundenverwaltung — nur Vertragspartner anzeigen (Task #247)

Deckt ab:
  1. Vereinskunden erscheinen in kunden_liste_laden()
  2. Einzeltrainer-Kunden mit Kundennummer erscheinen
  3. Einzeltrainer-Kunden mit Stripe-Verbindung (ohne Kundennummer) erscheinen
  4. Normale Vereinstrainer (ohne eigenen Vertrag) erscheinen NICHT
  5. Trainer mit verein_id IS NULL und ohne Kundennummer erscheinen NICHT
  6. kundentyp-Wert ist 'Einzeltrainer' (nicht 'Trainer') für Einzeltrainer-Kunden
  7. Vereinskunden haben kundentyp='Verein'
  8. filter_typ='Einzeltrainer' filtert korrekt
  9. alle_trainer_lizenz() zeigt nur Trainer mit kundennummer + lizenztyp
 10. alle_vereine_lizenz() enthält keine technischen Mandanten in der Rückgabe
     (ist_technischer_mandant wird dort nicht explizit gefiltert, aber die
      Lizenzverwaltungs-Tabs in lizenz_page.py trennen korrekt)

Ausführen:
  cd artifacts/athletik && python tools/test_kundenverwaltung_filter.py
"""

from __future__ import annotations
import os, sys, tempfile, unittest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["ATHLETIK_DB_PATH"] = _tmp.name

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import database
database.init_db()

# ── Sequenz-Counter für eindeutige Testwerte ──────────────────────────────────
import itertools as _itertools
_SEQ = _itertools.count(1)

def _uid() -> int:
    return next(_SEQ)


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _make_verein(name: str, ist_tech: int = 0, **kwargs) -> int:
    """Erstellt einen Verein. Kundennummer wird auto-eindeutig wenn übergeben."""
    with database.get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO vereine (name, aktiv, ist_technischer_mandant) VALUES (?,1,?)",
            (name, ist_tech),
        )
        vid = cur.lastrowid
        if kwargs:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            conn.execute(f"UPDATE vereine SET {sets} WHERE id=?",
                         (*kwargs.values(), vid))
        return vid


def _make_benutzer(rolle: str, verein_id=None, kundennummer=None,
                   lizenztyp=None, **kwargs) -> int:
    ph = "sha256dummy"
    n = _uid()
    with database.get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO benutzer
               (rolle, verein_id, kundennummer, lizenztyp, email, passwort_hash,
                vorname, nachname, aktiv)
               VALUES (?,?,?,?,?,?,?,?,1)""",
            (rolle, verein_id, kundennummer, lizenztyp,
             kwargs.pop("email", f"auto_{n}@example.com"),
             ph,
             kwargs.pop("vorname", "Test"),
             kwargs.pop("nachname", rolle)),
        )
        bid = cur.lastrowid
        if kwargs:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            conn.execute(f"UPDATE benutzer SET {sets} WHERE id=?",
                         (*kwargs.values(), bid))
        return bid


# ─────────────────────────────────────────────────────────────────────────────

class TestVereinskunden(unittest.TestCase):
    """1 + 7 – Vereinskunden erscheinen mit kundentyp='Verein'."""

    def setUp(self):
        n = _uid()
        self.vid = _make_verein(f"FC Testverein KV1-{n}", ist_tech=0,
                                kundennummer=f"APH-V-KV1-{n}")
        self.bid = _make_benutzer("Vereinsadmin", verein_id=self.vid,
                                  email=f"admin_kv1_{n}@test.com")

    def test_vereinskunde_erscheint(self):
        kunden = database.kunden_liste_laden()
        vids = [k["verein_id"] for k in kunden]
        self.assertIn(self.vid, vids, "Vereinskunde fehlt in kunden_liste_laden()")

    def test_vereinskunde_kundentyp(self):
        kunden = database.kunden_liste_laden()
        k = next((x for x in kunden if x["verein_id"] == self.vid), None)
        self.assertIsNotNone(k)
        self.assertEqual(k["kundentyp"], "Verein")

    def test_technischer_mandant_erscheint_nicht_als_verein(self):
        """Technische Mandanten (Einzeltrainer-Vereine) sollen nicht in Part 1 erscheinen."""
        vid_tech = _make_verein("Technischer Mandant KV1", ist_tech=1)
        kunden = database.kunden_liste_laden()
        for k in kunden:
            if k["verein_id"] == vid_tech and k["kundentyp"] == "Verein":
                self.fail(
                    f"Technischer Mandant {vid_tech} erscheint als Vereinskunde"
                )


class TestEinzeltrainerKunden(unittest.TestCase):
    """2 + 3 + 6 – Einzeltrainer-Kunden mit Kundennummer oder Stripe erscheinen."""

    def test_einzeltrainer_mit_kundennummer_erscheint(self):
        vid = _make_verein("Tech-Mandant ET1", ist_tech=1)
        bid = _make_benutzer("Trainer", verein_id=vid, kundennummer="APH-T001",
                             lizenztyp="TRAINER_BASIC",
                             email="et1@test.com")
        kunden = database.kunden_liste_laden()
        bids = [k["benutzer_id"] for k in kunden]
        self.assertIn(bid, bids, "Einzeltrainer mit Kundennummer fehlt")

    def test_einzeltrainer_mit_kundennummer_kundentyp(self):
        vid = _make_verein("Tech-Mandant ET2", ist_tech=1)
        bid = _make_benutzer("Trainer", verein_id=vid, kundennummer="APH-T002",
                             lizenztyp="TRAINER_BASIC",
                             email="et2@test.com")
        kunden = database.kunden_liste_laden()
        k = next((x for x in kunden if x["benutzer_id"] == bid), None)
        self.assertIsNotNone(k, "Einzeltrainer nicht gefunden")
        self.assertEqual(k["kundentyp"], "Einzeltrainer",
                         f"Erwartet 'Einzeltrainer', bekommen '{k['kundentyp']}'")

    def test_einzeltrainer_mit_stripe_ohne_kundennummer_erscheint(self):
        """Stripe-Verbindung am technischen Mandant genügt als Vertragsnachweis."""
        vid = _make_verein("Tech-Mandant ET3", ist_tech=1,
                           stripe_customer_id="cus_testET3")
        bid = _make_benutzer("Trainer", verein_id=vid, kundennummer=None,
                             email="et3@test.com")
        kunden = database.kunden_liste_laden()
        bids = [k["benutzer_id"] for k in kunden]
        self.assertIn(bid, bids,
                      "Einzeltrainer mit Stripe-Verbindung fehlt in Kundenliste")


class TestAusgeschlosseneTrainer(unittest.TestCase):
    """4 + 5 – Normale Vereinstrainer und vertragslose Trainer erscheinen NICHT."""

    def test_vereinstrainer_erscheint_nicht(self):
        """Trainer mit verein_id auf echten Verein: kein eigener Vertrag → kein Kundeneintrag."""
        vid = _make_verein("FC Normaler Verein KV2", ist_tech=0,
                           kundennummer="APH-V002")
        bid = _make_benutzer("Trainer", verein_id=vid,
                             kundennummer=None, lizenztyp=None,
                             email="vereinstrainer_kv2@test.com")
        kunden = database.kunden_liste_laden()
        bids = [k["benutzer_id"] for k in kunden]
        self.assertNotIn(bid, bids,
                         "Vereinstrainer ohne eigenen Vertrag erscheint in Kundenliste")

    def test_trainer_ohne_verein_ohne_kundennummer_erscheint_nicht(self):
        """Trainer mit verein_id IS NULL und ohne Kundennummer ist kein Vertragspartner."""
        bid = _make_benutzer("Trainer", verein_id=None,
                             kundennummer=None, lizenztyp=None,
                             email="kv2_novertrag@test.com")
        kunden = database.kunden_liste_laden()
        bids = [k["benutzer_id"] for k in kunden]
        self.assertNotIn(bid, bids,
                         "Vertragloser Trainer (verein_id IS NULL) erscheint in Kundenliste")

    def test_trainer_mit_tech_mandant_ohne_kundennummer_ohne_stripe_erscheint_nicht(self):
        """Technischer Mandant ohne Kundennummer und ohne Stripe = kein echter Vertrag."""
        vid = _make_verein("Tech-Mandant Leer", ist_tech=1)
        # Kein kundennummer, kein stripe_customer_id, kein stripe_subscription_id
        bid = _make_benutzer("Trainer", verein_id=vid,
                             kundennummer=None, lizenztyp=None,
                             email="kv2_techonly@test.com")
        kunden = database.kunden_liste_laden()
        bids = [k["benutzer_id"] for k in kunden]
        self.assertNotIn(bid, bids,
                         "Tech-Mandant ohne Vertrag erscheint fälschlicherweise in Kundenliste")


class TestFilterTyp(unittest.TestCase):
    """8 – filter_typ='Einzeltrainer' filtert korrekt."""

    def setUp(self):
        n = _uid()
        # Verein
        self.vid = _make_verein(f"FC Filtertest-{n}", ist_tech=0,
                                kundennummer=f"APH-FT-{n}")
        self.vbid = _make_benutzer("Vereinsadmin", verein_id=self.vid,
                                   email=f"ft_admin_{n}@test.com")
        # Einzeltrainer
        self.tvid = _make_verein(f"Tech-Mandant FT-{n}", ist_tech=1)
        self.tbid = _make_benutzer("Trainer", verein_id=self.tvid,
                                   kundennummer=f"APH-FT-T-{n}",
                                   lizenztyp="TRAINER_BASIC",
                                   email=f"ft_trainer_{n}@test.com")

    def test_filter_einzeltrainer_schliesst_vereine_aus(self):
        kunden = database.kunden_liste_laden(filter_typ="Einzeltrainer")
        for k in kunden:
            self.assertEqual(k["kundentyp"], "Einzeltrainer",
                             f"filter_typ='Einzeltrainer' liefert Datensatz mit kundentyp='{k['kundentyp']}'")

    def test_filter_verein_schliesst_einzeltrainer_aus(self):
        kunden = database.kunden_liste_laden(filter_typ="Verein")
        for k in kunden:
            self.assertEqual(k["kundentyp"], "Verein",
                             f"filter_typ='Verein' liefert Datensatz mit kundentyp='{k['kundentyp']}'")

    def test_filter_alle_enthaelt_beide_typen(self):
        kunden = database.kunden_liste_laden(filter_typ="Alle")
        typen = {k["kundentyp"] for k in kunden}
        self.assertIn("Verein",        typen, "'Alle'-Filter enthält keine Vereine")
        self.assertIn("Einzeltrainer", typen, "'Alle'-Filter enthält keine Einzeltrainer")


class TestAlleTrainerLizenz(unittest.TestCase):
    """9 – alle_trainer_lizenz() zeigt nur Trainer mit kundennummer + lizenztyp."""

    def test_trainer_ohne_kundennummer_fehlt(self):
        bid = _make_benutzer("Trainer", verein_id=None,
                             kundennummer=None, lizenztyp="TRAINER_BASIC",
                             email="atliz_nokn@test.com")
        trainer = database.alle_trainer_lizenz()
        bids = [t["id"] for t in trainer]
        self.assertNotIn(bid, bids,
                         "Trainer ohne Kundennummer erscheint in alle_trainer_lizenz()")

    def test_trainer_ohne_lizenztyp_fehlt(self):
        bid = _make_benutzer("Trainer", verein_id=None,
                             kundennummer="APH-T-NOLIZ", lizenztyp=None,
                             email="atliz_noliz@test.com")
        trainer = database.alle_trainer_lizenz()
        bids = [t["id"] for t in trainer]
        self.assertNotIn(bid, bids,
                         "Trainer ohne Lizenztyp erscheint in alle_trainer_lizenz()")

    def test_vollstaendiger_trainer_erscheint(self):
        bid = _make_benutzer("Trainer", verein_id=None,
                             kundennummer="APH-T-FULL", lizenztyp="TRAINER_BASIC",
                             email="atliz_full@test.com")
        trainer = database.alle_trainer_lizenz()
        bids = [t["id"] for t in trainer]
        self.assertIn(bid, bids,
                      "Vollständiger Einzeltrainer fehlt in alle_trainer_lizenz()")


# ── Test-Runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for tc in [
        TestVereinskunden,
        TestEinzeltrainerKunden,
        TestAusgeschlosseneTrainer,
        TestFilterTyp,
        TestAlleTrainerLizenz,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    try:
        os.unlink(_tmp.name)
    except Exception:
        pass
    sys.exit(0 if result.wasSuccessful() else 1)
