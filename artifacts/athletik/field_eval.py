"""
Normbereiche für Athletik-Testfelder — mit Altersgruppen-Korrekturen.

Öffentliche API
───────────────
alter_zu_altersgruppe(alter)
    → "U10" | "U12" | "U14" | "U16" | "U18" | "Senior"

bewerte_feld(value, test_id, field_id, altersgruppe=None)
    → (stufe, label, icon)
    stufe: "gut" | "grenz" | "auffaellig" | "kritisch" | None

badge_html(value, test_id, field_id, altersgruppe=None)
    → HTML-String oder ""

Norm-Typen in _NORMEN / _NORMEN_ALTERSGRUPPE
─────────────────────────────────────────────
("niedriger_besser", gut_max, grenz_max)
    gut   : value ≤ gut_max
    grenz : gut_max < value ≤ grenz_max
    auffäl.: value > grenz_max

("höher_besser", gut_min, grenz_min)
    gut   : value ≥ gut_min
    grenz : grenz_min ≤ value < gut_min
    auffäl.: value < grenz_min

("bereich", gut_lo, gut_hi, grenz_lo, grenz_hi)
    gut   : gut_lo ≤ value ≤ gut_hi
    grenz : grenz_lo ≤ value ≤ grenz_hi  (außerhalb gut)
    auffäl.: außerhalb grenz

("fms",)
    3 → gut  · 2 → grenz  · 1 → auffällig  · 0 → kritisch
"""
from __future__ import annotations

# ── Pauschal-Normen (Fallback / Senior-Niveau) ───────────────────────────────

_NORMEN: dict[str, dict[str, tuple | None]] = {

    # ── Sprint (s) – niedriger = besser ──────────────────────────────────────
    "sprint": {
        "sprint_5m":  ("niedriger_besser", 1.05, 1.20),
        "sprint_10m": ("niedriger_besser", 1.80, 2.05),
        "sprint_20m": ("niedriger_besser", 3.05, 3.40),
        "sprint_30m": ("niedriger_besser", 4.35, 4.80),
    },

    # ── Y-Balance – Rohdaten ohne Beinlänge nicht normierbar ─────────────────
    "y_balance": {
        "beinlaenge":     None,
        "anterior":       None,
        "posteromedial":  None,
        "posterolateral": None,
    },

    # ── FMS (0–3 Punkte) ─────────────────────────────────────────────────────
    "fms": {
        "deep_squat":       ("fms",),
        "hurdle_step":      ("fms",),
        "inline_lunge":     ("fms",),
        "shoulder":         ("fms",),
        "aslr":             ("fms",),
        "trunk_stability":  ("fms",),
        "rotary_stability": ("fms",),
    },

    # ── Sprung (cm / s) ───────────────────────────────────────────────────────
    "jump": {
        "cmj_beid":   ("höher_besser",  35.0, 25.0),
        "cmj_r":      ("höher_besser",  28.0, 20.0),
        "cmj_l":      ("höher_besser",  28.0, 20.0),
        "squat_jump": ("höher_besser",  30.0, 22.0),
        "dj_hoehe":   ("höher_besser",  28.0, 18.0),
        "dj_kontakt": ("niedriger_besser", 0.20, 0.30),
        "standweit":  ("höher_besser", 200.0, 170.0),
    },

    # ── Agilität (s) – niedriger = besser ─────────────────────────────────────
    "agility": {
        "t505_r":   ("niedriger_besser",  2.20,  2.60),
        "t505_l":   ("niedriger_besser",  2.20,  2.60),
        "t5_10_5":  ("niedriger_besser",  4.50,  5.20),
        "t_test":   ("niedriger_besser",  9.50, 11.00),
        "illinois": ("niedriger_besser", 15.50, 17.50),
    },

    # ── Yo-Yo / Ausdauer ─────────────────────────────────────────────────────
    "yoyo": {
        "distanz": ("höher_besser", 1200.0, 600.0),
        "hf_max":  None,
        "rpe":     None,
    },

    # ── Anthropometrie ────────────────────────────────────────────────────────
    "anthropometrie": {
        "groesse":     None,
        "gewicht":     None,
        "koerperfett": ("bereich", 6.0, 20.0, 3.0, 26.0),
        "muskelmasse": None,
        "sitzhoehe":   None,
        "beinlaenge":  None,
        "armspann":    None,
    },
}

# ── Altersgruppen-spezifische Normen ─────────────────────────────────────────
# Struktur: _NORMEN_ALTERSGRUPPE[altersgruppe][test_id][field_id] = norm_tuple
# FMS und y_balance werden nicht überschrieben (kategorisch bzw. None).
# Fehlende Einträge fallen auf _NORMEN zurück.

