"""
Periodization engine v3 — 4-Phase progression, deficit-driven, scientifically structured.

Sports-science design (Faigenbaum & Myer 2010; Lloyd et al. 2014; NSCA 2016):

  Phase 1 (W1–2):  Grundlagen         — Mobilität, Bewegungsqualität, Aktivierung
  Phase 2 (W3–5):  Stabilität & Kraft — Core-Stabilität, Gelenkstabilität, Kraftaufbau
  Phase 3 (W6–8):  Leistungsentwicklung— Schnellkraft, Sprint, Richtungswechsel, Explosivität
  Phase 4 (W9–12): Fußballspezifisch  — RSA, Reaktivkraft, Belastungssteuerung, Prävention

Key improvements vs. v2:
  • No identical training weeks — exercise offset rotates every week within each phase
  • Pool expanded to 6 exercises per area/phase → 12-week plan stays variation-rich
  • Phase-progressive pool_key per week (stabilisation → kraft → power)
  • Volume/intensity increase explicitly encoded in per-week config table (_WOCHE_PLAN)
  • Phase 4 always boosts Fußball-specific work regardless of diagnostics
  • Deficit scoring unchanged: primary=3, secondary=2, tertiary=1
"""

from database import (
    periodisierung_loeschen, periodisierung_bulk_insert, periodisierung_laden,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern,
)

# ─────────────────────────────────────────────────────────────────────────────
# Exercise pool  (area → phase-key → list of (uebung, saetze, volumen, haeuf))
# 6 exercises per area/phase → enables 6 unique weeks without cycling
# ─────────────────────────────────────────────────────────────────────────────

