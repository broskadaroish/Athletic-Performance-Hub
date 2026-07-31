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

def zyklus_erstellen(spieler_id: int, schwerpunkt_text: str,
                     wochen: int = 12,
                     alter: float | None = None) -> list[dict]:
    """
    Altersbasierter Periodisierungszyklus (12-Wochen oder kürzer).
    Quelle: Faigenbaum & Myer (2010), Lloyd et al. (2014), NSCA Essentials.

    Altersanpassung:
      U10  → Nur Phase 1 (Stabilisation) / max. 4 Wochen
      U14  → Phase 1 + 2 (Stabilisation + Kraft), kein Power
      U18  → Alle Phasen (moderate Power-Intensität)
      Senior → Vollständig
      Ü40  → Alle Phasen, reduzierte Power-Intensität
      Ü55  → Phase 1 + 2 nur (keine Power-Phase)
    """
    wochen = wochen if wochen in (4, 6, 8, 12) else 12
    scores = defizit_score(schwerpunkt_text)
    plangruppe = _alter_zu_plangruppe(alter)
    cfg        = _PLANGRUPPEN_CONFIG[plangruppe]
    plan: list[dict] = []

    # Phasen altersgerecht begrenzen
    def _phase_erlaubt(pool_key: str) -> bool:
        return _max_pool_key(pool_key, cfg["max_pool_key"]) == pool_key

    if wochen == 12:
        for woche_start, woche_end, pool_key, ph_name, ph_ziel in _PHASEN:
            _pk = _max_pool_key(pool_key, cfg["max_pool_key"])
            for w in range(woche_start, woche_end + 1):
                if w > wochen:
                    break
                plan.extend(_woche_eintraege(w, wochen, scores, ph_name, ph_ziel, _pk))
    else:
        block_size = wochen // (len(_SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "", "")])))
        phase_defs = _SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "Stabilisation", "")])
        w = 1
        for phase_start, pool_key, ph_name, ph_ziel in phase_defs:
            _pk = _max_pool_key(pool_key, cfg["max_pool_key"])
            for week_nr in range(w, w + block_size):
                if week_nr > wochen:
                    break
                plan.extend(_woche_eintraege(week_nr, wochen, scores, ph_name, ph_ziel, _pk))
            w += block_size

    # Altersgerechte Übungssubstitution im Zyklus-Plan
    filtered = []
    for entry in plan:
        uebung = entry.get("uebung", "")
        ersatz = _ersatz_uebung(uebung, plangruppe)
        if ersatz is None:
            continue  # nicht geeignet
        if ersatz != "ok":
            entry = dict(entry)
            entry["uebung"]      = ersatz[0]
            entry["saetze"]      = _saetze_begrenzen(ersatz[1], cfg["max_saetze"])
            entry["volumen"]     = ersatz[2]
            entry["haeufigkeit"] = _haeufigkeit_begrenzen(ersatz[3], cfg["haeuf_cap"])
        else:
            entry = dict(entry)
            entry["saetze"] = _saetze_begrenzen(str(entry.get("saetze", "3")), cfg["max_saetze"])
            h = entry.get("haeufigkeit", "")
            entry["haeufigkeit"] = _haeufigkeit_begrenzen(h, cfg["haeuf_cap"])
        filtered.append(entry)

    periodisierung_loeschen(spieler_id)
    periodisierung_bulk_insert(spieler_id, filtered)
    return filtered


def zyklus_laden(spieler_id: int) -> list:
    return periodisierung_laden(spieler_id)


# ─── Legacy compatibility ──────────────────────────────────────────────────
# Called from page_trainingsplan() — generate into the trainingsplan table
# ─── Training-Day assignment helpers ─────────────────────────────────────────

