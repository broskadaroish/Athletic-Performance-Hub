#!/usr/bin/env python3
"""Gezielte Regressionen für die zentrale Defizitlogik.

Prüft die verbindliche Kette:
strukturierte Testbewertung -> Trainingsbereich-Score -> Plan-/Periodisierungsinput.
Die Suite verwendet keine Datenbank und verändert keine Produktivdaten.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import (
    defizite_ermitteln,
    schwerpunkt_sammeln,
    trainingsbereich_scores_ermitteln,
)
from periodisierung import defizit_score
from sprint import SprintErgebnis


PASS = 0
FAIL = 0


def check(label, got, expected):
    global PASS, FAIL
    if got == expected:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}: got={got!r}, expected={expected!r}")


def has_area(defizite, bereich):
    return any(d["bereich"] == bereich for d in defizite)


print("\n=== 1. Sprint: aktuelle Bewertung vor Legacy-Text ===")
sprint_gut_mit_legacy = {
    "bewertung_10m": "Gut (Leistungssport)",
    "bewertung_30m": "Sehr gut (Profi-Niveau)",
    "defizite": '["Maximalgeschwindigkeit (20–30 m)"]',
}
d = defizite_ermitteln(None, None, sprint_gut_mit_legacy)
scores = trainingsbereich_scores_ermitteln(sprint_row=sprint_gut_mit_legacy)
check("Guter 10-/30-m-Sprint ignoriert alten Schnelligkeitstext", "Schnelligkeit" in scores, False)
check("Guter 10-/30-m-Sprint erzeugt kein Geschwindigkeitsdefizit", has_area(d, "Maximalgeschwindigkeit"), False)
check("Textadapter bleibt bei gutem Sprint leer", schwerpunkt_sammeln(None, None, sprint_gut_mit_legacy), "")

sprint_schlecht = {"bewertung_10m": "Verbesserungsbedarf", "bewertung_30m": "Gut (Leistungssport)"}
scores = trainingsbereich_scores_ermitteln(sprint_row=sprint_schlecht)
check("Schlechter 10-m-Sprint erzeugt Schnelligkeit", scores.get("Schnelligkeit"), 3)
check("Periodisierung übernimmt strukturierten Schnelligkeitsscore", defizit_score(scores).get("Schnelligkeit"), 3)

sprint_legacy = {"bewertung_10m": None, "bewertung_30m": "—", "defizite": "Maximalgeschwindigkeit (20–30 m)"}
scores = trainingsbereich_scores_ermitteln(sprint_row=sprint_legacy)
check("Legacy-Sprint ohne verwertbare Bewertung bleibt nutzbar", "Schnelligkeit" in scores, True)

mixed_10m_gut_30m_ohne_bewertung = {
    "bewertung_10m": "Gut (Leistungssport)",
    "bewertung_30m": "—",
    "defizite": "Maximalgeschwindigkeit (20–30 m)",
}
d = defizite_ermitteln(None, None, mixed_10m_gut_30m_ohne_bewertung)
check("Gutes 10 m blendet unbewerteten 30-m-Legacybefund nicht aus",
      has_area(d, "Maximalgeschwindigkeit"), True)

mixed_30m_gut_10m_ohne_bewertung = {
    "bewertung_10m": "—",
    "bewertung_30m": "Gut (Leistungssport)",
    "defizite": "Linearbeschleunigung (0–10 m)",
}
d = defizite_ermitteln(None, None, mixed_30m_gut_10m_ohne_bewertung)
check("Gutes 30 m blendet unbewerteten 10-m-Legacybefund nicht aus",
      has_area(d, "Lineargeschwindigkeit"), True)

res_gut_u10 = SprintErgebnis(
    beste_10m=2.07, beste_30m=5.06, geschlecht="Männlich", alter=9.0
)
check("Altersgerecht guter U10-Sprint erzeugt keine Legacy-Defizite", res_gut_u10.defizite, [])


print("\n=== 2. Bewegungsqualität und Balance ===")
scores = trainingsbereich_scores_ermitteln(fms_row={"score": 12})
check("FMS-Score 12 priorisiert Rumpf", scores.get("Rumpf"), 3)
scores = trainingsbereich_scores_ermitteln(fms_row={"score": 15})
check("FMS-Score 15 erzeugt kein Rumpfdefizit ohne Schwerpunkt", "Rumpf" in scores, False)

scores = trainingsbereich_scores_ermitteln(y_row={"asymmetrie": "Anterior-Asymmetrie"})
check("Y-Balance anterior priorisiert Sprunggelenk", scores.get("Sprunggelenk"), 3)
scores = trainingsbereich_scores_ermitteln(y_row={"asymmetrie": "Posteromedial-Asymmetrie"})
check("Y-Balance posteromedial priorisiert Hüfte", scores.get("Hüfte"), 3)


print("\n=== 3. Sprung und Agilität ===")
sprung = {"bewertung_cmj": "Mittel (Breitensport)", "cmj_asymmetrie": 11, "rsi": 1.2}
scores = trainingsbereich_scores_ermitteln(sprung_row=sprung)
check("CMJ/RSI ergibt Explosivität", scores.get("Explosivität"), 2)
check("Sprungasymmetrie ergibt Knie", scores.get("Knie"), 3)

agil = {"bew_t_test": "Verbesserungsbedarf", "bew_505": "Gut", "asym_505": 12}
scores = trainingsbereich_scores_ermitteln(agil_row=agil)
check("T-Test/505-Asymmetrie ergibt Agilität", scores.get("Agilität"), 3)


print("\n=== 4. Ausdauer, Kraft und Stufentest ===")
aus_gut = {"bewertung": "Gut", "vo2max": 40.8, "altersgruppe": "U10/U11"}
scores = trainingsbereich_scores_ermitteln(aus_row=aus_gut)
check("Altersgerechte gute U10-Ausdauer ergibt keinen Bereich", "Ausdauer" in scores, False)

aus_schlecht = {"bewertung": "Verbesserungsbedarf", "vo2max": 30, "altersgruppe": "U10/U11"}
scores = trainingsbereich_scores_ermitteln(aus_row=aus_schlecht)
check("Schwache Yo-Yo-Ausdauer priorisiert Ausdauer", scores.get("Ausdauer"), 3)

kraft = {
    "relative_kraft_direkt": 0.8,
    "ventral_sekunden": 60,
    "lateral_asymmetrie_pct": 12,
}
scores = trainingsbereich_scores_ermitteln(kraft_row=kraft)
check("Bestehende Kraftschwellen priorisieren Rumpf", scores.get("Rumpf"), 2)
check("Laterale Kraftasymmetrie ergänzt Hüfte", scores.get("Hüfte"), 2)

spiro = {"vo2_peak": 42, "schwelle_geschwindigkeit": 11}
scores = trainingsbereich_scores_ermitteln(spiro_row=spiro)
check("Stufentest unter bestehender Schwelle priorisiert Ausdauer", scores.get("Ausdauer"), 3)


print("\n=== 5. Anthropometrie bleibt Kontext ===")
anthro = {"bmi": 31, "reifestatus": "vor PHV"}
d = defizite_ermitteln(None, None, anthro_row=anthro)
scores = trainingsbereich_scores_ermitteln(anthro_row=anthro)
check("Anthropometrie bleibt als Hinweis sichtbar", len(d) >= 1, True)
check("Anthropometrie erzeugt keinen medizinisch interpretierten Planbereich", scores, {})


print("\n=== 6. Textkompatibilität ===")
check("Textpfad für externe Aufrufer bleibt erhalten", "Ausdauer" in defizit_score("Aerobe Ausdauer verbesserungswürdig"), True)


print("\n" + "=" * 60)
print(f"Ergebnis: {PASS} PASS, {FAIL} FAIL")
print("=" * 60)
if FAIL:
    sys.exit(1)