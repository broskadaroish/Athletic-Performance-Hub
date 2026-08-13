"""Rollenbasiertes SaaS-Dashboard — Superadmin / Vereinsadmin / Trainer."""

import datetime
import plotly.graph_objects as go
import streamlit as st

from analytics import athletik_score, risiko_score, risiko_label
from database import (
    dashboard_sa_kpis, dashboard_va_kpis,
    dashboard_monatlich_vereine, dashboard_monatlich_trainer,
    dashboard_monatlich_diagnostiken,
    dashboard_spieler_altersklassen, dashboard_spieler_mannschaften,
    dashboard_letzte_logins, dashboard_verein_uebersicht,
    dashboard_trainer_letzte_spieler, dashboard_trainer_ohne_test,
    dashboard_trainer_neue_verletzungen, dashboard_trainer_diagnostiken_monat,
    spieler_laden, verein_by_id, spieler_ohne_verein_zaehlen,
    fms_letzter, y_balance_letzter, sprint_letzter, sprung_letzter,
    agilitaet_letzter, ausdauer_letzter, spiro_test_letzter, verletzungen_laden,
)

# ── Design-Konstanten (Dark Mode) ─────────────────────────────────────────────
_C = {
    "bg":      "rgba(0,0,0,0)",
    "grid":    "#21262d",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
    "surf":    "#161b22",
    "border":  "#30363d",
    "blue":    "#58a6ff",
    "green":   "#3fb950",
    "orange":  "#d29922",
    "red":     "#f85149",
    "purple":  "#bc8cff",
    "teal":    "#39d353",
}
_PALETTE = ["#58a6ff","#3fb950","#d29922","#f85149","#bc8cff","#ffa657","#39d353","#ff7b72"]
_DE_MON  = ["Jan","Feb","Mrz","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
_DE_TAG  = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
_DE_MFULL = ["Januar","Februar","März","April","Mai","Juni",
             "Juli","August","September","Oktober","November","Dezember"]


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _gruss(vorname: str = "") -> str:
    h = datetime.datetime.now().hour
    g = "Guten Morgen" if h < 12 else "Guten Tag" if h < 18 else "Guten Abend"
    return f"{g}{', ' + vorname if vorname else ''}!"


def _datum_de() -> str:
    d = datetime.date.today()
    return f"{_DE_TAG[d.weekday()]}, {d.day}. {_DE_MFULL[d.month-1]} {d.year}"


def _last_n_months(n: int = 12) -> list[str]:
    today = datetime.date.today()
    result = []
    for i in range(n - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        result.append(f"{y:04d}-{m:02d}")
    return result


def _fill_months(rows: list, n: int = 12) -> tuple[list, list]:
    keys   = _last_n_months(n)
    lookup = {r["monat"]: r["n"] for r in rows}
    values = [lookup.get(k, 0) for k in keys]
    labels = [_DE_MON[int(k[5:7]) - 1] + " '" + k[2:4] for k in keys]
    return labels, values


def _plotly_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=_C["bg"], plot_bgcolor=_C["bg"],
        font=dict(color=_C["text"], family="Inter, sans-serif", size=11),
        margin=dict(l=4, r=4, t=36, b=4),
        xaxis=dict(gridcolor=_C["grid"], showgrid=True, zeroline=False,
                   tickfont=dict(color=_C["muted"], size=10)),
        yaxis=dict(gridcolor=_C["grid"], showgrid=True, zeroline=False,
                   tickfont=dict(color=_C["muted"], size=10)),
        showlegend=False,
    )
    base.update(kw)
    return base


def _kpi(label: str, value, icon: str = "", color: str = "#58a6ff",
         sub: str = "", delta: str = "", warn: bool = False) -> str:
    c = _C["red"] if warn and (isinstance(value, int) and value > 0) else color
    dh = (f'<div style="font-size:10px;margin-top:3px;color:{_C["green"]}">{delta}</div>'
          if delta else "")
    sh = (f'<div style="font-size:10px;color:{_C["muted"]};margin-top:2px">{sub}</div>'
          if sub else "")
    return (
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:10px;padding:16px 18px;height:100%">'
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;margin-bottom:8px">'
        f'{icon}&nbsp;&nbsp;{label.upper()}</div>'
        f'<div style="font-size:30px;font-weight:800;color:{c};line-height:1">{value}</div>'
        f'{dh}{sh}</div>'
    )


def _kpi_row(items: list[tuple]) -> None:
    """items = [(label, value, icon, color, sub, delta, warn)]"""
    cols = st.columns(len(items))
    for col, args in zip(cols, items):
        with col:
            st.markdown(_kpi(*args), unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)


def _bar(labels, values, title: str, color: str = "#58a6ff",
         horizontal: bool = False) -> go.Figure:
    orientation = "h" if horizontal else "v"
    x, y = (values, labels) if horizontal else (labels, values)
    fig = go.Figure(go.Bar(
        x=x, y=y,
        orientation=orientation,
        marker=dict(
            color=color,
            line=dict(width=0),
        ),
        text=values,
        textposition="outside",
        textfont=dict(color=_C["muted"], size=10),
        hovertemplate="%{y}: %{x}<extra></extra>" if horizontal
                      else "%{x}: %{y}<extra></extra>",
    ))
    layout = _plotly_layout()
    layout["title"] = dict(text=title, font=dict(size=12, color=_C["muted"]),
                           x=0, pad=dict(l=4))
    if horizontal:
        layout.pop("xaxis", None)
        layout.pop("yaxis", None)
        layout["xaxis"] = dict(gridcolor=_C["grid"], showgrid=True, zeroline=False,
                                tickfont=dict(color=_C["muted"], size=10))
        layout["yaxis"] = dict(gridcolor=_C["grid"], showgrid=False, zeroline=False,
                                tickfont=dict(color=_C["muted"], size=10))
    fig.update_layout(**layout)
    return fig


def _line(labels, values, title: str, color: str = "#58a6ff") -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=labels, y=values,
        mode="lines+markers",
        line=dict(color=color, width=2, shape="spline"),
        marker=dict(color=color, size=5),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.09)",
        hovertemplate="%{x}: %{y}<extra></extra>",
    ))
    layout = _plotly_layout()
    layout["title"] = dict(text=title, font=dict(size=12, color=_C["muted"]),
                           x=0, pad=dict(l=4))
    fig.update_layout(**layout)
    return fig


