"""
Lizenz-Seite — Bruce Football Performance Diagnostics.

Vereinsadmin: aktueller Tarif, Testphase, Upgrade, Kündigung.
Superadmin: Alle Vereine verwalten (Lizenz ändern, sperren, etc.)
"""

from __future__ import annotations

import datetime
import streamlit as st

from database import (
    lizenz_info_laden,
    lizenz_setzen,
    verein_sperren as db_verein_sperren,
    testphase_verlaengern,
    rechnungen_laden,
    alle_vereine_lizenz,
    stripe_ids_setzen,
)
from license import (
    LIZENZ_TYPEN,
    TESTPHASE_TAGE,
    get_lizenz_info,
    invalidate_lizenz_cache,
)
from stripe_service import stripe_verfuegbar

# ── Design-Konstanten ──────────────────────────────────────────────────────────
_C = {
    "bg":     "rgba(0,0,0,0)",
    "surf":   "#161b22",
    "border": "#30363d",
    "text":   "#e6edf3",
    "muted":  "#8b949e",
    "green":  "#3fb950",
    "blue":   "#58a6ff",
    "orange": "#d29922",
    "red":    "#f85149",
    "purple": "#bc8cff",
}


def _status_badge(status: str) -> str:
    farben = {
        "trial":     (_C["blue"],   "Testphase"),
        "active":    (_C["green"],  "Aktiv"),
        "expired":   (_C["red"],    "Abgelaufen"),
        "suspended": (_C["red"],    "Gesperrt"),
        "cancelled": (_C["orange"], "Gekündigt"),
    }
    color, label = farben.get(status, (_C["muted"], status.capitalize()))
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;'
        f'background:{color}22;color:{color};font-size:12px;font-weight:700;'
        f'border:1px solid {color}44">{label}</span>'
    )


def _kpi(label: str, value: str, color: str = "#58a6ff", sub: str = "") -> None:
    sub_html = f'<div style="font-size:10px;color:{_C["muted"]};margin-top:2px">{sub}</div>' if sub else ""
    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:8px;padding:16px 18px;text-align:center">'
        f'<div style="font-size:10px;color:{_C["muted"]};letter-spacing:.8px;margin-bottom:6px">{label.upper()}</div>'
        f'<div style="font-size:26px;font-weight:800;color:{color};line-height:1">{value}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def _stripe_upgrade(typ_key: str, verein_id: int, info: dict) -> None:
    """Leitet zum Stripe-Checkout weiter oder zeigt Fallback-Kontakt."""
    from stripe_service import stripe_verfuegbar, customer_erstellen, checkout_session_erstellen
    from database import stripe_ids_setzen
    from license import LIZENZ_TYPEN

    typ_def = LIZENZ_TYPEN.get(typ_key, {})

    if not stripe_verfuegbar():
        st.info(
            f"Für einen Wechsel auf **{typ_def.get('label', typ_key)}** kontaktiere uns bitte: "
            "**Broska_daroish@hotmail.de** · Tel. 01741682671"
        )
        return

    # Periodenauswahl
    col1, col2 = st.columns(2)
    with col1:
        periode = st.radio(
            "Abrechnungszeitraum",
            ["Monatlich", "Jährlich (2 Monate gratis)"],
            key=f"periode_{typ_key}",
            horizontal=True,
        )
    periode_key = "monat" if periode == "Monatlich" else "jahr"
    price_id = typ_def.get(f"stripe_price_{periode_key}", "")

    if not price_id:
        st.warning("Stripe-Price-ID noch nicht konfiguriert. Bitte Env-Var setzen.")
        return

    if st.button(
        f"💳 Jetzt auf {typ_def.get('label', typ_key)} upgraden",
        key=f"checkout_{typ_key}_{periode_key}",
        type="primary",
        use_container_width=True,
    ):
        try:
            # Stripe-Kunden anlegen oder vorhandene ID nutzen
            customer_id = info.get("stripe_customer_id")
            if not customer_id:
                user = st.session_state.get("user", {})
                customer_id = customer_erstellen(
                    email=user.get("email", ""),
                    name=user.get("name", ""),
                    verein_id=verein_id,
                )
                stripe_ids_setzen(verein_id, customer_id=customer_id)

            checkout_url = checkout_session_erstellen(
                customer_id=customer_id,
                price_id=price_id,
                verein_id=verein_id,
            )
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={checkout_url}">'
                f'<p>Weiterleitung zu Stripe… '
                f'<a href="{checkout_url}" target="_blank">Hier klicken</a></p>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Checkout-Session: {e}")


