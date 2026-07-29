"""
Reusable UI components — all return HTML strings or render directly via st.markdown.
Import these instead of duplicating markup across pages.
"""

from theme import C


# ─── KPI / Metric card ────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, subtitle: str = "", color: str | None = None) -> str:
    """Full-width KPI card with coloured value. Returns HTML string."""
    col = color or C["text"]
    sub = f'<div class="kpi-sub">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{col}">{value}</div>'
        f'{sub}'
        f'</div>'
    )


def score_kpi(score: int) -> str:
    """KPI card for athletik score with auto-colour."""
    color = C["green"] if score >= 75 else C["yellow"] if score >= 50 else C["red"]
    return kpi_card("Athletik Score", f'{score}<span style="font-size:16px;font-weight:400;color:{C["muted"]}">/100</span>', color=color)


def risk_kpi(level: str) -> str:
    """KPI card for risk level."""
    icons  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    labels = {"hoch": "HANDLUNGSBEDARF HOCH", "mittel": "HANDLUNGSBEDARF", "gering": "UNAUFFÄLLIG"}
    colors = {"hoch": C["red"], "mittel": C["yellow"], "gering": C["green"]}
    return kpi_card("Athletik-Status", f'{icons.get(level,"")} {labels.get(level,"—")}', color=colors.get(level, C["text"]))


# ─── Player banner ────────────────────────────────────────────────────────────

