"""
Database layer — single source of truth for all SQLite operations.
Uses a context manager for every connection so files are never left open.
"""

import logging as _logging
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

_logger = _logging.getLogger(__name__)

import os as _os
# DB-Pfad aus config.py lesen (zentrales Settings-Modul).
# Fallback auf direkten Env-Var-Zugriff falls config noch nicht geladen.
try:
    from config import SQLITE_PATH as DB_PATH
except ImportError:
    DB_PATH = _os.environ.get("ATHLETIK_DB_PATH", "athletik.db")

# Sentinel für optionale Parameter (unterscheidet None von "nicht übergeben")
_UNSET = object()


def _row(r):
    """sqlite3.Row → dict (Streamlit kann Row-Objekte nicht pickling)."""
    return dict(r) if r is not None else None


def _rows(rs):
    """Liste von sqlite3.Row → Liste von dicts."""
    return [dict(r) for r in rs]


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL")      # besser für Mehrbenutzer-Betrieb
    conn.execute("PRAGMA synchronous=NORMAL")    # WAL + NORMAL = sicher und schnell
    conn.execute("PRAGMA cache_size=-32000")     # 32 MB Query-Cache
    conn.execute("PRAGMA temp_store=MEMORY")     # Temp-Tabellen im RAM
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Schema ────────────────────────────────────────────────────────────────

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        -- ── Multi-Tenant: Vereine ──────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS vereine (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            aktiv       INTEGER DEFAULT 1,
            erstellt_am TEXT    DEFAULT (date('now'))
        );

        -- ── Multi-Tenant: Benutzer ─────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS benutzer (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            verein_id     INTEGER REFERENCES vereine(id),
            vorname       TEXT,
            nachname      TEXT,
            email         TEXT UNIQUE NOT NULL,
            passwort_hash TEXT NOT NULL,
            rolle         TEXT NOT NULL DEFAULT 'Trainer',
            aktiv         INTEGER DEFAULT 1,
            erstellt_am   TEXT    DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS spieler (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            geburtsdatum    TEXT,
            position        TEXT,
            spielbein       TEXT,
            mannschaft      TEXT,
            vorname         TEXT,
            nachname        TEXT,
            geschlecht      TEXT,
            altersklasse    TEXT,
            hauptposition   TEXT,
            nebenposition   TEXT,
            leistungsniveau TEXT,
            trainingsstatus TEXT,
            trainer_id      INTEGER REFERENCES benutzer(id),
            verein_id       INTEGER REFERENCES vereine(id)
        );

        CREATE TABLE IF NOT EXISTS verletzung (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id   INTEGER REFERENCES spieler(id),
            datum        TEXT,
            art          TEXT,
            koerperteil  TEXT,
            schwere      TEXT,
            ausfall_tage INTEGER,
            notizen      TEXT
        );

        CREATE TABLE IF NOT EXISTS einwilligung (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            datum     TEXT NOT NULL,
            version   TEXT NOT NULL,
            benutzer  TEXT NOT NULL DEFAULT 'Trainer'
        );

        CREATE TABLE IF NOT EXISTS anthropometrie (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id    INTEGER REFERENCES spieler(id),
            datum         TEXT,
            groesse       REAL,
            gewicht       REAL,
            sitzhoehe     REAL,
            beinlaenge    REAL,
            armspannweite REAL,
            koerperfett   REAL,
            muskelmasse   REAL,
            bmi           REAL,
            bmi_kategorie TEXT,
            phv_offset    REAL,
            reifestatus   TEXT
        );

        CREATE TABLE IF NOT EXISTS fms_test (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id       INTEGER REFERENCES spieler(id),
            datum            TEXT,
            deep_squat       INTEGER,
            hurdle_links     INTEGER,
            hurdle_rechts    INTEGER,
            inline_links     INTEGER,
            inline_rechts    INTEGER,
            shoulder_links   INTEGER,
            shoulder_rechts  INTEGER,
            aslr_links       INTEGER,
            aslr_rechts      INTEGER,
            trunk            INTEGER,
            rotary_links     INTEGER,
            rotary_rechts    INTEGER,
            score            INTEGER,
            bewertung        TEXT,
            asymmetrie       TEXT,
            schwerpunkt      TEXT
        );

        CREATE TABLE IF NOT EXISTS y_balance_test (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id            INTEGER REFERENCES spieler(id),
            datum                 TEXT,
            anterior_rechts       REAL,
            anterior_links        REAL,
            posteromedial_rechts  REAL,
            posteromedial_links   REAL,
            posterolateral_rechts REAL,
            posterolateral_links  REAL,
            diff_anterior         REAL,
            diff_posteromedial    REAL,
            diff_posterolateral   REAL,
            composite_rechts      REAL,
            composite_links       REAL,
            asymmetrie            TEXT,
            schwerpunkt           TEXT
        );

        CREATE TABLE IF NOT EXISTS sprint_test (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id  INTEGER REFERENCES spieler(id),
            datum       TEXT,
            v1_5m  REAL, v2_5m  REAL, v3_5m  REAL, beste_5m  REAL,
            v1_10m REAL, v2_10m REAL, v3_10m REAL, beste_10m REAL,
            v1_20m REAL, v2_20m REAL, v3_20m REAL, beste_20m REAL,
            v1_30m REAL, v2_30m REAL, v3_30m REAL, beste_30m REAL,
            beschl_index REAL,
            bewertung_10m TEXT, bewertung_30m TEXT,
            defizite TEXT
        );

        CREATE TABLE IF NOT EXISTS sprung_test (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id      INTEGER REFERENCES spieler(id),
            datum           TEXT,
            cmj_beid        REAL,
            cmj_rechts      REAL,
            cmj_links       REAL,
            cmj_asymmetrie  REAL,
            squat_jump      REAL,
            drop_jump_hoehe REAL,
            drop_jump_kz    REAL,
            rsi             REAL,
            standweit       REAL,
            bewertung_cmj   TEXT,
            defizite        TEXT
        );

        CREATE TABLE IF NOT EXISTS agilitaet_test (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id  INTEGER REFERENCES spieler(id),
            datum       TEXT,
            t505_r      REAL,
            t505_l      REAL,
            asym_505    REAL,
            t5_10_5     REAL,
            t_test      REAL,
            illinois    REAL,
            bew_505     TEXT,
            bew_t_test  TEXT,
            bew_illinois TEXT,
            defizite    TEXT
        );

        CREATE TABLE IF NOT EXISTS ausdauer_test (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id   INTEGER REFERENCES spieler(id),
            datum        TEXT,
            test_typ     TEXT,
            distanz_m    REAL,
            hf_max       REAL,
            rpe          INTEGER,
            vo2max       REAL,
            bewertung    TEXT,
            altersgruppe TEXT,
            defizite     TEXT
        );

        -- ── Spiroergometrie-Erweiterung ──────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS spiro_protokoll (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            name                 TEXT NOT NULL,
            geraeteart           TEXT,
            hersteller           TEXT,
            startgeschwindigkeit REAL,
            steigerung           REAL,
            stufendauer          REAL,
            steigung             REAL DEFAULT 0,
            pausenzeit           REAL DEFAULT 0,
            max_stufen           INTEGER,
            aktiv                INTEGER DEFAULT 1,
            erstellt_am          TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS spiro_test (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id               INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
            protokoll_id             INTEGER REFERENCES spiro_protokoll(id),
            datum                    TEXT NOT NULL,
            testtyp                  TEXT NOT NULL DEFAULT 'spiro_laufband',
            geraeteart               TEXT,
            testort                  TEXT,
            tester                   TEXT,
            mit_spiro                INTEGER DEFAULT 0,
            mit_laktat               INTEGER DEFAULT 0,
            raumtemperatur           REAL,
            letzte_mahlzeit          TEXT,
            letzte_intensive_einheit TEXT,
            akute_beschwerden        TEXT,
            koerpergewicht           REAL,
            maximale_geschwindigkeit REAL,
            maximale_herzfrequenz    REAL,
            vo2_peak                 REAL,
            vo2_max                  REAL,
            geschaetzte_vo2max       REAL,
            vt1_geschwindigkeit      REAL,
            vt1_herzfrequenz         REAL,
            vt2_geschwindigkeit      REAL,
            vt2_herzfrequenz         REAL,
            laktatschwelle_methode   TEXT,
            schwelle_geschwindigkeit REAL,
            schwelle_herzfrequenz    REAL,
            schwelle_laktat          REAL,
            ruhelaktat               REAL,
            laktat_blutentnahmeort   TEXT,
            laktat_messgeraet        TEXT,
            rpe_max                  INTEGER,
            abbruchgrund             TEXT,
            bemerkung                TEXT,
            created_at               TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS spiro_stufe (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            spiro_test_id        INTEGER NOT NULL REFERENCES spiro_test(id) ON DELETE CASCADE,
            stufennummer         INTEGER NOT NULL,
            geschwindigkeit_kmh  REAL,
            steigung_prozent     REAL,
            dauer_sekunden       REAL,
            strecke_meter        REAL,
            herzfrequenz_bpm     REAL,
            hf_durchschnitt      REAL,
            vo2_absolut          REAL,
            vo2_relativ          REAL,
            vco2                 REAL,
            ve                   REAL,
            rer                  REAL,
            atemfrequenz         REAL,
            sauerstoffpuls       REAL,
            laktat_mmol_l        REAL,
            rpe                  INTEGER,
            stufe_vollstaendig   INTEGER DEFAULT 1,
            blutprobe_gueltig    INTEGER DEFAULT 1,
            bemerkung            TEXT
        );

        CREATE TABLE IF NOT EXISTS spiro_nachbelastung (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            spiro_test_id    INTEGER NOT NULL REFERENCES spiro_test(id) ON DELETE CASCADE,
            zeitpunkt_minuten REAL NOT NULL,
            herzfrequenz_bpm REAL,
            laktat_mmol_l    REAL,
            bemerkung        TEXT
        );

        CREATE TABLE IF NOT EXISTS training (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            bereich        TEXT,
            problem        TEXT,
            uebung         TEXT,
            saetze         TEXT,
            wiederholungen TEXT,
            haeufigkeit    TEXT
        );

        CREATE TABLE IF NOT EXISTS trainingsplan (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id     INTEGER REFERENCES spieler(id),
            datum          TEXT,
            woche          INTEGER,
            bereich        TEXT,
            uebung         TEXT,
            saetze         TEXT,
            wiederholungen TEXT,
            haeufigkeit    TEXT,
            status         TEXT DEFAULT 'offen'
        );

        CREATE TABLE IF NOT EXISTS trainingsplan_versionen (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id       INTEGER REFERENCES spieler(id),
            version_nr       INTEGER NOT NULL DEFAULT 1,
            datum            TEXT NOT NULL,
            erstellt_von     TEXT DEFAULT '',
            status           TEXT DEFAULT 'AKTIV',
            modus            TEXT DEFAULT 'Basis',
            schwerpunkt      TEXT DEFAULT '',
            trainingszeit_min INTEGER DEFAULT 60,
            notizen          TEXT DEFAULT '',
            diagnose_snapshot TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS periodisierung (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id   INTEGER REFERENCES spieler(id),
            woche        INTEGER,
            phase        TEXT,
            ziel         TEXT,
            bereich      TEXT,
            uebung       TEXT,
            intensitaet  TEXT,
            volumen      TEXT,
            haeufigkeit  TEXT,
            status       TEXT DEFAULT 'offen'
        );

        CREATE TABLE IF NOT EXISTS checkliste_custom (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT NOT NULL UNIQUE,
            punkte  TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS kraft_test (
            id                         INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id                 INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
            datum                      TEXT NOT NULL,
            koerpergewicht             REAL,
            direktes_1rm               REAL,
            geschaetztes_1rm           REAL,
            verwendete_formel          TEXT DEFAULT 'Epley',
            relative_kraft_direkt      REAL,
            relative_kraft_geschaetzt  REAL,
            sicherheit_bestaetigt      INTEGER DEFAULT 0,
            ventral_variante           TEXT,
            ventral_sekunden           REAL,
            ventral_versuch2           REAL,
            lateral_rechts_variante    TEXT,
            lateral_rechts_sekunden    REAL,
            lateral_links_variante     TEXT,
            lateral_links_sekunden     REAL,
            dorsal_variante            TEXT,
            dorsal_sekunden            REAL,
            rumpf_gesamt_sekunden      REAL,
            lateral_differenz_sekunden REAL,
            lateral_asymmetrie_prozent REAL,
            ratio_ventral_dorsal       REAL,
            ratio_lateral_r_dorsal     REAL,
            ratio_lateral_l_dorsal     REAL,
            abbruchgrund               TEXT,
            bemerkung                  TEXT,
            created_at                 TEXT DEFAULT (datetime('now')),
            updated_at                 TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS kraft_test_versuch (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            kraft_test_id       INTEGER NOT NULL REFERENCES kraft_test(id) ON DELETE CASCADE,
            uebung              TEXT NOT NULL,
            versuchsnummer      INTEGER NOT NULL,
            gewicht             REAL,
            wiederholungen      INTEGER,
            zeit_sekunden       REAL,
            gueltig             INTEGER DEFAULT 1,
            ungueltigkeitsgrund TEXT
        );

        CREATE TABLE IF NOT EXISTS trainerbeobachtung (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id     INTEGER NOT NULL REFERENCES spieler(id),
            test_id        TEXT    NOT NULL,
            datum          TEXT    NOT NULL,
            beob_ids       TEXT    NOT NULL DEFAULT '[]',
            seite          TEXT,
            auspraegung    TEXT,
            freitext       TEXT,
            text_generiert TEXT,
            created_at     TEXT    DEFAULT (datetime('now')),
            updated_at     TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS app_einstellungen (
            schluessel TEXT PRIMARY KEY,
            wert       BLOB,
            geaendert  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS spieler_zuweisung_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            spieler_id       INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
            zeitstempel      TEXT    NOT NULL DEFAULT (datetime('now')),
            ausfuehrender_id INTEGER REFERENCES benutzer(id) ON DELETE SET NULL,
            alt_trainer_id   INTEGER,
            neu_trainer_id   INTEGER,
            alt_verein_id    INTEGER,
            neu_verein_id    INTEGER
        );

        CREATE TABLE IF NOT EXISTS benachrichtigungen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
            typ         TEXT    NOT NULL DEFAULT 'info',
            text        TEXT    NOT NULL,
            gelesen     INTEGER NOT NULL DEFAULT 0,
            erstellt_am TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ── Lizenz-Ablauf-Warnungen (Deduplizierung) ───────────────────────────
        CREATE TABLE IF NOT EXISTS lizenz_warn_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            verein_id   INTEGER NOT NULL REFERENCES vereine(id) ON DELETE CASCADE,
            gesendet_am TEXT    NOT NULL DEFAULT (date('now'))
        );

        -- ── Login-Audit-Log ────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS login_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            zeitstempel TEXT    NOT NULL DEFAULT (datetime('now')),
            email       TEXT    NOT NULL,
            ergebnis    TEXT    NOT NULL,  -- 'erfolg' | 'fehlschlag' | 'gesperrt'
            ip          TEXT,
            benutzer_id INTEGER REFERENCES benutzer(id) ON DELETE SET NULL,
            verein_id   INTEGER REFERENCES vereine(id)  ON DELETE SET NULL
        );

        -- ── Stripe-Webhook-Fehler (Superadmin-Monitoring) ──────────────────────
        CREATE TABLE IF NOT EXISTS webhook_fehler (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id    TEXT,
            event_type  TEXT,
            fehlergrund TEXT    NOT NULL,
            zeitstempel TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        """)
    # Migrationen: neue Spalten und Indizes für bestehende Datenbanken nachträglich anlegen
    _migrate_spieler_columns()
    _migrate_db()
    _migrate_multitenant()
    _migrate_szl_actor_fk()  # Korrigiert ON DELETE SET NULL auf ausfuehrender_id
    _create_indexes()


# ─── Stripe-Webhook-Fehler ────────────────────────────────────────────────────

def webhook_fehler_speichern(
    fehlergrund: str,
    event_id: str | None = None,
    event_type: str | None = None,
) -> None:
    """Speichert einen fehlerhaften Stripe-Webhook-Event für das Superadmin-Dashboard."""
    with get_conn() as conn:
        # Tabelle anlegen falls sie (in älteren DBs) noch nicht existiert
        conn.execute("""
            CREATE TABLE IF NOT EXISTS webhook_fehler (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id    TEXT,
                event_type  TEXT,
                fehlergrund TEXT    NOT NULL,
                zeitstempel TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "INSERT INTO webhook_fehler (event_id, event_type, fehlergrund) VALUES (?, ?, ?)",
            (event_id, event_type, fehlergrund),
        )


def webhook_fehler_laden(limit: int = 50) -> list[dict]:
    """Gibt die letzten fehlerhaften Stripe-Webhook-Events zurück (neueste zuerst)."""
    with get_conn() as conn:
        # Tabelle anlegen falls sie (in älteren DBs) noch nicht existiert
        conn.execute("""
            CREATE TABLE IF NOT EXISTS webhook_fehler (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id    TEXT,
                event_type  TEXT,
                fehlergrund TEXT    NOT NULL,
                zeitstempel TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        return _rows(conn.execute(
            """SELECT id, event_id, event_type, fehlergrund, zeitstempel
               FROM webhook_fehler
               ORDER BY id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall())


def webhook_fehler_loeschen() -> int:
    """Löscht alle gespeicherten Webhook-Fehler. Gibt Anzahl gelöschter Zeilen zurück."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM webhook_fehler")
        return cur.rowcount


# ─── Trainerbeobachtungen ─────────────────────────────────────────────────────

def beobachtung_speichern(
    spieler_id: int,
    test_id: str,
    datum: str,
    beob_ids_json: str,
    seite: str | None,
    auspraegung: str | None,
    freitext: str | None,
    text_generiert: str | None,
) -> None:
    """Legt eine Beobachtung an oder überschreibt die für diesen Tag (UPSERT)."""
    with get_conn() as conn:
        # Erst vorhandene Einträge für diesen Tag löschen (inkl. ggf. Duplikate),
        # dann sauber neu einfügen — idempotent und ohne Duplikat-Risiko
        conn.execute(
            "DELETE FROM trainerbeobachtung WHERE spieler_id=? AND test_id=? AND datum=?",
            (spieler_id, test_id, datum),
        )
        conn.execute(
            """INSERT INTO trainerbeobachtung
               (spieler_id, test_id, datum, beob_ids, seite, auspraegung, freitext, text_generiert, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (spieler_id, test_id, datum, beob_ids_json,
             seite, auspraegung, freitext, text_generiert),
        )


def beobachtung_laden(spieler_id: int, test_id: str, datum: str) -> dict | None:
    """Lädt die Beobachtung für einen Spieler, Test und Tag (oder None)."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM trainerbeobachtung
               WHERE spieler_id=? AND test_id=? AND datum=?
               ORDER BY id DESC LIMIT 1""",
            (spieler_id, test_id, datum),
        ).fetchone()
    return _row(row)


def beobachtung_loeschen(spieler_id: int, test_id: str, datum: str) -> None:
    """Löscht alle Beobachtungen für diesen Spieler/Test/Tag."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM trainerbeobachtung WHERE spieler_id=? AND test_id=? AND datum=?",
            (spieler_id, test_id, datum),
        )


def beobachtung_history(spieler_id: int, test_id: str) -> list[dict]:
    """Gibt alle gespeicherten Beobachtungen für Spieler+Test zurück (neueste zuerst)."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum, beob_ids, seite, auspraegung, freitext, text_generiert
               FROM trainerbeobachtung
               WHERE spieler_id=? AND test_id=?
               ORDER BY datum DESC""",
            (spieler_id, test_id),
        ).fetchall())


def beobachtungen_alle_fuer_spieler(spieler_id: int) -> list[dict]:
    """Alle Trainerbeobachtungen für einen Spieler mit Inhalt (neueste zuerst).
    Nur Einträge mit text_generiert oder freitext werden zurückgegeben."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT test_id, datum, text_generiert, freitext
               FROM trainerbeobachtung
               WHERE spieler_id=?
                 AND (
                     (text_generiert IS NOT NULL AND text_generiert != '')
                     OR (freitext IS NOT NULL AND freitext != '')
                 )
               ORDER BY datum DESC""",
            (spieler_id,),
        ).fetchall())


# ─── Trainer-Checkliste (custom) ──────────────────────────────────────────────

# ─── App-Einstellungen (key-value, inkl. Vereinslogo BLOB) ───────────────────

def einstellung_speichern(schluessel: str, wert) -> None:
    """Speichert einen Einstellungswert (Text oder bytes) dauerhaft."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO app_einstellungen (schluessel, wert, geaendert)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(schluessel) DO UPDATE
               SET wert=excluded.wert, geaendert=datetime('now')""",
            (schluessel, wert),
        )


def einstellung_laden(schluessel: str):
    """Lädt einen gespeicherten Einstellungswert (oder None)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT wert FROM app_einstellungen WHERE schluessel=?", (schluessel,)
        ).fetchone()
    return row["wert"] if row else None


def einstellung_loeschen(schluessel: str) -> None:
    """Löscht einen Einstellungseintrag vollständig."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM app_einstellungen WHERE schluessel=?", (schluessel,)
        )


def logo_laden() -> bytes | None:
    """Lädt das gespeicherte Vereinslogo (bytes) oder None."""
    return einstellung_laden("vereinslogo")


def logo_speichern(logo_bytes: bytes) -> None:
    """Speichert das Vereinslogo als BLOB in der Datenbank."""
    einstellung_speichern("vereinslogo", logo_bytes)


def logo_loeschen() -> None:
    """Entfernt das gespeicherte Vereinslogo."""
    einstellung_loeschen("vereinslogo")


def checkliste_custom_laden(test_id: str) -> str:
    """Gibt gespeicherte Custom-Punkte als mehrzeiligen Text zurück (leer = keine)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT punkte FROM checkliste_custom WHERE test_id = ?", (test_id,)
        ).fetchone()
    return row["punkte"] if row else ""


def checkliste_custom_speichern(test_id: str, punkte_text: str) -> None:
    """Speichert oder überschreibt Custom-Punkte für einen Test."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO checkliste_custom (test_id, punkte)
               VALUES (?, ?)
               ON CONFLICT(test_id) DO UPDATE SET punkte = excluded.punkte""",
            (test_id, punkte_text.strip()),
        )


def _migrate_szl_actor_fk():
    """Recreates spieler_zuweisung_log with ON DELETE SET NULL on ausfuehrender_id.

    SQLite does not support ALTER TABLE … DROP CONSTRAINT or adding ON DELETE actions,
    so we use the rename → create → copy → drop pattern with PRAGMA foreign_keys OFF.
    The migration is idempotent: a marker in app_einstellungen prevents double execution.
    """
    import sqlite3 as _sqlite3
    raw = _sqlite3.connect(DB_PATH, timeout=30)
    raw.row_factory = _sqlite3.Row
    raw.execute("PRAGMA journal_mode=WAL")
    # Must be OFF before altering/recreating tables with FK changes
    raw.execute("PRAGMA foreign_keys = OFF")
    try:
        # Idempotency check
        marker = raw.execute(
            "SELECT 1 FROM app_einstellungen WHERE schluessel='szl_actor_fk_v1'"
        ).fetchone()
        if marker:
            return

        # Clean up any aborted previous attempt
        raw.execute("DROP TABLE IF EXISTS _szl_tmp")
        raw.commit()

        tbl = raw.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='spieler_zuweisung_log'"
        ).fetchone()
        if tbl:
            raw.execute(
                "ALTER TABLE spieler_zuweisung_log RENAME TO _szl_tmp"
            )
            raw.execute("""
                CREATE TABLE spieler_zuweisung_log (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    spieler_id       INTEGER NOT NULL
                                     REFERENCES spieler(id) ON DELETE CASCADE,
                    zeitstempel      TEXT    NOT NULL DEFAULT (datetime('now')),
                    ausfuehrender_id INTEGER
                                     REFERENCES benutzer(id) ON DELETE SET NULL,
                    alt_trainer_id   INTEGER,
                    neu_trainer_id   INTEGER,
                    alt_verein_id    INTEGER,
                    neu_verein_id    INTEGER
                )
            """)
            raw.execute(
                "INSERT INTO spieler_zuweisung_log SELECT * FROM _szl_tmp"
            )
            raw.execute("DROP TABLE _szl_tmp")

        raw.execute(
            "INSERT OR IGNORE INTO app_einstellungen (schluessel, wert)"
            " VALUES ('szl_actor_fk_v1', '1')"
        )
        raw.commit()
    except Exception:
        try:
            raw.rollback()
        except Exception:
            pass
    finally:
        raw.close()


def _create_indexes():
    """Erstellt Performance-Indizes — idempotent, sicher bei wiederholtem Aufruf."""
    indexes = [
        # Multi-Tenant-Filtering
        "CREATE INDEX IF NOT EXISTS idx_spieler_verein    ON spieler(verein_id)",
        "CREATE INDEX IF NOT EXISTS idx_spieler_trainer   ON spieler(trainer_id)",
        "CREATE INDEX IF NOT EXISTS idx_benutzer_verein   ON benutzer(verein_id)",
        "CREATE INDEX IF NOT EXISTS idx_benutzer_email    ON benutzer(email)",
        # Test-Abfragen (spieler_id → letzter Test)
        "CREATE INDEX IF NOT EXISTS idx_fms_spieler       ON fms_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_y_spieler         ON y_balance_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_sprint_spieler    ON sprint_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_sprung_spieler    ON sprung_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_agil_spieler      ON agilitaet_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_ausdauer_spieler  ON ausdauer_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_kraft_spieler     ON kraft_test(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_anthro_spieler    ON anthropometrie(spieler_id, datum)",
        "CREATE INDEX IF NOT EXISTS idx_verletz_spieler   ON verletzung(spieler_id)",
        "CREATE INDEX IF NOT EXISTS idx_trainplan_spieler ON trainingsplan(spieler_id)",
    ]
    with get_conn() as conn:
        for stmt in indexes:
            try:
                conn.execute(stmt)
            except Exception:
                pass


def _migrate_spieler_columns():
    """Fügt neue Spalten zur spieler-Tabelle hinzu, falls noch nicht vorhanden."""
    neue_spalten = [
        ("vorname", "TEXT"), ("nachname", "TEXT"), ("geschlecht", "TEXT"),
        ("altersklasse", "TEXT"), ("hauptposition", "TEXT"), ("nebenposition", "TEXT"),
        ("leistungsniveau", "TEXT"), ("trainingsstatus", "TEXT"),
        ("trainer_id", "INTEGER"), ("verein_id", "INTEGER"),
        ("philosophie_key", "TEXT"),
    ]
    with get_conn() as conn:
        for spalte, typ in neue_spalten:
            try:
                conn.execute(f"ALTER TABLE spieler ADD COLUMN {spalte} {typ}")
            except Exception:
                pass  # Spalte existiert bereits


def _migrate_db():
    """Alle datenbankweiten Schema-Migrationen — idempotent, sicher bei wiederholtem Aufruf."""
    with get_conn() as conn:
        # ── Sprung: v1/v2/v3-Versuchsspalten hinzufügen ─────────────────────
        sprung_cols = [
            ("v1_cmj_beid","REAL"),("v2_cmj_beid","REAL"),("v3_cmj_beid","REAL"),
            ("v1_cmj_r","REAL"),   ("v2_cmj_r","REAL"),   ("v3_cmj_r","REAL"),
            ("v1_cmj_l","REAL"),   ("v2_cmj_l","REAL"),   ("v3_cmj_l","REAL"),
            ("v1_squat","REAL"),   ("v2_squat","REAL"),   ("v3_squat","REAL"),
            ("v1_dj_h","REAL"),    ("v2_dj_h","REAL"),    ("v3_dj_h","REAL"),
            ("v1_dj_kz","REAL"),   ("v2_dj_kz","REAL"),  ("v3_dj_kz","REAL"),
            ("v1_swj","REAL"),     ("v2_swj","REAL"),     ("v3_swj","REAL"),
        ]
        for col, typ in sprung_cols:
            try:
                conn.execute(f"ALTER TABLE sprung_test ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # ── Agilität: v1/v2/v3-Versuchsspalten + neue Tests ─────────────────
        agil_cols = [
            ("v1_t505_r","REAL"),  ("v2_t505_r","REAL"),  ("v3_t505_r","REAL"),
            ("v1_t505_l","REAL"),  ("v2_t505_l","REAL"),  ("v3_t505_l","REAL"),
            ("v1_t5_10_5","REAL"), ("v2_t5_10_5","REAL"), ("v3_t5_10_5","REAL"),
            ("v1_t_test","REAL"),  ("v2_t_test","REAL"),  ("v3_t_test","REAL"),
            ("v1_illinois","REAL"),("v2_illinois","REAL"),("v3_illinois","REAL"),
            # Phase 0C — neue Agility-Tests
            ("modified_t_test","REAL DEFAULT 0"),
            ("pro_agility","REAL DEFAULT 0"),
            ("arrowhead_r","REAL DEFAULT 0"),
            ("arrowhead_l","REAL DEFAULT 0"),
            ("zigzag","REAL DEFAULT 0"),
            ("balsom","REAL DEFAULT 0"),
            ("v1_modified_t_test","REAL"),("v2_modified_t_test","REAL"),("v3_modified_t_test","REAL"),
            ("v1_pro_agility","REAL"),    ("v2_pro_agility","REAL"),    ("v3_pro_agility","REAL"),
            ("v1_arrowhead_r","REAL"),    ("v2_arrowhead_r","REAL"),    ("v3_arrowhead_r","REAL"),
            ("v1_arrowhead_l","REAL"),    ("v2_arrowhead_l","REAL"),    ("v3_arrowhead_l","REAL"),
            ("v1_zigzag","REAL"),         ("v2_zigzag","REAL"),         ("v3_zigzag","REAL"),
            ("v1_balsom","REAL"),         ("v2_balsom","REAL"),         ("v3_balsom","REAL"),
        ]
        for col, typ in agil_cols:
            try:
                conn.execute(f"ALTER TABLE agilitaet_test ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # ── Sprint: 40m-Spalten ──────────────────────────────────────────────
        sprint_cols = [
            ("v1_40m","REAL DEFAULT 0"),("v2_40m","REAL DEFAULT 0"),
            ("v3_40m","REAL DEFAULT 0"),("beste_40m","REAL DEFAULT 0"),
        ]
        for col, typ in sprint_cols:
            try:
                conn.execute(f"ALTER TABLE sprint_test ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # ── Anthropometrie: bilaterale Beinlänge ────────────────────────────
        for col in [("beinlaenge_r","REAL"), ("beinlaenge_l","REAL")]:
            try:
                conn.execute(f"ALTER TABLE anthropometrie ADD COLUMN {col[0]} {col[1]}")
            except Exception:
                pass

        # ── Anthropometrie: Körperfett-Methode ──────────────────────────────
        try:
            conn.execute("ALTER TABLE anthropometrie ADD COLUMN koerperfett_methode TEXT")
        except Exception:
            pass

        # ── Trainingsplan: Tag, Pause, Ausführungsgeschwindigkeit ─────────────
        for _col, _typ in [
            ("tag",            "INTEGER DEFAULT 1"),
            ("pause_sekunden", "INTEGER DEFAULT 90"),
            ("ausfuehrung",    "TEXT    DEFAULT 'kontrolliert'"),
            ("rpe",            "INTEGER DEFAULT 7"),
            ("energie_system", "TEXT    DEFAULT 'Gemischt'"),
            ("equipment",      "TEXT    DEFAULT 'Körpergewicht'"),
            ("begruendung",    "TEXT    DEFAULT ''"),
            # SCHRITT 4: Versionierung + Bearbeitung
            ("plan_id",        "INTEGER DEFAULT NULL"),
            ("position",       "INTEGER DEFAULT 0"),
            ("notiz",          "TEXT    DEFAULT ''"),
            ("trainerhinweis", "TEXT    DEFAULT ''"),
            ("spielerhinweis", "TEXT    DEFAULT ''"),
            ("abgehakt",       "INTEGER DEFAULT 0"),
        ]:
            try:
                conn.execute(f"ALTER TABLE trainingsplan ADD COLUMN {_col} {_typ}")
            except Exception:
                pass

        # ── Wochenplanung-Erweiterung: wochenplanung_json für Vereinsbelastungs-Modus ──
        try:
            conn.execute(
                "ALTER TABLE trainingsplan_versionen ADD COLUMN wochenplanung_json TEXT DEFAULT NULL"
            )
        except Exception:
            pass  # Spalte existiert bereits

        # ── SCHRITT 4: Datenmigration — bestehende Pläne in AKTIV-Version einbetten ──
        try:
            _spieler_ohne_version = conn.execute("""
                SELECT DISTINCT t.spieler_id FROM trainingsplan t
                WHERE t.plan_id IS NULL AND t.spieler_id IS NOT NULL
            """).fetchall()
            for (_s_id,) in _spieler_ohne_version:
                _min_datum = (conn.execute(
                    "SELECT MIN(datum) FROM trainingsplan WHERE spieler_id=? AND plan_id IS NULL",
                    (_s_id,)
                ).fetchone() or [None])[0] or "2024-01-01"
                _max_v = (conn.execute(
                    "SELECT COALESCE(MAX(version_nr),0) FROM trainingsplan_versionen WHERE spieler_id=?",
                    (_s_id,)
                ).fetchone() or [0])[0]
                if _max_v == 0:  # Nur wenn noch keine Version existiert
                    _cur = conn.execute(
                        "INSERT INTO trainingsplan_versionen "
                        "(spieler_id,version_nr,datum,erstellt_von,status,modus,trainingszeit_min,notizen) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (_s_id, 1, _min_datum, "Migration", "AKTIV", "Basis", 60, ""),
                    )
                    _v_id = _cur.lastrowid
                    conn.execute(
                        "UPDATE trainingsplan SET plan_id=?,position=id WHERE spieler_id=? AND plan_id IS NULL",
                        (_v_id, _s_id),
                    )
        except Exception:
            pass

        # ── Duplikate in trainerbeobachtung bereinigen ───────────────────────
        conn.execute("""
            DELETE FROM trainerbeobachtung WHERE id NOT IN (
                SELECT MAX(id) FROM trainerbeobachtung
                GROUP BY spieler_id, test_id, datum
            )
        """)
        try:
            conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                idx_trainerbeob_unique ON trainerbeobachtung(spieler_id, test_id, datum)""")
        except Exception:
            pass

        # ── Duplikate in sprung_test bereinigen + UNIQUE INDEX ───────────────
        conn.execute("""
            DELETE FROM sprung_test WHERE id NOT IN (
                SELECT MAX(id) FROM sprung_test GROUP BY spieler_id, datum
            )
        """)
        try:
            conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                idx_sprung_unique ON sprung_test(spieler_id, datum)""")
        except Exception:
            pass

        # ── Duplikate in agilitaet_test bereinigen + UNIQUE INDEX ────────────
        conn.execute("""
            DELETE FROM agilitaet_test WHERE id NOT IN (
                SELECT MAX(id) FROM agilitaet_test GROUP BY spieler_id, datum
            )
        """)
        try:
            conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                idx_agil_unique ON agilitaet_test(spieler_id, datum)""")
        except Exception:
            pass

        # ── Zuweisung-Log-Tabelle (für bestehende Datenbanken) ───────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spieler_zuweisung_log (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                spieler_id       INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
                zeitstempel      TEXT    NOT NULL DEFAULT (datetime('now')),
                ausfuehrender_id INTEGER REFERENCES benutzer(id),
                alt_trainer_id   INTEGER,
                neu_trainer_id   INTEGER,
                alt_verein_id    INTEGER,
                neu_verein_id    INTEGER
            )
        """)

        # ── Benachrichtigungen-Tabelle (für bestehende Datenbanken) ──────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS benachrichtigungen (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
                typ         TEXT    NOT NULL DEFAULT 'info',
                text        TEXT    NOT NULL,
                gelesen     INTEGER NOT NULL DEFAULT 0,
                erstellt_am TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # ── Login-Audit-Log (für bestehende Datenbanken) ─────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                zeitstempel TEXT    NOT NULL DEFAULT (datetime('now')),
                email       TEXT    NOT NULL,
                ergebnis    TEXT    NOT NULL,
                ip          TEXT,
                benutzer_id INTEGER REFERENCES benutzer(id) ON DELETE SET NULL,
                verein_id   INTEGER REFERENCES vereine(id)  ON DELETE SET NULL
            )
        """)


# ─── Hilfsfunktionen ───────────────────────────────────────────────────────

def berechne_alter(geburtsdatum_str: str) -> int | None:
    """Berechnet das aktuelle Alter aus einem Datumsstring (TT.MM.JJJJ oder JJJJ-MM-TT).
    Gibt None zurück bei ungültigem Format, leerem Wert oder Geburtsdatum in der Zukunft."""
    if not geburtsdatum_str:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            geb = datetime.strptime(geburtsdatum_str, fmt).date()
            heute = date.today()
            if geb > heute:
                return None
            alter = heute.year - geb.year - ((heute.month, heute.day) < (geb.month, geb.day))
            return alter
        except ValueError:
            continue
    return None


def altersklasse_vorschlag(geburtsdatum_str: str) -> str:
    """Schlägt die passende Altersklasse anhand des Alters vor."""
    alter = berechne_alter(geburtsdatum_str)
    if alter is None:
        return "Unbekannt"
    if alter <= 7:   return "U7 (Bambini)"
    if alter <= 9:   return "U8/U9 (F-Jugend)"
    if alter <= 11:  return "U10/U11 (E-Jugend)"
    if alter <= 13:  return "U12/U13 (D-Jugend)"
    if alter <= 15:  return "U14/U15 (C-Jugend)"
    if alter <= 17:  return "U16/U17 (B-Jugend)"
    if alter <= 19:  return "U18/U19 (A-Jugend)"
    return "Senioren"


# ─── Spieler ───────────────────────────────────────────────────────────────

def spieler_speichern(vorname, nachname, geburtsdatum, geschlecht,
                      hauptposition, nebenposition, altersklasse,
                      spielbein, leistungsniveau, mannschaft, trainingsstatus,
                      trainer_id=None, verein_id=None):
    name = f"{vorname} {nachname}".strip()
    with get_conn() as conn:
        # F-05: Duplikatschutz — gleicher Name + Geburtsdatum
        existing = conn.execute(
            "SELECT id FROM spieler WHERE LOWER(name)=LOWER(?) AND geburtsdatum=?",
            (name, geburtsdatum),
        ).fetchone()
        if existing:
            return existing[0]
        cursor = conn.execute(
            """INSERT INTO spieler
               (name, vorname, nachname, geburtsdatum, geschlecht,
                position, hauptposition, nebenposition, altersklasse,
                spielbein, leistungsniveau, mannschaft, trainingsstatus,
                trainer_id, verein_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (name, vorname, nachname, geburtsdatum, geschlecht,
             hauptposition, hauptposition, nebenposition, altersklasse,
             spielbein, leistungsniveau, mannschaft, trainingsstatus,
             trainer_id, verein_id),
        )
        return cursor.lastrowid


# ─── Einwilligung / Zweckbestimmung ────────────────────────────────────────

def einwilligung_speichern(version: str, benutzer: str = "Trainer") -> None:
    """Speichert eine neue Bestätigung der Zweckbestimmung."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO einwilligung (datum, version, benutzer) VALUES (?,?,?)",
            (str(date.today()), version, benutzer),
        )


def einwilligung_letzter() -> dict | None:
    """Gibt die zuletzt gespeicherte Bestätigung zurück oder None."""
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM einwilligung ORDER BY id DESC LIMIT 1"
        ).fetchone())


def einwilligung_alle() -> list[dict]:
    """Gibt alle gespeicherten Bestätigungen zurück (neueste zuerst)."""
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM einwilligung ORDER BY id DESC"
        ).fetchall())


def zustimmung_registrierung_speichern(
    benutzer_id: int,
    datenschutz_version: str,
    agb_version: str,
) -> None:
    """Speichert Datenschutz- und AGB-Zustimmung für einen neu registrierten Benutzer.

    Zeitpunkt wird serverseitig gesetzt (datetime('now')).
    Darf nur einmal direkt nach der Registrierung aufgerufen werden.
    Bestehende Alt-Accounts ohne Zustimmung werden nicht verändert.
    """
    import datetime as _dt
    now = _dt.datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            """UPDATE benutzer
               SET datenschutz_akzeptiert    = 1,
                   datenschutz_akzeptiert_am = ?,
                   datenschutz_version       = ?,
                   agb_akzeptiert            = 1,
                   agb_akzeptiert_am         = ?,
                   agb_version               = ?
               WHERE id = ?""",
            (now, datenschutz_version, now, agb_version, benutzer_id),
        )


# ─── Spieler ───────────────────────────────────────────────────────────────

def spieler_laden(benutzer_id=None, rolle="Trainer", verein_id=None):
    """Lädt Spieler gefiltert nach Benutzerrolle (Multi-Tenant-Sicherheit).

    Superadmin  → alle Spieler
    Vereinsadmin → alle Spieler seines Vereins
    Trainer     → nur eigene Spieler (trainer_id = benutzer_id)
    """
    with get_conn() as conn:
        if rolle == "Superadmin":
            return _rows(conn.execute(
                "SELECT * FROM spieler ORDER BY name"
            ).fetchall())
        if rolle == "Vereinsadmin":
            return _rows(conn.execute(
                "SELECT * FROM spieler WHERE verein_id=? ORDER BY name",
                (verein_id,),
            ).fetchall())
        # Trainer (default)
        if benutzer_id is not None:
            return _rows(conn.execute(
                "SELECT * FROM spieler WHERE trainer_id=? ORDER BY name",
                (benutzer_id,),
            ).fetchall())
        # Fallback: kein User (Legacy / Einzelbetrieb ohne Login)
        return _rows(conn.execute("SELECT * FROM spieler ORDER BY name").fetchall())


def spieler_by_id(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute("SELECT * FROM spieler WHERE id=?", (spieler_id,)).fetchone())


def spieler_loeschen(spieler_id):
    with get_conn() as conn:
        # Tabellen ohne ON DELETE CASCADE müssen hier manuell bereinigt werden.
        # Tabellen MIT ON DELETE CASCADE (z.B. spiro_test, kraft_test, spieler_zuweisung_log)
        # werden beim DELETE FROM spieler automatisch kaskadiert — kein Eintrag nötig.
        # ⚠ Neue Tabellen mit spieler_id FK ohne CASCADE müssen hier ergänzt werden.
        # tools/test_spieler_loeschen.py stellt sicher, dass keine Tabelle fehlt.
        for tabelle in [
            "verletzung", "anthropometrie", "agilitaet_test", "ausdauer_test",
            "sprint_test", "sprung_test", "fms_test", "y_balance_test",
            "trainingsplan", "trainingsplan_versionen", "periodisierung",
            "trainerbeobachtung", "spieler_zuweisung_log",
        ]:
            try:
                conn.execute(f"DELETE FROM {tabelle} WHERE spieler_id=?", (spieler_id,))
            except Exception:
                pass  # Tabelle evtl. noch nicht vorhanden
        conn.execute("DELETE FROM spieler WHERE id=?", (spieler_id,))


def spieler_trainer_zuweisen(spieler_id: int, trainer_id, verein_id,
                             aufrufender_verein_id=None,
                             ausfuehrender_id=None) -> None:
    """Weist einem Spieler Trainer und Verein zu – mit serverseitiger Validierung.

    Regeln:
    - trainer_id darf None sein (Trainer entfernen).
    - Ist trainer_id gesetzt, muss der Benutzer Rolle "Trainer" und aktiv=1 haben.
    - Sind sowohl trainer_id als auch verein_id gesetzt, muss der Trainer zum
      angegebenen Verein gehören.
    - Ist aufrufender_verein_id gesetzt (Vereinsadmin-Kontext), wird verein_id
      serverseitig auf aufrufender_verein_id erzwungen und darf nicht abweichen.

    Raises:
        ValueError: Bei ungültiger Kombination.
    """
    with get_conn() as conn:
        # Vereinsadmin: Verein erzwingen
        if aufrufender_verein_id is not None:
            verein_id = aufrufender_verein_id

        # Trainer validieren
        if trainer_id is not None:
            row = conn.execute(
                "SELECT id, rolle, aktiv, verein_id FROM benutzer WHERE id=?",
                (trainer_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Benutzer {trainer_id} existiert nicht.")
            if row["rolle"] != "Trainer":
                raise ValueError(
                    f"Benutzer {trainer_id} hat Rolle '{row['rolle']}', nicht 'Trainer'."
                )
            if not row["aktiv"]:
                raise ValueError(f"Trainer {trainer_id} ist deaktiviert.")
            if verein_id is not None and row["verein_id"] != verein_id:
                raise ValueError(
                    f"Trainer {trainer_id} gehört zu Verein {row['verein_id']}, "
                    f"nicht zu Verein {verein_id}."
                )

        # Alte Werte lesen für Logging
        alt = conn.execute(
            "SELECT trainer_id, verein_id FROM spieler WHERE id=?",
            (spieler_id,),
        ).fetchone()
        alt_tid = alt["trainer_id"] if alt else None
        alt_vid = alt["verein_id"] if alt else None

        conn.execute(
            "UPDATE spieler SET trainer_id=?, verein_id=? WHERE id=?",
            (trainer_id, verein_id, spieler_id),
        )

        # Nur loggen wenn sich etwas geändert hat
        if alt_tid != trainer_id or alt_vid != verein_id:
            conn.execute(
                """INSERT INTO spieler_zuweisung_log
                   (spieler_id, ausfuehrender_id, alt_trainer_id, neu_trainer_id,
                    alt_verein_id, neu_verein_id)
                   VALUES (?,?,?,?,?,?)""",
                (spieler_id, ausfuehrender_id, alt_tid, trainer_id, alt_vid, verein_id),
            )

            # Spielername für Benachrichtigungstext ermitteln
            _sp = conn.execute(
                "SELECT name FROM spieler WHERE id=?", (spieler_id,)
            ).fetchone()
            _sp_name = _sp["name"] if _sp else f"Spieler #{spieler_id}"

            # Alten Trainer benachrichtigen (nur wenn wirklich gewechselt und es einen alten Trainer gab)
            if alt_tid is not None and alt_tid != trainer_id:
                _neu_name = "— kein Trainer —"
                if trainer_id is not None:
                    _neu_row = conn.execute(
                        "SELECT vorname, nachname FROM benutzer WHERE id=?", (trainer_id,)
                    ).fetchone()
                    if _neu_row:
                        _neu_name = f"{_neu_row['vorname']} {_neu_row['nachname']}".strip()
                _msg = (
                    f"Spieler **{_sp_name}** wurde einem anderen Trainer zugewiesen. "
                    f"Neuer Trainer: {_neu_name}."
                )
                try:
                    conn.execute(
                        "INSERT INTO benachrichtigungen (benutzer_id, typ, text) VALUES (?,?,?)",
                        (alt_tid, "spieler_wechsel", _msg),
                    )
                except Exception:
                    pass  # Tabelle evtl. noch nicht migriert


def spieler_aktualisieren(spieler_id, vorname, nachname, geburtsdatum, geschlecht,
                          hauptposition, nebenposition, altersklasse,
                          spielbein, leistungsniveau, mannschaft, trainingsstatus,
                          trainer_id=_UNSET, verein_id=_UNSET,
                          ausfuehrender_id=None):
    """Aktualisiert die Stammdaten eines bestehenden Spielers.

    trainer_id und verein_id sind optional: wird der Parameter weggelassen (Sentinel),
    bleibt der bisherige DB-Wert unverändert. Wird None übergeben, wird der Wert auf NULL gesetzt.
    """
    name = f"{vorname} {nachname}".strip()
    with get_conn() as conn:
        # Alte Zuweisung lesen, falls trainer_id oder verein_id geändert werden
        if trainer_id is not _UNSET or verein_id is not _UNSET:
            alt = conn.execute(
                "SELECT trainer_id, verein_id FROM spieler WHERE id=?",
                (spieler_id,),
            ).fetchone()
            alt_tid = alt["trainer_id"] if alt else None
            alt_vid = alt["verein_id"] if alt else None
        else:
            alt_tid = alt_vid = None

        conn.execute(
            """UPDATE spieler SET
               name=?, vorname=?, nachname=?, geburtsdatum=?, geschlecht=?,
               position=?, hauptposition=?, nebenposition=?, altersklasse=?,
               spielbein=?, leistungsniveau=?, mannschaft=?, trainingsstatus=?
               WHERE id=?""",
            (name, vorname, nachname, geburtsdatum, geschlecht,
             hauptposition, hauptposition, nebenposition, altersklasse,
             spielbein, leistungsniveau, mannschaft, trainingsstatus,
             spieler_id),
        )
        if trainer_id is not _UNSET:
            conn.execute("UPDATE spieler SET trainer_id=? WHERE id=?", (trainer_id, spieler_id))
        if verein_id is not _UNSET:
            conn.execute("UPDATE spieler SET verein_id=? WHERE id=?", (verein_id, spieler_id))

        # Zuweisung loggen, wenn sich trainer_id oder verein_id geändert hat
        neu_tid = trainer_id if trainer_id is not _UNSET else alt_tid
        neu_vid = verein_id  if verein_id  is not _UNSET else alt_vid
        if (trainer_id is not _UNSET or verein_id is not _UNSET) and (alt_tid != neu_tid or alt_vid != neu_vid):
            conn.execute(
                """INSERT INTO spieler_zuweisung_log
                   (spieler_id, ausfuehrender_id, alt_trainer_id, neu_trainer_id,
                    alt_verein_id, neu_verein_id)
                   VALUES (?,?,?,?,?,?)""",
                (spieler_id, ausfuehrender_id, alt_tid, neu_tid, alt_vid, neu_vid),
            )

            # Alten Trainer benachrichtigen (nur bei echtem Trainer-Wechsel)
            if alt_tid is not None and alt_tid != neu_tid:
                _sp_name = name  # name is already computed above
                _neu_name = "— kein Trainer —"
                if neu_tid is not None:
                    _neu_row = conn.execute(
                        "SELECT vorname, nachname FROM benutzer WHERE id=?", (neu_tid,)
                    ).fetchone()
                    if _neu_row:
                        _neu_name = f"{_neu_row['vorname']} {_neu_row['nachname']}".strip()
                _msg = (
                    f"Spieler **{_sp_name}** wurde einem anderen Trainer zugewiesen. "
                    f"Neuer Trainer: {_neu_name}."
                )
                try:
                    conn.execute(
                        "INSERT INTO benachrichtigungen (benutzer_id, typ, text) VALUES (?,?,?)",
                        (alt_tid, "spieler_wechsel", _msg),
                    )
                except Exception:
                    pass  # Tabelle evtl. noch nicht migriert


def benachrichtigung_schreiben(benutzer_id: int, text: str, typ: str = "info") -> None:
    """Schreibt eine neue In-App-Benachrichtigung für einen Benutzer."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO benachrichtigungen (benutzer_id, typ, text) VALUES (?,?,?)",
            (benutzer_id, typ, text),
        )


