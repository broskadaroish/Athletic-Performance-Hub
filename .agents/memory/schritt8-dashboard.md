---
name: SCHRITT 8 Dashboard Trainer
description: Redesign of _dash_trainer in modules/saas_dashboard.py; new helper functions; structure decisions.
---

## What changed

`modules/saas_dashboard.py` — replaced lines 613–830 (old _dash_trainer + old trainer section) with new helper functions + new _dash_trainer:

New helper functions added (in order, before _dash_trainer):
- `_trainer_greeting(vorname)` — compact greeting, no divider
- `_trainer_leer(trainer_id)` — empty-state onboarding card for 0-player accounts
- `_compute_team_score(alle_spieler)` → tuple(avg_score, high_risk, n_scored) — same logic as before, max 12 sample
- `_trainer_kpi_strip(n_spieler, faellig, high_risk, verletz, diag_monat)` — single-row compact KPIs; verletz only shown if >0
- `_trainer_score_card(avg_score, data_ok, n_scored)` — progress bar card with color-coded label
- `_trainer_handlung(faellig, high_risk, verletz)` — Handlungsbedarf card + action buttons
- `_trainer_schnellaktionen()` — 4 compact buttons (no decorative icon tiles)
- `_trainer_letzte_spieler(trainer_id)` — max 3 players, compact cards, athletikscore per player

## Key decisions

**Why removed decorative icon tiles for Schnellaktionen:**
The old design had large icon+button pairs (double height). Replaced with plain st.button in 4 columns — faster on mobile, less scrolling.

**Why fällige Tests shown as count only (not list):**
`dashboard_trainer_ohne_test()` returns only a count, not a list of specific tests/players. A namentliche List requires a new DB function (→ Task #192). SCHRITT 8 spec §32 says "keine zusätzlichen Dauerqueries" so we kept the existing query.

**Why Vereinsadmin/_dash_superadmin NOT changed:**
Spec §30: "Superadmin-Dashboard weiterhin getrennt behandeln". Vereinsadmin redesign proposed as follow-up Task #191.

**Navigation from "letzte Spieler":**
Sets global_player_id + _nav_goto="👤  Spieler" + nav_sub_spieler="🏃 Profil & Diagnostik" + st.rerun() — same pattern as Mannschaft page at app.py:1403-1405.

## No backend/DB/score changes
Score logic: identical to old code (same athletik_score() calls, same risiko_score() calls). No new DB functions. No price/license/session changes.