# ─── Pause und Ausführung — BEREICHSSPEZIFISCH ───────────────────────────────
# Format Ausführung: exzentrisch - isometr. Pause - konzentrisch (s)
#
# Sportwissenschaftliche Grundlagen:
#   Stabilisation  → 2-1-2 s Tempo (neuromot. Kontrolle), 30–45 s Pause
#   Kraft          → 3-0-1 s Tempo (exzentrischer Overload + schnell konzentrisch),
#                    60–90 s Pause (je nach Muskelgruppe)
#   Power/Explosiv → kein Tempo-Protokoll (max. Geschwindigkeit jede WH),
#                    90–180 s Pause (ZNS-Erholung entscheidend)
#   Sprint         → volle ZNS-Erholung 120–180 s (Qualität > Quantität)
#   Isometrisch    → Haltedauer definiert Intensität, 45 s Pause
#
# Quellen: Haff & Triplett (NSCA 2016), Zatsiorsky & Kraemer (2006),
#          Faigenbaum & Myer (2010), Buchheit & Laursen (2013)
#
# Schlüssel: (bereich, pool_key) → (pause_sekunden, ausfuehrung_text)

_BEREICH_PARAMS: dict[tuple[str, str], tuple[int, str]] = {

    # ── Rumpf (Core) ──────────────────────────────────────────────────────────
    # Stabilisation: isometrische Kontrolle, kurze Pause für Dauerreiz
    # Kraft: dynamische Rumpfkraft, kontrolliert exzentrisch
    # Power: rotative Kraft / Medizinball — explosiv, volle Pause
    ("Rumpf", "stabilisation"): (45,  "2-1-2 s (Stabilisationsphase halten)"),
    ("Rumpf", "kraft"):         (60,  "2-0-1 s (kontrolliert-exzentrisch)"),
    ("Rumpf", "power"):         (90,  "Explosiv / reaktiv"),

    # ── Hüfte ─────────────────────────────────────────────────────────────────
    # Hüftabduktoren, Gluteus medius — kurze Pause bei Stabi
    # Hip Thrust Kraft: moderate Pause, langsam exzentrisch
    # Power: explosiver Hip Thrust — volle Pause, max. Hüftstreckung
    ("Hüfte", "stabilisation"): (45,  "2-1-2 s (Hüftkontrolle betonen)"),
    ("Hüfte", "kraft"):         (75,  "3-0-1 s (langsam exzentrisch)"),
    ("Hüfte", "power"):         (90,  "Explosiv / max. Hüftextension"),

    # ── Knie ──────────────────────────────────────────────────────────────────
    # Knie: exzentrischer Fokus (Patellasehne, ACL-Prävention)
    # Kraft: längere Pause bei Bulgarian Split Squat etc.
    # Power: reaktiv — keine Erschöpfung, volle ZNS-Erholung
    ("Knie", "stabilisation"): (45,  "2-1-2 s (Knieachse kontrollieren)"),
    ("Knie", "kraft"):         (90,  "3-0-1 s (exzentrischer Fokus)"),
    ("Knie", "power"):         (120, "Reaktiv / max. Explosivkraft"),

    # ── Sprunggelenk ──────────────────────────────────────────────────────────
    # Wadenheben / Mobilisation — kurze Pause, hohe Wdh.-Qualität
    # Power: Ankle Jumps reaktiv — Elastizität der Achillessehne
    ("Sprunggelenk", "stabilisation"): (45, "2-1-2 s (Balance & Bodenkontakt)"),
    ("Sprunggelenk", "kraft"):         (60, "2-0-1 s (Exzentrik Wadenheben)"),
    ("Sprunggelenk", "power"):         (90, "Reaktiv / max. Elastizität Achillessehne"),

    # ── Oberschenkel (Hamstring-Fokus) ────────────────────────────────────────
    # Nordic Hamstring: besonders hohe exzentrische Belastung → längste Pause
    # Power: Explosive Nordic / Power RDL — volle ZNS-Erholung nötig
    ("Oberschenkel", "stabilisation"): (60,  "3-1-2 s (exzentrischer Hamstring-Fokus)"),
    ("Oberschenkel", "kraft"):         (90,  "3-0-1 s (kontrolliert exzentrisch)"),
    ("Oberschenkel", "power"):         (120, "Explosiv / max. Kraft — keine Ermüdung"),

    # ── Schnelligkeit (Sprint) ────────────────────────────────────────────────
    # WICHTIG: Sprinttraining erfordert VOLLE ZNS-Erholung
    # Kein Tempo-Protokoll — max. Geschwindigkeit jede Einheit
    # Kurze Pausen zerstören die Qualität und bewirken Laktatkonditionierung statt Schnelligkeit
    ("Schnelligkeit", "stabilisation"): (90,  "Max. Qualität / Lauf-ABC technisch"),
    ("Schnelligkeit", "kraft"):         (120, "Max. Intensität — volle ZNS-Erholung"),
    ("Schnelligkeit", "power"):         (180, "Max. Intensität — vollständige ZNS-Erholung"),

    # ── Explosivität (Plyometrie) ─────────────────────────────────────────────
    # Plyometrische Übungen: je höher Intensität, desto länger Pause
    # Ziel: jede WH mit maximaler Explosivität (keine Ermüdungsakkumulation)
    ("Explosivität", "stabilisation"): (60,  "Reaktiv / Qualität jede Wiederholung"),
    ("Explosivität", "kraft"):         (90,  "Explosiv / volle Pause zwischen Sätzen"),
    ("Explosivität", "power"):         (120, "Max. Explosivität — keine Ermüdung zulassen"),

    # ── Agilität ──────────────────────────────────────────────────────────────
    # Agility: reaktionsbasiert — moderate Pause, Qualität über Quantität
    # Power-Agility: signalbasiert, volle kognitive Erholung nötig
    ("Agilität", "stabilisation"): (60,  "Max. Richtungswechselqualität"),
    ("Agilität", "kraft"):         (90,  "Max. Intensität / COD-Geschwindigkeit"),
    ("Agilität", "power"):         (90,  "Reaktiv / signalbasiert — volle Konzentration"),

    # ── Fußball (fußballspezifisch) ───────────────────────────────────────────
    # Fußball-spezifische Belastungssteuerung: wettkampfnahe Intervalle
    # Power: kurze Pausen wie im Spiel (repeated sprint ability)
    ("Fußball", "stabilisation"): (45,  "Technisch / kontrolliert"),
    ("Fußball", "kraft"):         (60,  "Mittel-intensiv / wettkampfnah"),
    ("Fußball", "power"):         (60,  "Wettkampfintensität — kurze Pausen (RSA)"),
}

