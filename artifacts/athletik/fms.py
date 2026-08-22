"""
Functional Movement Screen (FMS) — scoring and analysis logic.
Max score: 21 points (7 patterns × 3 points each).
"""

from dataclasses import dataclass
from typing import List, Tuple


from age_norms import fms_bewertung_alter as _fms_bw_alter


def _row_wert(row, key, default=None):
    """Liest Dict-/sqlite-Zeilen robust, ohne Anzeige-Text zu interpretieren."""
    if not row:
        return default
    try:
        return row.get(key, default)
    except AttributeError:
        try:
            return row[key]
        except (KeyError, IndexError):
            return default


def fms_hat_relevante_asymmetrie(row) -> bool:
    """Ermittelt FMS-Seitenunterschiede strukturiert und legacy-sicher.

    ``Keine Asymmetrie`` ist eine positive Anzeige und darf nicht aufgrund
    des enthaltenen Wortes als auffällig gewertet werden. Wenn die
    Einzelwerte vorliegen, haben sie Vorrang vor dem historischen Text.
    """
    if not row:
        return False

    paare = (
        ("hurdle_links", "hurdle_rechts"),
        ("inline_links", "inline_rechts"),
        ("shoulder_links", "shoulder_rechts"),
        ("aslr_links", "aslr_rechts"),
        ("rotary_links", "rotary_rechts"),
    )
    hat_strukturierte_werte = False
    for links_key, rechts_key in paare:
        links = _row_wert(row, links_key)
        rechts = _row_wert(row, rechts_key)
        if links is None or rechts is None:
            continue
        hat_strukturierte_werte = True
        if links != rechts:
            return True

    if hat_strukturierte_werte:
        return False

    text = str(_row_wert(row, "asymmetrie", "") or "").strip().lower()
    if not text or text.startswith("keine"):
        return False
    return "asymmetrie" in text


@dataclass
class FMSResult:
    deep_squat: int
    hurdle_l: int
    hurdle_r: int
    inline_l: int
    inline_r: int
    shoulder_l: int
    shoulder_r: int
    aslr_l: int
    aslr_r: int
    trunk: int
    rotary_l: int
    rotary_r: int

    alter: float | None = None

    @property
    def score(self) -> int:
        """FMS composite score (uses min of bilateral pairs)."""
        return (
            self.deep_squat
            + min(self.hurdle_l, self.hurdle_r)
            + min(self.inline_l, self.inline_r)
            + min(self.shoulder_l, self.shoulder_r)
            + min(self.aslr_l, self.aslr_r)
            + self.trunk
            + min(self.rotary_l, self.rotary_r)
        )

    @property
    def asymmetrie(self) -> str:
        """Detect and describe bilateral asymmetries."""
        pairs: List[Tuple[str, int, int]] = [
            ("Hurdle Step", self.hurdle_l, self.hurdle_r),
            ("Inline Lunge", self.inline_l, self.inline_r),
            ("Shoulder Mobility", self.shoulder_l, self.shoulder_r),
            ("ASLR", self.aslr_l, self.aslr_r),
            ("Rotary Stability", self.rotary_l, self.rotary_r),
        ]
        asym = [name for name, l, r in pairs if l != r]
        if not asym:
            return "Keine Asymmetrie"
        if len(asym) == 1:
            return f"1 Asymmetrie ({asym[0]})"
        return f"{len(asym)} Asymmetrien ({', '.join(asym)})"

    @property
    def bewertung(self) -> str:
        return _fms_bw_alter(self.score, self.alter)

    @property
    def bewertung_kurz(self) -> str:
        """Kurze Erläuterung der Bewertungsstufe für Trainer und Eltern."""
        s = self.score
        if s >= 18:
            return "Sehr gute Bewegungsqualität — kein Handlungsbedarf, Niveau halten."
        if s >= 15:
            return "Solide Bewegungsbasis — gezielte Optimierung einzelner Muster empfohlen."
        if s >= 13:
            return "Einzelne Schwächen erkannt — regelmäßig beobachten und im Training ansprechen."
        return "Erhebliche Bewegungsdefizite — sofortiger Trainingsfokus auf Korrektur notwendig, erhöhtes Verletzungsrisiko."

    @property
    def risiko_level(self) -> str:
        if self.score <= 12:
            return "hoch"
        if self.score <= 14:
            return "mittel"
        return "gering"

    @property
    def schwerpunkt(self) -> str:
        """Primary training focus derived from the lowest-scoring patterns."""
        issues = []

        if self.deep_squat <= 1:
            issues.append("Hüftkette + Sprunggelenk Mobilität")
        if min(self.hurdle_l, self.hurdle_r) <= 1:
            issues.append("Hüftstabilität + Beinachsenkontrolle")
        if min(self.inline_l, self.inline_r) <= 1:
            issues.append("Knie + Sprunggelenk Stabilität")
        if min(self.shoulder_l, self.shoulder_r) <= 1:
            issues.append("Schulter Mobilität")
        if min(self.aslr_l, self.aslr_r) <= 1:
            issues.append("Hüftmobilität + Core Stabilität")
        if self.trunk <= 1:
            issues.append("Rumpfstabilität")
        if min(self.rotary_l, self.rotary_r) <= 1:
            issues.append("Rotationsstabilität Core")

        if self.score <= 12:
            if not issues:
                issues.append("Ganzkörper Stabilitätstraining")
        elif self.asymmetrie != "Keine Asymmetrie":
            if not issues:
                issues.append("Seitenasymmetrien korrigieren")

        if not issues:
            return "Kein akuter Handlungsbedarf"
        return " | ".join(issues)

    @property
    def pattern_scores(self) -> dict:
        """Dict mapping pattern name to score used in the composite."""
        return {
            "Deep Squat": self.deep_squat,
            "Hurdle Step": min(self.hurdle_l, self.hurdle_r),
            "Inline Lunge": min(self.inline_l, self.inline_r),
            "Shoulder Mobility": min(self.shoulder_l, self.shoulder_r),
            "ASLR": min(self.aslr_l, self.aslr_r),
            "Trunk Stability": self.trunk,
            "Rotary Stability": min(self.rotary_l, self.rotary_r),
        }


def fms_aus_row(row) -> FMSResult:
    """Reconstruct an FMSResult from a database row (sqlite3.Row)."""
    return FMSResult(
        deep_squat=row["deep_squat"],
        hurdle_l=row["hurdle_links"],
        hurdle_r=row["hurdle_rechts"],
        inline_l=row["inline_links"],
        inline_r=row["inline_rechts"],
        shoulder_l=row["shoulder_links"],
        shoulder_r=row["shoulder_rechts"],
        aslr_l=row["aslr_links"],
        aslr_r=row["aslr_rechts"],
        trunk=row["trunk"],
        rotary_l=row["rotary_links"],
        rotary_r=row["rotary_rechts"],
    )


def fms_bewertung_kurz(score: int | None) -> str:
    """Kurze Beurteilung aus dem FMS-Score — nutzbar mit DB-Zeilen ohne FMS-Objekt."""
    if score is None:
        return "—"
    s = int(score)
    if s >= 18:
        return "Sehr gute Bewegungsqualität — kein Handlungsbedarf, Niveau halten."
    if s >= 15:
        return "Solide Bewegungsbasis — gezielte Optimierung einzelner Muster empfohlen."
    if s >= 13:
        return "Einzelne Schwächen erkannt — regelmäßig beobachten und im Training ansprechen."
    return "Erhebliche Bewegungsdefizite — Trainingsfokus auf Korrektur und Verlaufskontrolle."
