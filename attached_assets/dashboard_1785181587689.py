import streamlit as st
import sqlite3

from training import training_nach_bereich

from trainingsplan import (
    trainingsplan_generieren,
    trainingsplan_laden
)

from periodisierung import (
    trainingszyklus_erstellen,
    periodisierung_laden
)


DB_NAME = "athletik.db"


# ==========================
# Datenbank Verbindung
# ==========================

def verbindung():

    return sqlite3.connect(DB_NAME)



# ==========================
# Spieler laden
# ==========================

def spieler_laden_dashboard():

    conn = verbindung()

    daten = conn.execute(
        """
        SELECT *
        FROM spieler
        ORDER BY name
        """
    ).fetchall()

    conn.close()

    return daten



# =====================================
# FMS Historie
# =====================================

def fms_history(spieler_id):

    conn = verbindung()

    daten = conn.execute(
        """
        SELECT 
            datum,
            score,
            bewertung,
            asymmetrie,
            schwerpunkt
        FROM fms_test
        WHERE spieler_id=?
        ORDER BY id DESC
        """,
        (spieler_id,)
    ).fetchall()

    conn.close()

    return daten



# =====================================
# Y-Balance Historie
# =====================================

def ybalance_history(spieler_id):

    conn = verbindung()

    daten = conn.execute(
        """
        SELECT
            datum,
            composite_rechts,
            composite_links,
            asymmetrie,
            schwerpunkt
        FROM y_balance_test
        WHERE spieler_id=?
        ORDER BY id DESC
        """,
        (spieler_id,)
    ).fetchall()

    conn.close()

    return daten



# ==========================
# FMS laden
# ==========================

def letzter_fms_test(spieler_id):

    conn = verbindung()

    daten = conn.execute(
        """
        SELECT *
        FROM fms_test
        WHERE spieler_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (spieler_id,)
    ).fetchone()

    conn.close()

    return daten



# ==========================
# Y Balance laden
# ==========================

def letzter_y_balance_test(spieler_id):

    conn = verbindung()

    daten = conn.execute(
        """
        SELECT *
        FROM y_balance_test
        WHERE spieler_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (spieler_id,)
    ).fetchone()

    conn.close()

    return daten



# ==========================
# Risiko
# ==========================

def risiko_berechnen(fms,y):

    risiko=0


    if fms:

        score=fms[15]

        if score<=12:
            risiko+=2

        elif score<=17:
            risiko+=1


        if "Asymmetrie" in fms[17]:
            risiko+=1



    if y:

        comp_r=y[12]
        comp_l=y[13]


        if comp_r<85 or comp_l<85:
            risiko+=2

        elif comp_r<90 or comp_l<90:
            risiko+=1



        if "Asymmetrie" in y[14]:
            risiko+=1



    if risiko>=4:

        return "🔴 HOHES RISIKO","Rot"


    elif risiko>=2:

        return "🟡 MITTLERES RISIKO","Gelb"


    else:

        return "🟢 GERINGES RISIKO","Grün"



# ==========================================
# Automatische Athletenbewertung
# ==========================================

def athleten_bewertung(fms, y, defizite):


    text = []


    # Risiko

    risiko_text = ""


    if fms:

        score = fms[15]


        if score <= 12:

            risiko_text = "🔴 Erhöhtes Verletzungsrisiko"

        elif score <= 14:

            risiko_text = "🟡 Mittleres Optimierungspotenzial"

        else:

            risiko_text = "🟢 Gute funktionelle Basis"



        text.append(
            risiko_text
        )



    # FMS Analyse

    if fms:


        if fms[15] <= 12:

            text.append(
                "• FMS Score unter optimalem Bereich"
            )


        if "Asymmetrie" in str(fms[17]):

            text.append(
                "• Mehrere funktionelle Asymmetrien vorhanden"
            )



    # Y Balance Analyse

    if y:


        if "Asymmetrie" in str(y[14]):

            text.append(
                "• Y-Balance zeigt Seitenunterschiede"
            )



    # Defizite

    if defizite:


        text.append("")

        text.append(
            "🎯 Trainingsschwerpunkte:"
        )


        gesehen=[]


        for d in defizite:


            bereich=d[1]


            if bereich not in gesehen:

                text.append(
                    "• " + bereich
                )

                gesehen.append(
                    bereich
                )



    return "\n".join(text)


# ==========================================
# Athletik Score berechnen 0-100
# ==========================================