def benachrichtigungen_laden(benutzer_id: int, nur_ungelesen: bool = False) -> list[dict]:
    """Lädt Benachrichtigungen für einen Benutzer (neueste zuerst)."""
    with get_conn() as conn:
        if nur_ungelesen:
            rows = conn.execute(
                "SELECT * FROM benachrichtigungen WHERE benutzer_id=? AND gelesen=0 ORDER BY id DESC",
                (benutzer_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM benachrichtigungen WHERE benutzer_id=? ORDER BY id DESC LIMIT 50",
                (benutzer_id,),
            ).fetchall()
    return _rows(rows)


def benachrichtigung_gelesen_setzen(benachrichtigung_id: int) -> None:
    """Markiert eine einzelne Benachrichtigung als gelesen."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE benachrichtigungen SET gelesen=1 WHERE id=?",
            (benachrichtigung_id,),
        )


def benachrichtigungen_alle_gelesen(benutzer_id: int) -> None:
    """Markiert alle Benachrichtigungen eines Benutzers als gelesen."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE benachrichtigungen SET gelesen=1 WHERE benutzer_id=?",
            (benutzer_id,),
        )


def zuweisung_log_laden(spieler_id: int) -> list[dict]:
    """Gibt alle Zuweisung-Log-Einträge für einen Spieler zurück (neueste zuerst).

    Jeder Eintrag enthält zusätzlich aufgelöste Namen für Trainer und Vereine
    (alt_trainer_name, neu_trainer_name, alt_verein_name, neu_verein_name).
    """
    with get_conn() as conn:
        rows = _rows(conn.execute(
            """SELECT l.*,
                      b_aus.vorname || ' ' || b_aus.nachname AS ausfuehrender_name,
                      b_alt.vorname || ' ' || b_alt.nachname AS alt_trainer_name,
                      b_neu.vorname || ' ' || b_neu.nachname AS neu_trainer_name,
                      v_alt.name AS alt_verein_name,
                      v_neu.name AS neu_verein_name
               FROM spieler_zuweisung_log l
               LEFT JOIN benutzer b_aus ON b_aus.id = l.ausfuehrender_id
               LEFT JOIN benutzer b_alt ON b_alt.id = l.alt_trainer_id
               LEFT JOIN benutzer b_neu ON b_neu.id = l.neu_trainer_id
               LEFT JOIN vereine  v_alt ON v_alt.id = l.alt_verein_id
               LEFT JOIN vereine  v_neu ON v_neu.id = l.neu_verein_id
               WHERE l.spieler_id = ?
               ORDER BY l.id DESC""",
            (spieler_id,),
        ).fetchall())
    return rows


def db_komplett_zuruecksetzen():
    """Löscht alle Bewegungsdaten — Spieler, Tests, Verletzungen, Einwilligungen.
    Die Datenbankstruktur bleibt erhalten; nur Datensätze werden entfernt."""
    _TABELLEN = [
        # Kind-Tabellen zuerst (Fremdschlüssel-Reihenfolge)
        "trainerbeobachtung", "checkliste_custom",
        "kraft_test_versuch", "kraft_test",
        "verletzung", "anthropometrie", "agilitaet_test", "ausdauer_test",
        "sprint_test", "sprung_test", "fms_test", "y_balance_test",
        "trainingsplan", "periodisierung", "einwilligung", "spieler",
    ]
    with get_conn() as conn:
        for tabelle in _TABELLEN:
            try:
                conn.execute(f"DELETE FROM {tabelle}")
            except Exception:
                pass  # Tabelle noch nicht vorhanden


# ─── Trainingsphilosophie ────────────────────────────────────────────────────

def philosophie_speichern(spieler_id: int, key: str | None) -> None:
    """Speichert die gewählte Trainingsphilosophie für einen Spieler."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE spieler SET philosophie_key=? WHERE id=?",
            (key, spieler_id),
        )


def philosophie_laden(spieler_id: int) -> str | None:
    """Lädt die gespeicherte Trainingsphilosophie eines Spielers."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT philosophie_key FROM spieler WHERE id=?",
            (spieler_id,),
        ).fetchone()
    if row:
        try:
            return row["philosophie_key"]
        except (IndexError, KeyError, TypeError):
            return row[0] if row[0] is not None else None
    return None


# ─── Verletzungshistorie ────────────────────────────────────────────────────

def verletzung_speichern(spieler_id, datum, art, koerperteil, schwere, ausfall_tage, notizen):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO verletzung
               (spieler_id, datum, art, koerperteil, schwere, ausfall_tage, notizen)
               VALUES (?,?,?,?,?,?,?)""",
            (spieler_id, datum, art, koerperteil, schwere, ausfall_tage, notizen),
        )


def verletzungen_laden(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM verletzung WHERE spieler_id=? ORDER BY datum DESC",
            (spieler_id,),
        ).fetchall())


def verletzung_loeschen(verletzung_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM verletzung WHERE id=?", (verletzung_id,))


# ─── FMS ───────────────────────────────────────────────────────────────────

def fms_speichern(spieler_id, datum, deep, hurdle_l, hurdle_r, inline_l, inline_r,
                  shoulder_l, shoulder_r, aslr_l, aslr_r, trunk, rotary_l, rotary_r,
                  score, bewertung, asymmetrie, schwerpunkt):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO fms_test
        (spieler_id,datum,deep_squat,hurdle_links,hurdle_rechts,inline_links,
         inline_rechts,shoulder_links,shoulder_rechts,aslr_links,aslr_rechts,
         trunk,rotary_links,rotary_rechts,score,bewertung,asymmetrie,schwerpunkt)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, deep, hurdle_l, hurdle_r, inline_l, inline_r,
              shoulder_l, shoulder_r, aslr_l, aslr_r, trunk, rotary_l, rotary_r,
              score, bewertung, asymmetrie, schwerpunkt))


def fms_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM fms_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def fms_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT datum,score,bewertung,asymmetrie,schwerpunkt FROM fms_test WHERE spieler_id=? ORDER BY datum",
            (spieler_id,),
        ).fetchall())


def fms_history_full(spieler_id):
    """Vollständiger FMS-Verlauf — alle Einzelbewertungen und Gesamtscore."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum,deep_squat,hurdle_links,hurdle_rechts,
                      inline_links,inline_rechts,shoulder_links,shoulder_rechts,
                      aslr_links,aslr_rechts,trunk,rotary_links,rotary_rechts,
                      score,bewertung,asymmetrie,schwerpunkt
               FROM fms_test WHERE spieler_id=? ORDER BY datum""",
            (spieler_id,),
        ).fetchall())


# ─── Anthropometrie ────────────────────────────────────────────────────────

def anthropometrie_speichern(spieler_id, datum, groesse, gewicht, sitzhoehe,
                              beinlaenge, armspannweite, koerperfett, muskelmasse,
                              bmi, bmi_kat, phv_offset, reifestatus,
                              beinlaenge_r=None, beinlaenge_l=None,
                              koerperfett_methode=None):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO anthropometrie
        (spieler_id,datum,groesse,gewicht,sitzhoehe,beinlaenge,armspannweite,
         koerperfett,muskelmasse,bmi,bmi_kategorie,phv_offset,reifestatus,
         beinlaenge_r,beinlaenge_l,koerperfett_methode)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, groesse, gewicht, sitzhoehe, beinlaenge,
              armspannweite, koerperfett, muskelmasse, bmi, bmi_kat, phv_offset, reifestatus,
              beinlaenge_r, beinlaenge_l, koerperfett_methode))


def anthropometrie_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM anthropometrie WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def anthropometrie_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum,groesse,gewicht,koerperfett,muskelmasse,bmi,bmi_kategorie,
                      sitzhoehe,beinlaenge,armspannweite,phv_offset,reifestatus,
                      COALESCE(beinlaenge_r,0) as beinlaenge_r,
                      COALESCE(beinlaenge_l,0) as beinlaenge_l,
                      koerperfett_methode
               FROM anthropometrie WHERE spieler_id=? ORDER BY datum""",
            (spieler_id,),
        ).fetchall())


def anthropometrie_loeschen_letzten(spieler_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM anthropometrie WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM anthropometrie WHERE id=?", (row["id"],))


# ─── Y-Balance ─────────────────────────────────────────────────────────────

def y_balance_speichern(spieler_id, datum, ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
                        diff_a, diff_pm, diff_pl, comp_r, comp_l, asymmetrie, schwerpunkt):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO y_balance_test
        (spieler_id,datum,anterior_rechts,anterior_links,posteromedial_rechts,
         posteromedial_links,posterolateral_rechts,posterolateral_links,
         diff_anterior,diff_posteromedial,diff_posterolateral,
         composite_rechts,composite_links,asymmetrie,schwerpunkt)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
              diff_a, diff_pm, diff_pl, comp_r, comp_l, asymmetrie, schwerpunkt))