_POOL: dict[str, dict[str, list]] = {

    "Rumpf": {
        "stabilisation": [
            ("Dead Bug",                    "3", "8 je Seite",    "3×/Woche"),
            ("Plank",                       "3", "40 Sekunden",   "3×/Woche"),
            ("Pallof Press",                "3", "12",            "3×/Woche"),
            ("Seitstütz",                   "3", "30 Sekunden",   "3×/Woche"),
            ("Hollow Body Hold",            "3", "20 Sekunden",   "3×/Woche"),
            ("Bird Dog",                    "3", "10 je Seite",   "3×/Woche"),
        ],
        "kraft": [
            ("Ab Wheel Rollout",            "3", "8",             "3×/Woche"),
            ("Plank mit Armheben",          "3", "10 je Seite",   "3×/Woche"),
            ("Pallof Press Stand",          "3", "12",            "3×/Woche"),
            ("Russischer Twist",            "3", "16",            "2×/Woche"),
            ("Cable Woodchop",              "3", "12 je Seite",   "2×/Woche"),
            ("Copenhagen Side Plank Dyn.", "3", "8 je Seite",    "2×/Woche"),
        ],
        "power": [
            ("Medizinball Rotationswurf",   "4", "8",             "2×/Woche"),
            ("Landmine Rotation",           "3", "10",            "2×/Woche"),
            ("Hanging Knee Raise",          "3", "12",            "2×/Woche"),
            ("Farmer's Walk",               "3", "30 Meter",      "2×/Woche"),
            ("Medizinball Chest Pass",      "4", "8",             "2×/Woche"),
            ("Kabelzug Sprungrotation",     "3", "8 je Seite",    "2×/Woche"),
        ],
    },

    "Hüfte": {
        "stabilisation": [
            ("Seitliches Miniband Gehen",   "3", "12 Meter",      "3×/Woche"),
            ("90/90 Hüftrotation",          "3", "10",            "2×/Woche"),
            ("Einbeinige Hüftbrücke",       "3", "10 je Seite",   "3×/Woche"),
            ("Copenhagen Plank (kurz)",     "3", "20 Sekunden",   "3×/Woche"),
            ("Monster Walk (Band)",         "3", "15 Meter",      "3×/Woche"),
            ("Side-Lying Clam Shell",       "3", "15 je Seite",   "3×/Woche"),
        ],
        "kraft": [
            ("Copenhagen Plank",            "3", "30 Sekunden",   "3×/Woche"),
            ("Einbeiniges Hip Hinge",       "3", "8 je Seite",    "3×/Woche"),
            ("Banded Lateral Walk",         "3", "15 Meter",      "3×/Woche"),
            ("Hip Thrust",                  "4", "10",            "2×/Woche"),
            ("Sumo Deadlift",               "3", "8",             "2×/Woche"),
            ("Lateral Step-Up",             "3", "10 je Seite",   "2×/Woche"),
        ],
        "power": [
            ("Explosiver Hip Thrust",       "4", "6",             "2×/Woche"),
            ("Lateral Bound stabilisiert",  "3", "6 je Seite",    "2×/Woche"),
            ("Single-Leg Glute Bridge +Gew","3", "8",             "2×/Woche"),
            ("Resisted Hip Abduction",      "3", "12",            "2×/Woche"),
            ("Broad Jump aus Hüfte",        "4", "5",             "2×/Woche"),
            ("Kettlebell Swing einbeinig",  "3", "10 je Seite",   "2×/Woche"),
        ],
    },

    "Knie": {
        "stabilisation": [
            ("Single Leg Squat (Qualität)", "3", "8 je Seite",    "3×/Woche"),
            ("Step Down",                   "3", "8 je Seite",    "2×/Woche"),
            ("Seitliche Miniband Squats",   "3", "10",            "2×/Woche"),
            ("Valgus-Kontroll Lunge",       "3", "8 je Seite",    "2×/Woche"),
            ("Terminal Knee Ext. (Band)",   "3", "15 je Seite",   "3×/Woche"),
            ("Slow Squat (5 s Exzentrik)",  "3", "8",             "2×/Woche"),
        ],
        "kraft": [
            ("Bulgarian Split Squat",       "3", "8 je Seite",    "2×/Woche"),
            ("Reverse Lunge",               "3", "10 je Seite",   "2×/Woche"),
            ("Box Squat",                   "4", "6",             "2×/Woche"),
            ("Single Leg Leg Press",        "3", "10 je Seite",   "2×/Woche"),
            ("Walking Lunge",               "3", "12 je Seite",   "2×/Woche"),
            ("Front Squat (leicht)",        "4", "8",             "2×/Woche"),
        ],
        "power": [
            ("Drop Landing → Sprung",       "4", "5",             "2×/Woche"),
            ("Bounding",                    "4", "20 Meter",      "2×/Woche"),
            ("Single Leg Jump & Stabi",     "3", "5 je Seite",    "2×/Woche"),
            ("Box Jump einbeinig",          "3", "4 je Seite",    "1×/Woche"),
            ("Split Jump",                  "4", "6 je Seite",    "2×/Woche"),
            ("Lateral Box Jump",            "3", "4 je Seite",    "1×/Woche"),
        ],
    },

    "Sprunggelenk": {
        "stabilisation": [
            ("Knie zur Wand Mobilisation",  "3", "10 je Seite",   "3×/Woche"),
            ("Einbeinstand Balance Pad",    "3", "30 Sekunden",   "3×/Woche"),
            ("Einbeinige Wadenheben",       "3", "15",            "3×/Woche"),
            ("Fersengang / Zehengang",      "3", "15 Meter",      "2×/Woche"),
            ("Fußkreisen einbeinig",        "3", "10 je Richtung","3×/Woche"),
            ("Einbeinstand (Augen zu)",     "3", "20 Sekunden",   "3×/Woche"),
        ],
        "kraft": [
            ("Single Leg Calf Raise (Treppe)","4","12",           "3×/Woche"),
            ("Ankle Banded Dorsiflexion",   "3", "15",            "2×/Woche"),
            ("Pogo Hops beidbeinig",        "3", "10 Sekunden",   "3×/Woche"),
            ("Einbeinige Pogo Hops",        "3", "10 je Seite",   "2×/Woche"),
            ("Banded Tibialis Raise",       "3", "15",            "3×/Woche"),
            ("Seated Calf Raise",           "4", "15",            "3×/Woche"),
        ],
        "power": [
            ("Ankle Jumps reaktiv",         "4", "8",             "2×/Woche"),
            ("Depth Drop → Sprung",         "3", "5",             "1×/Woche"),
            ("Lateral Hops reaktiv",        "3", "8 je Seite",    "2×/Woche"),
            ("Einbeinige Hüpfsprints",      "4", "20 Meter",      "2×/Woche"),
            ("Springseil (Einzel)",         "3", "30 Sekunden",   "2×/Woche"),
            ("Box Drop Einbeinig",          "3", "4 je Seite",    "1×/Woche"),
        ],
    },

    "Oberschenkel": {
        "stabilisation": [
            ("Nordic Hamstring Eccentric",  "3", "5",             "2×/Woche"),
            ("Einbeiniges RDL (leicht)",    "3", "8",             "2×/Woche"),
            ("Lying Hamstring Curl",        "3", "10",            "2×/Woche"),
            ("Gluteal Bridge Variante",     "3", "12",            "2×/Woche"),
            ("Prone Hip Ext. (isometr.)",   "3", "20 Sekunden",   "2×/Woche"),
            ("Hamstring Wall Bridge",       "3", "10",            "2×/Woche"),
        ],
        "kraft": [
            ("Nordic Hamstring Curl",       "3", "6",             "2×/Woche"),
            ("Romanian Deadlift einbeinig", "3", "8 je Seite",    "2×/Woche"),
            ("Seated Leg Curl",             "4", "10",            "2×/Woche"),
            ("Good Morning",               "3", "10",            "2×/Woche"),
            ("Einbeinige Kniebeuge (halb)", "3", "8 je Seite",    "2×/Woche"),
            ("Nordic Eccentric (Band-Ass.)","3", "6",             "2×/Woche"),
        ],
        "power": [
            ("Explosive Nordic",            "4", "4",             "1×/Woche"),
            ("Hamstring Sliders reaktiv",   "3", "6",             "2×/Woche"),
            ("Power RDL",                   "4", "5",             "2×/Woche"),
            ("Sprung aus Kniebeuge",        "3", "5",             "2×/Woche"),
            ("Glute Ham Raise",             "4", "5",             "1×/Woche"),
            ("Einbeiniger Sprung aus Stand","3", "5 je Seite",    "2×/Woche"),
        ],
    },

    "Schnelligkeit": {
        "stabilisation": [
            ("Lauf-ABC (A-Skip)",           "4", "20 Meter",      "2×/Woche"),
            ("Steigerungsläufe",            "4", "40 Meter",      "2×/Woche"),
            ("Lauf-ABC (B-Skip)",           "4", "20 Meter",      "2×/Woche"),
            ("Anfersen / Knieheben",        "4", "20 Meter",      "2×/Woche"),
            ("Koordinationsleiter Sprint",  "4", "Durchgänge",    "2×/Woche"),
            ("Schrittfrequenz-Drills",      "3", "15 Meter",      "2×/Woche"),
        ],
        "kraft": [
            ("10 m Sprintstarts",           "6", "10 m",          "2×/Woche"),
            ("Beschleunigungs-ABC",         "4", "20 Meter",      "2×/Woche"),
            ("Wall Drills",                 "3", "10 je Seite",   "2×/Woche"),
            ("Resistenz-Sprints (Band)",    "4", "20 Meter",      "1×/Woche"),
            ("Gewichtete Sprintstarts",     "5", "10 m",          "2×/Woche"),
            ("Fallsprints (Partnerfreigabe)","6","10 m",          "2×/Woche"),
        ],
        "power": [
            ("20–30 m Maximalsprints",      "6", "30 m",          "1×/Woche"),
            ("Reaktionssprints",            "6", "10 m",          "2×/Woche"),
            ("Fliegende 30er",              "4", "30 m",          "1×/Woche"),
            ("Bergaufsprints",              "6", "20 m",          "1×/Woche"),
            ("Max. 10 m Wdh.-Sprints",     "8", "10 m",          "1×/Woche"),
            ("Flying 20 m",                "4", "20 m",          "1×/Woche"),
        ],
    },

    "Explosivität": {
        "stabilisation": [
            ("Koordinations-Hops",          "3", "3×5 m",         "2×/Woche"),
            ("Squat Jump Einführung",       "3", "5",             "2×/Woche"),
            ("Knieheben einbeinig",         "3", "10 je Seite",   "2×/Woche"),
            ("Balance → Sprung Intro",      "3", "5",             "2×/Woche"),
            ("Tiefknie-Absprung (Technik)", "3", "6",             "2×/Woche"),
            ("Zweischritt-Absprung",        "3", "6",             "2×/Woche"),
        ],
        "kraft": [
            ("Squat Jump",                  "4", "6",             "2×/Woche"),
            ("Box Jump beidbeinig",         "4", "5",             "2×/Woche"),
            ("Medicine Ball Slam",          "3", "8",             "2×/Woche"),
            ("Hürdensprünge",               "3", "5",             "1×/Woche"),
            ("Kettlebell Swing",            "4", "10",            "2×/Woche"),
            ("Trap Bar Jump (leicht)",      "3", "5",             "2×/Woche"),
        ],
        "power": [
            ("Depth Jump",                  "4", "4",             "1×/Woche"),
            ("Einbeinige Plyo Sprünge",     "4", "5 je Seite",    "1×/Woche"),
            ("Box Jump maximal",            "5", "4",             "2×/Woche"),
            ("Reaktive Sprünge (DJ-RSI)",   "4", "5",             "1×/Woche"),
            ("Bounding (Weitsprung)",       "4", "5",             "2×/Woche"),
            ("Plyo Push-Up",               "3", "6",             "2×/Woche"),
        ],
    },

    "Agilität": {
        "stabilisation": [
            ("Footwork Leitertraining",     "4", "Durchgänge",    "2×/Woche"),
            ("Deceleration Drill",          "5", "10 m",          "2×/Woche"),
            ("Hexagon Drill",               "4", "Durchgänge",    "2×/Woche"),
            ("Lateral Shuffle (Technik)",   "4", "10 m",          "2×/Woche"),
            ("Seitwärtslauf Koordination",  "4", "15 m",          "2×/Woche"),
            ("Kreuzschritt-Drill",          "4", "10 m",          "2×/Woche"),
        ],
        "kraft": [
            ("5-10-5 Shuttle",              "5", "Durchgänge",    "2×/Woche"),
            ("Pro Agility Drill",           "5", "Durchgänge",    "1×/Woche"),
            ("T-Test",                      "4", "Durchgänge",    "1×/Woche"),
            ("Seitwärts Sprints",           "6", "10 m",          "2×/Woche"),
            ("L-Drill",                     "5", "Durchgänge",    "1×/Woche"),
            ("Backwards Sprint",            "6", "10 m",          "2×/Woche"),
        ],
        "power": [
            ("Randomized Agility (Signal)", "5", "Durchgänge",    "2×/Woche"),
            ("Illinois Test Tempo",         "4", "Durchgänge",    "1×/Woche"),
            ("COD Speed Drills",            "5", "Durchgänge",    "2×/Woche"),
            ("Fußball-Agility Parcours",    "4", "Durchgänge",    "1×/Woche"),
            ("Drop-Step → Sprint",          "5", "Durchgänge",    "2×/Woche"),
            ("Reaktions-Agility-Parcours",  "5", "Durchgänge",    "1×/Woche"),
        ],
    },

    "Fußball": {
        "stabilisation": [
            ("Einbeinige Ballkontakte",     "3", "60 Sekunden",   "2×/Woche"),
            ("Ballkontrolle Gleichgewicht", "3", "60 Sekunden",   "2×/Woche"),
            ("Fußballkoordination Leiter",  "4", "Durchgänge",    "2×/Woche"),
            ("Einbeiniges Torwarttraining", "3", "45 Sekunden",   "2×/Woche"),
            ("Technik Passspiel (Kontrol.)","3", "60 Sekunden",   "2×/Woche"),
            ("1-Touch-Kontrolle einbeinig", "3", "45 Sekunden",   "2×/Woche"),
        ],
        "kraft": [
            ("Partner Widerstandsdrücken",  "3", "10 Sekunden",   "2×/Woche"),
            ("Zweikampf Stabilität",        "3", "20 Sekunden",   "2×/Woche"),
            ("Koordination Leitertraining", "5", "Durchgänge",    "2×/Woche"),
            ("Ballführung unter Druck",     "4", "30 Sekunden",   "2×/Woche"),
            ("Pressing-Simulation mit Ball","4", "20 Sekunden",   "2×/Woche"),
            ("Sprung-Kopfball-Vorbereitung","3", "8",             "2×/Woche"),
        ],
        "power": [
            ("Repeated Sprint Ability (RSA)","6","30 m",          "1×/Woche"),
            ("30-30 Intervallläufe",        "10","30 Sekunden",   "1×/Woche"),
            ("Pressingsimulation",          "5", "30 Sekunden",   "2×/Woche"),
            ("Schusstraining explosiv",     "4", "8 je Seite",    "1×/Woche"),
            ("RSA + Ballkontrolle",         "6", "30 m",          "1×/Woche"),
            ("High-Int. Dribbling-Intervall","5","30 Sekunden",   "2×/Woche"),
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Per-week plan configuration — explicit, no formulas
# Each entry: (pool_key, phase_name, phase_ziel, is_deload, vol_mult, offset)
#
# offset: rotation index into the exercise pool for this week.
#         Different offset = different exercises selected from the same pool.
#         Resets to 0 when pool_key changes (new phase = fresh exercise set).
# vol_mult: 1.0 = baseline, 1.15 = +1 Satz, 0.70 = Deload (–1 Satz)
# ─────────────────────────────────────────────────────────────────────────────

_WOCHE_PLAN: dict[int, list[tuple]] = {

    12: [
        # Phase 1 — Grundlagen (W1–2): Mobilität, Bewegungsqualität, Technik
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.00, 0),
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.10, 1),
        # Phase 2 — Stabilität & Kraft (W3–5): Core, Gelenkstabilität, Kraftaufbau
        ("stabilisation","Phase 2 — Stabilität & Kraft",  "Core-Stabilität & Gelenkstabilität",               False, 1.15, 2),
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Funktionelle Stärke & Bewegungskontrolle",         False, 1.00, 0),
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Funktionelle Stärke & Kraftaufbau",                False, 1.15, 1),
        # Phase 3 — Leistungsentwicklung (W6–8): Schnellkraft, Sprint, Explosivität
        ("kraft",        "Phase 3 — Leistungsentwicklung","Schnellkraft, Sprint & Beschleunigung",             False, 1.20, 2),
        ("power",        "Phase 3 — Leistungsentwicklung","Explosivkraft, Richtungswechsel & Reaktivkraft",    False, 1.10, 0),
        ("power",        "Phase 3 — Leistungsentwicklung","Intensivierung & Übergangs-Deload",                 True,  0.70, 1),
        # Phase 4 — Fußballspezifisch (W9–12): RSA, Reaktivkraft, Prävention
        ("power",        "Phase 4 — Fußballspezifisch",   "Fußballbewegungen & Reaktivkraft",                 False, 1.10, 2),
        ("power",        "Phase 4 — Fußballspezifisch",   "Repeated Sprint & Richtungswechsel unter Belastung",False, 1.20, 3),
        ("power",        "Phase 4 — Fußballspezifisch",   "Wettkampfvorbereitung & Belastungssteuerung",      False, 1.15, 4),
        ("power",        "Phase 4 — Fußballspezifisch",   "Abschluss & aktive Prävention",                    True,  0.70, 5),
    ],

    8: [
        # Phase 1 — Grundlagen (W1–2)
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.00, 0),
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.10, 1),
        # Phase 2 — Stabilität & Kraft (W3–5)
        ("stabilisation","Phase 2 — Stabilität & Kraft",  "Core-Stabilität & Gelenkstabilität",               False, 1.15, 2),
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Funktionelle Stärke & Kraftaufbau",                False, 1.00, 0),
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Kraftaufbau & Bewegungskontrolle",                 False, 1.15, 1),
        # Phase 3 — Leistungsentwicklung (W6–8)
        ("kraft",        "Phase 3 — Leistungsentwicklung","Schnellkraft, Sprint & Beschleunigung",             False, 1.20, 2),
        ("power",        "Phase 3 — Leistungsentwicklung","Explosivkraft & Richtungswechsel",                  False, 1.10, 0),
        ("power",        "Phase 3 — Leistungsentwicklung","Abschluss & Übergangs-Deload",                      True,  0.70, 1),
    ],

    6: [
        # Phase 1 — Grundlagen (W1–2)
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.00, 0),
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.10, 1),
        # Phase 2 — Stabilität & Kraft (W3–4)
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Core-Stabilität & Kraftaufbau",                    False, 1.00, 0),
        ("kraft",        "Phase 2 — Stabilität & Kraft",  "Funktionelle Stärke",                              False, 1.15, 1),
        # Phase 3 — Leistungsentwicklung (W5–6)
        ("power",        "Phase 3 — Leistungsentwicklung","Schnellkraft, Sprint & Explosivität",               False, 1.10, 0),
        ("power",        "Phase 3 — Leistungsentwicklung","Leistungsphase & Abschluss",                        True,  0.80, 1),
    ],

    4: [
        # Phase 1 — Grundlagen (W1–2)
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.00, 0),
        ("stabilisation","Phase 1 — Grundlagen",          "Mobilität, Bewegungsqualität & Aktivierung",       False, 1.10, 1),
        # Phase 2 — Stabilität (W3–4)
        ("kraft",        "Phase 2 — Stabilität",          "Core-Stabilität & Kraftaufbau",                    False, 1.00, 0),
        ("kraft",        "Phase 2 — Stabilität",          "Kraftaufbau & Abschluss",                          True,  0.80, 1),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Pause + Ausführung — bereichsspezifisch (unverändert aus v2)
