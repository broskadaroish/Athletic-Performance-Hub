"""
Anthropometrie-Modul — Körpermessungen, BMI, Wachstum, Reifestatus-Schätzung.

HINWEIS: Die PHV- und Reifestatus-Schätzung ist eine wissenschaftliche Näherung
(Mirwald et al., 2002) und ersetzt KEINE medizinische Diagnose oder ärztliche Untersuchung.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from who_bmi_reference import who_bmi_grenzen


# ─── BMI-Kategorien (WHO Growth Reference 2007 / Erwachsene) ──────────────────

_BMI_NEUTRAL_TEXT = "Keine altersbezogene BMI-Bewertung möglich"
_WHO_REFERENCE = "WHO Growth Reference 2007 (BMI-for-age, 5–19 Jahre)"
_ADULT_REFERENCE = "WHO-BMI-Klassifikation für Erwachsene (ab 18 Jahren)"
_BMI_COLORS = {
    "neutral": "#8b949e",
    "unauffaellig": "#3fb950",
    "beobachten": "#d29922",
    "handlungsbedarf": "#f85149",
    "aktionsbedarf": "#f85149",
}


@dataclass(frozen=True)
class BMIBewertung:
    """Strukturierte BMI-Einordnung für alle UI- und Analyseverbraucher."""

    code: str
    kategorie: str
    anzeige: str
    schweregrad: str
    farbe: str
    referenz: str
    alter_monate: Optional[float] = None
    grenzwerte: Optional[tuple[float, float, float, float]] = None

    @property
    def ist_auffaellig(self) -> bool:
        return self.schweregrad in {"beobachten", "handlungsbedarf", "aktionsbedarf"}

    @property
    def kachel_text(self) -> str:
        """Einheitlicher, nicht aus Textfragmenten abgeleiteter UI-Status."""
        prefix = {
            "unauffaellig": "Unauffällig",
            "beobachten": "Beobachten",
            "handlungsbedarf": "Handlungsbedarf",
            "aktionsbedarf": "Aktionsbedarf",
        }.get(self.schweregrad)
        return f"{prefix} — {self.kategorie}" if prefix else self.anzeige


def _bmi_bewertung(
    code: str,
    kategorie: str,
    schweregrad: str,
    referenz: str,
    *,
    alter_monate: Optional[float] = None,
    grenzwerte: Optional[tuple[float, float, float, float]] = None,
) -> BMIBewertung:
    return BMIBewertung(
        code=code,
        kategorie=kategorie,
        anzeige=kategorie,
        schweregrad=schweregrad,
        farbe=_BMI_COLORS[schweregrad],
        referenz=referenz,
        alter_monate=alter_monate,
        grenzwerte=grenzwerte,
    )


def _bmi_neutral(anzeige: str = _BMI_NEUTRAL_TEXT) -> BMIBewertung:
    return BMIBewertung(
        code="not_assessable",
        kategorie=anzeige,
        anzeige=anzeige,
        schweregrad="neutral",
        farbe=_BMI_COLORS["neutral"],
        referenz="Keine passende BMI-Referenz anwendbar",
    )


def _datum_parsen(wert) -> Optional[date]:
    if isinstance(wert, datetime):
        return wert.date()
    if isinstance(wert, date):
        return wert
    if not wert:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(wert), fmt).date()
        except ValueError:
            continue
    return None


def _datum_mit_jahren(datum: date, jahre: int) -> date:
    """Addiert Kalenderjahre, einschließlich eines sicheren 29.-Februar-Falls."""
    try:
        return datum.replace(year=datum.year + jahre)
    except ValueError:
        return datum.replace(year=datum.year + jahre, month=2, day=28)


def _datum_mit_monaten(datum: date, monate: int) -> date:
    zielmonat = datum.month - 1 + monate
    zieljahr = datum.year + zielmonat // 12
    zielmonat = zielmonat % 12 + 1
    letzter_tag = (_datum_mit_jahren(date(zieljahr, 1, 1), 1) - date(zieljahr, 1, 1)).days
    if zielmonat != 1:
        folgemonat = date(zieljahr + (zielmonat == 12), (zielmonat % 12) + 1, 1)
        letzter_tag = (folgemonat - date(zieljahr, zielmonat, 1)).days
    return date(zieljahr, zielmonat, min(datum.day, letzter_tag))


def bmi_alter_monate(geburtsdatum, messdatum) -> Optional[float]:
    """Berechnet das Alter am Messdatum kalendergenau in Monaten."""
    geburt = _datum_parsen(geburtsdatum)
    messung = _datum_parsen(messdatum)
    if not geburt or not messung or messung < geburt:
        return None
    volle_monate = (messung.year - geburt.year) * 12 + messung.month - geburt.month
    if _datum_mit_monaten(geburt, volle_monate) > messung:
        volle_monate -= 1
    anker = _datum_mit_monaten(geburt, volle_monate)
    naechster_anker = _datum_mit_monaten(geburt, volle_monate + 1)
    anteil = (messung - anker).days / max((naechster_anker - anker).days, 1)
    return round(volle_monate + anteil, 4)


def _who_geschlecht(geschlecht: str | None) -> Optional[str]:
    wert = str(geschlecht or "").strip().lower()
    if wert in {"weiblich", "w", "female", "f"}:
        return "female"
    if wert in {"männlich", "maennlich", "m", "male"}:
        return "male"
    return None

def bmi_berechnen(gewicht_kg: float, groesse_cm: float) -> float:
    """Berechnet den BMI aus Gewicht (kg) und Größe (cm)."""
    if groesse_cm <= 0:
        return 0.0
    return round(gewicht_kg / (groesse_cm / 100) ** 2, 1)


def bmi_kategorie(bmi: float, alter: Optional[int] = None) -> str:
    """Legacy-Helfer für Erwachsene; neue Pfade nutzen :func:`bmi_bewerten`.

    Bei bekanntem Minderjährigenalter wird absichtlich keine Erwachsenenklasse
    zurückgegeben, weil ohne Messdatum und Geschlecht keine WHO-for-age-
    Bewertung möglich ist.
    """
    if bmi <= 0:
        return "—"
    if alter is not None and 0 <= alter < 18:
        return _BMI_NEUTRAL_TEXT
    if bmi < 18.5:  return "Untergewicht"
    if bmi < 25.0:  return "Normalgewicht"
    if bmi < 30.0:  return "Übergewicht"
    return "Adipositas"


def bmi_bewerten(bmi: float | None, geburtsdatum, messdatum, geschlecht: str | None) -> BMIBewertung:
    """Bewertet BMI zentral und ohne Fallback auf Erwachsene für Minderjährige.

    Für unter 18-Jährige verwendet die Funktion ausschließlich die lokale WHO
    Growth Reference 2007 (61–228 Monate). Die lokale Referenz ist damit auch
    für den vollständigen offiziellen 5–19-Jahre-Datenbereich reproduzierbar;
    gemäß Produktregel gelten ab dem 18. Geburtstag die bisherigen
    Erwachsenen-Grenzen 18,5 / 25 / 30.
    """
    try:
        bmi_wert = float(bmi or 0)
    except (TypeError, ValueError):
        bmi_wert = 0.0
    if bmi_wert <= 0:
        return _bmi_neutral("Keine BMI-Bewertung möglich")

    geburt = _datum_parsen(geburtsdatum)
    messung = _datum_parsen(messdatum)
    if not geburt or not messung or messung < geburt:
        return _bmi_neutral()

    if messung >= _datum_mit_jahren(geburt, 18):
        if bmi_wert < 18.5:
            return _bmi_bewertung("underweight", "Untergewicht", "beobachten", _ADULT_REFERENCE)
        if bmi_wert < 25.0:
            return _bmi_bewertung("normal", "Normalgewicht", "unauffaellig", _ADULT_REFERENCE)
        if bmi_wert < 30.0:
            return _bmi_bewertung("overweight", "Übergewicht", "handlungsbedarf", _ADULT_REFERENCE)
        return _bmi_bewertung("obesity", "Adipositas", "aktionsbedarf", _ADULT_REFERENCE)

    alter_monate = bmi_alter_monate(geburt, messung)
    who_geschlecht = _who_geschlecht(geschlecht)
    if alter_monate is None or who_geschlecht is None:
        return _bmi_neutral()
    grenzwerte = who_bmi_grenzen(who_geschlecht, alter_monate)
    if grenzwerte is None:
        return _bmi_neutral(
            "Keine altersbezogene BMI-Bewertung möglich (WHO-Referenz: 61–228 Monate)"
        )

    sd_minus_3, sd_minus_2, sd_plus_1, sd_plus_2 = grenzwerte
    if bmi_wert < sd_minus_3:
        return _bmi_bewertung(
            "severe_thinness", "Starkes Untergewicht", "aktionsbedarf", _WHO_REFERENCE,
            alter_monate=alter_monate, grenzwerte=grenzwerte,
        )
    if bmi_wert < sd_minus_2:
        return _bmi_bewertung(
            "thinness", "Untergewicht", "beobachten", _WHO_REFERENCE,
            alter_monate=alter_monate, grenzwerte=grenzwerte,
        )
    if bmi_wert <= sd_plus_1:
        return _bmi_bewertung(
            "normal", "Normalgewicht", "unauffaellig", _WHO_REFERENCE,
            alter_monate=alter_monate, grenzwerte=grenzwerte,
        )
    if bmi_wert <= sd_plus_2:
        return _bmi_bewertung(
            "overweight", "Übergewicht", "handlungsbedarf", _WHO_REFERENCE,
            alter_monate=alter_monate, grenzwerte=grenzwerte,
        )
    return _bmi_bewertung(
        "obesity", "Adipositas", "aktionsbedarf", _WHO_REFERENCE,
        alter_monate=alter_monate, grenzwerte=grenzwerte,
    )


def bmi_bewertung_aus_messung(anthro_row: dict | None, geburtsdatum, geschlecht: str | None) -> BMIBewertung:
    """Wertet eine gespeicherte Messung zur Anzeige neu aus, ohne sie zu ändern."""
    if not anthro_row:
        return _bmi_neutral("Keine BMI-Bewertung möglich")
    return bmi_bewerten(
        anthro_row.get("bmi"),
        geburtsdatum,
        anthro_row.get("datum") or anthro_row.get("erstellt_am"),
        geschlecht,
    )


def bmi_bewertung_aus_kategorie(kategorie: str | None) -> BMIBewertung:
    """Zentrale Anzeigezuordnung für historische Kategorien ohne Rohdatenkontext."""
    wert = str(kategorie or "").strip().lower()
    if wert in {"normalgewicht", "normalbereich"}:
        return _bmi_bewertung("normal", "Normalgewicht", "unauffaellig", "Historisch gespeicherte Kategorie")
    if wert == "untergewicht":
        return _bmi_bewertung("underweight", "Untergewicht", "beobachten", "Historisch gespeicherte Kategorie")
    if wert in {"starkes untergewicht", "schweres untergewicht"}:
        return _bmi_bewertung("severe_thinness", "Starkes Untergewicht", "aktionsbedarf", "Historisch gespeicherte Kategorie")
    if wert in {"übergewicht", "uebergewicht"}:
        return _bmi_bewertung("overweight", "Übergewicht", "handlungsbedarf", "Historisch gespeicherte Kategorie")
    if wert == "adipositas":
        return _bmi_bewertung("obesity", "Adipositas", "aktionsbedarf", "Historisch gespeicherte Kategorie")
    return _bmi_neutral()


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
