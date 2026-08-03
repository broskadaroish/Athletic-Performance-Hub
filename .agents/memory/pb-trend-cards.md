---
name: PB trend cards helper
description: _pb_trend_cards() helper in app.py — how to use it in Verlauf tabs across all modules
---

## Rule
Every module's Verlauf tab should call `_pb_trend_cards(df, metrics)` immediately after the DataFrame columns are set.

## How to apply
```python
_pb_trend_cards(df, [
    ("col_name", "Display Label", "unit", lower_is_better_bool),
])
```
- `lower_is_better=True` for times (Sprint, Agility)
- `lower_is_better=False` for scores, heights, distances
- unit strings: `"s"`, `"%"`, `"cm"`, `"kg"`, `"m"`, `"ml/kg/min"`, `"Punkte"`, `""`

## Status (all modules)
- ✅ FMS: Gesamtscore (Punkte, higher=better)
- ✅ Y-Balance: Composite R + L (%, higher=better)  
- ✅ Sprint: 5m, 10m, 20m, 30m, 40m (s, lower=better)
- ✅ Sprung: CMJ, Squat Jump, RSI, Standweit (cm/"", higher=better)
- ✅ Agility: 505R/L, T-Test, Illinois, 5-10-5 (s, lower=better)
- ✅ Ausdauer: Distanz (m), VO₂max (ml/kg/min), higher=better
- ✅ Kraft: Direkt 1RM, Epley 1RM, Ventral, Dorsal (kg/s, higher=better)
- ❌ Spiro: not yet added (spiro history structure needs checking first)
- ❌ Anthropometrie: body composition PB not added (no meaningful single PB)

**Why:** Users requested Personal Best visibility — the helper is reusable across all modules and automatically shows trend vs. previous test.