# Fallback-Werte falls Bereich nicht in der Tabelle
_PAUSE_FALLBACK:    dict[str, int] = {"stabilisation": 45, "kraft": 90, "power": 120}
_AUSFUEHRUNG_FALLBACK: dict[str, str] = {
    "stabilisation": "2-1-2 s (kontrolliert)",
    "kraft":         "3-0-1 s (exzentrisch-konzentrisch)",
    "power":         "Explosiv / max. Geschwindigkeit",
}


def _pause_und_ausfuehrung(bereich: str, pool_key: str,
                            is_deload: bool = False,
                            plangruppe: str = "Senior") -> tuple[int, str]:
    """Gibt alters- und bereichsspezifische (pause_sek, ausfuehrung) zurück."""
    pause_s, ausfuehr = _BEREICH_PARAMS.get(
        (bereich, pool_key),
        (_PAUSE_FALLBACK.get(pool_key, 90), _AUSFUEHRUNG_FALLBACK.get(pool_key, "kontrolliert")),
    )
    # Alters-Offset addieren
    cfg = _PLANGRUPPEN_CONFIG.get(plangruppe, _PLANGRUPPEN_CONFIG["Senior"])
    pause_s += cfg["pause_offset"]
    prefix = cfg["ausfuehr_prefix"]
    if prefix and not ausfuehr.startswith(prefix):
        ausfuehr = prefix + ausfuehr
    if is_deload:
        pause_s = max(30, pause_s - 15)
        ausfuehr = ausfuehr + " / leicht"
    return pause_s, ausfuehr



# ─────────────────────────────────────────────────────────────────────────────
# Altersbasiertes Planungs-System
# Quellen: Faigenbaum & Myer (2010) Br J Sports Med; Lloyd et al. (2014) BJSM;
#          NSCA Position Statement Youth Resistance Training (2009);
#          Kraemer et al.; Harridge & Suominen (Ü-40 Trainingslehre)
# ─────────────────────────────────────────────────────────────────────────────