def player_banner(player: dict, alter: int | float | None = None) -> str:
    """Horizontal player-info banner for page headers."""
    name   = player.get("name", "—")
    pos    = player.get("hauptposition") or player.get("position") or "—"
    team   = player.get("mannschaft") or "—"
    status = player.get("trainingsstatus") or "Volltraining"
    status_color = (
        C["red"]    if any(x in status.lower() for x in ["pause", "abklärung", "abklaerung"])
        else C["yellow"] if any(x in status.lower() for x in ["angepasst", "individuell", "freigabe"])
        else C["green"]
    )
    alter_str = f"{int(alter)} Jahre · " if alter else ""
    return (
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
        f'border-radius:12px;padding:14px 20px;margin-bottom:16px;'
        f'display:flex;align-items:center;gap:16px">'
        f'<div style="font-size:32px">⚽</div>'
        f'<div>'
        f'<div style="font-size:18px;font-weight:700;color:{C["text"]}">{name}</div>'
        f'<div style="font-size:12px;color:{C["muted"]};margin-top:3px">'
        f'{alter_str}{pos} · {team} · '
        f'<span style="color:{status_color};font-weight:600">{status}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


# ─── Section header ───────────────────────────────────────────────────────────

def section_header(title: str, subtitle: str = "") -> str:
    sub = f'<div style="font-size:13px;color:{C["muted"]};margin-top:4px">{subtitle}</div>' if subtitle else ""
    return (
        f'<div style="margin-bottom:20px">'
        f'<h1 style="margin:0;font-size:26px!important;font-weight:700!important">{title}</h1>'
        f'{sub}'
        f'</div>'
    )


# ─── Deficit row ──────────────────────────────────────────────────────────────

def deficit_row(d: dict) -> str:
    """Compact deficit row for the home page."""
    css   = "tag-crit" if d["level"] == "kritisch" else "tag-warn"
    modul = d.get("modul", "")
    modul_html = (
        f'<span style="font-size:10px;color:{C["muted"]};background:{C["surface2"]};'
        f'border-radius:4px;padding:1px 6px;margin-left:6px">{modul}</span>'
        if modul else ""
    )
    return (
        f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;'
        f'border-bottom:1px solid {C["border"]}">'
        f'<span class="{css}">{d["bereich"]}</span>'
        f'{modul_html}'
        f'<span style="font-size:12px;color:{C["muted"]};flex:1">{d["text"]}</span>'
        f'</div>'
    )


# ─── Strength row (inverse: modules with good scores) ────────────────────────

def strength_row(bereich: str, detail: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
        f'border-bottom:1px solid {C["border"]}">'
        f'<span class="tag-ok">✓ {bereich}</span>'
        f'<span style="font-size:12px;color:{C["muted"]}">{detail}</span>'
        f'</div>'
    )


# ─── Test status mini-card ────────────────────────────────────────────────────

def test_status_card(name: str, icon: str, last_date: str | None, rating: str | None) -> str:
    """Small card showing a test module's last result."""
    rating_color = (
        C["green"]  if rating and any(x in rating for x in ["Sehr gut", "Gut"])
        else C["yellow"] if rating and "Mittel" in rating
        else C["red"]    if rating and "Verbesserung" in rating
        else C["muted"]
    )
    date_str   = last_date or "Kein Test"
    rating_str = rating    or "—"
    return (
        f'<div class="card-sm" style="display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<div style="font-size:14px;font-weight:600;color:{C["text"]}">{icon} {name}</div>'
        f'<div style="font-size:11px;color:{C["muted"]};margin-top:2px">{date_str}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:12px;font-weight:600;color:{rating_color}">{rating_str}</div>'
        f'</div>'
        f'</div>'
    )


# ─── Empty state ─────────────────────────────────────────────────────────────

def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    sub = f'<div style="font-size:13px;color:{C["muted"]};margin-top:6px">{subtitle}</div>' if subtitle else ""
    return (
        f'<div style="text-align:center;padding:48px 24px;color:{C["muted"]}">'
        f'<div style="font-size:48px">{icon}</div>'
        f'<div style="font-size:16px;font-weight:600;color:{C["text"]};margin-top:12px">{title}</div>'
        f'{sub}'
        f'</div>'
    )


# ─── Anthropometrie summary card ─────────────────────────────────────────────

def anthro_karte(anthro: dict | None) -> str:
    """Compact Anthropometrie summary card — same tile style as test-status cards."""
    if not anthro:
        return (
            f'<div class="card-sm" style="display:flex;justify-content:space-between;'
            f'align-items:center;min-height:56px">'
            f'<div>'
            f'<div style="font-size:14px;font-weight:600;color:{C["text"]}">📐 Anthropometrie</div>'
            f'<div style="font-size:11px;color:{C["muted"]};margin-top:2px">Noch keine Messung</div>'
            f'</div>'
            f'<div style="font-size:12px;font-weight:600;color:{C["muted"]}">—</div>'
            f'</div>'
        )

    datum   = anthro.get("datum") or "—"
    groesse = anthro.get("groesse")
    gewicht = anthro.get("gewicht")
    bmi     = anthro.get("bmi")
    bmi_kat = anthro.get("bmi_kategorie") or "—"
    reife   = anthro.get("reifestatus") or "—"

    groesse_str = f"{groesse:.1f} cm" if groesse else "—"
    gewicht_str = f"{gewicht:.1f} kg" if gewicht else "—"
    bmi_str     = f"{bmi:.1f}" if bmi else "—"

    # BMI badge colour
    bmi_color = (
        C["red"]    if bmi_kat and any(x in bmi_kat.lower() for x in ["übergewicht", "adipositas", "untergewicht"])
        else C["yellow"] if bmi_kat and "grenzwertig" in bmi_kat.lower()
        else C["green"]
    )

    return (
        f'<div class="card-sm">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div>'
        f'<div style="font-size:14px;font-weight:600;color:{C["text"]}">📐 Anthropometrie</div>'
        f'<div style="font-size:11px;color:{C["muted"]};margin-top:2px">Letzte Messung: {datum}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<span style="font-size:11px;font-weight:600;color:{bmi_color};background:{C["surface2"]};'
        f'border-radius:4px;padding:2px 7px">{bmi_kat}</span>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap">'
        f'<div><div style="font-size:10px;color:{C["muted"]};letter-spacing:.5px">GRÖSSE</div>'
        f'<div style="font-size:15px;font-weight:700;color:{C["text"]}">{groesse_str}</div></div>'
        f'<div><div style="font-size:10px;color:{C["muted"]};letter-spacing:.5px">GEWICHT</div>'
        f'<div style="font-size:15px;font-weight:700;color:{C["text"]}">{gewicht_str}</div></div>'
        f'<div><div style="font-size:10px;color:{C["muted"]};letter-spacing:.5px">BMI</div>'
        f'<div style="font-size:15px;font-weight:700;color:{bmi_color}">{bmi_str}</div></div>'
        f'<div><div style="font-size:10px;color:{C["muted"]};letter-spacing:.5px">REIFESTATUS</div>'
        f'<div style="font-size:13px;font-weight:600;color:{C["text"]}">{reife}</div></div>'
        f'</div>'
        f'</div>'
    )


# ─── Score/risk badges (inline) ───────────────────────────────────────────────

def score_badge_html(score: int) -> str:
    cls = "badge-green" if score >= 75 else "badge-yellow" if score >= 50 else "badge-red"
    return f'<span class="score-badge {cls}">{score}<span style="font-size:13px;font-weight:400">/100</span></span>'


def risk_badge_html(level: str) -> str:
    cls    = {"hoch": "badge-red", "mittel": "badge-yellow", "gering": "badge-green"}.get(level, "badge-green")
    icons  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    labels = {"hoch": "HANDLUNGSBEDARF HOCH", "mittel": "HANDLUNGSBEDARF", "gering": "UNAUFFÄLLIG"}
    return f'<span class="score-badge {cls}">{icons[level]} {labels[level]}</span>'
