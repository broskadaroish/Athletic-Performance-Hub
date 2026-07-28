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
    fms_speichern, fms_letzter, fms_history,
    y_balance_speichern, y_balance_letzter, y_balance_history,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern, trainingsplan_laden,
)
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
        fig_bar.update_layout(**PLOTLY_LAYOUT, height=260,
                              yaxis=dict(range=[0, 105], **PLOTLY_LAYOUT["yaxis"]))
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
        col1, col2 = st.columns(2)
        name         = col1.text_input("Name *")
        geburtsdatum = col2.text_input("Geburtsdatum (z. B. 15.03.2002)")
        position     = col1.selectbox("Position", ["Torwart", "Innenverteidiger", "Außenverteidiger", "Mittelfeld", "Flügel", "Stürmer"])
        spielbein    = col2.selectbox("Spielbein", ["Rechts", "Links", "Beidfüßig"])
        mannschaft   = col1.text_input("Mannschaft")

        if st.button("💾 Spieler speichern", use_container_width=False):
            if not name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                spieler_speichern(name.strip(), geburtsdatum, position, spielbein, mannschaft)
                st.success(f"✅ Spieler **{name}** wurde gespeichert.")
                st.rerun()

    with tab_list:
        spieler = spieler_laden()
        if not spieler:
            st.info("Noch keine Spieler vorhanden.")
            return
        df = pd.DataFrame([dict(row) for row in spieler])
        df.columns = ["ID", "Name", "Geburtsdatum", "Position", "Spielbein", "Mannschaft"]
        st.dataframe(df.drop("ID", axis=1), use_container_width=True, hide_index=True)

        with st.expander("🗑️ Spieler löschen"):
            del_auswahl = st.selectbox("Spieler wählen", spieler, format_func=lambda x: x["name"], key="del_sel")
            if st.button("⚠️ Spieler löschen", type="primary"):
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

    # ── Header ────────────────────────────────────────────────────────────
    h1, h2, h3 = st.columns([2, 1, 1])
    with h1:
        st.markdown(f"## {auswahl['name']}")
        st.markdown(f"🏟️ {auswahl['position'] or '—'}  ·  {auswahl['mannschaft'] or '—'}  ·  Spielbein: {auswahl['spielbein'] or '—'}")
    with h2:
        st.markdown("**Athletik Score**")
        st.markdown(_score_badge(ascore), unsafe_allow_html=True)
    with h3:
        st.markdown("**Verletzungsrisiko**")
        st.markdown(_risk_badge(level), unsafe_allow_html=True)

    st.markdown("---")

    # ── Key metrics ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("FMS Score",       f"{fms['score']}/21" if fms else "Kein Test", delta=None)
    m2.metric("FMS Bewertung",   fms["bewertung"] if fms else "—")
    if y:
        avg_y = (y["composite_rechts"] + y["composite_links"]) / 2
        m3.metric("Y-Balance Ø",    f"{avg_y:.1f} %")
        m4.metric("Y-Balance Asym.", y["asymmetrie"][:25] if y else "—")
    else:
        m3.metric("Y-Balance",    "Kein Test")
        m4.metric("Y-Balance",    "—")

    st.markdown("---")

    # ── Defizite ──────────────────────────────────────────────────────────
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
                            f"Problem: {u['problem']} · {u['saetze']} Sätze · {u['wiederholungen']} · {u['haeufigkeit']}"
                        )

    st.markdown("---")

    # ── PDF download ──────────────────────────────────────────────────────
    st.markdown("### 📄 PDF Report")
    plan_rows = zyklus_laden(sid)
    if st.button("📥 PDF Report generieren"):
        pdf_bytes = generate_report(
            spieler=auswahl,
            fms_row=fms, y_row=y,
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

        df = pd.DataFrame([dict(row) for row in plan])
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

    df = pd.DataFrame([dict(row) for row in plan])
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
            df = pd.DataFrame([dict(row) for row in fms_hist])
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
            fig.update_layout(
                **PLOTLY_LAYOUT, height=340,
                title="FMS Score Verlauf",
                yaxis=dict(range=[0, 22], **PLOTLY_LAYOUT["yaxis"]),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_yb:
        if not yb_hist:
            st.info("Noch keine Y-Balance Tests vorhanden.")
        else:
            df = pd.DataFrame([dict(row) for row in yb_hist])
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
            fig2.update_layout(
                **PLOTLY_LAYOUT, height=340,
                title="Y-Balance Composite Score Verlauf",
                yaxis=dict(range=[70, 115], **PLOTLY_LAYOUT["yaxis"]),
            )
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
            "📝 FMS Test",
            "📏 Y-Balance Test",
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
    "📝 FMS Test":          page_fms,
    "📏 Y-Balance Test":    page_ybalance,
    "📅 Trainingsplan":     page_trainingsplan,
    "🔄 Periodisierung":    page_periodisierung,
    "📈 Fortschritt":       page_fortschritt,
}
pages[page]()