# Quellen: Haff & Triplett (NSCA 2016); Zatsiorsky & Kraemer (2006);
#          Faigenbaum & Myer (2010); Buchheit & Laursen (2013)
# ─────────────────────────────────────────────────────────────────────────────

_BEREICH_PARAMS: dict[tuple[str, str], tuple[int, str]] = {
    ("Rumpf",         "stabilisation"): (45,  "2-1-2 s (Stabilisationsphase halten)"),
    ("Rumpf",         "kraft"):         (60,  "2-0-1 s (kontrolliert-exzentrisch)"),
    ("Rumpf",         "power"):         (90,  "Explosiv / reaktiv"),
    ("Hüfte",         "stabilisation"): (45,  "2-1-2 s (Hüftkontrolle betonen)"),
    ("Hüfte",         "kraft"):         (75,  "3-0-1 s (langsam exzentrisch)"),
    ("Hüfte",         "power"):         (90,  "Explosiv / max. Hüftextension"),
    ("Knie",          "stabilisation"): (45,  "2-1-2 s (Knieachse kontrollieren)"),
    ("Knie",          "kraft"):         (90,  "3-0-1 s (exzentrischer Fokus)"),
    ("Knie",          "power"):         (120, "Reaktiv / max. Explosivkraft"),
    ("Sprunggelenk",  "stabilisation"): (45,  "2-1-2 s (Balance & Bodenkontakt)"),
    ("Sprunggelenk",  "kraft"):         (60,  "2-0-1 s (Exzentrik Wadenheben)"),
    ("Sprunggelenk",  "power"):         (90,  "Reaktiv / max. Elastizität Achillessehne"),
    ("Oberschenkel",  "stabilisation"): (60,  "3-1-2 s (exzentrischer Hamstring-Fokus)"),
    ("Oberschenkel",  "kraft"):         (90,  "3-0-1 s (kontrolliert exzentrisch)"),
    ("Oberschenkel",  "power"):         (120, "Explosiv / max. Kraft — keine Ermüdung"),
    ("Schnelligkeit", "stabilisation"): (90,  "Max. Qualität / Lauf-ABC technisch"),
    ("Schnelligkeit", "kraft"):         (120, "Max. Intensität — volle ZNS-Erholung"),
    ("Schnelligkeit", "power"):         (180, "Max. Intensität — vollständige ZNS-Erholung"),
    ("Explosivität",  "stabilisation"): (60,  "Reaktiv / Qualität jede Wiederholung"),
    ("Explosivität",  "kraft"):         (90,  "Explosiv / volle Pause zwischen Sätzen"),
    ("Explosivität",  "power"):         (120, "Max. Explosivität — keine Ermüdung zulassen"),
    ("Agilität",      "stabilisation"): (60,  "Max. Richtungswechselqualität"),
    ("Agilität",      "kraft"):         (90,  "Max. Intensität / COD-Geschwindigkeit"),
    ("Agilität",      "power"):         (90,  "Reaktiv / signalbasiert — volle Konzentration"),
    ("Fußball",       "stabilisation"): (45,  "Technisch / kontrolliert"),
    ("Fußball",       "kraft"):         (60,  "Mittel-intensiv / wettkampfnah"),
    ("Fußball",       "power"):         (60,  "Wettkampfintensität — kurze Pausen (RSA)"),
}

