import sqlite3


DB_NAME = "athletik.db"



import sqlite3


DB_NAME = "athletik.db"



# ==========================================
# Trainingsplan generieren
# ==========================================

import sqlite3
from datetime import date


DB_NAME = "athletik.db"


def trainingsplan_generieren(spieler_id, bereiche):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    if not bereiche:
        conn.close()
        return []


    platzhalter = ",".join(["?"] * len(bereiche))


    sql = f"""
    SELECT
        bereich,
        uebung,
        problem,
        saetze,
        wiederholungen,
        haeufigkeit

    FROM training

    WHERE bereich IN ({platzhalter})

    ORDER BY bereich
    """


    daten = cursor.execute(
        sql,
        bereiche
    ).fetchall()



    # alten Plan löschen

    cursor.execute(
        """
        DELETE FROM trainingsplan
        WHERE spieler_id=?
        """,
        (spieler_id,)
    )



    # neuen Plan speichern

    for u in daten:

        cursor.execute(
            """
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
                str(date.today()),
                1,
                u[0],
                u[1],
                u[3],
                u[4],
                u[5],
                "offen"
            )
        )


    conn.commit()
    conn.close()


    return daten



# ==========================================
# Trainingsplan laden
# ==========================================

def trainingsplan_laden(spieler_id):

    conn = sqlite3.connect(DB_NAME)


    daten = conn.execute(
        """
        SELECT
            bereich,
            uebung,
            saetze,
            wiederholungen,
            haeufigkeit

        FROM trainingsplan

        WHERE spieler_id = ?

        ORDER BY id
        """,
        (spieler_id,)
    ).fetchall()


    conn.close()


    return daten