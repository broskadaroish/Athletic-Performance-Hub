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


# ─── Fußball-Altersklasse → Yo-Yo-Normgruppe (zentrale Mapping-Funktion) ──────
# Ersetzt die lokale alter_zu_gruppe()-Funktion in app.py.
# Primär: Fußball-Altersklasse (aus saison.py); Fallback: chronologisches Alter.
#
# Beispiel: FK U11 (JG 2016, Saison 2026/27) → "U10/U11"
# Fußball-Altersklasse ≠ Testreferenz (UI soll beides getrennt anzeigen).

_FK_ZU_YOYO_GRUPPE: dict[str, str] = {
    "U4 (Minis)": "U8/U9",
    "U5": "U8/U9",  "U6": "U8/U9",  "U7": "U8/U9",
    "U8": "U8/U9",  "U9": "U8/U9",
    "U10": "U10/U11", "U11": "U10/U11",
    "U12": "U12/U13", "U13": "U12/U13",
    "U14": "U13/U14",
    "U15": "U15/U16", "U16": "U15/U16",
    "U17": "U17/U18", "U18": "U17/U18",
    "U19": "Senioren", "U20": "Senioren", "Senioren": "Senioren",
    # Nicht-U-Klassen (gebräuchliche Bezeichnungen im deutschen Amateurfußball)
    "A-Junioren": "U17/U18",   # entspricht U18/U19 — konservativ als U17/U18 eingestuft
    "B-Junioren": "U15/U16",   # entspricht U16/U17
    "C-Junioren": "U13/U14",   # entspricht U14/U15
    "D-Junioren": "U12/U13",   # entspricht U12/U13
    "E-Junioren": "U10/U11",   # entspricht U10/U11
    "F-Junioren": "U8/U9",     # entspricht U8/U9
    "Bambini":    "U8/U9",
}


def fussballklasse_zu_yoyo_gruppe(
    fussballklasse: str | None,
    alter: float | None = None,
) -> str:
    """Bestimmt die Yo-Yo-IR-Normgruppe aus FK (primär) oder Alter (Fallback).

    Fußball-Altersklasse hat Vorrang, da sie den Spielkontext bestimmt.
    Fallback (kein Geburtsdatum/FK): chronologisches Alter nach Bangsbo-Gruppen.

    Args:
        fussballklasse: aus saison.fussballklasse_aus_datum(), z.B. "U11"
        alter: chronologisches Alter am Testtag (Fallback wenn FK fehlt)

    Returns:
        Yo-Yo-Normgruppe, z.B. "U10/U11"

    Beispiele:
        FK "U11" → "U10/U11"   (nicht von Alter 9 abhängig!)
        FK "U14" → "U13/U14"
        FK=None, alter=9  → "U8/U9"   (Bangsbo-Fallback)
        FK=None, alter=10 → "U10/U11"
    """
    if fussballklasse:
        g = _FK_ZU_YOYO_GRUPPE.get(fussballklasse)
        if g:
            return g
        # Generische Auflösung für unbekannte/spätere U-Klassen (U21+)
        if fussballklasse.startswith("U"):
            try:
                nr = int(fussballklasse[1:].split(" ")[0])
                if nr <= 9:  return "U8/U9"
                if nr <= 11: return "U10/U11"
                if nr <= 13: return "U12/U13"
                if nr == 14: return "U13/U14"
                if nr <= 16: return "U15/U16"
                if nr <= 18: return "U17/U18"
                return "Senioren"
            except (ValueError, IndexError):
                pass
    # Fallback: chronologisches Alter — konsistent mit U-Logik (U = unter)
    # Alter 9 → spielt in U10 → Yo-Yo-Gruppe U10/U11 (nicht U8/U9!)
    if alter is not None:
        a = int(alter)
        if a <= 8: return "U8/U9"    # ≤ 8: spielt in U8/U9
        if a <= 10: return "U10/U11"  # 9–10: U10/U11
        if a <= 12: return "U12/U13"  # 11–12: U12/U13
        if a == 13: return "U13/U14"  # 13: U14
        if a <= 15: return "U15/U16"  # 14–15: U15/U16
        if a <= 17: return "U17/U18"  # 16–17: U17/U18
        return "Senioren"             # 18+: Senioren
    return "Senioren"


def _yoyo_gruppe_zu_normgruppe(yoyo_gruppe: str) -> str:
    """Mappt Yo-Yo-Normgruppe auf age_norms.py-Normgruppe (für VO₂max-Bewertung)."""
    return {
        "U8/U9":   "U8",
        "U10/U11": "U10",
        "U12/U13": "U12",
        "U13/U14": "U14",
        "U15/U16": "U16",
        "U17/U18": "U18",
        "Senioren": "Senioren",
    }.get(yoyo_gruppe, "Senioren")


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
        # IR2: Bangsbo-Formel gilt ausschließlich für IR1 — keine automatische
        # VO₂max-Schätzung für IR2 (andere Intensitätsstufen, anderer Koeffizient).
        return None

    @property
    def bewertung(self) -> str:
        if self.test_typ == "IR1" and self.distanz_m > 0:
            return bewertung_ir1(self.distanz_m, self.geschlecht, self.altersgruppe)
        return "—"

    @property
    def defizite(self) -> list[str]:
        """Defizite altersgerecht bestimmen — konsistent mit analytics.py.

        VO₂max-Schwelle basiert auf der gespeicherten Yo-Yo-Normgruppe (altersabhängig),
        nicht auf einer universellen Pauschalschwelle.
        """
        from age_norms import _VO2_NORMEN_M, _VO2_NORMEN_W
        d = []
        if self.distanz_m > 0 and self.bewertung == "Verbesserungsbedarf":
            d.append("Intermittierende Ausdauer (Yo-Yo IR)")
        if self.vo2max:
            normgruppe = _yoyo_gruppe_zu_normgruppe(self.altersgruppe)
            _ist_w = "w" in self.geschlecht.lower() or "f" in self.geschlecht.lower()
            tab = _VO2_NORMEN_W if _ist_w else _VO2_NORMEN_M
            schwelle = tab.get(normgruppe, tab["Senioren"])["Durchschnittlich"]
            if self.vo2max < schwelle:
                d.append(
                    f"Aerobe Kapazität (VO₂max-Schätzung: {self.vo2max} ml/kg/min, "
                    f"unter Norm für {normgruppe})"
                )
        return d