def y_balance_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM y_balance_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def y_balance_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT datum,composite_rechts,composite_links,asymmetrie,schwerpunkt FROM y_balance_test WHERE spieler_id=? ORDER BY datum",
            (spieler_id,),
        ).fetchall())


def y_balance_history_full(spieler_id):
    """Vollständiger Y-Balance-Verlauf — alle Einzelreichweiten und Composite-Scores."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum,anterior_rechts,anterior_links,
                      posteromedial_rechts,posteromedial_links,
                      posterolateral_rechts,posterolateral_links,
                      composite_rechts,composite_links,
                      diff_anterior,diff_posteromedial,diff_posterolateral,
                      asymmetrie,schwerpunkt
               FROM y_balance_test WHERE spieler_id=? ORDER BY datum""",
            (spieler_id,),
        ).fetchall())


# ─── Training ──────────────────────────────────────────────────────────────

def training_bibliothek_laden():
    """Return all exercises from the training table."""
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM training ORDER BY bereich, problem").fetchall())


def training_nach_bereich(bereich):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT bereich,uebung,problem,saetze,wiederholungen,haeufigkeit FROM training WHERE LOWER(bereich)=LOWER(?)",
            (bereich,),
        ).fetchall())


def training_count():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM training").fetchone()[0]


def training_bulk_insert(uebungen):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO training (bereich,problem,uebung,saetze,wiederholungen,haeufigkeit) VALUES (?,?,?,?,?,?)",
            uebungen,
        )


# ─── Sprint ────────────────────────────────────────────────────────────────

def sprint_speichern(spieler_id, datum,
                     v1_5, v2_5, v3_5, b5,
                     v1_10, v2_10, v3_10, b10,
                     v1_20, v2_20, v3_20, b20,
                     v1_30, v2_30, v3_30, b30,
                     beschl_index, bew_10, bew_30, defizite,
                     v1_40=None, v2_40=None, v3_40=None, b40=None):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO sprint_test
        (spieler_id,datum,
         v1_5m,v2_5m,v3_5m,beste_5m,
         v1_10m,v2_10m,v3_10m,beste_10m,
         v1_20m,v2_20m,v3_20m,beste_20m,
         v1_30m,v2_30m,v3_30m,beste_30m,
         v1_40m,v2_40m,v3_40m,beste_40m,
         beschl_index,bewertung_10m,bewertung_30m,defizite)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum,
              v1_5, v2_5, v3_5, b5,
              v1_10, v2_10, v3_10, b10,
              v1_20, v2_20, v3_20, b20,
              v1_30, v2_30, v3_30, b30,
              v1_40, v2_40, v3_40, b40 or 0,
              beschl_index, bew_10, bew_30, defizite))


def sprint_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM sprint_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def sprint_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum,beste_5m,beste_10m,beste_20m,beste_30m,
                      COALESCE(beste_40m,0) as beste_40m,
                      beschl_index,bewertung_10m
               FROM sprint_test WHERE spieler_id=? ORDER BY datum""",
            (spieler_id,),
        ).fetchall())


# ─── Sprung ────────────────────────────────────────────────────────────────

def sprung_speichern(spieler_id, datum,
                     cmj_beid, cmj_rechts, cmj_links, cmj_asym,
                     squat_jump, dj_hoehe, dj_kz, rsi,
                     standweit, bew_cmj, defizite,
                     v1_cmj_beid=None, v2_cmj_beid=None, v3_cmj_beid=None,
                     v1_cmj_r=None, v2_cmj_r=None, v3_cmj_r=None,
                     v1_cmj_l=None, v2_cmj_l=None, v3_cmj_l=None,
                     v1_squat=None, v2_squat=None, v3_squat=None,
                     v1_dj_h=None, v2_dj_h=None, v3_dj_h=None,
                     v1_dj_kz=None, v2_dj_kz=None, v3_dj_kz=None,
                     v1_swj=None, v2_swj=None, v3_swj=None):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO sprung_test
        (spieler_id,datum,cmj_beid,cmj_rechts,cmj_links,cmj_asymmetrie,
         squat_jump,drop_jump_hoehe,drop_jump_kz,rsi,standweit,bewertung_cmj,defizite,
         v1_cmj_beid,v2_cmj_beid,v3_cmj_beid,
         v1_cmj_r,v2_cmj_r,v3_cmj_r,
         v1_cmj_l,v2_cmj_l,v3_cmj_l,
         v1_squat,v2_squat,v3_squat,
         v1_dj_h,v2_dj_h,v3_dj_h,
         v1_dj_kz,v2_dj_kz,v3_dj_kz,
         v1_swj,v2_swj,v3_swj)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(spieler_id,datum) DO UPDATE SET
            cmj_beid=excluded.cmj_beid,cmj_rechts=excluded.cmj_rechts,
            cmj_links=excluded.cmj_links,cmj_asymmetrie=excluded.cmj_asymmetrie,
            squat_jump=excluded.squat_jump,drop_jump_hoehe=excluded.drop_jump_hoehe,
            drop_jump_kz=excluded.drop_jump_kz,rsi=excluded.rsi,
            standweit=excluded.standweit,bewertung_cmj=excluded.bewertung_cmj,
            defizite=excluded.defizite,
            v1_cmj_beid=excluded.v1_cmj_beid,v2_cmj_beid=excluded.v2_cmj_beid,v3_cmj_beid=excluded.v3_cmj_beid,
            v1_cmj_r=excluded.v1_cmj_r,v2_cmj_r=excluded.v2_cmj_r,v3_cmj_r=excluded.v3_cmj_r,
            v1_cmj_l=excluded.v1_cmj_l,v2_cmj_l=excluded.v2_cmj_l,v3_cmj_l=excluded.v3_cmj_l,
            v1_squat=excluded.v1_squat,v2_squat=excluded.v2_squat,v3_squat=excluded.v3_squat,
            v1_dj_h=excluded.v1_dj_h,v2_dj_h=excluded.v2_dj_h,v3_dj_h=excluded.v3_dj_h,
            v1_dj_kz=excluded.v1_dj_kz,v2_dj_kz=excluded.v2_dj_kz,v3_dj_kz=excluded.v3_dj_kz,
            v1_swj=excluded.v1_swj,v2_swj=excluded.v2_swj,v3_swj=excluded.v3_swj
        """, (spieler_id, datum,
              cmj_beid, cmj_rechts, cmj_links, cmj_asym,
              squat_jump, dj_hoehe, dj_kz, rsi,
              standweit, bew_cmj, defizite,
              v1_cmj_beid, v2_cmj_beid, v3_cmj_beid,
              v1_cmj_r, v2_cmj_r, v3_cmj_r,
              v1_cmj_l, v2_cmj_l, v3_cmj_l,
              v1_squat, v2_squat, v3_squat,
              v1_dj_h, v2_dj_h, v3_dj_h,
              v1_dj_kz, v2_dj_kz, v3_dj_kz,
              v1_swj, v2_swj, v3_swj))


def sprung_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM sprung_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def sprung_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT datum,cmj_beid,squat_jump,drop_jump_hoehe,rsi,standweit,cmj_asymmetrie,bewertung_cmj FROM sprung_test WHERE spieler_id=? ORDER BY datum",
            (spieler_id,),
        ).fetchall())


# ─── Agilität ──────────────────────────────────────────────────────────────

def agilitaet_speichern(spieler_id, datum, t505_r, t505_l, asym_505,
                         t5_10_5, t_test, illinois,
                         bew_505, bew_t_test, bew_illinois, defizite,
                         v1_t505_r=None, v2_t505_r=None, v3_t505_r=None,
                         v1_t505_l=None, v2_t505_l=None, v3_t505_l=None,
                         v1_t5_10_5=None, v2_t5_10_5=None, v3_t5_10_5=None,
                         v1_t_test=None, v2_t_test=None, v3_t_test=None,
                         v1_illinois=None, v2_illinois=None, v3_illinois=None,
                         # Phase 0C — neue Tests
                         modified_t_test=None, pro_agility=None,
                         arrowhead_r=None, arrowhead_l=None,
                         zigzag=None, balsom=None,
                         v1_modified_t_test=None, v2_modified_t_test=None, v3_modified_t_test=None,
                         v1_pro_agility=None, v2_pro_agility=None, v3_pro_agility=None,
                         v1_arrowhead_r=None, v2_arrowhead_r=None, v3_arrowhead_r=None,
                         v1_arrowhead_l=None, v2_arrowhead_l=None, v3_arrowhead_l=None,
                         v1_zigzag=None, v2_zigzag=None, v3_zigzag=None,
                         v1_balsom=None, v2_balsom=None, v3_balsom=None):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO agilitaet_test
        (spieler_id,datum,t505_r,t505_l,asym_505,t5_10_5,t_test,illinois,
         bew_505,bew_t_test,bew_illinois,defizite,
         v1_t505_r,v2_t505_r,v3_t505_r,
         v1_t505_l,v2_t505_l,v3_t505_l,
         v1_t5_10_5,v2_t5_10_5,v3_t5_10_5,
         v1_t_test,v2_t_test,v3_t_test,
         v1_illinois,v2_illinois,v3_illinois,
         modified_t_test,pro_agility,arrowhead_r,arrowhead_l,zigzag,balsom,
         v1_modified_t_test,v2_modified_t_test,v3_modified_t_test,
         v1_pro_agility,v2_pro_agility,v3_pro_agility,
         v1_arrowhead_r,v2_arrowhead_r,v3_arrowhead_r,
         v1_arrowhead_l,v2_arrowhead_l,v3_arrowhead_l,
         v1_zigzag,v2_zigzag,v3_zigzag,
         v1_balsom,v2_balsom,v3_balsom)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(spieler_id,datum) DO UPDATE SET
            t505_r=excluded.t505_r,t505_l=excluded.t505_l,
            asym_505=excluded.asym_505,t5_10_5=excluded.t5_10_5,
            t_test=excluded.t_test,illinois=excluded.illinois,
            bew_505=excluded.bew_505,bew_t_test=excluded.bew_t_test,
            bew_illinois=excluded.bew_illinois,defizite=excluded.defizite,
            v1_t505_r=excluded.v1_t505_r,v2_t505_r=excluded.v2_t505_r,v3_t505_r=excluded.v3_t505_r,
            v1_t505_l=excluded.v1_t505_l,v2_t505_l=excluded.v2_t505_l,v3_t505_l=excluded.v3_t505_l,
            v1_t5_10_5=excluded.v1_t5_10_5,v2_t5_10_5=excluded.v2_t5_10_5,v3_t5_10_5=excluded.v3_t5_10_5,
            v1_t_test=excluded.v1_t_test,v2_t_test=excluded.v2_t_test,v3_t_test=excluded.v3_t_test,
            v1_illinois=excluded.v1_illinois,v2_illinois=excluded.v2_illinois,v3_illinois=excluded.v3_illinois,
            modified_t_test=excluded.modified_t_test,pro_agility=excluded.pro_agility,
            arrowhead_r=excluded.arrowhead_r,arrowhead_l=excluded.arrowhead_l,
            zigzag=excluded.zigzag,balsom=excluded.balsom,
            v1_modified_t_test=excluded.v1_modified_t_test,v2_modified_t_test=excluded.v2_modified_t_test,v3_modified_t_test=excluded.v3_modified_t_test,
            v1_pro_agility=excluded.v1_pro_agility,v2_pro_agility=excluded.v2_pro_agility,v3_pro_agility=excluded.v3_pro_agility,
            v1_arrowhead_r=excluded.v1_arrowhead_r,v2_arrowhead_r=excluded.v2_arrowhead_r,v3_arrowhead_r=excluded.v3_arrowhead_r,
            v1_arrowhead_l=excluded.v1_arrowhead_l,v2_arrowhead_l=excluded.v2_arrowhead_l,v3_arrowhead_l=excluded.v3_arrowhead_l,
            v1_zigzag=excluded.v1_zigzag,v2_zigzag=excluded.v2_zigzag,v3_zigzag=excluded.v3_zigzag,
            v1_balsom=excluded.v1_balsom,v2_balsom=excluded.v2_balsom,v3_balsom=excluded.v3_balsom
        """, (spieler_id, datum, t505_r, t505_l, asym_505,
              t5_10_5, t_test, illinois,
              bew_505, bew_t_test, bew_illinois, defizite,
              v1_t505_r, v2_t505_r, v3_t505_r,
              v1_t505_l, v2_t505_l, v3_t505_l,
              v1_t5_10_5, v2_t5_10_5, v3_t5_10_5,
              v1_t_test, v2_t_test, v3_t_test,
              v1_illinois, v2_illinois, v3_illinois,
              modified_t_test or 0, pro_agility or 0,
              arrowhead_r or 0, arrowhead_l or 0,
              zigzag or 0, balsom or 0,
              v1_modified_t_test, v2_modified_t_test, v3_modified_t_test,
              v1_pro_agility, v2_pro_agility, v3_pro_agility,
              v1_arrowhead_r, v2_arrowhead_r, v3_arrowhead_r,
              v1_arrowhead_l, v2_arrowhead_l, v3_arrowhead_l,
              v1_zigzag, v2_zigzag, v3_zigzag,
              v1_balsom, v2_balsom, v3_balsom))


def agilitaet_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM agilitaet_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def agilitaet_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT datum,t505_r,t505_l,asym_505,t5_10_5,t_test,illinois,bew_t_test,
                      COALESCE(modified_t_test,0) as modified_t_test,
                      COALESCE(pro_agility,0) as pro_agility,
                      COALESCE(arrowhead_r,0) as arrowhead_r,
                      COALESCE(arrowhead_l,0) as arrowhead_l,
                      COALESCE(zigzag,0) as zigzag,
                      COALESCE(balsom,0) as balsom
               FROM agilitaet_test WHERE spieler_id=? ORDER BY datum""",
            (spieler_id,),
        ).fetchall())


# ─── Ausdauer ──────────────────────────────────────────────────────────────

def ausdauer_speichern(spieler_id, datum, test_typ, distanz_m,
                        hf_max, rpe, vo2max, bewertung, altersgruppe, defizite):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO ausdauer_test
        (spieler_id,datum,test_typ,distanz_m,hf_max,rpe,vo2max,bewertung,altersgruppe,defizite)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, test_typ, distanz_m,
              hf_max, rpe, vo2max, bewertung, altersgruppe, defizite))


def ausdauer_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM ausdauer_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def ausdauer_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT datum,test_typ,distanz_m,vo2max,bewertung,hf_max,rpe FROM ausdauer_test WHERE spieler_id=? ORDER BY datum",
            (spieler_id,),
        ).fetchall())


# ─── Spiroergometrie ───────────────────────────────────────────────────────

def spiro_protokoll_alle() -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM spiro_protokoll WHERE aktiv=1 ORDER BY name"
        ).fetchall())


def spiro_protokoll_speichern(name, geraeteart, startgeschwindigkeit, steigerung,
                               stufendauer, steigung=0, pausenzeit=0, max_stufen=None,
                               hersteller=None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO spiro_protokoll
               (name,geraeteart,hersteller,startgeschwindigkeit,steigerung,
                stufendauer,steigung,pausenzeit,max_stufen)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, geraeteart, hersteller, startgeschwindigkeit, steigerung,
             stufendauer, steigung, pausenzeit, max_stufen),
        )
        return cur.lastrowid


def spiro_test_speichern(spieler_id, datum, testtyp, geraeteart=None,
                          protokoll_id=None, testort=None, tester=None,
                          mit_spiro=0, mit_laktat=0, raumtemperatur=None,
                          letzte_mahlzeit=None, letzte_intensive_einheit=None,
                          akute_beschwerden=None, koerpergewicht=None,
                          maximale_geschwindigkeit=None, maximale_herzfrequenz=None,
                          vo2_peak=None, vo2_max=None, geschaetzte_vo2max=None,
                          vt1_geschwindigkeit=None, vt1_herzfrequenz=None,
                          vt2_geschwindigkeit=None, vt2_herzfrequenz=None,
                          laktatschwelle_methode=None, schwelle_geschwindigkeit=None,
                          schwelle_herzfrequenz=None, schwelle_laktat=None,
                          ruhelaktat=None, laktat_blutentnahmeort=None,
                          laktat_messgeraet=None, rpe_max=None,
                          abbruchgrund=None, bemerkung=None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO spiro_test
               (spieler_id,datum,testtyp,geraeteart,protokoll_id,testort,tester,
                mit_spiro,mit_laktat,raumtemperatur,letzte_mahlzeit,
                letzte_intensive_einheit,akute_beschwerden,koerpergewicht,
                maximale_geschwindigkeit,maximale_herzfrequenz,
                vo2_peak,vo2_max,geschaetzte_vo2max,
                vt1_geschwindigkeit,vt1_herzfrequenz,
                vt2_geschwindigkeit,vt2_herzfrequenz,
                laktatschwelle_methode,schwelle_geschwindigkeit,
                schwelle_herzfrequenz,schwelle_laktat,
                ruhelaktat,laktat_blutentnahmeort,laktat_messgeraet,
                rpe_max,abbruchgrund,bemerkung)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (spieler_id, datum, testtyp, geraeteart, protokoll_id, testort, tester,
             mit_spiro, mit_laktat, raumtemperatur, letzte_mahlzeit,
             letzte_intensive_einheit, akute_beschwerden, koerpergewicht,
             maximale_geschwindigkeit, maximale_herzfrequenz,
             vo2_peak, vo2_max, geschaetzte_vo2max,
             vt1_geschwindigkeit, vt1_herzfrequenz,
             vt2_geschwindigkeit, vt2_herzfrequenz,
             laktatschwelle_methode, schwelle_geschwindigkeit,
             schwelle_herzfrequenz, schwelle_laktat,
             ruhelaktat, laktat_blutentnahmeort, laktat_messgeraet,
             rpe_max, abbruchgrund, bemerkung),
        )
        return cur.lastrowid


def spiro_stufen_speichern(spiro_test_id: int, stufen: list[dict]) -> None:
    """Speichert alle Stufen eines Tests. Bestehende werden zuerst gelöscht."""
    with get_conn() as conn:
        conn.execute("DELETE FROM spiro_stufe WHERE spiro_test_id=?", (spiro_test_id,))
        for s in stufen:
            conn.execute(
                """INSERT INTO spiro_stufe
                   (spiro_test_id,stufennummer,geschwindigkeit_kmh,steigung_prozent,
                    dauer_sekunden,strecke_meter,herzfrequenz_bpm,hf_durchschnitt,
                    vo2_absolut,vo2_relativ,vco2,ve,rer,atemfrequenz,sauerstoffpuls,
                    laktat_mmol_l,rpe,stufe_vollstaendig,blutprobe_gueltig,bemerkung)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (spiro_test_id,
                 s.get("stufennummer"), s.get("geschwindigkeit_kmh"),
                 s.get("steigung_prozent"), s.get("dauer_sekunden"),
                 s.get("strecke_meter"), s.get("herzfrequenz_bpm"),
                 s.get("hf_durchschnitt"),
                 s.get("vo2_absolut") or None, s.get("vo2_relativ") or None,
                 s.get("vco2") or None, s.get("ve") or None,
                 s.get("rer") or None, s.get("atemfrequenz") or None,
                 s.get("sauerstoffpuls") or None,
                 s.get("laktat_mmol_l") or None,   # None statt 0 für fehlende Messung
                 s.get("rpe") or None,
                 1 if s.get("stufe_vollstaendig", True) else 0,
                 1 if s.get("blutprobe_gueltig", True) else 0,
                 s.get("bemerkung") or None),
            )


def spiro_nachbelastung_speichern(spiro_test_id: int, eintraege: list[dict]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM spiro_nachbelastung WHERE spiro_test_id=?", (spiro_test_id,))
        for e in eintraege:
            conn.execute(
                """INSERT INTO spiro_nachbelastung
                   (spiro_test_id,zeitpunkt_minuten,herzfrequenz_bpm,laktat_mmol_l,bemerkung)
                   VALUES (?,?,?,?,?)""",
                (spiro_test_id, e.get("zeitpunkt_minuten"),
                 e.get("herzfrequenz_bpm") or None,
                 e.get("laktat_mmol_l") or None,
                 e.get("bemerkung") or None),
            )


def spiro_stufen_laden(spiro_test_id: int) -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM spiro_stufe WHERE spiro_test_id=? ORDER BY stufennummer",
            (spiro_test_id,),
        ).fetchall())


def spiro_nachbelastung_laden(spiro_test_id: int) -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM spiro_nachbelastung WHERE spiro_test_id=? ORDER BY zeitpunkt_minuten",
            (spiro_test_id,),
        ).fetchall())


def spiro_test_letzter(spieler_id: int) -> dict | None:
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM spiro_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def spiro_test_alle(spieler_id: int) -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT t.*, p.name as protokoll_name
               FROM spiro_test t
               LEFT JOIN spiro_protokoll p ON t.protokoll_id = p.id
               WHERE t.spieler_id=?
               ORDER BY t.datum DESC, t.id DESC""",
            (spieler_id,),
        ).fetchall())


def spiro_test_loeschen(test_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM spiro_test WHERE id=?", (test_id,))


# ─── Trainingsplan ─────────────────────────────────────────────────────────

def trainingsplan_loeschen(spieler_id):
    """Löscht alle Trainingsplan-Einträge eines Spielers (wird vom Generator nicht mehr direkt genutzt)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM trainingsplan WHERE spieler_id=?", (spieler_id,))


def trainingsplan_eintrag_speichern(spieler_id, datum, woche, bereich, uebung, saetze, wdh,
                                    haeufigkeit, tag: int = 1,
                                    pause_sekunden: int = 90,
                                    ausfuehrung: str = "kontrolliert",
                                    rpe: int = 7,
                                    energie_system: str = "Gemischt",
                                    equipment: str = "Körpergewicht",
                                    begruendung: str = "",
                                    plan_id: int | None = None,
                                    position: int = 0,
                                    notiz: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trainingsplan (spieler_id,datum,woche,bereich,uebung,saetze,wiederholungen,"
            "haeufigkeit,status,tag,pause_sekunden,ausfuehrung,rpe,energie_system,equipment,begruendung,"
            "plan_id,position,notiz)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (spieler_id, datum, woche, bereich, uebung, saetze, wdh, haeufigkeit, "offen",
             tag, pause_sekunden, ausfuehrung, rpe, energie_system, equipment, begruendung,
             plan_id, position, notiz),
        )


def trainingsplan_laden(spieler_id):
    """Lädt den aktiven Trainingsplan (mit id-Spalte für Bearbeitung)."""
    with get_conn() as conn:
        # Aktive Version suchen
        v_row = conn.execute(
            "SELECT id FROM trainingsplan_versionen WHERE spieler_id=? AND status='AKTIV' ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone()
        if v_row:
            where = "plan_id=?"
            param = (v_row[0],)
        else:
            where = "spieler_id=?"
            param = (spieler_id,)
        return _rows(conn.execute(
            f"SELECT id,bereich,uebung,saetze,wiederholungen,haeufigkeit,woche,"
            f"COALESCE(tag,1) as tag,"
            f"COALESCE(pause_sekunden,90) as pause_sekunden,"
            f"COALESCE(ausfuehrung,'kontrolliert') as ausfuehrung,"
            f"COALESCE(rpe,7) as rpe,"
            f"COALESCE(energie_system,'Gemischt') as energie_system,"
            f"COALESCE(equipment,'Körpergewicht') as equipment,"
            f"COALESCE(begruendung,'') as begruendung,"
            f"COALESCE(position,0) as position,"
            f"COALESCE(notiz,'') as notiz,"
            f"COALESCE(abgehakt,0) as abgehakt "
            f"FROM trainingsplan WHERE {where} ORDER BY woche,tag,COALESCE(position,0),id",
            param,
        ).fetchall())


# ─── SCHRITT 4: Trainingsplan-Versionierung ───────────────────────────────────

def plan_version_erstellen(spieler_id: int, datum: str, erstellt_von: str = "",
                           modus: str = "Basis", schwerpunkt: str = "",
                           trainingszeit_min: int = 60, notizen: str = "",
                           diagnose_snapshot: str = "",
                           wochenplanung_json: str | None = None) -> int:
    """Erstellt eine neue AKTIV-Version und gibt deren ID zurück."""
    with get_conn() as conn:
        max_v = (conn.execute(
            "SELECT COALESCE(MAX(version_nr),0) FROM trainingsplan_versionen WHERE spieler_id=?",
            (spieler_id,),
        ).fetchone() or [0])[0]
        cur = conn.execute(
            "INSERT INTO trainingsplan_versionen "
            "(spieler_id,version_nr,datum,erstellt_von,status,modus,schwerpunkt,trainingszeit_min,notizen,"
            "diagnose_snapshot,wochenplanung_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (spieler_id, max_v + 1, datum, erstellt_von, "AKTIV", modus,
             schwerpunkt, trainingszeit_min, notizen, diagnose_snapshot, wochenplanung_json),
        )
        return cur.lastrowid


def plan_version_archivieren_aktiv(spieler_id: int):
    """Archiviert die aktuell aktive Version eines Spielers."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE trainingsplan_versionen SET status='ARCHIVIERT' WHERE spieler_id=? AND status='AKTIV'",
            (spieler_id,),
        )


def plan_aktive_version(spieler_id: int) -> dict | None:
    """Gibt die aktive Planversion als Dict zurück oder None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id,version_nr,datum,erstellt_von,status,modus,schwerpunkt,trainingszeit_min,notizen,"
            "COALESCE(wochenplanung_json,NULL) as wochenplanung_json "
            "FROM trainingsplan_versionen WHERE spieler_id=? AND status='AKTIV' ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone()
        if not row:
            return None
        return dict(zip(["id","version_nr","datum","erstellt_von","status","modus",
                          "schwerpunkt","trainingszeit_min","notizen","wochenplanung_json"], row))


def plan_aktive_version_id(spieler_id: int) -> int | None:
    v = plan_aktive_version(spieler_id)
    return v["id"] if v else None


def plan_versionen_laden(spieler_id: int) -> list:
    """Alle Versionen (AKTIV + ARCHIVIERT) für Historien-Anzeige.
    Gibt wochenplanung_json mit zurück (NULL für alte Pläne ohne Wochenplanung)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id,version_nr,datum,erstellt_von,status,modus,trainingszeit_min,notizen,"
            "COALESCE(wochenplanung_json,NULL) as wochenplanung_json "
            "FROM trainingsplan_versionen WHERE spieler_id=? ORDER BY id DESC",
            (spieler_id,),
        ).fetchall()
        cols = ["id","version_nr","datum","erstellt_von","status","modus",
                "trainingszeit_min","notizen","wochenplanung_json"]
        return [dict(zip(cols, r)) for r in rows]


def plan_laden_nach_version(version_id: int) -> list:
    """Lädt alle Übungen einer bestimmten Version (mit id für Bearbeitung)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id,bereich,uebung,saetze,wiederholungen,haeufigkeit,woche,"
            "COALESCE(tag,1) as tag,"
            "COALESCE(pause_sekunden,90) as pause_sekunden,"
            "COALESCE(ausfuehrung,'kontrolliert') as ausfuehrung,"
            "COALESCE(rpe,7) as rpe,"
            "COALESCE(energie_system,'Gemischt') as energie_system,"
            "COALESCE(equipment,'Körpergewicht') as equipment,"
            "COALESCE(begruendung,'') as begruendung,"
            "COALESCE(position,0) as position,"
            "COALESCE(notiz,'') as notiz,"
            "COALESCE(abgehakt,0) as abgehakt "
            "FROM trainingsplan WHERE plan_id=? ORDER BY woche,tag,COALESCE(position,0),id",
            (version_id,),
        ).fetchall()
        cols = ["id","bereich","uebung","saetze","wiederholungen","haeufigkeit","woche","tag",
                "pause_sekunden","ausfuehrung","rpe","energie_system","equipment","begruendung",
                "position","notiz","abgehakt"]
        return [dict(zip(cols, r)) for r in rows]


def plan_eintrag_loeschen(eintrag_id: int):
    """Löscht eine einzelne Übung aus dem Trainingsplan (Bibliotheksübung bleibt unberührt)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM trainingsplan WHERE id=?", (eintrag_id,))


def plan_eintrag_aktualisieren(eintrag_id: int, **felder):
    """Aktualisiert einzelne Felder einer Übung. Bibliotheksübungen bleiben unverändert."""
    _erlaubt = {"uebung","bereich","saetze","wiederholungen","haeufigkeit","pause_sekunden",
                "ausfuehrung","rpe","equipment","begruendung","notiz",
                "trainerhinweis","spielerhinweis","abgehakt","position","tag","woche"}
    updates = {k: v for k, v in felder.items() if k in _erlaubt}
    if not updates:
        return
    with get_conn() as conn:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE trainingsplan SET {set_clause} WHERE id=?",
                     list(updates.values()) + [eintrag_id])


def plan_eintraege_position_tauschen(id1: int, id2: int):
    """Tauscht die Reihenfolge zweier Übungen."""
    with get_conn() as conn:
        p1 = conn.execute("SELECT COALESCE(position,id) FROM trainingsplan WHERE id=?", (id1,)).fetchone()
        p2 = conn.execute("SELECT COALESCE(position,id) FROM trainingsplan WHERE id=?", (id2,)).fetchone()
        if p1 and p2:
            conn.execute("UPDATE trainingsplan SET position=? WHERE id=?", (p2[0], id1))
            conn.execute("UPDATE trainingsplan SET position=? WHERE id=?", (p1[0], id2))


def plan_notizen_speichern(version_id: int, notizen: str):
    """Speichert Trainer-Notizen zur Planversion."""
    with get_conn() as conn:
        conn.execute("UPDATE trainingsplan_versionen SET notizen=? WHERE id=?", (notizen, version_id))


def plan_trainingszeit_setzen(version_id: int, trainingszeit_min: int):
    """Aktualisiert die Trainingszeit einer Planversion."""
    with get_conn() as conn:
        conn.execute("UPDATE trainingsplan_versionen SET trainingszeit_min=? WHERE id=?",
                     (trainingszeit_min, version_id))


