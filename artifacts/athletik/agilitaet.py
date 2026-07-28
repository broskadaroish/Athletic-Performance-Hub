"""
Agilität & Richtungswechsel-Diagnostik.

Tests: 505-Test (rechts/links), 5-10-5 Shuttle, T-Test, Illinois Agility Run.
"""

from dataclasses import dataclass
from typing import Optional


# ─── Referenzwerte (Männlich, Fußball, Leistungssport) ───────────────────────
# Quellen: Sheppard & Young (2006), Pauole et al. (2000)

REFERENZ = {
    "505_rechts": {"Profi": 2.20, "Leistungssport": 2.35, "Breitensport": 2.55},
    "505_links":  {"Profi": 2.20, "Leistungssport": 2.35, "Breitensport": 2.55},
    "5_10_5":     {"Profi": 4.25, "Leistungssport": 4.50, "Breitensport": 4.80},
    "t_test":     {"Profi": 9.50, "Leistungssport": 10.20, "Breitensport": 11.00},
    "illinois":   {"Profi": 15.2, "Leistungssport": 16.5, "Breitensport": 17.5},
}

REFERENZ_W = {
    "505_rechts": {"Profi": 2.35, "Leistungssport": 2.55, "Breitensport": 2.75},
    "505_links":  {"Profi": 2.35, "Leistungssport": 2.55, "Breitensport": 2.75},
    "5_10_5":     {"Profi": 4.60, "Leistungssport": 4.90, "Breitensport": 5.25},
    "t_test":     {"Profi": 10.5, "Leistungssport": 11.5, "Breitensport": 12.5},
    "illinois":   {"Profi": 16.5, "Leistungssport": 18.0, "Breitensport": 19.5},
}


def bewertung(zeit: float, test_key: str,
              niveau: str = "Leistungssport",
              geschlecht: str = "Männlich") -> str:
    ref = REFERENZ_W if geschlecht == "Weiblich" else REFERENZ
    if test_key not in ref:
        return "—"
    r = ref[test_key]
    if zeit <= r["Profi"]:           return "Sehr gut (Profi-Niveau)"
    if zeit <= r["Leistungssport"]:  return "Gut (Leistungssport)"
    if zeit <= r["Breitensport"]:    return "Mittel (Breitensport)"
    return "Verbesserungsbedarf"


def bewertung_farbe(bew: str) -> str:
    return {
        "Sehr gut (Profi-Niveau)":   "#3fb950",
        "Gut (Leistungssport)":      "#58a6ff",
        "Mittel (Breitensport)":     "#d29922",
        "Verbesserungsbedarf":       "#f85149",
    }.get(bew, "#8b949e")


def asymmetrie_505(rechts: float, links: float) -> Optional[float]:
    """Seitenasymmetrie in % — > 10 % gilt als klinisch relevant."""
    if rechts > 0 and links > 0:
        return round(abs(rechts - links) / max(rechts, links) * 100, 1)
    return None


@dataclass
class AgilitaetErgebnis:
    """Zusammenfassung einer Agilität-Diagnostik-Session."""
    t505_r:   Optional[float] = None   # s
    t505_l:   Optional[float] = None   # s
    t5_10_5:  Optional[float] = None   # s
    t_test:   Optional[float] = None   # s
    illinois: Optional[float] = None   # s
    geschlecht: str = "Männlich"
    niveau:     str = "Leistungssport"

    @property
    def asym_505(self) -> Optional[float]:
        return asymmetrie_505(self.t505_r or 0, self.t505_l or 0)

    @property
    def bew_505(self) -> str:
        if self.t505_r:
            return bewertung(self.t505_r, "505_rechts", self.niveau, self.geschlecht)
        return "—"

    @property
    def bew_t_test(self) -> str:
        if self.t_test:
            return bewertung(self.t_test, "t_test", self.niveau, self.geschlecht)
        return "—"

    @property
    def bew_illinois(self) -> str:
        if self.illinois:
            return bewertung(self.illinois, "illinois", self.niveau, self.geschlecht)
        return "—"

    @property
    def defizite(self) -> list[str]:
        d = []
        ref = REFERENZ_W if self.geschlecht == "Weiblich" else REFERENZ
        grenze = 1.05
        if self.t505_r and self.t505_r > ref["505_rechts"]["Leistungssport"] * grenze:
            d.append("Richtungswechsel rechts (505-Test)")
        if self.t505_l and self.t505_l > ref["505_links"]["Leistungssport"] * grenze:
            d.append("Richtungswechsel links (505-Test)")
        if self.asym_505 and self.asym_505 > 10:
            d.append(f"Seitenasymmetrie Richtungswechsel ({self.asym_505:.1f} %)")
        if self.t_test and self.t_test > ref["t_test"]["Leistungssport"] * grenze:
            d.append("Mehrdirektionale Agilität (T-Test)")
        if self.illinois and self.illinois > ref["illinois"]["Leistungssport"] * grenze:
            d.append("Gesamtagilität / Richtungswechselgeschwindigkeit (Illinois)")
        if self.t5_10_5 and self.t5_10_5 > ref["5_10_5"]["Leistungssport"] * grenze:
            d.append("Shuttle-Beschleunigung / Abbremsfähigkeit (5-10-5)")
        return d
