"""
Y-Balance Test — composite score and asymmetry analysis.
Standard thresholds based on sports science literature:
  - Composite score < 89 % → elevated injury risk in athletes
  - Side-to-side difference ≥ 4 cm → clinically significant asymmetry
"""

from dataclasses import dataclass, field
from age_norms import yb_schwellenwert as _yb_sw
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

    alter: float | None = None  # für altersbasierte Schwellenwerte

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
    def hat_relevante_asymmetrie(self) -> bool:
        """Ob mindestens eine bestehende numerische Seitendifferenz auffällig ist."""
        return bool(self.asymmetrien)

    @property
    def asymmetrie_text(self) -> str:
        a = self.asymmetrien
        if not a:
            return "Keine relevante Asymmetrie"
        return "Asymmetrie: " + ", ".join(a)

    @property
    def risiko_level(self) -> str:
        """Overall injury risk based on age-adjusted composite scores and asymmetries."""
        schwelle = _yb_sw(self.alter)
        low_score = self.composite_r < schwelle or self.composite_l < schwelle
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
        _sw_th = _yb_sw(self.alter)
        if self.composite_r < _sw_th or self.composite_l < _sw_th:
            return "Allgemeine Balance + Beinachsenstabilität"
        return "Keine relevante Asymmetrie erkannt"

    def as_db_tuple(self):
        return (
            self.diff_anterior, self.diff_posteromedial, self.diff_posterolateral,
            self.composite_r, self.composite_l,
            self.asymmetrie_text, self.schwerpunkt,
        )


def y_balance_aus_row(row) -> YBalanceResult:
    """Erstellt YBalanceResult aus einer DB-Zeile.

    Verwendet die gespeicherten Composite-Werte direkt statt sie mit
    beinlaenge=1 falsch neu zu berechnen (Bug-Fix: beinlaenge=1 ergäbe
    composite = Summe/3 × 100, nicht den echten %-Wert der Beinlänge).
    """
    obj = YBalanceResult(
        anterior_r=row["anterior_rechts"] or 0.0,
        anterior_l=row["anterior_links"] or 0.0,
        posteromedial_r=row["posteromedial_rechts"] or 0.0,
        posteromedial_l=row["posteromedial_links"] or 0.0,
        posterolateral_r=row["posterolateral_rechts"] or 0.0,
        posterolateral_l=row["posterolateral_links"] or 0.0,
        beinlaenge_r=1,   # Dummy für __post_init__; wird unten überschrieben
        beinlaenge_l=1,
    )
    # Überschreibe mit den in der DB gespeicherten, korrekt berechneten Werten
    obj.composite_r = float(row["composite_rechts"] or 0.0)
    obj.composite_l = float(row["composite_links"] or 0.0)
    if row.get("diff_anterior") is not None:
        obj.diff_anterior       = float(row["diff_anterior"]       or 0.0)
        obj.diff_posteromedial  = float(row["diff_posteromedial"]  or 0.0)
        obj.diff_posterolateral = float(row["diff_posterolateral"] or 0.0)
    return obj


def y_balance_hat_relevante_asymmetrie(row) -> bool:
    """Bewertet gespeicherte Y-Balance-Daten über ihre numerischen Differenzen.

    Der Anzeigetext ``Keine relevante Asymmetrie`` ist bewusst kein
    Entscheidungsmerkmal: Er enthält zwar das Wort „Asymmetrie“, beschreibt aber
    gerade einen unauffälligen Befund. Die fachliche Schwelle bleibt vollständig
    in ``YBalanceResult.asymmetrien`` zentral definiert.
    """
    return bool(row) and y_balance_aus_row(row).hat_relevante_asymmetrie
