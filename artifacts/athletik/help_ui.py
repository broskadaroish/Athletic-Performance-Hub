"""
Wiederverwendbare UI-Komponenten für Testanleitungen.

Öffentliche API:
    sicherheitshinweis_box()                  — Pflicht-Sicherheitswarnung
    show_test_info(test_id)                   — Vollständige Testanleitung (Expander)
    show_field_help(test_id, field_id) -> str — Kurzhilfe-Text für help= Parameter
    field_info_col(col, test_id, field_id)    — ℹ️-Popover-Button in einer Spalte
"""
from __future__ import annotations
import os
import streamlit as st
from test_help import TEST_HELP, SICHERHEITSHINWEIS_ALLGEMEIN, COMPLIANCE_HINWEIS

_BASE = os.path.dirname(os.path.abspath(__file__))


def sicherheitshinweis_box() -> None:
    """Zeigt den Pflicht-Sicherheitshinweis vor körperlich belastenden Tests."""
    st.warning(
        f"⚠️ **Sicherheitshinweis:** {SICHERHEITSHINWEIS_ALLGEMEIN}"
    )


def show_test_info(test_id: str) -> None:
    """Vollständige Testanleitung als aufklappbarer Bereich (st.expander)."""
    info = TEST_HELP.get(test_id)
    if not info:
        return

    with st.expander(f"📋 Testanleitung öffnen: {info['name']}", expanded=False):

        # ── SVG-Skizze ────────────────────────────────────────────────────────
        bild = info.get("bild_pfad")
        if bild:
            bild_abs = os.path.join(_BASE, bild)
            if os.path.exists(bild_abs):
                with open(bild_abs, encoding="utf-8") as fh:
                    st.markdown(fh.read(), unsafe_allow_html=True)
                st.caption(f"Abbildung: {info['name']} — Testaufbau")

        # ── Inhalt zweispaltig ────────────────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            if info.get("ziel"):
                st.markdown("**🎯 Ziel**")
                st.markdown(info["ziel"])
                st.markdown("")
            if info.get("material"):
                st.markdown("**🛠️ Material**")
                st.markdown(info["material"])
                st.markdown("")
            if info.get("aufbau"):
                st.markdown("**📐 Aufbau**")
                st.markdown(info["aufbau"])
                st.markdown("")
            if info.get("aufwaermung"):
                st.markdown("**🔥 Aufwärmung**")
                st.markdown(info["aufwaermung"])

        with col2:
            if info.get("durchfuehrung"):
                st.markdown("**▶️ Durchführung**")
                st.markdown(info["durchfuehrung"])
                st.markdown("")
            if info.get("trainerhinweis"):
                st.markdown("**👁️ Trainerhinweis**")
                st.markdown(info["trainerhinweis"])
                st.markdown("")
            versuche = info.get("versuche")
            pause    = info.get("pause")
            messwert = info.get("messwert")
            einheit  = info.get("einheit")
            if versuche: st.markdown(f"**🔁 Versuche:** {versuche}")
            if pause:    st.markdown(f"**⏱️ Pause:** {pause}")
            if messwert: st.markdown(f"**📏 Messwert:** {messwert}" + (f" ({einheit})" if einheit else ""))

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            if info.get("gueltiger_versuch"):
                st.markdown("**✅ Gültiger Versuch**")
                st.markdown(info["gueltiger_versuch"])
                st.markdown("")
            if info.get("ungueltiger_versuch"):
                st.markdown("**❌ Ungültiger Versuch**")
                st.markdown(info["ungueltiger_versuch"])
        with c4:
            if info.get("fehler"):
                st.markdown("**⚠️ Häufige Fehler**")
                for fehler in info["fehler"]:
                    st.markdown(f"- {fehler}")
                st.markdown("")
            if info.get("sicherheit"):
                st.markdown("**🛡️ Sicherheit**")
                st.markdown(info["sicherheit"])

        # ── Quellenangabe & Compliance ────────────────────────────────────────
        st.markdown("---")
        meta_parts = []
        if info.get("quelle"):  meta_parts.append(f"Quelle: {info['quelle']}")
        if info.get("version"): meta_parts.append(f"Version {info['version']}")
        if info.get("datum"):   meta_parts.append(info["datum"])
        if meta_parts:
            st.caption(" | ".join(meta_parts))
        st.info(COMPLIANCE_HINWEIS, icon="ℹ️")


def show_field_help(test_id: str, field_id: str) -> str:
    """Kurzhilfe-Text für den help= Parameter eines Streamlit-Widgets.

    Gibt einen lesbaren String zurück oder "" wenn kein Eintrag vorhanden.
    """
    feld = TEST_HELP.get(test_id, {}).get("felder", {}).get(field_id, {})
    parts: list[str] = []
    if feld.get("kurzhilfe"):   parts.append(feld["kurzhilfe"])
    if feld.get("bereich"):     parts.append(feld["bereich"])
    if feld.get("eingabehilfe"):parts.append(f"Eingabe: {feld['eingabehilfe']}")
    return "  \n".join(parts) if parts else ""


def field_info_col(col, test_id: str, field_id: str) -> None:
    """Zeigt einen ℹ️-Popover-Button mit Kurzhilfe zum Eingabefeld.

    Verwendung:
        header_col, info_col = st.columns([5, 1])
        header_col.markdown("**10 m**")
        field_info_col(info_col, "sprint", "sprint_10m")
    """
    feld = TEST_HELP.get(test_id, {}).get("felder", {}).get(field_id, {})
    if not feld:
        return
    label = feld.get("label", field_id)
    einheit = feld.get("einheit", "")
    with col.popover("ℹ️"):
        st.markdown(f"**{label}**" + (f" — {einheit}" if einheit else ""))
        if feld.get("ziel"):
            st.markdown(f"*{feld['ziel']}*")
            st.markdown("")
        if feld.get("kurzhilfe"):
            st.info(feld["kurzhilfe"])
        if feld.get("eingabehilfe"):
            st.caption(f"✏️ Eingabe: {feld['eingabehilfe']}")
        if feld.get("bereich"):
            st.caption(f"📊 {feld['bereich']}")