_NORMEN_ALTERSGRUPPE: dict[str, dict[str, dict[str, tuple | None]]] = {

    # ── U7 (Bambini, ≤ 7 Jahre) ───────────────────────────────────────────────
    # Keine validierten Feldtest-Normen für 6–7-Jährige in der Sportwissenschaft.
    # Alle Felder → None: Badge wird ausgeblendet (kein falsches „Auffällig").
    "U7": {
        "sprint": {
            "sprint_5m":  None,
            "sprint_10m": None,
            "sprint_20m": None,
            "sprint_30m": None,
        },
        "jump": {
            "cmj_beid":   None,
            "cmj_r":      None,
            "cmj_l":      None,
            "squat_jump": None,
            "dj_hoehe":   None,
            "dj_kontakt": None,
            "standweit":  None,
        },
        "agility": {
            "t505_r":   None,
            "t505_l":   None,
            "t5_10_5":  None,
            "t_test":   None,
            "illinois": None,
        },
        "yoyo": {
            "distanz": None,
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 10.0, 26.0, 5.0, 32.0),
        },
    },

    # ── U8 (F-Jugend, 7–8 Jahre) ──────────────────────────────────────────────
    # Sprint: Quelle Rumpf 2016, DFB Junioren-Diagnostik (Leistungssport / Breitensport).
    # Altersbereich 7–8 J. (U = unter: alter < 9 → U8). Kein Badge für ältere Spieler.
    # Alle anderen Felder ohne belastbare U8-Norm → None (kein Badge statt falschem Wert).
    "U8": {
        "sprint": {
            "sprint_5m":  None,                              # keine U8-Norm vorhanden
            "sprint_10m": ("niedriger_besser", 2.55, 2.80),  # Leistungssport / Breitensport
            "sprint_20m": None,                              # keine U8-Norm vorhanden
            "sprint_30m": ("niedriger_besser", 7.20, 8.00),  # Leistungssport / Breitensport
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  13.0,  8.0),     # konservative U8-Schätzung JSCR
            "cmj_r":      None,
            "cmj_l":      None,
            "squat_jump": None,
            "dj_hoehe":   None,
            "dj_kontakt": None,
            "standweit":  ("höher_besser", 105.0, 80.0),     # DFB Junioren-Diagnostik
        },
        "agility": {
            "t505_r":   None,
            "t505_l":   None,
            "t5_10_5":  None,
            "t_test":   None,
            "illinois": None,
        },
        "yoyo": {
            "distanz": None,
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 10.0, 26.0, 5.0, 32.0),
        },
    },

    "U10": {
        "sprint": {
            "sprint_5m":  ("niedriger_besser", 1.35, 1.55),
            "sprint_10m": ("niedriger_besser", 2.30, 2.60),
            "sprint_20m": ("niedriger_besser", 3.85, 4.25),
            "sprint_30m": ("niedriger_besser", 5.60, 6.20),
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  17.0, 11.0),
            "cmj_r":      ("höher_besser",  12.0,  8.0),
            "cmj_l":      ("höher_besser",  12.0,  8.0),
            "squat_jump": ("höher_besser",  14.0,  9.0),
            "dj_hoehe":   ("höher_besser",  13.0,  8.0),
            "dj_kontakt": ("niedriger_besser", 0.32, 0.45),
            "standweit":  ("höher_besser", 120.0, 90.0),
        },
        "agility": {
            "t505_r":   ("niedriger_besser",  2.75,  3.15),
            "t505_l":   ("niedriger_besser",  2.75,  3.15),
            "t5_10_5":  ("niedriger_besser",  5.80,  6.50),
            "t_test":   ("niedriger_besser", 11.50, 13.00),
            "illinois": ("niedriger_besser", 18.00, 20.50),
        },
        "yoyo": {
            "distanz": ("höher_besser", 380.0, 160.0),
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 9.0, 24.0, 4.0, 30.0),
        },
    },

    "U12": {
        "sprint": {
            "sprint_5m":  ("niedriger_besser", 1.22, 1.42),
            "sprint_10m": ("niedriger_besser", 2.10, 2.40),
            "sprint_20m": ("niedriger_besser", 3.55, 3.95),
            "sprint_30m": ("niedriger_besser", 5.10, 5.70),
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  22.0, 14.0),
            "cmj_r":      ("höher_besser",  16.0, 10.0),
            "cmj_l":      ("höher_besser",  16.0, 10.0),
            "squat_jump": ("höher_besser",  18.0, 12.0),
            "dj_hoehe":   ("höher_besser",  17.0, 11.0),
            "dj_kontakt": ("niedriger_besser", 0.28, 0.40),
            "standweit":  ("höher_besser", 150.0, 115.0),
        },
        "agility": {
            "t505_r":   ("niedriger_besser",  2.58,  2.97),
            "t505_l":   ("niedriger_besser",  2.58,  2.97),
            "t5_10_5":  ("niedriger_besser",  5.40,  6.10),
            "t_test":   ("niedriger_besser", 10.80, 12.20),
            "illinois": ("niedriger_besser", 17.00, 19.50),
        },
        "yoyo": {
            "distanz": ("höher_besser", 580.0, 260.0),
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 8.0, 22.0, 4.0, 28.0),
        },
    },

    "U14": {
        "sprint": {
            "sprint_5m":  ("niedriger_besser", 1.14, 1.33),
            "sprint_10m": ("niedriger_besser", 1.95, 2.22),
            "sprint_20m": ("niedriger_besser", 3.28, 3.68),
            "sprint_30m": ("niedriger_besser", 4.75, 5.25),
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  27.0, 18.0),
            "cmj_r":      ("höher_besser",  20.0, 14.0),
            "cmj_l":      ("höher_besser",  20.0, 14.0),
            "squat_jump": ("höher_besser",  23.0, 16.0),
            "dj_hoehe":   ("höher_besser",  21.0, 14.0),
            "dj_kontakt": ("niedriger_besser", 0.25, 0.36),
            "standweit":  ("höher_besser", 175.0, 140.0),
        },
        "agility": {
            "t505_r":   ("niedriger_besser",  2.43,  2.80),
            "t505_l":   ("niedriger_besser",  2.43,  2.80),
            "t5_10_5":  ("niedriger_besser",  5.05,  5.75),
            "t_test":   ("niedriger_besser", 10.20, 11.60),
            "illinois": ("niedriger_besser", 16.20, 18.50),
        },
        "yoyo": {
            "distanz": ("höher_besser", 800.0, 380.0),
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 7.0, 21.0, 3.0, 27.0),
        },
    },

    "U16": {
        "sprint": {
            "sprint_5m":  ("niedriger_besser", 1.08, 1.26),
            "sprint_10m": ("niedriger_besser", 1.86, 2.12),
            "sprint_20m": ("niedriger_besser", 3.12, 3.50),
            "sprint_30m": ("niedriger_besser", 4.50, 5.00),
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  31.0, 22.0),
            "cmj_r":      ("höher_besser",  25.0, 17.0),
            "cmj_l":      ("höher_besser",  25.0, 17.0),
            "squat_jump": ("höher_besser",  27.0, 19.0),
            "dj_hoehe":   ("höher_besser",  25.0, 16.0),
            "dj_kontakt": ("niedriger_besser", 0.22, 0.32),
            "standweit":  ("höher_besser", 188.0, 155.0),
        },
        "agility": {
            "t505_r":   ("niedriger_besser",  2.30,  2.67),
            "t505_l":   ("niedriger_besser",  2.30,  2.67),
            "t5_10_5":  ("niedriger_besser",  4.75,  5.45),
            "t_test":   ("niedriger_besser",  9.80, 11.20),
            "illinois": ("niedriger_besser", 15.80, 18.00),
        },
        "yoyo": {
            "distanz": ("höher_besser", 980.0, 490.0),
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 7.0, 21.0, 3.0, 26.0),
        },
    },

    "U18": {
        "sprint": {
            "sprint_5m":  ("niedriger_besser", 1.06, 1.22),
            "sprint_10m": ("niedriger_besser", 1.82, 2.07),
            "sprint_20m": ("niedriger_besser", 3.08, 3.43),
            "sprint_30m": ("niedriger_besser", 4.38, 4.83),
        },
        "jump": {
            "cmj_beid":   ("höher_besser",  34.0, 24.0),
            "cmj_r":      ("höher_besser",  27.0, 19.0),
            "cmj_l":      ("höher_besser",  27.0, 19.0),
            "squat_jump": ("höher_besser",  29.0, 21.0),
            "dj_hoehe":   ("höher_besser",  27.0, 17.0),
            "dj_kontakt": ("niedriger_besser", 0.21, 0.31),
            "standweit":  ("höher_besser", 197.0, 165.0),
        },
        "agility": {
            "t505_r":   ("niedriger_besser",  2.23,  2.62),
            "t505_l":   ("niedriger_besser",  2.23,  2.62),
            "t5_10_5":  ("niedriger_besser",  4.58,  5.28),
            "t_test":   ("niedriger_besser",  9.60, 11.05),
            "illinois": ("niedriger_besser", 15.60, 17.70),
        },
        "yoyo": {
            "distanz": ("höher_besser", 1100.0, 540.0),
            "hf_max":  None,
            "rpe":     None,
        },
        "anthropometrie": {
            "koerperfett": ("bereich", 6.0, 20.0, 3.0, 26.0),
        },
    },

    # Senior = _NORMEN (Fallback — keine eigene Überschreibung nötig)
}