def _tarif_karte(
    typ_key: str,
    typ_def: dict,
    ist_aktuell: bool = False,
    on_upgrade=None,
) -> None:
    border = _C["green"] if ist_aktuell else _C["border"]
    badge  = ('<span style="background:#3fb95022;color:#3fb950;font-size:10px;'
              'font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px">'
              'AKTUELL</span>') if ist_aktuell else ""

    feats = typ_def["features"]
    feat_html = ""
    from license import FEATURE_LABELS as feat_labels
    for f in feats:
        feat_html += f'<div style="font-size:12px;color:{_C["muted"]};margin-bottom:3px">✓ {feat_labels.get(f, f)}</div>'

    preis_html = (
        f'<div style="font-size:22px;font-weight:800;color:{_C["text"]}">'
        f'{typ_def["preis_monat"]:.2f} €<span style="font-size:12px;font-weight:400;color:{_C["muted"]}"> / Monat</span></div>'
        f'<div style="font-size:11px;color:{_C["muted"]};margin-bottom:12px">'
        f'oder {typ_def["preis_jahr"]:.0f} € / Jahr</div>'
    )

    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {border};border-radius:10px;padding:20px 22px;height:100%">'
        f'<div style="font-size:14px;font-weight:700;color:{_C["text"]};margin-bottom:4px">'
        f'{typ_def["label"]}{badge}</div>'
        f'<div style="font-size:11px;color:{_C["muted"]};margin-bottom:8px">'
        f'Max. {typ_def["max_trainer"]} Trainer · {typ_def["max_spieler"]} Spieler</div>'
        f'{preis_html}{feat_html}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    if not ist_aktuell and on_upgrade and typ_def["preis_monat"] > 0:
        if st.button(f"Auf {typ_def['label']} wechseln", key=f"upgrade_{typ_key}", use_container_width=True):
            on_upgrade(typ_key)


# ══════════════════════════════════════════════════════════════════════════════
# Vereinsadmin-Seite
# ══════════════════════════════════════════════════════════════════════════════

