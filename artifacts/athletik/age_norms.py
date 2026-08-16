"""
age_norms.py — Altersbasierte Normen für alle Diagnostiktests (U8–Ü50)

Quellen / Referenzen:
  Sprint   : Rumpf et al. (2016) J Str Cond Res; Meyers et al. (2017) J Sci Med Sport;
             DFB-Talentförderung Junioren-Diagnostik (2019)
  Sprung   : Bedoya et al. (2015) JSCR; Moran et al. (2017) JSS;
             Jimenez-Reyes et al. (2019) Int J Sports Physiol Perform
  Agilität : Little & Williams (2005) J Str Cond Res; Raya et al. (2013) JOSPT;
             Sheppard & Young (2006) JSMS
  Y-Balance: Plisky et al. (2006, 2009) JOSPT; Butler et al. (2012) IJSPT
  FMS      : Cook et al. (2006); Goss et al. (2016) IJSPT; Teyhen et al. (2012) Mil Med
  Kraft    : NSCA Youth Strength Standards; Faigenbaum & Myer (2010) Br J Sports Med;
             Haff & Triplett (2016) NSCA Essentials
  Ausdauer : Bangsbo (1996, 2008) Yo-Yo Test Handbook (bereits in ausdauer.py integriert)
"""

from __future__ import annotations

_GRUPPEN = ["U8", "U10", "U12", "U14", "U16", "U18", "U21", "Senioren", "Ü35", "Ü50"]


def alter_zu_normgruppe(alter: float | None) -> str:
    """Ordnet ein Alter (Jahre) der Normgruppe zu."""
    if not alter or alter <= 0:
        return "Senioren"
    a = int(alter)
    if a <= 8:  return "U8"
    if a <= 10: return "U10"
    if a <= 12: return "U12"
    if a <= 14: return "U14"
    if a <= 16: return "U16"
    if a <= 18: return "U18"
    if a <= 21: return "U21"
    if a <= 35: return "Senioren"
    if a <= 50: return "Ü35"
    return "Ü50"


# Altersbereich-Labels je Normgruppe (für UI-Captions)
_ALTER_RANGE: dict[str, str] = {
    "U8":       "7–8",
    "U10":      "9–10",
    "U12":      "11–12",
    "U14":      "13–14",
    "U16":      "15–16",
    "U18":      "17–18",
    "U21":      "19–21",
    "Senioren": "22–35",
    "Ü35":      "36–50",
    "Ü50":      "50+",
}


def normgruppe_label(alter: float | None) -> str:
    """Testreferenz-Label für UI — benennt klar Normgruppe und Altersbereich.

    Zeigt: 'Testreferenz: U10 (Alter 9–10)' statt 'Referenz: U10 (Fußball)'
    → trennt Testreferenz von der jahrgangsbasierten Fußballklasse.
    """
    g = alter_zu_normgruppe(alter)
    r = _ALTER_RANGE.get(g, "")
    if r:
        return f"Testreferenz: {g} (Alter {r})"
    return f"Testreferenz: {g}"


# ─── Sprint ─────────────────────────────────────────────────────────────────
# 10 m (s) — schneller = besser
# Quelle: Rumpf 2016, Meyers 2017, DFB-Junioren
_SPRINT_10M_M: dict[str, dict] = {
    "U8":       {"Profi": 2.30, "Leistungssport": 2.55, "Breitensport": 2.80},
    "U10":      {"Profi": 2.10, "Leistungssport": 2.30, "Breitensport": 2.55},
    "U12":      {"Profi": 1.97, "Leistungssport": 2.13, "Breitensport": 2.35},
    "U14":      {"Profi": 1.88, "Leistungssport": 2.03, "Breitensport": 2.22},
    "U16":      {"Profi": 1.81, "Leistungssport": 1.95, "Breitensport": 2.13},
    "U18":      {"Profi": 1.76, "Leistungssport": 1.89, "Breitensport": 2.06},
    "U21":      {"Profi": 1.73, "Leistungssport": 1.85, "Breitensport": 2.02},
    "Senioren": {"Profi": 1.70, "Leistungssport": 1.83, "Breitensport": 2.00},
    "Ü35":      {"Profi": 1.80, "Leistungssport": 1.97, "Breitensport": 2.18},
    "Ü50":      {"Profi": 2.00, "Leistungssport": 2.22, "Breitensport": 2.50},
}
_SPRINT_10M_W = {g: {k: round(v * 1.08, 2) for k, v in d.items()}
                 for g, d in _SPRINT_10M_M.items()}