def plan_duplizieren(spieler_id: int, source_version_id: int, datum: str,
                     erstellt_von: str = "") -> int:
    """Dupliziert einen bestehenden Plan als neue AKTIV-Version (Original bleibt unverändert)."""
    src_rows = plan_laden_nach_version(source_version_id)
    with get_conn() as conn:
        r = conn.execute(
            "SELECT modus,schwerpunkt,trainingszeit_min FROM trainingsplan_versionen WHERE id=?",
            (source_version_id,),
        ).fetchone()
    src_meta = {"modus": r[0], "schwerpunkt": r[1], "trainingszeit_min": r[2]} if r else \
               {"modus": "Basis", "schwerpunkt": "", "trainingszeit_min": 60}
    plan_version_archivieren_aktiv(spieler_id)
    new_id = plan_version_erstellen(
        spieler_id, datum, erstellt_von,
        src_meta["modus"], src_meta["schwerpunkt"], src_meta["trainingszeit_min"],
    )
    with get_conn() as conn:
        for i, row in enumerate(src_rows):
            conn.execute(
                "INSERT INTO trainingsplan "
                "(spieler_id,datum,woche,bereich,uebung,saetze,wiederholungen,haeufigkeit,status,"
                "tag,pause_sekunden,ausfuehrung,rpe,energie_system,equipment,begruendung,plan_id,position,notiz) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (spieler_id, datum, row["woche"], row["bereich"], row["uebung"],
                 row["saetze"], row["wiederholungen"], row["haeufigkeit"], "offen",
                 row["tag"], row["pause_sekunden"], row["ausfuehrung"], row["rpe"],
                 row["energie_system"], row["equipment"], row["begruendung"],
                 new_id, i, row.get("notiz", "")),
            )
    return new_id


# ─── Periodisierung ────────────────────────────────────────────────────────

def periodisierung_loeschen(spieler_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM periodisierung WHERE spieler_id=?", (spieler_id,))


def periodisierung_bulk_insert(spieler_id, plan):
    rows = [
        (spieler_id, p["woche"], p["phase"], p["ziel"],
         p["bereich"], p["uebung"], p["intensitaet"], p["volumen"],
         p["haeufigkeit"], "offen")
        for p in plan
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO periodisierung (spieler_id,woche,phase,ziel,bereich,uebung,intensitaet,volumen,haeufigkeit,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )


def periodisierung_laden(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT woche,phase,ziel,bereich,uebung,intensitaet,volumen,haeufigkeit FROM periodisierung WHERE spieler_id=? ORDER BY woche",
            (spieler_id,),
        ).fetchall())


# ─── Kraftdiagnostik ───────────────────────────────────────────────────────────

def kraft_speichern(
    spieler_id: int, datum: str,
    koerpergewicht: float | None, direktes_1rm: float | None,
    geschaetztes_1rm: float | None, relative_kraft_direkt: float | None,
    relative_kraft_geschaetzt: float | None, sicherheit_bestaetigt: int,
    ventral_sekunden: float | None, ventral_versuch2: float | None,
    lateral_rechts_sekunden: float | None, lateral_links_sekunden: float | None,
    dorsal_sekunden: float | None, rumpf_gesamt_sekunden: float | None,
    lateral_differenz_sekunden: float | None, lateral_asymmetrie_prozent: float | None,
    ratio_ventral_dorsal: float | None, ratio_lateral_r_dorsal: float | None,
    ratio_lateral_l_dorsal: float | None,
    abbruchgrund: str | None = None, bemerkung: str | None = None,
) -> int:
    """Speichert oder überschreibt einen Kraft-Test (gleicher Spieler+Tag)."""
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM kraft_test WHERE spieler_id=? AND datum=?",
            (spieler_id, datum),
        ).fetchone()
        params = (
            koerpergewicht, direktes_1rm, geschaetztes_1rm,
            relative_kraft_direkt, relative_kraft_geschaetzt, sicherheit_bestaetigt,
            ventral_sekunden, ventral_versuch2,
            lateral_rechts_sekunden, lateral_links_sekunden,
            dorsal_sekunden, rumpf_gesamt_sekunden,
            lateral_differenz_sekunden, lateral_asymmetrie_prozent,
            ratio_ventral_dorsal, ratio_lateral_r_dorsal, ratio_lateral_l_dorsal,
            abbruchgrund, bemerkung,
        )
        if existing:
            kraft_id = existing[0]
            conn.execute("""
                UPDATE kraft_test SET
                    koerpergewicht=?,direktes_1rm=?,geschaetztes_1rm=?,
                    relative_kraft_direkt=?,relative_kraft_geschaetzt=?,
                    sicherheit_bestaetigt=?,ventral_sekunden=?,ventral_versuch2=?,
                    lateral_rechts_sekunden=?,lateral_links_sekunden=?,
                    dorsal_sekunden=?,rumpf_gesamt_sekunden=?,
                    lateral_differenz_sekunden=?,lateral_asymmetrie_prozent=?,
                    ratio_ventral_dorsal=?,ratio_lateral_r_dorsal=?,ratio_lateral_l_dorsal=?,
                    abbruchgrund=?,bemerkung=?,updated_at=datetime('now')
                WHERE id=?
            """, params + (kraft_id,))
            return kraft_id
        cursor = conn.execute("""
            INSERT INTO kraft_test (
                spieler_id,datum,
                koerpergewicht,direktes_1rm,geschaetztes_1rm,
                relative_kraft_direkt,relative_kraft_geschaetzt,sicherheit_bestaetigt,
                ventral_sekunden,ventral_versuch2,
                lateral_rechts_sekunden,lateral_links_sekunden,
                dorsal_sekunden,rumpf_gesamt_sekunden,
                lateral_differenz_sekunden,lateral_asymmetrie_prozent,
                ratio_ventral_dorsal,ratio_lateral_r_dorsal,ratio_lateral_l_dorsal,
                abbruchgrund,bemerkung
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum) + params)
        return cursor.lastrowid


def kraft_letzter(spieler_id: int) -> dict | None:
    """Letzter Kraft-Test des Spielers."""
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM kraft_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def kraft_history(spieler_id: int) -> list[dict]:
    """Alle Kraft-Tests des Spielers, aufsteigend nach Datum."""
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT datum,direktes_1rm,geschaetztes_1rm,
                   relative_kraft_direkt,relative_kraft_geschaetzt,
                   ventral_sekunden,lateral_rechts_sekunden,
                   lateral_links_sekunden,dorsal_sekunden,
                   lateral_asymmetrie_prozent,ratio_ventral_dorsal
            FROM kraft_test WHERE spieler_id=? ORDER BY datum
        """, (spieler_id,)).fetchall())


def kraft_versuch_speichern(
    kraft_test_id: int, uebung: str, versuchsnummer: int,
    gewicht: float | None = None, wiederholungen: int | None = None,
    zeit_sekunden: float | None = None, gueltig: bool = True,
    ungueltigkeitsgrund: str | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO kraft_test_versuch
            (kraft_test_id,uebung,versuchsnummer,gewicht,wiederholungen,
             zeit_sekunden,gueltig,ungueltigkeitsgrund)
            VALUES (?,?,?,?,?,?,?,?)
        """, (kraft_test_id, uebung, versuchsnummer, gewicht, wiederholungen,
              zeit_sekunden, 1 if gueltig else 0, ungueltigkeitsgrund))


def kraft_versuche_laden(kraft_test_id: int) -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM kraft_test_versuch WHERE kraft_test_id=? ORDER BY uebung,versuchsnummer",
            (kraft_test_id,),
        ).fetchall())


# --------------------------------------------------------------------------
# Multi-Tenant: Migration bestehender Datenbanken
# --------------------------------------------------------------------------

def _migrate_multitenant():
    """Legt vereine/benutzer-Tabellen und spieler-Spalten an, falls noch nicht vorhanden.
    Idempotent — kann beliebig oft aufgerufen werden."""
    with get_conn() as conn:
        # vereine-Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vereine (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                aktiv       INTEGER DEFAULT 1,
                erstellt_am TEXT    DEFAULT (date('now'))
            )
        """)
        # benutzer-Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS benutzer (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                verein_id     INTEGER REFERENCES vereine(id),
                vorname       TEXT,
                nachname      TEXT,
                email         TEXT UNIQUE NOT NULL,
                passwort_hash TEXT NOT NULL,
                rolle         TEXT NOT NULL DEFAULT 'Trainer',
                aktiv         INTEGER DEFAULT 1,
                erstellt_am   TEXT    DEFAULT (date('now'))
            )
        """)
        # spieler: neue Fremdschlüssel-Spalten
        for col in [("trainer_id", "INTEGER"), ("verein_id", "INTEGER")]:
            try:
                conn.execute(f"ALTER TABLE spieler ADD COLUMN {col[0]} {col[1]}")
            except Exception:
                pass
        # vereine: SaaS-Erweiterungsfelder
        neue_verein_cols = [
            ("logo_blob",       "BLOB"),
            ("farbe_primaer",   "TEXT"),
            ("farbe_sekundaer", "TEXT"),
            ("ansprechpartner", "TEXT"),
            ("email",           "TEXT"),
            ("telefon",         "TEXT"),
            ("adresse",         "TEXT"),
            ("homepage",        "TEXT"),
            ("lizenztyp",       "TEXT"),
            ("lizenz_bis",      "TEXT"),
            ("max_trainer",     "INTEGER"),
            ("max_spieler",     "INTEGER"),
            # ── Lizenzsystem (v2) ──────────────────────────────────────────
            ("testphase_bis",          "TEXT"),
            ("lizenz_status",          "TEXT DEFAULT 'trial'"),
            ("gesperrt",               "INTEGER DEFAULT 0"),
            ("stripe_customer_id",     "TEXT"),
            ("stripe_subscription_id", "TEXT"),
            ("zahlungsstatus",         "TEXT DEFAULT 'offen'"),
            ("registrier_code",        "TEXT"),
            # ── Technischer Mandant (persönlicher Verein für Einzeltrainer) ──
            # 1 = automatisch durch trainer_registrieren() angelegt;
            # wird in Kundenliste / Sidebar NICHT als echter Verein behandelt.
            ("ist_technischer_mandant", "INTEGER DEFAULT 0"),
            # ── Phase A2: Abrechnungsintervall ─────────────────────────────
            ("abo_intervall",           "TEXT"),   # 'monat' | 'jahr'
            # ── Phase A7: Zahlungs-Fehlschlag-Zeitstempel ──────────────────
            ("letzte_zahlung_fehlgeschlagen", "TEXT"),  # ISO-Datetime des letzten Fehlschlags
        ]
        for col, typ in neue_verein_cols:
            try:
                conn.execute(f"ALTER TABLE vereine ADD COLUMN {col} {typ}")
            except Exception:
                pass
        # Bestehenden Vereinen ohne Code einen generieren
        import secrets as _secrets
        vereine_ohne_code = conn.execute(
            "SELECT id FROM vereine WHERE registrier_code IS NULL"
        ).fetchall()
        for (_vid,) in vereine_ohne_code:
            _code = _secrets.token_urlsafe(6).upper()
            conn.execute(
                "UPDATE vereine SET registrier_code=? WHERE id=?", (_code, _vid)
            )
        # benutzer: Trainerportal-Felder
        neue_benutzer_cols = [
            ("foto_blob",       "BLOB"),
            ("telefon",         "TEXT"),
            ("lizenz",          "TEXT"),
            ("letzter_login",   "TEXT"),
            # ── Brute-Force-Schutz ─────────────────────────────────────────
            ("login_versuche",  "INTEGER DEFAULT 0"),
            ("gesperrt_bis",    "TEXT"),
        ]
        for col, typ in neue_benutzer_cols:
            try:
                conn.execute(f"ALTER TABLE benutzer ADD COLUMN {col} {typ}")
            except Exception:
                pass
        # ── Auth-Erweiterungsfelder (E-Mail-Verifikation, Passwort-Reset, Benutzername) ──
        neue_benutzer_auth_cols = [
            ("benutzername",            "TEXT"),
            ("email_verifiziert",       "INTEGER DEFAULT 0"),
            ("email_token",             "TEXT"),
            ("email_token_ablauf",      "TEXT"),
            ("email_token_gesendet_am", "TEXT"),
            ("pw_reset_token",          "TEXT"),
            ("pw_reset_ablauf",         "TEXT"),
        ]
        for col, typ in neue_benutzer_auth_cols:
            try:
                conn.execute(f"ALTER TABLE benutzer ADD COLUMN {col} {typ}")
            except Exception:
                pass
        # ── Lizenz/Vertragsspalten für standalone Trainer auf benutzer-Ebene ──
        neue_benutzer_lizenz_cols = [
            ("lizenztyp",              "TEXT DEFAULT 'BASIC'"),
            ("lizenz_status",          "TEXT DEFAULT 'trial'"),
            ("lizenz_bis",             "TEXT"),
            ("testphase_bis",          "TEXT"),
            ("vertragsbeginn",         "TEXT"),
            ("vertragsende",           "TEXT"),
            ("kuendigung_eingegangen", "TEXT"),
            ("gekuendigt_zum",         "TEXT"),
            ("kuendigungsstatus",      "TEXT DEFAULT 'aktiv'"),
        ]
        for col, typ in neue_benutzer_lizenz_cols:
            try:
                conn.execute(f"ALTER TABLE benutzer ADD COLUMN {col} {typ}")
            except Exception:
                pass
        # ── SCHRITT 5: Kündigungsgrund + Bestätigungsdatum ──────────────────
        for _tbl in ("benutzer", "vereine"):
            for _col, _typ in [("kuendigung_grund", "TEXT"),
                                ("kuendigung_bestaetigung_am", "TEXT")]:
                try:
                    conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN {_col} {_typ}")
                except Exception:
                    pass
        # Bestehende Benutzer sofort als verifiziert markieren — verhindert Lockout
        conn.execute(
            # Nur Altdaten ohne ausstehenden Verifizierungstoken (email_token IS NULL)
            # NIEMALS neu registrierte Benutzer mit laufendem Token überschreiben!
            "UPDATE benutzer SET email_verifiziert=1 "
            "WHERE (email_verifiziert IS NULL OR email_verifiziert=0) "
            "AND (email_token IS NULL OR email_token = '')"
        )
        # ── Session-Token-Version (Session-Invalidierung nach Passwortänderung) ──
        try:
            conn.execute(
                "ALTER TABLE benutzer ADD COLUMN session_token_version INTEGER NOT NULL DEFAULT 0"
            )
        except Exception:
            pass  # Spalte existiert bereits
        # Sessions-Tabelle (server-seitige Session-Persistenz)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token             TEXT    PRIMARY KEY,
                benutzer_id       INTEGER NOT NULL,
                erstellt_am       TEXT    NOT NULL,
                letzte_aktivitaet TEXT    NOT NULL,
                ablauf_am         TEXT    NOT NULL,
                aktiv             INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id)
            )
        """)
        try:
            conn.execute(
                "ALTER TABLE sessions ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"
            )
        except Exception:
            pass  # Spalte existiert bereits
        # ── DSGVO-Zustimmungsfelder (Datenschutz + AGB bei Registrierung) ──────
        zustimmung_cols = [
            ("datenschutz_akzeptiert",    "INTEGER DEFAULT 0"),
            ("datenschutz_akzeptiert_am", "TEXT"),
            ("datenschutz_version",       "TEXT"),
            ("agb_akzeptiert",            "INTEGER DEFAULT 0"),
            ("agb_akzeptiert_am",         "TEXT"),
            ("agb_version",               "TEXT"),
        ]
        for col, typ in zustimmung_cols:
            try:
                conn.execute(f"ALTER TABLE benutzer ADD COLUMN {col} {typ}")
            except Exception:
                pass  # Spalte existiert bereits
        # Rechnungsadressen-Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rechnungsadressen (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id    INTEGER NOT NULL UNIQUE,
                firma          TEXT,
                vorname        TEXT    NOT NULL DEFAULT '',
                nachname       TEXT    NOT NULL DEFAULT '',
                strasse        TEXT    NOT NULL DEFAULT '',
                hausnummer     TEXT    NOT NULL DEFAULT '',
                plz            TEXT    NOT NULL DEFAULT '',
                ort            TEXT    NOT NULL DEFAULT '',
                land           TEXT    NOT NULL DEFAULT 'Deutschland',
                rechnung_email TEXT    NOT NULL DEFAULT '',
                telefon        TEXT,
                ust_id         TEXT,
                erstellt_am    TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id)
            )
        """)

        # ── Kundennummern, Vertragsdaten, Audit-Log ──────────────────────────
        neue_verein_vertrag_cols = [
            ("kundennummer",            "TEXT"),
            ("vertragsbeginn",          "TEXT"),
            ("vertragsende",            "TEXT"),
            ("kuendigung_eingegangen",  "TEXT"),
            ("gekuendigt_zum",          "TEXT"),
            ("kuendigungsstatus",       "TEXT"),
            ("cancel_at_period_end",    "INTEGER DEFAULT 0"),
        ]
        for col, typ in neue_verein_vertrag_cols:
            try:
                conn.execute(f"ALTER TABLE vereine ADD COLUMN {col} {typ}")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE benutzer ADD COLUMN kundennummer TEXT")
        except Exception:
            pass
        # ── B2: UNIQUE-Indexes für Kundennummern (idempotent, NULL-sicher) ───
        # SQLite: partial index WHERE IS NOT NULL erlaubt mehrere NULL-Werte.
        # Führende Vertragsquelle: vereine (nicht benutzer).
        # benutzer.kundennummer gilt nur für standalone-Einzeltrainer ohne Verein.
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_vereine_kundennummer "
                "ON vereine(kundennummer) WHERE kundennummer IS NOT NULL"
            )
        except Exception:
            pass  # Besteht bereits oder Duplikate → keine Datenverlust-Migration
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_benutzer_kundennummer "
                "ON benutzer(kundennummer) WHERE kundennummer IS NOT NULL"
            )
        except Exception:
            pass  # Besteht bereits oder Duplikate → keine Datenverlust-Migration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id    INTEGER,
                aktion         TEXT    NOT NULL,
                details        TEXT,
                superadmin_id  INTEGER,
                erstellt_am    TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (benutzer_id)   REFERENCES benutzer(id),
                FOREIGN KEY (superadmin_id) REFERENCES benutzer(id)
            )
        """)
        # Kundennummern für bestehende Vereine vergeben (einmalig)
        for (vid,) in conn.execute(
            "SELECT id FROM vereine WHERE kundennummer IS NULL ORDER BY id"
        ).fetchall():
            _max_v = conn.execute(
                "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
                "FROM vereine WHERE kundennummer IS NOT NULL"
            ).fetchone()[0] or 0
            _max_b = conn.execute(
                "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
                "FROM benutzer WHERE kundennummer IS NOT NULL"
            ).fetchone()[0] or 0
            conn.execute(
                "UPDATE vereine SET kundennummer=? WHERE id=?",
                (f"APH-{max(_max_v, _max_b)+1:06d}", vid),
            )
        # Kundennummern für standalone Trainer (verein_id IS NULL ODER technischer Mandant, kein Superadmin)
        for (bid,) in conn.execute(
            "SELECT b.id FROM benutzer b "
            "LEFT JOIN vereine v ON v.id = b.verein_id "
            "WHERE b.kundennummer IS NULL AND b.rolle != 'Superadmin' "
            "AND (b.verein_id IS NULL OR COALESCE(v.ist_technischer_mandant,0)=1) "
            "ORDER BY b.id"
        ).fetchall():
            _max_v = conn.execute(
                "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
                "FROM vereine WHERE kundennummer IS NOT NULL"
            ).fetchone()[0] or 0
            _max_b = conn.execute(
                "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
                "FROM benutzer WHERE kundennummer IS NOT NULL"
            ).fetchone()[0] or 0
            conn.execute(
                "UPDATE benutzer SET kundennummer=? WHERE id=?",
                (f"APH-{max(_max_v, _max_b)+1:06d}", bid),
            )

        # ── Rechnungen-Tabelle ─────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rechnungen (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                verein_id        INTEGER NOT NULL,
                rechnungsnummer  TEXT    NOT NULL,
                rechnungsdatum   TEXT    NOT NULL DEFAULT (date('now')),
                betrag_eur       REAL    NOT NULL DEFAULT 0,
                lizenz_typ       TEXT,
                status           TEXT    NOT NULL DEFAULT 'offen',
                lizenz_von       TEXT,
                lizenz_bis_r     TEXT,
                stripe_invoice_id TEXT,
                erstellt_am      TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (verein_id) REFERENCES vereine(id)
            )
        """)

        # ── Testphase für bestehende Vereine initialisieren ────────────────
        # Vereine ohne testphase_bis bekommen heute + 14 Tage gesetzt
        conn.execute("""
            UPDATE vereine
               SET testphase_bis = date('now', '+30 days'),
                   lizenz_status = COALESCE(lizenz_status, 'trial')
             WHERE testphase_bis IS NULL
        """)

    # Auto-Zuweisung: Falls bereits ein Verein existiert und ein Superadmin,
    # der zu genau diesem Verein gehört, NULL-Spieler sofort zuweisen
    # (Upgrade-Szenario). Nur wenn Verein und Admin zusammengehören, um
    # Cross-Tenant-Zuweisung zu vermeiden. Nur vollständig fehlende Datensätze
    # (beide IDs NULL) werden atomar gesetzt.
    try:
        with get_conn() as conn:
            row = conn.execute(
                """SELECT b.id AS admin_id, b.verein_id
                     FROM benutzer b
                     JOIN vereine  v ON v.id = b.verein_id
                    WHERE b.rolle = 'Superadmin'
                    LIMIT 1"""
            ).fetchone()
            if row:
                _aid, _vid = row[0], row[1]
                conn.execute(
                    """UPDATE spieler
                          SET verein_id  = ?,
                              trainer_id = ?
                        WHERE verein_id IS NULL
                          AND trainer_id IS NULL""",
                    (_vid, _aid),
                )
    except Exception:
        pass

    # ── Reparatur-Migration: Trainer ohne Vereinszuordnung (verein_id=NULL) ──
    # Betrifft selbstregistrierte Trainer, die vor diesem Fix angelegt wurden.
    # Erstellt für jeden betroffenen Trainer einen persönlichen Verein und setzt
    # verein_id, damit alle verein_id-abhängigen Abfragen korrekt funktionieren.
    try:
        import datetime as _dt2
        import secrets as _sec2
        with get_conn() as _rc:
            _trainers_ohne_verein = _rc.execute(
                "SELECT id, vorname, nachname FROM benutzer "
                "WHERE rolle='Trainer' AND verein_id IS NULL ORDER BY id"
            ).fetchall()
        for (_tid, _tvn, _tnn) in _trainers_ohne_verein:
            _vname2 = f"Trainer: {_tvn or ''} {_tnn or ''}".strip()
            _testphase2 = (_dt2.date.today() + _dt2.timedelta(days=30)).isoformat()
            _code2 = _sec2.token_urlsafe(6).upper()
            with get_conn() as _rc2:
                _vcur2 = _rc2.execute(
                    """INSERT INTO vereine
                           (name, aktiv, lizenz_status, lizenztyp,
                            testphase_bis, registrier_code,
                            ist_technischer_mandant)
                       VALUES (?, 1, 'trial', 'BASIC', ?, ?, 1)""",
                    (_vname2, _testphase2, _code2),
                )
                _new_vid2 = _vcur2.lastrowid
                _rc2.execute(
                    "UPDATE benutzer SET verein_id=? WHERE id=?",
                    (_new_vid2, _tid),
                )
            # Kundennummer für neuen Verein vergeben
            try:
                kundennummer_vergeben_verein(_new_vid2)
            except Exception:
                pass
    except Exception:
        pass


# --------------------------------------------------------------------------
# Multi-Tenant Hilfsfunktionen
# --------------------------------------------------------------------------

def spieler_null_zuweisen(verein_id: int, trainer_id: int) -> int:
    """Weist alle Spieler, bei denen BEIDE IDs fehlen (verein_id IS NULL UND
    trainer_id IS NULL), atomar dem angegebenen Verein und Trainer zu.

    Validiert serverseitig, dass trainer_id zum verein_id gehört, um
    Cross-Tenant-Zuweisung zu verhindern.

    Gibt die Anzahl der aktualisierten Datensätze zurück.
    Wirft ValueError, wenn Trainer und Verein nicht übereinstimmen.
    """
    with get_conn() as conn:
        # Serverseitige Validierung: Trainer muss zum Verein gehören
        row = conn.execute(
            "SELECT id FROM benutzer WHERE id=? AND verein_id=?",
            (trainer_id, verein_id),
        ).fetchone()
        if not row:
            raise ValueError(
                f"Trainer {trainer_id} gehört nicht zu Verein {verein_id}. "
                "Zuweisung abgebrochen."
            )
        # Nur vollständig unzugeordnete Spieler (beide IDs NULL) atomar setzen
        cur = conn.execute(
            """UPDATE spieler
                  SET verein_id  = ?,
                      trainer_id = ?
                WHERE verein_id IS NULL
                  AND trainer_id IS NULL""",
            (verein_id, trainer_id),
        )
        return cur.rowcount


def spieler_ohne_verein_zaehlen() -> int:
    """Anzahl der Spieler, die noch keinem Verein zugeordnet sind (beide IDs NULL)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE verein_id IS NULL AND trainer_id IS NULL"
        ).fetchone()
        return row[0] if row else 0


# --------------------------------------------------------------------------
# Vereine
# --------------------------------------------------------------------------

def vereine_laden(nur_echte: bool = True) -> list[dict]:
    """Gibt alle Vereine zurück.

    nur_echte=True (Standard): Filtert technische Mandanten heraus
    (ist_technischer_mandant=1), die automatisch für selbstregistrierte
    Einzeltrainer angelegt werden. Diese sollen in der UI nicht als
    echte Vereine erscheinen.
    nur_echte=False: Gibt wirklich alle Vereine zurück (interne Nutzung).
    """
    with get_conn() as conn:
        if nur_echte:
            return _rows(conn.execute(
                "SELECT * FROM vereine "
                "WHERE COALESCE(ist_technischer_mandant, 0) = 0 "
                "ORDER BY name"
            ).fetchall())
        return _rows(conn.execute(
            "SELECT * FROM vereine ORDER BY name"
        ).fetchall())


def verein_speichern(name: str) -> int:
    import datetime as _dt
    testphase_bis = (
        _dt.date.today() + _dt.timedelta(days=30)
    ).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO vereine (name, aktiv, lizenz_status, lizenztyp, testphase_bis)
               VALUES (?, 1, 'trial', 'BASIC', ?)""",
            (name, testphase_bis),
        )
        return cur.lastrowid


# ── Selbstregistrierung ────────────────────────────────────────────────────────

_ERLAUBTE_VEREIN_PAKETE  = frozenset({"VEREIN_BASIC", "VEREIN_PRO"})
_ERLAUBTE_TRAINER_PAKETE = frozenset({"TRAINER_BASIC", "TRAINER_PRO"})
_ERLAUBTE_INTERVALLE     = frozenset({"monat", "jahr"})


def verein_registrieren(
    vereinsname: str,
    vorname: str,
    nachname: str,
    email: str,
    passwort: str,
    *,
    benutzername: str | None = None,
    lizenztyp: str = "VEREIN_BASIC",
    abo_intervall: str = "monat",
) -> tuple[int, int]:
    """Erstellt einen neuen Verein mit Vereinsadmin und startet 30-Tage-Testphase.
    Gibt (verein_id, benutzer_id) zurück.
    Setzt email_verifiziert=0 — Bestätigungs-E-Mail wird separat gesendet.

    lizenztyp muss VEREIN_BASIC oder VEREIN_PRO sein.
    abo_intervall muss 'monat' oder 'jahr' sein.
    """
    import datetime as _dt
    email_norm = normalize_email(email)
    testphase_bis = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()

    # Serverseitige Validierung: nur Vereinspakete erlaubt
    if lizenztyp not in _ERLAUBTE_VEREIN_PAKETE:
        raise ValueError(
            f"Ungültiges Paket für Verein: {lizenztyp!r}. "
            f"Erlaubt: {sorted(_ERLAUBTE_VEREIN_PAKETE)}"
        )
    if abo_intervall not in _ERLAUBTE_INTERVALLE:
        raise ValueError(
            f"Ungültiges Abrechnungsintervall: {abo_intervall!r}. "
            f"Erlaubt: {sorted(_ERLAUBTE_INTERVALLE)}"
        )

    # Eindeutigkeit prüfen
    with get_conn() as conn:
        if conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(email)=?", (email_norm,)
        ).fetchone():
            raise ValueError("Diese E-Mail-Adresse ist bereits registriert.")
        if benutzername and conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(benutzername)=LOWER(?)", (benutzername,)
        ).fetchone():
            raise ValueError(f"Der Benutzername '{benutzername}' ist bereits vergeben.")

    verein_id = verein_speichern(vereinsname)
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET testphase_bis=?, lizenz_status='trial', "
            "lizenztyp=?, abo_intervall=? WHERE id=?",
            (testphase_bis, lizenztyp, abo_intervall, verein_id),
        )

    benutzer_id = benutzer_speichern(
        verein_id, vorname, nachname, email_norm, passwort, "Vereinsadmin",
        benutzername=benutzername, email_verifiziert=0,
    )
    kundennummer_vergeben_verein(verein_id)
    return verein_id, benutzer_id


def verein_by_id(verein_id: int) -> dict | None:
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM vereine WHERE id=?", (verein_id,)
        ).fetchone())


def verein_aktivieren(verein_id: int, aktiv: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET aktiv=? WHERE id=?", (aktiv, verein_id)
        )


def verein_aktualisieren(
    verein_id: int, *,
    name: str,
    ansprechpartner: str | None = None,
    email: str | None = None,
    telefon: str | None = None,
    adresse: str | None = None,
    homepage: str | None = None,
    farbe_primaer: str | None = None,
    farbe_sekundaer: str | None = None,
    lizenztyp: str | None = None,
    lizenz_bis: str | None = None,
    max_trainer: int | None = None,
    max_spieler: int | None = None,
    aktiv: int = 1,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            UPDATE vereine SET
                name=?, ansprechpartner=?, email=?, telefon=?,
                adresse=?, homepage=?, farbe_primaer=?, farbe_sekundaer=?,
                lizenztyp=?, lizenz_bis=?, max_trainer=?, max_spieler=?, aktiv=?
            WHERE id=?
        """, (name, ansprechpartner, email, telefon,
              adresse, homepage, farbe_primaer, farbe_sekundaer,
              lizenztyp, lizenz_bis, max_trainer, max_spieler, aktiv,
              verein_id))