def athletik_score_berechnen(fms, y):

    score = 100


    # ==========================
    # FMS Bewertung
    # ==========================

    if fms:

        fms_score = fms[15]


        if fms_score <= 12:

            score -= 25

        elif fms_score <= 14:

            score -= 15

        elif fms_score <= 17:

            score -= 5



        # Asymmetrien

        if "Asymmetrie" in str(fms[17]):

            score -= 10



    else:

        score -= 20



    # ==========================
    # Y Balance Bewertung
    # ==========================

    if y:

        comp_r = y[12]

        comp_l = y[13]


        durchschnitt = (
            comp_r + comp_l
        ) / 2



        if durchschnitt < 85:

            score -= 20


        elif durchschnitt < 90:

            score -= 10


        elif durchschnitt < 94:

            score -= 5



        if "Asymmetrie" in str(y[14]):

            score -= 10



    else:

        score -= 15



    # Grenzen

    if score < 0:

        score = 0


    if score > 100:

        score = 100



    return score



# ==========================================
# Athletische Defizite analysieren
# ==========================================

def defizite_ermitteln(fms, ybalance):

    defizite = []

    # --------------------------
    # FMS
    # --------------------------

    if fms:

        score = fms[15]
        asym = str(fms[17]).lower()
        schwerpunkt = str(fms[18]).lower()

        if score <= 12:
            defizite.append(("🔴", "Ganzkörperstabilität", "Sehr niedriger FMS-Score."))

        elif score <= 14:
            defizite.append(("🟡", "Ganzkörperstabilität", "Verbesserungsbedarf."))

        if "hüft" in schwerpunkt:
            defizite.append(("🔴", "Hüfte", "Defizite der Hüftstabilität."))

        if "rumpf" in schwerpunkt or "core" in schwerpunkt:
            defizite.append(("🔴", "Core", "Defizite der Rumpfstabilität."))

        if "sprunggelenk" in schwerpunkt:
            defizite.append(("🟡", "Sprunggelenk", "Mobilität/Stabilität verbessern."))

        if "knie" in schwerpunkt:
            defizite.append(("🟡", "Knie", "Beinachsenkontrolle verbessern."))

        if "schulter" in schwerpunkt:
            defizite.append(("🟡", "Schulter", "Schulterbeweglichkeit verbessern."))

    # --------------------------
    # Y-Balance
    # --------------------------

    if ybalance:

        asym = str(ybalance[14]).lower()
        schwerpunkt = str(ybalance[15]).lower()

        if "anterior" in asym:
            defizite.append(("🔴", "Sprunggelenk", "Anterior-Asymmetrie."))

        if "posteromedial" in asym:
            defizite.append(("🔴", "Hüfte", "Posteromediale Asymmetrie."))

        if "posterolateral" in asym:
            defizite.append(("🔴", "Hüfte", "Posterolaterale Asymmetrie."))

        if "hüft" in schwerpunkt:
            defizite.append(("🔴", "Hüfte", "Hüftstabilität verbessern."))

        if "becken" in schwerpunkt:
            defizite.append(("🟡", "Core", "Beckenstabilität verbessern."))

    # --------------------------
    # Doppelte entfernen
    # --------------------------

    gesehen = set()
    neu = []

    for eintrag in defizite:

        key = (eintrag[0], eintrag[1], eintrag[2])

        if key not in gesehen:
            neu.append(eintrag)
            gesehen.add(key)

    return neu



# ==========================================
# Schwerpunkt automatisch erkennen
# ==========================================

def schwerpunkt_analyse(text):

    bereiche=[]

    text=text.lower()



    if "hüft" in text or "huft" in text:

        bereiche.append("Hüfte")



    if "gluteus" in text:

        bereiche.append("Hüfte")



    if "becken" in text:

        bereiche.append("Rumpf")



    if "core" in text or "rumpf" in text:

        bereiche.append("Rumpf")



    if "sprunggelenk" in text:

        bereiche.append("Sprunggelenk")



    if "knie" in text:

        bereiche.append("Knie")



    if "schulter" in text:

        bereiche.append("Schulter")



    return list(dict.fromkeys(bereiche))




# ==========================
# Dashboard
# ==========================


# ==========================================
# Automatische Athletenbewertung
# ==========================================

