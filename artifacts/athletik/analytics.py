"""
Athletic analytics engine — trainer hints, deficit detection and performance score.

The APH performance score deliberately measures performance capability only.
Movement quality and trainer hints are evaluated separately and never reduce
the performance score.
"""

from dataclasses import dataclass, field

from fms import fms_hat_relevante_asymmetrie
from y_balance import y_balance_hat_relevante_asymmetrie


# ─── Internal helpers ─────────────────────────────────────────────────────────

_BEWERTUNG_SCORE = {
    # Strukturierte Status-IDs
    "sehr_gut": 95,
    "gut": 78,
    "mittel": 58,
    "entwicklungsbedarf": 30,
    # Lesbare Bestandswerte aus allen bisherigen Leistungsmodulen
    "Sehr gut": 95,
    "Sehr gut (Profi-Niveau)": 95,
    "Gut": 78,
    "Gut (Leistungssport)": 78,
    "Mittel": 58,
    "Mittel (Breitensport)": 58,
    "Durchschnittlich": 58,
    "Unterdurchschnittlich": 45,
    "Verbesserungsbedarf": 30,
    "Kritisch": 30,
}

# Transparente APH-Produktgewichtung, keine universelle wissenschaftliche Formel.
ATHLETIK_LEISTUNGSGEWICHTE = {
    "Richtungswechsel / COD": 30,
    "Sprint": 25,
    "Sprung / Power": 20,
    "Ausdauer": 15,
    "Kraft": 10,
}


def _wert(row, key, default=None):
    """Liest sqlite-Zeilen und Dict-Testdaten robust."""
    if not row:
        return default
    try:
        return row.get(key, default)
    except AttributeError:
        try:
            return row[key]
        except (KeyError, IndexError):
            return default