_PAUSE_FALLBACK:       dict[str, int] = {"stabilisation": 45, "kraft": 90, "power": 120}
_AUSFUEHRUNG_FALLBACK: dict[str, str] = {
    "stabilisation": "2-1-2 s (kontrolliert)",
    "kraft":         "3-0-1 s (exzentrisch-konzentrisch)",
    "power":         "Explosiv / max. Geschwindigkeit",
}


# ─────────────────────────────────────────────────────────────────────────────
# Altersbasiertes Planungs-System
# ─────────────────────────────────────────────────────────────────────────────

def _alter_zu_plangruppe(alter: float | None) -> str:
    if not alter or alter <= 0:
        return "Senior"
    a = int(alter)
    if a <= 10: return "U10"
    if a <= 14: return "U14"
    if a <= 18: return "U18"
    if a <= 35: return "Senior"
    if a <= 50: return "Ü40"
    return "Ü55"


_PLANGRUPPEN_CONFIG: dict[str, dict] = {
    "U10": {
        "max_pool_key":    "stabilisation",
        "pause_offset":    45,
        "ausfuehr_prefix": "Technisch / Körpergefühl entwickeln — kein Tempo-Ziel · ",
        "max_saetze":      2,
        "haeuf_cap":       "2×",
        "label":           "U10 — Koordination & Bewegungsbildung",
    },
    "U14": {
        "max_pool_key":    "kraft",
        "pause_offset":    20,
        "ausfuehr_prefix": "Technisch kontrolliert · ",
        "max_saetze":      3,
        "haeuf_cap":       None,
        "label":           "U14 — Technischer Aufbau & Intro Krafttraining",
    },
    "U18": {
        "max_pool_key":    "power",
        "pause_offset":    10,
        "ausfuehr_prefix": "",
        "max_saetze":      99,
        "haeuf_cap":       None,
        "label":           "U18 — Strukturiertes Athletiktraining",
    },
    "Senior": {
        "max_pool_key":    "power",
        "pause_offset":    0,
        "ausfuehr_prefix": "",
        "max_saetze":      99,
        "haeuf_cap":       None,
        "label":           "Senior — Vollständiges Leistungstraining",
    },
    "Ü40": {
        "max_pool_key":    "power",
        "pause_offset":    20,
        "ausfuehr_prefix": "Kontrolliert / gelenkschonend · ",
        "max_saetze":      99,
        "haeuf_cap":       None,
        "label":           "Ü40 — Erhalt & Verletzungsprävention",
    },
    "Ü55": {
        "max_pool_key":    "kraft",
        "pause_offset":    40,
        "ausfuehr_prefix": "Sehr kontrolliert / gelenkschonend · ",
        "max_saetze":      3,
        "haeuf_cap":       "2×",
        "label":           "Ü55 — Funktionelle Stärke & Gelenkschonung",
    },
}


