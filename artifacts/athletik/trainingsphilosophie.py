"""
Trainingsphilosophie-Modul — Spec §1–§6

Definiert 11 Trainingsphilosophien als erweiterbare Daten-Dicts.
Neue Philosophien können ohne Programmänderungen hinzugefügt werden.

Exportierte API:
  PHILOSOPHIEN          — dict[key → definition]
  empfehle_philosophie  — automatische Empfehlung basierend auf Spielerprofil
  philosophie_normativ  — überschreibt Belastungsnormative basierend auf Philosophie
  philosophie_pool_cap  — begrenzt pool_key gemäß Philosophie
  philosophie_erklaerung — lesbare Begründung für die Empfehlung
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Philosophie-Definitionen
# Erweiterbar: neuen dict-Eintrag hinzufügen → kein weiterer Code nötig.
# ─────────────────────────────────────────────────────────────────────────────

PHILOSOPHIEN: dict[str, dict] = {

    "Kinderfußball": {
        "label":        "Kinderfußball (U8–U11)",
        "beschreibung": "Koordination, Spielfreude und Grundmotorik stehen im Vordergrund. "
                        "Kein Kraft- oder Hochintensitätstraining.",
        "ziel_plangruppen":   ["U10"],
        "pool_key_cap":       "stabilisation",
        "rpe_offset":         -2,
        "vol_faktor":         0.60,
        "satz_cap":           2,
        "pause_faktor":       0.80,
        "haeuf_cap_override": "2×/Woche",
        "erlaubte_bereiche":  None,   # None = alle erlaubt (Einschränkung über pool_key_cap)
        "gesperrte_bereiche": ["Explosivität"],
        "progression":        "langsam",
        "energiesystem_fokus":"Aerob",
        "trainingsmethoden":  ["Koordination", "Mobilität", "Stabilität"],
        "empfehle_wenn": {
            "max_alter": 12,
        },
    },

    "Grundlagenbereich": {
        "label":        "Grundlagenbereich (U12–U13)",
        "beschreibung": "Aufbau allgemeiner Bewegungsqualität und motorischer Grundlagen. "
                        "Leichte Kräftigung, kein Maximal- oder Explosivkrafttraining.",
        "ziel_plangruppen":   ["U14"],
        "pool_key_cap":       "kraft",
        "rpe_offset":         -1,
        "vol_faktor":         0.75,
        "satz_cap":           3,
        "pause_faktor":       0.90,
        "haeuf_cap_override": "3×/Woche",
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "langsam",
        "energiesystem_fokus":"Aerob",
        "trainingsmethoden":  ["Koordination", "Mobilität", "Stabilität", "Kraftausdauer"],
        "empfehle_wenn": {
            "min_alter": 11, "max_alter": 14,
        },
    },

    "Aufbaubereich": {
        "label":        "Aufbaubereich (U14–U16)",
        "beschreibung": "Systematischer Kraft- und Athletikaufbau. "
                        "Moderate Intensitäten, Technikfokus bei allen Übungen.",
        "ziel_plangruppen":   ["U14", "U18"],
        "pool_key_cap":       "kraft",
        "rpe_offset":         0,
        "vol_faktor":         0.85,
        "satz_cap":           4,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "moderat",
        "energiesystem_fokus":"Gemischt",
        "trainingsmethoden":  ["Koordination", "Stabilität", "Kraftausdauer", "Mobilität"],
        "empfehle_wenn": {
            "min_alter": 13, "max_alter": 17,
        },
    },

    "Leistungsbereich": {
        "label":        "Leistungsbereich (U17–U19)",
        "beschreibung": "Hochintensives Athletiktraining mit Vollprogression. "
                        "Olympisches Gewichtheben, Plyometrie und Maximalschnelligkeit erlaubt.",
        "ziel_plangruppen":   ["U18"],
        "pool_key_cap":       "power",
        "rpe_offset":         0,
        "vol_faktor":         1.00,
        "satz_cap":           5,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "leistungsorientiert",
        "energiesystem_fokus":"ATP-KP",
        "trainingsmethoden":  ["Maximalkraft", "Schnellkraft", "Explosivkraft", "Sprinttraining",
                               "Plyometrie", "Koordination"],
        "empfehle_wenn": {
            "min_alter": 16, "max_alter": 20,
        },
    },

    "Amateurfußball": {
        "label":        "Amateurfußball",
        "beschreibung": "Praxisorientiertes Athletiktraining für Freizeitspieler. "
                        "Balance zwischen Belastung und Regeneration.",
        "ziel_plangruppen":   ["Senior", "Ü40"],
        "pool_key_cap":       "kraft",
        "rpe_offset":         -1,
        "vol_faktor":         0.85,
        "satz_cap":           4,
        "pause_faktor":       1.10,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "moderat",
        "energiesystem_fokus":"Gemischt",
        "trainingsmethoden":  ["Stabilität", "Kraftausdauer", "Mobilität", "Koordination"],
        "empfehle_wenn": {
            "min_alter": 20, "max_alter": 50,
            "kein_nlz": True,
        },
    },

    "NLZ": {
        "label":        "Leistungszentrum (NLZ)",
        "beschreibung": "Wissenschaftlich fundiertes Hochleistungstraining in einem "
                        "Nachwuchsleistungszentrum. Alle Trainingsphasen, hohe Dichte.",
        "ziel_plangruppen":   ["U18", "Senior"],
        "pool_key_cap":       "power",
        "rpe_offset":         +1,
        "vol_faktor":         1.10,
        "satz_cap":           5,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "leistungsorientiert",
        "energiesystem_fokus":"ATP-KP",
        "trainingsmethoden":  ["Maximalkraft", "Schnellkraft", "Explosivkraft", "Sprinttraining",
                               "Plyometrie", "Ausdauertraining"],
        "empfehle_wenn": {
            "min_alter": 14, "max_alter": 28,
            "hohe_diagnostik": True,
        },
    },

    "Profifußball": {
        "label":        "Profifußball",
        "beschreibung": "Maximale Leistungssteigerung auf höchstem Niveau. "
                        "Volle Trainingsbelastung, individuell gesteuert.",
        "ziel_plangruppen":   ["Senior"],
        "pool_key_cap":       "power",
        "rpe_offset":         +2,
        "vol_faktor":         1.20,
        "satz_cap":           6,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "leistungsorientiert",
        "energiesystem_fokus":"ATP-KP",
        "trainingsmethoden":  ["Maximalkraft", "Schnellkraft", "Explosivkraft", "Sprinttraining",
                               "Plyometrie", "Koordination", "Ausdauertraining"],
        "empfehle_wenn": {
            "min_alter": 18, "max_alter": 36,
            "sehr_hohe_diagnostik": True,
        },
    },

    "Return-to-Play": {
        "label":        "Return-to-Play",
        "beschreibung": "Stufenweise Rückkehr nach Verletzung. "
                        "Schutzfokus, kein Hochintensitätstraining, erhöhte Pausen.",
        "ziel_plangruppen":   ["U10", "U14", "U18", "Senior", "Ü40", "Ü55"],
        "pool_key_cap":       "stabilisation",
        "rpe_offset":         -3,
        "vol_faktor":         0.55,
        "satz_cap":           2,
        "pause_faktor":       1.40,
        "haeuf_cap_override": "2×/Woche",
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": ["Schnelligkeit", "Explosivität"],
        "progression":        "langsam",
        "energiesystem_fokus":"Aerob",
        "trainingsmethoden":  ["Mobilität", "Stabilität", "Koordination"],
        "empfehle_wenn": {
            "verletzung_aktiv": True,
        },
    },

    "Prävention": {
        "label":        "Prävention",
        "beschreibung": "Verletzungsprävention und Stabilisierung. "
                        "Fokus auf Hüfte, Knie, Sprunggelenk und Rumpf.",
        "ziel_plangruppen":   ["U10", "U14", "U18", "Senior", "Ü40", "Ü55"],
        "pool_key_cap":       "kraft",
        "rpe_offset":         -1,
        "vol_faktor":         0.80,
        "satz_cap":           3,
        "pause_faktor":       1.10,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  ["Hüfte", "Knie", "Sprunggelenk", "Rumpf", "Oberschenkel"],
        "gesperrte_bereiche": [],
        "progression":        "langsam",
        "energiesystem_fokus":"Aerob",
        "trainingsmethoden":  ["Stabilität", "Mobilität", "Koordination", "Kraftausdauer"],
        "empfehle_wenn": {
            "niedriger_fms": True,
        },
    },

    "Leistungserhaltung": {
        "label":        "Leistungserhaltung",
        "beschreibung": "Erhalt der aufgebauten Leistungsfähigkeit in der Saison. "
                        "Reduziertes Volumen, gleichbleibende Intensität.",
        "ziel_plangruppen":   ["Senior", "U18", "Ü40"],
        "pool_key_cap":       "kraft",
        "rpe_offset":         -1,
        "vol_faktor":         0.80,
        "satz_cap":           4,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "moderat",
        "energiesystem_fokus":"Gemischt",
        "trainingsmethoden":  ["Stabilität", "Kraftausdauer", "Schnellkraft"],
        "empfehle_wenn": {
            "saison_phase": "Saison",
            "unauffaellig": True,
        },
    },

    "Leistungssteigerung": {
        "label":        "Leistungssteigerung",
        "beschreibung": "Gezielte Steigerung der athletischen Leistungsfähigkeit. "
                        "Progressive Überlastung, alle Trainingsphasen.",
        "ziel_plangruppen":   ["U18", "Senior", "Ü40"],
        "pool_key_cap":       "power",
        "rpe_offset":         +1,
        "vol_faktor":         1.10,
        "satz_cap":           5,
        "pause_faktor":       1.00,
        "haeuf_cap_override": None,
        "erlaubte_bereiche":  None,
        "gesperrte_bereiche": [],
        "progression":        "leistungsorientiert",
        "energiesystem_fokus":"ATP-KP",
        "trainingsmethoden":  ["Maximalkraft", "Schnellkraft", "Explosivkraft", "Sprinttraining", "Plyometrie"],
        "empfehle_wenn": {
            "saison_phase": "Vorbereitung",
            "unauffaellig": True,
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Empfehlungs-Engine
# ─────────────────────────────────────────────────────────────────────────────

def empfehle_philosophie(
    alter:             float | None    = None,
    plangruppe:        str | None      = None,
    fms_score:         float | None    = None,
    y_balance_ok:      bool | None     = None,
    sprint_score:      float | None    = None,  # normierter Score 0–100
    ausdauer_score:    float | None    = None,  # normierter Score 0–100
    saison_phase:      str             = "Normal",
    verletzung_aktiv:  bool            = False,
    diagnostik_score:  float | None    = None,  # 0–100, None = unbekannt
    trainingsalter:    float | None    = None,  # Jahre Trainingserfahrung
) -> tuple[str, float]:
    """
    Gibt (philosophie_key, confidence_0_to_1) zurück.
    Confidence 1.0 = starke Übereinstimmung, 0.5 = schwache Übereinstimmung.
    """
    scores: dict[str, float] = {k: 0.0 for k in PHILOSOPHIEN}

    # ── Verletzung: höchste Priorität ─────────────────────────────────────────
    if verletzung_aktiv:
        return "Return-to-Play", 1.0

    # ── FMS: niedriger Score → Prävention ────────────────────────────────────
    if fms_score is not None and fms_score < 14:
        scores["Prävention"]   += 3.0
        scores["Return-to-Play"] += 1.0

    # ── Alter / Plangruppe ────────────────────────────────────────────────────
    _alter = alter or 0.0
    pg     = plangruppe or ""

    if pg == "U10" or _alter < 12:
        scores["Kinderfußball"]   += 5.0
    elif pg == "U14" or 11 <= _alter <= 14:
        scores["Grundlagenbereich"] += 4.0
        scores["Aufbaubereich"]     += 2.0
    elif _alter <= 17:
        scores["Aufbaubereich"]   += 3.0
        scores["Leistungsbereich"] += 3.0
    elif _alter <= 20:
        scores["Leistungsbereich"] += 2.0
        scores["NLZ"]              += 2.0
        scores["Amateurfußball"]   += 1.0
    elif _alter <= 35:
        scores["Amateurfußball"]   += 2.0
        scores["NLZ"]              += 1.0
        scores["Profifußball"]     += 1.0
    else:  # Ü35+
        scores["Amateurfußball"]   += 3.0
        scores["Prävention"]       += 1.5

    # ── Saisonperiode ─────────────────────────────────────────────────────────
    if saison_phase == "Saison":
        scores["Leistungserhaltung"] += 4.0
        scores["Amateurfußball"]     += 1.0
    elif saison_phase == "Vorbereitung":
        scores["Leistungssteigerung"] += 4.0
        scores["NLZ"]                 += 1.0
    elif saison_phase == "Nachsaison":
        scores["Prävention"]          += 2.0
        scores["Leistungserhaltung"]  += 1.0

    # ── Diagnostik-Score (0–100, aggregiert) ──────────────────────────────────
    if diagnostik_score is not None:
        if diagnostik_score >= 85:
            scores["Leistungssteigerung"] += 3.0
            scores["NLZ"]                 += 2.0
            scores["Profifußball"]        += 1.5
        elif diagnostik_score >= 70:
            scores["Leistungserhaltung"]  += 2.0
            scores["Amateurfußball"]      += 1.5
        elif diagnostik_score < 50:
            scores["Prävention"]          += 2.0
            scores["Grundlagenbereich"]   += 1.0

    # ── Trainingsalter ─────────────────────────────────────────────────────────
    if trainingsalter is not None:
        if trainingsalter >= 5:
            scores["NLZ"]               += 1.5
            scores["Leistungssteigerung"] += 1.0
        elif trainingsalter < 1:
            scores["Kinderfußball"]     += 1.0
            scores["Grundlagenbereich"] += 1.5

    # Ergebnis: Key mit höchstem Score
    best_key  = max(scores, key=lambda k: scores[k])
    max_score = scores[best_key]
    # Confidence: normiert 0.5–1.0
    confidence = min(1.0, 0.5 + max_score / 12.0)
    return best_key, confidence


def philosophie_erklaerung(
    key:             str,
    alter:           float | None = None,
    plangruppe:      str | None   = None,
    fms_score:       float | None = None,
    saison_phase:    str          = "Normal",
    verletzung_aktiv:bool         = False,
    diagnostik_score:float | None = None,
    confidence:      float        = 0.8,
) -> str:
    """
    Liefert eine lesbare Begründung, warum diese Philosophie empfohlen wurde.
    Spec §4: Automatische Erklärung.
    """
    philo = PHILOSOPHIEN.get(key, {})
    label = philo.get("label", key)
    gruende: list[str] = []

    if verletzung_aktiv:
        gruende.append("aktive Verletzung erkannt")
    if fms_score is not None and fms_score < 14:
        gruende.append(f"FMS-Score {fms_score:.1f} < 14 (Bewegungsqualität eingeschränkt)")
    if plangruppe:
        gruende.append(f"Altersgruppe {plangruppe}")
    elif alter:
        gruende.append(f"Alter {alter:.0f} Jahre")
    if saison_phase != "Normal":
        _sp_labels = {
            "Vorbereitung": "Vorbereitungsphase (Aufbau)",
            "Saison": "laufende Saison (Erhaltung)",
            "Nachsaison": "Nachsaison (Regeneration)",
        }
        gruende.append(_sp_labels.get(saison_phase, saison_phase))
    if diagnostik_score is not None:
        if diagnostik_score >= 85:
            gruende.append(f"sehr guter Diagnostik-Score ({diagnostik_score:.0f}/100)")
        elif diagnostik_score < 50:
            gruende.append(f"Verbesserungsbedarf erkannt (Score {diagnostik_score:.0f}/100)")

    conf_text = f"{int(confidence * 100)} % Übereinstimmung" if confidence else ""
    gruende_text = ", ".join(gruende) if gruende else "allgemeine Eignung"
    return (
        f"Empfohlen: **{label}** — {gruende_text}. {conf_text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Normativ-Overrides: Philosophie modifiziert Belastungsnormative
# ─────────────────────────────────────────────────────────────────────────────

def philosophie_normativ(key: str | None, base: dict) -> dict:
    """
    Überschreibt Belastungsnormative gemäß Trainingsphilosophie.
    Gibt modifizierten dict zurück (base bleibt unverändert).
    Spec §3: Automatische Anpassungen.
    """
    if not key or key not in PHILOSOPHIEN:
        return base

    philo  = PHILOSOPHIEN[key]
    result = dict(base)

    # RPE anpassen
    raw_rpe = result.get("rpe", 6) + philo.get("rpe_offset", 0)
    result["rpe"] = max(3, min(10, raw_rpe))

    # Pausenlänge anpassen
    pf = philo.get("pause_faktor", 1.0)
    if pf != 1.0:
        result["pause_sek"] = int(result.get("pause_sek", 90) * pf)

    # Energiesystem-Fokus (override wenn explizit gesetzt)
    if philo.get("energiesystem_fokus") and philo["energiesystem_fokus"] != "Gemischt":
        result["energie"] = philo["energiesystem_fokus"]

    return result


def philosophie_pool_cap(key: str | None, pool_key: str) -> str:
    """
    Begrenzt pool_key auf das Maximum der gewählten Philosophie.
    Spec §3: pool_key_cap (stabilisation < kraft < power).
    """
    if not key or key not in PHILOSOPHIEN:
        return pool_key
    _order = {"stabilisation": 0, "kraft": 1, "power": 2}
    cap   = PHILOSOPHIEN[key].get("pool_key_cap", "power")
    if _order.get(pool_key, 1) > _order.get(cap, 2):
        return cap
    return pool_key


def philosophie_satz_cap(key: str | None, basis_cap: int) -> int:
    """Gibt den niedrigeren Satz-Cap (philosophie vs. plangruppe) zurück."""
    if not key or key not in PHILOSOPHIEN:
        return basis_cap
    philo_cap = PHILOSOPHIEN[key].get("satz_cap", 99)
    return min(basis_cap, philo_cap)


def philosophie_bereich_erlaubt(key: str | None, bereich: str) -> bool:
    """
    Gibt False zurück wenn der Bereich durch die Philosophie gesperrt ist,
    oder wenn erlaubte_bereiche definiert ist und der Bereich nicht darin vorkommt.
    """
    if not key or key not in PHILOSOPHIEN:
        return True
    philo = PHILOSOPHIEN[key]
    if bereich in (philo.get("gesperrte_bereiche") or []):
        return False
    erlaubt = philo.get("erlaubte_bereiche")
    if erlaubt is not None and bereich not in erlaubt:
        return False
    return True


def philosophie_haeuf_cap(key: str | None) -> str | None:
    """Gibt optionalen Häufigkeits-Override der Philosophie zurück."""
    if not key or key not in PHILOSOPHIEN:
        return None
    return PHILOSOPHIEN[key].get("haeuf_cap_override")
