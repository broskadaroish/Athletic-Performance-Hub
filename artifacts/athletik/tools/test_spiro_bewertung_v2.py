#!/usr/bin/env python3
"""Regressionen für die protokollspezifische Spiro-/Stufentest-Bewertung V2."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import defizite_ermitteln, trainingsbereich_scores_ermitteln
from spiro import spiro_bewertung_v2, spiro_vo2_messwert


PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")


print("\n=== Messwert-Herkunft ===")
messwert = spiro_vo2_messwert(
    {"vo2_peak": 48.0, "vo2_max": 47.0, "geschaetzte_vo2max": 39.0}
)
check("Direkte VO₂peak bleibt gegenüber Schätzung vorrangig",
      messwert["feld"] == "vo2_peak" and messwert["direkt_gemessen"])

messwert_schaetzung = spiro_vo2_messwert({"geschaetzte_vo2max": 39.0})
check("Ausschließlich geschätzter Wert ist klar gekennzeichnet",
      messwert_schaetzung["label"] == "VO₂max (geschätzt)"
      and not messwert_schaetzung["direkt_gemessen"])


print("\n=== Protokolltrennung ===")
feld = spiro_bewertung_v2(
    {"geraeteart": "Laufbasierter Feldtest", "protokoll_name": "IAT 3 min",
     "vo2_peak": 42.0, "schwelle_geschwindigkeit": 11.0},
    alter_testtag=12, geschlecht="Männlich",
)
check("Feld-/Laktattest erhält keine übertragene Bruce-Norm",
      feld["status"] == "keine_belastbare_referenz")

cycle = spiro_bewertung_v2(
    {"geraeteart": "Fahrradergometer (nicht fußballspezifisch)",
     "protokoll_name": "Ramp Cycle", "vo2_peak": 42.0, "koerpergewicht": 45.0},
    alter_testtag=12, geschlecht="Weiblich",
)
check("Cycle ohne vollständiges unterstütztes Modell bleibt neutral",
      cycle["status"] == "keine_belastbare_referenz")

nicht_bruce = spiro_bewertung_v2(
    {"geraeteart": "Laufband", "protokoll_name": "Ramp 1 min", "vo2_peak": 42.0},
    alter_testtag=12, geschlecht="Männlich",
)
check("Laufband ohne Bruce-Protokoll erhält keine Bruce-Norm",
      nicht_bruce["status"] == "keine_belastbare_referenz")


print("\n=== Bruce-Referenzvergleich ===")
bruce_stufen = [
    {"stufennummer": 1, "geschwindigkeit_kmh": 2.7, "steigung_prozent": 10.0,
     "dauer_sekunden": 180, "rer": 1.01, "stufe_vollstaendig": True},
    {"stufennummer": 2, "geschwindigkeit_kmh": 4.0, "steigung_prozent": 12.0,
     "dauer_sekunden": 180, "rer": 1.08, "stufe_vollstaendig": True},
]
bruce = spiro_bewertung_v2(
    {"protokoll_id": 1, "protokoll_geraeteart": "Laufband",
     "geraeteart": "Laufband", "protokoll_name": "Bruce Standard",
     "vo2_peak": 40.0, "koerpergewicht": 70.0},
    alter_testtag=13, geschlecht="Männlich", stufen=bruce_stufen,
)
check("Bruce wird nur mit dokumentiertem Protokoll referenziert",
      bruce["status"] == "bruce_referenzvergleich")
check("Bruce verwendet Alter am Testtag und Geschlecht in der Quelle",
      bruce["referenzwert"] == 30.8 and bruce["abweichung"] == 9.2)

bruce_ohne_rer = spiro_bewertung_v2(
    {"protokoll_id": 1, "protokoll_geraeteart": "Laufband",
     "geraeteart": "Laufband", "protokoll_name": "Bruce Standard",
     "vo2_peak": 40.0, "koerpergewicht": 70.0},
    alter_testtag=13, geschlecht="Männlich",
    stufen=[{"stufennummer": 1, "geschwindigkeit_kmh": 2.7, "steigung_prozent": 10.0,
             "dauer_sekunden": 360, "rer": 0.99, "stufe_vollstaendig": True}],
)
check("Bruce ohne dokumentiertes RER-Kriterium bleibt neutral",
      bruce_ohne_rer["status"] == "keine_belastbare_referenz")

bruce_schaetzung = spiro_bewertung_v2(
    {"protokoll_id": 1, "protokoll_geraeteart": "Laufband",
     "geraeteart": "Laufband", "protokoll_name": "Bruce Standard",
     "geschaetzte_vo2max": 40.0, "koerpergewicht": 70.0},
    alter_testtag=13, geschlecht="Männlich", stufen=bruce_stufen,
)
check("Bruce-Schätzung ersetzt keinen direkten Messwert",
      bruce_schaetzung["status"] == "keine_belastbare_referenz")

bruce_spoof = spiro_bewertung_v2(
    {"protokoll_id": 1, "protokoll_geraeteart": "Laufband",
     "geraeteart": "Laufband", "protokoll_name": "Bruce Eigenbau",
     "vo2_peak": 40.0, "koerpergewicht": 70.0},
    alter_testtag=13, geschlecht="Männlich",
    stufen=[{"stufennummer": 1, "geschwindigkeit_kmh": 6.0, "steigung_prozent": 0.0,
             "dauer_sekunden": 180, "rer": 1.08, "stufe_vollstaendig": True}],
)
check("Bruce im Namen reicht ohne standardkonforme Stufen nicht aus",
      bruce_spoof["status"] == "keine_belastbare_referenz")

bruce_falsche_dauer = spiro_bewertung_v2(
    {"protokoll_id": 1, "protokoll_geraeteart": "Laufband",
     "geraeteart": "Laufband", "protokoll_name": "Bruce Standard",
     "vo2_peak": 40.0, "koerpergewicht": 70.0},
    alter_testtag=13, geschlecht="Männlich",
    stufen=[{"stufennummer": 1, "geschwindigkeit_kmh": 2.7, "steigung_prozent": 10.0,
             "dauer_sekunden": 60, "rer": 1.08, "stufe_vollstaendig": True}],
)
check("Bruce mit abweichender Stufendauer bleibt neutral",
      bruce_falsche_dauer["status"] == "keine_belastbare_referenz")


print("\n=== Keine automatischen Spiro-Defizite ===")
spiro_niedrig = {
    "geraeteart": "Laufband", "protokoll_name": "IAT 3 min",
    "vo2_peak": 42.0, "schwelle_geschwindigkeit": 11.0,
}
defizite = defizite_ermitteln(None, None, spiro_row=spiro_niedrig)
scores = trainingsbereich_scores_ermitteln(spiro_row=spiro_niedrig)
check("<45 / <50 und <12 erzeugen kein automatisches Spiro-Defizit", not defizite)
check("Trainingsplan und Periodisierung erhalten denselben leeren Spiro-Input", scores == {})


print("\n" + "=" * 60)
print(f"Ergebnis: {PASS} PASS, {FAIL} FAIL")
print("=" * 60)
if FAIL:
    raise SystemExit(1)