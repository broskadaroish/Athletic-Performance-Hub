"""Regressionen für die zentrale WHO-2007-BMI-for-age-Bewertung."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from analytics import athletik_score, defizite_ermitteln, risiko_score
from anthropometrie import (
    bmi_alter_monate,
    bmi_bewerten,
    bmi_bewertung_aus_kategorie,
    bmi_bewertung_aus_messung,
)
from who_bmi_reference import who_bmi_grenzen
from ui_components import anthro_karte
from pdf_report import GREEN, ampel


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> None:
    # Die WHO-Tabellen sind lokal und in beiden Geschlechtern verfügbar.
    female = who_bmi_grenzen("female", 120.0)
    male = who_bmi_grenzen("male", 120.0)
    check("WHO-Grenzen Mädchen lokal", female is not None and len(female) == 4)
    check("WHO-Grenzen Jungen lokal", male is not None and len(male) == 4)
    check("WHO-Grenzen unterscheiden Geschlechter", female != male)
    check("WHO-Grenzen interpolieren Monatsanteile", who_bmi_grenzen("female", 120.5) != female)

    # Kalendergenaues Alter nutzt Messdatum statt heutiges Alter.
    check("Alter in Monaten am Testtag", 120.45 < bmi_alter_monate("01.01.2014", "15.01.2024") < 120.5)

    # Kinder und Jugendliche: offizielle Grenzwerte, Geschlecht und 17/18-Übergang.
    normal_kind = bmi_bewerten(15.0, "01.01.2014", "01.01.2024", "Weiblich")
    check("Kind WHO normal", normal_kind.code == "normal" and normal_kind.referenz.startswith("WHO"))
    thin_boy = bmi_bewerten(12.0, "01.01.2014", "01.01.2024", "Männlich")
    check("Kind WHO Untergewicht", thin_boy.code in {"thinness", "severe_thinness"})
    overweight_girl = bmi_bewerten(21.0, "01.01.2014", "01.01.2024", "Weiblich")
    check("Kind WHO Übergewicht", overweight_girl.code == "overweight")
    almost_adult = bmi_bewerten(24.0, "02.01.2006", "01.01.2024", "Männlich")
    adult = bmi_bewerten(24.0, "01.01.2006", "01.01.2024", "Männlich")
    adult_19 = bmi_bewerten(24.0, "01.01.2005", "01.01.2024", "Männlich")
    check("17 Jahre WHO", almost_adult.referenz.startswith("WHO"))
    check("ab 18 Erwachsene", adult.referenz.startswith("WHO-BMI") and adult.code == "normal")
    check("auch ab 19 Erwachsene", adult_19.referenz.startswith("WHO-BMI") and adult_19.code == "normal")
    check("WHO-Datenbereich endet reproduzierbar bei 228 Monaten", who_bmi_grenzen("male", 228.0) is not None)

    # Fehlende Pflichtangaben bleiben neutral und fallen nicht auf Erwachsene zurück.
    missing_sex = bmi_bewerten(30.0, "01.01.2014", "01.01.2024", None)
    missing_birth = bmi_bewerten(30.0, None, "01.01.2024", "Männlich")
    under_five_ref = bmi_bewerten(15.0, "01.01.2019", "01.01.2024", "Männlich")
    check("fehlendes Geschlecht neutral", missing_sex.schweregrad == "neutral")
    check("fehlendes Geburtsdatum neutral", missing_birth.schweregrad == "neutral")
    check("nicht unterstütztes Alter neutral", under_five_ref.schweregrad == "neutral")

    # Historische Werte werden nur in der Anzeige konsistent normalisiert.
    historic = bmi_bewertung_aus_kategorie("Normalbereich")
    check("historisches Normalbereich grün", historic.code == "normal" and historic.farbe == "#3fb950")
    historic_card = anthro_karte({"bmi": 23.4, "bmi_kategorie": "Normalbereich"})
    check("historisches Normalbereich in Profilkarte grün", "#3fb950" in historic_card)
    check("historisches Normalbereich im PDF grün", ampel("Normalbereich") == GREEN)
    from_row = bmi_bewertung_aus_messung(
        {"bmi": 15.0, "datum": "01.01.2024", "bmi_kategorie": "Untergewicht"},
        "01.01.2014", "Weiblich",
    )
    check("bestehende Messung wird nicht aus Text abgeleitet", from_row.code == "normal")

    # Scores bleiben explizit von Anthropometrie unabhängig.
    baseline_score = athletik_score(None, None, None, None, None, None)
    baseline_risk = risiko_score(None, None, [])
    anthro = {"bmi": 30.0, "datum": "01.01.2024"}
    deficits = defizite_ermitteln(
        None, None, anthro_row=anthro, geschlecht="Männlich", geburtsdatum="01.01.2014"
    )
    check("BMI nur Kontextwarnung", any(d["bereich"] == "Körperzusammensetzung" for d in deficits))
    without_context = defizite_ermitteln(
        None, None, anthro_row=anthro, geschlecht="Männlich", geburtsdatum=None
    )
    check(
        "fehlende Stammdaten erzeugen keine BMI-Warnung",
        not any(d["bereich"] == "Körperzusammensetzung" for d in without_context),
    )
    adult_underweight = defizite_ermitteln(
        None,
        None,
        anthro_row={"bmi": 17.5, "datum": "01.01.2024"},
        geschlecht="Männlich",
        geburtsdatum="01.01.1990",
    )
    check(
        "Untergewicht bei Erwachsenen bleibt Kontextwarnung",
        any(d["bereich"] == "Körperzusammensetzung" for d in adult_underweight),
    )
    check("Athletik-Score unverändert", athletik_score(None, None, None, None, None, None) == baseline_score)
    check("Risiko-Score unverändert", risiko_score(None, None, []) == baseline_risk)

    # Die Diagnostik-Übersicht darf bei noch fehlender Anthropometrie nicht beim
    # Entpacken der zentralen Farb-Rückgabe abbrechen.
    app_source = Path(ROOT, "app.py").read_text(encoding="utf-8")
    overview_helper = app_source[
        app_source.index("def _anthro_metric_rating()"):
        app_source.index("yb_metric, yb_rating, yb_status_color")
    ]
    check(
        "Diagnostik ohne Anthropometrie bleibt darstellbar",
        "if not anthro_d:\n            return None, None, None" in overview_helper,
    )


if __name__ == "__main__":
    main()