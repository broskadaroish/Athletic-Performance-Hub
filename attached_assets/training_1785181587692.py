import sqlite3


# ==================================================
# Datenbank
# ==================================================

DB_NAME = "athletik.db"



def verbindung():

    return sqlite3.connect(DB_NAME)



# ==================================================
# Training Tabelle erstellen
# ==================================================

def training_tabelle_erstellen():

    conn = verbindung()

    cursor = conn.cursor()


    cursor.execute("""
    DROP TABLE IF EXISTS training
    """)


    cursor.execute("""
    CREATE TABLE training (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        bereich TEXT,

        problem TEXT,

        uebung TEXT,

        saetze TEXT,

        wiederholungen TEXT,

        haeufigkeit TEXT

    )
    """)


    conn.commit()

    conn.close()



# ==================================================
# Trainingsbibliothek laden
# ==================================================

def training_standard_laden():

    training_tabelle_erstellen()

    conn = verbindung()
    cursor = conn.cursor()


    # Prüfen ob schon Übungen vorhanden sind

    anzahl = cursor.execute(
        "SELECT COUNT(*) FROM training"
    ).fetchone()[0]


    if anzahl > 0:

        conn.close()
        return



    uebungen = [


        # ==========================
        # SPRUNGGELENK
        # ==========================

        (
            "Sprunggelenk",
            "Mobilität",
            "Knie zur Wand Mobilisation",
            "3",
            "10 je Seite",
            "3x Woche"
        ),

        (
            "Sprunggelenk",
            "Stabilität",
            "Einbeinstand",
            "3",
            "30 Sekunden",
            "3x Woche"
        ),

        (
            "Sprunggelenk",
            "Stabilität",
            "Balance Pad Einbeinstand",
            "3",
            "30 Sekunden",
            "3x Woche"
        ),

        (
            "Sprunggelenk",
            "Kraft",
            "Einbeinige Wadenheben",
            "3",
            "12-15",
            "3x Woche"
        ),



        # ==========================
        # KNIE
        # ==========================

        (
            "Knie",
            "Valgus Kontrolle",
            "Single Leg Squat",
            "3",
            "8-10 je Seite",
            "3x Woche"
        ),

        (
            "Knie",
            "Landekontrolle",
            "Step Down",
            "3",
            "8 je Seite",
            "2x Woche"
        ),

        (
            "Knie",
            "Stabilität",
            "Seitliche Sprünge stabilisieren",
            "3",
            "8 je Seite",
            "2x Woche"
        ),

        (
            "Knie",
            "Sprungkraft",
            "Drop Landing",
            "3",
            "6 Wiederholungen",
            "2x Woche"
        ),



        # ==========================
        # HÜFTE
        # ==========================

        (
            "Hüfte",
            "Gluteus medius",
            "Copenhagen Plank",
            "3",
            "20 Sekunden",
            "3x Woche"
        ),

        (
            "Hüfte",
            "Beckenstabilität",
            "Seitliches Miniband Gehen",
            "3",
            "12 Meter",
            "3x Woche"
        ),

        (
            "Hüfte",
            "Gluteus",
            "Einbeinige Hüftbrücke",
            "3",
            "10 je Seite",
            "3x Woche"
        ),

        (
            "Hüfte",
            "Mobilität",
            "90/90 Hüftrotation",
            "3",
            "10 Wiederholungen",
            "2x Woche"
        ),



        # ==========================
        # OBERSCHENKEL
        # ==========================

        (
            "Oberschenkel",
            "Verletzungsprävention",
            "Nordic Hamstring Curl",
            "3",
            "5-8",
            "2x Woche"
        ),

        (
            "Oberschenkel",
            "Kraft",
            "Bulgarian Split Squat",
            "3",
            "8 je Seite",
            "2x Woche"
        ),

        (
            "Oberschenkel",
            "Kraft",
            "Einbeiniges rumänisches Kreuzheben",
            "3",
            "8 je Seite",
            "2x Woche"
        ),



        # ==========================
        # RUMPF
        # ==========================

        (
            "Rumpf",
            "Anti Rotation",
            "Pallof Press",
            "3",
            "12",
            "3x Woche"
        ),

        (
            "Rumpf",
            "Stabilität",
            "Plank",
            "3",
            "45 Sekunden",
            "3x Woche"
        ),

        (
            "Rumpf",
            "Koordination",
            "Bear Crawl",
            "3",
            "20 Meter",
            "2x Woche"
        ),



        # ==========================
        # SCHNELLIGKEIT
        # ==========================

        (
            "Schnelligkeit",
            "Antritt",
            "10 Meter Sprintstarts",
            "6",
            "10 Meter",
            "2x Woche"
        ),

        (
            "Schnelligkeit",
            "Beschleunigung",
            "20 Meter Sprint",
            "6",
            "20 Meter",
            "1x Woche"
        ),

        (
            "Schnelligkeit",
            "Reaktion",
            "Reaktionssprints",
            "6",
            "5 Sekunden",
            "1x Woche"
        ),



        # ==========================
# EXPLOSIVITÄT
# ==========================


        (
            "Explosivität",
            "Sprungkraft",
            "Squat Jump",
            "3",
            "6 Wiederholungen",
            "2x Woche"
        ),

        (
            "Explosivität",
            "Reaktivkraft",
            "Hürdensprünge",
            "3",
            "5 Wiederholungen",
            "1x Woche"
        ),

        (
            "Explosivität",
            "Einbeinige Kraft",
            "Single Leg Jump",
            "3",
            "5 je Seite",
            "1x Woche"
        ),



# ==========================
# AGILITÄT
# ==========================


        (
            "Agilität",
            "Richtungswechsel",
            "5-10-5 Shuttle Run",
            "5",
            "Durchgänge",
            "1x Woche"
        ),

        (
            "Agilität",
            "Bremsfähigkeit",
            "Deceleration Drill",
            "5",
            "10 Meter",
            "1x Woche"
        ),



# ==========================
# FUSSBALL SPEZIFISCH
# ==========================


        (
            "Fußball",
            "Zweikampf",
            "Einbeinige Stabilität mit Körperkontakt",
            "3",
            "20 Sekunden",
            "1x Woche"
        ),

        (
            "Fußball",
            "Duellkraft",
            "Partner Widerstandsdrücken",
            "3",
            "10 Sekunden",
            "1x Woche"
        ),

        (
            "Fußball",
            "Ballkontrolle",
            "Einbeinige Ballkontakte",
            "3",
            "60 Sekunden",
            "2x Woche"
        ),

        (
            "Fußball",
            "Koordination",
            "Leitertraining",
            "5",
            "Durchgänge",
            "1x Woche"
        ),

        (
            "Fußball",
            "Ausdauer",
            "30-30 Intervallläufe",
            "10",
            "30 Sekunden",
            "1x Woche"
        ),

        (
            "Fußball",
            "RSA Fähigkeit",
            "Repeated Sprint Ability",
            "6",
            "30 Meter",
            "1x Woche"
        )



    ]



    cursor.executemany(
        """

        INSERT INTO training

        (
            bereich,
            problem,
            uebung,
            saetze,
            wiederholungen,
            haeufigkeit
        )

        VALUES (?,?,?,?,?,?)

        """,

        uebungen

    )


    conn.commit()
    conn.close()