def athletenbewertung(fms, y):

    bewertung = []

    schwerpunkte = []


    # ==========================
    # FMS Analyse
    # ==========================

    if fms:

        score = fms[15]
        schwerpunkt = str(fms[18]).lower()


        if score <= 12:

            bewertung.append(
                "🔴 Niedriger FMS Score - funktionelle Defizite vorhanden."
            )


        elif score <= 14:

            bewertung.append(
                "🟡 FMS Score zeigt Verbesserungsbedarf."
            )


        else:

            bewertung.append(
                "🟢 Gute funktionelle Grundlage vorhanden."
            )


        if "hüft" in schwerpunkt:

            schwerpunkte.append(
                "Hüftstabilität"
            )


        if "rumpf" in schwerpunkt or "core" in schwerpunkt:

            schwerpunkte.append(
                "Core Stabilität"
            )


        if "sprunggelenk" in schwerpunkt:

            schwerpunkte.append(
                "Sprunggelenk Mobilität"
            )



    # ==========================
    # Y Balance Analyse
    # ==========================

    if y:

        asym = str(y[14]).lower()
        schwerpunkt = str(y[15]).lower()



        if "anterior" in asym:

            bewertung.append(
                "⚠️ Einschränkung in der vorderen Reichweite erkannt."
            )

            schwerpunkte.append(
                "Sprunggelenk Kontrolle"
            )



        if "posteromedial" in asym or "posterolateral" in asym:

            bewertung.append(
                "⚠️ Seitliche Stabilitätsdefizite vorhanden."
            )

            schwerpunkte.append(
                "Becken- und Hüftkontrolle"
            )



        if "hüft" in schwerpunkt:

            schwerpunkte.append(
                "Gluteus medius Training"
            )



    # ==========================
    # Doppelte entfernen
    # ==========================

    schwerpunkte = list(
        dict.fromkeys(schwerpunkte)
    )


    # ==========================
    # Ergebnis Text
    # ==========================

    text = ""


    for punkt in bewertung:

        text += punkt + "\n\n"



    if schwerpunkte:


        text += "\n🎯 Trainingsschwerpunkte:\n\n"


        for s in schwerpunkte:

            text += "\n• " + s


    else:

        text += "\nKeine besonderen Defizite erkannt."


    return text


