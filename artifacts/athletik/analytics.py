"""
Athletic analytics engine — injury risk scoring, deficit detection,
and composite athleticism rating.
All functions operate on sqlite3.Row objects from the database layer.
"""


# ─── Internal helpers ─────────────────────────────────────────────────────────

_BEWERTUNG_SCORE = {
    # Strukturierte Status-IDs (neu, stabil)
    "sehr_gut":           95,
    "gut":                78,
    "mittel":             58,
    "entwicklungsbedarf": 30,
    # Lesbare Bezeichnungen (Altbestand, bleiben für Rückwärtskompatibilität)
    "Sehr gut (Profi-Niveau)":    95,
    "Gut (Leistungssport)":       78,
    "Mittel (Breitensport)":      58,
    "Verbesserungsbedarf":        30,
    # Ausdauer verwendet eine vereinfachte Skala
    "Gut":                        85,
    "Mittel":                     60,
}


def _bew_to_score(bew: str) -> int | None:
    """Translate a text evaluation to a 0-100 sub-score.  None = no data."""
    return _BEWERTUNG_SCORE.get(bew)


# ─── Risk Score ───────────────────────────────────────────────────────────────

def risiko_score(fms_row, y_row, verletzungen=None) -> int:
    """
    Returns a numeric risk score 0–8+.
    0–1 = low  |  2–3 = medium  |  4+ = high

    verletzungen: list of dicts/Rows with keys 'schwere' and 'ausfall_tage'.
    """
    score = 0

    if fms_row:
        fms_score = fms_row["score"]
        if fms_score <= 12:
            score += 2
        elif fms_score <= 14:
            score += 1
        if "Asymmetrie" in str(fms_row["asymmetrie"]):
            score += 2  # Asymmetrie ist stärkerer Prädiktor als Rohscore (Kiesel et al. 2007)

    if y_row:
        comp_r = y_row["composite_rechts"]
        comp_l = y_row["composite_links"]
        avg = (comp_r + comp_l) / 2
        if avg < 85:
            score += 2
        elif avg < 89:
            score += 1
        if "Asymmetrie" in str(y_row["asymmetrie"]):
            score += 2  # Bilaterale Asymmetrie erhöhtes Verletzungsrisiko (Plisky et al. 2006)

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
    """Returns (label, level) where level is 'hoch'/'mittel'/'gering'."""
    if score >= 4:
        return "Erhöhte Hinweise — Trainer prüft", "hoch"
    if score >= 2:
        return "Einzelne Hinweise vorhanden", "mittel"
    return "Keine auffälligen Hinweise", "gering"


# ─── Athletik Score ───────────────────────────────────────────────────────────

def athletik_score(
    fms_row,
    y_row,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
) -> int:
    """
    Composite athleticism score 0–100.

    Weights (only available modules are counted; missing modules are skipped
    and the remaining weight is redistributed):
        FMS             18 %
        Y-Balance       18 %
        Sprint          13 %
        Sprung          13 %
        Agilität        13 %
        Ausdauer        13 %
        Spiro (VO₂peak) 12 %
    All seven weights sum to 100, so each module contributes exactly its
    stated percentage when all data is present.
    """
    # Weights sum to 100 when all 7 modules are present,
    # so each module contributes exactly its stated percentage.
    weights = {
        "fms":    18,
        "y":      18,
        "sprint": 13,
        "sprung": 13,
        "agil":   13,
        "aus":    13,
        "spiro":  12,
    }

    sub_scores: dict[str, int] = {}

    # ── FMS ──────────────────────────────────────────────────────────────────
    if fms_row:
        s = fms_row["score"]
        sub = round(s / 21 * 100)
        if "Asymmetrie" in str(fms_row["asymmetrie"]):
            sub = max(0, sub - 10)
        sub_scores["fms"] = sub

    # ── Y-Balance ────────────────────────────────────────────────────────────
    if y_row:
        avg = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        # Target norm is 94 %; map linearly with floor at 70 % → 0
        sub = round(min(100, max(0, (avg - 70) / (100 - 70) * 100)))
        if "Asymmetrie" in str(y_row["asymmetrie"]):
            sub = max(0, sub - 10)
        sub_scores["y"] = sub

    # ── Sprint ────────────────────────────────────────────────────────────────
    if sprint_row:
        bew = str(sprint_row.get("bewertung_10m") or sprint_row.get("bewertung_30m") or "")
        s = _bew_to_score(bew)
        if s is not None:
            sub_scores["sprint"] = s

    # ── Sprung ────────────────────────────────────────────────────────────────
    if sprung_row:
        bew = str(sprung_row.get("bewertung_cmj") or "")
        s = _bew_to_score(bew)
        if s is not None:
            asym = sprung_row.get("cmj_asymmetrie") or 0
            if asym and float(asym) > 10:
                s = max(0, s - 10)
            sub_scores["sprung"] = s

    # ── Agilität ─────────────────────────────────────────────────────────────
    if agil_row:
        bew = str(agil_row.get("bew_t_test") or agil_row.get("bew_505") or "")
        s = _bew_to_score(bew)
        if s is not None:
            asym = agil_row.get("asym_505") or 0
            if asym and float(asym) > 10:
                s = max(0, s - 8)
            sub_scores["agil"] = s

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    if aus_row:
        bew = str(aus_row.get("bewertung") or "")
        s = _bew_to_score(bew)
        if s is not None:
            # VO2max bonus/malus
            vo2 = aus_row.get("vo2max") or 0
            if vo2 and float(vo2) >= 55:
                s = min(100, s + 5)
            sub_scores["aus"] = s

    # ── Spiroergometrie (VO₂peak) ─────────────────────────────────────────────
    if spiro_row:
        vo2 = spiro_row.get("vo2_peak") or spiro_row.get("vo2_max")
        if vo2:
            # Linear map: 35 ml/kg/min → 0, 65 ml/kg/min → 100
            sub_scores["spiro"] = round(min(100, max(0, (float(vo2) - 35) / 30 * 100)))

    if not sub_scores:
        return 0  # no data at all

    # Redistribute weights for missing modules
    available_weight = sum(weights[k] for k in sub_scores)
    if available_weight == 0:
        return 0

    total = sum(sub_scores[k] * weights[k] for k in sub_scores) / available_weight
    return max(0, min(100, round(total)))


