"""
Periodization engine v2 — Multi-focus, deficit-driven, scientifically structured.

Sports-science design:
  • Every week has exercises from MULTIPLE training areas
    (primary deficit → secondary deficit → base stability)
  • 4-week mesocycles:
    – W1: Akkumulation I   (mittel Volumen, leicht–mittel Intensität)
    – W2: Akkumulation II  (hohes Volumen, mittel Intensität)
    – W3: Intensivierung   (niedrig–mittel Volumen, hoch Intensität)
    – W4: Deload           (sehr niedrig Volumen, leicht Intensität)
  • Progressive overload: intensity band increases across phases
  • Deficit scoring:  primary=3, secondary=2, tertiary=1
    → determines how many exercises per area per week
  • Supported plan lengths: 4, 6, 8, 12 weeks
"""

from database import (
    periodisierung_loeschen, periodisierung_bulk_insert, periodisierung_laden,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern,
)

# ─────────────────────────────────────────────────────────────────────────────
# Exercise pools  (area → phase → list of (uebung, saetze, wiederholungen, haeuf))
# ─────────────────────────────────────────────────────────────────────────────

_POOL: dict[str, dict[str, list]] = {

    "Rumpf": {                   # always inserted as base every week
        "stabilisation": [
            ("Dead Bug",                   "3", "8 je Seite",   "3×/Woche"),
            ("Pallof Press",               "3", "12",           "3×/Woche"),
            ("Plank",                      "3", "40 Sekunden",  "3×/Woche"),
            ("Seitstütz",                  "3", "30 Sekunden",  "3×/Woche"),
        ],
        "kraft": [
            ("Ab Wheel Rollout",           "3", "8",            "3×/Woche"),
            ("Plank mit Armheben",         "3", "10 je Seite",  "3×/Woche"),
            ("Pallof Press Stand",         "3", "12",           "3×/Woche"),
            ("Russischer Twist",           "3", "16",           "2×/Woche"),
        ],
        "power": [
            ("Medizinball Rotationswurf",  "4", "8",            "2×/Woche"),
            ("Landmine Rotation",          "3", "10",           "2×/Woche"),
            ("Hanging Knee Raise",         "3", "12",           "2×/Woche"),
            ("Farmer's Walk",              "3", "30 Meter",     "2×/Woche"),
        ],
    },

    "Hüfte": {
        "stabilisation": [
            ("Seitliches Miniband Gehen",  "3", "12 Meter",     "3×/Woche"),
            ("90/90 Hüftrotation",         "3", "10",           "2×/Woche"),
            ("Einbeinige Hüftbrücke",      "3", "10 je Seite",  "3×/Woche"),
            ("Copenhagen Plank (kurz)",    "3", "20 Sekunden",  "3×/Woche"),
        ],
        "kraft": [
            ("Copenhagen Plank",           "3", "30 Sekunden",  "3×/Woche"),
            ("Einbeiniges Hip Hinge",      "3", "8 je Seite",   "3×/Woche"),
            ("Banded Lateral Walk",        "3", "15 Meter",     "3×/Woche"),
            ("Hip Thrust",                 "4", "10",           "2×/Woche"),
        ],
        "power": [
            ("Explosiver Hip Thrust",      "4", "6",            "2×/Woche"),
            ("Lateral Bound stabilisiert", "3", "6 je Seite",   "2×/Woche"),
            ("Single-Leg Glute Bridge +Gewicht", "3", "8",      "2×/Woche"),
            ("Resisted Hip Abduction",     "3", "12",           "2×/Woche"),
        ],
    },

    "Knie": {
        "stabilisation": [
            ("Single Leg Squat (Qualität)", "3", "8 je Seite",  "3×/Woche"),
            ("Step Down",                  "3", "8 je Seite",   "2×/Woche"),
            ("Seitliche Miniband Squats",  "3", "10",           "2×/Woche"),
            ("Valgus-Kontroll Lunge",      "3", "8 je Seite",   "2×/Woche"),
        ],
        "kraft": [
            ("Bulgarian Split Squat",      "3", "8 je Seite",   "2×/Woche"),
            ("Reverse Lunge",              "3", "10 je Seite",  "2×/Woche"),
            ("Box Squat",                  "4", "6",            "2×/Woche"),
            ("Single Leg Leg Press",       "3", "10 je Seite",  "2×/Woche"),
        ],
        "power": [
            ("Drop Landing → Sprung",      "4", "5",            "2×/Woche"),
            ("Bounding",                   "4", "20 Meter",     "2×/Woche"),
            ("Single Leg Jump & Stabilisierung", "3", "5 je Seite", "2×/Woche"),
            ("Box Jump einbeinig",         "3", "4 je Seite",   "1×/Woche"),
        ],
    },

    "Sprunggelenk": {
        "stabilisation": [
            ("Knie zur Wand Mobilisation", "3", "10 je Seite",  "3×/Woche"),
            ("Einbeinstand Balance Pad",   "3", "30 Sekunden",  "3×/Woche"),
            ("Einbeinige Wadenheben",      "3", "15",           "3×/Woche"),
            ("Fersengang / Zehengang",     "3", "15 Meter",     "2×/Woche"),
        ],
        "kraft": [
            ("Single Leg Calf Raise (Treppe)", "4", "12",       "3×/Woche"),
            ("Ankle Banded Dorsiflexion",  "3", "15",           "2×/Woche"),
            ("Pogo Hops beidbeinig",       "3", "10 Sekunden",  "3×/Woche"),
            ("Einbeinige Pogo Hops",       "3", "10 je Seite",  "2×/Woche"),
        ],
        "power": [
            ("Ankle Jumps reaktiv",        "4", "8",            "2×/Woche"),
            ("Depth Drop → Sprung",        "3", "5",            "1×/Woche"),
            ("Lateral Hops reaktiv",       "3", "8 je Seite",   "2×/Woche"),
            ("Einbeinige Hüpfsprints",     "4", "20 Meter",     "2×/Woche"),
        ],
    },

    "Oberschenkel": {
        "stabilisation": [
            ("Nordic Hamstring Eccentric", "3", "5",            "2×/Woche"),
            ("Einbeiniges Rum. Kreuzheben (leicht)", "3", "8",  "2×/Woche"),
            ("Lying Hamstring Curl",       "3", "10",           "2×/Woche"),
            ("Gluteal Bridge Variante",    "3", "12",           "2×/Woche"),
        ],
        "kraft": [
            ("Nordic Hamstring Curl",      "3", "6",            "2×/Woche"),
            ("Romanian Deadlift einbeinig","3", "8 je Seite",   "2×/Woche"),
            ("Seated Leg Curl",            "4", "10",           "2×/Woche"),
            ("Good Morning",               "3", "10",           "2×/Woche"),
        ],
        "power": [
            ("Explosive Nordic",           "4", "4",            "1×/Woche"),
            ("Hamstring Sliders reaktiv",  "3", "6",            "2×/Woche"),
            ("Power RDL",                  "4", "5",            "2×/Woche"),
            ("Sprung aus Kniebeuge",       "3", "5",            "2×/Woche"),
        ],
    },

    "Schnelligkeit": {
        "stabilisation": [
            ("Lauf-ABC (A-Skip)",          "4", "20 Meter",     "2×/Woche"),
            ("Steigerungsläufe",           "4", "40 Meter",     "2×/Woche"),
        ],
        "kraft": [
            ("10 m Sprintstarts",          "6", "10 m",         "2×/Woche"),
            ("Beschleunigungs-ABC",        "4", "20 Meter",     "2×/Woche"),
            ("Wall Drills",                "3", "10 je Seite",  "2×/Woche"),
            ("Resistenz-Sprints (Band)",   "4", "20 Meter",     "1×/Woche"),
        ],
        "power": [
            ("20–30 m Maximalsprints",     "6", "30 m",         "1×/Woche"),
            ("Reaktionssprints",           "6", "10 m",         "2×/Woche"),
            ("Fliegende 30er",             "4", "30 m",         "1×/Woche"),
            ("Bergaufsprints",             "6", "20 m",         "1×/Woche"),
        ],
    },

    "Explosivität": {
        "stabilisation": [
            ("Koordinations-Hops",         "3", "3×5 m",        "2×/Woche"),
            ("Squat Jump Einführung",      "3", "5",            "2×/Woche"),
        ],
        "kraft": [
            ("Squat Jump",                 "4", "6",            "2×/Woche"),
            ("Box Jump beidbeinig",        "4", "5",            "2×/Woche"),
            ("Medicine Ball Slam",         "3", "8",            "2×/Woche"),
            ("Hürdensprünge",              "3", "5",            "1×/Woche"),
        ],
        "power": [
            ("Depth Jump",                 "4", "4",            "1×/Woche"),
            ("Einbeinige Plyo Sprünge",    "4", "5 je Seite",   "1×/Woche"),
            ("Box Jump maximal",           "5", "4",            "2×/Woche"),
            ("Reaktive Sprünge (DJ-RSI)", "4", "5",            "1×/Woche"),
        ],
    },

    "Agilität": {
        "stabilisation": [
            ("Footwork Leitertraining",    "4", "Durchgänge",   "2×/Woche"),
            ("Deceleration Drill",         "5", "10 m",         "2×/Woche"),
        ],
        "kraft": [
            ("5-10-5 Shuttle",             "5", "Durchgänge",   "2×/Woche"),
            ("Pro Agility Drill",          "5", "Durchgänge",   "1×/Woche"),
            ("T-Test",                     "4", "Durchgänge",   "1×/Woche"),
            ("Seitwärts Sprints",          "6", "10 m",         "2×/Woche"),
        ],
        "power": [
            ("Randomized Agility (Signal)","5", "Durchgänge",   "2×/Woche"),
            ("Illinois Test Tempo",        "4", "Durchgänge",   "1×/Woche"),
            ("COD Speed Drills",           "5", "Durchgänge",   "2×/Woche"),
            ("Fußball-Agility Parcours",   "4", "Durchgänge",   "1×/Woche"),
        ],
    },

    "Fußball": {
        "stabilisation": [
            ("Einbeinige Ballkontakte",    "3", "60 Sekunden",  "2×/Woche"),
            ("Ballkontrolle Gleichgewicht","3", "60 Sekunden",  "2×/Woche"),
        ],
        "kraft": [
            ("Partner Widerstandsdrücken", "3", "10 Sekunden",  "2×/Woche"),
            ("Zweikampf Stabilität",       "3", "20 Sekunden",  "2×/Woche"),
            ("Koordination Leitertraining","5", "Durchgänge",   "2×/Woche"),
            ("Ballführung unter Druck",    "4", "30 Sekunden",  "2×/Woche"),
        ],
        "power": [
            ("Repeated Sprint Ability (RSA)", "6", "30 m",      "1×/Woche"),
            ("30-30 Intervallläufe",       "10", "30 Sekunden", "1×/Woche"),
            ("Pressingsimulation",         "5", "30 Sekunden",  "2×/Woche"),
            ("Schusstraining explosiv",    "4", "8 je Seite",   "1×/Woche"),
        ],
    },
}

