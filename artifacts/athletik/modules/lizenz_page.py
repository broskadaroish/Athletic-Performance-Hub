"""
Lizenz-Seite — Bruce Football Performance Diagnostics.

Vereinsadmin: aktueller Tarif, Testphase, Upgrade, Kündigung.
Superadmin: Alle Vereine verwalten (Lizenz ändern, sperren, etc.)
"""

from __future__ import annotations

import datetime
import logging
import streamlit as st

from database import (
    lizenz_info_laden,
    lizenz_setzen,
    trainer_lizenz_setzen,
    verein_sperren as db_verein_sperren,
    testphase_verlaengern,
    rechnungen_laden,
    alle_vereine_lizenz,
    alle_trainer_lizenz,
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

_log = logging.getLogger("athletik.stripe_upgrade")

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
        "geloescht": (_C["muted"],  "Gelöscht"),
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


def _limit_label(value: int | None) -> str:
    """Formatiert ein Paketlimit ohne Python-None in der sichtbaren UI."""
    return "unbegrenzt" if value is None else str(value)


_UPGRADE_TARGET_KEY = "_aph_upgrade_target"


def _upgrade_target_setzen(key: str, state: dict | None = None) -> None:
    """Merkt das vom Nutzer gewählte Zielpaket über Streamlit-Reruns hinweg."""
    ziel_state = st.session_state if state is None else state
    if key in LIZENZ_TYPEN and LIZENZ_TYPEN[key].get("preis_monat", 0) > 0:
        ziel_state[_UPGRADE_TARGET_KEY] = key


def _upgrade_target_laden(state: dict | None = None) -> str | None:
    """Liest nur ein gültiges, kostenpflichtiges Upgrade-Ziel aus dem State."""
    ziel_state = st.session_state if state is None else state
    key = ziel_state.get(_UPGRADE_TARGET_KEY)
    if key in LIZENZ_TYPEN and LIZENZ_TYPEN[key].get("preis_monat", 0) > 0:
        return key
    return None


def _upgrade_periode_key(label: str) -> str:
    """Übersetzt die sichtbare Intervallauswahl in den kanonischen State-Wert."""
    return "monat" if label == "Monatlich" else "jahr"


def _stripe_upgrade(typ_key: str, verein_id: int, info: dict) -> None:
    """Zeigt den stabilen Zeitraum- und Checkout-Schritt für ein Upgrade."""
    from stripe_service import (
        stripe_verfuegbar,
        customer_erstellen,
        checkout_session_erstellen,
        get_price_id,
    )
    from database import stripe_ids_setzen
    from license import LIZENZ_TYPEN

    typ_def = LIZENZ_TYPEN.get(typ_key, {})
    if typ_key == "STARTER_FREE":
        st.info(
            "Die Starter-Testphase ist einmalig und löst keinen Stripe-Vorgang aus. "
            "Wähle nach Ablauf deiner Testphase ein reguläres Paket."
        )
        return
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
            key=f"upgrade_periode_{typ_key}",
            horizontal=True,
        )
    periode_key = _upgrade_periode_key(periode)
    try:
        price_id = get_price_id(typ_key, periode_key)
    except (TypeError, ValueError):
        price_id = None

    if not price_id:
        st.warning("Stripe-Price-ID noch nicht konfiguriert. Bitte Env-Var setzen.")
        return

    if st.button(
        f"💳 Jetzt auf {typ_def.get('label', typ_key)} upgraden",
        key=f"checkout_{typ_key}",
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
                lizenztyp=typ_key,
                abo_intervall=periode_key,
            )
            if not checkout_url:
                raise RuntimeError("Stripe hat keine Checkout-URL zurückgegeben.")
            st.success("Checkout wurde vorbereitet. Öffne jetzt den sicheren Stripe-Zahlungsdialog.")
            st.link_button(
                "→ Zu Stripe Checkout",
                checkout_url,
                type="primary",
                use_container_width=True,
            )
        except Exception:
            _log.exception(
                "Stripe-Checkout konnte nicht gestartet werden: verein_id=%s tarif=%s intervall=%s",
                verein_id,
                typ_key,
                periode_key,
            )
            st.error(
                "Der Zahlungsvorgang konnte nicht gestartet werden. "
                "Bitte versuche es erneut."
            )


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
        f'Max. {_limit_label(typ_def.get("max_trainer"))} Trainer · '
        f'{_limit_label(typ_def.get("max_spieler"))} Spieler</div>'
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
            with cols[i % len(cols)]:
                def _on_upgrade(key=typ_key, vid=verein_id, vinfo=info):
                    _upgrade_target_setzen(key)
                _tarif_karte(
                    typ_key,
                    typ_def_iter,
                    ist_aktuell=(typ_key == info["lizenz_typ"]),
                    on_upgrade=_on_upgrade,
                )

        _selected_upgrade = _upgrade_target_laden()
        if _selected_upgrade:
            _stripe_upgrade(_selected_upgrade, verein_id, info)

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
        if info["lizenz_typ"] == "STARTER_FREE" and info["lizenz_status"] == "trial":
            st.info(
                "Starter ist eine einmalige 30-Tage-Testphase. "
                "Du kannst den Zugang weiter nutzen oder jederzeit unter "
                "**Tarife** auf ein reguläres Paket upgraden."
            )
        elif info["lizenz_typ"] == "STARTER_FREE":
            st.info(
                "Deine Starter-Testphase ist abgelaufen. Wähle oben unter "
                "**Tarife** ein reguläres Paket, um deinen Zugang zu aktivieren."
            )
        else:
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
# Superadmin-Lizenz-Dashboard  —  Helpers
# ══════════════════════════════════════════════════════════════════════════════

