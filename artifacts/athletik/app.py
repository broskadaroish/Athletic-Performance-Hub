"""
Bruce Football Performance Diagnostics
────────────────────────────────────────
Main Streamlit entry point.  All pages live in this single file to keep
imports simple; shared logic is delegated to the module layer.
"""

# ─── Branding & Version ───────────────────────────────────────────────────────
APP_NAME      = "Bruce Football Performance Diagnostics"
APP_VERSION   = "1.0.0"
APP_DEVELOPER = "Broska Daroish"
APP_EMAIL     = "Broska_daroish@hotmail.de"
APP_PHONE     = "01741682671"
APP_COPYRIGHT = "\u00a9 2026 Broska Daroish. Alle Rechte vorbehalten."

import os
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
    anthro_karte,
    render_observation_selector,
)

from database import (
    init_db,
    spieler_speichern, spieler_laden, spieler_by_id, spieler_loeschen, spieler_aktualisieren,
    berechne_alter, altersklasse_vorschlag,
    verletzung_speichern, verletzungen_laden, verletzung_loeschen,
    anthropometrie_speichern, anthropometrie_letzter, anthropometrie_history, anthropometrie_loeschen_letzten,
    fms_speichern, fms_letzter, fms_history, fms_history_full,
    y_balance_speichern, y_balance_letzter, y_balance_history, y_balance_history_full,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern, trainingsplan_laden,
    sprint_speichern, sprint_letzter, sprint_history,
    sprung_speichern, sprung_letzter, sprung_history,
    agilitaet_speichern, agilitaet_letzter, agilitaet_history,
    ausdauer_speichern, ausdauer_letzter, ausdauer_history,
    kraft_speichern, kraft_letzter, kraft_history,
    einwilligung_speichern, einwilligung_letzter, einwilligung_alle,
    db_komplett_zuruecksetzen,
    checkliste_custom_laden, checkliste_custom_speichern,
    logo_laden, logo_speichern, logo_loeschen,
    beobachtung_speichern,
    beobachtungen_alle_fuer_spieler,
    spiro_protokoll_alle, spiro_protokoll_speichern,
    spiro_test_speichern, spiro_test_letzter, spiro_test_alle,
    spiro_stufen_speichern, spiro_stufen_laden,
    spiro_nachbelastung_speichern, spiro_nachbelastung_laden,
    spiro_test_loeschen,
)
from testprotokoll_pdf import (
    generate_testprotokoll, TEST_NAMEN, TEST_REIHENFOLGE,
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
    koerperfett_jp7, koerperfett_jp11,
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
from kraft import KraftErgebnis as _KraftErgebnis, epley_1rm as _epley_1rm
from analytics import (
    risiko_score, risiko_label, athletik_score, athletik_sub_scores,
    defizite_ermitteln, schwerpunkt_sammeln,
)
from periodisierung import (zyklus_erstellen, zyklus_laden, trainingsplan_multi_erstellen,
                             defizit_tabelle, _alter_zu_plangruppe, _PLANGRUPPEN_CONFIG, _POOL,
                             _ALTERS_ERSATZ)
from i18n import t, SPRACHEN, get_lang, set_lang
from pdf_report import generate_report, generate_vergleich_pdf, generate_trainingsplan_pdf
from pdf_anleitung import generate_anleitung_pdf, ALL_TEST_IDS, TEST_LABELS
from export import kader_excel_bytes, spieler_excel_bytes
from field_eval import alter_zu_altersgruppe, asymmetrie_badge_html, fms_asymmetrie_badge_html


# ─── Anleitung-Download-Button (wiederverwendbar auf jeder Testseite) ─────────

@st.cache_data(show_spinner=False)
def _generate_anleitung_cached(test_id: str, vereinsname: str, saison: str,
                               logo_bytes: bytes | None = None) -> bytes:
    """Generiert ein Einzel-Test-PDF (gecacht nach test_id + Vereinsinfos + Logo)."""
    return generate_anleitung_pdf(
        [test_id],
        mit_deckblatt=False,
        vereinsname=vereinsname,
        saison=saison,
        logo_bytes=logo_bytes,
    )


def _anleitung_download_button(test_id: str) -> None:
    """Zeigt einen kleinen PDF-Download-Button für die Testanleitung dieser Seite."""
    vn = st.session_state.get("cfg_vereinsname", "")
    sn = st.session_state.get("cfg_saison", "")
    try:
        pdf_bytes = _generate_anleitung_cached(test_id, vn, sn, logo_bytes=logo_laden())
    except Exception:
        return
    test_name = TEST_LABELS.get(test_id, test_id)
    fname = f"Anleitung_{test_name.replace(' ', '_')}.pdf"
    _, btn_col = st.columns([5, 1])
    with btn_col:
        st.download_button(
            label="📄 Anleitung",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            key=f"dl_anleitung_{test_id}",
            use_container_width=True,
            help=f"Testanleitung '{test_name}' als PDF herunterladen",
        )

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
from PIL import Image as _PILImage
_APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "app_logo.png")
if not os.path.exists(_APP_ICON_PATH):
    _APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
if not os.path.exists(_APP_ICON_PATH):
    _APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
_app_icon_img = _PILImage.open(_APP_ICON_PATH) if os.path.exists(_APP_ICON_PATH) else "⚽"

