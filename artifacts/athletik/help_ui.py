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
        # Fallback: Feld-Bild → Test-Hauptbild
        bild = feld.get("bild_pfad") or TEST_HELP.get(test_id, {}).get("bild_pfad")
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
# ─── Standard-Checkliste (gilt für ALLE Tests) ────────────────────────────────
# Quellen: NSCA Testing Guidelines; DFB Lizenztrainer-Empfehlungen;
#          Faigenbaum & Myer (2010) Sicherheitsprotokoll Jugendsport
_DEFAULT_CHECKLISTE: list[tuple[str, str]] = [
    # Umgebung & Material
    ("🏟️", "Testfläche frei, rutschfest, eben und ausreichend groß (min. Sicherheitsabstand 2 m)"),
    ("🛠️", "Material vollständig bereitgestellt, gereinigt und auf Funktion geprüft"),
    ("🌡️", "Umgebungstemperatur geprüft — optimal 15–25 °C, bei Hitze/Kälte Protokoll anpassen"),
    # Spieler-Vorbereitung
    ("🔥", "Spieler mind. 10 Min. allgemein aufgewärmt (Puls > 120 bpm)"),
    ("💧", "Ausreichende Flüssigkeitszufuhr sichergestellt (mind. 500 ml in letzter Stunde)"),
    ("🕐", "Mindestabstand zum letzten Hochintensitäts-Training: ≥ 24 Stunden"),
    # Aufklärung & Sicherheit
    ("📋", "Spieler über Ablauf, Ziel, Bewertungssystem und Abbruchsignal informiert"),
    ("❓", "Akute Beschwerden, Schmerzen oder Verletzungen beim Spieler abgefragt"),
    ("🚑", "Notfallprotokoll bekannt (Erste-Hilfe-Ausrüstung griffbereit, Notrufnummer bekannt)"),
    # Dokumentation
    ("⏱️", "Stoppuhr / Messgerät bereit, kalibriert und Nullpunkt geprüft"),
    ("📝", "Testprotokoll / App geöffnet, richtiger Spieler ausgewählt"),
    ("📸", "Videoaufnahme / Dokumentation nach Einwilligung vorbereitet"),
]