def verein_loeschen(verein_id: int) -> tuple[bool, str]:
    """Löscht einen Verein — nur wenn keine Spieler oder Benutzer mehr zugeordnet sind.
    Gibt (True, "") bei Erfolg zurück, sonst (False, Fehlermeldung)."""
    with get_conn() as conn:
        spieler_n = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (verein_id,)
        ).fetchone()[0]
        benutzer_n = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE verein_id=?", (verein_id,)
        ).fetchone()[0]
        if spieler_n > 0:
            return False, f"Verein hat noch {spieler_n} Spieler. Bitte zuerst alle Spieler entfernen oder einem anderen Verein zuweisen."
        if benutzer_n > 0:
            return False, f"Verein hat noch {benutzer_n} Benutzer. Bitte zuerst alle Benutzer entfernen oder verschieben."
        conn.execute("DELETE FROM vereine WHERE id=?", (verein_id,))
        return True, ""


# ── Lizenzsystem — DB-Funktionen ──────────────────────────────────────────────

def lizenz_info_laden(verein_id: int) -> dict | None:
    """Lädt alle Lizenzdaten eines Vereins (für get_lizenz_info()).

    Enthält ist_technischer_mandant damit normalize_lizenz_typ() den richtigen
    Kundentyp-Ast (Einzeltrainer vs. Verein) wählen kann.
    """
    with get_conn() as conn:
        return _row(conn.execute(
            """SELECT id, name, aktiv, lizenztyp, lizenz_bis, lizenz_status,
                      testphase_bis, gesperrt, stripe_customer_id,
                      stripe_subscription_id, zahlungsstatus,
                      ist_technischer_mandant, abo_intervall,
                      cancel_at_period_end, gekuendigt_zum
                 FROM vereine WHERE id=?""",
            (verein_id,),
        ).fetchone())


def lizenz_setzen(
    verein_id: int,
    lizenz_typ: str,
    lizenz_status: str,
    lizenz_bis: str | None = None,
    testphase_bis: str | None = None,
) -> None:
    """Setzt Lizenztyp, Status und Ablaufdaten für einen Verein."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE vereine
                  SET lizenztyp=?,
                      lizenz_status=?,
                      lizenz_bis=COALESCE(?, lizenz_bis),
                      testphase_bis=COALESCE(?, testphase_bis)
                WHERE id=?""",
            (lizenz_typ, lizenz_status, lizenz_bis, testphase_bis, verein_id),
        )


def trainer_lizenz_setzen(
    benutzer_id: int,
    lizenz_typ: str,
    lizenz_status: str,
    lizenz_bis: str | None = None,
    testphase_bis: str | None = None,
) -> None:
    """Setzt Lizenztyp, Status und Ablaufdaten für einen Trainer-Kunden (standalone, verein_id IS NULL)."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE benutzer
                  SET lizenztyp=?,
                      lizenz_status=?,
                      lizenz_bis=COALESCE(?, lizenz_bis),
                      testphase_bis=COALESCE(?, testphase_bis)
                WHERE id=?""",
            (lizenz_typ, lizenz_status, lizenz_bis, testphase_bis, benutzer_id),
        )


def trainer_vertrag_setzen(
    benutzer_id: int,
    *,
    vertragsbeginn: str | None = None,
    vertragsende: str | None = None,
    kuendigung_eingegangen: str | None = None,
    gekuendigt_zum: str | None = None,
    kuendigungsstatus: str | None = None,
    superadmin_id: int | None = None,
) -> None:
    """Setzt Vertragsdaten für einen Trainer-Kunden (standalone). Loggt Änderung."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE benutzer SET
                   vertragsbeginn         = COALESCE(?, vertragsbeginn),
                   vertragsende           = COALESCE(?, vertragsende),
                   kuendigung_eingegangen = COALESCE(?, kuendigung_eingegangen),
                   gekuendigt_zum         = COALESCE(?, gekuendigt_zum),
                   kuendigungsstatus      = COALESCE(?, kuendigungsstatus)
               WHERE id=?""",
            (vertragsbeginn, vertragsende, kuendigung_eingegangen,
             gekuendigt_zum, kuendigungsstatus, benutzer_id),
        )
    audit_log_eintragen(
        benutzer_id, "vertragsdaten_geaendert",
        f"benutzer_id={benutzer_id} status={kuendigungsstatus}",
        superadmin_id,
    )


def verein_sperren(verein_id: int, gesperrt: bool) -> None:
    """Sperrt oder entsperrt einen Verein (Superadmin)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET gesperrt=? WHERE id=?",
            (1 if gesperrt else 0, verein_id),
        )


def testphase_verlaengern(verein_id: int, tage: int) -> None:
    """Verlängert die Testphase um N Tage ab heute oder dem aktuellen Ablauf."""
    import datetime as _dt
    with get_conn() as conn:
        row = conn.execute(
            "SELECT testphase_bis FROM vereine WHERE id=?", (verein_id,)
        ).fetchone()
        if row and row[0]:
            try:
                basis = _dt.date.fromisoformat(str(row[0])[:10])
                neu = max(basis, _dt.date.today()) + _dt.timedelta(days=tage)
            except ValueError:
                neu = _dt.date.today() + _dt.timedelta(days=tage)
        else:
            neu = _dt.date.today() + _dt.timedelta(days=tage)
        conn.execute(
            "UPDATE vereine SET testphase_bis=?, lizenz_status='trial' WHERE id=?",
            (neu.isoformat(), verein_id),
        )


def stripe_ids_setzen(
    verein_id: int,
    customer_id: str | None = None,
    subscription_id: str | None = None,
) -> None:
    """Speichert Stripe-IDs nach erfolgreicher Checkout-Session."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE vereine
                  SET stripe_customer_id=COALESCE(?, stripe_customer_id),
                      stripe_subscription_id=COALESCE(?, stripe_subscription_id)
                WHERE id=?""",
            (customer_id, subscription_id, verein_id),
        )


def verein_kapazitaet_laden(verein_id: int) -> dict:
    """Gibt aktuelle Spieler- und Trainer-Anzahl eines Vereins zurück.

    Wird vor Downgrades aufgerufen um zu prüfen, ob das Limit des Zielpakets
    mit den bestehenden Datensätzen vereinbar ist.

    Rückgabe:
        {"spieler": int, "trainer": int}
    """
    with get_conn() as conn:
        spieler = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE verein_id=? AND aktiv=1",
            (verein_id,),
        ).fetchone()[0]
        trainer = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1 AND rolle='Trainer'",
            (verein_id,),
        ).fetchone()[0]
    return {"spieler": spieler, "trainer": trainer}


def zahlungsstatus_setzen(verein_id: int, status: str) -> None:
    """Setzt den Zahlungsstatus: offen | bezahlt | fehlgeschlagen | storniert."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET zahlungsstatus=? WHERE id=?",
            (status, verein_id),
        )


def rechnung_speichern(
    verein_id: int,
    rechnungsnummer: str,
    betrag_eur: float,
    lizenz_typ: str,
    status: str = "bezahlt",
    lizenz_von: str | None = None,
    lizenz_bis_r: str | None = None,
    stripe_invoice_id: str | None = None,
) -> int:
    """Speichert eine Rechnung und gibt die ID zurück."""
    import datetime as _dt
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO rechnungen
               (verein_id, rechnungsnummer, rechnungsdatum, betrag_eur,
                lizenz_typ, status, lizenz_von, lizenz_bis_r, stripe_invoice_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (verein_id, rechnungsnummer, _dt.date.today().isoformat(),
             betrag_eur, lizenz_typ, status, lizenz_von, lizenz_bis_r,
             stripe_invoice_id),
        )
        return cur.lastrowid


def rechnungen_laden(verein_id: int) -> list[dict]:
    """Lädt alle Rechnungen eines Vereins (neueste zuerst)."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT rechnungsnummer, rechnungsdatum, betrag_eur,
                      lizenz_typ, status, lizenz_von, lizenz_bis_r
                 FROM rechnungen
                WHERE verein_id=?
                ORDER BY rechnungsdatum DESC, id DESC""",
            (verein_id,),
        ).fetchall())


def alle_vereine_lizenz() -> list[dict]:
    """Alle Vereine mit Lizenzdaten für den Superadmin-Überblick."""
    with get_conn() as conn:
        return _rows(conn.execute(
            """SELECT id, name, aktiv, lizenztyp, lizenz_bis, lizenz_status,
                      testphase_bis, gesperrt, stripe_customer_id,
                      stripe_subscription_id, zahlungsstatus,
                      cancel_at_period_end, kuendigungsstatus, gekuendigt_zum,
                      kuendigung_eingegangen, letzte_zahlung_fehlgeschlagen
                 FROM vereine
                ORDER BY erstellt_am DESC""",
        ).fetchall())


def verein_logo_speichern(verein_id: int, logo_bytes: bytes | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET logo_blob=? WHERE id=?",
            (logo_bytes, verein_id)
        )


def verein_statistiken(verein_id: int) -> dict:
    """Zählt Trainer, Spieler und Diagnostiken für einen Verein."""
    _DIAG_TABLES = [
        "sprint_test", "sprung_test", "anthropometrie", "fms_ergebnis",
        "y_balance_ergebnis", "ausdauer_test", "kraft_test",
        "agilitaet_test", "spiro_test",
    ]
    with get_conn() as conn:
        trainer_n = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1",
            (verein_id,),
        ).fetchone()[0]
        spieler_n = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE verein_id=?",
            (verein_id,),
        ).fetchone()[0]
        diag_n = 0
        for tbl in _DIAG_TABLES:
            try:
                diag_n += conn.execute(
                    f"SELECT COUNT(*) FROM {tbl} "
                    f"WHERE spieler_id IN (SELECT id FROM spieler WHERE verein_id=?)",
                    (verein_id,),
                ).fetchone()[0]
            except Exception:
                pass
        return {"trainer": trainer_n, "spieler": spieler_n, "diagnostiken": diag_n}


# --------------------------------------------------------------------------
# Benutzer
# --------------------------------------------------------------------------

import hashlib as _hashlib
import hmac as _hmac
import secrets as _secrets


def _pw_hash(passwort: str) -> str:
    """PBKDF2-SHA256 mit zufälligem Salt (260.000 Iterationen).
    Format: pbkdf2:<salt_hex>:<hash_hex>
    Ersetzt das frühere unsalted SHA-256."""
    salt = _secrets.token_hex(16)
    h = _hashlib.pbkdf2_hmac(
        "sha256", passwort.encode("utf-8"), salt.encode("utf-8"), 260_000
    )
    return f"pbkdf2:{salt}:{h.hex()}"


def _pw_verify(passwort: str, stored_hash: str) -> bool:
    """Prüft Passwort gegen gespeicherten Hash.
    Unterstützt altes SHA-256 (ohne Salt) für nahtlose Migration."""
    if stored_hash.startswith("pbkdf2:"):
        try:
            _, salt, h = stored_hash.split(":", 2)
            h_new = _hashlib.pbkdf2_hmac(
                "sha256", passwort.encode("utf-8"), salt.encode("utf-8"), 260_000
            )
            return _hmac.compare_digest(h_new.hex(), h)
        except Exception:
            return False
    else:
        # Legacy: SHA-256 ohne Salt — wird beim nächsten Login automatisch upgegradet
        legacy = _hashlib.sha256(passwort.encode("utf-8")).hexdigest()
        return _hmac.compare_digest(legacy, stored_hash)


def benutzer_laden() -> list[dict]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT b.*, v.name AS verein
            FROM benutzer b
            LEFT JOIN vereine v ON b.verein_id = v.id
            ORDER BY v.name, b.nachname, b.vorname
        """).fetchall())


def benutzer_by_id(benutzer_id: int) -> dict | None:
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone())


def trainer_registrieren(
    vorname: str,
    nachname: str,
    email: str,
    passwort: str,
    *,
    benutzername: str | None = None,
    lizenztyp: str = "TRAINER_BASIC",
    abo_intervall: str = "monat",
) -> int:
    """Trainer-Selbstregistrierung mit persönlichem Einzeltrainer-Verein.

    Erstellt automatisch einen persönlichen Verein für den Trainer
    (lizenz_status='trial', 30 Tage Testphase, ist_technischer_mandant=1),
    damit verein_id niemals NULL ist.

    lizenztyp muss TRAINER_BASIC oder TRAINER_PRO sein.
    abo_intervall muss 'monat' oder 'jahr' sein.

    Startet mit aktiv=0 und email_verifiziert=0.
    Ein Admin schaltet das Konto nach E-Mail-Bestätigung frei.
    """
    # Serverseitige Validierung: nur Trainer-Pakete erlaubt
    if lizenztyp not in _ERLAUBTE_TRAINER_PAKETE:
        raise ValueError(
            f"Ungültiges Paket für Trainer: {lizenztyp!r}. "
            f"Erlaubt: {sorted(_ERLAUBTE_TRAINER_PAKETE)}"
        )
    if abo_intervall not in _ERLAUBTE_INTERVALLE:
        raise ValueError(
            f"Ungültiges Abrechnungsintervall: {abo_intervall!r}. "
            f"Erlaubt: {sorted(_ERLAUBTE_INTERVALLE)}"
        )
    import sqlite3 as _sqlite3
    import datetime as _dt
    import secrets as _secrets
    email_norm = normalize_email(email)

    # E-Mail und Benutzername auf Eindeutigkeit prüfen (vor dem Verein-Anlegen)
    with get_conn() as conn:
        if conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(email)=?", (email_norm,)
        ).fetchone():
            raise ValueError("Diese E-Mail-Adresse ist bereits registriert.")
        if benutzername and conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(benutzername)=LOWER(?)", (benutzername,)
        ).fetchone():
            raise ValueError(f"Der Benutzername '{benutzername}' ist bereits vergeben.")

    # Persönlichen Verein für den Trainer anlegen (technischer Mandant)
    _vname = f"Trainer: {vorname} {nachname}".strip()
    _testphase_bis = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()
    _reg_code = _secrets.token_urlsafe(6).upper()
    with get_conn() as conn:
        _vcur = conn.execute(
            """INSERT INTO vereine (name, aktiv, lizenz_status, lizenztyp,
                                    testphase_bis, registrier_code,
                                    ist_technischer_mandant, abo_intervall)
               VALUES (?, 1, 'trial', ?, ?, ?, 1, ?)""",
            (_vname, lizenztyp, _testphase_bis, _reg_code, abo_intervall),
        )
        _new_vid = _vcur.lastrowid

    # Kundennummer für den neuen Verein
    kundennummer_vergeben_verein(_new_vid)

    # Trainer-Benutzer mit verein_id anlegen
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """INSERT INTO benutzer
                       (verein_id, vorname, nachname, email, passwort_hash,
                        rolle, aktiv, benutzername, email_verifiziert)
                   VALUES (?, ?, ?, ?, ?, 'Trainer', 0, ?, 0)""",
                (_new_vid, vorname, nachname, email_norm, _pw_hash(passwort), benutzername),
            )
            _new_bid = cur.lastrowid
        except _sqlite3.IntegrityError as e:
            # Verein wieder löschen, da der Benutzer nicht angelegt werden konnte
            try:
                conn.execute("DELETE FROM vereine WHERE id=?", (_new_vid,))
            except Exception:
                pass
            msg = str(e)
            if "UNIQUE" in msg and "email" in msg:
                raise ValueError(f"Die E-Mail-Adresse '{email_norm}' ist bereits vergeben.") from e
            if "UNIQUE" in msg and "benutzername" in msg:
                raise ValueError(f"Der Benutzername '{benutzername}' ist bereits vergeben.") from e
            raise

    kundennummer_vergeben_benutzer(_new_bid)
    return _new_bid


def registrier_code_laden(verein_id: int) -> str | None:
    """Gibt den aktuellen Beitrittscode des Vereins zurück."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT registrier_code FROM vereine WHERE id=?", (verein_id,)
        ).fetchone()
        return row[0] if row else None


def registrier_code_regenerieren(verein_id: int) -> str:
    """Generiert einen neuen, global eindeutigen Beitrittscode.

    Prüft vor dem Speichern, ob der Code bereits bei einem anderen Verein
    verwendet wird. Bei Kollision wird ein neuer Code generiert (max. 10 Versuche).
    """
    import secrets as _secrets
    for _ in range(10):
        neuer_code = _secrets.token_urlsafe(6).upper()
        with get_conn() as conn:
            belegt = conn.execute(
                "SELECT id FROM vereine WHERE UPPER(registrier_code)=? AND id!=?",
                (neuer_code, verein_id),
            ).fetchone()
            if belegt:
                continue  # Kollision → nochmal versuchen
            conn.execute(
                "UPDATE vereine SET registrier_code=? WHERE id=?", (neuer_code, verein_id)
            )
            return neuer_code
    # Extrem unwahrscheinlich: nach 10 Versuchen keinen freien Code gefunden
    raise RuntimeError("Konnte keinen eindeutigen Beitrittscode generieren.")


def verein_by_registriercode(code: str) -> dict | None:
    """Sucht einen Verein anhand des Beitrittscodes (case-insensitiv, getrimmt).

    Gibt None zurück wenn kein passender, aktiver, nicht-gesperrter Verein
    gefunden wird oder der Code leer ist.
    Technische Mandanten (Einzeltrainer-Vereine) werden nicht zurückgegeben.
    """
    if not code or not code.strip():
        return None
    code_norm = code.strip().upper()
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id, name, aktiv, gesperrt, max_trainer, lizenz_status
               FROM vereine
               WHERE UPPER(registrier_code) = ?
                 AND aktiv = 1
                 AND (gesperrt IS NULL OR gesperrt = 0)
                 AND (ist_technischer_mandant IS NULL OR ist_technischer_mandant = 0)""",
            (code_norm,),
        ).fetchone()
        if not row:
            return None
        return {
            "id":            row[0],
            "name":          row[1],
            "aktiv":         row[2],
            "gesperrt":      row[3],
            "max_trainer":   row[4],
            "lizenz_status": row[5],
        }


def trainer_verein_beitreten(
    verein_id: int,
    vorname: str,
    nachname: str,
    email: str,
    passwort: str,
    *,
    benutzername: str | None = None,
) -> int:
    """Legt einen Trainer in einem bestehenden Verein an (Beitrittscode-Flow).

    - Kein neuer technischer Mandant
    - Kein Stripe-Checkout
    - aktiv=0 → muss vom Vereinsadmin freigeschaltet werden
    - Prüft max_trainer-Limit des Vereins (aktive Trainer)
    - Bestehende E-Mail-/Benutzername-Eindeutigkeitsprüfung bleibt erhalten
    """
    import sqlite3 as _sqlite3
    email_norm = normalize_email(email)

    with get_conn() as conn:
        # Frische Vereinsdaten holen
        v = conn.execute(
            "SELECT id, name, aktiv, gesperrt, max_trainer FROM vereine WHERE id=?",
            (verein_id,),
        ).fetchone()
        if not v or not v[2] or v[3]:
            raise ValueError("Der Verein ist nicht aktiv oder gesperrt.")

        max_trainer = v[4]
        if max_trainer is not None:
            # Aktive UND wartende (aktiv=0) Trainer zählen — verhindert,
            # dass beliebig viele Pending-Accounts angelegt werden.
            alle_trainer = conn.execute(
                """SELECT COUNT(*) FROM benutzer
                   WHERE verein_id = ? AND rolle = 'Trainer'""",
                (verein_id,),
            ).fetchone()[0]
            if alle_trainer >= max_trainer:
                raise ValueError(
                    "Das Trainerlimit des Vereins ist erreicht. "
                    "Bitte kontaktiere deinen Vereinsadmin."
                )

        # E-Mail-Duplikat prüfen
        if conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(email) = ?", (email_norm,)
        ).fetchone():
            raise ValueError("Diese E-Mail-Adresse ist bereits registriert.")

        # Benutzername-Duplikat prüfen
        if benutzername and conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(benutzername) = LOWER(?)",
            (benutzername,),
        ).fetchone():
            raise ValueError(f"Der Benutzername '{benutzername}' ist bereits vergeben.")

        try:
            cur = conn.execute(
                """INSERT INTO benutzer
                       (verein_id, vorname, nachname, email, passwort_hash,
                        rolle, aktiv, benutzername, email_verifiziert)
                   VALUES (?, ?, ?, ?, ?, 'Trainer', 0, ?, 0)""",
                (verein_id, vorname, nachname, email_norm,
                 _pw_hash(passwort), benutzername),
            )
            return cur.lastrowid
        except _sqlite3.IntegrityError as e:
            msg = str(e)
            if "UNIQUE" in msg and "email" in msg:
                raise ValueError(
                    f"Die E-Mail-Adresse '{email_norm}' ist bereits vergeben."
                ) from e
            if "UNIQUE" in msg and "benutzername" in msg:
                raise ValueError(
                    f"Der Benutzername '{benutzername}' ist bereits vergeben."
                ) from e
            raise


def normalize_email(email: str) -> str:
    """E-Mail-Normalisierung: nur Kleinschreibung.
    Keine Punkte entfernen, keine +Zusätze entfernen, keine Provider-Änderungen.
    Muss überall gleich verwendet werden: Registrierung, Login, Token, Passwort-Reset."""
    return email.strip().lower()


def benutzer_speichern(
    verein_id, vorname, nachname, email, passwort, rolle,
    *, benutzername: str | None = None, email_verifiziert: int = 1,
) -> int:
    import sqlite3 as _sqlite3
    email_norm = normalize_email(email)
    with get_conn() as conn:
        try:
            cur = conn.execute("""
                INSERT INTO benutzer (verein_id, vorname, nachname, email,
                                      passwort_hash, rolle, aktiv,
                                      benutzername, email_verifiziert)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (verein_id, vorname, nachname, email_norm,
                  _pw_hash(passwort), rolle, benutzername, email_verifiziert))
            return cur.lastrowid
        except _sqlite3.IntegrityError as e:
            msg = str(e)
            if "UNIQUE" in msg and "email" in msg:
                raise ValueError(f"Die E-Mail-Adresse '{email_norm}' ist bereits vergeben.") from e
            if "UNIQUE" in msg and "benutzername" in msg:
                raise ValueError(f"Der Benutzername '{benutzername}' ist bereits vergeben.") from e
            raise


def benutzer_aktualisieren(
    benutzer_id, verein_id, vorname, nachname, email, rolle,
    *, caller_rolle: str | None = None, caller_verein_id: int | None = None,
) -> None:
    """Aktualisiert Stammdaten und Rolle eines Benutzers.

    Guards (serverseitig):
    - Rolleneskalation zu 'Superadmin' ist nur für Superadmins erlaubt.
    - Nicht-Superadmins dürfen nur Benutzer des eigenen Mandanten (verein_id) ändern.

    caller_rolle / caller_verein_id: Rolle und Verein des aufrufenden Benutzers.
    Sind beide None, wird der Aufruf als vertrauenswürdiger interner Aufruf behandelt.
    """
    import sqlite3 as _sqlite3
    email_norm = normalize_email(email)

    # ── Guard 1: Rolleneskalation zu Superadmin verhindern ────────────────────
    if rolle == "Superadmin" and caller_rolle is not None and caller_rolle != "Superadmin":
        raise PermissionError(
            "Rolleneskalation zu 'Superadmin' ist nicht erlaubt."
        )

    with get_conn() as conn:
        # ── Guard 2: Mandantentrennung — nur Superadmin darf fremde Benutzer ändern
        if caller_rolle is not None and caller_rolle != "Superadmin":
            ziel = conn.execute(
                "SELECT verein_id FROM benutzer WHERE id=?", (benutzer_id,)
            ).fetchone()
            if ziel is None:
                raise PermissionError("Benutzer nicht gefunden.")
            if ziel[0] != caller_verein_id:
                raise PermissionError(
                    "Zugriff verweigert: Dieser Benutzer gehört zu einem anderen Mandanten."
                )
        # ─────────────────────────────────────────────────────────────────────

        try:
            conn.execute("""
                UPDATE benutzer
                SET verein_id=?, vorname=?, nachname=?, email=?, rolle=?
                WHERE id=?
            """, (verein_id, vorname, nachname, email_norm, rolle, benutzer_id))
        except _sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e) and "email" in str(e):
                raise ValueError(f"Die E-Mail-Adresse '{email_norm}' ist bereits vergeben.") from e
            raise


def benutzer_aktivieren(benutzer_id: int, aktiv: int) -> None:
    """Aktiviert oder deaktiviert einen Benutzer.

    Guards (serverseitig):
    - Den letzten aktiven Superadmin nicht deaktivierbar.
    - Trainer-Freischaltung prüft das max_trainer-Limit des Vereins, damit
      auch bei parallelen Pending-Registrierungen das Limit eingehalten wird.
    Wirft ValueError wenn ein Guard greift.
    """
    with get_conn() as conn:
        ziel = conn.execute(
            "SELECT rolle, verein_id FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone()

        # ── Guard: letzten aktiven Superadmin schützen ────────────────────────
        if aktiv == 0 and ziel and ziel[0] == "Superadmin":
            n_aktive_sa = conn.execute(
                "SELECT COUNT(*) FROM benutzer WHERE rolle='Superadmin' AND aktiv=1"
            ).fetchone()[0]
            if n_aktive_sa <= 1:
                raise ValueError(
                    "Der letzte aktive Superadmin kann nicht deaktiviert werden. "
                    "Bitte zuerst einen weiteren Superadmin anlegen."
                )

        # ── Guard: max_trainer-Limit bei Trainer-Freischaltung ────────────────
        if aktiv == 1 and ziel and ziel[0] == "Trainer":
            verein_id = ziel[1]
            verein = conn.execute(
                "SELECT max_trainer FROM vereine WHERE id=?", (verein_id,)
            ).fetchone()
            if verein and verein[0] is not None:
                aktive_trainer = conn.execute(
                    """SELECT COUNT(*) FROM benutzer
                       WHERE verein_id=? AND rolle='Trainer' AND aktiv=1""",
                    (verein_id,),
                ).fetchone()[0]
                if aktive_trainer >= verein[0]:
                    raise ValueError(
                        "Das Trainerlimit des Vereins ist erreicht. "
                        "Es können keine weiteren Trainer freigeschaltet werden."
                    )

        # ─────────────────────────────────────────────────────────────────────
        conn.execute(
            "UPDATE benutzer SET aktiv=? WHERE id=?", (aktiv, benutzer_id)
        )


def sessions_benutzer_beenden(benutzer_id: int, conn=None) -> int:
    """Deaktiviert alle aktiven Sessions eines Benutzers (z. B. nach Passwortänderung).

    Gibt die Anzahl der beendeten Sessions zurück.
    Kann eine bestehende Datenbankverbindung (conn) entgegennehmen, damit
    Passwortänderung + Session-Invalidierung atomar in einer Transaktion laufen.
    Wird von benutzer_passwort() und pw_reset_anwenden() aufgerufen.
    """
    if conn is not None:
        cur = conn.execute(
            "UPDATE sessions SET aktiv=0 WHERE benutzer_id=? AND aktiv=1",
            (benutzer_id,),
        )
        return cur.rowcount
    with get_conn() as _conn:
        cur = _conn.execute(
            "UPDATE sessions SET aktiv=0 WHERE benutzer_id=? AND aktiv=1",
            (benutzer_id,),
        )
        return cur.rowcount


def benutzer_passwort(benutzer_id: int, neues_passwort: str) -> None:
    """Setzt den Passwort-Hash, inkrementiert session_token_version und invalidiert
    alle aktiven Sessions atomar in einer Transaktion.

    Durch den Versions-Increment wird auch der Login-Race verhindert: Sessions, die
    mit einem älteren session_token_version-Wert erstellt wurden (d. h. das Passwort
    wurde noch während des Logins geändert), werden bei der nächsten Validierung
    als ungültig erkannt.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET passwort_hash=?, "
            "session_token_version = COALESCE(session_token_version, 0) + 1 "
            "WHERE id=?",
            (_pw_hash(neues_passwort), benutzer_id),
        )
        # Alle aktiven Sessions in derselben Transaktion invalidieren.
        sessions_benutzer_beenden(benutzer_id, conn=conn)


# --------------------------------------------------------------------------
# Benutzer — Trainerportal-Erweiterungen
# --------------------------------------------------------------------------

def benutzer_foto_speichern(benutzer_id: int, foto_bytes: bytes | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET foto_blob=? WHERE id=?",
            (foto_bytes, benutzer_id),
        )


def benutzer_letzter_login_aktualisieren(benutzer_id: int) -> None:
    from datetime import datetime as _dt2
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET letzter_login=? WHERE id=?",
            (_dt2.now().strftime("%Y-%m-%d %H:%M"), benutzer_id),
        )


# ─── Brute-Force-Schutz ────────────────────────────────────────────────────

def benutzer_login_fehlversuch(benutzer_id: int, max_versuche: int, sperre_minuten: int) -> None:
    """Zählt einen Fehlversuch atomar hoch; sperrt das Konto wenn max_versuche erreicht.

    Das gesamte Inkrement + Sperr-Entscheid + Behandlung abgelaufener Sperren erfolgt
    in einem einzigen SQL-UPDATE (kein vorheriger SELECT), sodass parallele Anfragen
    keine Race Condition erzeugen können.

    Logik in einem einzigen atomaren UPDATE:
    - Ist gesperrt_bis abgelaufen → Zähler auf 1 setzen (Neustart), abgelaufene Sperre löschen.
    - Sonst Zähler um 1 erhöhen; bei Erreichen von max_versuche neue Sperre setzen.
    """
    offset = f"+{sperre_minuten} minutes"
    with get_conn() as conn:
        conn.execute(
            """UPDATE benutzer
               SET login_versuche = CASE
                       -- Abgelaufene Sperre: frisch von 1 zählen
                       WHEN gesperrt_bis IS NOT NULL AND gesperrt_bis <= datetime('now')
                       THEN 1
                       -- Normale Erhöhung
                       ELSE login_versuche + 1
                   END,
                   gesperrt_bis = CASE
                       -- Abgelaufene Sperre: neu sperren nur wenn max=1, sonst zurücksetzen
                       WHEN gesperrt_bis IS NOT NULL AND gesperrt_bis <= datetime('now')
                       THEN CASE WHEN 1 >= :max THEN datetime('now', :offset) ELSE NULL END
                       -- Limit erreicht: neue Sperre setzen
                       WHEN login_versuche + 1 >= :max
                       THEN datetime('now', :offset)
                       -- Noch unter dem Limit: vorhandenen Wert behalten (normalerweise NULL)
                       ELSE gesperrt_bis
                   END
               WHERE id = :id""",
            {"max": max_versuche, "offset": offset, "id": benutzer_id},
        )


def benutzer_login_zuruecksetzen(benutzer_id: int) -> None:
    """Setzt Fehlversuch-Zähler und Sperre nach erfolgreichem Login zurück."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET login_versuche=0, gesperrt_bis=NULL WHERE id=?",
            (benutzer_id,),
        )


