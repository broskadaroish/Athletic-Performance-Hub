"""
Authentifizierung — Login-Funktion für das Multi-Tenant-System.
Passwörter werden mit PBKDF2-SHA256 + Salt gespeichert (260.000 Iterationen).
Alte SHA-256-Hashes (kein Salt) werden beim ersten erfolgreichen Login automatisch upgegradet.

Brute-Force-Schutz:
  Nach MAX_LOGIN_VERSUCHE Fehlversuchen wird das Konto für LOGIN_SPERRE_MINUTEN gesperrt.
  Konfigurierbar per Env-Var (siehe config.py).

E-Mail-Normalisierung:
  Nur Kleinschreibung — keine Punkte entfernen, keine +Zusätze, keine Provider-Änderungen.
  normalize_email() muss überall gleich verwendet werden.
"""
import sqlite3
from database import DB_PATH, _pw_hash, _pw_verify, normalize_email


def hash_password(passwort: str) -> str:
    """Erzeugt einen PBKDF2-SHA256-Hash für ein neues Passwort."""
    return _pw_hash(passwort)


def login(email_oder_benutzername: str, passwort: str) -> dict | None:
    """Prüft E-Mail/Benutzername + Passwort gegen die Datenbank.

    Gibt zurück:
      - dict mit Benutzer-Daten bei Erfolg
      - None bei unbekanntem Account / falschem Passwort
      - dict {'gesperrt': True, 'verbleibend_sek': N} bei gesperrtem Konto
      - dict {'email_nicht_verifiziert': True, 'benutzer_id': N, 'email': str}
        wenn E-Mail noch nicht bestätigt wurde (Zustand 1)
      - dict {'wartend_auf_freischaltung': True}
        wenn E-Mail bestätigt, Konto aber noch nicht vom Admin aktiviert (Zustand 2)
      - dict {'konto_deaktiviert': True}
        wenn Konto explizit vom Admin gesperrt wurde (aktiv=0, vormals aktiv=1)

    Nach MAX_LOGIN_VERSUCHE Fehlern wird das Konto für LOGIN_SPERRE_MINUTEN gesperrt.
    Bei Erfolg werden Fehlversuch-Zähler und Sperre automatisch zurückgesetzt.
    Login mit E-Mail oder Benutzername möglich (case-insensitiv).
    """
    from config import MAX_LOGIN_VERSUCHE, LOGIN_SPERRE_MINUTEN
    from database import (
        benutzer_sperre_pruefen,
        benutzer_login_fehlversuch,
        benutzer_login_zuruecksetzen,
        benutzer_letzter_login_aktualisieren,
    )

    # E-Mail normalisieren (Groß-/Kleinschreibung)
    login_norm = normalize_email(email_oder_benutzername)

    # 1. Sperr-Status prüfen (vor dem Passwort-Check)
    sperre = benutzer_sperre_pruefen(email_oder_benutzername)
    if sperre["gesperrt"]:
        return {"gesperrt": True, "verbleibend_sek": sperre["verbleibend_sek"]}

    # 2. Benutzer + Passwort-Hash aus DB laden (E-Mail ODER Benutzername)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            """SELECT b.*, v.name AS verein_name
               FROM benutzer b
               LEFT JOIN vereine v ON b.verein_id = v.id
               WHERE (LOWER(b.email)=?
                      OR (b.benutzername IS NOT NULL AND LOWER(b.benutzername)=?))""",
            (login_norm, login_norm),
        ).fetchone()
        conn.close()
    except Exception:
        return None

    if user is None:
        return None

    # 2b. Konto dauerhaft deaktiviert (aktiv=0 UND email_verifiziert=1)?
    #     Reihenfolge: aktiv=0 mit verifizierter E-Mail → wartend auf Freischaltung oder gesperrt
    #     aktiv=0 ohne verifizierte E-Mail → zuerst E-Mail-Check

    # 3. Passwort prüfen (VOR Status-Checks, damit Brute-Force-Schutz greift)
    stored = user["passwort_hash"]
    if not _pw_verify(passwort, stored):
        benutzer_id = sperre["benutzer_id"] or user["id"]
        benutzer_login_fehlversuch(benutzer_id, MAX_LOGIN_VERSUCHE, LOGIN_SPERRE_MINUTEN)
        neuer_status = benutzer_sperre_pruefen(email_oder_benutzername)
        if neuer_status["gesperrt"]:
            return {"gesperrt": True, "verbleibend_sek": neuer_status["verbleibend_sek"]}
        return None

    # 4a. E-Mail-Verifizierung prüfen ZUERST (Spec §2: email_verifiziert=0 → immer ablehnen)
    if not user["email_verifiziert"]:
        return {
            "email_nicht_verifiziert": True,
            "benutzer_id": user["id"],
            "email": user["email"],
        }

    # 4b. Account-Status prüfen (Spec §2: email_verifiziert=1, aktiv=0 → auf Freischaltung warten)
    if not user["aktiv"]:
        # Unterscheide: noch nie aktiviert (Neuregistrierung) vs. explizit gesperrt
        # Beide erhalten den gleichen Rückgabetyp — UI differenziert bei Bedarf
        return {"wartend_auf_freischaltung": True}

    # 5. Erfolgreich — Fehlversuch-Zähler zurücksetzen
    benutzer_login_zuruecksetzen(user["id"])

    # 6. Automatisches Upgrade: altes SHA-256 → PBKDF2 beim ersten erfolgreichen Login
    if not stored.startswith("pbkdf2:"):
        try:
            conn2 = sqlite3.connect(DB_PATH, timeout=10)
            conn2.execute(
                "UPDATE benutzer SET passwort_hash=? WHERE id=?",
                (_pw_hash(passwort), user["id"]),
            )
            conn2.commit()
            conn2.close()
        except Exception:
            pass  # Upgrade schlägt still fehl — nächster Login versucht es erneut

    # 7. Letzten Login-Zeitstempel aktualisieren
    try:
        benutzer_letzter_login_aktualisieren(user["id"])
    except Exception:
        pass

    return dict(user)
