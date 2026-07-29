---
name: Phase completion status
description: Tracks which implementation phases from the 19-phase overhaul are complete or pending
---

## Done
- Phase 1, 2, 5, 6, 7, 9, 10, 13, 14, 16 — completed in earlier sessions
- Phase 3 — _duplikat_check() helper in app.py; applied to FMS, Y-Balance, Sprint, Sprung, Agilitaet, Ausdauer save blocks
- Phase 4 — Anthropometrie plausibility warnings (future date, Sitzhoehe≥Groesse, Beinlaenge≥Groesse, Armspann outlier, BMI U18 note); Sprint future-date warning
- Phase 8 — beobachtungen_alle_fuer_spieler() in database.py; TRAINERBEOBACHTUNGEN section in pdf_report.py generate_report(); imported in app.py
- Phase 11 — kraft_letzter loaded in page_spieler_profil; kraft_row + beobachtungen params added to generate_report() call; KRAFTDIAGNOSTIK metric_box + section in pdf_report.py; kraft compare section in generate_vergleich_pdf(); kraft tab in page_fortschritt(); kraft columns in export.py
- Phase 12 — "kraft" entry in TEST_DEFS with Bankdruecken + Rumpfkraft table rendering; TEST_REIHENFOLGE includes "kraft"
- Phase 15 — IR2 vo2max returns None in ausdauer.py; IR2 info note shown in page_ausdauer()

## Still open
- Phase 17 — Navigation shortcuts (buttons in spielerprofil to jump directly to test pages; success-buttons after saves)
- Phase 18 — Automated pytest tests (30 cases, separate temp DB)
- Phase 19 — Final report document (sections A–F)

**Why track here:** The plan doc (attached_assets/) has the full spec; this file is just the progress tracker so future sessions don't repeat work.

**How to apply:** Before starting new implementation work, check this file to avoid redoing phases already done.