def _alter_zu_plangruppe(alter: float | None) -> str:
    """Ordnet ein Lebensalter der Trainingsplangruppe zu."""
    if not alter or alter <= 0:
        return "Senior"
    a = int(alter)
    if a <= 10: return "U10"
    if a <= 14: return "U14"
    if a <= 18: return "U18"
    if a <= 35: return "Senior"
    if a <= 50: return "Ü40"
    return "Ü55"


# Konfiguration je Plangruppe:
#   max_pool_key    : höchste erlaubte Phase (U10 nur Stabilisation, kein Power)
#   pause_offset    : Sekunden zusätzlich zur bereichsspezifischen Pause
#   ausfuehr_prefix : Textpräfix für die Ausführungsanweisung
#   max_saetze      : Maximale Satzzahl (ersetzt grössere Werte im Pool)
#   haeuf_cap       : Frequenzbegrenzung (z. B. max 2×/Woche)
#   label           : Anzeigename für die UI
_PLANGRUPPEN_CONFIG: dict[str, dict] = {
    "U10": {
        "max_pool_key":  "stabilisation",  # Kein Kraft/Power → Koordination & Körpergewicht
        "pause_offset":  45,               # +45 s Coaching-/Erklärungszeit
        "ausfuehr_prefix": "Technisch / Körpergefühl entwickeln — kein Tempo-Ziel · ",
        "max_saetze":    2,
        "haeuf_cap":     "2×",
        "label":         "U10 — Koordination & Bewegungsbildung",
    },
    "U14": {
        "max_pool_key":  "kraft",          # Kein Power → Intro Widerstandstraining
        "pause_offset":  20,
        "ausfuehr_prefix": "Technisch kontrolliert · ",
        "max_saetze":    3,
        "haeuf_cap":     None,
        "label":         "U14 — Technischer Aufbau & Intro Krafttraining",
    },
    "U18": {
        "max_pool_key":  "power",          # Vollständig, moderate Power-Intensität
        "pause_offset":  10,
        "ausfuehr_prefix": "",
        "max_saetze":    99,
        "haeuf_cap":     None,
        "label":         "U18 — Strukturiertes Athletiktraining",
    },
    "Senior": {
        "max_pool_key":  "power",
        "pause_offset":  0,
        "ausfuehr_prefix": "",
        "max_saetze":    99,
        "haeuf_cap":     None,
        "label":         "Senior — Vollständiges Leistungstraining",
    },
    "Ü40": {
        "max_pool_key":  "power",          # Power erlaubt, aber reduziert (s. u.)
        "pause_offset":  20,               # +20 s — Erholung dauert länger
        "ausfuehr_prefix": "Kontrolliert / gelenkschonend · ",
        "max_saetze":    99,
        "haeuf_cap":     None,
        "label":         "Ü40 — Erhalt & Verletzungsprävention",
    },
    "Ü55": {
        "max_pool_key":  "kraft",          # Kein Power → Funktionelle Stärke
        "pause_offset":  40,               # +40 s — längere Regeneration nötig
        "ausfuehr_prefix": "Sehr kontrolliert / gelenkschonend · ",
        "max_saetze":    3,
        "haeuf_cap":     "2×",
        "label":         "Ü55 — Funktionelle Stärke & Gelenkschonung",
    },
}