# ── Stufen-Definitionen ───────────────────────────────────────────────────────

_STUFEN: dict[str, tuple[str, str]] = {
    "gut":        ("✅", "Normbereich"),
    "grenz":      ("⚠️",  "Grenzbereich"),
    "auffaellig": ("🔴", "Auffällig"),
    "kritisch":   ("🚫", "Schmerzen / Abbruch"),
}

_HTML_COLORS: dict[str, tuple[str, str]] = {
    "gut":        ("#1a3326", "#3fb950"),
    "grenz":      ("#2d2a14", "#d29922"),
    "auffaellig": ("#3d1a1a", "#f85149"),
    "kritisch":   ("#3d1a1a", "#ff7b72"),
}


# ── Öffentliche Hilfsfunktion ─────────────────────────────────────────────────

def alter_zu_altersgruppe(alter: float | None) -> str:
    """Mappt ein Dezimalter auf die Altersgruppen-Bezeichnung.

    U = unter: Alter 9 (unter 10) → U10, Alter 7 (unter 8) → U8.
    Stimmt überein mit age_norms.alter_zu_normgruppe().

    Returns:
        "U7" | "U8" | "U10" | "U12" | "U14" | "U16" | "U18" | "Senior"

    U7 (< 7 J.): alle None — keine validierten Feldtest-Normen für ≤ 6-Jährige.
    U8 (7–8 J.): Sprint 10m/30m vorhanden; fehlende Distanzen → None.
    U10 (9–10 J.): vollständige Normen vorhanden.
    """
    if not alter:
        return "Senior"
    if alter < 7:   return "U7"   # ≤ 6 J.  (war: < 8)
    if alter < 9:   return "U8"   # 7–8 J.  (war: < 10)
    if alter < 11:  return "U10"  # 9–10 J. (war: < 12)
    if alter < 13:  return "U12"  # 11–12 J. (war: < 14)
    if alter < 15:  return "U14"  # 13–14 J. (war: < 16)
    if alter < 17:  return "U16"  # 15–16 J. (war: < 18)
    if alter < 21:  return "U18"  # 17–20 J.
    return "Senior"