# ─── Sub-scores für Radar-Chart ───────────────────────────────────────────────

def athletik_sub_scores(
    fms_row,
    y_row,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    spiro_row=None,
) -> dict[str, int]:
    """
    Gibt normierte Einzelwerte (0–100) pro Modul zurück — Grundlage für
    den Radar-Chart 'Athletisches Profil'.

    Schlüssel: 'FMS', 'Y-Balance', 'Sprint', 'Sprungkraft', 'Agilität', 'Ausdauer', 'Spiro'
    Nur Module mit Daten sind enthalten.
    """
    scores: dict[str, int] = {}

    if fms_row:
        s = round(fms_row["score"] / 21 * 100)
        if "Asymmetrie" in str(fms_row.get("asymmetrie", "")):
            s = max(0, s - 10)
        scores["FMS"] = s

    if y_row:
        avg = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        s = round(min(100, max(0, (avg - 70) / 30 * 100)))
        if "Asymmetrie" in str(y_row.get("asymmetrie", "")):
            s = max(0, s - 10)
        scores["Y-Balance"] = s

    if sprint_row:
        bew = str(sprint_row.get("bewertung_10m") or sprint_row.get("bewertung_30m") or "")
        s = _bew_to_score(bew)
        if s is not None:
            scores["Sprint"] = s

    if sprung_row:
        bew = str(sprung_row.get("bewertung_cmj") or "")
        s = _bew_to_score(bew)
        if s is not None:
            asym = sprung_row.get("cmj_asymmetrie") or 0
            if asym and float(asym) > 10:
                s = max(0, s - 10)
            scores["Sprungkraft"] = s

    if agil_row:
        bew = str(agil_row.get("bew_t_test") or agil_row.get("bew_505") or "")
        s = _bew_to_score(bew)
        if s is not None:
            asym = agil_row.get("asym_505") or 0
            if asym and float(asym) > 10:
                s = max(0, s - 8)
            scores["Agilitaet"] = s

    if aus_row:
        bew = str(aus_row.get("bewertung") or "")
        s = _bew_to_score(bew)
        if s is not None:
            vo2 = aus_row.get("vo2max") or 0
            if vo2 and float(vo2) >= 55:
                s = min(100, s + 5)
            scores["Ausdauer"] = s

    if spiro_row:
        vo2 = spiro_row.get("vo2_peak") or spiro_row.get("vo2_max")
        if vo2:
            scores["Spiro"] = round(min(100, max(0, (float(vo2) - 35) / 30 * 100)))

    return scores


# ─── Defizite ────────────────────────────────────────────────────────────────