_SPRINT_30M_M: dict[str, dict] = {
    "U8":       {"Profi": 6.50, "Leistungssport": 7.20, "Breitensport": 8.00},
    "U10":      {"Profi": 5.60, "Leistungssport": 6.10, "Breitensport": 6.80},
    "U12":      {"Profi": 5.10, "Leistungssport": 5.55, "Breitensport": 6.10},
    "U14":      {"Profi": 4.70, "Leistungssport": 5.05, "Breitensport": 5.60},
    "U16":      {"Profi": 4.40, "Leistungssport": 4.75, "Breitensport": 5.25},
    "U18":      {"Profi": 4.25, "Leistungssport": 4.55, "Breitensport": 5.05},
    "U21":      {"Profi": 4.15, "Leistungssport": 4.45, "Breitensport": 4.90},
    "Senioren": {"Profi": 4.10, "Leistungssport": 4.40, "Breitensport": 4.85},
    "Ü35":      {"Profi": 4.40, "Leistungssport": 4.80, "Breitensport": 5.35},
    "Ü50":      {"Profi": 5.00, "Leistungssport": 5.55, "Breitensport": 6.20},
}
_SPRINT_30M_W = {g: {k: round(v * 1.08, 2) for k, v in d.items()}
                 for g, d in _SPRINT_30M_M.items()}

# 20 m als Mittelwert aus 10 m und 30 m (grobe Annäherung)
_SPRINT_20M_M: dict[str, dict] = {
    g: {
        "Profi":          round((_SPRINT_10M_M[g]["Profi"] + _SPRINT_30M_M[g]["Profi"]) / 2, 2),
        "Leistungssport": round((_SPRINT_10M_M[g]["Leistungssport"] + _SPRINT_30M_M[g]["Leistungssport"]) / 2, 2),
        "Breitensport":   round((_SPRINT_10M_M[g]["Breitensport"] + _SPRINT_30M_M[g]["Breitensport"]) / 2, 2),
    }
    for g in _GRUPPEN
}
_SPRINT_20M_W = {g: {k: round(v * 1.08, 2) for k, v in d.items()}
                 for g, d in _SPRINT_20M_M.items()}

SPRINT_NORMEN: dict[str, dict] = {
    "Männlich": {"10m": _SPRINT_10M_M, "20m": _SPRINT_20M_M, "30m": _SPRINT_30M_M},
    "Weiblich": {"10m": _SPRINT_10M_W, "20m": _SPRINT_20M_W, "30m": _SPRINT_30M_W},
}

# ─── Sprung ─────────────────────────────────────────────────────────────────
# CMJ (cm) — höher = besser
_CMJ_M: dict[str, dict] = {
    "U8":       {"Profi": 22.0, "Leistungssport": 17.0, "Breitensport": 13.0},
    "U10":      {"Profi": 27.0, "Leistungssport": 22.0, "Breitensport": 17.0},
    "U12":      {"Profi": 32.0, "Leistungssport": 27.0, "Breitensport": 21.0},
    "U14":      {"Profi": 38.0, "Leistungssport": 32.0, "Breitensport": 25.0},
    "U16":      {"Profi": 43.0, "Leistungssport": 37.0, "Breitensport": 29.0},
    "U18":      {"Profi": 47.0, "Leistungssport": 40.0, "Breitensport": 32.0},
    "U21":      {"Profi": 49.0, "Leistungssport": 42.0, "Breitensport": 34.0},
    "Senioren": {"Profi": 50.0, "Leistungssport": 42.0, "Breitensport": 34.0},
    "Ü35":      {"Profi": 42.0, "Leistungssport": 35.0, "Breitensport": 27.0},
    "Ü50":      {"Profi": 33.0, "Leistungssport": 26.0, "Breitensport": 20.0},
}
_CMJ_W = {g: {k: round(v * 0.82, 1) for k, v in d.items()} for g, d in _CMJ_M.items()}