def _donut(labels, values, title: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=_PALETTE, line=dict(color=_C["surf"], width=2)),
        textinfo="percent",
        hovertemplate="%{label}: %{value}<extra></extra>",
        showlegend=True,
    ))
    layout = _plotly_layout()
    layout["title"] = dict(text=title, font=dict(size=12, color=_C["muted"]),
                           x=0, pad=dict(l=4))
    layout["legend"] = dict(font=dict(color=_C["muted"], size=10),
                             bgcolor="rgba(0,0,0,0)", x=1, y=0.5)
    layout.pop("xaxis", None)
    layout.pop("yaxis", None)
    fig.update_layout(**layout)
    return fig


def _aktivitaeten(logins: list, title: str = "🕐 Letzte Aktivitäten") -> None:
    st.markdown(
        f'<div style="font-size:12px;font-weight:700;color:{_C["muted"]};'
        f'letter-spacing:.5px;margin:4px 0 10px">{title.upper()}</div>',
        unsafe_allow_html=True,
    )
    if not logins:
        st.caption("Noch keine Anmeldungen erfasst.")
        return
    _ROLLE_C = {"Superadmin": _C["orange"], "Vereinsadmin": _C["blue"],
                "Trainer": _C["green"]}
    for l in logins:
        name  = f"{l.get('vorname','')} {l.get('nachname','')}".strip() or l.get("email","?")
        rolle = l.get("rolle", "—")
        rc    = _ROLLE_C.get(rolle, _C["muted"])
        login = l.get("letzter_login", "—")
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:6px 12px;border-radius:6px;margin-bottom:3px;'
            f'background:{_C["surf"]};border:1px solid {_C["border"]}">'
            f'<span style="font-size:12px;color:{_C["text"]}">{name}</span>'
            f'<span style="display:flex;gap:10px;align-items:center">'
            f'<span style="font-size:10px;color:{rc}">{rolle}</span>'
            f'<span style="font-size:10px;color:{_C["muted"]}">{login}</span>'
            f'</span></div>',
            unsafe_allow_html=True,
        )


def _navigate(section: str) -> None:
    # Use deferred navigation: _nav_goto is translated to nav_section BEFORE
    # the sidebar radio widget is instantiated on the next rerun, avoiding
    # StreamlitAPIException from mutating a widget-backed key mid-run.
    st.session_state["_nav_goto"] = section
    st.rerun()


# ── Vereinsvergleich-Tabelle (Superadmin) ─────────────────────────────────────

def _tage_bis(lizenz_bis_str) -> int | None:
    """Gibt die Anzahl der verbleibenden Tage bis Lizenzablauf zurück (negativ = abgelaufen)."""
    if not lizenz_bis_str:
        return None
    try:
        import datetime as _dt
        bis = _dt.date.fromisoformat(str(lizenz_bis_str))
        return (bis - _dt.date.today()).days
    except Exception:
        return None


def _letzte_aktivitaet_text(ts: str | None) -> str:
    """Wandelt einen ISO-Zeitstempel in einen lesbaren Relativtext um."""
    if not ts:
        return "—"
    try:
        import datetime as _dt
        dt = _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        dt = dt.replace(tzinfo=None)
        delta = _dt.datetime.now() - dt
        days  = delta.days
        if days == 0:
            h = delta.seconds // 3600
            return f"heute, vor {h} Std." if h > 0 else "gerade eben"
        if days == 1:
            return "gestern"
        if days < 7:
            return f"vor {days} Tagen"
        if days < 30:
            return f"vor {days // 7} Woche(n)"
        if days < 365:
            return f"vor {days // 30} Monat(en)"
        return f"vor {days // 365} Jahr(en)"
    except Exception:
        return str(ts)[:10]


