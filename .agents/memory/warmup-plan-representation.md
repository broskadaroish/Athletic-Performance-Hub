---
name: Warm-up plan representation
description: Shared UI/PDF rules for stored APH and FIFA 11+ warm-ups in training plans.
---

Warm-ups are stored as special existing `trainingsplan` rows rather than in a
new table. Their selection metadata lives in the existing note field, with
`bereich = "Warm-up"`. An explicit “Kein Warm-up” row is distinct from an old
plan without a warm-up row.

**Why:** The editor must preserve plan history and distinguish an intentional
no-warm-up choice from legacy plans. Legacy plans still need the historical APH
standard fallback. UI and PDF must show the same selected programme.

**How to apply:** Keep warm-up rows out of the normal main-exercise grouping and
duration calculation. Use `warmup.py` for every UI/PDF representation. For a
new APH Standard selection, persist the chosen block duration in its metadata;
that persisted duration wins over later plan-level defaults. A legacy fallback
uses the active plan's warm-up duration supplied by the caller.