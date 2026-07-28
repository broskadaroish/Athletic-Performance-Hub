"""
Football Athletik Diagnostik System
────────────────────────────────────
Main Streamlit entry point.  All pages live in this single file to keep
imports simple; shared logic is delegated to the module layer.
"""

import streamlit as st
from datetime import date
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

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
TRAININGSSTATUS   = ["Volltraining", "Eingeschränktes Training", "Reha", "Verletzt / Ausfall", "Pause / Urlaub"]
VERLETZUNGSARTEN  = ["Muskel", "Sehne / Band", "Knochen / Knorpel", "Prellung / Kontusion", "Sonstiges"]
KOERPERTEILE      = ["Sprunggelenk", "Knie", "Oberschenkel", "Leiste", "Hüfte", "Lendenwirbel", "Schulter", "Sonstiges"]
SCHWEREGRADE      = ["Leicht (1–7 Tage)", "Mittel (8–28 Tage)", "Schwer (> 28 Tage)"]
from training import init_training_bibliothek, empfehlung_bereiche, uebungen_fuer_bereiche
from fms import FMSResult
from y_balance import YBalanceResult
from analytics import (
    risiko_score, risiko_label, athletik_score,
    defizite_ermitteln, schwerpunkt_sammeln,
)
from periodisierung import zyklus_erstellen, zyklus_laden
from pdf_report import generate_report

