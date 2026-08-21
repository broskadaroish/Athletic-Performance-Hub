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
/* ── Frühe Hintergrundfarbe: verhindert weißen/hellen Frame auf iOS Safari ── */
/* iOS Safari zeigt den Browser-Default (#fff) bis Streamlit seinen CSS rendert. */
/* color-scheme: dark verhindert, dass Safari Auto-Inversionen oder weiße Frames */
/* zwischen Repaint-Zyklen einblendet.                                           */
html {
    background-color: #0d1117 !important;
    color-scheme: dark;
}
body {
    background-color: #0d1117 !important;
}

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

/* ── Sidebar sub-navigation ──
   Streamlit exposes the container key as `st-key-sidebar_subnav_*`.  This
   scope keeps the compact style limited to the second navigation level. */
[data-testid="stSidebarContent"] [class*="st-key-sidebar_subnav_"] {
    margin: -3px 0 6px;
}
[data-testid="stSidebarContent"] [class*="st-key-sidebar_subnav_"] [data-testid="stElementContainer"] {
    margin: 0 !important;
}
[data-testid="stSidebarContent"] [class*="st-key-sidebar_subnav_"] .stButton > button {
    min-height: 32px !important;
    padding: 5px 10px 5px 28px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    color: #8b949e !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
    line-height: 1.25 !important;
    text-align: left !important;
    box-shadow: none !important;
}
[data-testid="stSidebarContent"] [class*="st-key-sidebar_subnav_"] .stButton > button:hover {
    background: #161b22 !important;
    color: #e6edf3 !important;
    transform: none !important;
}
[data-testid="stSidebarContent"] [class*="st-key-sidebar_subnav_"] .stButton > button[kind="primary"] {
    background: #0d2044 !important;
    border-left: 3px solid #1f6feb !important;
    color: #58a6ff !important;
    font-weight: 650 !important;
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

/* ── Form labels — main content area (all widget types) ── */
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stTextArea"] label,
[data-testid="stDateInput"] label,
[data-testid="stTimeInput"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stToggle"] label,
[data-testid="stSlider"] label,
[data-testid="stFileUploader"] label {
    color: #E6EDF3 !important;
    opacity: 1 !important;
}

/* ── Text / Number / Date / Time inputs — dark bg, light text, iOS fix ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input {
    background: #1F2630 !important;
    background-color: #1F2630 !important;
    color: #F5F7FA !important;
    -webkit-text-fill-color: #F5F7FA !important;
    border: 1px solid #4B5563 !important;
    border-radius: 8px !important;
    opacity: 1 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"] input:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}

/* ── TextArea ── */
[data-testid="stTextArea"] textarea,
[data-baseweb="textarea"] textarea {
    background: #1F2630 !important;
    background-color: #1F2630 !important;
    color: #F5F7FA !important;
    -webkit-text-fill-color: #F5F7FA !important;
    border: 1px solid #4B5563 !important;
    border-radius: 8px !important;
    opacity: 1 !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-baseweb="textarea"] textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}

/* ── Selectbox — BaseWeb custom component (NOT a native <select>) ── */
/* Container + control div */
[data-baseweb="select"],
[data-baseweb="select"] > div {
    background: #1F2630 !important;
    background-color: #1F2630 !important;
    border-color: #4B5563 !important;
}
/* All text inside the select control (value, placeholder) */
[data-baseweb="select"] > div > div,
[data-baseweb="select"] > div > div > div {
    color: #F5F7FA !important;
    -webkit-text-fill-color: #F5F7FA !important;
}
/* Arrow / chevron SVG */
[data-baseweb="select"] svg {
    fill: #8b949e !important;
    color: #8b949e !important;
}
/* Dropdown portal: list container */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="menu"] {
    background: #161b22 !important;
    background-color: #161b22 !important;
    border: 1px solid #4B5563 !important;
    border-radius: 8px !important;
}
/* Dropdown items */
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] [role="option"] {
    background: #161b22 !important;
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    -webkit-text-fill-color: #e6edf3 !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background: #21262d !important;
    background-color: #21262d !important;
}
[data-baseweb="popover"] [aria-selected="true"],
[data-baseweb="menu"] [aria-selected="true"] {
    background: #0d2044 !important;
    background-color: #0d2044 !important;
    color: #58a6ff !important;
    -webkit-text-fill-color: #58a6ff !important;
}

/* ── NumberInput +/- step buttons ── */
[data-testid="stNumberInput"] button {
    background: #21262d !important;
    background-color: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #4B5563 !important;
}
[data-testid="stNumberInput"] button svg {
    fill: #e6edf3 !important;
}