# Übungsersatz für altersungeeignete Übungen
_ALTERS_ERSATZ: dict[str, dict[str, tuple | None]] = {
    "Nordic Hamstring Eccentric": {
        "U10": ("Einbeinige Hüftbrücke",              "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Nordic Hamstring Eccentric (assist.)","3", "4",           "2×/Woche"),
    },
    "Nordic Hamstring Curl": {
        "U10": ("Einbeinige Hüftbrücke",              "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",    "3", "4",            "2×/Woche"),
        "Ü55": ("Lying Hamstring Curl (Maschine)",    "3", "12",           "2×/Woche"),
    },
    "Nordic Eccentric (Band-Ass.)": {
        "U10": ("Einbeinige Hüftbrücke",              "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",    "3", "4",            "2×/Woche"),
    },
    "Box Squat": {
        "U10": ("Mini-Squat Körpergewicht",           "2", "12",           "3×/Woche"),
        "U14": ("Goblet Squat (leicht)",              "3", "10",           "2×/Woche"),
    },
    "Bulgarian Split Squat": {
        "U10": ("Ausfallschritt Körpergewicht",       "2", "8 je Seite",   "3×/Woche"),
        "U14": ("Ausfallschritt Körpergewicht",       "3", "8 je Seite",   "2×/Woche"),
    },
    "Single Leg Leg Press": {
        "U10": ("Einbeiniger Kniestand (Balance)",    "2", "10 je Seite",  "2×/Woche"),
    },
    "Front Squat (leicht)": {
        "U10": ("Goblet Squat Körpergewicht",         "2", "12",           "3×/Woche"),
    },
    "Good Morning": {
        "U10": ("Hinge-Bewegung Körpergewicht",       "2", "10",           "2×/Woche"),
        "U14": ("Rumänisches Kreuzheben (leicht)",    "3", "10",           "2×/Woche"),
    },
    "Sumo Deadlift": {
        "U10": ("Sumo-Squat Körpergewicht",           "2", "12",           "3×/Woche"),
        "U14": ("Sumo-Squat (leicht)",                "3", "10",           "2×/Woche"),
    },
    "Ab Wheel Rollout": {
        "U10": ("Plank mit Armheben",                 "2", "8 je Seite",   "3×/Woche"),
        "U14": ("Rollout (klein, kniend)",             "3", "6",            "2×/Woche"),
    },
    "Hanging Knee Raise": {
        "U10": ("Beckenheben liegend",                "2", "12",           "3×/Woche"),
        "U14": ("Knieheben an Stange (leicht)",       "3", "8",            "2×/Woche"),
    },
    "Farmer's Walk": {
        "U10": ("Einbeiniger Stand auf Wackelmatte",  "2", "30 Sekunden",  "2×/Woche"),
    },
    "Trap Bar Jump (leicht)": {
        "U10": ("Squat Jump Körpergewicht",           "2", "5",            "2×/Woche"),
        "U14": ("Squat Jump (leicht)",                "3", "5",            "2×/Woche"),
    },
    "Kettlebell Swing": {
        "U10": ("Hip Bridge reaktiv",                 "2", "10",           "2×/Woche"),
        "U14": ("Goblet Squat Swing-Intro",           "3", "8",            "2×/Woche"),
    },
    "Kettlebell Swing einbeinig": {
        "U10": ("Einbeinige Hüftbrücke reaktiv",      "2", "8 je Seite",   "2×/Woche"),
        "U14": ("Einbeiniges Hip Hinge (leicht)",     "3", "8 je Seite",   "2×/Woche"),
    },
    "Depth Jump": {
        "U10": ("Beidbeinige Sprünge (Boden)",        "2", "5",            "2×/Woche"),
        "U14": ("Box Jump (Höhe 30 cm)",              "3", "4",            "2×/Woche"),
        "Ü55": ("Box Step-Down kontrolliert",          "3", "6 je Seite",   "2×/Woche"),
    },
    "Depth Drop → Sprung": {
        "U10": ("Beidbeinige Sprünge (Boden)",        "2", "5",            "2×/Woche"),
        "U14": ("Drop Step → Squat",                  "3", "5",            "2×/Woche"),
        "Ü55": ("Box Step-Down kontrolliert",          "3", "6 je Seite",   "2×/Woche"),
    },
    "Einbeinige Plyo Sprünge": {
        "U10": ("Einbeiniger Stand + Rumpfrotation",  "2", "8 je Seite",   "2×/Woche"),
        "U14": ("Einbeinige Hops (niedrig)",          "3", "5 je Seite",   "1×/Woche"),
        "Ü55": ("Einbeinige Wadenheben (langsam)",    "3", "12 je Seite",  "2×/Woche"),
    },
    "Box Jump maximal": {
        "U10": ("Beidbeiniger Bodenabsprung",         "2", "5",            "2×/Woche"),
        "U14": ("Box Jump (Höhe 30–40 cm)",           "3", "4",            "2×/Woche"),
        "Ü55": ("Box Step-Up kontrolliert",            "3", "8 je Seite",   "2×/Woche"),
    },
    "Reaktive Sprünge (DJ-RSI)": {
        "U10": ("Koordinations-Hops (Boden)",         "2", "8",            "2×/Woche"),
        "U14": ("Ankle Jumps (niedrig)",              "3", "8",            "2×/Woche"),
        "Ü55": ("Pogo Hops (sehr leicht, kurz)",      "3", "8 Sekunden",   "2×/Woche"),
    },
    "Bounding (Weitsprung)": {
        "U10": ("Beidbeinige Hops (Boden)",           "2", "5",            "2×/Woche"),
        "U14": ("Bounding (niedrig, Qualität)",       "3", "5",            "2×/Woche"),
    },
    "Split Jump": {
        "U10": ("Ausfallschritt-Wechsel (langsam)",   "2", "6 je Seite",   "2×/Woche"),
        "U14": ("Split Jump (Körpergewicht)",         "3", "5 je Seite",   "1×/Woche"),
    },
    "Lateral Box Jump": {
        "U10": ("Seitensprung Boden (kurz)",          "2", "4 je Seite",   "2×/Woche"),
        "U14": ("Lateral Jump (niedrig)",             "3", "4 je Seite",   "1×/Woche"),
    },
    "Glute Ham Raise": {
        "U10": ("Einbeinige Hüftbrücke reaktiv",      "2", "8 je Seite",   "2×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",    "3", "4",            "1×/Woche"),
        "Ü55": ("Lying Hamstring Curl (langsam)",     "3", "10",           "2×/Woche"),
    },
    "Explosive Nordic": {
        "U10": ("Hip Bridge reaktiv",                 "2", "8",            "2×/Woche"),
        "U14": ("Nordic Eccentric (kontrolliert)",    "3", "4",            "1×/Woche"),
        "Ü55": ("Lying Hamstring Curl langsam",       "3", "10",           "2×/Woche"),
    },
    "Hamstring Sliders reaktiv": {
        "U10": ("Einbeinige Hüftbrücke",              "2", "10 je Seite",  "2×/Woche"),
        "U14": ("Hamstring Curl Maschine (leicht)",   "3", "10",           "2×/Woche"),
        "Ü55": ("Lying Hamstring Curl (langsam)",     "3", "12",           "2×/Woche"),
    },
    "Power RDL": {
        "U10": ("Hinge Körpergewicht",                "2", "10",           "2×/Woche"),
        "U14": ("RDL leicht (Körpergewicht)",         "3", "8 je Seite",   "2×/Woche"),
    },
    "Sprung aus Kniebeuge": {
        "U10": ("Squat Körpergewicht (langsam)",      "2", "10",           "3×/Woche"),
    },
    "10 m Sprintstarts": {
        "U10": ("Lauf-ABC — Knieheben (technisch)",   "3", "15 Meter",     "2×/Woche"),
    },
    "Gewichtete Sprintstarts": {
        "U10": ("Lauf-ABC Knieheben (technisch)",     "3", "15 Meter",     "2×/Woche"),
        "U14": ("Sprintstarts (ohne Gewicht)",        "5", "10 m",         "2×/Woche"),
    },
    "Fallsprints (Partnerfreigabe)": {
        "U10": ("Steigerungsläufe (technisch)",       "4", "30 Meter",     "2×/Woche"),
        "U14": ("Steigerungsläufe (schnell)",         "5", "30 Meter",     "2×/Woche"),
    },
    "Resistenz-Sprints (Band)": {
        "U10": ("Steigerungsläufe (technisch)",       "4", "30 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (moderat)",         "4", "20 Meter",     "2×/Woche"),
    },
    "20–30 m Maximalsprints": {
        "U10": ("Lauf-ABC + kurze Steigerung",        "4", "20 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (70–80 %)",         "4", "20 Meter",     "1×/Woche"),
    },
    "Max. 10 m Wdh.-Sprints": {
        "U10": ("Steigerungsläufe (kurz, technisch)", "4", "15 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (70 %)",            "4", "15 Meter",     "1×/Woche"),
    },
    "Fliegende 30er": {
        "U10": ("Fahrtenspiele 20 m",                 "4", "20 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (fliegend)",         "4", "20 Meter",     "1×/Woche"),
    },
    "Flying 20 m": {
        "U10": ("Steigerungsläufe 20 m",              "4", "20 Meter",     "2×/Woche"),
        "Ü55": ("Steigerungsläufe (70 %)",            "4", "20 Meter",     "1×/Woche"),
    },
    "Bergaufsprints": {
        "U10": ("Bergauflaufen (locker)",             "4", "20 Meter",     "1×/Woche"),
        "Ü55": ("Bergaufgehen (zügig)",               "4", "30 Meter",     "1×/Woche"),
    },
    "Medizinball Rotationswurf": {
        "U10": ("Pallof Press (Gummiband)",           "2", "10",           "2×/Woche"),
    },
    "Medizinball Chest Pass": {
        "U10": ("Wurfbewegung beidhändig (Luft)",     "2", "8",            "2×/Woche"),
        "U14": ("Medizinball Chest Pass (leicht)",    "3", "8",            "2×/Woche"),
    },
    "Landmine Rotation": {
        "U10": ("Russischer Twist (leicht)",          "2", "12",           "2×/Woche"),
        "U14": ("Landmine Rotation (leicht)",         "3", "8 je Seite",   "2×/Woche"),
    },
    "Explosiver Hip Thrust": {
        "U10": ("Einbeinige Hüftbrücke (normal)",     "2", "10 je Seite",  "3×/Woche"),
        "U14": ("Hip Thrust (langsam, Körpergew.)",   "3", "10",           "2×/Woche"),
    },
    "Lateral Bound stabilisiert": {
        "U10": ("Seitensprung Boden (kurz)",          "2", "5 je Seite",   "2×/Woche"),
    },
    "Ankle Jumps reaktiv": {
        "U10": ("Pogo Hops beidbeinig (kurz)",        "2", "6 Sekunden",   "2×/Woche"),
    },
    "Lateral Hops reaktiv": {
        "U10": ("Seitliche Schritte mit Balance",     "2", "6 je Seite",   "2×/Woche"),
    },
    "Einbeinige Hüpfsprints": {
        "U10": ("Beidbeinige Hops (Boden)",           "2", "15 Meter",     "1×/Woche"),
        "Ü55": ("Gehsprints (zügig)",                 "3", "20 Meter",     "2×/Woche"),
    },
    "Einbeiniger Sprung aus Stand": {
        "U10": ("Einbeiniges Hüpfen (Boden)",         "2", "5 je Seite",   "1×/Woche"),
        "U14": ("Einbeiniger Hop (kontrolliert)",     "3", "4 je Seite",   "1×/Woche"),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def defizit_score(schwerpunkt_text: str) -> dict[str, int]:
    """
    Parse the combined schwerpunkt text and return a priority score per area.
    Score: 3 = primary, 2 = secondary, 1 = tertiary.  Rumpf always ≥ 1.
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
        (["fußball", "fussball", "ausdauer", "aerob", "intermittier"], "Fußball"),
    ]
    counts: dict[str, int] = {}
    for keywords, area in _mapping:
        hits = sum(1 for kw in keywords if kw in txt)
        if hits > 0:
            counts[area] = hits
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
    scores.setdefault("Rumpf", 1)
    return scores


def _pool_fuer_area(area: str, pool_key: str, n: int, offset: int = 0) -> list:
    """Return up to n exercises from the pool, cycling with offset for variety."""
    exercises = _POOL.get(area, {}).get(pool_key, [])
    if not exercises:
        return []
    n = min(n, len(exercises))
    return [exercises[(offset + i) % len(exercises)] for i in range(n)]


def _pause_und_ausfuehrung(bereich: str, pool_key: str,
                            is_deload: bool = False,
                            plangruppe: str = "Senior") -> tuple[int, str]:
    """Gibt alters- und bereichsspezifische (pause_sek, ausfuehrung) zurück."""
    pause_s, ausfuehr = _BEREICH_PARAMS.get(
        (bereich, pool_key),
        (_PAUSE_FALLBACK.get(pool_key, 90), _AUSFUEHRUNG_FALLBACK.get(pool_key, "kontrolliert")),
    )
    cfg = _PLANGRUPPEN_CONFIG.get(plangruppe, _PLANGRUPPEN_CONFIG["Senior"])
    pause_s += cfg["pause_offset"]
    prefix = cfg["ausfuehr_prefix"]
    if prefix and not ausfuehr.startswith(prefix):
        ausfuehr = prefix + ausfuehr
    if is_deload:
        pause_s   = max(30, pause_s - 15)
        ausfuehr  = ausfuehr + " / leicht"
    return pause_s, ausfuehr


def _ersatz_uebung(uebung: str, plangruppe: str) -> tuple | None | str:
    ersatz = _ALTERS_ERSATZ.get(uebung, {})
    if plangruppe in ersatz:
        return ersatz[plangruppe]
    return "ok"


def _saetze_begrenzen(saetze_str: str, max_saetze: int) -> str:
    try:
        return str(min(int(saetze_str), max_saetze))
    except (ValueError, TypeError):
        return saetze_str


def _steigere_saetze(saetze_str: str, delta: int = 1) -> str:
    """Erhöht die Satzzahl um delta (für progressive Überlastung)."""
    try:
        return str(int(saetze_str) + delta)
    except (ValueError, TypeError):
        return saetze_str


def _haeufigkeit_begrenzen(haeuf: str, cap: str | None) -> str:
    if not cap:
        return haeuf
    h = haeuf or ""
    if "3×" in h: return h.replace("3×", cap)
    if "4×" in h: return h.replace("4×", cap)
    return h


def _max_pool_key(pool_key: str, max_key: str) -> str:
    rangfolge = {"stabilisation": 0, "kraft": 1, "power": 2}
    if rangfolge.get(pool_key, 1) > rangfolge.get(max_key, 2):
        return max_key
    return pool_key


def _tags_fuer_haeufigkeit(haeuf: str) -> list[int]:
    h = (haeuf or "").lower()
    if "4×" in h or "4x" in h: return [1, 2, 3, 4]
    if "3×" in h or "3x" in h: return [1, 2, 3]
    if "2×" in h or "2x" in h: return [1, 3]
    return [2]


# ─────────────────────────────────────────────────────────────────────────────
# Public API: Trainingsplan (4-Phase progression, week-by-week configuration)
# ─────────────────────────────────────────────────────────────────────────────

# ── Verletzungsbereich-Mapping (koerperteil → _POOL-Bereiche) ─────────────────
_VERLETZUNG_BEREICH_MAP: dict[str, list[str]] = {
    "Sprunggelenk":  ["Sprunggelenk"],
    "Knie":          ["Knie"],
    "Oberschenkel":  ["Oberschenkel", "Schnelligkeit", "Explosivität"],
    "Leiste":        ["Hüfte"],
    "Hüfte":         ["Hüfte"],
    "Lendenwirbel":  ["Rumpf"],
    "Schulter":      ["Schulter"],
    "Sonstiges":     [],
}


def verletzung_aktive_bereiche(verletzungen: list) -> set[str]:
    """Gibt die _POOL-Bereiche aktiver Verletzungen zurück (noch im Ausfall-Fenster)."""
    from datetime import date as _date, datetime as _dt, timedelta as _td
    bereiche: set[str] = set()
    heute = _date.today()
    for v in (verletzungen or []):
        ausfall = int(v.get("ausfall_tage") or 0)
        if ausfall <= 0:
            continue
        datum_str = str(v.get("datum") or "")
        try:
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    datum = _dt.strptime(datum_str, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                continue
            if datum + _td(days=ausfall) >= heute:
                koerperteil = str(v.get("koerperteil") or "")
                for b in _VERLETZUNG_BEREICH_MAP.get(koerperteil, []):
                    bereiche.add(b)
        except Exception:
            continue
    return bereiche


def trainingsplan_multi_erstellen(spieler_id: int, schwerpunkt_text: str,
                                  wochen: int = 8,
                                  alter: float | None = None,
                                  verletzung_bereiche: set | list | None = None,
                                  saison_phase: str = "Normal") -> int:
    """
    Altersbasierter Trainingsplan mit klarer 4-Phasen-Progression.
    Keine identischen Trainingswochen — Übungsoffset rotiert wochenweise.
    Phase 4 (W9–12) enthält immer Fußball-spezifische Einheiten.

    Progression:
      Phase 1 (W1–2):  stabilisation — Mobilität & Bewegungsqualität
      Phase 2 (W3–5):  stabilisation → kraft — Stabilität & Kraftaufbau
      Phase 3 (W6–8):  kraft → power — Leistungsentwicklung
      Phase 4 (W9–12): power — Fußballspezifisch & Belastungssteuerung

    saison_phase: "Normal" | "Vorbereitung" | "Saison" | "Nachsaison"
      - Normal/Vorbereitung: volle 4-Phasen-Progression
      - Saison:     Erhaltungstraining — reduziertes Volumen, kein Power, +Fußball
      - Nachsaison: Regeneration — nur Stabilisation, max. 4 Wochen

    verletzung_bereiche: Set von _POOL-Bereichsnamen, die ausgeschlossen werden sollen.
    """
    _verletzt = set(verletzung_bereiche or [])

    # Saisonperiode-Anpassungen
    _saison_max_key: str | None = None
    _saison_force_deload = False
    if saison_phase == "Saison":
        wochen = min(wochen, 4)
        _saison_max_key = "kraft"
        _saison_force_deload = True
    elif saison_phase == "Nachsaison":
        wochen = min(wochen, 4)
        _saison_max_key = "stabilisation"

    wochen = wochen if wochen in (4, 6, 8, 12) else 8
    basis_scores = defizit_score(schwerpunkt_text)
    plangruppe   = _alter_zu_plangruppe(alter)
    cfg          = _PLANGRUPPEN_CONFIG[plangruppe]
    woche_config = _WOCHE_PLAN[wochen]

    from database import trainingsplan_loeschen, trainingsplan_eintrag_speichern
    from datetime import date
    trainingsplan_loeschen(spieler_id)

    total = 0

    for w_idx, (pool_key, phase_name, phase_ziel, is_deload, vol_mult, offset) in enumerate(woche_config):
        woche    = w_idx + 1

        # Saison-Anpassungen auf Pool-Key
        if _saison_force_deload:
            is_deload = True
        pool_key = _max_pool_key(pool_key, cfg["max_pool_key"])
        if _saison_max_key:
            pool_key = _max_pool_key(pool_key, _saison_max_key)

        # Phase 4 / Saison-Phase: Fußball als Sekundärbereich einschließen
        scores = dict(basis_scores)
        if "Phase 4" in phase_name or saison_phase == "Saison":
            scores["Fußball"] = max(scores.get("Fußball", 0), 2)

        sorted_areas = sorted(scores.items(), key=lambda x: -x[1])

        for area, score in sorted_areas:
            # ── Verletzungs-Filter: verletzte Bereiche überspringen ───────────
            if area in _verletzt:
                continue
            # Deload: deutlich reduziertes Volumen
            if is_deload:
                n = max(0, score - 2)  # primär=1, sekundär=0, tertiär=0
            else:
                n = score              # primär=3, sekundär=2, tertiär=1

            if n <= 0:
                continue

            exercises = _pool_fuer_area(area, pool_key, n, offset=offset)

            for uebung, saetze, volumen, haeufigkeit in exercises:
                # Altersgerechter Übungsersatz
                ersatz = _ersatz_uebung(uebung, plangruppe)
                if ersatz is None:
                    continue
                if ersatz != "ok":
                    uebung, saetze, volumen, haeufigkeit = ersatz

                # Deload: Häufigkeit reduzieren
                if is_deload:
                    haeufigkeit = haeufigkeit.replace("3×", "2×").replace("4×", "2×")

                # Progressive Überlastung: ab vol_mult ≥ 1.15 einen Satz mehr
                if not is_deload and vol_mult >= 1.15:
                    saetze = _steigere_saetze(saetze, 1)

                saetze      = _saetze_begrenzen(saetze, cfg["max_saetze"])
                haeufigkeit = _haeufigkeit_begrenzen(haeufigkeit, cfg["haeuf_cap"])
                tags        = _tags_fuer_haeufigkeit(haeufigkeit)
                pause, aust = _pause_und_ausfuehrung(area, pool_key, is_deload, plangruppe)

                for tag in tags:
                    trainingsplan_eintrag_speichern(
                        spieler_id, str(date.today()), woche,
                        area, uebung, saetze, volumen,
                        haeufigkeit,
                        tag=tag,
                        pause_sekunden=pause,
                        ausfuehrung=aust,
                    )
                    total += 1

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Public API: Periodisierungszyklus (used by the Periodisierung page)
# ─────────────────────────────────────────────────────────────────────────────

# Phase definitions for zyklus_erstellen (12-week macrocycle)
_PHASEN = [
    (1,  4,  "stabilisation", "Phase 1 — Stabilisation",    "Bewegungsqualität & Verletzungsprävention"),
    (5,  8,  "kraft",         "Phase 2 — Kraftaufbau",       "Maximalkraft & funktionelle Stärke"),
    (9,  12, "power",         "Phase 3 — Fußballspezifisch", "Explosivkraft & Wettkampfvorbereitung"),
]

_SHORT_PLAN_PHASE = {
    4:  [(1, "stabilisation", "Stabilisation",       "Bewegungsqualität & Verletzungsprävention")],
    6:  [(1, "stabilisation", "Stabilisation",       "Bewegungsqualität & Verletzungsprävention"),
         (3, "kraft",         "Kraftaufbau",          "Maximalkraft & funktionelle Stärke")],
    8:  [(1, "stabilisation", "Stabilisation",       "Bewegungsqualität & Verletzungsprävention"),
         (5, "kraft",         "Kraftaufbau",          "Maximalkraft & funktionelle Stärke")],
}


def _woche_eintraege_zyklus(
    woche: int, total_wochen: int, scores: dict[str, int],
    phase_name: str, phase_ziel: str, pool_key: str,
) -> list[dict]:
    """Build one week's entries for zyklus_erstellen (periodisierung table)."""
    pos_in_block = (woche - 1) % 4
    is_deload = pos_in_block == 3
    # Use week number as offset for variety across the full cycle
    offset = woche - 1

    entries = []
    sorted_areas = sorted(scores.items(), key=lambda x: -x[1])
    for area, score in sorted_areas:
        n = max(0, score - 2) if is_deload else score
        exercises = _pool_fuer_area(area, pool_key, n, offset=offset)
        for uebung, saetze, volumen, haeufigkeit in exercises:
            if is_deload:
                haeufigkeit = haeufigkeit.replace("3×", "2×").replace("4×", "2×")
            woche_typ = ["Akkumulation I", "Akkumulation II", "Intensivierung", "Deload ⬇"][pos_in_block]
            intensitaet = "leicht" if is_deload else (
                "leicht–mittel" if pos_in_block == 0 else "mittel" if pos_in_block == 1 else "hoch"
            )
            entries.append({
                "woche":       woche,
                "phase":       f"{phase_name} ({woche_typ})",
                "ziel":        phase_ziel,
                "bereich":     area,
                "uebung":      uebung,
                "intensitaet": intensitaet,
                "volumen":     volumen,
                "haeufigkeit": haeufigkeit,
            })
    return entries


def zyklus_erstellen(spieler_id: int, schwerpunkt_text: str,
                     wochen: int = 12,
                     alter: float | None = None) -> list[dict]:
    """
    Altersbasierter Periodisierungszyklus für die Periodisierung-Seite.
    Quellen: Faigenbaum & Myer (2010), Lloyd et al. (2014), NSCA.
    """
    wochen     = wochen if wochen in (4, 6, 8, 12) else 12
    scores     = defizit_score(schwerpunkt_text)
    plangruppe = _alter_zu_plangruppe(alter)
    cfg        = _PLANGRUPPEN_CONFIG[plangruppe]
    plan: list[dict] = []

    if wochen == 12:
        for woche_start, woche_end, pool_key, ph_name, ph_ziel in _PHASEN:
            _pk = _max_pool_key(pool_key, cfg["max_pool_key"])
            for w in range(woche_start, woche_end + 1):
                plan.extend(_woche_eintraege_zyklus(w, wochen, scores, ph_name, ph_ziel, _pk))
    else:
        block_size = max(1, wochen // max(1, len(_SHORT_PLAN_PHASE.get(wochen, [(1, "", "", "")]))))
        phase_defs = _SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "Stabilisation", "")])
        w = 1
        for phase_start, pool_key, ph_name, ph_ziel in phase_defs:
            _pk = _max_pool_key(pool_key, cfg["max_pool_key"])
            for week_nr in range(w, w + block_size):
                if week_nr > wochen:
                    break
                plan.extend(_woche_eintraege_zyklus(week_nr, wochen, scores, ph_name, ph_ziel, _pk))
            w += block_size

    # Altersgerechte Übungssubstitution
    filtered = []
    for entry in plan:
        ersatz = _ersatz_uebung(entry.get("uebung", ""), plangruppe)
        if ersatz is None:
            continue
        entry = dict(entry)
        if ersatz != "ok":
            entry["uebung"]      = ersatz[0]
            entry["saetze"]      = _saetze_begrenzen(ersatz[1], cfg["max_saetze"])
            entry["volumen"]     = ersatz[2]
            entry["haeufigkeit"] = _haeufigkeit_begrenzen(ersatz[3], cfg["haeuf_cap"])
        else:
            entry["saetze"]      = _saetze_begrenzen(str(entry.get("saetze", "3")), cfg["max_saetze"])
            entry["haeufigkeit"] = _haeufigkeit_begrenzen(entry.get("haeufigkeit", ""), cfg["haeuf_cap"])
        filtered.append(entry)

    periodisierung_loeschen(spieler_id)
    periodisierung_bulk_insert(spieler_id, filtered)
    return filtered


def zyklus_laden(spieler_id: int) -> list:
    return periodisierung_laden(spieler_id)


# ─────────────────────────────────────────────────────────────────────────────
# Public API: Deficit display table
# ─────────────────────────────────────────────────────────────────────────────

def defizit_tabelle(schwerpunkt_text: str) -> list[dict]:
    """Return sorted deficit analysis for UI display."""
    scores   = defizit_score(schwerpunkt_text)
    prio_map = {3: "🔴 Primär", 2: "🟡 Sekundär", 1: "🟢 Tertiär"}
    return [
        {
            "Bereich":       area,
            "Priorität":     prio_map.get(score, "—"),
            "Volumen/Woche": f"{score} Übung(en)",
            "Score":         score,
        }
        for area, score in sorted(scores.items(), key=lambda x: -x[1])
    ]