def benutzer_sperre_pruefen(email_oder_benutzername: str) -> dict:
    """Gibt Sperr-Status für eine E-Mail oder einen Benutzernamen zurück.

    Alle Zeitvergleiche laufen in SQLite (UTC), sodass der Servertimezone keine Rolle spielt.
    Login ist case-insensitiv (E-Mail und Benutzername).

    Rückgabe: {
        'gesperrt': bool,
        'verbleibend_sek': int,   # Sekunden bis Entsperrung (0 wenn nicht gesperrt)
        'benutzer_id': int|None,
        'login_versuche': int,
    }
    """
    ein_lower = normalize_email(email_oder_benutzername)
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id,
                      login_versuche,
                      gesperrt_bis,
                      CASE
                          WHEN gesperrt_bis IS NOT NULL
                               AND datetime('now') < gesperrt_bis
                          THEN CAST(
                               (julianday(gesperrt_bis) - julianday('now')) * 86400
                               AS INTEGER)
                          ELSE 0
                      END AS verbleibend_sek,
                      CASE
                          WHEN gesperrt_bis IS NOT NULL
                               AND datetime('now') < gesperrt_bis
                          THEN 1 ELSE 0
                      END AS ist_gesperrt
               FROM benutzer
               WHERE (LOWER(email)=?
                      OR (benutzername IS NOT NULL AND LOWER(benutzername)=?))
                 AND aktiv = 1""",
            (ein_lower, ein_lower),
        ).fetchone()

    if row is None:
        return {"gesperrt": False, "verbleibend_sek": 0, "benutzer_id": None, "login_versuche": 0}

    if row["ist_gesperrt"]:
        return {
            "gesperrt": True,
            "verbleibend_sek": int(row["verbleibend_sek"]),
            "benutzer_id": row["id"],
            "login_versuche": row["login_versuche"] or 0,
        }

    # Sperre abgelaufen aber noch nicht gelöscht → bedingt zurücksetzen.
    # Das WHERE schützt vor einer Race Condition: ein paralleler Fehlversuch kann
    # zwischen unserem SELECT und diesem UPDATE eine neue Sperre setzen (gesperrt_bis
    # in der Zukunft). Die Bedingung `gesperrt_bis <= datetime('now')` stellt sicher,
    # dass nur wirklich abgelaufene Sperren gelöscht werden — eine frisch gesetzte
    # Zukunfts-Sperre wird dabei nicht berührt.
    if row["gesperrt_bis"] is not None:
        with get_conn() as conn:
            conn.execute(
                """UPDATE benutzer
                   SET login_versuche = 0, gesperrt_bis = NULL
                   WHERE id = ?
                     AND gesperrt_bis IS NOT NULL
                     AND gesperrt_bis <= datetime('now')""",
                (row["id"],),
            )
        return {
            "gesperrt": False,
            "verbleibend_sek": 0,
            "benutzer_id": row["id"],
            "login_versuche": 0,
        }

    return {
        "gesperrt": False,
        "verbleibend_sek": 0,
        "benutzer_id": row["id"],
        "login_versuche": row["login_versuche"] or 0,
    }


def login_log_eintrag(
    email: str,
    ergebnis: str,
    ip: str | None = None,
    benutzer_id: int | None = None,
) -> None:
    """Schreibt einen Eintrag in den Login-Audit-Log.

    ergebnis muss einer der Werte 'erfolg', 'fehlschlag' oder 'gesperrt' sein.
    verein_id wird automatisch aus dem Benutzer-Datensatz ermittelt, wenn benutzer_id
    übergeben wird.
    """
    verein_id: int | None = None
    if benutzer_id is not None:
        try:
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT verein_id FROM benutzer WHERE id=?", (benutzer_id,)
                ).fetchone()
                if row:
                    verein_id = row["verein_id"]
        except Exception:
            pass
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO login_log (email, ergebnis, ip, benutzer_id, verein_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (email, ergebnis, ip, benutzer_id, verein_id),
            )
    except Exception:
        pass  # Logging darf niemals einen Login blockieren


def login_log_laden(
    limit: int = 200,
    verein_id: int | None = None,
    ergebnis: str | None = None,
) -> list[dict]:
    """Lädt Login-Log-Einträge für das Superadmin-Dashboard.

    Gibt eine Liste von Dicts zurück, sortiert nach Zeitstempel und id absteigend
    (id als Tiebreaker, damit Ereignisse mit gleichem Sekundenbruchteil deterministisch
    geordnet werden — z.B. Fehlschlag + Sperre im selben Timestamp).

    verein_id: wenn gesetzt, nur Einträge dieses Vereins.
    ergebnis:  wenn gesetzt ('erfolg'|'fehlschlag'|'gesperrt'), wird in SQL gefiltert
               (vor LIMIT), sodass das Limit immer für Einträge dieses Typs gilt.
    """
    conditions: list[str] = []
    params: list = []

    if verein_id is not None:
        conditions.append("ll.verein_id = ?")
        params.append(verein_id)
    if ergebnis is not None:
        conditions.append("ll.ergebnis = ?")
        params.append(ergebnis)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    sql = f"""
        SELECT ll.id, ll.zeitstempel, ll.email, ll.ergebnis, ll.ip,
               ll.benutzer_id, ll.verein_id,
               v.name AS verein_name,
               b.vorname || ' ' || b.nachname AS benutzer_name
          FROM login_log ll
          LEFT JOIN vereine  v ON ll.verein_id   = v.id
          LEFT JOIN benutzer b ON ll.benutzer_id = b.id
         {where_clause}
         ORDER BY ll.zeitstempel DESC, ll.id DESC
         LIMIT ?
    """
    try:
        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def benutzer_profil_aktualisieren(
    benutzer_id: int,
    vorname: str, nachname: str, email: str,
    telefon: str | None = None,
    lizenz: str | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute("""
            UPDATE benutzer
            SET vorname=?, nachname=?, email=?, telefon=?, lizenz=?
            WHERE id=?
        """, (vorname, nachname, email, telefon, lizenz, benutzer_id))


def benutzer_benutzername_setzen(
    benutzer_id: int,
    benutzername: str | None,
) -> tuple[bool, str]:
    """
    Setzt oder löscht den Benutzernamen eines Benutzers.
    Leerer String oder None → Benutzername wird auf NULL gesetzt.
    Eindeutigkeitsprüfung erfolgt case-insensitiv; der eigene Eintrag
    wird korrekt ausgeschlossen (Benutzername bleibt bei gleicher Eingabe).
    Gibt (True, "") bei Erfolg zurück, (False, fehlermeldung) bei Fehler.
    """
    bn = benutzername.strip() if benutzername else None
    if not bn:
        bn = None  # explizit auf NULL setzen (Benutzername entfernen)

    with get_conn() as conn:
        if bn:
            clash = conn.execute(
                "SELECT id FROM benutzer "
                "WHERE LOWER(benutzername)=LOWER(?) AND id != ?",
                (bn, benutzer_id),
            ).fetchone()
            if clash:
                return False, f"Der Benutzername \"{bn}\" ist bereits vergeben."
        conn.execute(
            "UPDATE benutzer SET benutzername=? WHERE id=?",
            (bn, benutzer_id),
        )
    return True, ""


def trainer_statistiken(benutzer_id: int) -> dict:
    """Zählt Spieler und Diagnostiken für einen Trainer."""
    _DIAG_TBLS = [
        "sprint_test", "sprung_test", "anthropometrie", "fms_ergebnis",
        "y_balance_ergebnis", "ausdauer_test", "kraft_test",
        "agilitaet_test", "spiro_test",
    ]
    with get_conn() as conn:
        spieler_n = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE trainer_id=?", (benutzer_id,)
        ).fetchone()[0]
        diag_n = 0
        for tbl in _DIAG_TBLS:
            try:
                diag_n += conn.execute(
                    f"SELECT COUNT(*) FROM {tbl} "
                    f"WHERE spieler_id IN (SELECT id FROM spieler WHERE trainer_id=?)",
                    (benutzer_id,),
                ).fetchone()[0]
            except Exception:
                pass
        return {"spieler": spieler_n, "diagnostiken": diag_n}


def benutzer_loeschen(benutzer_id: int) -> tuple[bool, str]:
    """Löscht einen Benutzer — nur wenn keine Spieler zugeordnet sind.

    Guard (serverseitig): Der letzte aktive Superadmin kann nicht gelöscht werden.

    Vor dem DELETE werden alle abhängigen Zeilen ohne ON DELETE CASCADE / SET NULL
    manuell bereinigt, damit PRAGMA foreign_keys = ON keinen IntegrityError auslöst:
      - sessions            → DELETE (benutzer_id NOT NULL, kein Cascade)
      - rechnungsadressen   → DELETE (benutzer_id NOT NULL, kein Cascade)
      - spieler_zuweisung_log.ausfuehrender_id → SET NULL
      - audit_log.benutzer_id / superadmin_id  → SET NULL
    """
    with get_conn() as conn:
        # ── Guard: letzten aktiven Superadmin schützen ────────────────────────
        ziel = conn.execute(
            "SELECT rolle, aktiv FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone()
        if ziel and ziel[0] == "Superadmin":
            n_aktive_sa = conn.execute(
                "SELECT COUNT(*) FROM benutzer WHERE rolle='Superadmin' AND aktiv=1"
            ).fetchone()[0]
            if n_aktive_sa <= 1:
                return False, (
                    "Der letzte aktive Superadmin kann nicht gelöscht werden. "
                    "Bitte zuerst einen weiteren Superadmin anlegen."
                )
        # ─────────────────────────────────────────────────────────────────────

        spieler_n = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE trainer_id=?", (benutzer_id,)
        ).fetchone()[0]
        if spieler_n > 0:
            return False, (
                f"Trainer hat noch {spieler_n} Spieler. "
                "Bitte zuerst alle Spieler einem anderen Trainer zuweisen."
            )

        # ── Abhängige Zeilen ohne ON DELETE CASCADE/SET NULL bereinigen ───────
        # Sessions löschen (benutzer_id NOT NULL, kein Cascade in Schema)
        conn.execute("DELETE FROM sessions WHERE benutzer_id=?", (benutzer_id,))
        # Rechnungsadresse löschen (benutzer_id NOT NULL, kein Cascade)
        conn.execute(
            "DELETE FROM rechnungsadressen WHERE benutzer_id=?", (benutzer_id,)
        )
        # Zuweisung-Log: ausfuehrender_id nullen (nullable, ältere Schema-Version ohne SET NULL)
        conn.execute(
            "UPDATE spieler_zuweisung_log SET ausfuehrender_id=NULL "
            "WHERE ausfuehrender_id=?",
            (benutzer_id,),
        )
        # Audit-Log: benutzer_id und superadmin_id nullen (nullable, kein SET NULL)
        conn.execute(
            "UPDATE audit_log SET benutzer_id=NULL WHERE benutzer_id=?",
            (benutzer_id,),
        )
        conn.execute(
            "UPDATE audit_log SET superadmin_id=NULL WHERE superadmin_id=?",
            (benutzer_id,),
        )
        # ─────────────────────────────────────────────────────────────────────

        conn.execute("DELETE FROM benutzer WHERE id=?", (benutzer_id,))
        return True, ""


# ── Dashboard Analytics ───────────────────────────────────────────────────────

_DIAG_TBLS = [
    "sprint_test", "sprung_test", "anthropometrie", "fms_test",
    "y_balance_test", "ausdauer_test", "kraft_test", "agilitaet_test", "spiro_test",
]


def dashboard_sa_kpis() -> dict:
    """KPIs für Superadmin-Dashboard (B3: erweitert um Trial, Abos, Kündigungen, Zahlungsprobleme)."""
    with get_conn() as conn:
        _tm = "WHERE COALESCE(ist_technischer_mandant,0)=0"
        n_vereine  = conn.execute(f"SELECT COUNT(*) FROM vereine {_tm}").fetchone()[0]
        n_aktiv    = conn.execute(f"SELECT COUNT(*) FROM vereine {_tm} AND aktiv=1").fetchone()[0]
        n_gesperrt = conn.execute(f"SELECT COUNT(*) FROM vereine {_tm} AND aktiv=0").fetchone()[0]
        n_vadmin   = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE rolle='Vereinsadmin' AND aktiv=1"
        ).fetchone()[0]
        n_trainer  = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE rolle='Trainer' AND aktiv=1"
        ).fetchone()[0]
        n_spieler  = conn.execute("SELECT COUNT(*) FROM spieler").fetchone()[0]
        n_benutzer = conn.execute("SELECT COUNT(*) FROM benutzer WHERE aktiv=1").fetchone()[0]
        total_diag = 0
        for t in _DIAG_TBLS:
            try:
                total_diag += conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                pass

        # ── B3: Neue KPIs ─────────────────────────────────────────────────────
        # Standalone-Trainer-Subquery (kein Verein oder technischer Mandant)
        _sa_trainer_where = (
            "b.rolle='Trainer' AND "
            "(b.verein_id IS NULL OR EXISTS ("
            "SELECT 1 FROM vereine v WHERE v.id=b.verein_id "
            "AND COALESCE(v.ist_technischer_mandant,0)=1))"
        )

        # Kunden gesamt (Vereine + standalone Trainer)
        n_trainer_standalone = conn.execute(
            f"SELECT COUNT(*) FROM benutzer b WHERE {_sa_trainer_where}"
        ).fetchone()[0]
        n_kunden_gesamt = n_vereine + n_trainer_standalone

        # Testphasen (trial)
        try:
            n_trial = (
                conn.execute(
                    f"SELECT COUNT(*) FROM vereine {_tm} "
                    "AND COALESCE(lizenz_status,'trial')='trial'"
                ).fetchone()[0]
                + conn.execute(
                    f"SELECT COUNT(*) FROM benutzer b WHERE {_sa_trainer_where} "
                    "AND COALESCE(b.lizenz_status,'trial')='trial'"
                ).fetchone()[0]
            )
        except Exception:
            n_trial = 0

        # Aktive Abos (lizenz_status = 'active')
        try:
            n_aktive_abos = (
                conn.execute(
                    f"SELECT COUNT(*) FROM vereine {_tm} AND lizenz_status='active'"
                ).fetchone()[0]
                + conn.execute(
                    f"SELECT COUNT(*) FROM benutzer b WHERE {_sa_trainer_where} "
                    "AND b.lizenz_status='active'"
                ).fetchone()[0]
            )
        except Exception:
            n_aktive_abos = 0

        # Gekündigte Abos
        try:
            n_gekuendigt = conn.execute(
                f"SELECT COUNT(*) FROM vereine {_tm} "
                "AND kuendigungsstatus IS NOT NULL AND kuendigungsstatus != 'aktiv'"
            ).fetchone()[0]
        except Exception:
            n_gekuendigt = 0

        # Zahlungsprobleme
        try:
            n_zahlungsproblem = conn.execute(
                f"SELECT COUNT(*) FROM vereine {_tm} AND zahlungsstatus='fehlgeschlagen'"
            ).fetchone()[0]
        except Exception:
            n_zahlungsproblem = 0

    return {
        "n_vereine":        n_vereine,
        "n_aktiv":          n_aktiv,
        "n_gesperrt":       n_gesperrt,
        "n_vadmin":         n_vadmin,
        "n_trainer":        n_trainer,
        "n_spieler":        n_spieler,
        "n_benutzer":       n_benutzer,
        "n_diagnostiken":   total_diag,
        # B3 — neue KPIs
        "n_kunden_gesamt":  n_kunden_gesamt,
        "n_trial":          n_trial,
        "n_aktive_abos":    n_aktive_abos,
        "n_gekuendigt":     n_gekuendigt,
        "n_zahlungsproblem": n_zahlungsproblem,
    }


def dashboard_verein_uebersicht() -> list[dict]:
    """Gibt für jeden Verein eine Zeile mit aggregierten Kennzahlen zurück.

    Felder: id, name, lizenztyp, lizenz_bis, lizenz_status, aktiv, gesperrt,
            n_trainer, n_spieler, n_diagnostiken, letzte_aktivitaet
    """
    with get_conn() as conn:
        # Basisinfo aller Vereine — optional columns may not exist on older DBs
        try:
            vereine = _rows(conn.execute(
                "SELECT id, name, lizenztyp, lizenz_bis, lizenz_status, aktiv, gesperrt, "
                "cancel_at_period_end, gekuendigt_zum "
                "FROM vereine ORDER BY name"
            ).fetchall())
        except sqlite3.OperationalError as _e:
            if "no such column" not in str(_e):
                raise
            # Older schema: optional columns not yet added via ALTER TABLE
            vereine = _rows(conn.execute(
                "SELECT id, name, aktiv FROM vereine ORDER BY name"
            ).fetchall())
            for v in vereine:
                v.setdefault("lizenztyp", None)
                v.setdefault("lizenz_bis", None)
                v.setdefault("lizenz_status", None)
                v.setdefault("gesperrt", 0)
                v.setdefault("cancel_at_period_end", 0)
                v.setdefault("gekuendigt_zum", None)

        for v in vereine:
            vid = v["id"]
            v["n_trainer"] = conn.execute(
                "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1", (vid,)
            ).fetchone()[0]
            v["n_spieler"] = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (vid,)
            ).fetchone()[0]
            # Letzte Benutzeranmeldung im Verein
            row = conn.execute(
                "SELECT MAX(letzter_login) FROM benutzer WHERE verein_id=? "
                "AND letzter_login IS NOT NULL", (vid,)
            ).fetchone()
            v["letzte_aktivitaet"] = row[0] if row and row[0] else None
            # Diagnostiken quer über alle Tabellen
            diag_n = 0
            for tbl in _DIAG_TBLS:
                try:
                    diag_n += conn.execute(
                        f"SELECT COUNT(*) FROM {tbl} "
                        f"WHERE spieler_id IN (SELECT id FROM spieler WHERE verein_id=?)",
                        (vid,),
                    ).fetchone()[0]
                except Exception:
                    pass
            v["n_diagnostiken"] = diag_n
    return vereine


def dashboard_va_kpis(verein_id: int) -> dict:
    """KPIs für Vereinsadmin-Dashboard."""
    with get_conn() as conn:
        n_trainer  = conn.execute(
            "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1", (verein_id,)
        ).fetchone()[0]
        n_spieler  = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (verein_id,)
        ).fetchone()[0]
        n_verletz  = conn.execute(
            "SELECT COUNT(*) FROM verletzung v JOIN spieler s ON v.spieler_id=s.id "
            "WHERE s.verein_id=? AND (v.ausfall_tage IS NULL OR "
            "date(v.datum,'+'||v.ausfall_tage||' days')>=date('now'))", (verein_id,)
        ).fetchone()[0]
        # Players never tested
        n_ungetestet = conn.execute(
            "SELECT COUNT(*) FROM spieler s WHERE s.verein_id=? "
            "AND NOT EXISTS (SELECT 1 FROM fms_test WHERE spieler_id=s.id) "
            "AND NOT EXISTS (SELECT 1 FROM sprint_test WHERE spieler_id=s.id) "
            "AND NOT EXISTS (SELECT 1 FROM y_balance_test WHERE spieler_id=s.id)",
            (verein_id,)
        ).fetchone()[0]
        total_diag = 0
        for t in _DIAG_TBLS:
            try:
                total_diag += conn.execute(
                    f"SELECT COUNT(*) FROM {t} WHERE spieler_id IN "
                    f"(SELECT id FROM spieler WHERE verein_id=?)", (verein_id,)
                ).fetchone()[0]
            except Exception:
                pass
        # Avg FMS score (latest per player)
        avg_fms = conn.execute(
            "SELECT AVG(f.score) FROM fms_test f "
            "WHERE f.spieler_id IN (SELECT id FROM spieler WHERE verein_id=?) "
            "AND f.id=(SELECT MAX(id) FROM fms_test WHERE spieler_id=f.spieler_id)",
            (verein_id,)
        ).fetchone()[0]
    return {
        "n_trainer": n_trainer, "n_spieler": n_spieler, "n_verletzungen": n_verletz,
        "n_ungetestet": n_ungetestet, "n_diagnostiken": total_diag,
        "avg_fms": round(avg_fms, 1) if avg_fms else None,
    }


def dashboard_monatlich_vereine(n: int = 12) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m',erstellt_am) AS m, COUNT(*) AS n "
            "FROM vereine WHERE erstellt_am IS NOT NULL GROUP BY m ORDER BY m"
        ).fetchall()
    return [{"monat": r[0], "n": r[1]} for r in rows]


def dashboard_monatlich_trainer(n: int = 12) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m',erstellt_am) AS m, COUNT(*) AS n "
            "FROM benutzer WHERE rolle IN ('Trainer','Vereinsadmin') "
            "AND erstellt_am IS NOT NULL GROUP BY m ORDER BY m"
        ).fetchall()
    return [{"monat": r[0], "n": r[1]} for r in rows]


def dashboard_monatlich_diagnostiken(verein_id=None, n: int = 12) -> list:
    monthly: dict = {}
    with get_conn() as conn:
        for tbl in _DIAG_TBLS:
            try:
                if verein_id:
                    rows = conn.execute(
                        f"SELECT strftime('%Y-%m',t.datum) AS m, COUNT(*) AS n "
                        f"FROM {tbl} t JOIN spieler s ON t.spieler_id=s.id "
                        f"WHERE s.verein_id=? AND t.datum IS NOT NULL GROUP BY m",
                        (verein_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        f"SELECT strftime('%Y-%m',datum) AS m, COUNT(*) AS n "
                        f"FROM {tbl} WHERE datum IS NOT NULL GROUP BY m"
                    ).fetchall()
                for r in rows:
                    monthly[r[0]] = monthly.get(r[0], 0) + r[1]
            except Exception:
                pass
    return [{"monat": k, "n": v} for k, v in sorted(
        ((k, v) for k, v in monthly.items() if k is not None), key=lambda x: x[0]
    )]


def dashboard_spieler_altersklassen(verein_id=None) -> list:
    with get_conn() as conn:
        if verein_id:
            rows = conn.execute(
                "SELECT COALESCE(altersklasse,'Unbekannt') AS ak, COUNT(*) AS n "
                "FROM spieler WHERE verein_id=? GROUP BY ak ORDER BY n DESC", (verein_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT COALESCE(altersklasse,'Unbekannt') AS ak, COUNT(*) AS n "
                "FROM spieler GROUP BY ak ORDER BY n DESC"
            ).fetchall()
    return [{"altersklasse": r[0], "n": r[1]} for r in rows]


def dashboard_spieler_mannschaften(verein_id=None) -> list:
    with get_conn() as conn:
        if verein_id:
            rows = conn.execute(
                "SELECT COALESCE(mannschaft,'Ohne Mannschaft') AS m, COUNT(*) AS n "
                "FROM spieler WHERE verein_id=? GROUP BY m ORDER BY n DESC", (verein_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT COALESCE(mannschaft,'Ohne Mannschaft') AS m, COUNT(*) AS n "
                "FROM spieler GROUP BY m ORDER BY n DESC"
            ).fetchall()
    return [{"mannschaft": r[0], "n": r[1]} for r in rows]


def dashboard_letzte_logins(verein_id=None, limit: int = 8) -> list:
    with get_conn() as conn:
        if verein_id:
            rows = conn.execute(
                "SELECT vorname,nachname,email,rolle,letzter_login FROM benutzer "
                "WHERE verein_id=? AND letzter_login IS NOT NULL "
                "ORDER BY letzter_login DESC LIMIT ?", (verein_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT vorname,nachname,email,rolle,letzter_login FROM benutzer "
                "WHERE letzter_login IS NOT NULL ORDER BY letzter_login DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [{"vorname": r[0], "nachname": r[1], "email": r[2],
             "rolle": r[3], "letzter_login": r[4]} for r in rows]


def dashboard_trainer_letzte_spieler(trainer_id: int, limit: int = 6) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT s.id, s.name, s.vorname, s.nachname, s.mannschaft, s.altersklasse, "
            "(SELECT MAX(d) FROM ("
            " SELECT datum AS d FROM fms_test     WHERE spieler_id=s.id "
            " UNION ALL SELECT datum FROM sprint_test   WHERE spieler_id=s.id "
            " UNION ALL SELECT datum FROM y_balance_test WHERE spieler_id=s.id "
            " UNION ALL SELECT datum FROM agilitaet_test WHERE spieler_id=s.id "
            " UNION ALL SELECT datum FROM ausdauer_test  WHERE spieler_id=s.id "
            ")) AS letzte_messung "
            "FROM spieler s WHERE s.trainer_id=? "
            "ORDER BY letzte_messung DESC LIMIT ?",
            (trainer_id, limit),
        ).fetchall()
    return [{"id": r[0], "name": r[1], "vorname": r[2], "nachname": r[3],
             "mannschaft": r[4] or "—", "altersklasse": r[5] or "—",
             "letzte_messung": r[6]} for r in rows]


def dashboard_trainer_ohne_test(trainer_id: int) -> int:
    """Spieler ohne Test in den letzten 30 Tagen (inkl. nie getesteter)."""
    with get_conn() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM spieler s WHERE s.trainer_id=? "
            "AND NOT EXISTS ("
            " SELECT 1 FROM ("
            "  SELECT spieler_id, datum FROM fms_test "
            "  UNION ALL SELECT spieler_id, datum FROM sprint_test "
            "  UNION ALL SELECT spieler_id, datum FROM y_balance_test "
            "  UNION ALL SELECT spieler_id, datum FROM agilitaet_test "
            "  UNION ALL SELECT spieler_id, datum FROM ausdauer_test "
            " ) t WHERE t.spieler_id=s.id "
            "   AND t.datum >= date('now','-30 days')"
            ")",
            (trainer_id,),
        ).fetchone()[0]
    return n


def dashboard_trainer_neue_verletzungen(trainer_id: int) -> int:
    with get_conn() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM verletzung v JOIN spieler s ON v.spieler_id=s.id "
            "WHERE s.trainer_id=? AND v.datum >= date('now','-14 days')",
            (trainer_id,),
        ).fetchone()[0]
    return n


def dashboard_trainer_diagnostiken_monat(trainer_id: int) -> int:
    """Diagnostiken diesen Monat für alle Spieler des Trainers."""
    monat = __import__("datetime").date.today().strftime("%Y-%m")
    total = 0
    with get_conn() as conn:
        for t in _DIAG_TBLS:
            try:
                total += conn.execute(
                    f"SELECT COUNT(*) FROM {t} WHERE spieler_id IN "
                    f"(SELECT id FROM spieler WHERE trainer_id=?) "
                    f"AND strftime('%Y-%m',datum)=?",
                    (trainer_id, monat),
                ).fetchone()[0]
            except Exception:
                pass
    return total


# ─── Lizenz-Ablauf-Warnung ────────────────────────────────────────────────────

def lizenz_ablauf_vereine(tage: int = 30) -> list[dict]:
    """
    Gibt alle aktiven Vereine zurück, deren Lizenz in ≤ `tage` Tagen abläuft.

    Berücksichtigte Fälle:
    - lizenz_status = 'active': Ablaufdatum ist lizenz_bis
    - lizenz_status = 'trial':  Ablaufdatum ist testphase_bis

    Ausgeschlossen: expired, suspended, cancelled (bereits inaktiv oder abgelaufen),
    gesperrte und deaktivierte Vereine.

    Felder: id, name, lizenz_bis (effektives Ablaufdatum), tage_bis_ablauf
    """
    heute = date.today().isoformat()
    grenze = (date.today() + __import__("datetime").timedelta(days=tage)).isoformat()
    try:
        with get_conn() as conn:
            rows = _rows(conn.execute(
                """
                -- Aktive Lizenzen (lizenz_bis)
                SELECT id, name, lizenz_bis AS ablauf_datum
                  FROM vereine
                 WHERE lizenz_status = 'active'
                   AND lizenz_bis IS NOT NULL
                   AND lizenz_bis != ''
                   AND lizenz_bis >= ?
                   AND lizenz_bis <= ?
                   AND COALESCE(aktiv, 1) = 1
                   AND COALESCE(gesperrt, 0) = 0

                UNION ALL

                -- Trial-Lizenzen (testphase_bis)
                SELECT id, name, testphase_bis AS ablauf_datum
                  FROM vereine
                 WHERE lizenz_status = 'trial'
                   AND testphase_bis IS NOT NULL
                   AND testphase_bis != ''
                   AND testphase_bis >= ?
                   AND testphase_bis <= ?
                   AND COALESCE(aktiv, 1) = 1
                   AND COALESCE(gesperrt, 0) = 0

                ORDER BY ablauf_datum ASC
                """,
                (heute, grenze, heute, grenze),
            ).fetchall())
        today = date.today()
        result = []
        for r in rows:
            try:
                ablauf = date.fromisoformat(r["ablauf_datum"])
                r["lizenz_bis"] = r["ablauf_datum"]
                r["tage_bis_ablauf"] = (ablauf - today).days
            except Exception:
                r["lizenz_bis"] = r.get("ablauf_datum", "")
                r["tage_bis_ablauf"] = 0
            result.append(r)
        return result
    except Exception:
        return []


def superadmin_emails() -> list[str]:
    """Gibt die E-Mail-Adressen aller aktiven Superadmins zurück."""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT email FROM benutzer "
                "WHERE rolle='Superadmin' AND aktiv=1",
            ).fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def lizenz_warn_bereits_gesendet(verein_id: int, tage_fenster: int = 7) -> bool:
    """True wenn innerhalb der letzten `tage_fenster` Tage bereits eine Warnung gesendet wurde."""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM lizenz_warn_log "
                "WHERE verein_id=? "
                "  AND gesendet_am >= date('now', ?)",
                (verein_id, f"-{tage_fenster} days"),
            ).fetchone()
        return row is not None
    except Exception:
        return False


def lizenz_warn_protokollieren(verein_id: int) -> None:
    """Trägt den heutigen Tag als Warndatum für einen Verein ein."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lizenz_warn_log (verein_id, gesendet_am) "
                "VALUES (?, date('now'))",
                (verein_id,),
            )
    except Exception:
        pass


