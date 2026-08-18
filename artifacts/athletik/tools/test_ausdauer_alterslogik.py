"""
tools/test_ausdauer_alterslogik.py
===================================
Testet fussballklasse_zu_yoyo_gruppe() und fussballklasse_aus_datum()
über alle Altersgrenzen (8-19 J.).

Erwartetes Ergebnis: alle PASS, keine FAIL.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ausdauer import fussballklasse_zu_yoyo_gruppe, _FK_ZU_YOYO_GRUPPE
from saison   import fussballklasse_aus_datum

PASS = 0
FAIL = 0

def check(label, got, expected):
    global PASS, FAIL
    if got == expected:
        print(f"  PASS  {label}: {got!r}")
        PASS += 1
    else:
        print(f"  FAIL  {label}: expected {expected!r}, got {got!r}")
        FAIL += 1


# ── 1. Direkte FK-String-Mappings ──────────────────────────────────────────
print("\n=== 1. Direkte FK-String-Mappings ===")
FK_EXPECTED = {
    "U7":      "U8/U9",
    "U8":      "U8/U9",
    "U9":      "U8/U9",
    "U10":     "U10/U11",
    "U11":     "U10/U11",
    "U12":     "U12/U13",
    "U13":     "U12/U13",
    "U14":     "U13/U14",
    "U15":     "U15/U16",
    "U16":     "U15/U16",
    "U17":     "U17/U18",
    "U18":     "U17/U18",
    "A-Junioren": "U17/U18",
    "Senior":     "Senioren",
}
for fk, expected_gruppe in FK_EXPECTED.items():
    got = fussballklasse_zu_yoyo_gruppe(fk, alter=None)
    check(f"FK={fk}", got, expected_gruppe)


# ── 2. Alters-Fallback (kein gültiger FK) ─────────────────────────────────
print("\n=== 2. Alters-Fallback ===")
ALTER_EXPECTED = [
    # (alter, expected)
    (7,  "U8/U9"),
    (8,  "U8/U9"),
    (9,  "U10/U11"),   # Bug in alter_zu_gruppe(): gab U8/U9 → korrigiert
    (10, "U10/U11"),
    (11, "U12/U13"),   # age 11 → U12 → U12/U13 (U-Logik: alter N → U(N+1))
    (12, "U12/U13"),
    (13, "U13/U14"),   # age 13 → U14 → U13/U14
    (14, "U15/U16"),   # age 14 → U15 → U15/U16
    (15, "U15/U16"),
    (16, "U17/U18"),   # age 16 → U17 → U17/U18
    (17, "U17/U18"),
    (18, "Senioren"),
    (25, "Senioren"),
    (40, "Senioren"),
]
for alter, expected in ALTER_EXPECTED:
    got = fussballklasse_zu_yoyo_gruppe(None, alter=alter)
    check(f"alter={alter}", got, expected)


# ── 3. FK + Alter kombiniert: FK hat Vorrang ───────────────────────────────
print("\n=== 3. FK hat Vorrang über Alter ===")
# FK=U14 → U13/U14, egal ob alter=9 wäre
got = fussballklasse_zu_yoyo_gruppe("U14", alter=9)
check("FK=U14, alter=9 → FK hat Vorrang", got, "U13/U14")
# FK=U8 → U8/U9, egal ob alter=14
got = fussballklasse_zu_yoyo_gruppe("U8", alter=14)
check("FK=U8, alter=14 → FK hat Vorrang", got, "U8/U9")
# FK=None → Alter-Fallback
got = fussballklasse_zu_yoyo_gruppe(None, alter=10)
check("FK=None, alter=10 → Alter-Fallback", got, "U10/U11")
# FK='' → Alter-Fallback
got = fussballklasse_zu_yoyo_gruppe("", alter=10)
check("FK='', alter=10 → Alter-Fallback", got, "U10/U11")


# ── 4. Grenzwert-Prüfung aus fussballklasse_aus_datum ─────────────────────
print("\n=== 4. fussballklasse_aus_datum-Konsistenz ===")
from datetime import date
# Ein Spieler mit Geburtstag 2014-01-01 ist am Stichtag 01.08.2024 ein U11-Spieler
import datetime as _dt
gbd_u11 = "01.01.2014"
stichtag_u11 = _dt.date(2024, 8, 1)
fk_result = fussballklasse_aus_datum(gbd_u11, stichtag=stichtag_u11)
# Er ist Jahrgang 2014, also FK = U11 (Saison 24/25)
check("JG 2014 am 01.08.2024", fk_result, "U11")
yoyo_result = fussballklasse_zu_yoyo_gruppe(fk_result, alter=10)
check("U11 → Testreferenz U10/U11", yoyo_result, "U10/U11")


# ── 5. Robustheit: ungültige Eingaben ──────────────────────────────────────
print("\n=== 5. Robustheit ===")
got = fussballklasse_zu_yoyo_gruppe("Unbekannt", alter=None)
check("unbekannte FK ohne Alter → Senioren", got, "Senioren")
got = fussballklasse_zu_yoyo_gruppe(None, alter=None)
check("None/None → Senioren", got, "Senioren")
got = fussballklasse_zu_yoyo_gruppe(None, alter=0)
check("alter=0 → U8/U9", got, "U8/U9")


# ── Ergebnis ───────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Ergebnis: {PASS} PASS  |  {FAIL} FAIL")
if FAIL:
    sys.exit(1)