def page_lizenz_vereinsadmin() -> None:
    """Lizenz-Seite für Vereinsadmin."""
    from session_timeout import touch_session
    touch_session()

    user     = st.session_state.get("user", {})
    verein_id = user.get("verein_id")

    st.markdown(
        '<h2 style="color:#e6edf3;font-size:22px;font-weight:700;margin-bottom:4px">Lizenz & Abonnement</h2>',
        unsafe_allow_html=True,
    )

    # ── Aktuellen Status laden ─────────────────────────────────────────────────
    verein_row = lizenz_info_laden(verein_id) or {}
    info = get_lizenz_info(verein_row)
    typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["BASIC"])

    # ── Status-Banner ──────────────────────────────────────────────────────────
    badge = _status_badge(info["lizenz_status"])
    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:10px;padding:18px 22px;margin-bottom:18px;display:flex;'
        f'align-items:center;justify-content:space-between">'
        f'<div><div style="font-size:13px;color:{_C["muted"]};margin-bottom:4px">Aktueller Tarif</div>'
        f'<div style="font-size:20px;font-weight:800;color:{_C["text"]}">{typ_def["label"]} {badge}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPI-Kacheln ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tage = info.get("tage_verbleibend")
        if tage is None:
            _kpi("Verbleibend", "—", _C["muted"])
        elif tage <= 0:
            _kpi("Verbleibend", "Abgelaufen", _C["red"])
        elif tage <= 7:
            _kpi("Verbleibend", f"{tage} Tage", _C["orange"], "Bald ablaufend")
        else:
            label = "Testtage" if info["lizenz_status"] == "trial" else "Tage"
            _kpi(label, str(tage), _C["green"])

    with c2:
        ablauf = info.get("ablauf_datum")
        _kpi("Ablaufdatum",
             ablauf.strftime("%d.%m.%Y") if ablauf else "—",
             _C["muted"] if not ablauf else _C["text"])

    with c3:
        _kpi("Rechnungsstatus",
             info["zahlungsstatus"].capitalize(),
             _C["green"] if info["zahlungsstatus"] == "bezahlt" else _C["orange"])

    with c4:
        _kpi("Max. Spieler",
             str(typ_def["max_spieler"]),
             _C["blue"],
             f"Max. {typ_def['max_trainer']} Trainer")

    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_tarife, tab_rechnungen = st.tabs(["📦 Tarife", "🧾 Rechnungen"])

    with tab_tarife:
        st.markdown(
            f'<p style="color:{_C["muted"]};font-size:13px;margin-bottom:16px">'
            'Vergleiche die verfügbaren Tarife. Für Upgrades oder Kündigungen '
            'wende dich an <a href="mailto:support@brucefootball.de" style="color:{}">'
            'support@brucefootball.de</a>.</p>'.format(_C["blue"]),
            unsafe_allow_html=True,
        )

        cols = st.columns(2)
        for i, (typ_key, typ_def_iter) in enumerate(LIZENZ_TYPEN.items()):
            with cols[i]:
                def _on_upgrade(key=typ_key, vid=verein_id, vinfo=info):
                    _stripe_upgrade(key, vid, vinfo)
                _tarif_karte(
                    typ_key,
                    typ_def_iter,
                    ist_aktuell=(typ_key == info["lizenz_typ"]),
                    on_upgrade=_on_upgrade,
                )

        # Stripe Billing-Portal (wenn verfügbar)
        if stripe_verfuegbar() and info.get("stripe_customer_id"):
            st.markdown("---")
            st.markdown(
                f'<p style="color:{_C["muted"]};font-size:12px">'
                '⚡ Verwalte dein Abonnement direkt über das Stripe-Portal (Upgrade, Downgrade, Kündigung, Rechnungen).</p>',
                unsafe_allow_html=True,
            )
            if st.button("🔗 Stripe-Abrechnungsportal öffnen", type="primary"):
                try:
                    from stripe_service import billing_portal_erstellen
                    url = billing_portal_erstellen(info["stripe_customer_id"])
                    st.markdown(
                        f'<a href="{url}" target="_blank" style="color:{_C["blue"]}">→ Zum Portal</a>',
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Fehler beim Öffnen des Portals: {e}")

        # Kündigung (ohne Stripe)
        if info["lizenz_status"] in ("active", "trial") and not info.get("stripe_subscription_id"):
            st.markdown("---")
            with st.expander("⚠ Lizenz kündigen"):
                st.warning(
                    "Nach der Kündigung läuft die Lizenz bis zum Ablaufdatum weiter. "
                    "Danach ist kein Zugriff mehr möglich."
                )
                if st.button("Kündigung beantragen", type="secondary"):
                    st.info(
                        "Bitte sende eine E-Mail an: "
                        "**kuendigung@brucefootball.de** mit deiner Vereins-E-Mail."
                    )

    with tab_rechnungen:
        rechnungen = rechnungen_laden(verein_id)
        if not rechnungen:
            st.info("Noch keine Rechnungen vorhanden.")
        else:
            import pandas as pd
            df = pd.DataFrame(rechnungen)
            cols_map = {
                "rechnungsnummer": "Rechnungsnr.",
                "rechnungsdatum":  "Datum",
                "betrag_eur":      "Betrag (€)",
                "lizenz_typ":      "Tarif",
                "status":          "Status",
                "lizenz_von":      "Von",
                "lizenz_bis_r":    "Bis",
            }
            df = df.rename(columns=cols_map)
            anzeige_cols = [c for c in cols_map.values() if c in df.columns]
            st.dataframe(df[anzeige_cols], use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# Superadmin-Lizenz-Dashboard
# ══════════════════════════════════════════════════════════════════════════════

def page_lizenz_superadmin() -> None:
    """Lizenz-Verwaltung für Superadmin — alle Vereine im Überblick."""
    from session_timeout import touch_session
    touch_session()

    st.markdown(
        '<h2 style="color:#e6edf3;font-size:22px;font-weight:700;margin-bottom:4px">Lizenz-Verwaltung</h2>',
        unsafe_allow_html=True,
    )

    vereine = alle_vereine_lizenz()

    # ── KPI-Kacheln oben ──────────────────────────────────────────────────────
    total      = len(vereine)
    aktiv_n    = sum(1 for v in vereine if v.get("lizenz_status") == "active")
    trial_n    = sum(1 for v in vereine if v.get("lizenz_status") == "trial")
    expired_n  = sum(1 for v in vereine if v.get("lizenz_status") in ("expired", "suspended"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("Gesamt",     str(total),    _C["blue"])
    with c2: _kpi("Aktiv",      str(aktiv_n),  _C["green"])
    with c3: _kpi("Testphase",  str(trial_n),  _C["orange"])
    with c4: _kpi("Abgelaufen", str(expired_n),_C["red"])

    st.markdown("")

    # ── Filter ────────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        filter_status = st.selectbox(
            "Status filtern",
            ["Alle", "trial", "active", "expired", "suspended", "cancelled"],
            key="lizenz_sa_filter",
        )
    with col_f2:
        suche = st.text_input("Verein suchen", placeholder="Vereinsname...", key="lizenz_sa_suche")

    # ── Vereine-Tabelle mit Aktionen ──────────────────────────────────────────
    for v in vereine:
        info = get_lizenz_info(v)

        # Filtern
        if filter_status != "Alle" and info["lizenz_status"] != filter_status:
            continue
        if suche and suche.lower() not in (v.get("name") or "").lower():
            continue

        tage    = info.get("tage_verbleibend")
        ablauf  = info.get("ablauf_datum")
        badge   = _status_badge(info["lizenz_status"])
        typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["BASIC"])

        with st.expander(
            f"{v.get('name', '—')}  |  {typ_def['label']}  |  "
            f"{'Abgelaufen' if info['lizenz_status'] in ('expired', 'suspended') else (str(tage) + ' Tage' if tage is not None else '—')}",
            expanded=False,
        ):
            r1c1, r1c2 = st.columns([2, 2])

            with r1c1:
                st.markdown(
                    f"{badge} "
                    f'<span style="color:{_C["muted"]};font-size:12px">'
                    f"Ablauf: {ablauf.strftime('%d.%m.%Y') if ablauf else '—'} · "
                    f"Zahlung: {info['zahlungsstatus']}</span>",
                    unsafe_allow_html=True,
                )

            with r1c2:
                gesperrt_label = "🔓 Entsperren" if info["gesperrt"] else "🚫 Sperren"
                if st.button(gesperrt_label, key=f"sperren_{v['id']}"):
                    db_verein_sperren(v["id"], not info["gesperrt"])
                    invalidate_lizenz_cache(v["id"])
                    st.rerun()

            st.markdown("")

            # ── Lizenz bearbeiten ──────────────────────────────────────────
            ed_c1, ed_c2, ed_c3, ed_c4 = st.columns(4)
            with ed_c1:
                neuer_typ = st.selectbox(
                    "Lizenztyp",
                    list(LIZENZ_TYPEN.keys()),
                    index=list(LIZENZ_TYPEN.keys()).index(info["lizenz_typ"]),
                    key=f"typ_{v['id']}",
                )
            with ed_c2:
                neuer_status = st.selectbox(
                    "Status",
                    ["trial", "active", "expired", "suspended", "cancelled"],
                    index=["trial","active","expired","suspended","cancelled"].index(
                        info["lizenz_status"] if info["lizenz_status"] in
                        ["trial","active","expired","suspended","cancelled"] else "trial"
                    ),
                    key=f"status_{v['id']}",
                )
            with ed_c3:
                ablauf_input = st.date_input(
                    "Lizenz bis",
                    value=ablauf or datetime.date.today() + datetime.timedelta(days=30),
                    key=f"ablauf_{v['id']}",
                )
            with ed_c4:
                extra_tage = st.number_input(
                    "Testphase (+Tage)",
                    min_value=0, max_value=365, value=0,
                    key=f"extra_{v['id']}",
                    help="Fügt diese Tage zur bestehenden Testphase hinzu",
                )

            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button("💾 Lizenz speichern", key=f"save_{v['id']}", type="primary",
                             use_container_width=True):
                    lizenz_setzen(
                        verein_id=v["id"],
                        lizenz_typ=neuer_typ,
                        lizenz_status=neuer_status,
                        lizenz_bis=ablauf_input.isoformat(),
                    )
                    if extra_tage > 0:
                        testphase_verlaengern(v["id"], extra_tage)
                    invalidate_lizenz_cache(v["id"])
                    st.success(f"✅ Lizenz für **{v['name']}** aktualisiert.")
                    st.rerun()
            with btn_c2:
                if extra_tage > 0:
                    if st.button(f"⏱ Testphase +{extra_tage}d", key=f"tp_{v['id']}",
                                 use_container_width=True):
                        testphase_verlaengern(v["id"], extra_tage)
                        invalidate_lizenz_cache(v["id"])
                        st.success(f"Testphase um {extra_tage} Tage verlängert.")
                        st.rerun()

            # ── Rechnungen ─────────────────────────────────────────────────
            rechnungen = rechnungen_laden(v["id"])
            if rechnungen:
                st.markdown(
                    f'<div style="font-size:11px;color:{_C["muted"]};margin-top:8px">'
                    f'{len(rechnungen)} Rechnung(en) vorhanden</div>',
                    unsafe_allow_html=True,
                )
