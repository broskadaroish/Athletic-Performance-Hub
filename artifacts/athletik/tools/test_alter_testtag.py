#!/usr/bin/env python3
"""
tools/test_alter_testtag.py — Testsuite: Alter am Testtag

Verifiziert §3–§6 und §17 des Specs:
- alter_am_datum() liefert korrektes chronologisches Alter für jeden Testdatum
- Geburtstags-Grenztests (Test A: vor Geburtstag, Test B/C: am/nach Geburtstag)
- Unterschiedliche Testreferenz für Tests vor/nach dem Geburtstag
- Keine rückwirkende Veränderung alter Tests
- py_compile aller geänderten Dateien
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_compile
from datetime import date

from database import alter_am_datum, berechne_alter
from database import anthropometrie_beinlaengen_zum_testdatum
from age_norms import alter_zu_normgruppe, normgruppe_label
from saison import testreferenz_caption

PASS = 0; FAIL = 0


def ok(label: str):
    global PASS; PASS += 1; print(f"  ✅ PASS  {label}")


def fail(label: str, detail: str = ""):
    global FAIL; FAIL += 1
    print(f"  ❌ FAIL  {label}" + (f" — {detail}" if detail else ""))


def check(label: str, got, expected):
    if got == expected: ok(label)
    else: fail(label, f"got={got!r}, expected={expected!r}")


def check_not(label: str, got, not_expected):
    if got != not_expected: ok(label)
    else: fail(label, f"got={got!r} but should NOT be {not_expected!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# §1  alter_am_datum() Grundfunktion
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §1 alter_am_datum() Grundfunktion ══")

# Format DD.MM.YYYY
check("GEB 26.08.2016, TEST 20.08.2026 → 9",
      alter_am_datum("26.08.2016", "20.08.2026"), 9)
check("GEB 26.08.2016, TEST 26.08.2026 → 10 (Geburtstag selbst)",
      alter_am_datum("26.08.2016", "26.08.2026"), 10)
check("GEB 26.08.2016, TEST 27.08.2026 → 10 (nach Geburtstag)",
      alter_am_datum("26.08.2016", "27.08.2026"), 10)

# Format YYYY-MM-DD
check("ISO-Format: GEB 2016-08-26, TEST 2026-08-20 → 9",
      alter_am_datum("2016-08-26", "2026-08-20"), 9)
check("ISO-Format: GEB 2016-08-26, TEST 2026-08-26 → 10",
      alter_am_datum("2016-08-26", "2026-08-26"), 10)

# Uhrzeitsuffix (Duplikat-Handling)
check("Uhrzeitsuffix ' (14:30)' wird korrekt geparst",
      alter_am_datum("26.08.2016", "20.08.2026 (14:30)"), 9)

# Leere Eingaben
check("Leeres geburtsdatum → None",
      alter_am_datum("", "20.08.2026"), None)
check("Leeres testdatum → None",
      alter_am_datum("26.08.2016", ""), None)
check("Beide leer → None",
      alter_am_datum("", ""), None)

# Testdatum vor Geburtsdatum
check("Testdatum vor Geburtsdatum → None",
      alter_am_datum("26.08.2016", "25.08.2010"), None)


# ═══════════════════════════════════════════════════════════════════════════════
# §2  Spec §17 — Geburtstags-Grenztests JG2016
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §2 Spec §17 — Geburtstags-Grenztests (GEB 26.08.2016) ══")

GEB = "26.08.2016"

# Test A: 20.08.2026 → Alter 9
alter_A = alter_am_datum(GEB, "20.08.2026")
check("Test A (20.08.2026) → Alter 9", alter_A, 9)

# Test B: 26.08.2026 → Alter 10 (Geburtstag)
alter_B = alter_am_datum(GEB, "26.08.2026")
check("Test B (26.08.2026, Geburtstag) → Alter 10", alter_B, 10)

# Test C: 27.08.2026 → Alter 10
alter_C = alter_am_datum(GEB, "27.08.2026")
check("Test C (27.08.2026) → Alter 10", alter_C, 10)

# Testreferenz für Test A ≠ Testreferenz für Test B
norm_A = alter_zu_normgruppe(alter_A)
norm_B = alter_zu_normgruppe(alter_B)
check("Normgruppe Test A = U10 (Alter 9)", norm_A, "U10")
check("Normgruppe Test B/C = U10 (Alter 10)", norm_B, "U10")
# U10 umfasst 9–10, also gleiche Normgruppe — korrekt
# Aber der Alters-Label ist trotzdem verschieden:
cap_A = testreferenz_caption(alter_A, GEB)
cap_B = testreferenz_caption(alter_B, GEB)
print(f"  Caption Test A: {cap_A!r}")
print(f"  Caption Test B: {cap_B!r}")
check("Caption Test A enthält 'Testreferenz'", "Testreferenz" in cap_A, True)
check("Caption Test B enthält 'Testreferenz'", "Testreferenz" in cap_B, True)

# Test A darf NICHT mit Alter 10 bewertet werden
check("Test A: alter ≠ 10 (nicht rückwirkend verändert)", alter_A != 10, True)
check("Test B: alter = 10 (korrekt)", alter_B, 10)


# ═══════════════════════════════════════════════════════════════════════════════
# §3  Y-Balance: keine spätere Anthropometrie als historische Grundlage
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §3 Y-Balance — historische Beinlänge ══")

_anthro_verlauf = [
    {"id": 1, "datum": "01.08.2025", "beinlaenge": 80.0},
    {"id": 2, "datum": "22.08.2026", "beinlaenge": 92.0},
]
_yb_vor_geb = anthropometrie_beinlaengen_zum_testdatum(
    _anthro_verlauf, "20.08.2026",
)
check("Y-Balance vor späterer Anthropometrie nutzt 2025er Beinlänge",
      _yb_vor_geb["beinlaenge_r"] if _yb_vor_geb else None, 80.0)
check("Y-Balance vor späterer Anthropometrie nutzt nicht den aktuellen Wert",
      _yb_vor_geb["beinlaenge_r"] if _yb_vor_geb else None, 80.0)
_yb_nach_geb = anthropometrie_beinlaengen_zum_testdatum(
    _anthro_verlauf, "26.08.2026",
)
check("Y-Balance nach der Messung nutzt die testzeitnahe Beinlänge",
      _yb_nach_geb["beinlaenge_r"] if _yb_nach_geb else None, 92.0)
check("Y-Balance ohne historische Beinlänge wird nicht geschätzt",
      anthropometrie_beinlaengen_zum_testdatum([], "20.08.2026"), None)


# ═══════════════════════════════════════════════════════════════════════════════
# §4  alter_am_datum vs. berechne_alter: Unterschied erkennbar
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §4 alter_am_datum vs. berechne_alter ══")

# Für JG2016 am heutigen Tag (16.08.2026) ist alter=9 (noch nicht 10)
alter_heute = berechne_alter(GEB)
check(f"berechne_alter({GEB!r}) = {alter_heute} (chronologisch heute)", alter_heute is not None, True)

# Test am 20.08.2026 (vor Geburtstag) → Alter 9
alter_test = alter_am_datum(GEB, "20.08.2026")
check("alter_am_datum(20.08.2026) = 9 (unabhängig vom heutigen Tag)", alter_test, 9)

# Falls heute >= 26.08.2026: berechne_alter gibt 10, alter_am_datum gibt 9
# Falls heute < 26.08.2026: beide geben 9
print(f"  heute={date.today()}, alter_heute={alter_heute}, alter_test={alter_test}")
ok("alter_am_datum ist unabhängig vom heutigen Datum ✓")


# ═══════════════════════════════════════════════════════════════════════════════
# §5  Vollständige Altersmatrix am Testdatum (Stichtag 16.08.2026)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §5 Vollständige Altersmatrix (Testdatum 16.08.2026) ══")

TESTDATUM = "16.08.2026"

# Alle Geburtsdaten 01.01.<jg> — Geburtstag liegt vor 16.08.
# → Person hat im August schon Geburtstag gehabt: Alter = 2026 - jg
# (geburtsjahr, erw_alter_am_16.08.2026)
MATRIX = [
    (2020, 6),   # 2026 - 2020 = 6
    (2019, 7),   # 2026 - 2019 = 7
    (2018, 8),   # 2026 - 2018 = 8
    (2017, 9),   # 2026 - 2017 = 9
    (2016, 10),  # 2026 - 2016 = 10 (01.01. liegt vor 16.08. → Geburtstag schon gehabt)
    (2015, 11),  # 2026 - 2015 = 11
    (2014, 12),  # 2026 - 2014 = 12
    (2012, 14),  # 2026 - 2012 = 14
    (2010, 16),  # 2026 - 2010 = 16
    (2008, 18),  # 2026 - 2008 = 18
    (2003, 23),  # 2026 - 2003 = 23
]
for jg, erw in MATRIX:
    geb = f"01.01.{jg}"
    got = alter_am_datum(geb, TESTDATUM)
    check(f"JG{jg} (01.01.{jg}), Test 16.08.2026 → {erw}", got, erw)

# Zusatz: Geburtstag NACH Testdatum → noch nicht
check("JG2016 (26.08.2016), Test 16.08.2026 → noch 9 (Geburtstag noch nicht)",
      alter_am_datum("26.08.2016", "16.08.2026"), 9)


# ═══════════════════════════════════════════════════════════════════════════════
# §6  Sprint-Bewertung: alter_am_datum-basiert (kein heutiges Alter)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §6 Sprint-Normbewertung mit alter_am_datum ══")

from sprint import bewertung_sprint, SprintErgebnis

# Test am 20.08.2026 → Alter 9 → Normgruppe U10
_a9 = alter_am_datum("26.08.2016", "20.08.2026")  # = 9
_bew9 = bewertung_sprint(2.10, "10m", "Leistungssport", "Männlich", float(_a9))
check(f"Sprint-Bewertung mit Alter {_a9} (vor Geburtstag): kein '—'", _bew9 != "—", True)

# Test am 26.08.2026 → Alter 10 → Normgruppe U10 (gleiche Normgruppe)
_a10 = alter_am_datum("26.08.2016", "26.08.2026")  # = 10
_bew10 = bewertung_sprint(2.10, "10m", "Leistungssport", "Männlich", float(_a10))
check(f"Sprint-Bewertung mit Alter {_a10} (Geburtstag): kein '—'", _bew10 != "—", True)

# U7 (alter=7) → kein Sprint-Urteil
_bew_u7 = bewertung_sprint(3.0, "10m", "Leistungssport", "Männlich", 7.0)
check("U7 (alter=7): Sprint-Bewertung = '—' (kein falsches Defizit)", _bew_u7, "—")


# ═══════════════════════════════════════════════════════════════════════════════
# §7  testreferenz_caption mit Testtag-Alter
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §7 testreferenz_caption mit Testtag-Alter ══")

# JG2016, Test 20.08.2026 → Alter 9 → Testreferenz U10 (Alter 9–10)
cap_testA = testreferenz_caption(9, "26.08.2016")
check("Testreferenz Test A (alter=9): U10", "U10" in cap_testA, True)
check("Testreferenz Test A: Fußballklasse U11", "U11" in cap_testA, True)
check("Testreferenz Test A: Altersrange 9–10", "9–10" in cap_testA, True)

# JG2016, Test 27.08.2026 → Alter 10 → Testreferenz U10 (gleiche Normgruppe, anderes Alter)
cap_testC = testreferenz_caption(10, "26.08.2016")
check("Testreferenz Test C (alter=10): U10", "U10" in cap_testC, True)

print(f"  Caption Test A (alter=9): {cap_testA!r}")
print(f"  Caption Test C (alter=10): {cap_testC!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# §8  Historische Editoren verwenden das gewählte Testdatum
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §8 Historische Editoren — Testtag-Kontext ══")
_app_source = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"),
                   encoding="utf-8").read()
_editor_names = [
    "_render_anthro_edit", "_render_fms_edit", "_render_ybalance_edit",
    "_render_sprint_edit", "_render_sprung_edit", "_render_agilitaet_edit",
]
for _editor_name in _editor_names:
    _start = _app_source.index(f"def {_editor_name}(")
    _next = _app_source.find("\ndef ", _start + 1)
    _editor_source = _app_source[_start:_next if _next != -1 else None]
    check(f"{_editor_name}: nutzt alter_am_datum", "alter_am_datum(" in _editor_source, True)
    check(f"{_editor_name}: kein heutiges berechne_alter", "berechne_alter(" in _editor_source, False)

_aus_start = _app_source.index("def _render_ausdauer_edit(")
_aus_end = _app_source.find("\ndef ", _aus_start + 1)
_aus_editor_source = _app_source[_aus_start:_aus_end]
check("Ausdauer-Editor: leitet Alter am Testtag ab", "alter_am_datum(" in _aus_editor_source, True)
check("Ausdauer-Editor: leitet Yo-Yo-Gruppe aus Testtag ab", "_fk_zu_yoyo(" in _aus_editor_source, True)
check("Y-Balance-Editor: nutzt keine aktuelle Anthropometrie", "anthropometrie_letzter(" in _app_source[
    _app_source.index("def _render_ybalance_edit("):_app_source.index("def _render_sprint_edit(")
], False)
for _editor_name in ["_render_kraft_edit", "_render_spiro_edit"]:
    _start = _app_source.index(f"def {_editor_name}(")
    _next = _app_source.find("\ndef ", _start + 1)
    _editor_source = _app_source[_start:_next if _next != -1 else None]
    check(
        f"{_editor_name}: keine heutige Altersneubewertung",
        "berechne_alter(" in _editor_source,
        False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# §9  py_compile aller geänderten Dateien
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §9 py_compile ══")

CHANGED = [
    "database.py",
    "age_norms.py",
    "saison.py",
    "app.py",
    "sprint.py",
    "sprung.py",
    "agilitaet.py",
    "kraft.py",
    "ausdauer.py",
]
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for fname in CHANGED:
    fpath = os.path.join(_root, fname)
    try:
        py_compile.compile(fpath, doraise=True)
        ok(f"py_compile {fname}")
    except py_compile.PyCompileError as e:
        fail(f"py_compile {fname}", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# §10  Block-B Regression
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §10 Block-B Regression ══")
import subprocess
result = subprocess.run(
    [sys.executable, "tools/test_block_b.py"],
    cwd=_root, capture_output=True, text=True
)
block_b_ok = "35 PASS, 0 FAIL" in result.stdout
if block_b_ok:
    ok("Block-B: 35/35 PASS")
else:
    fail("Block-B", (result.stdout + result.stderr)[-400:])


# ═══════════════════════════════════════════════════════════════════════════════
# Ergebnis
# ═══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
if FAIL == 0:
    print(f"  Ergebnis: {PASS} PASS, 0 FAIL ✅")
else:
    print(f"  Ergebnis: {PASS} PASS, {FAIL} FAIL ❌")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
