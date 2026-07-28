"""
Database layer — single source of truth for all SQLite operations.
Uses a context manager for every connection so files are never left open.
"""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

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
            trainingsstatus TEXT
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
    # Migration: neue Spalten für bestehende Datenbanken nachträglich anlegen
    _migrate_spieler_columns()


def _migrate_spieler_columns():
    """Fügt neue Spalten zur spieler-Tabelle hinzu, falls noch nicht vorhanden."""
    neue_spalten = [
        ("vorname", "TEXT"), ("nachname", "TEXT"), ("geschlecht", "TEXT"),
        ("altersklasse", "TEXT"), ("hauptposition", "TEXT"), ("nebenposition", "TEXT"),
        ("leistungsniveau", "TEXT"), ("trainingsstatus", "TEXT"),
    ]
    with get_conn() as conn:
        for spalte, typ in neue_spalten:
            try:
                conn.execute(f"ALTER TABLE spieler ADD COLUMN {spalte} {typ}")
            except Exception:
                pass  # Spalte existiert bereits


# ─── Hilfsfunktionen ───────────────────────────────────────────────────────

def berechne_alter(geburtsdatum_str: str) -> int | None:
    """Berechnet das aktuelle Alter aus einem Datumsstring (TT.MM.JJJJ oder JJJJ-MM-TT)."""
    if not geburtsdatum_str:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            geb = datetime.strptime(geburtsdatum_str, fmt).date()
            heute = date.today()
            return heute.year - geb.year - ((heute.month, heute.day) < (geb.month, geb.day))
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
                      spielbein, leistungsniveau, mannschaft, trainingsstatus):
    name = f"{vorname} {nachname}".strip()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO spieler
               (name, vorname, nachname, geburtsdatum, geschlecht,
                position, hauptposition, nebenposition, altersklasse,
                spielbein, leistungsniveau, mannschaft, trainingsstatus)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (name, vorname, nachname, geburtsdatum, geschlecht,
             hauptposition, hauptposition, nebenposition, altersklasse,
             spielbein, leistungsniveau, mannschaft, trainingsstatus),
        )


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

def spieler_laden():
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM spieler ORDER BY name").fetchall())


def spieler_by_id(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute("SELECT * FROM spieler WHERE id=?", (spieler_id,)).fetchone())


def spieler_loeschen(spieler_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM verletzung WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM anthropometrie WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM agilitaet_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM ausdauer_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM sprint_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM sprung_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM fms_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM y_balance_test WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM trainingsplan WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM periodisierung WHERE spieler_id=?", (spieler_id,))
        conn.execute("DELETE FROM spieler WHERE id=?", (spieler_id,))


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


# ─── Anthropometrie ────────────────────────────────────────────────────────

def anthropometrie_speichern(spieler_id, datum, groesse, gewicht, sitzhoehe,
                              beinlaenge, armspannweite, koerperfett, muskelmasse,
                              bmi, bmi_kat, phv_offset, reifestatus):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO anthropometrie
        (spieler_id,datum,groesse,gewicht,sitzhoehe,beinlaenge,armspannweite,
         koerperfett,muskelmasse,bmi,bmi_kategorie,phv_offset,reifestatus)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, groesse, gewicht, sitzhoehe, beinlaenge,
              armspannweite, koerperfett, muskelmasse, bmi, bmi_kat, phv_offset, reifestatus))


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
                      sitzhoehe,beinlaenge,armspannweite,phv_offset,reifestatus
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
                     beschl_index, bew_10, bew_30, defizite):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO sprint_test
        (spieler_id,datum,
         v1_5m,v2_5m,v3_5m,beste_5m,
         v1_10m,v2_10m,v3_10m,beste_10m,
         v1_20m,v2_20m,v3_20m,beste_20m,
         v1_30m,v2_30m,v3_30m,beste_30m,
         beschl_index,bewertung_10m,bewertung_30m,defizite)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum,
              v1_5, v2_5, v3_5, b5,
              v1_10, v2_10, v3_10, b10,
              v1_20, v2_20, v3_20, b20,
              v1_30, v2_30, v3_30, b30,
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
            "SELECT datum,beste_5m,beste_10m,beste_20m,beste_30m,beschl_index,bewertung_10m FROM sprint_test WHERE spieler_id=? ORDER BY datum",
            (spieler_id,),
        ).fetchall())


# ─── Sprung ────────────────────────────────────────────────────────────────

def sprung_speichern(spieler_id, datum,
                     cmj_beid, cmj_rechts, cmj_links, cmj_asym,
                     squat_jump, dj_hoehe, dj_kz, rsi,
                     standweit, bew_cmj, defizite):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO sprung_test
        (spieler_id,datum,cmj_beid,cmj_rechts,cmj_links,cmj_asymmetrie,
         squat_jump,drop_jump_hoehe,drop_jump_kz,rsi,standweit,bewertung_cmj,defizite)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum,
              cmj_beid, cmj_rechts, cmj_links, cmj_asym,
              squat_jump, dj_hoehe, dj_kz, rsi,
              standweit, bew_cmj, defizite))


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
                         bew_505, bew_t_test, bew_illinois, defizite):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO agilitaet_test
        (spieler_id,datum,t505_r,t505_l,asym_505,t5_10_5,t_test,illinois,
         bew_505,bew_t_test,bew_illinois,defizite)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (spieler_id, datum, t505_r, t505_l, asym_505,
              t5_10_5, t_test, illinois,
              bew_505, bew_t_test, bew_illinois, defizite))


def agilitaet_letzter(spieler_id):
    with get_conn() as conn:
        return _row(conn.execute(
            "SELECT * FROM agilitaet_test WHERE spieler_id=? ORDER BY id DESC LIMIT 1",
            (spieler_id,),
        ).fetchone())


def agilitaet_history(spieler_id):
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT datum,t505_r,t505_l,asym_505,t5_10_5,t_test,illinois,bew_t_test FROM agilitaet_test WHERE spieler_id=? ORDER BY datum",
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
