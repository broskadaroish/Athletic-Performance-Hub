#!/usr/bin/env python3
"""Regressionen für strukturierte Y-Balance-Statuspfade.

Prüft, dass die gespeicherte positive Formulierung „Keine relevante
Asymmetrie“ niemals aufgrund ihres Wortlauts als negativer Befund zählt.
Die Tests verwenden keine Datenbank und verändern keine Produktivdaten.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics import athletik_score, athletik_sub_scores, risiko_label, risiko_score
from modules import saas_dashboard
from ui_components import C, test_status_card
from y_balance import y_balance_aus_row, y_balance_hat_relevante_asymmetrie


PASS = 0
FAIL = 0


def check(label: str, got, expected) -> None:
    global PASS, FAIL
    if got == expected:
        PASS += 1
        print(f"PASS  {label}")
    else:
        FAIL += 1
        print(f"FAIL  {label}: got={got!r}, expected={expected!r}")


def y_row(
    *,
    anterior_diff: float,
    posteromedial_diff: float = 1.0,
    posterolateral_diff: float = 1.0,
    text: str | None = None,
) -> dict:
    """Y-Balance-Zeile mit Demo-nahen Composite-Werten und numerischen Diffs."""
    result_text = text
    if result_text is None:
        result_text = (
            "Keine relevante Asymmetrie"
            if max(anterior_diff, posteromedial_diff, posterolateral_diff) < 4
            else "Asymmetrie: Anterior"
        )
    return {
        "anterior_rechts": 61.0,
        "anterior_links": 61.0 - anterior_diff,
        "posteromedial_rechts": 95.0,
        "posteromedial_links": 95.0 - posteromedial_diff,
        "posterolateral_rechts": 92.0,
        "posterolateral_links": 92.0 - posterolateral_diff,
        "diff_anterior": anterior_diff,
        "diff_posteromedial": posteromedial_diff,
        "diff_posterolateral": posterolateral_diff,
        "composite_rechts": 92.0,
        "composite_links": 91.0,
        "asymmetrie": result_text,
        "schwerpunkt": "Keine relevante Asymmetrie erkannt",
        "datum": "2026-08-22",
    }


print("\n=== Strukturierter Y-Balance-Befund ===")
demo_unauffaellig = y_row(anterior_diff=1.0)
check(
    "Demo-Fall R 92 % / L 91 % mit ca. 1 cm ist unauffällig",
    y_balance_aus_row(demo_unauffaellig).asymmetrie_text,
    "Keine relevante Asymmetrie",
)
check(
    "Unauffälliger Demo-Fall erzeugt keine relevante Asymmetrie",
    y_balance_hat_relevante_asymmetrie(demo_unauffaellig),
    False,
)

knapp_unter_grenze = y_row(anterior_diff=3.9)
check(
    "3,9 cm bleibt unter dem bestehenden 4-cm-Grenzwert unauffällig",
    y_balance_hat_relevante_asymmetrie(knapp_unter_grenze),
    False,
)

grenzwert = y_row(anterior_diff=4.0)
check(
    "Am bestehenden 4-cm-Grenzwert gilt der Befund weiterhin als relevant",
    y_balance_hat_relevante_asymmetrie(grenzwert),
    True,
)

relevante_asymmetrie = y_row(anterior_diff=5.0)
check(
    "Relevante Asymmetrie bleibt strukturiert auffällig",
    y_balance_hat_relevante_asymmetrie(relevante_asymmetrie),
    True,
)


print("\n=== Risiko, Score und Gesamtstatus ===")
check(
    "Keine relevante Asymmetrie verursacht keinen Y-Balance-Risikomalus",
    risiko_score(None, demo_unauffaellig),
    0,
)
check(
    "Grenzwertige Asymmetrie behält den bestehenden Risikomalus",
    risiko_score(None, grenzwert),
    2,
)
check(
    "Relevante Asymmetrie behält den bestehenden Risikomalus",
    risiko_score(None, relevante_asymmetrie),
    2,
)
check(
    "Unauffälliger Gesamtstatus bleibt gering",
    risiko_label(risiko_score(None, demo_unauffaellig))[1],
    "gering",
)
check(
    "Relevanter Befund bleibt ein Hinweis für den Trainer",
    risiko_label(risiko_score(None, relevante_asymmetrie))[1],
    "mittel",
)

base_y_score = round((91.5 - 70) / 30 * 100)
check(
    "Unauffälliger Y-Balance-Subscore hat keinen Malus",
    athletik_sub_scores(None, demo_unauffaellig)["Y-Balance"],
    base_y_score,
)
check(
    "Relevanter Y-Balance-Subscore behält den 10-Punkte-Malus",
    athletik_sub_scores(None, relevante_asymmetrie)["Y-Balance"],
    base_y_score - 10,
)
check(
    "Unauffälliger Athletik-Score hat keinen Y-Balance-Malus",
    athletik_score(None, demo_unauffaellig),
    base_y_score,
)
check(
    "Relevanter Athletik-Score behält den Y-Balance-Malus",
    athletik_score(None, relevante_asymmetrie),
    base_y_score - 10,
)


print("\n=== Darstellung: Dashboard, Vergleich und Übersichtskachel ===")
dashboard_dependencies = {
    name: getattr(saas_dashboard, name)
    for name in (
        "fms_letzter",
        "y_balance_letzter",
        "sprint_letzter",
        "sprung_letzter",
        "agilitaet_letzter",
        "ausdauer_letzter",
        "spiro_test_letzter",
        "verletzungen_laden",
    )
}
try:
    saas_dashboard.fms_letzter = lambda _pid: None
    saas_dashboard.y_balance_letzter = (
        lambda pid: demo_unauffaellig if pid == 1 else relevante_asymmetrie
    )
    saas_dashboard.sprint_letzter = lambda _pid: None
    saas_dashboard.sprung_letzter = lambda _pid: None
    saas_dashboard.agilitaet_letzter = lambda _pid: None
    saas_dashboard.ausdauer_letzter = lambda _pid: None
    saas_dashboard.spiro_test_letzter = lambda _pid: None
    saas_dashboard.verletzungen_laden = lambda _pid: []
    dashboard_score, dashboard_risk, dashboard_count = (
        saas_dashboard._compute_team_score([{"id": 1}, {"id": 2}])
    )
finally:
    for name, value in dashboard_dependencies.items():
        setattr(saas_dashboard, name, value)

check(
    "Dashboard zählt nur den relevanten Y-Balance-Befund als Risiko",
    (dashboard_score, dashboard_risk, dashboard_count),
    (round((base_y_score + (base_y_score - 10)) / 2), 1, 2),
)
check(
    "Übersichtskachel zeigt unauffälligen Y-Balance-Status grün",
    C["green"] in test_status_card(
        "Y-Balance",
        "📏",
        "2026-08-22",
        "Unauffällig — Keine relevante Asymmetrie",
    ),
    True,
)

app_source = (ROOT / "app.py").read_text(encoding="utf-8")
check(
    "Vergleichsansicht nutzt den strukturierten Y-Balance-Befund",
    'y_balance_hat_relevante_asymmetrie(row)' in app_source,
    True,
)
check(
    "Übersichtskachel nutzt den strukturierten Y-Balance-Befund",
    'y_balance_hat_relevante_asymmetrie(y)' in app_source,
    True,
)


print(f"\nErgebnis: {PASS} PASS, {FAIL} FAIL")
if FAIL:
    sys.exit(1)