st.set_page_config(
    page_title="Bruce Football Performance Diagnostics",
    page_icon=_app_icon_img,
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

# ─── Splash Screen (einmal pro Sitzung) ──────────────────────────────────────
if "splash_done" not in st.session_state:
    st.session_state["splash_done"] = True
    import time as _time
    _sc1, _sc2, _sc3 = st.columns([1, 2, 1])
    with _sc2:
        if os.path.exists(_APP_ICON_PATH):
            _ic1, _ic2, _ic3 = st.columns([1, 2, 1])
            _ic2.image(_APP_ICON_PATH, width=120)
        st.markdown(
            f'<div style="text-align:center;padding:20px 0 24px">'
            f'<div style="font-size:80px;line-height:1">{"" if os.path.exists(_APP_ICON_PATH) else "⚽"}</div>'
            f'<h1 style="color:#e6edf3;font-size:26px;font-weight:800;'
            f'letter-spacing:1px;margin:20px 0 6px;line-height:1.3">'
            f'Bruce Football<br>Performance Diagnostics</h1>'
            f'<div style="color:#58a6ff;font-size:13px;font-weight:600;'
            f'letter-spacing:2px;margin-bottom:12px">VERSION {APP_VERSION}</div>'
            f'<div style="color:#8b949e;font-size:11px">{APP_COPYRIGHT}</div>'
            f'<div style="color:#30363d;font-size:11px;margin-top:40px">'
            f'Startet automatisch …</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _time.sleep(2.5)
    st.rerun()

# ─── Helpers ──────────────────────────────────────────────────────────────────

# Delegate badge helpers to ui_components (keep aliases for existing page code)
def _risk_badge(level: str) -> str:
    return risk_badge_html(level)

def _score_badge(score: int) -> str:
    return score_badge_html(score)

def _progress_html(value: int, max_val: int, color: str = "#1f6feb") -> str:
    pct = min(value / max_val * 100, 100)
    return f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'

def _save_ok(msg: str) -> None:
    """Speichert eine Erfolgsmeldung in session_state für Anzeige nach st.rerun()."""
    st.session_state["__save_ok__"] = msg

def _check_save_ok() -> None:
    """Zeigt eine gespeicherte Erfolgsmeldung dauerhaft und löscht sie danach."""
    msg = st.session_state.pop("__save_ok__", None)
    if msg:
        st.markdown(
            f'<div style="background:#1a4a2e;border:1px solid #3fb950;border-radius:8px;'
            f'padding:10px 16px;margin:8px 0;font-size:0.97em;color:#e6edf3">'
            f'✅ {msg}</div>',
            unsafe_allow_html=True,
        )

def _validate_geburtsdatum(datum_str: str):
    """Prüft Datum TT.MM.JJJJ — gibt (True, None) oder (False, Fehlermeldung) zurück."""
    from datetime import datetime as _dt, date as _d
    s = datum_str.strip()
    if not s:
        return False, "Bitte ein Geburtsdatum eingeben."
    parts = s.split(".")
    if len(parts) != 3:
        return False, f"Format TT.MM.JJJJ erwartet (z. B. 15.03.2008), eingegeben: »{s}«"
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return False, f"Datum enthält ungültige Zeichen: »{s}«"
    if not (1 <= month <= 12):
        return False, f"Monat {month} ist ungültig — erlaubt: 1–12."
    if not (1 <= day <= 31):
        return False, f"Tag {day} ist ungültig — erlaubt: 1–31."
    if not (1900 <= year <= 2100):
        return False, f"Jahr {year} ist ungültig — erlaubt: 1900–2100."
    try:
        _dt(year, month, day)
    except ValueError:
        return False, f"Das Datum {day}.{month}.{year} existiert nicht (z. B. 31.02 gibt es nicht)."
    return True, None

def _color_for_score(score: int, max_val: int = 100) -> str:
    pct = score / max_val
    if pct >= 0.75: return C["green"]
    if pct >= 0.5:  return C["yellow"]
    return C["red"]


def _datum_filter(df: "pd.DataFrame", key: str) -> "pd.DataFrame":
    """Rendert einen optionalen Datum-Bereichsfilter über einer Verlaufstabelle.
    Erwartet eine Spalte 'Datum' im DataFrame. Gibt den gefilterten DataFrame zurück."""
    if df is None or df.empty or "Datum" not in df.columns:
        return df
    daten = df["Datum"].tolist()
    if len(daten) < 2:
        return df
    _fc1, _fc2 = st.columns(2)
    _von = _fc1.selectbox("📅 Zeitraum von", ["Alle"] + daten,
                           key=f"dfilter_von_{key}", label_visibility="visible")
    _bis = _fc2.selectbox("bis", ["Alle"] + list(reversed(daten)),
                           key=f"dfilter_bis_{key}", label_visibility="visible")
    if _von != "Alle" or _bis != "Alle":
        try:
            _von_idx = daten.index(_von) if _von != "Alle" else 0
            _bis_idx = daten.index(_bis) if _bis != "Alle" else len(daten) - 1
            if _von_idx > _bis_idx:
                _von_idx, _bis_idx = _bis_idx, _von_idx
            df = df.iloc[_von_idx:_bis_idx + 1].reset_index(drop=True)
            st.caption(f"🔍 {len(df)} von {len(daten)} Einträgen angezeigt.")
        except Exception:
            pass
    return df


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
    """Mannschaft-Seite: Kachelansicht, Filter, Trainingsgruppen, Warnmeldungen."""
    from datetime import timedelta as _td, datetime as _dt

    st.markdown(
        section_header("👥 Mannschaft", "Kaderübersicht, Trainingsgruppen und Warnmeldungen"),
        unsafe_allow_html=True,
    )

    all_players = spieler_laden()
    if not all_players:
        st.markdown(
            empty_state("👥", "Noch keine Spieler angelegt",
                        "Gehe zur Spielerverwaltung, um Spieler hinzuzufügen."),
            unsafe_allow_html=True,
        )
        return

    # ── Enrich all player data (one pass) ─────────────────────────────────────
    player_data = []
    for p in all_players:
        pid    = p["id"]
        fms    = fms_letzter(pid)
        y      = y_balance_letzter(pid)
        sprint = sprint_letzter(pid)
        sprung = sprung_letzter(pid)
        agil   = agilitaet_letzter(pid)
        aus    = ausdauer_letzter(pid)
        anthro = anthropometrie_letzter(pid)
        verlet = verletzungen_laden(pid)
        rs     = risiko_score(fms, y, verlet)
        _, level = risiko_label(rs)
        sc     = athletik_score(fms, y, sprint, sprung, agil, aus)
        defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro)
        # last test date across all modules
        dates = [d["datum"] for d in [fms, y, sprint, sprung, agil, aus]
                 if d and d.get("datum")]
        last_test_date = max(dates) if dates else None
        player_data.append({
            "p": p, "fms": fms, "y": y, "sprint": sprint, "sprung": sprung,
            "agil": agil, "aus": aus, "anthro": anthro, "verlet": verlet,
            "rs": rs, "level": level, "sc": sc, "defizite": defizite,
            "last_test_date": last_test_date,
        })

    total     = len(player_data)
    scores    = [d["sc"] for d in player_data]
    high_risk = sum(1 for d in player_data if d["level"] == "hoch")
    med_risk  = sum(1 for d in player_data if d["level"] == "mittel")
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    # ── KPI strip ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spieler gesamt", total)
    c2.metric("🔴 Handlungsbedarf Hoch", high_risk)
    c3.metric("🟡 Handlungsbedarf", med_risk)
    c4.metric("Ø Athletik Score", f"{avg_score}/100")

    st.markdown("---")

    # ── Helper: render color ───────────────────────────────────────────────────
    _RISK_COLOR  = {"hoch": C["red"], "mittel": C["yellow"], "gering": C["green"]}
    _RISK_ICON   = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    _RISK_LABEL  = {"hoch": "Handlungsbedarf hoch", "mittel": "Handlungsbedarf", "gering": "Unauffällig"}

    def _score_color(s: int) -> str:
        return C["green"] if s >= 75 else C["yellow"] if s >= 50 else C["red"]

    def _fmt_date(d: str | None) -> str:
        if not d:
            return "Kein Test"
        try:
            return _dt.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            return d

    def _days_since(d: str | None) -> int | None:
        if not d:
            return None
        try:
            delta = date.today() - _dt.strptime(d, "%Y-%m-%d").date()
            return delta.days
        except Exception:
            return None

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_kacheln, tab_gruppen, tab_warn, tab_tabelle = st.tabs([
        "🃏 Spielerkacheln", "🏋️ Trainingsgruppen", "⚠️ Warnmeldungen", "📊 Kader-Tabelle"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SPIELERKACHELN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_kacheln:
        # Filter bar
        f1, f2, f3, f4 = st.columns(4)
        alle_pos  = sorted({d["p"].get("hauptposition") or d["p"].get("position") or ""
                            for d in player_data
                            if d["p"].get("hauptposition") or d["p"].get("position")})
        alle_mann = sorted({d["p"].get("mannschaft") or "" for d in player_data
                            if d["p"].get("mannschaft")})
        alle_ak   = sorted({d["p"].get("altersklasse") or "" for d in player_data
                            if d["p"].get("altersklasse")})
        alle_stat = sorted({d["p"].get("trainingsstatus") or "" for d in player_data
                            if d["p"].get("trainingsstatus")})

        filt_pos  = f1.selectbox("Position",       ["Alle"] + alle_pos,  key="dash_pos",  label_visibility="visible")
        filt_mann = f2.selectbox("Mannschaft",      ["Alle"] + alle_mann, key="dash_mann", label_visibility="visible")
        filt_ak   = f3.selectbox("Altersklasse",    ["Alle"] + alle_ak,   key="dash_ak",   label_visibility="visible")
        filt_stat = f4.selectbox("Trainingsstatus", ["Alle"] + alle_stat, key="dash_stat", label_visibility="visible")

        filtered = player_data
        if filt_pos  != "Alle":
            filtered = [d for d in filtered
                        if (d["p"].get("hauptposition") or d["p"].get("position")) == filt_pos]
        if filt_mann != "Alle":
            filtered = [d for d in filtered if d["p"].get("mannschaft") == filt_mann]
        if filt_ak   != "Alle":
            filtered = [d for d in filtered if d["p"].get("altersklasse") == filt_ak]
        if filt_stat != "Alle":
            filtered = [d for d in filtered if d["p"].get("trainingsstatus") == filt_stat]

        st.caption(f"{len(filtered)} von {total} Spielern")

        if not filtered:
            st.info("Keine Spieler für die gewählten Filter.")
        else:
            cols = st.columns(3, gap="medium")
            for i, d in enumerate(filtered):
                p      = d["p"]
                level  = d["level"]
                rc     = _RISK_COLOR[level]
                sc_col = _score_color(d["sc"])
                pos    = p.get("hauptposition") or p.get("position") or "—"
                team   = p.get("mannschaft") or "—"

                # Key metrics (compact)
                metrics = []
                if d["fms"] and d["fms"].get("score"):
                    metrics.append(f"FMS {d['fms']['score']}/21")
                if d["sprint"] and d["sprint"].get("beste_10m"):
                    metrics.append(f"10m {d['sprint']['beste_10m']:.2f}s")
                if d["sprung"] and d["sprung"].get("cmj_beid"):
                    metrics.append(f"CMJ {d['sprung']['cmj_beid']:.0f}cm")
                metrics_str = " · ".join(metrics) if metrics else "Noch keine Testdaten"

                with cols[i % 3]:
                    st.markdown(
                        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                        f'border-top:3px solid {rc};border-radius:12px;'
                        f'padding:14px 16px 10px;margin-bottom:4px">'
                        f'<div style="font-size:16px;font-weight:700;color:{C["text"]}">{p["name"]}</div>'
                        f'<div style="font-size:11px;color:{C["muted"]};margin-bottom:8px">'
                        f'{pos} · {team}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px">'
                        f'<span style="font-size:28px;font-weight:800;color:{sc_col}">{d["sc"]}</span>'
                        f'<span style="font-size:11px;color:{C["muted"]}">/ 100 Athletik-Score</span>'
                        f'</div>'
                        f'<div style="font-size:11px;color:{rc};font-weight:600;margin-bottom:6px">'
                        f'{_RISK_ICON[level]} {_RISK_LABEL[level]}</div>'
                        f'<div style="font-size:10px;color:{C["muted"]}">'
                        f'{metrics_str}</div>'
                        f'<div style="font-size:10px;color:{C["muted"]};margin-top:4px">'
                        f'🗓 {_fmt_date(d["last_test_date"])}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Zum Profil →", key=f"kachel_profil_{p['id']}",
                                 use_container_width=True):
                        st.session_state["global_player_id"] = p["id"]
                        st.session_state["_nav_goto"]         = "👤  Spieler"
                        st.session_state["nav_sub_spieler"]   = "🏃 Profil & Diagnostik"
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — TRAININGSGRUPPEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_gruppen:
        st.markdown(
            f'<div style="font-size:13px;color:{C["muted"]};margin-bottom:16px">'
            f'Automatischer Vorschlag basierend auf kritischen Defiziten aus der Testanalyse. '
            f'Spieler werden dem Bereich mit dem dringlichsten Förderbedarf zugeordnet.</div>',
            unsafe_allow_html=True,
        )

        # Map defizit modul → group
        _MODUL_GRUPPE = {
            "Sprint":         "⚡ Gruppe Schnelligkeit",
            "Agilität":       "⚡ Gruppe Schnelligkeit",
            "Sprung":         "🦘 Gruppe Sprungkraft",
            "FMS":            "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "Y-Balance":      "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "Ausdauer":       "🫁 Gruppe Ausdauerkapazität",
        }
        _GRUPPE_INFO = {
            "⚡ Gruppe Schnelligkeit":              "Sprint, Beschleunigung, Richtungswechsel",
            "🦘 Gruppe Sprungkraft":                "Explosivkraft, Reaktivkraft, Beinachsenstabilität",
            "🔒 Gruppe Stabilität & Bewegungskontrolle": "FMS-Defizite, Y-Balance-Asymmetrien, Core-Stabilität",
            "🫁 Gruppe Ausdauerkapazität":          "Aerobe Basis, intermittierende Ausdauer",
            "✅ Kein spezifischer Förderbedarf":    "Keine kritischen Defizite — allgemeines Athletiktraining",
        }
        _GRUPPE_ORDER = [
            "⚡ Gruppe Schnelligkeit",
            "🦘 Gruppe Sprungkraft",
            "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "🫁 Gruppe Ausdauerkapazität",
            "✅ Kein spezifischer Förderbedarf",
        ]

        gruppen: dict[str, list] = {g: [] for g in _GRUPPE_ORDER}

        for d in player_data:
            # Find primary critical deficit, then warnung
            primary_group = None
            for level_filter in ("kritisch", "warnung"):
                for defizit in d["defizite"]:
                    if defizit["level"] == level_filter:
                        modul = defizit.get("modul", "")
                        if modul in _MODUL_GRUPPE:
                            primary_group = _MODUL_GRUPPE[modul]
                            break
                if primary_group:
                    break
            if not primary_group:
                primary_group = "✅ Kein spezifischer Förderbedarf"
            gruppen[primary_group].append(d)

        for gruppe_name in _GRUPPE_ORDER:
            mitglieder = gruppen[gruppe_name]
            if not mitglieder:
                continue
            info = _GRUPPE_INFO[gruppe_name]
            with st.expander(
                f"{gruppe_name} — {len(mitglieder)} Spieler",
                expanded=gruppe_name != "✅ Kein spezifischer Förderbedarf",
            ):
                st.caption(f"Trainingsschwerpunkt: {info}")
                cols = st.columns(min(len(mitglieder), 4))
                for j, d in enumerate(mitglieder):
                    p = d["p"]
                    rc = _RISK_COLOR[d["level"]]
                    # Show primary deficit text
                    prim_def = next(
                        (df["text"] for df in d["defizite"] if df.get("modul") in _MODUL_GRUPPE
                         and _MODUL_GRUPPE[df["modul"]] == gruppe_name),
                        None
                    )
                    with cols[j % 4]:
                        st.markdown(
                            f'<div style="background:{C["surface2"]};border:1px solid {C["border"]};'
                            f'border-left:3px solid {rc};border-radius:8px;padding:10px 12px;'
                            f'margin-bottom:6px">'
                            f'<div style="font-size:13px;font-weight:600;color:{C["text"]}">'
                            f'{p["name"]}</div>'
                            f'<div style="font-size:10px;color:{C["muted"]}">'
                            f'{p.get("hauptposition") or p.get("position") or "—"}</div>'
                            f'<div style="font-size:10px;color:{rc};margin-top:4px">'
                            f'{_RISK_ICON[d["level"]]} Score {d["sc"]}/100</div>'
                            + (f'<div style="font-size:9px;color:{C["muted"]};margin-top:4px;'
                               f'line-height:1.3">{prim_def}</div>' if prim_def else "")
                            + f'</div>',
                            unsafe_allow_html=True,
                        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — WARNMELDUNGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_warn:
        RETEST_TAGE = 56  # 8 Wochen

        warns_risiko     = [d for d in player_data if d["level"] == "hoch"]
        warns_retest     = [d for d in player_data
                            if (_days_since(d["last_test_date"]) or 999) > RETEST_TAGE]
        warns_wachstum   = []
        warns_eingeschr  = []

        for d in player_data:
            # Growth spurt: PHV-related reifestatus
            if d["anthro"]:
                reife = str(d["anthro"].get("reifestatus") or "").lower()
                phv   = d["anthro"].get("phv_offset")
                if ("vor phv" in reife or "wachstum" in reife
                        or (phv is not None and -1.5 <= float(phv) <= 1.0)):
                    warns_wachstum.append(d)
            # Restricted training status
            ts = str(d["p"].get("trainingsstatus") or "")
            if "Pause" in ts or "Abklärung" in ts or "Eingeschränkt" in ts or "Angepasst" in ts:
                warns_eingeschr.append(d)

        def _warn_block(title: str, icon: str, color: str, items: list,
                        detail_fn) -> None:
            if not items:
                st.markdown(
                    f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                    f'border-radius:8px;padding:10px 14px;margin-bottom:10px;'
                    f'display:flex;gap:10px;align-items:center">'
                    f'<span style="font-size:18px">{icon}</span>'
                    f'<div><div style="font-size:13px;font-weight:600;color:{C["muted"]}">'
                    f'{title}</div>'
                    f'<div style="font-size:11px;color:{C["muted"]}">Keine Auffälligkeiten</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                return
            with st.expander(f"{icon} {title} — {len(items)} Spieler", expanded=True):
                for d in items:
                    p   = d["p"]
                    det = detail_fn(d)
                    st.markdown(
                        f'<div style="background:{C["surface2"]};border-left:3px solid {color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px">'
                        f'<div style="font-size:13px;font-weight:600;color:{C["text"]}">'
                        f'{p["name"]}</div>'
                        f'<div style="font-size:11px;color:{C["muted"]}">'
                        f'{p.get("hauptposition") or p.get("position") or "—"} · '
                        f'{p.get("mannschaft") or "—"}</div>'
                        f'<div style="font-size:11px;color:{color};margin-top:4px">{det}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        _warn_block(
            "Hoher Risikoscore",
            "🔴", C["red"], warns_risiko,
            lambda d: f"Risikoscore {d['rs']} — FMS/Y-Balance oder Verletzungshistorie kritisch"
        )
        _warn_block(
            f"Fälliger Retest (>{RETEST_TAGE} Tage)",
            "📅", C["yellow"], warns_retest,
            lambda d: (f"Letzter Test: {_fmt_date(d['last_test_date'])} "
                       f"({_days_since(d['last_test_date']) or '?'} Tage)")
        )
        _warn_block(
            "Wachstumsschub-Fenster",
            "🌱", C["blue"], warns_wachstum,
            lambda d: (f"Reifestatus: {d['anthro'].get('reifestatus') or '—'} · "
                       f"PHV-Offset: {d['anthro'].get('phv_offset') or '—'} Jahre"
                       if d["anthro"] else "PHV-Daten vorhanden")
        )
        _warn_block(
            "Eingeschränkter Trainingsstatus",
            "🚫", C["muted"], warns_eingeschr,
            lambda d: d["p"].get("trainingsstatus") or "—"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — KADER-TABELLE (bestehende Ansicht)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_tabelle:
        col_left, col_right = st.columns([1, 2])
        with col_left:
            st.markdown("##### Athletik-Status Verteilung")
            low_risk = total - high_risk - med_risk
            fig_pie = go.Figure(go.Pie(
                labels=["Handlungsbedarf Hoch", "Handlungsbedarf", "Unauffällig"],
                values=[high_risk, med_risk, low_risk],
                hole=0.55,
                marker_colors=["#f85149", "#d29922", "#3fb950"],
                textfont=dict(color="#e6edf3"),
            ))
            fig_pie.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=True,
                                  legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_right:
            st.markdown("##### Athletik Scores — Kader")
            names  = [d["p"]["name"] for d in player_data]
            cols_c = [_color_for_score(d["sc"]) for d in player_data]
            fig_bar = go.Figure(go.Bar(
                x=names, y=scores,
                marker_color=cols_c,
                text=scores, textposition="outside",
                textfont=dict(color="#e6edf3"),
            ))
            fig_bar.update_layout(**_pl(height=240, yaxis=dict(range=[0, 105])))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        # ── Suche & Filter ────────────────────────────────────────────────────
        _kt_c1, _kt_c2, _kt_c3 = st.columns([3, 2, 2])
        _kt_suche = _kt_c1.text_input("🔍 Spieler suchen", placeholder="Name …",
                                       key="kt_suche", label_visibility="collapsed")
        _kt_risiko = _kt_c2.selectbox("Risikolevel", ["Alle", "🔴 Hoch", "🟡 Mittel", "🟢 Gering"],
                                       key="kt_risiko")
        _alle_kt_mann = sorted({d["p"].get("mannschaft") or "" for d in player_data if d["p"].get("mannschaft")})
        _kt_mann = _kt_c3.selectbox("Mannschaft", ["Alle"] + _alle_kt_mann, key="kt_mann2")

        rows = []
        for d in player_data:
            p, fms, y, sprint, sprung, agil, aus = (
                d["p"], d["fms"], d["y"], d["sprint"], d["sprung"], d["agil"], d["aus"]
            )
            # Suche & Filter anwenden
            if _kt_suche.strip() and _kt_suche.lower() not in p["name"].lower():
                continue
            _rl = d["level"]
            if _kt_risiko == "🔴 Hoch"   and _rl != "hoch":   continue
            if _kt_risiko == "🟡 Mittel" and _rl != "mittel": continue
            if _kt_risiko == "🟢 Gering" and _rl != "gering": continue
            if _kt_mann != "Alle" and p.get("mannschaft") != _kt_mann: continue

            icon = _RISK_ICON[_rl]
            rows.append({
                "Name":           p["name"],
                "Position":       p.get("hauptposition") or p.get("position") or "—",
                "Mannschaft":     p.get("mannschaft") or "—",
                "Altersklasse":   p.get("altersklasse") or "—",
                "Athletik Score": d["sc"],
                "FMS Score":      fms["score"] if fms else None,
                "Y-Balance Ø":    round((y["composite_rechts"] + y["composite_links"]) / 2, 1)
                                  if y else None,
                "Sprint 10m (s)": sprint["beste_10m"] if sprint and sprint.get("beste_10m") else None,
                "CMJ (cm)":       sprung["cmj_beid"] if sprung and sprung.get("cmj_beid") else None,
                "VO₂max":         aus["vo2max"] if aus and aus.get("vo2max") else None,
                "Risiko":         f"{icon} {_rl.capitalize()}",
            })
        _df_kt = pd.DataFrame(rows)
        if not _df_kt.empty:
            st.dataframe(
                _df_kt,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Athletik Score": st.column_config.ProgressColumn(
                        "Athletik Score", min_value=0, max_value=100, format="%d"),
                    "FMS Score":      st.column_config.NumberColumn("FMS Score", format="%d / 21"),
                    "Y-Balance Ø":    st.column_config.NumberColumn("Y-Balance Ø", format="%.1f %%"),
                    "Sprint 10m (s)": st.column_config.NumberColumn("Sprint 10m (s)", format="%.2f s"),
                    "CMJ (cm)":       st.column_config.NumberColumn("CMJ (cm)", format="%.0f cm"),
                    "VO₂max":         st.column_config.NumberColumn("VO₂max", format="%.1f"),
                },
            )
            st.caption(f"{len(rows)} von {total} Spielern angezeigt.")
        else:
            st.info("Keine Spieler für die gewählten Filter.")

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

def _render_inline_edit_form(sp: dict) -> None:
    """Inline-Bearbeitungsformular für einen Spieler direkt in der Spielerliste."""
    _sid = sp["id"]
    _vn_def = sp.get("vorname") or (sp["name"].split()[0] if " " in sp["name"] else sp["name"])
    _nn_def = sp.get("nachname") or (" ".join(sp["name"].split()[1:]) if " " in sp["name"] else "")

    st.markdown(
        '<div style="background:#161b22;border:1px solid #388bfd44;'
        'border-left:3px solid #388bfd;border-radius:8px;padding:16px 20px;margin:6px 0 14px 0">',
        unsafe_allow_html=True,
    )
    st.markdown(f"##### ✏️ {sp['name']} bearbeiten")

    st.markdown("**👤 Persönliche Daten**")
    _c1, _c2 = st.columns(2)
    _e_vn    = _c1.text_input("Vorname *",                    value=_vn_def,                     key=f"il_vn_{_sid}")
    _e_nn    = _c2.text_input("Nachname *",                   value=_nn_def,                     key=f"il_nn_{_sid}")
    _e_geb   = _c1.text_input("Geburtsdatum (TT.MM.JJJJ) *", value=sp.get("geburtsdatum") or "", key=f"il_geb_{_sid}")
    _gi      = ["Männlich", "Weiblich", "Divers"].index(sp.get("geschlecht", "Männlich")) \
               if sp.get("geschlecht") in ["Männlich", "Weiblich", "Divers"] else 0
    _e_gesch = _c2.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"],
                              index=_gi, key=f"il_gesch_{_sid}")
    _e_alter = berechne_alter(_e_geb)
    _e_ak_vs = altersklasse_vorschlag(_e_geb)
    if _e_alter:
        _c1.markdown(f"<small style='color:#3fb950'>Alter: **{_e_alter} Jahre** — Vorschlag: {_e_ak_vs}</small>",
                     unsafe_allow_html=True)
    _aki  = ALTERSKLASSEN.index(sp.get("altersklasse")) \
            if sp.get("altersklasse") in ALTERSKLASSEN else 7
    _e_ak = _c2.selectbox("Altersklasse", ALTERSKLASSEN, index=_aki, key=f"il_ak_{_sid}")

    st.markdown("**🏟️ Sportliche Daten**")
    _p1, _p2 = st.columns(2)
    _cur_hpos = sp.get("hauptposition") or sp.get("position") or POSITIONEN[0]
    _hpi    = POSITIONEN.index(_cur_hpos) if _cur_hpos in POSITIONEN else 0
    _e_hpos = _p1.selectbox("Hauptposition *", POSITIONEN, index=_hpi, key=f"il_hpos_{_sid}")
    _npl    = ["—"] + POSITIONEN
    _cur_npos = sp.get("nebenposition") or "—"
    _npi    = _npl.index(_cur_npos) if _cur_npos in _npl else 0
    _e_npos = _p2.selectbox("Nebenposition", _npl, index=_npi, key=f"il_npos_{_sid}")
    _sbi    = ["Rechts", "Links", "Beidfüßig"].index(sp.get("spielbein", "Rechts")) \
              if sp.get("spielbein") in ["Rechts", "Links", "Beidfüßig"] else 0
    _e_sb   = _p1.selectbox("Spielbein", ["Rechts", "Links", "Beidfüßig"], index=_sbi, key=f"il_sb_{_sid}")
    _lvi    = LEISTUNGSNIVEAUS.index(sp.get("leistungsniveau", LEISTUNGSNIVEAUS[0])) \
              if sp.get("leistungsniveau") in LEISTUNGSNIVEAUS else 0
    _e_lvl  = _p2.selectbox("Leistungsniveau", LEISTUNGSNIVEAUS, index=_lvi, key=f"il_lvl_{_sid}")

    st.markdown("**🏃 Teamdaten**")
    _t1, _t2 = st.columns(2)
    _e_mann = _t1.text_input("Mannschaft / Verein", value=sp.get("mannschaft") or "", key=f"il_mann_{_sid}")
    _tsi    = TRAININGSSTATUS.index(sp.get("trainingsstatus", TRAININGSSTATUS[0])) \
              if sp.get("trainingsstatus") in TRAININGSSTATUS else 0
    _e_ts   = _t2.selectbox("Trainingsstatus", TRAININGSSTATUS, index=_tsi, key=f"il_ts_{_sid}")

    _ba, _bb = st.columns([3, 1])
    if _ba.button("💾 Speichern", key=f"il_save_{_sid}", type="primary", use_container_width=True):
        if not _e_vn.strip() or not _e_nn.strip():
            st.error("❌ Bitte Vor- und Nachnamen eingeben.")
        else:
            _gok, _gerr = _validate_geburtsdatum(_e_geb)
            if not _gok:
                st.error(f"❌ Ungültiges Geburtsdatum: {_gerr}")
            else:
                spieler_aktualisieren(
                    _sid,
                    _e_vn.strip(), _e_nn.strip(), _e_geb.strip(),
                    _e_gesch, _e_hpos,
                    _e_npos if _e_npos != "—" else "",
                    _e_ak, _e_sb, _e_lvl,
                    _e_mann.strip(), _e_ts,
                )
                st.session_state.pop("inline_edit_id", None)
                _save_ok(f"**{_e_vn} {_e_nn}** wurde aktualisiert.")
                st.rerun()
    if _bb.button("✖️ Abbrechen", key=f"il_cancel_{_sid}", use_container_width=True):
        st.session_state.pop("inline_edit_id", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def page_spieler():
    st.markdown("# 👤 Spielerverwaltung")
    tab_add, tab_list = st.tabs(["➕ Neu anlegen", "📋 Alle Spieler"])

    # ── Tab 1: Neuen Spieler anlegen ──────────────────────────────────────────
    with tab_add:
        st.markdown("### Spieler hinzufügen")

        st.markdown("#### 👤 Persönliche Daten")
        # Zeile 1: Vorname | Nachname  (separate columns-Deklaration → korrekte Reihenfolge auch auf Mobilgeräten)
        _r1c1, _r1c2 = st.columns(2)
        vorname  = _r1c1.text_input("Vorname *",  key="neu_vn")
        nachname = _r1c2.text_input("Nachname *", key="neu_nn")

        # Zeile 2: Geburtsdatum | Geschlecht
        _r2c1, _r2c2 = st.columns(2)
        geburtsdatum = _r2c1.text_input("Geburtsdatum (TT.MM.JJJJ) *",
                                        placeholder="15.03.2008", key="neu_geb")
        geschlecht   = _r2c2.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"], key="neu_gesch")

        # Zeile 3: Alter-Anzeige | Altersklasse
        alter        = berechne_alter(geburtsdatum)
        ak_vorschlag = altersklasse_vorschlag(geburtsdatum)
        _r3c1, _r3c2 = st.columns(2)
        if alter:
            _r3c1.markdown(f"<small style='color:#3fb950'>Alter: **{alter} Jahre** — Vorschlag: {ak_vorschlag}</small>",
                           unsafe_allow_html=True)
        altersklasse = _r3c2.selectbox("Altersklasse", ALTERSKLASSEN,
                                       index=ALTERSKLASSEN.index(ak_vorschlag) if ak_vorschlag in ALTERSKLASSEN else 7,
                                       key="neu_ak")

        st.markdown("#### 🏟️ Sportliche Daten")
        p1, p2 = st.columns(2)
        hauptposition   = p1.selectbox("Hauptposition *", POSITIONEN,              key="neu_hpos")
        nebenposition   = p2.selectbox("Nebenposition",   ["—"] + POSITIONEN,      key="neu_npos")
        spielbein       = p1.selectbox("Spielbein",       ["Rechts", "Links", "Beidfüßig"], key="neu_sb")
        leistungsniveau = p2.selectbox("Leistungsniveau", LEISTUNGSNIVEAUS,        key="neu_lvl")

        st.markdown("#### 🏃 Teamdaten")
        t1, t2 = st.columns(2)
        mannschaft      = t1.text_input("Mannschaft / Verein", key="neu_mann")
        trainingsstatus = t2.selectbox("Trainingsstatus", TRAININGSSTATUS,         key="neu_ts")

        st.markdown("---")
        _check_save_ok()
        if st.button("💾 Spieler speichern", key="neu_save", type="primary", use_container_width=True):
            if not vorname.strip() or not nachname.strip():
                st.error("❌ Bitte Vor- und Nachnamen eingeben.")
            else:
                _geb_ok, _geb_err = _validate_geburtsdatum(geburtsdatum)
                if not _geb_ok:
                    st.error(f"❌ Ungültiges Geburtsdatum: {_geb_err}")
                else:
                    spieler_speichern(
                        vorname.strip(), nachname.strip(), geburtsdatum.strip(),
                        geschlecht, hauptposition,
                        nebenposition if nebenposition != "—" else "",
                        altersklasse, spielbein, leistungsniveau,
                        mannschaft.strip(), trainingsstatus,
                    )
                    _save_ok(f"Spieler **{vorname} {nachname}** wurde gespeichert.")
                    st.rerun()

    # ── Tab 2: Alle Spieler — direkt in der Tabelle bearbeiten ──────────────────
    with tab_list:
        _sp_list = spieler_laden()
        if not _sp_list:
            st.info("Noch keine Spieler vorhanden.")
            return

        # ── Suche & Filter ────────────────────────────────────────────────────
        _sc1, _sc2, _sc3, _sc4 = st.columns([2, 1.5, 1.5, 1.5])
        suche  = _sc1.text_input("🔍 Suchen", placeholder="Name oder Mannschaft …",
                                 key="spieler_suche", label_visibility="collapsed")
        _alle_mann = ["Alle Mannschaften"] + sorted(
            {p.get("mannschaft") or "" for p in _sp_list if p.get("mannschaft")})
        _alle_ak   = ["Alle Klassen"] + ALTERSKLASSEN
        _alle_pos  = ["Alle Positionen"] + POSITIONEN
        f_mann = _sc2.selectbox("Mannschaft",   _alle_mann, key="f_mann", label_visibility="collapsed")
        f_ak   = _sc3.selectbox("Altersklasse", _alle_ak,   key="f_ak",   label_visibility="collapsed")
        f_pos  = _sc4.selectbox("Position",     _alle_pos,  key="f_pos",  label_visibility="collapsed")

        gefiltert = _sp_list
        if suche.strip():
            _s = suche.lower()
            gefiltert = [p for p in gefiltert if
                         _s in p["name"].lower() or
                         _s in (p.get("mannschaft") or "").lower() or
                         _s in (p.get("hauptposition") or p.get("position") or "").lower()]
        if f_mann != "Alle Mannschaften":
            gefiltert = [p for p in gefiltert if p.get("mannschaft") == f_mann]
        if f_ak != "Alle Klassen":
            gefiltert = [p for p in gefiltert if p.get("altersklasse") == f_ak]
        if f_pos != "Alle Positionen":
            gefiltert = [p for p in gefiltert if
                         p.get("hauptposition") == f_pos or p.get("position") == f_pos]

        if not gefiltert:
            st.info("Keine Spieler gefunden.")
        else:
            # ── DataFrame aufbauen ────────────────────────────────────────────
            def _vn(p):
                return p.get("vorname") or (p["name"].split()[0] if p.get("name") else "")
            def _nn(p):
                parts = p["name"].split() if p.get("name") else []
                return p.get("nachname") or (" ".join(parts[1:]) if len(parts) > 1 else "")

            _df_spieler = pd.DataFrame([{
                "_id":             p["id"],
                "Vorname":         _vn(p),
                "Nachname":        _nn(p),
                "Geburtsdatum":    p.get("geburtsdatum") or "",
                "Geschlecht":      p.get("geschlecht") or "Männlich",
                "Hauptposition":   p.get("hauptposition") or p.get("position") or POSITIONEN[0],
                "Nebenposition":   p.get("nebenposition") or "—",
                "Altersklasse":    p.get("altersklasse") or ALTERSKLASSEN[7],
                "Spielbein":       p.get("spielbein") or "Rechts",
                "Leistungsniveau": p.get("leistungsniveau") or LEISTUNGSNIVEAUS[0],
                "Mannschaft":      p.get("mannschaft") or "",
                "Trainingsstatus": p.get("trainingsstatus") or TRAININGSSTATUS[0],
            } for p in gefiltert])

            _edited = st.data_editor(
                _df_spieler,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="spieler_data_editor",
                column_config={
                    "_id":             None,
                    "Vorname":         st.column_config.TextColumn("Vorname", required=True),
                    "Nachname":        st.column_config.TextColumn("Nachname", required=True),
                    "Geburtsdatum":    st.column_config.TextColumn("Geburtsdatum", help="Format: TT.MM.JJJJ"),
                    "Geschlecht":      st.column_config.SelectboxColumn("Geschlecht",
                                           options=["Männlich", "Weiblich", "Divers"]),
                    "Hauptposition":   st.column_config.SelectboxColumn("Hauptposition",
                                           options=POSITIONEN, required=True),
                    "Nebenposition":   st.column_config.SelectboxColumn("Nebenposition",
                                           options=["—"] + POSITIONEN),
                    "Altersklasse":    st.column_config.SelectboxColumn("Altersklasse",
                                           options=ALTERSKLASSEN, required=True),
                    "Spielbein":       st.column_config.SelectboxColumn("Spielbein",
                                           options=["Rechts", "Links", "Beidfüßig"]),
                    "Leistungsniveau": st.column_config.SelectboxColumn("Leistungsniveau",
                                           options=LEISTUNGSNIVEAUS),
                    "Mannschaft":      st.column_config.TextColumn("Mannschaft"),
                    "Trainingsstatus": st.column_config.SelectboxColumn("Trainingsstatus",
                                           options=TRAININGSSTATUS),
                },
                disabled=["_id"],
            )

            # ── Speichern ─────────────────────────────────────────────────────
            _editor_state = st.session_state.get("spieler_data_editor") or {}
            _edited_rows  = _editor_state.get("edited_rows") or {}
            _n_changes    = len(_edited_rows)

            _sa, _sb = st.columns([4, 1])
            if _n_changes:
                _sa.caption(f"✏️ {_n_changes} Zeile(n) geändert — bitte speichern.")
            else:
                _sa.caption(f"{len(gefiltert)} von {len(_sp_list)} Spieler "
                            "· Zelle anklicken zum Bearbeiten")

            if _sb.button("💾 Speichern", type="primary", use_container_width=True,
                          disabled=(_n_changes == 0), key="spl_save_btn"):
                _saved = 0
                for _ridx in _edited_rows:
                    _row  = _edited.iloc[int(_ridx)]
                    _geb  = str(_row["Geburtsdatum"]).strip() if _row["Geburtsdatum"] else ""
                    _ok, _err = _validate_geburtsdatum(_geb)
                    if not _ok:
                        st.error(f"❌ Zeile {int(_ridx)+1}: {_err}")
                        continue
                    _npos = str(_row["Nebenposition"])
                    spieler_aktualisieren(
                        int(_row["_id"]),
                        str(_row["Vorname"]).strip(),
                        str(_row["Nachname"]).strip(),
                        _geb,
                        str(_row["Geschlecht"]),
                        str(_row["Hauptposition"]),
                        _npos if _npos != "—" else "",
                        str(_row["Altersklasse"]),
                        str(_row["Spielbein"]),
                        str(_row["Leistungsniveau"]),
                        str(_row["Mannschaft"]).strip(),
                        str(_row["Trainingsstatus"]),
                    )
                    _saved += 1
                if _saved:
                    _save_ok(f"{_saved} Spieler aktualisiert.")
                    st.rerun()

        # ── Spieler löschen ───────────────────────────────────────────────────
        st.markdown("---")
        with st.expander("🗑️ Spieler löschen"):
            namen_lst = [p["name"] for p in gefiltert] if gefiltert else []
            loeschen_auswahl = st.multiselect(
                "Spieler auswählen (Mehrfachauswahl möglich)",
                namen_lst, key="multi_del",
            )
            if loeschen_auswahl:
                n_del = len(loeschen_auswahl)
                st.warning(
                    f"⚠️ {'Dieser Spieler wird' if n_del == 1 else f'Diese {n_del} Spieler werden'} "
                    "zusammen mit allen Testdaten unwiderruflich gelöscht."
                )
                _btn_label = (f"🗑️ {loeschen_auswahl[0]} endgültig löschen"
                              if n_del == 1 else f"🗑️ {n_del} Spieler endgültig löschen")
                if st.button(_btn_label, type="primary", key="multi_del_btn"):
                    ids_loeschen = [p["id"] for p in _sp_list if p["name"] in loeschen_auswahl]
                    for pid in ids_loeschen:
                        spieler_loeschen(pid)
                    if n_del == 1:
                        _save_ok(f"**{loeschen_auswahl[0]}** wurde gelöscht.")
                    else:
                        _save_ok(f"{n_del} Spieler wurden gelöscht.")
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────

def _duplikat_check(key_pfx: str, datum_str: str, hist: list) -> str:
    """Prüft ob für diesen Spieler bereits ein Test am gleichen Datum existiert.

    Returns: 'speichern' | 'zweiter' | 'abbrechen'
    """
    if not hist:
        return "speichern"
    existing = any(
        (r.get("datum") if isinstance(r, dict) else (r[0] if r else "")) == datum_str
        for r in hist
    )
    if not existing:
        return "speichern"
    wahl = st.radio(
        "⚠️ Für diesen Spieler existiert bereits ein Test an diesem Datum.",
        ["Bestehenden Test überschreiben", "Als zweiten Test speichern", "Abbrechen"],
        key=f"_dup_{key_pfx}",
        horizontal=True,
    )
    if "zweiten" in wahl:
        return "zweiter"
    if "Abbrechen" in wahl:
        return "abbrechen"
    return "speichern"


# ──────────────────────────────────────────────────────────────────────────────

def page_fms():
    st.markdown("# 📝 FMS — Functional Movement Screen")
    st.markdown("Sieben Bewegungsmuster werden bilateral getestet. Maximalpunktzahl: **21 Punkte**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("fms")
    show_test_info("fms")
    _anleitung_download_button("fms")

    auswahl = _player_selector("fms")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    _fms_sp = spieler_by_id(spieler_id)
    _fms_alter = berechne_alter(_fms_sp.get("geburtsdatum", "") if _fms_sp else None)
    _fms_geschl = _fms_sp.get("geschlecht", "Männlich") if _fms_sp else "Männlich"

    tab_neu, tab_letzter, tab_verlauf = st.tabs(["📋 Neuer Test", "📂 Letzter Test", "📈 Verlauf"])

    # ── Tab 1: Neuer Test ─────────────────────────────────────────────────────
    with tab_neu:
        st.markdown("---")
        st.markdown("### Testergebnisse eingeben")
        st.caption("Bewertung: 3 = korrekt | 2 = mit Kompensation | 1 = nicht möglich | 0 = Schmerzen. ℹ️ Tooltip an jedem Feld für Details.")

        _fh = lambda fid: show_field_help("fms", fid)

        def _fms_row(nr, label, key_l, key_r, fid):
            lbl_col, info_col = st.columns([8, 1])
            lbl_col.markdown(f"**{nr} · {label}**")
            field_info_col(info_col, "fms", fid)
            _cl, _cr = st.columns(2)
            l_val = _cl.number_input("Links",  0, 3, key=key_l, help=_fh(fid))
            r_val = _cr.number_input("Rechts", 0, 3, key=key_r, help=_fh(fid))
            norm_badge(l_val, "fms", fid, _cl)
            norm_badge(r_val, "fms", fid, _cr)
            asym_html = fms_asymmetrie_badge_html(l_val, r_val)
            if asym_html:
                st.markdown(asym_html, unsafe_allow_html=True)
            return l_val, r_val

        ds_lbl, ds_info = st.columns([8, 1])
        ds_lbl.markdown("**1 · Deep Squat** — ein Score (kein L/R)")
        field_info_col(ds_info, "fms", "deep_squat")
        _c1, _gap = st.columns([2, 4])
        deep = _c1.number_input("Punkte", 0, 3, key="ds", help=_fh("deep_squat"))
        norm_badge(deep, "fms", "deep_squat", _c1)

        st.markdown("---")
        st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
        hurdle_l, hurdle_r     = _fms_row(2, "Hurdle Step",       "hl",  "hr",  "hurdle_step")
        inline_l, inline_r     = _fms_row(3, "Inline Lunge",      "il",  "ir",  "inline_lunge")
        shoulder_l, shoulder_r = _fms_row(4, "Shoulder Mobility", "shl", "shr", "shoulder")
        aslr_l, aslr_r         = _fms_row(5, "ASLR",              "al",  "ar",  "aslr")

        st.markdown("---")
        ts_lbl, ts_info = st.columns([8, 1])
        ts_lbl.markdown("**6 · Trunk Stability Push-up** — ein Score (kein L/R)")
        field_info_col(ts_info, "fms", "trunk_stability")
        _c6, _gap6 = st.columns([2, 4])
        trunk = _c6.number_input("Punkte", 0, 3, key="ts", help=_fh("trunk_stability"))
        norm_badge(trunk, "fms", "trunk_stability", _c6)

        st.markdown("---")
        st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
        rotary_l, rotary_r     = _fms_row(7, "Rotary Stability",  "rl",  "rr",  "rotary_stability")

        st.markdown("---")
        obs_fms = render_observation_selector("fms", spieler_id, date.today().strftime("%d.%m.%Y"), "fms", standalone=False)
        _dup_fms = _duplikat_check("fms", str(date.today()), fms_history(spieler_id))

        if st.button("✅ FMS speichern & auswerten", use_container_width=True, type="primary"):
            if _dup_fms == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            import json as _j, datetime as _dtm
            _datum_fms = str(date.today())
            if _dup_fms == "zweiter":
                _datum_fms += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
            result = FMSResult(
                deep_squat=deep, hurdle_l=hurdle_l, hurdle_r=hurdle_r,
                inline_l=inline_l, inline_r=inline_r,
                shoulder_l=shoulder_l, shoulder_r=shoulder_r,
                aslr_l=aslr_l, aslr_r=aslr_r, trunk=trunk,
                rotary_l=rotary_l, rotary_r=rotary_r,
                alter=_fms_alter,
            )
            fms_speichern(
                spieler_id, _datum_fms,
                deep, hurdle_l, hurdle_r, inline_l, inline_r,
                shoulder_l, shoulder_r, aslr_l, aslr_r, trunk, rotary_l, rotary_r,
                result.score, result.bewertung, result.asymmetrie, result.schwerpunkt,
            )
            if obs_fms["beob_ids"] or obs_fms.get("freitext"):
                beobachtung_speichern(
                    spieler_id, "fms", _datum_fms,
                    _j.dumps(obs_fms["beob_ids"], ensure_ascii=False),
                    obs_fms["seite"], obs_fms["auspraegung"],
                    obs_fms["freitext"], obs_fms["text_generiert"],
                )
            st.success("✅ FMS Test gespeichert!")
            st.markdown("---")
            st.markdown("### Ergebnis")
            m1, m2, m3 = st.columns(3)
            m1.metric("Gesamtscore", f"{result.score} / 21")
            m2.metric("Bewertung", result.bewertung)
            m3.metric("Risikostufe", result.risiko_level.capitalize())
            from age_norms import normgruppe_label as _ngl
            st.caption(f"📊 {_ngl(_fms_alter)}")
            # ── Kurze Beurteilung ──────────────────────────────────────
            from fms import fms_bewertung_kurz as _fms_bkurz
            _fms_bw_clr = {"Ausgezeichnet": "#3fb950", "Gut": "#3fb950",
                           "Beobachten": "#d29922", "Aktionsbedarf": "#f85149"}
            _fms_bc = _fms_bw_clr.get(result.bewertung, "#8b949e")
            st.markdown(
                f'<div style="background:#161b22;border-left:4px solid {_fms_bc};'
                f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0">'
                f'<span style="color:{_fms_bc};font-weight:700">{result.bewertung}</span>'
                f'<span style="color:#8b949e;font-size:12px;margin-left:10px">{result.score}/21 Punkte</span><br>'
                f'<small style="color:#c9d1d9">{_fms_bkurz(result.score)}</small></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Pattern-Scores")
            for name, val in result.pattern_scores.items():
                col = _color_for_score(val, 3)
                st.markdown(f"**{name}** — {val}/3 {_progress_html(val, 3, col)}", unsafe_allow_html=True)
            st.info(f"**Trainingsschwerpunkt:** {result.schwerpunkt}")
            if result.asymmetrie != "Keine Asymmetrie":
                st.warning(f"⚠️ {result.asymmetrie}")

    # ── Tab 2: Letzter Test — alle 13 Einzelbewertungen ──────────────────────
    with tab_letzter:
        last = fms_letzter(spieler_id)
        if not last:
            st.info("Noch kein FMS-Test gespeichert.")
        else:
            lm1, lm2, lm3 = st.columns(3)
            lm1.metric("Gesamtscore", f"{last.get('score', 0)} / 21")
            lm2.metric("Bewertung",   last.get("bewertung", "—"))
            lm3.metric("Datum",       last.get("datum", "—"))
            # ── Kurze Beurteilung ──────────────────────────────────────────────
            from fms import fms_bewertung_kurz as _fms_bkurz2
            _fms_bw_clr2 = {"Ausgezeichnet": "#3fb950", "Gut": "#3fb950",
                             "Beobachten": "#d29922", "Aktionsbedarf": "#f85149"}
            _fms_bc2 = _fms_bw_clr2.get(last.get("bewertung", ""), "#8b949e")
            st.markdown(
                f'<div style="background:#161b22;border-left:4px solid {_fms_bc2};'
                f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0">'
                f'<span style="color:{_fms_bc2};font-weight:700">{last.get("bewertung","—")}</span>'
                f'<span style="color:#8b949e;font-size:12px;margin-left:10px">{last.get("score",0)}/21 Punkte</span><br>'
                f'<small style="color:#c9d1d9">{_fms_bkurz2(last.get("score"))}</small></div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown("#### Einzelbewertungen")
            _SC = {3: "#3fb950", 2: "#d29922", 1: "#f0883e", 0: "#f85149"}
            _FMS_EINZEL = [
                ("1 · Deep Squat",          last.get("deep_squat"),    None),
                ("2 · Hurdle Step",          last.get("hurdle_links"),  last.get("hurdle_rechts")),
                ("3 · Inline Lunge",         last.get("inline_links"),  last.get("inline_rechts")),
                ("4 · Shoulder Mobility",    last.get("shoulder_links"),last.get("shoulder_rechts")),
                ("5 · ASLR",                 last.get("aslr_links"),    last.get("aslr_rechts")),
                ("6 · Trunk Stability",      last.get("trunk"),         None),
                ("7 · Rotary Stability",     last.get("rotary_links"),  last.get("rotary_rechts")),
            ]
            for tname, lv, rv in _FMS_EINZEL:
                ca, cb, cc, cd = st.columns([3, 1, 1, 1])
                ca.markdown(f"**{tname}**")
                if rv is None:
                    v = int(lv or 0)
                    cb.markdown(f'<span style="color:{_SC.get(v,"#8b949e")};font-weight:700;font-size:1.15em">{v}</span> / 3', unsafe_allow_html=True)
                else:
                    lval = int(lv or 0); rval = int(rv or 0)
                    cb.markdown(f'L: <span style="color:{_SC.get(lval,"#8b949e")};font-weight:700">{lval}</span>/3', unsafe_allow_html=True)
                    cc.markdown(f'R: <span style="color:{_SC.get(rval,"#8b949e")};font-weight:700">{rval}</span>/3', unsafe_allow_html=True)
                    if lval != rval:
                        cd.markdown("⚠️ Asymm.")
            st.markdown("---")
            st.write("**Asymmetrie:**", last.get("asymmetrie") or "—")
            st.write("**Trainingsschwerpunkt:**", last.get("schwerpunkt") or "—")

    # ── Tab 3: Verlauf ────────────────────────────────────────────────────────
    with tab_verlauf:
        hist_full = fms_history_full(spieler_id)
        if not hist_full:
            st.info("Noch keine FMS-Tests vorhanden.")
        else:
            df_fms = pd.DataFrame([{
                "Datum":       r["datum"],
                "Deep Squat":  int(r.get("deep_squat") or 0),
                "Hurdle L":    int(r.get("hurdle_links") or 0),
                "Hurdle R":    int(r.get("hurdle_rechts") or 0),
                "Inline L":    int(r.get("inline_links") or 0),
                "Inline R":    int(r.get("inline_rechts") or 0),
                "Shoulder L":  int(r.get("shoulder_links") or 0),
                "Shoulder R":  int(r.get("shoulder_rechts") or 0),
                "ASLR L":      int(r.get("aslr_links") or 0),
                "ASLR R":      int(r.get("aslr_rechts") or 0),
                "Trunk":       int(r.get("trunk") or 0),
                "Rotary L":    int(r.get("rotary_links") or 0),
                "Rotary R":    int(r.get("rotary_rechts") or 0),
                "Gesamtscore": int(r.get("score") or 0),
                "Bewertung":   r.get("bewertung") or "—",
            } for r in hist_full])

            # Gesamtscore-Kurve
            fig_score = go.Figure()
            fig_score.add_trace(go.Scatter(
                x=df_fms["Datum"], y=df_fms["Gesamtscore"],
                mode="lines+markers+text", text=df_fms["Gesamtscore"],
                textposition="top center",
                line=dict(color="#3b82f6", width=3), marker=dict(size=9),
            ))
            fig_score.add_hline(y=14, line_dash="dash", line_color="#d29922",
                                annotation_text="Schwellenwert 14")
            fig_score.update_layout(**_pl(height=280, title="FMS Gesamtscore"))
            st.plotly_chart(fig_score, use_container_width=True)

            # Einzelwerte-Verlauf
            with st.expander("📊 Einzelwerte-Verlauf anzeigen"):
                _ecolors = ["#3b82f6","#3fb950","#56d364","#d29922","#e3b341",
                            "#f85149","#ff7b72","#58a6ff","#79c0ff","#a371f7","#f0883e","#ffa657"]
                _ecols   = ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                            "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R"]
                fig_e = go.Figure()
                for col_n, clr in zip(_ecols, _ecolors):
                    fig_e.add_trace(go.Scatter(
                        x=df_fms["Datum"], y=df_fms[col_n],
                        mode="lines+markers", name=col_n,
                        line=dict(color=clr, width=2),
                    ))
                fig_e.update_layout(**_pl(height=350, title="FMS Einzelbewertungen"))
                st.plotly_chart(fig_e, use_container_width=True)

            # Zwei Testtermine vergleichen
            daten = df_fms["Datum"].tolist()
            if len(daten) >= 2:
                with st.expander("⚖️ Zwei Testtermine vergleichen"):
                    vc1, vc2 = st.columns(2)
                    d_alt = vc1.selectbox("Älterer Termin", daten, index=0, key="fms_vgl_alt")
                    d_neu = vc2.selectbox("Neuerer Termin", daten, index=len(daten)-1, key="fms_vgl_neu")
                    if d_alt != d_neu:
                        r_alt = df_fms[df_fms["Datum"] == d_alt].iloc[0]
                        r_neu = df_fms[df_fms["Datum"] == d_neu].iloc[0]
                        _vcols = ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                                  "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R","Gesamtscore"]
                        vgl_rows = []
                        for c in _vcols:
                            v1 = int(r_alt[c]); v2 = int(r_neu[c]); delta = v2 - v1
                            vgl_rows.append({"Merkmal": c, d_alt: v1, d_neu: v2,
                                             "Δ": f"+{delta}" if delta > 0 else str(delta)})
                        st.dataframe(pd.DataFrame(vgl_rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("Bitte zwei verschiedene Testtermine auswählen.")

            # Volltabelle
            st.markdown("---")
            st.markdown("##### Alle Tests")
            show_cols = ["Datum","Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                         "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R","Gesamtscore","Bewertung"]
            _df_fms_show = _datum_filter(df_fms[show_cols].copy(), "fms_voll")
            st.dataframe(
                _df_fms_show,
                use_container_width=True, hide_index=True,
                column_config={
                    "Gesamtscore": st.column_config.NumberColumn("Gesamtscore", format="%d / 21"),
                    **{c: st.column_config.NumberColumn(c, format="%d") for c in
                       ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                        "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R"]},
                },
            )


# ──────────────────────────────────────────────────────────────────────────────

def page_ybalance():
    st.markdown("# 📏 Y-Balance Test")
    st.markdown("Composite Score = (A + PM + PL) / (3 × Beinlänge) × 100.  Schwellenwert: **≥ 89 %**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("y_balance")
    show_test_info("y_balance")
    _anleitung_download_button("y_balance")

    auswahl = _player_selector("yb")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    _yb_sp = spieler_by_id(spieler_id)
    _yb_alter = berechne_alter(_yb_sp.get("geburtsdatum", "") if _yb_sp else None)
    _yb_geschl = _yb_sp.get("geschlecht", "Männlich") if _yb_sp else "Männlich"

    tab_neu, tab_letzter, tab_verlauf = st.tabs(["📋 Neuer Test", "📂 Letzter Test", "📈 Verlauf"])

    # ── Tab 1: Neuer Test ─────────────────────────────────────────────────────
    with tab_neu:
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

        st.markdown("---")
        obs_yb = render_observation_selector("y_balance", spieler_id, date.today().strftime("%d.%m.%Y"), "yb", standalone=False)
        _dup_yb = _duplikat_check("yb", str(date.today()), y_balance_history(spieler_id))

        _yb_warns = []
        if bein_r > 0:
            for _val, _lbl in [(ant_r, "Anterior R"), (pm_r, "Posteromedial R"), (pl_r, "Posterolateral R")]:
                if _val > bein_r * 1.3:
                    _yb_warns.append(f"{_lbl} ({_val:.1f} cm > 130 % Beinlänge R)")
        if bein_l > 0:
            for _val, _lbl in [(ant_l, "Anterior L"), (pm_l, "Posteromedial L"), (pl_l, "Posterolateral L")]:
                if _val > bein_l * 1.3:
                    _yb_warns.append(f"{_lbl} ({_val:.1f} cm > 130 % Beinlänge L)")
        if bein_r > 0 and bein_l > 0 and abs(bein_r - bein_l) > 5:
            _yb_warns.append(f"Beinlängendifferenz R/L: {abs(bein_r - bein_l):.1f} cm — bitte prüfen")
        if _yb_warns:
            st.warning("⚠️ Ungewöhnliche Werte — bitte Eingaben prüfen (Speichern trotzdem möglich):\n"
                       + "\n".join(f"• {w}" for w in _yb_warns))

        if st.button("💾 Y-Balance berechnen & speichern", type="primary", use_container_width=True):
            if _dup_yb == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            import json as _j, datetime as _dtm
            _datum_yb = str(date.today())
            if _dup_yb == "zweiter":
                _datum_yb += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
            res = YBalanceResult(
                anterior_r=ant_r, anterior_l=ant_l,
                posteromedial_r=pm_r, posteromedial_l=pm_l,
                posterolateral_r=pl_r, posterolateral_l=pl_l,
                beinlaenge_r=bein_r, beinlaenge_l=bein_l,
                alter=_yb_alter,
            )
            y_balance_speichern(
                spieler_id, _datum_yb,
                ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
                res.diff_anterior, res.diff_posteromedial, res.diff_posterolateral,
                res.composite_r, res.composite_l,
                res.asymmetrie_text, res.schwerpunkt,
            )
            if obs_yb["beob_ids"] or obs_yb.get("freitext"):
                beobachtung_speichern(
                    spieler_id, "y_balance", _datum_yb,
                    _j.dumps(obs_yb["beob_ids"], ensure_ascii=False),
                    obs_yb["seite"], obs_yb["auspraegung"],
                    obs_yb["freitext"], obs_yb["text_generiert"],
                )
            _save_ok(f"Y-Balance Test gespeichert! — Composite R: {res.composite_r} % | L: {res.composite_l} %")
            st.rerun()

    # ── Tab 2: Letzter Test — alle Einzelwerte ───────────────────────────────
    with tab_letzter:
        last = y_balance_letzter(spieler_id)
        if not last:
            st.info("Noch kein Y-Balance-Test gespeichert.")
        else:
            lm1, lm2, lm3 = st.columns(3)
            lm1.metric("Composite Rechts", f"{last.get('composite_rechts','—')} %")
            lm2.metric("Composite Links",  f"{last.get('composite_links','—')} %")
            lm3.metric("Datum", last.get("datum","—"))
            st.markdown("---")
            st.markdown("#### Reichweiten")
            rc1, rc2 = st.columns(2)
            rc1.markdown("**Rechts**")
            rc2.markdown("**Links**")
            for _lbl, _rk, _lk in [
                ("Anterior",      "anterior_rechts",      "anterior_links"),
                ("Posteromedial", "posteromedial_rechts", "posteromedial_links"),
                ("Posterolateral","posterolateral_rechts","posterolateral_links"),
            ]:
                rc1.markdown(f"**{_lbl}:** {last.get(_rk,'—')} cm")
                rc2.markdown(f"**{_lbl}:** {last.get(_lk,'—')} cm")
            st.markdown("---")
            st.markdown("#### Seitendifferenzen")
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Δ Anterior",      f"{last.get('diff_anterior','—')} cm")
            dc2.metric("Δ Posteromedial", f"{last.get('diff_posteromedial','—')} cm")
            dc3.metric("Δ Posterolateral",f"{last.get('diff_posterolateral','—')} cm")
            st.markdown("---")
            st.write("**Asymmetrie:**",          last.get("asymmetrie") or "—")
            st.write("**Trainingsschwerpunkt:**", last.get("schwerpunkt") or "—")

    # ── Tab 3: Verlauf ────────────────────────────────────────────────────────
    with tab_verlauf:
        hist_yb = y_balance_history_full(spieler_id)
        if not hist_yb:
            st.info("Noch keine Y-Balance-Tests vorhanden.")
        else:
            df_yb = pd.DataFrame([{
                "Datum":           r["datum"],
                "Composite R (%)": round(float(r.get("composite_rechts") or 0), 1),
                "Composite L (%)": round(float(r.get("composite_links")  or 0), 1),
                "Ant R":           float(r.get("anterior_rechts")       or 0),
                "Ant L":           float(r.get("anterior_links")        or 0),
                "PM R":            float(r.get("posteromedial_rechts")  or 0),
                "PM L":            float(r.get("posteromedial_links")   or 0),
                "PL R":            float(r.get("posterolateral_rechts") or 0),
                "PL L":            float(r.get("posterolateral_links")  or 0),
                "Asymmetrie":      r.get("asymmetrie") or "—",
                "Schwerpunkt":     r.get("schwerpunkt") or "—",
            } for r in hist_yb])

            # Composite-Score-Kurve
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb["Composite R (%)"],
                mode="lines+markers", name="Composite Rechts", line=dict(color="#3b82f6", width=3)))
            fig_comp.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb["Composite L (%)"],
                mode="lines+markers", name="Composite Links",  line=dict(color="#f85149", width=3)))
            fig_comp.add_hline(y=89, line_dash="dash", line_color="#d29922",
                               annotation_text="Schwellenwert 89 %")
            fig_comp.update_layout(**_pl(height=280, title="Y-Balance Composite Scores"))
            st.plotly_chart(fig_comp, use_container_width=True)

            # Einzelrichtungen
            with st.expander("📊 Einzelrichtungen-Verlauf anzeigen"):
                fig_dir = go.Figure()
                for col_n, clr in [
                    ("Ant R","#3b82f6"),("Ant L","#79c0ff"),
                    ("PM R","#3fb950"),("PM L","#56d364"),
                    ("PL R","#f85149"),("PL L","#ffa657"),
                ]:
                    fig_dir.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb[col_n],
                        mode="lines+markers", name=col_n, line=dict(color=clr, width=2)))
                fig_dir.update_layout(**_pl(height=320, title="Reichweiten pro Richtung (cm)"))
                st.plotly_chart(fig_dir, use_container_width=True)

            # Zwei Testtermine vergleichen
            daten_yb = df_yb["Datum"].tolist()
            if len(daten_yb) >= 2:
                with st.expander("⚖️ Zwei Testtermine vergleichen"):
                    yvc1, yvc2 = st.columns(2)
                    yd_alt = yvc1.selectbox("Älterer Termin", daten_yb, index=0, key="yb_vgl_alt")
                    yd_neu = yvc2.selectbox("Neuerer Termin", daten_yb, index=len(daten_yb)-1, key="yb_vgl_neu")
                    if yd_alt != yd_neu:
                        yr_alt = df_yb[df_yb["Datum"] == yd_alt].iloc[0]
                        yr_neu = df_yb[df_yb["Datum"] == yd_neu].iloc[0]
                        _yvcols = ["Composite R (%)","Composite L (%)","Ant R","Ant L","PM R","PM L","PL R","PL L"]
                        yvgl = []
                        for c in _yvcols:
                            v1 = yr_alt[c]; v2 = yr_neu[c]; d = round(v2-v1, 1)
                            yvgl.append({"Merkmal":c, yd_alt: v1, yd_neu: v2, "Δ": f"+{d}" if d > 0 else str(d)})
                        st.dataframe(pd.DataFrame(yvgl), use_container_width=True, hide_index=True)
                    else:
                        st.info("Bitte zwei verschiedene Testtermine auswählen.")

            # Volltabelle
            st.markdown("---")
            st.markdown("##### Alle Tests")
            _df_yb_show = df_yb[["Datum","Composite R (%)","Composite L (%)","Ant R","Ant L",
                                   "PM R","PM L","PL R","PL L","Asymmetrie","Schwerpunkt"]].copy()
            _df_yb_show = _datum_filter(_df_yb_show, "yb_voll")
            st.dataframe(
                _df_yb_show,
                use_container_width=True, hide_index=True,
                column_config={
                    "Composite R (%)": st.column_config.NumberColumn("Composite R (%)", format="%.1f %%"),
                    "Composite L (%)": st.column_config.NumberColumn("Composite L (%)", format="%.1f %%"),
                    "Asymmetrie":      st.column_config.NumberColumn("Asymmetrie", format="%.1f %%"),
                    **{c: st.column_config.NumberColumn(c, format="%.1f cm")
                       for c in ["Ant R","Ant L","PM R","PM L","PL R","PL L"]},
                },
            )


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
    kraft  = kraft_letzter(sid)
    anthro      = anthropometrie_letzter(sid)
    anthro_hist = anthropometrie_history(sid)
    verlet = verletzungen_laden(sid)
    rs     = risiko_score(fms, y, verlet)
    label, level = risiko_label(rs)
    ascore   = athletik_score(fms, y, sprint, sprung, agil, aus)
    defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro)
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus, kraft_row=kraft_letzter(sid))
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

    # ── Schnellaktionen ────────────────────────────────────────────────────
    _btn_a, _btn_b, _ = st.columns([2, 2, 3])
    with _btn_a:
        if st.button("⚖️ Mit anderem Spieler vergleichen",
                     key="profil_goto_vergleich",
                     use_container_width=True):
            st.session_state["vergl_preset_pid"] = sid
            st.session_state["_nav_goto"] = "⚖️  Vergleich"
            st.rerun()
    with _btn_b:
        # Kein Cache — damit Änderungen (neue Tests, neue Verletzungen) sofort
        # im Export sichtbar sind und keine veralteten Daten ausgeliefert werden.
        _xlsx = spieler_excel_bytes(sid)
        _name_safe = auswahl["name"].replace(" ", "_")
        st.download_button(
            label="⬇️ Spieler exportieren (Excel)",
            data=_xlsx,
            file_name=f"Spieler_{_name_safe}_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="profil_xlsx_dl",
        )

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
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin")},
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

    # ── Anthropometrie-Karte ───────────────────────────────────────────────
    ak_col, ak_btn_col = st.columns([5, 1])
    with ak_col:
        st.markdown(anthro_karte(anthro), unsafe_allow_html=True)
    with ak_btn_col:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("📐 Messen →", key="profil_goto_anthro", use_container_width=True):
            st.session_state["_nav_goto"]              = "👤  Spieler"
            st.session_state["_nav_sub_spieler_goto"]  = "📐 Anthropometrie"
            st.rerun()

    # ── Anthropometrie-Verlauf (nur bei ≥ 2 Messungen) ────────────────────
    if len(anthro_hist) >= 2:
        df_ah = pd.DataFrame(anthro_hist)
        # Metric selector (compact, inline)
        metrik_opt = {"Größe (cm)": "groesse", "Gewicht (kg)": "gewicht", "BMI": "bmi"}
        metrik_label = st.radio(
            "Verlauf anzeigen",
            list(metrik_opt.keys()),
            horizontal=True,
            key="profil_anthro_metrik",
            label_visibility="collapsed",
        )
        metrik_col  = metrik_opt[metrik_label]
        metrik_farbe = {"groesse": "#3b82f6", "gewicht": "#3fb950", "bmi": "#d29922"}[metrik_col]
        metrik_einheit = {"groesse": "cm", "gewicht": "kg", "bmi": ""}[metrik_col]

        fig_ah = go.Figure()
        fig_ah.add_trace(go.Scatter(
            x=df_ah["datum"],
            y=df_ah[metrik_col],
            mode="lines+markers+text",
            text=[f"{v:.1f}{metrik_einheit}" if v else "" for v in df_ah[metrik_col]],
            textposition="top center",
            textfont=dict(size=10, color=metrik_farbe),
            line=dict(color=metrik_farbe, width=2),
            marker=dict(size=7, color=metrik_farbe),
            name=metrik_label,
        ))
        fig_ah.update_layout(**_pl(
            height=220,
            margin=dict(l=40, r=20, t=12, b=36),
            showlegend=False,
            xaxis=dict(title=None, tickfont=dict(size=10)),
            yaxis=dict(title=metrik_label, tickfont=dict(size=10)),
        ))
        st.plotly_chart(fig_ah, use_container_width=True)

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
            if st.button("💾 Verletzung speichern", key="v_save", type="primary", use_container_width=True):
                verletzung_speichern(sid, v_datum, v_art, v_koerper, v_schwere, int(v_ausfall), v_notizen)
                _save_ok("Verletzung gespeichert.")
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
                    _save_ok("Verletzungseintrag gelöscht.")
                    st.rerun()

    with tab_pdf:
        st.markdown("### 📄 PDF Report")

        # Daten laden
        plan_rows        = zyklus_laden(sid)
        anthro_row       = anthropometrie_letzter(sid)
        sprint_row       = sprint_letzter(sid)
        sprung_row       = sprung_letzter(sid)
        agil_row         = agilitaet_letzter(sid)
        aus_row          = ausdauer_letzter(sid)
        verletzungen_pdf = verletzungen_laden(sid)
        kraft_pdf        = kraft_letzter(sid)
        beob_pdf         = beobachtungen_alle_fuer_spieler(sid)
        spiro_pdf        = spiro_test_letzter(sid)

        # ── Modulauswahl ──────────────────────────────────────────────────────
        st.markdown("#### 📋 Module auswählen")
        st.caption(
            "Wähle, welche Abschnitte im PDF erscheinen sollen. "
            "Grau = noch keine Daten vorhanden."
        )

        # (label, session_key, hat_daten, daten_objekt)
        _MODULE_CFG = [
            ("📐 Anthropometrie",         "pdf_m_anthro",   bool(anthro_row),       anthro_row),
            ("📝 FMS",                    "pdf_m_fms",      bool(fms),              fms),
            ("📏 Y-Balance",              "pdf_m_ybal",     bool(y),                y),
            ("⚡ Sprint",                 "pdf_m_sprint",   bool(sprint_row),       sprint_row),
            ("🦘 Sprung / CMJ",           "pdf_m_sprung",   bool(sprung_row),       sprung_row),
            ("🔀 Agilität",               "pdf_m_agil",     bool(agil_row),         agil_row),
            ("🫁 Ausdauer (Yo-Yo)",       "pdf_m_ausdauer", bool(aus_row),          aus_row),
            ("💪 Kraftdiagnostik",        "pdf_m_kraft",    bool(kraft_pdf),        kraft_pdf),
            ("🫀 Spiroergometrie",        "pdf_m_spiro",    bool(spiro_pdf),        spiro_pdf),
            ("🩹 Verletzungshistorie",    "pdf_m_verletz",  bool(verletzungen_pdf), verletzungen_pdf),
            ("⚠️ Defizite & Empfehlungen","pdf_m_defizite", bool(defizite),         defizite),
            ("📅 Trainingsplan",          "pdf_m_plan",     bool(plan_rows),        plan_rows),
            ("🗒️ Trainerbeobachtungen",   "pdf_m_beob",     bool(beob_pdf),         beob_pdf),
        ]

        # Schnellauswahl-Buttons
        _qa1, _qa2, _qa3 = st.columns(3)
        if _qa1.button("✅ Alle aktivieren",  key="pdf_m_alle_an",  use_container_width=True):
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = True
        if _qa2.button("⬜ Alle deaktivieren", key="pdf_m_alle_aus", use_container_width=True):
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = False
        if _qa3.button("🔬 Nur Testergebnisse", key="pdf_m_nur_tests", use_container_width=True):
            _test_keys = {"pdf_m_anthro","pdf_m_fms","pdf_m_ybal","pdf_m_sprint",
                          "pdf_m_sprung","pdf_m_agil","pdf_m_ausdauer","pdf_m_kraft","pdf_m_spiro"}
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = _k in _test_keys

        st.markdown("")
        _mc1, _mc2, _mc3 = st.columns(3)
        _col_cycle = [_mc1, _mc2, _mc3]
        _selection = {}

        for _i, (_lbl, _key, _hat_daten, _daten) in enumerate(_MODULE_CFG):
            _col = _col_cycle[_i % 3]
            with _col:
                if _hat_daten:
                    _selection[_key] = st.checkbox(
                        _lbl,
                        value=st.session_state.get(_key, True),
                        key=_key,
                    )
                else:
                    st.checkbox(
                        _lbl,
                        value=False,
                        disabled=True,
                        key=f"{_key}_dis",
                        help="Noch keine Daten vorhanden",
                    )
                    _selection[_key] = False

        _n_aktiv = sum(1 for v in _selection.values() if v)

        st.markdown("---")

        # Vorschau-Banner
        _vorh_labels = [_lbl for (_lbl, _key, _hat, _) in _MODULE_CFG if _selection.get(_key)]
        if _vorh_labels:
            st.markdown(
                f'<div style="background:#0d1117;border:1px solid #238636;'
                f'border-radius:8px;padding:10px 14px;margin-bottom:12px">'
                f'<div style="font-size:10px;color:#3fb950;letter-spacing:1px;margin-bottom:6px">'
                f'PDF ENTHÄLT — {_n_aktiv} MODULE</div>'
                f'<div style="color:#c9d1d9;font-size:12px">'
                + "  ·  ".join(_vorh_labels)
                + '</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("⚠️ Kein Modul ausgewählt — bitte mindestens eines aktivieren.")

        if _n_aktiv > 0 and st.button(
            f"📥 PDF Report generieren  ({_n_aktiv} Module)",
            key="pdf_gen", type="primary", use_container_width=True,
        ):
            def _m(key, daten):
                return daten if _selection.get(key) else None

            pdf_bytes = generate_report(
                spieler=auswahl,
                fms_row=       _m("pdf_m_fms",      fms),
                y_row=         _m("pdf_m_ybal",     y),
                anthro_row=    _m("pdf_m_anthro",   anthro_row),
                sprint_row=    _m("pdf_m_sprint",   sprint_row),
                sprung_row=    _m("pdf_m_sprung",   sprung_row),
                agil_row=      _m("pdf_m_agil",     agil_row),
                aus_row=       _m("pdf_m_ausdauer", aus_row),
                kraft_row=     _m("pdf_m_kraft",    kraft_pdf),
                spiro_row=     _m("pdf_m_spiro",    spiro_pdf),
                verletzungen=  _m("pdf_m_verletz",  verletzungen_pdf) or [],
                athletik_score=ascore,
                risiko_label=label,
                defizite=      _m("pdf_m_defizite", defizite) or [],
                plan_rows=     _m("pdf_m_plan",     plan_rows) or [],
                beobachtungen= _m("pdf_m_beob",     beob_pdf) or [],
                vereinsname=st.session_state.get("cfg_vereinsname", ""),
                saison=st.session_state.get("cfg_saison", ""),
                logo_bytes=logo_laden(),
            )
            st.session_state["pdf_bytes_cache"] = pdf_bytes
            st.download_button(
                label="⬇️ PDF herunterladen",
                data=pdf_bytes,
                file_name=f"athletik_report_{auswahl['name'].replace(' ','_')}_{date.today()}.pdf",
                mime="application/pdf",
                key="pdf_dl",
            )
            st.success(f"✅ PDF erstellt mit {_n_aktiv} Modulen.")

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

    sid     = auswahl["id"]
    fms     = fms_letzter(sid)
    y       = y_balance_letzter(sid)
    sprint  = sprint_letzter(sid)
    sprung  = sprung_letzter(sid)
    agil    = agilitaet_letzter(sid)
    aus     = ausdauer_letzter(sid)
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus, kraft_row=kraft_letzter(sid))

    tab_auto, tab_manual, tab_view = st.tabs(["🤖 Automatisch generieren", "✍️ Manuell hinzufügen", "📋 Plan anzeigen"])

    with tab_auto:
        st.markdown("### Individuellen Trainingsplan aus Diagnostikdaten")

        # ── Deficit Analysis ──────────────────────────────────────────────────
        defizite = defizit_tabelle(schwerpunkt)
        if defizite:
            st.markdown("#### 🔍 Erkannte Defizite")
            _d_cols = st.columns(min(len(defizite), 4))
            _farben = {"🔴 Primär": "#f85149", "🟡 Sekundär": "#d29922", "🟢 Tertiär": "#3fb950"}
            for i, d in enumerate(defizite):
                col = _d_cols[i % len(_d_cols)]
                _clr = _farben.get(d["Priorität"], "#8b949e")
                col.markdown(
                    f'<div style="background:#161b22;border:2px solid {_clr};border-radius:8px;'
                    f'padding:10px 14px;margin-bottom:8px;text-align:center">'
                    f'<div style="font-size:18px">{d["Priorität"].split()[0]}</div>'
                    f'<div style="font-weight:700;color:#e6edf3;font-size:14px">{d["Bereich"]}</div>'
                    f'<div style="color:{_clr};font-size:12px">{d["Volumen/Woche"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("ℹ️ Keine Testdaten vorhanden — Standard-Plan (Hüfte + Rumpf + Knie) wird erstellt.")

        st.markdown("---")
        st.markdown("#### ⚙️ Planparameter")
        _pc1, _pc2 = st.columns(2)
        plan_laenge = _pc1.selectbox(
            "Planlänge",
            [4, 6, 8],
            format_func=lambda x: f"{x} Wochen",
            index=1,
            key="plan_laenge",
        )
        _pc2.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
            f'padding:12px 14px;margin-top:26px">'
            f'<b>Aufbau:</b> {plan_laenge // 2 if plan_laenge > 4 else plan_laenge} Wochen Aufbau · '
            f'{"je Woche 4 Deload" if plan_laenge >= 4 else ""}<br>'
            f'<small style="color:#8b949e">Mehrere Trainingsbereiche pro Woche · '
            f'Belastungssteuerung nach 4-Wochen-Block</small></div>',
            unsafe_allow_html=True,
        )

        # Altersgruppe ermitteln und anzeigen
        _tp_alter = berechne_alter(auswahl.get("geburtsdatum"))
        _tp_pg    = _alter_zu_plangruppe(_tp_alter)
        _tp_cfg   = _PLANGRUPPEN_CONFIG[_tp_pg]
        _pg_farben = {
            "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
            "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
        }
        _pg_clr = _pg_farben.get(_tp_pg, "#8b949e")
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_pg_clr};border-radius:8px;'
            f'padding:10px 16px;margin-bottom:12px">'
            f'<span style="font-size:13px;color:{_pg_clr};font-weight:700">🎯 Altersgruppe: {_tp_pg}</span>'
            f'<span style="color:#8b949e;font-size:12px;margin-left:10px">— {_tp_cfg["label"]}</span><br>'
            f'<small style="color:#8b949e">Quelle: Faigenbaum & Myer (2010) · Lloyd et al. (2014) · NSCA Youth RT Position Statement</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("⚡ Trainingsplan erstellen", use_container_width=True, key="auto_gen_btn"):
            n = trainingsplan_multi_erstellen(sid, schwerpunkt, wochen=plan_laenge, alter=_tp_alter)
            _save_ok(f"Trainingsplan erstellt — {n} Übungen über {plan_laenge} Wochen ({_tp_pg}).")
            st.rerun()

    with tab_manual:
        st.markdown("### Übung manuell hinzufügen")
        mc1, mc2 = st.columns(2)
        bereich = mc1.selectbox("Bereich", ["Sprunggelenk","Knie","Hüfte","Rumpf","Oberschenkel",
                                             "Schnelligkeit","Explosivität","Agilität","Fußball"],
                                key="manual_bereich")

        # Übungskatalog aus Pool für gewählten Bereich (ohne Duplikate, alle Phasen)
        _katalog: list[str] = []
        for _pk in ["stabilisation", "kraft", "power"]:
            for _u, *_ in _POOL.get(bereich, {}).get(_pk, []):
                if _u not in _katalog:
                    _katalog.append(_u)
        _EIGENE_OPT = "✏️ Eigene Übung eingeben..."
        _katalog_opts = _katalog + [_EIGENE_OPT]

        _ub_sel = mc2.selectbox("Übungsname", _katalog_opts,
                                key=f"manual_ub_{bereich}",
                                help="Alle Übungen aus dem Katalog für diesen Bereich. "
                                     "Ganz unten: eigene Übung frei eingeben.")
        if _ub_sel == _EIGENE_OPT:
            uebung = st.text_input("Eigene Übung eingeben", key="manual_ub_custom",
                                   placeholder="z. B. Reverse Lunge mit Rotation")
        else:
            uebung = _ub_sel

        saetze      = mc1.text_input("Sätze", "3",          key="manual_saetze")
        wdh         = mc2.text_input("Wiederholungen", "10", key="manual_wdh")
        haeufigkeit = mc1.text_input("Häufigkeit", "2×/Woche", key="manual_haeuf")
        woche       = mc2.number_input("Woche", 1, 12, 1,   key="manual_woche")
        if st.button("➕ Übung speichern", type="primary", use_container_width=True):
            trainingsplan_eintrag_speichern(sid, str(date.today()), woche,
                                            bereich, uebung, saetze, wdh, haeufigkeit)
            _save_ok("Übung gespeichert.")
            st.rerun()

    with tab_view:
        plan = trainingsplan_laden(sid)
        if not plan:
            st.info("Noch kein Trainingsplan vorhanden. Bitte zuerst automatisch generieren oder manuell Übungen hinzufügen.")
            return

        df = pd.DataFrame(plan)
        # New schema: bereich, uebung, saetze, wiederholungen, haeufigkeit, woche, tag, pause_sekunden, ausfuehrung
        expected_cols = ["Bereich","Übung","Sätze","Wdh.","Häufigkeit","Woche","Tag","Pause (s)","Ausführung"]
        if len(df.columns) == len(expected_cols):
            df.columns = expected_cols
        elif len(df.columns) == 6:
            df.columns = ["Bereich","Übung","Sätze","Wdh.","Häufigkeit","Woche"]
            df["Tag"]       = 1
            df["Pause (s)"] = 90
            df["Ausführung"] = "kontrolliert"
        else:
            df.columns = expected_cols[:len(df.columns)]

        _total_wochen   = int(df["Woche"].max())
        _total_uebungen = len(df["Übung"].unique()) if "Übung" in df.columns else len(df)
        _total_einheiten = int(df["Tag"].max()) if "Tag" in df.columns else 0
        _ci1, _ci2, _ci3, _ci4 = st.columns(4)
        _ci1.metric("Wochen", _total_wochen)
        _ci2.metric("Übungen (einzigartig)", _total_uebungen)
        _ci3.metric("Bereiche", df["Bereich"].nunique())
        _ci4.metric("Trainingstage/Woche", _total_einheiten)

        # ── PDF-Druck-Button ──────────────────────────────────────────────────
        _tv_alter   = berechne_alter(auswahl.get("geburtsdatum"))
        _tv_pg      = _alter_zu_plangruppe(_tv_alter)
        _tv_cfg     = _PLANGRUPPEN_CONFIG[_tv_pg]
        _tv_pg_farben = {
            "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
            "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
        }
        _tv_pg_clr = _tv_pg_farben.get(_tv_pg, "#8b949e")
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_tv_pg_clr};border-radius:8px;'
            f'padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:13px;color:{_tv_pg_clr};font-weight:700">🎯 Altersgruppe: {_tv_pg}</span>'
            f'<span style="color:#8b949e;font-size:12px">— {_tv_cfg["label"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("📄 PDF drucken", key="tp_pdf_btn", use_container_width=False):
            with st.spinner("Trainingsplan-PDF wird erstellt …"):
                try:
                    _tv_vereinsname = st.session_state.get("cfg_vereinsname", "")
                    _tv_plan_raw = trainingsplan_laden(sid)
                    # Normalisiere zu dict-Liste mit einheitlichen Spaltennamen
                    _tv_plan_dicts = []
                    for _row in (_tv_plan_raw or []):
                        if isinstance(_row, (list, tuple)):
                            _keys = ["bereich","uebung","saetze","wiederholungen",
                                     "haeufigkeit","woche","tag","pause_sekunden","ausfuehrung"]
                            _tv_plan_dicts.append(dict(zip(_keys, list(_row) + [""]*9)))
                        else:
                            _tv_plan_dicts.append(_row)
                    _tv_pdf_bytes = generate_trainingsplan_pdf(
                        spieler         = auswahl,
                        plan_rows       = _tv_plan_dicts,
                        plangruppe      = _tv_pg,
                        plangruppen_config = _tv_cfg,
                        alters_ersatz   = _ALTERS_ERSATZ,
                        vereinsname     = _tv_vereinsname,
                    )
                    _tv_vorname  = (auswahl.get("vorname") or "").strip()
                    _tv_nachname = (auswahl.get("nachname") or auswahl.get("name") or "Spieler").strip()
                    _tv_filename = f"Trainingsplan_{_tv_vorname}_{_tv_nachname}_{_tv_pg}.pdf".replace(" ","_")
                    st.download_button(
                        label     = "⬇️ PDF herunterladen",
                        data      = _tv_pdf_bytes,
                        file_name = _tv_filename,
                        mime      = "application/pdf",
                        key       = "tp_pdf_download",
                    )
                    st.success(f"✅ PDF fertig — {len(_tv_pdf_bytes) // 1024} KB · Altersgruppe: {_tv_pg}")
                except Exception as _tv_exc:
                    st.error(f"Fehler beim Erstellen des PDFs: {_tv_exc}")

        st.markdown("---")

        _farbe_bereich = {
            "Hüfte": "#3b82f6", "Knie": "#3fb950", "Rumpf": "#d29922",
            "Sprunggelenk": "#a371f7", "Oberschenkel": "#f85149",
            "Schnelligkeit": "#58a6ff", "Explosivität": "#e3b341",
            "Agilität": "#56d364", "Fußball": "#ff7b72",
        }

        # Standard-Warm-Up (fußballspezifisch, ~8–10 Minuten)
        _WARMUP = [
            ("🏃", "Aktivierungslauf",           "5 min",       "Leichtes Joggen, Seitwärtsläufe, Rückwärtsläufe"),
            ("🔄", "Hüftkreisen beidbeinig",      "2×10",        "Kontrolliert, langsam"),
            ("🌍", "World's Greatest Stretch",    "2×5/Seite",   "Tief und kontrolliert"),
            ("🦵", "Leg Swings vor/rück",         "2×10/Seite",  "Freies Pendeln, zunehmende Amplitude"),
            ("↔️", "Leg Swings seitlich",          "2×10/Seite",  "Lateral, gestreckt"),
            ("🟢", "Glute Bridge",                "2×10",        "Langsam, Becken oben halten 2 s"),
            ("🎯", "Mini-Band Walk",              "2×10 m",      "Lateral, Knie leicht gebeugt"),
        ]

        _tag_namen = {1: "Tag 1 — Montag", 2: "Tag 2 — Mittwoch", 3: "Tag 3 — Freitag",
                      4: "Tag 4 — Samstag", 0: "Alle Tage"}

        for woche_nr in sorted(df["Woche"].unique()):
            _is_deload = (woche_nr % 4 == 0)
            _woche_label = f"Woche {int(woche_nr)}" + (" — 🔄 Deload" if _is_deload else "")
            with st.expander(_woche_label, expanded=(woche_nr <= 2)):
                if _is_deload:
                    st.info("⬇️ **Deload-Woche:** Reduziertes Volumen und Intensität zur Regeneration. Technikfokus.")
                sub_w = df[df["Woche"] == woche_nr]
                tags_in_woche = sorted(sub_w["Tag"].unique())

                for tag_nr in tags_in_woche:
                    _tag_label = _tag_namen.get(int(tag_nr), f"Tag {int(tag_nr)}")
                    st.markdown(
                        f'<div style="background:#161b22;border-left:4px solid #1f6feb;'
                        f'border-radius:0 8px 8px 0;padding:8px 14px;margin:12px 0 6px">' +
                        f'<span style="color:#58a6ff;font-weight:700;font-size:14px">🗓️ {_tag_label}</span></div>',
                        unsafe_allow_html=True,
                    )

                    # ── Warm-Up Block ──────────────────────────────────────────
                    with st.expander("🔥 Warm-Up (8–10 min) — Standard-Aktivierung", expanded=False):
                        _wu_rows = []
                        for _icon, _wu_name, _wu_vol, _wu_hinw in _WARMUP:
                            _wu_rows.append({"Übung": f"{_icon} {_wu_name}", "Volumen": _wu_vol,
                                             "Pause": "30 s", "Hinweis": _wu_hinw})
                        st.dataframe(pd.DataFrame(_wu_rows), use_container_width=True, hide_index=True)

                    # ── Hauptteil ──────────────────────────────────────────────
                    sub_t = sub_w[sub_w["Tag"] == tag_nr].copy()
                    _bereiche_tag = sub_t["Bereich"].unique()
                    for breich in sorted(_bereiche_tag):
                        _clr = _farbe_bereich.get(breich, "#8b949e")
                        st.markdown(
                            f'<div style="font-size:12px;font-weight:700;color:{_clr};'
                            f'margin:8px 0 3px;border-left:3px solid {_clr};padding-left:8px">' +
                            f'{breich}</div>',
                            unsafe_allow_html=True,
                        )
                        _sub_b = sub_t[sub_t["Bereich"] == breich][
                            ["Übung","Sätze","Wdh.","Pause (s)","Ausführung"]
                        ].copy()
                        _sub_b = _sub_b.rename(columns={"Wdh.": "Wdh. / Dauer", "Pause (s)": "Pause (s)"})
                        st.dataframe(_sub_b, use_container_width=True, hide_index=True)

                    # ── Cool-Down Hinweis ──────────────────────────────────────
                    st.caption(
                        "🧘 **Cool-Down:** 5–10 min Stretching der trainierten Muskelgruppen. "
                        "Besonderes Augenmerk auf Hüftbeuger, Oberschenkel und Rumpf."
                    )