/* ── MultiSelect — BaseWeb input container + tags ── */
[data-testid="stMultiSelect"] [data-baseweb="input"],
[data-testid="stMultiSelect"] [data-baseweb="select"] {
    background: #1F2630 !important;
    background-color: #1F2630 !important;
    border-color: #4B5563 !important;
}
[data-baseweb="tag"] {
    background: #21262d !important;
    background-color: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    -webkit-text-fill-color: #e6edf3 !important;
}

/* ── Placeholder text — targeted per widget, not global ── */
[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stDateInput"] input::placeholder,
[data-testid="stTimeInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder,
[data-baseweb="input"] input::placeholder {
    color: #8F98A6 !important;
    opacity: 1 !important;
}
[data-testid="stTextInput"] input::-webkit-input-placeholder,
[data-testid="stNumberInput"] input::-webkit-input-placeholder,
[data-testid="stDateInput"] input::-webkit-input-placeholder,
[data-testid="stTextArea"] textarea::-webkit-input-placeholder {
    color: #8F98A6 !important;
    -webkit-text-fill-color: #8F98A6 !important;
}

/* ── Checkbox / Radio / Toggle — paragraph text beside them ── */
[data-testid="stCheckbox"] p,
[data-testid="stRadio"] p,
[data-testid="stToggle"] p {
    color: #E6EDF3 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span {
    color: #8b949e !important;
}

/* ── Help text / caption below widgets ── */
[data-testid="stWidgetLabel"] small {
    color: #AAB2BF !important;
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

/* ── Login / Registration Section Headers ── */
.aph-reg-section {
    margin: 12px 0 10px;
    padding: 0 0 6px;
    border-bottom: 1px solid #21262d;
    font-size: 14px;
    font-weight: 700;
    color: #e6edf3;
}

/* ── Package Cards – mobile stack ── */
@media (max-width: 768px) {
    /* Package cards: ensure no overflow */
    .aph-pkg-card { word-break: break-word; }
    /* Footer legal buttons: stack nicely */
    .aph-footer-btns .stButton > button { font-size: 11px; padding: 8px 4px; }
}

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
    /* Sidebar is a slide-in drawer on mobile — Streamlit shows it via its
       built-in hamburger (☰). Do NOT hide it. Only tighten its width. */
    section[data-testid="stSidebar"] {
        width: min(85vw, 320px) !important;
        max-width: min(85vw, 320px) !important;
        min-width: 220px !important;
    }
    /* Streamlit header has no useful content on mobile in v1.60.0 —
       the CollapseButton is inside stSidebarHeader (inside the sidebar itself).
       Hide the header strip to reclaim vertical space. */
    header[data-testid="stHeader"]  { display: none !important; }
    /* Main block: leave room for the fixed 44px floating button */
    .main .block-container {
        padding-top: 64px !important;
        padding-bottom: 16px !important;
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

/* ── Mobile sidebar: touch-friendly nav items inside the drawer ──────────── */
@media (max-width: 768px) {
    /* Nav radio labels: large tap targets (≥44px), full-width */
    [data-testid="stSidebarContent"] [data-testid="stRadio"] label {
        min-height: 44px !important;
        padding: 10px 12px !important;
        font-size: 15px !important;
    }
    /* Sub-nav items slightly smaller but still tap-safe */
    [data-testid="stSidebarContent"] .subnav [data-testid="stRadio"] label {
        min-height: 38px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
    }
    /* Make sidebar scroll independently if content is tall */
    [data-testid="stSidebarContent"] {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    /* Sidebar overlay: ensure it slides in from the left */
    section[data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        height: 100% !important;
        z-index: 10000 !important;
        overflow-y: auto !important;
    }
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

/* ══ Bottom navigation — disabled: sidebar is the drawer on all viewports ══ */
/* render_mobile_nav() is a no-op; inject_mobile_mehr_overlay() is disabled.
   stSegmentedControl is not used for navigation any more.
   If it appears anywhere else on the page, no special CSS needed. */

/* ══ APH Mobile Menu Button (#aph-menu-btn) ══════════════════════════════════
   Injected into parent DOM (doc.body) by inject_mobile_sidebar_opener().
   CSS lives HERE in theme.py so it is re-applied on every Streamlit rerun
   and always beats any older JS-injected style from a previous run.
   The JS in mobile.py only creates the element — no state tracking, no
   .aph-sidebar-open class, no MutationObserver.
   ══════════════════════════════════════════════════════════════════════════ */

/* Desktop ≥769px: never visible */
@media (min-width: 769px) {
    #aph-menu-btn { display: none !important; }
}

/* Mobile ≤768px: ALWAYS fixed top-left, above everything.
   Visible regardless of sidebar open/closed state. */
@media (max-width: 768px) {
    #aph-menu-btn {
        display:          flex !important;
        visibility:       visible !important;
        opacity:          1 !important;
        position:         fixed !important;
        top:              8px !important;
        left:             8px !important;
        z-index:          2147483000 !important;   /* max safe int — nothing covers this */
        width:            44px !important;
        height:           44px !important;
        min-width:        44px !important;
        min-height:       44px !important;
        align-items:      center !important;
        justify-content:  center !important;
        background:       rgba(22, 27, 34, 0.92) !important;
        border:           1px solid #30363d !important;
        border-radius:    10px !important;
        color:            #e6edf3 !important;
        font-size:        22px !important;
        line-height:      1 !important;
        cursor:           pointer !important;
        box-shadow:       0 2px 12px rgba(0, 0, 0, .55) !important;
        -webkit-tap-highlight-color: transparent !important;
        touch-action:     manipulation !important;
        pointer-events:   auto !important;
        overflow:         visible !important;
        transform:        none !important;
    }
    #aph-menu-btn:active {
        background:       rgba(88, 166, 255, 0.22) !important;
        border-color:     #58a6ff !important;
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
    /* "Spieler wechseln" button — hidden on desktop via adjacent-sibling rule below */
    .aph-mob-switch-marker { display: block; margin: 0; padding: 0; height: 0; }
    .aph-mph-switch {
        font-size: 12px; color: #58a6ff;
        white-space: nowrap; flex-shrink: 0; padding: 4px 0;
        /* button reset */
        background: none; border: none; cursor: pointer; font-family: inherit;
    }
    .aph-mph-switch:hover { text-decoration: underline; color: #79bcff; }
}

/* Hide mobile player-switch button on desktop (adjacent sibling of marker div) */
.aph-mob-switch-marker { display: none; }
@media (min-width: 769px) {
    .aph-mob-switch-marker + div { display: none !important; }
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

/* ══ Kundenverwaltung — Kündigungen responsive Karten (Task #199) ═══════════ */
/*
 * Strategy: render each Kündigung twice inside st.container() blocks.
 * A sentinel <div> inside each container lets CSS :has() toggle visibility.
 *   .aph-kuend-desktop-sentinel  → container shown on desktop, hidden on mobile
 *   .aph-kuend-mobile-sentinel   → container shown on mobile, hidden on desktop
 */
@media (max-width: 768px) {
    div[data-testid="stVerticalBlock"]:has(.aph-kuend-desktop-sentinel):not(:has([data-testid="stVerticalBlock"]:has(.aph-kuend-desktop-sentinel))) {
        display: none !important;
    }
}
@media (min-width: 769px) {
    div[data-testid="stVerticalBlock"]:has(.aph-kuend-mobile-sentinel):not(:has([data-testid="stVerticalBlock"]:has(.aph-kuend-mobile-sentinel))) {
        display: none !important;
    }
}

/* Kündigungen card — mobile layout */
.aph-kuend-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.aph-kuend-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 6px;
}
.aph-kuend-card-kn   { color: #e6edf3; font-size: 14px; font-weight: 600; }
.aph-kuend-card-name { color: #c9d1d9; font-size: 14px; }
.aph-kuend-card-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;
    color: #8b949e;
    margin-top: 6px;
}
.aph-kuend-card-meta span { display: block; }
.aph-kuend-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    white-space: nowrap;
}
.aph-kuend-badge-eingegangen { background: #1c2d3f; color: #58a6ff; border: 1px solid #388bfd; }
.aph-kuend-badge-bestaetigt  { background: #0d3b2e; color: #3fb950; border: 1px solid #3fb950; }
.aph-kuend-badge-beendet     { background: #21262d; color: #8b949e; border: 1px solid #30363d; }

/* ══ "Mehr" navigation screen ════════════════════════════════════════════════ */
/* Rendered via native st.button elements — no CSS overlay, no onclick HTML. */

@media (max-width: 768px) {
    .aph-mehr-header {
        display: flex;
        align-items: center;
        padding: 16px 16px 14px;
        border-bottom: 1px solid #21262d;
        background: #0d1117;
        margin-bottom: 8px;
    }
    .aph-mehr-title { font-size: 18px; font-weight: 700; color: #e6edf3; }
}
</style>
"""
