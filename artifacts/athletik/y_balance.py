"""
Y-Balance Test — composite score and asymmetry analysis.
Standard thresholds based on sports science literature:
  - Composite score < 89 % → elevated injury risk in athletes
  - Side-to-side difference ≥ 4 cm → clinically significant asymmetry
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class YBalanceResult:
    anterior_r: float
    anterior_l: float
    posteromedial_r: float
    posteromedial_l: float
    posterolateral_r: float
    posterolateral_l: float
    beinlaenge_r: float
    beinlaenge_l: float

    # Computed on post_init
    diff_anterior: float = field(init=False)
    diff_posteromedial: float = field(init=False)
    diff_posterolateral: float = field(init=False)
    composite_r: float = field(init=False)
    composite_l: float = field(init=False)

    def __post_init__(self):
        self.diff_anterior = round(abs(self.anterior_r - self.anterior_l), 1)
        self.diff_posteromedial = round(abs(self.posteromedial_r - self.posteromedial_l), 1)
        self.diff_posterolateral = round(abs(self.posterolateral_r - self.posterolateral_l), 1)

        self.composite_r = round(
            (self.anterior_r + self.posteromedial_r + self.posterolateral_r)
            / (3 * self.beinlaenge_r) * 100, 1
        ) if self.beinlaenge_r > 0 else 0.0

        self.composite_l = round(
            (self.anterior_l + self.posteromedial_l + self.posterolateral_l)
            / (3 * self.beinlaenge_l) * 100, 1
        ) if self.beinlaenge_l > 0 else 0.0

    @property
    def asymmetrien(self) -> List[str]:
        found = []
        if self.diff_anterior >= 4:
            found.append("Anterior")
        if self.diff_posteromedial >= 4:
            found.append("Posteromedial")
        if self.diff_posterolateral >= 4:
            found.append("Posterolateral")
        return found

    @property
    def asymmetrie_text(self) -> str:
        a = self.asymmetrien
        if not a:
            return "Keine relevante Asymmetrie"
        return "Asymmetrie: " + ", ".join(a)

    @property
    def risiko_level(self) -> str:
        """Overall injury risk based on composite scores and asymmetries."""
        low_score = self.composite_r < 89 or self.composite_l < 89
        has_asym = len(self.asymmetrien) > 0
        if low_score and has_asym:
            return "hoch"
        if low_score or has_asym:
            return "mittel"
        return "gering"

    @property
    def schwerpunkt(self) -> str:
        if self.diff_posteromedial >= 4:
            return "Hüftstabilität + Gluteus medius + Beckenstabilität"
        if self.diff_posterolateral >= 4:
            return "Knie Kontrolle + seitliche Stabilität"
        if self.diff_anterior >= 4:
            return "Sprunggelenk Mobilität + Knie-Vorschub verbessern"
        if self.composite_r < 89 or self.composite_l < 89:
            return "Allgemeine Balance + Beinachsenstabilität"
        return "Keine Auffälligkeit — leistungsorientiertes Training möglich"

    def as_db_tuple(self):
        return (
            self.diff_anterior, self.diff_posteromedial, self.diff_posterolateral,
            self.composite_r, self.composite_l,
            self.asymmetrie_text, self.schwerpunkt,
        )


def y_balance_aus_row(row) -> YBalanceResult:
    return YBalanceResult(
        anterior_r=row["anterior_rechts"],
        anterior_l=row["anterior_links"],
        posteromedial_r=row["posteromedial_rechts"],
        posteromedial_l=row["posteromedial_links"],
        posterolateral_r=row["posterolateral_rechts"],
        posterolateral_l=row["posterolateral_links"],
        beinlaenge_r=1,  # already normalised in DB
        beinlaenge_l=1,
    )
