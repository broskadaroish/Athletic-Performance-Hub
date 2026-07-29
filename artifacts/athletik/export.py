"""
export.py — Kader-Export als Excel-Datei
=========================================
Erstellt eine .xlsx-Datei mit zwei Tabellenblättern:
  1. Kader — alle Spieler mit Stammdaten und letzten Testwerten
  2. Verletzungshistorie — alle Verletzungen des gesamten Kaders
"""

import io
from datetime import date

import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter

from database import (
    spieler_laden,
    verletzungen_laden,
    anthropometrie_letzter,
    fms_letzter,
    y_balance_letzter,
    sprint_letzter,
    sprung_letzter,
    agilitaet_letzter,
    ausdauer_letzter,
    berechne_alter,
)
from analytics import risiko_score, risiko_label, athletik_score


# ─── Farben (dunkel, passend zum App-Theme) ───────────────────────────────────
_HDR_BG   = "1C2333"   # Kopfzeilen-Hintergrund (dunkelblau)
_HDR_FG   = "E6EDF3"   # Kopfzeilen-Schrift (hell)
_ALT_BG   = "161B27"   # Alternating row (dunkel)
_NORM_BG  = "0D1117"   # Normale Zeile
_ACCENT   = "238636"   # Grün (Athletik-Score gut)
_WARN     = "D29922"   # Gelb
_DANGER   = "F85149"   # Rot
_BORDER   = "30363D"   # Rahmenfarbe
_INJ_BG   = "1A1F2E"   # Verletzungsblatt Hintergrund
_INJ_HDR  = "6E40C9"   # Verletzungsblatt Header (lila)


def _thin_border():
    s = Side(style="thin", color=_BORDER)
    return Border(left=s, right=s, top=s, bottom=s)


def _header_style(cell, bg=_HDR_BG, fg=_HDR_FG, bold=True):
    cell.font      = Font(name="Calibri", bold=bold, color=fg, size=10)
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = _thin_border()


def _data_style(cell, bg=_NORM_BG, fg="C9D1D9", bold=False, align="center"):
    cell.font      = Font(name="Calibri", bold=bold, color=fg, size=10)
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal=align, vertical="center")
    cell.border    = _thin_border()


def _set_col_widths(ws, widths: dict):
    """widths: {col_letter: width}"""
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _val(d, key, fallback="—"):
    """Safe dict getter with fallback."""
    if not d:
        return fallback
    v = d.get(key)
    return v if v is not None else fallback


# ─── Blatt 1: Kader ──────────────────────────────────────────────────────────

_KADER_HEADERS = [
    # Stammdaten
    "Name", "Vorname", "Nachname", "Geburtsdatum", "Alter", "Geschlecht",
    "Altersklasse", "Hauptposition", "Nebenposition", "Spielbein",
    "Mannschaft", "Leistungsniveau", "Trainingsstatus",
    # Anthropometrie
    "Größe (cm)", "Gewicht (kg)", "BMI", "Körperfett (%)", "Muskelmasse (kg)",
    "Reifestatus",
    # Athletik Score & Risiko
    "Athletik Score", "Risiko",
    # FMS
    "FMS Score", "FMS Bewertung", "FMS Asymmetrie",
    # Y-Balance
    "YBal Composite R (%)", "YBal Composite L (%)", "YBal Asymmetrie",
    # Sprint
    "Sprint 5m (s)", "Sprint 10m (s)", "Sprint 20m (s)", "Sprint 30m (s)",
    "Sprint Beschl.-Index",
    # Sprung
    "CMJ beid. (cm)", "CMJ re (cm)", "CMJ li (cm)", "CMJ Asymmetrie (%)",
    "Squat Jump (cm)", "Drop Jump Höhe (cm)", "RSI", "Standweit (cm)",
    # Agilität
    "505 re (s)", "505 li (s)", "505 Asym. (%)", "5-10-5 (s)",
    "T-Test (s)", "Illinois (s)",
    # Ausdauer
    "Ausdauer Test-Typ", "Distanz (m)", "VO₂max", "HF max",
    # Datum letzter Tests
    "Datum FMS", "Datum Sprint", "Datum Sprung", "Datum Agilität", "Datum Ausdauer",
]


