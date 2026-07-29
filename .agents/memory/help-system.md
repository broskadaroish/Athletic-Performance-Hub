---
name: Help system architecture
description: How test instructions, SVG sketches, and info buttons are structured across the Football Athletik app
---

## Structure

- **`test_help.py`** — central dict `TEST_HELP` keyed by `test_id`. Each entry has: `name`, `kurzbeschreibung`, `ziel`, `material`, `aufbau`, `aufwaermung`, `durchfuehrung`, `trainerhinweis`, `versuche`, `pause`, `messwert`, `einheit`, `gueltiger_versuch`, `ungueltiger_versuch`, `fehler` (list), `sicherheit`, `bild_pfad`, `quelle`, `version`, `datum`, `felder` (dict of field dicts).
- **`help_ui.py`** — four UI helper functions consumed by all pages:
  - `sicherheitshinweis_box()` — yellow warning box (shown on all test pages)
  - `show_test_info(test_id)` — collapsible expander with SVG sketch + full protocol
  - `show_field_help(test_id, field_id)` — returns tooltip string for `help=` on number_input
  - `field_info_col(col, test_id, field_id)` — renders ℹ️ popover button in a column
- **SVG sketches** — stored under `assets/tests/<test_id>/`. All use dark theme (#161b22 background, system-ui font).

## Active test IDs
| test_id | Page function | SVG path |
|---|---|---|
| sprint | page_sprint() | assets/tests/sprint/sprint_setup.svg |
| y_balance | page_ybalance() | assets/tests/y_balance/ybalance_setup.svg |
| fms | page_fms() | assets/tests/fms/fms_overview.svg |
| jump | page_sprung() | assets/tests/jump/cmj_setup.svg |
| agility | page_agilitaet() | assets/tests/agility/test_505.svg |
| yoyo | page_ausdauer() | assets/tests/yoyo/yoyo_setup.svg |
| anthropometrie | page_anthropometrie() | assets/tests/anthropometrie/anthro_punkte.svg |

## Integration pattern for each page
1. `sicherheitshinweis_box()` immediately after page header markdown (except Anthropometrie — no safety gate needed)
2. `show_test_info(test_id)` after sicherheitshinweis, before player selector
3. `help=show_field_help(test_id, field_id)` on every number_input
4. `field_info_col(col, test_id, field_id)` for ℹ️ icon next to field headers (used in Sprint, Sprung, Agility)

**Why:** Keeps all protocol text maintainable in one file rather than scattered across 7+ page functions.
