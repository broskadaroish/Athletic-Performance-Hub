"""
Anthropometrie-Modul — Körpermessungen, BMI, Wachstum, Reifestatus-Schätzung.

HINWEIS: Die PHV- und Reifestatus-Schätzung ist eine wissenschaftliche Näherung
(Mirwald et al., 2002) und ersetzt KEINE medizinische Diagnose oder ärztliche Untersuchung.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── BMI-Kategorien (nach WHO) ────────────────────────────────────────────────

def bmi_berechnen(gewicht_kg: float, groesse_cm: float) -> float:
    """Berechnet den BMI aus Gewicht (kg) und Größe (cm)."""
    if groesse_cm <= 0:
        return 0.0
    return round(gewicht_kg / (groesse_cm / 100) ** 2, 1)


def bmi_kategorie(bmi: float, alter: Optional[int] = None) -> str:
    """Gibt die WHO-Kategorie für den BMI zurück (für Erwachsene)."""
    if bmi <= 0:
        return "—"
    if bmi < 18.5:  return "Untergewicht"
    if bmi < 25.0:  return "Normalgewicht"
    if bmi < 30.0:  return "Übergewicht"
    return "Adipositas"


# ─── PHV-Schätzung (Mirwald et al., 2002) ────────────────────────────────────

def phv_offset_berechnen(alter: float, groesse_cm: float, gewicht_kg: float,
                          sitzhoehe_cm: float, beinlaenge_cm: float,
                          geschlecht: str = "Männlich") -> Optional[float]:
    """
    Schätzt den PHV-Offset (Reifeversatz) nach Mirwald et al. (2002).
    Positiver Wert = PHV bereits überschritten.
    Negativer Wert = PHV steht noch bevor.

    ⚠️ NUR eine Schätzung — keine medizinische Aussage.
    Setzt vollständige Messungen voraus (Sitzhöhe + Beinlänge).
    """
    if not all([groesse_cm > 0, gewicht_kg > 0, sitzhoehe_cm > 0, beinlaenge_cm > 0, alter > 0]):
        return None

    if geschlecht == "Männlich":
        offset = (
            -9.236
            + 0.0002708 * (beinlaenge_cm * sitzhoehe_cm)
            - 0.001663 * (alter * beinlaenge_cm)
            + 0.007216 * (alter * sitzhoehe_cm)
            + 0.02292 * (gewicht_kg / groesse_cm * 100)
        )
    else:  # Weiblich
        offset = (
            -7.709133
            + 0.0042232 * (alter * groesse_cm)
            - 0.8224 * (alter / groesse_cm * 100)
            + 0.005900 * (beinlaenge_cm * sitzhoehe_cm)
            - 0.002432 * (alter * beinlaenge_cm)
        )
    return round(offset, 2)


def reifestatus_text(phv_offset: Optional[float]) -> str:
    """Gibt einen verständlichen Reifestatus-Text zurück."""
    if phv_offset is None:
        return "Keine Schätzung möglich (Messwerte unvollständig)"
    if phv_offset < -1.0:
        return f"Vor dem Wachstumsschub (PHV in ca. {abs(phv_offset):.1f} Jahren)"
    if phv_offset < 0.5:
        return f"Im Wachstumsschub (PHV vor ca. {abs(phv_offset):.1f} Jahren)"
    if phv_offset < 2.0:
        return f"Nach dem Wachstumsschub (+{phv_offset:.1f} Jahre)"
    return f"Wachstum weitgehend abgeschlossen (+{phv_offset:.1f} Jahre nach PHV)"


def reifestatus_farbe(phv_offset: Optional[float]) -> str:
    """Gibt eine Ampelfarbe für den Reifestatus zurück."""
    if phv_offset is None:
        return "#8b949e"
    if phv_offset < -0.5:
        return "#3b82f6"   # Blau: vor PHV
    if phv_offset < 1.0:
        return "#d29922"   # Gelb: im/nahe PHV
    return "#3fb950"       # Grün: nach PHV


# ─── Wachstum aus Verlauf ─────────────────────────────────────────────────────

def wachstum_berechnen(verlauf: list[dict]) -> Optional[float]:
    """
    Berechnet das durchschnittliche monatliche Wachstum (cm/Monat)
    aus einer zeitlich sortierten Liste von Anthropometrie-Einträgen.
    Verlauf muss nach Datum sortiert sein (ältester zuerst).
    Gibt None zurück wenn weniger als 2 Einträge vorhanden.
    """
    if len(verlauf) < 2:
        return None

    from datetime import datetime

    def parse_datum(d: str):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(d, fmt)
            except ValueError:
                continue
        return None

    erster = verlauf[0]
    letzter = verlauf[-1]

    d1 = parse_datum(str(erster.get("datum", "")))
    d2 = parse_datum(str(letzter.get("datum", "")))
    g1 = erster.get("groesse")
    g2 = letzter.get("groesse")

    if not all([d1, d2, g1, g2]):
        return None

    monate = (d2 - d1).days / 30.44
    if monate <= 0:
        return None

    return round((g2 - g1) / monate, 2)


# ─── Dataclass ───────────────────────────────────────────────────────────────

@dataclass
class AnthropometrieErgebnis:
    """Zusammenfassung einer anthropometrischen Messung."""
    groesse: float
    gewicht: float
    sitzhoehe: float = 0.0
    beinlaenge: float = 0.0
    armspannweite: float = 0.0
    koerperfett: float = 0.0
    muskelmasse: float = 0.0
    alter: float = 0.0
    geschlecht: str = "Männlich"

    @property
    def bmi(self) -> float:
        return bmi_berechnen(self.gewicht, self.groesse)

    @property
    def bmi_kat(self) -> str:
        return bmi_kategorie(self.bmi, int(self.alter) if self.alter else None)

    @property
    def phv_offset(self) -> Optional[float]:
        return phv_offset_berechnen(
            self.alter, self.groesse, self.gewicht,
            self.sitzhoehe, self.beinlaenge, self.geschlecht,
        )

    @property
    def reife_text(self) -> str:
        return reifestatus_text(self.phv_offset)

    @property
    def reife_farbe(self) -> str:
        return reifestatus_farbe(self.phv_offset)


# ─── Hautfalten-Körperfett (Jackson & Pollock) ───────────────────────────────

def _siri_bf(body_density: float) -> float:
    """Siri (1956): Körperfett-% aus Körperdichte."""
    if body_density <= 0:
        return 0.0
    return round((495.0 / body_density) - 450.0, 1)


def koerperfett_jp7(
    brust_mm: float, mittelachse_mm: float, trizeps_mm: float,
    subskapular_mm: float, abdomen_mm: float, suprailiakal_mm: float,
    oberschenkel_mm: float,
    alter: float, geschlecht: str = "Männlich",
) -> float:
    """
    Körperfett-% nach Jackson & Pollock 7-Punkt-Methode (1978).
    Punkte: Brust, Mittelachse, Trizeps, Subskapular, Abdomen, Suprailiakal, Oberschenkel.
    Gleichung → Körperdichte → Siri (1956).

    ⚠️ Nur ein Orientierungswert für die Trainingssteuerung.
    """
    s = brust_mm + mittelachse_mm + trizeps_mm + subskapular_mm + abdomen_mm + suprailiakal_mm + oberschenkel_mm
    if geschlecht == "Männlich":
        bd = 1.112 - 0.00043499 * s + 0.00000055 * s ** 2 - 0.00028826 * alter
    else:
        bd = 1.0970 - 0.00046971 * s + 0.00000056 * s ** 2 - 0.00012828 * alter
    return _siri_bf(bd)


def koerperfett_jp11(
    brust_mm: float, mittelachse_mm: float, trizeps_mm: float,
    subskapular_mm: float, abdomen_mm: float, suprailiakal_mm: float,
    oberschenkel_mm: float, bizeps_mm: float, wade_mm: float,
    unterer_ruecken_mm: float, pektoral_mm: float,
    alter: float, geschlecht: str = "Männlich",
) -> float:
    """
    Körperfett-% nach Pařízkova (1977) — 11 Messpunkte (Logarithmen-Methode).
    Punkte: Brust, Mittelachse, Trizeps, Subskapular, Abdomen, Suprailiakal,
            Oberschenkel, Bizeps, Wadeninnenseite, unterer Rücken, Pektoral.
    Formel: Männer: %KF = 11,7 × log₁₀(Σ) − 11,6
            Frauen: %KF = 15,0 × log₁₀(Σ) − 12,6
    Quelle: Pařízkova, J. (1977). Body fat and physical fitness. Martinus Nijhoff.

    ⚠️ Nur ein Orientierungswert für die Trainingssteuerung.
    """
    import math
    s = (brust_mm + mittelachse_mm + trizeps_mm + subskapular_mm + abdomen_mm
         + suprailiakal_mm + oberschenkel_mm + bizeps_mm + wade_mm
         + unterer_ruecken_mm + pektoral_mm)
    if s <= 0:
        return 0.0
    if geschlecht == "Männlich":
        kf = 11.7 * math.log10(s) - 11.6
    else:
        kf = 15.0 * math.log10(s) - 12.6
    return round(max(kf, 0.0), 1)
