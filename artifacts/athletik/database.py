"""
Database layer — single source of truth for all SQLite operations.
Uses a context manager for every connection so files are never left open.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date

DB_PATH = "athletik.db"


def _row(r):
    """sqlite3.Row → dict (Streamlit kann Row-Objekte nicht pickling)."""
    return dict(r) if r is not None else None


def _rows(rs):
    """Liste von sqlite3.Row → Liste von dicts."""
    return [dict(r) for r in rs]


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ─── Schema ────────────────────────────────────────────────────────────────

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS spieler (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            geburtsdatum TEXT,
            position     TEXT,
            spielbein    TEXT,
            mannschaft   TEXT
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
        """)


# ─── Spieler ───────────────────────────────────────────────────────────────

def spieler_speichern(name, geburtsdatum, position, spielbein, mannschaft):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO spieler (name,geburtsdatum,position,spielbein,mannschaft) VALUES (?,?,?,?,?)",
            (name, geburtsdatum, position, spielbein, mannschaft),
        )


def spieler_laden():
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM spieler ORDER BY name").fetchall())


def spieler_by_id(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute("SELECT * FROM spieler WHERE id=?", (spieler_id,)).fetchone())


def spieler_loeschen(spieler_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM spieler WHERE id=?", (spieler_id,))


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


# ─── Trainingsplan ─────────────────────────────────────────────────────────

def trainingsplan_loeschen(spieler_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM trainingsplan WHERE spieler_id=?", (spieler_id,))


def trainingsplan_eintrag_speichern(spieler_id, datum, woche, bereich, uebung, saetze, wdh, haeufigkeit):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO trainingsplan (spieler_id,datum,woche,bereich,uebung,saetze,wiederholungen,haeufigkeit,status) VALUES (?,?,?,?,?,?,?,?,?)",
            (spieler_id, datum, woche, bereich, uebung, saetze, wdh, haeufigkeit, "offen"),
        )


def trainingsplan_laden(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT bereich,uebung,saetze,wiederholungen,haeufigkeit,woche FROM trainingsplan WHERE spieler_id=? ORDER BY woche,id",
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
