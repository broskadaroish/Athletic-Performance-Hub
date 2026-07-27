import sqlite3
import os


# ==================================================
# Datenbank
# athletik.db liegt im gleichen Ordner wie app.py
# ==================================================

DB_NAME = "athletik.db"



# ==================================================
# Verbindung herstellen
# ==================================================

def verbindung():

    return sqlite3.connect(DB_NAME)





# ==================================================
# Datenbank erstellen
# ==================================================

def datenbank_erstellen():

    conn = verbindung()

    cursor = conn.cursor()



    # ==================================================
    # Spieler Tabelle
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spieler (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        geburtsdatum TEXT,

        position TEXT,

        spielbein TEXT,

        mannschaft TEXT

    )
    """)



    # ==================================================
    # FMS Tabelle
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fms_test (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        spieler_id INTEGER,


        datum TEXT,


        deep_squat INTEGER,


        hurdle_links INTEGER,

        hurdle_rechts INTEGER,


        inline_links INTEGER,

        inline_rechts INTEGER,


        shoulder_links INTEGER,

        shoulder_rechts INTEGER,


        aslr_links INTEGER,

        aslr_rechts INTEGER,


        trunk INTEGER,


        rotary_links INTEGER,

        rotary_rechts INTEGER,


        score INTEGER,


        bewertung TEXT,


        asymmetrie TEXT,


        schwerpunkt TEXT,


        FOREIGN KEY(spieler_id)
        REFERENCES spieler(id)

    )
    """)





    # ==================================================
    # Y-Balance Tabelle
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS y_balance_test (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        spieler_id INTEGER,


        datum TEXT,


        anterior_rechts REAL,

        anterior_links REAL,


        posteromedial_rechts REAL,

        posteromedial_links REAL,


        posterolateral_rechts REAL,

        posterolateral_links REAL,


        diff_anterior REAL,


        diff_posteromedial REAL,


        diff_posterolateral REAL,


        composite_rechts REAL,


        composite_links REAL,


        asymmetrie TEXT,


        schwerpunkt TEXT,


        FOREIGN KEY(spieler_id)
        REFERENCES spieler(id)

    )
    """)



   

    # ==================================================
    # Trainingsplan Tabelle
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trainingsplan (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        spieler_id INTEGER,

        datum TEXT,

        woche INTEGER,

        bereich TEXT,

        uebung TEXT,

        saetze TEXT,

        wiederholungen TEXT,

        haeufigkeit TEXT,

        status TEXT,


        FOREIGN KEY(spieler_id)
        REFERENCES spieler(id)

)
""")



    # ==================================================
    # Periodisierung Tabelle
    # ==================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS periodisierung (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        spieler_id INTEGER,

        woche INTEGER,

        phase TEXT,

        ziel TEXT,

        bereich TEXT,

        uebung TEXT,

        intensitaet TEXT,

        volumen TEXT,

        haeufigkeit TEXT,

        status TEXT,

        FOREIGN KEY(spieler_id)
        REFERENCES spieler(id)

    )
    """)


    conn.commit()

    conn.close()

    


# ==================================================
# Spieler speichern
# ==================================================

def spieler_speichern(
        name,
        geburtsdatum,
        position,
        spielbein,
        mannschaft):


    conn = verbindung()

    cursor = conn.cursor()


    cursor.execute("""
    
    INSERT INTO spieler
    (
        name,
        geburtsdatum,
        position,
        spielbein,
        mannschaft
    )

    VALUES (?,?,?,?,?)

    """,
    (
        name,
        geburtsdatum,
        position,
        spielbein,
        mannschaft
    ))


    conn.commit()

    conn.close()





# ==================================================
# Spieler laden
# ==================================================

def spieler_laden():

    conn = verbindung()


    daten = conn.execute("""
    
    SELECT *

    FROM spieler

    ORDER BY name

    """).fetchall()


    conn.close()


    return daten





# ==================================================
# FMS Test speichern
# ==================================================

def fms_speichern(

    spieler_id,

    datum,

    deep,

    hurdle_l,

    hurdle_r,

    inline_l,

    inline_r,

    shoulder_l,

    shoulder_r,

    aslr_l,

    aslr_r,

    trunk,

    rotary_l,

    rotary_r,

    score,

    bewertung,

    asymmetrie,

    schwerpunkt

):


    conn = verbindung()


    conn.execute("""
    
    INSERT INTO fms_test

    (

        spieler_id,

        datum,

        deep_squat,

        hurdle_links,

        hurdle_rechts,

        inline_links,

        inline_rechts,

        shoulder_links,

        shoulder_rechts,

        aslr_links,

        aslr_rechts,

        trunk,

        rotary_links,

        rotary_rechts,

        score,

        bewertung,

        asymmetrie,

        schwerpunkt

    )


    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        spieler_id,

        datum,

        deep,

        hurdle_l,

        hurdle_r,

        inline_l,

        inline_r,

        shoulder_l,

        shoulder_r,

        aslr_l,

        aslr_r,

        trunk,

        rotary_l,

        rotary_r,

        score,

        bewertung,

        asymmetrie,

        schwerpunkt

    ))


    conn.commit()

    conn.close()





# ==================================================
# Y-Balance Test speichern
# ==================================================

