"""Vereinsverwaltung — nur für Superadmin."""
import streamlit as st
from database import vereine_laden, verein_speichern, verein_aktivieren


def page_vereine():
    st.title("🏢 Vereinsverwaltung")
    st.caption("Nur für Superadmin sichtbar")

    vereine = vereine_laden()

    st.subheader("Vorhandene Vereine")
    if vereine:
        for v in vereine:
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.markdown(f"**{v['name']}**  `ID {v['id']}`")
            aktiv = c2.checkbox("Aktiv", value=bool(v["aktiv"]), key=f"va_{v['id']}")
            if c3.button("Speichern", key=f"vs_{v['id']}"):
                verein_aktivieren(v["id"], 1 if aktiv else 0)
                st.success("Gespeichert.")
                st.rerun()
    else:
        st.info("Noch keine Vereine vorhanden.")

    st.divider()
    st.subheader("Neuen Verein anlegen")
    name = st.text_input("Vereinsname", key="verein_neu_name")
    if st.button("✅ Verein speichern", key="verein_neu_btn"):
        if name.strip():
            verein_speichern(name.strip())
            st.success(f"Verein **{name}** angelegt.")
            st.rerun()
        else:
            st.error("Bitte einen Vereinsnamen eingeben.")