# Übungsersatz für altersungeeignete Übungen
# Format: Übungsname → { Plangruppe: (Ersatzübung, Sätze, Volumen, Häufigkeit) | None }
# None = Übung komplett weglassen
_ALTERS_ERSATZ: dict[str, dict[str, tuple | None]] = {
    # ── Hochbelastende Hamstring/Kraft-Übungen ────────────────────────────────
    "Nordic Hamstring Eccentric": {
        "U10": ("Einbeinige Hüftbrücke",             "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Nordic Hamstring Eccentric (assist.)","3", "4",           "2×/Woche"),
    },
    "Nordic Hamstring Curl": {
        "U10": ("Einbeinige Hüftbrücke",             "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",   "3", "4",            "2×/Woche"),
        "Ü55": ("Lying Hamstring Curl (Maschine)",   "3", "12",           "2×/Woche"),
    },
    "Box Squat": {
        "U10": ("Mini-Squat Körpergewicht",          "2", "12",           "3×/Woche"),
        "U14": ("Goblet Squat (leicht)",             "3", "10",           "2×/Woche"),
    },
    "Bulgarian Split Squat": {
        "U10": ("Ausfallschritt Körpergewicht",      "2", "8 je Seite",   "3×/Woche"),
        "U14": ("Ausfallschritt Körpergewicht",      "3", "8 je Seite",   "2×/Woche"),
    },
    "Single Leg Leg Press": {
        "U10": ("Einbeiniger Kniestand (Balance)",   "2", "10 je Seite",  "2×/Woche"),
    },
    "Good Morning": {
        "U10": ("Hinge-Bewegung Körpergewicht",      "2", "10",           "2×/Woche"),
        "U14": ("Rumänisches Kreuzheben (leicht)",   "3", "10",           "2×/Woche"),
    },
    "Ab Wheel Rollout": {
        "U10": ("Plank mit Armheben",               "2", "8 je Seite",   "3×/Woche"),
        "U14": ("Rollout (klein, kniend)",           "3", "6",            "2×/Woche"),
    },
    "Hanging Knee Raise": {
        "U10": ("Beckenheben liegend",              "2", "12",            "3×/Woche"),
        "U14": ("Knieheben an Stange (leicht)",     "3", "8",            "2×/Woche"),
    },
    "Farmer's Walk": {
        "U10": ("Einbeiniger Stand auf Wackelmatte","2", "30 Sekunden",  "2×/Woche"),
    },
    # ── Plyometrie / Power-Übungen ────────────────────────────────────────────
    "Depth Jump": {
        "U10": ("Beidbeinige Sprünge (Boden)",      "2", "5",             "2×/Woche"),
        "U14": ("Box Jump (Höhe 30 cm)",            "3", "4",             "2×/Woche"),
        "Ü55": ("Box Step-Down kontrolliert",        "3", "6 je Seite",   "2×/Woche"),
    },
    "Depth Drop → Sprung": {
        "U10": ("Beidbeinige Sprünge (Boden)",      "2", "5",             "2×/Woche"),
        "U14": ("Drop Step → Squat",                "3", "5",             "2×/Woche"),
        "Ü55": ("Box Step-Down kontrolliert",        "3", "6 je Seite",   "2×/Woche"),
    },
    "Einbeinige Plyo Sprünge": {
        "U10": ("Einbeiniger Stand + Rumpfrotation","2", "8 je Seite",   "2×/Woche"),
        "U14": ("Einbeinige Hops (niedrig)",        "3", "5 je Seite",   "1×/Woche"),
        "Ü55": ("Einbeinige Wadenheben (langsam)",  "3", "12 je Seite",  "2×/Woche"),
    },
    "Box Jump maximal": {
        "U10": ("Beidbeiniger Bodenabsprung (kniend aufkommen)", "2", "5", "2×/Woche"),
        "U14": ("Box Jump (Höhe 30–40 cm)",         "3", "4",             "2×/Woche"),
        "Ü55": ("Box Step-Up kontrolliert",          "3", "8 je Seite",   "2×/Woche"),
    },
    "Reaktive Sprünge (DJ-RSI)": {
        "U10": ("Koordinations-Hops (Boden)",       "2", "8",             "2×/Woche"),
        "U14": ("Ankle Jumps (niedrig)",            "3", "8",             "2×/Woche"),
        "Ü55": ("Pogo Hops (sehr leicht, kurz)",    "3", "8 Sekunden",   "2×/Woche"),
    },
    "Explosive Nordic": {
        "U10": ("Hip Bridge reaktiv",               "2", "8",             "2×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",  "3", "4",             "1×/Woche"),
        "Ü55": ("Lying Hamstring Curl langsam",     "3", "10",            "2×/Woche"),
    },
    "Hamstring Sliders reaktiv": {
        "U10": ("Einbeinige Hüftbrücke",            "2", "10 je Seite",  "2×/Woche"),
        "U14": ("Hamstring Curl Maschine (leicht)", "3", "10",            "2×/Woche"),
        "Ü55": ("Lying Hamstring Curl (langsam)",   "3", "12",            "2×/Woche"),
    },
    "Power RDL": {
        "U10": ("Hinge Körpergewicht",              "2", "10",            "2×/Woche"),
        "U14": ("RDL leicht (Körpergewicht)",       "3", "8 je Seite",   "2×/Woche"),
    },
    "Sprung aus Kniebeuge": {
        "U10": ("Squat Körpergewicht (langsam)",    "2", "10",            "3×/Woche"),
    },
    # ── Sprint-Übungen (U10: Technik statt Intensität) ─────────────────────────
    "10 m Sprintstarts": {
        "U10": ("Lauf-ABC — Knieheben (technisch)",  "3", "15 Meter",    "2×/Woche"),
    },
    "Resistenz-Sprints (Band)": {
        "U10": ("Steigerungsläufe (technisch)",     "4", "30 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (moderat)",       "4", "20 Meter",     "2×/Woche"),
    },
    "20–30 m Maximalsprints": {
        "U10": ("Lauf-ABC + kurze Steigerung",      "4", "20 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (70–80 %)",       "4", "20 Meter",     "1×/Woche"),
    },
    "Fliegende 30er": {
        "U10": ("Fahrtenspiele 20 m",               "4", "20 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (fliegend)",       "4", "20 Meter",     "1×/Woche"),
    },
    "Bergaufsprints": {
        "U10": ("Bergauflaufen (locker)",            "4", "20 Meter",     "1×/Woche"),
        "Ü55": ("Bergaufgehen (zügig)",              "4", "30 Meter",     "1×/Woche"),
    },
    # ── Rumpfübungen ──────────────────────────────────────────────────────────
    "Medizinball Rotationswurf": {
        "U10": ("Pallof Press (Gummiband)",         "2", "10",            "2×/Woche"),
    },
    "Landmine Rotation": {
        "U10": ("Russischer Twist (leicht)",        "2", "12",            "2×/Woche"),
        "U14": ("Landmine Rotation (leicht)",       "3", "8 je Seite",   "2×/Woche"),
    },
    # ── Hip Thrust / Explosiv-Hüfte ───────────────────────────────────────────
    "Explosiver Hip Thrust": {
        "U10": ("Einbeinige Hüftbrücke (normal)",   "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Hip Thrust (langsam, Körpergewicht)", "3", "10",        "2×/Woche"),
    },
    "Lateral Bound stabilisiert": {
        "U10": ("Seitensprung Boden (kurz)",        "2", "5 je Seite",   "2×/Woche"),
    },
    # ── Sprunggelenk Power ────────────────────────────────────────────────────
    "Ankle Jumps reaktiv": {
        "U10": ("Pogo Hops beidbeinig (kurz)",      "2", "6 Sekunden",   "2×/Woche"),
    },
    "Lateral Hops reaktiv": {
        "U10": ("Seitliche Schritte mit Balance",   "2", "6 je Seite",   "2×/Woche"),
    },
    "Einbeinige Hüpfsprints": {
        "U10": ("Beidbeinige Hops (Boden)",         "2", "15 Meter",     "1×/Woche"),
        "Ü55": ("Gehsprints (zügig)",               "3", "20 Meter",     "2×/Woche"),
    },
}