def _vereins_vergleich_tabelle() -> None:
    """Sortierbare Vereinsvergleich-Tabelle für den Superadmin."""
    st.markdown(
        f'<div style="font-size:12px;font-weight:700;color:{_C["muted"]};'
        f'letter-spacing:.5px;margin:4px 0 12px">🏢 VEREINSÜBERSICHT — VERGLEICH</div>',
        unsafe_allow_html=True,
    )

    vereine = dashboard_verein_uebersicht()
    if not vereine:
        st.info("Noch keine Vereine angelegt.")
        return

    # ── Sortiersteuerung ──────────────────────────────────────────────────────
    _SORT_OPTS = {
        "Name (A–Z)":          ("name",            False),
        "Diagnostiken ↓":      ("n_diagnostiken",  True),
        "Spieler ↓":           ("n_spieler",       True),
        "Trainer ↓":           ("n_trainer",       True),
        "Letzte Aktivität ↓":  ("letzte_aktivitaet", True),
        "Status":              ("_status_sort",    False),
    }
    sc1, sc2 = st.columns([2, 5])
    with sc1:
        sort_key = st.selectbox(
            "Sortieren nach",
            list(_SORT_OPTS.keys()),
            key="sa_vereinstab_sort",
            label_visibility="collapsed",
        )

    sort_field, sort_desc = _SORT_OPTS[sort_key]

    # Status-Hilfssortierung berechnen (0=aktiv, 1=ablaufend, 2=inaktiv/gesperrt)
    def _status_sort_val(v):
        if v.get("gesperrt") or not v.get("aktiv", 1):
            return 2
        tage = _tage_bis(v.get("lizenz_bis"))
        if tage is not None and tage < 0:
            return 2
        if tage is not None and tage <= 30:
            return 1
        return 0

    for v in vereine:
        v["_status_sort"] = _status_sort_val(v)

    # Sort with nulls always last, regardless of direction
    def _sort_val(v):
        val = v.get(sort_field)
        if isinstance(val, (int, float)):
            return val
        return str(val) if val is not None else None

    vereine_nonnull = [v for v in vereine if v.get(sort_field) is not None]
    vereine_null    = [v for v in vereine if v.get(sort_field) is None]
    vereine_nonnull.sort(key=_sort_val, reverse=sort_desc)
    vereine = vereine_nonnull + vereine_null

    # ── Tabellenkopf ─────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:grid;grid-template-columns:2fr 1fr 0.6fr 0.6fr 0.8fr 1.2fr 0.8fr 0.7fr;'
        f'gap:4px;padding:6px 12px;border-radius:6px;margin-bottom:2px;'
        f'background:{_C["surf"]};border:1px solid {_C["border"]}">'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px">VEREIN</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px">LIZENZ</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px;text-align:right">TRAINER</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px;text-align:right">SPIELER</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px;text-align:right">DIAGN.</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px">LETZTE AKTIVITÄT</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px">STATUS</span>'
        f'<span style="font-size:10px;font-weight:700;color:{_C["muted"]};letter-spacing:.5px"></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Zeilen ────────────────────────────────────────────────────────────────
    _LIZ_C = {
        # Neue 4-Paket-Keys
        "TRAINER_BASIC": _C["muted"],
        "TRAINER_PRO":   _C["green"],
        "VEREIN_BASIC":  _C["blue"],
        "VEREIN_PRO":    _C["orange"],
        # Legacy-Werte (Altdaten — Abwärtskompatibilität)
        "Enterprise":    _C["orange"],
        "Premium":       _C["blue"],
        "Standard":      _C["green"],
        "Basis":         _C["muted"],
        "Test (30 Tage)":_C["red"],
        "FREE":          _C["muted"],
    }

    for v in vereine:
        vid   = v["id"]
        name  = v.get("name") or f"Verein {vid}"
        lt    = v.get("lizenztyp") or "Basis"
        liz_c = _LIZ_C.get(lt, _C["muted"])

        # Status ermitteln
        gesperrt = v.get("gesperrt") or not v.get("aktiv", 1)
        tage     = _tage_bis(v.get("lizenz_bis"))
        if gesperrt or (tage is not None and tage < 0):
            row_status     = "Inaktiv"
            status_color   = _C["red"]
            row_bg         = f"{_C['red']}0d"
            row_border     = f"{_C['red']}44"
        elif tage is not None and tage <= 30:
            row_status     = f"Läuft ab ({tage}d)"
            status_color   = _C["orange"]
            row_bg         = f"{_C['orange']}0d"
            row_border     = f"{_C['orange']}44"
        else:
            row_status     = "Aktiv"
            status_color   = _C["green"]
            row_bg         = "rgba(0,0,0,0)"
            row_border     = _C["border"]

        akt_text = _letzte_aktivitaet_text(v.get("letzte_aktivitaet"))

        st.markdown(
            f'<div style="display:grid;grid-template-columns:2fr 1fr 0.6fr 0.6fr 0.8fr 1.2fr 0.8fr 0.7fr;'
            f'gap:4px;padding:8px 12px;border-radius:6px;margin-bottom:3px;'
            f'background:{row_bg};border:1px solid {row_border};align-items:center">'
            # Vereinsname
            f'<span style="font-size:13px;font-weight:600;color:{_C["text"]}">{name}</span>'
            # Lizenz-Badge
            f'<span><span style="background:{liz_c}22;color:{liz_c};font-size:10px;font-weight:700;'
            f'padding:2px 8px;border-radius:8px;border:1px solid {liz_c}44">{lt}</span></span>'
            # Trainer
            f'<span style="font-size:13px;color:{_C["text"]};text-align:right">{v["n_trainer"]}</span>'
            # Spieler
            f'<span style="font-size:13px;color:{_C["text"]};text-align:right">{v["n_spieler"]}</span>'
            # Diagnostiken
            f'<span style="font-size:13px;color:{_C["text"]};text-align:right">{v["n_diagnostiken"]}</span>'
            # Letzte Aktivität
            f'<span style="font-size:11px;color:{_C["muted"]}">{akt_text}</span>'
            # Status-Chip
            f'<span><span style="background:{status_color}22;color:{status_color};font-size:10px;'
            f'font-weight:700;padding:2px 8px;border-radius:8px;border:1px solid {status_color}44">'
            f'{row_status}</span></span>'
            # Platzhalter für Button-Spalte (Button wird danach gerendert)
            f'<span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Button zum Öffnen der Vereinsverwaltung
        if st.button("→ Details", key=f"sa_vdetail_{vid}", help=f"{name} in der Vereinsverwaltung öffnen"):
            st.session_state["sa_goto_verein_id"] = vid
            _navigate("🏢  Vereinsverwaltung")


# ── Hauptrouter ───────────────────────────────────────────────────────────────

def page_saas_dashboard():
    user  = st.session_state.get("user", {})
    rolle = user.get("rolle", "Trainer")
    if rolle == "Superadmin":
        _dash_superadmin(user)
    elif rolle == "Vereinsadmin":
        _dash_vereinsadmin(user)
    else:
        _dash_trainer(user)


# ── Superadmin ────────────────────────────────────────────────────────────────

def _dash_superadmin(user: dict):
    vorname = user.get("vorname") or ""
    st.markdown(
        f'<div style="margin-bottom:4px">'
        f'<h2 style="color:{_C["text"]};margin:0">{_gruss(vorname)}</h2>'
        f'<p style="color:{_C["muted"]};margin:2px 0 0;font-size:13px">'
        f'{_datum_de()} &nbsp;·&nbsp; Superadmin-Übersicht</p></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Banner: Spieler ohne Vereinszuweisung ─────────────────────────────────
    _n_ohne_verein = spieler_ohne_verein_zaehlen()
    if _n_ohne_verein > 0:
        _spieler_wort = "Spieler" if _n_ohne_verein == 1 else "Spieler"
        _text = (
            f"{'1 Spieler ist' if _n_ohne_verein == 1 else f'{_n_ohne_verein} Spieler sind'} "
            f"noch keinem Verein zugewiesen."
        )
        st.markdown(
            f'<div style="background:#856404;border:1px solid #ffc107;border-radius:8px;'
            f'padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:20px">⚠️</span>'
            f'<div style="flex:1">'
            f'<span style="color:#fff5d6;font-weight:600">{_text}</span>'
            f'<span style="color:#ffeaa7;font-size:13px;margin-left:8px">'
            f'→ Benutzerverwaltung öffnen und Verein zuweisen.</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔗 Zur Benutzerverwaltung — Spieler zuweisen",
                     key="btn_spieler_ohne_verein",
                     type="secondary"):
            st.session_state["_nav_goto"] = "🔑  Benutzerverwaltung"
            st.rerun()

    kpis = dashboard_sa_kpis()

    # ── KPI-Reihe 1 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Vereine",          kpis["n_vereine"],     "🏢", _C["blue"],  f"{kpis['n_aktiv']} aktiv"),
        ("Gesperrte Vereine",kpis["n_gesperrt"],    "🚫", _C["red"],   "", "", True),
        ("Vereinsadmins",    kpis["n_vadmin"],      "👔", _C["orange"],""),
        ("Aktive Benutzer",  kpis["n_benutzer"],    "✅", _C["green"], ""),
    ])
    # ── KPI-Reihe 2 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Trainer",          kpis["n_trainer"],     "🧑‍💼", _C["purple"],""),
        ("Spieler gesamt",   kpis["n_spieler"],     "⚽", _C["blue"],  ""),
        ("Diagnostiken",     kpis["n_diagnostiken"],"🔬", _C["teal"],  "alle Tests"),
        ("Aktive Abos",      kpis["n_aktiv"],       "💳", _C["green"], "Vereine"),
    ])

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        lbl, val = _fill_months(dashboard_monatlich_vereine())
        st.plotly_chart(_bar(lbl, val, "Neue Vereine pro Monat", _C["blue"]),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        lbl, val = _fill_months(dashboard_monatlich_trainer())
        st.plotly_chart(_bar(lbl, val, "Neue Trainer pro Monat", _C["green"]),
                        use_container_width=True, config={"displayModeBar": False})

    c3, c4 = st.columns(2)
    with c3:
        lbl, val = _fill_months(dashboard_monatlich_diagnostiken())
        st.plotly_chart(_line(lbl, val, "Durchgeführte Diagnostiken pro Monat", _C["purple"]),
                        use_container_width=True, config={"displayModeBar": False})
    with c4:
        ak = dashboard_spieler_altersklassen()
        if ak:
            ak_lab = [r["altersklasse"] for r in ak[:10]]
            ak_val = [r["n"]            for r in ak[:10]]
            st.plotly_chart(_bar(ak_lab, ak_val, "Spieler nach Altersklasse", _C["orange"],
                                 horizontal=True),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Noch keine Spieler angelegt.")

    st.divider()

    # ── Vereinsvergleich ──────────────────────────────────────────────────────
    _vereins_vergleich_tabelle()

    st.divider()

    # ── Letzte Aktivitäten ────────────────────────────────────────────────────
    _aktivitaeten(dashboard_letzte_logins(limit=10))


# ── Vereinsadmin ──────────────────────────────────────────────────────────────

def _dash_vereinsadmin(user: dict):
    verein_id = user.get("verein_id")
    verein    = verein_by_id(verein_id) if verein_id else {}
    vname     = (verein or {}).get("name", user.get("verein_name", "Dein Verein"))
    primaer   = (verein or {}).get("farbe_primaer") or _C["blue"]
    lizenz    = (verein or {}).get("lizenztyp") or "Basis"
    liz_bis   = (verein or {}).get("lizenz_bis") or ""
    logo_blob = (verein or {}).get("logo_blob")

    # ── Vereins-Header ────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([1, 7])
    with hc1:
        if logo_blob:
            try:
                st.image(bytes(logo_blob), width=72)
            except Exception:
                st.markdown(
                    f'<div style="width:72px;height:72px;border-radius:10px;'
                    f'background:{primaer}22;display:flex;align-items:center;'
                    f'justify-content:center;font-size:32px">🏟</div>',
                    unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="width:72px;height:72px;border-radius:10px;'
                f'background:{primaer}22;display:flex;align-items:center;'
                f'justify-content:center;font-size:32px;border:1px solid {primaer}44">🏟</div>',
                unsafe_allow_html=True)
    with hc2:
        liz_c = {
            "TRAINER_BASIC": _C["muted"],   "TRAINER_PRO": _C["green"],
            "VEREIN_BASIC":  _C["blue"],    "VEREIN_PRO":  _C["orange"],
            "Enterprise": _C["orange"], "Premium": _C["blue"],
            "Standard": _C["green"],
        }.get(lizenz, _C["muted"])
        st.markdown(
            f'<div style="padding-top:4px">'
            f'<h2 style="color:{_C["text"]};margin:0 0 4px">{vname}</h2>'
            f'<span style="background:{liz_c}22;color:{liz_c};font-size:10px;'
            f'font-weight:700;padding:2px 10px;border-radius:8px;border:1px solid {liz_c}44">'
            f'{lizenz}</span>'
            + (f'<span style="color:{_C["muted"]};font-size:10px;margin-left:10px">'
               f'Lizenz bis {liz_bis}</span>' if liz_bis else "")
            + f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    kpis = dashboard_va_kpis(verein_id) if verein_id else {}
    avg_fms = kpis.get("avg_fms")

    # ── KPI-Reihe 1 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Trainer",        kpis.get("n_trainer",0),      "🧑‍💼", _C["blue"],  "aktiv"),
        ("Spieler",        kpis.get("n_spieler",0),      "⚽",   _C["green"], ""),
        ("Diagnostiken",   kpis.get("n_diagnostiken",0), "🔬",   _C["purple"],"gesamt"),
        ("Aktive Verletz.", kpis.get("n_verletzungen",0), "🩺",   _C["red"],   "", "", True),
    ])
    # ── KPI-Reihe 2 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Nie getestet",   kpis.get("n_ungetestet",0),   "⚠",   _C["orange"],"Spieler ohne Test","","True"),
        ("Ø FMS Score",    f"{avg_fms}/21" if avg_fms else "—","📊",_C["teal"],  "Letzter je Spieler"),
        ("Gruss",          _gruss(user.get("vorname","")),"👋",   _C["muted"], _datum_de()),
        ("Dein Verein",    vname,                         "🏟",   primaer,    ""),
    ])

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        ak = dashboard_spieler_altersklassen(verein_id)
        if ak:
            st.plotly_chart(
                _bar([r["altersklasse"] for r in ak], [r["n"] for r in ak],
                     "Spieler nach Altersklasse", _C["blue"]),
                use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Noch keine Spieler mit Altersklasse.")
    with c2:
        ms = dashboard_spieler_mannschaften(verein_id)
        if ms:
            st.plotly_chart(
                _donut([r["mannschaft"] for r in ms], [r["n"] for r in ms],
                       "Spieler nach Mannschaft"),
                use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Noch keine Mannschaften angelegt.")

    lbl, val = _fill_months(dashboard_monatlich_diagnostiken(verein_id))
    st.plotly_chart(
        _line(lbl, val, "Diagnostiken der letzten 12 Monate", _C["purple"]),
        use_container_width=True, config={"displayModeBar": False})

    st.divider()
    _aktivitaeten(dashboard_letzte_logins(verein_id=verein_id, limit=8))


# ── Trainer ── Hilfsfunktionen ────────────────────────────────────────────────

def _trainer_greeting(vorname: str) -> None:
    """Kompakte Begrüßungszeile ohne Trenner darunter."""
    st.markdown(
        f'<div style="margin-bottom:16px">'
        f'<div style="font-size:22px;font-weight:700;color:{_C["text"]};line-height:1.2">'
        f'{_gruss(vorname)}</div>'
        f'<div style="font-size:12px;color:{_C["muted"]};margin-top:3px">{_datum_de()}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _trainer_leer(trainer_id) -> None:  # noqa: ARG001
    """Onboarding-Ansicht für neue Accounts ohne Spieler."""
    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:14px;padding:48px 24px;text-align:center;margin:8px 0 20px">'
        f'<div style="font-size:52px;margin-bottom:14px">⚽</div>'
        f'<div style="font-size:18px;font-weight:700;color:{_C["text"]};margin-bottom:8px">'
        f'Willkommen bei Athletic Performance Hub</div>'
        f'<div style="font-size:13px;color:{_C["muted"]};max-width:380px;margin:0 auto">'
        f'Lege deinen ersten Spieler an, um mit Diagnostik und Trainingsplanung zu starten.'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    _c1, _c2, _c3 = st.columns([1, 2, 1])
    with _c2:
        if st.button("➕ Ersten Spieler anlegen", key="leer_spieler_btn",
                     use_container_width=True, type="primary"):
            st.session_state["nav_sub_spieler"] = "👥 Verwaltung"
            _navigate("👤  Spieler")


def _compute_team_score(alle_spieler: list) -> tuple[int, int, int]:
    """
    Berechnet (avg_score, high_risk_count, n_scored).
    avg_score: Stichprobe max. 12 Spieler — bestehende Logik beibehalten.
    high_risk: alle Spieler (risiko_score >= 2).
    """
    scores = []
    for p in alle_spieler[:12]:
        pid = p["id"]
        sc  = athletik_score(
            fms_letzter(pid), y_balance_letzter(pid), sprint_letzter(pid),
            sprung_letzter(pid), agilitaet_letzter(pid), ausdauer_letzter(pid),
            spiro_row=spiro_test_letzter(pid),
        )
        scores.append(sc)
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    high_risk = 0
    for p in alle_spieler:
        pid = p["id"]
        rs  = risiko_score(fms_letzter(pid), y_balance_letzter(pid), verletzungen_laden(pid))
        if rs >= 2:
            high_risk += 1

    return avg_score, high_risk, len(scores)


def _trainer_kpi_strip(n_spieler: int, faellig: int,
                        high_risk: int, verletz: int, diag_monat: int) -> None:
    """Kompakter KPI-Streifen — eine Zeile, alle Kennzahlen."""
    items: list[tuple] = [
        ("⚽", "Spieler",      n_spieler,  _C["blue"],   False),
        ("📋", "Fällige Tests", faellig,    _C["orange"], faellig > 0),
        ("⚠",  "Erhöhtes Risiko", high_risk, _C["red"],   high_risk > 0),
    ]
    if verletz > 0:
        items.append(("🩺", "Verletzungen", verletz, _C["red"], True))
    items.append(("🔬", "Tests/Monat", diag_monat, _C["purple"], False))

    cols = st.columns(len(items))
    for col, (icon, label, value, color, warn) in zip(cols, items):
        c = _C["red"] if warn else color
        with col:
            st.markdown(
                f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
                f'border-radius:10px;padding:12px 8px;text-align:center">'
                f'<div style="font-size:9px;color:{_C["muted"]};letter-spacing:.7px;'
                f'margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                f'{icon} {label.upper()}</div>'
                f'<div style="font-size:24px;font-weight:800;color:{c};line-height:1">'
                f'{value}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)


def _trainer_score_card(avg_score: int, data_ok: bool, n_scored: int) -> None:
    """Prominente Team-Athletikscore-Karte mit Fortschrittsbalken."""
    if avg_score >= 70:
        sc_color, sc_label = _C["green"],  "Gut"
    elif avg_score >= 40:
        sc_color, sc_label = _C["orange"], "Verbesserungsbedarf"
    else:
        sc_color, sc_label = _C["red"],    "Kritisch"

    if not data_ok or avg_score == 0:
        sc_color, sc_label = _C["muted"], "—"
        note = "Keine ausreichenden Diagnosedaten für Team-Score."
        score_txt = "—"
        pct = 0
    else:
        note = ("Basierend auf den aktuell verfügbaren Diagnosedaten."
                if n_scored >= 3
                else f"Score basiert auf {n_scored} Spieler(n) — unvollständige Datenbasis.")
        score_txt = str(avg_score)
        pct = avg_score

    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:12px;padding:20px;min-height:160px">'
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;margin-bottom:14px">'
        f'📊 TEAM-ATHLETIKSCORE</div>'
        f'<div style="display:flex;align-items:flex-end;gap:8px;margin-bottom:10px">'
        f'<div style="font-size:46px;font-weight:800;color:{sc_color};line-height:1">'
        f'{score_txt}</div>'
        f'<div style="font-size:15px;color:{_C["muted"]};margin-bottom:6px">/100</div>'
        f'</div>'
        f'<div style="background:#21262d;border-radius:6px;height:8px;margin-bottom:8px">'
        f'<div style="background:{sc_color};width:{pct}%;height:8px;border-radius:6px"></div>'
        f'</div>'
        f'<div style="font-size:12px;font-weight:600;color:{sc_color}">{sc_label}</div>'
        f'<div style="font-size:10px;color:{_C["muted"]};margin-top:6px;line-height:1.4">'
        f'{note}</div></div>',
        unsafe_allow_html=True,
    )


def _trainer_handlung(faellig: int, high_risk: int, verletz: int) -> None:
    """Handlungsbedarf-Karte + Aktions-Buttons."""
    items = []
    if faellig > 0:
        items.append(("📋", _C["orange"],
                       f"{faellig} Spieler ohne aktuellen Test (> 30 Tage)",
                       "faellig", "👥  Mannschaft"))
    if high_risk > 0:
        items.append(("⚠", _C["red"],
                       f"{high_risk} Spieler mit erhöhtem Risiko",
                       "risiko", "👥  Mannschaft"))
    if verletz > 0:
        items.append(("🩺", _C["red"],
                       f"{verletz} neue Verletzung(en) – letzte 14 Tage",
                       "verletzt", "👥  Mannschaft"))

    items_html = (
        "".join(
            f'<div style="display:flex;align-items:flex-start;gap:10px;'
            f'border-left:3px solid {c};padding:8px 10px;'
            f'background:{c}15;border-radius:0 8px 8px 0;margin-bottom:8px">'
            f'<span style="font-size:14px;flex-shrink:0">{icon}</span>'
            f'<span style="font-size:12px;color:{_C["text"]};line-height:1.5">{txt}</span>'
            f'</div>'
            for icon, c, txt, _, __ in items
        )
        if items else
        f'<div style="display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;padding:20px 0">'
        f'<div style="font-size:28px;margin-bottom:6px">✅</div>'
        f'<div style="font-size:12px;color:{_C["muted"]}">Kein dringender Handlungsbedarf</div>'
        f'</div>'
    )

    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:12px;padding:20px;min-height:160px">'
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;margin-bottom:14px">'
        f'⚡ HANDLUNGSBEDARF</div>'
        f'{items_html}</div>',
        unsafe_allow_html=True,
    )
    for i, (icon, _, txt, kpi_val, section) in enumerate(items):
        if st.button(f"{icon} Anzeigen →", key=f"hdl_btn_{i}", use_container_width=True):
            st.session_state["kpi_filter"] = kpi_val
            _navigate(section)


def _trainer_schnellaktionen() -> None:
    """Kompakte Schnellaktionen — 4 Buttons in einer Zeile."""
    st.markdown(
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;'
        f'margin:18px 0 8px">⚡ SCHNELLAKTIONEN</div>',
        unsafe_allow_html=True,
    )
    _q1, _q2, _q3, _q4 = st.columns(4)
    with _q1:
        if st.button("👤 Spieler", key="qa2_spieler", use_container_width=True):
            st.session_state["nav_sub_spieler"] = "👥 Verwaltung"
            _navigate("👤  Spieler")
    with _q2:
        if st.button("🧪 Diagnostik", key="qa2_diag", use_container_width=True):
            _navigate("🔬  Diagnostik")
    with _q3:
        if st.button("📅 Training", key="qa2_training", use_container_width=True):
            _navigate("📅  Training")
    with _q4:
        if st.button("📄 PDF", key="qa2_pdf", use_container_width=True):
            _navigate("📄  Dokumente")


def _trainer_letzte_spieler(trainer_id) -> None:
    """Zuletzt verwendete Spieler — max 3, kompakte Karten."""
    st.markdown(
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;'
        f'margin:20px 0 12px">👤 ZULETZT VERWENDET</div>',
        unsafe_allow_html=True,
    )
    letzte = dashboard_trainer_letzte_spieler(trainer_id, limit=3) if trainer_id else []
    if not letzte:
        st.caption("Keine kürzlich verwendeten Spieler.")
        if st.button("👥 Alle Spieler anzeigen →", key="lsp_alle_leer",
                     use_container_width=True):
            st.session_state["nav_sub_spieler"] = "👥 Verwaltung"
            _navigate("👤  Spieler")
        return

    _FARBEN = ["#58a6ff", "#3fb950", "#d29922"]
    ncols = max(1, len(letzte))
    cols  = st.columns(ncols)

    for i, s in enumerate(letzte):
        pid     = s["id"]
        name    = (f"{s.get('vorname','')} {s.get('nachname','')}".strip()
                   or s.get("name", "—"))
        mannsch = s.get("mannschaft") or "—"
        letzte_m = s.get("letzte_messung") or "Noch kein Test"
        sc      = athletik_score(
            fms_letzter(pid), y_balance_letzter(pid), sprint_letzter(pid),
            sprung_letzter(pid), agilitaet_letzter(pid), ausdauer_letzter(pid),
            spiro_row=spiro_test_letzter(pid),
        )
        sc_c    = _C["green"] if sc >= 70 else _C["orange"] if sc >= 40 else _C["red"]
        sc_txt  = f"{sc}/100" if sc else "—"
        farbe   = _FARBEN[i % len(_FARBEN)]
        initial = name[0].upper() if name else "?"

        with cols[i]:
            st.markdown(
                f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
                f'border-radius:10px;padding:14px;margin-bottom:8px">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
                f'<div style="width:36px;height:36px;border-radius:50%;'
                f'background:{farbe}22;border:2px solid {farbe};'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:15px;font-weight:800;color:{farbe};flex-shrink:0">{initial}</div>'
                f'<div style="min-width:0">'
                f'<div style="font-size:13px;font-weight:700;color:{_C["text"]};'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{name}</div>'
                f'<div style="font-size:10px;color:{_C["muted"]}">{mannsch}</div>'
                f'</div></div>'
                f'<div style="display:flex;justify-content:space-between;'
                f'border-top:1px solid {_C["border"]};padding-top:8px">'
                f'<div><div style="font-size:9px;color:{_C["muted"]}">SCORE</div>'
                f'<div style="font-size:16px;font-weight:800;color:{sc_c}">{sc_txt}</div></div>'
                f'<div style="text-align:right">'
                f'<div style="font-size:9px;color:{_C["muted"]}">LETZTER TEST</div>'
                f'<div style="font-size:10px;color:{_C["muted"]}">{letzte_m}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Profil →", key=f"lsp_{pid}", use_container_width=True):
                st.session_state["global_player_id"]  = pid
                st.session_state["_nav_goto"]         = "👤  Spieler"
                st.session_state["nav_sub_spieler"]   = "🏃 Profil & Diagnostik"
                st.rerun()

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    if st.button("👥 Alle Spieler →", key="lsp_alle", use_container_width=True):
        st.session_state["nav_sub_spieler"] = "👥 Verwaltung"
        _navigate("👤  Spieler")


# ── Trainer-Dashboard ─────────────────────────────────────────────────────────

def _dash_trainer(user: dict):
    trainer_id = user.get("id")
    vorname    = user.get("vorname") or user.get("email", "Coach")

    # 1. Kompakte Begrüßung
    _trainer_greeting(vorname)

    # 2. Daten laden — gebündelt, kein Divider darunter
    alle_spieler = spieler_laden(trainer_id, "Trainer", user.get("verein_id"))
    n_spieler    = len(alle_spieler) if alle_spieler else 0

    # Leerer Account → Onboarding
    if not alle_spieler:
        _trainer_leer(trainer_id)
        return

    faellig    = dashboard_trainer_ohne_test(trainer_id)    if trainer_id else 0
    verletz    = dashboard_trainer_neue_verletzungen(trainer_id) if trainer_id else 0
    diag_monat = dashboard_trainer_diagnostiken_monat(trainer_id) if trainer_id else 0

    # Team-Score + Risiko (bestehende Berechnung, keine neue Logik)
    avg_score, high_risk, n_scored = _compute_team_score(alle_spieler)

    # 3. KPI-Streifen
    _trainer_kpi_strip(n_spieler, faellig, high_risk, verletz, diag_monat)

    # 4. Score-Karte + Handlungsbedarf (Desktop: nebeneinander; Mobile: gestapelt)
    _col_l, _col_r = st.columns([1, 1], gap="small")
    with _col_l:
        _trainer_score_card(avg_score, n_scored > 0, n_scored)
    with _col_r:
        _trainer_handlung(faellig, high_risk, verletz)

    # 5. Schnellaktionen
    _trainer_schnellaktionen()

    # 6. Zuletzt verwendete Spieler
    _trainer_letzte_spieler(trainer_id)

    # ── Daten laden ───────────────────────────────────────────────────────────
    alle_spieler = spieler_laden(trainer_id, "Trainer", user.get("verein_id"))
    n_spieler    = len(alle_spieler) if alle_spieler else 0
    faellig      = dashboard_trainer_ohne_test(trainer_id) if trainer_id else 0
    verletz      = dashboard_trainer_neue_verletzungen(trainer_id) if trainer_id else 0
    diag_monat   = dashboard_trainer_diagnostiken_monat(trainer_id) if trainer_id else 0

    # Athletikscore (Stichprobe max. 12) + Risiko für alle Spieler berechnen
    avg_score  = 0
    high_risk  = 0
    if alle_spieler:
        scores = []
        for p in alle_spieler[:12]:
            pid  = p["id"]
            fms  = fms_letzter(pid)
            y    = y_balance_letzter(pid)
            spr  = sprint_letzter(pid)
            sprg = sprung_letzter(pid)
            agi  = agilitaet_letzter(pid)
            aus  = ausdauer_letzter(pid)
            spi  = spiro_test_letzter(pid)
            sc   = athletik_score(fms, y, spr, sprg, agi, aus, spiro_row=spi)
            scores.append(sc)
        avg_score = round(sum(scores) / len(scores)) if scores else 0

        # Risiko über alle Spieler — stimmt mit dem Mannschafts-Filter überein
        for p in alle_spieler:
            pid = p["id"]
            fms = fms_letzter(pid)
            y   = y_balance_letzter(pid)
            vl  = verletzungen_laden(pid)
            rs  = risiko_score(fms, y, vl)
            if rs >= 2:
                high_risk += 1

    # ── KPI-Reihe 1 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Meine Spieler",      n_spieler,   "⚽",  _C["blue"],  ""),
        ("Fällige Tests",      faellig,     "📋",  _C["orange"],"ohne Test > 30 Tage", "", True),
        ("Neue Verletzungen",  verletz,     "🩺",  _C["red"],   "letzte 14 Tage",      "", True),
    ])
    # Direktlink-Buttons unter KPI-Reihe 1
    _b1, _b2, _b3 = st.columns(3)
    with _b2:
        if faellig > 0:
            if st.button("📋 Fällige Tests anzeigen →", key="kpi_btn_faellig",
                         use_container_width=True):
                st.session_state["kpi_filter"] = "faellig"
                _navigate("👥  Mannschaft")
    with _b3:
        if verletz > 0:
            if st.button("🩺 Verletzungen anzeigen →", key="kpi_btn_verletz",
                         use_container_width=True):
                st.session_state["kpi_filter"] = "verletzt"
                _navigate("👥  Mannschaft")

    # ── KPI-Reihe 2 ───────────────────────────────────────────────────────────
    _kpi_row([
        ("Diagnostiken",       diag_monat,  "🔬",  _C["purple"],"diesen Monat"),
        ("Ø Athletikscore",    f"{avg_score}/100","📊",_C["teal"],"basierend auf letzten Tests"),
        ("Erhöhtes Risiko",    high_risk,   "⚠",  _C["red"],   "Spieler mit Risiko mittel/hoch","","True"),
    ])
    # Direktlink-Button unter KPI-Reihe 2
    _c1, _c2, _c3 = st.columns(3)
    with _c3:
        if high_risk > 0:
            if st.button("⚠ Risikospieler anzeigen →", key="kpi_btn_risiko",
                         use_container_width=True):
                st.session_state["kpi_filter"] = "risiko"
                _navigate("👥  Mannschaft")

    # ── Meine letzten Spieler ─────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f'<div style="font-size:12px;font-weight:700;color:{_C["muted"]};'
        f'letter-spacing:.5px;margin-bottom:12px">MEINE LETZTEN SPIELER</div>',
        unsafe_allow_html=True,
    )

    letzte = dashboard_trainer_letzte_spieler(trainer_id, limit=6) if trainer_id else []

    if not letzte:
        st.markdown(
            f'<div style="text-align:center;padding:32px;background:{_C["surf"]};'
            f'border-radius:10px;border:1px dashed {_C["border"]}">'
            f'<div style="font-size:32px">⚽</div>'
            f'<div style="color:{_C["muted"]};margin-top:8px">Noch keine Spieler angelegt</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        # Athletikscore für angezeigte Spieler
        scores_map = {}
        for s in letzte:
            pid  = s["id"]
            sc   = athletik_score(
                fms_letzter(pid), y_balance_letzter(pid), sprint_letzter(pid),
                sprung_letzter(pid), agilitaet_letzter(pid), ausdauer_letzter(pid),
                spiro_row=spiro_test_letzter(pid),
            )
            scores_map[pid] = sc

        cols = st.columns(3)
        _FARBEN = ["#58a6ff","#3fb950","#d29922","#f85149","#bc8cff","#ffa657"]
        for i, s in enumerate(letzte):
            pid      = s["id"]
            name     = f"{s.get('vorname','')} {s.get('nachname','')}".strip() or s.get("name","—")
            mannsch  = s.get("mannschaft","—")
            ak       = s.get("altersklasse","—")
            letzte_m = s.get("letzte_messung") or "Noch kein Test"
            sc       = scores_map.get(pid, 0)
            farbe    = _FARBEN[i % len(_FARBEN)]
            initial  = name[0].upper() if name else "?"

            # Score-Farbe
            sc_c = _C["green"] if sc >= 70 else _C["orange"] if sc >= 40 else _C["red"]
            sc_txt = f"{sc}/100" if sc else "—"

            with cols[i % 3]:
                st.markdown(
                    f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
                    f'border-radius:10px;padding:16px;margin-bottom:8px">'
                    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
                    f'<div style="width:44px;height:44px;border-radius:50%;'
                    f'background:{farbe}22;border:2px solid {farbe};'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-size:18px;font-weight:800;color:{farbe};flex-shrink:0">{initial}</div>'
                    f'<div>'
                    f'<div style="font-size:14px;font-weight:700;color:{_C["text"]}">{name}</div>'
                    f'<div style="font-size:10px;color:{_C["muted"]}">{mannsch} · {ak}</div>'
                    f'</div></div>'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;border-top:1px solid {_C["border"]};padding-top:10px">'
                    f'<div>'
                    f'<div style="font-size:9px;color:{_C["muted"]};letter-spacing:.5px">ATHLETIKSCORE</div>'
                    f'<div style="font-size:18px;font-weight:800;color:{sc_c}">{sc_txt}</div>'
                    f'</div>'
                    f'<div style="text-align:right">'
                    f'<div style="font-size:9px;color:{_C["muted"]};letter-spacing:.5px">LETZTE MESSUNG</div>'
                    f'<div style="font-size:11px;color:{_C["muted"]}">{letzte_m}</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )

    # ── Schnellzugriffe ───────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f'<div style="font-size:12px;font-weight:700;color:{_C["muted"]};'
        f'letter-spacing:.5px;margin-bottom:12px">SCHNELLZUGRIFFE</div>',
        unsafe_allow_html=True,
    )

    qa1, qa2, qa3, qa4 = st.columns(4)
    _BTN = "use_container_width=True"

    with qa1:
        st.markdown(
            f'<div style="background:{_C["blue"]}18;border:1px solid {_C["blue"]}44;'
            f'border-radius:10px;padding:16px;text-align:center;margin-bottom:4px">'
            f'<div style="font-size:28px">⚽</div>'
            f'<div style="font-size:12px;font-weight:700;color:{_C["blue"]};margin-top:4px">'
            f'Neuer Spieler</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("➕ Spieler anlegen", key="qa_spieler", use_container_width=True):
            # Explizit auf "👥 Verwaltung" (= page_spieler mit "Neu anlegen"-Tab) navigieren.
            # Ohne dieses Assignment landet der User auf dem zuletzt aktiven Sub (z.B.
            # "🏃 Profil & Diagnostik") — was beim nächsten Widget-Rerun zum Nav-Reset führt.
            st.session_state["nav_sub_spieler"] = "👥 Verwaltung"
            _navigate("👤  Spieler")

    with qa2:
        st.markdown(
            f'<div style="background:{_C["purple"]}18;border:1px solid {_C["purple"]}44;'
            f'border-radius:10px;padding:16px;text-align:center;margin-bottom:4px">'
            f'<div style="font-size:28px">🔬</div>'
            f'<div style="font-size:12px;font-weight:700;color:{_C["purple"]};margin-top:4px">'
            f'Neue Diagnostik</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("➕ Diagnostik starten", key="qa_diag", use_container_width=True):
            _navigate("🔬  Diagnostik")

    with qa3:
        st.markdown(
            f'<div style="background:{_C["green"]}18;border:1px solid {_C["green"]}44;'
            f'border-radius:10px;padding:16px;text-align:center;margin-bottom:4px">'
            f'<div style="font-size:28px">📅</div>'
            f'<div style="font-size:12px;font-weight:700;color:{_C["green"]};margin-top:4px">'
            f'Trainingsplan</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("➕ Trainingsplan", key="qa_training", use_container_width=True):
            _navigate("📅  Training")

    with qa4:
        st.markdown(
            f'<div style="background:{_C["orange"]}18;border:1px solid {_C["orange"]}44;'
            f'border-radius:10px;padding:16px;text-align:center;margin-bottom:4px">'
            f'<div style="font-size:28px">📄</div>'
            f'<div style="font-size:12px;font-weight:700;color:{_C["orange"]};margin-top:4px">'
            f'PDF erstellen</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("📄 PDF erstellen", key="qa_pdf", use_container_width=True):
            _navigate("📄  Dokumente")