_SA_STATUS_ORDER: dict[str, int] = {
    "bald_abgelaufen": 0,
    "aktiv":           1,
    "testphase":       2,
    "abgelaufen":      3,
    "gesperrt":        4,
    "archiviert":      5,
}

# (Hintergrundfarbe, Textfarbe, Label)
_SA_BADGE_DEF: dict[str, tuple[str, str, str]] = {
    "aktiv":           (_C["green"]  + "22", _C["green"],  "🟢 Aktiv"),
    "testphase":       (_C["blue"]   + "22", _C["blue"],   "🔵 Testphase"),
    "bald_abgelaufen": (_C["orange"] + "22", _C["orange"], "🟠 Läuft bald ab"),
    "abgelaufen":      (_C["red"]    + "22", _C["red"],    "🔴 Abgelaufen"),
    "gesperrt":        (_C["red"]    + "22", _C["red"],    "🔴 Gesperrt"),
    "archiviert":      ("#6e768122",         "#6e7681",    "⚪ Archiviert"),
}

_SA_STATUS_ALLE = ["trial", "active", "expired", "suspended", "cancelled", "beendet"]
_30_TAGE = 30  # einheitlicher Schwellenwert für „läuft bald ab"


def _sa_badge_html(display_status: str) -> str:
    bg, color, label = _SA_BADGE_DEF.get(display_status, ("#6e768122", "#6e7681", display_status))
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        f'background:{bg};color:{color};font-size:11px;font-weight:700;'
        f'border:1px solid {color}55;white-space:nowrap">{label}</span>'
    )


def _sa_display_status(row: dict) -> str:
    """Berechnet den normierten Anzeige-Status aus rohem lizenz_status + lizenz_bis."""
    s = (row.get("lizenz_status") or "").lower()
    if s in ("cancelled", "beendet"):
        return "archiviert"
    if s == "geloescht":
        return "archiviert"
    if s == "expired":
        return "abgelaufen"
    if s == "suspended":
        return "gesperrt"
    # Eine laufende Testphase bleibt als solche sichtbar. Das Ablaufdatum wird
    # daneben separat gezeigt; ein tatsächlich abgelaufener Starter kommt über
    # die zentrale Lizenzbewertung bereits als "expired" hier an.
    if s == "trial":
        return "testphase"
    bis_str = row.get("lizenz_bis") or ""
    if s == "active" and bis_str:
        try:
            bis_dt = datetime.date.fromisoformat(str(bis_str)[:10])
            if (bis_dt - datetime.date.today()).days <= _30_TAGE:
                return "bald_abgelaufen"
        except Exception:
            pass
    return "aktiv"


def _sa_tage_verbleibend(row: dict) -> int | None:
    bis = row.get("lizenz_bis")
    if not bis:
        return None
    try:
        return max(0, (datetime.date.fromisoformat(str(bis)[:10]) - datetime.date.today()).days)
    except Exception:
        return None


def _sa_tage_label(row: dict) -> str:
    ds = row.get("_display_status", "")
    if ds == "archiviert":
        return "Archiviert"
    if ds in ("abgelaufen", "gesperrt"):
        return "Abgelaufen"
    t = row.get("_tage")
    if t is None:
        return "—"
    if t == 0:
        return "Heute"
    return f"{t} Tage"


def _sa_sort_key(row: dict) -> tuple:
    ds = row.get("_display_status", "aktiv")
    bis = row.get("lizenz_bis") or "9999-12-31"
    return (_SA_STATUS_ORDER.get(ds, 9), str(bis))


def _sa_ablauf_fmt(row: dict) -> str:
    bis = row.get("lizenz_bis")
    if not bis:
        return "—"
    try:
        return datetime.date.fromisoformat(str(bis)[:10]).strftime("%d.%m.%Y")
    except Exception:
        return str(bis)[:10]


