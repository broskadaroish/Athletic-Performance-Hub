"""
Periodization engine — generates a 12-week training cycle split into:
  Phase 1 (Weeks 1–4):  Stabilisation & Movement Quality
  Phase 2 (Weeks 5–8):  Strength & Power Development
  Phase 3 (Weeks 9–12): Football-Specific Performance
"""

from database import periodisierung_loeschen, periodisierung_bulk_insert, periodisierung_laden

# ─── Phase templates ──────────────────────────────────────────────────────

_PHASE1 = [
    ("Sprunggelenk", "Knie zur Wand Mobilisation",  "leicht", "3×10 je Seite",   "3×/Woche"),
    ("Hüfte",        "Seitliches Miniband Gehen",   "leicht", "3×12 Meter",      "3×/Woche"),
    ("Rumpf",        "Dead Bug",                     "leicht", "3×8 je Seite",    "3×/Woche"),
    ("Rumpf",        "Pallof Press",                 "leicht", "3×12",            "3×/Woche"),
    ("Hüfte",        "90/90 Hüftrotation",           "leicht", "3×10",            "2×/Woche"),
]

_PHASE2 = [
    ("Hüfte",        "Einbeinige Hüftbrücke",        "mittel", "3×10 je Seite",  "3×/Woche"),
    ("Knie",         "Step Down",                    "mittel", "3×8 je Seite",   "2×/Woche"),
    ("Oberschenkel", "Nordic Hamstring Curl",         "hoch",  "3×6",             "2×/Woche"),
    ("Knie",         "Single Leg Squat",              "mittel","3×8 je Seite",   "2×/Woche"),
    ("Explosivität", "Squat Jump",                   "mittel", "3×6",             "2×/Woche"),
]

_PHASE3 = [
    ("Fußball",      "Deceleration Drill",            "hoch",  "5 Durchgänge",   "1×/Woche"),
    ("Schnelligkeit","10 m Sprintstarts",             "hoch",  "6×10 m",          "2×/Woche"),
    ("Agilität",     "5-10-5 Shuttle Run",            "hoch",  "5 Durchgänge",   "1×/Woche"),
    ("Fußball",      "Repeated Sprint Ability",       "maximal","6×30 m",         "1×/Woche"),
    ("Explosivität", "Hürdensprünge",                "hoch",   "3×5",             "1×/Woche"),
]


def _build_plan(prioritaeten: list[str]) -> list[dict]:
    plan = []

    # Weigh priority areas by adding them first / repeating in phases
    priority_map = {
        "knie":         "Knie",
        "hüfte":        "Hüfte",
        "huft":         "Hüfte",
        "becken":       "Rumpf",
        "rumpf":        "Rumpf",
        "core":         "Rumpf",
        "sprunggelenk": "Sprunggelenk",
        "stabilitätstraining": "Rumpf",
    }

    def _entries(phase_exercises, woche, phase_name, ziel):
        for bereich, uebung, intensitaet, volumen, haeufigkeit in phase_exercises:
            plan.append({
                "woche": woche,
                "phase": phase_name,
                "ziel": ziel,
                "bereich": bereich,
                "uebung": uebung,
                "intensitaet": intensitaet,
                "volumen": volumen,
                "haeufigkeit": haeufigkeit,
            })

    for woche in range(1, 5):
        _entries(_PHASE1, woche, "Phase 1 — Stabilisation", "Bewegungsqualität & Verletzungsprävention")

    for woche in range(5, 9):
        _entries(_PHASE2, woche, "Phase 2 — Kraftaufbau", "Maximalkraft & funktionelle Stärke")

    for woche in range(9, 13):
        _entries(_PHASE3, woche, "Phase 3 — Fußballspezifisch", "Leistung & Wettkampfvorbereitung")

    return plan


def zyklus_erstellen(spieler_id: int, schwerpunkt_text: str) -> list[dict]:
    """
    Generate and persist a full 12-week periodised plan.
    Returns the full plan as a list of dicts.
    """
    text = schwerpunkt_text.lower()
    prioritaeten = [v for k, v in {
        "knie": "Knie", "hüfte": "Hüfte", "huft": "Hüfte",
        "becken": "Rumpf", "rumpf": "Rumpf", "core": "Rumpf",
        "sprunggelenk": "Sprunggelenk",
    }.items() if k in text]

    plan = _build_plan(prioritaeten)

    periodisierung_loeschen(spieler_id)
    periodisierung_bulk_insert(spieler_id, plan)

    return plan


def zyklus_laden(spieler_id: int) -> list:
    return periodisierung_laden(spieler_id)
