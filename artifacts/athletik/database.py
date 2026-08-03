"""
Database layer — single source of truth for all SQLite operations.
Uses a context manager for every connection so files are never left open.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

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
        """)
    # Migrationen: neue Spalten und Indizes für bestehende Datenbanken nachträglich anlegen
    _migrate_spieler_columns()
    _migrate_db()
    _migrate_multitenant()
    _migrate_szl_actor_fk()  # Korrigiert ON DELETE SET NULL auf ausfuehrender_id
    _create_indexes()


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
            ("ausfuehrung",    "TEXT DEFAULT 'kontrolliert'"),
        ]:
            try:
                conn.execute(f"ALTER TABLE trainingsplan ADD COLUMN {_col} {_typ}")
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
        for tabelle in [
            "verletzung", "anthropometrie", "agilitaet_test", "ausdauer_test",
            "sprint_test", "sprung_test", "fms_test", "y_balance_test",
            "trainingsplan", "periodisierung", "trainerbeobachtung", "kraft_test",
            "spieler_zuweisung_log",
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
    with get_conn() as conn:
        conn.execute("DELETE FROM trainingsplan WHERE spieler_id=?", (spieler_id,))


def trainingsplan_eintrag_speichern(spieler_id, datum, woche, bereich, uebung, saetze, wdh,
                                    haeufigkeit, tag: int = 1,
                                    pause_sekunden: int = 90,
                                    ausfuehrung: str = "kontrolliert"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trainingsplan (spieler_id,datum,woche,bereich,uebung,saetze,wiederholungen,"
            "haeufigkeit,status,tag,pause_sekunden,ausfuehrung) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (spieler_id, datum, woche, bereich, uebung, saetze, wdh, haeufigkeit, "offen",
             tag, pause_sekunden, ausfuehrung),
        )


def trainingsplan_laden(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT bereich,uebung,saetze,wiederholungen,haeufigkeit,woche,"
            "COALESCE(tag,1) as tag,"
            "COALESCE(pause_sekunden,90) as pause_sekunden,"
            "COALESCE(ausfuehrung,'kontrolliert') as ausfuehrung "
            "FROM trainingsplan WHERE spieler_id=? ORDER BY woche,tag,id",
            (spieler_id,),
        ).fetchall())


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


# ==========================================================================
# Multi-Tenant: Migration bestehender Datenbanken
# ==========================================================================

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


# ==========================================================================
# Multi-Tenant Hilfsfunktionen
# ==========================================================================

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


# ==========================================================================
# Vereine
# ==========================================================================

def vereine_laden() -> list[dict]:
    with get_conn() as conn:
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

