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
        smtp.send_message(msg)       # send_message() ist zuverlässiger als sendmail+as_bytes()

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
    subject = f"{_APP_NAME} \u2013 Passwort zur\u00fccksetzen"
    text = (
        f"Hallo {name},\n\n"
        f"du hast angefordert, dein Passwort f\u00fcr {_APP_NAME} zur\u00fcckzusetzen.\n\n"
        "Klicke auf den folgenden Link, um ein neues Passwort festzulegen:\n\n"
        f"{reset_url}\n\n"
        "Der Link ist nur f\u00fcr einen begrenzten Zeitraum g\u00fcltig (24 Stunden) "
        "und kann nur einmal verwendet werden.\n\n"
        "Wenn du diese Anfrage nicht gestellt hast, kannst du diese E-Mail ignorieren. "
        "Dein Passwort bleibt in diesem Fall unver\u00e4ndert.\n\n"
        f"Bei Fragen: {_SUPPORT_EMAIL}\n\n"
        f"Viele Gr\u00fc\u00dfe\n{_APP_NAME}"
    )
    html = (
        "<!DOCTYPE html><html><body style='font-family:Arial,sans-serif;"
        "background:#f6f8fa;padding:24px'>"
        "<div style='max-width:560px;margin:0 auto;background:#ffffff;"
        "border:1px solid #d0d7de;border-radius:8px;padding:32px'>"
        f"<h2 style='color:#24292f;margin-top:0'>{_APP_NAME}</h2>"
        f"<p style='color:#24292f'>Hallo <strong>{name}</strong>,</p>"
        f"<p style='color:#24292f'>du hast angefordert, dein Passwort f\u00fcr "
        f"<strong>{_APP_NAME}</strong> zur\u00fcckzusetzen.</p>"
        "<p style='color:#24292f'>Klicke auf den folgenden Button, um ein neues Passwort festzulegen:</p>"
        f'<p><a href="{reset_url}" style="background:#0969da;color:#ffffff;'
        "padding:12px 28px;border-radius:6px;text-decoration:none;"
        "display:inline-block;font-weight:bold;font-size:15px\">"
        "Passwort zur\u00fccksetzen</a></p>"
        "<p style='color:#57606a;font-size:13px'>Falls der Button nicht funktioniert, "
        "kopiere diesen Link in deinen Browser:</p>"
        f'<p style="word-break:break-all"><a href="{reset_url}" style="color:#0969da">'
        f"{reset_url}</a></p>"
        "<hr style='border:none;border-top:1px solid #d0d7de;margin:24px 0'>"
        "<p style='color:#57606a;font-size:13px'>"
        "Der Link ist <strong>24 Stunden</strong> g\u00fcltig und kann nur einmal verwendet werden.</p>"
        "<p style='color:#57606a;font-size:13px'>"
        "Wenn du diese Anfrage nicht gestellt hast, kannst du diese E-Mail ignorieren. "
        "Dein Passwort bleibt unver\u00e4ndert.</p>"
        f"<p style='color:#57606a;font-size:12px'>Bei Fragen: "
        f"<a href='mailto:{_SUPPORT_EMAIL}' style='color:#0969da'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='color:#57606a;font-size:12px'>Viele Gr\u00fc\u00dfe<br>"
        f"<strong>{_APP_NAME}</strong></p>"
        "</div></body></html>"
    )
    _send(to, subject, text, html)


def send_username_reminder(to: str, name: str, benutzername: str | None,
                           login_url: str = "https://aphsystem.de") -> None:
    """Sendet den Benutzernamen per E-Mail.
    Wenn benutzername=None: erklärt, dass das Konto keinen Benutzernamen hat."""
    subject = f"{_APP_NAME} \u2013 Dein Benutzername"

    if benutzername:
        uname_text = (
            f"Dein Benutzername lautet:\n\n    {benutzername}\n\n"
            f"Du kannst dich hier anmelden:\n{login_url}\n\n"
        )
        uname_html = (
            "<p style='color:#24292f'>Dein Benutzername lautet:</p>"
            f"<p style='background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;"
            f"padding:12px 20px;font-size:18px;font-weight:bold;letter-spacing:1px;"
            f"color:#24292f'>{benutzername}</p>"
        )
    else:
        uname_text = (
            "F\u00fcr dein Konto wurde kein separater Benutzername angelegt.\n"
            "Du kannst dich mit deiner E-Mail-Adresse und deinem Passwort anmelden:\n\n"
            f"    {login_url}\n\n"
        )
        uname_html = (
            "<p style='color:#24292f'>F\u00fcr dein Konto wurde kein separater "
            "Benutzername angelegt.</p>"
            "<p style='color:#24292f'>Du kannst dich direkt mit deiner "
            "<strong>E-Mail-Adresse</strong> und deinem Passwort anmelden.</p>"
        )

    text = (
        f"Hallo {name},\n\n"
        f"du hast deinen Benutzernamen f\u00fcr {_APP_NAME} angefordert.\n\n"
        + uname_text
        + "Wenn du diese Anfrage nicht gestellt hast, kannst du diese E-Mail ignorieren.\n\n"
        f"Bei Fragen: {_SUPPORT_EMAIL}\n\n"
        f"Viele Gr\u00fc\u00dfe\n{_APP_NAME}"
    )
    html = (
        "<!DOCTYPE html><html><body style='font-family:Arial,sans-serif;"
        "background:#f6f8fa;padding:24px'>"
        "<div style='max-width:560px;margin:0 auto;background:#ffffff;"
        "border:1px solid #d0d7de;border-radius:8px;padding:32px'>"
        f"<h2 style='color:#24292f;margin-top:0'>{_APP_NAME}</h2>"
        f"<p style='color:#24292f'>Hallo <strong>{name}</strong>,</p>"
        f"<p style='color:#24292f'>du hast deinen Benutzernamen f\u00fcr "
        f"<strong>{_APP_NAME}</strong> angefordert.</p>"
        + uname_html
        + f'<p style="margin-top:20px"><a href="{login_url}" style="background:#238636;color:#ffffff;'
        "padding:12px 28px;border-radius:6px;text-decoration:none;"
        "display:inline-block;font-weight:bold;font-size:15px\">"
        "Jetzt anmelden</a></p>"
        "<hr style='border:none;border-top:1px solid #d0d7de;margin:24px 0'>"
        "<p style='color:#57606a;font-size:13px'>"
        "Wenn du diese Anfrage nicht gestellt hast, kannst du diese E-Mail ignorieren.</p>"
        f"<p style='color:#57606a;font-size:12px'>Bei Fragen: "
        f"<a href='mailto:{_SUPPORT_EMAIL}' style='color:#0969da'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='color:#57606a;font-size:12px'>Viele Gr\u00fc\u00dfe<br>"
        f"<strong>{_APP_NAME}</strong></p>"
        "</div></body></html>"
    )
    _send(to, subject, text, html)


