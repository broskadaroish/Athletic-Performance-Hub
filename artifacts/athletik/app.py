"""
Football Athletik Diagnostik System
────────────────────────────────────
Main Streamlit entry point.  All pages live in this single file to keep
imports simple; shared logic is delegated to the module layer.
"""

import streamlit as st
from datetime import date, datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from theme import APP_CSS, C, PLOTLY_LAYOUT as _PL_BASE
from help_ui import sicherheitshinweis_box, show_test_info, show_field_help, field_info_col, norm_badge, show_trainer_checkliste
from ui_components import (
    kpi_card, score_kpi, risk_kpi,
    player_banner, section_header, deficit_row, strength_row,
    test_status_card, empty_state,
    score_badge_html, risk_badge_html,
)

from database import (
    init_db,
    spieler_speichern, spieler_laden, spieler_by_id, spieler_loeschen,
    berechne_alter, altersklasse_vorschlag,
    verletzung_speichern, verletzungen_laden, verletzung_loeschen,
    anthropometrie_speichern, anthropometrie_letzter, anthropometrie_history, anthropometrie_loeschen_letzten,
    fms_speichern, fms_letzter, fms_history,
    y_balance_speichern, y_balance_letzter, y_balance_history,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern, trainingsplan_laden,
    sprint_speichern, sprint_letzter, sprint_history,
    sprung_speichern, sprung_letzter, sprung_history,
    agilitaet_speichern, agilitaet_letzter, agilitaet_history,
    ausdauer_speichern, ausdauer_letzter, ausdauer_history,
    einwilligung_speichern, einwilligung_letzter, einwilligung_alle,
    db_komplett_zuruecksetzen,
    checkliste_custom_laden, checkliste_custom_speichern,
)
from safety_texts import (
    ZWECKBESTIMMUNG_VERSION,
    ZWECKBESTIMMUNG_TITEL,
    ZWECKBESTIMMUNG_TEXT_DISPLAY,
    AMPEL_GRUEN, AMPEL_GELB, AMPEL_ROT, AMPEL_FUSSZEILE,
    TRAININGSPLAN_HINWEIS,
    PHV_HINWEIS,
    FMS_HINWEIS,
    BESCHWERDEN_HINWEIS,
    ABBRUCH_HINWEIS,
    PDF_FUSSZEILE,
    KURZ_HINWEIS,
    EMAIL_NACHRICHT_VORLAGE,
)
from anthropometrie import (
    bmi_berechnen, bmi_kategorie, phv_offset_berechnen,
    reifestatus_text, reifestatus_farbe, wachstum_berechnen,
)
from sprint import SprintErgebnis
from sprung import SprungErgebnis
from agilitaet import AgilitaetErgebnis, bewertung as agil_bewertung, bewertung_farbe as agil_farbe
from ausdauer import AusdauerErgebnis, trainingsbereiche, bewertung_farbe as aus_farbe

# ─── Konstanten ───────────────────────────────────────────────────────────────

POSITIONEN = [
    "Torwart", "Innenverteidiger", "Außenverteidiger (rechts)",
    "Außenverteidiger (links)", "Defensives Mittelfeld", "Zentrales Mittelfeld",
    "Offensives Mittelfeld", "Rechtes Mittelfeld", "Linkes Mittelfeld",
    "Rechter Flügel", "Linker Flügel", "Hängende Spitze", "Mittelstürmer",
]
ALTERSKLASSEN = [
    "U7 (Bambini)", "U8/U9 (F-Jugend)", "U10/U11 (E-Jugend)",
    "U12/U13 (D-Jugend)", "U14/U15 (C-Jugend)", "U16/U17 (B-Jugend)",
    "U18/U19 (A-Jugend)", "Senioren", "Ü-Mannschaft",
]
LEISTUNGSNIVEAUS  = ["Breitensport", "Leistungssport", "Regionalkader", "Landeskader", "Bundeskader", "Profi"]
TRAININGSSTATUS   = [
    "Uneingeschränktes Mannschaftstraining",
    "Angepasstes Mannschaftstraining",
    "Individuelles Training",
    "Trainingspause",
    "Externe Abklärung empfohlen",
    "Externe Freigabe dokumentiert",
]
VERLETZUNGSARTEN  = ["Muskel", "Sehne / Band", "Knochen / Knorpel", "Prellung / Kontusion", "Sonstiges"]
KOERPERTEILE      = ["Sprunggelenk", "Knie", "Oberschenkel", "Leiste", "Hüfte", "Lendenwirbel", "Schulter", "Sonstiges"]
SCHWEREGRADE      = ["Leicht (1–7 Tage)", "Mittel (8–28 Tage)", "Schwer (> 28 Tage)"]
from training import init_training_bibliothek, empfehlung_bereiche, uebungen_fuer_bereiche
from fms import FMSResult
from y_balance import YBalanceResult
from analytics import (
    risiko_score, risiko_label, athletik_score, athletik_sub_scores,
    defizite_ermitteln, schwerpunkt_sammeln,
)
from periodisierung import zyklus_erstellen, zyklus_laden
from pdf_report import generate_report
from pdf_anleitung import generate_anleitung_pdf, ALL_TEST_IDS, TEST_LABELS
from export import kader_excel_bytes

# ─── Bootstrap ────────────────────────────────────────────────────────────────
init_db()
init_training_bibliothek()

# ─── Startup: Zweckbestimmung bestätigen ──────────────────────────────────────
def _zweck_bestaetigt() -> bool:
    """True wenn die Zweckbestimmung dieser Version bereits bestätigt wurde."""
    if st.session_state.get("zweck_bestaetigt"):
        return True
    letzter = einwilligung_letzter()
    if letzter and letzter.get("version") == ZWECKBESTIMMUNG_VERSION:
        st.session_state["zweck_bestaetigt"] = True
        return True
    return False

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Football Athletik Diagnostik",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject central design system ────────────────────────────────────────────
st.markdown(APP_CSS, unsafe_allow_html=True)

# ─── Startup-Gate: Zweckbestimmung muss bestätigt werden ─────────────────────
if not _zweck_bestaetigt():
    st.markdown(
        f'<div style="max-width:700px;margin:40px auto;padding:36px 40px;'
        f'background:#161b22;border:2px solid #d29922;border-radius:12px">'
        f'<div style="font-size:28px;text-align:center;margin-bottom:8px">⚠️</div>'
        f'<h2 style="color:#e6edf3;text-align:center;margin-bottom:4px">'
        f'Zweckbestimmung und Anwendungshinweise</h2>'
        f'<p style="color:#8b949e;text-align:center;font-size:12px;margin-bottom:24px">'
        f'Version {ZWECKBESTIMMUNG_VERSION} — Bitte vor der ersten Nutzung bestätigen</p>',
        unsafe_allow_html=True,
    )
    for absatz in ZWECKBESTIMMUNG_TEXT_DISPLAY.split("\n\n"):
        st.markdown(absatz)
    st.markdown(
        '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;'
        'padding:14px 16px;margin-top:20px;color:#f0a030;font-size:13px">'
        '⚠️ Diese Anwendung ist eine sportliche Trainings- und Dokumentationshilfe. '
        'Sie stellt keine medizinische Diagnose und erteilt keine medizinische Freigabe.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    benutzer_name = st.text_input(
        "Ihr Name (Trainer / Nutzer)",
        placeholder="z. B. Thomas Müller",
        key="zweck_benutzer",
    )
    bestaetigt = st.checkbox(
        "Ich habe die Zweckbestimmung und Anwendungshinweise gelesen und verstanden.",
        key="zweck_checkbox",
    )
    if st.button("✅ Bestätigen und App starten", type="primary",
                 disabled=not bestaetigt, use_container_width=True):
        name = benutzer_name.strip() or "Trainer"
        einwilligung_speichern(ZWECKBESTIMMUNG_VERSION, name)
        st.session_state["zweck_bestaetigt"] = True
        st.rerun()
    st.stop()


# ─── Helpers ──────────────────────────────────────────────────────────────────

# Delegate badge helpers to ui_components (keep aliases for existing page code)
def _risk_badge(level: str) -> str:
    return risk_badge_html(level)

def _score_badge(score: int) -> str:
    return score_badge_html(score)

def _progress_html(value: int, max_val: int, color: str = "#1f6feb") -> str:
    pct = min(value / max_val * 100, 100)
    return f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'

def _color_for_score(score: int, max_val: int = 100) -> str:
    pct = score / max_val
    if pct >= 0.75: return C["green"]
    if pct >= 0.5:  return C["yellow"]
    return C["red"]


def _player_selector(key_suffix="") -> dict | None:
    """Returns the globally selected player (no per-page dropdown rendered).
    The selector lives in the sidebar; all pages share the same active player."""
    spieler = spieler_laden()
    if not spieler:
        st.warning("👤 Noch keine Spieler angelegt. Gehe zu **Spieler → Verwaltung** um den ersten Spieler anzulegen.")
        return None
    pid = st.session_state.get("global_player_id")
    if pid:
        match = next((p for p in spieler if p["id"] == pid), None)
        if match:
            return match
    # Fallback to first player; also store in session state
    st.session_state["global_player_id"] = spieler[0]["id"]
    return spieler[0]


# ─── Plotly theme helper ───────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#e6edf3", family="Inter, Segoe UI, system-ui"),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
    margin=dict(l=40, r=20, t=40, b=40),
)

_AXIS_BASE = dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d")