# ──────────────────────────────────────────────────────────────────────────────

def page_periodisierung():
    st.markdown("# 🔄 Periodisierungsplan")
    st.markdown("Regelbasierter Athletik-Zyklus: Defizit-gewichtet · Multi-Fokus pro Woche · Progressive Belastungssteuerung")

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
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus, kraft_row=kraft_letzter(sid))

    # ── Deficit summary ───────────────────────────────────────────────────────
    defizite = defizit_tabelle(schwerpunkt)
    if defizite:
        st.markdown("#### 🔍 Defizit-Analyse")
        _d_cols = st.columns(min(len(defizite), 4))
        _farben = {"🔴 Primär": "#f85149", "🟡 Sekundär": "#d29922", "🟢 Tertiär": "#3fb950"}
        for i, d in enumerate(defizite):
            _clr = _farben.get(d["Priorität"], "#8b949e")
            _d_cols[i % len(_d_cols)].markdown(
                f'<div style="background:#161b22;border:2px solid {_clr};border-radius:8px;'
                f'padding:8px 12px;margin-bottom:6px;text-align:center">'
                f'<div style="font-size:16px">{d["Priorität"].split()[0]}</div>'
                f'<div style="font-weight:700;color:#e6edf3;font-size:13px">{d["Bereich"]}</div>'
                f'<div style="color:{_clr};font-size:11px">{d["Volumen/Woche"]}/Woche</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ️ Keine Testdaten — Standard-Basisplan wird erstellt.")

    st.markdown("---")
    col_info, col_gen = st.columns([3, 2])
    with col_info:
        wochen_auswahl = st.selectbox(
            "Planlänge",
            [4, 8, 12],
            index=2,
            format_func=lambda x: f"{x} Wochen",
            key="perio_wochen",
        )
        if wochen_auswahl == 4:
            st.markdown("**Phase 1** (W1–4): Stabilisation & Bewegungsqualität")
        elif wochen_auswahl == 8:
            st.markdown("**Phase 1** (W1–4): Stabilisation  \n**Phase 2** (W5–8): Kraftaufbau")
        else:
            st.markdown(
                "**Phase 1** (W1–4): Stabilisation  \n"
                "**Phase 2** (W5–8): Kraftaufbau  \n"
                "**Phase 3** (W9–12): Fußballspezifisch"
            )
        st.caption("Jede 4. Woche = Deload · Jede Woche = mehrere Trainingsschwerpunkte")
    # Altersgruppe ermitteln
    _pz_alter = berechne_alter(auswahl.get("geburtsdatum"))
    _pz_pg    = _alter_zu_plangruppe(_pz_alter)
    _pz_cfg   = _PLANGRUPPEN_CONFIG[_pz_pg]
    _pg_farben2 = {
        "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
        "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
    }
    _pg_clr2 = _pg_farben2.get(_pz_pg, "#8b949e")

    with col_info:
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_pg_clr2};border-radius:8px;'
            f'padding:8px 14px;margin-top:8px">'
            f'<span style="color:{_pg_clr2};font-weight:700;font-size:13px">🎯 {_pz_pg}</span>'
            f'<span style="color:#8b949e;font-size:11px;margin-left:8px">{_pz_cfg["label"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Zyklus erstellen / neu generieren", use_container_width=True, key="perio_gen"):
            zyklus_erstellen(sid, schwerpunkt, wochen=wochen_auswahl, alter=_pz_alter)
            _save_ok(f"{wochen_auswahl}-Wochen-Zyklus generiert! ({_pz_pg})")
            st.rerun()

    plan = zyklus_laden(sid)
    if not plan:
        st.info("Noch kein Periodisierungsplan vorhanden. Klicke auf **Zyklus erstellen**.")
        return

    df = pd.DataFrame(plan)
    df.columns = ["Woche", "Phase", "Ziel", "Bereich", "Übung", "Intensität", "Volumen", "Häufigkeit"]

    # Statistik-Header
    _pi1, _pi2, _pi3, _pi4 = st.columns(4)
    _pi1.metric("Wochen", int(df["Woche"].max()))
    _pi2.metric("Übungen gesamt", len(df))
    _pi3.metric("Bereiche", df["Bereich"].nunique())
    _pi4.metric("Phasen", df["Phase"].str.split("(").str[0].str.strip().nunique())
    st.markdown("---")

    # Phase colour map — match on prefix (new format includes week type in parens)
    _phase_defs = [
        ("Phase 1 — Stabilisation",    "#1f6feb"),
        ("Phase 2 — Kraftaufbau",       "#3fb950"),
        ("Phase 3 — Fußballspezifisch", "#d29922"),
        # Short plans (4/8 wk) may use generic phase names
        ("Stabilisation",               "#1f6feb"),
        ("Kraftaufbau",                 "#3fb950"),
    ]
    _seen_phases: set = set()

    _farbe_bereich = {
        "Hüfte": "#3b82f6", "Knie": "#3fb950", "Rumpf": "#d29922",
        "Sprunggelenk": "#a371f7", "Oberschenkel": "#f85149",
        "Schnelligkeit": "#58a6ff", "Explosivität": "#e3b341",
        "Agilität": "#56d364", "Fußball": "#ff7b72",
    }

    # Group by leading phase name (strip the "(Woche-Typ)" suffix)
    df["_PhaseGroup"] = df["Phase"].str.extract(r"^(Phase \d+ — [^(]+|[^(]+)", expand=False).str.strip()

    for phase_prefix, color in _phase_defs:
        sub = df[df["_PhaseGroup"].str.startswith(phase_prefix)]
        if sub.empty or phase_prefix in _seen_phases:
            continue
        _seen_phases.add(phase_prefix)
        weeks = sorted(sub["Woche"].unique())
        _ziel = sub.iloc[0]["Ziel"]
        st.markdown(
            f'<div style="border-left:4px solid {color};padding-left:12px;margin:20px 0 8px">'
            f'<h4 style="color:{color};margin:0 0 2px">{phase_prefix}</h4>'
            f'<small style="color:#8b949e">Wochen {weeks[0]}–{weeks[-1]} · {_ziel}</small></div>',
            unsafe_allow_html=True,
        )
        for woche_nr in weeks:
            _is_deload = (woche_nr % 4 == 0)
            _woche_typ = sub[sub["Woche"] == woche_nr]["Phase"].iloc[0]
            _typ_label = _woche_typ.split("(")[-1].rstrip(")") if "(" in _woche_typ else ""
            _exp_label = f"Woche {woche_nr}" + (f" — {_typ_label}" if _typ_label else "")
            w_sub = sub[sub["Woche"] == woche_nr]
            with st.expander(_exp_label, expanded=(woche_nr == weeks[0])):
                if _is_deload:
                    st.caption("⬇️ Deload-Woche: reduziertes Volumen zur aktiven Regeneration")
                for breich in sorted(w_sub["Bereich"].unique()):
                    _clr = _farbe_bereich.get(breich, "#8b949e")
                    st.markdown(
                        f'<div style="font-size:12px;font-weight:700;color:{_clr};'
                        f'border-left:3px solid {_clr};padding-left:8px;margin:6px 0 2px">{breich}</div>',
                        unsafe_allow_html=True,
                    )
                    _b_sub = w_sub[w_sub["Bereich"] == breich][["Übung", "Intensität", "Volumen", "Häufigkeit"]]
                    st.dataframe(_b_sub, use_container_width=True, hide_index=True)

    # Download plan CSV
    _csv_df = df.drop(columns=["_PhaseGroup"])
    csv = _csv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Plan als CSV herunterladen", csv,
        f"periodisierung_{auswahl['name'].replace(' ', '_')}.csv", "text/csv",
    )


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
    kraft_hist  = kraft_history(sid)
    anthro_hist = anthropometrie_history(sid)

    tab_profil, tab_beweg, tab_speed, tab_auskoerp = st.tabs([
        "🕸️ Athletisches Profil",
        "🦵 Beweglichkeit",
        "⚡ Speed & Kraft",
        "🫁 Ausdauer & Körper",
    ])

    # ── Athletisches Profil — Radar-Chart ────────────────────────────────────
    with tab_profil:
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

    # ── Beweglichkeit: FMS + Y-Balance ──────────────────────────────────────────
    with tab_beweg:
        _beweg_sel = st.radio(
            "Modul auswählen", ["📝 FMS", "📏 Y-Balance"],
            horizontal=True, key="fort_beweg_radio", label_visibility="collapsed",
        )
        if _beweg_sel == "📝 FMS":
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
                _df_fms_f = _datum_filter(df.copy(), "fort_fms")
                st.dataframe(_df_fms_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Score": st.column_config.NumberColumn("Score", format="%d / 21"),
                             })
        else:
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
                _df_yb_f = _datum_filter(df.copy(), "fort_yb")
                st.dataframe(_df_yb_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Composite R": st.column_config.NumberColumn("Composite R (%)", format="%.1f %%"),
                                 "Composite L": st.column_config.NumberColumn("Composite L (%)", format="%.1f %%"),
                                 "Asymmetrie":  st.column_config.NumberColumn("Asymmetrie", format="%.1f %%"),
                             })

    # ── Speed & Kraft: Sprint + Sprung + Agilität + Kraft ─────────────────────
    with tab_speed:
        _speed_sel = st.radio(
            "Modul auswählen", ["⚡ Sprint", "🦘 Sprung", "🔀 Agilität", "💪 Kraft"],
            horizontal=True, key="fort_speed_radio", label_visibility="collapsed",
        )
        if _speed_sel == "⚡ Sprint":
            if not sprint_hist:
                st.info("Noch keine Sprint-Tests vorhanden.")
            else:
                df = pd.DataFrame(sprint_hist)
                df.columns = ["Datum", "5m", "10m", "20m", "30m", "40m", "Beschl.-Index", "Bewertung 10m"]
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
                _df_sp_f = _datum_filter(df.copy(), "fort_sprint")
                st.dataframe(_df_sp_f, use_container_width=True, hide_index=True,
                             column_config={c: st.column_config.NumberColumn(c, format="%.2f s")
                                            for c in ["5m","10m","20m","30m"]})
        elif _speed_sel == "🦘 Sprung":
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
                _df_sprung_f = _datum_filter(df.copy(), "fort_sprung")
                st.dataframe(_df_sprung_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "CMJ beid.":  st.column_config.NumberColumn("CMJ beid. (cm)", format="%.1f cm"),
                                 "Squat Jump": st.column_config.NumberColumn("Squat Jump (cm)", format="%.1f cm"),
                                 "Drop Jump":  st.column_config.NumberColumn("Drop Jump (cm)", format="%.1f cm"),
                                 "CMJ Asymm.": st.column_config.NumberColumn("CMJ Asymm. (%)", format="%.1f %%"),
                             })
        elif _speed_sel == "🔀 Agilität":
            if not agil_hist:
                st.info("Noch keine Agilitäts-Tests vorhanden.")
            else:
                df = pd.DataFrame(agil_hist).rename(columns={
                    "datum": "Datum", "t505_r": "505 R (s)", "t505_l": "505 L (s)",
                    "asym_505": "Asymm. 505 (%)", "t5_10_5": "5-10-5 (s)",
                    "t_test": "T-Test (s)", "illinois": "Illinois (s)",
                    "bew_t_test": "Bewertung T-Test", "modified_t_test": "Mod. T-Test (s)",
                    "pro_agility": "Pro Agility (s)", "arrowhead_r": "Arrowhead R (s)",
                    "arrowhead_l": "Arrowhead L (s)", "zigzag": "Zigzag (s)", "balsom": "Balsom (s)",
                })
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
                _df_agil_f = _datum_filter(df.copy(), "fort_agil")
                st.dataframe(_df_agil_f, use_container_width=True, hide_index=True,
                             column_config={c: st.column_config.NumberColumn(c, format="%.2f s")
                                            for c in ["505 R (s)","505 L (s)","5-10-5 (s)","T-Test (s)","Illinois (s)"]})
        else:  # Kraft
            if not kraft_hist:
                st.info("Noch keine Krafttests vorhanden.")
            else:
                df_k = pd.DataFrame(kraft_hist)
                figk1 = go.Figure()
                if "direktes_1rm" in df_k.columns:
                    figk1.add_trace(go.Scatter(
                        x=df_k["datum"], y=df_k["direktes_1rm"],
                        mode="lines+markers", name="Direktes 1RM (kg)",
                        line=dict(color="#3fb950", width=3), marker=dict(size=9),
                    ))
                if "geschaetztes_1rm" in df_k.columns:
                    figk1.add_trace(go.Scatter(
                        x=df_k["datum"], y=df_k["geschaetztes_1rm"],
                        mode="lines+markers", name="Epley 1RM (kg)",
                        line=dict(color="#3b82f6", width=2, dash="dash"), marker=dict(size=7),
                    ))
                figk1.update_layout(**_pl(height=300, title="Bankdrücken 1RM Verlauf (kg)",
                                         yaxis=dict(title="kg")))
                st.plotly_chart(figk1, use_container_width=True)
                if "rumpf_gesamt_sekunden" in df_k.columns:
                    figk2 = go.Figure()
                    for col_k, lbl_k, clr_k in [
                        ("ventral_sekunden",        "Ventral (Plank)", "#3fb950"),
                        ("lateral_rechts_sekunden", "Lateral rechts",  "#3b82f6"),
                        ("lateral_links_sekunden",  "Lateral links",   "#d29922"),
                        ("dorsal_sekunden",          "Dorsal",          "#9e6a03"),
                        ("rumpf_gesamt_sekunden",    "Gesamtzeit",      "#f85149"),
                    ]:
                        if col_k in df_k.columns:
                            figk2.add_trace(go.Scatter(
                                x=df_k["datum"], y=df_k[col_k],
                                mode="lines+markers", name=lbl_k,
                                line=dict(color=clr_k, width=2), marker=dict(size=7),
                            ))
                    figk2.update_layout(**_pl(height=300, title="Rumpfkraftausdauer Verlauf (s)",
                                             yaxis=dict(title="Sekunden")))
                    st.plotly_chart(figk2, use_container_width=True)
                _df_kraft_ren = df_k.rename(columns={
                    "datum": "Datum", "direktes_1rm": "1RM direkt (kg)",
                    "geschaetztes_1rm": "1RM Epley (kg)",
                    "relative_kraft_direkt": "Rel. K. direkt",
                    "relative_kraft_geschaetzt": "Rel. K. Epley",
                    "ventral_sekunden": "Ventral (s)",
                    "lateral_rechts_sekunden": "Lat. R (s)",
                    "lateral_links_sekunden": "Lat. L (s)",
                    "dorsal_sekunden": "Dorsal (s)",
                    "rumpf_gesamt_sekunden": "Rumpf ges. (s)",
                    "lateral_asymmetrie_prozent": "Lat. Asym (%)",
                })
                _df_kraft_f = _datum_filter(_df_kraft_ren, "fort_kraft")
                st.dataframe(_df_kraft_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "1RM direkt (kg)": st.column_config.NumberColumn("1RM direkt (kg)", format="%.1f kg"),
                                 "1RM Epley (kg)":  st.column_config.NumberColumn("1RM Epley (kg)", format="%.1f kg"),
                                 "Lat. Asym (%)":   st.column_config.NumberColumn("Lat. Asym (%)", format="%.1f %%"),
                             })

    # ── Ausdauer & Körper: Ausdauer + Anthropometrie ───────────────────────────
    with tab_auskoerp:
        _ausd_sel = st.radio(
            "Modul auswählen", ["🫁 Ausdauer", "⚖️ Anthropometrie"],
            horizontal=True, key="fort_ausd_radio", label_visibility="collapsed",
        )
        if _ausd_sel == "🫁 Ausdauer":
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
                _df_aus_f = _datum_filter(df.copy(), "fort_ausdauer")
                st.dataframe(_df_aus_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "VO₂max":      st.column_config.NumberColumn("VO₂max", format="%.1f ml/kg/min"),
                                 "Distanz (m)": st.column_config.NumberColumn("Distanz (m)", format="%d m"),
                             })
        else:
            if not anthro_hist:
                st.info("Noch keine Anthropometrie-Messungen vorhanden.")
            else:
                df = pd.DataFrame(anthro_hist)
                df.columns = ["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)", "Muskelmasse (kg)",
                              "BMI", "BMI-Kat.", "Sitzhöhe (cm)", "Beinlänge (cm)", "Armspann (cm)",
                              "PHV-Offset", "Reifestatus", "Beinlänge R", "Beinlänge L", "KF-Methode"]
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
                _df_anthro_show = df[["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)",
                                       "Muskelmasse (kg)", "BMI", "BMI-Kat.", "PHV-Offset", "Reifestatus"]].copy()
                _df_anthro_f = _datum_filter(_df_anthro_show, "fort_anthro")
                st.dataframe(_df_anthro_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Größe (cm)":      st.column_config.NumberColumn("Größe (cm)", format="%.0f cm"),
                                 "Gewicht (kg)":    st.column_config.NumberColumn("Gewicht (kg)", format="%.1f kg"),
                                 "Körperfett (%)":  st.column_config.NumberColumn("Körperfett (%)", format="%.1f %%"),
                                 "Muskelmasse (kg)":st.column_config.NumberColumn("Muskelmasse (kg)", format="%.1f kg"),
                                 "BMI":             st.column_config.NumberColumn("BMI", format="%.1f"),
                             })

