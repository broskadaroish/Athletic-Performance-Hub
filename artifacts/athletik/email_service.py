"""
E-Mail-Versand über IONOS SMTP (SSL/TLS, Port 465).

Umgebungsvariablen (via Replit Secrets):
  SMTP_HOST      – Standard: smtp.ionos.de
  SMTP_PORT      – Standard: 465
  SMTP_USERNAME  – Standard: noreply@aphsystem.de
  SMTP_PASSWORD  – PFLICHT (nie im Code speichern oder loggen!)
  SMTP_FROM      – Standard: noreply@aphsystem.de
  SUPPORT_EMAIL  – Standard: support@aphsystem.de

SMTP_PASSWORD darf niemals geloggt, angezeigt oder in Fehlermeldungen sichtbar sein.
"""
from __future__ import annotations
import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("athletik.email")

_SMTP_HOST     = os.environ.get("SMTP_HOST",     "smtp.ionos.de")
_SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
_SMTP_USER     = os.environ.get("SMTP_USERNAME", "noreply@aphsystem.de")
_SMTP_FROM     = os.environ.get("SMTP_FROM",     "noreply@aphsystem.de")
_SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@aphsystem.de")
_APP_NAME      = "Athletic Performance Hub"


def _get_smtp_password() -> str | None:
    """Liest SMTP_PASSWORD aus der Umgebung. Darf niemals geloggt oder angezeigt werden."""
    return os.environ.get("SMTP_PASSWORD")


def _send(to: str, subject: str, body_text: str, body_html: str | None = None) -> None:
    """Intern: sendet eine E-Mail via IONOS SMTP SSL/TLS Port 465.

    Wirft RuntimeError wenn SMTP_PASSWORD nicht konfiguriert ist.
    Wirft smtplib.SMTPException bei Verbindungsfehlern.
    SMTP_PASSWORD wird niemals geloggt.
    """
    pw = _get_smtp_password()
    if not pw:
        raise RuntimeError(
            "SMTP_PASSWORD ist nicht konfiguriert. "
            "Bitte in Replit Secrets unter 'SMTP_PASSWORD' eintragen."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{_APP_NAME} <{_SMTP_FROM}>"
    msg["To"]      = to
    msg["Reply-To"] = _SUPPORT_EMAIL

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, context=context) as smtp:
        smtp.login(_SMTP_USER, pw)   # pw absichtlich nicht geloggt
        smtp.sendmail(_SMTP_FROM, [to], msg.as_bytes())

    log.info("E-Mail gesendet an %s — Betreff: %s", to, subject)


# ── Öffentliche Sende-Funktionen ──────────────────────────────────────────────

def send_verification_email(to: str, name: str, token: str, base_url: str) -> None:
    """Sendet die E-Mail-Bestätigungsmail nach der Registrierung."""
    verify_url = f"{base_url.rstrip('/')}/?verify={token}"
    subject = f"{_APP_NAME} – E-Mail-Adresse bestätigen"
    text = (
        f"Hallo {name},\n\n"
        "bitte bestätige deine E-Mail-Adresse durch Klick auf den folgenden Link:\n\n"
        f"{verify_url}\n\n"
        "Der Link ist 24 Stunden gültig und kann nur einmal verwendet werden.\n\n"
        "Falls du dich nicht registriert hast, kannst du diese E-Mail ignorieren.\n\n"
        f"Support: {_SUPPORT_EMAIL}\n\n"
        f"Viele Grüße\n{_APP_NAME}"
    )
    html = (
        f"<p>Hallo <strong>{name}</strong>,</p>"
        "<p>bitte bestätige deine E-Mail-Adresse:</p>"
        f'<p><a href="{verify_url}" style="background:#238636;color:#fff;'
        f'padding:10px 24px;border-radius:6px;text-decoration:none;display:inline-block;font-weight:bold">'
        f"E-Mail-Adresse bestätigen</a></p>"
        "<p>Der Link ist <strong>24 Stunden</strong> gültig und kann nur einmal verwendet werden.</p>"
        "<p>Falls du dich nicht registriert hast, ignoriere diese E-Mail.</p>"
        f"<hr><p style='font-size:12px;color:#666'>Support: "
        f"<a href='mailto:{_SUPPORT_EMAIL}'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='font-size:12px;color:#666'>Viele Grüße<br><strong>{_APP_NAME}</strong></p>"
    )
    _send(to, subject, text, html)


