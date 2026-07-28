"""
Sprung-Diagnostik-Modul — vertikale und horizontale Sprungkraft.

Tests: CMJ (Countermovement Jump), Squat Jump, Drop Jump (RSI), Standweitsprung,
       einbeinige Varianten (links/rechts) für Asymmetrie-Analyse.
"""

from dataclasses import dataclass
from typing import Optional
import math


# ─── Normwerte (männlich, Fußball, Leistungssport) ───────────────────────────
# Quellen: Markovic (2004), Meylan et al. (2009)

NORMWERTE_CMJ = {
    "Profi":          40.0,   # cm
    "Leistungssport": 33.0,
    "Breitensport":   26.0,
}
NORMWERTE_CMJ_W = {
    "Profi":          30.0,
    "Leistungssport": 25.0,
    "Breitensport":   20.0,
}
NORMWERTE_SWJ = {
    "Profi":          240.0,  # cm
    "Leistungssport": 210.0,
    "Breitensport":   180.0,
}


def flugzeit_zu_hoehe(flugzeit_s: float) -> float:
    """Berechnet Sprunghöhe aus Flugzeit (s). h = g * t² / 8"""
    return round(9.81 * flugzeit_s ** 2 / 8 * 100, 1)  # in cm


def rsi_berechnen(hoehe_cm: float, kontaktzeit_s: float) -> Optional[float]:
    """
    Reactive Strength Index = Sprunghöhe (m) / Kontaktzeit (s).
    Gut: RSI > 1.5, Elite: > 2.5
    """
    if kontaktzeit_s and kontaktzeit_s > 0 and hoehe_cm > 0:
        return round((hoehe_cm / 100) / kontaktzeit_s, 2)
    return None


def asymmetrie_prozent(rechts: float, links: float) -> Optional[float]:
    """Asymmetrie = |R-L| / max(R,L) * 100 — > 10 % = klinisch relevant."""
    if rechts > 0 and links > 0:
        return round(abs(rechts - links) / max(rechts, links) * 100, 1)
    return None


def bewertung_cmj(hoehe_cm: float, niveau: str = "Leistungssport",
                  geschlecht: str = "Männlich") -> str:
    ref = NORMWERTE_CMJ_W if geschlecht == "Weiblich" else NORMWERTE_CMJ
    if hoehe_cm >= ref["Profi"]:          return "Sehr gut (Profi-Niveau)"
    if hoehe_cm >= ref["Leistungssport"]: return "Gut (Leistungssport)"
    if hoehe_cm >= ref["Breitensport"]:   return "Mittel (Breitensport)"
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
class SprungErgebnis:
    """Zusammenfassung einer Sprung-Diagnostik-Session."""
    cmj_beid:       Optional[float] = None   # cm, beidbeinig
    cmj_rechts:     Optional[float] = None   # cm, einbeinig rechts
    cmj_links:      Optional[float] = None   # cm, einbeinig links
    squat_jump:     Optional[float] = None   # cm
    drop_jump_hoehe: Optional[float] = None  # cm
    drop_jump_kz:   Optional[float] = None   # s (Kontaktzeit)
    standweit:      Optional[float] = None   # cm
    geschlecht: str = "Männlich"
    niveau: str = "Leistungssport"

    @property
    def cmj_asymmetrie(self) -> Optional[float]:
        if self.cmj_rechts and self.cmj_links:
            return asymmetrie_prozent(self.cmj_rechts, self.cmj_links)
        return None

    @property
    def rsi(self) -> Optional[float]:
        if self.drop_jump_hoehe and self.drop_jump_kz:
            return rsi_berechnen(self.drop_jump_hoehe, self.drop_jump_kz)
        return None

    @property
    def bewertung_cmj(self) -> str:
        if self.cmj_beid:
            return bewertung_cmj(self.cmj_beid, self.niveau, self.geschlecht)
        return "—"

    @property
    def defizite(self) -> list[str]:
        """Gibt Diagnose-Bereiche zurück, die auf Trainingsbedarf hinweisen."""
        d = []
        ref = NORMWERTE_CMJ_W if self.geschlecht == "Weiblich" else NORMWERTE_CMJ
        if self.cmj_beid and self.cmj_beid < ref["Leistungssport"] * 0.95:
            d.append("Explosivkraft / Vertikalsprung (CMJ)")
        if self.cmj_asymmetrie and self.cmj_asymmetrie > 10:
            d.append(f"Sprungasymmetrie links/rechts ({self.cmj_asymmetrie:.1f} %)")
        if self.rsi and self.rsi < 1.5:
            d.append("Reaktivkraft / Drop Jump (RSI < 1.5)")
        if self.standweit and self.standweit < NORMWERTE_SWJ["Leistungssport"] * 0.95:
            d.append("Horizontalexplosivkraft (Standweitsprung)")
        return d
