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
    _r = (rating or "").lower()
    rating_color = (
        C["green"]  if _r and any(x in _r for x in [
            "sehr gut", "gut", "ausgezeichnet", "unauffällig",
            "keine asym", "keine auffäl", "symmetrisch", "kein akuter"])
        else C["yellow"] if _r and any(x in _r for x in [
            "beobachten", "mittel", "durchschnittlich", "grenzwertig"])
        else C["red"]    if _r and any(x in _r for x in [
            "aktionsbedarf", "handlungsbedarf", "verbesserung",
            "kritisch", "unterdurchschnittlich", "auffällig", "risiko", "asymmetrie"])
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

def render_observation_selector(
    test_id: str,
    spieler_id: int,
    datum_str: str,
    key_prefix: str,
    standalone: bool = True,
) -> dict:
    """Rendert den Trainerbeobachtungs-Selektor für einen Test.

    standalone=True  → eigene Speichern/Zurücksetzen-Buttons (Einzelmodus)
    standalone=False → keine eigenen Buttons; Rückgabewert wird vom aufrufenden
                       Test-Speichern-Button mitgespeichert.

    Gibt immer ein Dict zurück:
      {"beob_ids": list, "seite": str|None, "auspraegung": str|None,
       "freitext": str|None, "text_generiert": str|None}
    """
    import streamlit as st
    import json
    from test_observations import (
        BEOBACHTUNGEN, get_beobachtungen, check_konflikte,
        generate_observation_text,
    )
    from database import beobachtung_speichern, beobachtung_laden, beobachtung_loeschen

    info = BEOBACHTUNGEN.get(test_id)
    if not info:
        return {"beob_ids": [], "seite": None, "auspraegung": None, "freitext": None, "text_generiert": None}

    with st.expander("🔍 Trainerbeobachtungen (optional)", expanded=False):
        # Vorhandene Beobachtung laden
        existing = beobachtung_laden(spieler_id, test_id, datum_str)
        saved_ids: list[str] = json.loads(existing["beob_ids"]) if existing and existing.get("beob_ids") else []
        saved_seite    = existing.get("seite")     if existing else None
        saved_ausp     = existing.get("auspraegung") if existing else None
        saved_freitext = existing.get("freitext")  if existing else ""
        saved_text     = existing.get("text_generiert") if existing else ""

        if existing:
            st.success("✅ Beobachtung für dieses Datum gespeichert.")

        # ── Modus-Auswahl ──────────────────────────────────────────────────────
        modus = st.radio(
            "Modus",
            ["Standard", "Experte"],
            horizontal=True,
            key=f"{key_prefix}_obs_modus",
            label_visibility="collapsed",
        ).lower()

        beob_list = get_beobachtungen(test_id, modus)

        # ── Checkboxen nach Kategorie ──────────────────────────────────────────
        selected_ids: list[str] = []
        kategorien: dict[str, list[dict]] = {}
        for b in beob_list:
            kategorien.setdefault(b["kat"], []).append(b)

        for kat, items in kategorien.items():
            st.markdown(f'<div style="font-size:11px;color:#8b949e;letter-spacing:1px;'
                        f'margin-top:10px;margin-bottom:4px">{kat.upper()}</div>',
                        unsafe_allow_html=True)
            for b in items:
                icon = "✅" if b["typ"] == "positiv" else "⚠️"
                checked = b["id"] in saved_ids
                val = st.checkbox(
                    f"{icon} {b['text']}",
                    value=checked,
                    key=f"{key_prefix}_obs_{b['id']}",
                )
                if val:
                    selected_ids.append(b["id"])

        # ── Konflikt-Warnung ───────────────────────────────────────────────────
        konflikte = check_konflikte(test_id, selected_ids)
        if konflikte:
            beob_map = {b["id"]: b["text"] for b in beob_list}
            for a, b_ in konflikte:
                st.warning(
                    f"\u26a0\ufe0f Widerspruch: \u201e{beob_map.get(a, a)}\u201c und "
                    f"\u201e{beob_map.get(b_, b_)}\u201c wurden gleichzeitig "
                    f"ausgew\u00e4hlt \u2014 bitte pr\u00fcfen."
                )

        # ── Seite (nur wenn test hat_seite) ───────────────────────────────────
        seite = None
        if info["hat_seite"]:
            seite_opts = ["— keine Angabe —", "rechts", "links", "beidseitig"]
            seite_idx  = seite_opts.index(saved_seite) if saved_seite in seite_opts else 0
            seite_raw  = st.selectbox(
                "Seite (optional)",
                seite_opts,
                index=seite_idx,
                key=f"{key_prefix}_obs_seite",
            )
            seite = seite_raw if seite_raw != "— keine Angabe —" else None

        # ── Ausprägung (nur wenn test hat_auspraegung) ────────────────────────
        auspraegung = None
        if info["hat_auspraegung"] and selected_ids:
            ausp_opts = ["— keine Angabe —", "leicht", "mittel", "deutlich"]
            ausp_idx  = ausp_opts.index(saved_ausp) if saved_ausp in ausp_opts else 0
            ausp_raw  = st.selectbox(
                "Ausprägung (optional)",
                ausp_opts,
                index=ausp_idx,
                key=f"{key_prefix}_obs_ausp",
            )
            auspraegung = ausp_raw if ausp_raw != "— keine Angabe —" else None

        # ── Freitext ───────────────────────────────────────────────────────────
        freitext = st.text_area(
            "Zusätzliche Trainernotiz (optional)",
            value=saved_freitext or "",
            height=80,
            placeholder="Freie Beobachtungen, die nicht in den Kategorien abgedeckt sind …",
            key=f"{key_prefix}_obs_freitext",
        )

        # ── Vorschau ───────────────────────────────────────────────────────────
        preview_text = generate_observation_text(
            test_id, selected_ids, seite, auspraegung, freitext
        )
        if preview_text:
            st.markdown(
                f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
                f'padding:10px 14px;margin:8px 0">'
                f'<div style="font-size:11px;color:#8b949e;margin-bottom:4px">TEXTVORSCHAU</div>'
                f'<div style="color:#e6edf3;font-size:13px">{preview_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Buttons (nur im standalone-Modus) ────────────────────────────────
        if standalone:
            bc1, bc2, _bc3 = st.columns([2, 2, 3])
            if bc1.button("💾 Beobachtung speichern", key=f"{key_prefix}_obs_save",
                          use_container_width=True):
                beobachtung_speichern(
                    spieler_id, test_id, datum_str,
                    json.dumps(selected_ids, ensure_ascii=False),
                    seite, auspraegung,
                    freitext.strip() or None,
                    preview_text or None,
                )
                st.success("✅ Beobachtung gespeichert.")
                st.rerun()

            if bc2.button("🔄 Zurücksetzen", key=f"{key_prefix}_obs_reset",
                          use_container_width=True):
                beobachtung_loeschen(spieler_id, test_id, datum_str)
                st.info("Beobachtungen für dieses Datum gelöscht.")
                st.rerun()

            # Gespeicherter Text
            if existing and saved_text:
                with st.expander("📋 Gespeicherter Beobachtungstext"):
                    st.write(saved_text)
        else:
            # Im integrierten Modus: Hinweis dass beim Test-Speichern mitgespeichert wird
            st.caption("💡 Wird beim Speichern des Tests automatisch mitgespeichert.")

        return {
            "beob_ids": selected_ids,
            "seite": seite,
            "auspraegung": auspraegung,
            "freitext": freitext.strip() if freitext else None,
            "text_generiert": preview_text or None,
        }


def score_badge_html(score: int) -> str:
    cls = "badge-green" if score >= 75 else "badge-yellow" if score >= 50 else "badge-red"
    return f'<span class="score-badge {cls}">{score}<span style="font-size:13px;font-weight:400">/100</span></span>'


def risk_badge_html(level: str) -> str:
    cls    = {"hoch": "badge-red", "mittel": "badge-yellow", "gering": "badge-green"}.get(level, "badge-green")
    icons  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    labels = {"hoch": "HANDLUNGSBEDARF HOCH", "mittel": "HANDLUNGSBEDARF", "gering": "UNAUFFÄLLIG"}
    return f'<span class="score-badge {cls}">{icons[level]} {labels[level]}</span>'