def _pl(**overrides) -> dict:
    """Erstellt ein Plotly-Layout ohne doppelte Schlüsselkonflikte."""
    layout = {k: v for k, v in PLOTLY_LAYOUT.items()
              if k not in overrides and k not in ("xaxis", "yaxis")}
    layout["xaxis"] = {**_AXIS_BASE, **overrides.pop("xaxis", {})}
    layout["yaxis"] = {**_AXIS_BASE, **overrides.pop("yaxis", {})}
    layout.update(overrides)
    return layout


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    st.markdown("# ⚽ Coach Dashboard")
    st.markdown("---")

    all_players = spieler_laden()
    if not all_players:
        st.info("Noch keine Spieler angelegt. Gehe zur **Spielerverwaltung**, um Spieler hinzuzufügen.")
        return

    # ── Team overview metrics ──────────────────────────────────────────────
    total = len(all_players)
    high_risk, med_risk, low_risk = 0, 0, 0
    scores = []

    # Load all module data per player in one pass (also used for the table below)
    player_data = []
    for p in all_players:
        pid    = p["id"]
        fms    = fms_letzter(pid)
        y      = y_balance_letzter(pid)
        sprint = sprint_letzter(pid)
        sprung = sprung_letzter(pid)
        agil   = agilitaet_letzter(pid)
        aus    = ausdauer_letzter(pid)
        verlet = verletzungen_laden(pid)
        rs     = risiko_score(fms, y, verlet)
        _, level = risiko_label(rs)
        sc     = athletik_score(fms, y, sprint, sprung, agil, aus)
        if level == "hoch":    high_risk += 1
        elif level == "mittel": med_risk += 1
        else:                   low_risk += 1
        scores.append(sc)
        player_data.append({
            "p": p, "fms": fms, "y": y, "sprint": sprint, "sprung": sprung,
            "agil": agil, "aus": aus, "verlet": verlet, "rs": rs, "level": level, "sc": sc,
        })

    avg_score = round(sum(scores) / len(scores)) if scores else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spieler gesamt", total)
    c2.metric("Handlungsbedarf Hoch 🔴", high_risk)
    c3.metric("Handlungsbedarf 🟡", med_risk)
    c4.metric("Ø Athletik Score", f"{avg_score}/100")

    # ── Teamschnitt-Widgets für Sprint, CMJ, Yo-Yo (nur wenn ≥1 Datenpunkt) ──
    sprint_vals = [d["sprint"]["beste_10m"] for d in player_data
                   if d["sprint"] and d["sprint"].get("beste_10m")]
    cmj_vals    = [d["sprung"]["cmj_beid"] for d in player_data
                   if d["sprung"] and d["sprung"].get("cmj_beid")]
    yoyo_vals   = [d["aus"]["distanz_m"] for d in player_data
                   if d["aus"] and d["aus"].get("distanz_m")]

    if sprint_vals or cmj_vals or yoyo_vals:
        cols_kpi = st.columns(3)
        if sprint_vals:
            avg_s = sum(sprint_vals) / len(sprint_vals)
            cols_kpi[0].metric("Ø Sprint 10m", f"{avg_s:.2f} s",
                               help=f"Datenbasis: {len(sprint_vals)} Spieler")
        else:
            cols_kpi[0].metric("Ø Sprint 10m", "—", help="Noch keine Sprintdaten")
        if cmj_vals:
            avg_c = sum(cmj_vals) / len(cmj_vals)
            cols_kpi[1].metric("Ø CMJ", f"{avg_c:.1f} cm",
                               help=f"Datenbasis: {len(cmj_vals)} Spieler")
        else:
            cols_kpi[1].metric("Ø CMJ", "—", help="Noch keine Sprungdaten")
        if yoyo_vals:
            avg_y = sum(yoyo_vals) / len(yoyo_vals)
            cols_kpi[2].metric("Ø Yo-Yo Distanz", f"{avg_y:.0f} m",
                               help=f"Datenbasis: {len(yoyo_vals)} Spieler")
        else:
            cols_kpi[2].metric("Ø Yo-Yo Distanz", "—", help="Noch keine Ausdauerdaten")

    st.markdown("---")

    # ── Risk breakdown pie ─────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### Athletik-Status Verteilung")
        fig_pie = go.Figure(go.Pie(
            labels=["Handlungsbedarf Hoch", "Handlungsbedarf", "Unauffällig"],
            values=[high_risk, med_risk, low_risk],
            hole=0.55,
            marker_colors=["#f85149", "#d29922", "#3fb950"],
            textfont=dict(color="#e6edf3"),
        ))
        fig_pie.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=True,
                              legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.markdown("### Athletik Scores — Kader")
        names = [p["name"] for p in all_players]
        colors = [_color_for_score(s) for s in scores]
        fig_bar = go.Figure(go.Bar(
            x=names, y=scores,
            marker_color=colors,
            text=scores, textposition="outside",
            textfont=dict(color="#e6edf3"),
        ))
        fig_bar.update_layout(**_pl(height=260, yaxis=dict(range=[0, 105])))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### Spieler Einzelübersicht")

    # ── Per-player table ───────────────────────────────────────────────────
    rows = []
    for d in player_data:
        p, fms, y, sprint, sprung, agil, aus = (
            d["p"], d["fms"], d["y"], d["sprint"], d["sprung"], d["agil"], d["aus"]
        )
        level = d["level"]
        icon  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}[level]
        rows.append({
            "Name":           p["name"],
            "Position":       p["position"] or "—",
            "Mannschaft":     p["mannschaft"] or "—",
            "Athletik Score": d["sc"],
            "FMS Score":      fms["score"] if fms else "—",
            "Y-Balance Ø":    f"{(y['composite_rechts']+y['composite_links'])/2:.1f}%" if y else "—",
            "Sprint 10m":     f"{sprint['beste_10m']}s" if sprint and sprint.get("beste_10m") else "—",
            "CMJ":            f"{sprung['cmj_beid']}cm" if sprung and sprung.get("cmj_beid") else "—",
            "VO₂max":         f"{aus['vo2max']}" if aus and aus.get("vo2max") else "—",
            "Risiko":         f"{icon} {level.capitalize()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📥 Kader-Export")
    col_exp, _ = st.columns([1, 3])
    with col_exp:
        with st.spinner("Excel wird vorbereitet …"):
            excel_data = kader_excel_bytes()
        filename = f"Kader_Export_{date.today().strftime('%Y-%m-%d')}.xlsx"
        st.download_button(
            label="⬇️ Kader-Export (Excel)",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Exportiert alle Spieler-Stammdaten, letzte Testwerte und die gesamte Verletzungshistorie als Excel-Datei (2 Tabellenblätter).",
        )


# ──────────────────────────────────────────────────────────────────────────────

def page_spieler():
    st.markdown("# 👤 Spielerverwaltung")
    tab_add, tab_list = st.tabs(["➕ Neuen Spieler anlegen", "📋 Alle Spieler"])

    with tab_add:
        st.markdown("### Spieler hinzufügen")

        # ── Persönliche Daten ──────────────────────────────────────────────
        st.markdown("#### 👤 Persönliche Daten")
        c1, c2 = st.columns(2)
        vorname      = c1.text_input("Vorname *")
        nachname     = c2.text_input("Nachname *")
        geburtsdatum = c1.text_input("Geburtsdatum (TT.MM.JJJJ) *", placeholder="15.03.2008")
        geschlecht   = c2.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"])

        # Alter + Altersklasse automatisch
        alter = berechne_alter(geburtsdatum)
        ak_vorschlag = altersklasse_vorschlag(geburtsdatum)
        if alter:
            c1.markdown(f"<small style='color:#3fb950'>Alter: **{alter} Jahre** — Vorschlag: {ak_vorschlag}</small>", unsafe_allow_html=True)
        altersklasse = c2.selectbox("Altersklasse", ALTERSKLASSEN,
                                    index=ALTERSKLASSEN.index(ak_vorschlag) if ak_vorschlag in ALTERSKLASSEN else 7)

        st.markdown("#### 🏟️ Sportliche Daten")
        p1, p2 = st.columns(2)
        hauptposition = p1.selectbox("Hauptposition *", POSITIONEN)
        nebenposition = p2.selectbox("Nebenposition",   ["—"] + POSITIONEN)
        spielbein     = p1.selectbox("Spielbein",       ["Rechts", "Links", "Beidfüßig"])
        leistungsniveau = p2.selectbox("Leistungsniveau", LEISTUNGSNIVEAUS)

        st.markdown("#### 🏃 Teamdaten")
        t1, t2 = st.columns(2)
        mannschaft     = t1.text_input("Mannschaft / Verein")
        trainingsstatus = t2.selectbox("Trainingsstatus", TRAININGSSTATUS)

        st.markdown("---")
        if st.button("💾 Spieler speichern", use_container_width=False):
            if not vorname.strip() or not nachname.strip():
                st.error("Bitte Vor- und Nachnamen eingeben.")
            elif not geburtsdatum.strip():
                st.error("Bitte ein Geburtsdatum eingeben.")
            else:
                spieler_speichern(
                    vorname.strip(), nachname.strip(), geburtsdatum.strip(),
                    geschlecht, hauptposition,
                    nebenposition if nebenposition != "—" else "",
                    altersklasse, spielbein, leistungsniveau,
                    mannschaft.strip(), trainingsstatus,
                )
                st.success(f"✅ Spieler **{vorname} {nachname}** wurde gespeichert.")
                st.rerun()

    with tab_list:
        spieler = spieler_laden()
        if not spieler:
            st.info("Noch keine Spieler vorhanden.")
            return

        # Tabelle mit den relevanten Spalten
        zeilen = []
        for p in spieler:
            alter = berechne_alter(p.get("geburtsdatum"))
            zeilen.append({
                "Name":            p["name"],
                "Alter":           f"{alter} J." if alter else "—",
                "Altersklasse":    p.get("altersklasse") or "—",
                "Hauptposition":   p.get("hauptposition") or p.get("position") or "—",
                "Spielbein":       p.get("spielbein") or "—",
                "Mannschaft":      p.get("mannschaft") or "—",
                "Leistungsniveau": p.get("leistungsniveau") or "—",
                "Status":          p.get("trainingsstatus") or "Volltraining",
            })
        st.dataframe(pd.DataFrame(zeilen), use_container_width=True, hide_index=True)

        with st.expander("🗑️ Spieler löschen"):
            del_auswahl = st.selectbox("Spieler wählen", spieler, format_func=lambda x: x["name"], key="del_sel")
            st.warning("⚠️ Alle Testdaten dieses Spielers werden ebenfalls gelöscht.")
            if st.button("Spieler endgültig löschen", type="primary"):
                spieler_loeschen(del_auswahl["id"])
                st.success("Spieler gelöscht.")
                st.rerun()


# ──────────────────────────────────────────────────────────────────────────────

def page_fms():
    st.markdown("# 📝 FMS — Functional Movement Screen")
    st.markdown("Sieben Bewegungsmuster werden bilateral getestet. Maximalpunktzahl: **21 Punkte**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("fms")
    show_test_info("fms")

    auswahl = _player_selector("fms")
    if not auswahl:
        return

    spieler_id = auswahl["id"]

    st.markdown("---")
    st.markdown("### Testergebnisse eingeben")
    st.caption("Bewertung: 3 = korrekt | 2 = mit Kompensation | 1 = nicht möglich | 0 = Schmerzen. ℹ️ Tooltip an jedem Feld für Details.")

    _fh = lambda fid: show_field_help("fms", fid)

    def _fms_row(nr, label, key_l, key_r, fid):
        """Eine FMS-Zeile: Testname | Links | Rechts — mit ℹ️-Info-Button."""
        lbl_col, info_col = st.columns([8, 1])
        lbl_col.markdown(f"**{nr} · {label}**")
        field_info_col(info_col, "fms", fid)
        _cl, _cr = st.columns(2)
        l_val = _cl.number_input("Links",  0, 3, key=key_l, help=_fh(fid))
        r_val = _cr.number_input("Rechts", 0, 3, key=key_r, help=_fh(fid))
        norm_badge(l_val, "fms", fid, _cl)
        norm_badge(r_val, "fms", fid, _cr)
        return l_val, r_val

    # ── Test 1: Deep Squat (ein Gesamtscore) ─────────────────────────────────
    ds_lbl, ds_info = st.columns([8, 1])
    ds_lbl.markdown("**1 · Deep Squat** — ein Score (kein L/R)")
    field_info_col(ds_info, "fms", "deep_squat")
    _c1, _gap = st.columns([2, 4])
    deep = _c1.number_input("Punkte", 0, 3, key="ds", help=_fh("deep_squat"))
    norm_badge(deep, "fms", "deep_squat", _c1)

    st.markdown("---")
    st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
    # ── Test 2: Hurdle Step ───────────────────────────────────────────────────
    hurdle_l, hurdle_r     = _fms_row(2, "Hurdle Step",       "hl",  "hr",  "hurdle_step")
    # ── Test 3: Inline Lunge ─────────────────────────────────────────────────
    inline_l, inline_r     = _fms_row(3, "Inline Lunge",      "il",  "ir",  "inline_lunge")
    # ── Test 4: Shoulder Mobility ────────────────────────────────────────────
    shoulder_l, shoulder_r = _fms_row(4, "Shoulder Mobility", "shl", "shr", "shoulder")
    # ── Test 5: ASLR ─────────────────────────────────────────────────────────
    aslr_l, aslr_r         = _fms_row(5, "ASLR",              "al",  "ar",  "aslr")

    st.markdown("---")
    # ── Test 6: Trunk Stability Push-up (ein Gesamtscore) ────────────────────
    ts_lbl, ts_info = st.columns([8, 1])
    ts_lbl.markdown("**6 · Trunk Stability Push-up** — ein Score (kein L/R)")
    field_info_col(ts_info, "fms", "trunk_stability")
    _c6, _gap6 = st.columns([2, 4])
    trunk = _c6.number_input("Punkte", 0, 3, key="ts", help=_fh("trunk_stability"))
    norm_badge(trunk, "fms", "trunk_stability", _c6)

    st.markdown("---")
    st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
    # ── Test 7: Rotary Stability ──────────────────────────────────────────────
    rotary_l, rotary_r     = _fms_row(7, "Rotary Stability",  "rl",  "rr",  "rotary_stability")

    if st.button("✅ FMS speichern & auswerten", use_container_width=False):
        result = FMSResult(
            deep_squat=deep, hurdle_l=hurdle_l, hurdle_r=hurdle_r,
            inline_l=inline_l, inline_r=inline_r,
            shoulder_l=shoulder_l, shoulder_r=shoulder_r,
            aslr_l=aslr_l, aslr_r=aslr_r, trunk=trunk,
            rotary_l=rotary_l, rotary_r=rotary_r,
        )
        fms_speichern(
            spieler_id, str(date.today()),
            deep, hurdle_l, hurdle_r, inline_l, inline_r,
            shoulder_l, shoulder_r, aslr_l, aslr_r, trunk, rotary_l, rotary_r,
            result.score, result.bewertung, result.asymmetrie, result.schwerpunkt,
        )
        st.success("✅ FMS Test gespeichert!")

        st.markdown("---")
        st.markdown("### Ergebnis")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gesamtscore", f"{result.score} / 21")
        m2.metric("Bewertung", result.bewertung)
        m3.metric("Risikostufe", result.risiko_level.capitalize())

        st.markdown("#### Pattern-Scores")
        for name, val in result.pattern_scores.items():
            col = _color_for_score(val, 3)
            st.markdown(f"**{name}** — {val}/3 {_progress_html(val, 3, col)}", unsafe_allow_html=True)

        st.info(f"**Trainingsschwerpunkt:** {result.schwerpunkt}")
        if result.asymmetrie != "Keine Asymmetrie":
            st.warning(f"⚠️ {result.asymmetrie}")

    # ── Previous test
    last = fms_letzter(spieler_id)
    if last:
        with st.expander("📂 Letzter gespeicherter Test anzeigen"):
            l1, l2, l3 = st.columns(3)
            l1.metric("Score", f"{last['score']} / 21")
            l2.metric("Bewertung", last["bewertung"])
            l3.metric("Datum", last["datum"])
            st.write("**Asymmetrie:**", last["asymmetrie"])
            st.write("**Schwerpunkt:**", last["schwerpunkt"])


# ──────────────────────────────────────────────────────────────────────────────

def page_ybalance():
    st.markdown("# 📏 Y-Balance Test")
    st.markdown("Composite Score = (A + PM + PL) / (3 × Beinlänge) × 100.  Schwellenwert: **≥ 89 %**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("y_balance")
    show_test_info("y_balance")

    auswahl = _player_selector("yb")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    st.markdown("---")

    _fh = lambda fid: show_field_help("y_balance", fid)
    col1, col2 = st.columns(2)
    br_h, br_i = col1.columns([5, 1]); br_h.markdown("**Beinlänge Rechts (cm) \\***"); field_info_col(br_i, "y_balance", "beinlaenge")
    bein_r = col1.number_input("Beinlänge Rechts (cm) *", min_value=1.0, value=90.0, step=0.5,
                                label_visibility="collapsed", help=_fh("beinlaenge"))
    bl_h, bl_i = col2.columns([5, 1]); bl_h.markdown("**Beinlänge Links (cm) \\***"); field_info_col(bl_i, "y_balance", "beinlaenge")
    bein_l = col2.number_input("Beinlänge Links (cm) *",  min_value=1.0, value=90.0, step=0.5,
                                label_visibility="collapsed", help=_fh("beinlaenge"))

    st.markdown("#### Reichweiten (cm)")
    ch1, ch2 = st.columns(2)
    ch1.markdown("**Rechte Seite**")
    ch2.markdown("**Linke Seite**")
    ar_h, ar_i = ch1.columns([5, 1]); ar_h.markdown("**Anterior R (cm)**"); field_info_col(ar_i, "y_balance", "anterior")
    ant_r  = ch1.number_input("Anterior R",       0.0, 200.0, 0.0, step=0.5, key="antr", label_visibility="collapsed", help=_fh("anterior"))
    al_h, al_i = ch2.columns([5, 1]); al_h.markdown("**Anterior L (cm)**"); field_info_col(al_i, "y_balance", "anterior")
    ant_l  = ch2.number_input("Anterior L",       0.0, 200.0, 0.0, step=0.5, key="antl", label_visibility="collapsed", help=_fh("anterior"))
    pmr_h, pmr_i = ch1.columns([5, 1]); pmr_h.markdown("**Posteromedial R (cm)**"); field_info_col(pmr_i, "y_balance", "posteromedial")
    pm_r   = ch1.number_input("Posteromedial R",  0.0, 200.0, 0.0, step=0.5, key="pmr",  label_visibility="collapsed", help=_fh("posteromedial"))
    pml_h, pml_i = ch2.columns([5, 1]); pml_h.markdown("**Posteromedial L (cm)**"); field_info_col(pml_i, "y_balance", "posteromedial")
    pm_l   = ch2.number_input("Posteromedial L",  0.0, 200.0, 0.0, step=0.5, key="pml",  label_visibility="collapsed", help=_fh("posteromedial"))
    plr_h, plr_i = ch1.columns([5, 1]); plr_h.markdown("**Posterolateral R (cm)**"); field_info_col(plr_i, "y_balance", "posterolateral")
    pl_r   = ch1.number_input("Posterolateral R", 0.0, 200.0, 0.0, step=0.5, key="plr",  label_visibility="collapsed", help=_fh("posterolateral"))
    pll_h, pll_i = ch2.columns([5, 1]); pll_h.markdown("**Posterolateral L (cm)**"); field_info_col(pll_i, "y_balance", "posterolateral")
    pl_l   = ch2.number_input("Posterolateral L", 0.0, 200.0, 0.0, step=0.5, key="pll",  label_visibility="collapsed", help=_fh("posterolateral"))

    if st.button("💾 Y-Balance berechnen & speichern"):
        res = YBalanceResult(
            anterior_r=ant_r, anterior_l=ant_l,
            posteromedial_r=pm_r, posteromedial_l=pm_l,
            posterolateral_r=pl_r, posterolateral_l=pl_l,
            beinlaenge_r=bein_r, beinlaenge_l=bein_l,
        )
        y_balance_speichern(
            spieler_id, str(date.today()),
            ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
            res.diff_anterior, res.diff_posteromedial, res.diff_posterolateral,
            res.composite_r, res.composite_l,
            res.asymmetrie_text, res.schwerpunkt,
        )
        st.success("✅ Y-Balance Test gespeichert!")

        st.markdown("---")
        st.markdown("### Ergebnis")
        m1, m2, m3 = st.columns(3)
        m1.metric("Composite Rechts", f"{res.composite_r} %")
        m2.metric("Composite Links",  f"{res.composite_l} %")
        m3.metric("Risikostufe", res.risiko_level.capitalize())

        # Radar chart
        fig = go.Figure()
        categories = ["Anterior", "Posteromedial", "Posterolateral"]
        fig.add_trace(go.Scatterpolar(
            r=[ant_r / bein_r * 100, pm_r / bein_r * 100, pl_r / bein_r * 100],
            theta=categories, fill="toself", name="Rechts",
            line_color="#3b82f6",
        ))
        fig.add_trace(go.Scatterpolar(
            r=[ant_l / bein_l * 100, pm_l / bein_l * 100, pl_l / bein_l * 100],
            theta=categories, fill="toself", name="Links",
            line_color="#f85149",
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(visible=True, range=[0, 120], color="#8b949e", gridcolor="#30363d"),
                angularaxis=dict(color="#8b949e", gridcolor="#30363d"),
            ),
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            height=340, showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(f"**Trainingsschwerpunkt:** {res.schwerpunkt}")
        if res.asymmetrien:
            st.warning(f"⚠️ Asymmetrien erkannt: {', '.join(res.asymmetrien)}")

    last = y_balance_letzter(spieler_id)
    if last:
        with st.expander("📂 Letzter gespeicherter Test"):
            c1, c2 = st.columns(2)
            c1.metric("Composite Rechts", f"{last['composite_rechts']} %")
            c2.metric("Composite Links",  f"{last['composite_links']} %")
            st.write("**Asymmetrie:**", last["asymmetrie"])
            st.write("**Schwerpunkt:**", last["schwerpunkt"])


# ──────────────────────────────────────────────────────────────────────────────

def page_spieler_profil():
    st.markdown("# 🏃 Spielerprofil & Diagnostik")

    auswahl = _player_selector("profil")
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    anthro = anthropometrie_letzter(sid)
    verlet = verletzungen_laden(sid)
    rs     = risiko_score(fms, y, verlet)
    label, level = risiko_label(rs)
    ascore   = athletik_score(fms, y, sprint, sprung, agil, aus)
    defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro)
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus)
    alter = berechne_alter(auswahl.get("geburtsdatum"))

    # ── Header ────────────────────────────────────────────────────────────
    h1, h2, h3 = st.columns([2, 1, 1])
    with h1:
        st.markdown(f"## {auswahl['name']}")
        haupt = auswahl.get("hauptposition") or auswahl.get("position") or "—"
        neben = auswahl.get("nebenposition") or ""
        pos_str = f"{haupt}" + (f" / {neben}" if neben else "")
        info_zeile = (
            f"🎂 {alter} Jahre  ·  "
            f"⚽ {pos_str}  ·  "
            f"🏟️ {auswahl.get('mannschaft') or '—'}  ·  "
            f"🦵 Spielbein: {auswahl.get('spielbein') or '—'}"
        )
        st.markdown(f"<small style='color:#8b949e'>{info_zeile}</small>", unsafe_allow_html=True)
        ak = auswahl.get("altersklasse") or "—"
        niv = auswahl.get("leistungsniveau") or "—"
        status = auswahl.get("trainingsstatus") or "Volltraining"
        status_color = (
            "#f85149" if any(x in status.lower() for x in ["pause", "abklärung", "abklaerung"])
            else "#d29922" if any(x in status.lower() for x in ["angepasst", "individuell", "freigabe"])
            else "#3fb950"
        )
        st.markdown(
            f"<small style='color:#8b949e'>{ak}  ·  {niv}  ·  "
            f"<span style='color:{status_color};font-weight:600'>{status}</span></small>",
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown("**Athletik Score**")
        st.markdown(_score_badge(ascore), unsafe_allow_html=True)
    with h3:
        st.markdown("**Athletik-Status**")
        st.markdown(_risk_badge(level), unsafe_allow_html=True)

    # ── Radar-Chart im Header (wenn ≥ 3 Module vorhanden) ─────────────────
    sub_scores_header = athletik_sub_scores(fms, y, sprint, sprung, agil, aus)
    if len(sub_scores_header) >= 3:
        label_map_h = {
            "FMS": "FMS", "Y-Balance": "Y-Balance", "Sprint": "Sprint",
            "Sprungkraft": "Sprungkraft", "Agilitaet": "Agilität", "Ausdauer": "Ausdauer",
        }
        cats_h  = [label_map_h.get(k, k) for k in sub_scores_header.keys()]
        vals_h  = list(sub_scores_header.values())
        cats_hc = cats_h + [cats_h[0]]
        vals_hc = vals_h + [vals_h[0]]
        fig_hdr = go.Figure()
        fig_hdr.add_trace(go.Scatterpolar(
            r=vals_hc, theta=cats_hc,
            fill="toself", name="Profil",
            line=dict(color="#3b82f6", width=2),
            fillcolor="rgba(59,130,246,0.18)",
            marker=dict(size=7, color="#58a6ff"),
        ))
        fig_hdr.update_layout(
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(visible=True, range=[0, 100],
                               color="#8b949e", gridcolor="#30363d",
                               tickfont=dict(size=8)),
                angularaxis=dict(color="#e6edf3", gridcolor="#30363d",
                                 tickfont=dict(size=10)),
            ),
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            height=280, showlegend=False, margin=dict(l=40, r=40, t=20, b=20),
        )
        _, rc = st.columns([3, 2])
        with rc:
            st.plotly_chart(fig_hdr, use_container_width=True)

    st.markdown("---")

    # ── Key metrics ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("FMS Score",      f"{fms['score']}/21" if fms else "Kein Test")
    m2.metric("FMS Bewertung",  fms["bewertung"] if fms else "—")
    if y:
        avg_y = (y["composite_rechts"] + y["composite_links"]) / 2
        m3.metric("Y-Balance Ø",    f"{avg_y:.1f} %")
        m4.metric("Y-Balance Asym.", y["asymmetrie"][:25])
    else:
        m3.metric("Y-Balance",  "Kein Test")
        m4.metric("Y-Balance",  "—")

    st.markdown("---")

    # ── Tabs: Defizite / Verletzungshistorie / PDF ─────────────────────────
    tab_def, tab_verletz, tab_pdf = st.tabs(["🎯 Defizite & Empfehlungen", "🩹 Verletzungshistorie", "📄 PDF Report"])

    with tab_def:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🎯 Erkannte Defizite")
            if not defizite:
                st.success("✅ Keine auffälligen Defizite erkannt.")
            else:
                for d in defizite:
                    css   = "tag-crit" if d["level"] == "kritisch" else "tag-warn"
                    modul = d.get("modul", "")
                    modul_badge = (
                        f'<span style="font-size:10px;color:#8b949e;background:#21262d;'
                        f'border-radius:4px;padding:1px 6px;margin-left:6px">{modul}</span>'
                        if modul else ""
                    )
                    st.markdown(
                        f'<div class="card"><span class="{css}">{d["bereich"]}</span>'
                        f'{modul_badge}'
                        f'<br><small style="color:#8b949e">{d["text"]}</small></div>',
                        unsafe_allow_html=True,
                    )
        with col_r:
            st.markdown("### 🏋️ Trainingsempfehlungen")
            bereiche = empfehlung_bereiche(schwerpunkt)
            if not bereiche:
                st.info("Kein spezifischer Trainingsschwerpunkt erkannt.")
            else:
                for bereich, uebungen in uebungen_fuer_bereiche(bereiche).items():
                    with st.expander(f"**{bereich}** — {len(uebungen)} Übungen"):
                        for u in uebungen:
                            st.markdown(
                                f"**{u['uebung']}**  \n"
                                f"Problem: {u['problem']} · {u['saetze']} Sätze · "
                                f"{u['wiederholungen']} · {u['haeufigkeit']}"
                            )

    with tab_verletz:
        st.markdown("### 🩹 Verletzungshistorie")

        # Neue Verletzung eintragen
        with st.expander("➕ Neue Verletzung eintragen"):
            va1, va2 = st.columns(2)
            v_datum      = va1.text_input("Datum (TT.MM.JJJJ)", value=date.today().strftime("%d.%m.%Y"), key="v_dat")
            v_art        = va2.selectbox("Verletzungsart", VERLETZUNGSARTEN, key="v_art")
            v_koerper    = va1.selectbox("Körperteil", KOERPERTEILE, key="v_koerper")
            v_schwere    = va2.selectbox("Schweregrad", SCHWEREGRADE, key="v_schwere")
            v_ausfall    = va1.number_input("Ausfalltage (geschätzt)", 0, 365, 0, key="v_ausfall")
            v_notizen    = st.text_area("Notizen / Anmerkungen", key="v_notizen", height=80)
            if st.button("💾 Verletzung speichern", key="v_save"):
                verletzung_speichern(sid, v_datum, v_art, v_koerper, v_schwere, int(v_ausfall), v_notizen)
                st.success("✅ Verletzung gespeichert.")
                st.rerun()

        # Verletzungsliste
        verletzungen = verletzungen_laden(sid)
        if not verletzungen:
            st.info("Noch keine Verletzungen eingetragen.")
        else:
            gesamt_ausfall = sum(v.get("ausfall_tage") or 0 for v in verletzungen)
            va, vb = st.columns(2)
            va.metric("Einträge gesamt", len(verletzungen))
            vb.metric("Ausfalltage gesamt", gesamt_ausfall)
            st.markdown("---")
            for v in verletzungen:
                schwere_color = (
                    "#f85149" if "schwer" in (v.get("schwere") or "").lower()
                    else "#d29922" if "mittel" in (v.get("schwere") or "").lower()
                    else "#3fb950"
                )
                st.markdown(
                    f'<div class="card">'
                    f'<div style="display:flex;justify-content:space-between">'
                    f'<span style="font-weight:700;color:#e6edf3">{v.get("koerperteil","—")} — {v.get("art","—")}</span>'
                    f'<span style="color:#8b949e;font-size:13px">{v.get("datum","")}</span>'
                    f'</div>'
                    f'<span style="color:{schwere_color};font-size:12px;font-weight:600">{v.get("schwere","—")}</span>'
                    f'  ·  <span style="color:#8b949e;font-size:12px">{v.get("ausfall_tage",0)} Ausfalltage</span>'
                    + (f'<br><small style="color:#8b949e">{v["notizen"]}</small>' if v.get("notizen") else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )
            with st.expander("🗑️ Verletzungseintrag löschen"):
                del_v = st.selectbox(
                    "Eintrag wählen", verletzungen,
                    format_func=lambda x: f"{x.get('datum','')} — {x.get('koerperteil','')} ({x.get('art','')})",
                    key="del_v",
                )
                if st.button("Eintrag löschen", key="del_v_btn"):
                    verletzung_loeschen(del_v["id"])
                    st.success("Gelöscht.")
                    st.rerun()

    with tab_pdf:
        st.markdown("### 📄 PDF Report")
        st.markdown(
            "Der Bericht enthält alle vorhandenen Testergebnisse: "
            "Anthropometrie, FMS, Y-Balance, Sprint, Sprung, Agilität, Ausdauer, "
            "Verletzungshistorie, Defizite und Trainingsplan."
        )
        plan_rows   = zyklus_laden(sid)
        anthro_row  = anthropometrie_letzter(sid)
        sprint_row  = sprint_letzter(sid)
        sprung_row  = sprung_letzter(sid)
        agil_row    = agilitaet_letzter(sid)
        aus_row     = ausdauer_letzter(sid)
        verletzungen_pdf = verletzungen_laden(sid)

        # Anzahl vorhandener Module anzeigen
        module = {
            "FMS": fms, "Y-Balance": y, "Anthropometrie": anthro_row,
            "Sprint": sprint_row, "Sprung": sprung_row,
            "Agilität": agil_row, "Ausdauer": aus_row,
        }
        vorh = [k for k, v in module.items() if v]
        fehlt = [k for k, v in module.items() if not v]
        if vorh:
            st.success(f"✅ Enthaltene Module: {', '.join(vorh)}")
        if fehlt:
            st.info(f"ℹ️ Noch keine Daten: {', '.join(fehlt)}")

        if st.button("📥 PDF Report generieren", key="pdf_gen"):
            pdf_bytes = generate_report(
                spieler=auswahl,
                fms_row=fms,
                y_row=y,
                anthro_row=anthro_row,
                sprint_row=sprint_row,
                sprung_row=sprung_row,
                agil_row=agil_row,
                aus_row=aus_row,
                verletzungen=verletzungen_pdf,
                athletik_score=ascore,
                risiko_label=label,
                defizite=defizite,
                plan_rows=plan_rows,
            )
            st.session_state["pdf_bytes_cache"] = pdf_bytes
            st.download_button(
                label="⬇️ PDF herunterladen",
                data=pdf_bytes,
                file_name=f"athletik_report_{auswahl['name'].replace(' ','_')}_{date.today()}.pdf",
                mime="application/pdf",
                key="pdf_dl",
            )

        st.markdown("---")
        st.markdown("### 📧 E-Mail vorbereiten")
        st.caption(
            "Erstelle eine vorbereitete E-Mail mit dem Pflichthinweis aus den "
            "Anwendungshinweisen. Die E-Mail wird in deinem Standard-Mail-Programm geöffnet."
        )
        ec1, ec2 = st.columns(2)
        email_empfaenger = ec1.text_input(
            "Empfänger-Adresse", placeholder="spieler@beispiel.de", key="email_to"
        )
        email_trainername = ec2.text_input(
            "Absender / Trainername", key="email_trainer",
            value=st.session_state.get("cfg_vereinsname", ""),
            placeholder="Dein Name oder Vereinsname"
        )
        spieler_name = auswahl.get("name", "Spieler")
        email_betreff = f"Athletik Testprotokoll – {spieler_name} – {date.today().strftime('%d.%m.%Y')}"
        email_text = EMAIL_NACHRICHT_VORLAGE.format(
            trainername=email_trainername.strip() or "Trainer"
        )
        email_text_edit = email_text
        with st.expander("📋 E-Mail-Text Vorschau / bearbeiten"):
            email_text_edit = st.text_area(
                "E-Mail-Text (bearbeitbar)", value=email_text,
                height=160, key="email_text_edit",
                label_visibility="collapsed"
            )

        import urllib.parse
        mailto_body  = urllib.parse.quote(email_text_edit)
        mailto_subj  = urllib.parse.quote(email_betreff)
        mailto_link  = f"mailto:{email_empfaenger}?subject={mailto_subj}&body={mailto_body}"
        st.link_button(
            "📨 E-Mail-Programm öffnen",
            url=mailto_link,
            use_container_width=True,
        )
        st.info(
            "💡 Der Pflichthinweis ist im E-Mail-Text enthalten. "
            "Hänge den heruntergeladenen PDF-Report manuell als Anhang an."
        )


# ──────────────────────────────────────────────────────────────────────────────

def page_trainingsplan():
    st.markdown("# 📅 Trainingsplan")

    auswahl = _player_selector("plan")
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus)

    tab_auto, tab_manual, tab_view = st.tabs(["🤖 Automatisch generieren", "✍️ Manuell hinzufügen", "📋 Plan anzeigen"])

    with tab_auto:
        st.markdown("### Individuellen Plan aus Diagnostik generieren")
        bereiche = empfehlung_bereiche(schwerpunkt)
        if bereiche:
            st.info(f"**Erkannte Schwerpunkte aus allen Testmodulen:** {', '.join(bereiche)}")
        else:
            st.warning("Kein Diagnostik-Schwerpunkt vorhanden. Standard-Plan wird erstellt.")

        if st.button("⚡ Trainingsplan jetzt erstellen"):
            trainingsplan_loeschen(sid)
            alle_uebungen = uebungen_fuer_bereiche(bereiche or ["Hüfte", "Rumpf", "Knie"])
            woche = 1
            for bereich, uebungen in alle_uebungen.items():
                for u in uebungen:
                    trainingsplan_eintrag_speichern(
                        sid, str(date.today()), woche,
                        u["bereich"], u["uebung"], u["saetze"], u["wiederholungen"], u["haeufigkeit"],
                    )
                woche = min(woche + 1, 4)
            st.success("✅ Trainingsplan wurde erstellt!")
            st.rerun()

    with tab_manual:
        st.markdown("### Übung manuell hinzufügen")
        mc1, mc2 = st.columns(2)
        bereich   = mc1.selectbox("Bereich", ["Sprunggelenk","Knie","Hüfte","Rumpf","Oberschenkel","Schnelligkeit","Explosivität","Agilität","Fußball"])
        uebung    = mc2.text_input("Übungsname")
        saetze    = mc1.text_input("Sätze",           "3")
        wdh       = mc2.text_input("Wiederholungen",  "10")
        haeufigkeit = mc1.text_input("Häufigkeit",    "2x Woche")
        woche     = mc2.number_input("Woche",          1, 12, 1)
        if st.button("➕ Übung speichern"):
            trainingsplan_eintrag_speichern(sid, str(date.today()), woche, bereich, uebung, saetze, wdh, haeufigkeit)
            st.success("Übung gespeichert!")
            st.rerun()

    with tab_view:
        plan = trainingsplan_laden(sid)
        if not plan:
            st.info("Noch kein Trainingsplan vorhanden.")
            return

        df = pd.DataFrame(plan)
        df.columns = ["Bereich", "Übung", "Sätze", "Wdh.", "Häufigkeit", "Woche"]
        df = df[["Woche", "Bereich", "Übung", "Sätze", "Wdh.", "Häufigkeit"]]

        for woche_nr in sorted(df["Woche"].unique()):
            with st.expander(f"**Woche {woche_nr}**", expanded=(woche_nr == 1)):
                sub = df[df["Woche"] == woche_nr].drop("Woche", axis=1)
                st.dataframe(sub, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_periodisierung():
    st.markdown("# 🔄 12-Wochen-Periodisierung")
    st.markdown("Vollautomatischer Trainingszyklus in 3 Phasen: Stabilisation → Kraftaufbau → Fußballspezifisch.")

    auswahl = _player_selector("perio")
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus)

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown("""
        | Phase | Wochen | Ziel |
        |---|---|---|
        | 1 — Stabilisation | 1–4 | Bewegungsqualität & Verletzungsprävention |
        | 2 — Kraftaufbau   | 5–8 | Maximalkraft & funktionelle Stärke |
        | 3 — Fußballspezifisch | 9–12 | Leistung & Wettkampfvorbereitung |
        """)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Zyklus erstellen / neu generieren", use_container_width=True):
            zyklus_erstellen(sid, schwerpunkt)
            st.success("✅ 12-Wochen-Zyklus generiert!")
            st.rerun()

    plan = zyklus_laden(sid)
    if not plan:
        st.info("Noch kein Periodisierungsplan vorhanden. Klicke auf **Zyklus erstellen**.")
        return

    df = pd.DataFrame(plan)
    df.columns = ["Woche", "Phase", "Ziel", "Bereich", "Übung", "Intensität", "Volumen", "Häufigkeit"]

    # Phase colour map
    phase_colors = {
        "Phase 1 — Stabilisation":      "#1f6feb",
        "Phase 2 — Kraftaufbau":         "#3fb950",
        "Phase 3 — Fußballspezifisch":   "#d29922",
    }

    for phase_name, color in phase_colors.items():
        sub = df[df["Phase"] == phase_name]
        if sub.empty:
            continue
        weeks = sorted(sub["Woche"].unique())
        label = f"**{phase_name}** — Wochen {weeks[0]}–{weeks[-1]}"
        st.markdown(f'<div style="border-left:4px solid {color};padding-left:12px;margin:16px 0 6px">'
                    f'<h4 style="color:{color};margin:0">{phase_name}</h4>'
                    f'<small style="color:#8b949e">{sub.iloc[0]["Ziel"]}</small></div>',
                    unsafe_allow_html=True)
        for woche_nr in weeks:
            w_sub = sub[sub["Woche"] == woche_nr][["Bereich", "Übung", "Intensität", "Volumen", "Häufigkeit"]]
            with st.expander(f"Woche {woche_nr}", expanded=(woche_nr == weeks[0])):
                st.dataframe(w_sub, use_container_width=True, hide_index=True)

    # Download plan CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Plan als CSV herunterladen", csv,
                       f"periodisierung_{auswahl['name'].replace(' ','_')}.csv", "text/csv")


# ──────────────────────────────────────────────────────────────────────────────

def page_fortschritt():
    st.markdown("# 📈 Fortschrittsverfolgung")

    auswahl = _player_selector("prog")
    if not auswahl:
        return

    sid = auswahl["id"]
    st.markdown(f"### {auswahl['name']} — historische Testergebnisse")

    fms_hist    = fms_history(sid)
    yb_hist     = y_balance_history(sid)
    sprint_hist = sprint_history(sid)
    sprung_hist = sprung_history(sid)
    agil_hist   = agilitaet_history(sid)
    aus_hist    = ausdauer_history(sid)
    anthro_hist = anthropometrie_history(sid)

    tab_radar, tab_fms, tab_yb, tab_sprint, tab_sprung, tab_agil, tab_aus, tab_anthro = st.tabs([
        "🕸️ Athletisches Profil",
        "FMS Verlauf",
        "Y-Balance Verlauf",
        "Sprint Verlauf",
        "Sprung Verlauf",
        "Agilität Verlauf",
        "Ausdauer Verlauf",
        "Anthropometrie Verlauf",
    ])

    # ── Athletisches Profil — Radar-Chart ────────────────────────────────────
    with tab_radar:
        fms_now    = fms_letzter(sid)
        y_now      = y_balance_letzter(sid)
        sprint_now = sprint_letzter(sid)
        sprung_now = sprung_letzter(sid)
        agil_now   = agilitaet_letzter(sid)
        aus_now    = ausdauer_letzter(sid)
        sub = athletik_sub_scores(fms_now, y_now, sprint_now, sprung_now, agil_now, aus_now)

        if len(sub) < 2:
            st.info("Mindestens 2 Testmodule müssen vorliegen, um das Radar-Chart zu zeichnen.")
        else:
            # Label-Mapping für Anzeige
            label_map = {
                "FMS": "FMS",
                "Y-Balance": "Y-Balance",
                "Sprint": "Sprint",
                "Sprungkraft": "Sprungkraft",
                "Agilitaet": "Agilität",
                "Ausdauer": "Ausdauer",
            }
            cats   = [label_map.get(k, k) for k in sub.keys()]
            vals   = list(sub.values())
            # Radar geschlossen
            cats_closed = cats + [cats[0]]
            vals_closed = vals + [vals[0]]

            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(
                r=vals_closed, theta=cats_closed,
                fill="toself", name="Aktuell",
                line=dict(color="#3b82f6", width=2),
                fillcolor="rgba(59,130,246,0.15)",
                marker=dict(size=8, color="#58a6ff"),
            ))
            # Referenzlinie 70 (Teamziel)
            ref_cats = cats + [cats[0]]
            ref_vals = [70] * len(ref_cats)
            fig_r.add_trace(go.Scatterpolar(
                r=ref_vals, theta=ref_cats,
                mode="lines", name="Teamziel 70",
                line=dict(color="#d29922", width=1, dash="dash"),
            ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="#161b22",
                    radialaxis=dict(visible=True, range=[0, 100],
                                   color="#8b949e", gridcolor="#30363d",
                                   tickfont=dict(size=9)),
                    angularaxis=dict(color="#e6edf3", gridcolor="#30363d"),
                ),
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                height=420, showlegend=True,
                legend=dict(orientation="h", y=-0.1),
                title=dict(text="Athletisches Profil (normiert 0–100)", font=dict(color="#e6edf3")),
            )
            col_rad, col_tbl = st.columns([3, 2])
            with col_rad:
                st.plotly_chart(fig_r, use_container_width=True)
            with col_tbl:
                st.markdown("### Modulscores")
                for k, v in sub.items():
                    label = label_map.get(k, k)
                    bar_color = "#3fb950" if v >= 75 else "#d29922" if v >= 50 else "#f85149"
                    st.markdown(
                        f"**{label}** — {v}/100 "
                        f"<span style='display:inline-block;width:{v}px;max-width:100px;"
                        f"height:8px;background:{bar_color};border-radius:4px;vertical-align:middle'></span>",
                        unsafe_allow_html=True,
                    )

    # ── FMS ──────────────────────────────────────────────────────────────────
    with tab_fms:
        if not fms_hist:
            st.info("Noch keine FMS Tests vorhanden.")
        else:
            df = pd.DataFrame(fms_hist)
            df.columns = ["Datum", "Score", "Bewertung", "Asymmetrie", "Schwerpunkt"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Datum"], y=df["Score"],
                mode="lines+markers+text",
                text=df["Score"], textposition="top center",
                line=dict(color="#3b82f6", width=3),
                marker=dict(size=9, color="#58a6ff"),
                name="FMS Score",
            ))
            fig.add_hline(y=14, line_dash="dash", line_color="#d29922",
                          annotation_text="Beobachten ≤14", annotation_position="top right")
            fig.add_hline(y=12, line_dash="dash", line_color="#f85149",
                          annotation_text="Aktionsbedarf ≤12", annotation_position="top right")
            fig.update_layout(**_pl(height=340, title="FMS Score Verlauf", yaxis=dict(range=[0, 22])))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Y-Balance ────────────────────────────────────────────────────────────
    with tab_yb:
        if not yb_hist:
            st.info("Noch keine Y-Balance Tests vorhanden.")
        else:
            df = pd.DataFrame(yb_hist)
            df.columns = ["Datum", "Composite R", "Composite L", "Asymmetrie", "Schwerpunkt"]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df["Datum"], y=df["Composite R"],
                mode="lines+markers", name="Rechts",
                line=dict(color="#3b82f6", width=3), marker=dict(size=9),
            ))
            fig2.add_trace(go.Scatter(
                x=df["Datum"], y=df["Composite L"],
                mode="lines+markers", name="Links",
                line=dict(color="#f85149", width=3), marker=dict(size=9),
            ))
            fig2.add_hline(y=89, line_dash="dash", line_color="#d29922",
                           annotation_text="Normwert 89 %", annotation_position="top right")
            fig2.update_layout(**_pl(height=340, title="Y-Balance Composite Score Verlauf",
                                    yaxis=dict(range=[70, 115])))
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Sprint ────────────────────────────────────────────────────────────────
    with tab_sprint:
        if not sprint_hist:
            st.info("Noch keine Sprint-Tests vorhanden.")
        else:
            df = pd.DataFrame(sprint_hist)
            df.columns = ["Datum", "5m", "10m", "20m", "30m", "Beschl.-Index", "Bewertung 10m"]
            fig3 = go.Figure()
            for col, color in [("10m", "#3b82f6"), ("30m", "#3fb950")]:
                if col in df.columns and df[col].notna().any():
                    fig3.add_trace(go.Scatter(
                        x=df["Datum"], y=df[col],
                        mode="lines+markers", name=f"Sprint {col}",
                        line=dict(color=color, width=3), marker=dict(size=9),
                    ))
            fig3.update_layout(**_pl(height=320, title="Sprintzeiten Verlauf",
                                    yaxis=dict(title="Zeit (s)")))
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Sprung ────────────────────────────────────────────────────────────────
    with tab_sprung:
        if not sprung_hist:
            st.info("Noch keine Sprung-Tests vorhanden.")
        else:
            df = pd.DataFrame(sprung_hist)
            df.columns = ["Datum", "CMJ beid.", "Squat Jump", "Drop Jump", "RSI",
                          "Standweit", "CMJ Asymm.", "Bewertung CMJ"]
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=df["Datum"], y=df["CMJ beid."],
                mode="lines+markers+text",
                text=df["CMJ beid."], textposition="top center",
                line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                name="CMJ beidbeinig (cm)",
            ))
            fig4.add_hline(y=33, line_dash="dash", line_color="#d29922",
                           annotation_text="Norm Leistungssport 33 cm",
                           annotation_position="top right")
            fig4.update_layout(**_pl(height=320, title="CMJ Sprunghöhe Verlauf",
                                    yaxis=dict(title="Höhe (cm)")))
            st.plotly_chart(fig4, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Agilität ─────────────────────────────────────────────────────────────
    with tab_agil:
        if not agil_hist:
            st.info("Noch keine Agilitäts-Tests vorhanden.")
        else:
            df = pd.DataFrame(agil_hist)
            df.columns = ["Datum", "505 R (s)", "505 L (s)", "Asymm. 505 (%)",
                          "5-10-5 (s)", "T-Test (s)", "Illinois (s)", "Bewertung T-Test"]
            fig5 = go.Figure()
            for col, color in [("T-Test (s)", "#3b82f6"), ("Illinois (s)", "#3fb950")]:
                if col in df.columns and df[col].notna().any():
                    fig5.add_trace(go.Scatter(
                        x=df["Datum"], y=df[col],
                        mode="lines+markers", name=col,
                        line=dict(color=color, width=3), marker=dict(size=9),
                    ))
            fig5.update_layout(**_pl(height=320, title="Agilitätszeiten Verlauf",
                                    yaxis=dict(title="Zeit (s)")))
            st.plotly_chart(fig5, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    with tab_aus:
        if not aus_hist:
            st.info("Noch keine Ausdauer-Tests vorhanden.")
        else:
            df = pd.DataFrame(aus_hist)
            df.columns = ["Datum", "Test-Typ", "Distanz (m)", "VO₂max", "Bewertung", "HF max", "RPE"]
            fig6 = go.Figure()
            if "VO₂max" in df.columns and df["VO₂max"].notna().any():
                fig6.add_trace(go.Scatter(
                    x=df["Datum"], y=df["VO₂max"],
                    mode="lines+markers+text",
                    text=df["VO₂max"], textposition="top center",
                    line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                    name="VO₂max (ml/kg/min)",
                ))
            fig6.add_hline(y=50, line_dash="dash", line_color="#d29922",
                           annotation_text="Zielwert ≥ 50 ml/kg/min",
                           annotation_position="top right")
            fig6.update_layout(**_pl(height=320, title="VO₂max Verlauf",
                                    yaxis=dict(title="VO₂max (ml/kg/min)")))
            st.plotly_chart(fig6, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Anthropometrie ────────────────────────────────────────────────────────
    with tab_anthro:
        if not anthro_hist:
            st.info("Noch keine Anthropometrie-Messungen vorhanden.")
        else:
            df = pd.DataFrame(anthro_hist)
            df.columns = ["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)", "Muskelmasse (kg)",
                          "BMI", "BMI-Kat.", "Sitzhöhe (cm)", "Beinlänge (cm)", "Armspann (cm)",
                          "PHV-Offset", "Reifestatus"]
            fig7 = go.Figure()
            fig7.add_trace(go.Scatter(
                x=df["Datum"], y=df["Gewicht (kg)"],
                mode="lines+markers", name="Gewicht (kg)",
                line=dict(color="#3b82f6", width=3), marker=dict(size=9),
            ))
            fig7.add_trace(go.Scatter(
                x=df["Datum"], y=df["Muskelmasse (kg)"],
                mode="lines+markers", name="Muskelmasse (kg)",
                line=dict(color="#3fb950", width=3), marker=dict(size=9),
            ))
            fig7.update_layout(**_pl(height=320, title="Körperzusammensetzung Verlauf",
                                    yaxis=dict(title="kg")))
            st.plotly_chart(fig7, use_container_width=True)

            # BMI + PHV chart
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(
                x=df["Datum"], y=df["BMI"],
                mode="lines+markers", name="BMI",
                line=dict(color="#d29922", width=3), marker=dict(size=9),
            ))
            fig8.add_hline(y=25, line_dash="dash", line_color="#f85149",
                           annotation_text="Übergewicht ≥ 25", annotation_position="top right")
            fig8.update_layout(**_pl(height=260, title="BMI Verlauf"))
            st.plotly_chart(fig8, use_container_width=True)
            st.dataframe(df[["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)",
                              "Muskelmasse (kg)", "BMI", "BMI-Kat.", "PHV-Offset", "Reifestatus"]],
                         use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_anthropometrie():
    st.markdown("# 📐 Anthropometrie")
    st.markdown("Körpermessungen, BMI und Wachstumsverlauf — Grundlage für belastungsgerechtes Training.")

    sicherheitshinweis_box()
    show_trainer_checkliste("anthropometrie")
    show_test_info("anthropometrie")

    auswahl = _player_selector("anthro")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    alter  = berechne_alter(sp.get("geburtsdatum", "")) if sp else 0.0
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"

    history = anthropometrie_history(sid)
    letzter = anthropometrie_letzter(sid)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_neu, tab_verlauf = st.tabs(["📋 Neue Messung", "📈 Verlauf"])

    with tab_neu:
        st.markdown("### Körpermessung eingeben")
        c1, c2 = st.columns(2)
        datum        = c1.date_input("Datum", value=date.today(), key="anthro_datum")
        _fh = lambda fid: show_field_help("anthropometrie", fid)
        g_h, g_i = c1.columns([5, 1]); g_h.markdown("**Körpergröße (cm)**"); field_info_col(g_i, "anthropometrie", "groesse")
        groesse      = c1.number_input("Körpergröße (cm)", 100.0, 220.0,
                                        float(letzter["groesse"]) if letzter else 175.0,
                                        step=0.5, key="anthro_groesse", label_visibility="collapsed", help=_fh("groesse"))
        gw_h, gw_i = c1.columns([5, 1]); gw_h.markdown("**Körpergewicht (kg)**"); field_info_col(gw_i, "anthropometrie", "gewicht")
        gewicht      = c1.number_input("Körpergewicht (kg)", 30.0, 150.0,
                                        float(letzter["gewicht"]) if letzter else 70.0,
                                        step=0.5, key="anthro_gewicht", label_visibility="collapsed", help=_fh("gewicht"))
        kf_h, kf_i = c1.columns([5, 1]); kf_h.markdown("**Körperfett (%)**"); field_info_col(kf_i, "anthropometrie", "koerperfett")
        koerperfett  = c1.number_input("Körperfett (%)", 0.0, 50.0,
                                        float(letzter["koerperfett"]) if letzter else 12.0,
                                        step=0.1, key="anthro_kf", label_visibility="collapsed", help=_fh("koerperfett"))
        if koerperfett > 0: norm_badge(koerperfett, "anthropometrie", "koerperfett", c1)
        mm_h, mm_i = c1.columns([5, 1]); mm_h.markdown("**Muskelmasse (kg)**"); field_info_col(mm_i, "anthropometrie", "muskelmasse")
        muskelmasse  = c1.number_input("Muskelmasse (kg)", 0.0, 100.0,
                                        float(letzter["muskelmasse"]) if letzter else 0.0,
                                        step=0.5, key="anthro_mm", label_visibility="collapsed", help=_fh("muskelmasse"))
        sh_h, sh_i = c2.columns([5, 1]); sh_h.markdown("**Sitzhöhe (cm) — optional für PHV**"); field_info_col(sh_i, "anthropometrie", "sitzhoehe")
        sitzhoehe    = c2.number_input("Sitzhöhe (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["sitzhoehe"]) if letzter else 0.0,
                                        step=0.5, key="anthro_sh", label_visibility="collapsed", help=_fh("sitzhoehe"))
        bl_h, bl_i = c2.columns([5, 1]); bl_h.markdown("**Beinlänge (cm) — optional für PHV**"); field_info_col(bl_i, "anthropometrie", "beinlaenge")
        beinlaenge   = c2.number_input("Beinlänge (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["beinlaenge"]) if letzter else 0.0,
                                        step=0.5, key="anthro_bl", label_visibility="collapsed", help=_fh("beinlaenge"))
        as_h, as_i = c2.columns([5, 1]); as_h.markdown("**Armspannweite (cm)**"); field_info_col(as_i, "anthropometrie", "armspann")
        armspann     = c2.number_input("Armspannweite (cm)", 0.0, 250.0,
                                        float(letzter["armspannweite"]) if letzter else 0.0,
                                        step=0.5, key="anthro_arm", label_visibility="collapsed", help=_fh("armspann"))

        bmi     = bmi_berechnen(gewicht, groesse)
        bmi_kat = bmi_kategorie(bmi)
        phv     = phv_offset_berechnen(alter, groesse, gewicht, sitzhoehe, beinlaenge, geschl) if alter else None
        reife   = reifestatus_text(phv)
        farbe   = reifestatus_farbe(phv)

        # Vorschau
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("BMI", f"{bmi}", bmi_kat)
        m2.metric("Körperfett", f"{koerperfett} %")
        if phv is not None:
            m3.metric("PHV-Offset", f"{phv:+.1f} Jahre")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid {farbe};border-radius:8px;padding:10px 14px;margin:8px 0">'
            f'<span style="color:{farbe};font-weight:600">⚠️ Reifestatus (Schätzung): </span>'
            f'<span style="color:#e6edf3">{reife}</span><br>'
            f'<small style="color:#8b949e">Hinweis: Diese Schätzung (Mirwald-Formel) ersetzt keine ärztliche Untersuchung.</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_sv, col_del = st.columns([3, 1])
        with col_sv:
            if st.button("💾 Messung speichern", use_container_width=True, key="anthro_save"):
                anthropometrie_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    groesse, gewicht, sitzhoehe, beinlaenge, armspann,
                    koerperfett, muskelmasse,
                    bmi, bmi_kat, phv, reife,
                )
                st.success("✅ Messung gespeichert!")
                st.rerun()
        with col_del:
            if letzter and st.button("🗑️ Letzte löschen", use_container_width=True, key="anthro_del"):
                anthropometrie_loeschen_letzten(sid)
                st.warning("Letzte Messung gelöscht.")
                st.rerun()

    with tab_verlauf:
        if not history:
            st.info("Noch keine Messungen vorhanden.")
            return

        df = pd.DataFrame(history)
        df.columns = ["Datum", "Größe", "Gewicht", "Körperfett", "Muskelmasse",
                      "BMI", "BMI-Kat.", "Sitzhöhe", "Beinlänge", "Armspann",
                      "PHV-Offset", "Reifestatus"]

        # Wachstum/Monat
        wachstum = wachstum_berechnen(history)
        if wachstum is not None and wachstum > 0:
            st.info(f"📏 Durchschnittliches Wachstum: **{wachstum} cm/Monat**")

        c_g, c_w = st.columns(2)
        with c_g:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Datum"], y=df["Größe"],
                                     mode="lines+markers+text", text=df["Größe"].round(1),
                                     textposition="top center",
                                     line=dict(color="#3b82f6", width=3),
                                     marker=dict(size=8), name="Größe (cm)"))
            fig.update_layout(**_pl(height=280, title="Körpergröße"))
            st.plotly_chart(fig, use_container_width=True)

        with c_w:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["Datum"], y=df["Gewicht"],
                                      mode="lines+markers+text", text=df["Gewicht"].round(1),
                                      textposition="top center",
                                      line=dict(color="#3fb950", width=3),
                                      marker=dict(size=8), name="Gewicht (kg)"))
            fig2.update_layout(**_pl(height=280, title="Körpergewicht"))
            st.plotly_chart(fig2, use_container_width=True)

        c_kf, c_bmi = st.columns(2)
        with c_kf:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["Datum"], y=df["Körperfett"],
                                      mode="lines+markers+text", text=df["Körperfett"].round(1),
                                      textposition="top center",
                                      line=dict(color="#d29922", width=3),
                                      marker=dict(size=8), name="Körperfett (%)"))
            fig3.update_layout(**_pl(height=280, title="Körperfett"))
            st.plotly_chart(fig3, use_container_width=True)

        with c_bmi:
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=df["Datum"], y=df["BMI"],
                                  marker_color="#58a6ff", text=df["BMI"].round(1),
                                  textposition="outside", name="BMI"))
            fig4.add_hline(y=18.5, line_dash="dash", line_color="#3fb950",
                           annotation_text="Untergrenze 18.5")
            fig4.add_hline(y=25.0, line_dash="dash", line_color="#d29922",
                           annotation_text="Übergewicht 25")
            fig4.update_layout(**_pl(height=280, title="BMI-Verlauf"))
            st.plotly_chart(fig4, use_container_width=True)

        st.dataframe(df[["Datum", "Größe", "Gewicht", "BMI", "BMI-Kat.", "Körperfett",
                          "Muskelmasse", "PHV-Offset", "Reifestatus"]],
                     use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def _sprint_eingabe(distanz_label: str, key_prefix: str, letzter_row, col,
                    field_id: str = ""):
    """Hilfsfunktion: 3-Versuch-Eingabe für eine Sprint-Distanz mit Info-Button."""
    hdr, info_btn = col.columns([5, 1])
    hdr.markdown(f"**{distanz_label}**")
    if field_id:
        field_info_col(info_btn, "sprint", field_id)
    c1, c2, c3 = col.columns(3)
    help_txt = show_field_help("sprint", field_id) if field_id else ""
    v1 = c1.number_input("V1", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v1", label_visibility="collapsed",
                          help=f"Versuch 1 — {distanz_label}  \n{help_txt}" if help_txt else f"Versuch 1 — {distanz_label}")
    v2 = c2.number_input("V2", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v2", label_visibility="collapsed",
                          help=f"Versuch 2 — {distanz_label}")
    v3 = c3.number_input("V3", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v3", label_visibility="collapsed",
                          help=f"Versuch 3 — {distanz_label}")
    bester = min((v for v in [v1, v2, v3] if v > 0), default=None)
    if bester:
        col.markdown(f'<small style="color:#8b949e">Bester Versuch: <b style="color:#58a6ff">{bester:.2f} s</b></small>', unsafe_allow_html=True)
        if field_id:
            norm_badge(bester, "sprint", field_id, col)
    return v1, v2, v3, bester


def page_sprint():
    st.markdown("# ⚡ Sprint-Diagnostik")
    st.markdown("Lineare Beschleunigung und Maximalgeschwindigkeit — 5 m bis 30 m, je 3 Versuche.")

    # ── Sicherheitshinweis & Testanleitung ────────────────────────────────────
    sicherheitshinweis_box()
    show_trainer_checkliste("sprint")
    show_test_info("sprint")

    auswahl = _player_selector("sprint")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"

    letzter = sprint_letzter(sid)
    hist    = sprint_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprint_datum")
        st.markdown("#### Zeiten eingeben (Sekunden) — Versuch 1 / 2 / 3")
        st.caption("Nicht gemessene Distanzen auf 0.00 lassen. ℹ️-Button neben jeder Distanz für Eingabehilfe.")

        c_l, c_r = st.columns(2)
        v1_5,  v2_5,  v3_5,  b5  = _sprint_eingabe("5 m",  "s5",  letzter, c_l, "sprint_5m")
        v1_10, v2_10, v3_10, b10 = _sprint_eingabe("10 m", "s10", letzter, c_l, "sprint_10m")
        v1_20, v2_20, v3_20, b20 = _sprint_eingabe("20 m", "s20", letzter, c_r, "sprint_20m")
        v1_30, v2_30, v3_30, b30 = _sprint_eingabe("30 m", "s30", letzter, c_r, "sprint_30m")

        from sprint import (beschleunigungsindex, bewertung_sprint, bewertung_farbe,
                            SprintErgebnis as _SE)
        res = _SE(beste_5m=b5, beste_10m=b10, beste_20m=b20, beste_30m=b30,
                  geschlecht=geschl, niveau=niveau)

        if any([b5, b10, b20, b30]):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if b10: m1.metric("10 m", f"{b10:.2f} s", res.bewertung_10m)
            if b20: m2.metric("20 m", f"{b20:.2f} s")
            if b30: m3.metric("30 m", f"{b30:.2f} s", res.bewertung_30m)
            if res.beschl_index: m4.metric("Beschl.-Index", f"{res.beschl_index:.3f}")

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        # F-04: Plausibilitätsprüfung Sprint-Zeiten
        if b5 and b10 and b10 < b5:
            st.warning("⚠️ Plausibilitätsprüfung: Die 10-m-Zeit ist kleiner als die 5-m-Zeit — bitte Eingaben prüfen.")
        if b10 and b20 and b20 < b10:
            st.warning("⚠️ Plausibilitätsprüfung: Die 20-m-Zeit ist kleiner als die 10-m-Zeit — bitte Eingaben prüfen.")
        if b20 and b30 and b30 < b20:
            st.warning("⚠️ Plausibilitätsprüfung: Die 30-m-Zeit ist kleiner als die 20-m-Zeit — bitte Eingaben prüfen.")

        if st.button("💾 Test speichern", use_container_width=True, key="sprint_save"):
            if not any([b5, b10, b20, b30]):
                st.error("Bitte mindestens eine Distanz eingeben.")
            else:
                from sprint import beschleunigungsindex, bewertung_sprint
                import json
                sprint_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    v1_5, v2_5, v3_5, b5 or 0,
                    v1_10, v2_10, v3_10, b10 or 0,
                    v1_20, v2_20, v3_20, b20 or 0,
                    v1_30, v2_30, v3_30, b30 or 0,
                    res.beschl_index or 0,
                    res.bewertung_10m, res.bewertung_30m,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                st.success("✅ Sprint-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Sprint-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "5 m", "10 m", "20 m", "30 m", "Beschl.-Index", "Bew. 10 m"]

        fig = go.Figure()
        for col_name, color in [("10 m", "#3b82f6"), ("20 m", "#3fb950"),
                                  ("30 m", "#d29922"), ("5 m", "#f85149")]:
            sub = df[df[col_name] > 0]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                     mode="lines+markers", name=col_name,
                                     line=dict(color=color, width=2),
                                     marker=dict(size=7)))
        fig.update_layout(**_pl(height=340, title="Sprintzeiten-Verlauf",
                                yaxis=dict(autorange="reversed",
                                           title="Zeit (s) — niedriger = besser")))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_sprung():
    st.markdown("# 🦘 Sprung-Diagnostik")
    st.markdown("Explosivkraft, Reaktivkraft und Seitenasymmetrie — CMJ, Squat Jump, Drop Jump, Standweitsprung.")

    sicherheitshinweis_box()
    show_trainer_checkliste("jump")
    show_test_info("jump")

    auswahl = _player_selector("sprung")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"

    letzter = sprung_letzter(sid)
    hist    = sprung_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprung_datum")
        st.markdown("#### Messwerte (cm / s) — nicht gemessene Tests auf 0 lassen")

        _fh = lambda fid: show_field_help("jump", fid)
        c1, c2 = st.columns(2)

        lc1, li1 = c1.columns([5,1])
        lc1.markdown("**CMJ beidbeinig (cm)**"); field_info_col(li1, "jump", "cmj_beid")
        cmj_beid = c1.number_input("CMJ beidbeinig", 0.0, 100.0, 0.0, step=0.5, key="cmj_beid", label_visibility="collapsed", help=_fh("cmj_beid"))
        if cmj_beid > 0: norm_badge(cmj_beid, "jump", "cmj_beid", c1)

        lc2, li2 = c1.columns([5,1])
        lc2.markdown("**CMJ einbeinig rechts (cm)**"); field_info_col(li2, "jump", "cmj_r")
        cmj_r    = c1.number_input("CMJ rechts", 0.0, 80.0, 0.0, step=0.5, key="cmj_r", label_visibility="collapsed", help=_fh("cmj_r"))
        if cmj_r > 0: norm_badge(cmj_r, "jump", "cmj_r", c1)

        lc3, li3 = c1.columns([5,1])
        lc3.markdown("**CMJ einbeinig links (cm)**"); field_info_col(li3, "jump", "cmj_l")
        cmj_l    = c1.number_input("CMJ links", 0.0, 80.0, 0.0, step=0.5, key="cmj_l", label_visibility="collapsed", help=_fh("cmj_l"))
        if cmj_l > 0: norm_badge(cmj_l, "jump", "cmj_l", c1)

        lc4, li4 = c1.columns([5,1])
        lc4.markdown("**Squat Jump (cm)**"); field_info_col(li4, "jump", "squat_jump")
        squat    = c1.number_input("Squat Jump", 0.0, 100.0, 0.0, step=0.5, key="squat", label_visibility="collapsed", help=_fh("squat_jump"))
        if squat > 0: norm_badge(squat, "jump", "squat_jump", c1)

        rc1, ri1 = c2.columns([5,1])
        rc1.markdown("**Drop Jump — Höhe (cm)**"); field_info_col(ri1, "jump", "dj_hoehe")
        dj_h  = c2.number_input("Drop Jump Höhe", 0.0, 80.0, 0.0, step=0.5, key="dj_h", label_visibility="collapsed", help=_fh("dj_hoehe"))
        if dj_h > 0: norm_badge(dj_h, "jump", "dj_hoehe", c2)

        rc2, ri2 = c2.columns([5,1])
        rc2.markdown("**Drop Jump — Kontaktzeit (s)**"); field_info_col(ri2, "jump", "dj_kontakt")
        dj_kz = c2.number_input("Drop Jump Kontaktzeit", 0.0, 2.0, 0.0, step=0.01, format="%.2f", key="dj_kz", label_visibility="collapsed", help=_fh("dj_kontakt"))
        if dj_kz > 0: norm_badge(dj_kz, "jump", "dj_kontakt", c2)

        rc3, ri3 = c2.columns([5,1])
        rc3.markdown("**Standweitsprung (cm)**"); field_info_col(ri3, "jump", "standweit")
        swj   = c2.number_input("Standweitsprung", 0.0, 400.0, 0.0, step=1.0, key="swj", label_visibility="collapsed", help=_fh("standweit"))
        if swj > 0: norm_badge(swj, "jump", "standweit", c2)

        from sprung import SprungErgebnis as _SpE, asymmetrie_prozent, rsi_berechnen
        res = _SpE(cmj_beid=cmj_beid or None, cmj_rechts=cmj_r or None,
                   cmj_links=cmj_l or None, squat_jump=squat or None,
                   drop_jump_hoehe=dj_h or None, drop_jump_kz=dj_kz or None,
                   standweit=swj or None, geschlecht=geschl, niveau=niveau)

        if any([cmj_beid, cmj_r, cmj_l, squat, dj_h, swj]):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if cmj_beid: m1.metric("CMJ", f"{cmj_beid:.1f} cm", res.bewertung_cmj)
            if squat:    m2.metric("Squat Jump", f"{squat:.1f} cm")
            if res.rsi:  m3.metric("RSI", f"{res.rsi:.2f}", "gut" if res.rsi >= 1.5 else "niedrig")
            if res.cmj_asymmetrie:
                color_txt = "⚠️ auffällig" if res.cmj_asymmetrie > 10 else "✅ ok"
                m4.metric("Asymmetrie", f"{res.cmj_asymmetrie:.1f} %", color_txt)

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        if st.button("💾 Test speichern", use_container_width=True, key="sprung_save"):
            if not any([cmj_beid, cmj_r, cmj_l, squat, dj_h, swj]):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json
                sprung_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    cmj_beid or 0, cmj_r or 0, cmj_l or 0,
                    res.cmj_asymmetrie or 0,
                    squat or 0, dj_h or 0, dj_kz or 0,
                    res.rsi or 0, swj or 0,
                    res.bewertung_cmj,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                st.success("✅ Sprung-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Sprung-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "CMJ", "Squat Jump", "Drop Jump H.", "RSI",
                      "Standweit", "Asymmetrie %", "Bewertung CMJ"]

        c_cmj, c_asym = st.columns(2)
        with c_cmj:
            fig = go.Figure()
            for col_name, color in [("CMJ", "#3b82f6"), ("Squat Jump", "#3fb950")]:
                sub = df[df[col_name] > 0]
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                         mode="lines+markers", name=col_name,
                                         line=dict(color=color, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=280, title="CMJ & Squat Jump (cm)",
                                    yaxis=dict(title="cm")))
            st.plotly_chart(fig, use_container_width=True)

        with c_asym:
            sub_a = df[df["Asymmetrie %"] > 0]
            if not sub_a.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=sub_a["Datum"], y=sub_a["Asymmetrie %"],
                                      marker_color=["#f85149" if v > 10 else "#3fb950"
                                                    for v in sub_a["Asymmetrie %"]],
                                      text=sub_a["Asymmetrie %"].round(1),
                                      textposition="outside"))
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922",
                               annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=280, title="CMJ-Asymmetrie links/rechts"))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Keine einbeinigen CMJ-Werte vorhanden.")

        st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def _zeit_eingabe(label: str, key: str, col, letzter=None, letzter_key=None,
                  test_id: str = "", field_id: str = ""):
    """Hilfsfunktion: Zeiteingabe mit optionalem ℹ️-Button."""
    if field_id and test_id:
        hdr, info_btn = col.columns([5, 1])
        hdr.markdown(f"**{label}**")
        field_info_col(info_btn, test_id, field_id)
    else:
        col.markdown(f"**{label}**")
    default = float(letzter[letzter_key]) if (letzter and letzter_key and letzter.get(letzter_key)) else 0.0
    help_txt = show_field_help(test_id, field_id) if (test_id and field_id) else None
    v = col.number_input(label, 0.0, 30.0, default, step=0.01, format="%.2f",
                         key=key, label_visibility="collapsed", help=help_txt)
    if v > 0 and test_id and field_id:
        norm_badge(v, test_id, field_id, col)
    return v if v > 0 else None