# ──────────────────────────────────────────────────────────────────────────────

def page_anthropometrie():
    st.markdown("# 📐 Anthropometrie")
    st.markdown("Körpermessungen, BMI und Wachstumsverlauf — Grundlage für belastungsgerechtes Training.")

    sicherheitshinweis_box()
    show_trainer_checkliste("anthropometrie")
    show_test_info("anthropometrie")
    _anleitung_download_button("anthropometrie")

    auswahl = _player_selector("anthro")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    alter  = berechne_alter(sp.get("geburtsdatum", "")) if sp else 0.0
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    altersgruppe_norm = alter_zu_altersgruppe(alter)

    history = anthropometrie_history(sid)
    letzter = anthropometrie_letzter(sid)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_neu, tab_verlauf = st.tabs(["📋 Neue Messung", "📈 Verlauf"])

    with tab_neu:
        st.markdown("### Körpermessung eingeben")
        _check_save_ok()
        _fh = lambda fid: show_field_help("anthropometrie", fid)
        _APP_DIR = os.path.dirname(os.path.abspath(__file__))

        datum = st.date_input("Datum", value=date.today(), key="anthro_datum")

        # ── Körperfett-Methode — zuerst und volle Breite ──────────────────────
        st.markdown("#### 📏 Körperfett-Messung")
        kf_methode = st.radio(
            "Methode wählen",
            ["Manuell", "7-Hautfalten (JP)", "11-Hautfalten (JP)", "Körperanalysewaage"],
            key="anthro_kf_methode", horizontal=True, label_visibility="collapsed",
        )
        _kf_default = float(letzter["koerperfett"]) if letzter and letzter.get("koerperfett") else 0.0
        koerperfett = 0.0

        if kf_methode in ("Manuell", "Körperanalysewaage"):
            _kf_note = "Gerätewert direkt eingeben (BIA-Waage, DEXA o. ä.)" if kf_methode == "Körperanalysewaage" else "Bekannten Prozentwert direkt eingeben"
            st.caption(_kf_note)
            _kfrc1, _kfrc2 = st.columns([2, 5])
            koerperfett = _kfrc1.number_input(
                "Körperfett (%)", 0.0, 50.0, _kf_default, step=0.1, key="anthro_kf_man"
            )
            if koerperfett > 0:
                norm_badge(koerperfett, "anthropometrie", "koerperfett", _kfrc1, altersgruppe=altersgruppe_norm)

        elif kf_methode == "7-Hautfalten (JP)":
            _svg7 = os.path.join(_APP_DIR, "assets", "tests", "anthropometrie", "hautfalten_7.svg")
            _img7_col, _inp7_col = st.columns([5, 11])
            with _img7_col:
                if os.path.exists(_svg7):
                    st.image(_svg7, use_container_width=True)
                else:
                    st.caption("📍 Brust · Abdomen · Suprailiakal · Oberschenkel · Trizeps · Subskapular · Mittelachse")
            with _inp7_col:
                st.caption("**Jackson & Pollock (1978)** — alle Werte in mm, rechte Körperseite, entspannte Muskulatur")
                _h7r1, _h7r2, _h7r3, _h7r4 = st.columns(4)
                _h7r5, _h7r6, _h7r7, _h7res  = st.columns(4)
                s_brust  = _h7r1.number_input("Brust (mm)",        0.0, 80.0, 0.0, step=0.5, key="hf7_br")
                s_mittel = _h7r2.number_input("Mittelachse (mm)",  0.0, 60.0, 0.0, step=0.5, key="hf7_mi")
                s_tri    = _h7r3.number_input("Trizeps (mm)",      0.0, 60.0, 0.0, step=0.5, key="hf7_tr")
                s_sub    = _h7r4.number_input("Subskapular (mm)",  0.0, 60.0, 0.0, step=0.5, key="hf7_su")
                s_abd    = _h7r5.number_input("Abdomen (mm)",      0.0, 80.0, 0.0, step=0.5, key="hf7_ab")
                s_sup    = _h7r6.number_input("Suprailiakal (mm)", 0.0, 60.0, 0.0, step=0.5, key="hf7_sp")
                s_ober   = _h7r7.number_input("Oberschenkel (mm)", 0.0, 60.0, 0.0, step=0.5, key="hf7_ob")
                _all7 = [s_brust, s_mittel, s_tri, s_sub, s_abd, s_sup, s_ober]
                if all(v > 0 for v in _all7) and alter and alter > 0:
                    koerperfett = koerperfett_jp7(*_all7, float(alter), geschl)
                    _h7res.metric("Körperfett (JP7)", f"{koerperfett} %")
                    norm_badge(koerperfett, "anthropometrie", "koerperfett", _h7res, altersgruppe=altersgruppe_norm)
                else:
                    st.info("ℹ️ Alle 7 Werte > 0 eingeben — Körperfett wird automatisch berechnet.")

        elif kf_methode == "11-Hautfalten (JP)":
            _svg11 = os.path.join(_APP_DIR, "assets", "tests", "anthropometrie", "hautfalten_11.svg")
            _img11_col, _inp11_col = st.columns([5, 11])
            with _img11_col:
                if os.path.exists(_svg11):
                    st.image(_svg11, use_container_width=True)
                else:
                    st.caption("📍 7-Punkt + Bizeps · Wadeninnenseite · unt. Rücken · Pektoral")
            with _inp11_col:
                st.caption("**Pařízkova (1977)** — 11 Messpunkte, rechte Körperseite, Werte in mm")
                _h11a, _h11b, _h11c, _h11d   = st.columns(4)
                _h11e, _h11f, _h11g, _h11h   = st.columns(4)
                _h11i, _h11j, _h11k, _h11res = st.columns(4)
                s11_br  = _h11a.number_input("Brust",        0.0, 80.0, 0.0, step=0.5, key="hf11_br")
                s11_mi  = _h11b.number_input("Mittelachse",  0.0, 60.0, 0.0, step=0.5, key="hf11_mi")
                s11_tr  = _h11c.number_input("Trizeps",      0.0, 60.0, 0.0, step=0.5, key="hf11_tr")
                s11_su  = _h11d.number_input("Subskapular",  0.0, 60.0, 0.0, step=0.5, key="hf11_su")
                s11_ab  = _h11e.number_input("Abdomen",      0.0, 80.0, 0.0, step=0.5, key="hf11_ab")
                s11_sp  = _h11f.number_input("Suprailiakal", 0.0, 60.0, 0.0, step=0.5, key="hf11_sp")
                s11_ob  = _h11g.number_input("Oberschenkel", 0.0, 60.0, 0.0, step=0.5, key="hf11_ob")
                s11_biz = _h11h.number_input("Bizeps",       0.0, 60.0, 0.0, step=0.5, key="hf11_bz")
                s11_wa  = _h11i.number_input("Wade innen",   0.0, 40.0, 0.0, step=0.5, key="hf11_wa")
                s11_rk  = _h11j.number_input("Unt. Rücken",  0.0, 60.0, 0.0, step=0.5, key="hf11_rk")
                s11_pk  = _h11k.number_input("Pektoral",     0.0, 60.0, 0.0, step=0.5, key="hf11_pk")
                _all11 = [s11_br, s11_mi, s11_tr, s11_su, s11_ab, s11_sp, s11_ob, s11_biz, s11_wa, s11_rk, s11_pk]
                if all(v > 0 for v in _all11) and alter and alter > 0:
                    koerperfett = koerperfett_jp11(*_all11, float(alter), geschl)
                    _h11res.metric("Körperfett (JP11)", f"{koerperfett} %")
                    norm_badge(koerperfett, "anthropometrie", "koerperfett", _h11res, altersgruppe=altersgruppe_norm)
                else:
                    st.info("ℹ️ Alle 11 Werte > 0 eingeben — Körperfett wird automatisch berechnet.")

        # ── Körpermessungen ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📐 Körpermessungen")
        c1, c2 = st.columns(2)
        g_h, g_i = c1.columns([5, 1]); g_h.markdown("**Körpergröße (cm)**"); field_info_col(g_i, "anthropometrie", "groesse")
        groesse      = c1.number_input("Körpergröße (cm)", 100.0, 220.0,
                                        float(letzter["groesse"]) if letzter else 175.0,
                                        step=0.5, key="anthro_groesse", label_visibility="collapsed", help=_fh("groesse"))
        gw_h, gw_i = c1.columns([5, 1]); gw_h.markdown("**Körpergewicht (kg)**"); field_info_col(gw_i, "anthropometrie", "gewicht")
        gewicht      = c1.number_input("Körpergewicht (kg)", 15.0, 150.0,
                                        float(letzter["gewicht"]) if letzter else 70.0,
                                        step=0.5, key="anthro_gewicht", label_visibility="collapsed", help=_fh("gewicht"))
        mm_h, mm_i = c1.columns([5, 1]); mm_h.markdown("**Muskelmasse (kg)**"); field_info_col(mm_i, "anthropometrie", "muskelmasse")
        muskelmasse  = c1.number_input("Muskelmasse (kg)", 0.0, 100.0,
                                        float(letzter["muskelmasse"]) if letzter else 0.0,
                                        step=0.5, key="anthro_mm", label_visibility="collapsed", help=_fh("muskelmasse"))
        sh_h, sh_i = c2.columns([5, 1]); sh_h.markdown("**Sitzhöhe (cm) — optional für PHV**"); field_info_col(sh_i, "anthropometrie", "sitzhoehe")
        sitzhoehe    = c2.number_input("Sitzhöhe (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["sitzhoehe"]) if letzter else 0.0,
                                        step=0.5, key="anthro_sh", label_visibility="collapsed", help=_fh("sitzhoehe"))
        _def_bl_r = float(letzter.get("beinlaenge_r") or letzter.get("beinlaenge") or 0) if letzter else 0.0
        _def_bl_l = float(letzter.get("beinlaenge_l") or letzter.get("beinlaenge") or 0) if letzter else 0.0
        blr_h, blr_i = c2.columns([5, 1]); blr_h.markdown("**Beinlänge rechts (cm)**"); field_info_col(blr_i, "anthropometrie", "beinlaenge")
        beinlaenge_r = c2.number_input("Beinlänge rechts (cm)", 0.0, 120.0, _def_bl_r,
                                        step=0.5, key="anthro_bl_r", label_visibility="collapsed", help=_fh("beinlaenge"))
        bll_h, bll_i = c2.columns([5, 1]); bll_h.markdown("**Beinlänge links (cm)**"); field_info_col(bll_i, "anthropometrie", "beinlaenge")
        beinlaenge_l = c2.number_input("Beinlänge links (cm)", 0.0, 120.0, _def_bl_l,
                                        step=0.5, key="anthro_bl_l", label_visibility="collapsed", help=_fh("beinlaenge"))
        beinlaenge = (beinlaenge_r + beinlaenge_l) / 2.0 if beinlaenge_r > 0 and beinlaenge_l > 0 else max(beinlaenge_r, beinlaenge_l)
        if beinlaenge_r > 0 and beinlaenge_l > 0:
            _diff_bl = abs(beinlaenge_r - beinlaenge_l)
            if _diff_bl >= 0.5:
                c2.warning(f"⚠️ Beinlängendifferenz {_diff_bl:.1f} cm — Ärztliche Untersuchung empfohlen.")
        as_h, as_i = c2.columns([5, 1]); as_h.markdown("**Armspannweite (cm)**"); field_info_col(as_i, "anthropometrie", "armspann")
        armspann     = c2.number_input("Armspannweite (cm)", 0.0, 250.0,
                                        float(letzter["armspannweite"]) if letzter else 0.0,
                                        step=0.5, key="anthro_arm", label_visibility="collapsed", help=_fh("armspann"))

        bmi     = bmi_berechnen(gewicht, groesse)
        bmi_kat = bmi_kategorie(bmi)
        phv     = phv_offset_berechnen(alter, groesse, gewicht, sitzhoehe, beinlaenge, geschl) if alter else None
        reife   = reifestatus_text(phv)
        farbe   = reifestatus_farbe(phv)

        # ── Plausibilitätsprüfungen ──────────────────────────────────────────
        if datum > date.today():
            st.warning("⚠️ Datum liegt in der Zukunft — bitte prüfen.")
        if sitzhoehe > 0 and sitzhoehe >= groesse:
            st.warning("⚠️ Sitzhöhe ≥ Körpergröße — Eingaben prüfen.")
        if beinlaenge > 0 and beinlaenge >= groesse:
            st.warning("⚠️ Beinlänge ≥ Körpergröße — Eingaben prüfen.")
        if armspann > 0 and (armspann < groesse * 0.75 or armspann > groesse * 1.25):
            st.warning(
                f"⚠️ Armspannweite ({armspann:.0f} cm) liegt deutlich außerhalb der "
                f"Körpergröße ({groesse:.0f} cm) — Eingaben prüfen."
            )
        if alter and alter < 18 and bmi > 0:
            st.info(
                "ℹ️ Hinweis: BMI-Normbereiche für Erwachsene (≥ 18 J.) gelten nicht direkt "
                "für Kinder und Jugendliche — bitte altersabhängige Normkurven verwenden."
            )

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

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_anthro = render_observation_selector("anthropometrie", sid, datum.strftime("%d.%m.%Y"), "anthro", standalone=False)

        col_sv, col_del = st.columns([3, 1])
        with col_sv:
            if st.button("💾 Messung speichern", use_container_width=True, key="anthro_save", type="primary"):
                import json as _j
                anthropometrie_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    groesse, gewicht, sitzhoehe, beinlaenge, armspann,
                    koerperfett, muskelmasse,
                    bmi, bmi_kat, phv, reife,
                    beinlaenge_r=beinlaenge_r, beinlaenge_l=beinlaenge_l,
                    koerperfett_methode=kf_methode,
                )
                if obs_anthro["beob_ids"] or obs_anthro.get("freitext"):
                    beobachtung_speichern(
                        sid, "anthropometrie", datum.strftime("%d.%m.%Y"),
                        _j.dumps(obs_anthro["beob_ids"], ensure_ascii=False),
                        obs_anthro["seite"], obs_anthro["auspraegung"],
                        obs_anthro["freitext"], obs_anthro["text_generiert"],
                    )
                _save_ok("Messung gespeichert!")
                st.rerun()
        with col_del:
            if letzter and st.button("🗑️ Letzte löschen", use_container_width=True, key="anthro_del"):
                anthropometrie_loeschen_letzten(sid)
                _save_ok("Letzte Messung gelöscht.")
                st.rerun()

    with tab_verlauf:
        if not history:
            st.info("Noch keine Messungen vorhanden.")
            return

        df = pd.DataFrame(history)
        df.columns = ["Datum", "Größe", "Gewicht", "Körperfett", "Muskelmasse",
                      "BMI", "BMI-Kat.", "Sitzhöhe", "Beinlänge", "Armspann",
                      "PHV-Offset", "Reifestatus", "Beinlänge R", "Beinlänge L",
                      "KF-Methode"]

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
            _kf_hover = df.apply(
                lambda r: f"{r['Körperfett']:.1f} %<br>Methode: {r['KF-Methode'] or '—'}",
                axis=1,
            )
            fig3.add_trace(go.Scatter(x=df["Datum"], y=df["Körperfett"],
                                      mode="lines+markers+text", text=df["Körperfett"].round(1),
                                      textposition="top center",
                                      hovertext=_kf_hover, hoverinfo="x+text",
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
                          "KF-Methode", "Muskelmasse", "PHV-Offset", "Reifestatus"]],
                     use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def _sprint_eingabe(distanz_label: str, key_prefix: str, letzter_row, col,
                    field_id: str = "", altersgruppe: str = "Senior"):
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
            norm_badge(bester, "sprint", field_id, col, altersgruppe=altersgruppe)
    return v1, v2, v3, bester


def page_sprint():
    st.markdown("# ⚡ Sprint-Diagnostik")
    st.markdown("Lineare Beschleunigung und Maximalgeschwindigkeit — 5 m bis 40 m, je 3 Versuche.")

    # ── Sicherheitshinweis & Testanleitung ────────────────────────────────────
    sicherheitshinweis_box()
    show_trainer_checkliste("sprint")
    show_test_info("sprint")
    _anleitung_download_button("sprint")

    auswahl = _player_selector("sprint")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_sprint = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_sprint or 0)

    letzter = sprint_letzter(sid)
    hist    = sprint_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprint_datum")
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")
        st.markdown("#### Zeiten eingeben (Sekunden) — Versuch 1 / 2 / 3")
        st.caption("Nicht gemessene Distanzen auf 0.00 lassen. ℹ️-Button neben jeder Distanz für Eingabehilfe.")

        c_l, c_r = st.columns(2)
        v1_5,  v2_5,  v3_5,  b5  = _sprint_eingabe("5 m",  "s5",  letzter, c_l, "sprint_5m",  altersgruppe)
        v1_10, v2_10, v3_10, b10 = _sprint_eingabe("10 m", "s10", letzter, c_l, "sprint_10m", altersgruppe)
        v1_20, v2_20, v3_20, b20 = _sprint_eingabe("20 m", "s20", letzter, c_r, "sprint_20m", altersgruppe)
        v1_30, v2_30, v3_30, b30 = _sprint_eingabe("30 m", "s30", letzter, c_r, "sprint_30m", altersgruppe)
        v1_40, v2_40, v3_40, b40 = _sprint_eingabe("40 m", "s40", letzter, c_l, "sprint_5m", altersgruppe)
        c_l.caption("40-m-Zeit nur eingeben wenn gemessen — sonst auf 0.00 lassen.")

        from sprint import (beschleunigungsindex, bewertung_sprint, bewertung_farbe,
                            SprintErgebnis as _SE)
        res = _SE(beste_5m=b5, beste_10m=b10, beste_20m=b20, beste_30m=b30,
                  geschlecht=geschl, niveau=niveau, alter=alter_sprint)

        if any([b5, b10, b20, b30, b40]):
            st.markdown("---")
            m1, m2, m3, m4, m5 = st.columns(5)
            if b10: m1.metric("10 m", f"{b10:.2f} s", res.bewertung_10m)
            if b20: m2.metric("20 m", f"{b20:.2f} s")
            if b30: m3.metric("30 m", f"{b30:.2f} s", res.bewertung_30m)
            if b40: m4.metric("40 m", f"{b40:.2f} s")
            if res.beschl_index: m5.metric("Beschl.-Index", f"{res.beschl_index:.3f}")
            from age_norms import normgruppe_label as _ngl
            st.caption(f"📊 {_ngl(alter_sprint)}")

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        # Plausibilitätsprüfung Sprint-Zeiten
        if b5 and b10 and b10 < b5:
            st.warning("⚠️ Plausibilitätsprüfung: Die 10-m-Zeit ist kleiner als die 5-m-Zeit — bitte Eingaben prüfen.")
        if b10 and b20 and b20 < b10:
            st.warning("⚠️ Plausibilitätsprüfung: Die 20-m-Zeit ist kleiner als die 10-m-Zeit — bitte Eingaben prüfen.")
        if b20 and b30 and b30 < b20:
            st.warning("⚠️ Plausibilitätsprüfung: Die 30-m-Zeit ist kleiner als die 20-m-Zeit — bitte Eingaben prüfen.")
        if b30 and b40 and b40 < b30:
            st.warning("⚠️ Plausibilitätsprüfung: Die 40-m-Zeit ist kleiner als die 30-m-Zeit — bitte Eingaben prüfen.")

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_sprint = render_observation_selector("sprint", sid, datum.strftime("%d.%m.%Y"), "sprint", standalone=False)
        _dup_spr = _duplikat_check("sprint", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="sprint_save", type="primary"):
            if _dup_spr == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any([b5, b10, b20, b30, b40]):
                st.error("Bitte mindestens eine Distanz eingeben.")
            else:
                from sprint import beschleunigungsindex, bewertung_sprint
                import json, datetime as _dtm
                _datum_spr = datum.strftime("%d.%m.%Y")
                if _dup_spr == "zweiter":
                    _datum_spr += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                sprint_speichern(
                    sid, _datum_spr,
                    v1_5, v2_5, v3_5, b5 or 0,
                    v1_10, v2_10, v3_10, b10 or 0,
                    v1_20, v2_20, v3_20, b20 or 0,
                    v1_30, v2_30, v3_30, b30 or 0,
                    res.beschl_index or 0,
                    res.bewertung_10m, res.bewertung_30m,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_40=v1_40, v2_40=v2_40, v3_40=v3_40, b40=b40,
                )
                if obs_sprint["beob_ids"] or obs_sprint.get("freitext"):
                    beobachtung_speichern(
                        sid, "sprint", _datum_spr,
                        json.dumps(obs_sprint["beob_ids"], ensure_ascii=False),
                        obs_sprint["seite"], obs_sprint["auspraegung"],
                        obs_sprint["freitext"], obs_sprint["text_generiert"],
                    )
                _save_ok("Sprint-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Sprint-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "5 m", "10 m", "20 m", "30 m", "40 m", "Beschl.-Index", "Bew. 10 m"]

        # ── Letzter Test ────────────────────────────────────────────────────
        if letzter:
            with st.expander("📋 Letzter gespeicherter Test", expanded=True):
                lt = letzter
                l1, l2, l3, l4, l5, l6 = st.columns(6)
                def _sm(col, label, val):
                    if val and val > 0:
                        col.metric(label, f"{val:.2f} s")
                _sm(l1, "5 m",  lt.get("beste_5m"))
                _sm(l2, "10 m", lt.get("beste_10m"))
                _sm(l3, "20 m", lt.get("beste_20m"))
                _sm(l4, "30 m", lt.get("beste_30m"))
                _sm(l5, "40 m", lt.get("beste_40m"))
                if lt.get("beschl_index"):
                    l6.metric("Beschl.-Index", f"{lt['beschl_index']:.3f}")
                if lt.get("bewertung_10m"):
                    st.caption(f"Bewertung 10 m: **{lt['bewertung_10m']}** | Datum: {lt.get('datum','—')}")

        # ── Verlaufschart ────────────────────────────────────────────────────
        fig = go.Figure()
        for col_name, color in [("10 m", "#3b82f6"), ("20 m", "#3fb950"),
                                  ("30 m", "#d29922"), ("40 m", "#a371f7"), ("5 m", "#f85149")]:
            sub = df[df[col_name] > 0] if col_name in df.columns else pd.DataFrame()
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

        # ── Zwei Termine vergleichen ─────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums = df["Datum"].tolist()
                cd1, cd2 = st.columns(2)
                d1 = cd1.selectbox("Termin 1", datums, index=0, key="spr_cmp_d1")
                d2 = cd2.selectbox("Termin 2", datums, index=len(datums)-1, key="spr_cmp_d2")
                r1 = df[df["Datum"] == d1].iloc[0]
                r2 = df[df["Datum"] == d2].iloc[0]
                compare_cols = ["5 m", "10 m", "20 m", "30 m", "40 m", "Beschl.-Index"]
                rows_cmp = []
                for c in compare_cols:
                    v1_c = r1.get(c, 0) or 0
                    v2_c = r2.get(c, 0) or 0
                    if v1_c > 0 or v2_c > 0:
                        diff = round(v2_c - v1_c, 3) if v1_c > 0 and v2_c > 0 else "—"
                        rows_cmp.append({"Messung": c, d1: f"{v1_c:.2f}" if v1_c else "—",
                                         d2: f"{v2_c:.2f}" if v2_c else "—",
                                         "Differenz": f"{diff:+.3f}" if isinstance(diff, float) else diff})
                if rows_cmp:
                    st.dataframe(pd.DataFrame(rows_cmp), use_container_width=True, hide_index=True)
                    st.caption("Differenz: negativ = schneller, positiv = langsamer")


# ──────────────────────────────────────────────────────────────────────────────

def page_sprung():
    st.markdown("# 🦘 Sprung-Diagnostik")
    st.markdown("Explosivkraft, Reaktivkraft und Seitenasymmetrie — CMJ, Squat Jump, Drop Jump, Standweitsprung.")

    sicherheitshinweis_box()
    show_trainer_checkliste("jump")
    show_test_info("jump")
    _anleitung_download_button("jump")

    auswahl = _player_selector("sprung")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_sprung = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_sprung or 0)

    letzter = sprung_letzter(sid)
    hist    = sprung_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    def _v3_sprung(label, key_pfx, max_val, step=0.5, col=None, field_id=""):
        """3-Versuch-Eingabe (Höhe cm oder Zeit s) — Bestwert = max()."""
        ct = col if col else st
        lbl_c, info_c = ct.columns([5, 1])
        lbl_c.markdown(f"**{label}**")
        if field_id:
            field_info_col(info_c, "jump", field_id)
        vc1, vc2, vc3, vbest = ct.columns(4)
        vc1.caption("V1"); vc2.caption("V2"); vc3.caption("V3"); vbest.caption("Bestwert")
        v1 = vc1.number_input(key_pfx+"v1", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v1", label_visibility="collapsed")
        v2 = vc2.number_input(key_pfx+"v2", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v2", label_visibility="collapsed")
        v3 = vc3.number_input(key_pfx+"v3", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v3", label_visibility="collapsed")
        vals = [v for v in [v1, v2, v3] if v > 0]
        best = max(vals) if vals else None
        if best:
            vbest.metric("✓", f"{best:.1f}")
            if field_id:
                norm_badge(best, "jump", field_id, ct, altersgruppe=altersgruppe)
        return (v1 or None), (v2 or None), (v3 or None), best

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprung_datum")
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")
        st.markdown("#### Sprünge — je 3 Versuche | Bestwert = max(V1, V2, V3)")
        st.caption("0.00 = Versuch nicht durchgeführt")

        c1, c2 = st.columns(2)

        v1_cb, v2_cb, v3_cb, b_cmj_beid = _v3_sprung("CMJ beidbeinig (cm)", "cmj_beid_", 100.0, col=c1, field_id="cmj_beid")
        v1_cr, v2_cr, v3_cr, b_cmj_r    = _v3_sprung("CMJ einbeinig rechts (cm)", "cmj_r_",  80.0,  col=c1, field_id="cmj_r")
        v1_cl, v2_cl, v3_cl, b_cmj_l    = _v3_sprung("CMJ einbeinig links (cm)",  "cmj_l_",  80.0,  col=c1, field_id="cmj_l")
        if b_cmj_r and b_cmj_l:
            c1.markdown(asymmetrie_badge_html(b_cmj_r, b_cmj_l, niedriger_besser=False), unsafe_allow_html=True)
        v1_sq, v2_sq, v3_sq, b_squat    = _v3_sprung("Squat Jump (cm)", "squat_", 100.0, col=c1, field_id="squat_jump")
        v1_dh, v2_dh, v3_dh, b_dj_h     = _v3_sprung("Drop Jump — Höhe (cm)", "dj_h_", 80.0, col=c2, field_id="dj_hoehe")
        v1_dk, v2_dk, v3_dk, b_dj_kz    = _v3_sprung("Drop Jump — KZ (s)", "dj_kz_", 2.0, step=0.01, col=c2, field_id="dj_kontakt")
        v1_sw, v2_sw, v3_sw, b_swj       = _v3_sprung("Standweitsprung (cm)", "swj_", 400.0, step=1.0, col=c2, field_id="standweit")

        from sprung import SprungErgebnis as _SpE
        res = _SpE(cmj_beid=b_cmj_beid, cmj_rechts=b_cmj_r, cmj_links=b_cmj_l,
                   squat_jump=b_squat, drop_jump_hoehe=b_dj_h, drop_jump_kz=b_dj_kz,
                   standweit=b_swj, geschlecht=geschl, niveau=niveau, alter=alter_sprung)

        if any([b_cmj_beid, b_cmj_r, b_cmj_l, b_squat, b_dj_h, b_swj]):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if b_cmj_beid: m1.metric("CMJ", f"{b_cmj_beid:.1f} cm", res.bewertung_cmj)
            if b_squat:    m2.metric("Squat Jump", f"{b_squat:.1f} cm")
            if res.rsi:    m3.metric("RSI", f"{res.rsi:.2f}", "gut" if res.rsi >= 1.5 else "niedrig")
            if res.cmj_asymmetrie:
                color_txt = "⚠️ auffällig" if res.cmj_asymmetrie > 10 else "✅ ok"
                m4.metric("Asymmetrie", f"{res.cmj_asymmetrie:.1f} %", color_txt)
            from age_norms import normgruppe_label as _ngl
            st.caption(f"📊 {_ngl(alter_sprung)}")
            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite: st.markdown(f"- {d}")

        # ── Plausibilitätsprüfung ──────────────────────────────────────────
        _sprung_warns = []
        if b_cmj_beid and b_cmj_beid > 80:
            _sprung_warns.append(f"CMJ beidbeinig {b_cmj_beid:.1f} cm (> 80 cm = absoluter Weltklasse-Wert)")
        if b_cmj_r and b_cmj_r > 70:
            _sprung_warns.append(f"CMJ rechts {b_cmj_r:.1f} cm (> 70 cm — bitte prüfen)")
        if b_cmj_l and b_cmj_l > 70:
            _sprung_warns.append(f"CMJ links {b_cmj_l:.1f} cm (> 70 cm — bitte prüfen)")
        if b_swj and b_swj > 330:
            _sprung_warns.append(f"Standweitsprung {b_swj:.0f} cm (> 330 cm = außergewöhnlich)")
        if _sprung_warns:
            st.warning(
                "⚠️ Ungewöhnliche Werte — bitte Eingaben prüfen (Speichern trotzdem möglich):\n"
                + "\n".join(f"• {w}" for w in _sprung_warns)
            )

        st.markdown("---")
        obs_sprung = render_observation_selector("sprung", sid, datum.strftime("%d.%m.%Y"), "sprung", standalone=False)
        _dup_spg = _duplikat_check("sprung", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="sprung_save", type="primary"):
            if _dup_spg == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any([b_cmj_beid, b_cmj_r, b_cmj_l, b_squat, b_dj_h, b_swj]):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json, datetime as _dtm
                _datum_spg = datum.strftime("%d.%m.%Y")
                if _dup_spg == "zweiter":
                    _datum_spg += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                sprung_speichern(
                    sid, _datum_spg,
                    b_cmj_beid or 0, b_cmj_r or 0, b_cmj_l or 0,
                    res.cmj_asymmetrie or 0,
                    b_squat or 0, b_dj_h or 0, b_dj_kz or 0,
                    res.rsi or 0, b_swj or 0,
                    res.bewertung_cmj,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_cmj_beid=v1_cb, v2_cmj_beid=v2_cb, v3_cmj_beid=v3_cb,
                    v1_cmj_r=v1_cr,    v2_cmj_r=v2_cr,    v3_cmj_r=v3_cr,
                    v1_cmj_l=v1_cl,    v2_cmj_l=v2_cl,    v3_cmj_l=v3_cl,
                    v1_squat=v1_sq,    v2_squat=v2_sq,    v3_squat=v3_sq,
                    v1_dj_h=v1_dh,     v2_dj_h=v2_dh,     v3_dj_h=v3_dh,
                    v1_dj_kz=v1_dk,    v2_dj_kz=v2_dk,    v3_dj_kz=v3_dk,
                    v1_swj=v1_sw,      v2_swj=v2_sw,       v3_swj=v3_sw,
                )
                if obs_sprung["beob_ids"] or obs_sprung.get("freitext"):
                    beobachtung_speichern(
                        sid, "sprung", _datum_spg,
                        json.dumps(obs_sprung["beob_ids"], ensure_ascii=False),
                        obs_sprung["seite"], obs_sprung["auspraegung"],
                        obs_sprung["freitext"], obs_sprung["text_generiert"],
                    )
                _save_ok("Sprung-Test gespeichert!")
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
            fig.update_layout(**_pl(height=280, title="CMJ & Squat Jump (cm)", yaxis=dict(title="cm")))
            st.plotly_chart(fig, use_container_width=True)
        with c_asym:
            sub_a = df[df["Asymmetrie %"] > 0]
            if not sub_a.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=sub_a["Datum"], y=sub_a["Asymmetrie %"],
                                      marker_color=["#f85149" if v > 10 else "#3fb950" for v in sub_a["Asymmetrie %"]],
                                      text=sub_a["Asymmetrie %"].round(1), textposition="outside"))
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922", annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=280, title="CMJ-Asymmetrie links/rechts"))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Keine einbeinigen CMJ-Werte vorhanden.")

        st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def _zeit_eingabe(label: str, key: str, col, letzter=None, letzter_key=None,
                  test_id: str = "", field_id: str = "", altersgruppe: str = "Senior"):
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
        norm_badge(v, test_id, field_id, col, altersgruppe=altersgruppe)
    return v if v > 0 else None


