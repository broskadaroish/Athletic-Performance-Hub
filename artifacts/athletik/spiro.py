"""
spiro.py — Spiroergometrie-Stufentest Berechnungen & Auswertungslogik.

WICHTIG: Diese App führt keine medizinische Spiroergometrie durch.
Sie dient zur strukturierten Eingabe, Auswertung und Verlaufskontrolle
von Ergebnissen fachgerecht durchgeführter Tests. Keine Diagnose, keine
Sportfreigabe, kein Ersatz für einen qualifizierten Diagnostiker.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ─── Gerätetype ───────────────────────────────────────────────────────────────

GERAETEARTEN = [
    "Laufband",
    "Laufbasierter Feldtest",
    "Fahrradergometer (nicht fußballspezifisch)",
]

# Standard Bruce-Protokoll: Geschwindigkeit in km/h, Steigung in Prozent,
# Dauer in Sekunden.
# Es dient ausschließlich zur Plausibilisierung eines als Bruce gespeicherten Tests.
BRUCE_STUFEN = (
    (2.7, 10.0, 180), (4.0, 12.0, 180), (5.5, 14.0, 180),
    (6.8, 16.0, 180), (8.0, 18.0, 180), (8.8, 20.0, 180),
    (9.7, 22.0, 180), (10.5, 24.0, 180), (11.3, 26.0, 180),
    (12.1, 28.0, 180),
)


# ─── Wissenschaftliche Referenzbewertung V2 ───────────────────────────────────

def spiro_vo2_messwert(spiro_row: dict | None) -> dict:
    """Kennzeichnet den verfügbaren VO₂-Wert ohne direkte und geschätzte Werte zu vermischen."""
    row = spiro_row or {}
    for feld, label in (
        ("vo2_peak", "VO₂peak (direkt gemessen)"),
        ("vo2_max", "VO₂max (direkt gemessen)"),
        ("geschaetzte_vo2max", "VO₂max (geschätzt)"),
    ):
        wert = row.get(feld)
        if wert is not None and float(wert) > 0:
            return {
                "wert": float(wert),
                "feld": feld,
                "label": label,
                "direkt_gemessen": feld != "geschaetzte_vo2max",
            }
    return {"wert": None, "feld": None, "label": None, "direkt_gemessen": False}


def _bruce_testdauer_minuten(stufen: list[dict] | None) -> float | None:
    """Liefert nur die vollständig dokumentierte Belastungsdauer in Minuten."""
    if not stufen:
        return None
    dauern = []
    for stufe in stufen:
        if stufe.get("stufe_vollstaendig") in (False, 0):
            return None
        dauer = stufe.get("dauer_sekunden")
        if dauer is None or float(dauer) <= 0:
            return None
        dauern.append(float(dauer))
    return sum(dauern) / 60 if dauern else None


def _bruce_rer_max(stufen: list[dict] | None) -> float | None:
    if not stufen:
        return None
    werte = [float(s["rer"]) for s in stufen if s.get("rer") is not None]
    return max(werte) if werte else None


def ist_dokumentiertes_bruce_protokoll(spiro_row: dict | None, stufen: list[dict] | None) -> bool:
    """Prüft, ob die gespeicherten Protokoll- und Stufendaten dem Bruce-Test entsprechen."""
    row = spiro_row or {}
    if (
        not row.get("protokoll_id")
        or str(row.get("geraeteart") or "").strip() != "Laufband"
        or str(row.get("protokoll_geraeteart") or "").strip() != "Laufband"
        or "bruce" not in str(row.get("protokoll_name") or "").lower()
        or not stufen
        or len(stufen) > len(BRUCE_STUFEN)
    ):
        return False
    for index, stufe in enumerate(stufen, start=1):
        if stufe.get("stufennummer") != index:
            return False
        speed = stufe.get("geschwindigkeit_kmh")
        grade = stufe.get("steigung_prozent")
        dauer = stufe.get("dauer_sekunden")
        if speed is None or grade is None or dauer is None:
            return False
        expected_speed, expected_grade, expected_dauer = BRUCE_STUFEN[index - 1]
        if (
            abs(float(speed) - expected_speed) > 0.15
            or abs(float(grade) - expected_grade) > 0.5
            or abs(float(dauer) - expected_dauer) > 1
        ):
            return False
    return True


def spiro_bewertung_v2(
    spiro_row: dict | None,
    *,
    alter_testtag: float | None = None,
    geschlecht: str = "Männlich",
    stufen: list[dict] | None = None,
) -> dict:
    """Erstellt eine protokollspezifische, nicht diagnostische Spirobewertung.

    Der einzige automatisch berechnete Referenzvergleich basiert auf Griffith
    et al. (Am J Cardiol 2024, PMID 38042265) und gilt ausschließlich für
    dokumentierte Bruce-Laufbandtests bei 6- bis 18-Jährigen. Es werden bewusst
    keine Kategorien, Perzentile oder Defizite aus einem Abweichungswert
    abgeleitet. Cycle- und Feld-/Laktat-Tests bleiben neutral, solange ihre
    vollständigen Eingangsdaten bzw. reproduzierbaren Gleichungen nicht vorliegen.
    """
    row = spiro_row or {}
    messwert = spiro_vo2_messwert(row)
    geraet = str(row.get("geraeteart") or "").strip()
    ist_bruce = ist_dokumentiertes_bruce_protokoll(row, stufen)

    def neutral(begruendung: str) -> dict:
        if messwert["wert"] is not None:
            prefix = f"{messwert['label']}: {messwert['wert']:.1f} ml·kg⁻¹·min⁻¹"
            text = f"{prefix} — keine belastbare Referenzbewertung verfügbar ({begruendung})."
        elif row.get("schwelle_geschwindigkeit") is not None:
            text = (
                f"Schwellengeschwindigkeit: {float(row['schwelle_geschwindigkeit']):.1f} km/h "
                f"— keine belastbare Referenzbewertung verfügbar ({begruendung})."
            )
        else:
            text = f"Keine belastbare Referenzbewertung verfügbar ({begruendung})."
        return {
            "status": "keine_belastbare_referenz",
            "text": text,
            "messwert": messwert,
            "referenzwert": None,
            "abweichung": None,
            "quelle": None,
        }

    if not ist_bruce:
        if "fahrrad" in geraet.lower():
            return neutral(
                "für das Cycle-Modell fehlen die vollständig erforderlichen "
                "testtagsbezogenen Eingangsdaten"
            )
        return neutral("kein vollständig dokumentiertes Bruce-Laufbandprotokoll")
    if not messwert["direkt_gemessen"]:
        return neutral("eine VO₂-Schätzung darf nicht als direkter Bruce-Messwert bewertet werden")
    if alter_testtag is None or not 6 <= float(alter_testtag) <= 18:
        return neutral("Bruce-Referenz gilt nur für das dokumentierte Alter von 6 bis 18 Jahren")

    gewicht = row.get("koerpergewicht")
    dauer_min = _bruce_testdauer_minuten(stufen)
    rer_max = _bruce_rer_max(stufen)
    if gewicht is None or float(gewicht) <= 0:
        return neutral("Körpergewicht am Testtag fehlt")
    if dauer_min is None:
        return neutral("vollständige Stufendauer fehlt")
    if rer_max is None or rer_max < 1.00:
        return neutral("dokumentierter maximaler RER von mindestens 1,00 fehlt")

    weiblich = "w" in geschlecht.lower() or "f" in geschlecht.lower()
    referenz = (
        16.411
        + 3.423 * dauer_min
        - 5.145 * (1 if weiblich else 0)
        - 0.121 * float(gewicht)
        + 0.179 * float(alter_testtag)
    )
    abweichung = messwert["wert"] - referenz
    return {
        "status": "bruce_referenzvergleich",
        "text": (
            f"{messwert['label']}: {messwert['wert']:.1f} ml·kg⁻¹·min⁻¹ — "
            f"Bruce-Referenzwert nach Griffith et al.: {referenz:.1f} ml·kg⁻¹·min⁻¹ "
            f"(Δ {abweichung:+.1f}). Kein automatisches Trainingsdefizit."
        ),
        "messwert": messwert,
        "referenzwert": round(referenz, 1),
        "abweichung": round(abweichung, 1),
        "quelle": "Griffith et al., Am J Cardiol 2024, PMID 38042265",
    }


SCHWELLENMETHODEN = [
    "Fixer Wert 2 mmol/l",
    "Fixer Wert 4 mmol/l",
    "Visuelle Schwelle",
    "Dmax",
    "Modifizierter Dmax",
    "Individuelle anaerobe Schwelle",
    "Ventilatorische Schwelle VT1",
    "Ventilatorische Schwelle VT2",
]


# ─── Interpolation ────────────────────────────────────────────────────────────

def interpoliere_bei_laktat(
    stufen: list[dict],
    laktat_ziel: float,
    x_feld: str = "geschwindigkeit_kmh",
) -> Optional[dict]:
    """Lineare Interpolation der Laufleistung bei einem Ziel-Laktatwert.

    Gibt None zurück, wenn der Zielwert außerhalb des gemessenen Bereichs liegt
    (keine Extrapolation außerhalb der Messwerte).

    Returns dict mit Schlüsseln:
        x_wert (float): interpolierter Wert der X-Achse
        interpoliert (bool): immer True
        methode (str): Beschreibung
    """
    gueltig = [
        s for s in stufen
        if s.get("laktat_mmol_l") is not None
        and s.get(x_feld) is not None
        and s.get("blutprobe_gueltig", True) is not False
    ]
    gueltig.sort(key=lambda s: s[x_feld])

    if len(gueltig) < 2:
        return None

    laktate = [s["laktat_mmol_l"] for s in gueltig]
    xs      = [s[x_feld]           for s in gueltig]

    # Außerhalb des gemessenen Bereichs → keine Extrapolation
    if laktat_ziel < min(laktate) or laktat_ziel > max(laktate):
        return None

    for i in range(len(gueltig) - 1):
        l1, l2 = laktate[i], laktate[i + 1]
        x1, x2 = xs[i],      xs[i + 1]
        lo, hi = min(l1, l2), max(l1, l2)
        if lo <= laktat_ziel <= hi:
            if l2 == l1:
                return {"x_wert": round(x1, 2), "interpoliert": True,
                        "methode": f"Interpoliert bei {laktat_ziel} mmol/l"}
            t = (laktat_ziel - l1) / (l2 - l1)
            x_interp = x1 + t * (x2 - x1)
            return {
                "x_wert": round(x_interp, 2),
                "interpoliert": True,
                "methode": f"Lineare Interpolation bei {laktat_ziel:.1f} mmol/l",
            }
    return None


def interpoliere_bei_hf(
    stufen: list[dict],
    hf_ziel: float,
    x_feld: str = "geschwindigkeit_kmh",
) -> Optional[dict]:
    """Lineare Interpolation der Laufleistung bei einer Ziel-Herzfrequenz."""
    gueltig = [
        s for s in stufen
        if s.get("herzfrequenz_bpm") is not None and s.get(x_feld) is not None
    ]
    gueltig.sort(key=lambda s: s[x_feld])
    if len(gueltig) < 2:
        return None

    hfs = [s["herzfrequenz_bpm"] for s in gueltig]
    xs  = [s[x_feld]             for s in gueltig]

    if hf_ziel < min(hfs) or hf_ziel > max(hfs):
        return None

    for i in range(len(gueltig) - 1):
        h1, h2 = hfs[i], hfs[i + 1]
        x1, x2 = xs[i],  xs[i + 1]
        lo, hi = min(h1, h2), max(h1, h2)
        if lo <= hf_ziel <= hi:
            if h2 == h1:
                return {"x_wert": round(x1, 2), "interpoliert": True}
            t = (hf_ziel - h1) / (h2 - h1)
            return {"x_wert": round(x1 + t * (x2 - x1), 2), "interpoliert": True}
    return None


# ─── Kurvenverschiebung ───────────────────────────────────────────────────────

def kurvenverschiebung_bewerten(
    v_alt: Optional[float],
    v_neu: Optional[float],
    laktat_ziel: float,
) -> tuple[str, str]:
    """Neutrale Bewertung einer Kurvenverschiebung.

    Returns: (bewertungsstufe, text)
    Bewertungsstufen: 'wahrscheinlich verbessert' | 'weitgehend unverändert' |
                      'möglicherweise vermindert' | 'nicht sicher vergleichbar'
    """
    if v_alt is None or v_neu is None:
        return (
            "nicht sicher vergleichbar",
            f"Für {laktat_ziel:.1f} mmol/l konnte kein interpolierbarer "
            f"Vergleichswert aus beiden Tests ermittelt werden.",
        )
    diff = v_neu - v_alt
    if abs(diff) < 0.3:
        return (
            "weitgehend unverändert",
            f"Bei {laktat_ziel:.1f} mmol/l wurde nahezu die gleiche "
            f"Geschwindigkeit erreicht ({v_alt:.1f} → {v_neu:.1f} km/h, "
            f"Differenz: {diff:+.1f} km/h).",
        )
    elif diff > 0:
        return (
            "wahrscheinlich verbessert",
            f"Die Laktatleistungskurve ist unter vergleichbaren Testbedingungen "
            f"nach rechts verschoben. Bei {laktat_ziel:.1f} mmol/l wurde eine "
            f"höhere Laufgeschwindigkeit erreicht "
            f"({v_alt:.1f} → {v_neu:.1f} km/h, +{diff:.1f} km/h). "
            f"Dies spricht für eine verbesserte submaximale Ausdauerleistungsfähigkeit.",
        )
    else:
        return (
            "möglicherweise vermindert",
            f"Im Vergleichstest wurde {laktat_ziel:.1f} mmol/l bei einer "
            f"niedrigeren Geschwindigkeit erreicht "
            f"({v_alt:.1f} → {v_neu:.1f} km/h, {diff:.1f} km/h). "
            f"Das Ergebnis kann auf eine geringere aktuelle Ausdauerleistungsfähigkeit "
            f"hinweisen. Trainingsbelastung, Regeneration, Ernährung, Tagesform und "
            f"Testbedingungen sollten bei der Interpretation berücksichtigt werden.",
        )


# ─── Protokollvergleich ───────────────────────────────────────────────────────

def protokolle_vergleichbar(p1: dict, p2: dict) -> tuple[bool, list[str]]:
    """Prüft ob zwei Protokolle für einen direkten Vergleich ausreichend ähnlich sind.

    Returns: (vergleichbar: bool, abweichungen: list[str])
    """
    abweichungen = []
    prueffelder = [
        ("geraeteart",           "Geräteart"),
        ("startgeschwindigkeit", "Startgeschwindigkeit"),
        ("steigerung",           "Geschwindigkeitssteigerung"),
        ("stufendauer",          "Stufendauer (min)"),
        ("steigung",             "Laufbandsteigung (%)"),
    ]
    for key, label in prueffelder:
        v1, v2 = p1.get(key), p2.get(key)
        if v1 is not None and v2 is not None and str(v1) != str(v2):
            abweichungen.append(f"{label}: {v1} vs. {v2}")
    return len(abweichungen) == 0, abweichungen


# ─── Schwellenvergleich ───────────────────────────────────────────────────────

SCHWELLEN_ZIELWERTE = [2.0, 4.0]


def schwellenvergleich_tabelle(
    test1_stufen: list[dict],
    test2_stufen: list[dict],
    test1_datum: str,
    test2_datum: str,
) -> list[dict]:
    """Erzeugt eine Vergleichstabelle bei festen Laktatwerten (2 und 4 mmol/l).

    Gibt eine Liste von Zeilen zurück, die als DataFrame dargestellt werden kann.
    """
    zeilen = []
    for ziel in SCHWELLEN_ZIELWERTE:
        r1 = interpoliere_bei_laktat(test1_stufen, ziel)
        r2 = interpoliere_bei_laktat(test2_stufen, ziel)
        v1 = r1["x_wert"] if r1 else None
        v2 = r2["x_wert"] if r2 else None
        diff_v = None
        if v1 is not None and v2 is not None:
            diff_v = round(v2 - v1, 2)

        # HF bei Laktatwert
        hf_stufen_1 = [
            s for s in test1_stufen
            if s.get("laktat_mmol_l") is not None and s.get("herzfrequenz_bpm")
        ]
        hf_stufen_2 = [
            s for s in test2_stufen
            if s.get("laktat_mmol_l") is not None and s.get("herzfrequenz_bpm")
        ]

        def _hf_bei_v(stufen, v_ziel):
            if v_ziel is None:
                return None
            nächste = sorted(stufen, key=lambda s: abs(s.get("geschwindigkeit_kmh", 0) - v_ziel))
            return nächste[0]["herzfrequenz_bpm"] if nächste else None

        hf1 = _hf_bei_v(hf_stufen_1, v1)
        hf2 = _hf_bei_v(hf_stufen_2, v2)
        diff_hf = round(hf2 - hf1, 0) if (hf1 and hf2) else None

        v1_txt = (f"{v1:.2f} km/h" + (" (interp.)" if r1 and r1.get("interpoliert") else "")) if v1 else "—"
        v2_txt = (f"{v2:.2f} km/h" + (" (interp.)" if r2 and r2.get("interpoliert") else "")) if v2 else "—"
        zeilen.append({
            "Kennwert":    f"Geschwindigkeit bei {ziel:.0f} mmol/l",
            test1_datum:   v1_txt,
            test2_datum:   v2_txt,
            "Veränderung": (f"{diff_v:+.2f} km/h" if diff_v is not None else "—"),
        })
        zeilen.append({
            "Kennwert":    f"HF bei {ziel:.0f} mmol/l",
            test1_datum:   (f"{hf1:.0f} bpm" if hf1 else "—"),
            test2_datum:   (f"{hf2:.0f} bpm" if hf2 else "—"),
            "Veränderung": (f"{diff_hf:+.0f} bpm" if diff_hf is not None else "—"),
        })
    return zeilen


# ─── Trainingsbereiche (schwellenbasiert) ─────────────────────────────────────

def trainingsbereiche_aus_schwellen(
    vt1_hf: Optional[float] = None,
    vt2_hf: Optional[float] = None,
    schwelle_hf: Optional[float] = None,
    hf_max: Optional[float] = None,
    grundlage_text: str = "",
) -> list[dict]:
    """Erzeugt Trainingsbereiche auf Basis gemessener Schwellenwerte.

    Verwendet keine 220-minus-Alter-Formel, wenn gemessene Werte vorhanden sind.
    """
    bereiche = []

    # Präferenz: VT1/VT2 → Laktatschwelle → nichts
    if vt1_hf and vt2_hf:
        bereiche = [
            {"Bereich": "Regeneration / Kompensation", "HF-Bereich": f"< {vt1_hf - 10:.0f} bpm",
             "Intensität": "< VT1 - 10"},
            {"Bereich": "Grundlagenausdauer (aerob)",  "HF-Bereich": f"{vt1_hf - 10:.0f}–{vt1_hf:.0f} bpm",
             "Intensität": "um VT1"},
            {"Bereich": "Entwicklungsbereich",         "HF-Bereich": f"{vt1_hf:.0f}–{vt2_hf:.0f} bpm",
             "Intensität": "VT1–VT2"},
            {"Bereich": "Schwellentraining (anaerob)", "HF-Bereich": f"{vt2_hf:.0f}–{(vt2_hf + (hf_max or vt2_hf + 10) * 0.03):.0f} bpm",
             "Intensität": "um VT2"},
        ]
        if hf_max:
            bereiche.append({"Bereich": "VO₂max-Training", "HF-Bereich": f"> {vt2_hf:.0f} bpm",
                             "Intensität": "> VT2"})
    elif schwelle_hf and hf_max:
        bereiche = [
            {"Bereich": "Regeneration",       "HF-Bereich": f"< {schwelle_hf * 0.85:.0f} bpm", "Intensität": "< 85% Schwellen-HF"},
            {"Bereich": "Grundlage",          "HF-Bereich": f"{schwelle_hf * 0.85:.0f}–{schwelle_hf:.0f} bpm", "Intensität": "85–100% Schwellen-HF"},
            {"Bereich": "Entwicklungsbereich","HF-Bereich": f"{schwelle_hf:.0f}–{min(schwelle_hf * 1.05, hf_max):.0f} bpm", "Intensität": "100–105% Schwellen-HF"},
        ]

    for b in bereiche:
        b["Grundlage"] = grundlage_text or "Gemessene Schwellenwerte"
    return bereiche