def y_balance_speichern(

    spieler_id,

    datum,

    anterior_r,

    anterior_l,

    posteromedial_r,

    posteromedial_l,

    posterolateral_r,

    posterolateral_l,

    diff_a,

    diff_pm,

    diff_pl,

    composite_r,

    composite_l,

    asymmetrie,

    schwerpunkt

):


    conn = verbindung()


    conn.execute("""
    
    INSERT INTO y_balance_test

    (

        spieler_id,

        datum,

        anterior_rechts,

        anterior_links,

        posteromedial_rechts,

        posteromedial_links,

        posterolateral_rechts,

        posterolateral_links,

        diff_anterior,

        diff_posteromedial,

        diff_posterolateral,

        composite_rechts,

        composite_links,

        asymmetrie,

        schwerpunkt

    )


    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        spieler_id,

        datum,

        anterior_r,

        anterior_l,

        posteromedial_r,

        posteromedial_l,

        posterolateral_r,

        posterolateral_l,

        diff_a,

        diff_pm,

        diff_pl,

        composite_r,

        composite_l,

        asymmetrie,

        schwerpunkt

    ))


    conn.commit()

    conn.close()



# ==================================================
# Letzten FMS Test laden
# ==================================================

def letzter_fms_test(spieler_id):


    conn = verbindung()


    daten = conn.execute("""
    
    SELECT *

    FROM fms_test

    WHERE spieler_id = ?

    ORDER BY id DESC

    LIMIT 1

    """,
    (spieler_id,)).fetchone()


    conn.close()


    return daten





# ==================================================
# Letzten Y-Balance Test laden
# ==================================================

def letzter_y_balance_test(spieler_id):


    conn = verbindung()


    daten = conn.execute("""
    
    SELECT *

    FROM y_balance_test

    WHERE spieler_id = ?

    ORDER BY id DESC

    LIMIT 1

    """,
    (spieler_id,)).fetchone()


    conn.close()


    return daten





# ==================================================
# Spieler mit allen Grunddaten laden
# ==================================================

def spieler_info(spieler_id):


    conn = verbindung()


    daten = conn.execute("""
    
    SELECT

        id,

        name,

        geburtsdatum,

        position,

        spielbein,

        mannschaft


    FROM spieler


    WHERE id = ?

    """,
    (spieler_id,)).fetchone()


    conn.close()


    return daten





# ==================================================
# Alle Tests eines Spielers (Historie)
# ==================================================

def spieler_historie(spieler_id):


    conn = verbindung()


    fms = conn.execute("""
    
    SELECT *

    FROM fms_test

    WHERE spieler_id = ?

    ORDER BY datum DESC


    """,
    (spieler_id,)).fetchall()



    y_balance = conn.execute("""
    
    SELECT *

    FROM y_balance_test

    WHERE spieler_id = ?

    ORDER BY datum DESC


    """,
    (spieler_id,)).fetchall()



    conn.close()



    return {

        "fms": fms,

        "y_balance": y_balance

    }



# ==================================================
# Prüfen ob Tabelle existiert
# ==================================================

def tabelle_existiert(tabellen_name):


    conn = verbindung()


    daten = conn.execute("""
    
    SELECT name

    FROM sqlite_master

    WHERE type='table'

    AND name=?

    """,
    (tabellen_name,)).fetchone()


    conn.close()


    return daten is not None





# ==================================================
# Datenbank Status prüfen
# ==================================================

def datenbank_status():

    tabellen = [

        "spieler",

        "fms_test",

        "y_balance_test",

        "trainingsplan"

    ]


    status = {}


    for tabelle in tabellen:

        status[tabelle] = tabelle_existiert(tabelle)



    return status



# ==================================================
# Trainingsplan speichern
# ==================================================

def trainingsplan_speichern(
        spieler_id,
        datum,
        woche,
        bereich,
        uebung,
        saetze,
        wiederholungen,
        haeufigkeit):


    conn = verbindung()


    conn.execute("""
    
    INSERT INTO trainingsplan

    (
        spieler_id,
        datum,
        woche,
        bereich,
        uebung,
        saetze,
        wiederholungen,
        haeufigkeit,
        status
    )


    VALUES (?,?,?,?,?,?,?,?,?)

    """,

    (
        spieler_id,
        datum,
        woche,
        bereich,
        uebung,
        saetze,
        wiederholungen,
        haeufigkeit,
        "offen"
    ))


    conn.commit()

    conn.close()




# ==================================================
# Trainingsplan laden
# ==================================================

def trainingsplan_laden(spieler_id):


    conn = verbindung()


    daten = conn.execute("""
    
    SELECT *

    FROM trainingsplan

    WHERE spieler_id=?

    ORDER BY woche, id

    """,
    (spieler_id,)).fetchall()


    conn.close()


    return daten    


# ==================================================
# Datenbank initialisieren
# Wird in app.py aufgerufen
# ==================================================

def system_start():

    datenbank_erstellen()

    status = datenbank_status()

    return status



# =====================================
# FMS Historie laden
# =====================================

def fms_history(spieler_id):

    conn = sqlite3.connect(DB_NAME)

    daten = conn.execute(
        """
        SELECT *
        FROM fms_test
        WHERE spieler_id=?
        ORDER BY id DESC
        """,
        (spieler_id,)
    ).fetchall()

    conn.close()

    return daten



# =====================================
# Y-Balance Historie laden
# =====================================

def ybalance_history(spieler_id):

    conn = sqlite3.connect(DB_NAME)

    daten = conn.execute(
        """
        SELECT *
        FROM y_balance_test
        WHERE spieler_id=?
        ORDER BY id DESC
        """,
        (spieler_id,)
    ).fetchall()

    conn.close()

    return daten