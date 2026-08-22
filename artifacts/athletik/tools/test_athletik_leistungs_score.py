"""Regressionen für den performance-only Athletik-Score."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analytics import athletik_leistungsbewertung, athletik_score, risiko_score
from fms import fms_hat_relevante_asymmetrie


def test_fms_und_y_balance_senken_keinen_leistungs_score():
    basis = dict(
        sprint_row={"bewertung_10m": "Gut (Leistungssport)"},
        agil_row={"bew_t_test": "Sehr gut (Profi-Niveau)"},
    )
    ohne_hinweise = athletik_score(**basis)
    mit_hinweisen = athletik_score(
        {"score": 8, "asymmetrie": "1 Asymmetrie"},
        {"composite_rechts": 80, "composite_links": 70, "asymmetrie": "Auffällig"},
        **basis,
    )
    assert ohne_hinweise == mit_hinweisen == 87


def test_ein_bereich_ist_kein_gesamt_score():
    result = athletik_leistungsbewertung(sprint_row={"bewertung_10m": "Gut (Leistungssport)"})
    assert result.gesamt_score is None
    assert result.module_scores == {"Sprint": 78}
    assert "kein Gesamt-Athletikscore" in result.datenbasis_text


def test_gewichte_werden_nur_ueber_vorhandene_leistungsbereiche_normalisiert():
    result = athletik_leistungsbewertung(
        sprint_row={"bewertung_10m": "Gut (Leistungssport)"},
        sprung_row={"bewertung_cmj": "Sehr gut (Profi-Niveau)", "cmj_asymmetrie": 24},
        aus_row={"bewertung": "Mittel", "vo2max": 70},
    )
    assert result.module_scores["Sprung / Power"] == 95  # keine Asymmetrie-Strafe
    assert result.module_scores["Ausdauer"] == 58  # kein VO₂-Bonus
    assert result.gesamt_score == 79


def test_fms_keine_asymmetrie_ist_neutral():
    fms = {"score": 14, "asymmetrie": "Keine Asymmetrie"}
    assert not fms_hat_relevante_asymmetrie(fms)
    assert risiko_score(fms, None, []) == 1  # FMS-Rohwert, ohne falschen Asymmetrieaufschlag


def test_abgeleitete_weibliche_normen_erzeugen_keinen_leistungs_score():
    result = athletik_leistungsbewertung(
        sprint_row={"bewertung_10m": "Sehr gut (Profi-Niveau)", "beste_10m": 2.0},
        sprung_row={"bewertung_cmj": "Sehr gut (Profi-Niveau)", "cmj_beid": 30},
        agil_row={"bew_t_test": "Sehr gut (Profi-Niveau)", "t_test": 11.0},
        geschlecht="Weiblich",
    )
    assert result.gesamt_score is None
    assert result.module_scores == {}


def test_unvollstaendige_datenbasis_hat_neutralen_anzeigewert_fuer_kaderlisten():
    result = athletik_leistungsbewertung(sprint_row={"bewertung_10m": "Gut (Leistungssport)"})
    assert (result.gesamt_score if result.gesamt_score is not None else "—") == "—"


def test_vergleichs_pdf_akzeptiert_fehlende_gesamt_scores():
    from pdf_report import generate_vergleich_pdf

    a = {"name": "Spieler A"}
    b = {"name": "Spieler B"}
    assert generate_vergleich_pdf(a, b, sc1=None, sc2=None).startswith(b"%PDF")
    assert generate_vergleich_pdf(a, b, sc1=78, sc2=None).startswith(b"%PDF")


if __name__ == "__main__":
    test_fms_und_y_balance_senken_keinen_leistungs_score()
    test_ein_bereich_ist_kein_gesamt_score()
    test_gewichte_werden_nur_ueber_vorhandene_leistungsbereiche_normalisiert()
    test_fms_keine_asymmetrie_ist_neutral()
    test_abgeleitete_weibliche_normen_erzeugen_keinen_leistungs_score()
    test_unvollstaendige_datenbasis_hat_neutralen_anzeigewert_fuer_kaderlisten()
    test_vergleichs_pdf_akzeptiert_fehlende_gesamt_scores()
    print("PASS: zentrale Leistungs-Score-Regressionen")