# --------------------------------------------------------------------------
# E-Mail-Verifikation
# --------------------------------------------------------------------------

def email_token_erzeugen(benutzer_id: int) -> str:
    """Erzeugt einen neuen E-Mail-Verifikationstoken (24h gültig, einmalig)."""
    import datetime as _dt
    token  = _secrets.token_urlsafe(32)
    ablauf = (_dt.datetime.utcnow() + _dt.timedelta(hours=24)).isoformat()
    jetzt  = _dt.datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """UPDATE benutzer
               SET email_token=?, email_token_ablauf=?, email_token_gesendet_am=?
             WHERE id=?""",
            (token, ablauf, jetzt, benutzer_id),
        )
    return token


def email_token_resend_erlaubt(benutzer_id: int, min_abstand_min: int = 5) -> bool:
    """Rate-Limit: True wenn seit der letzten Sendung mindestens min_abstand_min Minuten vergangen."""
    import datetime as _dt
    with get_conn() as conn:
        row = conn.execute(
            "SELECT email_token_gesendet_am FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone()
    if not row or not row[0]:
        return True
    try:
        gesendet = _dt.datetime.fromisoformat(row[0])
        return (_dt.datetime.utcnow() - gesendet).total_seconds() >= min_abstand_min * 60
    except (ValueError, TypeError):
        return True


def email_token_validieren(token: str) -> int | None:
    """Prüft Token, markiert E-Mail als verifiziert. Gibt benutzer_id zurück oder None.
    Token wird nach Verwendung invalidiert — kann nur einmal verwendet werden."""
    import datetime as _dt
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email_token_ablauf, email_verifiziert FROM benutzer WHERE email_token=?",
            (token,),
        ).fetchone()
        if not row:
            return None
        bid, ablauf, bereits = row[0], row[1], row[2]
        if bereits:
            return None  # Token bereits verwendet
        if ablauf:
            try:
                if _dt.datetime.utcnow() > _dt.datetime.fromisoformat(ablauf):
                    return None  # abgelaufen
            except (ValueError, TypeError):
                return None
        conn.execute(
            "UPDATE benutzer SET email_verifiziert=1, email_token=NULL, email_token_ablauf=NULL WHERE id=?",
            (bid,),
        )
        return bid


# --------------------------------------------------------------------------
# Passwort-Reset
# --------------------------------------------------------------------------

def pw_reset_token_erzeugen(email_oder_benutzername: str) -> tuple[str, str, str] | None:
    """Erzeugt Reset-Token für E-Mail oder Benutzername (1h gültig, einmalig).
    Gibt (token, vorname, email) zurück oder None wenn kein Konto gefunden."""
    import datetime as _dt
    ein = normalize_email(email_oder_benutzername)
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id, vorname, email FROM benutzer
               WHERE (LOWER(email)=? OR (benutzername IS NOT NULL AND LOWER(benutzername)=?))
                 AND aktiv=1""",
            (ein, ein),
        ).fetchone()
        if not row:
            return None
        bid, vorname, email = row[0], row[1], row[2]
        token  = _secrets.token_urlsafe(32)
        ablauf = (_dt.datetime.utcnow() + _dt.timedelta(hours=24)).isoformat()
        conn.execute(
            "UPDATE benutzer SET pw_reset_token=?, pw_reset_ablauf=? WHERE id=?",
            (token, ablauf, bid),
        )
        return token, vorname or "Benutzer", email


def pw_reset_token_validieren(token: str) -> int | None:
    """Prüft Reset-Token. Gibt benutzer_id zurück oder None (abgelaufen/ungültig)."""
    import datetime as _dt
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, pw_reset_ablauf FROM benutzer WHERE pw_reset_token=?", (token,)
        ).fetchone()
        if not row:
            return None
        bid, ablauf = row[0], row[1]
        if ablauf:
            try:
                if _dt.datetime.utcnow() > _dt.datetime.fromisoformat(ablauf):
                    return None
            except (ValueError, TypeError):
                return None
        return bid


def kuendigung_einreichen(
    entity_id: int,
    ist_verein: bool,
    grund: str | None = None,
    *,
    kuendigungsstatus_override: str | None = None,
    cancel_at_period_end: bool = False,
    gekuendigt_zum: str | None = None,
) -> tuple[bool, str]:
    """Speichert eine Kündigung. Gibt (True, iso-zeitstempel) oder (False, 'bereits_gekuendigt').

    kuendigungsstatus_override: wenn angegeben, wird dieser Status gesetzt statt 'eingegangen'
    cancel_at_period_end: setzt cancel_at_period_end=1 (nur für vereine-Tabelle, Stripe-backed)
    gekuendigt_zum: ISO-Datum des Vertragsendes aus Stripe (optional)
    """
    from datetime import datetime
    jetzt = datetime.utcnow().isoformat()
    tabelle = "vereine" if ist_verein else "benutzer"
    status = kuendigungsstatus_override or "eingegangen"
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT kuendigung_eingegangen FROM {tabelle} WHERE id=?", (entity_id,)
        ).fetchone()
        if row and row[0]:
            return False, "bereits_gekuendigt"
        if ist_verein and cancel_at_period_end:
            conn.execute(
                f"UPDATE {tabelle} SET kuendigung_eingegangen=?, "
                f"kuendigungsstatus=?, kuendigung_grund=?, "
                f"cancel_at_period_end=1, gekuendigt_zum=COALESCE(?,gekuendigt_zum) WHERE id=?",
                (jetzt, status, grund, gekuendigt_zum, entity_id),
            )
        else:
            conn.execute(
                f"UPDATE {tabelle} SET kuendigung_eingegangen=?, "
                f"kuendigungsstatus=?, kuendigung_grund=? WHERE id=?",
                (jetzt, status, grund, entity_id),
            )
    return True, jetzt


def kuendigung_widerrufen(entity_id: int, ist_verein: bool) -> tuple[bool, str]:
    """Zieht eine eingereichte Kündigung zurück.

    Nur möglich solange kuendigungsstatus IN ('eingegangen','vorgemerkt') UND die
    optionale Widerruf-Frist (KUENDIGUNG_WIDERRUF_STUNDEN, 0 = unbegrenzt) noch
    nicht abgelaufen ist.

    Atomisches bedingtes UPDATE — kein TOCTOU-Risiko: die Frist- und
    Statusprüfung erfolgt direkt in der WHERE-Klausel des UPDATEs.

    Gibt zurück:
      (True,  'ok')                — Widerruf erfolgreich
      (False, 'frist_abgelaufen')  — Frist überschritten, Status noch 'eingegangen'/'vorgemerkt'
      (False, 'nicht_widerrufbar') — Status bereits 'bestaetigt' oder 'beendet'
    """
    import os as _os
    import datetime as _dt

    tabelle = "vereine" if ist_verein else "benutzer"

    # Optionale Widerruf-Frist: ältester erlaubter Eingangszeitpunkt (UTC-ISO)
    frist_cutoff: str | None = None
    try:
        frist_stunden = int(_os.environ.get("KUENDIGUNG_WIDERRUF_STUNDEN", "0"))
        if frist_stunden > 0:
            frist_cutoff = (
                _dt.datetime.utcnow() - _dt.timedelta(hours=frist_stunden)
            ).isoformat(timespec="seconds")
    except (ValueError, TypeError):
        pass

    with get_conn() as conn:
        # Beide Zustände ('eingegangen' und 'vorgemerkt') sind widerrufbar
        _cancel_reset = "cancel_at_period_end=0, gekuendigt_zum=NULL, " if ist_verein else ""
        cur = conn.execute(
            f"UPDATE {tabelle} SET "
            f"kuendigung_eingegangen=NULL, "
            f"kuendigungsstatus='aktiv', "
            f"kuendigung_grund=NULL, "
            f"{_cancel_reset}"
            f"kuendigung_bestaetigung_am=NULL "
            f"WHERE id=? AND kuendigungsstatus IN ('eingegangen','vorgemerkt') "
            f"AND (? IS NULL OR kuendigung_eingegangen >= ?)",
            (entity_id, frist_cutoff, frist_cutoff),
        )
        if cur.rowcount == 0:
            # Unterscheiden: Frist abgelaufen vs. Status bereits geändert
            row = conn.execute(
                f"SELECT kuendigungsstatus FROM {tabelle} WHERE id=?",
                (entity_id,),
            ).fetchone()
            if row and row["kuendigungsstatus"] in ("eingegangen", "vorgemerkt") and frist_cutoff:
                # Status noch widerrufbar → UPDATE scheiterte an der Frist
                return False, "frist_abgelaufen"
            return False, "nicht_widerrufbar"
    return True, "ok"


def kuendigung_bestaetigen(
    entity_id: int,
    ist_verein: bool,
    vertragsende: str | None = None,
    status: str = "bestaetigt",
) -> tuple[bool, str]:
    """Superadmin bestätigt / beendet eine Kündigung; setzt optional Vertragsende.

    Atomische Zustandsprüfung — gültige Vorgänger-Zustände:
      'bestaetigt': nur aus 'eingegangen'
      'beendet':    aus 'eingegangen' oder 'bestaetigt'

    rowcount == 0 bedeutet, dass die Kündigung inzwischen vom Kunden widerrufen
    oder der Status anderweitig geändert wurde — kein Update wird ausgeführt.

    Rückgabe: (True, 'ok') bei Erfolg
              (False, 'widerrufen_oder_ungueltig') wenn Voraussetzung nicht erfüllt

    Wenn status='beendet' und Update erfolgreich:
      - lizenz_status wird auf 'cancelled' gesetzt
      - aktiv=0 wird auf die Entität gesetzt
      - Bei Verein: alle zugehörigen Benutzer werden ebenfalls deaktiviert (aktiv=0)
    """
    from datetime import datetime
    jetzt = datetime.utcnow().isoformat()
    tabelle = "vereine" if ist_verein else "benutzer"

    # Gültige Vorgänger-Zustände je Ziel-Status
    if status == "bestaetigt":
        vorgaenger = ("eingegangen",)
    elif status == "beendet":
        vorgaenger = ("eingegangen", "bestaetigt")
    else:
        vorgaenger = ("eingegangen",)  # Fallback: konservativ

    platzhalter = ",".join("?" * len(vorgaenger))

    with get_conn() as conn:
        # Atomisches bedingtes UPDATE — nur wenn Vorgänger-Status gültig
        cur = conn.execute(
            f"UPDATE {tabelle} "
            f"SET kuendigungsstatus=?, "
            f"    gekuendigt_zum=COALESCE(?, gekuendigt_zum), "
            f"    kuendigung_bestaetigung_am=? "
            f"WHERE id=? AND kuendigungsstatus IN ({platzhalter})",
            (status, vertragsende, jetzt, entity_id, *vorgaenger),
        )
        if cur.rowcount == 0:
            return False, "widerrufen_oder_ungueltig"

        # Status-Kaskade bei "beendet" — nur wenn obiges UPDATE erfolgreich war
        if status == "beendet":
            conn.execute(
                f"UPDATE {tabelle} SET lizenz_status='cancelled', aktiv=0 WHERE id=?",
                (entity_id,),
            )
            if ist_verein:
                conn.execute(
                    "UPDATE benutzer SET aktiv=0 WHERE verein_id=?",
                    (entity_id,),
                )

    # Audit-Log (darf nie blockieren)
    _audit_benutzer_id = None if ist_verein else entity_id
    _audit_details = (
        f"{'Verein' if ist_verein else 'Trainer'} id={entity_id} "
        f"kuendigungsstatus='{status}'"
        + (f" gekuendigt_zum={vertragsende}" if vertragsende else "")
        + (" → lizenz_status=cancelled, aktiv=0" if status == "beendet" else "")
    )
    audit_log_eintragen(
        _audit_benutzer_id,
        f"kuendigung_{status}",
        _audit_details,
    )
    return True, "ok"


def kuendigung_liste_laden(status_filter: str | None = None) -> list[dict]:
    """Gibt alle Kündigungen (Vereine + Trainer) für die Superadmin-Übersicht."""
    with get_conn() as conn:
        rows_v = conn.execute("""
            SELECT 'Verein' AS kundentyp, id AS entity_id, 1 AS ist_verein,
                   kundennummer, name, lizenztyp, lizenz_status,
                   kuendigung_eingegangen, gekuendigt_zum, kuendigungsstatus,
                   kuendigung_grund, kuendigung_bestaetigung_am
            FROM vereine
            WHERE kuendigung_eingegangen IS NOT NULL
        """).fetchall()
        rows_b = conn.execute("""
            SELECT 'Trainer' AS kundentyp, id AS entity_id, 0 AS ist_verein,
                   kundennummer,
                   COALESCE(benutzername, email) AS name,
                   lizenztyp, lizenz_status,
                   kuendigung_eingegangen, gekuendigt_zum, kuendigungsstatus,
                   kuendigung_grund, kuendigung_bestaetigung_am
            FROM benutzer
            WHERE kuendigung_eingegangen IS NOT NULL AND rolle='Trainer'
        """).fetchall()
    result = [dict(r) for r in rows_v] + [dict(r) for r in rows_b]
    if status_filter and status_filter != "Alle":
        result = [r for r in result if r.get("kuendigungsstatus") == status_filter]
    return sorted(result, key=lambda x: x.get("kuendigung_eingegangen") or "", reverse=True)


def pw_reset_anwenden(token: str, neues_passwort: str) -> bool:
    """Setzt Passwort via Reset-Token. Gibt True bei Erfolg, False bei ungültigem Token.

    Alles läuft atomar in einer einzigen Transaktion:
    - UPDATE mit WHERE-Bedingung auf das Token (kein vorheriger SELECT) → verhindert
      doppelten Token-Verbrauch: zwei gleichzeitige Aufrufe können nicht beide Zeilen
      aktualisieren, da SQLite exklusive Schreibsperren hat und der Token nach dem
      ersten Treffer auf NULL gesetzt ist.
    - RETURNING id liefert die benutzer_id ohne zweiten Lookup.
    - session_token_version wird inkrementiert → laufende Logins mit altem Passwort
      können danach keine gültige Session mehr erstellen.
    - Alle aktiven Sessions werden in derselben Transaktion invalidiert.
    """
    import datetime as _dt
    jetzt = _dt.datetime.utcnow().isoformat()
    with get_conn() as conn:
        row = conn.execute(
            """UPDATE benutzer
               SET passwort_hash         = ?,
                   pw_reset_token        = NULL,
                   pw_reset_ablauf       = NULL,
                   session_token_version = COALESCE(session_token_version, 0) + 1
               WHERE pw_reset_token = ?
                 AND (pw_reset_ablauf IS NULL OR pw_reset_ablauf > ?)
               RETURNING id""",
            (_pw_hash(neues_passwort), token, jetzt),
        ).fetchone()
        if not row:
            # Token nicht gefunden, bereits verbraucht oder abgelaufen
            return False
        sessions_benutzer_beenden(row[0], conn=conn)
    return True


def benutzername_reminder_laden(email: str) -> tuple[str, str, str] | None:
    """Gibt (benutzername, vorname, email_aus_db) zurück wenn E-Mail verifiziert, sonst None.
    Prüft email_verifiziert=1 (brauchen gültige Zieladresse), aber NICHT aktiv=1 —
    Spec §11: keine unnötige Blockade für Konten, die auf Admin-Freischaltung warten."""
    email_norm = normalize_email(email)
    with get_conn() as conn:
        row = conn.execute(
            """SELECT benutzername, vorname, email FROM benutzer
               WHERE LOWER(email)=? AND email_verifiziert=1""",
            (email_norm,),
        ).fetchone()
    if not row:
        return None
    # row[0] (benutzername) kann None sein — Aufrufer behandelt diesen Fall
    return row[0], row[1] or "Benutzer", row[2]


# --------------------------------------------------------------------------
# Server-seitige Sessions (Cookie-Persistenz)
# --------------------------------------------------------------------------

def session_erstellen(
    benutzer_id: int,
    idle_sek: int = 3600,
    max_sek: int = 86400,
    expected_token_version: int | None = None,
) -> str:
    """Erstellt eine neue DB-Session und gibt das Token zurück.

    expected_token_version (optional): der session_token_version-Wert, den
    auth.login() beim Passwort-Check gelesen hat. Wenn er nicht mehr mit dem
    aktuellen Wert in der DB übereinstimmt, wurde das Passwort während des
    Logins geändert — die Session-Erstellung wird dann abgebrochen (ValueError).
    Das verhindert den Login-Race: alte Credentials können keine neue Session
    erzeugen, nachdem das Passwort geändert wurde.
    """
    import datetime as _dt
    token  = _secrets.token_urlsafe(32)
    jetzt  = _dt.datetime.utcnow()
    ablauf = (jetzt + _dt.timedelta(seconds=max_sek)).isoformat()
    with get_conn() as conn:
        if expected_token_version is not None:
            row = conn.execute(
                "SELECT COALESCE(session_token_version, 0) FROM benutzer WHERE id=?",
                (benutzer_id,),
            ).fetchone()
            current_version = row[0] if row else 0
            if current_version != expected_token_version:
                raise ValueError(
                    f"session_token_version mismatch: expected {expected_token_version}, "
                    f"got {current_version}. Passwort wurde während des Logins geändert."
                )
        # token_version aus der DB lesen und in der Session speichern
        ver_row = conn.execute(
            "SELECT COALESCE(session_token_version, 0) FROM benutzer WHERE id=?",
            (benutzer_id,),
        ).fetchone()
        token_version = ver_row[0] if ver_row else 0
        conn.execute(
            """INSERT INTO sessions
               (token, benutzer_id, erstellt_am, letzte_aktivitaet, ablauf_am, aktiv, token_version)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (token, benutzer_id, jetzt.isoformat(), jetzt.isoformat(), ablauf, token_version),
        )
        # Soft-Cleanup: maximal _MAX_ACTIVE_SESSIONS parallele Sessions pro Benutzer.
        # Verhindert Ansammlung durch wiederholte externe Navigationen (z. B. Stripe-Checkout).
        # Die ältesten (nach letzte_aktivitaet) Sessions werden deaktiviert.
        # Andere Geräte mit neueren Sessions bleiben unberührt.
        # Hinweis: sessions hat kein id-Feld — rowid (SQLite-intern) als Schlüssel.
        _MAX_ACTIVE_SESSIONS = 5
        conn.execute(
            """UPDATE sessions SET aktiv=0
                WHERE benutzer_id=? AND aktiv=1
                  AND rowid NOT IN (
                    SELECT rowid FROM sessions
                     WHERE benutzer_id=? AND aktiv=1
                     ORDER BY letzte_aktivitaet DESC
                     LIMIT ?
                  )""",
            (benutzer_id, benutzer_id, _MAX_ACTIVE_SESSIONS),
        )
    return token


def session_validieren(token: str, idle_sek: int = 3600) -> dict | None:
    """Validiert Session-Token, aktualisiert letzte_aktivitaet.
    Gibt vollständiges user-dict zurück oder None (abgelaufen/ungültig/version-mismatch)."""
    import datetime as _dt
    jetzt = _dt.datetime.utcnow()
    with get_conn() as conn:
        row = conn.execute(
            """SELECT s.benutzer_id, s.letzte_aktivitaet, s.ablauf_am, b.aktiv,
                      b.email_verifiziert,
                      COALESCE(s.token_version, 0),
                      COALESCE(b.session_token_version, 0)
               FROM sessions s
               JOIN benutzer b ON b.id = s.benutzer_id
               WHERE s.token=? AND s.aktiv=1""",
            (token,),
        ).fetchone()
        if not row:
            return None
        bid, letzte, ablauf_str, b_aktiv, b_verif, sess_ver, benutzer_ver = (
            row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        )
        # Version mismatch → Passwort wurde seit Session-Erstellung geändert
        if sess_ver != benutzer_ver:
            conn.execute("UPDATE sessions SET aktiv=0 WHERE token=?", (token,))
            return None
        # Max-Lifetime prüfen
        if ablauf_str:
            try:
                if jetzt > _dt.datetime.fromisoformat(ablauf_str):
                    conn.execute("UPDATE sessions SET aktiv=0 WHERE token=?", (token,))
                    return None
            except (ValueError, TypeError):
                pass
        # Idle-Timeout prüfen
        if letzte:
            try:
                if (_dt.datetime.utcnow() - _dt.datetime.fromisoformat(letzte)).total_seconds() > idle_sek:
                    conn.execute("UPDATE sessions SET aktiv=0 WHERE token=?", (token,))
                    return None
            except (ValueError, TypeError):
                pass
        if not b_aktiv or not b_verif:
            return None
        # Letzte Aktivität aktualisieren
        conn.execute(
            "UPDATE sessions SET letzte_aktivitaet=? WHERE token=?",
            (jetzt.isoformat(), token),
        )
        user = _row(conn.execute(
            """SELECT b.*, v.name AS verein_name,
                      COALESCE(v.ist_technischer_mandant, 0) AS ist_technischer_mandant
               FROM benutzer b
               LEFT JOIN vereine v ON b.verein_id = v.id
               WHERE b.id=?""",
            (bid,),
        ).fetchone())
        return user


def session_token_aktiv(token: str) -> bool:
    """Prüft, ob ein Session-Token noch gültig ist: aktiv=1 UND token_version
    stimmt mit benutzer.session_token_version überein.

    Wird bei jedem Rerun der authentifizierten App aufgerufen, um nach einer
    Passwortänderung oder einem Admin-Reset sofort alle offenen Sessions zu sperren.
    Schreibt keine letzte_aktivitaet (das übernimmt check_session_timeout).

    Fail-closed: bei DB-Fehler wird False zurückgegeben — der Benutzer muss sich
    erneut anmelden. Das ist sicherer als im Zweifel Zugriff zu gewähren.
    """
    try:
        with get_conn() as conn:
            row = conn.execute(
                """SELECT s.aktiv, s.token_version,
                          COALESCE(b.session_token_version, 0)
                   FROM sessions s
                   JOIN benutzer b ON b.id = s.benutzer_id
                   WHERE s.token=?""",
                (token,),
            ).fetchone()
            if not row:
                return False
            aktiv, sess_ver, benutzer_ver = row[0], row[1], row[2]
            return bool(aktiv == 1 and sess_ver == benutzer_ver)
    except Exception:
        return False  # Fail-closed: DB-Fehler → Zugriff verweigern


def session_beenden(token: str) -> None:
    """Markiert Session als inaktiv (Logout)."""
    try:
        with get_conn() as conn:
            conn.execute("UPDATE sessions SET aktiv=0 WHERE token=?", (token,))
    except Exception:
        pass


def session_bereinigen() -> None:
    """Löscht abgelaufene und inaktive Sessions (Housekeeping)."""
    import datetime as _dt
    jetzt = _dt.datetime.utcnow().isoformat()
    try:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE ablauf_am < ? OR aktiv=0", (jetzt,)
            )
    except Exception:
        pass


# --------------------------------------------------------------------------
# Rechnungsadressen
# --------------------------------------------------------------------------

def rechnungsadresse_speichern(
    benutzer_id: int,
    firma: str | None,
    vorname: str,
    nachname: str,
    strasse: str,
    hausnummer: str,
    plz: str,
    ort: str,
    land: str,
    rechnung_email: str,
    telefon: str | None = None,
    ust_id: str | None = None,
) -> None:
    """Speichert oder aktualisiert die Rechnungsadresse eines Benutzers (UPSERT)."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO rechnungsadressen
                (benutzer_id, firma, vorname, nachname, strasse, hausnummer,
                 plz, ort, land, rechnung_email, telefon, ust_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(benutzer_id) DO UPDATE SET
                firma=excluded.firma, vorname=excluded.vorname, nachname=excluded.nachname,
                strasse=excluded.strasse, hausnummer=excluded.hausnummer, plz=excluded.plz,
                ort=excluded.ort, land=excluded.land, rechnung_email=excluded.rechnung_email,
                telefon=excluded.telefon, ust_id=excluded.ust_id
        """, (benutzer_id, firma, vorname, nachname, strasse, hausnummer,
              plz, ort, land, rechnung_email, telefon, ust_id))


def rechnungsadresse_laden(benutzer_id: int) -> dict | None:
    """Gibt die Rechnungsadresse eines Benutzers zurück oder None."""
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM rechnungsadressen WHERE benutzer_id=?", (benutzer_id,)
        ).fetchone())


# --------------------------------------------------------------------------
# Kundenverwaltung — Kundennummern, Audit-Log, Listen- und Detailabfragen
# --------------------------------------------------------------------------

def naechste_kundennummer() -> str:
    """Gibt die nächste freie Kundennummer im Format APH-XXXXXX zurück.

    Nur als Hilfsfunktion; für die Vergabe bitte kundennummer_vergeben_verein()
    oder kundennummer_vergeben_benutzer() verwenden — diese sind atomar.
    """
    with get_conn() as conn:
        _mv = conn.execute(
            "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
            "FROM vereine WHERE kundennummer LIKE 'APH-%'"
        ).fetchone()[0] or 0
        _mb = conn.execute(
            "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
            "FROM benutzer WHERE kundennummer LIKE 'APH-%'"
        ).fetchone()[0] or 0
        return f"APH-{max(_mv, _mb)+1:06d}"


def _naechste_kundennummer_in_conn(conn) -> str:
    """Berechnet die nächste Kundennummer innerhalb einer bestehenden Verbindung (atomar)."""
    mv = conn.execute(
        "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
        "FROM vereine WHERE kundennummer LIKE 'APH-%'"
    ).fetchone()[0] or 0
    mb = conn.execute(
        "SELECT MAX(CAST(SUBSTR(kundennummer,5) AS INTEGER)) "
        "FROM benutzer WHERE kundennummer LIKE 'APH-%'"
    ).fetchone()[0] or 0
    return f"APH-{max(mv, mb)+1:06d}"


def kundennummer_vergeben_verein(verein_id: int) -> str:
    """Vergibt eine neue Kundennummer an einen Verein — atomar in einer Transaktion.

    B2: Lese-/Schreib-/MAX-Berechnung erfolgen in einer einzigen DB-Verbindung,
    sodass keine race condition zwischen zwei parallelen Registrierungen entsteht.
    vereine ist die führende Vertragsquelle für Kundennummern.
    """
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT kundennummer FROM vereine WHERE id=?", (verein_id,)
        ).fetchone()
        if existing and existing[0]:
            return existing[0]
        kn = _naechste_kundennummer_in_conn(conn)
        conn.execute("UPDATE vereine SET kundennummer=? WHERE id=?", (kn, verein_id))
    return kn


def kundennummer_vergeben_benutzer(benutzer_id: int) -> str:
    """Vergibt eine neue Kundennummer an einen standalone-Benutzer — atomar.

    B2: Wie kundennummer_vergeben_verein, aber für Einzeltrainer ohne Verein.
    """
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT kundennummer FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone()
        if existing and existing[0]:
            return existing[0]
        kn = _naechste_kundennummer_in_conn(conn)
        conn.execute("UPDATE benutzer SET kundennummer=? WHERE id=?", (kn, benutzer_id))
    return kn