# ─── Testspezifische Checklisten ──────────────────────────────────────────────
_TEST_CHECKLISTE: dict[str, list[tuple[str, str]]] = {

    # ── Sprint ────────────────────────────────────────────────────────────────
    "sprint": [
        ("📐", "Startlinie und alle Lichtschrankenpositionen (10 m, 20 m, 30 m) exakt ausgemessen"),
        ("🚦", "Lichtschranken kalibriert ODER manuelle Stoppuhren synchronisiert (≥ 2 Zeitnehmer)"),
        ("👟", "Geeignetes Schuhwerk: Leichtathletik-Spikes oder Turnschuhe (keine Stollen)"),
        ("🌬️", "Windverhältnisse notiert — Rückenwind > 2 m/s: Ergebnis als windunterstützt kennzeichnen"),
        ("🔄", "Startposition und Startkommando erklärt (Standing Start / Crouch Start einheitlich)"),
        ("😴", "Mindestpause zwischen Versuchen: ≥ 3 Minuten (vollständige ZNS-Erholung)"),
        ("🏁", "Laufbahn eben, trocken und frei von Hindernissen bis 10 m hinter Ziellinie"),
    ],

    # ── Y-Balance ─────────────────────────────────────────────────────────────
    "y_balance": [
        ("📏", "Y-Balance-Kit aufgebaut, alle drei Schienen auf 0 cm gesetzt"),
        ("🦵", "Beinlänge (ASIS bis Malleolus medialis) gemessen und in App eingetragen"),
        ("🧦", "Spieler barfuß oder in Socken (kein Schuhwerk — verfälscht Ergebnis)"),
        ("🔁", "3 Probewiederholungen je Seite und Richtung ohne Wertung absolviert"),
        ("📋", "Reihenfolge eingehalten: Anterior → Posteromedial → Posterolateral"),
        ("❌", "Disqualifikationskriterien erklärt: Standbein verlassen, Boden berühren, Balance verloren, Anstoßen"),
        ("📐", "Markierungsband auf der Schiene (Höchstwert je Versuch sofort ablesen)"),
        ("🔄", "3 gewertete Versuche je Seite — bester Versuch zählt"),
    ],

    # ── FMS ───────────────────────────────────────────────────────────────────
    "fms": [
        ("📏", "Hürde auf exakte Hüfthöhe des Spielers eingestellt und kontrolliert"),
        ("🪵", "FMS-Brett auf ebenem Untergrund ausgerichtet, Befestigungsbolzen eingesteckt"),
        ("👣", "Spieler barfuß oder mit einheitlichem dünnen Schuhwerk"),
        ("🔕", "Kein Coaching oder Feedback während der Ausführung — ausschließlich beobachten"),
        ("📋", "Reihenfolge: Deep Squat → Hurdle Step → Inline Lunge → Shoulder Mobility → ASLR → Trunk Stability → Rotary Stability"),
        ("🎯", "Scoring-System erklärt: 3 = schmerzfrei korrekt, 2 = kompensiert, 1 = nicht möglich, 0 = Schmerz → sofort stoppen"),
        ("⚠️", "Bei Score 0 (Schmerz): Test sofort abbrechen, medizinische Abklärung empfehlen"),
        ("📊", "Bilateral: schlechteste Seite zählt als Gesamtscore"),
        ("📸", "Videoaufnahme aus sagittaler und frontaler Ebene für Nachbesprechung aktiv"),
    ],

    # ── Sprung / CMJ / Drop Jump ──────────────────────────────────────────────
    "jump": [
        ("📐", "Kontaktmatte ODER Videokamera positioniert, kalibriert und gestartet"),
        ("📦", "Drop-Jump-Box auf Standsicherheit und korrekte Höhe geprüft (30/40/60 cm)"),
        ("👟", "Geeignetes Schuhwerk: Turnschuhe mit flacher Sohle (keine Stollen)"),
        ("🦵", "3–5 submaximale Einsprünge als Einstimmung — anschließend 2 Min. Pause"),
        ("💨", "Armbewegung festgelegt: frei ODER fixiert (Hände in Hüfte) — einheitlich für alle"),
        ("📐", "Sprungrichtung senkrecht nach oben instruiert (kein Anlauf, kein Ausholschritt)"),
        ("🔄", "Mindestpause zwischen Versuchen: ≥ 30 Sekunden (Phosphatsystem erholen)"),
        ("🔢", "Anzahl der gewerteten Versuche festgelegt: Standard = 3 (bester zählt)"),
    ],

    # ── Agilität ──────────────────────────────────────────────────────────────
    "agility": [
        ("📏", "Hütchen-Abstände nach Testprotokoll exakt ausgemessen: T-Test / Illinois / 505 / 5-10-5"),
        ("🚦", "Lichtschrankenstartlinie markiert ODER Handstoppuhr synchronisiert"),
        ("🏃", "2 Probeläufe mit ~70% Intensität — Strecke und Richtungswechsel geübt"),
        ("👟", "Geeignetes Schuhwerk: Fußballschuhe mit Stollen oder Indoorschuhe (je nach Untergrund)"),
        ("↩️", "Technik erklärt: frontales vs. seitliches Abdrehen je nach Test"),
        ("🌬️", "Bei Außentest: Windverhältnisse und Untergrundqualität notiert"),
        ("🔄", "Mindestpause zwischen Versuchen: ≥ 2–3 Minuten (vollständige Erholung)"),
        ("🔢", "Anzahl Versuche: Standard = 2–3 (bester zählt)"),
    ],

    # ── Yo-Yo Ausdauer ────────────────────────────────────────────────────────
    "yoyo": [
        ("🔊", "Audio-Signal geprüft: App-Ton oder CD — 20-m-Distanz zur Signalfrequenz kalibriert"),
        ("📏", "20-m-Pendellinie und 5-m-Erholungszone mit Hütchen klar markiert"),
        ("💧", "Spieler ausreichend hydriert — mind. 500 ml in letzter Stunde"),
        ("🕐", "Test erst ≥ 48 Stunden nach letztem Hochintensitätstraining durchführen"),
        ("❤️", "Herzfrequenz-Monitor angelegt (optional — für Intensitätskontrolle)"),
        ("🚦", "Abbruchkriterien erklärt: 2× hintereinander Linie nicht rechtzeitig erreicht"),
        ("📋", "Yo-Yo-Testvariante festgelegt: Intermittent Recovery Level 1 oder Level 2"),
        ("🌡️", "Bei Temperaturen > 25 °C: erhöhte Monitoring-Frequenz, Abbruch bei Erschöpfung"),
    ],

    # ── Anthropometrie ────────────────────────────────────────────────────────
    "anthropometrie": [
        ("📏", "Maßband, Messzirkel (Kaliper) und Waage gereinigt, auf 0 gesetzt und kalibriert"),
        ("🧍", "Spieler in Sportunterwäsche oder engen Shorts (keine weite Kleidung)"),
        ("🌡️", "Raumtemperatur 20–22 °C — entspannte Muskulatur für valide Hautfaltenmessung"),
        ("🕐", "Messung morgens nüchtern ODER mind. 2 Stunden nach letzter Mahlzeit"),
        ("💧", "Keine intensive Belastung ≥ 24 Stunden vor Messung (Wasserhaushalt stabil)"),
        ("🔄", "Alle Maße je 2× gemessen — bei Abweichung > 5 mm / 0,5 kg: 3. Messung"),
        ("📐", "Körpergröße barfuß, aufrecht, Fersen und Rücken an Wand (Frankfort-Ebene)"),
        ("🗺️", "Messreihenfolge einhalten: Gewicht → Größe → Umfänge → Hautfalten"),
    ],

    # ── Kraft ─────────────────────────────────────────────────────────────────
    "kraft": [
        ("🏋️", "Geräte, Gewichte und Hanteln vollständig aufgebaut, gesichert und auf Funktion geprüft"),
        ("📏", "Aktuelle Körpermaße notiert (Gewicht, Größe) — Grundlage für relative Kraftwerte"),
        ("🔄", "Aufwärmsätze vollständig absolviert: 40% → 60% → 75% → 90% → 1RM-Versuch"),
        ("👀", "Sicherheitssicherung (Spotter) bei Freihanteln obligatorisch und eingewiesen"),
        ("⏱️", "Mindestpause zwischen Versuchen: 3–5 Minuten (vollständige Phosphatre-synthese)"),
        ("📋", "Testformat festgelegt: 1RM / 3RM / Kraftausdauer (% 1RM × Wiederholungen)"),
        ("🎯", "Bewegungsausführung standardisiert: Tiefe, Griffweite und Tempo definiert"),
        ("❌", "Abbruchkriterien erklärt: Kompensationsbewegung, Schmerz, unkontrollierte Ausführung"),
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