# Phase-Zonen: which pool key to use per week range
_PHASEN = [
    (1,  4,  "stabilisation",  "Phase 1 — Stabilisation",    "Bewegungsqualität & Verletzungsprävention"),
    (5,  8,  "kraft",          "Phase 2 — Kraftaufbau",       "Maximalkraft & funktionelle Stärke"),
    (9,  12, "power",          "Phase 3 — Fußballspezifisch", "Explosivkraft & Wettkampfvorbereitung"),
]

# 4-week block load pattern (position within 4-week block → volume factor, intensity label)
_BLOCK_LOAD = [
    (1.00, "leicht–mittel",  "Akkumulation I"),
    (1.15, "mittel",         "Akkumulation II"),
    (0.90, "hoch",           "Intensivierung"),
    (0.60, "leicht",         "Deload ⬇"),      # week 4 of each block
]

# For plan lengths < 12 weeks: use these week mappings into the phase pool
_SHORT_PLAN_PHASE = {
    4:  [(1, "stabilisation", "Stabilisation",            "Bewegungsqualität & Verletzungsprävention")],
    6:  [(1, "stabilisation", "Stabilisation",            "Bewegungsqualität & Verletzungsprävention"),
         (5, "kraft",         "Kraftaufbau",              "Maximalkraft & funktionelle Stärke")],
    8:  [(1, "stabilisation", "Stabilisation",            "Bewegungsqualität & Verletzungsprävention"),
         (5, "kraft",         "Kraftaufbau",              "Maximalkraft & funktionelle Stärke")],
}


