---
name: Age-based diagnostic norms
description: All test modules now use age-specific norm tables (U8–Ü50) from age_norms.py; how the system works and what to be consistent with.
---

## Rule
All bewertung/beurteilung functions in the test modules accept `alter: float | None = None`. When `None`, they fall back to "Senioren" norms (adult defaults). All dataclasses (SprintErgebnis, SprungErgebnis, AgilitaetErgebnis, FMSResult, YBalanceResult) have an `alter: float | None = None` field that is passed through to the underlying functions.

**Why:** User requested age-appropriate norms from U8 to Ü50 based on sports science studies.

## Central module: age_norms.py
Single source of truth for all norm tables. Key exports:
- `alter_zu_normgruppe(alter)` → group key (e.g. "U14", "Senioren", "Ü35")
- `normgruppe_label(alter)` → UI string e.g. "Referenz: U14 (Fußball, Sportwissenschaft)"
- `SPRINT_NORMEN`, `SPRUNG_NORMEN`, `AGIL_NORMEN`, `YB_NORMEN`, `FMS_NORMEN`, `KRAFT_NORMEN`
- `fms_bewertung_alter(score, alter)` → str
- `kraft_bewertung_alter(rel_kraft, alter, geschlecht)` → (stufe, empfehlung)
- `yb_schwellenwert(alter, geschlecht)` → float (composite % threshold)

## Age group mapping
U8 (≤8), U10 (9-10), U12 (11-12), U14 (13-14), U16 (15-16), U18 (17-18), U21 (19-21), Senioren (22-35), Ü35 (36-50), Ü50 (51+)

## How to apply in app.py
For each test page, compute `alter_xxx = berechne_alter(sp.get("geburtsdatum", ""))` and pass `alter=alter_xxx` to the dataclass constructor. The `altersgruppe` (for norm_badge etc.) is computed separately with `alter_zu_altersgruppe()`.

## Scientific references
- Sprint: Rumpf et al. (2016), Meyers et al. (2017)
- CMJ: Bedoya et al. (2015), Moran et al. (2017)
- Agility: Little & Williams (2005), Raya et al. (2013)
- Y-Balance: Plisky et al. (2006/2009), Butler et al. (2012)
- FMS: Cook et al. (2006), Goss et al. (2016 youth)
- Kraft: NSCA Youth Standards, Faigenbaum & Myer (2010)
- Ausdauer: Bangsbo Yo-Yo (already age-integrated in ausdauer.py)
