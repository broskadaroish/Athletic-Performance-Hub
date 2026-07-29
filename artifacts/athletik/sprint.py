"""
Sprint-Diagnostik-Modul — Linearbeschleunigung & Maximalgeschwindigkeit.

Unterstützte Distanzen: 5 m, 10 m, 20 m, 30 m (je 3 Versuche).
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── Referenzwerte (Durchschnitt männlich, Fußball, Leistungssport) ───────────
# Quellen: Little & Williams (2005), Haugen et al. (2014)

REFERENZ_ZEITEN = {
    "10m": {"Profi": 1.80, "Leistungssport": 1.92, "Breitensport": 2.05},
    "20m": {"Profi": 2.85, "Leistungssport": 3.05, "Breitensport": 3.25},
    "30m": {"Profi": 3.90, "Leistungssport": 4.15, "Breitensport": 4.45},
}

REFERENZ_WEIBLICH = {
    "10m": {"Profi": 1.95, "Leistungssport": 2.08, "Breitensport": 2.25},
    "20m": {"Profi": 3.10, "Leistungssport": 3.30, "Breitensport": 3.55},
    "30m": {"Profi": 4.25, "Leistungssport": 4.55, "Breitensport": 4.85},
}


def _bester(versuche: list[float]) -> Optional[float]:
    valide = [v for v in versuche if v and v > 0]
    return round(min(valide), 3) if valide else None


def _durchschnitt(versuche: list[float]) -> Optional[float]:
    valide = [v for v in versuche if v and v > 0]
    return round(sum(valide) / len(valide), 3) if valide else None


def beschleunigungsindex(t5: Optional[float], t10: Optional[float]) -> Optional[float]:
    """
    Schätzt die Beschleunigungsfähigkeit als Verhältnis 5m/10m-Split.
    Werte > 0.55 gelten als gute Anfangsbeschleunigung.
    """
    if t5 and t10 and t10 > 0:
        return round(t5 / t10, 3)
    return None


def bewertung_sprint(beste_zeit: float, distanz: str,
                     niveau: str = "Leistungssport",
                     geschlecht: str = "Männlich") -> str:
    """Gibt eine Textbewertung zur Sprintzeit zurück."""
    ref = REFERENZ_WEIBLICH if geschlecht == "Weiblich" else REFERENZ_ZEITEN
    if distanz not in ref:
        return "—"
    r = ref[distanz]
    if beste_zeit <= r["Profi"]:
        return "Sehr gut (Profi-Niveau)"
    if beste_zeit <= r["Leistungssport"]:
        return "Gut (Leistungssport)"
    if beste_zeit <= r["Breitensport"]:
        return "Mittel (Breitensport)"
    return "Verbesserungsbedarf"


def bewertung_farbe(bewertung: str) -> str:
    mapping = {
        "Sehr gut (Profi-Niveau)":    "#3fb950",
        "Gut (Leistungssport)":       "#58a6ff",
        "Mittel (Breitensport)":      "#d29922",
        "Verbesserungsbedarf":        "#f85149",
    }
    return mapping.get(bewertung, "#8b949e")


@dataclass
class SprintErgebnis:
    """Zusammenfassung einer Sprint-Diagnostik-Session."""
    beste_5m:  Optional[float] = None
    beste_10m: Optional[float] = None
    beste_20m: Optional[float] = None
    beste_30m: Optional[float] = None
    geschlecht: str = "Männlich"
    niveau: str = "Leistungssport"

    @property
    def beschl_index(self) -> Optional[float]:
        return beschleunigungsindex(self.beste_5m, self.beste_10m)

    @property
    def bewertung_10m(self) -> str:
        if self.beste_10m:
            return bewertung_sprint(self.beste_10m, "10m", self.niveau, self.geschlecht)
        return "—"

    @property
    def bewertung_30m(self) -> str:
        if self.beste_30m:
            return bewertung_sprint(self.beste_30m, "30m", self.niveau, self.geschlecht)
        return "—"

    @property
    def defizite(self) -> list[str]:
        """Gibt Trainingsbereiche zurück, die auf Optimierungsbedarf hinweisen."""
        d = []
        if self.beste_10m and self.beste_10m > REFERENZ_ZEITEN["10m"]["Leistungssport"] * (1.05 if self.geschlecht == "Männlich" else 1.05):
            d.append("Linearbeschleunigung (0–10 m)")
        if self.beste_30m and self.beste_30m > REFERENZ_ZEITEN["30m"]["Leistungssport"] * (1.05 if self.geschlecht == "Männlich" else 1.05):
            d.append("Maximalgeschwindigkeit (20–30 m)")
        if self.beschl_index and self.beschl_index > 0.60:
            d.append("Startexplosivität (Beschleunigungsindex)")
        return d