def page_agilitaet():
    st.markdown("# 🔀 Agilität & Richtungswechsel")
    st.markdown("505-Test, 5-10-5 Shuttle, T-Test, Illinois Agility Run — Richtungswechsel-Fähigkeit und Abbremsstärke.")

    sicherheitshinweis_box()
    show_trainer_checkliste("agility")
    show_test_info("agility")
    _anleitung_download_button("agility")

    auswahl = _player_selector("agil")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_agil = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_agil or 0)

    letzter = agilitaet_letzter(sid)
    hist    = agilitaet_history(sid)

    tab_neu, tab_verlauf, tab_info = st.tabs(["📋 Neuer Test", "📈 Verlauf", "ℹ️ Testbeschreibung"])

    def _v3_agil(label, key_pfx, col, field_id="", max_val=30.0):
        """3-Versuch-Eingabe (Zeiten s) — Bestzeit = min()."""
        if field_id:
            hdr, info = col.columns([5, 1])
            hdr.markdown(f"**{label}**")
            field_info_col(info, "agility", field_id)
        else:
            col.markdown(f"**{label}**")
        vc1, vc2, vc3, vbest = col.columns(4)
        vc1.caption("V1"); vc2.caption("V2"); vc3.caption("V3"); vbest.caption("Bestzeit")
        v1 = vc1.number_input(key_pfx+"v1", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v1", label_visibility="collapsed")
        v2 = vc2.number_input(key_pfx+"v2", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v2", label_visibility="collapsed")
        v3 = vc3.number_input(key_pfx+"v3", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v3", label_visibility="collapsed")
        vals = [v for v in [v1, v2, v3] if v > 0]
        best = min(vals) if vals else None
        if best:
            vbest.metric("s", f"{best:.2f}")
            if field_id:
                norm_badge(best, "agility", field_id, col, altersgruppe=altersgruppe)
        return (v1 or None), (v2 or None), (v3 or None), best

    _ALLE_AGIL = ["505-Test R/L", "5-10-5 Shuttle", "T-Test", "Illinois Agility",
                  "Modified T-Test", "Pro Agility Shuttle", "Arrowhead R/L", "Zig-Zag", "Balsom"]

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="agil_datum")
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")

        aktive_agil = st.multiselect(
            "Tests für diese Sitzung aktivieren — nicht benötigte Tests abwählen",
            _ALLE_AGIL, default=_ALLE_AGIL, key="agil_aktive_tests",
        )

        st.markdown("#### Zeiten — je 3 Versuche | Bestzeit = min(V1, V2, V3)")
        st.caption("0.00 = Versuch nicht durchgeführt")
        c1, c2 = st.columns(2)

        # ── Standardtests (mit Normbewertung) ─────────────────────────────
        v1_505r=v2_505r=v3_505r=t505_r = None
        v1_505l=v2_505l=v3_505l=t505_l = None
        v1_510=v2_510=v3_510=t5_10_5 = None
        v1_tt=v2_tt=v3_tt=t_test = None
        v1_ill=v2_ill=v3_ill=illinois = None

        if "505-Test R/L" in aktive_agil:
            v1_505r, v2_505r, v3_505r, t505_r = _v3_agil("505-Test rechts (s)", "a505r_", c1, field_id="t505_r")
            v1_505l, v2_505l, v3_505l, t505_l = _v3_agil("505-Test links (s)",  "a505l_", c1, field_id="t505_l")
            if t505_r and t505_l:
                c1.markdown(asymmetrie_badge_html(t505_r, t505_l, niedriger_besser=True), unsafe_allow_html=True)
        if "5-10-5 Shuttle" in aktive_agil:
            v1_510, v2_510, v3_510, t5_10_5 = _v3_agil("5-10-5 Shuttle (s)", "a5105_", c2, field_id="t5_10_5")
        if "T-Test" in aktive_agil:
            v1_tt, v2_tt, v3_tt, t_test = _v3_agil("T-Test (s)", "att_", c2, field_id="t_test")
        if "Illinois Agility" in aktive_agil:
            v1_ill, v2_ill, v3_ill, illinois = _v3_agil("Illinois Agility (s)", "aill_", c1, field_id="illinois")

        # ── Weitere Tests (ohne automatische Normbewertung) ───────────────
        v1_mtt=v2_mtt=v3_mtt=modified_t_test = None
        v1_pa=v2_pa=v3_pa=pro_agility = None
        v1_arr_r=v2_arr_r=v3_arr_r=arrowhead_r = None
        v1_arr_l=v2_arr_l=v3_arr_l=arrowhead_l = None
        v1_zz=v2_zz=v3_zz=zigzag = None
        v1_bal=v2_bal=v3_bal=balsom_t = None

        weitere_aktiv = [t for t in ["Modified T-Test","Pro Agility Shuttle","Arrowhead R/L","Zig-Zag","Balsom"]
                         if t in aktive_agil]
        if weitere_aktiv:
            st.markdown("---")
            st.markdown("##### Weitere Tests (Bestzeit erfassen)")
        if "Modified T-Test" in aktive_agil:
            v1_mtt, v2_mtt, v3_mtt, modified_t_test = _v3_agil("Modified T-Test (s)", "amtt_", c2, field_id="modified_t_test")
        if "Pro Agility Shuttle" in aktive_agil:
            v1_pa, v2_pa, v3_pa, pro_agility = _v3_agil("Pro Agility Shuttle (s)", "apa_", c1, field_id="pro_agility")
        if "Arrowhead R/L" in aktive_agil:
            v1_arr_r, v2_arr_r, v3_arr_r, arrowhead_r = _v3_agil("Arrowhead rechts (s)", "aarrr_", c2, field_id="arrowhead_r")
            v1_arr_l, v2_arr_l, v3_arr_l, arrowhead_l = _v3_agil("Arrowhead links (s)",  "adarrl_", c2, field_id="arrowhead_l")
            if arrowhead_r and arrowhead_l:
                c2.markdown(asymmetrie_badge_html(arrowhead_r, arrowhead_l, niedriger_besser=True), unsafe_allow_html=True)
        if "Zig-Zag" in aktive_agil:
            v1_zz, v2_zz, v3_zz, zigzag = _v3_agil("Zig-Zag Agility (s)", "azz_", c1, field_id="zigzag")
        if "Balsom" in aktive_agil:
            v1_bal, v2_bal, v3_bal, balsom_t = _v3_agil("Balsom Agility Test (s)", "abal_", c2, field_id="balsom")

        from agilitaet import AgilitaetErgebnis as _AE
        res = _AE(t505_r=t505_r, t505_l=t505_l, t5_10_5=t5_10_5,
                  t_test=t_test, illinois=illinois,
                  geschlecht=geschl, niveau=niveau, alter=alter_agil)

        alle_werte = [t505_r, t505_l, t5_10_5, t_test, illinois,
                      modified_t_test, pro_agility, arrowhead_r, arrowhead_l, zigzag, balsom_t]

        if any(alle_werte):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if t505_r:   m1.metric("505 rechts", f"{t505_r:.2f} s",   res.bew_505)
            if t505_l:   m2.metric("505 links",  f"{t505_l:.2f} s")
            if t_test:   m3.metric("T-Test",     f"{t_test:.2f} s",   res.bew_t_test)
            if illinois: m4.metric("Illinois",   f"{illinois:.2f} s", res.bew_illinois)
            from age_norms import normgruppe_label as _ngl
            st.caption(f"📊 {_ngl(alter_agil)}")
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
                for d in res.defizite: st.markdown(f"- {d}")

        st.markdown("---")
        obs_agil = render_observation_selector("agilitaet", sid, datum.strftime("%d.%m.%Y"), "agil", standalone=False)
        _dup_agil = _duplikat_check("agil", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="agil_save", type="primary"):
            if _dup_agil == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any(alle_werte):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json, datetime as _dtm
                _datum_agil = datum.strftime("%d.%m.%Y")
                if _dup_agil == "zweiter":
                    _datum_agil += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                agilitaet_speichern(
                    sid, _datum_agil,
                    t505_r or 0, t505_l or 0, res.asym_505 or 0,
                    t5_10_5 or 0, t_test or 0, illinois or 0,
                    res.bew_505, res.bew_t_test, res.bew_illinois,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_t505_r=v1_505r, v2_t505_r=v2_505r, v3_t505_r=v3_505r,
                    v1_t505_l=v1_505l, v2_t505_l=v2_505l, v3_t505_l=v3_505l,
                    v1_t5_10_5=v1_510, v2_t5_10_5=v2_510, v3_t5_10_5=v3_510,
                    v1_t_test=v1_tt,   v2_t_test=v2_tt,   v3_t_test=v3_tt,
                    v1_illinois=v1_ill, v2_illinois=v2_ill, v3_illinois=v3_ill,
                    modified_t_test=modified_t_test, pro_agility=pro_agility,
                    arrowhead_r=arrowhead_r, arrowhead_l=arrowhead_l,
                    zigzag=zigzag, balsom=balsom_t,
                    v1_modified_t_test=v1_mtt, v2_modified_t_test=v2_mtt, v3_modified_t_test=v3_mtt,
                    v1_pro_agility=v1_pa, v2_pro_agility=v2_pa, v3_pro_agility=v3_pa,
                    v1_arrowhead_r=v1_arr_r, v2_arrowhead_r=v2_arr_r, v3_arrowhead_r=v3_arr_r,
                    v1_arrowhead_l=v1_arr_l, v2_arrowhead_l=v2_arr_l, v3_arrowhead_l=v3_arr_l,
                    v1_zigzag=v1_zz, v2_zigzag=v2_zz, v3_zigzag=v3_zz,
                    v1_balsom=v1_bal, v2_balsom=v2_bal, v3_balsom=v3_bal,
                )
                if obs_agil["beob_ids"] or obs_agil.get("freitext"):
                    beobachtung_speichern(
                        sid, "agilitaet", _datum_agil,
                        json.dumps(obs_agil["beob_ids"], ensure_ascii=False),
                        obs_agil["seite"], obs_agil["auspraegung"],
                        obs_agil["freitext"], obs_agil["text_generiert"],
                    )
                _save_ok("Agilität-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Agilität-Tests vorhanden.")
        else:
            df = pd.DataFrame(hist)
            df.columns = ["Datum", "505 R", "505 L", "Asymmetrie %",
                          "5-10-5", "T-Test", "Illinois", "Bew. T-Test",
                          "Mod. T-Test", "Pro Agility", "Arrowhead R", "Arrowhead L",
                          "Zig-Zag", "Balsom"]

            # Letzter Test
            if letzter:
                with st.expander("📋 Letzter gespeicherter Test", expanded=True):
                    la = letzter
                    _agil_zeiten = [
                        ("505 R", la.get("t505_r")), ("505 L", la.get("t505_l")),
                        ("5-10-5", la.get("t5_10_5")), ("T-Test", la.get("t_test")),
                        ("Illinois", la.get("illinois")),
                        ("Mod. T-Test", la.get("modified_t_test")),
                        ("Pro Agility", la.get("pro_agility")),
                        ("Arrow. R", la.get("arrowhead_r")),
                        ("Arrow. L", la.get("arrowhead_l")),
                        ("Zig-Zag", la.get("zigzag")),
                        ("Balsom", la.get("balsom")),
                    ]
                    vorh = [(lbl, v) for lbl, v in _agil_zeiten if v and float(v) > 0]
                    if vorh:
                        cols_la = st.columns(min(len(vorh), 6))
                        for i, (lbl, v) in enumerate(vorh[:6]):
                            cols_la[i].metric(lbl, f"{float(v):.2f} s")
                        if len(vorh) > 6:
                            cols_la2 = st.columns(len(vorh) - 6)
                            for i, (lbl, v) in enumerate(vorh[6:]):
                                cols_la2[i].metric(lbl, f"{float(v):.2f} s")
                    st.caption(f"Datum: {la.get('datum','—')}")

            fig = go.Figure()
            for col_name, clr in [("T-Test","#3b82f6"),("Illinois","#3fb950"),
                                   ("5-10-5","#d29922"),("505 R","#f85149"),("505 L","#a371f7"),
                                   ("Mod. T-Test","#79c0ff"),("Pro Agility","#56d364"),
                                   ("Arrowhead R","#ffa657"),("Arrowhead L","#ff7b72"),
                                   ("Zig-Zag","#bc8cff"),("Balsom","#e3b341")]:
                if col_name not in df.columns: continue
                sub = df[df[col_name] > 0]
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                         mode="lines+markers", name=col_name,
                                         line=dict(color=clr, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=350, title="Agilitätszeiten-Verlauf (s)",
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
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922", annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=240, title="505-Asymmetrie R vs. L (%)"))
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

            if len(df) >= 2:
                with st.expander("🔍 Zwei Termine vergleichen"):
                    datums_a = df["Datum"].tolist()
                    ac1, ac2 = st.columns(2)
                    ad1 = ac1.selectbox("Termin 1", datums_a, index=0, key="agil_cmp_d1")
                    ad2 = ac2.selectbox("Termin 2", datums_a, index=len(datums_a)-1, key="agil_cmp_d2")
                    ar1 = df[df["Datum"] == ad1].iloc[0]
                    ar2 = df[df["Datum"] == ad2].iloc[0]
                    cmp_cols_a = ["505 R","505 L","5-10-5","T-Test","Illinois",
                                  "Mod. T-Test","Pro Agility","Arrowhead R","Arrowhead L","Zig-Zag","Balsom"]
                    rows_a = []
                    for ca in cmp_cols_a:
                        if ca not in df.columns: continue
                        v1a = ar1.get(ca, 0) or 0
                        v2a = ar2.get(ca, 0) or 0
                        if v1a > 0 or v2a > 0:
                            diff_a = round(v2a - v1a, 3) if v1a > 0 and v2a > 0 else "—"
                            rows_a.append({"Test": ca, ad1: f"{v1a:.2f}" if v1a else "—",
                                           ad2: f"{v2a:.2f}" if v2a else "—",
                                           "Differenz": f"{diff_a:+.3f}" if isinstance(diff_a, float) else diff_a})
                    if rows_a:
                        st.dataframe(pd.DataFrame(rows_a), use_container_width=True, hide_index=True)
                        st.caption("Differenz: negativ = schneller, positiv = langsamer")

    with tab_info:
        # ── Standardtests mit Normbewertung ──────────────────────────────────
        st.markdown("#### Standardtests — mit automatischer Normbewertung ✅")
        _agil_info_std = [
            ("assets/tests/agility/test_505.svg",    "505-Test R/L",
             "10 m anlaufen → 180° Wendung → 5 m Sprint\nGetrennt für rechts und links. Asymmetrie > 10 % = trainingsrelevant."),
            ("assets/tests/agility/shuttle_5_10_5.svg", "5-10-5 Shuttle",
             "5 m links → 10 m rechts → 5 m zurück zur Mitte\nShuttle-Beschleunigung und Abbremsfähigkeit."),
            ("assets/tests/agility/t_test.svg",      "T-Test",
             "9,14 m vor → je 4,57 m seitwärts → rückwärts\nMehrdirektionale Agilität: vorwärts, lateral, rückwärts."),
            ("assets/tests/agility/illinois.svg",    "Illinois Agility",
             "10 m Slalomkurs mit 8 Kegeln\nGesamtagilität und Richtungswechselgeschwindigkeit."),
        ]
        cols_std = st.columns(4)
        for i, (svg, name, desc) in enumerate(_agil_info_std):
            with cols_std[i]:
                st.markdown(f"**{name}**")
                try:
                    st.image(svg, width="stretch")
                except Exception:
                    st.caption("(Skizze nicht verfügbar)")
                st.caption(desc)

        st.markdown("---")
        st.markdown("#### Weitere Tests — Bestzeit erfassen")
        _agil_info_neu = [
            ("assets/tests/agility/modified_t_test.svg", "Modified T-Test",
             "Kürzere T-Test-Variante\nStart → A (9,15 m) → B links → C rechts → A → Start"),
            ("assets/tests/agility/pro_agility.svg",     "Pro Agility Shuttle",
             "NFL-Combine-Standard (5-10-5)\n5 yd links → 10 yd rechts → 5 yd zurück"),
            ("assets/tests/agility/arrowhead.svg",       "Arrowhead R/L",
             "Pfeilförmiges Muster, bilateral\nStart → Spitze → Kegel rechts/links → Start"),
            ("assets/tests/agility/zigzag.svg",          "Zig-Zag Agility",
             "4–5 Kegel im Zickzack\nca. 20–25 m, Kurskontrolle"),
            ("assets/tests/agility/balsom.svg",          "Balsom Agility Test",
             "4×4 m Rechteck + Mittelpunkt\n3 Läufe à 25 s, Richtungswechsel zählen"),
        ]
        cols_neu = st.columns(5)
        for i, (svg, name, desc) in enumerate(_agil_info_neu):
            with cols_neu[i]:
                st.markdown(f"**{name}**")
                try:
                    st.image(svg, width="stretch")
                except Exception:
                    st.caption("(Skizze nicht verfügbar)")
                st.caption(desc)


# ──────────────────────────────────────────────────────────────────────────────

ALTERSGRUPPEN_YO = ["U8/U9", "U10/U11", "U12/U13", "U13/U14", "U15/U16", "U17/U18", "Senioren"]


# ──────────────────────────────────────────────────────────────────────────────
# SPIROERGOMETRIE-STUFENTEST (innerhalb Ausdauerbereich)
# ──────────────────────────────────────────────────────────────────────────────

def _page_spiro():
    """Spiroergometrie-Stufentest — Eingabe, Auswertung, Verlauf & Vergleich."""
    from spiro import (
        interpoliere_bei_laktat as _ibl,
        kurvenverschiebung_bewerten as _kvb,
        protokolle_vergleichbar as _pv,
        schwellenvergleich_tabelle as _svt,
        trainingsbereiche_aus_schwellen as _tbs,
        GERAETEARTEN, SCHWELLENMETHODEN,
    )

    st.markdown(
        '<div style="background:#1a2233;border:1px solid #3b82f6;border-radius:8px;'
        'padding:12px 16px;margin-bottom:14px;font-size:13px;color:#cdd9e5">'
        'ℹ️ <b>Hinweis:</b> Diese App führt keine Spiroergometrie durch. Sie dient zur '
        'strukturierten Erfassung, Auswertung und Verlaufskontrolle von Ergebnissen '
        'fachgerecht durchgeführter Tests. Keine medizinische Diagnose, keine Sportfreigabe.'
        '</div>',
        unsafe_allow_html=True,
    )

    auswahl = _player_selector("spiro")
    if not auswahl:
        return
    sid = auswahl["id"]

    alle_tests      = spiro_test_alle(sid)
    alle_protokolle = spiro_protokoll_alle()

    tab_neu, tab_ausw, tab_vgl = st.tabs([
        "📋 Neuer Test", "📊 Auswertung", "📈 Verlauf & Vergleich"
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1 — NEUER TEST
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_neu:
        # ── Protokoll ─────────────────────────────────────────────────────────
        st.markdown("### Testprotokoll")
        prot_optionen = ["— Kein Protokoll —"] + [
            f"{p['name']} ({p.get('geraeteart','?')}, "
            f"Start {p.get('startgeschwindigkeit','?')} km/h, "
            f"+{p.get('steigerung','?')} km/h, "
            f"{p.get('stufendauer','?')} min)"
            for p in alle_protokolle
        ]
        prot_wahl = st.selectbox("Protokoll auswählen", prot_optionen, key="spiro_prot_wahl")
        prot_id   = None
        if prot_wahl != "— Kein Protokoll —" and alle_protokolle:
            prot_idx = prot_optionen.index(prot_wahl) - 1
            prot_id  = alle_protokolle[prot_idx]["id"] if 0 <= prot_idx < len(alle_protokolle) else None

        with st.expander("➕ Neues Protokoll erstellen / speichern"):
            pn_name = st.text_input("Protokollname *", key="prot_name",
                                    placeholder="z.B. IAT-Laufband-Standard 3 min")
            pc1, pc2 = st.columns(2)
            pn_geraet    = pc1.selectbox("Geräteart", GERAETEARTEN, key="prot_geraet")
            pn_start     = pc1.number_input("Startgeschwindigkeit (km/h)", 2.0, 20.0, 8.0, 0.5, key="prot_start")
            pn_steigerung= pc2.number_input("Steigerung pro Stufe (km/h)",  0.5,  4.0, 2.0, 0.5, key="prot_steig")
            pn_dauer     = pc2.number_input("Stufendauer (min)",             1.0, 10.0, 3.0, 0.5, key="prot_dauer")
            pn_steigung  = pc1.number_input("Laufbandsteigung (%)",          0.0, 15.0, 1.0, 0.5, key="prot_steigung")
            pn_pause     = pc2.number_input("Pausendauer Blutabnahme (s)",     0,  120,  30,   5, key="prot_pause")
            if st.button("💾 Protokoll speichern", key="prot_save", type="primary", use_container_width=True):
                if not pn_name.strip():
                    st.error("Protokollname ist erforderlich.")
                else:
                    spiro_protokoll_speichern(
                        pn_name.strip(), pn_geraet, pn_start, pn_steigerung,
                        pn_dauer, pn_steigung, pn_pause / 60,
                    )
                    st.success("✅ Protokoll gespeichert.")
                    st.rerun()

        st.markdown("---")

        # ── Testmetadaten ─────────────────────────────────────────────────────
        st.markdown("### Testdaten")
        d1, d2 = st.columns(2)
        # Datum nach erfolgreichem Speichern erhalten (spiro_saved_datum wird beim Speichern gesetzt)
        if "spiro_saved_datum" in st.session_state and "spiro_datum" not in st.session_state:
            st.session_state["spiro_datum"] = st.session_state.pop("spiro_saved_datum")
        elif "spiro_saved_datum" in st.session_state:
            st.session_state.pop("spiro_saved_datum", None)
        datum_spiro = d1.date_input("Testdatum *", value=date.today(), key="spiro_datum")
        if datum_spiro > date.today():
            d1.warning("⚠️ Datum in der Zukunft.")
        geraeteart_spiro = d2.selectbox("Geräteart *", GERAETEARTEN, key="spiro_geraet")
        d3, d4 = st.columns(2)
        testort_spiro = d3.text_input("Testort", key="spiro_testort")
        tester_spiro  = d4.text_input("Tester / Trainer", key="spiro_tester")

        st.markdown("**Testumfang (Mehrfachauswahl möglich)**")
        tm1, tm2 = st.columns(2)
        mit_spiro_cb  = tm1.checkbox("Mit Atemgasanalyse (Spirometrie)", key="spiro_mit_spiro")
        mit_laktat_cb = tm2.checkbox("Mit kapillarer Laktatmessung",     key="spiro_mit_laktat")

        with st.expander("Optionale Testbedingungen"):
            oc1, oc2 = st.columns(2)
            raumtemp_spiro = oc1.number_input("Raumtemperatur (°C)", -10.0, 45.0, 20.0, 0.5, key="spiro_temp")
            kgew_default   = float((anthropometrie_letzter(sid) or {}).get("gewicht") or 75.0)
            kgew_spiro     = oc2.number_input("Körpergewicht (kg)", 20.0, 200.0, kgew_default, 0.5, key="spiro_kgew")
            mahlzeit_spiro = oc1.text_input("Letzte Mahlzeit (wann, was)", key="spiro_mahlzeit")
            einheit_spiro  = oc2.text_input("Letzte intensive Einheit (wann)", key="spiro_letzte_einheit")
            beschw_spiro   = st.text_area("Akute Beschwerden", key="spiro_beschw", height=55)

        # Laktat-Sicherheitshinweis
        ruhelaktat_spiro = None
        blut_ort_spiro   = None
        geraet_spiro     = None
        if mit_laktat_cb:
            st.warning(
                "⚠️ **Sicherheitshinweis Laktatmessung:** Kapillare Blutentnahmen dürfen nur von "
                "entsprechend eingewiesenen Personen unter Einhaltung der geltenden Hygiene-, "
                "Arbeitsschutz- und Entsorgungsvorgaben durchgeführt werden. "
                "Diese App ist kein Ersatz für eine fachliche Einweisung."
            )
            ll1, ll2 = st.columns(2)
            ruhelaktat_spiro = ll1.number_input(
                "Ruhe-Laktat (mmol/l) — leer lassen wenn nicht gemessen",
                0.0, 20.0, 0.0, 0.1, key="spiro_ruhelaktat",
            )
            blut_ort_spiro = ll2.selectbox(
                "Blutentnahmeort", ["Ohrläppchen", "Fingerbeere", "Anderes"], key="spiro_blut_ort"
            )
            geraet_spiro = ll1.text_input("Messgerät / Chargennummer", key="spiro_laktat_geraet")

        st.markdown("---")

        # ── Stufentabelle (dynamisch via st.data_editor) ──────────────────────
        st.markdown("### Belastungsstufen")
        st.caption(
            "Stufen manuell eintragen oder bei ausgewähltem Protokoll automatisch befüllen. "
            "Fehlende Messwerte **leer lassen** — nicht 0 eintragen."
        )

        # Spalten je nach Testumfang
        base_stufen_cols = [
            "Stufe", "Geschw. (km/h)", "Steigung (%)", "HF Ende (bpm)", "RPE (0–10)",
            "✓ vollst.", "Bemerkung",
        ]
        base_stufen_keys = [
            "stufennummer", "geschwindigkeit_kmh", "steigung_prozent",
            "herzfrequenz_bpm", "rpe", "stufe_vollstaendig", "bemerkung",
        ]
        if mit_laktat_cb:
            base_stufen_cols += ["Laktat (mmol/l)", "Probe ✓"]
            base_stufen_keys += ["laktat_mmol_l", "blutprobe_gueltig"]
        if mit_spiro_cb:
            base_stufen_cols += ["VO₂ rel. (ml/kg/min)", "VO₂ abs. (l/min)", "RER"]
            base_stufen_keys += ["vo2_relativ", "vo2_absolut", "rer"]

        # Auto-Befüllung aus Protokoll
        if st.button("🔄 Stufen aus Protokoll befüllen", key="spiro_fill_prot",
                     disabled=(prot_id is None)):
            p_data = next((p for p in alle_protokolle if p["id"] == prot_id), None)
            if p_data and p_data.get("startgeschwindigkeit") and p_data.get("steigerung"):
                n_max = int(p_data.get("max_stufen") or 10)
                rows = []
                for i in range(n_max):
                    v_kmh = round(p_data["startgeschwindigkeit"] + i * p_data["steigerung"], 1)
                    row   = dict(zip(base_stufen_cols,
                                    [i+1, v_kmh, p_data.get("steigung", 0),
                                     None, None, True, ""] +
                                    ([None, True] if mit_laktat_cb else []) +
                                    ([None, None, None] if mit_spiro_cb else [])))
                    rows.append(row)
                st.session_state[f"spiro_editor_{sid}_data"] = rows

        # data_editor
        existing_rows = st.session_state.get(f"spiro_editor_{sid}_data", [])
        df_init = (pd.DataFrame(existing_rows, columns=base_stufen_cols)
                   if existing_rows else pd.DataFrame(columns=base_stufen_cols))

        col_cfg = {
            "Stufe":            st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
            "Geschw. (km/h)":   st.column_config.NumberColumn(min_value=0, step=0.5, format="%.1f"),
            "Steigung (%)":     st.column_config.NumberColumn(min_value=0, step=0.5, format="%.1f"),
            "HF Ende (bpm)":    st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
            "RPE (0–10)":       st.column_config.NumberColumn(min_value=0, max_value=10,  step=1),
            "✓ vollst.":        st.column_config.CheckboxColumn(default=True),
            "Laktat (mmol/l)":  st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f",
                                    help="Leer lassen wenn nicht gemessen — nicht 0 eintragen"),
            "Probe ✓":          st.column_config.CheckboxColumn(default=True),
            "VO₂ rel. (ml/kg/min)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "VO₂ abs. (l/min)": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
            "RER":              st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
        }
        edited_stufen = st.data_editor(
            df_init,
            num_rows="dynamic",
            use_container_width=True,
            key=f"spiro_stufen_editor_{sid}",
            column_config={k: v for k, v in col_cfg.items() if k in base_stufen_cols},
        )

        # Plausibilitätsprüfung
        if not edited_stufen.empty:
            df_check = edited_stufen.dropna(subset=["Stufe"])
            if df_check["Stufe"].duplicated().any():
                st.warning("⚠️ Doppelte Stufennummern erkannt.")
            hf_vals = df_check.get("HF Ende (bpm)", pd.Series()).dropna()
            if len(hf_vals) and ((hf_vals <= 0).any() or (hf_vals > 250).any()):
                st.warning("⚠️ Herzfrequenz außerhalb des Bereichs 1–250 bpm.")
            if mit_laktat_cb and "Laktat (mmol/l)" in df_check.columns:
                lak = df_check["Laktat (mmol/l)"].dropna()
                if (lak < 0).any():
                    st.warning("⚠️ Negativer Laktatwert erkannt.")
                if (lak == 0).any():
                    st.warning("⚠️ Laktat = 0 mmol/l: Bitte leer lassen wenn nicht gemessen.")

        # Nachbelastung
        edited_nb = None
        if mit_laktat_cb or mit_spiro_cb:
            st.markdown("---")
            st.markdown("### Nachbelastungswerte (optional)")
            nb_df = pd.DataFrame(
                [{"Zeit (min)": t, "HF (bpm)": None, "Laktat (mmol/l)": None, "Bemerkung": ""}
                 for t in [1, 3, 5]],
            )
            edited_nb = st.data_editor(
                nb_df, num_rows="dynamic", use_container_width=True, key=f"spiro_nb_{sid}",
                column_config={
                    "Zeit (min)":       st.column_config.NumberColumn(min_value=0, step=1),
                    "HF (bpm)":         st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
                    "Laktat (mmol/l)":  st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
                },
            )

        # Atemgas-Kennwerte
        vo2_peak_v = vo2_max_v = hf_max_spiro = None
        vt1_v_s = vt1_h_s = vt2_v_s = vt2_h_s = None
        if mit_spiro_cb:
            st.markdown("---")
            st.markdown("### Atemgas-Kennwerte (Spiro-Zusammenfassung)")
            st.caption("Direkt gemessene Werte aus dem Spiroergometrie-Gerät — kein VO₂max ohne Ausbelastungsnachweis.")
            sg1, sg2, sg3 = st.columns(3)
            vo2_peak_v   = sg1.number_input("VO₂peak (ml/kg/min)", 0.0, 100.0, 0.0, 0.1, key="spiro_vo2peak")
            vo2_max_v    = sg2.number_input("VO₂max — nur wenn Kriterien erfüllt", 0.0, 100.0, 0.0, 0.1, key="spiro_vo2max")
            hf_max_spiro = sg3.number_input("HF max (bpm)", 0, 250, 0, 1, key="spiro_hf_max")
            sg4, sg5 = st.columns(2)
            vt1_v_s = sg4.number_input("VT1 Geschwindigkeit (km/h)", 0.0, 30.0, 0.0, 0.1, key="spiro_vt1_v")
            vt1_h_s = sg5.number_input("VT1 Herzfrequenz (bpm)",     0, 250, 0, 1, key="spiro_vt1_hf")
            vt2_v_s = sg4.number_input("VT2 Geschwindigkeit (km/h)", 0.0, 30.0, 0.0, 0.1, key="spiro_vt2_v")
            vt2_h_s = sg5.number_input("VT2 Herzfrequenz (bpm)",     0, 250, 0, 1, key="spiro_vt2_hf")
            st.info("ℹ️ VO₂max gilt nur bei dokumentierten Ausbelastungskriterien (RER ≥ 1,10, plateau, HF max). Ohne Nachweis: VO₂peak verwenden.")

        # Maximale Werte & Schwelle
        st.markdown("---")
        st.markdown("### Maximale Testwerte")
        mv1, mv2 = st.columns(2)
        v_max_spiro = mv1.number_input("Maximale Geschwindigkeit (km/h)", 0.0, 40.0, 0.0, 0.1, key="spiro_v_max")
        rpe_max_s   = mv2.number_input("RPE max (0–10)", 0, 10, 10, 1, key="spiro_rpe_max")
        abbruch_s   = st.text_input("Abbruchgrund (falls nicht vollständig absolviert)", key="spiro_abbruch")

        # ── Auto-Schwellenberechnung (aus Laktat-Kurve) ──────────────────────
        if mit_laktat_cb and not edited_stufen.empty:
            _auto_stufen = []
            for _, _row in edited_stufen.dropna(subset=["Stufe"]).iterrows():
                _auto_stufen.append({
                    "geschwindigkeit_kmh": _row.get("Geschw. (km/h)"),
                    "laktat_mmol_l":       _row.get("Laktat (mmol/l)"),
                    "herzfrequenz_bpm":    _row.get("HF Ende (bpm)"),
                    "blutprobe_gueltig":   _row.get("Probe ✓", True),
                })
            _hat_laktat = any(
                s["laktat_mmol_l"] is not None and not (isinstance(s["laktat_mmol_l"], float) and pd.isna(s["laktat_mmol_l"]))
                for s in _auto_stufen
            )
            if _hat_laktat:
                ac1, ac2 = st.columns([3, 1])
                ac1.caption("💡 Laktat-Daten vorhanden — Schwellenwerte können automatisch berechnet werden (2 mmol/l oder 4 mmol/l Interpolation).")
                _calc_ziel = ac2.selectbox("Ziel-Laktat", ["2 mmol/l", "4 mmol/l"], key="spiro_calc_ziel")
                if st.button("🔢 Schwellen automatisch berechnen", key="spiro_auto_calc"):
                    _lak_ziel = 2.0 if "2" in _calc_ziel else 4.0
                    _res_v = _ibl(_auto_stufen, _lak_ziel)
                    if _res_v:
                        st.session_state["spiro_schw_v"]    = float(_res_v["x_wert"])
                        st.session_state["spiro_schwmeth"]  = f"Fixer Wert {int(_lak_ziel)} mmol/l"
                        # Schwellen-HF per linearer Interpolation auf geschw ermitteln
                        _res_hf = _ibl(
                            [{"geschwindigkeit_kmh": s["geschwindigkeit_kmh"],
                              "laktat_mmol_l": s["herzfrequenz_bpm"],
                              "blutprobe_gueltig": True}
                             for s in _auto_stufen if s.get("herzfrequenz_bpm") and s.get("geschwindigkeit_kmh")],
                            _res_v["x_wert"],
                        )
                        if _res_hf:
                            st.session_state["spiro_schw_hf"] = float(_res_hf["x_wert"])
                        st.session_state["spiro_schw_lak"] = _lak_ziel
                        st.success(f"✅ Schwelle bei {_lak_ziel} mmol/l → {_res_v['x_wert']:.1f} km/h berechnet. Werte in Expander übernommen.")
                    else:
                        st.warning(f"⚠️ Interpolation bei {_lak_ziel} mmol/l nicht möglich — Laktat-Wert liegt außerhalb des gemessenen Bereichs.")

        with st.expander("Schwellenwert eintragen / überschreiben"):
            schw_meth = st.selectbox("Schwellenmethode", ["—"] + SCHWELLENMETHODEN, key="spiro_schwmeth")
            sw1, sw2, sw3 = st.columns(3)
            schw_v   = sw1.number_input("Schwelle Geschwindigkeit (km/h)", 0.0, 30.0, step=0.1, format="%.1f", key="spiro_schw_v")
            schw_hf  = sw2.number_input("Schwelle Herzfrequenz (bpm)",     0, 250, step=1, key="spiro_schw_hf")
            schw_lak = sw3.number_input("Schwelle Laktat (mmol/l)",        0.0, 20.0, step=0.1, format="%.1f", key="spiro_schw_lak")
            st.caption("✏️ Berechnete Werte können hier manuell angepasst oder überschrieben werden.")

        bemerkung_s = st.text_area("Bemerkungen", key="spiro_bemerkung", height=65)

        # ── Speichern ─────────────────────────────────────────────────────────
        st.markdown("---")
        if st.button("💾 Stufentest speichern", use_container_width=True, key="spiro_save", type="primary"):
            df_valid = edited_stufen.dropna(subset=["Stufe"]) if not edited_stufen.empty else pd.DataFrame()
            if df_valid.empty:
                st.error("Bitte mindestens eine Belastungsstufe eintragen.")
            else:
                # HF max automatisch aus Stufen wenn nicht manuell
                hf_max_eff = hf_max_spiro or None
                if not hf_max_eff and "HF Ende (bpm)" in df_valid.columns:
                    hf_series = df_valid["HF Ende (bpm)"].dropna()
                    if not hf_series.empty:
                        hf_max_eff = float(hf_series.max())
                v_max_eff = v_max_spiro or None
                if not v_max_eff and "Geschw. (km/h)" in df_valid.columns:
                    v_series = df_valid["Geschw. (km/h)"].dropna()
                    if not v_series.empty:
                        v_max_eff = float(v_series.max())

                testtyp_s = (
                    "spiro_laufband" if "Laufband" in geraeteart_spiro
                    else "spiro_feld" if "Feld" in geraeteart_spiro
                    else "spiro_fahrrad_optional"
                )
                test_id = spiro_test_speichern(
                    spieler_id=sid,
                    datum=datum_spiro.strftime("%Y-%m-%d"),
                    testtyp=testtyp_s,
                    geraeteart=geraeteart_spiro,
                    protokoll_id=prot_id,
                    testort=testort_spiro or None,
                    tester=tester_spiro or None,
                    mit_spiro=1 if mit_spiro_cb else 0,
                    mit_laktat=1 if mit_laktat_cb else 0,
                    raumtemperatur=raumtemp_spiro if raumtemp_spiro != 20.0 else None,
                    letzte_mahlzeit=mahlzeit_spiro or None,
                    letzte_intensive_einheit=einheit_spiro or None,
                    akute_beschwerden=beschw_spiro or None,
                    koerpergewicht=kgew_spiro if kgew_spiro != 75.0 else None,
                    maximale_geschwindigkeit=v_max_eff,
                    maximale_herzfrequenz=hf_max_eff,
                    vo2_peak=vo2_peak_v or None,
                    vo2_max=vo2_max_v or None,
                    vt1_geschwindigkeit=vt1_v_s or None,
                    vt1_herzfrequenz=vt1_h_s or None,
                    vt2_geschwindigkeit=vt2_v_s or None,
                    vt2_herzfrequenz=vt2_h_s or None,
                    laktatschwelle_methode=schw_meth if schw_meth != "—" else None,
                    schwelle_geschwindigkeit=schw_v or None,
                    schwelle_herzfrequenz=schw_hf or None,
                    schwelle_laktat=schw_lak or None,
                    ruhelaktat=ruhelaktat_spiro if (ruhelaktat_spiro and ruhelaktat_spiro > 0) else None,
                    laktat_blutentnahmeort=blut_ort_spiro,
                    laktat_messgeraet=geraet_spiro or None,
                    rpe_max=rpe_max_s or None,
                    abbruchgrund=abbruch_s or None,
                    bemerkung=bemerkung_s or None,
                )
                # Stufen speichern
                stufen_liste = []
                for _, row in df_valid.iterrows():
                    stufe_dict = {}
                    for col_name, key_name in zip(base_stufen_cols, base_stufen_keys):
                        val = row.get(col_name)
                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            stufe_dict[key_name] = None
                        else:
                            stufe_dict[key_name] = val
                    # Laktat 0 → None (keine Messung)
                    if stufe_dict.get("laktat_mmol_l") == 0:
                        stufe_dict["laktat_mmol_l"] = None
                    stufen_liste.append(stufe_dict)
                spiro_stufen_speichern(test_id, stufen_liste)
                # Nachbelastung speichern
                if edited_nb is not None and not edited_nb.empty:
                    nb_liste = []
                    for _, nb_row in edited_nb.iterrows():
                        t_min = nb_row.get("Zeit (min)")
                        if t_min is None or (isinstance(t_min, float) and pd.isna(t_min)):
                            continue
                        nb_liste.append({
                            "zeitpunkt_minuten": t_min,
                            "herzfrequenz_bpm": None if (nb_row.get("HF (bpm)") is None or pd.isna(nb_row.get("HF (bpm)", float("nan")))) else nb_row["HF (bpm)"],
                            "laktat_mmol_l":    None if (nb_row.get("Laktat (mmol/l)") is None or pd.isna(nb_row.get("Laktat (mmol/l)", float("nan")))) else nb_row["Laktat (mmol/l)"],
                            "bemerkung":        nb_row.get("Bemerkung") or None,
                        })
                    spiro_nachbelastung_speichern(test_id, nb_liste)
                # Datum und Tester erhalten, alles andere zurücksetzen
                _saved_date = datum_spiro
                _clear_keys = [
                    "spiro_mit_spiro", "spiro_mit_laktat",
                    "spiro_vo2peak", "spiro_vo2max", "spiro_hf_max",
                    "spiro_vt1_v", "spiro_vt1_hf", "spiro_vt2_v", "spiro_vt2_hf",
                    "spiro_schw_v", "spiro_schw_hf", "spiro_schw_lak", "spiro_schwmeth",
                    "spiro_v_max", "spiro_rpe_max", "spiro_abbruch", "spiro_bemerkung",
                    "spiro_ruhelaktat", "spiro_mahlzeit", "spiro_letzte_einheit",
                    "spiro_beschw", "spiro_temp", "spiro_kgew",
                    f"spiro_editor_{sid}_data", f"spiro_stufen_editor_{sid}",
                    f"spiro_nb_{sid}",
                ]
                for _k in _clear_keys:
                    st.session_state.pop(_k, None)
                # Datum für nächsten Test vorbelegen
                st.session_state["spiro_saved_datum"] = _saved_date
                _save_ok(f"Stufentest vom {datum_spiro.strftime('%d.%m.%Y')} gespeichert!")
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2 — AUSWERTUNG
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_ausw:
        if not alle_tests:
            st.info("Noch keine Stufentests für diesen Spieler vorhanden.")
        else:
            test_labels_a = [
                f"{t['datum']} | {t.get('geraeteart','?')}"
                f"{' | Laktat' if t.get('mit_laktat') else ''}"
                f"{' | Spiro' if t.get('mit_spiro') else ''}"
                f"{(' | ' + t['protokoll_name']) if t.get('protokoll_name') else ''}"
                for t in alle_tests
            ]
            ausw_idx = st.selectbox("Test auswählen", range(len(test_labels_a)),
                                     format_func=lambda i: test_labels_a[i], key="spiro_ausw_idx")
            test_a  = alle_tests[ausw_idx]
            stufen_a = spiro_stufen_laden(test_a["id"])
            nb_a     = spiro_nachbelastung_laden(test_a["id"])

            # Kennzahlen-Header
            aw1, aw2, aw3, aw4 = st.columns(4)
            if test_a.get("maximale_geschwindigkeit"):
                aw1.metric("V max", f"{test_a['maximale_geschwindigkeit']:.1f} km/h")
            if test_a.get("maximale_herzfrequenz"):
                aw2.metric("HF max", f"{test_a['maximale_herzfrequenz']:.0f} bpm")
            vo2_lbl = "VO₂peak" if test_a.get("vo2_peak") else ("VO₂max" if test_a.get("vo2_max") else None)
            vo2_val = test_a.get("vo2_peak") or test_a.get("vo2_max")
            if vo2_lbl and vo2_val:
                aw3.metric(f"{vo2_lbl} (gemessen)", f"{vo2_val:.1f} ml/kg/min")
            if test_a.get("schwelle_geschwindigkeit"):
                meth_s = (test_a.get("laktatschwelle_methode") or "Schwelle")[:14]
                aw4.metric(f"V bei {meth_s}", f"{test_a['schwelle_geschwindigkeit']:.1f} km/h")

            if stufen_a:
                df_st_a = pd.DataFrame(stufen_a)
                lak_rows = df_st_a[df_st_a["laktat_mmol_l"].notna()].copy() if "laktat_mmol_l" in df_st_a.columns else pd.DataFrame()

                # Laktat-Leistungskurve
                if not lak_rows.empty and "geschwindigkeit_kmh" in lak_rows.columns:
                    fig_lak = go.Figure()
                    fig_lak.add_trace(go.Scatter(
                        x=lak_rows["geschwindigkeit_kmh"], y=lak_rows["laktat_mmol_l"],
                        mode="lines+markers+text", name="Laktat (mmol/l)",
                        text=lak_rows["laktat_mmol_l"].round(1), textposition="top center",
                        line=dict(color="#f85149", width=3), marker=dict(size=10),
                    ))
                    for zl_c, clr_c in [(2.0, "#d29922"), (4.0, "#f85149")]:
                        r_z = _ibl(stufen_a, zl_c)
                        if r_z:
                            fig_lak.add_vline(
                                x=r_z["x_wert"], line_dash="dash", line_color=clr_c,
                                annotation_text=f"{zl_c:.0f} mmol/l → {r_z['x_wert']:.1f} km/h (interp.)",
                                annotation_position="top right",
                            )
                    if test_a.get("schwelle_geschwindigkeit"):
                        fig_lak.add_vline(
                            x=test_a["schwelle_geschwindigkeit"], line_dash="dot",
                            line_color="#3fb950",
                            annotation_text=f"Schwelle: {(test_a.get('laktatschwelle_methode') or '')[:18]}",
                        )
                    fig_lak.update_layout(**_pl(
                        height=320,
                        title="Laktat-Leistungskurve (tatsächliche Messpunkte)",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="Laktat (mmol/l)"),
                    ))
                    st.plotly_chart(fig_lak, use_container_width=True)
                    st.caption(
                        "📌 Verbunden sind nur tatsächlich gemessene Werte. "
                        "Interpolierte Schwellenwerte (gestrichelt) werden nicht extrapoliert."
                    )

                # HF-Leistungskurve
                hf_rows = df_st_a[df_st_a["herzfrequenz_bpm"].notna()].copy() if "herzfrequenz_bpm" in df_st_a.columns else pd.DataFrame()
                if not hf_rows.empty and "geschwindigkeit_kmh" in hf_rows.columns:
                    fig_hf = go.Figure()
                    fig_hf.add_trace(go.Scatter(
                        x=hf_rows["geschwindigkeit_kmh"], y=hf_rows["herzfrequenz_bpm"],
                        mode="lines+markers", name="Herzfrequenz (bpm)",
                        line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                    ))
                    for vt_key, vt_col, vt_lbl in [("vt1_geschwindigkeit","#d29922","VT1"),("vt2_geschwindigkeit","#f85149","VT2")]:
                        if test_a.get(vt_key):
                            fig_hf.add_vline(x=test_a[vt_key], line_dash="dash",
                                             line_color=vt_col, annotation_text=vt_lbl)
                    fig_hf.update_layout(**_pl(
                        height=260,
                        title="Herzfrequenz-Leistungskurve",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="HF (bpm)"),
                    ))
                    st.plotly_chart(fig_hf, use_container_width=True)

                # Stufentabelle
                st.markdown("#### Stufentabelle")
                show_st_cols = [c for c in [
                    "stufennummer", "geschwindigkeit_kmh", "herzfrequenz_bpm",
                    "laktat_mmol_l", "rpe", "stufe_vollstaendig",
                    "vo2_relativ", "rer",
                ] if c in df_st_a.columns]
                st.dataframe(
                    df_st_a[show_st_cols].rename(columns={
                        "stufennummer": "Stufe", "geschwindigkeit_kmh": "km/h",
                        "herzfrequenz_bpm": "HF (bpm)", "laktat_mmol_l": "Laktat (mmol/l)",
                        "rpe": "RPE", "stufe_vollstaendig": "vollst.",
                        "vo2_relativ": "VO₂ rel.", "rer": "RER",
                    }),
                    use_container_width=True, hide_index=True,
                )

            if nb_a:
                st.markdown("#### Nachbelastungswerte")
                df_nb_a = pd.DataFrame(nb_a)[["zeitpunkt_minuten","herzfrequenz_bpm","laktat_mmol_l","bemerkung"]]
                df_nb_a.columns = ["Zeit (min)", "HF (bpm)", "Laktat (mmol/l)", "Bemerkung"]
                st.dataframe(df_nb_a, use_container_width=True, hide_index=True)

            # Trainingsbereiche aus Schwellen
            if (test_a.get("vt1_herzfrequenz") and test_a.get("vt2_herzfrequenz")) \
               or test_a.get("schwelle_herzfrequenz"):
                grundlage_tb = (
                    f"{test_a.get('laktatschwelle_methode') or 'VT-Schwellen'} "
                    f"aus Stufentest vom {test_a.get('datum','')}"
                )
                bereiche_tb = _tbs(
                    vt1_hf=test_a.get("vt1_herzfrequenz"),
                    vt2_hf=test_a.get("vt2_herzfrequenz"),
                    schwelle_hf=test_a.get("schwelle_herzfrequenz"),
                    hf_max=test_a.get("maximale_herzfrequenz"),
                    grundlage_text=grundlage_tb,
                )
                if bereiche_tb:
                    st.markdown("#### Individuelle Trainingsbereiche")
                    st.caption(f"Grundlage: {grundlage_tb}")
                    st.dataframe(
                        pd.DataFrame(bereiche_tb)[["Bereich","HF-Bereich","Intensität"]],
                        use_container_width=True, hide_index=True,
                    )
                    st.caption("Keine Verwendung der 220-minus-Alter-Formel — Basis sind gemessene Schwellenwerte.")

            # Fußball-Einordnung
            st.markdown("---")
            st.info(
                "🏟️ **Fußballbezogene Einordnung:** Der laufbasierte Stufentest beschreibt die "
                "aerobe und submaximale Ausdauerleistungsfähigkeit unter standardisierten Bedingungen. "
                "Geschwindigkeit, Herzfrequenz, Atemgaswerte und Laktat können für die individuelle "
                "Trainingssteuerung verwendet werden. Ein Labortest bildet nicht alle Anforderungen "
                "des Fußballspiels ab."
            )

            st.markdown("---")
            if st.button("🗑️ Diesen Test löschen", key="spiro_del", type="secondary"):
                spiro_test_loeschen(test_a["id"])
                st.success("✅ Stufentest gelöscht.")
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3 — VERLAUF & VERGLEICH
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_vgl:
        if not alle_tests:
            st.info("Noch keine Stufentests vorhanden.")
        else:
            # Übersichtstabelle
            st.markdown("### Alle Stufentests")
            ov_cols = ["datum","geraeteart","maximale_geschwindigkeit","maximale_herzfrequenz",
                        "vo2_peak","vo2_max","schwelle_geschwindigkeit","laktatschwelle_methode","protokoll_name"]
            df_ov = pd.DataFrame(alle_tests)[[c for c in ov_cols if c in pd.DataFrame(alle_tests).columns]]
            df_ov = df_ov.rename(columns={
                "datum":"Datum","geraeteart":"Gerät","maximale_geschwindigkeit":"V max (km/h)",
                "maximale_herzfrequenz":"HF max","vo2_peak":"VO₂peak","vo2_max":"VO₂max",
                "schwelle_geschwindigkeit":"V Schwelle","laktatschwelle_methode":"Methode",
                "protokoll_name":"Protokoll",
            })
            st.dataframe(df_ov, use_container_width=True, hide_index=True)

            if len(alle_tests) < 2:
                st.info("Mindestens 2 Tests für den Vergleich erforderlich.")
                return

            st.markdown("---")
            st.markdown("### Laktatkurven vergleichen")
            vl1, vl2 = st.columns(2)
            vgl_labels = [
                f"{t['datum']} — {t.get('geraeteart','?')}"
                f"{(' | ' + t['protokoll_name']) if t.get('protokoll_name') else ''}"
                for t in alle_tests
            ]
            idx_t1 = vl1.selectbox("Test 1 (Referenz)", range(len(vgl_labels)),
                                    format_func=lambda i: vgl_labels[i], key="vgl_t1")
            idx_t2 = vl2.selectbox("Test 2 (Vergleich)", range(len(vgl_labels)),
                                    format_func=lambda i: vgl_labels[i],
                                    index=min(1, len(alle_tests) - 1), key="vgl_t2")

            if idx_t1 == idx_t2:
                st.warning("Bitte zwei verschiedene Tests auswählen.")
            else:
                t_ref  = alle_tests[idx_t1]
                t_new  = alle_tests[idx_t2]
                st_ref = spiro_stufen_laden(t_ref["id"])
                st_new = spiro_stufen_laden(t_new["id"])

                # Protokollkompatibilität prüfen
                p_ref = next((p for p in alle_protokolle if p["id"] == t_ref.get("protokoll_id")), {})
                p_new = next((p for p in alle_protokolle if p["id"] == t_new.get("protokoll_id")), {})
                if t_ref.get("protokoll_id") and t_new.get("protokoll_id"):
                    vgl_ok, vgl_abw = _pv(p_ref, p_new)
                    if not vgl_ok:
                        st.warning(
                            "⚠️ **Protokolle unterscheiden sich — direkter Vergleich eingeschränkt:**\n\n"
                            + "  \n".join(f"• {a}" for a in vgl_abw)
                        )
                    else:
                        st.success("✅ Gleiche Protokollparameter — direkter Vergleich möglich.")
                elif t_ref.get("geraeteart") != t_new.get("geraeteart"):
                    st.warning(
                        "⚠️ Verschiedene Gerätearten — direkter Vergleich eingeschränkt. "
                        f"({t_ref.get('geraeteart','?')} vs. {t_new.get('geraeteart','?')})"
                    )
                else:
                    st.info("ℹ️ Kein vollständiges Protokoll hinterlegt — Vergleichbarkeit nicht automatisch prüfbar.")

                # Overlay Laktatkurven
                lak_ref = [r for r in st_ref if r.get("laktat_mmol_l") and r.get("geschwindigkeit_kmh")]
                lak_new = [r for r in st_new if r.get("laktat_mmol_l") and r.get("geschwindigkeit_kmh")]

                if lak_ref and lak_new:
                    fig_ov_lak = go.Figure()
                    for rows_v, lbl_v, clr_v in [(lak_ref, t_ref["datum"], "#3b82f6"), (lak_new, t_new["datum"], "#f85149")]:
                        fig_ov_lak.add_trace(go.Scatter(
                            x=[r["geschwindigkeit_kmh"] for r in rows_v],
                            y=[r["laktat_mmol_l"]       for r in rows_v],
                            mode="lines+markers", name=lbl_v,
                            line=dict(color=clr_v, width=3), marker=dict(size=9),
                        ))
                    fig_ov_lak.update_layout(**_pl(
                        height=340,
                        title="Laktatkurven-Overlay — gleiche Achsenskalierung",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="Laktat (mmol/l)"),
                    ))
                    st.plotly_chart(fig_ov_lak, use_container_width=True)

                    # Schwellenvergleich
                    zeilen_sv = _svt(st_ref, st_new, t_ref["datum"], t_new["datum"])
                    if zeilen_sv:
                        st.markdown("#### Vergleich bei festen Laktatwerten")
                        st.caption("Interpolierte Werte: als '(interp.)' markiert. Keine Extrapolation außerhalb der Messung.")
                        st.dataframe(pd.DataFrame(zeilen_sv), use_container_width=True, hide_index=True)

                    # Kurvenverschiebung
                    st.markdown("#### Kurvenverschiebung — neutrale Bewertung")
                    for zl_v in [2.0, 4.0]:
                        r_ref_z = _ibl(st_ref, zl_v)
                        r_new_z = _ibl(st_new, zl_v)
                        stufe_v, text_v = _kvb(
                            r_ref_z["x_wert"] if r_ref_z else None,
                            r_new_z["x_wert"] if r_new_z else None,
                            zl_v,
                        )
                        clr_v = {
                            "wahrscheinlich verbessert": "#3fb950",
                            "weitgehend unverändert":    "#d29922",
                            "möglicherweise vermindert": "#f85149",
                            "nicht sicher vergleichbar": "#8b949e",
                        }.get(stufe_v, "#8b949e")
                        st.markdown(
                            f'<div style="background:#161b22;border-left:3px solid {clr_v};'
                            f'padding:10px 14px;margin:6px 0;border-radius:4px">'
                            f'<b style="color:{clr_v}">{stufe_v}</b><br>'
                            f'<span style="font-size:13px;color:#cdd9e5">{text_v}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        "⚠️ Eine Kurvenverschiebung beweist keine eindeutige Verbesserung oder Verschlechterung. "
                        "Tagesform, Vorbelastung, Regeneration, Ernährung, Temperatur, Testbedingungen, "
                        "Ausbelastungsgrad, RPE und Herzfrequenz müssen bei der Interpretation berücksichtigt werden."
                    )
                else:
                    st.info("Für mindestens einen der gewählten Tests sind keine Laktatwerte verfügbar.")

                # HF-Overlay
                hf_ref = [r for r in st_ref if r.get("herzfrequenz_bpm") and r.get("geschwindigkeit_kmh")]
                hf_new = [r for r in st_new if r.get("herzfrequenz_bpm") and r.get("geschwindigkeit_kmh")]
                if hf_ref and hf_new:
                    fig_ov_hf = go.Figure()
                    for rows_h, lbl_h, clr_h in [(hf_ref, t_ref["datum"], "#3b82f6"), (hf_new, t_new["datum"], "#f85149")]:
                        fig_ov_hf.add_trace(go.Scatter(
                            x=[r["geschwindigkeit_kmh"] for r in rows_h],
                            y=[r["herzfrequenz_bpm"]    for r in rows_h],
                            mode="lines+markers", name=lbl_h,
                            line=dict(color=clr_h, width=3), marker=dict(size=9),
                        ))
                    fig_ov_hf.update_layout(**_pl(
                        height=260,
                        title="Herzfrequenz-Leistungskurven — Vergleich",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="HF (bpm)"),
                    ))
                    st.plotly_chart(fig_ov_hf, use_container_width=True)
