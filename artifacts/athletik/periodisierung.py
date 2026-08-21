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
from trainingsphilosophie import (
    philosophie_pool_cap,
    philosophie_normativ,
    philosophie_satz_cap,
    philosophie_bereich_erlaubt,
    philosophie_haeuf_cap,
    PHILOSOPHIEN,
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
            ("Banded Pallof Press",         "3", "12 je Seite",   "2×/Woche"),
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
            ("Psoas March",                 "3", "10 je Seite",   "2×/Woche"),
            ("Resistance Band Psoas March", "3", "10 je Seite",   "2×/Woche"),
            ("Side Plank mit Abduktion",    "3", "10 je Seite",   "2×/Woche"),
            ("Hip Abduktor Maschine",       "3", "15 je Seite",   "2×/Woche"),
        ],
        "kraft": [
            ("Copenhagen Plank",            "3", "30 Sekunden",   "3×/Woche"),
            ("Einbeiniges Hip Hinge",       "3", "8 je Seite",    "3×/Woche"),
            ("Banded Lateral Walk",         "3", "15 Meter",      "3×/Woche"),
            ("Hip Thrust",                  "4", "10",            "2×/Woche"),
            ("Sumo Deadlift",               "3", "8",             "2×/Woche"),
            ("Lateral Step-Up",             "3", "10 je Seite",   "2×/Woche"),
            ("DB Lateral Lunge",            "3", "10 je Seite",   "2×/Woche"),
            ("Sled Push Heavy",             "4", "20 Meter",      "1×/Woche"),
            ("Cable Pull-Through",          "3", "12",            "2×/Woche"),
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
            ("DB Step-Up",                  "3", "10 je Seite",   "2×/Woche"),
            ("Leg Press beidbeinig",        "4", "12",            "2×/Woche"),
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
            ("Hamstring Bridge",            "3", "12",            "3×/Woche"),
        ],
        "kraft": [
            ("Nordic Hamstring Curl",       "3", "6",             "2×/Woche"),
            ("Romanian Deadlift einbeinig", "3", "8 je Seite",    "2×/Woche"),
            ("Seated Leg Curl",             "4", "10",            "2×/Woche"),
            ("Good Morning",               "3", "10",            "2×/Woche"),
            ("Einbeinige Kniebeuge (halb)", "3", "8 je Seite",    "2×/Woche"),
            ("Nordic Eccentric (Band-Ass.)","3", "6",             "2×/Woche"),
            ("BB Romanian Deadlift",        "3", "8",             "2×/Woche"),
            ("Leg Curl Maschine",           "4", "12",            "2×/Woche"),
            ("DB Single-Leg RDL",           "3", "8 je Seite",    "2×/Woche"),
            ("Band-Assisted Nordic",        "3", "5",             "2×/Woche"),
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
            ("High Knee Drill",             "4", "20 Meter",      "2×/Woche"),
            ("Standing Knee Drive",         "3", "10 je Seite",   "2×/Woche"),
        ],
        "kraft": [
            ("10 m Sprintstarts",           "6", "10 m",          "2×/Woche"),
            ("Beschleunigungs-ABC",         "4", "20 Meter",      "2×/Woche"),
            ("Wall Drills",                 "3", "10 je Seite",   "2×/Woche"),
            ("Resistenz-Sprints (Band)",    "4", "20 Meter",      "1×/Woche"),
            ("Gewichtete Sprintstarts",     "5", "10 m",          "2×/Woche"),
            ("Fallsprints (Partnerfreigabe)","6","10 m",          "2×/Woche"),
            ("Sled Push (leicht)",          "4", "20 Meter",      "1×/Woche"),
            ("Sled Sprint",                 "5", "20 Meter",      "1×/Woche"),
            ("Rückwärts Schlitten ziehen",  "4", "20 Meter",      "1×/Woche"),
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
# Altersgerechter Ausdauer-Pool — fußballspezifisch, nach Plangruppe
# (Quelle: Bangsbo 2008; Buchheit & Laursen 2013; DFB-Junioren-Konzept)
#
# Drei Kategorien:
#   "Jugend"  → plangruppe U7/U8/U10  (Alter ≤ 11 J.) — spielerisch, mit Ball
#   "Mittel"  → plangruppe U14         (Alter 12–14 J.) — strukturierte Intervalle
#   "Senior"  → plangruppe U18/Senior/Ü40/Ü55 (Alter 15+) — GA1/GA2/RSA
#
# Übungen folgen demselben (pool_key, saetze, volumen, haeufigkeit)-Schema wie _POOL.
# ─────────────────────────────────────────────────────────────────────────────

_AUSDAUER_POOL: dict[str, dict[str, list]] = {

    # ── Jugend (≤ U11) — spielerisch, kurze intermittierende Belastungen ──────
    "Jugend": {
        "stabilisation": [   # Phase 1/2: aerobe Basis, niedrig intensiv
            ("Fangspiel mit Ballkontrolle",     "1", "8 Minuten",    "2×/Woche"),
            ("Dribbling-Staffel aerob",         "3", "Durchgänge",   "2×/Woche"),
            ("Reaktionsspiel Tempowechsel",      "1", "6 Minuten",    "2×/Woche"),
            ("Pass-Lauf-Kombinationen",          "1", "8 Minuten",    "2×/Woche"),
            ("Bewegungsaufgaben mit Ball",       "1", "8 Minuten",    "2×/Woche"),
            ("Kleine Spielform 2v2 extensiv",   "1", "6 Minuten",    "2×/Woche"),
        ],
        "kraft": [           # Phase 2/3: mittelintensiv, ballnah
            ("Dribbel-Ausdauerzirkel",           "1", "10 Minuten",   "2×/Woche"),
            ("Pass-Ausdauerzirkel",              "1", "10 Minuten",   "2×/Woche"),
            ("Kleine Spielform 3v3",             "1", "8 Minuten",    "2×/Woche"),
            ("Shuttle-Lauf mit Ball",            "5", "Durchgänge",   "2×/Woche"),
            ("Rondo-Ausdauerform 4+1",           "1", "8 Minuten",    "2×/Woche"),
            ("Ballbesitz-Laufspiel",             "1", "8 Minuten",    "2×/Woche"),
        ],
        "power": [           # Phase 3/4: höhere Intensität, kurze Belastungen
            ("Spielform 4v4 großes Feld",        "1", "10 Minuten",   "1×/Woche"),
            ("Spielform 5v5 mit Laufaufgaben",   "1", "10 Minuten",   "1×/Woche"),
            ("Tempolauf-Staffel",                "5", "Durchgänge",   "2×/Woche"),
            ("Reaktivitäts-Laufspiel",           "1", "6 Minuten",    "2×/Woche"),
            ("Intermittierende Spielform",       "1", "10 Minuten",   "1×/Woche"),
            ("Dribbling-Intervall mit Pause",    "8", "Durchgänge",   "1×/Woche"),
        ],
    },

    # ── Mittel (U14 — Alter 12–14) — strukturierte Spielformen + Intervalle ───
    "Mittel": {
        "stabilisation": [
            ("Extensive Spielform 4v4",          "1", "12 Minuten",   "2×/Woche"),
            ("Ballbesitz-Ausdauerform groß",     "1", "12 Minuten",   "2×/Woche"),
            ("Tempo-Dribblings extensiv",        "1", "10 Minuten",   "2×/Woche"),
            ("Rondo-Ausdauerform 5+2",           "1", "10 Minuten",   "2×/Woche"),
            ("Pass-Ausdauerzirkel intensiv",     "1", "12 Minuten",   "2×/Woche"),
            ("Spielform 5v5 extensiv",           "1", "12 Minuten",   "2×/Woche"),
        ],
        "kraft": [
            ("15:15 Intervalle mit Ball",        "8", "Durchgänge",   "2×/Woche"),
            ("20:20 Spielform-Intervalle",       "6", "Durchgänge",   "2×/Woche"),
            ("Shuttle-Intervall 20 m",           "6", "Durchgänge",   "2×/Woche"),
            ("Ballbesitz-Intervall 5v5",         "5", "Durchgänge",   "2×/Woche"),
            ("Tempowechsellauf mit Ball",        "6", "Durchgänge",   "2×/Woche"),
            ("Intensive Spielform 4v4",          "1", "8 Minuten",    "2×/Woche"),
        ],
        "power": [
            ("30:30 Intervalle fußballspezifisch","8","Durchgänge",   "1×/Woche"),
            ("Intensive Spielform 5v5 groß",     "1", "12 Minuten",   "1×/Woche"),
            ("Richtungswechsel-Intervall",        "8", "Durchgänge",   "2×/Woche"),
            ("High-Intensity Spielform 4v4",     "1", "6 Minuten",    "2×/Woche"),
            ("Pressing-Ausdauer-Übung",          "6", "Durchgänge",   "1×/Woche"),
            ("RSA-orientiertes Laufspiel",       "6", "Durchgänge",   "1×/Woche"),
        ],
    },

    # ── Senior (U18+) — GA1/GA2, Intervalle, RSA ──────────────────────────────
    "Senior": {
        "stabilisation": [
            ("GA1-Dauerlauf 65–75 % HFmax",     "1", "20 Minuten",   "2×/Woche"),
            ("Extensive Dauermethode",           "1", "25 Minuten",   "1×/Woche"),
            ("Fahrtspiel fußballspezifisch",     "1", "20 Minuten",   "2×/Woche"),
            ("Ballbesitzspiel extensiv groß",    "1", "15 Minuten",   "2×/Woche"),
            ("Tempodauerlauf 70 % HFmax",        "1", "20 Minuten",   "2×/Woche"),
            ("Aerobe Spielform 6v6+",            "1", "20 Minuten",   "2×/Woche"),
        ],
        "kraft": [
            ("15:15 Intervall aerob-anaerob",    "10","Durchgänge",   "2×/Woche"),
            ("30:30 fußballspezifisch",          "10","Durchgänge",   "1×/Woche"),
            ("Extensive Intervallmethode",        "6", "×4 min",       "2×/Woche"),
            ("GA2-Intervall 80–85 % HFmax",      "5", "×4 min",       "2×/Woche"),
            ("Shuttle-Intervall 40 m",           "8", "Durchgänge",   "2×/Woche"),
            ("Intensive Spielform 6v6",          "1", "15 Minuten",   "2×/Woche"),
        ],
        "power": [
            ("RSA 6×30 m mit Erholungsphase",   "6", "Serien",        "1×/Woche"),
            ("Intensive Intervallmethode",        "6", "×1 min",       "2×/Woche"),
            ("High-Intensity Shuttle 40 m",      "8", "Durchgänge",   "1×/Woche"),
            ("Pressing-Simulation intensiv",     "6", "Durchgänge",   "2×/Woche"),
            ("RSA + Ballkontrolle",              "6", "30 m",          "1×/Woche"),
            ("Intermittierende Hochintensität",  "6", "Durchgänge",   "2×/Woche"),
        ],
    },
}

# Mapping Plangruppe → Ausdauer-Kategorie
_PLANGRUPPE_ZU_AUSDAUER: dict[str, str] = {
    "U7": "Jugend", "U8": "Jugend", "U10": "Jugend",   # Alter ≤ 11
    "U14": "Mittel",                                     # Alter 12–14
    "U18": "Senior", "Senior": "Senior",                 # Alter 15+
    "Ü40": "Senior", "Ü55": "Senior",
}


def _ausdauer_pool_fuer_plangruppe(
    plangruppe: str,
    pool_key: str,
    n: int,
    offset: int = 0,
) -> list:
    """Gibt altersgerechte Ausdauer-Übungen zurück.

    Selektiert aus _AUSDAUER_POOL[Jugend|Mittel|Senior][pool_key].
    Ü40/Ü55 nutzen Senior-Pool, werden aber durch _max_pool_key auf
    'stabilisation'/'kraft' begrenzt (keine RSA-power-Übungen).
    """
    kategorie = _PLANGRUPPE_ZU_AUSDAUER.get(plangruppe, "Senior")
    exercises  = _AUSDAUER_POOL.get(kategorie, {}).get(pool_key, [])
    if not exercises:
        return []
    n = min(n, len(exercises))
    return [exercises[(offset + i) % len(exercises)] for i in range(n)]


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
    # Ausdauer: Pause = aktive Erholungszeit zwischen Intervallen/Spielformen
    ("Ausdauer",      "stabilisation"): (60,  "Aerob / kontinuierlich — Belastung aufrechterhalten"),
    ("Ausdauer",      "kraft"):         (60,  "Aktive Pause / Belastungs-Pausen-Verhältnis 1:1"),
    ("Ausdauer",      "power"):         (90,  "Vollständige Erholung zwischen Intensiv-Intervallen"),
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
    """Ordnet ein Alter der Trainingsplangruppe zu.

    U = unter: Alter 9 (unter 10) → U10-Trainingsgruppe.
    Stimmt überein mit field_eval.alter_zu_altersgruppe() und age_norms.alter_zu_normgruppe().

    Mapping:
        ≤ 6  → U7   (Bambini)
        7–8  → U8   (F-Jugend)
        9–11 → U10  (E-Jugend)
        12–14→ U14
        15–18→ U18
        19–35→ Senior
        36–50→ Ü40
        51+  → Ü55
    """
    if not alter or alter <= 0:
        return "Senior"
    a = int(alter)
    if a <= 6:  return "U7"   # ≤ 6 J.  (war: a <= 7)
    if a <= 8:  return "U8"   # 7–8 J.  (war: a <= 9)
    if a <= 11: return "U10"  # 9–11 J. (unverändert; deckt jetzt auch 9-Jährige ab)
    if a <= 14: return "U14"
    if a <= 18: return "U18"
    if a <= 35: return "Senior"
    if a <= 50: return "Ü40"
    return "Ü55"


_PLANGRUPPEN_CONFIG: dict[str, dict] = {
    # ── U7: Bambini — Bewegungserfahrung & spielerische Koordination ────────────
    "U7": {
        "max_pool_key":    "stabilisation",
        "pause_offset":    60,
        "ausfuehr_prefix": "Spielerisch / Körpergefühl entdecken — kein Tempo-Ziel · ",
        "max_saetze":      2,
        "haeuf_cap":       "2×",
        "label":           "U7 — Bewegungserfahrung & Koordination",
    },
    # ── U8: F-Jugend — Koordination & Bewegungskompetenz ───────────────────────
    "U8": {
        "max_pool_key":    "stabilisation",
        "pause_offset":    50,
        "ausfuehr_prefix": "Technisch / Körpergefühl entwickeln — kein Tempo-Ziel · ",
        "max_saetze":      2,
        "haeuf_cap":       "2×",
        "label":           "U8/U9 — Koordination & Bewegungskompetenz",
    },
    "U10": {
        "max_pool_key":    "stabilisation",
        "pause_offset":    45,
        "ausfuehr_prefix": "Technisch / Körpergefühl entwickeln — kein Tempo-Ziel · ",
        "max_saetze":      2,
        "haeuf_cap":       "2×",
        "label":           "U10/U11 — Koordination & Bewegungsbildung",
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
# Trainingswissenschaftliche Belastungsmetadaten (Spec §1–§7)
# Quellen: NSCA (2016), Zatsiorsky & Kraemer (2006), Buchheit & Laursen (2013)
# ─────────────────────────────────────────────────────────────────────────────

# §2 Trainingsreihenfolge: Slot 1–17 — hohe neuronale Belastung immer zuerst (§3)
_TRAININGS_SEQUENZ: dict[tuple[str, str], int] = {
    ("Sprunggelenk",  "stabilisation"): 1,   # Aktivierung / Fußmobilisierung
    ("Hüfte",         "stabilisation"): 2,   # Dynamisches Dehnen / Hüftmobilität
    ("Schnelligkeit", "stabilisation"): 3,   # Sprinttechnik
    ("Schnelligkeit", "kraft"):         4,   # Antrittsschnelligkeit
    ("Agilität",      "stabilisation"): 4,   # COD-Technik
    ("Schnelligkeit", "power"):         5,   # Maximalschnelligkeit
    ("Agilität",      "kraft"):         5,   # COD-Kraft
    ("Agilität",      "power"):         5,   # reaktive Agilität
    ("Explosivität",  "stabilisation"): 6,   # Plyometrie-Einführung
    # Slot 7: Olympisches Gewichtheben — via _olympic_geeignet() gate
    ("Oberschenkel",  "kraft"):         8,   # Maximalkraft (Hamstrings)
    ("Explosivität",  "kraft"):         9,   # Schnellkraft
    ("Oberschenkel",  "power"):         9,   # Schnellkraft (Hamstring explosiv)
    ("Explosivität",  "power"):         10,  # Explosivkraft
    ("Knie",          "power"):         10,  # Explosivkraft Knie
    ("Hüfte",         "power"):         10,  # Explosivkraft Hüfte
    ("Knie",          "kraft"):         11,  # Mehrgelenk komplex
    ("Hüfte",         "kraft"):         12,  # Mehrgelenk einfach
    ("Sprunggelenk",  "kraft"):         13,  # Eingelenkige Kraftübungen
    ("Rumpf",         "kraft"):         14,  # Core
    ("Rumpf",         "power"):         14,  # Core reaktiv
    ("Rumpf",         "stabilisation"): 15,  # Stabilisation
    ("Knie",          "stabilisation"): 16,  # Prävention
    ("Oberschenkel",  "stabilisation"): 16,  # Prävention
    ("Sprunggelenk",  "power"):         16,  # reaktive Prävention
    ("Fußball",       "stabilisation"): 17,  # Cool-down / Fußball
    ("Fußball",       "kraft"):         17,
    ("Fußball",       "power"):         17,
    ("Ausdauer",      "stabilisation"): 16,  # Ausdauerblock — nach Kraft/Speed
    ("Ausdauer",      "kraft"):         16,
    ("Ausdauer",      "power"):         16,
}

# §5 Energiesystem-Zuordnung pro (bereich, pool_key)
_ENERGIE_SYSTEM: dict[tuple[str, str], str] = {
    ("Schnelligkeit", "stabilisation"): "ATP-KP",
    ("Schnelligkeit", "kraft"):         "ATP-KP",
    ("Schnelligkeit", "power"):         "ATP-KP",
    ("Explosivität",  "stabilisation"): "ATP-KP",
    ("Explosivität",  "kraft"):         "ATP-KP",
    ("Explosivität",  "power"):         "ATP-KP",
    ("Agilität",      "stabilisation"): "ATP-KP",
    ("Agilität",      "kraft"):         "ATP-KP",
    ("Agilität",      "power"):         "ATP-KP",
    ("Oberschenkel",  "stabilisation"): "Aerob",
    ("Oberschenkel",  "kraft"):         "Gemischt",
    ("Oberschenkel",  "power"):         "ATP-KP",
    ("Knie",          "stabilisation"): "Aerob",
    ("Knie",          "kraft"):         "Gemischt",
    ("Knie",          "power"):         "ATP-KP",
    ("Hüfte",         "stabilisation"): "Aerob",
    ("Hüfte",         "kraft"):         "Gemischt",
    ("Hüfte",         "power"):         "ATP-KP",
    ("Rumpf",         "stabilisation"): "Aerob",
    ("Rumpf",         "kraft"):         "Gemischt",
    ("Rumpf",         "power"):         "ATP-KP",
    ("Sprunggelenk",  "stabilisation"): "Aerob",
    ("Sprunggelenk",  "kraft"):         "Aerob",
    ("Sprunggelenk",  "power"):         "ATP-KP",
    ("Fußball",       "stabilisation"): "Aerob",
    ("Fußball",       "kraft"):         "Gemischt",
    ("Fußball",       "power"):         "Laktazid",
    ("Ausdauer",      "stabilisation"): "Aerob",
    ("Ausdauer",      "kraft"):         "Laktazid",
    ("Ausdauer",      "power"):         "Laktazid",
}

# §4 Primäres Equipment pro (bereich, pool_key)
_EQUIPMENT_PRIMÄR: dict[tuple[str, str], str] = {
    ("Schnelligkeit", "stabilisation"): "Körpergewicht",
    ("Schnelligkeit", "kraft"):         "Körpergewicht",
    ("Schnelligkeit", "power"):         "Körpergewicht",
    ("Explosivität",  "stabilisation"): "Körpergewicht",
    ("Explosivität",  "kraft"):         "Körpergewicht",
    ("Explosivität",  "power"):         "Körpergewicht",
    ("Agilität",      "stabilisation"): "Körpergewicht",
    ("Agilität",      "kraft"):         "Körpergewicht",
    ("Agilität",      "power"):         "Körpergewicht",
    ("Oberschenkel",  "stabilisation"): "Körpergewicht",
    ("Oberschenkel",  "kraft"):         "Maschine",
    ("Oberschenkel",  "power"):         "Freie Gewichte",
    ("Knie",          "stabilisation"): "Körpergewicht",
    ("Knie",          "kraft"):         "Freie Gewichte",
    ("Knie",          "power"):         "Körpergewicht",
    ("Hüfte",         "stabilisation"): "Miniband",
    ("Hüfte",         "kraft"):         "Freie Gewichte",
    ("Hüfte",         "power"):         "Kettlebell",
    ("Rumpf",         "stabilisation"): "Körpergewicht",
    ("Rumpf",         "kraft"):         "Körpergewicht",
    ("Rumpf",         "power"):         "Medizinball",
    ("Sprunggelenk",  "stabilisation"): "Körpergewicht",
    ("Sprunggelenk",  "kraft"):         "Körpergewicht",
    ("Sprunggelenk",  "power"):         "Körpergewicht",
    ("Fußball",       "stabilisation"): "Ball",
    ("Fußball",       "kraft"):         "Ball",
    ("Fußball",       "power"):         "Ball",
    ("Ausdauer",      "stabilisation"): "Ball",
    ("Ausdauer",      "kraft"):         "Ball",
    ("Ausdauer",      "power"):         "Ball",
}

# Equipment-Fallback: alternative pool_key wenn primäres Equipment fehlt (§4)
_EQUIPMENT_FALLBACK_POOL: dict[str, str] = {
    "Maschine":       "stabilisation",  # Kein Gerät → Körpergewicht-Variante
    "Kettlebell":     "kraft",          # Kein Kettlebell → Freie-Gewichte-Variante
    "Medizinball":    "kraft",          # Kein Medizinball → Kraft-Variante
    "Freie Gewichte": "stabilisation",  # Keine freien Gewichte → Körpergewicht
    "Miniband":       "stabilisation",  # Kein Miniband → Körpergewicht
}

# §6 Olympisches Gewichtheben — Übungspool (nur für geeignete Athleten)
_OLYMPIC_POOL: list[tuple] = [
    ("Hang Power Clean",          "4", "3 Wdh.",  "2×/Woche"),
    ("Power Clean",               "4", "3 Wdh.",  "2×/Woche"),
    ("High Pull",                 "4", "4 Wdh.",  "2×/Woche"),
    ("Power Clean + Push Press",  "3", "3 Wdh.",  "1×/Woche"),
    ("Hang Snatch (leicht)",      "3", "3 Wdh.",  "1×/Woche"),
    ("Push Press",                "4", "4 Wdh.",  "2×/Woche"),
]


# ─────────────────────────────────────────────────────────────────────────────
# §4b Per-Übung Equipment-Metadaten (Spec §4b)
#
# Miniband  = kurzes Schlaufenband (Loop Band, z. B. Glute Band)
# Powerband = langes Widerstandsband (Resistance Band, Assist Band)
# Freie Gewichte = Oberkategorie → wird zu Unterkat. expandiert
# Kurzhanteln / Langhanteln / Kettlebell / Trap Bar / Landmine = Unterkat.
# ─────────────────────────────────────────────────────────────────────────────

_FREIE_GEWICHTE_UNTERKAT: frozenset[str] = frozenset({
    "Kurzhanteln", "Langhanteln", "Kettlebell", "Trap Bar", "Landmine",
})

_UEBUNG_EQUIPMENT: dict[str, frozenset[str]] = {
    # ── RUMPF — stabilisation ─────────────────────────────────────────────
    "Dead Bug":                     frozenset({"Körpergewicht"}),
    "Plank":                        frozenset({"Körpergewicht"}),
    "Pallof Press":                 frozenset({"Miniband", "Maschine", "Powerband"}),
    "Seitstütz":                    frozenset({"Körpergewicht"}),
    "Hollow Body Hold":             frozenset({"Körpergewicht"}),
    "Bird Dog":                     frozenset({"Körpergewicht"}),
    # ── RUMPF — kraft ─────────────────────────────────────────────────────
    "Ab Wheel Rollout":             frozenset({"Körpergewicht"}),
    "Plank mit Armheben":           frozenset({"Körpergewicht"}),
    "Pallof Press Stand":           frozenset({"Miniband", "Maschine", "Powerband"}),
    "Russischer Twist":             frozenset({"Körpergewicht", "Medizinball"}),
    "Cable Woodchop":               frozenset({"Maschine"}),
    "Copenhagen Side Plank Dyn.":   frozenset({"Körpergewicht"}),
    "Banded Pallof Press":          frozenset({"Powerband"}),
    # ── RUMPF — power ─────────────────────────────────────────────────────
    "Medizinball Rotationswurf":    frozenset({"Medizinball"}),
    "Landmine Rotation":            frozenset({"Freie Gewichte", "Landmine"}),
    "Hanging Knee Raise":           frozenset({"Körpergewicht"}),
    "Farmer's Walk":                frozenset({"Freie Gewichte", "Kurzhanteln", "Langhanteln", "Kettlebell"}),
    "Medizinball Chest Pass":       frozenset({"Medizinball"}),
    "Kabelzug Sprungrotation":      frozenset({"Maschine"}),
    # ── HÜFTE — stabilisation ─────────────────────────────────────────────
    "Seitliches Miniband Gehen":    frozenset({"Miniband"}),
    "90/90 Hüftrotation":           frozenset({"Körpergewicht"}),
    "Einbeinige Hüftbrücke":        frozenset({"Körpergewicht"}),
    "Copenhagen Plank (kurz)":      frozenset({"Körpergewicht"}),
    "Monster Walk (Band)":          frozenset({"Miniband"}),
    "Side-Lying Clam Shell":        frozenset({"Körpergewicht", "Miniband"}),
    "Psoas March":                  frozenset({"Körpergewicht"}),
    "Resistance Band Psoas March":  frozenset({"Powerband", "Miniband"}),
    "Side Plank mit Abduktion":     frozenset({"Körpergewicht", "Miniband"}),
    "Hip Abduktor Maschine":        frozenset({"Maschine"}),
    # ── HÜFTE — kraft ─────────────────────────────────────────────────────
    "Copenhagen Plank":             frozenset({"Körpergewicht"}),
    "Einbeiniges Hip Hinge":        frozenset({"Körpergewicht"}),
    "Banded Lateral Walk":          frozenset({"Miniband"}),
    "Hip Thrust":                   frozenset({"Freie Gewichte", "Langhanteln", "Körpergewicht"}),
    "Sumo Deadlift":                frozenset({"Freie Gewichte", "Langhanteln"}),
    "Lateral Step-Up":              frozenset({"Körpergewicht", "Kurzhanteln"}),
    "DB Lateral Lunge":             frozenset({"Kurzhanteln"}),
    "Sled Push Heavy":              frozenset({"Schlitten"}),
    "Cable Pull-Through":           frozenset({"Maschine"}),
    # ── HÜFTE — power ─────────────────────────────────────────────────────
    "Explosiver Hip Thrust":        frozenset({"Freie Gewichte", "Langhanteln", "Körpergewicht"}),
    "Lateral Bound stabilisiert":   frozenset({"Körpergewicht"}),
    "Single-Leg Glute Bridge +Gew": frozenset({"Freie Gewichte", "Kurzhanteln"}),
    "Resisted Hip Abduction":       frozenset({"Miniband", "Maschine"}),
    "Broad Jump aus Hüfte":         frozenset({"Körpergewicht"}),
    "Kettlebell Swing einbeinig":   frozenset({"Kettlebell"}),
    # ── KNIE — stabilisation ──────────────────────────────────────────────
    "Single Leg Squat (Qualität)":  frozenset({"Körpergewicht"}),
    "Step Down":                    frozenset({"Körpergewicht"}),
    "Seitliche Miniband Squats":    frozenset({"Miniband"}),
    "Valgus-Kontroll Lunge":        frozenset({"Körpergewicht"}),
    "Terminal Knee Ext. (Band)":    frozenset({"Miniband", "Powerband"}),
    "Slow Squat (5 s Exzentrik)":   frozenset({"Körpergewicht"}),
    # ── KNIE — kraft ──────────────────────────────────────────────────────
    "Bulgarian Split Squat":        frozenset({"Körpergewicht", "Kurzhanteln", "Langhanteln"}),
    "Reverse Lunge":                frozenset({"Körpergewicht", "Kurzhanteln"}),
    "Box Squat":                    frozenset({"Freie Gewichte", "Langhanteln"}),
    "Single Leg Leg Press":         frozenset({"Maschine"}),
    "Walking Lunge":                frozenset({"Körpergewicht", "Kurzhanteln", "Langhanteln"}),
    "Front Squat (leicht)":         frozenset({"Freie Gewichte", "Langhanteln"}),
    "DB Step-Up":                   frozenset({"Kurzhanteln"}),
    "Leg Press beidbeinig":         frozenset({"Maschine"}),
    # ── KNIE — power ──────────────────────────────────────────────────────
    "Drop Landing → Sprung":        frozenset({"Körpergewicht"}),
    "Bounding":                     frozenset({"Körpergewicht"}),
    "Single Leg Jump & Stabi":      frozenset({"Körpergewicht"}),
    "Box Jump einbeinig":           frozenset({"Körpergewicht"}),
    "Split Jump":                   frozenset({"Körpergewicht"}),
    "Lateral Box Jump":             frozenset({"Körpergewicht"}),
    # ── SPRUNGGELENK — stabilisation ──────────────────────────────────────
    "Knie zur Wand Mobilisation":   frozenset({"Körpergewicht"}),
    "Einbeinstand Balance Pad":     frozenset({"Körpergewicht"}),
    "Einbeinige Wadenheben":        frozenset({"Körpergewicht"}),
    "Fersengang / Zehengang":       frozenset({"Körpergewicht"}),
    "Fußkreisen einbeinig":         frozenset({"Körpergewicht"}),
    "Einbeinstand (Augen zu)":      frozenset({"Körpergewicht"}),
    # ── SPRUNGGELENK — kraft ──────────────────────────────────────────────
    "Single Leg Calf Raise (Treppe)":frozenset({"Körpergewicht"}),
    "Ankle Banded Dorsiflexion":    frozenset({"Miniband", "Powerband"}),
    "Pogo Hops beidbeinig":         frozenset({"Körpergewicht"}),
    "Einbeinige Pogo Hops":         frozenset({"Körpergewicht"}),
    "Banded Tibialis Raise":        frozenset({"Miniband", "Powerband"}),
    "Seated Calf Raise":            frozenset({"Maschine", "Körpergewicht"}),
    # ── SPRUNGGELENK — power ──────────────────────────────────────────────
    "Ankle Jumps reaktiv":          frozenset({"Körpergewicht"}),
    "Depth Drop → Sprung":          frozenset({"Körpergewicht"}),
    "Lateral Hops reaktiv":         frozenset({"Körpergewicht"}),
    "Einbeinige Hüpfsprints":       frozenset({"Körpergewicht"}),
    "Springseil (Einzel)":          frozenset({"Körpergewicht"}),
    "Box Drop Einbeinig":           frozenset({"Körpergewicht"}),
    # ── OBERSCHENKEL — stabilisation ──────────────────────────────────────
    "Nordic Hamstring Eccentric":   frozenset({"Körpergewicht"}),
    "Einbeiniges RDL (leicht)":     frozenset({"Körpergewicht"}),
    "Lying Hamstring Curl":         frozenset({"Maschine"}),
    "Gluteal Bridge Variante":      frozenset({"Körpergewicht"}),
    "Prone Hip Ext. (isometr.)":    frozenset({"Körpergewicht"}),
    "Hamstring Wall Bridge":        frozenset({"Körpergewicht"}),
    "Hamstring Bridge":             frozenset({"Körpergewicht"}),
    # ── OBERSCHENKEL — kraft ──────────────────────────────────────────────
    "Nordic Hamstring Curl":        frozenset({"Körpergewicht"}),
    "Romanian Deadlift einbeinig":  frozenset({"Körpergewicht", "Freie Gewichte", "Kurzhanteln", "Langhanteln"}),
    "Seated Leg Curl":              frozenset({"Maschine"}),
    "Good Morning":                 frozenset({"Freie Gewichte", "Langhanteln"}),
    "Einbeinige Kniebeuge (halb)":  frozenset({"Körpergewicht"}),
    "Nordic Eccentric (Band-Ass.":  frozenset({"Powerband"}),
    "Nordic Eccentric (Band-Ass.)": frozenset({"Powerband"}),
    "BB Romanian Deadlift":         frozenset({"Langhanteln"}),
    "Leg Curl Maschine":            frozenset({"Maschine"}),
    "DB Single-Leg RDL":            frozenset({"Kurzhanteln"}),
    "Band-Assisted Nordic":         frozenset({"Powerband"}),
    # ── OBERSCHENKEL — power ──────────────────────────────────────────────
    "Explosive Nordic":             frozenset({"Körpergewicht"}),
    "Hamstring Sliders reaktiv":    frozenset({"Körpergewicht"}),
    "Power RDL":                    frozenset({"Freie Gewichte", "Langhanteln"}),
    "Sprung aus Kniebeuge":         frozenset({"Körpergewicht"}),
    "Glute Ham Raise":              frozenset({"Körpergewicht"}),
    "Einbeiniger Sprung aus Stand": frozenset({"Körpergewicht"}),
    # ── SCHNELLIGKEIT — stabilisation ─────────────────────────────────────
    "Lauf-ABC (A-Skip)":            frozenset({"Körpergewicht"}),
    "Steigerungsläufe":             frozenset({"Körpergewicht"}),
    "Lauf-ABC (B-Skip)":            frozenset({"Körpergewicht"}),
    "Anfersen / Knieheben":         frozenset({"Körpergewicht"}),
    "Koordinationsleiter Sprint":   frozenset({"Körpergewicht"}),
    "Schrittfrequenz-Drills":       frozenset({"Körpergewicht"}),
    "High Knee Drill":              frozenset({"Körpergewicht"}),
    "Standing Knee Drive":          frozenset({"Körpergewicht"}),
    # ── SCHNELLIGKEIT — kraft ─────────────────────────────────────────────
    "10 m Sprintstarts":            frozenset({"Körpergewicht"}),
    "Beschleunigungs-ABC":          frozenset({"Körpergewicht"}),
    "Wall Drills":                  frozenset({"Körpergewicht"}),
    "Resistenz-Sprints (Band)":     frozenset({"Powerband"}),
    "Gewichtete Sprintstarts":      frozenset({"Freie Gewichte"}),
    "Fallsprints (Partnerfreigabe)":frozenset({"Körpergewicht"}),
    "Sled Push (leicht)":           frozenset({"Schlitten"}),
    "Sled Sprint":                  frozenset({"Schlitten"}),
    "Rückwärts Schlitten ziehen":   frozenset({"Schlitten"}),
    # ── SCHNELLIGKEIT — power ─────────────────────────────────────────────
    "20–30 m Maximalsprints":       frozenset({"Körpergewicht"}),
    "Reaktionssprints":             frozenset({"Körpergewicht"}),
    "Fliegende 30er":               frozenset({"Körpergewicht"}),
    "Bergaufsprints":               frozenset({"Körpergewicht"}),
    "Max. 10 m Wdh.-Sprints":       frozenset({"Körpergewicht"}),
    "Flying 20 m":                  frozenset({"Körpergewicht"}),
    # ── EXPLOSIVITÄT — stabilisation ──────────────────────────────────────
    "Koordinations-Hops":           frozenset({"Körpergewicht"}),
    "Squat Jump Einführung":        frozenset({"Körpergewicht"}),
    "Knieheben einbeinig":          frozenset({"Körpergewicht"}),
    "Balance → Sprung Intro":       frozenset({"Körpergewicht"}),
    "Tiefknie-Absprung (Technik)":  frozenset({"Körpergewicht"}),
    "Zweischritt-Absprung":         frozenset({"Körpergewicht"}),
    # ── EXPLOSIVITÄT — kraft ──────────────────────────────────────────────
    "Squat Jump":                   frozenset({"Körpergewicht"}),
    "Box Jump beidbeinig":          frozenset({"Körpergewicht"}),
    "Medicine Ball Slam":           frozenset({"Medizinball"}),
    "Hürdensprünge":                frozenset({"Körpergewicht"}),
    "Kettlebell Swing":             frozenset({"Kettlebell"}),
    "Trap Bar Jump (leicht)":       frozenset({"Trap Bar", "Freie Gewichte"}),
    # ── EXPLOSIVITÄT — power ──────────────────────────────────────────────
    "Depth Jump":                   frozenset({"Körpergewicht"}),
    "Einbeinige Plyo Sprünge":      frozenset({"Körpergewicht"}),
    "Box Jump maximal":             frozenset({"Körpergewicht"}),
    "Reaktive Sprünge (DJ-RSI)":    frozenset({"Körpergewicht"}),
    "Bounding (Weitsprung)":        frozenset({"Körpergewicht"}),
    "Plyo Push-Up":                 frozenset({"Körpergewicht"}),
    # ── AGILITÄT — stabilisation ──────────────────────────────────────────
    "Footwork Leitertraining":      frozenset({"Körpergewicht"}),
    "Deceleration Drill":           frozenset({"Körpergewicht"}),
    "Hexagon Drill":                frozenset({"Körpergewicht"}),
    "Lateral Shuffle (Technik)":    frozenset({"Körpergewicht"}),
    "Seitwärtslauf Koordination":   frozenset({"Körpergewicht"}),
    "Kreuzschritt-Drill":           frozenset({"Körpergewicht"}),
    # ── AGILITÄT — kraft ──────────────────────────────────────────────────
    "5-10-5 Shuttle":               frozenset({"Körpergewicht"}),
    "Pro Agility Drill":            frozenset({"Körpergewicht"}),
    "T-Test":                       frozenset({"Körpergewicht"}),
    "Seitwärts Sprints":            frozenset({"Körpergewicht"}),
    "L-Drill":                      frozenset({"Körpergewicht"}),
    "Backwards Sprint":             frozenset({"Körpergewicht"}),
    # ── AGILITÄT — power ──────────────────────────────────────────────────
    "Randomized Agility (Signal)":  frozenset({"Körpergewicht"}),
    "Illinois Test Tempo":          frozenset({"Körpergewicht"}),
    "COD Speed Drills":             frozenset({"Körpergewicht"}),
    "Fußball-Agility Parcours":     frozenset({"Ball", "Körpergewicht"}),
    "Drop-Step → Sprint":           frozenset({"Körpergewicht"}),
    "Reaktions-Agility-Parcours":   frozenset({"Körpergewicht"}),
    # ── FUSSBALL — stabilisation ──────────────────────────────────────────
    "Einbeinige Ballkontakte":      frozenset({"Ball"}),
    "Ballkontrolle Gleichgewicht":  frozenset({"Ball"}),
    "Fußballkoordination Leiter":   frozenset({"Ball", "Körpergewicht"}),
    "Einbeiniges Torwarttraining":  frozenset({"Ball"}),
    "Technik Passspiel (Kontrol.":  frozenset({"Ball"}),
    "Technik Passspiel (Kontrol.)": frozenset({"Ball"}),
    "1-Touch-Kontrolle einbeinig":  frozenset({"Ball"}),
    # ── FUSSBALL — kraft ──────────────────────────────────────────────────
    "Partner Widerstandsdrücken":   frozenset({"Körpergewicht"}),
    "Zweikampf Stabilität":         frozenset({"Körpergewicht"}),
    "Koordination Leitertraining":  frozenset({"Körpergewicht"}),
    "Ballführung unter Druck":      frozenset({"Ball"}),
    "Pressing-Simulation mit Ball": frozenset({"Ball"}),
    "Sprung-Kopfball-Vorbereitung": frozenset({"Ball"}),
    # ── FUSSBALL — power ──────────────────────────────────────────────────
    "Repeated Sprint Ability (RSA)":frozenset({"Körpergewicht"}),
    "30-30 Intervallläufe":         frozenset({"Körpergewicht"}),
    "Pressingsimulation":           frozenset({"Körpergewicht"}),
    "Schusstraining explosiv":      frozenset({"Ball"}),
    "RSA + Ballkontrolle":          frozenset({"Ball"}),
    "High-Int. Dribbling-Intervall":frozenset({"Ball"}),
    # ── OLYMPISCHES GEWICHTHEBEN ──────────────────────────────────────────
    "Hang Power Clean":             frozenset({"Langhanteln"}),
    "Power Clean":                  frozenset({"Langhanteln"}),
    "High Pull":                    frozenset({"Langhanteln"}),
    "Power Clean + Push Press":     frozenset({"Langhanteln"}),
    "Hang Snatch (leicht)":         frozenset({"Langhanteln"}),
    "Push Press":                   frozenset({"Langhanteln"}),
    # ── AUSDAUER — Jugend-Pool ────────────────────────────────────────────
    "Fangspiel mit Ballkontrolle":  frozenset({"Ball"}),
    "Dribbling-Staffel aerob":      frozenset({"Ball"}),
    "Reaktionsspiel Tempowechsel":  frozenset({"Körpergewicht"}),
    "Pass-Lauf-Kombinationen":      frozenset({"Ball"}),
    "Bewegungsaufgaben mit Ball":   frozenset({"Ball"}),
    "Kleine Spielform 2v2 extensiv":frozenset({"Ball"}),
    "Dribbel-Ausdauerzirkel":       frozenset({"Ball"}),
    "Pass-Ausdauerzirkel":          frozenset({"Ball"}),
    "Kleine Spielform 3v3":         frozenset({"Ball"}),
    "Shuttle-Lauf mit Ball":        frozenset({"Ball"}),
    "Rondo-Ausdauerform 4+1":       frozenset({"Ball"}),
    "Ballbesitz-Laufspiel":         frozenset({"Ball"}),
    "Spielform 4v4 großes Feld":    frozenset({"Ball"}),
    "Spielform 5v5 mit Laufaufgaben":frozenset({"Ball"}),
    "Tempolauf-Staffel":            frozenset({"Körpergewicht"}),
    "Reaktivitäts-Laufspiel":       frozenset({"Körpergewicht"}),
    "Intermittierende Spielform":   frozenset({"Ball"}),
    "Dribbling-Intervall mit Pause":frozenset({"Ball"}),
    # ── AUSDAUER — Mittel-Pool ────────────────────────────────────────────
    "Extensive Spielform 4v4":          frozenset({"Ball"}),
    "Ballbesitz-Ausdauerform groß":     frozenset({"Ball"}),
    "Tempo-Dribblings extensiv":        frozenset({"Ball"}),
    "Rondo-Ausdauerform 5+2":           frozenset({"Ball"}),
    "Pass-Ausdauerzirkel intensiv":     frozenset({"Ball"}),
    "Spielform 5v5 extensiv":           frozenset({"Ball"}),
    "15:15 Intervalle mit Ball":        frozenset({"Ball"}),
    "20:20 Spielform-Intervalle":       frozenset({"Ball"}),
    "Shuttle-Intervall 20 m":           frozenset({"Körpergewicht"}),
    "Ballbesitz-Intervall 5v5":         frozenset({"Ball"}),
    "Tempowechsellauf mit Ball":        frozenset({"Ball"}),
    "Intensive Spielform 4v4":          frozenset({"Ball"}),
    "30:30 Intervalle fußballspezifisch":frozenset({"Ball"}),
    "Intensive Spielform 5v5 groß":     frozenset({"Ball"}),
    "Richtungswechsel-Intervall":       frozenset({"Körpergewicht"}),
    "High-Intensity Spielform 4v4":     frozenset({"Ball"}),
    "Pressing-Ausdauer-Übung":          frozenset({"Ball"}),
    "RSA-orientiertes Laufspiel":       frozenset({"Körpergewicht"}),
    # ── AUSDAUER — Senior-Pool ────────────────────────────────────────────
    "GA1-Dauerlauf 65–75 % HFmax":      frozenset({"Körpergewicht"}),
    "Extensive Dauermethode":           frozenset({"Körpergewicht"}),
    "Fahrtspiel fußballspezifisch":     frozenset({"Körpergewicht"}),
    "Ballbesitzspiel extensiv groß":    frozenset({"Ball"}),
    "Tempodauerlauf 70 % HFmax":        frozenset({"Körpergewicht"}),
    "Aerobe Spielform 6v6+":            frozenset({"Ball"}),
    "15:15 Intervall aerob-anaerob":    frozenset({"Körpergewicht"}),
    "30:30 fußballspezifisch":          frozenset({"Körpergewicht"}),
    "Extensive Intervallmethode":       frozenset({"Körpergewicht"}),
    "GA2-Intervall 80–85 % HFmax":      frozenset({"Körpergewicht"}),
    "Shuttle-Intervall 40 m":           frozenset({"Körpergewicht"}),
    "Intensive Spielform 6v6":          frozenset({"Ball"}),
    "RSA 6×30 m mit Erholungsphase":    frozenset({"Körpergewicht"}),
    "Intensive Intervallmethode":       frozenset({"Körpergewicht"}),
    "High-Intensity Shuttle 40 m":      frozenset({"Körpergewicht"}),
    "Pressing-Simulation intensiv":     frozenset({"Ball"}),
    "Intermittierende Hochintensität":  frozenset({"Körpergewicht"}),
}


def _equip_expanded(equip_sel: set | None) -> set | None:
    """
    Expandiert 'Freie Gewichte' in der Auswahl auf alle Unterkategorien.
    Beispiel: {'Freie Gewichte', 'Miniband'} → {'Freie Gewichte', 'Miniband',
               'Kurzhanteln', 'Langhanteln', 'Kettlebell', 'Trap Bar', 'Landmine'}
    None → kein Filter (alles erlaubt).
    """
    if equip_sel is None:
        return None
    expanded = set(equip_sel)
    if "Freie Gewichte" in expanded:
        expanded.update(_FREIE_GEWICHTE_UNTERKAT)
    return expanded


def _equip_verfuegbar(uebung: str, equip_exp: set | None) -> bool:
    """
    Prüft ob eine Übung mit dem verfügbaren Equipment durchführbar ist.
    Gibt True zurück wenn:
    - equip_exp ist None (kein Filter) ODER
    - mindestens ein Equipment-Tag der Übung in equip_exp ist.
    Übungen ohne Dict-Eintrag werden als Körpergewicht-Übung behandelt.
    """
    if equip_exp is None:
        return True
    tags = _UEBUNG_EQUIPMENT.get(uebung, frozenset({"Körpergewicht"}))
    return bool(tags & equip_exp)


def _olympic_geeignet(plangruppe: str, pool_key: str, verletzt: set) -> bool:
    """
    Olympisches Gewichtheben nur wenn (Spec §6):
    - Athletisch geeignet: Senior oder U18 (Kraftbasis vorhanden)
    - Power-Phase (ausreichende Kraftbasis vorausgesetzt)
    - Keine relevante Verletzung (Rumpf/Schulter/Oberschenkel)
    """
    if plangruppe not in ("Senior", "U18"):
        return False
    if pool_key != "power":
        return False
    if verletzt & {"Rumpf", "Schulter", "Oberschenkel"}:
        return False
    return True


def belastungsnormative_berechnen(
    bereich: str,
    pool_key: str,
    alter: float | None,
    saison_phase: str,
    is_deload: bool,
    energie: str,
) -> dict:
    """
    Berechnet alle 10 Belastungsnormative dynamisch (Spec §1).
    Parameter passen sich automatisch an Diagnostik, Alter, Saisonphase an.
    Quellen: NSCA (2016), Zatsiorsky & Kraemer (2006), Buchheit & Laursen (2013)
    """
    pg  = _alter_zu_plangruppe(alter)
    cfg = _PLANGRUPPEN_CONFIG[pg]

    # ① RPE (1–10 modifizierte Borg-Skala)
    rpe = {"stabilisation": 5, "kraft": 7, "power": 8}.get(pool_key, 6)
    rpe += {"Vorbereitung": 1, "Saison": -1, "Nachsaison": -2}.get(saison_phase, 0)
    rpe += -1 if is_deload else 0
    # U7/U8/U10 und Ü55 erhalten eine zusätzliche RPE-Reduktion (Altersschutz)
    rpe += -1 if pg in ("U7", "U8", "U10", "Ü55") else 0
    rpe = max(4, min(10, rpe))

    # ② Belastungsintensität (% 1RM / Maximalleistung)
    _int = {"stabilisation": (50, 65), "kraft": (70, 80), "power": (82, 93)}
    lo, hi = _int.get(pool_key, (60, 75))
    if is_deload:
        lo, hi = max(40, lo - 15), max(55, hi - 15)
    # U7/U8/U10: Intensität weiter reduziert (Körpergewicht/technisch, kein Maximalkraft-Ziel)
    if pg in ("U7", "U8", "U10"):
        lo, hi = max(40, lo - 10), max(55, hi - 10)
    intensitaet = f"{lo}–{hi} % max. Leistung"

    # ③ Belastungsdauer
    belastungsdauer = {"stabilisation": "20–35 min", "kraft": "30–45 min", "power": "25–40 min"}.get(pool_key, "30 min")

    # ④ Belastungsumfang
    if is_deload:
        belastungsumfang = "Sehr niedrig — Deload (60–70 % max. Wochenvolumen)"
    else:
        belastungsumfang = {
            "stabilisation": "Niedrig (≤ 80 % max. Wochenvolumen)",
            "kraft":         "Mittel (80–100 % max. Wochenvolumen)",
            "power":         "Hoch (100–120 % max. Wochenvolumen)",
        }.get(pool_key, "Mittel")

    # ⑤ Belastungshäufigkeit
    belastungshaeufigkeit = {"stabilisation": "2–3×/Woche", "kraft": "2×/Woche", "power": "1–2×/Woche"}.get(pool_key, "2×/Woche")

    # ⑥ Belastungsdichte (Belastung:Pause-Verhältnis)
    belastungsdichte = {"stabilisation": "1:2", "kraft": "1:3", "power": "1:4–1:6"}.get(pool_key, "1:3")

    # ⑨ Pausenlänge (s) — bereichsspezifisch + altersbasiert
    pause_sek, _ = _BEREICH_PARAMS.get(
        (bereich, pool_key),
        (_PAUSE_FALLBACK.get(pool_key, 90), ""),
    )
    pause_sek = max(30, pause_sek + cfg["pause_offset"] + (-15 if is_deload else 0))

    # ⑩ HFmax (nur für Ausdauer-/Intervallbelastungen relevant)
    _hf = {"stabilisation": (65, 75), "kraft": (72, 82), "power": (82, 92)}
    hf_lo, hf_hi = _hf.get(pool_key, (70, 80))
    hfmax = f"{hf_lo}–{hf_hi} % HFmax" if energie in ("Aerob", "Laktazid", "Gemischt") else None

    # Angewendete Trainingsprinzipien (Spec §3)
    prinzipien: list[str] = []
    if bereich in ("Schnelligkeit", "Agilität"):
        prinzipien += ["Schnelligkeit vor Kraftausdauer", "Hohe neuronale vor metabolischer Belastung"]
    if bereich == "Explosivität" and pool_key in ("kraft", "power"):
        prinzipien.append("Komplexe Übungen vor einfachen (Plyometrie-Prinzip)")
    if bereich in ("Oberschenkel", "Knie"):
        prinzipien.append("Große Muskelgruppen vor kleinen")
    if bereich == "Rumpf" and pool_key == "stabilisation":
        prinzipien.append("Core/Stabilisation am Ende der Einheit")
    if bereich in ("Knie", "Oberschenkel") and pool_key == "stabilisation":
        prinzipien.append("Präventiver Fokus am Ende der Einheit")

    return {
        "rpe":                   rpe,
        "intensitaet":           intensitaet,
        "belastungsdauer":       belastungsdauer,
        "belastungsumfang":      belastungsumfang,
        "belastungshaeufigkeit": belastungshaeufigkeit,
        "belastungsdichte":      belastungsdichte,
        "pause_sek":             pause_sek,
        "hfmax":                 hfmax,
        "energie":               energie,
        "prinzipien":            prinzipien,
    }


def _generate_begruendung(
    bereich: str,
    pool_key: str,
    phase_name: str,
    phase_ziel: str,
    saison_phase: str,
    is_deload: bool,
    plangruppe: str,
    energie: str,
    seq_order: int,
) -> str:
    """
    Automatische Dokumentation je Trainingsblock (Spec §8).
    Erklärt: Reihenfolge, Parameter, Übungsauswahl, Prinzipien, Energiesystem.
    """
    _seq_labels = {
        1: "Aktivierung", 2: "Dynamisches Dehnen", 3: "Sprinttechnik",
        4: "Antrittsschnelligkeit", 5: "Maximalschnelligkeit", 6: "Plyometrie",
        7: "Olympisches Gewichtheben", 8: "Maximalkraft", 9: "Schnellkraft",
        10: "Explosivkraft", 11: "Mehrgelenk-komplex", 12: "Mehrgelenk-einfach",
        13: "Eingelenkig", 14: "Core", 15: "Stabilisation", 16: "Prävention",
        17: "Cool-down / Fußball",
    }
    seq_label = _seq_labels.get(seq_order, f"Block {seq_order}")
    parts = [
        f"Reihenfolge: Pos. {seq_order}/17 ({seq_label})",
        f"Phase: {phase_name}",
        f"Ziel: {phase_ziel}",
        f"Energiesystem: {energie}",
    ]
    if saison_phase != "Normal":
        parts.append(f"Saisonperiode {saison_phase}: Belastungsparameter angepasst")
    if is_deload:
        parts.append("Deload-Woche: Volumen −30–40 % für aktive Regeneration")
    if plangruppe not in ("Senior", "U18"):
        parts.append(f"Altersgruppe {plangruppe}: Übungsauswahl und Intensität altersadaptiert")
    return " | ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def defizit_score(schwerpunkt_text: str | dict[str, int]) -> dict[str, int]:
    """
    Liefert Prioritäten pro Trainingsbereich.

    Strukturierte Bereichsscores aus analytics.py werden unverändert verwendet.
    Der Textpfad bleibt nur für bestehende bzw. externe Aufrufer kompatibel.
    Score: 3 = primär, 2 = sekundär, 1 = tertiär.
    """
    if not schwerpunkt_text:
        return {}  # NO_DATA: keine Defizite, Basis-Modus aktiv
    if isinstance(schwerpunkt_text, dict):
        return {
            bereich: max(1, min(3, int(prioritaet)))
            for bereich, prioritaet in schwerpunkt_text.items()
            # Ausdauer nutzt einen eigenen altersgerechten Pool und gehört
            # deshalb nicht zu den normalen _POOL-Schlüsseln.
            if (bereich in _POOL or bereich == "Ausdauer") and prioritaet
        }
    txt = schwerpunkt_text.lower().strip()
    if not txt:
        return {}  # leer nach strip → Basis-Modus
    _mapping = [
        (["hüft", "huft", "gluteus", "becken", "seitenasymmetrie"],         "Hüfte"),
        (["knie", "valgus", "landungskontrolle", "sprungasymmetrie"],       "Knie"),
        # "ganzkörperstabilität", "stabilität", "schulter" → Rumpf/Core
        (["rumpf", "core", "rotations", "anti-rotation", "schulter",
          "stabilität", "stabilitaet", "ganzkörper", "ganzkoerper"],        "Rumpf"),
        (["oberschenkel", "hamstring", "nordisch"],                          "Oberschenkel"),
        (["sprunggelenk", "ankle", "wade", "fersengang"],                   "Sprunggelenk"),
        # "maximalgeschwindigkeit", "geschwindigkeit" → Schnelligkeit
        (["schnelligkeit", "sprint", "beschleunigung",
          "maximalgeschwindigkeit", "geschwindigkeit", "sprintschnelligkeit",
          "antrittsschnelligkeit"],                                          "Schnelligkeit"),
        (["explosiv", "sprung", "sprungkraft"],                             "Explosivität"),
        (["agil", "richtungswechsel", "505"],                               "Agilität"),
        (["fußball", "fussball"],                                           "Fußball"),
        # Ausdauer-Keywords → eigenständiger "Ausdauer"-Bereich (nicht Fußball-Bereich)
        (["ausdauer", "aerob", "intermittier", "yo-yo", "yoyo"],           "Ausdauer"),
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
    """Gibt die altersgerechte Ersatzübung zurück oder 'ok' (Übung beibehalten).

    Schutzprinzip U7/U8 (Spec §3 Altersschutz):
    Wenn kein eigener U7/U8-Ersatz vorhanden ist, greift der U10-Ersatz als Mindestschutz.
    So sind U7/U8 mindestens genauso streng geschützt wie U10 — nie weniger.
    """
    ersatz = _ALTERS_ERSATZ.get(uebung, {})
    if plangruppe in ersatz:
        return ersatz[plangruppe]
    # Fallback für U7/U8: U10-Ersatz verwenden (≥ U10-Schutz garantiert)
    if plangruppe in ("U7", "U8") and "U10" in ersatz:
        return ersatz["U10"]
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


# Basis-Modus: ausgewogene Schwerpunkte je Altersgruppe wenn keine Diagnosedaten vorliegen
# KEINE Defizite — diese Bereiche sind altersgerechte Trainingsschwerpunkte, keine Diagnosen
_BASIS_MODUS_BEREICHE: dict[str, dict[str, int]] = {
    # U7: Bewegungserfahrung & spielerische Koordination — keine Explosivität
    "U7":    {"Agilität": 2, "Schnelligkeit": 2, "Rumpf": 2},
    # U8: Koordination & Bewegungskompetenz — keine Plyometrie/Explosivität
    "U8":    {"Agilität": 2, "Schnelligkeit": 2, "Rumpf": 1, "Hüfte": 1},
    "U10":   {"Schnelligkeit": 2, "Agilität": 2, "Explosivität": 1, "Rumpf": 1, "Hüfte": 1},
    "U14":   {"Schnelligkeit": 2, "Agilität": 2, "Explosivität": 2, "Rumpf": 1, "Knie": 1},
    "U18":   {"Schnelligkeit": 2, "Explosivität": 2, "Agilität": 2, "Rumpf": 1, "Hüfte": 1},
    "Senior": {"Schnelligkeit": 2, "Explosivität": 2, "Rumpf": 2, "Hüfte": 1, "Agilität": 1},
    "Ü40":   {"Rumpf": 2, "Hüfte": 2, "Knie": 1, "Schnelligkeit": 1, "Agilität": 1},
    "Ü55":   {"Rumpf": 2, "Hüfte": 2, "Knie": 2, "Schnelligkeit": 1},
}


# ─── Zeitbudget-Konfiguration ─────────────────────────────────────────────────
# Bestimmt maximale Übungsanzahl pro Tag + Satz-Cap je verfügbarer Trainingszeit.
# Spec §8: Die Zeit muss die Planerstellung fachlich beeinflussen, nicht nur kürzen.
_ZEITBUDGET_CONFIG: dict[int, dict] = {
    20: {"max_ueb_tag": 4,  "satz_cap": 2, "warmup_min": 5,  "cooldown_min": 3},
    30: {"max_ueb_tag": 6,  "satz_cap": 2, "warmup_min": 5,  "cooldown_min": 3},
    45: {"max_ueb_tag": 9,  "satz_cap": 3, "warmup_min": 8,  "cooldown_min": 5},
    60: {"max_ueb_tag": 13, "satz_cap": 3, "warmup_min": 10, "cooldown_min": 5},
    75: {"max_ueb_tag": 17, "satz_cap": 4, "warmup_min": 10, "cooldown_min": 5},
    90: {"max_ueb_tag": 22, "satz_cap": 4, "warmup_min": 10, "cooldown_min": 5},
}


def _zeitbudget_cfg(trainingszeit_min: int) -> dict:
    """Nächstkleinere Konfiguration für die gewählte Trainingszeit."""
    for t in sorted(_ZEITBUDGET_CONFIG.keys(), reverse=True):
        if trainingszeit_min >= t:
            return _ZEITBUDGET_CONFIG[t]
    return _ZEITBUDGET_CONFIG[20]


def schaetze_uebungs_dauer_min(saetze_str: str, wdh_str: str,
                                pause_sekunden: int = 90) -> float:
    """Schätzt Übungsdauer in Minuten (aktive Zeit + Pausen)."""
    try:
        saetze = int(str(saetze_str).split("–")[0].strip().split("×")[0].strip())
    except (ValueError, AttributeError, IndexError):
        saetze = 3
    satz_aktiv_sek = 40   # ~40 s aktive Belastung pro Satz
    pause_total = pause_sekunden * max(0, saetze - 1)
    return round((saetze * satz_aktiv_sek + pause_total) / 60, 1)


def schaetze_tag_dauer_min(eintraege: list[dict]) -> float:
    """Schätzt Gesamtdauer aller Übungen eines Trainingstages in Minuten."""
    return round(sum(
        schaetze_uebungs_dauer_min(
            e.get("saetze", "3"), e.get("wiederholungen", "10"),
            int(e.get("pause_sekunden", 90))
        ) for e in eintraege
    ), 1)


def trainingsplan_multi_erstellen(spieler_id: int, schwerpunkt_text: str | dict[str, int],
                                  wochen: int = 8,
                                  alter: float | None = None,
                                  verletzung_bereiche: set | list | None = None,
                                  saison_phase: str = "Normal",
                                  verfuegbares_equipment: list | None = None,
                                  philosophie_key: str | None = None,
                                  trainingszeit_min: int = 60,
                                  plan_id: int | None = None,
                                  vb_anzahl: int | None = None) -> int:
    """
    Altersbasierter Trainingsplan mit klarer 4-Phasen-Progression.
    Spec §1–§8: Belastungsnormative, Trainingsreihenfolge, Trainingsprinzipien,
    Equipment-Fallback, Energiesysteme, Olymp. Gewichtheben-Gate, Dokumentation.
    Trainingsphilosophie-Spec §1–§6: philosophie_key steuert Übungsauswahl, Normative,
    Methoden, Intensität, Umfang, Häufigkeit, Progression.

    saison_phase: "Normal" | "Vorbereitung" | "Saison" | "Nachsaison"
    verletzung_bereiche: Set von _POOL-Bereichsnamen, die ausgeschlossen werden.
    verfuegbares_equipment: Liste verfügbarer Equipment-Typen; None = alles.
    philosophie_key: Schlüssel aus PHILOSOPHIEN-Dict; None = kein Override.
    """
    _verletzt  = set(verletzung_bereiche or [])
    _equip_set = set(verfuegbares_equipment) if verfuegbares_equipment else None
    _philo     = philosophie_key  # shorthand

    _saison_max_key: str | None = None
    _saison_force_deload = False
    if saison_phase == "Saison":
        wochen = min(wochen, 4)
        _saison_max_key = "kraft"
        _saison_force_deload = True
    elif saison_phase == "Nachsaison":
        wochen = min(wochen, 4)
        _saison_max_key = "stabilisation"

    wochen       = wochen if wochen in (4, 6, 8, 12) else 8
    basis_scores = defizit_score(schwerpunkt_text)
    plangruppe   = _alter_zu_plangruppe(alter)
    if not basis_scores:
        # Basis-Modus: keine Diagnosedaten → altersgerechte ausgewogene Schwerpunkte
        # Diese Bereiche sind KEINE Defizite, sondern allgemeine Trainingsschwerpunkte
        basis_scores = dict(_BASIS_MODUS_BEREICHE.get(plangruppe, _BASIS_MODUS_BEREICHE["Senior"]))
    cfg          = _PLANGRUPPEN_CONFIG[plangruppe]
    woche_config = _WOCHE_PLAN[wochen]

    from database import trainingsplan_eintrag_speichern
    from datetime import date

    # Zeitbudget-Konfiguration für diesen Plan
    _zb = _zeitbudget_cfg(trainingszeit_min)
    _zb_satz_cap = _zb["max_ueb_tag"]   # maximale Übungen pro Tag
    # Der Satz-Cap aus dem Zeitbudget begrenzt additional den Altersgruppen-Cap
    _zb_eff_satz = _zb["satz_cap"]

    total     = 0
    _position = 0   # globaler Positions-Zähler für Bearbeitbarkeit

    for w_idx, (pool_key, phase_name, phase_ziel, is_deload, vol_mult, offset) in enumerate(woche_config):
        woche = w_idx + 1

        if _saison_force_deload:
            is_deload = True
        pool_key = _max_pool_key(pool_key, cfg["max_pool_key"])
        if _saison_max_key:
            pool_key = _max_pool_key(pool_key, _saison_max_key)
        # Trainingsphilosophie: pool_key-Cap anwenden
        pool_key = philosophie_pool_cap(_philo, pool_key)

        scores = dict(basis_scores)
        if "Phase 4" in phase_name or saison_phase == "Saison":
            scores["Fußball"] = max(scores.get("Fußball", 0), 2)

        sorted_areas = sorted(scores.items(), key=lambda x: -x[1])

        # §2 Trainingsreihenfolge: Einträge sammeln und nach Sequenz-Slot sortieren
        week_entries: list[tuple] = []

        # §6 Olympisches Gewichtheben (gate-controlled)
        if _olympic_geeignet(plangruppe, pool_key, _verletzt):
            _ol_u, _ol_s, _ol_v, _ol_h = _OLYMPIC_POOL[offset % len(_OLYMPIC_POOL)]
            if is_deload:
                _ol_h = _ol_h.replace("2×", "1×")
            _, _ol_aust = _pause_und_ausfuehrung("Schnelligkeit", pool_key, is_deload, plangruppe)
            _ol_aust = "Maximale Technikqualität · " + _ol_aust
            _ol_begruend = (
                f"Reihenfolge: Pos. 7/17 (Olympisches Gewichtheben) | Phase: {phase_name} | "
                f"Ziel: {phase_ziel} | Energiesystem: ATP-KP | "
                f"Nur für {plangruppe}: Technikvoraussetzungen erfüllt (Spec §6)"
            )
            for _tag in _tags_fuer_haeufigkeit(_ol_h):
                week_entries.append((
                    7, _tag, "Explosivität", _ol_u, _ol_s, _ol_v, _ol_h,
                    180, _ol_aust, 8, "ATP-KP", "Langhantel", _ol_begruend,
                ))

        for area, score in sorted_areas:
            if area in _verletzt:
                continue
            # Trainingsphilosophie: Bereich gesperrt oder nicht erlaubt
            if not philosophie_bereich_erlaubt(_philo, area):
                continue
            if is_deload:
                # Standard-Deload: score-2 (kann 0 ergeben).
                # VB-Modus-Deload: mindestens 1 Exercise pro enthaltenen Bereich,
                # damit die einzige APH-Einheit nicht leer bleibt.
                n = max(1 if vb_anzahl is not None else 0, score - 2)
            else:
                n = score
            if n <= 0:
                continue

            # §4 Equipment-Fallback: Wenn Equipment nicht verfügbar → alternativer Pool-Key
            effective_pk = pool_key
            eq_primary   = _EQUIPMENT_PRIMÄR.get((area, pool_key), "Körpergewicht")
            if (_equip_set and eq_primary not in _equip_set
                    and eq_primary not in ("Körpergewicht", "Ball")):
                fallback = _EQUIPMENT_FALLBACK_POOL.get(eq_primary)
                if fallback:
                    effective_pk = _max_pool_key(fallback, "stabilisation")
                    eq_primary   = _EQUIPMENT_PRIMÄR.get((area, effective_pk), "Körpergewicht")

            # Ausdauer-Bereich nutzt altersgerechten Pool statt _POOL
            if area == "Ausdauer":
                exercises = _ausdauer_pool_fuer_plangruppe(plangruppe, effective_pk, n, offset=offset)
            else:
                exercises = _pool_fuer_area(area, effective_pk, n, offset=offset)

            # §4b Per-Übung Equipment-Filter (nach Pool-Key-Fallback)
            if _equip_set is not None:
                _equip_exp_set = _equip_expanded(_equip_set)
                _filtered = [e for e in exercises if _equip_verfuegbar(e[0], _equip_exp_set)]
                if not _filtered:
                    # Fallback 1: stabilisation-Pool des gleichen Bereichs versuchen
                    if area == "Ausdauer":
                        _fb_src = _ausdauer_pool_fuer_plangruppe(plangruppe, "stabilisation", n, offset=offset)
                    else:
                        _fb_src = _pool_fuer_area(area, "stabilisation", n, offset=offset)
                    _fb = [e for e in _fb_src if _equip_verfuegbar(e[0], _equip_exp_set)]
                    # Kein ungefilterter Fallback: lieber leer als inkompatible Übung
                    exercises = _fb  # kann leer sein → Bereich wird übersprungen
                else:
                    exercises = _filtered

            # §2 Sequenz-Slot + §5 Energiesystem + §8 Dokumentation
            seq_order = _TRAININGS_SEQUENZ.get((area, effective_pk), 15)
            energie   = _ENERGIE_SYSTEM.get((area, effective_pk), "Gemischt")
            begruend  = _generate_begruendung(
                area, effective_pk, phase_name, phase_ziel,
                saison_phase, is_deload, plangruppe, energie, seq_order,
            )

            # §1 Belastungsnormative (dynamisch) + Trainingsphilosophie-Override
            bnorm     = belastungsnormative_berechnen(
                area, effective_pk, alter, saison_phase, is_deload, energie,
            )
            bnorm     = philosophie_normativ(_philo, bnorm)
            pause_sek = bnorm["pause_sek"]
            _, aust   = _pause_und_ausfuehrung(area, effective_pk, is_deload, plangruppe)
            rpe       = bnorm["rpe"]

            # Philosophie: maximaler Satz-Cap + Zeitbudget-Cap (das Kleinere gewinnt)
            _eff_satz_cap = min(philosophie_satz_cap(_philo, cfg["max_saetze"]), _zb_eff_satz)

            # Philosophie: Häufigkeits-Override
            _philo_haeuf = philosophie_haeuf_cap(_philo)

            # Begruendung: Philosophie-Info anfügen
            _philo_label = PHILOSOPHIEN.get(_philo, {}).get("label", "") if _philo else ""
            if _philo_label:
                begruend += f" | Philosophie: {_philo_label}"

            for uebung, saetze, volumen, haeufigkeit in exercises:
                # Altersgerechter Übungsersatz
                ersatz = _ersatz_uebung(uebung, plangruppe)
                if ersatz is None:
                    continue
                if ersatz != "ok":
                    uebung, saetze, volumen, haeufigkeit = ersatz

                # Philosophie: Häufigkeit überschreiben wenn gesetzt
                if _philo_haeuf:
                    haeufigkeit = _philo_haeuf

                if is_deload:
                    haeufigkeit = haeufigkeit.replace("3×", "2×").replace("4×", "2×")
                if not is_deload and vol_mult >= 1.15:
                    saetze = _steigere_saetze(saetze, 1)

                saetze      = _saetze_begrenzen(saetze, _eff_satz_cap)
                haeufigkeit = _haeufigkeit_begrenzen(haeufigkeit, cfg["haeuf_cap"])
                tags        = _tags_fuer_haeufigkeit(haeufigkeit)

                # VB-Modus: Tag-Anzahl auf gewaehlte_athletik_anzahl begrenzen.
                # Im VB-Modus immer sequenzielle Tags 1..vb_anzahl verwenden —
                # kein altes [1,3]- oder [1,2,3]-Muster, das mehr Einheiten erzeugt als gewählt.
                if vb_anzahl is not None:
                    tags = list(range(1, vb_anzahl + 1))

                for tag in tags:
                    week_entries.append((
                        seq_order, tag, area, uebung, saetze, volumen, haeufigkeit,
                        pause_sek, aust, rpe, energie, eq_primary, begruend,
                    ))

        # §2 + §3 Trainingsreihenfolge erzwingen: erst nach Tag, dann nach Sequenz-Slot
        week_entries.sort(key=lambda e: (e[1], e[0]))

        # Zeitbudget-Cap: max N Übungen pro Trainingstag (Spec §8 — fachliche Verteilung)
        # Zähle Übungen pro Tag und verwerfe niedrigst-priorisierte wenn Limit überschritten
        _tag_counts: dict[int, int] = {}
        _filtered_entries = []
        for entry in week_entries:
            _t = entry[1]  # tag-Index
            _c = _tag_counts.get(_t, 0)
            if _c < _zb_satz_cap:   # _zb_satz_cap = max_ueb_tag aus Zeitbudget-Config
                _filtered_entries.append(entry)
                _tag_counts[_t] = _c + 1

        for seq_ord, tag, area, uebung, saetze, volumen, haeufigkeit, pause_sek, aust, rpe, energie, equipment, begruend in _filtered_entries:
            trainingsplan_eintrag_speichern(
                spieler_id, str(date.today()), woche,
                area, uebung, saetze, volumen, haeufigkeit,
                tag=tag,
                pause_sekunden=pause_sek,
                ausfuehrung=aust,
                rpe=rpe,
                energie_system=energie,
                equipment=equipment,
                begruendung=begruend,
                plan_id=plan_id,
                position=_position,
            )
            total     += 1
            _position += 1

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
    plangruppe: str = "Senior",
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
        if area == "Ausdauer":
            exercises = _ausdauer_pool_fuer_plangruppe(
                plangruppe, pool_key, n, offset=offset
            )
        else:
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


def zyklus_erstellen(spieler_id: int, schwerpunkt_text: str | dict[str, int],
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
                plan.extend(_woche_eintraege_zyklus(
                    w, wochen, scores, ph_name, ph_ziel, _pk, plangruppe
                ))
    else:
        block_size = max(1, wochen // max(1, len(_SHORT_PLAN_PHASE.get(wochen, [(1, "", "", "")]))))
        phase_defs = _SHORT_PLAN_PHASE.get(wochen, [(1, "stabilisation", "Stabilisation", "")])
        w = 1
        for phase_start, pool_key, ph_name, ph_ziel in phase_defs:
            _pk = _max_pool_key(pool_key, cfg["max_pool_key"])
            for week_nr in range(w, w + block_size):
                if week_nr > wochen:
                    break
                plan.extend(_woche_eintraege_zyklus(
                    week_nr, wochen, scores, ph_name, ph_ziel, _pk, plangruppe
                ))
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

def defizit_tabelle(schwerpunkt_text: str | dict[str, int]) -> list[dict]:
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


# ─────────────────────────────────────────────────────────────────────────────
# Wochenplanung: APH-Empfehlungslogik (Spec §9, §12, §13)
# ─────────────────────────────────────────────────────────────────────────────

_WOCHENTAGE_WP = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_WT_IDX_WP = {t: i for i, t in enumerate(_WOCHENTAGE_WP)}


def _schwerpunkt_intensitaet_wp(schwerpunkt_text: str | dict[str, int]) -> int:
    """
    Gibt die Intensitätsstufe des Trainingsschwerpunkts zurück.
    0 = leicht (Mobilität, Stabilität, Korrektiv)
    1 = mittel (Kraft, Hüfte, Knie, Agilität)
    2 = hoch (Sprint, Beschleunigung, Explosivkraft, Power, Schnelligkeit)
    """
    if isinstance(schwerpunkt_text, dict):
        bereiche = set(schwerpunkt_text)
        if bereiche & {"Schnelligkeit", "Explosivität"}:
            return 2
        if bereiche & {"Agilität", "Knie", "Hüfte", "Oberschenkel", "Fußball"}:
            return 1
        return 0

    txt = schwerpunkt_text.lower()
    if any(w in txt for w in ("sprint", "beschleunig", "explosiv", "power", "schnell",
                               "sprung", "maximum", "plyometrie")):
        return 2
    if any(w in txt for w in ("kraft", "agilität", "knie", "hüfte", "oberschenkel",
                               "fußball")):
        return 1
    return 0


def empfohlene_athletik_einheiten(
    alter: float | None,
    verein_anzahl: int,
    spielbelastung: str,
    saison_phase: str = "Normal",
    hat_defizite: bool = False,
    trainingszeit_min: int = 60,
) -> tuple[int, str]:
    """
    Berechnet die empfohlene Anzahl wöchentlicher Zusatz-Athletikeinheiten.
    Berücksichtigt: Alter, Vereinstraining, Spielbelastung, Saisonphase, Defizite.
    Spec §9, §8, §23.

    Returns:
        (anzahl, begruendung_text)
    """
    alter = alter or 18.0

    # Spielbelastungs-Score
    _spiel_scores = {
        "Kein Spiel": 0,
        "1 Spiel": 1,
        "2 Spiele": 2,
        "Turnier / mehrere Spiele": 3,
        "wechselnd": 1,
    }
    spiel_score = _spiel_scores.get(spielbelastung, 1)
    fussball_score = verein_anzahl + spiel_score  # Gesamtbelastung 0–9+

    # Altersabhängige Maximalgrenze (Spec §8 — keine Erwachsenen-Modelle auf Kinder)
    if alter < 10:
        max_empfehlung = 1
    elif alter < 12:
        max_empfehlung = 1
    elif alter < 14:
        max_empfehlung = 2
    elif alter < 16:
        max_empfehlung = 2
    elif alter < 18:
        max_empfehlung = 3
    else:
        max_empfehlung = 3

    # Saisonperiode-Anpassung (Spec §23)
    if saison_phase == "Nachsaison":
        max_empfehlung = min(max_empfehlung, 1)
    elif saison_phase == "Saison":
        max_empfehlung = min(max_empfehlung, 2)
    elif saison_phase == "Vorbereitung" and alter >= 14:
        max_empfehlung = min(max_empfehlung + 1, 4)

    # Hauptregel: Athletikbelastung im Verhältnis zur Fußballbelastung (Spec §7)
    if fussball_score <= 1:
        base = 2
        grund = "geringe Gesamtbelastung"
    elif fussball_score <= 3:
        base = 2 if hat_defizite else 1
        grund = "mittlere Fußballbelastung"
    elif fussball_score <= 5:
        base = 1
        grund = "hohe Fußballbelastung"
    else:
        base = 1
        grund = "sehr hohe Fußballbelastung"

    # Turnier-Reduktion
    if spielbelastung == "Turnier / mehrere Spiele":
        base = max(0, base - 1)
        grund += " + Turnierwoche"

    empfehlung = min(base, max_empfehlung)

    # Begründungstext
    teile = []
    if verein_anzahl > 0:
        teile.append(f"{verein_anzahl}× Vereinstraining")
    if spiel_score > 0:
        teile.append(spielbelastung)
    teile_str = " + ".join(teile) if teile else "keine Vereinsbelastung angegeben"

    begruendung = (
        f"Bei {teile_str} empfiehlt APH {empfehlung} zusätzliche "
        f"Athletikeinheit(en) pro Woche ({grund}"
    )
    if saison_phase != "Normal":
        begruendung += f", Saisonphase: {saison_phase}"
    if alter < 14:
        begruendung += f", altersgerechte Anpassung (U14)"
    elif alter < 18:
        begruendung += f", altersgerechte Anpassung (U18)"
    begruendung += ")."

    return empfehlung, begruendung


def empfohlene_athletik_tage(
    anzahl: int,
    verein_tage: list[str],
    spiel_tage: list[str],
    alter: float | None = None,
    schwerpunkt_text: str | dict[str, int] = "",
) -> list[str]:
    """
    Schlägt geeignete Wochentage für Athletikeinheiten vor.
    Berücksichtigt: Vereinstrainingstage, Spieltag, Intensität, Erholung.
    Spec §12, §13.

    Args:
        anzahl: Gewünschte Anzahl Athletiktage.
        verein_tage: z.B. ["Dienstag", "Donnerstag"]
        spiel_tage: z.B. ["Samstag"] — leer wenn kein Spiel.
        alter: Spieleralter (für zukünftige Erweiterungen).
        schwerpunkt_text: Trainingsinhalt-Text oder strukturierte Bereichsscores
            zur Intensitätseinschätzung.

    Returns:
        Sortierte Liste von Wochentagsnamen.
    """
    if anzahl <= 0:
        return []

    verein_idx = {_WT_IDX_WP[t] for t in verein_tage if t in _WT_IDX_WP}
    spiel_idx  = {_WT_IDX_WP[t] for t in spiel_tage  if t in _WT_IDX_WP}
    belegt     = verein_idx | spiel_idx
    intensitaet = _schwerpunkt_intensitaet_wp(schwerpunkt_text)

    # Freie Tage (nicht durch Vereinstraining/Spiel belegt)
    freie_tage = [i for i in range(7) if i not in belegt]

    def score(tag_idx: int) -> float:
        """Höherer Score = besserer Tag für Athletik."""
        s = 0.0
        # Abstand zu Spieltagen berücksichtigen
        for si in spiel_idx:
            abstand_vor_spiel = (si - tag_idx) % 7
            if abstand_vor_spiel == 1:
                # Direkt vor Spiel: intensive Inhalte stark bestrafen (Spec §13)
                s -= 10 if intensitaet >= 2 else 3
            elif abstand_vor_spiel == 2:
                s += 1   # 2 Tage vor Spiel: akzeptabel
            elif abstand_vor_spiel >= 4:
                s += 2   # Weit weg vom Spiel: gut
        # Abstand nach Vereinstraining
        for vi in verein_idx:
            abstand_nach_verein = (tag_idx - vi) % 7
            if abstand_nach_verein == 1:
                s += 1   # Tag nach Vereinstraining: Erholung hat begonnen
            elif abstand_nach_verein == 2:
                s += 2   # 2 Tage nach Vereinstraining: ideal
        # Freie Tage bevorzugen
        if tag_idx not in belegt:
            s += 1
        return s

    # Kandidaten sortieren: freie Tage bevorzugen, dann alle Tage
    kandidaten_frei = sorted(freie_tage, key=score, reverse=True)
    kandidaten_alle = sorted(range(7), key=score, reverse=True)
    # Fülle mit freien Tagen auf, dann falls nötig mit belegten Tagen
    gewaehlte_idx: list[int] = []
    for idx in kandidaten_frei:
        if len(gewaehlte_idx) >= anzahl:
            break
        gewaehlte_idx.append(idx)
    if len(gewaehlte_idx) < anzahl:
        for idx in kandidaten_alle:
            if idx not in gewaehlte_idx and len(gewaehlte_idx) < anzahl:
                gewaehlte_idx.append(idx)

    return [_WOCHENTAGE_WP[i] for i in sorted(gewaehlte_idx)]
