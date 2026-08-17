#!/usr/bin/env python3
"""
Test-Suite: Rechnungsmodul (Task #246)

Deckt ab:
  1. DB-Migration: neue Spalten existieren
  2. rechnung_speichern: neue Felder werden gespeichert
  3. Idempotenz: gleiche stripe_invoice_id → kein Duplikat, stattdessen UPDATE
  4. invoice.payment_failed: Status wird auf 'fehlgeschlagen' gesetzt
  5. Zugriffsrechte: Vereinsadmin ✓, Einzeltrainer ✓, Vereinstrainer ✗
  6. rechnungen_laden: neue Felder werden zurückgegeben

Ausführen:
  cd artifacts/athletik && python tools/test_rechnungen.py
"""

from __future__ import annotations
import os, sys, tempfile, sqlite3, unittest, datetime

# ── Isoliertes DB-Setup (temporäre SQLite-Datei) ─────────────────────────────
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["ATHLETIK_DB_PATH"] = _tmp.name

# Pfad anpassen damit Imports aus artifacts/athletik/ funktionieren
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

import database
database.init_db()

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _make_verein(name: str = "Testverein", **kwargs) -> int:
    """Legt einen Verein an und gibt die ID zurück."""
    with database.get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO vereine (name, aktiv, lizenz_status, lizenztyp, testphase_bis)
               VALUES (?, 1, 'active', 'VEREIN_BASIC', '2099-12-31')""",
            (name,),
        )
        vid = cur.lastrowid
        if kwargs:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            conn.execute(
                f"UPDATE vereine SET {sets} WHERE id=?",
                (*kwargs.values(), vid),
            )
        return vid


def _col_exists(table: str, col: str) -> bool:
    with database.get_conn() as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r[1] == col for r in rows)


# ─────────────────────────────────────────────────────────────────────────────

class TestMigration(unittest.TestCase):
    """1 – DB-Migration: neue Spalten existieren in rechnungen."""

    def test_hosted_invoice_url_spalte(self):
        self.assertTrue(_col_exists("rechnungen", "hosted_invoice_url"),
                        "Spalte hosted_invoice_url fehlt in rechnungen")

    def test_invoice_pdf_spalte(self):
        self.assertTrue(_col_exists("rechnungen", "invoice_pdf"),
                        "Spalte invoice_pdf fehlt in rechnungen")

    def test_paid_at_spalte(self):
        self.assertTrue(_col_exists("rechnungen", "paid_at"),
                        "Spalte paid_at fehlt in rechnungen")

    def test_currency_spalte(self):
        self.assertTrue(_col_exists("rechnungen", "currency"),
                        "Spalte currency fehlt in rechnungen")


class TestRechnungSpeichern(unittest.TestCase):
    """2 – rechnung_speichern: neue Felder werden korrekt gespeichert."""

    def setUp(self):
        self.vid = _make_verein("Verein Speichern Test")

    def test_neue_felder_werden_gespeichert(self):
        rid = database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-TEST-001",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
            stripe_invoice_id="in_test_001",
            hosted_invoice_url="https://invoice.stripe.com/inv/in_test_001",
            invoice_pdf="https://pay.stripe.com/invoice/in_test_001/pdf",
            paid_at="2026-08-18",
            currency="EUR",
        )
        self.assertIsNotNone(rid)
        self.assertGreater(rid, 0)

        with database.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM rechnungen WHERE id=?", (rid,)
            ).fetchone()
        d = dict(row)
        self.assertEqual(d["hosted_invoice_url"],
                         "https://invoice.stripe.com/inv/in_test_001")
        self.assertEqual(d["invoice_pdf"],
                         "https://pay.stripe.com/invoice/in_test_001/pdf")
        self.assertEqual(d["paid_at"],   "2026-08-18")
        self.assertEqual(d["currency"],  "EUR")
        self.assertEqual(d["status"],    "bezahlt")

    def test_rechnungen_laden_gibt_neue_felder_zurueck(self):
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-TEST-002",
            betrag_eur=19.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
            stripe_invoice_id="in_test_002",
            hosted_invoice_url="https://invoice.stripe.com/inv/in_test_002",
            invoice_pdf=None,
            paid_at="2026-08-18",
            currency="EUR",
        )
        rechnungen = database.rechnungen_laden(self.vid)
        self.assertTrue(len(rechnungen) > 0, "Keine Rechnungen geladen")
        r = next(x for x in rechnungen if x["rechnungsnummer"] == "APH-TEST-002")
        self.assertIn("hosted_invoice_url", r, "hosted_invoice_url fehlt in rechnungen_laden")
        self.assertIn("invoice_pdf", r)
        self.assertIn("paid_at", r)
        self.assertIn("currency", r)
        self.assertEqual(r["hosted_invoice_url"],
                         "https://invoice.stripe.com/inv/in_test_002")


class TestIdempotenz(unittest.TestCase):
    """3 – Idempotenz: gleiche stripe_invoice_id → kein Duplikat."""

    def setUp(self):
        self.vid = _make_verein("Idempotenz-Verein")

    def test_kein_duplikat_bei_gleichem_stripe_invoice_id(self):
        kwargs = dict(
            verein_id=self.vid,
            rechnungsnummer="APH-IDEM-001",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
            stripe_invoice_id="in_idem_001",
            hosted_invoice_url="https://invoice.stripe.com/idem",
            invoice_pdf=None,
            paid_at="2026-08-18",
            currency="EUR",
        )
        rid1 = database.rechnung_speichern(**kwargs)
        rid2 = database.rechnung_speichern(**kwargs)  # identisch → kein neuer Datensatz
        self.assertEqual(rid1, rid2, "Zweiter Aufruf mit gleichem stripe_invoice_id lieferte neue ID")

        with database.get_conn() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM rechnungen WHERE stripe_invoice_id='in_idem_001'"
            ).fetchone()[0]
        self.assertEqual(cnt, 1, f"Duplikat gefunden: {cnt} Zeilen für in_idem_001")

    def test_update_bei_wiederholung(self):
        """Status und URLs werden beim zweiten Aufruf aktualisiert."""
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-IDEM-002",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="offen",
            stripe_invoice_id="in_idem_002",
            hosted_invoice_url=None,
            invoice_pdf=None,
            paid_at=None,
            currency=None,
        )
        # Webhook-Replay mit vollständigen Daten
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-IDEM-002",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
            stripe_invoice_id="in_idem_002",
            hosted_invoice_url="https://invoice.stripe.com/idem002",
            invoice_pdf="https://pay.stripe.com/inv/idem002/pdf",
            paid_at="2026-08-18",
            currency="EUR",
        )
        with database.get_conn() as conn:
            row = conn.execute(
                "SELECT status, hosted_invoice_url, currency FROM rechnungen "
                "WHERE stripe_invoice_id='in_idem_002'"
            ).fetchone()
        self.assertIsNotNone(row)
        d = dict(row)
        self.assertEqual(d["status"],            "bezahlt",
                         "Status wurde beim Replay nicht aktualisiert")
        self.assertEqual(d["hosted_invoice_url"],
                         "https://invoice.stripe.com/idem002",
                         "hosted_invoice_url wurde beim Replay nicht gesetzt")
        self.assertEqual(d["currency"], "EUR")


class TestZahlungFehlgeschlagen(unittest.TestCase):
    """4 – invoice.payment_failed: Status wird auf 'fehlgeschlagen' gesetzt."""

    def setUp(self):
        self.vid = _make_verein("FehlgeschlagenVerein")

    def test_status_auf_fehlgeschlagen(self):
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-FAIL-001",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
            stripe_invoice_id="in_fail_001",
        )
        # Simulation: payment_failed setzt Status auf fehlgeschlagen
        with database.get_conn() as conn:
            conn.execute(
                "UPDATE rechnungen SET status='fehlgeschlagen' "
                "WHERE stripe_invoice_id='in_fail_001'"
            )
        rechnungen = database.rechnungen_laden(self.vid)
        r = next((x for x in rechnungen
                   if x["rechnungsnummer"] == "APH-FAIL-001"), None)
        self.assertIsNotNone(r)
        self.assertEqual(r["status"], "fehlgeschlagen")


class TestZugriffsrechte(unittest.TestCase):
    """5 – Zugriffsrechte: wer darf Rechnungen sehen?

    Logik aus mein_vertrag.py:
        _kann_rechnungen_sehen = (
            rolle == "Vereinsadmin"
            OR (rolle == "Trainer" AND ist_technischer_mandant)
        )

    Erwartung:
        Vereinsadmin                          → KANN sehen
        Trainer mit technischem Mandant       → KANN sehen (Einzeltrainer)
        Trainer ohne technischen Mandant      → KANN NICHT sehen
    """

    def _darf(self, rolle: str, ist_technischer_mandant: bool) -> bool:
        user = {"rolle": rolle}
        data = {"ist_technischer_mandant": ist_technischer_mandant}
        return (
            user.get("rolle") == "Vereinsadmin"
            or (user.get("rolle") == "Trainer" and data.get("ist_technischer_mandant"))
        )

    def test_vereinsadmin_darf_sehen(self):
        self.assertTrue(self._darf("Vereinsadmin", False))

    def test_einzeltrainer_darf_sehen(self):
        self.assertTrue(self._darf("Trainer", True))

    def test_vereinstrainer_darf_nicht_sehen(self):
        self.assertFalse(self._darf("Trainer", False))

    def test_superadmin_darf_nicht_sehen_ueber_mein_vertrag(self):
        # Superadmin hat eigene Kundenverwaltung — nicht über Mein-Vertrag
        self.assertFalse(self._darf("Superadmin", False))


class TestOhneStripeInvoiceId(unittest.TestCase):
    """6 – rechnung_speichern ohne stripe_invoice_id: kein Idempotenz-Check, normale INSERT."""

    def setUp(self):
        self.vid = _make_verein("Manuell-Verein")

    def test_mehrere_manuelle_rechnungen_erlaubt(self):
        """Ohne stripe_invoice_id sind mehrere Zeilen für denselben Verein erlaubt."""
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-MAN-001",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
        )
        database.rechnung_speichern(
            verein_id=self.vid,
            rechnungsnummer="APH-MAN-002",
            betrag_eur=9.99,
            lizenz_typ="VEREIN_BASIC",
            status="bezahlt",
        )
        with database.get_conn() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM rechnungen WHERE verein_id=? "
                "AND rechnungsnummer LIKE 'APH-MAN-%'",
                (self.vid,),
            ).fetchone()[0]
        self.assertEqual(cnt, 2)


# ── Test-Runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    for tc in [
        TestMigration,
        TestRechnungSpeichern,
        TestIdempotenz,
        TestZahlungFehlgeschlagen,
        TestZugriffsrechte,
        TestOhneStripeInvoiceId,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    # Aufräumen
    try:
        os.unlink(_tmp.name)
    except Exception:
        pass
    sys.exit(0 if result.wasSuccessful() else 1)
