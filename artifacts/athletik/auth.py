"""
Authentifizierung — Login-Funktion für das Multi-Tenant-System.
Passwörter werden mit PBKDF2-SHA256 + Salt gespeichert (260.000 Iterationen).
Alte SHA-256-Hashes (kein Salt) werden beim ersten erfolgreichen Login automatisch upgegradet.
"""
import sqlite3
from database import DB_PATH, _pw_hash, _pw_verify


def hash_password(passwort: str) -> str:
    """Erzeugt einen PBKDF2-SHA256-Hash für ein neues Passwort."""
    return _pw_hash(passwort)


def login(email: str, passwort: str) -> dict | None:
    """Prüft E-Mail + Passwort gegen die Datenbank.
    Gibt den Benutzer-Dict zurück oder None bei Fehler.
    Upgradet automatisch alte SHA-256-Hashes auf PBKDF2."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            """SELECT b.*, v.name AS verein_name
               FROM benutzer b
               LEFT JOIN vereine v ON b.verein_id = v.id
               WHERE b.email = ? AND b.aktiv = 1""",
            (email,),
        ).fetchone()
        conn.close()
    except Exception:
        return None

    if user is None:
        return None

    stored = user["passwort_hash"]
    if not _pw_verify(passwort, stored):
        return None

    # Automatisches Upgrade: altes SHA-256 → PBKDF2 beim ersten erfolgreichen Login
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

    # Letzten Login-Zeitstempel aktualisieren
    try:
        from database import benutzer_letzter_login_aktualisieren
        benutzer_letzter_login_aktualisieren(user["id"])
    except Exception:
        pass

    return dict(user)
