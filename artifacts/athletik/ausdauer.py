"""
Yo-Yo Ausdauer-Diagnostik — Intermittierende Ausdauer im Fußball.

Tests: Yo-Yo Intermittent Recovery Test Level 1 (IR1) und Level 2 (IR2).
"""

from dataclasses import dataclass
from typing import Optional


# ─── Distanz → Stufen-Lookup (Yo-Yo IR1) ─────────────────────────────────────
# Quelle: Bangsbo et al. (2008). Jede Stufe = 2 × 20 m = 40 m

YO_YO_IR1_STUFEN = [
    (0,    "5", 0),
    (160,  "7", 160),
    (280,  "9", 280),
    (440,  "11", 440),
    (640,  "13", 640),
    (920,  "15", 920),
    (1240, "16", 1240),
    (1600, "17", 1600),
    (2000, "18", 2000),
    (2400, "19", 2400),
    (2800, "20", 2800),
    (3200, "21", 3200),
]

YO_YO_IR2_STUFEN = [
    (0,   "11", 0),
    (80,  "12", 80),
    (160, "13", 160),
    (320, "14", 320),
    (560, "15", 560),
    (840, "16", 840),
    (1160, "17", 1160),
    (1520, "18", 1520),
    (1920, "19", 1920),
]


# ─── VO₂max-Schätzung ─────────────────────────────────────────────────────────
# Bangsbo et al. (2008): VO₂max ≈ distanz(m) × 0.0084 + 36.4  (IR1)

def vo2max_schaetzen_ir1(distanz_m: float) -> float:
    return round(distanz_m * 0.0084 + 36.4, 1)

def vo2max_schaetzen_ir2(distanz_m: float) -> float:
    return round(distanz_m * 0.0136 + 45.3, 1)


# ─── Trainingsbereiche (VO₂max-basiert) ──────────────────────────────────────

def trainingsbereiche(vo2max: float) -> list[dict]:
    return [
        {"Bereich": "Regeneration",         "% VO₂max": "< 60 %",  "VO₂max (ml/kg/min)": f"< {int(vo2max*0.60):.0f}"},
        {"Bereich": "Grundlagenausdauer 1",  "% VO₂max": "60–70 %", "VO₂max (ml/kg/min)": f"{int(vo2max*0.60):.0f}–{int(vo2max*0.70):.0f}"},
        {"Bereich": "Grundlagenausdauer 2",  "% VO₂max": "70–80 %", "VO₂max (ml/kg/min)": f"{int(vo2max*0.70):.0f}–{int(vo2max*0.80):.0f}"},
        {"Bereich": "Entwicklungsbereich",   "% VO₂max": "80–90 %", "VO₂max (ml/kg/min)": f"{int(vo2max*0.80):.0f}–{int(vo2max*0.90):.0f}"},
        {"Bereich": "VO₂max-Training",       "% VO₂max": "90–100 %","VO₂max (ml/kg/min)": f"{int(vo2max*0.90):.0f}–{int(vo2max):.0f}"},
    ]


# ─── Normwerte Yo-Yo IR1 (Distanz in Meter) ───────────────────────────────────
# nach Geschlecht und Altersklasse (Bangebo & Mohr, 2012)

NORMWERTE_IR1 = {
    "Männlich": {
        "U8/U9":   {"Gut": 200,  "Mittel": 120,  "Verbesserungsbedarf": 0},
        "U10/U11": {"Gut": 480,  "Mittel": 280,  "Verbesserungsbedarf": 0},
        "U12/U13": {"Gut": 800,  "Mittel": 480,  "Verbesserungsbedarf": 0},
        "U13/U14": {"Gut": 1200, "Mittel": 800,  "Verbesserungsbedarf": 0},
        "U15/U16": {"Gut": 1600, "Mittel": 1100, "Verbesserungsbedarf": 0},
        "U17/U18": {"Gut": 2000, "Mittel": 1400, "Verbesserungsbedarf": 0},
        "Senioren": {"Gut": 2400, "Mittel": 1600, "Verbesserungsbedarf": 0},
    },
    "Weiblich": {
        "U8/U9":   {"Gut": 160,  "Mittel": 100,  "Verbesserungsbedarf": 0},
        "U10/U11": {"Gut": 360,  "Mittel": 200,  "Verbesserungsbedarf": 0},
        "U12/U13": {"Gut": 600,  "Mittel": 360,  "Verbesserungsbedarf": 0},
        "U13/U14": {"Gut": 800,  "Mittel": 500,  "Verbesserungsbedarf": 0},
        "U15/U16": {"Gut": 1000, "Mittel": 700,  "Verbesserungsbedarf": 0},
        "U17/U18": {"Gut": 1200, "Mittel": 800,  "Verbesserungsbedarf": 0},
        "Senioren": {"Gut": 1400, "Mittel": 900,  "Verbesserungsbedarf": 0},
    },
}


def bewertung_ir1(distanz_m: float, geschlecht: str = "Männlich",
                  altersgruppe: str = "Senioren") -> str:
    ref = NORMWERTE_IR1.get(geschlecht, NORMWERTE_IR1["Männlich"])
    r   = ref.get(altersgruppe, ref["Senioren"])
    if distanz_m >= r["Gut"]:    return "Gut"
    if distanz_m >= r["Mittel"]: return "Mittel"
    return "Verbesserungsbedarf"


def bewertung_farbe(bew: str) -> str:
    return {"Gut": "#3fb950", "Mittel": "#d29922",
            "Verbesserungsbedarf": "#f85149"}.get(bew, "#8b949e")


@dataclass
class AusdauerErgebnis:
    """Zusammenfassung eines Yo-Yo Tests."""
    test_typ:  str = "IR1"          # "IR1" oder "IR2"
    distanz_m: float = 0.0
    hf_max:    Optional[float] = None   # bpm
    rpe:       Optional[int]   = None   # 6–20 Borg-Skala
    geschlecht: str = "Männlich"
    altersgruppe: str = "Senioren"

    @property
    def vo2max(self) -> Optional[float]:
        if self.distanz_m <= 0:
            return None
        if self.test_typ == "IR1":
            return vo2max_schaetzen_ir1(self.distanz_m)
        return vo2max_schaetzen_ir2(self.distanz_m)

    @property
    def bewertung(self) -> str:
        if self.test_typ == "IR1" and self.distanz_m > 0:
            return bewertung_ir1(self.distanz_m, self.geschlecht, self.altersgruppe)
        return "—"

    @property
    def defizite(self) -> list[str]:
        d = []
        if self.distanz_m > 0 and self.bewertung == "Verbesserungsbedarf":
            d.append("Intermittierende Ausdauer (Yo-Yo IR)")
        if self.vo2max and self.vo2max < 50:
            d.append(f"Aerobe Kapazität (VO₂max-Schätzung: {self.vo2max} ml/kg/min)")
        return d