def defizite_ermitteln(
    fms_row,
    y_row,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    anthro_row=None,
    spiro_row=None,
    geschlecht: str = "Männlich",
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
        defizit_text = str(sprint_row.get("defizite") or "")
        bew10  = str(sprint_row.get("bewertung_10m") or "")
        bew30  = str(sprint_row.get("bewertung_30m") or "")
        _d     = sprint_row.get("datum") or sprint_row.get("erstellt_am")
        if bew10 == "Verbesserungsbedarf":
            add("kritisch", "Lineargeschwindigkeit", "10-m-Sprintzeit unter Referenzwert — Beschleunigung verbessern.", "Sprint", _d)
        elif bew10 in ("Mittel (Breitensport)",):
            add("warnung", "Lineargeschwindigkeit", "10-m-Sprintzeit im mittleren Bereich.", "Sprint", _d)
        if bew30 == "Verbesserungsbedarf":
            add("kritisch", "Maximalgeschwindigkeit", "30-m-Sprintzeit unter Referenzwert — Maximalgeschwindigkeit verbessern.", "Sprint", _d)
        elif bew30 == "Mittel (Breitensport)":
            add("warnung", "Maximalgeschwindigkeit", "30-m-Sprintzeit im mittleren Bereich.", "Sprint", _d)
        if "Startexplosivität" in defizit_text:
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
        bmi   = anthro_row.get("bmi") or 0
        reife = str(anthro_row.get("reifestatus") or "").lower()
        _d    = anthro_row.get("datum") or anthro_row.get("erstellt_am")

        if float(bmi) >= 30:
            add("kritisch", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — Übergewicht kann Leistung und Gelenkbelastung erhöhen.", "Anthropometrie", _d)
        elif float(bmi) >= 25:
            add("warnung", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — leichtes Übergewicht, Körperfett reduzieren.", "Anthropometrie", _d)
        elif float(bmi) < 18.5 and float(bmi) > 0:
            add("warnung", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — Untergewicht, Ernährung prüfen.", "Anthropometrie", _d)
        if "vor phv" in reife or "wachstumsschub" in reife:
            add("warnung", "Wachstum / Belastungssteuerung",
                "Spieler befindet sich im oder vor dem Wachstumsschub — Belastung anpassen.", "Anthropometrie", _d)

    # ── Spiroergometrie / Stufentest ──────────────────────────────────────────
    if spiro_row:
        vo2    = spiro_row.get("vo2_peak") or spiro_row.get("vo2_max") or spiro_row.get("geschaetzte_vo2max")
        schw_v = spiro_row.get("schwelle_geschwindigkeit")
        _d     = spiro_row.get("datum") or spiro_row.get("erstellt_am")
        if vo2:
            v = float(vo2)
            if v < 45:
                add("kritisch", "Aerobe Kapazität",
                    f"VO₂peak {v:.1f} ml·kg⁻¹·min⁻¹ — aerobe Basis dringend stärken (Stufentest).", "Stufentest", _d)
            elif v < 50:
                add("warnung", "Aerobe Kapazität",
                    f"VO₂peak {v:.1f} ml·kg⁻¹·min⁻¹ — Ausdauertraining intensivieren.", "Stufentest", _d)
        if schw_v and float(schw_v) < 12:
            add("warnung", "Laktatschwelle",
                f"Schwellengeschwindigkeit {float(schw_v):.1f} km/h — Schwellentraining empfohlen.", "Stufentest", _d)

    return defizite


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
    """Combine schwerpunkt/deficit texts from all modules for training recommendations."""
    parts = []
    if fms_row and fms_row.get("schwerpunkt"):
        parts.append(str(fms_row["schwerpunkt"]))
    if y_row and y_row.get("schwerpunkt"):
        parts.append(str(y_row["schwerpunkt"]))
    if sprint_row:
        defizite = str(sprint_row.get("defizite") or "")
        if defizite:
            parts.append(defizite)
        bew10 = str(sprint_row.get("bewertung_10m") or "")
        bew30 = str(sprint_row.get("bewertung_30m") or "")
        if "Verbesserungsbedarf" in bew10 or "Mittel (Breitensport)" in bew10:
            parts.append("sprint beschleunigung")
        if "Verbesserungsbedarf" in bew30 or "Mittel (Breitensport)" in bew30:
            parts.append("sprint schnelligkeit")
    if sprung_row:
        bew = str(sprung_row.get("bewertung_cmj") or "")
        if "Verbesserungsbedarf" in bew:
            parts.append("explosivkraft sprung")
        asym = sprung_row.get("cmj_asymmetrie") or 0
        if asym and float(asym) > 10:
            parts.append("sprungasymmetrie knie")
    if agil_row:
        bew = str(agil_row.get("bew_t_test") or "")
        if "Verbesserungsbedarf" in bew:
            parts.append("agilität richtungswechsel")
        asym = agil_row.get("asym_505") or 0
        if asym and float(asym) > 10:
            parts.append("hüfte seitenasymmetrie")
    if aus_row:
        bew = str(aus_row.get("bewertung") or "")
        if bew == "Verbesserungsbedarf":
            parts.append("ausdauer intermittierend")
    if kraft_row:
        # Relative Kraft auswerten
        rel = kraft_row.get("relative_kraft_direkt") or kraft_row.get("relative_kraft_geschaetzt") or 0
        if rel and float(rel) < 1.0:
            parts.append("kraftdefizit bankdruecken rumpf")
        # Rumpfkraftausdauer
        ventral = kraft_row.get("ventral_sekunden") or 0
        if ventral and float(ventral) < 90:
            parts.append("rumpf stabilisation")
        lateral_asym = kraft_row.get("lateral_asymmetrie_pct") or 0
        if lateral_asym and float(lateral_asym) > 10:
            parts.append("hüfte seitenasymmetrie rumpf")
    if spiro_row:
        vo2 = spiro_row.get("vo2_peak") or spiro_row.get("vo2_max") or spiro_row.get("geschaetzte_vo2max")
        if vo2 and float(vo2) < 50:
            parts.append("ausdauer aerob grundlage")
        schw = spiro_row.get("schwelle_geschwindigkeit")
        if schw and float(schw) < 12:
            parts.append("ausdauer schwellentraining")
    return " ".join(parts)


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
    sw = schwerpunkt_sammeln(
        fms_row, y_row, sprint_row, sprung_row, agil_row, aus_row, spiro_row=spiro_row
    )
    return not sw.strip()
