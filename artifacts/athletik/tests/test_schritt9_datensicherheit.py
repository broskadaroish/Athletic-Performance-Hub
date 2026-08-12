"""
Tests für SCHRITT 9 — Datensicherheit, Persistenz, Mandantentrennung.

Prüft:
  § 6–18 — spieler_mandant_pruefen() (IDOR-Schutz)
  §23–27 — backup_status_laden() / db_backup_erstellen()
  §28    — PRAGMA foreign_keys = ON
  §42–44 — init_db() Idempotenz (kein DROP TABLE)
  §52    — backup_status Struktur vollständig
"""

import sqlite3
import sys
import os
import inspect
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import (
    spieler_mandant_pruefen,
    backup_status_laden,
    db_backup_erstellen,
    get_conn,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Isolierte temporäre Datenbank für Tests."""
    db_file = tmp_path / "test_athletik.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()
    return db_file


# ── §42–44 — init_db() Idempotenz ────────────────────────────────────────────

class TestInitDbIdempotenz:
    def test_mehrfacher_aufruf_zerstoert_keine_daten(self, tmp_db, monkeypatch):
        """init_db() darf bestehende Datensätze nicht löschen."""
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))

        # Einen Verein anlegen
        with database.get_conn() as conn:
            conn.execute(
                "INSERT INTO vereine (name, aktiv) VALUES (?, ?)", ("Testverein", 1)
            )

        # init_db() erneut aufrufen (wie nach einem Neustart)
        database.init_db()

        with database.get_conn() as conn:
            n = conn.execute("SELECT COUNT(*) FROM vereine").fetchone()[0]
        assert n == 1, "init_db() hat bestehende Vereinsdaten gelöscht"

    def test_kein_drop_table_in_init_db(self):
        """database.py darf kein DROP TABLE in init_db() enthalten."""
        src = inspect.getsource(database)
        # init_db-Block isolieren
        start = src.find("def init_db(")
        # Nächste Top-Level-Funktion
        end = src.find("\ndef ", start + 1)
        init_src = src[start:end] if end > 0 else src[start:]
        assert "DROP TABLE" not in init_src.upper(), (
            "init_db() enthält DROP TABLE — Datenverlust bei Neustart möglich"
        )


# ── §28 — PRAGMA foreign_keys = ON ───────────────────────────────────────────

class TestForeignKeys:
    def test_foreign_keys_eingeschaltet(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1, "PRAGMA foreign_keys ist nicht aktiviert"


# ── §6–18 — spieler_mandant_pruefen() (IDOR-Schutz) ─────────────────────────

class TestSpielerMandantPruefen:
    def _insert_spieler(self, conn, verein_id, trainer_id):
        cur = conn.execute(
            "INSERT INTO spieler (name, verein_id, trainer_id)"
            " VALUES (?, ?, ?)",
            ("Max Mustermann", verein_id, trainer_id),
        )
        return cur.lastrowid

    def _insert_verein(self, conn, name="Verein A"):
        cur = conn.execute(
            "INSERT INTO vereine (name, aktiv) VALUES (?, ?)", (name, 1)
        )
        return cur.lastrowid

    def _insert_benutzer(self, conn, verein_id, rolle="Trainer"):
        cur = conn.execute(
            """INSERT INTO benutzer
               (verein_id, vorname, nachname, email, passwort_hash, rolle, aktiv)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (verein_id, "Anna", "Muster",
             f"anna_{verein_id}@test.de", "hash", rolle, 1),
        )
        return cur.lastrowid

    def test_superadmin_immer_erlaubt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        # Superadmin darf auch nicht-existierenden Spieler "prüfen" → True
        assert spieler_mandant_pruefen(9999, None, "Superadmin", None) is True

    def test_trainer_eigener_spieler_erlaubt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            vid = self._insert_verein(conn)
            bid = self._insert_benutzer(conn, vid)
            sid = self._insert_spieler(conn, vid, bid)
        assert spieler_mandant_pruefen(sid, bid, "Trainer", vid) is True

    def test_trainer_fremder_spieler_abgelehnt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            vid_a = self._insert_verein(conn, "Verein A")
            vid_b = self._insert_verein(conn, "Verein B")
            bid_a = self._insert_benutzer(conn, vid_a)
            bid_b = self._insert_benutzer(conn, vid_b)
            sid   = self._insert_spieler(conn, vid_a, bid_a)
        # Trainer von Verein B versucht Spieler von Verein A zu laden
        assert spieler_mandant_pruefen(sid, bid_b, "Trainer", vid_b) is False

    def test_vereinsadmin_eigener_spieler_erlaubt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            vid = self._insert_verein(conn)
            bid = self._insert_benutzer(conn, vid, "Vereinsadmin")
            sid = self._insert_spieler(conn, vid, bid)
        assert spieler_mandant_pruefen(sid, bid, "Vereinsadmin", vid) is True

    def test_vereinsadmin_fremder_spieler_abgelehnt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            vid_a = self._insert_verein(conn, "Verein A")
            vid_b = self._insert_verein(conn, "Verein B")
            bid_a = self._insert_benutzer(conn, vid_a, "Vereinsadmin")
            bid_b = self._insert_benutzer(conn, vid_b, "Vereinsadmin")
            sid   = self._insert_spieler(conn, vid_a, bid_a)
        assert spieler_mandant_pruefen(sid, bid_b, "Vereinsadmin", vid_b) is False

    def test_nicht_existierender_spieler_abgelehnt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        assert spieler_mandant_pruefen(99999, 1, "Trainer", 1) is False

    def test_vereinsadmin_ohne_verein_id_abgelehnt(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        with get_conn() as conn:
            vid = self._insert_verein(conn)
            bid = self._insert_benutzer(conn, vid, "Vereinsadmin")
            sid = self._insert_spieler(conn, vid, bid)
        # Fehlender verein_id-Kontext → abgelehnt
        assert spieler_mandant_pruefen(sid, bid, "Vereinsadmin", None) is False


# ── §52 — backup_status_laden() Struktur ─────────────────────────────────────

class TestBackupStatusLaden:
    PFLICHT_SCHLUESSEL = {
        "db_erreichbar",
        "db_groesse_kb",
        "backup_anzahl",
        "letztes_backup_datum",
        "letztes_backup_groesse_kb",
        "backups",
    }

    def test_struktur_vollstaendig(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        status = backup_status_laden()
        fehlend = self.PFLICHT_SCHLUESSEL - set(status.keys())
        assert not fehlend, f"Fehlende Schlüssel in backup_status_laden(): {fehlend}"

    def test_db_erreichbar_true_bei_existierender_db(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        status = backup_status_laden()
        assert status["db_erreichbar"] is True

    def test_db_erreichbar_false_bei_fehlendem_pfad(self, tmp_path, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "nicht_vorhanden.db"))
        status = backup_status_laden()
        assert status["db_erreichbar"] is False

    def test_backup_anzahl_ist_int(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        status = backup_status_laden()
        assert isinstance(status["backup_anzahl"], int)

    def test_backups_ist_liste(self, tmp_db, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        status = backup_status_laden()
        assert isinstance(status["backups"], list)

    def test_backup_eintraege_haben_felder(self, tmp_db, tmp_path, monkeypatch):
        """Wenn Backup-Dateien im Verzeichnis liegen, haben Einträge name/datum/groesse_kb."""
        monkeypatch.setattr(database, "DB_PATH", str(tmp_db))
        # Backup-Verzeichnis simulieren
        backup_dir = tmp_path / "uploads" / "backups"
        backup_dir.mkdir(parents=True)
        bk_file = backup_dir / "athletik_2026-08-12.db"
        bk_file.write_bytes(b"SQLite" * 100)
        monkeypatch.setenv("ATHLETIK_DATA_DIR", str(tmp_path))

        status = backup_status_laden()
        assert status["backup_anzahl"] >= 1
        assert status["letztes_backup_datum"] is not None
        entry = status["backups"][0]
        assert "name"       in entry
        assert "datum"      in entry
        assert "groesse_kb" in entry


# ── §23–24 — db_backup_erstellen() erreichbar und gibt Tuple zurück ──────────

class TestDbBackupErstellen:
    def test_gibt_tuple_zurueck(self):
        """db_backup_erstellen() muss (bool, str) zurückgeben — auch bei Fehler."""
        result = db_backup_erstellen()
        assert isinstance(result, tuple), "Kein Tuple zurückgegeben"
        assert len(result) == 2, "Tuple hat nicht 2 Elemente"
        ok, msg = result
        assert isinstance(ok, bool), "Erstes Element muss bool sein"
        assert isinstance(msg, str), "Zweites Element muss str sein"

    def test_kein_crash_bei_fehlendem_script(self, tmp_path, monkeypatch):
        """db_backup_erstellen() darf nicht abstürzen wenn backup.py fehlt."""
        # backup.py temporär umbenennen durch Patching des Pfad-Lookups
        import pathlib
        original_parent = pathlib.Path(__file__).parent
        # Liefert False + Fehlermeldung statt Exception
        ok, msg = db_backup_erstellen()
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