# SWJ / Standweitsprung (cm) — höher = besser
_SWJ_M: dict[str, dict] = {
    "U8":       {"Profi": 130.0, "Leistungssport": 110.0, "Breitensport": 90.0},
    "U10":      {"Profi": 155.0, "Leistungssport": 133.0, "Breitensport": 110.0},
    "U12":      {"Profi": 178.0, "Leistungssport": 155.0, "Breitensport": 130.0},
    "U14":      {"Profi": 202.0, "Leistungssport": 175.0, "Breitensport": 148.0},
    "U16":      {"Profi": 222.0, "Leistungssport": 193.0, "Breitensport": 163.0},
    "U18":      {"Profi": 237.0, "Leistungssport": 208.0, "Breitensport": 178.0},
    "U21":      {"Profi": 243.0, "Leistungssport": 213.0, "Breitensport": 183.0},
    "Senioren": {"Profi": 240.0, "Leistungssport": 210.0, "Breitensport": 180.0},
    "Ü35":      {"Profi": 210.0, "Leistungssport": 182.0, "Breitensport": 155.0},
    "Ü50":      {"Profi": 175.0, "Leistungssport": 148.0, "Breitensport": 122.0},
}
_SWJ_W = {g: {k: round(v * 0.85, 1) for k, v in d.items()} for g, d in _SWJ_M.items()}

SPRUNG_NORMEN: dict[str, dict] = {
    "Männlich": {"cmj": _CMJ_M, "swj": _SWJ_M},
    "Weiblich": {"cmj": _CMJ_W, "swj": _SWJ_W},
}

# ─── Agilität ───────────────────────────────────────────────────────────────
# T-Test (s) — schneller = besser
_T_TEST_M: dict[str, dict] = {
    "U8":       {"Profi": 14.0, "Leistungssport": 15.5, "Breitensport": 17.5},
    "U10":      {"Profi": 12.5, "Leistungssport": 14.0, "Breitensport": 15.5},
    "U12":      {"Profi": 11.5, "Leistungssport": 13.0, "Breitensport": 14.5},
    "U14":      {"Profi": 10.8, "Leistungssport": 12.0, "Breitensport": 13.5},
    "U16":      {"Profi": 10.2, "Leistungssport": 11.3, "Breitensport": 12.5},
    "U18":      {"Profi":  9.8, "Leistungssport": 10.8, "Breitensport": 12.0},
    "U21":      {"Profi":  9.6, "Leistungssport": 10.5, "Breitensport": 11.7},
    "Senioren": {"Profi":  9.5, "Leistungssport": 10.5, "Breitensport": 11.5},
    "Ü35":      {"Profi": 10.0, "Leistungssport": 11.2, "Breitensport": 12.5},
    "Ü50":      {"Profi": 11.5, "Leistungssport": 13.0, "Breitensport": 14.5},
}
_T_TEST_W = {g: {k: round(v * 1.07, 2) for k, v in d.items()} for g, d in _T_TEST_M.items()}

# 505-Test (s)
_T505_M: dict[str, dict] = {
    "U8":       {"Profi": 3.40, "Leistungssport": 3.80, "Breitensport": 4.30},
    "U10":      {"Profi": 3.00, "Leistungssport": 3.35, "Breitensport": 3.75},
    "U12":      {"Profi": 2.65, "Leistungssport": 2.95, "Breitensport": 3.30},
    "U14":      {"Profi": 2.40, "Leistungssport": 2.68, "Breitensport": 3.00},
    "U16":      {"Profi": 2.25, "Leistungssport": 2.50, "Breitensport": 2.80},
    "U18":      {"Profi": 2.15, "Leistungssport": 2.40, "Breitensport": 2.70},
    "U21":      {"Profi": 2.10, "Leistungssport": 2.35, "Breitensport": 2.65},
    "Senioren": {"Profi": 2.05, "Leistungssport": 2.30, "Breitensport": 2.60},
    "Ü35":      {"Profi": 2.25, "Leistungssport": 2.55, "Breitensport": 2.90},
    "Ü50":      {"Profi": 2.60, "Leistungssport": 2.95, "Breitensport": 3.40},
}
_T505_W = {g: {k: round(v * 1.07, 2) for k, v in d.items()} for g, d in _T505_M.items()}