def _sa_normalize(vereine_raw: list[dict], trainer_raw: list[dict]) -> list[dict]:
    """Konvertiert Vereine + Trainer in eine einheitliche Datenstruktur."""
    result: list[dict] = []
    for v in vereine_raw:
        info = get_lizenz_info(v)
        ablauf = info.get("ablauf_datum")
        result.append({
            "_typ":           "verein",
            "_id":            v["id"],
            "_name":          v.get("name") or "—",
            "email":          v.get("email") or "—",
            "kundennummer":   v.get("kundennummer") or "",
            "_paket_key":     info["lizenz_typ"],
            "_paket_label":   LIZENZ_TYPEN.get(info["lizenz_typ"], {}).get("label", info["lizenz_typ"]),
            "lizenz_status":  info["lizenz_status"],
            "lizenz_bis":     ablauf.isoformat() if ablauf else None,
            "gesperrt":       bool(info.get("gesperrt")),
            "zahlungsstatus": (v.get("zahlungsstatus") or ""),
            "stripe_customer_id":       v.get("stripe_customer_id") or "",
            "stripe_subscription_id":   v.get("stripe_subscription_id") or "",
            "letzte_zahlung_fehlgeschlagen": v.get("letzte_zahlung_fehlgeschlagen") or "",
            "cancel_at_period_end":     bool(v.get("cancel_at_period_end")),
            "kuendigungsstatus":        v.get("kuendigungsstatus") or "",
            "gekuendigt_zum":           v.get("gekuendigt_zum") or "",
            "kuendigung_eingegangen":   v.get("kuendigung_eingegangen") or "",
            "_raw_verein": v,
            "_raw_info":   info,
            "_raw_trainer": None,
        })
    for t in trainer_raw:
        # Technische Einzeltrainer-Mandanten führen ihre Trial-Frist in
        # testphase_bis. Die zentrale Auswertung liefert daraus Ablaufdatum,
        # verbleibende Tage und den wirksamen Status (auch nach Ablauf).
        trainer_info = get_lizenz_info({
            **t,
            "ist_technischer_mandant": bool(t.get("vertrag_verein_id")),
            "aktive_benutzer_anzahl": 1 if t.get("aktiv") else 0,
        })
        typ_key = trainer_info["lizenz_typ"]
        ablauf = trainer_info.get("ablauf_datum")
        result.append({
            "_typ":           "trainer",
            "_id":            t["id"],
            "_name":          f"{t.get('vorname', '')} {t.get('nachname', '')}".strip() or "—",
            "email":          t.get("email") or "—",
            "kundennummer":   t.get("kundennummer") or "",
            "_paket_key":     typ_key,
            "_paket_label":   LIZENZ_TYPEN.get(typ_key, {}).get("label", typ_key),
            "lizenz_status":  trainer_info["lizenz_status"],
            "lizenz_bis":     ablauf.isoformat() if ablauf else None,
            "gesperrt":       False,
            "zahlungsstatus": t.get("zahlungsstatus") or "",
            "stripe_customer_id":       t.get("stripe_customer_id") or "",
            "stripe_subscription_id":   t.get("stripe_subscription_id") or "",
            "letzte_zahlung_fehlgeschlagen": t.get("letzte_zahlung_fehlgeschlagen") or "",
            "cancel_at_period_end":     bool(t.get("cancel_at_period_end")),
            "kuendigungsstatus":        t.get("kuendigungsstatus") or "",
            "gekuendigt_zum":           t.get("gekuendigt_zum") or "",
            "kuendigung_eingegangen":   t.get("kuendigung_eingegangen") or "",
            "_raw_verein":  None,
            "_raw_info":    None,
            "_raw_trainer": t,
            "_vertrag_verein_id": t.get("vertrag_verein_id"),
        })
    for row in result:
        row["_display_status"] = _sa_display_status(row)
        row["_tage"]           = _sa_tage_verbleibend(row)
    return result


# ── Dialog: Lizenz-Details ────────────────────────────────────────────────────