def _positive_zahl(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _bew_to_score(bew: str) -> int | None:
    """Übersetzt aktuelle und historische Bewertungslabels stabil zu 0–100."""
    return _BEWERTUNG_SCORE.get(str(bew or "").strip())


# ─── Risk Score ───────────────────────────────────────────────────────────────

def risiko_score(fms_row, y_row, verletzungen=None) -> int:
    """
    Returns a trainer-hint score 0–8+.
    0–1 = unauffällig | 2–3 = beobachten | 4+ = hoher Handlungsbedarf

    verletzungen: list of dicts/Rows with keys 'schwere' and 'ausfall_tage'.
    Der Wert ist keine individuelle Verletzungsprognose.
    """
    score = 0

    if fms_row:
        fms_score = _wert(fms_row, "score", 21)
        if fms_score <= 12:
            score += 2
        elif fms_score <= 14:
            score += 1
        if fms_hat_relevante_asymmetrie(fms_row):
            score += 2

    if y_row:
        comp_r = _wert(y_row, "composite_rechts", 0)
        comp_l = _wert(y_row, "composite_links", 0)
        avg = (comp_r + comp_l) / 2
        if avg < 85:
            score += 2
        elif avg < 89:
            score += 1
        if y_balance_hat_relevante_asymmetrie(y_row):
            score += 2

    # ── Verletzungshistorie ──────────────────────────────────────────────────
    if verletzungen:
        for v in verletzungen:
            schwere    = str(v.get("schwere") or "").lower()
            ausfall    = int(v.get("ausfall_tage") or 0)
            if "schwer" in schwere or ausfall > 28:
                score += 2
                break       # one severe injury is already max penalty
            elif "mittel" in schwere or ausfall >= 8:
                score += 1
                break       # one medium injury adds 1

    return score


def risiko_label(score: int) -> tuple[str, str]:
    """Returns trainer-oriented display label and level."""
    if score >= 4:
        return "Trainer-Handlungsbedarf hoch", "hoch"
    if score >= 2:
        return "Einzelne Hinweise / beobachten", "mittel"
    return "Unauffällig", "gering"


# ─── Leistungs-Athletikscore ──────────────────────────────────────────────────

@dataclass
class AthletikLeistungsbewertung:
    """Zentrale, transparente Leistungsbewertung für UI, Export und Diagnose."""

    gesamt_score: int | None
    module_scores: dict[str, int] = field(default_factory=dict)
    module_details: dict[str, dict] = field(default_factory=dict)
    nicht_scorefaehige_messwerte: list[str] = field(default_factory=list)

    @property
    def anzahl_bereiche(self) -> int:
        return len(self.module_scores)

    @property
    def datenbasis_text(self) -> str:
        anzahl = self.anzahl_bereiche
        if anzahl == 0:
            return "Keine scorefähigen Leistungsbereiche vorhanden"
        if anzahl == 1:
            return "1 von 5 Leistungsbereichen – nur Modulscore, kein Gesamt-Athletikscore"
        if anzahl == 2:
            return "2 von 5 Leistungsbereichen – eingeschränkte Aussagekraft"
        if anzahl == 3:
            return "3 von 5 Leistungsbereichen – mittlere Aussagekraft"
        return f"{anzahl} von 5 Leistungsbereichen – gute Aussagekraft"

    @property
    def gesamt_score_anzeigen(self) -> bool:
        return self.gesamt_score is not None


def _score_aus_bewertung(
    gespeichert: object,
    rohwert: float | None = None,
    test_key: str | None = None,
    alter: float | None = None,
    geschlecht: str = "Männlich",
) -> int | None:
    """Bevorzugt bestehende Bewertung; berechnet nur mit vorhandener Referenz."""
    # Die hinterlegten weiblichen Sprint-/CMJ-/COD-Schwellen sind aktuell
    # rechnerische Ableitungen, keine validierte Referenzstichprobe. Sie dürfen
    # weder live noch aus ihrem historischen Textlabel einen Leistungs-Score
    # erzeugen; der Messwert bleibt als Befund sichtbar.
    if geschlecht == "Weiblich" and test_key in {
        "10m", "30m", "cmj", "505_rechts", "505_links", "5_10_5", "t_test", "illinois",
    }:
        return None
    score = _bew_to_score(str(gespeichert or ""))
    if score is not None:
        return score
    if rohwert is None or alter is None or not test_key:
        return None
    if test_key in {"10m", "30m"}:
        from sprint import bewertung_sprint
        return _bew_to_score(bewertung_sprint(rohwert, test_key, geschlecht=geschlecht, alter=alter))
    if test_key == "cmj":
        from sprung import bewertung_cmj
        return _bew_to_score(bewertung_cmj(rohwert, geschlecht=geschlecht, alter=alter))
    if test_key in {"505_rechts", "505_links", "5_10_5", "t_test", "illinois"}:
        from agilitaet import bewertung
        return _bew_to_score(bewertung(rohwert, test_key, geschlecht=geschlecht, alter=alter))
    return None


def _sprint_bewertung(row, alter, geschlecht) -> tuple[int | None, dict, list[str]]:
    """10 m und 30 m sind die derzeit belastbar normierten Sprintdistanzen."""
    if not row:
        return None, {}, []
    teilwerte: list[tuple[str, int]] = []
    nicht_scorefaehig: list[str] = []
    for label, bew_key, wert_key in (
        ("10 m", "bewertung_10m", "beste_10m"),
        ("30 m", "bewertung_30m", "beste_30m"),
    ):
        raw = _positive_zahl(_wert(row, wert_key))
        score = _score_aus_bewertung(
            _wert(row, bew_key), raw, wert_key.replace("beste_", ""), alter, geschlecht
        )
        if score is not None:
            teilwerte.append((label, score))
    for label, key in (("5 m", "beste_5m"), ("20 m", "beste_20m"), ("40 m", "beste_40m")):
        if _positive_zahl(_wert(row, key)) is not None:
            nicht_scorefaehig.append(
                f"Sprint {label}: Messwert vorhanden – keine belastbare Referenzbewertung verfügbar"
            )
    if geschlecht == "Weiblich" and any(
        _positive_zahl(_wert(row, key)) is not None for key in ("beste_10m", "beste_30m")
    ):
        nicht_scorefaehig.append(
            "Sprint: weibliche Referenz ist derzeit nur abgeleitet und daher nicht scorewirksam"
        )
    if not teilwerte:
        return None, {}, nicht_scorefaehig
    return round(sum(score for _, score in teilwerte) / len(teilwerte)), {
        "scorewirksame_teiltests": [label for label, _ in teilwerte],
        "beschreibung": "Mittelwert der vorhandenen scorefähigen Sprintdistanzen",
    }, nicht_scorefaehig


def _power_bewertung(row, alter, geschlecht) -> tuple[int | None, dict, list[str]]:
    """CMJ ist scorefähig; Squat Jump bleibt ohne belastbare Projektnorm sichtbar."""
    if not row:
        return None, {}, []
    cmj = _score_aus_bewertung(
        _wert(row, "bewertung_cmj"),
        _positive_zahl(_wert(row, "cmj_beid")),
        "cmj",
        alter,
        geschlecht,
    )
    nicht_scorefaehig: list[str] = []
    if _positive_zahl(_wert(row, "squat_jump")) is not None:
        nicht_scorefaehig.append(
            "Squat Jump: Messwert vorhanden – keine belastbare Referenzbewertung verfügbar"
        )
    for label, key in (("Drop Jump", "drop_jump_hoehe"), ("RSI", "rsi"), ("Standweitsprung", "standweit")):
        if _positive_zahl(_wert(row, key)) is not None:
            nicht_scorefaehig.append(
                f"{label}: sichtbar als Leistungswert bzw. Hinweis, derzeit nicht scorewirksam"
            )
    if geschlecht == "Weiblich" and _positive_zahl(_wert(row, "cmj_beid")) is not None:
        nicht_scorefaehig.append(
            "CMJ: weibliche Referenz ist derzeit nur abgeleitet und daher nicht scorewirksam"
        )
    if cmj is None:
        return None, {}, nicht_scorefaehig
    return cmj, {
        "scorewirksame_teiltests": ["CMJ"],
        "beschreibung": "CMJ; Seitenunterschiede bleiben separat als Trainerhinweis",
    }, nicht_scorefaehig


def _cod_bewertung(row, alter, geschlecht) -> tuple[int | None, dict, list[str]]:
    """Bildet COD aus bis zu drei gleich gewichteten Bewegungs-Unterbereichen."""
    if not row:
        return None, {}, []

    unterbereiche: list[tuple[str, int, list[str]]] = []
    # 180° COD: beide Seiten gehören zu einem Unterbereich und werden gemittelt.
    s505: list[int] = []
    for key, label in (("t505_r", "505 rechts"), ("t505_l", "505 links")):
        raw = _positive_zahl(_wert(row, key))
        test_key = "505_rechts" if key == "t505_r" else "505_links"
        score = _score_aus_bewertung(None, raw, test_key, alter, geschlecht)
        if score is not None:
            s505.append(score)
    if not s505:
        legacy_505 = _score_aus_bewertung(
            _wert(row, "bew_505"), test_key="505_rechts", alter=alter, geschlecht=geschlecht
        )
        if legacy_505 is not None:
            s505.append(legacy_505)
    if s505:
        unterbereiche.append(("180° COD", round(sum(s505) / len(s505)), ["505"]))

    shuttle = _score_aus_bewertung(
        None,
        _positive_zahl(_wert(row, "t5_10_5")),
        "5_10_5",
        alter,
        geschlecht,
    )
    if shuttle is not None:
        unterbereiche.append(("Shuttle COD", shuttle, ["5-10-5"]))

    multi: list[tuple[str, int]] = []
    for raw_key, bew_key, test_key, label in (
        ("t_test", "bew_t_test", "t_test", "T-Test"),
        ("illinois", "bew_illinois", "illinois", "Illinois"),
    ):
        score = _score_aus_bewertung(
            _wert(row, bew_key),
            _positive_zahl(_wert(row, raw_key)),
            test_key,
            alter,
            geschlecht,
        )
        if score is not None:
            multi.append((label, score))
    if multi:
        unterbereiche.append((
            "Multidirektionaler COD",
            round(sum(score for _, score in multi) / len(multi)),
            [label for label, _ in multi],
        ))

    if not unterbereiche:
        if geschlecht == "Weiblich" and any(
            _positive_zahl(_wert(row, key)) is not None
            for key in ("t505_r", "t505_l", "t5_10_5", "t_test", "illinois")
        ):
            return None, {}, [
                "COD: weibliche Referenz ist derzeit nur abgeleitet und daher nicht scorewirksam"
            ]
        return None, {}, []
    return round(sum(score for _, score, _ in unterbereiche) / len(unterbereiche)), {
        "scorewirksame_teiltests": [name for _, _, labels in unterbereiche for name in labels],
        "unterbereiche": {name: score for name, score, _ in unterbereiche},
        "beschreibung": "Mittelwert der vorhandenen COD-Unterbereiche; 505-Asymmetrie bleibt ein Hinweis",
    }, []


def _ausdauer_bewertung(row, spiro_row) -> tuple[int | None, dict, list[str]]:
    """Bewertet einen Yo-Yo-Feldtest ohne Doppelanrechnung der VO₂-Schätzung."""
    nicht_scorefaehig: list[str] = []
    if spiro_row:
        nicht_scorefaehig.append(
            "Spiroergometrie: separat sichtbar, ohne protokollspezifisch vergleichbaren Score nicht scorewirksam"
        )
    if not row:
        return None, {}, nicht_scorefaehig
    score = _bew_to_score(str(_wert(row, "bewertung", "") or ""))
    if score is None:
        return None, {}, nicht_scorefaehig
    return score, {
        "scorewirksame_teiltests": ["Yo-Yo Feldtest"],
        "beschreibung": "Vorhandene Yo-Yo-Bewertung; VO₂-Schätzung erzeugt keinen Zusatzbonus",
    }, nicht_scorefaehig


def _kraft_bewertung(row, alter, geschlecht) -> tuple[int | None, dict, list[str]]:
    """Verwendet nur die vorhandene relative Bankdrückkraft als Oberkörperkraft."""
    if not row:
        return None, {}, []
    rel = _positive_zahl(_wert(row, "relative_kraft_direkt"))
    quelle = "Relative Bankdrückkraft (direkt)"
    if rel is None:
        rel = _positive_zahl(_wert(row, "relative_kraft_geschaetzt"))
        quelle = "Relative Bankdrückkraft (geschätzt)"

    nicht_scorefaehig: list[str] = []
    for label, key in (
        ("Ventrale Rumpfkraftausdauer", "ventral_sekunden"),
        ("Laterale Rumpfkraftausdauer", "lateral_rechts_sekunden"),
        ("Dorsale Rumpfkraftausdauer", "dorsal_sekunden"),
    ):
        if _positive_zahl(_wert(row, key)) is not None:
            nicht_scorefaehig.append(f"{label}: sichtbar als Trainerhinweis, nicht scorewirksam")
    if rel is None or alter is None:
        if rel is not None and alter is None:
            nicht_scorefaehig.append(
                "Relative Bankdrückkraft: Alter fehlt – keine altersgerechte Scorebewertung"
            )
        return None, {}, nicht_scorefaehig

    from age_norms import kraft_bewertung_alter
    bewertung, _ = kraft_bewertung_alter(rel, alter, geschlecht)
    score = _bew_to_score(bewertung)
    if score is None:
        return None, {}, nicht_scorefaehig
    return score, {
        "scorewirksame_teiltests": [quelle],
        "beschreibung": "Kraftscore basiert auf verfügbarer relativer Oberkörperkraft",
    }, nicht_scorefaehig


def athletik_leistungsbewertung(
    fms_row=None,
    y_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
    kraft_row=None,
    *,
    alter: float | None = None,
    geschlecht: str = "Männlich",
    geburtsdatum: str | None = None,
) -> AthletikLeistungsbewertung:
    """Ermittelt den APH-Leistungs-Score und seine transparente Datenbasis.

    FMS und Y-Balance werden bewusst nicht eingerechnet. Sie werden weiterhin
    über ``risiko_score`` und die strukturierte Defizitlogik als Trainerhinweis
    geführt. Fehlende Leistungsbereiche werden neutral behandelt.
    """
    module_scores: dict[str, int] = {}
    details: dict[str, dict] = {}
    nicht_scorefaehig: list[str] = []

    def _alter_zum_test(row) -> float | None:
        """Nutze das Testalter, wenn Geburts- und Messdatum vorliegen."""
        if geburtsdatum and _wert(row, "datum"):
            try:
                from database import alter_am_datum
                return alter_am_datum(geburtsdatum, _wert(row, "datum"))
            except (ImportError, TypeError, ValueError):
                pass
        return alter

    pruefungen = (
        ("Sprint", _sprint_bewertung(sprint_row, _alter_zum_test(sprint_row), geschlecht)),
        ("Sprung / Power", _power_bewertung(sprung_row, _alter_zum_test(sprung_row), geschlecht)),
        ("Richtungswechsel / COD", _cod_bewertung(agil_row, _alter_zum_test(agil_row), geschlecht)),
        ("Ausdauer", _ausdauer_bewertung(aus_row, spiro_row)),
        ("Kraft", _kraft_bewertung(kraft_row, _alter_zum_test(kraft_row), geschlecht)),
    )
    for name, (score, detail, nicht) in pruefungen:
        nicht_scorefaehig.extend(nicht)
        if score is not None:
            module_scores[name] = max(0, min(100, round(score)))
            details[name] = detail

    if len(module_scores) < 2:
        return AthletikLeistungsbewertung(
            gesamt_score=None,
            module_scores=module_scores,
            module_details=details,
            nicht_scorefaehige_messwerte=nicht_scorefaehig,
        )

    gewicht_summe = sum(ATHLETIK_LEISTUNGSGEWICHTE[name] for name in module_scores)
    gesamt = round(
        sum(module_scores[name] * ATHLETIK_LEISTUNGSGEWICHTE[name] for name in module_scores)
        / gewicht_summe
    )
    return AthletikLeistungsbewertung(
        gesamt_score=max(0, min(100, gesamt)),
        module_scores=module_scores,
        module_details=details,
        nicht_scorefaehige_messwerte=nicht_scorefaehig,
    )


def athletik_score(
    fms_row=None,
    y_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
    kraft_row=None,
    *,
    alter: float | None = None,
    geschlecht: str = "Männlich",
    geburtsdatum: str | None = None,
) -> int | None:
    """Kompatibler Kurzadapter: Gesamt-Score erst ab zwei Leistungsbereichen."""
    return athletik_leistungsbewertung(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row,
        spiro_row, kraft_row, alter=alter, geschlecht=geschlecht,
        geburtsdatum=geburtsdatum,
    ).gesamt_score


def athletik_sub_scores(
    fms_row=None,
    y_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
    kraft_row=None,
    *,
    alter: float | None = None,
    geschlecht: str = "Männlich",
    geburtsdatum: str | None = None,
) -> dict[str, int]:
    """Gibt die fünf Leistungs-Subscores für das Athletik-Radar zurück."""
    return athletik_leistungsbewertung(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row,
        spiro_row, kraft_row, alter=alter, geschlecht=geschlecht,
        geburtsdatum=geburtsdatum,
    ).module_scores


# ─── Defizite ────────────────────────────────────────────────────────────────

def defizite_ermitteln(
    fms_row,
    y_row,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    anthro_row=None,
    kraft_row=None,
    spiro_row=None,
    geschlecht: str = "Männlich",
    geburtsdatum: str | None = None,
) -> list[dict]:
    """
    Returns a deduplicated list of deficit dicts.  NO_DATA (None row) ≠ Defizit.
    Keys per entry:
      level     : 'kritisch' | 'warnung'
      bereich   : str  (canonical area — same bereich → merged, not duplicated)
      modul     : str  (source(s), e.g. 'FMS' or 'FMS + Y-Balance')
      text      : str  (most severe finding)
      datum     : str | None
      prioritaet: int  (3 = kritisch, 2 = warnung)
    """
    defizite: list[dict] = []
    seen: dict[str, int] = {}  # bereich → index in defizite

    def add(level: str, bereich: str, text: str, modul: str = "", datum=None):
        """Fügt ein Defizit hinzu oder führt gleiche Bereiche zusammen.
        NO_DATA = diese Funktion wird gar nicht aufgerufen (Guards oben)."""
        sev = 3 if level == "kritisch" else 2
        if bereich in seen:
            ex = defizite[seen[bereich]]
            if sev > ex["prioritaet"]:
                ex["level"] = level
                ex["text"] = text
                ex["prioritaet"] = sev
            if modul and modul not in ex["modul"]:
                ex["modul"] = (ex["modul"] + " + " + modul).strip(" + ")
            if datum and not ex["datum"]:
                ex["datum"] = datum
        else:
            seen[bereich] = len(defizite)
            defizite.append({
                "level": level, "bereich": bereich, "text": text,
                "modul": modul, "datum": datum, "prioritaet": sev,
            })

    # ── FMS ──────────────────────────────────────────────────────────────────
    if fms_row:
        s  = fms_row["score"]
        sw = str(fms_row.get("schwerpunkt") or "").lower()
        _d = fms_row.get("datum") or fms_row.get("erstellt_am")

        if s <= 12:
            add("kritisch", "Ganzkörperstabilität", "FMS-Score unter 13 — deutlicher Trainingsbedarf.", "FMS", _d)
        elif s <= 14:
            add("warnung", "Ganzkörperstabilität", "FMS-Score zeigt Verbesserungsbedarf.", "FMS", _d)

        if "hüft" in sw:
            add("kritisch", "Hüfte", "Auffälligkeit der Hüftstabilität im FMS erkannt.", "FMS", _d)
        if "rumpf" in sw or "core" in sw or "rotations" in sw:
            add("kritisch", "Core / Rumpf", "Rumpfstabilität auffällig im FMS.", "FMS", _d)
        if "sprunggelenk" in sw:
            add("warnung", "Sprunggelenk", "Sprunggelenk-Mobilität / -Stabilität auffällig.", "FMS", _d)
        if "knie" in sw:
            add("warnung", "Knie", "Beinachsenkontrolle auffällig im FMS.", "FMS", _d)
        if "schulter" in sw:
            add("warnung", "Schulter", "Schulterbeweglichkeit eingeschränkt im FMS.", "FMS", _d)

    # ── Y-Balance ────────────────────────────────────────────────────────────
    if y_row:
        asym = str(y_row.get("asymmetrie") or "").lower()
        sw   = str(y_row.get("schwerpunkt") or "").lower()
        _d   = y_row.get("datum") or y_row.get("erstellt_am")

        if "anterior" in asym:
            add("kritisch", "Sprunggelenk", "Anterior-Asymmetrie im Y-Balance-Test.", "Y-Balance", _d)
        if "posteromedial" in asym:
            add("kritisch", "Hüfte", "Posteromediale Asymmetrie — Beckenstabilität auffällig.", "Y-Balance", _d)
        if "posterolateral" in asym:
            add("kritisch", "Hüfte", "Posterolaterale Asymmetrie — Knie-/Hüftkontrolle auffällig.", "Y-Balance", _d)
        if "gluteus" in sw:
            add("warnung", "Hüfte", "Funktioneller Schwerpunkt Gluteus medius erkannt.", "Y-Balance", _d)
        if "becken" in sw:
            add("warnung", "Core / Rumpf", "Beckenstabilität als Trainingsschwerpunkt erkannt.", "Y-Balance", _d)

    # ── Sprint ────────────────────────────────────────────────────────────────
    if sprint_row:
        bew10  = str(sprint_row.get("bewertung_10m") or "")
        bew30  = str(sprint_row.get("bewertung_30m") or "")
        beschl_idx = sprint_row.get("beschl_index") or 0
        _d     = sprint_row.get("datum") or sprint_row.get("erstellt_am")
        _hat_bew10 = bool(bew10 and bew10 != "—")
        _hat_bew30 = bool(bew30 and bew30 != "—")
        _legacy_defizite = str(sprint_row.get("defizite") or "").lower()

        if bew10 == "Verbesserungsbedarf":
            add("kritisch", "Lineargeschwindigkeit", "10-m-Sprintzeit unter Referenzwert — Beschleunigung verbessern.", "Sprint", _d)
        elif bew10 == "Mittel (Breitensport)":
            add("warnung", "Lineargeschwindigkeit", "10-m-Sprintzeit im mittleren Bereich.", "Sprint", _d)
        elif not _hat_bew10 and any(
            kw in _legacy_defizite for kw in ("linearbeschleunigung", "antrittsschnelligkeit")
        ):
            add("warnung", "Lineargeschwindigkeit", "Historischer Sprintbefund weist auf Beschleunigungsbedarf hin.", "Sprint", _d)

        if bew30 == "Verbesserungsbedarf":
            add("kritisch", "Maximalgeschwindigkeit", "30-m-Sprintzeit unter Referenzwert — Maximalgeschwindigkeit verbessern.", "Sprint", _d)
        elif bew30 == "Mittel (Breitensport)":
            add("warnung", "Maximalgeschwindigkeit", "30-m-Sprintzeit im mittleren Bereich.", "Sprint", _d)
        elif not _hat_bew30 and (
            "maximalgeschwindigkeit" in _legacy_defizite
            or ("schnelligkeit" in _legacy_defizite and "antrittsschnelligkeit" not in _legacy_defizite)
        ):
            add("warnung", "Maximalgeschwindigkeit", "Historischer Sprintbefund weist auf Maximalgeschwindigkeitsbedarf hin.", "Sprint", _d)

        if not beschl_idx and "startexplosivität" in _legacy_defizite:
            add("warnung", "Startexplosivität", "Historischer Sprintbefund weist auf einen auffälligen Beschleunigungsindex hin.", "Sprint", _d)
        # Der Beschleunigungsindex ist ein strukturierter aktueller Wert und
        # bleibt unabhängig von 10-/30-m-Bewertungen maßgeblich.
        if beschl_idx and float(beschl_idx) > 0.60:
            add("warnung", "Startexplosivität", "Beschleunigungsindex erhöht — Reaktivkraft fördern.", "Sprint", _d)

    # ── Sprung ────────────────────────────────────────────────────────────────
    if sprung_row:
        bew_cmj      = str(sprung_row.get("bewertung_cmj") or "")
        asym         = sprung_row.get("cmj_asymmetrie") or 0
        rsi          = sprung_row.get("rsi") or 0
        defizit_text = str(sprung_row.get("defizite") or "")
        _d           = sprung_row.get("datum") or sprung_row.get("erstellt_am")

        if bew_cmj == "Verbesserungsbedarf":
            add("kritisch", "Explosivkraft", "CMJ-Sprunghöhe deutlich unter Normwert.", "Sprung", _d)
        elif bew_cmj == "Mittel (Breitensport)":
            add("warnung", "Explosivkraft", "CMJ-Sprunghöhe im mittleren Bereich.", "Sprung", _d)
        if asym and float(asym) > 10:
            add("kritisch", "Sprungasymmetrie",
                f"Einbeinige Sprungasymmetrie {float(asym):.1f} % — Seitenunterschied auffällig.", "Sprung", _d)
        if rsi and float(rsi) < 1.5:
            add("warnung", "Reaktivkraft", f"RSI = {float(rsi):.2f} — Drop-Jump-Reaktivkraft verbessern.", "Sprung", _d)
        if "Horizontalexplosivkraft" in defizit_text:
            add("warnung", "Horizontalexplosivkraft", "Standweitsprung unter Normwert.", "Sprung", _d)

    # ── Agilität ─────────────────────────────────────────────────────────────
    if agil_row:
        bew_t   = str(agil_row.get("bew_t_test") or "")
        bew_505 = str(agil_row.get("bew_505") or "")
        bew_ill = str(agil_row.get("bew_illinois") or "")
        asym505 = agil_row.get("asym_505") or 0
        _d      = agil_row.get("datum") or agil_row.get("erstellt_am")

        if bew_t == "Verbesserungsbedarf":
            add("kritisch", "Mehrdirektionale Agilität", "T-Test unter Referenzwert — Richtungswechselkraft verbessern.", "Agilität", _d)
        elif bew_t == "Mittel (Breitensport)":
            add("warnung", "Mehrdirektionale Agilität", "T-Test im mittleren Bereich.", "Agilität", _d)
        if bew_505 == "Verbesserungsbedarf":
            add("kritisch", "Richtungswechsel", "505-Test unter Referenzwert.", "Agilität", _d)
        if bew_ill == "Verbesserungsbedarf":
            add("warnung", "Gesamtagilität", "Illinois-Test unter Referenzwert — Gesamtagilität verbessern.", "Agilität", _d)
        if asym505 and float(asym505) > 10:
            add("kritisch", "Richtungswechsel-Asymmetrie",
                f"505-Test Seitenasymmetrie {float(asym505):.1f} % — Seitenunterschied auffällig.", "Agilität", _d)

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    if aus_row:
        bew         = str(aus_row.get("bewertung") or "")
        vo2max      = aus_row.get("vo2max") or 0
        yoyo_gruppe = str(aus_row.get("altersgruppe") or "Senioren")
        _d          = aus_row.get("datum") or aus_row.get("erstellt_am")

        if bew == "Verbesserungsbedarf":
            add("kritisch", "Intermittierende Ausdauer",
                "Yo-Yo IR-Ergebnis unter Normwert — Ausdauerkapazität verbessern.", "Ausdauer", _d)
        elif bew == "Mittel":
            add("warnung", "Intermittierende Ausdauer",
                "Yo-Yo IR-Ergebnis im mittleren Bereich.", "Ausdauer", _d)

        # Altersgerechte VO₂max-Bewertung statt altersblinder Pauschalschwelle.
        # Norm-Gruppe aus der gespeicherten Yo-Yo-Altersgruppe abgeleitet —
        # dadurch konsistent mit der Testbewertung, die ebenfalls altersabhängig ist.
        if vo2max and float(vo2max) > 0:
            from age_norms import _VO2_NORMEN_M, _VO2_NORMEN_W
            _YO_MAP = {
                "U8/U9": "U8", "U10/U11": "U10", "U12/U13": "U12",
                "U13/U14": "U14", "U15/U16": "U16", "U17/U18": "U18",
                "Senioren": "Senioren",
            }
            _normgruppe = _YO_MAP.get(yoyo_gruppe, "Senioren")
            _ist_w = "w" in geschlecht.lower() or "f" in geschlecht.lower()
            _tab   = _VO2_NORMEN_W if _ist_w else _VO2_NORMEN_M
            _n     = _tab.get(_normgruppe, _tab["Senioren"])
            _v     = float(vo2max)
            if _v < _n["Durchschnittlich"] * 0.85:
                add("kritisch", "Aerobe Kapazität",
                    f"VO₂max-Schätzung {_v:.1f} ml/kg/min — deutlich unter Norm für {_normgruppe} "
                    f"(Grenze: {_n['Durchschnittlich']:.0f}).", "Ausdauer", _d)
            elif _v < _n["Durchschnittlich"]:
                add("warnung", "Aerobe Kapazität",
                    f"VO₂max-Schätzung {_v:.1f} ml/kg/min — unter Norm für {_normgruppe} "
                    f"(Grenze: {_n['Durchschnittlich']:.0f}).", "Ausdauer", _d)

    # ── Anthropometrie ────────────────────────────────────────────────────────
    if anthro_row:
        from anthropometrie import bmi_bewertung_aus_messung
        bmi_status = bmi_bewertung_aus_messung(anthro_row, geburtsdatum, geschlecht)
        reife = str(anthro_row.get("reifestatus") or "").lower()
        _d    = anthro_row.get("datum") or anthro_row.get("erstellt_am")

        if bmi_status.code in {"severe_thinness", "obesity"}:
            add("kritisch", "Körperzusammensetzung",
                f"BMI {float(anthro_row['bmi']):.1f} — {bmi_status.kategorie} nach {bmi_status.referenz}.",
                "Anthropometrie", _d)
        elif bmi_status.code in {"underweight", "thinness", "overweight"}:
            add("warnung", "Körperzusammensetzung",
                f"BMI {float(anthro_row['bmi']):.1f} — {bmi_status.kategorie} nach {bmi_status.referenz}.",
                "Anthropometrie", _d)
        if "vor phv" in reife or "wachstumsschub" in reife:
            add("warnung", "Wachstum / Belastungssteuerung",
                "Spieler befindet sich im oder vor dem Wachstumsschub — Belastung anpassen.", "Anthropometrie", _d)

    # ── Kraftdiagnostik ───────────────────────────────────────────────────────
    if kraft_row:
        _d = kraft_row.get("datum") or kraft_row.get("erstellt_am")
        rel = kraft_row.get("relative_kraft_direkt") or kraft_row.get("relative_kraft_geschaetzt") or 0
        ventral = kraft_row.get("ventral_sekunden") or 0
        lateral_asym = kraft_row.get("lateral_asymmetrie_pct") or 0
        # Bereits bestehende Schwellen aus schwerpunkt_sammeln() unverändert nutzen.
        if rel and float(rel) < 1.0:
            add("warnung", "Rumpfkraft", "Relative Kraft unter bestehender Trainingsschwelle.", "Kraft", _d)
        if ventral and float(ventral) < 90:
            add("warnung", "Rumpfkraft", "Rumpfkraftausdauer unter bestehender Trainingsschwelle.", "Kraft", _d)
        if lateral_asym and float(lateral_asym) > 10:
            add("warnung", "Hüfte", "Laterale Kraftasymmetrie über bestehender Trainingsschwelle.", "Kraft", _d)
            add("warnung", "Rumpfkraft", "Laterale Kraftasymmetrie erfordert Rumpfstabilisierung.", "Kraft", _d)

    return defizite


# ─── Zentrale Defizit-zu-Trainingsbereich-Abbildung ───────────────────────────

_DEFIZIT_TRAININGSBEREICH = {
    "Ganzkörperstabilität": "Rumpf",
    "Core / Rumpf": "Rumpf",
    "Rumpfkraft": "Rumpf",
    "Schulter": "Rumpf",
    "Hüfte": "Hüfte",
    "Knie": "Knie",
    "Sprunggelenk": "Sprunggelenk",
    "Lineargeschwindigkeit": "Schnelligkeit",
    "Maximalgeschwindigkeit": "Schnelligkeit",
    "Startexplosivität": "Schnelligkeit",
    "Explosivkraft": "Explosivität",
    "Horizontalexplosivkraft": "Explosivität",
    "Reaktivkraft": "Explosivität",
    "Sprungasymmetrie": "Knie",
    "Mehrdirektionale Agilität": "Agilität",
    "Richtungswechsel": "Agilität",
    "Gesamtagilität": "Agilität",
    "Richtungswechsel-Asymmetrie": "Agilität",
    "Intermittierende Ausdauer": "Ausdauer",
    "Aerobe Kapazität": "Ausdauer",
    "Laktatschwelle": "Ausdauer",
}


def trainingsbereich_scores_ermitteln(
    fms_row=None,
    y_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    anthro_row=None,
    kraft_row=None,
    spiro_row=None,
    geschlecht: str = "Männlich",
    geburtsdatum: str | None = None,
) -> dict[str, int]:
    """Leitet Planbereiche ausschließlich aus strukturierten Defiziten ab.

    Anthropometrie bleibt absichtlich ein sichtbarer Kontext-/Hinweisbereich:
    Für BMI und Reifestatus wird ohne neue medizinische Interpretation kein
    Trainingsbereich erzeugt.
    """
    scores: dict[str, int] = {}
    for defizit in defizite_ermitteln(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row,
        anthro_row, kraft_row, spiro_row, geschlecht, geburtsdatum,
    ):
        bereich = _DEFIZIT_TRAININGSBEREICH.get(defizit["bereich"])
        if bereich:
            scores[bereich] = max(scores.get(bereich, 0), int(defizit["prioritaet"]))
    return scores


# ─── Schwerpunkt-Text ─────────────────────────────────────────────────────────

def sprint_trainingsschwerpunkte_ermitteln(
    sprint_row=None,
    fms_row=None,
    y_row=None,
) -> list[dict]:
    """
    Ermittelt mögliche Trainingsschwerpunkte aus Sprint + FMS + Y-Balance.

    Strenge Interpretationsregel (Spec §2, §35):
      - Keine Muskeldiagnosen aus Sprintzeiten allein.
      - Keine kausalen Aussagen ("Psoas schwach" o.ä.).
      - NO_DATA → leere Liste.
      - Nur VALID_DATA erzeugt Schwerpunkte.

    Rückgabe: Liste von dicts mit keys:
      bereich     : str  — Trainingsbereich
      beschreibung: str  — vorsichtige Formulierung
      quellen     : list[str]  — welche Tests diesen Bereich stützen
      prioritaet  : int  — 1 (gering) bis 3 (deutlich)
    """
    if not sprint_row:
        return []  # NO_DATA → keine Schwerpunkte

    bew10       = str(sprint_row.get("bewertung_10m") or "")
    bew30       = str(sprint_row.get("bewertung_30m") or "")
    beschl_idx  = sprint_row.get("beschl_index") or 0
    # "—" bedeutet "nicht gemessen" — für Logikprüfungen bereinigen
    if bew10 == "—":
        bew10 = ""
    if bew30 == "—":
        bew30 = ""

    # Auffälligkeiten aus validen Sprint-Daten ableiten
    sprint_beschl_auff = bew10 in ("Verbesserungsbedarf", "Mittel (Breitensport)")
    sprint_max_auff    = bew30 in ("Verbesserungsbedarf", "Mittel (Breitensport)")

    # Fallback: gespeichertes Defizite-Feld auswerten —
    # greift wenn z.B. nur 5m/20m/40m gemessen wurde und 10m/30m leer sind,
    # aber beim Speichern bereits ein Defizit erkannt und eingetragen wurde.
    _saved_def = str(sprint_row.get("defizite") or "").lower()
    if _saved_def:
        if not sprint_beschl_auff and any(
            kw in _saved_def for kw in (
                "linearbeschleunigung", "antrittsschnelligkeit", "beschleunigungsindex",
            )
        ):
            sprint_beschl_auff = True
        if not sprint_max_auff and any(
            kw in _saved_def for kw in (
                "maximalgeschwindigkeit", "schnelligkeit", "geschwindigkeit",
            )
        ):
            sprint_max_auff = True

    sprint_auff = sprint_beschl_auff or sprint_max_auff

    if not sprint_auff:
        return []  # Gute Sprintwerte → keine künstlichen Schwerpunkte (TEST F / TEST I)

    # FMS-Auffälligkeiten (§15)
    fms_hueft_auff = False
    fms_rumpf_auff = False
    if fms_row:
        sw = str(fms_row.get("schwerpunkt") or "").lower()
        s  = fms_row.get("score") or 21
        fms_hueft_auff = "hüft" in sw or (s is not None and int(s) <= 12)
        fms_rumpf_auff = any(kw in sw for kw in ("rumpf", "core", "rotations"))

    # Y-Balance-Auffälligkeiten (§16)
    yb_asymm_auff    = False
    yb_einbeinig_auff = False
    if y_row:
        asym = str(y_row.get("asymmetrie") or "").lower()
        sw   = str(y_row.get("schwerpunkt") or "").lower()
        yb_asymm_auff    = any(kw in asym for kw in ("posteromedial", "posterolateral", "anterior"))
        yb_einbeinig_auff = any(kw in sw for kw in ("gluteus", "becken")) or yb_asymm_auff

    schwerpunkte: list[dict] = []

    def _add(bereich: str, beschreibung: str, quellen: list, prioritaet: int = 2) -> None:
        for sp in schwerpunkte:
            if sp["bereich"] == bereich:
                if prioritaet > sp["prioritaet"]:
                    sp["prioritaet"] = prioritaet
                    sp["beschreibung"] = beschreibung
                for q in quellen:
                    if q not in sp["quellen"]:
                        sp["quellen"].append(q)
                return
        schwerpunkte.append({
            "bereich":      bereich,
            "beschreibung": beschreibung,
            "quellen":      list(quellen),
            "prioritaet":   prioritaet,
        })

    # ── Beschleunigung ────────────────────────────────────────────────────────
    if sprint_beschl_auff and (fms_hueft_auff or yb_einbeinig_auff):
        # §21: Mehrere Quellen → Bereich stärker priorisieren
        q = ["Sprintdiagnostik"]
        if fms_hueft_auff:    q.append("FMS")
        if yb_einbeinig_auff: q.append("Y-Balance")
        _add(
            "Hüft- und Beckenstabilität",
            "Möglicher leistungsrelevanter Trainingsbereich: Hüft- und Beckenstabilität — "
            "mehrere Tests zeigen Auffälligkeiten in für die Sprintbeschleunigung "
            "funktionell relevanten Bereichen.",
            q, 3,
        )
    elif sprint_beschl_auff:
        # §17: Sprint-Auffälligkeit ohne FMS/Y-Balance → Explosivkraft und Technik
        _add(
            "Beschleunigung und Explosivkraft",
            "Möglicher leistungsrelevanter Trainingsbereich: horizontale Kraftentwicklung "
            "und Sprintbeschleunigung.",
            ["Sprintdiagnostik"], 2,
        )
        _add(
            "Sprinttechnik",
            "Mögliches Trainingsfeld: Sprinttechnik und Antrittsoptimierung.",
            ["Sprintdiagnostik"], 1,
        )

    # ── Maximalgeschwindigkeit ────────────────────────────────────────────────
    if sprint_max_auff and (fms_rumpf_auff or yb_asymm_auff):
        q = ["Sprintdiagnostik"]
        if fms_rumpf_auff: q.append("FMS")
        if yb_asymm_auff:  q.append("Y-Balance")
        _add(
            "Rumpf- und Beckenstabilität",
            "Möglicher leistungsrelevanter Trainingsbereich: Core und Beckenstabilität "
            "als funktionelle Grundlage für die Maximalgeschwindigkeitsphase.",
            q, 2,
        )

    if sprint_max_auff:
        _add(
            "Hintere Kette und Reaktivkraft",
            "Mögliches Trainingsfeld: Maximal- und Reaktivkraft der hinteren Kette "
            "für die Maximalgeschwindigkeitsphase.",
            ["Sprintdiagnostik"], 2,
        )

    # ── Asymmetrie / einbeinige Kontrolle ─────────────────────────────────────
    if sprint_auff and yb_asymm_auff:
        _add(
            "Einbeinige Kontrolle und Seitenausgleich",
            "Möglicher Trainingsbereich: einbeinige Stabilität und Seitenausgleich — "
            "Sprintauffälligkeit liegt gleichzeitig mit einem Seitenunterschied vor.",
            ["Sprintdiagnostik", "Y-Balance"], 2,
        )

    # §18: Rumpfstabilität ergänzen bei Sprint + Core-Auffälligkeit
    if sprint_auff and fms_rumpf_auff and not any(
        sp["bereich"] == "Rumpf- und Beckenstabilität" for sp in schwerpunkte
    ):
        _add(
            "Rumpf- und Beckenstabilität",
            "Mögliches ergänzendes Trainingsfeld: Core-Stabilität — "
            "Rumpfauffälligkeit im FMS bei gleichzeitiger Sprintauffälligkeit.",
            ["Sprintdiagnostik", "FMS"], 1,
        )

    schwerpunkte.sort(key=lambda x: x["prioritaet"], reverse=True)
    return schwerpunkte


def schwerpunkt_sammeln(
    fms_row,
    y_row,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    kraft_row=None,
    spiro_row=None,
) -> str:
    """Kompatibler Textadapter über die zentrale strukturierte Defizitquelle.

    Neue Aufrufer sollen ``trainingsbereich_scores_ermitteln()`` direkt nutzen.
    Der Text bleibt für bestehende Schnittstellen erhalten und enthält bewusst
    nur kanonische Planbereiche, nicht mehr abweichende Modul-Keywords.
    """
    scores = trainingsbereich_scores_ermitteln(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row,
        kraft_row=kraft_row, spiro_row=spiro_row,
    )
    return " ".join(
        bereich.lower()
        for bereich, prioritaet in scores.items()
        for _ in range(prioritaet)
    )


# ── Erhaltungstraining ─────────────────────────────────────────────────────────
# Schwerpunkt-Text für unauffällige Diagnostik — liefert ausgewogene Coverage:
#   Rumpf/Core: 3 Treffer → Primär  |  Hüfte, Schnelligkeit, Explosivität,
#   Oberschenkel: 2 Treffer → Sekundär  |  Sprunggelenk, Agilität, Fußball: 1 → Tertiär
ERHALTUNGS_SCHWERPUNKT = (
    "hüfte becken sprunggelenk rumpf core rotations "
    "schnelligkeit sprint explosiv sprung oberschenkel hamstring "
    "agilität fußball"
)

# Begründungstext gemäß Spezifikation
ERHALTUNGS_BEGRUENDUNG = (
    "Die Diagnostik zeigt keine relevanten Defizite oder Asymmetrien. "
    "Daher wurde ein Erhaltungs- und Leistungssteigerungsprogramm erstellt. "
    "Ziel ist es, die aktuelle Leistungsfähigkeit langfristig zu sichern, "
    "Verletzungen vorzubeugen und gezielt weitere Leistungsreize zu setzen."
)


def testdaten_uebersicht(
    fms_row=None, y_row=None, sprint_row=None, sprung_row=None,
    agil_row=None, aus_row=None, spiro_row=None,
) -> dict[str, tuple[str, str | None]]:
    """Gibt pro Test {name: (status, datum)} zurück.
    Status: 'NO_DATA' | 'VALID_DATA'
    Dient der Transparenz-Anzeige im Trainingsbereich (Spec §20)."""
    def _s(row, *keys):
        if not row:
            return ("NO_DATA", None)
        for k in keys:
            v = row.get(k)
            if v:
                return ("VALID_DATA", str(v))
        return ("VALID_DATA", None)
    return {
        "FMS":        _s(fms_row,    "datum", "erstellt_am"),
        "Y-Balance":  _s(y_row,      "datum", "erstellt_am"),
        "Sprint":     _s(sprint_row, "datum", "erstellt_am"),
        "Sprung":     _s(sprung_row, "datum", "erstellt_am"),
        "Agilität":   _s(agil_row,   "datum", "erstellt_am"),
        "Ausdauer":   _s(aus_row,    "datum", "erstellt_am"),
        "Stufentest": _s(spiro_row,  "datum", "erstellt_am"),
    }


def ist_unauffaellig(
    fms_row=None,
    y_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
) -> bool:
    """True wenn ≥1 Test vorhanden und keine relevanten Defizite erkannt.
    Ein positiver Test → Erhaltungstraining, niemals 'kein Training notwendig'."""
    tests_vorhanden = any([fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row, spiro_row])
    if not tests_vorhanden:
        return False
    scores = trainingsbereich_scores_ermitteln(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row, spiro_row=spiro_row
    )
    return not scores