# ─── Bootstrap ────────────────────────────────────────────────────────────────
init_db()
init_training_bibliothek()

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Football Athletik Diagnostik",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Dark UI theme (CSS) ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}
section[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
/* ── Headers ── */
h1, h2, h3, h4 { color: #ffffff !important; }
/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 12px; }
[data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 26px; font-weight: 700; }
/* ── Score badge ── */
.score-badge {
    display:inline-block; padding:6px 18px; border-radius:50px;
    font-weight:700; font-size:20px; letter-spacing:1px;
}
.badge-green  { background:#0d3b2e; color:#3fb950; border:1px solid #3fb950; }
.badge-yellow { background:#3b2a0d; color:#d29922; border:1px solid #d29922; }
.badge-red    { background:#3b0d0d; color:#f85149; border:1px solid #f85149; }
/* ── Cards ── */
.card {
    background:#161b22; border:1px solid #30363d; border-radius:12px;
    padding:20px 24px; margin-bottom:14px;
}
.card-title {
    font-size:13px; font-weight:600; text-transform:uppercase;
    letter-spacing:1px; color:#8b949e; margin-bottom:8px;
}
.card-value { font-size:28px; font-weight:700; color:#e6edf3; }
/* ── Deficit tag ── */
.tag-crit {
    display:inline-block; background:#3b0d0d; color:#f85149;
    border:1px solid #f85149; border-radius:6px;
    padding:3px 10px; font-size:12px; font-weight:600; margin:3px;
}
.tag-warn {
    display:inline-block; background:#3b2a0d; color:#d29922;
    border:1px solid #d29922; border-radius:6px;
    padding:3px 10px; font-size:12px; font-weight:600; margin:3px;
}
/* ── Progress bar ── */
.prog-wrap { background:#21262d; border-radius:6px; height:10px; margin:4px 0 10px; }
.prog-fill  { height:10px; border-radius:6px; }
/* ── Inputs / selects ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stTextArea"] textarea {
    background:#21262d !important; color:#e6edf3 !important;
    border:1px solid #30363d !important; border-radius:6px !important;
}
/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,#1f6feb,#388bfd);
    color:#fff; border:none; border-radius:8px;
    font-weight:600; letter-spacing:0.5px;
    padding:10px 24px; transition:all .2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#388bfd,#58a6ff);
    transform:translateY(-1px);
}
/* ── Tables ── */
.dataframe { background:#161b22 !important; color:#e6edf3 !important; }
thead tr th { background:#21262d !important; color:#8b949e !important; }
tbody tr:nth-child(even) { background:#0d1117 !important; }
/* ── Tabs ── */
[data-testid="stTab"] { color:#8b949e; }
button[aria-selected="true"] { color:#58a6ff !important; border-color:#58a6ff !important; }
/* ── Divider ── */
hr { border-color:#30363d; }
/* ── Sidebar radio ── */
[data-testid="stSidebarContent"] label { color:#c9d1d9 !important; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _risk_badge(level: str) -> str:
    cls = {"hoch": "badge-red", "mittel": "badge-yellow", "gering": "badge-green"}.get(level, "badge-green")
    icons = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    labels = {"hoch": "HOHES RISIKO", "mittel": "MITTLERES RISIKO", "gering": "GERINGES RISIKO"}
    return f'<span class="score-badge {cls}">{icons[level]} {labels[level]}</span>'


def _score_badge(score: int) -> str:
    cls = "badge-green" if score >= 75 else "badge-yellow" if score >= 50 else "badge-red"
    return f'<span class="score-badge {cls}">{score}<span style="font-size:14px;font-weight:400">/100</span></span>'


def _progress_html(value: int, max_val: int, color: str = "#1f6feb") -> str:
    pct = min(value / max_val * 100, 100)
    return f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'


def _color_for_score(score: int, max_val: int = 100) -> str:
    pct = score / max_val
    if pct >= 0.75:
        return "#3fb950"
    if pct >= 0.5:
        return "#d29922"
    return "#f85149"


def _player_selector(key_suffix="") -> tuple | None:
    spieler = spieler_laden()
    if not spieler:
        st.info("👤 Noch keine Spieler angelegt. Bitte zuerst einen Spieler erstellen.")
        return None
    return st.selectbox(
        "Spieler auswählen",
        spieler,
        format_func=lambda x: f"{x['name']}  —  {x['position'] or ''}  ({x['mannschaft'] or ''})",
        key=f"player_sel_{key_suffix}",
    )


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

    for p in all_players:
        fms = fms_letzter(p["id"])
        y   = y_balance_letzter(p["id"])
        rs  = risiko_score(fms, y)
        _, level = risiko_label(rs)
        if level == "hoch":   high_risk += 1
        elif level == "mittel": med_risk += 1
        else:                   low_risk += 1
        scores.append(athletik_score(fms, y))

    avg_score = round(sum(scores) / len(scores)) if scores else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spieler gesamt", total)
    c2.metric("Hohes Risiko 🔴", high_risk)
    c3.metric("Mittleres Risiko 🟡", med_risk)
    c4.metric("Ø Athletik Score", f"{avg_score}/100")

    st.markdown("---")

    # ── Risk breakdown pie ─────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### Risikoverteilung")
        fig_pie = go.Figure(go.Pie(
            labels=["Hohes Risiko", "Mittleres Risiko", "Geringes Risiko"],
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
    for p, s in zip(all_players, scores):
        fms = fms_letzter(p["id"])
        y   = y_balance_letzter(p["id"])
        rs  = risiko_score(fms, y)
        _, level = risiko_label(rs)
        icon = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}[level]
        rows.append({
            "Name":          p["name"],
            "Position":      p["position"] or "—",
            "Mannschaft":    p["mannschaft"] or "—",
            "Athletik Score": s,
            "FMS Score":     fms["score"] if fms else "—",
            "Y-Balance Ø":   f"{(y['composite_rechts']+y['composite_links'])/2:.1f}%" if y else "—",
            "Risiko":        f"{icon} {level.capitalize()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


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

    auswahl = _player_selector("fms")
    if not auswahl:
        return

    spieler_id = auswahl["id"]

    st.markdown("---")
    st.markdown("### Testergebnisse eingeben")

    c1, c2, c3 = st.columns(3)
    deep        = c1.number_input("Deep Squat", 0, 3, key="ds")
    trunk       = c2.number_input("Trunk Stability Push-up", 0, 3, key="ts")
    st.markdown("##### Bilateral — Links / Rechts")
    col_l, col_r = st.columns(2)
    hurdle_l    = col_l.number_input("Hurdle Step Links",        0, 3, key="hl")
    hurdle_r    = col_r.number_input("Hurdle Step Rechts",       0, 3, key="hr")
    inline_l    = col_l.number_input("Inline Lunge Links",       0, 3, key="il")
    inline_r    = col_r.number_input("Inline Lunge Rechts",      0, 3, key="ir")
    shoulder_l  = col_l.number_input("Shoulder Mobility Links",  0, 3, key="shl")
    shoulder_r  = col_r.number_input("Shoulder Mobility Rechts", 0, 3, key="shr")
    aslr_l      = col_l.number_input("ASLR Links",               0, 3, key="al")
    aslr_r      = col_r.number_input("ASLR Rechts",              0, 3, key="ar")
    rotary_l    = col_l.number_input("Rotary Stability Links",   0, 3, key="rl")
    rotary_r    = col_r.number_input("Rotary Stability Rechts",  0, 3, key="rr")

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

    auswahl = _player_selector("yb")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    st.markdown("---")

    col1, col2 = st.columns(2)
    bein_r = col1.number_input("Beinlänge Rechts (cm) *", min_value=1.0, value=90.0, step=0.5)
    bein_l = col2.number_input("Beinlänge Links (cm) *",  min_value=1.0, value=90.0, step=0.5)

    st.markdown("#### Reichweiten (cm)")
    ch1, ch2 = st.columns(2)
    ch1.markdown("**Rechte Seite**")
    ch2.markdown("**Linke Seite**")
    ant_r  = ch1.number_input("Anterior R",       0.0, 200.0, 0.0, step=0.5, key="antr")
    ant_l  = ch2.number_input("Anterior L",       0.0, 200.0, 0.0, step=0.5, key="antl")
    pm_r   = ch1.number_input("Posteromedial R",  0.0, 200.0, 0.0, step=0.5, key="pmr")
    pm_l   = ch2.number_input("Posteromedial L",  0.0, 200.0, 0.0, step=0.5, key="pml")
    pl_r   = ch1.number_input("Posterolateral R", 0.0, 200.0, 0.0, step=0.5, key="plr")
    pl_l   = ch2.number_input("Posterolateral L", 0.0, 200.0, 0.0, step=0.5, key="pll")

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

    sid   = auswahl["id"]
    fms   = fms_letzter(sid)
    y     = y_balance_letzter(sid)
    rs    = risiko_score(fms, y)
    label, level = risiko_label(rs)
    ascore = athletik_score(fms, y)
    defizite = defizite_ermitteln(fms, y)
    schwerpunkt = schwerpunkt_sammeln(fms, y)
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
        status_color = "#f85149" if "verletzt" in status.lower() or "ausfall" in status.lower() \
                       else "#d29922" if "eingeschränkt" in status.lower() or "reha" in status.lower() \
                       else "#3fb950"
        st.markdown(
            f"<small style='color:#8b949e'>{ak}  ·  {niv}  ·  "
            f"<span style='color:{status_color};font-weight:600'>{status}</span></small>",
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown("**Athletik Score**")
        st.markdown(_score_badge(ascore), unsafe_allow_html=True)
    with h3:
        st.markdown("**Verletzungsrisiko**")
        st.markdown(_risk_badge(level), unsafe_allow_html=True)

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
                    css = "tag-crit" if d["level"] == "kritisch" else "tag-warn"
                    st.markdown(
                        f'<div class="card"><span class="{css}">{d["bereich"]}</span>'
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
            v_notizen    = st.text_area("Notizen / Diagnose", key="v_notizen", height=80)
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
            st.download_button(
                label="⬇️ PDF herunterladen",
                data=pdf_bytes,
                file_name=f"athletik_report_{auswahl['name'].replace(' ','_')}_{date.today()}.pdf",
                mime="application/pdf",
                key="pdf_dl",
            )


# ──────────────────────────────────────────────────────────────────────────────

def page_trainingsplan():
    st.markdown("# 📅 Trainingsplan")

    auswahl = _player_selector("plan")
    if not auswahl:
        return

    sid = auswahl["id"]
    fms = fms_letzter(sid)
    y   = y_balance_letzter(sid)
    schwerpunkt = schwerpunkt_sammeln(fms, y)

    tab_auto, tab_manual, tab_view = st.tabs(["🤖 Automatisch generieren", "✍️ Manuell hinzufügen", "📋 Plan anzeigen"])

    with tab_auto:
        st.markdown("### Individuellen Plan aus Diagnostik generieren")
        bereiche = empfehlung_bereiche(schwerpunkt)
        if bereiche:
            st.info(f"**Erkannte Schwerpunkte aus FMS + Y-Balance:** {', '.join(bereiche)}")
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

    sid = auswahl["id"]
    fms = fms_letzter(sid)
    y   = y_balance_letzter(sid)
    schwerpunkt = schwerpunkt_sammeln(fms, y)

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

    fms_hist = fms_history(sid)
    yb_hist  = y_balance_history(sid)

    tab_fms, tab_yb = st.tabs(["FMS Verlauf", "Y-Balance Verlauf"])

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
                text=df["Score"],
                textposition="top center",
                line=dict(color="#3b82f6", width=3),
                marker=dict(size=9, color="#58a6ff"),
                name="FMS Score",
            ))
            # Risk threshold lines
            fig.add_hline(y=14, line_dash="dash", line_color="#d29922",
                          annotation_text="Beobachten ≤14", annotation_position="top right")
            fig.add_hline(y=12, line_dash="dash", line_color="#f85149",
                          annotation_text="Hohes Risiko ≤12", annotation_position="top right")
            fig.update_layout(**_pl(height=340, title="FMS Score Verlauf", yaxis=dict(range=[0, 22])))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

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
                line=dict(color="#3b82f6", width=3),
                marker=dict(size=9),
            ))
            fig2.add_trace(go.Scatter(
                x=df["Datum"], y=df["Composite L"],
                mode="lines+markers", name="Links",
                line=dict(color="#f85149", width=3),
                marker=dict(size=9),
            ))
            fig2.add_hline(y=89, line_dash="dash", line_color="#d29922",
                           annotation_text="Normwert 89 %", annotation_position="top right")
            fig2.update_layout(**_pl(height=340, title="Y-Balance Composite Score Verlauf", yaxis=dict(range=[70, 115])))
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_anthropometrie():
    st.markdown("# 📐 Anthropometrie")
    st.markdown("Körpermessungen, BMI und Wachstumsverlauf — Grundlage für belastungsgerechtes Training.")

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
        groesse      = c1.number_input("Körpergröße (cm)", 100.0, 220.0,
                                        float(letzter["groesse"]) if letzter else 175.0,
                                        step=0.5, key="anthro_groesse")
        gewicht      = c1.number_input("Körpergewicht (kg)", 30.0, 150.0,
                                        float(letzter["gewicht"]) if letzter else 70.0,
                                        step=0.5, key="anthro_gewicht")
        koerperfett  = c1.number_input("Körperfett (%)", 0.0, 50.0,
                                        float(letzter["koerperfett"]) if letzter else 12.0,
                                        step=0.1, key="anthro_kf")
        muskelmasse  = c1.number_input("Muskelmasse (kg)", 0.0, 100.0,
                                        float(letzter["muskelmasse"]) if letzter else 0.0,
                                        step=0.5, key="anthro_mm")
        sitzhoehe    = c2.number_input("Sitzhöhe (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["sitzhoehe"]) if letzter else 0.0,
                                        step=0.5, key="anthro_sh")
        beinlaenge   = c2.number_input("Beinlänge (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["beinlaenge"]) if letzter else 0.0,
                                        step=0.5, key="anthro_bl")
        armspann     = c2.number_input("Armspannweite (cm)", 0.0, 250.0,
                                        float(letzter["armspannweite"]) if letzter else 0.0,
                                        step=0.5, key="anthro_arm")

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

def _sprint_eingabe(distanz_label: str, key_prefix: str, letzter_row, col):
    """Hilfsfunktion: 3-Versuch-Eingabe für eine Sprint-Distanz."""
    col.markdown(f"**{distanz_label}**")
    c1, c2, c3 = col.columns(3)
    v1 = c1.number_input("V1", 0.0, 20.0, 0.0, step=0.01, format="%.2f", key=f"{key_prefix}_v1", label_visibility="collapsed")
    v2 = c2.number_input("V2", 0.0, 20.0, 0.0, step=0.01, format="%.2f", key=f"{key_prefix}_v2", label_visibility="collapsed")
    v3 = c3.number_input("V3", 0.0, 20.0, 0.0, step=0.01, format="%.2f", key=f"{key_prefix}_v3", label_visibility="collapsed")
    bester = min((v for v in [v1, v2, v3] if v > 0), default=None)
    if bester:
        col.markdown(f'<small style="color:#8b949e">Bester Versuch: <b style="color:#58a6ff">{bester:.2f} s</b></small>', unsafe_allow_html=True)
    return v1, v2, v3, bester


def page_sprint():
    st.markdown("# ⚡ Sprint-Diagnostik")
    st.markdown("Lineare Beschleunigung und Maximalgeschwindigkeit — 5 m bis 30 m, je 3 Versuche.")

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
        st.caption("Nicht gemessene Distanzen einfach auf 0.00 lassen.")

        c_l, c_r = st.columns(2)
        v1_5,  v2_5,  v3_5,  b5  = _sprint_eingabe("5 m",  "s5",  letzter, c_l)
        v1_10, v2_10, v3_10, b10 = _sprint_eingabe("10 m", "s10", letzter, c_l)
        v1_20, v2_20, v3_20, b20 = _sprint_eingabe("20 m", "s20", letzter, c_r)
        v1_30, v2_30, v3_30, b30 = _sprint_eingabe("30 m", "s30", letzter, c_r)

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

        c1, c2 = st.columns(2)
        c1.markdown("**CMJ beidbeinig (cm)**")
        cmj_beid = c1.number_input("CMJ beidbeinig", 0.0, 100.0, 0.0, step=0.5, key="cmj_beid", label_visibility="collapsed")
        c1.markdown("**CMJ einbeinig rechts (cm)**")
        cmj_r    = c1.number_input("CMJ rechts", 0.0, 80.0, 0.0, step=0.5, key="cmj_r", label_visibility="collapsed")
        c1.markdown("**CMJ einbeinig links (cm)**")
        cmj_l    = c1.number_input("CMJ links", 0.0, 80.0, 0.0, step=0.5, key="cmj_l", label_visibility="collapsed")
        c1.markdown("**Squat Jump (cm)**")
        squat    = c1.number_input("Squat Jump", 0.0, 100.0, 0.0, step=0.5, key="squat", label_visibility="collapsed")

        c2.markdown("**Drop Jump — Höhe (cm)**")
        dj_h  = c2.number_input("Drop Jump Höhe", 0.0, 80.0, 0.0, step=0.5, key="dj_h", label_visibility="collapsed")
        c2.markdown("**Drop Jump — Kontaktzeit (s)**")
        dj_kz = c2.number_input("Drop Jump Kontaktzeit", 0.0, 2.0, 0.0, step=0.01, format="%.2f", key="dj_kz", label_visibility="collapsed")
        c2.markdown("**Standweitsprung (cm)**")
        swj   = c2.number_input("Standweitsprung", 0.0, 400.0, 0.0, step=1.0, key="swj", label_visibility="collapsed")

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

def _zeit_eingabe(label: str, key: str, col, letzter=None, letzter_key=None):
    """Hilfsfunktion: Zeiteingabe mit Vorschau-Bewertung."""
    col.markdown(f"**{label}**")
    default = float(letzter[letzter_key]) if (letzter and letzter_key and letzter.get(letzter_key)) else 0.0
    v = col.number_input(label, 0.0, 30.0, default, step=0.01, format="%.2f",
                         key=key, label_visibility="collapsed")
    return v if v > 0 else None


def page_agilitaet():
    st.markdown("# 🔀 Agilität & Richtungswechsel")
    st.markdown("505-Test, 5-10-5 Shuttle, T-Test, Illinois Agility Run — Richtungswechsel-Fähigkeit und Abbremsstärke.")

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
        t505_r  = _zeit_eingabe("505-Test rechts (s)", "a505r", c1, letzter, "t505_r")
        t505_l  = _zeit_eingabe("505-Test links (s)",  "a505l", c1, letzter, "t505_l")
        t5_10_5 = _zeit_eingabe("5-10-5 Shuttle (s)",  "a5105", c2, letzter, "t5_10_5")
        t_test  = _zeit_eingabe("T-Test (s)",           "att",   c2, letzter, "t_test")
        illinois = _zeit_eingabe("Illinois Agility (s)","aill",  c1, letzter, "illinois")

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

ALTERSGRUPPEN_YO = ["U13/U14", "U15/U16", "U17/U18", "Senioren"]
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
        if a < 15: return "U13/U14"
        if a < 17: return "U15/U16"
        if a < 19: return "U17/U18"
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
        c3, c4, c5 = st.columns(3)
        distanz_m = c3.number_input("Erzielte Distanz (m)", 0, 5000,
                                     int(letzter["distanz_m"]) if letzter else 0,
                                     step=40, key="aus_dist")
        hf_max    = c4.number_input("HF max (bpm)", 0, 230,
                                     int(letzter["hf_max"]) if letzter and letzter.get("hf_max") else 0,
                                     step=1, key="aus_hf")
        rpe_val   = c5.selectbox("RPE (Borg 6–20)", list(range(6, 21)),
                                  index=9, key="aus_rpe",
                                  format_func=lambda x: RPE_LABELS.get(x, str(x)))

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
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
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
pages[page]()