def _get_norm(
    test_id: str,
    field_id: str,
    altersgruppe: str | None,
) -> tuple | None:
    """Gibt die Norm-Tuple zurück — altersgruppiert wenn vorhanden, sonst Fallback."""
    if altersgruppe and altersgruppe != "Senior":
        ag_norms = _NORMEN_ALTERSGRUPPE.get(altersgruppe, {})
        test_norms = ag_norms.get(test_id, {})
        if field_id in test_norms:
            return test_norms[field_id]
    # Fallback: Pauschal-Normen
    return _NORMEN.get(test_id, {}).get(field_id)


def bewerte_feld(
    value: float | int | None,
    test_id: str,
    field_id: str,
    altersgruppe: str | None = None,
) -> tuple[str | None, str, str]:
    """Bewertet einen eingegebenen Wert gegen die hinterlegten Normen.

    Args:
        value:        Messwert
        test_id:      Test-ID (z.B. "sprint", "jump")
        field_id:     Feld-ID (z.B. "sprint_10m", "cmj_beid")
        altersgruppe: Optional — "U10" | "U12" | "U14" | "U16" | "U18" | "Senior"
                      Wird für altersgerechte Normen verwendet.

    Returns:
        (stufe, label, icon)
        stufe  — "gut" | "grenz" | "auffaellig" | "kritisch" | None
        label  — lesbarer Text, z. B. "Normbereich (U14)"
        icon   — Emoji, z. B. "✅"
        Gibt (None, "", "") zurück wenn kein Normwert vorhanden.
    """
    if value is None:
        return None, "", ""

    norm = _get_norm(test_id, field_id, altersgruppe)
    if norm is None:
        return None, "", ""

    typ = norm[0]

    if typ == "fms":
        v = int(value)
        if v == 3:   stufe = "gut"
        elif v == 2: stufe = "grenz"
        elif v == 1: stufe = "auffaellig"
        else:        stufe = "kritisch"

    elif typ == "niedriger_besser":
        _, gut_max, grenz_max = norm
        if value <= gut_max:
            stufe = "gut"
        elif value <= grenz_max:
            stufe = "grenz"
        else:
            stufe = "auffaellig"

    elif typ == "höher_besser":
        _, gut_min, grenz_min = norm
        if value >= gut_min:
            stufe = "gut"
        elif value >= grenz_min:
            stufe = "grenz"
        else:
            stufe = "auffaellig"

    elif typ == "bereich":
        _, gut_lo, gut_hi, grenz_lo, grenz_hi = norm
        if gut_lo <= value <= gut_hi:
            stufe = "gut"
        elif grenz_lo <= value <= grenz_hi:
            stufe = "grenz"
        else:
            stufe = "auffaellig"

    else:
        return None, "", ""

    icon, label_base = _STUFEN[stufe]
    # Altersgruppen-Label anhängen wenn nicht Senior
    if altersgruppe and altersgruppe != "Senior":
        label = f"{label_base} ({altersgruppe})"
    else:
        label = label_base
    return stufe, label, icon


