"""
Wiederverwendbare UI-Komponenten für Testanleitungen.

Öffentliche API:
    sicherheitshinweis_box()                  — Pflicht-Sicherheitswarnung
    show_test_info(test_id)                   — Vollständige Testanleitung (Expander)
    show_field_help(test_id, field_id) -> str — Kurzhilfe-Text für help= Parameter
    field_info_col(col, test_id, field_id)    — ℹ️-Popover-Button in einer Spalte
"""
from __future__ import annotations
import base64
import os
import streamlit as st
from test_help import TEST_HELP, SICHERHEITSHINWEIS_ALLGEMEIN, COMPLIANCE_HINWEIS
from field_eval import badge_html as _badge_html, alter_zu_altersgruppe as _alter_zu_ag
from database import checkliste_custom_laden

_BASE = os.path.dirname(os.path.abspath(__file__))


def _svg_as_img(path: str) -> str:
    """Liest eine SVG-Datei und gibt einen fertigen <img>-Tag als HTML zurück.

    Durch Base64-Kodierung umgeht das Bild den Streamlit-HTML-Sanitizer,
    der komplexe SVG-Elemente wie <defs> und <marker> entfernt.
    """
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" '
        'style="width:100%;max-width:620px;display:block;margin:0 auto">'
    )


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
                st.markdown(_svg_as_img(bild_abs), unsafe_allow_html=True)
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


def norm_badge(
    value: float | int | None,
    test_id: str,
    field_id: str,
    container=None,
    altersgruppe: str | None = None,
) -> None:
    """Rendert einen farbigen Norm-Badge unterhalb eines Eingabefelds.

    container    — Streamlit-Container (z. B. eine Spalte). None → globaler st-Kontext.
    altersgruppe — Optional: "U10" | "U12" | "U14" | "U16" | "U18" | "Senior"
                   Aktiviert altersgerechte Normwerte statt Senior-Pauschalnormen.
    Zeigt nichts, wenn kein Normwert definiert ist oder value ist None/0.
    """
    html = _badge_html(value, test_id, field_id, altersgruppe)
    if not html:
        return
    target = container if container is not None else st
    target.markdown(html, unsafe_allow_html=True)


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
        # ── Übungs-SVG (wenn vorhanden, z. B. je FMS-Muster) ─────────────
        bild = feld.get("bild_pfad")
        if bild:
            bild_abs = os.path.join(_BASE, bild)
            if os.path.exists(bild_abs):
                st.markdown(_svg_as_img(bild_abs), unsafe_allow_html=True)
                st.markdown("")
        if feld.get("kurzhilfe"):
            st.info(feld["kurzhilfe"])
        if feld.get("eingabehilfe"):
            st.caption(f"✏️ Eingabe: {feld['eingabehilfe']}")
        if feld.get("bereich"):
            st.caption(f"📊 {feld['bereich']}")


# ─────────────────────────────────────────────────────────────────────────────
# Trainer-Checkliste
# ─────────────────────────────────────────────────────────────────────────────

# Standard-Checkliste falls kein Test spezifische liefert
_DEFAULT_CHECKLISTE: list[tuple[str, str]] = [
    ("🏟️", "Testfläche frei, rutschfest und ausreichend groß"),
    ("🛠️", "Material vollständig bereitgestellt und geprüft"),
    ("🔥", "Spieler mind. 10 Min. allgemein aufgewärmt"),
    ("📋", "Spieler über Ablauf, Ziel und Abbruchsignal informiert"),
    ("❓", "Akute Beschwerden oder Schmerzen beim Spieler abgefragt"),
    ("⏱️", "Stoppuhr / Messgerät bereit und kalibriert"),
    ("📝", "Testprotokoll / App geöffnet, Spieler ausgewählt"),
]

# Testspezifische Zusätze
_TEST_CHECKLISTE: dict[str, list[tuple[str, str]]] = {
    "sprint": [
        ("📐", "Startlinie und Lichtschrankenpositionen (10 m, 20 m, 30 m) ausgemessen"),
        ("🚦", "Lichtschranken oder manuelle Stoppuhr synchronisiert"),
        ("👟", "Spieler trägt Spikes oder geeignetes Schuhwerk"),
    ],
    "y_balance": [
        ("📏", "Y-Balance-Kit aufgebaut, Skalen auf 0 gesetzt"),
        ("🦵", "Standbeinlänge gemessen und notiert"),
        ("🔁", "3 Probewiederholungen je Seite absolviert"),
    ],
    "fms": [
        ("📏", "Hürde auf Hüfthöhe des Spielers eingestellt"),
        ("🪵", "FMS-Brett auf ebenem Untergrund ausgerichtet"),
        ("👣", "Spieler barfuß oder mit einheitlichem Schuhwerk"),
        ("🔕", "Kein Coaching während der Ausführung — nur beobachten"),
        ("📋", "Reihenfolge: Deep Squat → Hurdle → Lunge → Shoulder → ASLR → Trunk → Rotary"),
    ],
    "jump": [
        ("📐", "Kontaktmatte / Videokamera positioniert und gestartet"),
        ("📦", "Drop-Jump-Box auf Standsicherheit geprüft"),
        ("🦵", "3–5 submaximale Einsprünge als Einstimmung"),
    ],
    "agility": [
        ("📏", "Hütchen-Abstände nach Testprotokoll (T-Test / Illinois / 505 / 5-10-5) ausgemessen"),
        ("🚦", "Lichtschrankenstartlinie markiert"),
        ("🏃", "2 Probeläufe mit ~70% Intensität"),
    ],
    "yoyo": [
        ("🔊", "Audio-CD oder App-Ton geprüft (20 m korrekt kalibriert)"),
        ("📏", "20-m-Pendellinie und 5-m-Erholungszone markiert"),
        ("💧", "Spieler ist ausreichend hydriert"),
    ],
    "anthropometrie": [
        ("📏", "Maßband und Messzirkel gereinigt und auf 0 gesetzt"),
        ("🧍", "Spieler in Sportunterwäsche oder engem Outfit"),
        ("🔄", "Messungen je 2× — bei Abweichung > 5 mm: 3. Messung"),
    ],
}


def show_trainer_checkliste(test_id: str | None = None) -> None:
    """Zeigt eine interaktive Trainer-Checkliste vor dem Test.

    Ohne test_id erscheint nur die allgemeine Checkliste.
    Mit test_id werden testspezifische Punkte ergänzt.
    """
    punkte = list(_DEFAULT_CHECKLISTE)
    if test_id and test_id in _TEST_CHECKLISTE:
        punkte += _TEST_CHECKLISTE[test_id]

    test_name = ""
    if test_id:
        info = TEST_HELP.get(test_id)
        if info:
            test_name = f": {info['name']}"

    # Eigene Punkte aus DB laden und anhängen
    custom_text = checkliste_custom_laden(test_id or "")
    if custom_text:
        for line in custom_text.splitlines():
            line = line.strip()
            if line:
                punkte.append(("📌", line))

    with st.expander(f"✅ Trainer-Checkliste{test_name}", expanded=False):
        st.caption("Bitte vor dem Test abhaken — alle Punkte erfüllt?")
        alle_ok = True
        for icon, text in punkte:
            checked = st.checkbox(f"{icon} {text}", key=f"chk_{test_id}_{text[:20]}")
            if not checked:
                alle_ok = False
        if alle_ok:
            st.success("✅ Alle Punkte erledigt — Test kann beginnen!", icon="🚀")
        else:
            st.warning("Noch nicht alle Punkte abgehakt.", icon="⏳")
