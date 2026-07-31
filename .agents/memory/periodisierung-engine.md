---
name: Periodisierung Engine v2
description: Design decisions and gotchas for the new multi-focus training plan engine in periodisierung.py
---

## Rule
`_POOL` tuples are ordered **(uebung, saetze, volumen, haeufigkeit)**. When unpacking in `_woche_eintraege` and `trainingsplan_multi_erstellen`, use `for uebung, saetze, volumen, haeufigkeit in exercises:`. Swapping saetze/uebung causes exercise names to render as "3".

**Why:** Discovered when test output showed exercise names as "3" instead of actual names.

**How to apply:** Any new loop over `_pool_fuer_area()` results must follow this order.

## Key design decisions
- `_pool_fuer_area()` caps `n = min(n, len(exercises))` to avoid in-week duplicates when score > pool size
- 4-week mesocycle load pattern: W1=Akkumulation I, W2=Akkumulation II, W3=Intensivierung, W4=Deload (60% volume)
- Deficit scoring: primary=3, secondary=2, tertiary=1 exercises per area per non-deload week
- Rumpf always included as base (score defaults to 1 minimum)
- Phase rotation: stabilisation pool (W1–4) → kraft pool (W5–8) → power pool (W9–12)
- Supported plan lengths: 4, 6, 8, 12 weeks

## Public API
- `zyklus_erstellen(spieler_id, schwerpunkt_text, wochen=12)` → periodisierung table
- `trainingsplan_multi_erstellen(spieler_id, schwerpunkt_text, wochen=8)` → trainingsplan table  
- `defizit_tabelle(schwerpunkt_text)` → list of dicts for UI display
- `defizit_score(schwerpunkt_text)` → dict[area, score 1–3]
