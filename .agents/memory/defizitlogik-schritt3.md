---
name: Defizitlogik Schritt-3
description: NO_DATA≠Defizit fix, Basis-Modus, Defizit-Deduplizierung, Plan-Preservation, Datenbasis-Transparenz
---

## Core Rule: NO_DATA ≠ DEFIZIT

The root bug was `defizit_score()` in periodisierung.py calling `scores.setdefault("Rumpf", 1)` unconditionally — this injected "Rumpf" as a deficit even when no test data existed. Fixed by removing the setdefault and returning `{}` for empty input.

## What was changed

### analytics.py
- `defizite_ermitteln()`: dedup key changed from `(bereich, text)` to `bereich` — same area from multiple sources (FMS + Y-Balance) now merges into one entry with `modul = "FMS + Y-Balance"`. Added `datum` and `prioritaet` fields per entry. All guards already correct (`if fms_row:` etc.).
- New `testdaten_uebersicht()`: returns `{test_name: (status, datum)}` — "NO_DATA" or "VALID_DATA" per test — used for transparency display in training page.

### periodisierung.py
- `defizit_score()`: added `if not txt: return {}` at top — returns empty dict for empty schwerpunkt text.
- Removed `scores.setdefault("Rumpf", 1)` — Rumpf is no longer unconditionally added.
- New `_BASIS_MODUS_BEREICHE` constant: age-appropriate balanced pools (U10/U14/U18/Senior/Ü40/Ü55), used when no diagnosis data exists. NOT labeled as deficits.
- `trainingsplan_multi_erstellen()`: after `basis_scores = defizit_score(...)`, if empty → `basis_scores = _BASIS_MODUS_BEREICHE[plangruppe]`. Plan still deleted when button is clicked (correct — only auto-delete is forbidden).

### app.py
- `testdaten_uebersicht` imported from analytics.
- `_plan_modus` variable: "Basis" (no tests) | "Erhaltung" (tests, no deficits) | "Diagnostik" (real deficits).
- `defizite_valide = defizite_ermitteln(...)` computed early; `_anzahl_defizite` = count.
- `schwerpunkt` only set to `ERHALTUNGS_SCHWERPUNKT` in "Erhaltung" mode, NOT in "Basis" mode.
- Mode banner shows correct context per mode; "Erkannte Defizite" only shown in Diagnostik mode from `defizite_valide`.
- "Datenbasis" expander shows all 7 tests with NO_DATA vs VALID_DATA + date.
- §19 hint: tab_view checks if newest diagnosis date > plan max date → shows "Neue Diagnosedaten sind verfügbar" info without deleting the plan.

## Critical constraints
- `defizit_tabelle()` still used for some other views (2635, 3599 in app.py) — these are read-only displays that also benefit from the fixed `defizit_score`.
- Existing plan in DB is NEVER auto-deleted — only when user explicitly clicks "Trainingsplan erstellen".
- `_BASIS_MODUS_BEREICHE` entries must NOT be labeled as "Defizite" in UI — they are "Altersgerechte Athletikbausteine".

**Why:**
SCHRITT-3 spec required clean separation of NO_DATA from real deficits to prevent false deficit display.