def _ersatz_uebung(uebung: str, plangruppe: str) -> tuple | None | str:
    """
    Gibt einen alternativen Übungseintrag zurück, wenn die Übung für die
    Plangruppe nicht geeignet ist. None = Übung weglassen. "ok" = keine Änderung.
    """
    ersatz = _ALTERS_ERSATZ.get(uebung, {})
    if plangruppe in ersatz:
        return ersatz[plangruppe]  # (uebung, saetze, volumen, haeufigkeit) oder None
    return "ok"


def _saetze_begrenzen(saetze_str: str, max_saetze: int) -> str:
    """Begrenzt die Satzzahl gemäß Konfiguration der Altersgruppe."""
    try:
        s = int(saetze_str)
        return str(min(s, max_saetze))
    except (ValueError, TypeError):
        return saetze_str


def _haeufigkeit_begrenzen(haeuf: str, cap: str | None) -> str:
    """Begrenzt Trainingshäufigkeit (z. B. U10/Ü55 max 2×/Woche)."""
    if not cap:
        return haeuf
    h = haeuf or ""
    if "3×" in h: return h.replace("3×", cap)
    if "4×" in h: return h.replace("4×", cap)
    return h


def _max_pool_key(pool_key: str, max_key: str) -> str:
    """Begrenzt pool_key auf das Alter-Maximum (Hierarchie: stabilisation < kraft < power)."""
    rangfolge = {"stabilisation": 0, "kraft": 1, "power": 2}
    if rangfolge.get(pool_key, 1) > rangfolge.get(max_key, 2):
        return max_key
    return pool_key

