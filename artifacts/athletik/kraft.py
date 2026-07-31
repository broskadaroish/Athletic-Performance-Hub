"""
kraft.py — Kraftdiagnostik-Modul

Bankdrücken (1RM direkt und geschätzt nach Epley)
Rumpfkraftausdauer (ventral / lateral R+L / dorsal)

WICHTIG: Kein Test ersetzt eine ärztliche Untersuchung oder Sportfreigabe.
Direkte 1RM-Tests erfordern ausreichende Sicherung und Aufwärmung.
Alle Werte dienen ausschließlich der internen Trainingsplanung.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── Epley-Formel ─────────────────────────────────────────────────────────────

def epley_1rm(gewicht_kg: Optional[float], wiederholungen: Optional[int]) -> Optional[float]:
    """
    Schätzt das 1-Wiederholungsmaximum nach der Epley-Formel.
    Epley (1985): 1RM = Gewicht × (1 + WH / 30)

    Gültig für 1–10 Wiederholungen; darüber nimmt die Genauigkeit stark ab.
    Bei 1 Wiederholung ist das Testgewicht selbst das 1RM.
    """
    if not gewicht_kg or gewicht_kg <= 0:
        return None
    if not wiederholungen or wiederholungen <= 0:
        return None
    if wiederholungen == 1:
        return round(float(gewicht_kg), 1)
    if wiederholungen > 10:
        # Warnung sollte in UI erfolgen; Formel wird trotzdem berechnet
        pass
    return round(float(gewicht_kg) * (1 + wiederholungen / 30), 1)


def relative_kraft_berechnen(rm_kg: Optional[float], koerpergewicht_kg: float) -> Optional[float]:
    """Relative Kraft = absolutes 1RM / Körpergewicht (dimensionslos)."""
    if rm_kg is None or rm_kg <= 0 or koerpergewicht_kg <= 0:
        return None
    return round(rm_kg / koerpergewicht_kg, 2)


# ─── Rumpfkraftausdauer ───────────────────────────────────────────────────────

def lateral_asymmetrie(sek_rechts: Optional[float], sek_links: Optional[float]) -> Optional[float]:
    """
    Seitendifferenz der Lateralflexion-Ausdauer in Prozent.
    Formel: |R - L| / max(R, L) × 100
    Grenzwert: > 10 % gilt als auffällig (seitenspezifisches Training empfohlen).
    """
    if not sek_rechts or not sek_links or sek_rechts <= 0 or sek_links <= 0:
        return None
    mx = max(sek_rechts, sek_links)
    return round(abs(sek_rechts - sek_links) / mx * 100, 1)


def rumpf_ratio(a_sek: Optional[float], b_sek: Optional[float]) -> Optional[float]:
    """Verhältnis zweier Rumpfkraft-Zeiten (a / b)."""
    if not a_sek or not b_sek or b_sek <= 0:
        return None
    return round(a_sek / b_sek, 2)


# ─── Ergebnis-Dataclass ───────────────────────────────────────────────────────

@dataclass
class KraftErgebnis:
    """Zusammenfassung aller Kraft-Testergebnisse für einen Spieler/Test-Tag."""

    # ── Bankdrücken ──────────────────────────────────────────────────────────
    koerpergewicht:        Optional[float] = None
    direktes_1rm:          Optional[float] = None   # Direkt gemessenes 1RM (kg)
    epley_gewicht:         Optional[float] = None   # Submaximalgewicht für Schätzung
    epley_wiederholungen:  Optional[int]   = None   # Wiederholungen mit Submaximalgewicht
    sicherheit_bestaetigt: bool            = False  # Sicherheitsprotokoll bestätigt?

    # ── Rumpfkraftausdauer ───────────────────────────────────────────────────
    ventral_sekunden:        Optional[float] = None  # Plank ventral V1
    ventral_versuch2:        Optional[float] = None  # Plank ventral V2
    lateral_rechts_sekunden: Optional[float] = None  # Seitstütz rechts
    lateral_links_sekunden:  Optional[float] = None  # Seitstütz links
    dorsal_sekunden:         Optional[float] = None  # Rückenlage-Ausdauer / Biering-Sørensen

    # ── Berechnete Felder (init=False) ───────────────────────────────────────
    geschaetztes_1rm:          Optional[float] = field(default=None, init=False)
    relative_kraft_direkt:     Optional[float] = field(default=None, init=False)
    relative_kraft_geschaetzt: Optional[float] = field(default=None, init=False)
    ventral_bestwert:          Optional[float] = field(default=None, init=False)
    lateral_asymmetrie_pct:    Optional[float] = field(default=None, init=False)
    ratio_ventral_dorsal:      Optional[float] = field(default=None, init=False)
    ratio_lateral_r_dorsal:    Optional[float] = field(default=None, init=False)
    ratio_lateral_l_dorsal:    Optional[float] = field(default=None, init=False)

    def __post_init__(self):
        # Epley-Schätzung (nur bei Submaximaltest)
        self.geschaetztes_1rm = epley_1rm(self.epley_gewicht, self.epley_wiederholungen)

        # Relative Kraft
        kgew = self.koerpergewicht or 0
        self.relative_kraft_direkt     = relative_kraft_berechnen(self.direktes_1rm, kgew)
        self.relative_kraft_geschaetzt = relative_kraft_berechnen(self.geschaetztes_1rm, kgew)

        # Ventral-Bestwert (2 Versuche, höhere Zeit gewinnt)
        ventr_vals = [v for v in [self.ventral_sekunden, self.ventral_versuch2] if v and v > 0]
        self.ventral_bestwert = max(ventr_vals) if ventr_vals else None

        # Rumpf-Asymmetrie und Ratios
        self.lateral_asymmetrie_pct = lateral_asymmetrie(
            self.lateral_rechts_sekunden, self.lateral_links_sekunden
        )
        self.ratio_ventral_dorsal   = rumpf_ratio(self.ventral_bestwert, self.dorsal_sekunden)
        self.ratio_lateral_r_dorsal = rumpf_ratio(self.lateral_rechts_sekunden, self.dorsal_sekunden)
        self.ratio_lateral_l_dorsal = rumpf_ratio(self.lateral_links_sekunden, self.dorsal_sekunden)

    # ── Hilfseigenschaften ───────────────────────────────────────────────────

    @property
    def hat_bankdruecken_daten(self) -> bool:
        return bool(self.direktes_1rm or self.geschaetztes_1rm)

    @property
    def hat_rumpfkraft_daten(self) -> bool:
        return any([
            self.ventral_bestwert,
            self.lateral_rechts_sekunden,
            self.lateral_links_sekunden,
            self.dorsal_sekunden,
        ])

    @property
    def hat_daten(self) -> bool:
        return self.hat_bankdruecken_daten or self.hat_rumpfkraft_daten

    @property
    def bestes_1rm(self) -> Optional[float]:
        """Gibt das beste verfügbare 1RM zurück (direkt bevorzugt)."""
        return self.direktes_1rm or self.geschaetztes_1rm

    @property
    def hinweise(self) -> list[str]:
        """Trainer-Hinweise auf Basis der Rumpfkraft-Analyse (keine Diagnosen)."""
        h = []
        if self.lateral_asymmetrie_pct and self.lateral_asymmetrie_pct > 10:
            seite = "R > L" if (self.lateral_rechts_sekunden or 0) > (self.lateral_links_sekunden or 0) else "L > R"
            h.append(
                f"Seitendifferenz lateral {self.lateral_asymmetrie_pct:.1f} % ({seite}) — "
                "seitenspezifisches Training empfohlen"
            )
        if self.ratio_ventral_dorsal:
            if self.ratio_ventral_dorsal < 0.75:
                h.append(
                    f"Ventral/Dorsal-Ratio {self.ratio_ventral_dorsal:.2f} — "
                    "dorsale Kette relativ stärker; ventrale Ausdauer gezielt fördern"
                )
            elif self.ratio_ventral_dorsal > 1.50:
                h.append(
                    f"Ventral/Dorsal-Ratio {self.ratio_ventral_dorsal:.2f} — "
                    "ventrale Kette dominiert; dorsale Rumpfausdauer gezielt fördern"
                )
        return h


# ─── Beurteilung / Normbewertung ─────────────────────────────────────────────

def beurteilung_relative_kraft(rel_kraft: float | None) -> tuple[str, str]:
    """
    Beurteilung der relativen Bankdrück-Kraft für Fußballspieler.
    Orientierungswerte (kein standardisierter Normtest):
      < 0.80 × KGW  = Kritisch
      0.80–0.99     = Unterdurchschnittlich
      1.00–1.24     = Durchschnittlich
      1.25–1.49     = Gut
      ≥ 1.50        = Sehr gut / Elite
    Returns (Stufe: str, Empfehlung: str)
    """
    if rel_kraft is None or rel_kraft <= 0:
        return "—", "Keine Daten"
    if rel_kraft < 0.80:
        return "Kritisch", "Kraftaufbau Bankdrücken hat höchste Priorität"
    if rel_kraft < 1.00:
        return "Unterdurchschnittlich", "Systematischer Kraftaufbau empfohlen"
    if rel_kraft < 1.25:
        return "Durchschnittlich", "Planmäßige Kraftentwicklung fortsetzen"
    if rel_kraft < 1.50:
        return "Gut", "Niveau halten, Explosivität integrieren"
    return "Sehr gut", "Elite-Niveau — Krafterhalt und spezifische Schnellkraft"


def beurteilung_ventral_plank(sekunden: float | None) -> tuple[str, str]:
    """
    Beurteilung der ventralen Rumpfkraftausdauer (Plank-Haltezeit).
    Orientierungswerte:
      < 60 s   = Kritisch
      60–89 s  = Unterdurchschnittlich
      90–119 s = Durchschnittlich
      120–149s = Gut
      ≥ 150 s  = Sehr gut
    """
    if sekunden is None or sekunden <= 0:
        return "—", "Keine Daten"
    if sekunden < 60:
        return "Kritisch", "Ventrale Rumpfkraft sofort gezielt trainieren"
    if sekunden < 90:
        return "Unterdurchschnittlich", "Progressiver Rumpfkraftaufbau empfohlen"
    if sekunden < 120:
        return "Durchschnittlich", "Rumpfausdauer weiter steigern"
    if sekunden < 150:
        return "Gut", "Gute Rumpfbasis — Qualität und Varianz erhöhen"
    return "Sehr gut", "Exzellente Rumpfausdauer"


def beurteilung_dorsal(sekunden: float | None) -> tuple[str, str]:
    """Beurteilung der dorsalen Rumpfkraftausdauer (Biering-Sørensen)."""
    if sekunden is None or sekunden <= 0:
        return "—", "Keine Daten"
    if sekunden < 60:
        return "Kritisch", "Dorsale Kette sofort stärken (Verletzungsrisiko)"
    if sekunden < 90:
        return "Unterdurchschnittlich", "Dorsalen Rumpf systematisch aufbauen"
    if sekunden < 120:
        return "Durchschnittlich", "Weiter steigern"
    if sekunden < 150:
        return "Gut", "Gute dorsale Ausdauer"
    return "Sehr gut", "Exzellente dorsale Rumpfausdauer"
