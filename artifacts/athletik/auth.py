"""
Authentifizierung — Login-Funktion für das Multi-Tenant-System.
Passwörter werden als SHA-256-Hash gespeichert (kein Klartext).
"""
import hashlib
import sqlite3
from database import DB_PATH


def hash_password(passwort: str) -> str:
    return hashlib.sha256(passwort.encode()).hexdigest()


def login(email: str, passwort: str) -> dict | None:
    """Prüft E-Mail + Passwort gegen die Datenbank.
    Gibt den Benutzer-Dict zurück oder None bei Fehler."""
    try:
        conn = sqlite3.connect(DB_PATH)
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
    if user["passwort_hash"] != hash_password(passwort):
        return None
    return dict(user)
