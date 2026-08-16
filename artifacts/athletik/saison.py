"""
saison.py — Fußball-Saisonlogik und Altersklassen-Berechnung

Trennt klar drei Altersebenen:

  A) Chronologisches Alter   — für Testnormen und Belastungssteuerung
  B) Fußball-Altersklasse    — jahrgangsbasiert, saisonabhängig
  C) Test-/Normgruppe        — richtet sich nach wissenschaftlicher Referenz

Berechnungsregel (Saisonwechsel default: 01. Juli):
  Wenn heutiges Datum >= Saisonwechsel → Saison = aktuelles Jahr / aktuelles Jahr + 1
  Wenn heutiges Datum <  Saisonwechsel → Saison = letztes Jahr   / aktuelles Jahr

  Fußball-U-Klasse = Saison-Endjahr − Geburtsjahr

Beispiel (Saisonwechsel 01.07., Stichtag 16.08.2026 → Saison 2026/27):
  JG 2021 → U6   JG 2020 → U7   JG 2019 → U8
  JG 2016 → U11  JG 2015 → U12  JG 2013 → U14
"""

from __future__ import annotations
from datetime import date, datetime
import calendar as _cal


# ─── DB-Schlüssel ────────────────────────────────────────────────────────────

_KEY_TAG   = "saisonwechsel_tag"
_KEY_MONAT = "saisonwechsel_monat"
_DEF_TAG   = 1
_DEF_MONAT = 7


# ─── Saisonwechsel lesen/schreiben ───────────────────────────────────────────

def saisonwechsel_laden() -> tuple[int, int]:
    """Lädt Saisonwechsel-Datum (Tag, Monat) aus den App-Einstellungen.
    Default: 1. Juli (1, 7).
    """
    from database import einstellung_laden
    try:
        tag   = int(einstellung_laden(_KEY_TAG)   or _DEF_TAG)
        monat = int(einstellung_laden(_KEY_MONAT) or _DEF_MONAT)
    except (TypeError, ValueError):
        tag, monat = _DEF_TAG, _DEF_MONAT
    return max(1, min(31, tag)), max(1, min(12, monat))


def saisonwechsel_speichern(tag: int, monat: int) -> None:
    """Speichert Saisonwechsel-Datum dauerhaft in den App-Einstellungen."""
    from database import einstellung_speichern
    einstellung_speichern(_KEY_TAG,   str(int(tag)))
    einstellung_speichern(_KEY_MONAT, str(int(monat)))


# ─── Saisonberechnung ────────────────────────────────────────────────────────

def aktuelle_saison(
    sw_tag: int = _DEF_TAG,
    sw_monat: int = _DEF_MONAT,
    stichtag: date | None = None,
) -> tuple[int, int]:
    """Gibt (Startjahr, Endjahr) der aktuellen Saison zurück.

    Wenn heute >= Saisonwechsel-Datum → Saison endet nächstes Jahr.
    Wenn heute <  Saisonwechsel-Datum → Saison endet dieses Jahr.

    Beispiele (Saisonwechsel 01.07.):
      16.08.2026 → (2026, 2027)
      30.06.2026 → (2025, 2026)
      01.07.2026 → (2026, 2027)  ← Grenzfall: >= ist inklusive
    """
    heute = stichtag or date.today()
    # Korrektur bei ungültigem Tag (z. B. 31.02. → letzter gültiger Tag)
    letzter = _cal.monthrange(heute.year, sw_monat)[1]
    sw = date(heute.year, sw_monat, min(sw_tag, letzter))
    if heute >= sw:
        return (heute.year, heute.year + 1)
    return (heute.year - 1, heute.year)


def saison_label(
    sw_tag: int = _DEF_TAG,
    sw_monat: int = _DEF_MONAT,
    stichtag: date | None = None,
) -> str:
    """Aktuelle Saison als lesbarer String, z. B. '2026/27'."""
    start, ende = aktuelle_saison(sw_tag, sw_monat, stichtag)
    return f"{start}/{str(ende)[-2:]}"