def page_agilitaet():
    st.markdown("# 🔀 Agilität & Richtungswechsel")
    st.markdown("505-Test, 5-10-5 Shuttle, T-Test, Illinois Agility Run — Richtungswechsel-Fähigkeit und Abbremsstärke.")

    sicherheitshinweis_box()
    show_trainer_checkliste("agility")
    show_test_info("agility")

    auswahl = _player_selector("agil")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"

    letzter = agilitaet_letzter(sid)
    hist    = agilitaet_history(sid)

    tab_neu, tab_verlauf, tab_info = st.tabs(["📋 Neuer Test", "📈 Verlauf", "ℹ️ Testbeschreibung"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="agil_datum")
        st.markdown("#### Zeiten (s) — nicht gemessene Tests auf 0.00 lassen")

        c1, c2 = st.columns(2)
        t505_r  = _zeit_eingabe("505-Test rechts (s)", "a505r", c1, letzter, "t505_r",  "agility", "t505_r")
        t505_l  = _zeit_eingabe("505-Test links (s)",  "a505l", c1, letzter, "t505_l",  "agility", "t505_l")
        t5_10_5 = _zeit_eingabe("5-10-5 Shuttle (s)",  "a5105", c2, letzter, "t5_10_5", "agility", "t5_10_5")
        t_test  = _zeit_eingabe("T-Test (s)",           "att",   c2, letzter, "t_test",  "agility", "t_test")
        illinois = _zeit_eingabe("Illinois Agility (s)","aill",  c1, letzter, "illinois","agility", "illinois")

        from agilitaet import AgilitaetErgebnis as _AE
        res = _AE(t505_r=t505_r, t505_l=t505_l, t5_10_5=t5_10_5,
                  t_test=t_test, illinois=illinois,
                  geschlecht=geschl, niveau=niveau)

        if any([t505_r, t505_l, t5_10_5, t_test, illinois]):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if t505_r:   m1.metric("505 rechts", f"{t505_r:.2f} s",   res.bew_505)
            if t505_l:   m2.metric("505 links",  f"{t505_l:.2f} s")
            if t_test:   m3.metric("T-Test",     f"{t_test:.2f} s",   res.bew_t_test)
            if illinois: m4.metric("Illinois",   f"{illinois:.2f} s", res.bew_illinois)

            if res.asym_505:
                color = "#f85149" if res.asym_505 > 10 else "#3fb950"
                sign  = "⚠️ auffällig" if res.asym_505 > 10 else "✅ symmetrisch"
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {color};border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0">'
                    f'<span style="color:{color};font-weight:600">505-Asymmetrie: {res.asym_505:.1f} % — {sign}</span>'
                    f'<br><small style="color:#8b949e">Grenzwert: 10 % (klinisch relevant)</small></div>',
                    unsafe_allow_html=True,
                )

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        if st.button("💾 Test speichern", use_container_width=True, key="agil_save"):
            if not any([t505_r, t505_l, t5_10_5, t_test, illinois]):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json
                agilitaet_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    t505_r or 0, t505_l or 0, res.asym_505 or 0,
                    t5_10_5 or 0, t_test or 0, illinois or 0,
                    res.bew_505, res.bew_t_test, res.bew_illinois,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                st.success("✅ Agilität-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Agilität-Tests vorhanden.")
        else:
            df = pd.DataFrame(hist)
            df.columns = ["Datum", "505 R", "505 L", "Asymmetrie %",
                          "5-10-5", "T-Test", "Illinois", "Bewertung T-Test"]

            fig = go.Figure()
            for col_name, color in [("T-Test","#3b82f6"), ("Illinois","#3fb950"),
                                     ("5-10-5","#d29922"), ("505 R","#f85149"), ("505 L","#a371f7")]:
                sub = df[df[col_name] > 0]
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                         mode="lines+markers", name=col_name,
                                         line=dict(width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=320, title="Agilitätszeiten-Verlauf (s)",
                                    yaxis=dict(autorange="reversed", title="Zeit (s)")))
            st.plotly_chart(fig, use_container_width=True)

            sub_a = df[df["Asymmetrie %"] > 0]
            if not sub_a.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=sub_a["Datum"], y=sub_a["Asymmetrie %"],
                    marker_color=["#f85149" if v > 10 else "#3fb950" for v in sub_a["Asymmetrie %"]],
                    text=sub_a["Asymmetrie %"].round(1), textposition="outside",
                ))
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922",
                               annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=240, title="505-Asymmetrie R vs. L (%)"))
                st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_info:
        st.markdown("""
        | Test | Distanz / Aufbau | Misst |
        |---|---|---|
        | **505-Test** | 10 m anlaufen → 180° Wendung → 5 m Sprint | Richtungswechsel, getrennt R/L |
        | **5-10-5 Shuttle** | 5 m links → 10 m rechts → 5 m zurück | Shuttle-Beschleunigung, Abbremsen |
        | **T-Test** | 9,14 m vor, je 4,57 m seitwärts, zurück | Mehrdirektionale Agilität |
        | **Illinois Agility** | 10 m Slalomkurs | Gesamtagilität, Richtungswechselgeschwindigkeit |
        """)


