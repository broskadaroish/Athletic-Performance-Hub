"""
E-Mail-Versand-Dienst — zentraler SMTP-Wrapper für Systembenachrichtigungen.

Konfiguration über Umgebungsvariablen (config.py):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

Wenn SMTP_USER leer ist, wird kein E-Mail versendet und eine Warnung geloggt.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

_log = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(config.SMTP_USER and config.SMTP_PASSWORD and config.SMTP_HOST)


def send_email(to: str, subject: str, body_html: str, body_text: str = "") -> bool:
    """
    Versendet eine E-Mail per SMTP (STARTTLS).

    Gibt True zurück wenn erfolgreich, False bei Fehler oder fehlender Konfiguration.
    """
    if not _smtp_configured():
        _log.warning(
            "E-Mail-Versand deaktiviert: SMTP_USER/SMTP_PASSWORD nicht konfiguriert. "
            "Empfänger: %s | Betreff: %s", to, subject
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.SMTP_FROM or config.SMTP_USER
    msg["To"]      = to

    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(config.SMTP_USER, config.SMTP_PASSWORD)
            srv.sendmail(msg["From"], [to], msg.as_string())
        _log.info("E-Mail versendet an %s | Betreff: %s", to, subject)
        return True
    except Exception as exc:
        _log.error("E-Mail-Versand fehlgeschlagen an %s: %s", to, exc)
        return False


def send_lizenz_ablauf_warnung(
    to: str,
    ablaufende_vereine: list[dict],
) -> bool:
    """
    Sendet eine Lizenz-Ablauf-Warnung an den Superadmin.

    ablaufende_vereine: Liste von dicts mit Schlüsseln:
        name (str), lizenz_bis (str 'YYYY-MM-DD'), tage_bis_ablauf (int)
    """
    if not ablaufende_vereine:
        return False

    n = len(ablaufende_vereine)
    subject = (
        f"⚠️ Lizenz-Ablauf-Warnung: {n} Verein{'e' if n != 1 else ''} "
        f"läuft{'laufen' if n != 1 else ''} in ≤ 30 Tagen ab"
    )

    zeilen_html = "\n".join(
        f"<tr>"
        f"<td style='padding:8px 16px;border-bottom:1px solid #e0e0e0'>"
        f"<strong>{v['name']}</strong></td>"
        f"<td style='padding:8px 16px;border-bottom:1px solid #e0e0e0'>"
        f"{v['lizenz_bis']}</td>"
        f"<td style='padding:8px 16px;border-bottom:1px solid #e0e0e0;"
        f"color:{'#c0392b' if v['tage_bis_ablauf'] <= 7 else '#e67e22'}'>"
        f"<strong>{v['tage_bis_ablauf']} Tag{'e' if v['tage_bis_ablauf'] != 1 else ''}</strong></td>"
        f"</tr>"
        for v in ablaufende_vereine
    )

    zeilen_text = "\n".join(
        f"  • {v['name']}: läuft ab am {v['lizenz_bis']} "
        f"(noch {v['tage_bis_ablauf']} Tag{'e' if v['tage_bis_ablauf'] != 1 else ''})"
        for v in ablaufende_vereine
    )

    body_html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:640px;margin:0 auto">
  <div style="background:#1e3a5f;padding:24px 32px;border-radius:8px 8px 0 0">
    <h2 style="color:#fff;margin:0">⚠️ Lizenz-Ablauf-Warnung</h2>
    <p style="color:#cce0ff;margin:8px 0 0">Bruce Football Performance Diagnostics</p>
  </div>
  <div style="background:#fff;padding:24px 32px;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <p>Hallo,</p>
    <p>die folgenden <strong>{n} Verein{'e haben' if n != 1 else ' hat'}</strong> eine Lizenz,
       die in den nächsten <strong>30 Tagen</strong> ausläuft:</p>
    <table style="border-collapse:collapse;width:100%;margin:16px 0">
      <thead>
        <tr style="background:#f5f5f5">
          <th style="padding:8px 16px;text-align:left;border-bottom:2px solid #ddd">Verein</th>
          <th style="padding:8px 16px;text-align:left;border-bottom:2px solid #ddd">Ablaufdatum</th>
          <th style="padding:8px 16px;text-align:left;border-bottom:2px solid #ddd">Verbleibend</th>
        </tr>
      </thead>
      <tbody>
{zeilen_html}
      </tbody>
    </table>
    <p>Bitte erneuere die Lizenzen rechtzeitig, um eine Unterbrechung des Dienstes zu vermeiden.</p>
    <p style="color:#888;font-size:13px;margin-top:32px">
      Diese E-Mail wurde automatisch vom Lizenzverwaltungssystem generiert.<br>
      Antworten auf diese E-Mail werden nicht bearbeitet.
    </p>
  </div>
</body>
</html>"""

    body_text = (
        f"Lizenz-Ablauf-Warnung — Bruce Football Performance Diagnostics\n"
        f"{'=' * 60}\n\n"
        f"Die folgenden {n} Verein(e) haben eine Lizenz, die in den nächsten 30 Tagen ausläuft:\n\n"
        f"{zeilen_text}\n\n"
        f"Bitte erneuere die Lizenzen rechtzeitig.\n\n"
        f"(Diese E-Mail wurde automatisch generiert.)\n"
    )

    return send_email(to, subject, body_html, body_text)