def verein_registrieren(
    vereinsname: str,
    vorname: str,
    nachname: str,
    email: str,
    passwort: str,
) -> tuple[int, int]:
    """Erstellt einen neuen Verein mit Vereinsadmin und startet 30-Tage-Testphase.
    Gibt (verein_id, benutzer_id) zurück."""
    import datetime as _dt
    testphase_bis = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()

    # Prüfen ob E-Mail bereits vergeben
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM benutzer WHERE email=?", (email.strip().lower(),)
        ).fetchone()
        if existing:
            raise ValueError("Diese E-Mail-Adresse ist bereits registriert.")

    verein_id = verein_speichern(vereinsname)
    # Testphase explizit setzen (verein_speichern setzt sie bereits)
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET testphase_bis=?, lizenz_status='trial', lizenztyp='BASIC' WHERE id=?",
            (testphase_bis, verein_id),
        )

    benutzer_id = benutzer_speichern(
        verein_id, vorname, nachname, email.strip().lower(), passwort, "Vereinsadmin"
    )
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
    """Lädt alle Lizenzdaten eines Vereins (für get_lizenz_info())."""
    with get_conn() as conn:
        return _row(conn.execute(
            """SELECT id, name, aktiv, lizenztyp, lizenz_bis, lizenz_status,
                      testphase_bis, gesperrt, stripe_customer_id,
                      stripe_subscription_id, zahlungsstatus
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
                      stripe_subscription_id, zahlungsstatus
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


# ==========================================================================
# Benutzer
# ==========================================================================

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
    verein_id: int,
    vorname: str,
    nachname: str,
    email: str,
    passwort: str,
) -> int:
    """Trainer-Selbstregistrierung über Vereinsauswahl.
    Gibt benutzer_id zurück. Wirft ValueError bei ungültigem Verein / doppelter E-Mail.
    Der Trainer startet als inaktiv=0 (muss vom Vereinsadmin freigeschaltet werden)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM vereine WHERE id=? AND aktiv=1", (verein_id,)
        ).fetchone()
        if not row:
            raise ValueError("Ungültiger Verein. Bitte wähle deinen Verein aus der Liste.")
        existing = conn.execute(
            "SELECT id FROM benutzer WHERE LOWER(email)=LOWER(?)", (email,)
        ).fetchone()
        if existing:
            raise ValueError("Diese E-Mail-Adresse ist bereits registriert.")
        cur = conn.execute(
            """INSERT INTO benutzer
                   (verein_id, vorname, nachname, email, passwort_hash, rolle, aktiv)
               VALUES (?, ?, ?, ?, ?, 'Trainer', 0)""",
            (verein_id, vorname, nachname, email, _pw_hash(passwort)),
        )
        return cur.lastrowid


def registrier_code_laden(verein_id: int) -> str | None:
    """Gibt den aktuellen Beitrittscode des Vereins zurück."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT registrier_code FROM vereine WHERE id=?", (verein_id,)
        ).fetchone()
        return row[0] if row else None


def registrier_code_regenerieren(verein_id: int) -> str:
    """Generiert einen neuen Beitrittscode (ungültig macht den alten)."""
    import secrets as _secrets
    neuer_code = _secrets.token_urlsafe(6).upper()
    with get_conn() as conn:
        conn.execute(
            "UPDATE vereine SET registrier_code=? WHERE id=?", (neuer_code, verein_id)
        )
    return neuer_code


def benutzer_speichern(verein_id, vorname, nachname, email, passwort, rolle) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO benutzer (verein_id, vorname, nachname, email,
                                  passwort_hash, rolle, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (verein_id, vorname, nachname, email, _pw_hash(passwort), rolle))
        return cur.lastrowid


def benutzer_aktualisieren(benutzer_id, verein_id, vorname, nachname, email, rolle) -> None:
    with get_conn() as conn:
        conn.execute("""
            UPDATE benutzer
            SET verein_id=?, vorname=?, nachname=?, email=?, rolle=?
            WHERE id=?
        """, (verein_id, vorname, nachname, email, rolle, benutzer_id))


def benutzer_aktivieren(benutzer_id: int, aktiv: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET aktiv=? WHERE id=?", (aktiv, benutzer_id)
        )


def benutzer_passwort(benutzer_id: int, neues_passwort: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE benutzer SET passwort_hash=? WHERE id=?",
            (_pw_hash(neues_passwort), benutzer_id)
        )


# ==========================================================================
# Benutzer — Trainerportal-Erweiterungen
# ==========================================================================

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


def benutzer_sperre_pruefen(email: str) -> dict:
    """Gibt Sperr-Status für eine E-Mail zurück.

    Alle Zeitvergleiche laufen in SQLite (UTC), sodass der Servertimezone keine Rolle spielt.

    Rückgabe: {
        'gesperrt': bool,
        'verbleibend_sek': int,   # Sekunden bis Entsperrung (0 wenn nicht gesperrt)
        'benutzer_id': int|None,
        'login_versuche': int,
    }
    """
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
               FROM benutzer WHERE email = ? AND aktiv = 1""",
            (email,),
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
    """Löscht einen Benutzer — nur wenn keine Spieler zugeordnet sind."""
    with get_conn() as conn:
        spieler_n = conn.execute(
            "SELECT COUNT(*) FROM spieler WHERE trainer_id=?", (benutzer_id,)
        ).fetchone()[0]
        if spieler_n > 0:
            return False, (
                f"Trainer hat noch {spieler_n} Spieler. "
                "Bitte zuerst alle Spieler einem anderen Trainer zuweisen."
            )
        conn.execute("DELETE FROM benutzer WHERE id=?", (benutzer_id,))
        return True, ""


# ── Dashboard Analytics ───────────────────────────────────────────────────────

_DIAG_TBLS = [
    "sprint_test", "sprung_test", "anthropometrie", "fms_test",
    "y_balance_test", "ausdauer_test", "kraft_test", "agilitaet_test", "spiro_test",
]


def dashboard_sa_kpis() -> dict:
    """KPIs für Superadmin-Dashboard."""
    with get_conn() as conn:
        n_vereine  = conn.execute("SELECT COUNT(*) FROM vereine").fetchone()[0]
        n_aktiv    = conn.execute("SELECT COUNT(*) FROM vereine WHERE aktiv=1").fetchone()[0]
        n_gesperrt = conn.execute("SELECT COUNT(*) FROM vereine WHERE aktiv=0").fetchone()[0]
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
    return {
        "n_vereine": n_vereine, "n_aktiv": n_aktiv, "n_gesperrt": n_gesperrt,
        "n_vadmin": n_vadmin, "n_trainer": n_trainer, "n_spieler": n_spieler,
        "n_benutzer": n_benutzer, "n_diagnostiken": total_diag,
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
                "SELECT id, name, lizenztyp, lizenz_bis, lizenz_status, aktiv, gesperrt "
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
