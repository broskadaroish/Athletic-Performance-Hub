---
name: Trainingsplan Schritt-4
description: Versioned training plans, Zeitbudget time-budget cap, per-exercise interactive editing in tab_view
---

# Trainingsplan Versionierung + Bearbeitung (SCHRITT 4)

## Rule
All training plans are versioned through `trainingsplan_versionen` table. The generator (`trainingsplan_multi_erstellen`) no longer deletes old plans — the caller (app.py tab_auto) archives the current active version first, then creates a new version and passes `plan_id` + `trainingszeit_min` to the generator.

**Why:** Protects against accidental overwrites; gives trainers a browseable history; enables duplicate-and-edit workflow without losing the original.

**How to apply:**
- Never call `trainingsplan_loeschen()` from the generator or directly when creating a new plan
- Always call `plan_version_archivieren_aktiv(sid)` → `plan_version_erstellen(...)` → `trainingsplan_multi_erstellen(..., plan_id=_new_pid)` in that order
- `tab_view` loads via `plan_aktive_version(sid)` + `plan_laden_nach_version(vid)`, never `trainingsplan_laden(sid)` directly

## Zeitbudget
`_ZEITBUDGET_CONFIG` in periodisierung.py maps {20, 30, 45, 60, 75, 90} → `{max_ueb_tag, satz_cap, warmup_min, cooldown_min}`.
- `max_ueb_tag` caps exercises per training day at generator level
- `satz_cap` applies as `min(philosophie_satz_cap, _zb_eff_satz)` — lower bound wins
- Duration estimate shown in tab_view per training day with ⚠️ if >10 min over budget

## Per-Exercise Editing
tab_view uses session_state flags `tv_edit_{eid}`, `tv_del_{eid}`, `tv_swap_{eid}` for inline forms.
- Edit: `plan_eintrag_aktualisieren(eid, ...)` 
- Delete: `plan_eintrag_loeschen(eid)`
- Swap: selectbox from `_POOL[bereich]` pool, then `plan_eintrag_aktualisieren(eid, uebung=..., bereich=...)`
- Reorder: `plan_eintraege_position_tauschen(eid1, eid2)` between adjacent entries in same bereich×tag

## Plan Actions
- "Plan duplizieren" → `plan_duplizieren(sid, vid, datum, username)` — archives current, copies all exercises to new version
- "Als neue Version speichern" → same as duplizieren (snapshot before further edits)
- "Neue Diagnosedaten" banner shows 3 buttons: Behalten / Plan anpassen (duplizieren) / Neuen Plan erstellen

## DB Functions added (database.py)
`plan_version_erstellen`, `plan_version_archivieren_aktiv`, `plan_aktive_version`, `plan_aktive_version_id`,
`plan_versionen_laden`, `plan_laden_nach_version`, `plan_eintrag_loeschen`, `plan_eintrag_aktualisieren`,
`plan_eintraege_position_tauschen`, `plan_notizen_speichern`, `plan_trainingszeit_setzen`, `plan_duplizieren`
