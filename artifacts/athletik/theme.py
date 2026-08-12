"""
Central design system — colors, CSS tokens, and layout constants.
Import APP_CSS and inject via st.markdown(APP_CSS, unsafe_allow_html=True).
"""

# ─── Color tokens ─────────────────────────────────────────────────────────────
C = {
    "bg":         "#0d1117",
    "surface":    "#161b22",
    "surface2":   "#21262d",
    "border":     "#30363d",
    "text":       "#e6edf3",
    "muted":      "#8b949e",
    "green":      "#3fb950",
    "green_bg":   "#0d3b2e",
    "yellow":     "#d29922",
    "yellow_bg":  "#3b2a0d",
    "red":        "#f85149",
    "red_bg":     "#3b0d0d",
    "blue":       "#58a6ff",
    "blue_dark":  "#1f6feb",
    "blue_bg":    "#0d2044",
}

# ─── Plotly base layout (shared across all charts) ────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["bg"],
    font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
    xaxis=dict(gridcolor=C["surface2"], linecolor=C["border"], zerolinecolor=C["border"]),
    yaxis=dict(gridcolor=C["surface2"], linecolor=C["border"], zerolinecolor=C["border"]),
    margin=dict(l=40, r=20, t=40, b=40),
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
APP_CSS = """
<style>
/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
.stApp { background-color: #0d1117; color: #e6edf3; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
    min-width: 240px !important;
    max-width: 260px !important;
}

/* ── Nav radio — style as menu items ── */
[data-testid="stSidebarContent"] [data-testid="stRadio"] > div {
    gap: 1px !important;
}
[data-testid="stSidebarContent"] [data-testid="stRadio"] label {
    border-radius: 8px;
    padding: 9px 12px !important;
    color: #8b949e !important;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
}
[data-testid="stSidebarContent"] [data-testid="stRadio"] label:hover {
    background: #161b22 !important;
    color: #e6edf3 !important;
}
[data-testid="stSidebarContent"] [data-testid="stRadio"] label[data-baseweb="radio"] p {
    color: inherit !important;
}
/* Hide the radio circle, show full-width label */
[data-testid="stSidebarContent"] [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
    display: none !important;
}
[data-testid="stSidebarContent"] [data-testid="stRadio"] label[aria-checked="true"] {
    background: #161b22 !important;
    color: #58a6ff !important;
    border-left: 3px solid #1f6feb;
    padding-left: 9px !important;
}

/* Sub-nav (second level radio) */
.subnav [data-testid="stRadio"] label {
    font-size: 13px !important;
    padding: 7px 10px 7px 28px !important;
}
.subnav [data-testid="stRadio"] label[aria-checked="true"] {
    color: #58a6ff !important;
    background: #0d2044 !important;
    border-left: 2px solid #1f6feb;
    padding-left: 26px !important;
}

/* ── Headers ── */
h1, h2, h3, h4 { color: #ffffff !important; }
h1 { font-size: 28px !important; font-weight: 700 !important; }
h2 { font-size: 20px !important; }
h3 { font-size: 16px !important; font-weight: 600 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 18px;
}
[data-testid="stMetricLabel"]  { color: #8b949e !important; font-size: 12px !important; letter-spacing: 0.5px; }
[data-testid="stMetricValue"]  { color: #e6edf3 !important; font-size: 26px !important; font-weight: 700 !important; }

/* ── Cards ── */
.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
}
.card-sm {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.card-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8b949e;
    margin-bottom: 6px;
}
.card-value { font-size: 28px; font-weight: 700; color: #e6edf3; }

/* ── KPI card (home page) ── */
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}
.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 34px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}
.kpi-sub { font-size: 12px; color: #8b949e; }

/* ── Badges ── */
.score-badge {
    display: inline-block;
    padding: 5px 16px;
    border-radius: 50px;
    font-weight: 700;
    font-size: 18px;
    letter-spacing: 0.5px;
}
.badge-green  { background: #0d3b2e; color: #3fb950; border: 1px solid #3fb950; }
.badge-yellow { background: #3b2a0d; color: #d29922; border: 1px solid #d29922; }
.badge-red    { background: #3b0d0d; color: #f85149; border: 1px solid #f85149; }
.badge-blue   { background: #0d2044; color: #58a6ff; border: 1px solid #58a6ff; }

/* ── Deficit/strength tags ── */
.tag-crit {
    display: inline-block;
    background: #3b0d0d; color: #f85149;
    border: 1px solid #f85149;
    border-radius: 6px;
    padding: 3px 10px; font-size: 12px; font-weight: 600; margin: 3px;
}
.tag-warn {
    display: inline-block;
    background: #3b2a0d; color: #d29922;
    border: 1px solid #d29922;
    border-radius: 6px;
    padding: 3px 10px; font-size: 12px; font-weight: 600; margin: 3px;
}
.tag-ok {
    display: inline-block;
    background: #0d3b2e; color: #3fb950;
    border: 1px solid #3fb950;
    border-radius: 6px;
    padding: 3px 10px; font-size: 12px; font-weight: 600; margin: 3px;
}

/* ── Progress bar ── */
.prog-wrap { background: #21262d; border-radius: 6px; height: 8px; margin: 4px 0 10px; }
.prog-fill  { height: 8px; border-radius: 6px; }

/* ── Inputs / selects ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stTextArea"] textarea {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.4px;
    padding: 10px 22px;
    transition: all .2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff);
    transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #30363d !important;
    transform: translateY(-1px);
}

/* ── Tables ── */
.dataframe { background: #161b22 !important; color: #e6edf3 !important; }
thead tr th { background: #21262d !important; color: #8b949e !important; font-size: 12px !important; }
tbody tr:nth-child(even) { background: #0d1117 !important; }

/* ── Tabs ── */
[data-testid="stTab"] { color: #8b949e; font-size: 13px; }
button[aria-selected="true"] { color: #58a6ff !important; border-color: #58a6ff !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
}

/* ── Divider ── */
hr { border-color: #30363d; margin: 16px 0; }

/* ── Info/warning/success boxes ── */
[data-testid="stInfo"]    { background: #0d2044; border-left-color: #1f6feb; }
[data-testid="stWarning"] { background: #3b2a0d; border-left-color: #d29922; }
[data-testid="stSuccess"] { background: #0d3b2e; border-left-color: #3fb950; }
[data-testid="stError"]   { background: #3b0d0d; border-left-color: #f85149; }

/* ── Sidebar label ── */
[data-testid="stSidebarContent"] label { color: #c9d1d9 !important; }

/* ── Player pill in sidebar ── */
.player-pill {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 10px 0;
}
.player-pill-name {
    font-size: 15px;
    font-weight: 700;
    color: #e6edf3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.player-pill-sub {
    font-size: 11px;
    color: #8b949e;
    margin-top: 2px;
}

/* ══════════════════════════════════════════════════════════════════════════════
   RESPONSIVE / MOBILE — SCHRITT 7
   Breakpoints: mobile ≤768px · tablet 769–1024px · desktop ≥1025px
   ══════════════════════════════════════════════════════════════════════════════ */

/* Prevent horizontal overflow globally */
html, body { overflow-x: hidden; max-width: 100vw; }

/* ── Mobile: ≤768px ────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    /* Hide Streamlit sidebar completely */
    section[data-testid="stSidebar"]          { display: none !important; }
    [data-testid="stSidebarCollapsedControl"]  { display: none !important; }
    button[data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    /* Remove default Streamlit top padding/header space */
    header[data-testid="stHeader"]             { display: none !important; }
    /* Main block: full width, side padding, bottom room for nav bar */
    .main .block-container {
        padding-top: 12px !important;
        padding-bottom: 80px !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
        max-width: 100% !important;
    }
    /* Compact headings */
    h1 { font-size: 20px !important; margin-bottom: 4px !important; line-height: 1.25 !important; }
    h2 { font-size: 17px !important; }
    h3 { font-size: 14px !important; }
    /* Improved contrast for secondary/muted text (readable outdoors) */
    .stMarkdown p             { color: #c9d1d9 !important; }
    [data-testid="stCaptionContainer"] { color: #c9d1d9 !important; }
    /* Smaller metric values to fit narrow screens */
    [data-testid="stMetricValue"] { font-size: 22px !important; }
    /* Buttons: large touch target, full width by default */
    .stButton > button {
        min-height: 44px !important;
        font-size: 14px !important;
    }
    /* Prevent tables / iframes from causing horizontal scroll */
    .stDataFrame, .stTable, iframe { max-width: 100% !important; overflow-x: auto !important; }
    /* Tighter card padding on mobile */
    .card     { padding: 12px 14px !important; }
    .card-sm  { padding: 10px 12px !important; }
    .kpi-card { padding: 14px !important; }
    /* Columns: allow wrapping on very narrow screens */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    /* Streamlit anchor link icons in headings — hide on mobile */
    h1 a[href^="#"], h2 a[href^="#"], h3 a[href^="#"] { display: none !important; }
}

/* ── Tablet: 769–1024px ────────────────────────────────────────────────────── */
@media (min-width: 769px) and (max-width: 1024px) {
    section[data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 220px !important;
    }
    .main .block-container {
        padding-left: 16px !important;
        padding-right: 16px !important;
    }
}

/* ══ Bottom navigation bar ═══════════════════════════════════════════════════ */
.aph-bottom-nav { display: none; }

@media (max-width: 768px) {
    .aph-bottom-nav {
        display: flex;
        position: fixed;
        bottom: 0; left: 0; right: 0;
        z-index: 9999;
        background: #0d1117;
        border-top: 1px solid #21262d;
        height: 62px;
        align-items: stretch;
        justify-content: space-around;
        box-shadow: 0 -2px 16px rgba(0,0,0,0.65);
        padding-bottom: env(safe-area-inset-bottom, 0px);
    }
    .aph-bn-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        flex: 1;
        /* button reset */
        background: none;
        border: none;
        cursor: pointer;
        font-family: inherit;
        /* visual */
        color: #8b949e;
        padding: 6px 4px;
        min-width: 0;
        -webkit-tap-highlight-color: transparent;
        transition: color 0.12s;
        user-select: none;
    }
    .aph-bn-item.aph-bn-active { color: #58a6ff; }
    .aph-bn-item:active         { opacity: 0.7; }
    .aph-bn-icon  { font-size: 20px; line-height: 1.2; display: block; }
    .aph-bn-label {
        font-size: 10px;
        font-weight: 600;
        margin-top: 2px;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    /* Ensure bottom content is not hidden behind the fixed nav */
    .main .block-container {
        padding-bottom: 80px !important;
    }
}

/* ══ Mobile active-player header pill ════════════════════════════════════════ */
.aph-mph { display: none; }

@media (max-width: 768px) {
    .aph-mph {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 14px;
    }
    .aph-mph-icon { font-size: 22px; flex-shrink: 0; }
    .aph-mph-info { flex: 1; min-width: 0; }
    .aph-mph-name {
        font-size: 14px; font-weight: 700; color: #e6edf3;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .aph-mph-sub  { font-size: 11px; color: #c9d1d9; margin-top: 1px; }
    .aph-mph-switch {
        font-size: 12px; color: #58a6ff;
        white-space: nowrap; flex-shrink: 0; padding: 4px 0;
        /* button reset */
        background: none; border: none; cursor: pointer; font-family: inherit;
    }
    .aph-mph-switch:hover { text-decoration: underline; color: #79bcff; }
}

/* ══ Mobile inline player selector ══════════════════════════════════════════ */
.aph-mob-sel-wrap { display: none; }

@media (max-width: 768px) {
    .aph-mob-sel-wrap {
        display: block;
        margin-bottom: 14px;
    }
    .aph-mob-sel-label {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .8px;
        color: #8b949e;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .aph-mob-sel {
        width: 100%;
        background: #161b22;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px 36px 12px 14px;
        font-size: 15px;
        font-weight: 500;
        -webkit-appearance: none;
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238b949e' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 14px center;
        cursor: pointer;
        min-height: 48px;
    }
    .aph-mob-sel:focus {
        outline: none;
        border-color: #58a6ff;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.15);
    }
    .aph-mob-sel option {
        background: #161b22;
        color: #e6edf3;
    }
}

/* ══ Kundenverwaltung — responsive Kundenkarten (Spec §22) ══════════════════ */
.aph-kunden-karte {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 6px;
    text-decoration: none !important;
    color: inherit;
    transition: border-color .15s;
    cursor: pointer;
}
.aph-kunden-karte:hover { border-color: #58a6ff; text-decoration: none !important; }
.aph-kunden-info  { flex: 1; min-width: 0; }
.aph-kc-header    { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 3px; }
.aph-kc-kn        { color: #e6edf3; font-size: 14px; }
.aph-kc-vname     { color: #e6edf3; font-size: 13px; }
.aph-kc-sub       { color: #8b949e; font-size: 11px; margin-bottom: 5px;
                     white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.aph-kc-meta      { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 4px; }
.aph-kc-chip      { background: #21262d; color: #8b949e; font-size: 11px;
                     padding: 2px 7px; border-radius: 10px; white-space: nowrap; }
.aph-kc-chip-active    { background: #0d3b2e; color: #3fb950; }
.aph-kc-chip-expired   { background: #3b1c1c; color: #f85149; }
.aph-kc-chip-suspended { background: #3b2d0d; color: #d29922; }
.aph-kc-chip-cancelled { background: #2d0d0d; color: #f85149; }
.aph-kunden-btn-wrap { flex-shrink: 0; }
.aph-kunden-btn {
    display: inline-block;
    background: #21262d;
    color: #e6edf3 !important;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    white-space: nowrap;
    text-decoration: none !important;
}
.aph-kunden-karte:hover .aph-kunden-btn { background: #30363d; border-color: #58a6ff; }

@media (max-width: 768px) {
    .aph-kunden-karte {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .aph-kc-sub { white-space: normal; }
    .aph-kunden-btn {
        display: block;
        text-align: center;
        padding: 11px;
        font-size: 15px;
        border-radius: 8px;
        background: #1f6feb;
        border-color: #1f6feb;
        color: #ffffff !important;
        font-weight: 600;
        min-height: 44px;
        line-height: 1.5;
    }
    .aph-kunden-karte:hover .aph-kunden-btn { background: #388bfd; border-color: #388bfd; }
}

/* ══ "Mehr" overlay ══════════════════════════════════════════════════════════ */
.aph-mehr-overlay { display: none; }

@media (max-width: 768px) {
    .aph-mehr-overlay {
        display: block;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 9998;
        background: #0d1117;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 70px;
    }
    .aph-mehr-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 16px 14px;
        border-bottom: 1px solid #21262d;
        position: sticky;
        top: 0;
        background: #0d1117;
        z-index: 1;
    }
    .aph-mehr-title    { font-size: 18px; font-weight: 700; color: #e6edf3; }
    .aph-mehr-close    {
        font-size: 22px; color: #8b949e; padding: 6px 2px; line-height: 1;
        /* button reset */
        background: none; border: none; cursor: pointer; font-family: inherit;
    }
    .aph-mehr-close:hover { color: #e6edf3; }
    .aph-mehr-section-label {
        font-size: 11px; font-weight: 700; letter-spacing: 1px;
        color: #8b949e; padding: 14px 16px 6px; text-transform: uppercase;
    }
    .aph-mehr-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px 16px;
        border-bottom: 1px solid #161b22;
        color: #e6edf3;
        font-size: 15px;
        -webkit-tap-highlight-color: transparent;
        width: 100%;
        /* button reset */
        background: none; border: none; cursor: pointer;
        font-family: inherit; text-align: left;
    }
    .aph-mehr-item:hover        { background: #161b22; }
    .aph-mehr-item:active       { opacity: 0.7; }
    .aph-mehr-item-text         { color: #e6edf3; }
    .aph-mehr-item-arrow        { color: #8b949e; font-size: 18px; flex-shrink: 0; }
    .aph-mehr-divider           { height: 1px; background: #21262d; margin: 8px 0; }
    .aph-mehr-logout .aph-mehr-item-text  { color: #f85149; }
    .aph-mehr-logout .aph-mehr-item-arrow { color: #f85149; }
}
</style>
"""
