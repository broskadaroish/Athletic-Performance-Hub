print("PERIODISIERUNG DATEI GELADEN")


import sqlite3
from datetime import date




DB_NAME = "athletik.db"



# ==========================================
# Verbindung
# ==========================================

def verbindung():

    return sqlite3.connect(DB_NAME)



# ==========================================
# 12 Wochen Trainingszyklus erstellen
# ==========================================

def trainingszyklus_erstellen(spieler_id, schwerpunkt):


    plan = []



    # Schwerpunkt Text vorbereiten
    text = schwerpunkt.lower()

    prioritaeten=[]


    if "knee" in text or "knie" in text:
        prioritaeten.append("Knie")

    if "seitliche stabilität" in text:
        prioritaeten.append("Hüfte")

    if "stabilitätstraining" in text:
        prioritaeten.append("Rumpf")

    if "hüfte" in text or "huft" in text:
        prioritaeten.append("Hüfte")


    if "gluteus" in text:
        prioritaeten.append("Hüfte")


    if "becken" in text:
        prioritaeten.append("Rumpf")


    if "sprunggelenk" in text:
        prioritaeten.append("Sprunggelenk")



    # ==================================
    # PHASE 1
    # Woche 1-4 Stabilität
    # ==================================

    phase1 = [

        ("Sprunggelenk",
         "Knie zur Wand Mobilisation",
         "leicht",
         "3x10 je Seite",
         "3x Woche"),


        ("Hüfte",
         "Seitliches Miniband Gehen",
         "leicht",
         "3x12 Meter",
         "3x Woche"),


        ("Rumpf",
         "Pallof Press",
         "leicht",
         "3x12",
         "3x Woche")

    ]



    # ==================================
    # PHASE 2
    # Woche 5-8 Kraft
    # ==================================

    phase2 = [

        ("Hüfte",
         "Einbeinige Hüftbrücke",
         "mittel",
         "3x10 je Seite",
         "3x Woche"),


        ("Knie",
         "Step Down",
         "mittel",
         "3x8 je Seite",
         "2x Woche"),


        ("Oberschenkel",
         "Nordic Hamstring Curl",
         "hoch",
         "3x6",
         "2x Woche")

    ]



    # ==================================
    # PHASE 3
    # Woche 9-12 Fußball
    # ==================================

    phase3 = [

        ("Fußball",
         "Deceleration Drill",
         "hoch",
         "5 Durchgänge",
         "1x Woche"),


        ("Schnelligkeit",
         "10 Meter Sprintstarts",
         "hoch",
         "6x10 Meter",
         "2x Woche"),


        ("Agilität",
         "5-10-5 Shuttle Run",
         "hoch",
         "5 Durchgänge",
         "1x Woche")

    ]




    # ==================================
    # Wochen erzeugen
    # ==================================

    for woche in range(1,5):

        for uebung in phase1:

            plan.append({

                "woche":woche,
                "phase":"Stabilisation",
                "ziel":"Bewegungskontrolle",
                "bereich":uebung[0],
                "uebung":uebung[1],
                "intensitaet":uebung[2],
                "volumen":uebung[3],
                "haeufigkeit":uebung[4]

            })



    for woche in range(5,9):

        for uebung in phase2:

            plan.append({

                "woche":woche,
                "phase":"Kraftaufbau",
                "ziel":"Maximalkraft und Stabilität",
                "bereich":uebung[0],
                "uebung":uebung[1],
                "intensitaet":uebung[2],
                "volumen":uebung[3],
                "haeufigkeit":uebung[4]

            })



    for woche in range(9,13):

        for uebung in phase3:

            plan.append({

                "woche":woche,
                "phase":"Fußballspezifisch",
                "ziel":"Leistung und Verletzungsprävention",
                "bereich":uebung[0],
                "uebung":uebung[1],
                "intensitaet":uebung[2],
                "volumen":uebung[3],
                "haeufigkeit":uebung[4]

            })



    speichern_periodisierung(
        spieler_id,
        plan
    )


    return plan





# ==========================================
# In Datenbank speichern
# ==========================================

def speichern_periodisierung(spieler_id, plan):


    conn = verbindung()

    cursor = conn.cursor()


    # alten Plan löschen

    cursor.execute(
        """
        DELETE FROM periodisierung
        WHERE spieler_id=?
        """,
        (spieler_id,)
    )



    for p in plan:


        cursor.execute(
            """
            INSERT INTO periodisierung
            (
            spieler_id,
            woche,
            phase,
            ziel,
            bereich,
            uebung,
            intensitaet,
            volumen,
            haeufigkeit,
            status
            )

            VALUES (?,?,?,?,?,?,?,?,?,?)

            """,

            (

            spieler_id,
            p["woche"],
            p["phase"],
            p["ziel"],
            p["bereich"],
            p["uebung"],
            p["intensitaet"],
            p["volumen"],
            p["haeufigkeit"],
            "offen"

            )

        )



    conn.commit()

    conn.close()





# ==========================================
# Plan laden
# ==========================================

def periodisierung_laden(spieler_id):


    conn = verbindung()


    daten = conn.execute(

        """
        SELECT
        woche,
        phase,
        ziel,
        bereich,
        uebung,
        intensitaet,
        volumen,
        haeufigkeit

        FROM periodisierung

        WHERE spieler_id=?

        ORDER BY woche

        """,

        (spieler_id,)

    ).fetchall()



    conn.close()


    return daten