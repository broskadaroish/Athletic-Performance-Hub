"""
tools/test_ausdauer_defizit.py
================================
Prüft die altersgerechte VO₂max-Defiziterkennung in:
  - AusdauerErgebnis.defizite  (ausdauer.py)
  - defizite_ermitteln()       (analytics.py)

Kernregel: 520 m / VO₂max ~40.8 / U10-U11-Kind → KEIN Defizit
           (wäre nach alter Pauschalschwelle < 50 fälschlicherweise ein Defizit gewesen)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ausdauer  import AusdauerErgebnis
from analytics import defizite_ermitteln

PASS = 0
FAIL = 0

def check(label, got, expected):
    global PASS, FAIL
    ok = got == expected
    tag = "PASS" if ok else "FAIL"
    print(f"  {tag}  {label}: got {got!r}" + ("" if ok else f", expected {expected!r}"))
    if ok:
        PASS += 1
    else:
        FAIL += 1


# ── 1. AusdauerErgebnis.defizite ─────────────────────────────────────────
# AusdauerErgebnis.vo2max und .bewertung sind Properties (aus distanz_m berechnet)
print("\n=== 1. AusdauerErgebnis.defizite ===")

# Gutes Ergebnis für U10/U11 (520 m → VO₂max ≈ 40.8 per IR1-Formel)
# Norm für U10: Durchschnittlich = 32 ml/kg/min → 40.8 > 32 → KEIN Defizit
ae_gut = AusdauerErgebnis(
    distanz_m=520,
    test_typ="IR1",
    altersgruppe="U10/U11",
    geschlecht="Männlich",
)
print(f"    (vo2max={ae_gut.vo2max}, bewertung={ae_gut.bewertung})")
check("520m IR1 U10/U11 → kein Defizit", ae_gut.defizite, [])

# Schlechtes Ergebnis für U10/U11 — unter Norm → Defizit
# U10/U11: Mittel-Grenze = 280m → für "Verbesserungsbedarf" brauchen wir < 280m
ae_schlecht = AusdauerErgebnis(
    distanz_m=160,
    test_typ="IR1",
    altersgruppe="U10/U11",
    geschlecht="Männlich",
)
print(f"    (vo2max={ae_schlecht.vo2max}, bewertung={ae_schlecht.bewertung})")
d = ae_schlecht.defizite
check("160m IR1 U10/U11 Verbesserungsbedarf → mind. 1 Defizit", len(d) >= 1, True)

# Gutes Ergebnis für Senioren (840 m → VO₂max ≈ 43.5 per IR1 — über Norm 46 Sehr gut braucht 53)
# Norm Senioren: Durchschnittlich = 46 → 43.5 < 46 → VO₂max-Defizit
ae_senior_grenz = AusdauerErgebnis(
    distanz_m=840,
    test_typ="IR1",
    altersgruppe="Senioren",
    geschlecht="Männlich",
)
print(f"    (vo2max={ae_senior_grenz.vo2max}, schwelle_senio=46)")
vo2_def_senior = any("Aerobe Kapazität" in x for x in ae_senior_grenz.defizite)
check("840m IR1 Senior (VO₂max≈43.5 < 46) → VO₂max-Defizit", vo2_def_senior, True)

# Senioren: sehr hoher Wert → kein Defizit
ae_senior_gut = AusdauerErgebnis(
    distanz_m=1400,
    test_typ="IR1",
    altersgruppe="Senioren",
    geschlecht="Männlich",
)
print(f"    (vo2max={ae_senior_gut.vo2max})")
check("1400m IR1 Senior → kein VO₂max-Defizit", any("Aerobe Kapazität" in x for x in ae_senior_gut.defizite), False)

# Frau: andere Normen — kein Exception
ae_frau = AusdauerErgebnis(
    distanz_m=360,
    test_typ="IR1",
    altersgruppe="Senioren",
    geschlecht="Weiblich",
)
try:
    _ = ae_frau.defizite
    check("Weibliche Norm: kein Exception", True, True)
except Exception as e:
    check(f"Weibliche Norm: kein Exception ({e})", False, True)


# ── 2. defizite_ermitteln() aus analytics.py ────────────────────────────
print("\n=== 2. defizite_ermitteln() ===")

# 520 m / U10/U11 / bewertung "Gut" (via bewertung_ir1) → kein Ausdauer-Defizit
aus_u11_gut = {
    "distanz_m": 520,
    "vo2max": 40.8,           # gespeicherter VO₂max-Wert
    "bewertung": "Gut",
    "altersgruppe": "U10/U11",
    "datum": "2024-08-01",
}
defizite = defizite_ermitteln(
    None, None, None, None, None, aus_u11_gut, None,
    geschlecht="Männlich",
)
# defizite_ermitteln() gibt dicts mit "modul" (nicht "bereich") == "Ausdauer"
aus_defizite = [d for d in defizite if d["modul"] == "Ausdauer"]
check("520m/40.8 U10/U11 Gut → kein Ausdauer-Defizit", len(aus_defizite), 0)

# Schlechter Wert → Defizit (Verbesserungsbedarf → Yo-Yo-Defizit via modul=Ausdauer)
aus_u11_bad = {
    "distanz_m": 280,
    "vo2max": 38.75,
    "bewertung": "Verbesserungsbedarf",
    "altersgruppe": "U10/U11",
    "datum": "2024-08-01",
}
defizite2 = defizite_ermitteln(
    None, None, None, None, None, aus_u11_bad, None,
    geschlecht="Männlich",
)
aus_defizite2 = [d for d in defizite2 if d["modul"] == "Ausdauer"]
check("280m/38.75 U10/U11 Verbesserungsbedarf → Defizit", len(aus_defizite2) >= 1, True)

# Normwert Senioren = 46: VO₂max 42.5 unter Norm → Defizit (modul=Ausdauer)
aus_senior_bad = {
    "distanz_m": 560,
    "vo2max": 42.5,
    "bewertung": "Mittel",
    "altersgruppe": "Senioren",
    "datum": "2024-08-01",
}
defizite3 = defizite_ermitteln(
    None, None, None, None, None, aus_senior_bad, None,
    geschlecht="Männlich",
)
aus_defizite3 = [d for d in defizite3 if d["modul"] == "Ausdauer"]
check("Senior 42.5 Mittel (unter Norm 46) → Defizit", len(aus_defizite3) >= 1, True)


# ── Ergebnis ─────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Ergebnis: {PASS} PASS  |  {FAIL} FAIL")
if FAIL:
    sys.exit(1)
