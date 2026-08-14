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
    verein_kapazitaet_laden,
    webhook_fehler_laden,
    webhook_fehler_loeschen,
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
        "beendet":   (_C["red"],    "Beendet"),
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
            "**support@aphsystem.de**"
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
# Tarif-Wechsel-Logik (A9)
# ══════════════════════════════════════════════════════════════════════════════

def _gleicher_kundentyp(typ_a: str, typ_b: str) -> bool:
    """True wenn beide Lizenztypen zum selben Kundentyp (Trainer / Verein) gehören."""
    def kt(t: str) -> str:
        return LIZENZ_TYPEN.get(t, {}).get("kundentyp", "")
    return kt(typ_a) == kt(typ_b)


def _ist_upgrade(aktuell: str, ziel: str) -> bool:
    """True wenn der Wechsel ein Upgrade ist (höherer Preis)."""
    preis_aktuell = LIZENZ_TYPEN.get(aktuell, {}).get("preis_monat", 0.0)
    preis_ziel    = LIZENZ_TYPEN.get(ziel,    {}).get("preis_monat", 0.0)
    return preis_ziel > preis_aktuell


def _downgrade_blockiert(
    verein_id: int,
    ziel_typ: str,
) -> tuple[bool, str]:
    """Prüft ob ein Downgrade durch bestehende Datenmenge blockiert wird.

    Rückgabe:
        (False, "")              — Downgrade erlaubt
        (True,  "Fehlermeldung") — Downgrade blockiert
    """
    from license import LIZENZ_TYPEN as _LT
    ziel_def = _LT.get(ziel_typ, {})
    max_s = ziel_def.get("max_spieler")
    max_t = ziel_def.get("max_trainer")

    try:
        kap = verein_kapazitaet_laden(verein_id)
    except Exception:
        return False, ""  # Im Zweifel erlauben, Stripe fängt echte Limits

    meldungen = []
    if max_s is not None and kap["spieler"] > max_s:
        meldungen.append(
            f"Du hast aktuell **{kap['spieler']} aktive Spieler**, "
            f"aber das Zielpaket erlaubt nur **{max_s}**."
        )
    if max_t is not None and kap["trainer"] > max_t:
        meldungen.append(
            f"Du hast aktuell **{kap['trainer']} aktive Trainer**, "
            f"aber das Zielpaket erlaubt nur **{max_t}**."
        )

    if meldungen:
        text = (
            "Downgrade nicht möglich:\n\n"
            + "\n".join(f"• {m}" for m in meldungen)
            + "\n\nBitte reduziere zuerst die Anzahl, bevor du das Paket wechselst."
        )
        return True, text

    return False, ""