# Illinois (s)
_ILLINOIS_M: dict[str, dict] = {
    "U8":       {"Profi": 20.0, "Leistungssport": 22.5, "Breitensport": 25.5},
    "U10":      {"Profi": 18.0, "Leistungssport": 20.0, "Breitensport": 22.5},
    "U12":      {"Profi": 16.5, "Leistungssport": 18.5, "Breitensport": 20.5},
    "U14":      {"Profi": 15.5, "Leistungssport": 17.5, "Breitensport": 19.5},
    "U16":      {"Profi": 15.0, "Leistungssport": 16.7, "Breitensport": 18.5},
    "U18":      {"Profi": 14.8, "Leistungssport": 16.2, "Breitensport": 18.0},
    "U21":      {"Profi": 14.8, "Leistungssport": 16.2, "Breitensport": 18.0},
    "Senioren": {"Profi": 15.2, "Leistungssport": 16.5, "Breitensport": 17.5},
    "Ü35":      {"Profi": 16.0, "Leistungssport": 17.5, "Breitensport": 19.5},
    "Ü50":      {"Profi": 18.0, "Leistungssport": 20.0, "Breitensport": 22.5},
}
_ILLINOIS_W = {g: {k: round(v * 1.07, 2) for k, v in d.items()} for g, d in _ILLINOIS_M.items()}

# 5-10-5 Shuttle (s)
_5105_M: dict[str, dict] = {
    "U8":       {"Profi": 5.80, "Leistungssport": 6.40, "Breitensport": 7.20},
    "U10":      {"Profi": 5.10, "Leistungssport": 5.65, "Breitensport": 6.30},
    "U12":      {"Profi": 4.65, "Leistungssport": 5.10, "Breitensport": 5.70},
    "U14":      {"Profi": 4.35, "Leistungssport": 4.75, "Breitensport": 5.30},
    "U16":      {"Profi": 4.15, "Leistungssport": 4.55, "Breitensport": 5.05},
    "U18":      {"Profi": 4.05, "Leistungssport": 4.43, "Breitensport": 4.90},
    "U21":      {"Profi": 4.00, "Leistungssport": 4.38, "Breitensport": 4.83},
    "Senioren": {"Profi": 4.00, "Leistungssport": 4.38, "Breitensport": 4.80},
    "Ü35":      {"Profi": 4.30, "Leistungssport": 4.73, "Breitensport": 5.25},
    "Ü50":      {"Profi": 4.90, "Leistungssport": 5.40, "Breitensport": 6.00},
}
_5105_W = {g: {k: round(v * 1.07, 2) for k, v in d.items()} for g, d in _5105_M.items()}

AGIL_NORMEN: dict[str, dict] = {
    "Männlich": {
        "t_test":     _T_TEST_M,
        "505_rechts": _T505_M, "505_links": _T505_M,
        "illinois":   _ILLINOIS_M,
        "5_10_5":     _5105_M,
    },
    "Weiblich": {
        "t_test":     _T_TEST_W,
        "505_rechts": _T505_W, "505_links": _T505_W,
        "illinois":   _ILLINOIS_W,
        "5_10_5":     _5105_W,
    },
}

# ─── Y-Balance composite (%) ─────────────────────────────────────────────────
# Quelle: Plisky 2009, Butler 2012, youth sports norms
_YB_M: dict[str, dict] = {
    "U8":       {"Gut": 80.0, "Mittel": 68.0},
    "U10":      {"Gut": 83.0, "Mittel": 71.0},
    "U12":      {"Gut": 86.0, "Mittel": 74.0},
    "U14":      {"Gut": 88.0, "Mittel": 77.0},
    "U16":      {"Gut": 90.0, "Mittel": 80.0},
    "U18":      {"Gut": 92.0, "Mittel": 82.0},
    "U21":      {"Gut": 93.0, "Mittel": 83.0},
    "Senioren": {"Gut": 94.0, "Mittel": 85.0},
    "Ü35":      {"Gut": 90.0, "Mittel": 80.0},
    "Ü50":      {"Gut": 84.0, "Mittel": 73.0},
}
_YB_W = {g: {"Gut": d["Gut"] - 2.0, "Mittel": d["Mittel"] - 2.0}
          for g, d in _YB_M.items()}

YB_NORMEN: dict[str, dict] = {"Männlich": _YB_M, "Weiblich": _YB_W}


def yb_schwellenwert(alter: float | None, geschlecht: str = "Männlich") -> float:
    """Liefert den altersbasierten Y-Balance Composite-Grenzwert (% Beinlänge)."""
    g = alter_zu_normgruppe(alter)
    tab = YB_NORMEN.get(geschlecht, YB_NORMEN["Männlich"])
    return tab.get(g, tab["Senioren"])["Gut"]