# ==================================================
# Übungen nach Bereich laden
# ==================================================

def training_nach_bereich(bereich):

    conn = verbindung()


    daten = conn.execute(
        """

        SELECT

            bereich,
            uebung,
            problem,
            saetze,
            wiederholungen,
            haeufigkeit


        FROM training


        WHERE LOWER(bereich)=LOWER(?)


        ORDER BY problem, uebung


        """,

        (bereich,)

    ).fetchall()


    conn.close()


    return daten





# ==================================================
# Trainingsschwerpunkt automatisch erkennen
# ==================================================

def training_empfehlung(schwerpunkt):


    if not schwerpunkt:

        return []



    text = schwerpunkt.lower()



    bereiche = []



    if "sprunggelenk" in text:

        bereiche.append("Sprunggelenk")



    if "fuß" in text or "fuss" in text:

        bereiche.append("Fuß")



    if "knie" in text:

        bereiche.append("Knie")



    if "hüft" in text or "huft" in text:

        bereiche.append("Hüfte")



    if "rumpf" in text or "core" in text or "becken" in text:

        bereiche.append("Rumpf")



    if "oberschenkel" in text or "hamstring" in text:

        bereiche.append("Oberschenkel")



    if "schnelligkeit" in text:

        bereiche.append("Schnelligkeit")



    if "explosiv" in text:

        bereiche.append("Explosivität")



    if "agil" in text:

        bereiche.append("Agilität")



    if "fußball" in text or "fussball" in text:

        bereiche.append("Fußball")




    # doppelte entfernen

    bereiche = list(dict.fromkeys(bereiche))



    alle_uebungen = []



    for bereich in bereiche:


        daten = training_nach_bereich(bereich)



        for uebung in daten:


            alle_uebungen.append(

                (bereich,) + uebung

            )



    return alle_uebungen