def send_password_reset(to: str, name: str, token: str, base_url: str) -> None:
    """Sendet den Passwort-Reset-Link. Kein Klartextpasswort in der E-Mail."""
    reset_url = f"{base_url.rstrip('/')}/?reset={token}"
    subject = f"{_APP_NAME} – Passwort zurücksetzen"
    text = (
        f"Hallo {name},\n\n"
        "du hast das Zurücksetzen deines Passworts angefordert.\n\n"
        f"{reset_url}\n\n"
        "Der Link ist 1 Stunde gültig und kann nur einmal verwendet werden.\n\n"
        "Falls du keine Anfrage gestellt hast, kannst du diese E-Mail ignorieren. "
        "Dein Passwort bleibt in diesem Fall unverändert.\n\n"
        f"Support: {_SUPPORT_EMAIL}\n\n"
        f"Viele Grüße\n{_APP_NAME}"
    )
    html = (
        f"<p>Hallo <strong>{name}</strong>,</p>"
        "<p>du hast das Zurücksetzen deines Passworts angefordert:</p>"
        f'<p><a href="{reset_url}" style="background:#0969da;color:#fff;'
        f'padding:10px 24px;border-radius:6px;text-decoration:none;display:inline-block;font-weight:bold">'
        f"Passwort zurücksetzen</a></p>"
        "<p>Der Link ist <strong>1 Stunde</strong> gültig und kann nur einmal verwendet werden.</p>"
        "<p>Falls du keine Anfrage gestellt hast, ignoriere diese E-Mail. "
        "Dein Passwort bleibt unverändert.</p>"
        f"<hr><p style='font-size:12px;color:#666'>Support: "
        f"<a href='mailto:{_SUPPORT_EMAIL}'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='font-size:12px;color:#666'>Viele Grüße<br><strong>{_APP_NAME}</strong></p>"
    )
    _send(to, subject, text, html)


def send_username_reminder(to: str, name: str, benutzername: str) -> None:
    """Sendet den Benutzernamen per E-Mail (kein Passwort-Klartextversand)."""
    subject = f"{_APP_NAME} – Dein Benutzername"
    text = (
        f"Hallo {name},\n\n"
        f"dein Benutzername lautet: {benutzername}\n\n"
        "Du kannst dich mit deiner E-Mail-Adresse oder deinem Benutzernamen anmelden.\n\n"
        f"Support: {_SUPPORT_EMAIL}\n\n"
        f"Viele Grüße\n{_APP_NAME}"
    )
    html = (
        f"<p>Hallo <strong>{name}</strong>,</p>"
        f"<p>dein Benutzername lautet: <strong>{benutzername}</strong></p>"
        "<p>Du kannst dich mit deiner E-Mail-Adresse oder deinem Benutzernamen anmelden.</p>"
        f"<hr><p style='font-size:12px;color:#666'>Support: "
        f"<a href='mailto:{_SUPPORT_EMAIL}'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='font-size:12px;color:#666'>Viele Grüße<br><strong>{_APP_NAME}</strong></p>"
    )
    _send(to, subject, text, html)


def send_test_mail(to: str) -> None:
    """Testmail für Superadmin — prüft ob SMTP-Konfiguration funktioniert."""
    subject = f"{_APP_NAME} – E-Mail-Test"
    text = (
        "Hallo,\n\n"
        f"der E-Mail-Versand von {_APP_NAME} funktioniert erfolgreich.\n\n"
        f"Automatischer Absender:\n{_SMTP_FROM}\n\n"
        f"Support:\n{_SUPPORT_EMAIL}\n\n"
        f"Viele Grüße\n{_APP_NAME}"
    )
    _send(to, subject, text)