# ─────────────────────────────────────────────────────────────────────────────
# Deficit scoring
# ─────────────────────────────────────────────────────────────────────────────

def defizit_score(schwerpunkt_text: str) -> dict[str, int]:
    """
    Parse the combined schwerpunkt text and return a priority score per area.
    Score: 3 = primary deficit, 2 = secondary, 1 = tertiary / mentioned once.
    Rumpf always gets at least 1 (base stability).
    """
    txt = schwerpunkt_text.lower()

    _mapping = [
        (["hüft", "huft", "gluteus", "becken", "seitenasymmetrie"],     "Hüfte"),
        (["knie", "valgus", "landungskontrolle", "sprungasymmetrie"],   "Knie"),
        (["rumpf", "core", "rotations", "anti-rotation", "schulter"],   "Rumpf"),
        (["oberschenkel", "hamstring", "nordisch"],                      "Oberschenkel"),
        (["sprunggelenk", "ankle", "wade", "fersengang"],               "Sprunggelenk"),
        (["schnelligkeit", "sprint", "beschleunigung"],                 "Schnelligkeit"),
        (["explosiv", "sprung", "sprungkraft"],                         "Explosivität"),
        (["agil", "richtungswechsel", "505"],                           "Agilität"),
        (["fußball", "fussball", "ausdauer", "intermittierend"],        "Fußball"),
    ]

    counts: dict[str, int] = {}
    for keywords, area in _mapping:
        hits = sum(1 for kw in keywords if kw in txt)
        if hits > 0:
            counts[area] = hits

    # Convert hit counts to priority score 1–3
    scores: dict[str, int] = {}
    if counts:
        max_hits = max(counts.values())
        for area, hits in counts.items():
            if hits == max_hits:
                scores[area] = 3
            elif hits >= max_hits * 0.5:
                scores[area] = 2
            else:
                scores[area] = 1

    # Rumpf is always at least 1 (base stability every week)
    scores.setdefault("Rumpf", 1)
    return scores