# ──────────────────────────────────────────────────────────────────────────────

ALTERSGRUPPEN_YO = ["U8/U9", "U10/U11", "U12/U13", "U13/U14", "U15/U16", "U17/U18", "Senioren"]
RPE_LABELS = {
    6: "6 — Gar keine Anstrengung", 7: "7", 8: "8", 9: "9",
    10: "10 — Sehr leicht", 11: "11 — Leicht", 12: "12",
    13: "13 — Etwas anstrengend", 14: "14",
    15: "15 — Anstrengend", 16: "16", 17: "17 — Sehr anstrengend",
    18: "18", 19: "19 — Extrem anstrengend", 20: "20 — Maximale Anstrengung",
}


def page_ausdauer():
    st.markdown("# 🫁 Yo-Yo Ausdauer-Diagnostik")
    st.markdown("Yo-Yo Intermittent Recovery Test Level 1 (IR1) und Level 2 (IR2) — Standardtest im Fußball.")

    sicherheitshinweis_box()
    show_trainer_checkliste("yoyo")
    show_test_info("yoyo")

    auswahl = _player_selector("aus")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    alter  = berechne_alter(sp.get("geburtsdatum","")) if sp else 0

    letzter = ausdauer_letzter(sid)
    hist    = ausdauer_history(sid)

    # Altersgruppe aus Alter ableiten
    def alter_zu_gruppe(a):
        if a < 10: return "U8/U9"
        if a < 12: return "U10/U11"
        if a < 14: return "U12/U13"
        if a < 16: return "U15/U16"
        if a < 18: return "U17/U18"
        return "Senioren"

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        c1, c2 = st.columns(2)
        datum       = c1.date_input("Testdatum", value=date.today(), key="aus_datum")
        test_typ    = c1.selectbox("Test-Level", ["IR1", "IR2"], key="aus_typ")
        altersgruppe = c2.selectbox("Altersgruppe", ALTERSGRUPPEN_YO,
                                     index=ALTERSGRUPPEN_YO.index(alter_zu_gruppe(alter or 20)),
                                     key="aus_ag")

        st.markdown("#### Testergebnis")
        _fh = lambda fid: show_field_help("yoyo", fid)
        c3, c4, c5 = st.columns(3)
        dist_h, dist_i = c3.columns([5, 1]); dist_h.markdown("**Erzielte Distanz (m)**"); field_info_col(dist_i, "yoyo", "distanz")
        distanz_m = c3.number_input("Erzielte Distanz (m)", 0, 5000,
                                     int(letzter["distanz_m"]) if letzter else 0,
                                     step=40, key="aus_dist", label_visibility="collapsed", help=_fh("distanz"))
        if distanz_m > 0: norm_badge(distanz_m, "yoyo", "distanz", c3)
        hf_h, hf_i = c4.columns([5, 1]); hf_h.markdown("**HF max (bpm)**"); field_info_col(hf_i, "yoyo", "hf_max")
        hf_max    = c4.number_input("HF max (bpm)", 0, 230,
                                     int(letzter["hf_max"]) if letzter and letzter.get("hf_max") else 0,
                                     step=1, key="aus_hf", label_visibility="collapsed", help=_fh("hf_max"))
        rpe_h, rpe_i = c5.columns([5, 1]); rpe_h.markdown("**RPE (Borg 6–20)**"); field_info_col(rpe_i, "yoyo", "rpe")
        rpe_val   = c5.selectbox("RPE (Borg 6–20)", list(range(6, 21)),
                                  index=9, key="aus_rpe",
                                  format_func=lambda x: RPE_LABELS.get(x, str(x)),
                                  help=_fh("rpe"), label_visibility="collapsed")

        from ausdauer import AusdauerErgebnis as _AE, trainingsbereiche, bewertung_ir1
        res = _AE(test_typ=test_typ, distanz_m=distanz_m,
                  hf_max=hf_max or None, rpe=rpe_val,
                  geschlecht=geschl, altersgruppe=altersgruppe)

        if distanz_m > 0:
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Distanz", f"{distanz_m} m")
            if res.vo2max:
                m2.metric("VO₂max (Schätzung ⚠️)", f"{res.vo2max} ml/kg/min")
            bew_color = aus_farbe(res.bewertung)
            m3.markdown(
                f'<div style="background:#161b22;border:1px solid {bew_color};border-radius:8px;'
                f'padding:8px 12px;text-align:center">'
                f'<div style="color:{bew_color};font-weight:700;font-size:18px">{res.bewertung}</div>'
                f'<div style="color:#8b949e;font-size:11px">Bewertung {altersgruppe}</div></div>',
                unsafe_allow_html=True,
            )

            st.caption("⚠️ Die VO₂max-Schätzung basiert auf der Bangsbo-Formel und ist kein Laborwert.")

            if res.vo2max:
                st.markdown("#### Trainingsbereiche")
                tb = trainingsbereiche(res.vo2max)
                st.dataframe(pd.DataFrame(tb), use_container_width=True, hide_index=True)

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        if st.button("💾 Test speichern", use_container_width=True, key="aus_save"):
            if distanz_m <= 0:
                st.error("Bitte Distanz eingeben.")
            else:
                import json
                ausdauer_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    test_typ, distanz_m,
                    hf_max or 0, rpe_val,
                    res.vo2max or 0, res.bewertung,
                    altersgruppe,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                st.success("✅ Ausdauer-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Ausdauer-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "Test", "Distanz (m)", "VO₂max", "Bewertung", "HF max", "RPE"]

        c_d, c_v = st.columns(2)
        with c_d:
            fig = go.Figure()
            for typ, color in [("IR1", "#3b82f6"), ("IR2", "#3fb950")]:
                sub = df[df["Test"] == typ]
                if sub.empty: continue
                fig.add_trace(go.Scatter(
                    x=sub["Datum"], y=sub["Distanz (m)"],
                    mode="lines+markers+text", name=f"Yo-Yo {typ}",
                    text=sub["Distanz (m)"], textposition="top center",
                    line=dict(color=color, width=3), marker=dict(size=8),
                ))
            fig.update_layout(**_pl(height=300, title="Yo-Yo Distanz-Verlauf (m)"))
            st.plotly_chart(fig, use_container_width=True)

        with c_v:
            sub_v = df[df["VO₂max"] > 0]
            if not sub_v.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=sub_v["Datum"], y=sub_v["VO₂max"],
                    mode="lines+markers+text", name="VO₂max (Schätzung)",
                    text=sub_v["VO₂max"].round(1), textposition="top center",
                    line=dict(color="#d29922", width=3), marker=dict(size=8),
                ))
                fig2.add_hline(y=50, line_dash="dash", line_color="#3fb950",
                               annotation_text="Zielwert 50 ml/kg/min")
                fig2.update_layout(**_pl(height=300, title="VO₂max-Schätzung ⚠️"))
                st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# NEW PAGES (Phase 1)
