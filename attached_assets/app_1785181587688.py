import streamlit as st
from datetime import date


from database import (

    datenbank_erstellen,

    spieler_speichern,

    spieler_laden,

    fms_speichern,

    y_balance_speichern

)


from training import (

    training_standard_laden

)


from fms import (
  
    fms_score_berechnen,

    fms_bewertung,

    asymmetrie_pruefen,

    fms_problem_analyse

)


from dashboard import dashboard_anzeigen


from y_balance import y_balance_berechnen





# ==========================
# Datenbank starten
# ==========================

datenbank_erstellen()

training_standard_laden()





# ==========================
# Seite
# ==========================

st.set_page_config(

    page_title="Fußball Athletik System",

    layout="wide"

)



st.title(
    "⚽ Fußball Athletik Diagnostik System"
)





# ==========================
# Menü
# ==========================

menu = st.sidebar.selectbox(

    "Menü",

    [

        "Dashboard",

        "Spielerverwaltung",

        "FMS Test",

        "Y-Balance Test"

    ]

)





# ==========================
# Dashboard
# ==========================

if menu == "Dashboard":


    dashboard_anzeigen()





# ==========================
# Spielerverwaltung
# ==========================

elif menu == "Spielerverwaltung":


    st.header("👤 Spielerverwaltung")


    name = st.text_input("Name")

    geburtsdatum = st.text_input("Geburtsdatum")


    position = st.selectbox(

        "Position",

        [

            "Torwart",

            "Innenverteidiger",

            "Außenverteidiger",

            "Mittelfeld",

            "Flügel",

            "Stürmer"

        ]

    )


    spielbein = st.selectbox(

        "Spielbein",

        [

            "Rechts",

            "Links",

            "Beidfüßig"

        ]

    )


    mannschaft = st.text_input("Mannschaft")



    if st.button("💾 Spieler speichern"):


        spieler_speichern(

            name,

            geburtsdatum,

            position,

            spielbein,

            mannschaft

        )


        st.success(
            "Spieler gespeichert"
        )





# ==========================
# FMS TEST
# ==========================

elif menu == "FMS Test":


    st.header("📝 FMS Test")


    spieler = spieler_laden()



    if len(spieler)==0:


        st.warning(
            "Bitte zuerst Spieler anlegen"
        )


    else:


        auswahl = st.selectbox(

            "Spieler auswählen",

            spieler,

            format_func=lambda x:x[1]

        )


        spieler_id = auswahl[0]



        deep = st.number_input("Deep Squat",0,3)

        hurdle_l = st.number_input("Hurdle Links",0,3)

        hurdle_r = st.number_input("Hurdle Rechts",0,3)

        inline_l = st.number_input("Inline Links",0,3)

        inline_r = st.number_input("Inline Rechts",0,3)

        shoulder_l = st.number_input("Shoulder Links",0,3)

        shoulder_r = st.number_input("Shoulder Rechts",0,3)

        aslr_l = st.number_input("ASLR Links",0,3)

        aslr_r = st.number_input("ASLR Rechts",0,3)

        trunk = st.number_input("Trunk Stability",0,3)

        rotary_l = st.number_input("Rotary Links",0,3)

        rotary_r = st.number_input("Rotary Rechts",0,3)



        if st.button("✅ FMS speichern"):


            score = fms_score_berechnen(

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

                rotary_r

            )


            bewertung = fms_bewertung(score)


            asym = asymmetrie_pruefen(

                [

                    (hurdle_l,hurdle_r),

                    (inline_l,inline_r),

                    (shoulder_l,shoulder_r),

                    (aslr_l,aslr_r),

                    (rotary_l,rotary_r)

                ]

            )


            schwerpunkt = fms_problem_analyse(

                score,

                asym

            )


            fms_speichern(

                spieler_id,

                str(date.today()),

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

                asym,

                schwerpunkt

            )


            st.success("✅ FMS gespeichert")





# ==========================
# Y-BALANCE TEST
# ==========================

elif menu == "Y-Balance Test":


    st.header("📏 Y-Balance Test")


    spieler = spieler_laden()



    if len(spieler)==0:


        st.warning(
            "Bitte zuerst Spieler anlegen"
        )


    else:


        auswahl = st.selectbox(

            "Spieler auswählen",

            spieler,

            format_func=lambda x:x[1]

        )


        spieler_id = auswahl[0]


        st.subheader("Beinlänge")


        bein_r = st.number_input(

            "Beinlänge Rechts cm",

            min_value=1

        )


        bein_l = st.number_input(

            "Beinlänge Links cm",

            min_value=1

        )


        st.subheader("Rechte Seite")


        anterior_r = st.number_input("Anterior Rechts")

        posteromedial_r = st.number_input("Posteromedial Rechts")

        posterolateral_r = st.number_input("Posterolateral Rechts")



        st.subheader("Linke Seite")


        anterior_l = st.number_input("Anterior Links")

        posteromedial_l = st.number_input("Posteromedial Links")

        posterolateral_l = st.number_input("Posterolateral Links")





        if st.button("💾 Y-Balance berechnen und speichern"):



            ergebnis = y_balance_berechnen(


                anterior_r,

                anterior_l,


                posteromedial_r,

                posteromedial_l,


                posterolateral_r,

                posterolateral_l,


                bein_r,

                bein_l

            )



            y_balance_speichern(


                spieler_id,

                str(date.today()),


                anterior_r,

                anterior_l,


                posteromedial_r,

                posteromedial_l,


                posterolateral_r,

                posterolateral_l,


                ergebnis["diff_anterior"],

                ergebnis["diff_posteromedial"],

                ergebnis["diff_posterolateral"],


                ergebnis["composite_rechts"],

                ergebnis["composite_links"],


                ergebnis["asymmetrie"],

                ergebnis["schwerpunkt"]


            )




            st.success(
                "✅ Y-Balance Test gespeichert"
            )



            st.divider()



            st.subheader("Ergebnis")


            col1,col2 = st.columns(2)


            with col1:

                st.metric(

                    "Composite Rechts",

                    f"{ergebnis['composite_rechts']} %"

                )


            with col2:

                st.metric(

                    "Composite Links",

                    f"{ergebnis['composite_links']} %"

                )



            st.write(

                "Asymmetrie:",

                ergebnis["asymmetrie"]

            )


            st.write(

                "Trainingsschwerpunkt:",

                ergebnis["schwerpunkt"]

            )