RPE_LABELS = {
    6: "6 — Gar keine Anstrengung", 7: "7", 8: "8", 9: "9",
    10: "10 — Sehr leicht", 11: "11 — Leicht", 12: "12",
    13: "13 — Etwas anstrengend", 14: "14",
    15: "15 — Anstrengend", 16: "16", 17: "17 — Sehr anstrengend",
    18: "18", 19: "19 — Extrem anstrengend", 20: "20 — Maximale Anstrengung",
}


def page_ausdauer():
    st.markdown("# 🫁 Ausdauer-Diagnostik")

    # ── Bereichsselektor ──────────────────────────────────────────────────────
    bereich = st.radio(
        "Ausdauertest",
        ["🏃 Yo-Yo Intermittent Recovery Test", "🔬 Spiroergometrie-Stufentest"],
        horizontal=True,
        key="aus_bereich_wahl",
        label_visibility="collapsed",
    )
    st.markdown("---")

    if bereich == "🔬 Spiroergometrie-Stufentest":
        _page_spiro()
        return

    # ── Yo-Yo (unveränderter Code) ────────────────────────────────────────────
    st.markdown("## 🏃 Yo-Yo Intermittent Recovery Test")
    st.markdown("Yo-Yo Intermittent Recovery Test Level 1 (IR1) und Level 2 (IR2) — Standardtest im Fußball.")

    sicherheitshinweis_box()
    show_trainer_checkliste("yoyo")
    show_test_info("yoyo")
    _anleitung_download_button("yoyo")

    auswahl = _player_selector("aus")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    alter  = berechne_alter(sp.get("geburtsdatum","")) if sp else 0
    ag_norm = alter_zu_altersgruppe(alter or 0)   # für field_eval-Normbadge

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
        if distanz_m > 0: norm_badge(distanz_m, "yoyo", "distanz", c3, altersgruppe=ag_norm)
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
            if test_typ == "IR2":
                st.info(
                    "ℹ️ Für den Yo-Yo IR2 wird keine automatische VO₂max-Schätzung berechnet — "
                    "der Bangsbo-Koeffizient gilt ausschließlich für den IR1."
                )

            if res.vo2max:
                st.markdown("#### Trainingsbereiche")
                tb = trainingsbereiche(res.vo2max)
                st.dataframe(pd.DataFrame(tb), use_container_width=True, hide_index=True)

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_aus = render_observation_selector("ausdauer", sid, datum.strftime("%d.%m.%Y"), "aus", standalone=False)
        _dup_aus = _duplikat_check("aus", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="aus_save", type="primary"):
            if _dup_aus == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if distanz_m <= 0:
                st.error("Bitte Distanz eingeben.")
            else:
                import json, datetime as _dtm
                _datum_aus = datum.strftime("%d.%m.%Y")
                if _dup_aus == "zweiter":
                    _datum_aus += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                ausdauer_speichern(
                    sid, _datum_aus,
                    test_typ, distanz_m,
                    hf_max or 0, rpe_val,
                    res.vo2max or 0, res.bewertung,
                    altersgruppe,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                if obs_aus["beob_ids"] or obs_aus.get("freitext"):
                    beobachtung_speichern(
                        sid, "ausdauer", _datum_aus,
                        json.dumps(obs_aus["beob_ids"], ensure_ascii=False),
                        obs_aus["seite"], obs_aus["auspraegung"],
                        obs_aus["freitext"], obs_aus["text_generiert"],
                    )
                _save_ok("Ausdauer-Test gespeichert!")
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


# ──────────────────────────────────────────────────────────────────────────────

def page_kraft():
    st.markdown("# 💪 Kraftdiagnostik")
    st.markdown(
        "Bankdrücken 1RM (direkt oder Epley-Schätzung) und Rumpfkraftausdauer — "
        "interne Orientierungswerte für die Trainingssteuerung. "
        "Kein Test ersetzt eine ärztliche Einschätzung oder Sportfreigabe."
    )

    sicherheitshinweis_box()
    show_trainer_checkliste("kraft")
    show_test_info("kraft")

    auswahl = _player_selector("kraft")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    kgew   = anthropometrie_letzter(sid)
    hist   = kraft_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="kraft_datum")
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")

        koerpergewicht_default = float(kgew["gewicht"]) if kgew and kgew.get("gewicht") else 75.0
        koerpergewicht = st.number_input(
            "Körpergewicht (kg) — für Berechnung der relativen Kraft",
            15.0, 150.0, koerpergewicht_default, step=0.5, key="kraft_kgew"
        )

        st.markdown("---")
        # ── Bankdrücken ────────────────────────────────────────────────────
        bd_head, bd_info = st.columns([6, 1])
        bd_head.markdown("### 🏋️ Bankdrücken — 1-Wiederholungsmaximum (1RM)")
        field_info_col(bd_info, "kraft", "direktes_1rm")
        st.caption(
            "Interner Orientierungswert für die Trainingssteuerung. "
            "Direkte 1RM-Tests nur mit Sicherung und ausreichendem Aufwärmen."
        )
        bd_methode = st.radio(
            "Testmethode",
            ["Submaximaltest (Epley-Schätzung) — empfohlen", "Direkter 1RM-Test"],
            key="kraft_bd_methode",
        )

        direktes_1rm  = None
        epley_gewicht = None
        epley_wdh     = None
        sicherheit_ok = False

        if "Direkt" in bd_methode:
            st.warning(
                "⚠️ **Sicherheitshinweis — Direkter 1RM-Test**\n\n"
                "• Mindestens 2 Trainer/Spotters als Sicherung\n"
                "• Ausreichendes Aufwärmen abgeschlossen (progressive Laststeigerung)\n"
                "• Technikbeherrschung und Testprotokoll erklärt\n"
                "• Sofortabbruch bei technischen Mängeln oder Schmerzen"
            )
            c1, c2, c3 = st.columns(3)
            ok1 = c1.checkbox("✅ Sicherung durch mind. 2 Trainer", key="kraft_sek1")
            ok2 = c2.checkbox("✅ Aufwärmphase abgeschlossen", key="kraft_sek2")
            ok3 = c3.checkbox("✅ Technik & Protokoll besprochen", key="kraft_sek3")
            sicherheit_ok = ok1 and ok2 and ok3
            if not sicherheit_ok:
                st.info("Alle drei Sicherheitspunkte müssen bestätigt sein.")
            else:
                st.success("✅ Sicherheitsprotokoll vollständig — Test kann durchgeführt werden.")
            direktes_1rm = st.number_input(
                "Direktes 1RM (kg)", 0.0, 300.0, 0.0, step=2.5, key="kraft_d1rm",
                disabled=(not sicherheit_ok)
            ) or None
            if direktes_1rm and direktes_1rm > 200:
                st.warning(f"⚠️ {direktes_1rm:.0f} kg ist ein außergewöhnlicher 1RM-Wert — bitte Eingabe prüfen.")
        else:
            st.caption("Eingabe: Gewicht und Wiederholungsanzahl aus dem Submaximaltest (empfohlen 2–10 WH).")
            c1, c2 = st.columns(2)
            epley_gewicht = c1.number_input("Testgewicht (kg)", 0.0, 300.0, 0.0, step=2.5, key="kraft_e_gew") or None
            epley_wdh_raw = c2.number_input("Wiederholungen", 1, 15, 5, key="kraft_e_wdh")
            epley_wdh = int(epley_wdh_raw)
            if epley_wdh > 10:
                st.warning("⚠️ Die Epley-Formel ist für > 10 Wiederholungen weniger genau.")
            if epley_gewicht:
                est = _epley_1rm(epley_gewicht, epley_wdh)
                if est:
                    rel = round(est / koerpergewicht, 2) if koerpergewicht > 0 else None
                    c1, c2 = st.columns(2)
                    c1.metric("Geschätztes 1RM (Epley)", f"{est:.1f} kg")
                    if rel: c2.metric("Relative Kraft", f"{rel:.2f} ×KGW")
            sicherheit_ok = True

        from kraft import KraftErgebnis as _KE
        kraft_res = _KE(
            koerpergewicht=koerpergewicht,
            direktes_1rm=direktes_1rm,
            epley_gewicht=epley_gewicht,
            epley_wiederholungen=epley_wdh,
            sicherheit_bestaetigt=sicherheit_ok,
        )
        if kraft_res.hat_bankdruecken_daten:
            from kraft import beurteilung_relative_kraft as _bwrk
            m1, m2, m3 = st.columns(3)
            if direktes_1rm:              m1.metric("Direkt 1RM", f"{direktes_1rm:.1f} kg")
            if kraft_res.geschaetztes_1rm: m2.metric("Epley-Schätzung", f"{kraft_res.geschaetztes_1rm:.1f} kg")
            rel = kraft_res.relative_kraft_direkt or kraft_res.relative_kraft_geschaetzt
            if rel:
                m3.metric("Relative Kraft", f"{rel:.2f} ×KGW")
                _stufe_rk, _empf_rk = _bwrk(rel, alter=alter, geschlecht=geschl)
                _clr_rk = {"Sehr gut": "#3fb950", "Gut": "#3fb950",
                           "Durchschnittlich": "#d29922",
                           "Unterdurchschnittlich": "#f85149", "Kritisch": "#f85149"}.get(_stufe_rk, "#8b949e")
                from age_norms import normgruppe_label as _ngl
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {_clr_rk};border-radius:8px;'
                    f'padding:10px 14px;margin:6px 0">'
                    f'<span style="color:{_clr_rk};font-weight:700">Bankdrücken Rel. Kraft: {_stufe_rk}</span>'
                    f'<span style="color:#8b949e;font-size:12px;margin-left:12px">{rel:.2f} ×KGW</span><br>'
                    f'<small style="color:#8b949e">{_empf_rk}</small>'
                    f'<br><small style="color:#8b949e;font-size:11px">📊 {_ngl(alter)}</small></div>',
                    unsafe_allow_html=True,
                )

        # ── Rumpfkraftausdauer ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧱 Rumpfkraftausdauer — Haltedauer (Sekunden)")
        st.caption("Ventral: 2 Versuche (Bestwert = länger). Lateral R/L und Dorsal: je 1 Versuch.")

        rc1, rc2 = st.columns(2)
        vh_head, vh_info = rc1.columns([5, 1])
        vh_head.markdown("**Ventral (Plank) — 2 Versuche**")
        field_info_col(vh_info, "kraft", "ventral_sekunden")
        rv1_c, rv2_c = rc1.columns(2)
        ventral_v1 = rv1_c.number_input("V1 (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_vent_v1") or None
        ventral_v2 = rv2_c.number_input("V2 (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_vent_v2") or None
        ventr_best = max([v for v in [ventral_v1, ventral_v2] if v], default=None)
        if ventr_best: rc1.success(f"Bestwert ventral: **{ventr_best:.0f} s**")

        lh_head, lh_info = rc2.columns([5, 1])
        lh_head.markdown("**Lateral (Seitstütz) — R/L**")
        field_info_col(lh_info, "kraft", "lateral_rechts")
        lateral_r = rc2.number_input("Lateral rechts (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_lat_r") or None
        lateral_l = rc2.number_input("Lateral links (s)",  0.0, 600.0, 0.0, step=1.0, key="kraft_lat_l") or None
        dh_head, dh_info = rc1.columns([5, 1])
        dh_head.markdown("**Dorsal (Biering-Sørensen)**")
        field_info_col(dh_info, "kraft", "dorsal_sekunden")
        dorsal    = rc1.number_input("Dorsal (s)",         0.0, 600.0, 0.0, step=1.0, key="kraft_dors") or None

        rumpf_res = _KE(
            koerpergewicht=koerpergewicht,
            direktes_1rm=direktes_1rm, epley_gewicht=epley_gewicht,
            epley_wiederholungen=epley_wdh, sicherheit_bestaetigt=sicherheit_ok,
            ventral_sekunden=ventral_v1, ventral_versuch2=ventral_v2,
            lateral_rechts_sekunden=lateral_r, lateral_links_sekunden=lateral_l,
            dorsal_sekunden=dorsal,
        )

        if rumpf_res.hat_rumpfkraft_daten:
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if rumpf_res.ventral_bestwert: m1.metric("Ventral", f"{rumpf_res.ventral_bestwert:.0f} s")
            if lateral_r:                  m2.metric("Lateral R", f"{lateral_r:.0f} s")
            if lateral_l:                  m3.metric("Lateral L", f"{lateral_l:.0f} s")
            if dorsal:                     m4.metric("Dorsal", f"{dorsal:.0f} s")
            if rumpf_res.lateral_asymmetrie_pct is not None:
                color = "#f85149" if rumpf_res.lateral_asymmetrie_pct > 10 else "#3fb950"
                hint  = "⚠️ auffällig" if rumpf_res.lateral_asymmetrie_pct > 10 else "✅ symmetrisch"
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {color};border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0">'
                    f'<span style="color:{color};font-weight:600">Lateral-Asymmetrie: '
                    f'{rumpf_res.lateral_asymmetrie_pct:.1f} % — {hint}</span>'
                    f'<br><small style="color:#8b949e">Grenzwert: 10 % Seitendifferenz</small></div>',
                    unsafe_allow_html=True,
                )
            # ── Rumpfkraftausdauer Beurteilung ──────────────────────────────
            from kraft import beurteilung_ventral_plank as _bwvp, beurteilung_dorsal as _bwdors, beurteilung_lateral as _bwlat
            _rk_bwcols = [x for x in [
                ("Ventral (Plank)", rumpf_res.ventral_bestwert, _bwvp),
                ("Lateral R",       lateral_r,                  _bwlat),
                ("Lateral L",       lateral_l,                  _bwlat),
                ("Dorsal",          dorsal,                     _bwdors),
            ] if x[1]]
            if _rk_bwcols:
                _bc = st.columns(len(_rk_bwcols))
                _bw_clr_map = {"Sehr gut": "#3fb950", "Gut": "#3fb950",
                               "Durchschnittlich": "#d29922",
                               "Unterdurchschnittlich": "#f85149", "Kritisch": "#f85149"}
                for _i, (_lbl, _val, _fn) in enumerate(_rk_bwcols):
                    _st2, _em2 = _fn(_val)
                    _c2 = _bw_clr_map.get(_st2, "#8b949e")
                    _bc[_i].markdown(
                        f'<div style="background:#161b22;border:1px solid {_c2};border-radius:8px;'
                        f'padding:10px 14px;text-align:center">'
                        f'<div style="color:{_c2};font-weight:700;font-size:13px">{_lbl}: {_st2}</div>'
                        f'<div style="color:#e6edf3;font-size:22px;font-weight:700">{_val:.0f} s</div>'
                        f'<small style="color:#8b949e">{_em2}</small></div>',
                        unsafe_allow_html=True,
                    )
            if rumpf_res.hinweise:
                st.markdown("**🔵 Trainingshinweise:**")
                for h in rumpf_res.hinweise:
                    st.markdown(f"- {h}")

        st.markdown("---")
        bemerkung = st.text_area("Trainernotiz (optional)", height=70, key="kraft_bemerkung") or None
        obs_kraft = render_observation_selector("kraft", sid, datum.strftime("%d.%m.%Y"), "kraft", standalone=False)

        save_disabled = ("Direkt" in bd_methode) and (not sicherheit_ok)
        if st.button("💾 Test speichern", use_container_width=True, key="kraft_save", type="primary",
                     disabled=save_disabled):
            if not rumpf_res.hat_daten:
                st.error("Bitte mindestens einen Messwert eingeben.")
            else:
                import json
                lat_diff  = round(abs(lateral_r - lateral_l), 1) if lateral_r and lateral_l else None
                rumpf_ges = None
                vals_r = [v for v in [rumpf_res.ventral_bestwert, lateral_r, lateral_l, dorsal] if v]
                if vals_r: rumpf_ges = round(sum(vals_r), 1)
                kraft_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    koerpergewicht, rumpf_res.direktes_1rm, rumpf_res.geschaetztes_1rm,
                    rumpf_res.relative_kraft_direkt, rumpf_res.relative_kraft_geschaetzt,
                    1 if sicherheit_ok else 0,
                    ventral_v1, ventral_v2, lateral_r, lateral_l, dorsal,
                    rumpf_ges, lat_diff, rumpf_res.lateral_asymmetrie_pct,
                    rumpf_res.ratio_ventral_dorsal, rumpf_res.ratio_lateral_r_dorsal,
                    rumpf_res.ratio_lateral_l_dorsal, bemerkung=bemerkung,
                )
                if obs_kraft["beob_ids"] or obs_kraft.get("freitext"):
                    beobachtung_speichern(
                        sid, "kraft", datum.strftime("%d.%m.%Y"),
                        json.dumps(obs_kraft["beob_ids"], ensure_ascii=False),
                        obs_kraft["seite"], obs_kraft["auspraegung"],
                        obs_kraft["freitext"], obs_kraft["text_generiert"],
                    )
                _save_ok("Kraft-Test gespeichert!")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Kraft-Tests vorhanden.")
            return
        df = pd.DataFrame(hist)
        df.columns = [
            "Datum", "Direkt 1RM", "Epley 1RM",
            "Rel. Kraft D", "Rel. Kraft E",
            "Ventral (s)", "Lateral R (s)", "Lateral L (s)",
            "Dorsal (s)", "Lat.-Asym. %", "V/D-Ratio",
        ]

        # ── Letzter Test ──────────────────────────────────────────────────────
        with st.expander("📋 Letzter gespeicherter Test", expanded=True):
            lr = df.iloc[-1]
            ka1, ka2, ka3, ka4, ka5, ka6 = st.columns(6)
            def _km(col, label, val, fmt="%.1f", suffix=""):
                if val and float(val) > 0:
                    col.metric(label, f"{float(val):{fmt.replace('%','')}} {suffix}".strip())
            _km(ka1, "Direkt 1RM",  lr.get("Direkt 1RM"), fmt="%.1f", suffix="kg")
            _km(ka2, "Epley 1RM",   lr.get("Epley 1RM"),  fmt="%.1f", suffix="kg")
            _km(ka3, "Ventral",     lr.get("Ventral (s)"),   fmt="%.0f", suffix="s")
            _km(ka4, "Lateral R",   lr.get("Lateral R (s)"), fmt="%.0f", suffix="s")
            _km(ka5, "Lateral L",   lr.get("Lateral L (s)"), fmt="%.0f", suffix="s")
            _km(ka6, "Dorsal",      lr.get("Dorsal (s)"),    fmt="%.0f", suffix="s")
            if lr.get("Lat.-Asym. %") and float(lr["Lat.-Asym. %"]) > 0:
                color = "#f85149" if float(lr["Lat.-Asym. %"]) > 10 else "#3fb950"
                st.markdown(
                    f'<small style="color:{color}">Lateral-Asymmetrie: '
                    f'<b>{float(lr["Lat.-Asym. %"]):.1f} %</b> | Datum: {lr["Datum"]}</small>',
                    unsafe_allow_html=True,
                )

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            for col_n, clr in [("Direkt 1RM", "#3b82f6"), ("Epley 1RM", "#3fb950")]:
                sub = df[df[col_n] > 0] if col_n in df.columns else pd.DataFrame()
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_n], mode="lines+markers",
                                         name=col_n, line=dict(color=clr, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=280, title="Bankdrücken 1RM-Verlauf (kg)", yaxis=dict(title="kg")))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure()
            for col_n, clr in [("Ventral (s)", "#3b82f6"), ("Lateral R (s)", "#3fb950"),
                                ("Lateral L (s)", "#d29922"), ("Dorsal (s)", "#a371f7")]:
                sub = df[df[col_n] > 0] if col_n in df.columns else pd.DataFrame()
                if sub.empty: continue
                fig2.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_n], mode="lines+markers",
                                          name=col_n, line=dict(color=clr, width=2), marker=dict(size=7)))
            fig2.update_layout(**_pl(height=280, title="Rumpfkraftausdauer-Verlauf (s)", yaxis=dict(title="s")))
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ──────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums_k = df["Datum"].tolist()
                kc1, kc2 = st.columns(2)
                kd1 = kc1.selectbox("Termin 1", datums_k, index=0, key="kr_cmp_d1")
                kd2 = kc2.selectbox("Termin 2", datums_k, index=len(datums_k)-1, key="kr_cmp_d2")
                kr1 = df[df["Datum"] == kd1].iloc[0]
                kr2 = df[df["Datum"] == kd2].iloc[0]
                compare_cols_k = ["Direkt 1RM", "Epley 1RM", "Rel. Kraft D", "Rel. Kraft E",
                                   "Ventral (s)", "Lateral R (s)", "Lateral L (s)", "Dorsal (s)", "Lat.-Asym. %"]
                rows_k = []
                for ck in compare_cols_k:
                    v1k = kr1.get(ck, 0) or 0
                    v2k = kr2.get(ck, 0) or 0
                    if v1k > 0 or v2k > 0:
                        diff_k = round(v2k - v1k, 2) if v1k > 0 and v2k > 0 else "—"
                        rows_k.append({"Messung": ck, kd1: f"{v1k:.2f}" if v1k else "—",
                                       kd2: f"{v2k:.2f}" if v2k else "—",
                                       "Differenz": f"{diff_k:+.2f}" if isinstance(diff_k, float) else diff_k})
                if rows_k:
                    st.dataframe(pd.DataFrame(rows_k), use_container_width=True, hide_index=True)


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
    kraft  = kraft_letzter(sid)
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
    # Kraft-Beurteilungstext für Startseite-Karte
    from kraft import beurteilung_relative_kraft as _bwrk_s
    _rel_ks = (kraft.get("relative_kraft_direkt") or kraft.get("relative_kraft_geschaetzt")) if kraft else None
    if _rel_ks:
        _kraft_rating_s = _bwrk_s(_rel_ks, alter=alter, geschlecht=auswahl.get("geschlecht", "Männlich"))[0]
    elif kraft and kraft.get("ventral_sekunden"):
        _kraft_rating_s = "Ventral: %.0f s" % kraft["ventral_sekunden"]
    else:
        _kraft_rating_s = None

    # Y-Balance: Asymmetrie-Text als Rating (Farblogik in test_status_card reagiert auf "auffällig" / "Asymmetrie")
    _yb_rating_s = str(y["asymmetrie"]) if y and y.get("asymmetrie") else None

    cards = [
        ("FMS", "📝", fms,
         (fms["bewertung"] + " — " + __import__("fms").fms_bewertung_kurz(fms["score"])[:55] + "…")
          if fms else None,
         fms["datum"] if fms else None),
        ("Y-Balance", "📏", y,      _yb_rating_s,           y["datum"] if y else None),
        ("Sprint",    "⚡", sprint, sprint["bewertung_10m"] if sprint else None, sprint["datum"] if sprint else None),
        ("Sprung",    "🦘", sprung, sprung["bewertung_cmj"] if sprung else None, sprung["datum"] if sprung else None),
        ("Agilität",  "🔀", agil,   agil["bew_t_test"]      if agil   else None, agil["datum"]   if agil   else None),
        ("Ausdauer",  "🫁", aus,    aus["bewertung"]        if aus    else None, aus["datum"]    if aus    else None),
        ("Kraft",     "💪", kraft,  _kraft_rating_s,         kraft["datum"] if kraft else None),
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

    with st.expander("⚙️ Allgemein", expanded=True):
        st.markdown("### Vereinsinformationen")
        c1, c2 = st.columns(2)
        vereinsname = c1.text_input("Vereinsname", value=st.session_state.get("cfg_vereinsname", ""), key="cfg_vname")
        saison      = c2.text_input("Aktuelle Saison", value=st.session_state.get("cfg_saison", "2025/26"), key="cfg_saison")
        if st.button("💾 Speichern", key="cfg_save", type="primary"):
            st.session_state["cfg_vereinsname"] = vereinsname
            st.session_state["cfg_saison"]      = saison
            st.success("✅ Einstellungen gespeichert (Session).")

        st.markdown("---")
        st.markdown("### 🏷️ Vereinslogo")
        st.caption(
            "Das Logo wird in allen generierten PDFs (Anleitungen, Profile, Protokolle) "
            "automatisch eingebunden — einmal hochladen, dauerhaft gespeichert."
        )
        _gespeichertes_logo = logo_laden()
        _col_logo, _col_logo_btn = st.columns([3, 1])
        with _col_logo:
            _neue_logo_datei = st.file_uploader(
                "Logo hochladen (PNG, JPG — max. 2 MB)",
                type=["png", "jpg", "jpeg"],
                key="cfg_logo_upload",
                label_visibility="collapsed",
            )
        with _col_logo_btn:
            if _gespeichertes_logo:
                if st.button("🗑️ Logo löschen", key="cfg_logo_del",
                             use_container_width=True):
                    logo_loeschen()
                    _save_ok("Vereinslogo gelöscht.")
                    st.rerun()
        if _neue_logo_datei is not None:
            _logo_raw = _neue_logo_datei.getvalue()
            if len(_logo_raw) > 2 * 1024 * 1024:
                st.error("❌ Datei zu groß — maximale Größe: 2 MB.")
            else:
                logo_speichern(_logo_raw)
                _save_ok("Vereinslogo gespeichert.")
                st.rerun()
        if _gespeichertes_logo:
            import io as _io
            try:
                st.image(_io.BytesIO(_gespeichertes_logo), width=160,
                         caption=f"Gespeichertes Logo ({len(_gespeichertes_logo)//1024} KB)")
            except Exception:
                st.info("Logo gespeichert (Vorschau nicht verfügbar).")
        else:
            st.info("Noch kein Vereinslogo gespeichert.")

        st.markdown("---")
        st.markdown("### Kader-Übersicht")
        alle = spieler_laden()
        st.metric("Spieler gesamt", len(alle))
        if alle:
            mannschaften = list({p.get("mannschaft") or "Keine" for p in alle})
            st.markdown(f"**Mannschaften:** {', '.join(sorted(mannschaften))}")

    with st.expander("📋 Zweckbestimmung"):
        page_zweckbestimmung()

    with st.expander("✅ Checklisten"):
        from help_ui import _DEFAULT_CHECKLISTE, _TEST_CHECKLISTE

        chk_view_tab, chk_edit_tab = st.tabs(
            ["👁️ Alle Checklisten ansehen", "✏️ Eigene Punkte ergänzen"]
        )

        with chk_view_tab:
            st.markdown("### 📋 Standard-Checkliste (gilt für alle Tests)")
            st.caption(
                "Diese Punkte erscheinen vor jedem Test. "
                "Basierend auf NSCA-Richtlinien und DFB-Trainerempfehlungen."
            )
            for icon, text in _DEFAULT_CHECKLISTE:
                st.markdown(
                    f'<div style="display:flex;gap:10px;padding:5px 0;'
                    f'border-bottom:1px solid #21262d">'
                    f'<span style="font-size:16px;min-width:22px">{icon}</span>'
                    f'<span style="color:#e6edf3;font-size:13px">{text}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### 🔬 Testspezifische Checklisten")

            _CHK_TEST_MAP = {
                "sprint": ("⚡ Sprint", "sprint"),
                "jump":   ("🦘 Sprung / CMJ / Drop Jump", "jump"),
                "agility":("🔀 Agilität", "agility"),
                "yoyo":   ("🫁 Yo-Yo Ausdauer", "yoyo"),
                "fms":    ("📝 FMS", "fms"),
                "y_balance":("📏 Y-Balance", "y_balance"),
                "anthropometrie": ("📐 Anthropometrie", "anthropometrie"),
                "kraft":  ("💪 Kraft", "kraft"),
            }
            for tid, (label, chk_key) in _CHK_TEST_MAP.items():
                items = _TEST_CHECKLISTE.get(chk_key, [])
                if not items:
                    continue
                with st.expander(f"📋 {label}  ({len(items)} Punkte)", expanded=False):
                    for icon, text in items:
                        st.markdown(
                            f'<div style="display:flex;gap:10px;padding:4px 0;'
                            f'border-bottom:1px solid #21262d">'
                            f'<span style="font-size:15px;min-width:22px">{icon}</span>'
                            f'<span style="color:#c9d1d9;font-size:12px">{text}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # Eigene Punkte aus DB anzeigen
                    custom = checkliste_custom_laden(tid)
                    if custom:
                        st.markdown(
                            f'<div style="margin-top:8px;font-size:10px;color:#58a6ff;'
                            f'letter-spacing:1px">EIGENE PUNKTE</div>',
                            unsafe_allow_html=True,
                        )
                        for line in custom.splitlines():
                            if line.strip():
                                st.markdown(
                                    f'<div style="display:flex;gap:10px;padding:4px 0">'
                                    f'<span>📌</span>'
                                    f'<span style="color:#c9d1d9;font-size:12px">{line.strip()}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

        with chk_edit_tab:
            st.markdown("### ✏️ Eigene Checklistenpunkte pro Test")
            st.caption(
                "Ergänze testspezifische Routineschritte, die nach den Standardpunkten "
                "in der Trainer-Checkliste erscheinen. Ein Punkt pro Zeile."
            )
            st.markdown("---")
            for tid in ALL_TEST_IDS:
                label = TEST_LABELS[tid]
                aktuell = checkliste_custom_laden(tid)
                n_std = len(_DEFAULT_CHECKLISTE) + len(_TEST_CHECKLISTE.get(tid, []))
                badge = f"{n_std} Standard"
                with st.expander(f"📋 {label}  —  {badge}-Punkte", expanded=False):
                    neuer_text = st.text_area(
                        "Eigene Punkte (eine Zeile = ein Punkt)",
                        value=aktuell,
                        height=130,
                        placeholder=(
                            "z. B.\nVideoaufnahme starten\n"
                            "Trikot-Nummer notiert\nEltern informiert"
                        ),
                        key=f"chk_custom_{tid}",
                        label_visibility="collapsed",
                    )
                    col_save, col_reset = st.columns([2, 1])
                    if col_save.button("💾 Speichern", key=f"chk_save_{tid}",
                                       use_container_width=True):
                        checkliste_custom_speichern(tid, neuer_text)
                        st.success("✅ Gespeichert.")
                    if col_reset.button("🗑️ Löschen", key=f"chk_del_{tid}",
                                        use_container_width=True):
                        checkliste_custom_speichern(tid, "")
                        st.rerun()

    with st.expander("🌐 Sprache / Language"):
        st.markdown("### 🌐 Sprache / Language")
        st.caption(
            "Wähle die Anzeigesprache für die Navigation und Benutzeroberfläche. "
            "Die fachlichen Testinhalte bleiben in der jeweiligen Originalsprache."
        )
        st.markdown("---")

        aktuell_lang = get_lang()
        lang_options  = list(SPRACHEN.keys())
        lang_labels   = list(SPRACHEN.values())
        try:
            lang_idx = lang_options.index(aktuell_lang)
        except ValueError:
            lang_idx = 0

        neue_sprache_label = st.radio(
            "Sprache / Language",
            lang_labels,
            index=lang_idx,
            key="lang_radio_sel",
            label_visibility="collapsed",
        )
        # Index rückrechnen
        neue_sprache_code = lang_options[lang_labels.index(neue_sprache_label)]

        if st.button("✅ Sprache übernehmen / Apply Language", type="primary",
                     use_container_width=True):
            set_lang(neue_sprache_code)
            st.success(
                f"✅ Sprache gesetzt: {SPRACHEN[neue_sprache_code]}"
                if neue_sprache_code == "de"
                else f"✅ Language set: {SPRACHEN[neue_sprache_code]}"
            )
            st.rerun()

        st.markdown("---")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;'
            f'border-radius:8px;padding:14px 16px">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;margin-bottom:8px">VORSCHAU / PREVIEW</div>'
            f'<div style="color:#e6edf3;font-size:13px">'
            f'<b>Navigation:</b> {t("nav_startseite")} &nbsp;·&nbsp; '
            f'{t("nav_spieler")} &nbsp;·&nbsp; {t("nav_diagnostik")}<br>'
            f'<b>Buttons:</b> {t("speichern")} &nbsp;·&nbsp; {t("loeschen")} &nbsp;·&nbsp; {t("generieren")}<br>'
            f'<b>Felder:</b> {t("vorname")} &nbsp;·&nbsp; {t("nachname")} &nbsp;·&nbsp; {t("geburtsdatum")}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    with st.expander("🔒 Datenschutz & Datenverwaltung"):
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

    with st.expander("💾 Export & Backup"):
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
# HELPER: Eigene Dokumente hochladen / verwalten
# ══════════════════════════════════════════════════════════════════════════════

def _custom_docs_section(kategorie: str, titel: str = "Eigene Dokumente"):
    """Upload, Anzeige und Verwaltung eigener PDF-Dokumente.
    kategorie: 'anleitungen' oder 'protokolle'.
    """
    import pathlib

    ordner = pathlib.Path(__file__).parent / "assets" / "custom_docs" / kategorie
    ordner.mkdir(parents=True, exist_ok=True)

    st.markdown(f"---\n### 📂 {titel}")
    st.caption(
        "Eigene PDFs hochladen — z. B. externe Anleitungen, Vereinsformulare "
        "oder angepasste Protokolle. Die Dateien bleiben dauerhaft gespeichert."
    )

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "PDF hochladen (Mehrfachauswahl möglich)",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"custom_upload_{kategorie}",
    )
    if uploaded:
        neu = 0
        for f in uploaded:
            ziel = ordner / f.name
            with open(ziel, "wb") as fh:
                fh.write(f.getvalue())
            neu += 1
        _save_ok(f"{neu} Datei(en) gespeichert.")
        st.rerun()

    # ── Gespeicherte Dateien ──────────────────────────────────────────────────
    dateien = sorted(ordner.glob("*.pdf"))
    if not dateien:
        st.info("Noch keine eigenen Dokumente hochgeladen.")
        return

    st.markdown(f"**{len(dateien)} gespeicherte{'s' if len(dateien) == 1 else ''} "
                f"Dokument{'' if len(dateien) == 1 else 'e'}:**")
    for pdf_path in dateien:
        c_name, c_dl, c_del = st.columns([5, 2, 1])
        size_kb = pdf_path.stat().st_size // 1024
        c_name.markdown(
            f'<div style="padding:5px 0;color:#e6edf3;font-size:13px">'
            f'📄 {pdf_path.name}'
            f'<span style="color:#8b949e;font-size:11px;margin-left:8px">{size_kb} KB</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with open(pdf_path, "rb") as fh:
            c_dl.download_button(
                "⬇️ Download",
                data=fh.read(),
                file_name=pdf_path.name,
                mime="application/pdf",
                key=f"dl_{kategorie}_{pdf_path.stem}",
                use_container_width=True,
            )
        if c_del.button("🗑️", key=f"del_{kategorie}_{pdf_path.stem}",
                        help=f"{pdf_path.name} löschen", use_container_width=True):
            pdf_path.unlink(missing_ok=True)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DOKUMENTE (Protokoll + Anleitungen kombiniert)
# ══════════════════════════════════════════════════════════════════════════════

def page_dokumente():
    """Kombinierte Dokumente-Seite: Anleitungen und Protokoll in einer."""
    st.markdown(
        section_header("📄 Dokumente", "Testanleitungen und Druckprotokolle"),
        unsafe_allow_html=True,
    )
    tab_anl, tab_proto = st.tabs(["📄 Testanleitungen", "🖨️ Druckprotokoll"])
    with tab_anl:
        page_export_pdf()
    with tab_proto:
        page_testprotokoll()


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

    # ── Einzeltest-Schnelldownload ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Einzeltest-Schnelldownload")
    st.caption("Ein Test direkt als PDF — kein weiterer Klick nötig.")
    _qt_cols = st.columns(4)
    for _qi, _tid in enumerate(ALL_TEST_IDS):
        _ql = TEST_LABELS[_tid]
        if _qt_cols[_qi % 4].button(f"📄 {_ql}", key=f"qt_{_tid}", use_container_width=True):
            with st.spinner(f"{_ql} wird erstellt …"):
                try:
                    _qb = generate_anleitung_pdf(
                        [_tid],
                        mit_deckblatt=False,
                        vereinsname=st.session_state.get("cfg_vereinsname", ""),
                        saison=st.session_state.get("cfg_saison", ""),
                        logo_bytes=logo_laden(),
                    )
                    st.download_button(
                        f"⬇️ {_ql} herunterladen",
                        data=_qb,
                        file_name=f"Anleitung_{_ql.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"qt_dl_{_tid}",
                    )
                except Exception as _qe:
                    st.error(f"Fehler: {_qe}")

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

        # ── Vereins-Personalisierung ─────────────────────────────────────────
        st.markdown("### 🏟️ Vereins-Personalisierung")
        _vn = st.session_state.get("cfg_vereinsname", "")
        _sn = st.session_state.get("cfg_saison", "")
        if _vn or _sn:
            _info_parts = []
            if _vn:
                _info_parts.append(f"**Verein:** {_vn}")
            if _sn:
                _info_parts.append(f"**Saison:** {_sn}")
            st.success("  ·  ".join(_info_parts) + "  — wird im PDF-Header und Deckblatt verwendet.")
        else:
            st.info(
                "Kein Vereinsname oder Saison eingetragen. "
                "Unter **⚙️ Einstellungen → Allgemein** eintragen, um das PDF zu personalisieren."
            )

        # ── Logo: dauerhaft aus DB, optional überschreiben ───────────────────
        _logo_bytes: bytes | None = logo_laden()
        if _logo_bytes:
            import io as _io2
            try:
                _lcol1, _lcol2 = st.columns([1, 4])
                _lcol1.image(_io2.BytesIO(_logo_bytes), width=80)
                _lcol2.success(
                    "✅ Vereinslogo aus den Einstellungen wird automatisch verwendet. "
                    "Anderes Logo hochladen, um es für dieses PDF zu ersetzen."
                )
            except Exception:
                st.success("✅ Vereinslogo gespeichert — wird im PDF verwendet.")
        else:
            st.info(
                "Kein Logo gespeichert. Unter **⚙️ Einstellungen → Allgemein** dauerhaft hinterlegen, "
                "oder hier einmalig für dieses PDF hochladen."
            )
        _logo_override = st.file_uploader(
            "Alternatives Logo (nur für diesen Export, PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key="pdf_logo_upload",
            label_visibility="collapsed",
        )
        if _logo_override is not None:
            _logo_bytes = _logo_override.getvalue()

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
                        vereinsname=st.session_state.get("cfg_vereinsname", ""),
                        saison=st.session_state.get("cfg_saison", ""),
                        logo_bytes=_logo_bytes,
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

    _custom_docs_section("anleitungen", "Eigene Anleitungen")


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

    # ── Preset from profile page ───────────────────────────────────────────────
    if "vergl_preset_pid" in st.session_state:
        _preset_pid = st.session_state.pop("vergl_preset_pid")
        _preset_player = next((p for p in alle_spieler if p["id"] == _preset_pid), None)
        if _preset_player:
            st.session_state["vergl_sp1"] = _preset_player

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
    _section_header("🫁", "Ausdauer")
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

    # ── PDF-Export ────────────────────────────────────────────────────────────
    st.markdown("---")
    _ex_col, _ = st.columns([3, 7])
    with _ex_col:
        @st.cache_data(show_spinner=False)
        def _vergleich_pdf_cached(pid1, pid2, sc1, sc2):
            return generate_vergleich_pdf(
                sp1=sp1, sp2=sp2, sc1=sc1, sc2=sc2,
                fms1=fms1, fms2=fms2,
                y1=y1, y2=y2,
                spr1=spr1, spr2=spr2,
                spg1=spg1, spg2=spg2,
                agil1=agil1, agil2=agil2,
                aus1=aus1, aus2=aus2,
            )
        pdf_bytes = _vergleich_pdf_cached(pid1, pid2, sc1, sc2)
        filename = f"vergleich_{sp1['name'].replace(' ', '_')}_{sp2['name'].replace(' ', '_')}.pdf"
        st.download_button(
            label="📄 Vergleich als PDF exportieren",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            key="vergl_pdf_dl",
        )

    # ── Entwicklungsverlauf ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Entwicklungsverlauf")
    st.markdown(
        '<p style="color:#8b949e;margin-top:-8px">'
        'Athletik-Score und Einzelmodule beider Spieler im Zeitverlauf.</p>',
        unsafe_allow_html=True,
    )

    from datetime import timedelta as _tdd
    _tf_col, _ = st.columns([2, 5])
    zeitraum = _tf_col.selectbox(
        "Zeitraum",
        ["Letzte 3 Monate", "Letzte 6 Monate", "Letzte 12 Monate", "Alles"],
        index=1,
        key="vergl_zeitraum",
    )
    _today = date.today()
    if zeitraum == "Letzte 3 Monate":
        cutoff = str(_today - _tdd(days=90))
    elif zeitraum == "Letzte 6 Monate":
        cutoff = str(_today - _tdd(days=182))
    elif zeitraum == "Letzte 12 Monate":
        cutoff = str(_today - _tdd(days=365))
    else:
        cutoff = "0000-00-00"

    def _filter(rows): return [r for r in rows if (r.get("datum") or "") >= cutoff]

    h_fms1   = _filter(fms_history(pid1));          h_fms2   = _filter(fms_history(pid2))
    h_y1     = _filter(y_balance_history(pid1));    h_y2     = _filter(y_balance_history(pid2))
    h_spr1   = _filter(sprint_history(pid1));       h_spr2   = _filter(sprint_history(pid2))
    h_spg1   = _filter(sprung_history(pid1));       h_spg2   = _filter(sprung_history(pid2))
    h_agil1  = _filter(agilitaet_history(pid1));    h_agil2  = _filter(agilitaet_history(pid2))
    h_aus1   = _filter(ausdauer_history(pid1));     h_aus2   = _filter(ausdauer_history(pid2))

    def _score_timeline(fh, yh, sprh, spgh, agilh, aush):
        """Berechnet Athletik-Score für jeden Testtermin (kumulativer Zustand)."""
        state = {"fms": None, "y": None, "sprint": None, "sprung": None, "agil": None, "aus": None}
        events = (
            [(r["datum"], "fms",    r) for r in fh]
            + [(r["datum"], "y",      r) for r in yh]
            + [(r["datum"], "sprint", r) for r in sprh]
            + [(r["datum"], "sprung", r) for r in spgh]
            + [(r["datum"], "agil",   r) for r in agilh]
            + [(r["datum"], "aus",    r) for r in aush]
        )
        events.sort(key=lambda x: x[0])
        out = []
        for datum, mod, row in events:
            state[mod] = row
            sc = athletik_score(state["fms"], state["y"], state["sprint"],
                                state["sprung"], state["agil"], state["aus"])
            if sc > 0:
                out.append((datum, sc))
        return out

    tl1 = _score_timeline(h_fms1, h_y1, h_spr1, h_spg1, h_agil1, h_aus1)
    tl2 = _score_timeline(h_fms2, h_y2, h_spr2, h_spg2, h_agil2, h_aus2)

    # ── Gesamtscore-Chart ─────────────────────────────────────────────────────
    if tl1 or tl2:
        fig_tl = go.Figure()
        if tl1:
            _d1, _s1 = zip(*tl1)
            fig_tl.add_trace(go.Scatter(
                x=list(_d1), y=list(_s1),
                mode="lines+markers", name=sp1["name"],
                line=dict(color="#1f6feb", width=2.5),
                marker=dict(size=7, color="#1f6feb"),
            ))
        if tl2:
            _d2, _s2 = zip(*tl2)
            fig_tl.add_trace(go.Scatter(
                x=list(_d2), y=list(_s2),
                mode="lines+markers", name=sp2["name"],
                line=dict(color="#3fb950", width=2.5),
                marker=dict(size=7, color="#3fb950"),
            ))
        fig_tl.update_layout(
            title=dict(text="Athletik-Gesamtscore (0–100)",
                       font=dict(size=14, color=C["text"]), x=0.0),
            xaxis=dict(gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"])),
            yaxis=dict(title="Score", range=[0, 100], gridcolor=C["surface2"],
                       linecolor=C["border"], tickfont=dict(color=C["muted"])),
            paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
            legend=dict(bgcolor=C["surface"], bordercolor=C["border"], borderwidth=1,
                        orientation="h", x=0.5, xanchor="center", y=-0.18),
            margin=dict(l=40, r=20, t=50, b=70),
            height=320,
        )
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info(f"Noch keine Testdaten im Zeitraum «{zeitraum}» vorhanden.")

    # ── Einzelmodul-Charts (Expander) ─────────────────────────────────────────
    def _modul_chart(title: str, rows1: list, rows2: list,
                     field: str, label: str, unit: str = "",
                     invert: bool = False, ymin=None, ymax=None):
        """Hilfsfunktion: Liniendiagramm eines Rohwerts für beide Spieler."""
        pts1 = [(r["datum"], float(r[field])) for r in rows1 if r.get(field)]
        pts2 = [(r["datum"], float(r[field])) for r in rows2 if r.get(field)]
        if not pts1 and not pts2:
            return
        fig = go.Figure()
        if pts1:
            _x1, _y1 = zip(*pts1)
            fig.add_trace(go.Scatter(
                x=list(_x1), y=list(_y1),
                mode="lines+markers", name=sp1["name"],
                line=dict(color="#1f6feb", width=2),
                marker=dict(size=6),
            ))
        if pts2:
            _x2, _y2 = zip(*pts2)
            fig.add_trace(go.Scatter(
                x=list(_x2), y=list(_y2),
                mode="lines+markers", name=sp2["name"],
                line=dict(color="#3fb950", width=2),
                marker=dict(size=6),
            ))
        note = " (niedriger = besser)" if invert else ""
        fig.update_layout(
            title=dict(text=f"{title}{note}", font=dict(size=13, color=C["text"]), x=0.0),
            xaxis=dict(gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"], size=9)),
            yaxis=dict(title=f"{label}{unit}", autorange="reversed" if invert else True,
                       gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"], size=9),
                       range=[ymin, ymax] if ymin is not None else None),
            paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
            legend=dict(bgcolor=C["surface"], bordercolor=C["border"], borderwidth=1,
                        orientation="h", x=0.5, xanchor="center", y=-0.22, font=dict(size=10)),
            margin=dict(l=40, r=10, t=40, b=60),
            height=260,
        )
        return fig

    any_module_data = any([h_fms1, h_fms2, h_y1, h_y2, h_spr1, h_spr2,
                           h_spg1, h_spg2, h_agil1, h_agil2, h_aus1, h_aus2])
    if any_module_data:
        with st.expander("📊 Einzelmodule im Detail anzeigen"):
            # Row 1: FMS + Y-Balance
            mc1, mc2 = st.columns(2)
            with mc1:
                fig = _modul_chart("FMS-Score", h_fms1, h_fms2,
                                   "score", "Punkte", "/21", ymin=0, ymax=21)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_fms1 or h_fms2: st.caption("FMS — kein Wert im Zeitraum.")
            with mc2:
                # Y-Balance: compute average composite per row
                def _yb_avg(rows):
                    out = []
                    for r in rows:
                        cr = r.get("composite_rechts") or 0
                        cl = r.get("composite_links") or 0
                        if cr or cl:
                            out.append({"datum": r["datum"], "_avg": (cr + cl) / 2})
                    return out
                h_y1a = _yb_avg(h_y1); h_y2a = _yb_avg(h_y2)
                fig = _modul_chart("Y-Balance Ø Composite", h_y1a, h_y2a,
                                   "_avg", "%", ymin=70, ymax=110)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_y1 or h_y2: st.caption("Y-Balance — kein Wert im Zeitraum.")

            # Row 2: Sprint + Sprung
            mc3, mc4 = st.columns(2)
            with mc3:
                fig = _modul_chart("Sprint 10 m", h_spr1, h_spr2,
                                   "beste_10m", "Zeit", " s", invert=True)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_spr1 or h_spr2: st.caption("Sprint — kein 10-m-Wert im Zeitraum.")
            with mc4:
                fig = _modul_chart("CMJ beidbeinig", h_spg1, h_spg2,
                                   "cmj_beid", "Höhe", " cm", ymin=0)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_spg1 or h_spg2: st.caption("Sprung — kein CMJ-Wert im Zeitraum.")

            # Row 3: Agilität + Ausdauer
            mc5, mc6 = st.columns(2)
            with mc5:
                # Prefer t_test, fall back to t505_r
                def _agil_rows(rows):
                    out = []
                    for r in rows:
                        v = r.get("t_test") or r.get("t505_r")
                        if v:
                            out.append({"datum": r["datum"], "_agil": float(v)})
                    return out
                h_ag1f = _agil_rows(h_agil1); h_ag2f = _agil_rows(h_agil2)
                fig = _modul_chart("Agilität (T-Test / 505)", h_ag1f, h_ag2f,
                                   "_agil", "Zeit", " s", invert=True)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_agil1 or h_agil2: st.caption("Agilität — kein Wert im Zeitraum.")
            with mc6:
                fig = _modul_chart("Yo-Yo Distanz", h_aus1, h_aus2,
                                   "distanz_m", "Distanz", " m", ymin=0)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_aus1 or h_aus2: st.caption("Ausdauer — kein Wert im Zeitraum.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DIAGNOSTIK ÜBERSICHT (Kachel-Grid)
# ══════════════════════════════════════════════════════════════════════════════

def page_diagnostik_overview() -> None:
    """Diagnostik-Startscreen: Kachelübersicht aller 6 Testmodule."""
    st.markdown(
        section_header("🔬 Diagnostik", "Testübersicht — wähle ein Modul und starte direkt"),
        unsafe_allow_html=True,
    )

    sid = st.session_state.get("global_player_id")
    if not sid:
        st.markdown(
            empty_state("👤", "Kein Spieler ausgewählt",
                        "Bitte einen Spieler in der Seitenleiste auswählen."),
            unsafe_allow_html=True,
        )
        return

    # ── Last results ──────────────────────────────────────────────────────────
    fms_d   = fms_letzter(sid)
    yb_d    = y_balance_letzter(sid)
    spr_d   = sprint_letzter(sid)
    sprg_d  = sprung_letzter(sid)
    agil_d  = agilitaet_letzter(sid)
    aus_d   = ausdauer_letzter(sid)
    kraft_d = kraft_letzter(sid)
    spiro_d = spiro_test_letzter(sid)

    def _rating_color(rating: str | None) -> str:
        if not rating:
            return C["muted"]
        r = rating.lower()
        if any(x in r for x in ["sehr gut", "gut", "ausgezeichnet", "unauffällig",
                                  "keine asym", "keine auffäl", "optimal", "symmetrisch", "kein akuter"]):
            return C["green"]
        if any(x in r for x in ["beobachten", "mittel", "grenzwertig", "gering", "durchschnitt"]):
            return C["yellow"]
        if any(x in r for x in ["aktionsbedarf", "handlungsbedarf", "verbesserung",
                                  "risiko", "mangelhaft", "schlecht", "asymmetrie",
                                  "auffällig", "hoch", "schwäche", "kritisch", "unterdurchschnitt"]):
            return C["red"]
        return C["muted"]

    def _fmt_date(d: str | None) -> str:
        if not d:
            return "Noch kein Test"
        try:
            from datetime import datetime as _dt
            return _dt.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            return d

    # ── Key metric per test ───────────────────────────────────────────────────
    def _yb_metric():
        if not yb_d:
            return None, None
        cr = yb_d.get("composite_rechts")
        cl = yb_d.get("composite_links")
        if cr and cl:
            return f"R {cr:.0f} % / L {cl:.0f} %", yb_d.get("asymmetrie")
        return None, None

    def _agil_metric():
        if not agil_d:
            return None, None
        if agil_d.get("t_test"):
            return f"T-Test: {agil_d['t_test']:.2f} s", agil_d.get("bew_t_test")
        if agil_d.get("illinois"):
            return f"Illinois: {agil_d['illinois']:.2f} s", agil_d.get("bew_illinois")
        if agil_d.get("t505_r"):
            return f"505: R {agil_d['t505_r']:.2f} s", agil_d.get("bew_505")
        return None, None

    yb_metric, yb_rating   = _yb_metric()
    agil_metric, agil_rating = _agil_metric()

    tiles = [
        {
            "icon": "📝", "name": "FMS",
            "desc": "Functional Movement Screen",
            "sub":  "📝 FMS",
            "metric": f"{fms_d['score']}/21" if fms_d else None,
            "rating": (
                fms_d.get("bewertung","") + " — " +
                __import__("fms").fms_bewertung_kurz(fms_d.get("score"))[:60] + "…"
                if fms_d else None
            ),
            "date":   fms_d.get("datum")     if fms_d else None,
        },
        {
            "icon": "📏", "name": "Y-Balance",
            "desc": "Dynamische Gleichgewichtskontrolle",
            "sub":  "📏 Y-Balance",
            "metric": yb_metric,
            "rating": yb_rating,
            "date":   yb_d.get("datum") if yb_d else None,
        },
        {
            "icon": "⚡", "name": "Sprint",
            "desc": "Lineare Schnelligkeit",
            "sub":  "⚡ Sprint",
            "metric": (f"10 m: {spr_d['beste_10m']:.2f} s"
                       if spr_d and spr_d.get("beste_10m") else None),
            "rating": spr_d.get("bewertung_10m") if spr_d else None,
            "date":   spr_d.get("datum")         if spr_d else None,
        },
        {
            "icon": "🦘", "name": "Sprung",
            "desc": "Sprungkraft & Reaktivkraft",
            "sub":  "🦘 Sprung",
            "metric": (f"CMJ: {sprg_d['cmj_beid']:.1f} cm"
                       if sprg_d and sprg_d.get("cmj_beid") else None),
            "rating": sprg_d.get("bewertung_cmj") if sprg_d else None,
            "date":   sprg_d.get("datum")         if sprg_d else None,
        },
        {
            "icon": "🔀", "name": "Agilität",
            "desc": "Richtungswechsel & Reaktion",
            "sub":  "🔀 Agilität",
            "metric": agil_metric,
            "rating": agil_rating,
            "date":   agil_d.get("datum") if agil_d else None,
        },
        {
            "icon": "🫁", "name": "Ausdauer",
            "desc": "Aerobe Kapazität (Yo-Yo)",
            "sub":  "🫁 Ausdauer",
            "metric": (f"VO₂max: {aus_d['vo2max']:.1f} ml·kg⁻¹·min⁻¹"
                       if aus_d and aus_d.get("vo2max") else None),
            "rating": aus_d.get("bewertung") if aus_d else None,
            "date":   aus_d.get("datum")     if aus_d else None,
        },
        {
            "icon": "💪", "name": "Kraftdiagnostik",
            "desc": "Bankdrücken 1RM & Rumpfkraft",
            "sub":  "💪 Kraft",
            "metric": (
                f"1RM: {kraft_d.get('direktes_1rm') or kraft_d.get('geschaetztes_1rm'):.1f} kg"
                if kraft_d and (kraft_d.get("direktes_1rm") or kraft_d.get("geschaetztes_1rm"))
                else ("Rumpf: %.0f s" % kraft_d["rumpf_gesamt_sekunden"]
                      if kraft_d and kraft_d.get("rumpf_gesamt_sekunden") else None)
            ),
            "rating": (
                __import__("kraft").beurteilung_relative_kraft(
                    kraft_d.get("relative_kraft_direkt") or kraft_d.get("relative_kraft_geschaetzt")
                )[0]  # alter nicht verfügbar im Vergleichs-Kontext
                if kraft_d and (kraft_d.get("relative_kraft_direkt") or kraft_d.get("relative_kraft_geschaetzt"))
                else ("Ventral: %.0f s" % kraft_d["ventral_sekunden"]
                      if kraft_d and kraft_d.get("ventral_sekunden") else None)
            ),
            "date": kraft_d.get("datum") if kraft_d else None,
        },
        {
            "icon": "🔬", "name": "Stufentest",
            "desc": "Spiroergometrie / Laktatstufen",
            "sub":  "🫁 Ausdauer",  # öffnet Ausdauer-Seite (Selector wählt Spiro)
            "metric": (
                f"V max: {spiro_d['maximale_geschwindigkeit']:.1f} km/h"
                if spiro_d and spiro_d.get("maximale_geschwindigkeit") else
                (f"Schwelle: {spiro_d['schwelle_geschwindigkeit']:.1f} km/h"
                 if spiro_d and spiro_d.get("schwelle_geschwindigkeit") else None)
            ),
            "rating": (
                f"VO₂peak: {spiro_d['vo2_peak']:.1f}"
                if spiro_d and spiro_d.get("vo2_peak") else
                (f"VO₂max: {spiro_d['vo2_max']:.1f}"
                 if spiro_d and spiro_d.get("vo2_max") else None)
            ),
            "date": spiro_d.get("datum") if spiro_d else None,
        },
    ]

    # ── Render grid: Zeile 1 = 4 Kacheln, Zeile 2 = 4 Kacheln ───────────────
    cols_top = st.columns(4, gap="medium")
    cols_bot = st.columns(4, gap="medium")
    all_cols = cols_top + cols_bot

    for i, tile in enumerate(tiles):
        with all_cols[i]:
            has_data     = tile["metric"] is not None
            rc           = _rating_color(tile["rating"]) if has_data else C["border"]
            dot          = (
                f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                f'background:{rc};margin-right:5px;vertical-align:middle"></span>'
            )

            metric_html  = (
                f'<div style="font-size:22px;font-weight:800;color:{C["text"]};'
                f'margin:10px 0 2px;letter-spacing:-0.5px">{tile["metric"]}</div>'
                if has_data else
                f'<div style="font-size:12px;color:{C["muted"]};margin:10px 0 2px;'
                f'font-style:italic">Noch kein Test vorhanden</div>'
            )
            rating_html  = (
                f'<div style="font-size:11px;color:{rc};font-weight:600;margin-bottom:6px">'
                f'{dot}{tile["rating"]}</div>'
                if has_data and tile["rating"] else
                f'<div style="font-size:11px;color:{C["muted"]};margin-bottom:6px">—</div>'
            )

            st.markdown(
                f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                f'border-top:3px solid {rc};border-radius:12px;padding:16px 18px 10px;'
                f'margin-bottom:2px;min-height:140px">'
                f'<div style="display:flex;align-items:center;gap:9px">'
                f'<span style="font-size:24px;line-height:1">{tile["icon"]}</span>'
                f'<div>'
                f'<div style="font-size:15px;font-weight:700;color:{C["text"]}">{tile["name"]}</div>'
                f'<div style="font-size:10px;color:{C["muted"]};letter-spacing:0.5px">'
                f'{tile["desc"].upper()}</div>'
                f'</div></div>'
                f'{metric_html}'
                f'{rating_html}'
                f'<div style="font-size:10px;color:{C["muted"]}">🗓 {_fmt_date(tile["date"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "Test starten →",
                key=f"tile_btn_{i}",
                use_container_width=True,
            ):
                st.session_state["_nav_sub_diagnostik_goto"] = tile["sub"]
                st.rerun()

        # small vertical gap between rows
        if i == 3:
            st.write("")


# ══════════════════════════════════════════════════════════════════════════════
# TESTPROTOKOLL DRUCKEN
# ══════════════════════════════════════════════════════════════════════════════

def page_testprotokoll():
    st.markdown(
        section_header("🖨️ Testprotokoll drucken",
                       "Leere Druckbogen fuer die papierbasierte Erfassung"),
        unsafe_allow_html=True,
    )

    alle_spieler = spieler_laden()

    # ── Schritt 1: Variante ────────────────────────────────────────────────────
    st.markdown("### Schritt 1 — Variante")
    variante = st.radio(
        "Druckvariante",
        ["📄 Leeres Protokoll (ohne Spieler)", "👤 Protokoll mit Spieler(n)"],
        horizontal=True,
        label_visibility="collapsed",
        key="proto_variante",
    )
    leer = variante.startswith("📄")

    # ── Schritt 2: Tests auswählen ─────────────────────────────────────────────
    st.markdown("### Schritt 2 — Tests auswählen")

    # Schnellauswahl nach Bereich
    _BEREICH_FILTER = {
        "Alle Tests": list(TEST_REIHENFOLGE),
        "Beweglichkeit & Stabilität": ["fms", "y_balance"],
        "Schnelligkeit & Kraft":       ["sprint", "jump", "agility", "kraft"],
        "Ausdauer & Körper":           ["yoyo", "anthropometrie"],
    }
    bereich_wahl = st.selectbox(
        "Schnellauswahl nach Bereich",
        list(_BEREICH_FILTER.keys()),
        key="proto_bereich_filter",
        label_visibility="visible",
    )
    vorauswahl = _BEREICH_FILTER[bereich_wahl]

    col_all, col_none = st.columns([2, 8])
    if col_all.button("Alle auswählen", key="proto_all"):
        for tid in TEST_REIHENFOLGE:
            st.session_state[f"proto_test_{tid}"] = True
    if col_none.button("Alle abwählen", key="proto_none"):
        for tid in TEST_REIHENFOLGE:
            st.session_state[f"proto_test_{tid}"] = False

    cols = st.columns(4)
    selected_tests = []
    for i, tid in enumerate(TEST_REIHENFOLGE):
        default_val = tid in vorauswahl if bereich_wahl != "Alle Tests" else True
        checked = cols[i % 4].checkbox(
            TEST_NAMEN[tid],
            value=st.session_state.get(f"proto_test_{tid}", default_val),
            key=f"proto_test_{tid}",
        )
        if checked:
            selected_tests.append(tid)

    # ── Schritt 3: Kopfdaten vorausfüllen (optional) ───────────────────────────
    st.markdown("### Schritt 3 — Kopfdaten (optional)")
    st.caption("Diese Angaben werden in den Protokoll-Header gedruckt.")
    _h1, _h2, _h3 = st.columns(3)
    proto_datum    = _h1.text_input("Testdatum",    value="", placeholder="TT.MM.JJJJ", key="proto_datum")
    proto_trainer  = _h2.text_input("Trainer",      value=st.session_state.get("cfg_trainer_name", ""), placeholder="Name des Trainers", key="proto_trainer")
    proto_ort      = _h3.text_input("Testort",      value="", placeholder="z. B. Sportplatz", key="proto_ort")

    # Trainer-Name für spätere Sessions merken
    if proto_trainer:
        st.session_state["cfg_trainer_name"] = proto_trainer

    # ── Schritt 4: Spieler (nur bei "mit Spieler") ────────────────────────────
    selected_spieler = []
    if not leer:
        st.markdown("### Schritt 4 — Spieler auswählen")

        # Mannschaft-Filter
        mannschaften = sorted({p.get("mannschaft") or "Ohne Mannschaft" for p in alle_spieler}) if alle_spieler else []
        if mannschaften:
            mann_filter = st.selectbox(
                "Nach Mannschaft filtern",
                ["Alle Mannschaften"] + mannschaften,
                key="proto_mann_filter",
            )
            if mann_filter == "Alle Mannschaften":
                spieler_fuer_auswahl = alle_spieler
            else:
                spieler_fuer_auswahl = [
                    p for p in alle_spieler
                    if (p.get("mannschaft") or "Ohne Mannschaft") == mann_filter
                ]
        else:
            spieler_fuer_auswahl = alle_spieler

        if not spieler_fuer_auswahl:
            st.warning("Keine Spieler gefunden. Bitte zuerst Spieler anlegen.")
        else:
            opts = {p["name"]: p for p in spieler_fuer_auswahl}
            # Schnell: ganze Mannschaft auswählen
            if st.button("✅ Alle angezeigten Spieler auswählen", key="proto_all_sp"):
                st.session_state["proto_spieler_sel"] = list(opts.keys())
            auswahl = st.multiselect(
                "Spieler (Mehrfachauswahl möglich)",
                list(opts.keys()),
                key="proto_spieler_sel",
            )
            selected_spieler = [opts[n] for n in auswahl]

    # ── Vorschau ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Vorschau")
    if not selected_tests:
        st.warning("Bitte mindestens einen Test auswählen.")
        return

    n_spieler = max(len(selected_spieler), 1)
    info_cols = st.columns(4)
    info_cols[0].metric("Ausgewählte Tests", len(selected_tests))
    info_cols[1].metric("Spieler / Bögen", n_spieler)
    info_cols[2].metric("Geschätzte Seiten", f"ca. {n_spieler}–{n_spieler * 3}")
    info_cols[3].metric("Testdatum", proto_datum or "handschriftlich")

    st.markdown("**Tests:**  " + "  ·  ".join([f"`{TEST_NAMEN[t]}`" for t in selected_tests]))
    if not leer and selected_spieler:
        st.markdown("**Spieler:**  " + "  ·  ".join([f"`{p['name']}`" for p in selected_spieler]))
    if proto_trainer:
        st.markdown(f"**Trainer:**  `{proto_trainer}`")
    if proto_ort:
        st.markdown(f"**Ort:**  `{proto_ort}`")

    if leer:
        st.info("📄 Leeres Protokoll — Spielerdaten werden handschriftlich eingetragen.")
    elif not selected_spieler:
        st.warning("Bitte mindestens einen Spieler auswählen, oder zur Variante 'Leeres Protokoll' wechseln.")
        return

    # ── Druck-Tipps ───────────────────────────────────────────────────────────
    with st.expander("🖨️ Druck-Tipps", expanded=False):
        st.markdown(
            "- **Papierformat:** DIN A4, Hochformat\n"
            "- **Ränder:** min. 10 mm (Systemstandard)\n"
            "- **Druckskalierung:** 100 % (nicht 'Auf Seitengröße anpassen')\n"
            "- **Farbe:** Schwarz/Weiß reicht aus\n"
            "- **Empfehlung:** Nach dem Druck laminieren für Outdoor-Einsatz"
        )

    # ── PDF generieren ─────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("📥 Testprotokoll PDF erstellen", use_container_width=True,
                 type="primary", key="proto_gen"):
        with st.spinner("PDF wird erstellt …"):
            pdf_bytes = generate_testprotokoll(
                test_ids=selected_tests,
                spieler_liste=selected_spieler if not leer else None,
                variante="leer" if leer else "spieler",
                logo_bytes=logo_laden(),
            )
        dateiname = "testprotokoll_leer.pdf" if leer else "testprotokoll_spieler.pdf"
        st.download_button(
            label="⬇️ PDF herunterladen",
            data=pdf_bytes,
            file_name=dateiname,
            mime="application/pdf",
            use_container_width=True,
            key="proto_dl",
        )
        st.success(f"✅ PDF erstellt — {len(selected_tests)} Test(s), {n_spieler} Bogen/Bögen.")

    _custom_docs_section("protokolle", "Eigene Protokolle")


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION  (7-section structure)
# ══════════════════════════════════════════════════════════════════════════════

# ── Sub-page maps per section ─────────────────────────────────────────────────
def page_ueber_software():
    """Über die Software — Branding, Kontakt, Urheberrecht."""
    import io as _uio
    _ueber_logo = logo_laden()
    if _ueber_logo:
        try:
            _ulcol, _umcol, _urcol = st.columns([1, 2, 1])
            with _umcol:
                st.image(_uio.BytesIO(_ueber_logo), use_container_width=True)
        except Exception:
            pass
    _icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_logo.png")
    if not _ueber_logo and os.path.exists(_icon_path):
        try:
            _ulcol2, _umcol2, _urcol2 = st.columns([1, 2, 1])
            with _umcol2:
                st.image(_icon_path, use_container_width=True)
        except Exception:
            pass
    _header_icon = "" if (_ueber_logo or os.path.exists(_icon_path)) else '<div style="font-size:64px">⚽</div>'
    _header_pad  = "16px" if _ueber_logo else "40px"
    st.markdown(
        f'<div style="max-width:700px;margin:0 auto">'
        f'<div style="text-align:center;padding:{_header_pad} 0 24px">'
        f'{_header_icon}'
        f'<h1 style="color:#e6edf3;font-size:22px;font-weight:800;'
        f'letter-spacing:0.5px;margin:16px 0 4px">{APP_NAME}</h1>'
        f'<div style="color:#58a6ff;font-size:12px;font-weight:600;'
        f'letter-spacing:2px">VERSION {APP_VERSION}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;'
            f'border-radius:10px;padding:20px 22px;margin-bottom:12px">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
            f'margin-bottom:10px">SOFTWARE</div>'
            f'<div style="color:#e6edf3;font-weight:700;font-size:14px;margin-bottom:4px">'
            f'{APP_NAME}</div>'
            f'<div style="color:#8b949e;font-size:12px">Version {APP_VERSION}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;'
            f'border-radius:10px;padding:20px 22px;margin-bottom:12px">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
            f'margin-bottom:10px">ENTWICKLER</div>'
            f'<div style="color:#e6edf3;font-weight:700;font-size:14px;margin-bottom:8px">'
            f'{APP_DEVELOPER}</div>'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
            f'margin-bottom:6px">KONTAKT</div>'
            f'<div style="color:#58a6ff;font-size:12px;margin-bottom:2px">'
            f'✉ {APP_EMAIL}</div>'
            f'<div style="color:#8b949e;font-size:12px">☎ {APP_PHONE}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_r:
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;'
            f'border-radius:10px;padding:20px 22px;margin-bottom:12px">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
            f'margin-bottom:10px">COPYRIGHT</div>'
            f'<div style="color:#e6edf3;font-weight:700;font-size:13px;margin-bottom:4px">'
            f'{APP_COPYRIGHT}</div>'
            f'<div style="color:#8b949e;font-size:11px;margin-top:8px">'
            f'Diese Software befindet sich in kontinuierlicher Weiterentwicklung.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        mailto_link = (
            f"mailto:{APP_EMAIL}?subject=Bruce Football Performance Diagnostics — Supportanfrage"
            f"&body=Hallo Herr Daroish,%0D%0A%0D%0A"
        )
        st.link_button(
            "📧 Entwickler kontaktieren",
            mailto_link,
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### ⚖️ Urheberrecht")
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #d29922;'
        f'border-radius:6px;padding:16px 18px;color:#8b949e;font-size:12px;'
        f'line-height:1.7">'
        f'Diese Software ist urheberrechtlich geschützt. Das Kopieren, Vervielfältigen, '
        f'Verändern, Verbreiten oder die Weitergabe der Software oder von Teilen der '
        f'Software ohne ausdrückliche schriftliche Genehmigung des Entwicklers ist untersagt. '
        f'Zuwiderhandlungen können rechtliche Konsequenzen nach den geltenden gesetzlichen '
        f'Bestimmungen nach sich ziehen.'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption(APP_COPYRIGHT)


_SUB_SPIELER = {
    "👥 Verwaltung":        page_spieler,
    "🏃 Profil & Diagnostik": page_spieler_profil,
    "📐 Anthropometrie":    page_anthropometrie,
}
_SUB_DIAGNOSTIK = {
    "🏠 Übersicht":         page_diagnostik_overview,
    "📝 FMS":               page_fms,
    "📏 Y-Balance":         page_ybalance,
    "⚡ Sprint":             page_sprint,
    "🦘 Sprung":             page_sprung,
    "🔀 Agilität":          page_agilitaet,
    "🫁 Ausdauer":  page_ausdauer,
    "💪 Kraft":              page_kraft,
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
    "📄  Dokumente",
    "⚙️  Einstellungen",
    "ℹ️  Über",
]

with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="padding:10px 0 8px;text-align:center">'
        f'<div style="font-weight:800;font-size:13px;color:{C["text"]};letter-spacing:0.5px;margin-top:6px">BRUCE FOOTBALL</div>'
        f'<div style="font-weight:700;font-size:11px;color:{C["text"]};letter-spacing:0.5px">PERFORMANCE DIAGNOSTICS</div>'
        f'<div style="font-size:9px;color:{C["muted"]};margin-top:2px">v{APP_VERSION}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if os.path.exists(_APP_ICON_PATH):
        st.image(_APP_ICON_PATH, width=64)

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
    if "_nav_sub_diagnostik_goto" in st.session_state:
        st.session_state["nav_sub_diagnostik"] = st.session_state.pop("_nav_sub_diagnostik_goto")
    if "_nav_sub_spieler_goto" in st.session_state:
        st.session_state["nav_sub_spieler"] = st.session_state.pop("_nav_sub_spieler_goto")

    # ── Main navigation (mit Übersetzung) ────────────────────────────────────
    _NAV_TRANS = {
        "🏠  Startseite":    {"de": "🏠  Startseite",    "en": "🏠  Dashboard",    "tr": "🏠  Ana Sayfa",    "es": "🏠  Inicio",        "fr": "🏠  Accueil",       "pt": "🏠  Início",        "ru": "🏠  Главная",       "ar": "🏠  الرئيسية"},
        "👤  Spieler":       {"de": "👤  Spieler",        "en": "👤  Players",      "tr": "👤  Oyuncular",    "es": "👤  Jugadores",     "fr": "👤  Joueurs",       "pt": "👤  Jogadores",     "ru": "👤  Игроки",        "ar": "👤  اللاعبون"},
        "🔬  Diagnostik":    {"de": "🔬  Diagnostik",     "en": "🔬  Diagnostics",  "tr": "🔬  Tanı",         "es": "🔬  Diagnóstico",   "fr": "🔬  Diagnostic",    "pt": "🔬  Diagnóstico",   "ru": "🔬  Диагностика",   "ar": "🔬  التشخيص"},
        "📅  Training":      {"de": "📅  Training",       "en": "📅  Training",     "tr": "📅  Antrenman",    "es": "📅  Entrenamiento", "fr": "📅  Entraînement",  "pt": "📅  Treino",        "ru": "📅  Тренировка",    "ar": "📅  التدريب"},
        "📈  Entwicklung":   {"de": "📈  Entwicklung",    "en": "📈  Development",  "tr": "📈  Gelişim",      "es": "📈  Desarrollo",    "fr": "📈  Développement", "pt": "📈  Desenvolvimento","ru": "📈  Развитие",       "ar": "📈  التطور"},
        "⚖️  Vergleich":     {"de": "⚖️  Vergleich",     "en": "⚖️  Comparison",   "tr": "⚖️  Karşılaştır", "es": "⚖️  Comparación",  "fr": "⚖️  Comparaison",   "pt": "⚖️  Comparação",    "ru": "⚖️  Сравнение",     "ar": "⚖️  المقارنة"},
        "👥  Mannschaft":    {"de": "👥  Mannschaft",     "en": "👥  Team",         "tr": "👥  Takım",        "es": "👥  Equipo",        "fr": "👥  Équipe",        "pt": "👥  Equipa",        "ru": "👥  Команда",        "ar": "👥  الفريق"},
        "📄  Dokumente":      {"de": "📄  Dokumente",      "en": "📄  Documents",    "tr": "📄  Belgeler",     "es": "📄  Documentos",    "fr": "📄  Documents",      "pt": "📄  Documentos",    "ru": "📄  Документы",     "ar": "📄  المستندات"},
        "⚙️  Einstellungen": {"de": "⚙️  Einstellungen", "en": "⚙️  Settings",     "tr": "⚙️  Ayarlar",     "es": "⚙️  Ajustes",      "fr": "⚙️  Paramètres",    "pt": "⚙️  Definições",    "ru": "⚙️  Настройки",     "ar": "⚙️  الإعدادات"},
        "ℹ️  Über":          {"de": "ℹ️  Über",           "en": "ℹ️  About",        "tr": "ℹ️  Hakkında",    "es": "ℹ️  Acerca de",    "fr": "ℹ️  À propos",      "pt": "ℹ️  Sobre",         "ru": "ℹ️  О программе",   "ar": "ℹ️  حول"},
    }
    _cur_lang = get_lang()
    section = st.radio(
        "",
        _MAIN_SECTIONS,
        key="nav_section",
        label_visibility="collapsed",
        format_func=lambda x: _NAV_TRANS.get(x, {}).get(_cur_lang, x),
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

    # ── Copyright-Footer ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="position:fixed;bottom:0;left:0;width:240px;padding:8px 12px;'
        f'background:{C["bg"]};border-top:1px solid {C["border"]};z-index:100">'
        f'<div style="font-size:9px;color:{C["muted"]};text-align:center;line-height:1.5">'
        f'{APP_COPYRIGHT}<br>'
        f'<a href="ℹ️  Über" style="color:{C["muted"]};text-decoration:none">'
        f'v{APP_VERSION}</a>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

# ── Route ─────────────────────────────────────────────────────────────────────
_check_save_ok()
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
elif section == "📄  Dokumente":
    page_dokumente()
elif section == "⚙️  Einstellungen":
    page_einstellungen()
elif section == "ℹ️  Über":
    page_ueber_software()