# ─────────────────────────────────────────────────────────────────────────────
# Weekly plan builder
# ─────────────────────────────────────────────────────────────────────────────

def _pool_fuer_area(area: str, pool_key: str, n: int, offset: int = 0) -> list:
    """Return up to n exercises from the pool, cycling with offset for variety.
    Never returns duplicates within one call (caps at pool size)."""
    exercises = _POOL.get(area, {}).get(pool_key, [])
    if not exercises:
        return []
    n = min(n, len(exercises))          # avoid in-week duplicates
    result = []
    for i in range(n):
        result.append(exercises[(offset + i) % len(exercises)])
    return result


def _woche_eintraege(
    woche: int,
    total_wochen: int,
    scores: dict[str, int],
    phase_name: str,
    phase_ziel: str,
    pool_key: str,
) -> list[dict]:
    """Build one week's exercises. Returns a list of plan row dicts."""

    pos_in_block = (woche - 1) % 4                   # 0–3 within 4-week block
    vol_factor, intensitaet_label, woche_typ = _BLOCK_LOAD[pos_in_block]
    is_deload = pos_in_block == 3
    offset = (woche - 1) // 4                         # exercise rotation across blocks

    entries = []

    # Sorted by score descending
    sorted_areas = sorted(scores.items(), key=lambda x: -x[1])

    for area, score in sorted_areas:
        if is_deload:
            n = max(0, score - 2)  # 1 exercise for primary, 0 for others on deload
        else:
            n = score              # 3 for primary, 2 for secondary, 1 for tertiary

        exercises = _pool_fuer_area(area, pool_key, n, offset=offset)
        for uebung, saetze, volumen, haeufigkeit in exercises:
            # Adjust intensity wording in saetze/haeufigkeit on deload
            if is_deload:
                haeufigkeit = haeufigkeit.replace("3×", "2×").replace("4×", "2×")
            entries.append({
                "woche":       woche,
                "phase":       f"{phase_name} ({woche_typ})",
                "ziel":        phase_ziel,
                "bereich":     area,
                "uebung":      uebung,
                "intensitaet": "leicht" if is_deload else intensitaet_label,
                "volumen":     volumen,
                "haeufigkeit": haeufigkeit,
            })

    return entries


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def zyklus_erstellen(spieler_id: int, schwerpunkt_text: str, wochen: int = 12) -> list[dict]:
    """
    Generate and persist a multi-focus, deficit-driven training cycle.

    Parameters
    ----------
    spieler_id      : DB id of the player
    schwerpunkt_text: Combined deficit text from schwerpunkt_sammeln()
    wochen          : Plan length — 4, 6, 8, or 12 weeks
    """
    wochen = wochen if wochen in (4, 6, 8, 12) else 12
    scores = defizit_score(schwerpunkt_text)
    plan: list[dict] = []

    if wochen == 12:
        # Full 3-phase 12-week plan
        for woche_start, woche_end, pool_key, ph_name, ph_ziel in _PHASEN:
            for w in range(woche_start, woche_end + 1):
                plan.extend(_woche_eintraege(w, 12, scores, ph_name, ph_ziel, pool_key))
    else:
        # Shorter plans: use stabilisation + kraft pools proportionally
        block_size = wochen // (len(_SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "", "")])))
        phase_defs = _SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "Stabilisation", "")])
        w = 1
        for phase_start, pool_key, ph_name, ph_ziel in phase_defs:
            end = min(phase_start + block_size - 1, wochen)
            for week_nr in range(w, w + block_size):
                if week_nr > wochen:
                    break
                plan.extend(_woche_eintraege(week_nr, wochen, scores, ph_name, ph_ziel, pool_key))
            w += block_size

    periodisierung_loeschen(spieler_id)
    periodisierung_bulk_insert(spieler_id, plan)
    return plan