# ─── FMS-Schwellenwerte nach Alter ──────────────────────────────────────────
# Quelle: Cook 2006, Goss 2016, Teyhen 2012
# Ausgezeichnet ≥ X, Gut ≥ Y, Beobachten ≥ Z, sonst Aktionsbedarf
FMS_NORMEN: dict[str, dict] = {
    "U8":       {"Ausgezeichnet": 16, "Gut": 13, "Beobachten": 10},
    "U10":      {"Ausgezeichnet": 17, "Gut": 14, "Beobachten": 11},
    "U12":      {"Ausgezeichnet": 17, "Gut": 14, "Beobachten": 11},
    "U14":      {"Ausgezeichnet": 17, "Gut": 14, "Beobachten": 12},
    "U16":      {"Ausgezeichnet": 18, "Gut": 15, "Beobachten": 12},
    "U18":      {"Ausgezeichnet": 18, "Gut": 15, "Beobachten": 13},
    "U21":      {"Ausgezeichnet": 18, "Gut": 15, "Beobachten": 13},
    "Senioren": {"Ausgezeichnet": 18, "Gut": 15, "Beobachten": 13},
    "Ü35":      {"Ausgezeichnet": 17, "Gut": 14, "Beobachten": 12},
    "Ü50":      {"Ausgezeichnet": 16, "Gut": 13, "Beobachten": 11},
}


def fms_bewertung_alter(score: int, alter: float | None) -> str:
    """Altersbasierte FMS-Bewertung."""
    g = alter_zu_normgruppe(alter)
    n = FMS_NORMEN.get(g, FMS_NORMEN["Senioren"])
    if score >= n["Ausgezeichnet"]: return "Ausgezeichnet"
    if score >= n["Gut"]:           return "Gut"
    if score >= n["Beobachten"]:    return "Beobachten"
    return "Aktionsbedarf"


# ─── Relative Kraft Bankdrücken (×KGW) nach Alter ────────────────────────────
# Quelle: NSCA Youth Strength Standards, Faigenbaum & Myer 2010
_KRAFT_M: dict[str, dict] = {
    "U8":       {"Sehr gut": 0.50, "Gut": 0.35, "Durchschnittlich": 0.20},
    "U10":      {"Sehr gut": 0.62, "Gut": 0.46, "Durchschnittlich": 0.32},
    "U12":      {"Sehr gut": 0.78, "Gut": 0.60, "Durchschnittlich": 0.42},
    "U14":      {"Sehr gut": 0.95, "Gut": 0.75, "Durchschnittlich": 0.57},
    "U16":      {"Sehr gut": 1.12, "Gut": 0.90, "Durchschnittlich": 0.72},
    "U18":      {"Sehr gut": 1.28, "Gut": 1.02, "Durchschnittlich": 0.82},
    "U21":      {"Sehr gut": 1.42, "Gut": 1.14, "Durchschnittlich": 0.92},
    "Senioren": {"Sehr gut": 1.50, "Gut": 1.20, "Durchschnittlich": 0.95},
    "Ü35":      {"Sehr gut": 1.35, "Gut": 1.05, "Durchschnittlich": 0.82},
    "Ü50":      {"Sehr gut": 1.10, "Gut": 0.85, "Durchschnittlich": 0.65},
}
_KRAFT_W = {g: {k: round(v * 0.70, 2) for k, v in d.items()} for g, d in _KRAFT_M.items()}

KRAFT_NORMEN: dict[str, dict] = {"Männlich": _KRAFT_M, "Weiblich": _KRAFT_W}