@st.dialog("Lizenz-Details", width="large")
def _sa_detail_dialog(row: dict) -> None:
    """Zeigt alle verfügbaren Lizenz-Details in einem Modal."""
    typ_icon = "🏟" if row["_typ"] == "verein" else "👤"
    st.markdown(
        f'<div style="margin-bottom:12px">'
        f'<div style="font-size:18px;font-weight:700;color:{_C["text"]}">'
        f'{typ_icon} {row["_name"]}</div>'
        f'<div style="font-size:13px;color:{_C["muted"]}">{row["email"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_sa_badge_html(row["_display_status"]), unsafe_allow_html=True)
    st.markdown("")

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown(f"**Kundentyp:** {'Verein' if row['_typ'] == 'verein' else 'Einzeltrainer'}")
        st.markdown(f"**Paket:** {row['_paket_label']}")
        st.markdown(f"**Kundennummer:** {row['kundennummer'] or '—'}")
        st.markdown(f"**Ablauf:** {_sa_ablauf_fmt(row)}")
        st.markdown(f"**Verbleibend:** {_sa_tage_label(row)}")
        if row["gesperrt"]:
            st.markdown(f"**Sperrung:** 🔴 Gesperrt")
    with dc2:
        if row.get("zahlungsstatus"):
            st.markdown(f"**Zahlungsstatus:** {row['zahlungsstatus']}")
        if row.get("stripe_customer_id"):
            st.markdown(f"**Stripe Customer:** `{row['stripe_customer_id']}`")
        if row.get("stripe_subscription_id"):
            st.markdown(f"**Stripe Subscription:** `{row['stripe_subscription_id']}`")
        if row.get("cancel_at_period_end"):
            st.markdown(f"**Kündigung aktiv:** ✅ Ja (cancel_at_period_end)")
        if row.get("kuendigungsstatus") and row["kuendigungsstatus"] not in ("aktiv", ""):
            st.markdown(f"**Kündigungsstatus:** {row['kuendigungsstatus']}")
        if row.get("gekuendigt_zum"):
            st.markdown(f"**Vertragsende:** {str(row['gekuendigt_zum'])[:10]}")
        if row.get("kuendigung_eingegangen"):
            st.markdown(f"**Kündigung eingegangen:** {str(row['kuendigung_eingegangen'])[:10]}")
        if row.get("letzte_zahlung_fehlgeschlagen"):
            st.markdown(
                f'**Letzter Zahlungsfehlschlag:** '
                f'<span style="color:{_C["red"]}">'
                f'{str(row["letzte_zahlung_fehlgeschlagen"])[:16].replace("T", " ")}</span>',
                unsafe_allow_html=True,
            )

    # Rechnungen (nur Vereine)
    if row["_typ"] == "verein" and row.get("_raw_verein"):
        rechnungen = rechnungen_laden(row["_id"])
        if rechnungen:
            st.markdown("---")
            st.markdown(f"**Rechnungen** ({len(rechnungen)} Einträge)")
            import pandas as pd
            df_r = pd.DataFrame(rechnungen)
            df_r = df_r.rename(columns={
                "rechnungsnummer": "Nr.", "datum": "Datum",
                "betrag_eur": "Betrag (€)", "lizenz_typ": "Paket",
                "status": "Status", "lizenz_von": "Von", "lizenz_bis": "Bis",
            })
            anzeige = [c for c in ["Nr.", "Datum", "Betrag (€)", "Paket", "Status", "Von", "Bis"] if c in df_r.columns]
            st.dataframe(df_r[anzeige], use_container_width=True, hide_index=True)


# ── Dialog: Lizenz bearbeiten ────────────────────────────────────────────────

@st.dialog("Lizenz bearbeiten", width="large")
def _sa_edit_dialog(row: dict) -> None:
    """Formular zum Bearbeiten einer Lizenz — Verein oder Trainer."""
    st.markdown(
        f'<div style="font-size:16px;font-weight:700;color:{_C["text"]};margin-bottom:4px">'
        f'{"🏟" if row["_typ"] == "verein" else "👤"} {row["_name"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_sa_badge_html(row["_display_status"]), unsafe_allow_html=True)
    st.markdown("")

    if row["lizenz_status"] == "geloescht":
        st.info(
            "Dieser Datensatz wurde endgültig anonymisiert und ist nur aus "
            "gesetzlichen Aufbewahrungsgründen archiviert. Er kann nicht bearbeitet oder reaktiviert werden."
        )
        if st.button("Schließen", use_container_width=True, key="edit_dlg_deleted_close"):
            st.rerun()
        return

    typ_keys  = list(LIZENZ_TYPEN.keys())
    cur_typ   = row["_paket_key"] if row["_paket_key"] in typ_keys else typ_keys[0]
    cur_status = row["lizenz_status"] if row["lizenz_status"] in _SA_STATUS_ALLE else _SA_STATUS_ALLE[0]
    try:
        cur_bis = datetime.date.fromisoformat(str(row["lizenz_bis"])[:10]) if row.get("lizenz_bis") else datetime.date.today() + datetime.timedelta(days=30)
    except Exception:
        cur_bis = datetime.date.today() + datetime.timedelta(days=30)

    ec1, ec2 = st.columns(2)
    _stripe_kuendigung_offen = bool(
        row.get("stripe_subscription_id") and row.get("cancel_at_period_end")
    )
    if _stripe_kuendigung_offen:
        st.info(
            "Für dieses Stripe-Abo ist eine Kündigung zum Periodenende vorgemerkt. "
            "Der Status kann nur über den Stripe-Widerruf auf der Vertragsseite geändert werden."
        )

    with ec1:
        neuer_typ = st.selectbox(
            "Lizenztyp",
            typ_keys,
            index=typ_keys.index(cur_typ),
            format_func=lambda k: LIZENZ_TYPEN[k]["label"],
            key="edit_dlg_typ",
        )
        neuer_status = st.selectbox(
            "Status",
            _SA_STATUS_ALLE,
            index=_SA_STATUS_ALLE.index(cur_status),
            key="edit_dlg_status",
            disabled=_stripe_kuendigung_offen,
        )
    with ec2:
        ablauf_input = st.date_input("Lizenz bis", value=cur_bis, key="edit_dlg_ablauf")
        extra_tage   = st.number_input(
            "Testphase (+Tage)",
            min_value=0, max_value=365, value=0,
            key="edit_dlg_extra",
            help="Fügt diese Tage zur aktuellen Testphase hinzu",
        )

    # Sperren/Entsperren (nur Vereine)
    if row["_typ"] == "verein":
        st.markdown("")
        gesperrt_label = "🔓 Entsperren" if row["gesperrt"] else "🚫 Sperren"
        if st.button(gesperrt_label, key="edit_dlg_sperren"):
            db_verein_sperren(row["_id"], not row["gesperrt"])
            invalidate_lizenz_cache(row["_id"])
            st.success("✅ Sperrung aktualisiert.")
            st.rerun()

    st.markdown("")
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button("💾 Speichern", type="primary", use_container_width=True, key="edit_dlg_save"):
            if row["_typ"] == "verein":
                lizenz_setzen(
                    verein_id=row["_id"],
                    lizenz_typ=neuer_typ,
                    lizenz_status=neuer_status,
                    lizenz_bis=ablauf_input.isoformat(),
                )
                if extra_tage > 0:
                    testphase_verlaengern(row["_id"], extra_tage)
                invalidate_lizenz_cache(row["_id"])
            else:
                vertrag_verein_id = row.get("_vertrag_verein_id")
                if vertrag_verein_id:
                    lizenz_setzen(
                        verein_id=vertrag_verein_id,
                        lizenz_typ=neuer_typ,
                        lizenz_status=neuer_status,
                        lizenz_bis=ablauf_input.isoformat(),
                    )
                    if extra_tage > 0:
                        testphase_verlaengern(vertrag_verein_id, extra_tage)
                    invalidate_lizenz_cache(vertrag_verein_id)
                else:
                    trainer_lizenz_setzen(
                        benutzer_id=row["_id"],
                        lizenz_typ=neuer_typ,
                        lizenz_status=neuer_status,
                        lizenz_bis=ablauf_input.isoformat(),
                    )
            st.success(f"✅ Lizenz für **{row['_name']}** gespeichert.")
            st.rerun()
    with sc2:
        if st.button("Abbrechen", use_container_width=True, key="edit_dlg_cancel"):
            st.rerun()


# ── Dialog: Lizenz zuweisen ──────────────────────────────────────────────────

@st.dialog("+ Lizenz zuweisen", width="large")
def _sa_zuweisen_dialog(vereine_raw: list[dict], trainer_raw: list[dict]) -> None:
    """Manuelles Zuweisen einer Lizenz an einen bestehenden Kunden."""
    st.markdown("Wähle einen bestehenden Kunden und lege das Lizenzpaket fest.")

    # Auswahl: Verein oder Trainer
    kunden_typ = st.radio("Kundentyp", ["Verein", "Einzeltrainer"], horizontal=True, key="zuw_ktyp")

    if kunden_typ == "Verein":
        verein_opts = {v.get("name", f"ID {v['id']}"): v["id"] for v in vereine_raw}
        if not verein_opts:
            st.info("Keine Vereine vorhanden.")
            return
        verein_name = st.selectbox("Verein auswählen", list(verein_opts.keys()), key="zuw_verein")
        zuw_id = verein_opts[verein_name]
    else:
        trainer_opts = {
            f"{t.get('vorname', '')} {t.get('nachname', '')}".strip() + f" ({t.get('email', '')})"
            if t.get("email") else f"{t.get('vorname', '')} {t.get('nachname', '')}".strip(): t["id"]
            for t in trainer_raw
        }
        if not trainer_opts:
            st.info("Keine Einzeltrainer vorhanden.")
            return
        trainer_name = st.selectbox("Trainer auswählen", list(trainer_opts.keys()), key="zuw_trainer")
        zuw_id = trainer_opts[trainer_name]

    st.markdown("")
    zc1, zc2 = st.columns(2)
    with zc1:
        typ_keys = list(LIZENZ_TYPEN.keys())
        zuw_typ = st.selectbox(
            "Lizenzpaket",
            typ_keys,
            format_func=lambda k: LIZENZ_TYPEN[k]["label"],
            key="zuw_typ",
        )
        zuw_status = st.selectbox("Status", _SA_STATUS_ALLE, index=1, key="zuw_status")
    with zc2:
        zuw_start  = st.date_input("Startdatum", value=datetime.date.today(), key="zuw_start")
        zuw_bis    = st.date_input(
            "Enddatum",
            value=datetime.date.today() + datetime.timedelta(days=365),
            key="zuw_bis",
        )

    st.markdown("")
    zbc1, zbc2 = st.columns(2)
    with zbc1:
        if st.button("✅ Lizenz zuweisen", type="primary", use_container_width=True, key="zuw_save"):
            if kunden_typ == "Verein":
                lizenz_setzen(
                    verein_id=zuw_id,
                    lizenz_typ=zuw_typ,
                    lizenz_status=zuw_status,
                    lizenz_bis=zuw_bis.isoformat(),
                )
                invalidate_lizenz_cache(zuw_id)
            else:
                trainer_lizenz_setzen(
                    benutzer_id=zuw_id,
                    lizenz_typ=zuw_typ,
                    lizenz_status=zuw_status,
                    lizenz_bis=zuw_bis.isoformat(),
                )
            st.success("✅ Lizenz erfolgreich zugewiesen.")
            st.rerun()
    with zbc2:
        if st.button("Abbrechen", use_container_width=True, key="zuw_cancel"):
            st.rerun()


# ── Tab-Renderer ─────────────────────────────────────────────────────────────

def _sa_render_tab(
    rows: list[dict],
    tab_key: str,
    vereine_raw: list[dict],
) -> None:
    """Rendert Filter + Tabelle/Karten für einen einzelnen Tab."""

    # ── Filterleiste ──
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
    with fc1:
        suche = st.text_input(
            "Suche",
            placeholder="Name, E-Mail, Paket …",
            key=f"lv_s_{tab_key}",
            label_visibility="collapsed",
        )
    with fc2:
        paket_opts = ["Alle"] + sorted({r["_paket_label"] for r in rows})
        paket_filter = st.selectbox("Lizenztyp", paket_opts, key=f"lv_p_{tab_key}", label_visibility="collapsed")
    with fc3:
        if tab_key == "archiv":
            status_opts = ["Alle", "Archiviert"]
        else:
            status_opts = ["Alle", "Aktiv", "Testphase", "Läuft bald ab", "Abgelaufen", "Gesperrt"]
        status_filter = st.selectbox("Status", status_opts, key=f"lv_st_{tab_key}", label_visibility="collapsed")
    with fc4:
        if st.button("↺", key=f"lv_r_{tab_key}", help="Filter zurücksetzen"):
            for k in [f"lv_s_{tab_key}", f"lv_p_{tab_key}", f"lv_st_{tab_key}"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Filterlogik ──
    _STATUS_LABEL_MAP = {
        "Aktiv":          "aktiv",
        "Testphase":      "testphase",
        "Läuft bald ab":  "bald_abgelaufen",
        "Abgelaufen":     "abgelaufen",
        "Gesperrt":       "gesperrt",
        "Archiviert":     "archiviert",
    }
    gefiltert = rows
    if suche:
        _s = suche.lower()
        gefiltert = [r for r in gefiltert if
                     _s in (r["_name"] or "").lower()
                     or _s in (r["email"] or "").lower()
                     or _s in (r["_paket_label"] or "").lower()
                     or _s in (r["kundennummer"] or "").lower()]
    if paket_filter != "Alle":
        gefiltert = [r for r in gefiltert if r["_paket_label"] == paket_filter]
    if status_filter != "Alle":
        ziel_ds = _STATUS_LABEL_MAP.get(status_filter, "")
        gefiltert = [r for r in gefiltert if r["_display_status"] == ziel_ds]

    gefiltert = sorted(gefiltert, key=_sa_sort_key)

    if not gefiltert:
        st.info("Keine Lizenzen gefunden.")
        return

    # ── Tabellenheader (Desktop) ──
    st.markdown(
        f'<div style="display:grid;grid-template-columns:2fr 1.5fr 1fr 1.5fr 1.3fr 1.5fr;'
        f'gap:0 8px;padding:6px 12px 6px 4px;'
        f'border-bottom:1px solid {_C["border"]};'
        f'font-size:11px;font-weight:700;color:{_C["muted"]};text-transform:uppercase;'
        f'letter-spacing:.04em">'
        f'<span>Kunde</span><span>Paket</span><span>Typ</span>'
        f'<span>Status</span><span>Verbleibend</span><span>Aktionen</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Zeilen ──
    for i, row in enumerate(gefiltert):
        _sa_render_row(row, i, tab_key)


def _sa_render_row(row: dict, idx: int, tab_key: str) -> None:
    """Rendert eine einzelne Lizenz-Zeile (Desktop-Tabelle + Mobile-Karte)."""
    uid = f"{row['_typ']}_{row['_id']}_{tab_key}_{idx}"

    # Zahlung-Warnung
    _zahlung_warn = row.get("zahlungsstatus") == "fehlgeschlagen"
    _zahlung_badge_html = (
        f' <span style="padding:1px 6px;border-radius:8px;background:{_C["red"]}22;'
        f'color:{_C["red"]};font-size:10px;border:1px solid {_C["red"]}44">⚠ Zahlung</span>'
    ) if _zahlung_warn else ""

    with st.container(border=True):
        # ── Mobile-freundliche Karten-Übersicht ──────────────────────────────
        # Kompakter Header (Karte)
        st.markdown(
            f'<div style="display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;margin-bottom:4px">'
            f'<div style="flex:1;min-width:120px">'
            f'<div style="font-weight:700;font-size:13px;color:{_C["text"]}">'
            f'{"🏟" if row["_typ"] == "verein" else "👤"} {row["_name"]}{_zahlung_badge_html}</div>'
            f'<div style="font-size:11px;color:{_C["muted"]};margin-top:1px">{row["email"]}</div>'
            f'</div>'
            f'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">'
            f'<code style="font-size:11px;padding:1px 6px;background:{_C["surf"]};'
            f'border:1px solid {_C["border"]};border-radius:4px">{row["_paket_label"]}</code>'
            f'{_sa_badge_html(row["_display_status"])}'
            f'<span style="font-size:12px;color:{_C["muted"]}">{_sa_tage_label(row)}'
            f'{(" · Ablauf: " + _sa_ablauf_fmt(row)) if row.get("lizenz_bis") else ""}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Aktionsleiste ────────────────────────────────────────────────────
        ac1, ac2, ac3 = st.columns([1, 1, 1])
        with ac1:
            if st.button("Details", key=f"det_{uid}", use_container_width=True):
                _sa_detail_dialog(row)
        with ac2:
            if st.button("Bearbeiten", key=f"edit_{uid}", use_container_width=True):
                _sa_edit_dialog(row)
        with ac3:
            with st.popover("⋮ Mehr", use_container_width=True):
                # Sperren/Entsperren (nur Vereine)
                if row["_typ"] == "verein":
                    sperr_label = "🔓 Entsperren" if row["gesperrt"] else "🚫 Sperren"
                    if st.button(sperr_label, key=f"sperr_{uid}", use_container_width=True):
                        db_verein_sperren(row["_id"], not row["gesperrt"])
                        invalidate_lizenz_cache(row["_id"])
                        st.rerun()
                # Testphase verlängern
                tp_tage = st.number_input(
                    "Testphase (+Tage)",
                    min_value=1, max_value=365, value=14,
                    key=f"tp_n_{uid}",
                )
                if st.button(f"⏱ Testphase +{tp_tage}d", key=f"tp_{uid}", use_container_width=True):
                    # Einzeltrainer mit technischem Mandant speichern ihre Lizenz
                    # auf dem Mandanten, nicht auf der Benutzer-ID.
                    lizenz_entity_id = row.get("_vertrag_verein_id") or row["_id"]
                    testphase_verlaengern(lizenz_entity_id, tp_tage)
                    if row["_typ"] == "verein" or row.get("_vertrag_verein_id"):
                        invalidate_lizenz_cache(lizenz_entity_id)
                    st.success(f"Testphase um {tp_tage} Tage verlängert.")
                    st.rerun()
                # Kündigungs-Info (nur wenn relevant)
                if row.get("kuendigungsstatus") and row["kuendigungsstatus"] not in ("aktiv", ""):
                    st.markdown(
                        f'<div style="font-size:11px;color:{_C["orange"]};margin-top:6px">'
                        f'🔔 Kündigung: {row["kuendigungsstatus"]}</div>',
                        unsafe_allow_html=True,
                    )


# ══════════════════════════════════════════════════════════════════════════════
# Superadmin-Lizenz-Dashboard  —  Hauptfunktion
# ══════════════════════════════════════════════════════════════════════════════

def page_lizenz_superadmin() -> None:
    """Lizenz-Verwaltung für Superadmin — übersichtliches Dashboard aller Lizenzen."""
    from session_timeout import touch_session
    touch_session()

    # ── Superadmin-Sicherheitsprüfung  (serverseitige Guard) ─────────────────
    _u = st.session_state.get("user", {})
    if (_u.get("rolle") or "").lower() != "superadmin":
        st.error("⛔ Kein Zugriff. Diese Seite ist ausschließlich für Superadmins.")
        st.stop()
        return

    # ── Daten laden ──────────────────────────────────────────────────────────
    vereine_raw = alle_vereine_lizenz()
    trainer_raw = alle_trainer_lizenz()
    alle        = _sa_normalize(vereine_raw, trainer_raw)

    # ── Stripe Webhook-Warnung (nur wenn Fehler vorhanden) ───────────────────
    fehler_liste = webhook_fehler_laden(limit=50)
    if fehler_liste:
        sig_f    = [f for f in fehler_liste if "Signaturprüfung"      in (f.get("fehlergrund") or "")]
        price_f  = [f for f in fehler_liste if "Price-ID"             in (f.get("fehlergrund") or "")]
        zahlung_f= [f for f in fehler_liste if "Zahlung fehlgeschlagen" in (f.get("fehlergrund") or "")]
        sonstige = [f for f in fehler_liste
                    if f not in sig_f and f not in price_f and f not in zahlung_f]
        with st.expander(
            f"⚠️ Stripe-Zahlungs-/Webhook-Problem erkannt ({len(fehler_liste)} Einträge)",
            expanded=False,
        ):
            wc1, wc2, wc3, wc4 = st.columns(4)
            with wc1: _kpi("Signaturprüfung",    str(len(sig_f)),     _C["red"]    if sig_f     else _C["muted"])
            with wc2: _kpi("Unbekannte Price-ID", str(len(price_f)),  _C["orange"] if price_f   else _C["muted"])
            with wc3: _kpi("Zahlung fehlgeschl.", str(len(zahlung_f)),_C["orange"] if zahlung_f else _C["muted"])
            with wc4: _kpi("Sonstige",            str(len(sonstige)), _C["red"]    if sonstige  else _C["muted"])
            st.markdown("")
            import pandas as pd
            df_f = pd.DataFrame(fehler_liste).rename(columns={
                "id": "ID", "event_id": "Event-ID", "event_type": "Event-Typ",
                "fehlergrund": "Fehlergrund", "zeitstempel": "Zeitstempel",
            })
            anzeige_cols = [c for c in ["Zeitstempel", "Event-Typ", "Fehlergrund", "Event-ID"] if c in df_f.columns]
            st.dataframe(df_f[anzeige_cols], use_container_width=True, hide_index=True)
            st.markdown("")
            if st.button("🗑 Alle Webhook-Fehler löschen", key="webhook_fehler_loeschen_btn",
                         help="Löscht alle gespeicherten Webhook-Fehler aus der Datenbank."):
                anzahl = webhook_fehler_loeschen()
                st.success(f"✅ {anzahl} Webhook-Fehler gelöscht.")
                st.rerun()

    # ── Header ───────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        st.markdown(
            f'<h2 style="color:{_C["text"]};font-size:22px;font-weight:700;margin-bottom:2px">'
            f'Lizenzverwaltung</h2>'
            f'<p style="color:{_C["muted"]};font-size:13px;margin:0">Übersicht und Verwaltung aller Lizenzen</p>',
            unsafe_allow_html=True,
        )
    with hc2:
        if st.button("+ Lizenz zuweisen", type="primary", key="lv_zuweisen_btn",
                     use_container_width=True):
            _sa_zuweisen_dialog(vereine_raw, trainer_raw)

    st.markdown("")

    # ── KPI-Kacheln ──────────────────────────────────────────────────────────
    nicht_archiv = [r for r in alle if r["_display_status"] != "archiviert"]
    gesamt_n     = len(nicht_archiv)
    aktiv_n      = sum(1 for r in nicht_archiv if r["_display_status"] in ("aktiv", "testphase"))
    bald_n       = sum(1 for r in nicht_archiv if r["_display_status"] == "bald_abgelaufen")
    abg_n        = sum(1 for r in nicht_archiv if r["_display_status"] in ("abgelaufen", "gesperrt"))

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1: _kpi("Gesamt",          str(gesamt_n), _C["blue"])
    with kc2: _kpi("Aktiv",           str(aktiv_n),  _C["green"])
    with kc3: _kpi("Läuft bald ab",   str(bald_n),   _C["orange"])
    with kc4: _kpi("Abgelaufen",      str(abg_n),    _C["red"])

    st.markdown("")

    # ── Datensätze aufteilen ─────────────────────────────────────────────────
    archiviert      = [r for r in alle if r["_display_status"] == "archiviert"]
    nicht_archiviert = [r for r in alle if r["_display_status"] != "archiviert"]

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        f"🗂 Alle Lizenzen ({len(nicht_archiviert)})",
        f"🏟 Vereinslizenzen ({sum(1 for r in nicht_archiviert if r['_typ'] == 'verein')})",
        f"👤 Trainerlizenzen ({sum(1 for r in nicht_archiviert if r['_typ'] == 'trainer')})",
        f"📦 Archiv ({len(archiviert)})",
    ])

    with tab1:
        _sa_render_tab(nicht_archiviert, "alle", vereine_raw)
    with tab2:
        _sa_render_tab([r for r in nicht_archiviert if r["_typ"] == "verein"], "verein", vereine_raw)
    with tab3:
        _sa_render_tab([r for r in nicht_archiviert if r["_typ"] == "trainer"], "trainer", vereine_raw)
    with tab4:
        _sa_render_tab(archiviert, "archiv", vereine_raw)
