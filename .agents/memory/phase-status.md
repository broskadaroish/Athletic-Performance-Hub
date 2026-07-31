---
name: Phase completion status
description: Which implementation phases are done; tracks what remains open
---

## Completed Phases (0–16 + 0C)

- Phases 0–16: all done (established functionality)
- Phase 17, 18, 19: open (not started)
- **Phase 0C: DONE (2026-07-31)**

## Phase 0C — What was implemented

### Sprint
- 40m Distanz: DB-Migration (`_migrate_db` → sprint_test.v1_40m/v2_40m/v3_40m/beste_40m)
- `sprint_speichern()` updated with optional v1_40/v2_40/v3_40/b40 params
- `sprint_history()` updated with `COALESCE(beste_40m,0) as beste_40m`
- UI: 40m input via `_sprint_eingabe` in tab_neu, plausibility check, 40m in metrics row
- UI: "Letzter Test" expander in tab_verlauf (shows all distances)
- UI: "Zwei Termine vergleichen" expander in tab_verlauf

### Kraft
- "Letzter Test" expander in tab_verlauf (shows 1RM, Rumpfkraft, Asymmetrie)
- "Zwei Termine vergleichen" expander in tab_verlauf

### Agility — 5 neue Tests
- New DB columns added via `_migrate_db`: modified_t_test, pro_agility, arrowhead_r/l, zigzag, balsom + 3 attempt cols each
- `agilitaet_speichern()` extended with new optional test params
- `agilitaet_history()` extended with COALESCE for new columns (14 columns total)
- UI: multiselect "Tests für diese Sitzung aktivieren" at top of tab_neu (session-state only)
- UI: new test inputs (with 3-attempt _v3_agil helper) shown conditionally
- UI: arrowhead R/L asymmetrie badge
- UI: "weitere Tests" section header when any new test selected
- UI: Verlauf chart includes all 11 time series (+ 5 new)
- UI: "Letzter Test" expander in Verlauf
- UI: "Zwei Termine vergleichen" expander in Verlauf
- UI: tab_info updated with 9-row table including all tests

### SVG files created (assets/tests/agility/)
- modified_t_test.svg, pro_agility.svg, arrowhead.svg, zigzag.svg, balsom.svg

## Open Phase 0C items (minor)
- New agility tests have no norm values (no AgilitaetErgebnis rating) — by design (calculation logic frozen)
- 40m sprint has no norm values — by design
- Agility test activation is session-state only (not persisted to DB) — by design for now
