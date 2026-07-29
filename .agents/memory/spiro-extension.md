---
name: Spiroergometrie extension
description: Architecture and key constraints for the Spiro Stufentest feature added to the Ausdauer section.
---

# Spiroergometrie-Stufentest Extension

## What was built
Full Spiroergometrie-Stufentest feature integrated into `page_ausdauer()`.

## Key architecture decisions

**Why:** The spec required the Yo-Yo code to remain 100% untouched while adding a full Stufentest alongside it.

**How to apply:**
- `page_ausdauer()` shows a top-level `st.radio` selector (Yo-Yo / Spiro). If Spiro chosen → calls `_page_spiro()` and returns.
- All spiro logic lives in `_page_spiro()` (inserted just before `page_ausdauer()` at ~line 2640 in app.py).
- `spiro.py` — pure calculation module (interpolation, Kurvenverschiebung, Protokollvergleich, Schwellenvergleich).
- 4 new DB tables added to `init_db()` in `database.py`: `spiro_protokoll`, `spiro_test`, `spiro_stufe`, `spiro_nachbelastung`.

## Laktat safety constraint
A prominent warning is shown whenever `mit_laktat=True` — do not remove it. Spec required it.

## VO₂max vs VO₂peak
The UI explicitly warns that VO₂max is only valid with documented exhaustion criteria. `vo2_peak` and `vo2_max` are separate fields in `spiro_test`.

## Laktat 0 → None rule
Zero lactate is treated as "not measured" and stored as NULL — not 0. Applied in both save code and plausibility check.

## Interpolation: no extrapolation
`interpoliere_bei_laktat()` in `spiro.py` returns None for values outside the measured range. This is intentional — the spec required no extrapolation.

## Diagnostik-Übersicht tile
Added "🔬 Stufentest" as 8th tile in `page_diagnostik_overview()`. Grid changed from 4+3 to 4+4. The tile's `sub` key points to `"🫁 Ausdauer (Yo-Yo)"` (opens Ausdauer page — user selects Spiro from selector).

## What was deferred
- PDF/export integration for Spiro results
- Print protocol (Testprotokoll) for Stufentest paper form
- Export.py Spiro history columns
- Mannschaft view Spiro warnings