def _tarif_wechseln_section(verein_id: int, info: dict, verein_row: dict) -> None:
    """UI-Abschnitt: Paket oder Abrechnungsintervall wechseln.

    info      — Rückgabe von get_lizenz_info() (LizenzInfo TypedDict)
    verein_row — Roh-DB-Row (lizenz_info_laden), enthält abo_intervall

    Ruft paket_wechseln() oder intervall_wechseln() aus stripe_service auf.
    DB-Synchronisation erfolgt ausschließlich über den Webhook.
    """
    from stripe_service import (
        hat_aktive_subscription,
        paket_wechseln,
        intervall_wechseln,
        get_price_id,
        STRIPE_PRICES,
    )

    aktuell_typ       = info.get("lizenz_typ", "TRAINER_BASIC")
    # abo_intervall kommt aus der Roh-DB-Row — LizenzInfo enthält es nicht
    aktuell_intervall = (verein_row.get("abo_intervall") or "monat")
    sub_id            = info.get("stripe_subscription_id")

    # ── Kein aktives Stripe-Abo ────────────────────────────────────────────────
    if not stripe_verfuegbar():
        st.info(
            "Stripe ist nicht konfiguriert. Kontaktiere uns für einen Tarifwechsel: "
            "**support@aphsystem.de**"
        )
        return

    hat_abo, _ = hat_aktive_subscription(verein_id)
    if not hat_abo or not sub_id:
        st.info(
            "Kein aktives Stripe-Abonnement gefunden. "
            "Starte zunächst ein Abonnement über den Tab **📦 Tarife**."
        )
        return

    aktuell_def = LIZENZ_TYPEN.get(aktuell_typ, LIZENZ_TYPEN["TRAINER_BASIC"])

    # ── Mögliche Ziel-Pakete (nur gleicher Kundentyp, nicht aktueller Tarif) ──
    erlaubte_ziele = [
        (k, v) for k, v in LIZENZ_TYPEN.items()
        if k != aktuell_typ and _gleicher_kundentyp(k, aktuell_typ)
    ]

    if not erlaubte_ziele:
        st.info("Für deinen Kundentyp gibt es derzeit kein anderes Paket.")
        return

    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:8px;padding:14px 18px;margin-bottom:16px">'
        f'<div style="font-size:11px;color:{_C["muted"]};letter-spacing:.6px">AKTUELLES PAKET</div>'
        f'<div style="font-size:18px;font-weight:800;color:{_C["text"]};margin-top:2px">'
        f'{aktuell_def["label"]}</div>'
        f'<div style="font-size:12px;color:{_C["muted"]};margin-top:4px">'
        f'Intervall: {"Monatlich" if aktuell_intervall == "monat" else "Jährlich"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Paket wählen ──────────────────────────────────────────────────────────
    ziel_labels = {k: v["label"] for k, v in erlaubte_ziele}
    ziel_keys   = list(ziel_labels.keys())

    col_paket, col_intervall = st.columns(2)

    with col_paket:
        ziel_typ = st.selectbox(
            "Neues Paket",
            options=ziel_keys,
            format_func=lambda k: ziel_labels[k],
            key="wechsel_paket",
        )

    with col_intervall:
        intervall_wahl = st.selectbox(
            "Abrechnungsintervall",
            options=["monat", "jahr"],
            format_func=lambda x: "Monatlich" if x == "monat" else "Jährlich (2 Monate gratis)",
            index=0 if aktuell_intervall == "monat" else 1,
            key="wechsel_intervall",
        )

    # ── Wechsel-Art bestimmen ──────────────────────────────────────────────────
    paket_aendert    = (ziel_typ != aktuell_typ)
    intervall_aendert = (intervall_wahl != aktuell_intervall)

    if not paket_aendert and not intervall_aendert:
        st.info("Keine Änderung ausgewählt — wähle ein anderes Paket oder Intervall.")
        return

    neue_price_id = get_price_id(ziel_typ, intervall_wahl)
    if not neue_price_id:
        st.warning(
            f"Stripe Price-ID für **{LIZENZ_TYPEN[ziel_typ]['label']} / "
            f"{'Monatlich' if intervall_wahl == 'monat' else 'Jährlich'}** ist noch nicht "
            f"konfiguriert. Bitte Env-Var setzen."
        )
        return

    # ── Vorschau der Änderung ──────────────────────────────────────────────────
    ist_upgrade   = paket_aendert and _ist_upgrade(aktuell_typ, ziel_typ)
    ist_downgrade = paket_aendert and not ist_upgrade

    aendert_str = []
    if paket_aendert:
        richtung = "⬆️ Upgrade" if ist_upgrade else "⬇️ Downgrade"
        aendert_str.append(
            f"{richtung}: **{aktuell_def['label']}** → **{LIZENZ_TYPEN[ziel_typ]['label']}**"
        )
    if intervall_aendert:
        alt_int = "Monatlich" if aktuell_intervall == "monat" else "Jährlich"
        neu_int = "Monatlich" if intervall_wahl == "monat" else "Jährlich"
        aendert_str.append(f"Intervall: {alt_int} → {neu_int}")

    if ist_upgrade:
        wirksamkeit = "**sofort** (mit anteiliger Abrechnung über Stripe)"
    else:
        wirksamkeit = "**zum Ende des aktuellen Abrechnungszeitraums**"

    st.markdown(
        f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
        f'border-radius:8px;padding:14px 18px;margin:12px 0">'
        f'<div style="font-size:11px;color:{_C["muted"]};letter-spacing:.6px;margin-bottom:6px">VORSCHAU DER ÄNDERUNG</div>'
        + "".join(
            f'<div style="font-size:13px;color:{_C["text"]};margin-bottom:3px">• {t}</div>'
            for t in aendert_str
        )
        + f'<div style="font-size:12px;color:{_C["muted"]};margin-top:8px">'
        f'Wirksam: {wirksamkeit}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Downgrade-Limit-Check ──────────────────────────────────────────────────
    if ist_downgrade:
        blockiert, grund = _downgrade_blockiert(verein_id, ziel_typ)
        if blockiert:
            st.error(grund)
            return

    # ── Bestätigungs-Schritt ───────────────────────────────────────────────────
    confirm_key = f"wechsel_bestaetigt_{ziel_typ}_{intervall_wahl}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    if not st.session_state[confirm_key]:
        st.warning(
            "Bitte bestätige die Änderung. "
            "Du kannst deinen Tarif jederzeit erneut wechseln."
        )
        if st.button(
            "✅ Änderung bestätigen",
            key=f"bestaetigen_{ziel_typ}_{intervall_wahl}",
            type="primary",
        ):
            st.session_state[confirm_key] = True
            st.rerun()
        return

    # ── Wechsel durchführen ────────────────────────────────────────────────────
    st.success("Bereit zum Wechseln. Klicke unten um die Änderung an Stripe zu übermitteln.")

    if st.button(
        f"🔄 Jetzt wechseln",
        key=f"wechsel_ausfuehren_{ziel_typ}_{intervall_wahl}",
        type="primary",
        use_container_width=True,
    ):
        try:
            if ist_upgrade:
                paket_wechseln(sub_id, neue_price_id, sofort=True)
            elif ist_downgrade:
                paket_wechseln(sub_id, neue_price_id, sofort=False)
            else:
                # Nur Intervallwechsel
                intervall_wechseln(sub_id, neue_price_id)

            # Bestätigungs-State zurücksetzen
            del st.session_state[confirm_key]
            invalidate_lizenz_cache(verein_id)

            st.success(
                "✅ Wechsel erfolgreich an Stripe übermittelt! "
                "Die Lizenzseite wird nach dem nächsten Webhook-Event automatisch aktualisiert."
            )
        except Exception as e:
            st.error(f"Fehler beim Tarifwechsel: {e}")
            del st.session_state[confirm_key]


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
    typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["TRAINER_BASIC"])

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
    tab_tarife, tab_wechseln, tab_rechnungen = st.tabs(
        ["📦 Tarife", "🔄 Tarif wechseln", "🧾 Rechnungen"]
    )

    with tab_tarife:
        st.markdown(
            f'<p style="color:{_C["muted"]};font-size:13px;margin-bottom:16px">'
            'Vergleiche die verfügbaren Tarife. Für Upgrades wende dich an '
            '<a href="mailto:support@aphsystem.de" style="color:{}">'
            'support@aphsystem.de</a>.</p>'.format(_C["blue"]),
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

        # Kündigung — Verweis auf "Mein Vertrag" Seite
        if info["lizenz_status"] in ("active", "trial") and not info.get("stripe_subscription_id"):
            st.markdown("---")
            st.info(
                "Möchtest du deinen Vertrag kündigen? "
                "Nutze dafür die Seite **📋 Mein Vertrag** in der Navigation."
            )

    with tab_wechseln:
        _tarif_wechseln_section(verein_id, info, verein_row)

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
            ["Alle", "trial", "active", "expired", "suspended", "cancelled", "beendet"],
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
            f"{'Abgelaufen' if info['lizenz_status'] in ('expired', 'suspended', 'beendet') else (str(tage) + ' Tage' if tage is not None else '—')}",
            expanded=False,
        ):
            r1c1, r1c2 = st.columns([2, 2])

            with r1c1:
                _zahlung_st = info.get("zahlungsstatus") or v.get("zahlungsstatus") or "—"
                _lzf = v.get("letzte_zahlung_fehlgeschlagen") or ""
                _zahlung_fehlgeschlagen = _zahlung_st == "fehlgeschlagen"
                _zahlung_badge = (
                    f'<span style="display:inline-block;margin-left:8px;padding:1px 8px;'
                    f'border-radius:10px;background:{_C["red"]}22;color:{_C["red"]};'
                    f'font-size:11px;font-weight:700;border:1px solid {_C["red"]}44">'
                    f'⚠ Zahlung fehlgeschlagen</span>'
                ) if _zahlung_fehlgeschlagen else ""
                _lzf_hint = (
                    f' · Letzter Fehlschlag: <span style="color:{_C["red"]}">'
                    f'{_lzf[:16].replace("T", " ")}</span>'
                ) if _zahlung_fehlgeschlagen and _lzf else ""
                st.markdown(
                    f"{badge}{_zahlung_badge} "
                    f'<span style="color:{_C["muted"]};font-size:12px">'
                    f"Ablauf: {ablauf.strftime('%d.%m.%Y') if ablauf else '—'} · "
                    f"Zahlung: {_zahlung_st}{_lzf_hint}</span>",
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
                _sa_statuses = ["trial", "active", "expired", "suspended", "cancelled", "beendet"]
                neuer_status = st.selectbox(
                    "Status",
                    _sa_statuses,
                    index=_sa_statuses.index(info["lizenz_status"])
                          if info["lizenz_status"] in _sa_statuses else 0,
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

            # ── Stripe-Kündigungsfelder ────────────────────────────────────
            _cap_val = v.get("cancel_at_period_end")
            _kuend_st = v.get("kuendigungsstatus") or "—"
            _gek_zum  = v.get("gekuendigt_zum") or "—"
            _kuend_ein = v.get("kuendigung_eingegangen") or "—"
            if _cap_val or _kuend_st not in ("aktiv", "—", None):
                st.markdown(
                    f'<div style="background:{_C["surf"]};border:1px solid {_C["border"]};'
                    f'border-radius:6px;padding:10px 14px;margin-top:10px">'
                    f'<div style="font-size:11px;font-weight:700;color:{_C["orange"]};margin-bottom:6px">🔔 Kündigung</div>'
                    f'<div style="font-size:11px;color:{_C["muted"]}">Status: '
                    f'<span style="color:{_C["text"]}">{_kuend_st}</span></div>'
                    f'<div style="font-size:11px;color:{_C["muted"]}">cancel_at_period_end: '
                    f'<span style="color:{_C["text"]}">{"✅ Ja" if _cap_val else "Nein"}</span></div>'
                    f'<div style="font-size:11px;color:{_C["muted"]}">Vertragsende: '
                    f'<span style="color:{_C["text"]}">{_gek_zum}</span></div>'
                    f'<div style="font-size:11px;color:{_C["muted"]}">Kündigung eingegangen: '
                    f'<span style="color:{_C["text"]}">{_kuend_ein[:10] if _kuend_ein != "—" else "—"}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Rechnungen ─────────────────────────────────────────────────
            rechnungen = rechnungen_laden(v["id"])
            if rechnungen:
                st.markdown(
                    f'<div style="font-size:11px;color:{_C["muted"]};margin-top:8px">'
                    f'{len(rechnungen)} Rechnung(en) vorhanden</div>',
                    unsafe_allow_html=True,
                )

    # ── Webhook-Fehler-Log ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<h3 style="color:{_C["orange"]};font-size:16px;font-weight:700;margin-bottom:8px">'
        f'⚠ Stripe Webhook-Fehler</h3>',
        unsafe_allow_html=True,
    )

    fehler_liste = webhook_fehler_laden(limit=50)

    if not fehler_liste:
        st.markdown(
            f'<div style="color:{_C["green"]};font-size:13px">✅ Keine fehlerhaften Webhook-Events vorhanden.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Aufschlüsselung nach Fehlertyp
        sig_fehler   = [f for f in fehler_liste if "Signaturprüfung" in f.get("fehlergrund", "")]
        price_fehler = [f for f in fehler_liste if "Price-ID" in f.get("fehlergrund", "")]
        zahlung_fehler = [f for f in fehler_liste if "Zahlung fehlgeschlagen" in f.get("fehlergrund", "")]
        sonstige     = [f for f in fehler_liste
                        if f not in sig_fehler and f not in price_fehler and f not in zahlung_fehler]

        kf1, kf2, kf3, kf4 = st.columns(4)
        with kf1:
            _kpi("Signaturprüfung", str(len(sig_fehler)), _C["red"] if sig_fehler else _C["muted"])
        with kf2:
            _kpi("Unbekannte Price-ID", str(len(price_fehler)), _C["orange"] if price_fehler else _C["muted"])
        with kf3:
            _kpi("Zahlung fehlgeschlagen", str(len(zahlung_fehler)), _C["orange"] if zahlung_fehler else _C["muted"])
        with kf4:
            _kpi("Sonstige Fehler", str(len(sonstige)), _C["red"] if sonstige else _C["muted"])

        st.markdown("")

        import pandas as pd
        df_fehler = pd.DataFrame(fehler_liste)
        df_fehler = df_fehler.rename(columns={
            "id":          "ID",
            "event_id":    "Event-ID",
            "event_type":  "Event-Typ",
            "fehlergrund": "Fehlergrund",
            "zeitstempel": "Zeitstempel",
        })
        anzeige_cols = [c for c in ["Zeitstempel", "Event-Typ", "Fehlergrund", "Event-ID"] if c in df_fehler.columns]
        st.dataframe(
            df_fehler[anzeige_cols],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("")
        if st.button(
            "🗑 Alle Webhook-Fehler löschen",
            key="webhook_fehler_loeschen_btn",
            help="Löscht alle gespeicherten Webhook-Fehler aus der Datenbank.",
        ):
            anzahl = webhook_fehler_loeschen()
            st.success(f"✅ {anzahl} Webhook-Fehler gelöscht.")
            st.rerun()
