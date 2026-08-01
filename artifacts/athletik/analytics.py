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
            score += 1

    if y_row:
        comp_r = y_row["composite_rechts"]
        comp_l = y_row["composite_links"]
        avg = (comp_r + comp_l) / 2
        if avg < 85:
            score += 2
        elif avg < 89:
            score += 1
        if "Asymmetrie" in str(y_row["asymmetrie"]):
            score += 1

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
) -> list[dict]:
    """
    Returns a list of deficit dicts with keys:
      level  : 'kritisch' | 'warnung'
      bereich: str
      modul  : str   (source module label)
      text   : str
    """
    defizite = []
    seen: set = set()

    def add(level, bereich, text, modul=""):
        key = (bereich, text)
        if key not in seen:
            defizite.append({"level": level, "bereich": bereich, "text": text, "modul": modul})
            seen.add(key)

    # ── FMS ──────────────────────────────────────────────────────────────────
    if fms_row:
        s = fms_row["score"]
        sw = str(fms_row["schwerpunkt"]).lower()

        if s <= 12:
            add("kritisch", "Ganzkörperstabilität", "FMS-Score unter 13 — deutlicher Trainingsbedarf.", "FMS")
        elif s <= 14:
            add("warnung", "Ganzkörperstabilität", "FMS-Score zeigt Verbesserungsbedarf.", "FMS")

        if "hüft" in sw:
            add("kritisch", "Hüfte", "Defizite der Hüftstabilität erkannt.", "FMS")
        if "rumpf" in sw or "core" in sw or "rotations" in sw:
            add("kritisch", "Core / Rumpf", "Rumpfstabilität eingeschränkt.", "FMS")
        if "sprunggelenk" in sw:
            add("warnung", "Sprunggelenk", "Sprunggelenk-Mobilität / -Stabilität auffällig.", "FMS")
        if "knie" in sw:
            add("warnung", "Knie", "Beinachsenkontrolle auffällig.", "FMS")
        if "schulter" in sw:
            add("warnung", "Schulter", "Schulterbeweglichkeit eingeschränkt.", "FMS")

    # ── Y-Balance ────────────────────────────────────────────────────────────
    if y_row:
        asym = str(y_row["asymmetrie"]).lower()
        sw = str(y_row["schwerpunkt"]).lower()

        if "anterior" in asym:
            add("kritisch", "Sprunggelenk", "Anterior-Asymmetrie im Y-Balance Test.", "Y-Balance")
        if "posteromedial" in asym:
            add("kritisch", "Hüfte", "Posteromediale Asymmetrie — Beckenstabilität prüfen.", "Y-Balance")
        if "posterolateral" in asym:
            add("kritisch", "Hüfte", "Posterolaterale Asymmetrie — Knie-/Hüftkontrolle prüfen.", "Y-Balance")
        if "gluteus" in sw:
            add("warnung", "Hüfte", "Gluteus medius Training empfohlen.", "Y-Balance")
        if "becken" in sw:
            add("warnung", "Core / Rumpf", "Beckenstabilität verbessern.", "Y-Balance")

    # ── Sprint ────────────────────────────────────────────────────────────────
    if sprint_row:
        defizit_text = str(sprint_row.get("defizite") or "")
        bew10  = str(sprint_row.get("bewertung_10m") or "")
        bew30  = str(sprint_row.get("bewertung_30m") or "")
        if bew10 == "Verbesserungsbedarf":
            add("kritisch", "Lineargeschwindigkeit", "10-m-Sprintzeit unter Referenzwert — Beschleunigung verbessern.", "Sprint")
        elif bew10 in ("Mittel (Breitensport)",):
            add("warnung", "Lineargeschwindigkeit", "10-m-Sprintzeit im mittleren Bereich.", "Sprint")
        if bew30 == "Verbesserungsbedarf":
            add("kritisch", "Maximalgeschwindigkeit", "30-m-Sprintzeit unter Referenzwert — Maximalgeschwindigkeit verbessern.", "Sprint")
        elif bew30 == "Mittel (Breitensport)":
            add("warnung", "Maximalgeschwindigkeit", "30-m-Sprintzeit im mittleren Bereich.", "Sprint")
        if "Startexplosivität" in defizit_text:
            add("warnung", "Startexplosivität", "Beschleunigungsindex erhöht — Reaktivkraft fördern.", "Sprint")

    # ── Sprung ────────────────────────────────────────────────────────────────
    if sprung_row:
        bew_cmj = str(sprung_row.get("bewertung_cmj") or "")
        asym    = sprung_row.get("cmj_asymmetrie") or 0
        rsi     = sprung_row.get("rsi") or 0
        defizit_text = str(sprung_row.get("defizite") or "")

        if bew_cmj == "Verbesserungsbedarf":
            add("kritisch", "Explosivkraft", "CMJ-Sprunghöhe deutlich unter Normwert.", "Sprung")
        elif bew_cmj == "Mittel (Breitensport)":
            add("warnung", "Explosivkraft", "CMJ-Sprunghöhe im mittleren Bereich.", "Sprung")
        if asym and float(asym) > 10:
            add("kritisch", "Sprungasymmetrie",
                f"Einbeinige Sprungasymmetrie {float(asym):.1f} % — Asymmetrie auffällig, Trainingsschwerpunkt prüfen.", "Sprung")
        if rsi and float(rsi) < 1.5:
            add("warnung", "Reaktivkraft", f"RSI = {float(rsi):.2f} — Drop-Jump-Reaktivkraft verbessern.", "Sprung")
        if "Horizontalexplosivkraft" in defizit_text:
            add("warnung", "Horizontalexplosivkraft", "Standweitsprung unter Normwert.", "Sprung")

    # ── Agilität ─────────────────────────────────────────────────────────────
    if agil_row:
        bew_t   = str(agil_row.get("bew_t_test") or "")
        bew_505 = str(agil_row.get("bew_505") or "")
        bew_ill = str(agil_row.get("bew_illinois") or "")
        asym505 = agil_row.get("asym_505") or 0

        if bew_t == "Verbesserungsbedarf":
            add("kritisch", "Mehrdirektionale Agilität", "T-Test Zeit unter Referenzwert — Richtungswechselkraft verbessern.", "Agilität")
        elif bew_t == "Mittel (Breitensport)":
            add("warnung", "Mehrdirektionale Agilität", "T-Test im mittleren Bereich.", "Agilität")
        if bew_505 == "Verbesserungsbedarf":
            add("kritisch", "Richtungswechsel", "505-Test Zeit unter Referenzwert.", "Agilität")
        if bew_ill == "Verbesserungsbedarf":
            add("warnung", "Gesamtagilität", "Illinois-Test unter Referenzwert — Gesamtagilität verbessern.", "Agilität")
        if asym505 and float(asym505) > 10:
            add("kritisch", "Richtungswechsel-Asymmetrie",
                f"505-Test Seitenasymmetrie {float(asym505):.1f} % — Asymmetrie auffällig, Richtungswechseltraining anpassen.", "Agilität")

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    if aus_row:
        bew    = str(aus_row.get("bewertung") or "")
        vo2max = aus_row.get("vo2max") or 0

        if bew == "Verbesserungsbedarf":
            add("kritisch", "Intermittierende Ausdauer",
                "Yo-Yo IR-Ergebnis unter Normwert — Ausdauerkapazität verbessern.", "Ausdauer")
        elif bew == "Mittel":
            add("warnung", "Intermittierende Ausdauer",
                "Yo-Yo IR-Ergebnis im mittleren Bereich.", "Ausdauer")
        if vo2max and float(vo2max) < 45:
            add("kritisch", "Aerobe Kapazität",
                f"VO₂max-Schätzung {float(vo2max):.1f} ml/kg/min — aerobe Basis stärken.", "Ausdauer")
        elif vo2max and float(vo2max) < 50:
            add("warnung", "Aerobe Kapazität",
                f"VO₂max-Schätzung {float(vo2max):.1f} ml/kg/min — Ausdauertraining intensivieren.", "Ausdauer")

    # ── Anthropometrie ────────────────────────────────────────────────────────
    if anthro_row:
        bmi    = anthro_row.get("bmi") or 0
        bmi_k  = str(anthro_row.get("bmi_kategorie") or "").lower()
        reife  = str(anthro_row.get("reifestatus") or "").lower()

        if float(bmi) >= 30:
            add("kritisch", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — Übergewicht kann Leistung und Gelenkbelastung erhöhen.", "Anthropometrie")
        elif float(bmi) >= 25:
            add("warnung", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — leichtes Übergewicht, Körperfett reduzieren.", "Anthropometrie")
        elif float(bmi) < 18.5 and float(bmi) > 0:
            add("warnung", "Körperzusammensetzung",
                f"BMI {float(bmi):.1f} — Untergewicht, Ernährung prüfen.", "Anthropometrie")
        if "vor phv" in reife or "wachstumsschub" in reife:
            add("warnung", "Wachstum / Belastungssteuerung",
                "Spieler befindet sich im oder vor dem Wachstumsschub — Belastung anpassen.", "Anthropometrie")

    # ── Spiroergometrie / Stufentest ──────────────────────────────────────────
    if spiro_row:
        vo2 = spiro_row.get("vo2_peak") or spiro_row.get("vo2_max") or spiro_row.get("geschaetzte_vo2max")
        schw_v = spiro_row.get("schwelle_geschwindigkeit")
        if vo2:
            v = float(vo2)
            if v < 45:
                add("kritisch", "Aerobe Kapazität (Spiro)",
                    f"VO₂peak {v:.1f} ml·kg⁻¹·min⁻¹ — aerobe Basis dringend stärken (Spiroergometrie).", "Stufentest")
            elif v < 50:
                add("warnung", "Aerobe Kapazität (Spiro)",
                    f"VO₂peak {v:.1f} ml·kg⁻¹·min⁻¹ — Ausdauertraining intensivieren.", "Stufentest")
        if schw_v and float(schw_v) < 12:
            add("warnung", "Laktatschwelle",
                f"Schwellengeschwindigkeit {float(schw_v):.1f} km/h — Schwellentraining empfohlen.", "Stufentest")

    return defizite


# ─── Schwerpunkt-Text ─────────────────────────────────────────────────────────

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
        bew = str(sprint_row.get("bewertung_10m") or "")
        if "Verbesserungsbedarf" in bew:
            parts.append("sprint beschleunigung")
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
