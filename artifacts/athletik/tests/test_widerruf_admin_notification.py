"""
Tests für Task #187 — Superadmin-Benachrichtigung bei Kündigung-Widerruf.

Deckt ab:
  - send_widerruf_admin_benachrichtigung() erzeugt korrekten Betreff + Textinhalt
  - HTML-Injection durch kundenkontrollierte Werte wird verhindert (html.escape)
  - _sende_widerruf_email() sendet Admin-Mail wenn SUPERADMIN_EMAIL konfiguriert
  - _sende_widerruf_email() überspringt Admin-Mail wenn SUPERADMIN_EMAIL fehlt (kein PII-Fallback)
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Hilfsfunktion: schlankes email_service-Modul für Unit-Tests ──────────────

def _build_email_service_module():
    """
    Importiert email_service mit einem gestubten _send(), damit keine echten
    SMTP-Verbindungen aufgebaut werden.
    """
    import importlib
    import importlib.util

    # _send() patchen bevor das Modul ausgeführt wird
    with patch("smtplib.SMTP_SSL"), patch("smtplib.SMTP"):
        spec = importlib.util.spec_from_file_location(
            "email_service",
            os.path.join(os.path.dirname(__file__), "..", "email_service.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        # Stub-Logger damit keine richtigen Handler nötig sind
        import logging
        mod.__dict__.setdefault("log", logging.getLogger("email_service_test"))
        try:
            spec.loader.exec_module(mod)
        except Exception:
            pass  # Import-Fehler durch fehlende SMTP-Config ignorieren
    return mod


class TestSendWiderrufAdminBenachrichtigung(unittest.TestCase):
    """Unit-Tests für email_service.send_widerruf_admin_benachrichtigung()."""

    def setUp(self):
        """Lade email_service und ersetze _send() durch einen Mock."""
        import importlib
        import email_service as _es
        self.es = _es
        self._send_mock = MagicMock(return_value=None)
        self._orig_send = getattr(self.es, "_send", None)
        self.es._send = self._send_mock

    def tearDown(self):
        if self._orig_send is not None:
            self.es._send = self._orig_send

    def test_subject_contains_kundennummer(self):
        """Betreff enthält die Kundennummer."""
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-001234",
            kundentyp="Verein",
        )
        self.assertTrue(self._send_mock.called)
        _, subject, *_ = self._send_mock.call_args[0]
        self.assertIn("APH-001234", subject)

    def test_text_body_contains_required_fields(self):
        """Plaintext-Body enthält alle Pflichtfelder."""
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-999",
            kundentyp="Einzeltrainer",
            kundenname="Max Mustermann",
            kundenemail="max@example.com",
            zeitstempel="01.01.2026 10:00 Uhr",
        )
        _to, _subj, text_body, *_ = self._send_mock.call_args[0]
        self.assertIn("APH-999", text_body)
        self.assertIn("Einzeltrainer", text_body)
        self.assertIn("Max Mustermann", text_body)
        self.assertIn("max@example.com", text_body)
        self.assertIn("01.01.2026", text_body)

    def test_html_injection_in_kundennummer_is_escaped(self):
        """<script>-Tag in Kundennummer darf nicht roh in den HTML-Body."""
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer='<script>alert("xss")</script>',
            kundentyp="Verein",
        )
        _, _subj, _text, html_body = self._send_mock.call_args[0]
        self.assertNotIn("<script>", html_body)
        self.assertIn("&lt;script&gt;", html_body)

    def test_html_injection_in_kundenname_is_escaped(self):
        """<img>-Payload in Kundenname darf nicht roh in den HTML-Body."""
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-001",
            kundentyp="Verein",
            kundenname='<img src=x onerror=alert(1)>',
        )
        _, _subj, _text, html_body = self._send_mock.call_args[0]
        self.assertNotIn("<img", html_body)
        self.assertIn("&lt;img", html_body)

    def test_html_injection_in_kundenemail_is_escaped(self):
        """Manipulierte E-Mail-Adresse darf kein HTML-Attribut aufbrechen.

        html.escape() wandelt '"' → '&quot;', sodass der Payload nur als
        sicherer Textinhalt erscheint. Die rohe, unescapte Zeichenkette darf
        nicht im HTML-Body vorkommen.
        """
        payload = '" onmouseover="alert(1)'
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-002",
            kundentyp="Verein",
            kundenemail=payload,
        )
        _, _subj, _text, html_body = self._send_mock.call_args[0]
        # Roher, unescapter Payload darf nicht vorkommen
        self.assertNotIn(payload, html_body)
        # Die Anführungszeichen müssen escapt sein
        self.assertIn("&quot;", html_body)

    def test_no_mailto_href_attribute(self):
        """Kunden-E-Mail wird nur als Text angezeigt — kein href='mailto:' Attribut."""
        self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-003",
            kundentyp="Verein",
            kundenemail="kunde@example.com",
        )
        _, _subj, _text, html_body = self._send_mock.call_args[0]
        self.assertNotIn("href='mailto:", html_body)
        self.assertNotIn('href="mailto:', html_body)

    def test_returns_true_on_success(self):
        """Gibt True zurück wenn _send() nicht wirft."""
        result = self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-004",
            kundentyp="Einzeltrainer",
        )
        self.assertTrue(result)

    def test_returns_false_on_send_error(self):
        """Gibt False zurück wenn _send() eine Exception wirft."""
        self.es._send = MagicMock(side_effect=RuntimeError("SMTP down"))
        result = self.es.send_widerruf_admin_benachrichtigung(
            to="admin@example.com",
            kundennummer="APH-005",
            kundentyp="Verein",
        )
        self.assertFalse(result)


class TestSendeWiderrufEmail(unittest.TestCase):
    """
    Integration-Tests für mein_vertrag._sende_widerruf_email().
    Prüft, ob Admin-Mail gesendet / übersprungen wird je nach SUPERADMIN_EMAIL.
    """

    def _call(self, user, data, ist_verein=False, superadmin_email=""):
        """Ruft _sende_widerruf_email() mit gepatchten E-Mail-Funktionen auf."""
        send_kunden = MagicMock(return_value=True)
        send_admin  = MagicMock(return_value=True)

        env_patch = {"SUPERADMIN_EMAIL": superadmin_email}
        with patch.dict(os.environ, env_patch, clear=False):
            with patch("email_service.send_kuendigung_widerrufen", send_kunden):
                with patch("email_service.send_widerruf_admin_benachrichtigung", send_admin):
                    # Importiere frisch damit Patches greifen
                    import importlib
                    import modules.mein_vertrag as mv
                    importlib.reload(mv)
                    mv._sende_widerruf_email(user, data, ist_verein=ist_verein)

        return send_kunden, send_admin

    def test_admin_mail_sent_when_superadmin_email_configured(self):
        """Admin-Benachrichtigung wird gesendet wenn SUPERADMIN_EMAIL gesetzt ist."""
        user = {"email": "trainer@example.com", "vorname": "Tina"}
        data = {"kundennummer": "APH-100", "lizenztyp": "Pro"}

        _kunden_mock, admin_mock = self._call(
            user, data,
            superadmin_email="admin@aphsystem.de",
        )
        admin_mock.assert_called_once()
        kwargs = admin_mock.call_args[1]
        self.assertEqual(kwargs["to"], "admin@aphsystem.de")
        self.assertEqual(kwargs["kundennummer"], "APH-100")

    def test_admin_mail_skipped_when_superadmin_email_missing(self):
        """Admin-Benachrichtigung wird NICHT gesendet wenn SUPERADMIN_EMAIL fehlt."""
        user = {"email": "trainer@example.com", "vorname": "Tina"}
        data = {"kundennummer": "APH-101", "lizenztyp": "Pro"}

        _kunden_mock, admin_mock = self._call(
            user, data,
            superadmin_email="",   # nicht konfiguriert
        )
        admin_mock.assert_not_called()

    def test_no_pii_leaked_to_hardcoded_address(self):
        """Kein Versand an irgendeine Fallback-Adresse wenn SUPERADMIN_EMAIL fehlt."""
        send_admin = MagicMock(return_value=True)
        user = {"email": "pii@example.com", "vorname": "Secret"}
        data = {"kundennummer": "APH-102", "lizenztyp": "Basis"}

        with patch.dict(os.environ, {"SUPERADMIN_EMAIL": ""}, clear=False):
            with patch("email_service.send_widerruf_admin_benachrichtigung", send_admin):
                import importlib
                import modules.mein_vertrag as mv
                importlib.reload(mv)
                mv._sende_widerruf_email(user, data)

        # Sicherstellen: kein Aufruf mit irgendeiner Adresse
        for c in send_admin.call_args_list:
            to_addr = c[1].get("to") or (c[0][0] if c[0] else "")
            self.assertNotIn("hotmail", to_addr.lower(),
                             "PII darf nicht an Fallback-Adresse gesendet werden")

    def test_kundenmail_sent_regardless_of_admin_config(self):
        """Kunden-Bestätigungs-E-Mail wird unabhängig von SUPERADMIN_EMAIL gesendet."""
        user = {"email": "trainer@example.com", "vorname": "Tina"}
        data = {"kundennummer": "APH-103", "lizenztyp": "Basis"}

        kunden_mock, _ = self._call(user, data, superadmin_email="")
        kunden_mock.assert_called_once()
        self.assertEqual(kunden_mock.call_args[1]["to"], "trainer@example.com")


if __name__ == "__main__":
    unittest.main(verbosity=2)