def _tags_fuer_haeufigkeit(haeuf: str) -> list[int]:
    """Return training-day tags for a given haeufigkeit string."""
    h = (haeuf or "").lower()
    if "4×" in h or "4x" in h:
        return [1, 2, 3, 4]
    if "3×" in h or "3x" in h:
        return [1, 2, 3]
    if "2×" in h or "2x" in h:
        return [1, 3]   # Montag / Donnerstag
    return [2]           # 1×/Woche → Mitte der Woche


def trainingsplan_multi_erstellen(spieler_id: int, schwerpunkt_text: str,
                                  wochen: int = 8,
                                  alter: float | None = None) -> int:
    """
    Altersbasierter Trainingsplan in die trainingsplan-Tabelle.
    Quelle: Faigenbaum & Myer (2010), Lloyd et al. (2014), NSCA Youth RT Position Statement.
    """
    wochen = wochen if wochen in (4, 6, 8) else 8
    scores = defizit_score(schwerpunkt_text)
    plangruppe = _alter_zu_plangruppe(alter)
    cfg        = _PLANGRUPPEN_CONFIG[plangruppe]

    base_pool_key = "stabilisation" if wochen <= 4 else "kraft" if wochen <= 8 else "power"
    # Alters-Beschränkung: z. B. U10 darf nie "power" nutzen
    pool_key = _max_pool_key(base_pool_key, cfg["max_pool_key"])

    from database import trainingsplan_loeschen, trainingsplan_eintrag_speichern
    from datetime import date
    trainingsplan_loeschen(spieler_id)

    total = 0
    for w in range(1, wochen + 1):
        pos       = (w - 1) % 4
        is_deload = pos == 3
        offset    = (w - 1) // 4

        sorted_areas = sorted(scores.items(), key=lambda x: -x[1])
        for area, score in sorted_areas:
            n = max(0, score - 1) if is_deload else score
            exercises = _pool_fuer_area(area, pool_key, n, offset=offset)
            for uebung, saetze, volumen, haeufigkeit in exercises:
                # Altersgerechte Übungssubstitution prüfen
                ersatz = _ersatz_uebung(uebung, plangruppe)
                if ersatz is None:
                    continue  # Übung für diese Altersgruppe nicht geeignet
                if ersatz != "ok":
                    uebung, saetze, volumen, haeufigkeit = ersatz

                if is_deload:
                    haeufigkeit = haeufigkeit.replace("3×", "2×").replace("4×", "2×")
                # Altersbedingte Begrenzungen
                saetze      = _saetze_begrenzen(saetze, cfg["max_saetze"])
                haeufigkeit = _haeufigkeit_begrenzen(haeufigkeit, cfg["haeuf_cap"])
                tags        = _tags_fuer_haeufigkeit(haeufigkeit)
                # Bereichs- + Altersbasierte Pause & Ausführung
                _pause, _aust = _pause_und_ausfuehrung(area, pool_key, is_deload, plangruppe)
                for tag in tags:
                    trainingsplan_eintrag_speichern(
                        spieler_id, str(date.today()), w,
                        area, uebung, saetze, volumen,
                        haeufigkeit,
                        tag=tag,
                        pause_sekunden=_pause,
                        ausfuehrung=_aust,
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