def zyklus_laden(spieler_id: int) -> list:
    return periodisierung_laden(spieler_id)


# ─── Legacy compatibility ──────────────────────────────────────────────────
# Called from page_trainingsplan() — generate into the trainingsplan table
def trainingsplan_multi_erstellen(spieler_id: int, schwerpunkt_text: str, wochen: int = 8) -> int:
    """
    Generate a multi-focus plan into the trainingsplan table (shorter plans).
    Returns number of entries created.
    """
    wochen = wochen if wochen in (4, 6, 8) else 8
    scores = defizit_score(schwerpunkt_text)

    pool_key = "stabilisation" if wochen <= 4 else "kraft" if wochen <= 8 else "power"

    from database import trainingsplan_loeschen, trainingsplan_eintrag_speichern
    from datetime import date
    trainingsplan_loeschen(spieler_id)

    total = 0
    for w in range(1, wochen + 1):
        pos = (w - 1) % 4
        is_deload = pos == 3
        offset = (w - 1) // 4

        sorted_areas = sorted(scores.items(), key=lambda x: -x[1])
        for area, score in sorted_areas:
            n = max(0, score - 1) if is_deload else score
            exercises = _pool_fuer_area(area, pool_key, n, offset=offset)
            for uebung, saetze, volumen, haeufigkeit in exercises:
                trainingsplan_eintrag_speichern(
                    spieler_id, str(date.today()), w,
                    area, uebung, saetze, volumen,
                    haeufigkeit.replace("3×", "2×") if is_deload else haeufigkeit,
                )
                total += 1

    return total


def defizit_tabelle(schwerpunkt_text: str) -> list[dict]:
    """
    Return a sorted list of dicts for displaying the deficit analysis.
    Each dict: {area, score, prioritaet, kennzeichnung}
    """
    scores = defizit_score(schwerpunkt_text)
    prio_map = {3: "🔴 Primär", 2: "🟡 Sekundär", 1: "🟢 Tertiär"}
    result = []
    for area, score in sorted(scores.items(), key=lambda x: -x[1]):
        result.append({
            "Bereich":    area,
            "Priorität":  prio_map.get(score, "—"),
            "Volumen/Woche": f"{score} Übung(en)",
            "Score":      score,
        })
    return result