def audit_log_eintragen(
    benutzer_id: int | None,
    aktion: str,
    details: str = "",
    superadmin_id: int | None = None,
) -> None:
    """Schreibt einen Audit-Log-Eintrag.
    Niemals Passwörter, Tokens oder Secrets speichern!"""
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO audit_log (benutzer_id, aktion, details, superadmin_id)
                   VALUES (?, ?, ?, ?)""",
                (benutzer_id, aktion, details, superadmin_id),
            )
    except Exception:
        pass  # Audit darf die Hauptoperation nie blockieren


def kunden_liste_laden(
    such: str = "",
    filter_typ: str = "Alle",
    filter_status: str = "Alle",
    filter_lizenz: str = "Alle",
    filter_zahlungsstatus: str = "Alle",   # B3: neu
) -> list[dict]:
    """Lädt alle Kunden (Vereine + standalone Trainer) für Superadmin-Übersicht.
    Gibt eine flache Liste von dicts zurück, die beide Kundentypen vereinheitlicht.
    B3: zahlungsstatus in SELECT; filter_zahlungsstatus-Parameter ergänzt.
    """
    sql = """
        SELECT
            v.id                            AS verein_id,
            b.id                            AS benutzer_id,
            'Verein'                        AS kundentyp,
            v.kundennummer                  AS kundennummer,
            v.name                          AS vereinsname,
            b.vorname,
            b.nachname,
            b.benutzername,
            b.email,
            COALESCE(b.email_verifiziert,1) AS email_verifiziert,
            b.erstellt_am                   AS registriert_am,
            b.letzter_login,
            COALESCE(b.aktiv,1)             AS aktiv,
            b.gesperrt_bis,
            COALESCE(v.lizenztyp,'BASIC')        AS lizenztyp,
            COALESCE(v.lizenz_status,'trial')    AS lizenz_status,
            v.lizenz_bis,
            v.testphase_bis,
            v.vertragsbeginn,
            v.vertragsende,
            COALESCE(v.kuendigungsstatus,'aktiv') AS kuendigungsstatus,
            v.kuendigung_eingegangen,
            v.gekuendigt_zum,
            COALESCE(v.gesperrt,0)          AS verein_gesperrt,
            v.zahlungsstatus,
            b.telefon
        FROM vereine v
        LEFT JOIN benutzer b
               ON b.verein_id = v.id
              AND b.rolle = 'Vereinsadmin'
        WHERE COALESCE(v.ist_technischer_mandant, 0) = 0

        UNION ALL

        -- Trainer-Kunden: Vertrags-/Lizenz-/Stripe-Felder kommen aus dem technischen Mandant (vereine v2),
        -- personenbezogene Daten aus benutzer (b). COALESCE bevorzugt v2 gegenüber b.
        SELECT
            NULL                            AS verein_id,
            b.id                            AS benutzer_id,
            'Trainer'                       AS kundentyp,
            b.kundennummer,
            NULL                            AS vereinsname,
            b.vorname,
            b.nachname,
            b.benutzername,
            b.email,
            COALESCE(b.email_verifiziert,1) AS email_verifiziert,
            b.erstellt_am                   AS registriert_am,
            b.letzter_login,
            COALESCE(b.aktiv,1)             AS aktiv,
            b.gesperrt_bis,
            COALESCE(v2.lizenztyp,  b.lizenztyp,  'BASIC')        AS lizenztyp,
            COALESCE(v2.lizenz_status, b.lizenz_status, 'trial')   AS lizenz_status,
            COALESCE(v2.lizenz_bis,    b.lizenz_bis)               AS lizenz_bis,
            COALESCE(v2.testphase_bis, b.testphase_bis)            AS testphase_bis,
            COALESCE(v2.vertragsbeginn, b.vertragsbeginn)          AS vertragsbeginn,
            COALESCE(v2.vertragsende,   b.vertragsende)            AS vertragsende,
            COALESCE(v2.kuendigungsstatus, b.kuendigungsstatus, 'aktiv') AS kuendigungsstatus,
            COALESCE(v2.kuendigung_eingegangen, b.kuendigung_eingegangen) AS kuendigung_eingegangen,
            COALESCE(v2.gekuendigt_zum, b.gekuendigt_zum)          AS gekuendigt_zum,
            0                               AS verein_gesperrt,
            v2.zahlungsstatus,
            b.telefon
        FROM benutzer b
        LEFT JOIN vereine v2
               ON v2.id = b.verein_id
              AND COALESCE(v2.ist_technischer_mandant, 0) = 1
        -- Trainer-Kunden: Rolle='Trainer' UND (kein Verein ODER technischer Mandant)
        WHERE b.rolle = 'Trainer'
          AND (
              b.verein_id IS NULL
              OR EXISTS (
                  SELECT 1 FROM vereine v3
                  WHERE v3.id = b.verein_id
                    AND COALESCE(v3.ist_technischer_mandant, 0) = 1
              )
          )

        ORDER BY kundennummer
    """
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]

    such_l = such.strip().lower()
    result = []
    for r in rows:
        # Suchfilter
        if such_l:
            felder = [
                (r.get("kundennummer") or "").lower(),
                (r.get("vorname") or "").lower(),
                (r.get("nachname") or "").lower(),
                (r.get("vereinsname") or "").lower(),
                (r.get("benutzername") or "").lower(),
                (r.get("email") or "").lower(),
            ]
            if not any(such_l in f for f in felder):
                continue
        # Kundentyp-Filter
        if filter_typ != "Alle" and r["kundentyp"] != filter_typ:
            continue
        # Accountstatus-Filter
        if filter_status != "Alle":
            if filter_status == "Aktiv" and not r["aktiv"]:
                continue
            if filter_status == "Deaktiviert" and r["aktiv"]:
                continue
            if filter_status == "E-Mail nicht bestätigt" and r["email_verifiziert"]:
                continue
            if filter_status == "Gesperrt" and not r.get("verein_gesperrt"):
                continue
            if filter_status == "Trial" and r.get("lizenz_status") != "trial":
                continue
        # Lizenzstatus-Filter
        if filter_lizenz != "Alle" and r["lizenz_status"] != filter_lizenz:
            continue
        # Zahlungsstatus-Filter (B3)
        if filter_zahlungsstatus != "Alle":
            if (r.get("zahlungsstatus") or "") != filter_zahlungsstatus:
                continue
        result.append(r)
    return result


def kunde_vollstaendig_laden(
    verein_id: int | None = None,
    benutzer_id: int | None = None,
) -> dict | None:
    """Lädt alle Daten eines Kunden: benutzer + verein + rechnungsadresse + lizenz.
    Genau ein von verein_id oder benutzer_id muss angegeben werden."""
    with get_conn() as conn:
        if verein_id:
            v = _row(conn.execute("SELECT * FROM vereine WHERE id=?", (verein_id,)).fetchone())
            if not v:
                return None
            b = _row(conn.execute(
                "SELECT * FROM benutzer WHERE verein_id=? AND rolle='Vereinsadmin' LIMIT 1",
                (verein_id,),
            ).fetchone())
        else:
            b = _row(conn.execute("SELECT * FROM benutzer WHERE id=?", (benutzer_id,)).fetchone())
            if not b:
                return None
            if b.get("verein_id"):
                _v_raw = _row(conn.execute(
                    "SELECT * FROM vereine WHERE id=?", (b.get("verein_id"),)
                ).fetchone())
                # Technischer Mandant: wird als v zurückgegeben — ist_technischer_mandant=1
                # signalisiert der UI, dass es ein Trainer-Konto ist (keine Vereinsstruktur),
                # aber vereine ist die führende Datenquelle für Vertrag/Lizenz/Stripe.
                v = _v_raw  # v.get("ist_technischer_mandant") in UI auswerten
            else:
                v = None

        ra = _row(conn.execute(
            "SELECT * FROM rechnungsadressen WHERE benutzer_id=?", (b["id"] if b else None,)
        ).fetchone()) if b else None

        audit = [dict(r) for r in conn.execute(
            "SELECT al.*, sb.vorname AS sa_vorname, sb.nachname AS sa_nachname "
            "FROM audit_log al "
            "LEFT JOIN benutzer sb ON sb.id = al.superadmin_id "
            "WHERE al.benutzer_id=? ORDER BY al.erstellt_am DESC LIMIT 20",
            (b["id"] if b else None,),
        ).fetchall()] if b else []

    return {
        "verein":          v,
        "benutzer":        b,
        "rechnungsadresse": ra,
        "audit":           audit,
    }


def superadmin_email_aendern(
    benutzer_id: int,
    neue_email: str,
    superadmin_id: int,
) -> str:
    """Ändert die E-Mail eines Benutzers (Superadmin).
    Normalisiert, prüft Duplikat, setzt email_verifiziert=0, erstellt neuen Token.
    Gibt den Verifikationstoken zurück (für E-Mail-Versand).
    Wirft ValueError bei Duplikat."""
    import sqlite3 as _sq
    email_norm = normalize_email(neue_email)
    with get_conn() as conn:
        dup = conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(email)=? AND id!=?",
            (email_norm, benutzer_id),
        ).fetchone()
        if dup:
            raise ValueError(f"Die E-Mail-Adresse '{email_norm}' ist bereits vergeben.")
        alte_email = (conn.execute(
            "SELECT email FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone() or [None])[0]
        conn.execute(
            "UPDATE benutzer SET email=?, email_verifiziert=0, email_token=NULL WHERE id=?",
            (email_norm, benutzer_id),
        )
    token = email_token_erzeugen(benutzer_id)
    audit_log_eintragen(
        benutzer_id,
        "email_geaendert",
        f"alt={alte_email} → neu={email_norm}",
        superadmin_id,
    )
    return token


def superadmin_benutzername_aendern(
    benutzer_id: int,
    neuer_name: str,
    superadmin_id: int,
) -> None:
    """Ändert den Benutzernamen. Prüft auf Duplikate. Loggt Änderung.
    Wirft ValueError bei Duplikat."""
    neuer_name = neuer_name.strip()
    with get_conn() as conn:
        dup = conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(benutzername)=LOWER(?) AND id!=?",
            (neuer_name, benutzer_id),
        ).fetchone()
        if dup:
            raise ValueError(f"Der Benutzername '{neuer_name}' ist bereits vergeben.")
        alter = (conn.execute(
            "SELECT benutzername FROM benutzer WHERE id=?", (benutzer_id,)
        ).fetchone() or [None])[0]
        conn.execute(
            "UPDATE benutzer SET benutzername=? WHERE id=?", (neuer_name, benutzer_id)
        )
    audit_log_eintragen(
        benutzer_id, "benutzername_geaendert",
        f"alt={alter} → neu={neuer_name}", superadmin_id,
    )


def vertragsfelder_setzen(
    verein_id: int,
    *,
    vertragsbeginn: str | None = None,
    vertragsende: str | None = None,
    kuendigung_eingegangen: str | None = None,
    gekuendigt_zum: str | None = None,
    kuendigungsstatus: str | None = None,
    superadmin_id: int | None = None,
) -> None:
    """Setzt Vertragsdaten für einen Verein. Loggt Änderung."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE vereine SET
                   vertragsbeginn        = COALESCE(?, vertragsbeginn),
                   vertragsende          = COALESCE(?, vertragsende),
                   kuendigung_eingegangen = COALESCE(?, kuendigung_eingegangen),
                   gekuendigt_zum        = COALESCE(?, gekuendigt_zum),
                   kuendigungsstatus     = COALESCE(?, kuendigungsstatus)
               WHERE id=?""",
            (vertragsbeginn, vertragsende, kuendigung_eingegangen,
             gekuendigt_zum, kuendigungsstatus, verein_id),
        )
    audit_log_eintragen(
        None, "vertragsdaten_geaendert",
        f"verein_id={verein_id} status={kuendigungsstatus}",
        superadmin_id,
    )


def kundenstamm_aendern(
    benutzer_id: int,
    verein_id: int | None,
    *,
    vorname: str | None = None,
    nachname: str | None = None,
    telefon: str | None = None,
    vereinsname: str | None = None,
    ansprechpartner: str | None = None,
    aktiv: int | None = None,
    superadmin_id: int | None = None,
) -> None:
    """Ändert Kundenstammdaten (Benutzer + optional Verein). Loggt Änderung."""
    with get_conn() as conn:
        if vorname is not None or nachname is not None or telefon is not None:
            conn.execute(
                """UPDATE benutzer SET
                       vorname  = COALESCE(?, vorname),
                       nachname = COALESCE(?, nachname),
                       telefon  = COALESCE(?, telefon),
                       aktiv    = COALESCE(?, aktiv)
                   WHERE id=?""",
                (vorname, nachname, telefon, aktiv, benutzer_id),
            )
        if verein_id and (vereinsname is not None or ansprechpartner is not None):
            conn.execute(
                """UPDATE vereine SET
                       name            = COALESCE(?, name),
                       ansprechpartner = COALESCE(?, ansprechpartner),
                       aktiv           = COALESCE(?, aktiv)
                   WHERE id=?""",
                (vereinsname, ansprechpartner, aktiv, verein_id),
            )
    audit_log_eintragen(
        benutzer_id, "kundendaten_geaendert",
        f"verein_id={verein_id} vorname={vorname} nachname={nachname}",
        superadmin_id,
    )


# ── SCHRITT 9 — Datensicherheit, Persistenz, Mandantentrennung ────────────────

def spieler_mandant_pruefen(
    spieler_id: int,
    benutzer_id: int | None,
    rolle: str,
    verein_id: int | None,
) -> bool:
    """
    IDOR-Schutz: prüft ob spieler_id zum aktuellen Mandanten gehört.

    Superadmin  → immer erlaubt.
    Vereinsadmin → Spieler muss zur selben verein_id gehören.
    Trainer      → Spieler muss trainer_id oder verein_id des Trainers besitzen.

    Gibt False zurück, wenn der Spieler nicht existiert oder nicht zugehörig.
    """
    if rolle == "Superadmin":
        return True
    with get_conn() as conn:
        row = conn.execute(
            "SELECT trainer_id, verein_id FROM spieler WHERE id=?",
            (spieler_id,),
        ).fetchone()
    if not row:
        return False
    sp_verein  = row["verein_id"]
    sp_trainer = row["trainer_id"]
    if rolle == "Vereinsadmin":
        return verein_id is not None and sp_verein == verein_id
    # Trainer: eigener Spieler ODER Spieler im selben Verein
    return sp_trainer == benutzer_id or (
        verein_id is not None and sp_verein == verein_id
    )


def backup_status_laden() -> dict:
    """
    Gibt Backup-Status für die Datensicherheitsanzeige im Superadmin-Bereich zurück.
    Liest aus dem konfigurierten Backup-Verzeichnis (uploads/backups/).
    Keine sensiblen Pfade oder Secrets werden zurückgegeben.
    """
    import datetime as _dt
    from pathlib import Path as _P

    data_dir   = _P(_os.environ.get("ATHLETIK_DATA_DIR", str(_P(DB_PATH).parent)))
    backup_dir = data_dir / "uploads" / "backups"

    result: dict = {
        "db_erreichbar":             False,
        "db_groesse_kb":             None,
        "backup_anzahl":             0,
        "letztes_backup_datum":      None,
        "letztes_backup_groesse_kb": None,
        "backups":                   [],
    }

    # DB-Erreichbarkeit prüfen — Datei muss existieren UND lesbar sein
    # (SQLite erzeugt sonst eine neue leere Datei, was kein echter Betriebszustand wäre)
    _db_path = _P(DB_PATH)
    if _db_path.exists():
        try:
            with get_conn() as conn:
                conn.execute("SELECT 1")
            result["db_erreichbar"] = True
            result["db_groesse_kb"] = round(_db_path.stat().st_size / 1024, 1)
        except Exception:
            pass

    # Backup-Verzeichnis auslesen
    try:
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("athletik_*.db"), reverse=True)
            result["backup_anzahl"] = len(backups)
            if backups:
                latest = backups[0]
                mtime  = _dt.datetime.fromtimestamp(latest.stat().st_mtime)
                result["letztes_backup_datum"]      = mtime.strftime("%d.%m.%Y %H:%M")
                result["letztes_backup_groesse_kb"] = round(
                    latest.stat().st_size / 1024, 1
                )
                result["backups"] = [
                    {
                        "name":       f.name,
                        "datum":      _dt.datetime.fromtimestamp(
                                          f.stat().st_mtime
                                      ).strftime("%d.%m.%Y %H:%M"),
                        "groesse_kb": round(f.stat().st_size / 1024, 1),
                    }
                    for f in backups[:10]
                ]
    except Exception:
        pass

    return result


def kunde_zusammenfassung_laden(verein_id: int | None, benutzer_id: int) -> dict:
    """
    Liefert eine Zusammenfassung der Daten eines Kunden für den Lösch-Dialog.
    Tenant-sicher: nur Daten des angegebenen verein_id/benutzer_id.
    """
    with get_conn() as conn:
        if verein_id:
            n_spieler = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (verein_id,)
            ).fetchone()[0]
            n_tests = 0
            for tbl in [
                "sprint_test", "sprung_test", "agilitaet_test", "ausdauer_test",
                "fms_test", "y_balance_test", "kraft_test", "spiro_test",
            ]:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE spieler_id IN "
                        f"(SELECT id FROM spieler WHERE verein_id=?)",
                        (verein_id,),
                    ).fetchone()
                    n_tests += row[0] if row else 0
                except Exception:
                    pass
            n_plaene = 0
            try:
                n_plaene = conn.execute(
                    "SELECT COUNT(*) FROM trainingsplan_versionen tv "
                    "JOIN spieler sp ON tv.spieler_id=sp.id WHERE sp.verein_id=?",
                    (verein_id,),
                ).fetchone()[0]
            except Exception:
                pass
            row = conn.execute(
                "SELECT lizenz_status FROM vereine WHERE id=?", (verein_id,)
            ).fetchone()
            vertragsstatus = row[0] if row else "—"
        else:
            # Standalone-Trainer: Spieler sind über trainer_id verknüpft (nicht benutzer_id —
            # die Spalte existiert nicht in der spieler-Tabelle)
            try:
                n_spieler = conn.execute(
                    "SELECT COUNT(*) FROM spieler WHERE trainer_id=?", (benutzer_id,)
                ).fetchone()[0]
            except Exception:
                n_spieler = 0
            n_tests = 0
            for tbl in [
                "sprint_test", "sprung_test", "agilitaet_test", "ausdauer_test",
                "fms_test", "y_balance_test", "kraft_test",
            ]:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE spieler_id IN "
                        f"(SELECT id FROM spieler WHERE trainer_id=?)",
                        (benutzer_id,),
                    ).fetchone()
                    n_tests += row[0] if row else 0
                except Exception:
                    pass
            n_plaene = 0
            try:
                n_plaene = conn.execute(
                    "SELECT COUNT(*) FROM trainingsplan_versionen tv "
                    "JOIN spieler sp ON tv.spieler_id=sp.id WHERE sp.trainer_id=?",
                    (benutzer_id,),
                ).fetchone()[0]
            except Exception:
                pass
            vertragsstatus = "Einzeltrainer"
        # ── Rechnungsdaten / Sessions / Weitere Zählungen ────────────────────
        n_rechnungsadressen = 0
        n_sessions          = 0
        n_tp_eintraege      = 0
        n_audit_eintraege   = 0
        n_benachrichtigungen = 0
        n_push_tokens       = 0
        alle_bid_list: list[int] = []
        if verein_id:
            alle_bid_list = [
                r[0] for r in conn.execute(
                    "SELECT id FROM benutzer WHERE verein_id=? OR id=?",
                    (verein_id, benutzer_id),
                ).fetchall()
            ]
        else:
            alle_bid_list = [benutzer_id]

        for _bid in alle_bid_list:
            try:
                n_rechnungsadressen += conn.execute(
                    "SELECT COUNT(*) FROM rechnungsadressen WHERE benutzer_id=?", (_bid,)
                ).fetchone()[0]
            except Exception:
                pass
            try:
                n_sessions += conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE benutzer_id=?", (_bid,)
                ).fetchone()[0]
            except Exception:
                pass
            try:
                n_audit_eintraege += conn.execute(
                    "SELECT COUNT(*) FROM audit_log WHERE benutzer_id=?", (_bid,)
                ).fetchone()[0]
            except Exception:
                pass
            try:
                n_benachrichtigungen += conn.execute(
                    "SELECT COUNT(*) FROM benachrichtigungen WHERE benutzer_id=?", (_bid,)
                ).fetchone()[0]
            except Exception:
                pass
            try:
                n_push_tokens += conn.execute(
                    "SELECT COUNT(*) FROM push_tokens WHERE benutzer_id=?", (_bid,)
                ).fetchone()[0]
            except Exception:
                pass

        # Trainingsplan-Einträge
        # spieler.verein_id → Verein-Kunden; spieler.trainer_id → Standalone-Trainer
        # (spieler.benutzer_id existiert nicht im Schema)
        try:
            _sp_filter = "verein_id=?" if verein_id else "trainer_id=?"
            _sp_val    = verein_id if verein_id else benutzer_id
            n_tp_eintraege = conn.execute(
                f"SELECT COUNT(*) FROM trainingsplan te "
                f"JOIN spieler sp ON te.spieler_id=sp.id "
                f"WHERE sp.{_sp_filter}",
                (_sp_val,),
            ).fetchone()[0]
        except Exception:
            pass

        # Logo vorhanden?
        logo_vorhanden = False
        try:
            if verein_id:
                logo_vorhanden = bool(conn.execute(
                    "SELECT 1 FROM vereine WHERE id=? AND logo IS NOT NULL", (verein_id,)
                ).fetchone())
            else:
                logo_vorhanden = bool(conn.execute(
                    "SELECT 1 FROM benutzer WHERE id=? AND foto IS NOT NULL", (benutzer_id,)
                ).fetchone())
        except Exception:
            pass

        return {
            "n_spieler":          n_spieler,
            "n_tests":            n_tests,
            "n_plaene":           n_plaene,
            "n_tp_eintraege":     n_tp_eintraege,
            "n_rechnungsadressen": n_rechnungsadressen,
            "n_sessions":         n_sessions,
            "n_audit_eintraege":  n_audit_eintraege,
            "n_benachrichtigungen": n_benachrichtigungen,
            "n_push_tokens":      n_push_tokens,
            "n_benutzerkonten":   len(alle_bid_list),
            "logo_vorhanden":     logo_vorhanden,
            "vertragsstatus":     vertragsstatus,
        }


def kunde_loeschen(
    verein_id: int | None,
    benutzer_id: int,
    superadmin_id: int | None = None,
) -> dict:
    """
    Löscht einen Kunden endgültig (Superadmin-only). Atomar — alles in einer Transaktion.

    Aufbewahrungspflichtige Daten (Rechnungen, Rechnungsadressen, Audit-Log,
    Login-Log) werden anonymisiert statt gelöscht.

    Tenant-sicher: es werden ausschließlich Daten des angegebenen
    verein_id/benutzer_id entfernt. Fremde Mandantendaten bleiben unberührt.

    Gibt dict mit {"n_spieler": int, "n_benutzer": int} zurück.
    Wirft bei Fehler eine Exception — kein stilles Scheitern.
    """

    with get_conn() as conn:
        # PRAGMA foreign_keys = ON ist bereits durch get_conn() gesetzt und bleibt aktiv.
        # Alle Abhängigkeiten werden in der korrekten FK-konformen Reihenfolge behandelt.

        # ── Schritt 1: IDs sammeln ────────────────────────────────────────────
        if verein_id:
            spieler_ids = [
                r[0] for r in conn.execute(
                    "SELECT id FROM spieler WHERE verein_id=?", (verein_id,)
                ).fetchall()
            ]
            alle_benutzer_ids = [
                r[0] for r in conn.execute(
                    "SELECT id FROM benutzer WHERE verein_id=? OR id=?",
                    (verein_id, benutzer_id),
                ).fetchall()
            ]
        else:
            # Standalone-Trainer: Spieler über trainer_id verknüpft (nicht benutzer_id —
            # diese Spalte existiert nicht in der spieler-Tabelle)
            spieler_ids = [
                r[0] for r in conn.execute(
                    "SELECT id FROM spieler WHERE trainer_id=?", (benutzer_id,)
                ).fetchall()
            ]
            alle_benutzer_ids = [benutzer_id]

        n_spieler = len(spieler_ids)

        # ── Schritt 2: Spieler-Abhängigkeiten löschen (Kind vor Eltern) ──────
        for sid in spieler_ids:
            # kraft_test_versuch → kraft_test → spieler
            try:
                conn.execute(
                    "DELETE FROM kraft_test_versuch WHERE kraft_test_id IN "
                    "(SELECT id FROM kraft_test WHERE spieler_id=?)", (sid,)
                )
            except Exception:
                pass
            # spiro_stufe / spiro_nachbelastung → spiro_test → spieler
            try:
                conn.execute(
                    "DELETE FROM spiro_stufe WHERE spiro_test_id IN "
                    "(SELECT id FROM spiro_test WHERE spieler_id=?)", (sid,)
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "DELETE FROM spiro_nachbelastung WHERE spiro_test_id IN "
                    "(SELECT id FROM spiro_test WHERE spieler_id=?)", (sid,)
                )
            except Exception:
                pass
            # Alle weiteren spieler-direkten Tabellen
            for _tbl in [
                "spiro_test", "verletzung", "anthropometrie", "agilitaet_test",
                "ausdauer_test", "sprint_test", "sprung_test", "fms_test",
                "y_balance_test", "kraft_test", "trainerbeobachtung",
                "periodisierung", "trainingsplan", "trainingsplan_versionen",
                "spieler_zuweisung_log",
            ]:
                try:
                    conn.execute(f"DELETE FROM {_tbl} WHERE spieler_id=?", (sid,))
                except Exception:
                    pass
            conn.execute("DELETE FROM spieler WHERE id=?", (sid,))

        # ── Schritt 3: Benutzer-Abhängigkeiten bereinigen (FK=ON konform) ────
        # Reihenfolge: NOT-NULL-NO-ACTION-FKs zuerst, dann NULLABLE-Felder,
        # dann DELETE benutzer (CASCADE + SET NULL FKs feuern automatisch).
        for bid in alle_benutzer_ids:
            # sessions.benutzer_id: NOT NULL, ON DELETE=NO ACTION → explizit löschen
            conn.execute("DELETE FROM sessions WHERE benutzer_id=?", (bid,))

            # rechnungsadressen.benutzer_id: NOT NULL, ON DELETE=NO ACTION
            # Rechnungsadressen können vollständig gelöscht werden —
            # gesetzliche Aufbewahrungspflicht (HGB §257) gilt für Rechnungen (rechnungen-Tabelle),
            # nicht für Rechnungsadressen (Kontaktdaten des Kunden).
            conn.execute("DELETE FROM rechnungsadressen WHERE benutzer_id=?", (bid,))

            # audit_log: benutzer_id + superadmin_id sind NULLABLE, ON DELETE=NO ACTION
            # → Datensatz bleibt als Nachweis erhalten, PII-Bezug wird gekappt
            try:
                conn.execute(
                    "UPDATE audit_log SET benutzer_id=NULL WHERE benutzer_id=?", (bid,)
                )
            except Exception:
                pass
            try:
                conn.execute(
                    "UPDATE audit_log SET superadmin_id=NULL WHERE superadmin_id=?", (bid,)
                )
            except Exception:
                pass

            # login_log.email: vor benutzer-DELETE anonymisieren (danach nicht mehr auffindbar)
            # login_log.benutzer_id ist ON DELETE=SET NULL (CASCADE) → wird automatisch genullt
            try:
                conn.execute(
                    "UPDATE login_log SET email='[gelöscht]' WHERE benutzer_id=?", (bid,)
                )
            except Exception:
                pass

        # DELETE benutzer: CASCADE → benachrichtigungen auto-gelöscht;
        # SET NULL → login_log.benutzer_id, spieler_zuweisung_log.ausfuehrender_id auto-genullt
        if verein_id:
            conn.execute("DELETE FROM benutzer WHERE verein_id=?", (verein_id,))
        conn.execute("DELETE FROM benutzer WHERE id=?", (benutzer_id,))

        # ── Schritt 4: Verein anonymisieren (NICHT löschen) ──────────────────
        # rechnungen.verein_id ist NOT NULL, ON DELETE=NO ACTION →
        # physisches Löschen des Vereins würde FK-Violation auslösen solange
        # Rechnungen existieren. Lösung: Verein anonymisieren (PII entfernen,
        # Zeile bleibt für FK-Integrität). Rechnungen bleiben vollständig
        # erhalten (Aufbewahrungspflicht 10 Jahre).
        # Der anonymisierte Verein erscheint nicht in der Kundenliste, da
        # kunden_liste_laden() einen INNER JOIN mit benutzer macht
        # (alle benutzer wurden in Schritt 3/4 gelöscht).
        if verein_id:
            # lizenz_warn_log.verein_id: NOT NULL, ON DELETE=CASCADE →
            # würde bei Vereinslöschung auto-gelöscht; da wir nicht löschen,
            # manuell entfernen (keine Aufbewahrungspflicht).
            try:
                conn.execute("DELETE FROM lizenz_warn_log WHERE verein_id=?", (verein_id,))
            except Exception:
                pass

            # login_log.verein_id: NULLABLE, ON DELETE=SET NULL →
            # würde bei Vereinslöschung auto-genullt; da wir nicht löschen,
            # manuell nullen.
            try:
                conn.execute(
                    "UPDATE login_log SET verein_id=NULL WHERE verein_id=?", (verein_id,)
                )
            except Exception:
                pass

            # Verein anonymisieren: alle personenbezogenen Felder leeren,
            # Zeile bleibt für FK-Referenzen aus rechnungen erhalten.
            conn.execute(
                """UPDATE vereine SET
                       name        = '[Archiviert]',
                       aktiv       = 0,
                       gesperrt    = 1,
                       lizenz_status = 'geloescht',
                       logo_blob   = NULL,
                       farbe_primaer  = NULL,
                       farbe_sekundaer = NULL,
                       ansprechpartner = '',
                       email       = '',
                       telefon     = '',
                       adresse     = '',
                       homepage    = '',
                       stripe_customer_id      = NULL,
                       stripe_subscription_id  = NULL,
                       registrier_code         = NULL,
                       kundennummer            = '[gelöscht]'
                   WHERE id = ?""",
                (verein_id,),
            )

    return {"n_spieler": n_spieler, "n_benutzer": len(alle_benutzer_ids)}


def db_backup_erstellen() -> tuple[bool, str]:
    """
    Erstellt ein Datenbank-Backup aus dem laufenden Prozess.
    Ruft tools/backup.py als Subprocess auf (kein Import-Coupling).
    Gibt (True, meldung) oder (False, fehlermeldung) zurück.
    """
    import subprocess
    from pathlib import Path as _P

    backup_script = _P(__file__).parent / "tools" / "backup.py"
    if not backup_script.exists():
        return False, "Backup-Skript nicht gefunden (tools/backup.py)"
    try:
        proc = subprocess.run(
            ["python3", str(backup_script)],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode == 0:
            return True, "Backup erfolgreich erstellt"
        err = (proc.stderr or proc.stdout or "Unbekannter Fehler").strip()
        err_short = err.splitlines()[-1] if err else "Unbekannter Fehler"
        return False, err_short
    except subprocess.TimeoutExpired:
        return False, "Timeout — Backup dauerte zu lange (>120 s)"
    except Exception as exc:
        return False, str(exc)