# ══════════════════════════════════════════════════════════════════════════════

def page_startseite():
    """Home — personalisierte Übersicht für den aktiven Spieler."""
    spieler_liste = spieler_laden()
    if not spieler_liste:
        st.markdown(empty_state("⚽", "Willkommen bei Athletik Diagnostik",
                                "Lege unter Spieler → Verwaltung deinen ersten Spieler an."),
                    unsafe_allow_html=True)
        return

    auswahl = _player_selector()
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    anthro = anthropometrie_letzter(sid)
    verlet = verletzungen_laden(sid)

    rs              = risiko_score(fms, y, verlet)
    _, level        = risiko_label(rs)
    ascore          = athletik_score(fms, y, sprint, sprung, agil, aus)
    defizite        = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro)
    alter           = berechne_alter(auswahl.get("geburtsdatum"))

    # ── Greeting ──────────────────────────────────────────────────────────────
    hour = datetime.now().hour
    greeting = "Guten Morgen" if hour < 12 else "Guten Tag" if hour < 18 else "Guten Abend"
    st.markdown(f"## {greeting}, Coach")

    # ── Player banner ─────────────────────────────────────────────────────────
    st.markdown(player_banner(auswahl, alter), unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    score_color = C["green"] if ascore >= 75 else C["yellow"] if ascore >= 50 else C["red"]
    risk_colors = {"hoch": C["red"], "mittel": C["yellow"], "gering": C["green"]}
    risk_icons  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    risk_labels = {"hoch": "HANDLUNGSBEDARF HOCH", "mittel": "HANDLUNGSBEDARF", "gering": "UNAUFFÄLLIG"}

    # Last test date across all modules
    dates = []
    for row in [fms, y, sprint, sprung, agil, aus, anthro]:
        if row and row.get("datum"):
            dates.append(str(row["datum"]))
    letzter_test = max(dates) if dates else None

    # F-07: Hinweis wenn noch keine Testdaten vorhanden
    hat_tests = any([fms, y, sprint, sprung, agil, aus])
    if not hat_tests:
        st.info("ℹ️ Noch nicht genug Testdaten für einen vollständigen Athletik-Score. Führe mindestens einen Test durch.")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        score_display = (
            f'{ascore}<span style="font-size:16px;font-weight:400;color:{C["muted"]}">/100</span>'
            if hat_tests else
            f'<span style="font-size:20px;color:{C["muted"]}">—</span>'
        )
        st.markdown(kpi_card("Athletik Score", score_display, color=score_color if hat_tests else C["muted"]),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Athletik-Status",
                             f'{risk_icons[level]} {risk_labels[level]}',
                             color=risk_colors[level]), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Letzter Test", letzter_test or "Kein Test",
                             subtitle="Datum"), unsafe_allow_html=True)
    with k4:
        verlet_count = len(verlet) if verlet else 0
        ausfall_ges  = sum(v.get("ausfall_tage") or 0 for v in (verlet or []))
        st.markdown(kpi_card("Verletzungshistorie",
                             str(verlet_count),
                             subtitle=f"{ausfall_ges} Ausfalltage gesamt"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Defizite & Stärken ────────────────────────────────────────────────────
    col_def, col_str = st.columns(2)

    with col_def:
        st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:8px">TOP DEFIZITE</div>', unsafe_allow_html=True)
        if not defizite:
            st.markdown(f'<div style="color:{C["green"]};font-size:14px;padding:10px 0">✅ Keine auffälligen Defizite erkannt.</div>', unsafe_allow_html=True)
        else:
            for d in defizite[:5]:
                st.markdown(deficit_row(d), unsafe_allow_html=True)
            if len(defizite) > 5:
                st.caption(f"+ {len(defizite)-5} weitere Defizite — Details im Spielerprofil")

    with col_str:
        st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:8px">STÄRKEN</div>', unsafe_allow_html=True)
        strengths = []
        if fms and fms["score"] >= 17:
            strengths.append(("FMS Bewegungsqualität", f'Score {fms["score"]}/21'))
        if y:
            avg_y = (y["composite_rechts"] + y["composite_links"]) / 2
            if avg_y >= 92:
                strengths.append(("Y-Balance", f'Ø {avg_y:.1f} %'))
        if sprint and sprint.get("bewertung_10m") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Sprint", sprint["bewertung_10m"]))
        if sprung and sprung.get("bewertung_cmj") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Explosivkraft", sprung["bewertung_cmj"]))
        if agil and agil.get("bew_t_test") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Agilität", agil["bew_t_test"]))
        if aus and aus.get("bewertung") == "Gut":
            strengths.append(("Ausdauer", f'VO₂max ~{aus["vo2max"]} ml/kg/min' if aus.get("vo2max") else "Gut"))
        if not strengths:
            st.markdown(f'<div style="color:{C["muted"]};font-size:14px;padding:10px 0">Noch keine Tests mit Stärken vorhanden.</div>', unsafe_allow_html=True)
        for bereich, detail in strengths[:5]:
            st.markdown(strength_row(bereich, detail), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Test-Übersicht ────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:10px">TESTMODULE — AKTUELLER STATUS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    cards = [
        ("FMS",       "📝", fms,    fms["bewertung"]        if fms    else None, fms["datum"]    if fms    else None),
        ("Y-Balance", "📏", y,      "Asymmetrie: " + y["asymmetrie"][:12] if y else None, y["datum"] if y else None),
        ("Sprint",    "⚡", sprint, sprint["bewertung_10m"] if sprint else None, sprint["datum"] if sprint else None),
        ("Sprung",    "🦘", sprung, sprung["bewertung_cmj"] if sprung else None, sprung["datum"] if sprung else None),
        ("Agilität",  "🔀", agil,   agil["bew_t_test"]      if agil   else None, agil["datum"]   if agil   else None),
        ("Ausdauer",  "🫁", aus,    aus["bewertung"]        if aus    else None, aus["datum"]    if aus    else None),
    ]
    for i, (name, icon, row, rating, dt) in enumerate(cards):
        col = [c1, c2, c3][i % 3]
        with col:
            st.markdown(test_status_card(name, icon, dt, rating), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:10px">SCHNELLZUGRIFF</div>', unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    if qa1.button("👤 Spielerprofil", use_container_width=True):
        st.session_state["_nav_goto"] = "👤  Spieler"
        st.session_state["nav_sub_spieler"] = "🏃 Profil & Diagnostik"
        st.rerun()
    if qa2.button("🔬 Test starten", use_container_width=True):
        st.session_state["_nav_goto"] = "🔬  Diagnostik"
        st.rerun()
    if qa3.button("📅 Trainingsplan", use_container_width=True):
        st.session_state["_nav_goto"] = "📅  Training"
        st.rerun()
    if qa4.button("📈 Verlauf", use_container_width=True):
        st.session_state["_nav_goto"] = "📈  Entwicklung"
        st.rerun()


def page_zweckbestimmung():
    """Zweckbestimmung und Hinweise — erneut abrufbar aus den Einstellungen."""
    st.markdown("# 📋 Zweckbestimmung und Anwendungshinweise")
    st.markdown(
        f'<div style="background:#1c2128;border:1px solid #d29922;border-radius:8px;'
        f'padding:16px 20px;margin-bottom:20px">'
        f'<span style="color:#d29922;font-size:12px;font-weight:600;letter-spacing:1px">'
        f'VERSION {ZWECKBESTIMMUNG_VERSION}</span></div>',
        unsafe_allow_html=True,
    )

    for absatz in ZWECKBESTIMMUNG_TEXT_DISPLAY.split("\n\n"):
        st.markdown(absatz)

    st.markdown("---")
    st.markdown("### 🟢 🟡 🔴 Bedeutung der Ampelfarben")
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #3fb950;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#3fb950">Grün</b><br>'
        f'<span style="color:#8b949e">{AMPEL_GRUEN}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #d29922;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#d29922">Gelb</b><br>'
        f'<span style="color:#8b949e">{AMPEL_GELB}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #f85149;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#f85149">Rot</b><br>'
        f'<span style="color:#8b949e">{AMPEL_ROT}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"ℹ️ {AMPEL_FUSSZEILE}")

    st.markdown("---")
    st.markdown("### 🏋️ Trainingsplan-Hinweis")
    st.info(TRAININGSPLAN_HINWEIS)

    st.markdown("### 📐 Wachstum / Anthropometrie")
    st.info(PHV_HINWEIS)

    st.markdown("### 📝 FMS / Y-Balance")
    st.info(FMS_HINWEIS)

    st.markdown("---")
    st.markdown("### 📜 Bestätigungsprotokoll")
    alle = einwilligung_alle()
    if alle:
        df_einw = pd.DataFrame(alle)[["datum", "version", "benutzer"]]
        df_einw.columns = ["Datum", "Version", "Bestätigt von"]
        st.dataframe(df_einw, use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Bestätigung gespeichert.")

    st.markdown("---")
    st.markdown("### 🔄 Zweckbestimmung erneut bestätigen")
    benutzer_neu = st.text_input("Name", key="zweck_renew_name", placeholder="Trainer / Nutzer")
    if st.button("✅ Erneut bestätigen und speichern", key="zweck_renew_btn"):
        einwilligung_speichern(ZWECKBESTIMMUNG_VERSION, benutzer_neu.strip() or "Trainer")
        st.success("✅ Zweckbestimmung erneut bestätigt und gespeichert.")
        st.rerun()


def page_einstellungen():
    """Einstellungen — App-Konfiguration."""
    st.markdown(section_header("⚙️ Einstellungen", "App-Konfiguration und Datenverwaltung"),
                unsafe_allow_html=True)

    tab_allg, tab_zweck, tab_chk, tab_export, tab_dsg = st.tabs([
        "⚙️ Allgemein", "📋 Zweckbestimmung", "✅ Checklisten", "💾 Export & Backup", "🔒 Datenschutz"
    ])

    with tab_allg:
        st.markdown("### Vereinsinformationen")
        c1, c2 = st.columns(2)
        vereinsname = c1.text_input("Vereinsname", value=st.session_state.get("cfg_vereinsname", ""), key="cfg_vname")
        saison      = c2.text_input("Aktuelle Saison", value=st.session_state.get("cfg_saison", "2025/26"), key="cfg_saison")
        if st.button("💾 Speichern", key="cfg_save"):
            st.session_state["cfg_vereinsname"] = vereinsname
            st.session_state["cfg_saison"]      = saison
            st.success("✅ Einstellungen gespeichert (Session).")

        st.markdown("---")
        st.markdown("### Kader-Übersicht")
        alle = spieler_laden()
        st.metric("Spieler gesamt", len(alle))
        if alle:
            mannschaften = list({p.get("mannschaft") or "Keine" for p in alle})
            st.markdown(f"**Mannschaften:** {', '.join(sorted(mannschaften))}")

    with tab_zweck:
        page_zweckbestimmung()

    with tab_chk:
        st.markdown("### ✅ Eigene Checklistenpunkte pro Test")
        st.caption(
            "Ergänze testspezifische Routineschritte, die nach den Standardpunkten "
            "in der Trainer-Checkliste erscheinen. Ein Punkt pro Zeile."
        )
        st.markdown("---")
        for tid in ALL_TEST_IDS:
            label = TEST_LABELS[tid]
            aktuell = checkliste_custom_laden(tid)
            with st.expander(f"📋 {label}", expanded=False):
                neuer_text = st.text_area(
                    "Eigene Punkte (eine Zeile = ein Punkt)",
                    value=aktuell,
                    height=120,
                    placeholder="z. B.\nVideoaufnahme starten\nTrikot-Nummer notiert\nEltern informiert",
                    key=f"chk_custom_{tid}",
                    label_visibility="collapsed",
                )
                col_save, col_reset = st.columns([2, 1])
                if col_save.button("💾 Speichern", key=f"chk_save_{tid}",
                                   use_container_width=True):
                    checkliste_custom_speichern(tid, neuer_text)
                    st.success("✅ Gespeichert.", icon="✅")
                if col_reset.button("🗑️ Löschen", key=f"chk_del_{tid}",
                                    use_container_width=True):
                    checkliste_custom_speichern(tid, "")
                    st.rerun()

    with tab_dsg:
        st.markdown("### 🔒 Datenschutz & Datenverwaltung")

        st.info(
            "**Was wird gespeichert?** Name, Geburtsdatum, Positions- und "
            "Vereinsangaben sowie alle eingegebenen Testergebnisse und "
            "Verletzungseinträge.\n\n"
            "**Wo?** Ausschließlich lokal in der Datei `athletik.db` auf diesem "
            "Gerät. Es erfolgt keine Übertragung an externe Server oder Cloud-Dienste.\n\n"
            "**Wie lange?** Bis zur manuellen Löschung — es gibt keine automatische "
            "Löschfrist. Erstelle regelmäßig Sicherungskopien der Datenbankdatei."
        )

        st.markdown("---")
        st.markdown("### 🗑️ Einzelnen Spieler vollständig löschen")
        st.caption(
            "Löscht den Spieler samt aller Testdaten, Verletzungshistorie und "
            "Trainingsplan. Diese Aktion kann nicht rückgängig gemacht werden."
        )
        alle_spieler = spieler_laden()
        if not alle_spieler:
            st.info("Keine Spieler vorhanden.")
        else:
            del_namen = {p["name"]: p["id"] for p in alle_spieler}
            del_auswahl_name = st.selectbox(
                "Spieler auswählen", options=list(del_namen.keys()),
                key="dsg_del_spieler"
            )
            bestaetigung = st.text_input(
                f'Zur Bestätigung den Namen **{del_auswahl_name}** eintippen:',
                key="dsg_del_confirm"
            )
            if st.button("🗑️ Spieler unwiderruflich löschen", key="dsg_del_btn",
                         type="primary"):
                if bestaetigung.strip() == del_auswahl_name:
                    spieler_loeschen(del_namen[del_auswahl_name])
                    if st.session_state.get("aktiver_spieler_id") == del_namen[del_auswahl_name]:
                        del st.session_state["aktiver_spieler_id"]
                    st.success(f"✅ Spieler **{del_auswahl_name}** und alle zugehörigen Daten gelöscht.")
                    st.rerun()
                else:
                    st.error("❌ Name stimmt nicht überein — Löschung abgebrochen.")

        st.markdown("---")
        st.markdown("### ⚠️ Gesamte Datenbank zurücksetzen")
        st.warning(
            "Löscht **alle** Spieler, Testergebnisse, Verletzungshistorien und "
            "Einwilligungseinträge. Die App-Struktur bleibt erhalten. "
            "**Diese Aktion ist endgültig und kann nicht rückgängig gemacht werden.**"
        )
        reset_check = st.checkbox(
            "Ich habe eine Sicherungskopie erstellt und bestätige den vollständigen Reset.",
            key="dsg_reset_check"
        )
        reset_confirm = st.text_input(
            "Zur Bestätigung **RESET** eintippen:", key="dsg_reset_text"
        )
        if st.button("🔥 Alle Daten löschen", key="dsg_reset_btn",
                     type="primary", disabled=not reset_check):
            if reset_confirm.strip() == "RESET":
                db_komplett_zuruecksetzen()
                for key in list(st.session_state.keys()):
                    if key.startswith("aktiver_spieler") or key == "zweck_bestaetigt":
                        del st.session_state[key]
                st.success("✅ Alle Daten wurden gelöscht. Die App ist zurückgesetzt.")
                st.rerun()
            else:
                st.error("❌ Bestätigungswort falsch — Reset abgebrochen.")

    with tab_export:
        st.markdown("### Daten exportieren")
        alle = spieler_laden()
        if not alle:
            st.info("Keine Spieler vorhanden.")
        else:
            rows = []
            for p in alle:
                fms    = fms_letzter(p["id"])
                y      = y_balance_letzter(p["id"])
                sprint = sprint_letzter(p["id"])
                aus    = ausdauer_letzter(p["id"])
                verlet = verletzungen_laden(p["id"])
                ascore = athletik_score(fms, y, sprint, None, None, aus)
                rs     = risiko_score(fms, y, verlet)
                _, rlv = risiko_label(rs)
                rows.append({
                    "Name":            p["name"],
                    "Position":        p.get("position") or "—",
                    "Mannschaft":      p.get("mannschaft") or "—",
                    "Altersklasse":    p.get("altersklasse") or "—",
                    "Athletik Score":  ascore,
                    "Risiko":          rlv.capitalize(),
                    "FMS":             fms["score"] if fms else "—",
                    "VO₂max":          aus["vo2max"] if aus else "—",
                })
            df_export = pd.DataFrame(rows)
            st.dataframe(df_export, use_container_width=True, hide_index=True)
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Kader-CSV herunterladen", csv,
                               f"kader_export_{date.today()}.csv", "text/csv",
                               use_container_width=True)

        st.markdown("---")
        st.markdown("### Datenbank")
        db_path = "athletik.db"
        import os
        import os as _os
        db_size = _os.path.getsize(db_path) / 1024 if _os.path.exists(db_path) else 0
        st.metric("Datenbankgröße", f"{db_size:.1f} KB")
        st.info("💡 Erstelle regelmäßig Sicherungen der Datei `athletik.db`.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TESTANLEITUNGEN EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def page_export_pdf():
    """Testanleitungen als druckbares PDF exportieren."""
    st.markdown(
        section_header("📄 Testanleitungen exportieren",
                       "Vollständige Coaching-Anleitungen als druckbares PDF"),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:{C['surface']};border:1px solid {C['border']};
                    border-radius:10px;padding:16px 20px;margin-bottom:18px">
          <div style="font-size:13px;color:{C['text']};line-height:1.7">
            Exportiere vollständige Testanleitungen für Coaches ohne App-Zugang.<br>
            Das PDF enthält: <b>Ziel, Aufbau, Durchführung, Trainerhinweis,
            Fehlerquellen, Sicherheitshinweise und Testskizzen</b>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Testauswahl ──────────────────────────────────────────────────────────
    st.markdown("### 📋 Tests auswählen")

    col_auswahl, col_opt = st.columns([3, 1])

    with col_opt:
        alle_auswaehlen = st.checkbox("Alle Tests", value=True, key="pdf_alle")
        mit_deckblatt   = st.checkbox("Deckblatt", value=True, key="pdf_deckblatt")

    with col_auswahl:
        if alle_auswaehlen:
            selected_ids = ALL_TEST_IDS
            # Show labels as info
            muted_color = C["muted"]
            st.markdown(
                f"<div style='color:{muted_color};font-size:12px;padding:4px 0'>"
                + " &nbsp;·&nbsp; ".join(TEST_LABELS[tid] for tid in ALL_TEST_IDS)
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            options     = list(TEST_LABELS.values())
            id_by_label = {v: k for k, v in TEST_LABELS.items()}
            selected_labels = st.multiselect(
                "Tests auswählen",
                options,
                default=options[:3],
                key="pdf_test_select",
                label_visibility="collapsed",
            )
            selected_ids = [id_by_label[lbl] for lbl in selected_labels]

    # ── Vorschau der Inhalte ─────────────────────────────────────────────────
    if selected_ids:
        st.markdown("---")
        st.markdown("### 📑 Enthaltene Abschnitte")

        from test_help import TEST_HELP as _TH
        cols = st.columns(min(len(selected_ids), 3))
        for i, tid in enumerate(selected_ids):
            data = _TH[tid]
            with cols[i % len(cols)]:
                st.markdown(
                    f"""
                    <div style="background:{C['surface']};border:1px solid {C['border']};
                                border-radius:8px;padding:12px 14px;margin-bottom:10px">
                      <div style="font-weight:700;font-size:12px;color:{C['blue']};
                                  margin-bottom:4px">{data['name']}</div>
                      <div style="font-size:11px;color:{C['muted']};line-height:1.5">
                        {data['kurzbeschreibung'][:100]}…
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # ── Generieren ───────────────────────────────────────────────────────
        st.markdown("### 📥 PDF generieren")
        n_tests = len(selected_ids)
        st.info(
            f"**{n_tests} Test{'s' if n_tests != 1 else ''}** ausgewählt. "
            "Das PDF wird direkt im Browser zum Download angeboten."
        )

        if st.button("⚙️ PDF generieren", type="primary", use_container_width=True,
                     key="pdf_generate_btn"):
            with st.spinner("PDF wird erstellt …"):
                try:
                    pdf_bytes = generate_anleitung_pdf(
                        selected_ids,
                        mit_deckblatt=mit_deckblatt,
                    )
                    st.session_state["_pdf_bytes"]    = pdf_bytes
                    st.session_state["_pdf_ready"]    = True
                    st.session_state["_pdf_test_ids"] = selected_ids
                except Exception as exc:
                    st.error(f"Fehler beim Erstellen des PDFs: {exc}")
                    st.session_state["_pdf_ready"] = False

        if st.session_state.get("_pdf_ready") and "_pdf_bytes" in st.session_state:
            ids_in_file = st.session_state.get("_pdf_test_ids", selected_ids)
            if set(ids_in_file) == set(selected_ids):
                pdf_bytes = st.session_state["_pdf_bytes"]
                n = len(ids_in_file)
                if n == len(ALL_TEST_IDS):
                    fname = "Testanleitungen_Komplett.pdf"
                elif n == 1:
                    fname = f"Testanleitung_{TEST_LABELS[ids_in_file[0]].replace(' ', '_')}.pdf"
                else:
                    fname = f"Testanleitungen_{n}_Tests.pdf"

                st.success(f"✅ PDF fertig — {len(pdf_bytes) // 1024} KB")
                st.download_button(
                    label="📥 PDF herunterladen",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True,
                    key="pdf_dl_btn",
                )
    else:
        st.warning("Bitte mindestens einen Test auswählen.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SPIELER-VERGLEICH
# ══════════════════════════════════════════════════════════════════════════════

def page_spieler_vergleich():
    st.markdown("# ⚖️ Spieler-Vergleich")
    st.markdown(
        '<p style="color:#8b949e;margin-top:-8px">Zwei Athleten direkt gegenüberstellen — '
        'Testwerte, Stärken und Defizite auf einen Blick.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    alle_spieler = spieler_laden()
    if len(alle_spieler) < 2:
        st.info("⚠️ Mindestens **zwei Spieler** werden für den Vergleich benötigt. "
                "Bitte unter **Spieler → Verwaltung** weitere Spieler anlegen.")
        return

    # ── Player selectors ──────────────────────────────────────────────────────
    c1, _gap, c2 = st.columns([5, 1, 5])
    with c1:
        sp1 = st.selectbox(
            "🔵 Spieler A",
            alle_spieler,
            format_func=lambda x: x["name"],
            key="vergl_sp1",
        )
    with c2:
        # Default to a different player
        sp2_default = next(
            (p for p in alle_spieler if p["id"] != sp1["id"]),
            alle_spieler[0],
        )
        sp2_idx = next(
            (i for i, p in enumerate(alle_spieler) if p["id"] == sp2_default["id"]), 0
        )
        sp2 = st.selectbox(
            "🟢 Spieler B",
            alle_spieler,
            index=sp2_idx,
            format_func=lambda x: x["name"],
            key="vergl_sp2",
        )

    if sp1["id"] == sp2["id"]:
        st.warning("⚠️ Bitte zwei **verschiedene** Spieler auswählen.")
        return

    # ── Load data ─────────────────────────────────────────────────────────────
    pid1, pid2 = sp1["id"], sp2["id"]
    fms1  = fms_letzter(pid1);        fms2  = fms_letzter(pid2)
    y1    = y_balance_letzter(pid1);  y2    = y_balance_letzter(pid2)
    spr1  = sprint_letzter(pid1);     spr2  = sprint_letzter(pid2)
    spg1  = sprung_letzter(pid1);     spg2  = sprung_letzter(pid2)
    agil1 = agilitaet_letzter(pid1);  agil2 = agilitaet_letzter(pid2)
    aus1  = ausdauer_letzter(pid1);   aus2  = ausdauer_letzter(pid2)

    # ── Composite scores ──────────────────────────────────────────────────────
    sc1 = athletik_score(fms1, y1, spr1, spg1, agil1, aus1)
    sc2 = athletik_score(fms2, y2, spr2, spg2, agil2, aus2)
    sub1 = athletik_sub_scores(fms1, y1, spr1, spg1, agil1, aus1)
    sub2 = athletik_sub_scores(fms2, y2, spr2, spg2, agil2, aus2)

    # ── Score banner ──────────────────────────────────────────────────────────
    def _score_color(s: int) -> str:
        if s >= 75: return C["green"]
        if s >= 50: return C["yellow"]
        return C["red"]

    b1, _bm, b2 = st.columns([5, 1, 5])
    with b1:
        col = _score_color(sc1)
        st.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-left:4px solid #1f6feb;border-radius:10px;padding:16px 20px;text-align:center">'
            f'<div style="font-size:12px;color:{C["muted"]};letter-spacing:1px">SPIELER A</div>'
            f'<div style="font-size:22px;font-weight:800;color:{C["text"]};margin:4px 0">{sp1["name"]}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">'
            f'{sp1.get("hauptposition") or sp1.get("position") or "—"} · '
            f'{sp1.get("mannschaft") or "—"}</div>'
            f'<div style="font-size:32px;font-weight:900;color:{col};margin-top:8px">{sc1}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">Athletik-Score / 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with _bm:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;'
            'height:100%;font-size:24px;color:#30363d;padding-top:30px">VS</div>',
            unsafe_allow_html=True,
        )
    with b2:
        col = _score_color(sc2)
        st.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-left:4px solid #3fb950;border-radius:10px;padding:16px 20px;text-align:center">'
            f'<div style="font-size:12px;color:{C["muted"]};letter-spacing:1px">SPIELER B</div>'
            f'<div style="font-size:22px;font-weight:800;color:{C["text"]};margin:4px 0">{sp2["name"]}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">'
            f'{sp2.get("hauptposition") or sp2.get("position") or "—"} · '
            f'{sp2.get("mannschaft") or "—"}</div>'
            f'<div style="font-size:32px;font-weight:900;color:{col};margin-top:8px">{sc2}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">Athletik-Score / 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar chart ───────────────────────────────────────────────────────────
    _CAT_KEYS   = ["FMS", "Y-Balance", "Sprint", "Sprungkraft", "Agilitaet", "Ausdauer"]
    _CAT_LABELS = ["FMS", "Y-Balance", "Sprint", "Sprungkraft", "Agilität", "Ausdauer"]

    v1 = [sub1.get(k, 0) for k in _CAT_KEYS]
    v2 = [sub2.get(k, 0) for k in _CAT_KEYS]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=v1 + [v1[0]],
        theta=_CAT_LABELS + [_CAT_LABELS[0]],
        fill="toself",
        fillcolor="rgba(31,111,235,0.15)",
        line=dict(color="#1f6feb", width=2),
        name=sp1["name"],
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=v2 + [v2[0]],
        theta=_CAT_LABELS + [_CAT_LABELS[0]],
        fill="toself",
        fillcolor="rgba(63,185,80,0.15)",
        line=dict(color="#3fb950", width=2),
        name=sp2["name"],
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=9, color=C["muted"]),
                gridcolor=C["surface2"],
                linecolor=C["border"],
            ),
            angularaxis=dict(gridcolor=C["surface2"], linecolor=C["border"]),
            bgcolor=C["bg"],
        ),
        paper_bgcolor=C["bg"],
        font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
        legend=dict(
            bgcolor=C["surface"],
            bordercolor=C["border"],
            borderwidth=1,
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.08,
        ),
        margin=dict(l=40, r=40, t=60, b=60),
        title=dict(
            text="Athletisches Profil (normiert 0–100)",
            font=dict(size=15, color=C["text"]),
            x=0.5,
        ),
        height=460,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Detailed comparison table ─────────────────────────────────────────────
    st.markdown("### 📊 Testwerte im Detail")

    # Helper: render a metric cell with traffic-light color
    def _cell(label: str, val, unit: str = "", color: str | None = None) -> str:
        if val is None:
            return (
                f'<div style="padding:8px 0">'
                f'<div style="font-size:11px;color:{C["muted"]}">{label}</div>'
                f'<div style="font-size:13px;color:{C["muted"]};font-style:italic">—</div>'
                f'</div>'
            )
        c = color or C["text"]
        return (
            f'<div style="padding:8px 0">'
            f'<div style="font-size:11px;color:{C["muted"]}">{label}</div>'
            f'<div style="font-size:16px;font-weight:700;color:{c}">{val}{unit}</div>'
            f'</div>'
        )

    def _bewertung_farbe(bew: str | None) -> str:
        if not bew:
            return C["muted"]
        if "Sehr gut" in bew or bew == "Gut":
            return C["green"]
        if "Mittel" in bew:
            return C["yellow"]
        if "Verbesserung" in bew:
            return C["red"]
        return C["muted"]

    def _missing_notice(name: str) -> str:
        return (
            f'<div style="padding:12px 16px;background:{C["surface"]};border-radius:8px;'
            f'border:1px solid {C["border"]};color:{C["muted"]};font-style:italic;font-size:13px">'
            f'ℹ️ {name} hat diesen Test noch nicht absolviert.</div>'
        )

    def _section_header(icon: str, title: str):
        st.markdown(
            f'<div style="margin:24px 0 8px;padding:10px 16px;background:{C["surface2"]};'
            f'border-radius:8px;border-left:3px solid {C["border"]}">'
            f'<span style="font-weight:700;color:{C["text"]}">{icon} {title}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def _row_card(html1: str, html2: str):
        """Render two side-by-side data cards."""
        ca, cb = st.columns(2)
        ca.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-top:3px solid #1f6feb;border-radius:10px;padding:14px 18px">{html1}</div>',
            unsafe_allow_html=True,
        )
        cb.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-top:3px solid #3fb950;border-radius:10px;padding:14px 18px">{html2}</div>',
            unsafe_allow_html=True,
        )

    # ── Column headers ────────────────────────────────────────────────────────
    ha, hb = st.columns(2)
    ha.markdown(
        f'<div style="text-align:center;font-size:12px;color:#1f6feb;font-weight:700;'
        f'letter-spacing:1px;padding:4px 0">🔵 {sp1["name"].upper()}</div>',
        unsafe_allow_html=True,
    )
    hb.markdown(
        f'<div style="text-align:center;font-size:12px;color:#3fb950;font-weight:700;'
        f'letter-spacing:1px;padding:4px 0">🟢 {sp2["name"].upper()}</div>',
        unsafe_allow_html=True,
    )

    # ── FMS ───────────────────────────────────────────────────────────────────
    _section_header("📝", "FMS — Functional Movement Screen")
    if fms1 or fms2:
        def _fms_html(row, name):
            if not row:
                return _missing_notice(name)
            sc  = row["score"]
            col = C["green"] if sc >= 17 else (C["yellow"] if sc >= 14 else C["red"])
            asym = row.get("asymmetrie") or "—"
            asym_col = C["red"] if "Asymmetrie" in str(asym) else C["green"]
            bew = row.get("bewertung") or "—"
            return (
                _cell("Gesamtscore", f"{sc}/21", color=col)
                + _cell("Bewertung", bew, color=_bewertung_farbe(bew))
                + _cell("Asymmetrie", asym, color=asym_col)
            )
        _row_card(_fms_html(fms1, sp1["name"]), _fms_html(fms2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den FMS-Test absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Y-Balance ─────────────────────────────────────────────────────────────
    _section_header("📏", "Y-Balance Test")
    if y1 or y2:
        def _ybal_html(row, name):
            if not row:
                return _missing_notice(name)
            cr = row.get("composite_rechts") or 0
            cl = row.get("composite_links") or 0
            avg = (cr + cl) / 2
            col = C["green"] if avg >= 94 else (C["yellow"] if avg >= 89 else C["red"])
            asym = row.get("asymmetrie") or "—"
            asym_col = C["red"] if "Asymmetrie" in str(asym) else C["green"]
            return (
                _cell("Composite Rechts", f"{cr:.1f}", "%", col)
                + _cell("Composite Links", f"{cl:.1f}", "%", col)
                + _cell("Ø Composite", f"{avg:.1f}", "%", col)
                + _cell("Asymmetrie", asym, color=asym_col)
            )
        _row_card(_ybal_html(y1, sp1["name"]), _ybal_html(y2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Y-Balance-Test absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Sprint ────────────────────────────────────────────────────────────────
    _section_header("⚡", "Sprint-Diagnostik")
    if spr1 or spr2:
        def _spr_html(row, name):
            if not row:
                return _missing_notice(name)
            t10 = row.get("beste_10m")
            t30 = row.get("beste_30m")
            bew10 = row.get("bewertung_10m") or "—"
            bew30 = row.get("bewertung_30m") or "—"
            # Lower is better for sprint times
            def _t_col(t, gut, mittel):
                if t is None: return C["muted"]
                return C["green"] if t <= gut else (C["yellow"] if t <= mittel else C["red"])
            return (
                _cell("10-m Zeit", f"{t10:.2f}" if t10 else "—", " s",
                      _t_col(t10, 1.80, 1.95))
                + _cell("Bewertung 10 m", bew10, color=_bewertung_farbe(bew10))
                + _cell("30-m Zeit", f"{t30:.2f}" if t30 else "—", " s",
                        _t_col(t30, 4.00, 4.30))
                + _cell("Bewertung 30 m", bew30, color=_bewertung_farbe(bew30))
            )
        _row_card(_spr_html(spr1, sp1["name"]), _spr_html(spr2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat die Sprint-Diagnostik absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Sprung ────────────────────────────────────────────────────────────────
    _section_header("🦘", "Sprung-Diagnostik")
    if spg1 or spg2:
        def _spg_html(row, name):
            if not row:
                return _missing_notice(name)
            cmj  = row.get("cmj_beid")
            asym = row.get("cmj_asymmetrie")
            rsi  = row.get("rsi")
            sw   = row.get("standweit")
            bew  = row.get("bewertung_cmj") or "—"
            cmj_col = C["green"] if (cmj and cmj >= 40) else (C["yellow"] if (cmj and cmj >= 30) else C["red"])
            asym_col = (C["red"] if (asym and float(asym) > 10) else C["green"]) if asym is not None else C["muted"]
            return (
                _cell("CMJ beidbeinig", f"{cmj:.1f}" if cmj else "—", " cm", cmj_col)
                + _cell("Bewertung CMJ", bew, color=_bewertung_farbe(bew))
                + _cell("CMJ-Asymmetrie", f"{float(asym):.1f}" if asym is not None else "—", " %", asym_col)
                + _cell("RSI", f"{float(rsi):.2f}" if rsi else "—",
                        color=(C["green"] if rsi and float(rsi) >= 1.5 else C["yellow"]) if rsi else C["muted"])
                + _cell("Standweit", f"{sw:.2f}" if sw else "—", " m")
            )
        _row_card(_spg_html(spg1, sp1["name"]), _spg_html(spg2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat die Sprung-Diagnostik absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Agilität ──────────────────────────────────────────────────────────────
    _section_header("🔀", "Agilität")
    if agil1 or agil2:
        def _agil_html(row, name):
            if not row:
                return _missing_notice(name)
            t505r = row.get("t505_r")
            t505l = row.get("t505_l")
            asym  = row.get("asym_505")
            t_test = row.get("t_test")
            bew505 = row.get("bew_505") or "—"
            bew_t  = row.get("bew_t_test") or "—"
            asym_col = (C["red"] if asym and float(asym) > 10 else C["green"]) if asym is not None else C["muted"]
            return (
                _cell("505-Test rechts", f"{t505r:.2f}" if t505r else "—", " s")
                + _cell("505-Test links", f"{t505l:.2f}" if t505l else "—", " s")
                + _cell("Asymmetrie 505", f"{float(asym):.1f}" if asym is not None else "—", " %", asym_col)
                + _cell("T-Test", f"{t_test:.2f}" if t_test else "—", " s")
                + _cell("Bewertung T-Test", bew_t, color=_bewertung_farbe(bew_t))
            )
        _row_card(_agil_html(agil1, sp1["name"]), _agil_html(agil2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Agilitätstest absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    _section_header("🫁", "Ausdauer (Yo-Yo)")
    if aus1 or aus2:
        def _aus_html(row, name):
            if not row:
                return _missing_notice(name)
            dist = row.get("distanz_m")
            vo2  = row.get("vo2max")
            bew  = row.get("bewertung") or "—"
            dist_col = C["green"] if dist and dist >= 1600 else (C["yellow"] if dist and dist >= 800 else C["red"])
            vo2_col  = C["green"] if vo2 and float(vo2) >= 55 else (C["yellow"] if vo2 and float(vo2) >= 45 else C["red"])
            return (
                _cell("Distanz", f"{int(dist)}" if dist else "—", " m", dist_col)
                + _cell("VO₂max", f"{float(vo2):.1f}" if vo2 else "—", " ml/kg/min", vo2_col)
                + _cell("Bewertung", bew, color=_bewertung_farbe(bew))
            )
        _row_card(_aus_html(aus1, sp1["name"]), _aus_html(aus2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Ausdauertest absolviert.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Missing tests summary ─────────────────────────────────────────────────
    def _fehlende_tests(name, fms, y, spr, spg, agil, aus):
        fehlend = []
        if not fms:  fehlend.append("FMS")
        if not y:    fehlend.append("Y-Balance")
        if not spr:  fehlend.append("Sprint")
        if not spg:  fehlend.append("Sprung")
        if not agil: fehlend.append("Agilität")
        if not aus:  fehlend.append("Ausdauer")
        return fehlend

    f1 = _fehlende_tests(sp1["name"], fms1, y1, spr1, spg1, agil1, aus1)
    f2 = _fehlende_tests(sp2["name"], fms2, y2, spr2, spg2, agil2, aus2)

    if f1 or f2:
        st.markdown("#### ℹ️ Ausstehende Tests")
        nc1, nc2 = st.columns(2)
        with nc1:
            if f1:
                st.warning(
                    f"**{sp1['name']}** hat folgende Tests noch nicht absolviert: "
                    + ", ".join(f1)
                )
        with nc2:
            if f2:
                st.warning(
                    f"**{sp2['name']}** hat folgende Tests noch nicht absolviert: "
                    + ", ".join(f2)
                )


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION  (7-section structure)
# ══════════════════════════════════════════════════════════════════════════════

# ── Sub-page maps per section ─────────────────────────────────────────────────
_SUB_SPIELER = {
    "👥 Verwaltung":        page_spieler,
    "🏃 Profil & Diagnostik": page_spieler_profil,
    "📐 Anthropometrie":    page_anthropometrie,
}
_SUB_DIAGNOSTIK = {
    "📝 FMS":               page_fms,
    "📏 Y-Balance":         page_ybalance,
    "⚡ Sprint":             page_sprint,
    "🦘 Sprung":             page_sprung,
    "🔀 Agilität":          page_agilitaet,
    "🫁 Ausdauer (Yo-Yo)":  page_ausdauer,
}
_SUB_TRAINING = {
    "📅 Trainingsplan":     page_trainingsplan,
    "🔄 Periodisierung":    page_periodisierung,
}

_MAIN_SECTIONS = [
    "🏠  Startseite",
    "👤  Spieler",
    "🔬  Diagnostik",
    "📅  Training",
    "📈  Entwicklung",
    "⚖️  Vergleich",
    "👥  Mannschaft",
    "📄  Anleitungen",
    "⚙️  Einstellungen",
]

with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="padding:18px 0 10px;text-align:center">'
        f'<div style="font-size:38px">⚽</div>'
        f'<div style="font-weight:800;font-size:14px;color:{C["text"]};letter-spacing:1px;margin-top:4px">ATHLETIK DIAGNOSTIK</div>'
        f'<div style="font-size:10px;color:{C["muted"]};margin-top:2px">Football Performance System</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Global player selector ────────────────────────────────────────────────
    alle_spieler = spieler_laden()
    if alle_spieler:
        pid_current = st.session_state.get("global_player_id")
        idx_current = 0
        if pid_current:
            ids = [p["id"] for p in alle_spieler]
            if pid_current in ids:
                idx_current = ids.index(pid_current)
        sel_player = st.selectbox(
            "Aktiver Spieler",
            alle_spieler,
            index=idx_current,
            format_func=lambda x: x["name"],
            key="sidebar_player_sel",
        )
        st.session_state["global_player_id"] = sel_player["id"]
        # Show player pill
        pos  = sel_player.get("hauptposition") or sel_player.get("position") or "—"
        team = sel_player.get("mannschaft") or "—"
        st.markdown(
            f'<div class="player-pill">'
            f'<div class="player-pill-sub">{pos} · {team}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="padding:8px 0;color:{C["muted"]};font-size:12px">Kein Spieler angelegt.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<hr style="border-color:{C["surface2"]};margin:10px 0">', unsafe_allow_html=True)

    # ── Pending navigation from quick-action buttons ───────────────────────────
    # Must be applied before the widget is instantiated to avoid StreamlitAPIException
    if "_nav_goto" in st.session_state:
        st.session_state["nav_section"] = st.session_state.pop("_nav_goto")

    # ── Main navigation ───────────────────────────────────────────────────────
    section = st.radio(
        "",
        _MAIN_SECTIONS,
        key="nav_section",
        label_visibility="collapsed",
    )

    # ── Sub-navigation ────────────────────────────────────────────────────────
    sub_map = None
    sub_key = None
    if section == "👤  Spieler":
        sub_map, sub_key = _SUB_SPIELER, "nav_sub_spieler"
    elif section == "🔬  Diagnostik":
        sub_map, sub_key = _SUB_DIAGNOSTIK, "nav_sub_diagnostik"
    elif section == "📅  Training":
        sub_map, sub_key = _SUB_TRAINING, "nav_sub_training"

    sub_choice = None
    if sub_map:
        st.markdown('<div class="subnav">', unsafe_allow_html=True)
        sub_choice = st.radio(
            "",
            list(sub_map.keys()),
            key=sub_key,
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<hr style="border-color:{C["surface2"]};margin:10px 0">', unsafe_allow_html=True)

    # ── Kader count ───────────────────────────────────────────────────────────
    n = len(alle_spieler) if alle_spieler else 0
    st.markdown(
        f'<div style="padding:8px 12px;background:{C["surface"]};border-radius:8px;border:1px solid {C["border"]}">'
        f'<div style="font-size:10px;color:{C["muted"]};letter-spacing:1px">KADER</div>'
        f'<div style="font-size:20px;font-weight:700;color:{C["text"]}">{n} Spieler</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Route ─────────────────────────────────────────────────────────────────────
if section == "🏠  Startseite":
    page_startseite()
elif section == "👤  Spieler":
    _SUB_SPIELER[sub_choice]()
elif section == "🔬  Diagnostik":
    _SUB_DIAGNOSTIK[sub_choice]()
elif section == "📅  Training":
    _SUB_TRAINING[sub_choice]()
elif section == "📈  Entwicklung":
    page_fortschritt()
elif section == "⚖️  Vergleich":
    page_spieler_vergleich()
elif section == "👥  Mannschaft":
    page_dashboard()
elif section == "📄  Anleitungen":
    page_export_pdf()
elif section == "⚙️  Einstellungen":
    page_einstellungen()
    st.markdown(
        '<div style="text-align:center;padding:16px 0 8px">'
        '<div style="font-size:36px">⚽</div>'
        '<div style="font-weight:700;font-size:15px;color:#e6edf3;letter-spacing:0.5px">ATHLETIK DIAGNOSTIK</div>'
        '<div style="font-size:11px;color:#8b949e;margin-top:2px">Football Performance System</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr style="border-color:#30363d;margin:12px 0">', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "🏠 Coach Dashboard",
            "👤 Spielerverwaltung",
            "🏃 Spielerprofil",
            "📐 Anthropometrie",
            "📝 FMS Test",
            "📏 Y-Balance Test",
            "⚡ Sprint-Diagnostik",
            "🦘 Sprung-Diagnostik",
            "🔀 Agilität",
            "🫁 Ausdauer (Yo-Yo)",
            "📅 Trainingsplan",
            "🔄 Periodisierung",
            "📈 Fortschritt",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<hr style="border-color:#30363d;margin:12px 0">', unsafe_allow_html=True)
    spieler_count = len(spieler_laden())
    st.markdown(
        f'<div style="padding:10px 8px;background:#161b22;border-radius:8px;border:1px solid #30363d">'
        f'<div style="font-size:11px;color:#8b949e">KADER</div>'
        f'<div style="font-size:22px;font-weight:700;color:#e6edf3">{spieler_count} Spieler</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Route ─────────────────────────────────────────────────────────────────────
pages = {
    "🏠 Coach Dashboard":   page_dashboard,
    "👤 Spielerverwaltung": page_spieler,
    "🏃 Spielerprofil":     page_spieler_profil,
    "📐 Anthropometrie":    page_anthropometrie,
    "📝 FMS Test":          page_fms,
    "📏 Y-Balance Test":    page_ybalance,
    "⚡ Sprint-Diagnostik": page_sprint,
    "🦘 Sprung-Diagnostik": page_sprung,
    "🔀 Agilität":          page_agilitaet,
    "🫁 Ausdauer (Yo-Yo)":  page_ausdauer,
    "📅 Trainingsplan":     page_trainingsplan,
    "🔄 Periodisierung":    page_periodisierung,
    "📈 Fortschritt":       page_fortschritt,
}