def send_freischaltung_email(to: str, name: str, base_url: str) -> None:
    """Sendet die Freischaltungsbenachrichtigung nach der Admin-Aktivierung."""
    login_url = base_url.rstrip("/")
    subject = f"{_APP_NAME} – Dein Zugang wurde freigeschaltet"
    text = (
        f"Hallo {name},\n\n"
        f"dein Zugang zu {_APP_NAME} wurde freigeschaltet. "
        "Du kannst dich jetzt anmelden.\n\n"
        f"Anmelden: {login_url}\n\n"
        f"Support: {_SUPPORT_EMAIL}\n\n"
        f"Viele Grüße\n{_APP_NAME}"
    )
    html = (
        f"<p>Hallo <strong>{name}</strong>,</p>"
        f"<p>dein Zugang zu <strong>{_APP_NAME}</strong> wurde freigeschaltet. "
        "Du kannst dich jetzt anmelden.</p>"
        f'<p><a href="{login_url}" style="background:#238636;color:#fff;'
        f'padding:10px 24px;border-radius:6px;text-decoration:none;display:inline-block;font-weight:bold">'
        f"Jetzt anmelden</a></p>"
        f"<hr><p style='font-size:12px;color:#666'>Support: "
        f"<a href='mailto:{_SUPPORT_EMAIL}'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='font-size:12px;color:#666'>Viele Grüße<br><strong>{_APP_NAME}</strong></p>"
    )
    _send(to, subject, text, html)


def send_lizenz_ablauf_warnung(to: str, vereine: list[dict]) -> bool:
    """Sendet Superadmin-Warnung über ablaufende Lizenzen. Gibt True bei Erfolg zurück."""
    subject = f"{_APP_NAME} \u2013 Ablaufende Lizenzen"
    anzahl = len(vereine)
    zeilen = "\n".join(
        f"  - {v.get('name','?')} (bis {v.get('lizenz_bis','?')})"
        for v in vereine
    )
    text = (
        f"Hallo,\n\n"
        f"bei {anzahl} Verein(en) l\u00e4uft die Lizenz in K\u00fcrze ab:\n\n"
        f"{zeilen}\n\n"
        "Bitte pr\u00fcfe die Kundenverwaltung und nehme ggf. Kontakt auf.\n\n"
        f"Bei Fragen: {_SUPPORT_EMAIL}\n\n"
        f"Viele Gr\u00fc\u00dfe\n{_APP_NAME}"
    )
    rows_html = "".join(
        f"<tr><td style='padding:6px 12px;border-bottom:1px solid #d0d7de'>"
        f"{v.get('name','?')}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #d0d7de'>"
        f"{v.get('lizenz_bis','?')}</td></tr>"
        for v in vereine
    )
    html = (
        "<!DOCTYPE html><html><body style='font-family:Arial,sans-serif;"
        "background:#f6f8fa;padding:24px'>"
        "<div style='max-width:600px;margin:0 auto;background:#ffffff;"
        "border:1px solid #d0d7de;border-radius:8px;padding:32px'>"
        f"<h2 style='color:#24292f;margin-top:0'>{_APP_NAME} \u2013 Lizenz-Warnung</h2>"
        f"<p style='color:#24292f'>Bei <strong>{anzahl} Verein(en)</strong> l\u00e4uft die Lizenz in K\u00fcrze ab:</p>"
        "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        "<thead><tr style='background:#f6f8fa'>"
        "<th style='padding:8px 12px;text-align:left;border-bottom:2px solid #d0d7de'>Verein</th>"
        "<th style='padding:8px 12px;text-align:left;border-bottom:2px solid #d0d7de'>Lizenz bis</th>"
        "</tr></thead><tbody>"
        + rows_html
        + "</tbody></table>"
        "<p style='color:#57606a;font-size:13px'>"
        "Bitte pr\u00fcfe die Kundenverwaltung und nehme ggf. Kontakt auf.</p>"
        f"<p style='color:#57606a;font-size:12px'>Bei Fragen: "
        f"<a href='mailto:{_SUPPORT_EMAIL}' style='color:#0969da'>{_SUPPORT_EMAIL}</a></p>"
        f"<p style='color:#57606a;font-size:12px'>Viele Gr\u00fc\u00dfe<br>"
        f"<strong>{_APP_NAME}</strong></p>"
        "</div></body></html>"
    )
    try:
        _send(to, subject, text, html)
        return True
    except Exception as exc:
        log.error("send_lizenz_ablauf_warnung fehlgeschlagen (%s)", type(exc).__name__)
        return False


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
