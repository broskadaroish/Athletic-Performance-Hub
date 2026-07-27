"""
Football-specific training library — exercises categorised by body region.
Loads the default library into the DB on first run (idempotent).
"""

from database import training_count, training_bulk_insert, training_nach_bereich

# ─── Default exercise library ─────────────────────────────────────────────

_STANDARD_UEBUNGEN = [
    # Sprunggelenk
    ("Sprunggelenk", "Mobilität",         "Knie zur Wand Mobilisation",           "3", "10 je Seite",    "3x Woche"),
    ("Sprunggelenk", "Stabilität",        "Einbeinstand",                         "3", "30 Sekunden",    "3x Woche"),
    ("Sprunggelenk", "Stabilität",        "Balance Pad Einbeinstand",             "3", "30 Sekunden",    "3x Woche"),
    ("Sprunggelenk", "Kraft",             "Einbeinige Wadenheben",                "3", "12–15",           "3x Woche"),
    # Knie
    ("Knie",         "Valgus Kontrolle",  "Single Leg Squat",                     "3", "8–10 je Seite",  "3x Woche"),
    ("Knie",         "Landekontrolle",    "Step Down",                            "3", "8 je Seite",     "2x Woche"),
    ("Knie",         "Stabilität",        "Seitliche Sprünge stabilisieren",      "3", "8 je Seite",     "2x Woche"),
    ("Knie",         "Sprungkraft",       "Drop Landing",                         "3", "6",               "2x Woche"),
    # Hüfte
    ("Hüfte",        "Gluteus medius",    "Copenhagen Plank",                     "3", "20 Sekunden",    "3x Woche"),
    ("Hüfte",        "Beckenstabilität",  "Seitliches Miniband Gehen",            "3", "12 Meter",       "3x Woche"),
    ("Hüfte",        "Gluteus",           "Einbeinige Hüftbrücke",                "3", "10 je Seite",    "3x Woche"),
    ("Hüfte",        "Mobilität",         "90/90 Hüftrotation",                   "3", "10",              "2x Woche"),
    # Oberschenkel
    ("Oberschenkel", "Verletzungsprävention", "Nordic Hamstring Curl",            "3", "5–8",            "2x Woche"),
    ("Oberschenkel", "Kraft",             "Bulgarian Split Squat",                "3", "8 je Seite",     "2x Woche"),
    ("Oberschenkel", "Kraft",             "Einbeiniges rumänisches Kreuzheben",   "3", "8 je Seite",     "2x Woche"),
    # Rumpf
    ("Rumpf",        "Anti-Rotation",     "Pallof Press",                         "3", "12",              "3x Woche"),
    ("Rumpf",        "Stabilität",        "Plank",                                "3", "45 Sekunden",    "3x Woche"),
    ("Rumpf",        "Koordination",      "Bear Crawl",                           "3", "20 Meter",       "2x Woche"),
    ("Rumpf",        "Stabilität",        "Dead Bug",                             "3", "8 je Seite",     "3x Woche"),
    # Schnelligkeit
    ("Schnelligkeit","Antritt",           "10 m Sprintstarts",                    "6", "10 m",            "2x Woche"),
    ("Schnelligkeit","Beschleunigung",    "20 m Sprint",                          "6", "20 m",            "1x Woche"),
    ("Schnelligkeit","Reaktion",          "Reaktionssprints",                     "6", "5 Sekunden",     "1x Woche"),
    # Explosivität
    ("Explosivität", "Sprungkraft",       "Squat Jump",                           "3", "6",               "2x Woche"),
    ("Explosivität", "Reaktivkraft",      "Hürdensprünge",                        "3", "5",               "1x Woche"),
    ("Explosivität", "Einbeinige Kraft",  "Single Leg Jump",                      "3", "5 je Seite",     "1x Woche"),
    # Agilität
    ("Agilität",     "Richtungswechsel",  "5-10-5 Shuttle Run",                   "5", "Durchgänge",     "1x Woche"),
    ("Agilität",     "Bremsfähigkeit",    "Deceleration Drill",                   "5", "10 m",            "1x Woche"),
    # Fußball-spezifisch
    ("Fußball",      "Zweikampf",         "Einbeinige Stabilität mit Körperkontakt", "3", "20 Sekunden", "1x Woche"),
    ("Fußball",      "Duellkraft",        "Partner Widerstandsdrücken",           "3", "10 Sekunden",    "1x Woche"),
    ("Fußball",      "Ballkontrolle",     "Einbeinige Ballkontakte",              "3", "60 Sekunden",    "2x Woche"),
    ("Fußball",      "Koordination",      "Leitertraining",                       "5", "Durchgänge",     "1x Woche"),
    ("Fußball",      "Ausdauer",          "30-30 Intervallläufe",                 "10","30 Sekunden",    "1x Woche"),
    ("Fußball",      "RSA-Fähigkeit",     "Repeated Sprint Ability",              "6", "30 m",            "1x Woche"),
]


def init_training_bibliothek():
    """Idempotent: inserts default exercises only if the table is empty."""
    if training_count() == 0:
        training_bulk_insert(_STANDARD_UEBUNGEN)


def empfehlung_bereiche(schwerpunkt_text: str) -> list[str]:
    """
    Extract relevant training areas from a combined schwerpunkt string.
    Returns a deduplicated list in priority order.
    """
    text = schwerpunkt_text.lower()
    mapping = [
        ("sprunggelenk",   "Sprunggelenk"),
        ("knie",           "Knie"),
        ("hüft",           "Hüfte"),
        ("huft",           "Hüfte"),
        ("gluteus",        "Hüfte"),
        ("becken",         "Rumpf"),
        ("rumpf",          "Rumpf"),
        ("core",           "Rumpf"),
        ("rotations",      "Rumpf"),
        ("oberschenkel",   "Oberschenkel"),
        ("hamstring",      "Oberschenkel"),
        ("nordisch",       "Oberschenkel"),
        ("schulter",       "Rumpf"),
        ("schnelligkeit",  "Schnelligkeit"),
        ("explosiv",       "Explosivität"),
        ("agil",           "Agilität"),
        ("fußball",        "Fußball"),
        ("fussball",       "Fußball"),
    ]
    seen, bereiche = set(), []
    for keyword, area in mapping:
        if keyword in text and area not in seen:
            bereiche.append(area)
            seen.add(area)
    return bereiche


def uebungen_fuer_bereiche(bereiche: list[str]) -> dict[str, list]:
    """Return a dict of area → list of exercise rows."""
    result = {}
    for bereich in bereiche:
        rows = training_nach_bereich(bereich)
        if rows:
            result[bereich] = rows
    return result