# ─── Fußball-Altersklasse ────────────────────────────────────────────────────

def fussballklasse_berechnen(
    geburtsjahr: int,
    stichtag: date | None = None,
    sw_tag: int = _DEF_TAG,
    sw_monat: int = _DEF_MONAT,
) -> str:
    """Berechnet die Fußball-Altersklasse aus Geburtsjahr + Saisonwechsel.

    U-Klasse = Saison-Endjahr − Geburtsjahr

    Beispiele (Saisonwechsel 01.07., Stichtag 16.08.2026 → Saison 2026/27):
      JG 2021 → U6   JG 2020 → U7   JG 2019 → U8
      JG 2018 → U9   JG 2016 → U11  JG 2015 → U12
    """
    _, end_year = aktuelle_saison(sw_tag, sw_monat, stichtag)
    u_nr = end_year - geburtsjahr
    if u_nr <= 4:
        return "U4 (Minis)"
    if u_nr == 5:
        return "U5"
    if u_nr == 6:
        return "U6"
    if u_nr >= 20:
        return "Senioren"
    return f"U{u_nr}"


def fussballklasse_aus_datum(
    geburtsdatum_str: str,
    stichtag: date | None = None,
    sw_tag: int = _DEF_TAG,
    sw_monat: int = _DEF_MONAT,
) -> str | None:
    """Berechnet Fußballklasse aus Geburtsdatum-String (TT.MM.JJJJ / JJJJ-MM-TT).
    Gibt None zurück bei leerem oder ungültigem Datum.
    """
    if not geburtsdatum_str:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            geb = datetime.strptime(geburtsdatum_str, fmt).date()
            return fussballklasse_berechnen(geb.year, stichtag, sw_tag, sw_monat)
        except ValueError:
            continue
    return None


def geburtsjahr_aus_datum(geburtsdatum_str: str) -> int | None:
    """Extrahiert das Geburtsjahr aus einem Datumsstring."""
    if not geburtsdatum_str:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(geburtsdatum_str, fmt).year
        except ValueError:
            continue
    return None


# ─── UI-Hilfsfunktionen ──────────────────────────────────────────────────────

def fussballklasse_info(
    geburtsdatum_str: str,
    stichtag: date | None = None,
) -> dict:
    """Gibt alle Alters-Infos für einen Spieler zurück.

    Returns dict mit:
      fussballklasse: str | None   z.B. "U11"
      jahrgang:       int | None   z.B. 2016
      saison:         str          z.B. "2026/27"
      sw_tag:         int
      sw_monat:       int
    """
    sw_tag, sw_monat = saisonwechsel_laden()
    return {
        "fussballklasse": fussballklasse_aus_datum(
            geburtsdatum_str, stichtag, sw_tag, sw_monat
        ),
        "jahrgang":   geburtsjahr_aus_datum(geburtsdatum_str),
        "saison":     saison_label(sw_tag, sw_monat, stichtag),
        "sw_tag":     sw_tag,
        "sw_monat":   sw_monat,
    }


def testreferenz_caption(
    alter: float | None,
    geburtsdatum_str: str = "",
    stichtag: date | None = None,
) -> str:
    """Generiert einen Caption-String der BEIDE Ebenen klar trennt:

      Testreferenz: U10 (Alter 9–10)  ·  Fußballklasse: U11 (Saison 2026/27)

    Wenn kein Geburtsdatum → nur Testreferenz.
    """
    from age_norms import normgruppe_label as _ngl
    tref = _ngl(alter)
    if geburtsdatum_str:
        info = fussballklasse_info(geburtsdatum_str, stichtag)
        fk   = info.get("fussballklasse")
        sl   = info.get("saison", "")
        if fk:
            return f"{tref}  ·  Fußballklasse: {fk} (Saison {sl})"
    return tref