def _build_kader_sheet(ws):
    """Füllt Blatt 1 mit allen Spielern und ihren letzten Testwerten."""
    ws.title = "Kader"
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    # Kopfzeile
    for col_idx, header in enumerate(_KADER_HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        _header_style(cell)

    # Zeilen
    all_players = spieler_laden()
    for row_idx, p in enumerate(all_players, start=2):
        pid    = p["id"]
        anthr  = anthropometrie_letzter(pid)
        fms    = fms_letzter(pid)
        y      = y_balance_letzter(pid)
        sprint = sprint_letzter(pid)
        sprung = sprung_letzter(pid)
        agil   = agilitaet_letzter(pid)
        aus    = ausdauer_letzter(pid)
        verlet = []  # nur für Risiko-Score nötig — wir laden separat
        from database import verletzungen_laden as _vl
        verlet = _vl(pid)
        rs     = risiko_score(fms, y, verlet)
        _, level = risiko_label(rs)
        sc     = athletik_score(fms, y, sprint, sprung, agil, aus)
        alter  = berechne_alter(p.get("geburtsdatum")) or "—"

        risiko_de = {"hoch": "Hoch ⚠", "mittel": "Mittel", "gering": "Gering"}.get(level, level)

        row_data = [
            # Stammdaten
            p.get("name", "—"),
            p.get("vorname") or "—",
            p.get("nachname") or "—",
            p.get("geburtsdatum") or "—",
            alter,
            p.get("geschlecht") or "—",
            p.get("altersklasse") or "—",
            p.get("hauptposition") or p.get("position") or "—",
            p.get("nebenposition") or "—",
            p.get("spielbein") or "—",
            p.get("mannschaft") or "—",
            p.get("leistungsniveau") or "—",
            p.get("trainingsstatus") or "—",
            # Anthropometrie
            _val(anthr, "groesse"),
            _val(anthr, "gewicht"),
            _val(anthr, "bmi"),
            _val(anthr, "koerperfett"),
            _val(anthr, "muskelmasse"),
            _val(anthr, "reifestatus"),
            # Scores
            sc,
            risiko_de,
            # FMS
            _val(fms, "score"),
            _val(fms, "bewertung"),
            _val(fms, "asymmetrie"),
            # Y-Balance
            _val(y, "composite_rechts"),
            _val(y, "composite_links"),
            _val(y, "asymmetrie"),
            # Sprint
            _val(sprint, "beste_5m"),
            _val(sprint, "beste_10m"),
            _val(sprint, "beste_20m"),
            _val(sprint, "beste_30m"),
            _val(sprint, "beschl_index"),
            # Sprung
            _val(sprung, "cmj_beid"),
            _val(sprung, "cmj_rechts"),
            _val(sprung, "cmj_links"),
            _val(sprung, "cmj_asymmetrie"),
            _val(sprung, "squat_jump"),
            _val(sprung, "drop_jump_hoehe"),
            _val(sprung, "rsi"),
            _val(sprung, "standweit"),
            # Agilität
            _val(agil, "t505_r"),
            _val(agil, "t505_l"),
            _val(agil, "asym_505"),
            _val(agil, "t5_10_5"),
            _val(agil, "t_test"),
            _val(agil, "illinois"),
            # Ausdauer
            _val(aus, "test_typ"),
            _val(aus, "distanz_m"),
            _val(aus, "vo2max"),
            _val(aus, "hf_max"),
            # Testdaten
            _val(fms, "datum"),
            _val(sprint, "datum"),
            _val(sprung, "datum"),
            _val(agil, "datum"),
            _val(aus, "datum"),
        ]

        bg = _ALT_BG if row_idx % 2 == 0 else _NORM_BG
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            # Risiko-Spalte farbig hervorheben (Spalte 21)
            if col_idx == 21:  # Risiko
                if level == "hoch":
                    _data_style(cell, bg=_DANGER, fg="FFFFFF", bold=True)
                elif level == "mittel":
                    _data_style(cell, bg=_WARN, fg="0D1117", bold=True)
                else:
                    _data_style(cell, bg=_ACCENT, fg="FFFFFF", bold=True)
            elif col_idx == 20:  # Athletik Score
                _data_style(cell, bg=bg, fg="E6EDF3", bold=True, align="center")
            elif col_idx <= 13:  # Stammdaten linksbündig
                _data_style(cell, bg=bg, fg="C9D1D9", align="left")
            else:
                _data_style(cell, bg=bg, fg="C9D1D9", align="center")

    # Spaltenbreiten
    widths = {
        "A": 22, "B": 14, "C": 14, "D": 13, "E": 7,  "F": 11,
        "G": 14, "H": 20, "I": 16, "J": 12, "K": 18, "L": 14, "M": 22,
        "N": 11, "O": 12, "P": 8,  "Q": 12, "R": 14, "S": 14,
        "T": 14, "U": 12,
        "V": 11, "W": 16, "X": 14,
        "Y": 14, "Z": 14,
    }
    # Weitere Spalten (AA onward)
    extra = [12, 11, 11, 11, 13, 11, 11, 14, 13, 11, 11, 14, 14, 8, 8, 11, 10, 14,
             13, 14, 11, 13, 13, 13, 13]
    for i, w in enumerate(extra, start=27):
        widths[get_column_letter(i)] = w
    _set_col_widths(ws, widths)

    ws.row_dimensions[1].height = 36


# ─── Blatt 2: Verletzungshistorie ────────────────────────────────────────────

_INJ_HEADERS = [
    "Name", "Datum", "Verletzungsart", "Körperteil",
    "Schweregrad", "Ausfall (Tage)", "Notizen",
]


def _build_verletzung_sheet(ws):
    """Füllt Blatt 2 mit der Verletzungshistorie aller Spieler."""
    ws.title = "Verletzungshistorie"
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    for col_idx, header in enumerate(_INJ_HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        _header_style(cell, bg=_INJ_HDR)

    all_players = spieler_laden()
    row_idx = 2
    for p in all_players:
        verlet = verletzungen_laden(p["id"])
        for v in verlet:
            bg = _ALT_BG if row_idx % 2 == 0 else _INJ_BG
            row_data = [
                p.get("name", "—"),
                v.get("datum") or "—",
                v.get("art") or "—",
                v.get("koerperteil") or "—",
                v.get("schwere") or "—",
                v.get("ausfall_tage") or "—",
                v.get("notizen") or "—",
            ]
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if col_idx == 5:  # Schweregrad farbig
                    schwere = str(value)
                    if "Schwer" in schwere:
                        _data_style(cell, bg=_DANGER, fg="FFFFFF", bold=True)
                    elif "Mittel" in schwere:
                        _data_style(cell, bg=_WARN, fg="0D1117", bold=True)
                    else:
                        _data_style(cell, bg=_ACCENT, fg="FFFFFF")
                elif col_idx == 7:  # Notizen linksbündig
                    _data_style(cell, bg=bg, fg="C9D1D9", align="left")
                else:
                    _data_style(cell, bg=bg, fg="C9D1D9", align="left" if col_idx == 1 else "center")
            row_idx += 1

    if row_idx == 2:
        # Keine Verletzungen vorhanden
        cell = ws.cell(row=2, column=1, value="Keine Verletzungen dokumentiert.")
        _data_style(cell, bg=_INJ_BG, fg="8B949E", align="left")

    _set_col_widths(ws, {
        "A": 22, "B": 13, "C": 22, "D": 18,
        "E": 22, "F": 15, "G": 40,
    })
    ws.row_dimensions[1].height = 30


# ─── Öffentliche API ─────────────────────────────────────────────────────────

def kader_excel_bytes() -> bytes:
    """Gibt den kompletten Excel-Export als Bytes-Objekt zurück.
    Kann direkt an st.download_button(data=...) übergeben werden."""
    wb = openpyxl.Workbook()
    ws_kader = wb.active
    _build_kader_sheet(ws_kader)

    ws_inj = wb.create_sheet()
    _build_verletzung_sheet(ws_inj)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
