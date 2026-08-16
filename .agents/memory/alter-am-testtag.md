---
name: Alter am Testtag
description: alter_am_datum() in database.py; Testbefund vs. Belastungssteuerung vs. Fußballklasse klar getrennt
---

## Regel

**TESTBEFUND** (Bewertung, Defizite, Testreferenz-Caption) → `alter_am_datum(geb, testdatum)`
**BELASTUNGSSTEUERUNG** (Trainingsplan, Periodisierung) → `berechne_alter(geb)` [= heute]
**FUSSBALLKLASSE** → `fussballklasse_berechnen(geb, stichtag)` [saisonbasiert]

**Why:** Ein Test am 20.08.2026 für JG2016 (GEB 26.08.2016) muss dauerhaft `alter=9` erhalten,
auch wenn die Person 6 Tage später Geburtstag hat. Ohne Testtag-Bezug würde nach dem
Geburtstag dasselbe Testergebnis mit Alter 10 neu bewertet → falsche Norm.

## Implementierung

`database.py`:
- `alter_am_datum(geburtsdatum_str, testdatum_str) -> int | None`
- Robuste Parsing: DD.MM.YYYY + YYYY-MM-DD + Uhrzeitsuffix " (HH:MM)" abschneiden
- Gibt None bei leerem Datum, Fehler, oder Testdatum < Geburtsdatum

`app.py` — tab_neu jedes Testmoduls (nach datum-Widget):
- Sprint:    `alter_sprint_td = alter_am_datum(...) or alter_sprint`
- Sprung:    `alter_sprung_td = alter_am_datum(...) or alter_sprung`
- Agilität: `alter_agil_td   = alter_am_datum(...) or alter_agil`
- Kraft:     `alter_td        = alter_am_datum(...) or alter`
- Ausdauer:  `_alter_aus_td   = alter_am_datum(...) or alter` (für Selectbox-Default)

FMS, Y-Balance, Anthropometrie, Spiro → kein Altersnorm-Konstrukt → kein _td nötig.

Sprint Verlauf "Letzter Test": Testreferenz-Caption ebenfalls aus `alter_am_datum(geb, lt["datum"])`.

## Testsuite
`tools/test_alter_testtag.py` — 51 PASS / 0 FAIL
Inkl. §17 Geburtstags-Grenztests: 20.08/26.08/27.08.2026 für GEB 26.08.2016.