def dashboard_anzeigen():


    st.header(
        "📊 Fußball Athletik Dashboard"
    )


    spieler=spieler_laden_dashboard()


    if not spieler:

        st.warning(
            "Keine Spieler vorhanden"
        )

        return



    auswahl=st.selectbox(

        "👤 Spieler auswählen",

        spieler,

        format_func=lambda x:x[1]

    )


    spieler_id=auswahl[0]


    fms=letzter_fms_test(spieler_id)

    y=letzter_y_balance_test(spieler_id)

    # ==========================
    # FMS HISTORY
    # ==========================

    st.divider()

    st.subheader("📈 FMS Entwicklung")

    daten = fms_history(spieler_id)

    if daten:

        st.dataframe(
            daten,
            use_container_width=True
        )

    else:

        st.info(
            "Noch keine FMS Historie vorhanden."
        )




    # ==========================
    # Y-Balance HISTORY
    # ==========================

    st.divider()

    st.subheader("📈 Y-Balance Entwicklung")

    daten_y = ybalance_history(spieler_id)

    if daten_y:

        st.dataframe(
            daten_y,
            use_container_width=True
    )

    else:

        st.info(
            "Noch keine Y-Balance Historie vorhanden."
    )



    # ==========================
    # Athletik Score
    # ==========================

    athletik_score = athletik_score_berechnen(
        fms,
        y
    )


    st.subheader(
        "⚽ Athletik Score"
    )


    st.metric(
        "Gesamtbewertung",
        f"{athletik_score}/100"
    )


    if athletik_score >= 85:

         st.success(
            "🟢 Sehr guter Athletikstatus"
    )


    elif athletik_score >= 70:

        st.warning(
             "🟡 Verbesserungsbedarf vorhanden"
    )


    else:

        st.error(
            "🔴 Athletikdefizite erkannt"
    )



    # ==========================
    # Spieler
    # ==========================

    st.subheader(
        "👤 Spielerinformationen"
    )


    col1,col2,col3=st.columns(3)


    col1.write(
        f"Name: {auswahl[1]}"
    )


    col2.write(
        f"Position: {auswahl[3]}"
    )


    col3.write(
         f"Spielbein: {auswahl[4]}"
        )



    st.divider()



    # ==========================
    # Risiko
    # ==========================

    st.subheader(
        "🚦 Gesamtrisiko"
    )


    status,farbe=risiko_berechnen(fms,y)


    if farbe=="Rot":

        st.error(status)

    elif farbe=="Gelb":

        st.warning(status)

    else:

        st.success(status)




    # ==========================
    # FMS
    # ==========================

    st.divider()

    st.subheader(
        "📝 FMS Test"
    )


    if fms:

        st.metric(
            "FMS Score",
            f"{fms[15]}/21"
        )


        st.write(
            "Bewertung:",
            fms[16]
        )


        st.write(
            "Asymmetrie:",
            fms[17]
        )


        st.warning(
            fms[18]
        )


    else:

        st.info(
            "Kein FMS Test vorhanden"
        )



    
    # ==========================
    # Y Balance
    # ==========================

    st.divider()


    st.subheader(
        "📏 Y-Balance"
    )


    if y:


        col1,col2=st.columns(2)


        col1.metric(
            "Rechts",
            f"{y[12]}%"
        )


        col2.metric(
            "Links",
            f"{y[13]}%"
        )


        st.write(    
            y[14]
        )


        st.warning(
            y[15]
        )


    else:

        st.info(
            "Kein Y-Balance Test vorhanden"
        )



    # ==========================
    # Erkannte Defizite
    # ==========================

    st.divider()

    st.subheader(
        "🎯 Erkannte Defizite"
    )


    defizite = defizite_ermitteln(
        fms,
        y
    )


    if len(defizite) == 0:

        st.success(
            "Keine auffälligen Defizite erkannt."
        )


    else:


        for symbol, bereich, text in defizite:


            st.warning(
                f"""
                {symbol} **{bereich}**

                {text}
                """
            )



    # ==========================
    # Athletenbewertung
    # ==========================

    st.divider()

    st.subheader(
        "🧑‍⚽ Athletenbewertung"
    )


    analyse = athletenbewertung(
        fms,
        y
    )


    st.info(
        analyse
    )



    # ==========================
    # Trainer Empfehlung
    # ==========================



    st.divider()

   
    st.divider()


    st.subheader(
        "🏋️ Trainer Empfehlung"
    )


    # Schwerpunkt aus FMS und Y-Balance sammeln

    schwerpunkte = []


    if fms:

        schwerpunkte.append(
            str(fms[18]).lower()
        )


    if y:

        schwerpunkte.append(
            str(y[15]).lower()
        )



    if len(schwerpunkte) > 0:

        schwerpunkt = " ".join(schwerpunkte)


    else:

        st.write("FMS Schwerpunkt:", fms[18] if fms else "kein FMS")
        st.write("Y Schwerpunkt:", y[15] if y else "kein Y")
        st.write("Kein Schwerpunkt vorhanden")      



   

    bereiche = schwerpunkt_analyse(
        schwerpunkt
    )   



    # doppelte Bereiche entfernen

    bereiche = list(dict.fromkeys(bereiche))



    if bereiche:


        for bereich in bereiche:


            st.write(
                "##",
                bereich
            )


            übungen = training_nach_bereich(
                bereich
            )


            if not übungen:

                st.info(
                    "Keine Übungen gefunden"
                )


            for u in übungen:


                st.success(
f"""

Bereich:
🏋️ {u[0]}

Übungen:
{u[1]}

Probleme:
{u[2]}

Sätze:
{u[3]}

Wiederholungen:
{u[4]}

Häufigkeit:
{u[5]}
"""
                )


    else:


        st.info(
            "Kein Trainingsschwerpunkt erkannt"
        )




    # ================================
    # Individueller Trainingsplan
    # ================================

    st.divider()

    st.subheader(
        "📅 Individueller Trainingsplan"
)


    # immer initialisieren

    schwerpunkt = ""

    bereiche = []



    # FMS Schwerpunkt

    if fms:

        schwerpunkt += " " + str(fms[18]).lower()



    # Y-Balance Schwerpunkt

    if y:

        schwerpunkt += " " + str(y[15]).lower()



    st.write(
        "DEBUG Schwerpunkt:",
        schwerpunkt
)



    # ================================
    # Bereiche erkennen
    # ================================


    if "hüft" in schwerpunkt or "hüfte" in schwerpunkt or "huft" in schwerpunkt:

        bereiche.append("Hüfte")


    if "rumpf" in schwerpunkt or "core" in schwerpunkt or "becken" in schwerpunkt:

        bereiche.append("Rumpf")


    if "knie" in schwerpunkt:

        bereiche.append("Knie")


    if "sprunggelenk" in schwerpunkt:

        bereiche.append("Sprunggelenk")



    # doppelte entfernen

    bereiche = list(set(bereiche))



    # ================================
    # Bereiche erkennen
    # ================================

    # immer vorher erstellen
    plan = []


    if st.button("📅 Trainingsplan erstellen"):


        
        plan = trainingszyklus_erstellen(
            spieler_id,
            schwerpunkt
    )


        st.session_state["plan"] = periodisierung_laden(spieler_id)



    if "plan" in st.session_state:

        plan = st.session_state["plan"]

        st.success("Trainingsplan wurde erstellt!")


    else:

        plan = []

        st.info("Noch keinen Trainingsplan erstellt.")


    st.subheader(
        "📋 Dein Trainingsplan"
    )


    for p in plan:

        st.success(
    f"""
    🏋️ Woche: {p[0]}

    🔹 Phase:
    {p[1]}

    🎯 Ziel:
    {p[2]}

    Bereich:
    {p[3]}

    Übung:
    {p[4]}

    Intensität:
    {p[5]}

    Umfang:
    {p[6]}

    Häufigkeit:
    {p[7]}
    """
)


    