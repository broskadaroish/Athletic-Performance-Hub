"""
test_observations.py — Zentrale Beobachtungsstruktur für alle Tests
====================================================================
Jede Beobachtung hat:
  id        — eindeutige ID (String, z. B. "fms_std_komp")
  kat       — Kategorie (wird als Gruppenüberschrift angezeigt)
  text      — sichtbarer Text in der UI
  bericht   — Text für den generierten Satz (wird eingebettet)
  typ       — "positiv" | "auffaellig"
  modus     — "standard" | "experte"

Für Tests mit hat_seite=True wird der seite-Parameter in den Satz eingebettet.
Für Tests mit hat_auspraegung=True wird die Ausprägung (leicht/mittel/deutlich)
  als Adverb eingefügt.

Kein Eintrag enthält medizinische Diagnosen oder Sportfreigaben.
"""

from __future__ import annotations

_AUSP_ADV = {
    "leicht":   "leicht",
    "mittel":   "deutlich",
    "deutlich": "stark",
}

_SEITE_TEXT = {
    "rechts":     " (rechte Seite)",
    "links":      " (linke Seite)",
    "beidseitig": " (beidseitig)",
}

# ─── Beobachtungsdaten ────────────────────────────────────────────────────────

BEOBACHTUNGEN: dict[str, dict] = {

    "fms": {
        "test_name":      "FMS – Functional Movement Screen",
        "hat_seite":      False,
        "hat_auspraegung": False,
        "beobachtungen": [
            # Standard
            {"id": "fms_std_fluss",   "kat": "Bewegungsfluss",    "text": "Flüssige, kontrollierte Bewegungsausführung",             "bericht": "zeigte eine flüssige und kontrollierte Bewegungsausführung",                                  "typ": "positiv",    "modus": "standard"},
            {"id": "fms_std_komp",    "kat": "Bewegungsqualität", "text": "Sichtbare Kompensationsbewegungen",                       "bericht": "zeigte sichtbare Kompensationsbewegungen bei einzelnen FMS-Mustern",                         "typ": "auffaellig", "modus": "standard"},
            {"id": "fms_std_asym",    "kat": "Seitenasymmetrie",  "text": "Deutliche Seitenasymmetrie erkennbar",                    "bericht": "zeigte deutliche Seitenunterschiede in der Bewegungsausführung",                             "typ": "auffaellig", "modus": "standard"},
            {"id": "fms_std_mobil",   "kat": "Mobilität",         "text": "Eingeschränkte Beweglichkeit beobachtet",                 "bericht": "zeigte eingeschränkte Beweglichkeit in bestimmten Bereichen",                                "typ": "auffaellig", "modus": "standard"},
            {"id": "fms_std_stab",    "kat": "Stabilität",        "text": "Gute Rumpfstabilität vorhanden",                         "bericht": "zeigte gute Rumpfstabilität über alle FMS-Bewegungsmuster",                                 "typ": "positiv",    "modus": "standard"},
            {"id": "fms_std_beschw",  "kat": "Beschwerden",       "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            # Experte
            {"id": "fms_exp_squat_fersen", "kat": "Deep Squat",          "text": "Fersen heben sich beim Deep Squat",                    "bericht": "zeigte beim Deep Squat ein Anheben der Fersen",                                              "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_squat_fw",     "kat": "Deep Squat",          "text": "Starkes Vorneigen des Oberkörpers beim Deep Squat",     "bericht": "zeigte beim Deep Squat ein ausgeprägtes Vorneigen des Oberkörpers",                         "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_hurdle",       "kat": "Hurdle Step",         "text": "Gewichtsverlagerung beim Hurdle Step",                  "bericht": "zeigte beim Hurdle Step eine sichtbare Gewichtsverlagerung",                                 "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_lunge",        "kat": "Inline Lunge",        "text": "Gleichgewichtsprobleme bei der Inline Lunge",           "bericht": "zeigte bei der Inline Lunge Gleichgewichtsprobleme",                                         "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_shoulder",     "kat": "Shoulder Mobility",   "text": "Eingeschränkte Schulterrotation",                      "bericht": "zeigte eine eingeschränkte Schulterrotation bei der Shoulder-Mobility-Übung",                 "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_rotary",       "kat": "Rotary Stability",    "text": "Rumpfrotation nicht kontrolliert",                     "bericht": "zeigte bei der Rotary Stability eine unzureichend kontrollierte Rumpfrotation",                "typ": "auffaellig", "modus": "experte"},
            {"id": "fms_exp_trunk",        "kat": "Trunk Stability",     "text": "Rumpfstabilisierung beim Push-up eingeschränkt",       "bericht": "zeigte beim Trunk-Stability-Push-up eine eingeschränkte Rumpfstabilisierung",                 "typ": "auffaellig", "modus": "experte"},
        ],
        "konflikte": [
            ("fms_std_fluss", "fms_std_komp"),
            ("fms_std_fluss", "fms_std_asym"),
            ("fms_std_stab",  "fms_std_komp"),
        ],
    },

    "y_balance": {
        "test_name":      "Y-Balance Test",
        "hat_seite":      True,
        "hat_auspraegung": True,
        "beobachtungen": [
            {"id": "yb_std_stab",     "kat": "Stabilität",        "text": "Gute Standbein-Stabilität",                              "bericht": "zeigte eine gute Standbein-Stabilität beim Y-Balance Test",                                 "typ": "positiv",    "modus": "standard"},
            {"id": "yb_std_asym",     "kat": "Seitenasymmetrie",  "text": "Seitenunterschied in der Reichweite erkennbar",           "bericht": "zeigte einen sichtbaren Seitenunterschied in der Reichweite beim Y-Balance Test",            "typ": "auffaellig", "modus": "standard"},
            {"id": "yb_std_trunk",    "kat": "Rumpf",             "text": "Rumpf kippt beim Erreichen",                             "bericht": "zeigte beim Erreichen ein seitliches Abkippen des Rumpfs",                                   "typ": "auffaellig", "modus": "standard"},
            {"id": "yb_std_gleichgew","kat": "Gleichgewicht",     "text": "Gleichgewicht gut gehalten",                             "bericht": "hielt das Gleichgewicht während des Y-Balance Tests gut aufrecht",                            "typ": "positiv",    "modus": "standard"},
            {"id": "yb_std_fuss",     "kat": "Fußkontakt",        "text": "Standfuß hebt sich kurzzeitig",                          "bericht": "zeigte beim Y-Balance Test ein kurzzeitiges Abheben des Standfußes",                         "typ": "auffaellig", "modus": "standard"},
            {"id": "yb_std_beschw",   "kat": "Beschwerden",       "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            {"id": "yb_exp_knie",     "kat": "Knie",              "text": "Kniescheibe weicht nach innen (Valgus-Tendenz)",          "bericht": "zeigte beim Y-Balance Test eine Valgus-Tendenz am Standbein",                               "typ": "auffaellig", "modus": "experte"},
            {"id": "yb_exp_huefte",   "kat": "Hüfte",             "text": "Hüfte dreht kompensatorisch nach außen",                 "bericht": "zeigte beim Y-Balance Test eine kompensatorische Außendrehung der Hüfte",                    "typ": "auffaellig", "modus": "experte"},
            {"id": "yb_exp_anterior", "kat": "Richtung",          "text": "Anteriore Reichweite eingeschränkt",                     "bericht": "zeigte eine eingeschränkte Reichweite in der anterioren Richtung",                            "typ": "auffaellig", "modus": "experte"},
            {"id": "yb_exp_pm",       "kat": "Richtung",          "text": "Posteromediale Reichweite eingeschränkt",                 "bericht": "zeigte eine eingeschränkte Reichweite in der posteromedialen Richtung",                       "typ": "auffaellig", "modus": "experte"},
        ],
        "konflikte": [
            ("yb_std_gleichgew", "yb_std_trunk"),
            ("yb_std_gleichgew", "yb_std_fuss"),
            ("yb_std_stab",      "yb_std_asym"),
        ],
    },

    "sprint": {
        "test_name":      "Sprint-Diagnostik",
        "hat_seite":      False,
        "hat_auspraegung": True,
        "beobachtungen": [
            {"id": "spr_std_start",    "kat": "Start",          "text": "Gute Startposition und schnelle Reaktion",               "bericht": "zeigte eine gute Startposition und schnelle Reaktion",                                       "typ": "positiv",    "modus": "standard"},
            {"id": "spr_std_frueh",    "kat": "Lauftechnik",    "text": "Aufrichtung zu früh in der Beschleunigungsphase",        "bericht": "richtete sich in der Beschleunigungsphase zu früh auf",                                      "typ": "auffaellig", "modus": "standard"},
            {"id": "spr_std_arm_gut",  "kat": "Armeinsatz",     "text": "Armeinsatz unterstützt den Vortrieb",                   "bericht": "setzte die Arme effektiv zur Unterstützung des Vortriebs ein",                                "typ": "positiv",    "modus": "standard"},
            {"id": "spr_std_arm_schwach","kat": "Armeinsatz",   "text": "Armeinsatz unkoordiniert oder fehlend",                 "bericht": "zeigte einen unkoordinierten oder unzureichenden Armeinsatz",                                "typ": "auffaellig", "modus": "standard"},
            {"id": "spr_std_beschw",   "kat": "Beschwerden",    "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            {"id": "spr_exp_schrittl", "kat": "Schritttechnik", "text": "Schrittlänge in der Maximalgeschwindigkeit gering",     "bericht": "zeigte in der Maximalgeschwindigkeitsphase eine vergleichsweise geringe Schrittlänge",         "typ": "auffaellig", "modus": "experte"},
            {"id": "spr_exp_fuss",     "kat": "Fußaufsatz",     "text": "Fußaufsatz vor dem Körperschwerpunkt (Bremswirkung)",   "bericht": "zeigte einen Fußaufsatz vor dem Körperschwerpunkt mit erkennbarer Bremswirkung",              "typ": "auffaellig", "modus": "experte"},
            {"id": "spr_exp_huefte",   "kat": "Hüfte",          "text": "Geringe Hüftstreckung in der Antriebsphase",            "bericht": "zeigte in der Antriebsphase eine eingeschränkte Hüftstreckung",                              "typ": "auffaellig", "modus": "experte"},
            {"id": "spr_exp_kniehub",  "kat": "Kniehub",        "text": "Guter Kniehub in der Beschleunigungsphase",             "bericht": "zeigte in der Beschleunigungsphase einen guten Kniehub",                                     "typ": "positiv",    "modus": "experte"},
        ],
        "konflikte": [
            ("spr_std_arm_gut", "spr_std_arm_schwach"),
            ("spr_std_start",   "spr_std_frueh"),
        ],
    },

    "sprung": {
        "test_name":      "Sprung-Diagnostik",
        "hat_seite":      True,
        "hat_auspraegung": True,
        "beobachtungen": [
            {"id": "spg_std_explosiv",     "kat": "Explosivkraft",   "text": "Hohe Explosivkraft im Absprung",                      "bericht": "zeigte eine ausgeprägte Explosivkraft im Absprung",                                       "typ": "positiv",    "modus": "standard"},
            {"id": "spg_std_knie_valgus",  "kat": "Kniestabilität",  "text": "Kniescheibe weicht im Absprung nach innen",           "bericht": "zeigte im Absprung eine Kniescheibe, die nach innen abwich",                             "typ": "auffaellig", "modus": "standard"},
            {"id": "spg_std_landung_gut",  "kat": "Landung",         "text": "Kontrollierte, weiche Landung",                      "bericht": "zeigte eine kontrollierte und weiche Landung",                                            "typ": "positiv",    "modus": "standard"},
            {"id": "spg_std_landung_hart", "kat": "Landung",         "text": "Harte, unkontrollierte Landung",                     "bericht": "zeigte eine harte und unkontrollierte Landung",                                           "typ": "auffaellig", "modus": "standard"},
            {"id": "spg_std_asym",         "kat": "Asymmetrie",      "text": "Seitenasymmetrie beim einbeinigen Sprung erkennbar",  "bericht": "zeigte beim einbeinigen Absprung eine erkennbare Seitenasymmetrie",                      "typ": "auffaellig", "modus": "standard"},
            {"id": "spg_std_beschw",       "kat": "Beschwerden",     "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            {"id": "spg_exp_arm",          "kat": "Armeinsatz",      "text": "Armschwung unterstützt den Absprung effektiv",        "bericht": "nutzte den Armschwung effektiv zur Unterstützung des Absprungs",                          "typ": "positiv",    "modus": "experte"},
            {"id": "spg_exp_rumpf",        "kat": "Rumpfkontrolle",  "text": "Rumpf beugt sich bei der Landung stark vor",          "bericht": "zeigte bei der Landung ein ausgeprägtes Vorneigen des Rumpfs",                            "typ": "auffaellig", "modus": "experte"},
            {"id": "spg_exp_drop_reaktiv", "kat": "Drop Jump",       "text": "Kurze Bodenkontaktzeit beim Drop Jump",               "bericht": "zeigte beim Drop Jump eine effiziente, kurze Bodenkontaktzeit",                          "typ": "positiv",    "modus": "experte"},
        ],
        "konflikte": [
            ("spg_std_landung_gut", "spg_std_landung_hart"),
        ],
    },

    "agilitaet": {
        "test_name":      "Agilität",
        "hat_seite":      True,
        "hat_auspraegung": True,
        "beobachtungen": [
            {"id": "agil_std_schnell",  "kat": "Richtungswechsel", "text": "Schnelle, kontrollierte Richtungswechsel",              "bericht": "zeigte schnelle und kontrollierte Richtungswechsel",                                      "typ": "positiv",    "modus": "standard"},
            {"id": "agil_std_bremsung", "kat": "Abstopp",          "text": "Verzögerte oder unkontrollierte Abbremsphase",          "bericht": "zeigte eine verzögerte oder unkontrollierte Abbremsphase beim Richtungswechsel",           "typ": "auffaellig", "modus": "standard"},
            {"id": "agil_std_asym",     "kat": "Seitenasymmetrie", "text": "Seitenunterschied beim Richtungswechsel erkennbar",     "bericht": "zeigte erkennbare Unterschiede zwischen linkem und rechtem Richtungswechsel",               "typ": "auffaellig", "modus": "standard"},
            {"id": "agil_std_stab",     "kat": "Stabilität",       "text": "Gute Körperstabilität während der Richtungswechsel",   "bericht": "zeigte eine gute Körperstabilität während aller Richtungswechsel",                        "typ": "positiv",    "modus": "standard"},
            {"id": "agil_std_beschw",   "kat": "Beschwerden",      "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            {"id": "agil_exp_knie",     "kat": "Kniestabilität",   "text": "Kniestabilität beim Abstopp eingeschränkt",            "bericht": "zeigte beim Abstopp eine eingeschränkte Kniestabilität",                                  "typ": "auffaellig", "modus": "experte"},
            {"id": "agil_exp_huefte",   "kat": "Hüftposition",     "text": "Gute tiefe Hüftposition bei Richtungswechseln",        "bericht": "arbeitete bei den Richtungswechseln in einer guten, tiefen Hüftposition",                  "typ": "positiv",    "modus": "experte"},
            {"id": "agil_exp_fuss",     "kat": "Fußtechnik",       "text": "Fußaufsatz bei Richtungswechsel effizient",            "bericht": "zeigte beim Richtungswechsel einen technisch effizienten Fußaufsatz",                     "typ": "positiv",    "modus": "experte"},
        ],
        "konflikte": [
            ("agil_std_schnell", "agil_std_bremsung"),
            ("agil_std_stab",    "agil_std_asym"),
        ],
    },

    "ausdauer": {
        "test_name":      "Ausdauer / Yo-Yo Test",
        "hat_seite":      False,
        "hat_auspraegung": False,
        "beobachtungen": [
            {"id": "aus_std_leistung",      "kat": "Leistung",     "text": "Ausdauerleistung entspricht dem Trainingsstatus",       "bericht": "zeigte eine dem Trainingsstatus entsprechende Ausdauerleistung",                            "typ": "positiv",    "modus": "standard"},
            {"id": "aus_std_abbruch",       "kat": "Leistung",     "text": "Vorzeitiger Abbruch durch Erschöpfung",                "bericht": "brach den Test vorzeitig durch Erschöpfung ab",                                           "typ": "auffaellig", "modus": "standard"},
            {"id": "aus_std_technik_stabil","kat": "Lauftechnik",  "text": "Lauftechnik über den Test stabil",                    "bericht": "hielt die Lauftechnik über den gesamten Test stabil aufrecht",                             "typ": "positiv",    "modus": "standard"},
            {"id": "aus_std_technik_abfall","kat": "Lauftechnik",  "text": "Lauftechnik nimmt im Verlauf deutlich ab",             "bericht": "zeigte im Verlauf des Tests einen deutlichen Rückgang der Lauftechnikqualität",              "typ": "auffaellig", "modus": "standard"},
            {"id": "aus_std_motivation",    "kat": "Einsatz",      "text": "Hoher Einsatz und Motivation erkennbar",               "bericht": "zeigte während des Tests einen hohen Einsatz und eine gute Motivation",                   "typ": "positiv",    "modus": "standard"},
            {"id": "aus_std_beschw",        "kat": "Beschwerden",  "text": "Spieler gab Beschwerden an — Test angepasst / abgebrochen","bericht": "gab während des Tests Beschwerden an. Der Test wurde angepasst bzw. abgebrochen. Bei anhaltenden Beschwerden sollte eine medizinische oder therapeutische Fachperson hinzugezogen werden.", "typ": "auffaellig", "modus": "standard"},
            {"id": "aus_exp_atem",          "kat": "Atmung",       "text": "Gleichmäßige Atemkontrolle über die Testdauer",        "bericht": "zeigte eine gute Atemkontrolle über die gesamte Testdauer",                               "typ": "positiv",    "modus": "experte"},
            {"id": "aus_exp_hf_erholung",   "kat": "Herzfrequenz", "text": "Herzfrequenz-Erholung nach Test schnell",              "bericht": "zeigte nach Testende eine schnelle Herzfrequenz-Erholung",                                "typ": "positiv",    "modus": "experte"},
        ],
        "konflikte": [
            ("aus_std_leistung",       "aus_std_abbruch"),
            ("aus_std_technik_stabil", "aus_std_technik_abfall"),
        ],
    },

    "anthropometrie": {
        "test_name":      "Anthropometrie-Messung",
        "hat_seite":      False,
        "hat_auspraegung": False,
        "beobachtungen": [
            {"id": "anth_std_koop",      "kat": "Durchführung",   "text": "Gute Kooperation bei der Messung",                     "bericht": "zeigte eine gute Kooperation bei der Durchführung der Messung",                           "typ": "positiv",    "modus": "standard"},
            {"id": "anth_std_haltung",   "kat": "Messposition",   "text": "Messhaltung korrekt eingehalten",                      "bericht": "hielt die Messposition während der Körpergrößenmessung korrekt ein",                      "typ": "positiv",    "modus": "standard"},
            {"id": "anth_std_wachstum",  "kat": "Entwicklung",    "text": "Merkliches Längenwachstum seit letzter Messung",        "bericht": "zeigte seit der letzten Messung ein merkliches Längenwachstum",                          "typ": "positiv",    "modus": "standard"},
            {"id": "anth_std_gewicht",   "kat": "Entwicklung",    "text": "Deutliche Veränderung des Körpergewichts seit letzter Messung","bericht": "zeigte seit der letzten Messung eine deutliche Veränderung des Körpergewichts",  "typ": "auffaellig", "modus": "standard"},
            {"id": "anth_exp_reife",     "kat": "Reifestatus",    "text": "Reifestatus auffällig im Vergleich zur Altersgruppe",   "bericht": "zeigte einen im Vergleich zur Altersgruppe auffälligen Reifestatus",                    "typ": "auffaellig", "modus": "experte"},
        ],
        "konflikte": [],
    },
}


# ─── Öffentliche Hilfsfunktionen ──────────────────────────────────────────────

def get_test_info(test_id: str) -> dict | None:
    """Gibt Metadaten (test_name, hat_seite, hat_auspraegung) zurück."""
    d = BEOBACHTUNGEN.get(test_id)
    if not d:
        return None
    return {
        "test_name":       d["test_name"],
        "hat_seite":       d["hat_seite"],
        "hat_auspraegung": d["hat_auspraegung"],
    }


def get_beobachtungen(test_id: str, modus: str = "standard") -> list[dict]:
    """Gibt alle Beobachtungen für test_id gefiltert nach modus zurück.
    modus='experte' gibt Standard + Experte zurück."""
    d = BEOBACHTUNGEN.get(test_id, {})
    items = d.get("beobachtungen", [])
    if modus == "experte":
        return items
    return [b for b in items if b["modus"] == "standard"]


def check_konflikte(test_id: str, beob_ids: list[str]) -> list[tuple[str, str]]:
    """Gibt Konflikte zurück, bei denen beide IDs ausgewählt sind."""
    konflikte = BEOBACHTUNGEN.get(test_id, {}).get("konflikte", [])
    ids_set = set(beob_ids)
    return [(a, b) for a, b in konflikte if a in ids_set and b in ids_set]


def generate_observation_text(
    test_id: str,
    beob_ids: list[str],
    seite: str | None = None,
    auspraegung: str | None = None,
    freitext: str | None = None,
) -> str:
    """Erzeugt deutschen Beobachtungstext aus den gewählten IDs.

    Regeln:
    - Kein medizinischer Diagnose- oder Sportfreigabetext.
    - Positive und auffällige Beobachtungen werden getrennt aufgeführt.
    - Seite und Ausprägung werden eingebettet.
    - Beschwerden werden immer als neutraler Hinweis formuliert.
    """
    if not beob_ids and not freitext:
        return ""

    d = BEOBACHTUNGEN.get(test_id, {})
    items = {b["id"]: b for b in d.get("beobachtungen", [])}

    positiv   = []
    auffaellig = []

    seite_str   = _SEITE_TEXT.get(seite, "") if seite else ""
    ausp_str    = _AUSP_ADV.get(auspraegung, "") if auspraegung else ""

    for bid in beob_ids:
        b = items.get(bid)
        if not b:
            continue
        # Beschwerden-Text wird unverändert übernommen
        if "anhaltenden Beschwerden" in b["bericht"]:
            auffaellig.append(f"Der Spieler {b['bericht']}")
            continue

        bericht = b["bericht"]
        if ausp_str and d.get("hat_auspraegung"):
            bericht = bericht + f" ({ausp_str})"
        if seite_str and d.get("hat_seite"):
            bericht = bericht + seite_str

        if b["typ"] == "positiv":
            positiv.append(f"Der Spieler {bericht}.")
        else:
            auffaellig.append(f"Der Spieler {bericht}.")

    parts: list[str] = []

    if positiv:
        if len(positiv) == 1:
            parts.append(positiv[0])
        else:
            parts.append(" ".join(positiv))

    if auffaellig:
        if len(auffaellig) == 1:
            parts.append(auffaellig[0])
        else:
            parts.append(" ".join(auffaellig))

    if freitext and freitext.strip():
        parts.append(f"Zusätzliche Trainerbeobachtung: {freitext.strip()}")

    return " ".join(parts)
