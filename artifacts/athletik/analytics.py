"""
Athletic analytics engine — injury risk scoring, deficit detection,
and composite athleticism rating.
All functions operate on sqlite3.Row objects from the database layer.
"""


def risiko_score(fms_row, y_row) -> int:
    """
    Returns a numeric risk score 0–6.
    0–1 = low  |  2–3 = medium  |  4+ = high
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

    return score


def risiko_label(score: int) -> tuple[str, str]:
    """Returns (label, level) where level is 'hoch'/'mittel'/'gering'."""
    if score >= 4:
        return "HOHES RISIKO", "hoch"
    if score >= 2:
        return "MITTLERES RISIKO", "mittel"
    return "GERINGES RISIKO", "gering"


def athletik_score(fms_row, y_row) -> int:
    """
    Composite athleticism score 0–100.
    Deductions for low FMS, low Y-Balance composite, and asymmetries.
    """
    total = 100

    if fms_row:
        s = fms_row["score"]
        if s <= 12:
            total -= 25
        elif s <= 14:
            total -= 15
        elif s <= 17:
            total -= 5
        if "Asymmetrie" in str(fms_row["asymmetrie"]):
            total -= 10
    else:
        total -= 20  # no data penalty

    if y_row:
        avg = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        if avg < 85:
            total -= 20
        elif avg < 89:
            total -= 10
        elif avg < 94:
            total -= 5
        if "Asymmetrie" in str(y_row["asymmetrie"]):
            total -= 10
    else:
        total -= 15  # no data penalty

    return max(0, min(100, total))


def defizite_ermitteln(fms_row, y_row) -> list[dict]:
    """
    Returns a list of deficit dicts with keys:
      level  : 'kritisch' | 'warnung'
      bereich: str
      text   : str
    """
    defizite = []
    seen = set()

    def add(level, bereich, text):
        key = (bereich, text)
        if key not in seen:
            defizite.append({"level": level, "bereich": bereich, "text": text})
            seen.add(key)

    if fms_row:
        s = fms_row["score"]
        sw = str(fms_row["schwerpunkt"]).lower()

        if s <= 12:
            add("kritisch", "Ganzkörperstabilität", "FMS-Score unter 13 — hohes Verletzungsrisiko.")
        elif s <= 14:
            add("warnung", "Ganzkörperstabilität", "FMS-Score zeigt Verbesserungsbedarf.")

        if "hüft" in sw:
            add("kritisch", "Hüfte", "Defizite der Hüftstabilität erkannt.")
        if "rumpf" in sw or "core" in sw or "rotations" in sw:
            add("kritisch", "Core / Rumpf", "Rumpfstabilität eingeschränkt.")
        if "sprunggelenk" in sw:
            add("warnung", "Sprunggelenk", "Sprunggelenk-Mobilität / -Stabilität auffällig.")
        if "knie" in sw:
            add("warnung", "Knie", "Beinachsenkontrolle auffällig.")
        if "schulter" in sw:
            add("warnung", "Schulter", "Schulterbeweglichkeit eingeschränkt.")

    if y_row:
        asym = str(y_row["asymmetrie"]).lower()
        sw = str(y_row["schwerpunkt"]).lower()

        if "anterior" in asym:
            add("kritisch", "Sprunggelenk", "Anterior-Asymmetrie im Y-Balance Test.")
        if "posteromedial" in asym:
            add("kritisch", "Hüfte", "Posteromediale Asymmetrie — Beckenstabilität prüfen.")
        if "posterolateral" in asym:
            add("kritisch", "Hüfte", "Posterolaterale Asymmetrie — Knie-/Hüftkontrolle prüfen.")
        if "gluteus" in sw:
            add("warnung", "Hüfte", "Gluteus medius Training empfohlen.")
        if "becken" in sw:
            add("warnung", "Core / Rumpf", "Beckenstabilität verbessern.")

    return defizite


def schwerpunkt_sammeln(fms_row, y_row) -> str:
    """Combine FMS + Y-Balance schwerpunkt into one text for further parsing."""
    parts = []
    if fms_row and fms_row["schwerpunkt"]:
        parts.append(str(fms_row["schwerpunkt"]))
    if y_row and y_row["schwerpunkt"]:
        parts.append(str(y_row["schwerpunkt"]))
    return " ".join(parts)