def badge_html(
    value: float | int | None,
    test_id: str,
    field_id: str,
    altersgruppe: str | None = None,
) -> str:
    """Gibt einen fertigen HTML-Badge-String zurück oder '' wenn kein Norm vorhanden."""
    stufe, label, icon = bewerte_feld(value, test_id, field_id, altersgruppe)
    if stufe is None:
        return ""
    bg, color = _HTML_COLORS[stufe]
    return (
        f'<div style="display:inline-block;font-size:11px;font-weight:600;'
        f'padding:2px 9px;border-radius:10px;margin:2px 0 6px;'
        f'background:{bg};color:{color}">'
        f'{icon} {label}</div>'
    )


# ── Asymmetrie-Badges ─────────────────────────────────────────────────────────

def asymmetrie_badge_html(
    val_r: float | None,
    val_l: float | None,
    niedriger_besser: bool = False,
) -> str:
    """HTML-Badge für die Seitenasymmetrie zwischen rechts (R) und links (L).

    Args:
        val_r:             Messwert rechte Seite.
        val_l:             Messwert linke Seite.
        niedriger_besser:  True für Zeittests (505, Sprint) — bessere Seite = kleinerer Wert.
                           False für Sprungtests (CMJ) — bessere Seite = größerer Wert.

    Formel:  ASI = |R − L| / Referenz × 100
    Referenz = min(R, L) für niedriger_besser (schnellste Seite als Basis)
               max(R, L) für höher_besser   (stärkste Seite als Basis)

    Gibt '' zurück wenn nicht beide Werte > 0.
    """
    if not val_r or not val_l or val_r <= 0 or val_l <= 0:
        return ""

    diff = abs(val_r - val_l)
    ref  = min(val_r, val_l) if niedriger_besser else max(val_r, val_l)
    if ref <= 0:
        return ""

    asym_pct = diff / ref * 100

    if asym_pct <= 10.0:
        bg, color = "#1a3326", "#3fb950"
        label = f"✅ Symmetrisch ({asym_pct:.1f} %)"
    elif asym_pct <= 15.0:
        bg, color = "#2d2a14", "#d29922"
        label = f"⚠️ Asymmetrie {asym_pct:.1f} % — trainingsrelevant"
    else:
        bg, color = "#3d1a1a", "#f85149"
        label = f"🔴 Asymmetrie {asym_pct:.1f} % — deutlich erhöht"

    return (
        f'<div style="display:inline-block;font-size:11px;font-weight:600;'
        f'padding:3px 10px;border-radius:10px;margin:4px 0 6px;'
        f'background:{bg};color:{color}">'
        f'{label}</div>'
    )


def fms_asymmetrie_badge_html(
    val_l: int | None,
    val_r: int | None,
) -> str:
    """HTML-Badge für Seitenasymmetrie bei FMS-Bilateral-Tests (Skala 0–3).

    Gibt '' zurück wenn beide Seiten 0 oder gleich.
    """
    if val_l is None or val_r is None:
        return ""
    if val_l == 0 and val_r == 0:
        return ""

    diff = abs(val_l - val_r)
    if diff == 0:
        return ""

    if diff == 1:
        bg, color = "#2d2a14", "#d29922"
        label = "⚠️ Seitenunterschied 1 Pkt."
    else:
        bg, color = "#3d1a1a", "#f85149"
        label = f"🔴 Seitenunterschied {diff} Pkt. — auffällig"

    return (
        f'<div style="display:inline-block;font-size:11px;font-weight:600;'
        f'padding:3px 10px;border-radius:10px;margin:4px 0 6px;'
        f'background:{bg};color:{color}">'
        f'{label}</div>'
    )