# ─── Spiroergometrie / VO₂ ──────────────────────────────────────────────────
# VO₂peak-Normen für Fußball (ml·kg⁻¹·min⁻¹)
# Quellen: Helgerud et al. (2001) Med Sci Sports Exerc; Stølen et al. (2005) Sports Med;
#          Bangsbo (1993) Science Football; DFB-Leistungsdiagnostik (2019)
_VO2_NORMEN_M: dict[str, dict] = {
    "U8":       {"Sehr gut": 40, "Gut": 35, "Durchschnittlich": 30},
    "U10":      {"Sehr gut": 44, "Gut": 38, "Durchschnittlich": 32},
    "U12":      {"Sehr gut": 48, "Gut": 42, "Durchschnittlich": 36},
    "U14":      {"Sehr gut": 52, "Gut": 46, "Durchschnittlich": 40},
    "U16":      {"Sehr gut": 56, "Gut": 49, "Durchschnittlich": 43},
    "U18":      {"Sehr gut": 59, "Gut": 52, "Durchschnittlich": 46},
    "U21":      {"Sehr gut": 62, "Gut": 55, "Durchschnittlich": 48},
    "Senioren": {"Sehr gut": 60, "Gut": 53, "Durchschnittlich": 46},
    "Ü35":      {"Sehr gut": 55, "Gut": 48, "Durchschnittlich": 42},
    "Ü50":      {"Sehr gut": 48, "Gut": 42, "Durchschnittlich": 36},
}
_VO2_NORMEN_W: dict[str, dict] = {
    "U8":       {"Sehr gut": 34, "Gut": 29, "Durchschnittlich": 24},
    "U10":      {"Sehr gut": 38, "Gut": 32, "Durchschnittlich": 26},
    "U12":      {"Sehr gut": 42, "Gut": 36, "Durchschnittlich": 30},
    "U14":      {"Sehr gut": 46, "Gut": 40, "Durchschnittlich": 34},
    "U16":      {"Sehr gut": 50, "Gut": 43, "Durchschnittlich": 37},
    "U18":      {"Sehr gut": 53, "Gut": 46, "Durchschnittlich": 40},
    "U21":      {"Sehr gut": 55, "Gut": 48, "Durchschnittlich": 41},
    "Senioren": {"Sehr gut": 53, "Gut": 46, "Durchschnittlich": 40},
    "Ü35":      {"Sehr gut": 48, "Gut": 42, "Durchschnittlich": 36},
    "Ü50":      {"Sehr gut": 42, "Gut": 36, "Durchschnittlich": 30},
}


def vo2_bewertung_alter(vo2: float, alter: float | None,
                        geschlecht: str = "Männlich") -> tuple[str, str]:
    """Altersbasierte VO₂peak-Beurteilung für Fußball (ml·kg⁻¹·min⁻¹)."""
    g   = alter_zu_normgruppe(alter)
    tab = _VO2_NORMEN_W if "w" in geschlecht.lower() or "f" in geschlecht.lower() else _VO2_NORMEN_M
    n   = tab.get(g, tab["Senioren"])
    if vo2 >= n["Sehr gut"]:
        return "Sehr gut", f"Hervorragende aerobe Kapazität für {g} — VO₂peak {vo2:.1f} ml·kg⁻¹·min⁻¹"
    if vo2 >= n["Gut"]:
        return "Gut", f"Gute aerobe Kapazität für {g} — VO₂peak {vo2:.1f} ml·kg⁻¹·min⁻¹"
    if vo2 >= n["Durchschnittlich"]:
        return "Durchschnittlich", f"Durchschnittliche Ausdauer für {g} — VO₂peak {vo2:.1f} ml·kg⁻¹·min⁻¹"
    if vo2 >= n["Durchschnittlich"] * 0.85:
        return "Verbesserungsbedarf", f"Unter Norm für {g} — VO₂peak {vo2:.1f} ml·kg⁻¹·min⁻¹, Ausdauer aufbauen"
    return "Kritisch", f"Deutlich unter Norm für {g} — VO₂peak {vo2:.1f} ml·kg⁻¹·min⁻¹, sofort handeln"


def kraft_bewertung_alter(rel_kraft: float, alter: float | None,
                          geschlecht: str = "Männlich") -> tuple[str, str]:
    """Altersbasierte Beurteilung der relativen Bankdrück-Kraft."""
    g   = alter_zu_normgruppe(alter)
    tab = KRAFT_NORMEN.get(geschlecht, KRAFT_NORMEN["Männlich"])
    n   = tab.get(g, tab["Senioren"])
    if rel_kraft >= n["Sehr gut"]:
        return "Sehr gut", f"Elite-Niveau für {g} — Krafterhalt und Schnellkraft"
    if rel_kraft >= n["Gut"]:
        return "Gut", f"Über Norm für {g} — planmäßige Entwicklung"
    if rel_kraft >= n["Durchschnittlich"]:
        return "Durchschnittlich", f"Im Normbereich für {g} — Steigerung empfohlen"
    if rel_kraft >= n["Durchschnittlich"] * 0.80:
        return "Unterdurchschnittlich", f"Unter Norm für {g} — Kraftaufbau einleiten"
    return "Kritisch", f"Deutlich unter Norm für {g} — sofortiger Kraftaufbau nötig"
