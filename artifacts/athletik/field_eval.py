"""
Normbereiche für Athletik-Testfelder.

Öffentliche API
───────────────
bewerte_feld(value, test_id, field_id)
    → (stufe, label, icon)
    stufe: "gut" | "grenz" | "auffaellig" | "kritisch" | None

Typen in _NORMEN
────────────────
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
        "cmj_beid":   ("höher_besser",  35.0, 25.0),   # cm – beidbeinig
        "cmj_r":      ("höher_besser",  28.0, 20.0),   # cm – einbeinig
        "cmj_l":      ("höher_besser",  28.0, 20.0),
        "squat_jump": ("höher_besser",  30.0, 22.0),   # cm
        "dj_hoehe":   ("höher_besser",  28.0, 18.0),   # cm
        "dj_kontakt": ("niedriger_besser", 0.20, 0.30),# s – kürzer = besser
        "standweit":  ("höher_besser", 200.0, 170.0),  # cm
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
        "distanz": ("höher_besser", 1200.0, 600.0),  # m – IR1-Orientierung
        "hf_max":  None,   # individuell
        "rpe":     None,   # subjektiv
    },

    # ── Anthropometrie ────────────────────────────────────────────────────────
    "anthropometrie": {
        "groesse":     None,
        "gewicht":     None,
        "koerperfett": ("bereich", 6.0, 20.0, 3.0, 26.0),  # % — sportartübergreifend
        "muskelmasse": None,
        "sitzhoehe":   None,
        "beinlaenge":  None,
        "armspann":    None,
    },
}

# ── Stufen-Definitionen ───────────────────────────────────────────────────────
_STUFEN: dict[str, tuple[str, str]] = {
    "gut":        ("✅", "Normbereich"),
    "grenz":      ("⚠️",  "Grenzbereich"),
    "auffaellig": ("🔴", "Auffällig"),
    "kritisch":   ("🚫", "Schmerzen / Abbruch"),
}

_HTML_COLORS: dict[str, tuple[str, str]] = {
    # (bg, text)
    "gut":        ("#1a3326", "#3fb950"),
    "grenz":      ("#2d2a14", "#d29922"),
    "auffaellig": ("#3d1a1a", "#f85149"),
    "kritisch":   ("#3d1a1a", "#ff7b72"),
}


def bewerte_feld(
    value: float | int | None,
    test_id: str,
    field_id: str,
) -> tuple[str | None, str, str]:
    """Bewertet einen eingegebenen Wert gegen die hinterlegten Normen.

    Rückgabe: (stufe, label, icon)
        stufe  — "gut" | "grenz" | "auffaellig" | "kritisch" | None
        label  — lesbarer Text, z. B. "Normbereich"
        icon   — Emoji, z. B. "✅"
    Gibt (None, "", "") zurück, wenn kein Normwert vorhanden.
    """
    if value is None:
        return None, "", ""

    norm = _NORMEN.get(test_id, {}).get(field_id)
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

    icon, label = _STUFEN[stufe]
    return stufe, label, icon


def badge_html(
    value: float | int | None,
    test_id: str,
    field_id: str,
) -> str:
    """Gibt einen fertigen HTML-Badge-String zurück oder '' wenn kein Norm vorhanden."""
    stufe, label, icon = bewerte_feld(value, test_id, field_id)
    if stufe is None:
        return ""
    bg, color = _HTML_COLORS[stufe]
    return (
        f'<div style="display:inline-block;font-size:11px;font-weight:600;'
        f'padding:2px 9px;border-radius:10px;margin:2px 0 6px;'
        f'background:{bg};color:{color}">'
        f'{icon} {label}</div>'
    )
