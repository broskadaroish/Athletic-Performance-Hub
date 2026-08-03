"""
Lizenzsystem — Bruce Football Performance Diagnostics.

Saubere Trennung von Lizenz-Logik und App-Code.
Alle Lizenzprüfungen laufen hier durch.

Lizenztypen: FREE → BASIC → PRO → ENTERPRISE
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import TypedDict

import streamlit as st

# ─── Lizenztypen-Definition ────────────────────────────────────────────────────

class LizenzTypDef(TypedDict):
    label: str
    max_trainer: int
    max_spieler: int
    preis_monat: int   # EUR
    preis_jahr: int    # EUR
    stripe_price_monat: str   # Stripe Price-ID Platzhalter
    stripe_price_jahr: str    # Stripe Price-ID Platzhalter
    features: list[str]


LIZENZ_TYPEN: dict[str, LizenzTypDef] = {
    "FREE": {
        "label":               "Free",
        "max_trainer":         1,
        "max_spieler":         15,
        "preis_monat":         0,
        "preis_jahr":          0,
        "stripe_price_monat":  "",  # kein Stripe für Free
        "stripe_price_jahr":   "",
        "features": [
            "diagnostik_basis",
            "spielerprofil",
        ],
    },
    "BASIC": {
        "label":               "Basic",
        "max_trainer":         3,
        "max_spieler":         50,
        "preis_monat":         29,
        "preis_jahr":          290,
        "stripe_price_monat":  os.environ.get("STRIPE_PRICE_BASIC_MONAT", "price_basic_monat_placeholder"),
        "stripe_price_jahr":   os.environ.get("STRIPE_PRICE_BASIC_JAHR",  "price_basic_jahr_placeholder"),
        "features": [
            "diagnostik_basis",
            "diagnostik_erweitert",
            "spielerprofil",
            "pdf_export",
            "excel_export",
            "verletzungsmanagement",
        ],
    },
    "PRO": {
        "label":               "Pro",
        "max_trainer":         10,
        "max_spieler":         200,
        "preis_monat":         79,
        "preis_jahr":          790,
        "stripe_price_monat":  os.environ.get("STRIPE_PRICE_PRO_MONAT", "price_pro_monat_placeholder"),
        "stripe_price_jahr":   os.environ.get("STRIPE_PRICE_PRO_JAHR",  "price_pro_jahr_placeholder"),
        "features": [
            "diagnostik_basis",
            "diagnostik_erweitert",
            "diagnostik_spiro",
            "spielerprofil",
            "pdf_export",
            "excel_export",
            "verletzungsmanagement",
            "trainingsplanung",
            "periodisierung",
            "spielervergleich",
            "mannschaftsdashboard",
        ],
    },
    "ENTERPRISE": {
        "label":               "Enterprise",
        "max_trainer":         9999,
        "max_spieler":         9999,
        "preis_monat":         199,
        "preis_jahr":          1990,
        "stripe_price_monat":  os.environ.get("STRIPE_PRICE_ENT_MONAT", "price_ent_monat_placeholder"),
        "stripe_price_jahr":   os.environ.get("STRIPE_PRICE_ENT_JAHR",  "price_ent_jahr_placeholder"),
        "features": ["all"],
    },
}

TESTPHASE_TAGE = 14   # Tage kostenlose Testphase bei Neuregistrierung

# ─── Status-Typen ─────────────────────────────────────────────────────────────

# lizenz_status Werte in der DB:
#   "trial"     — aktive Testphase
#   "active"    — bezahlte aktive Lizenz
#   "expired"   — Testphase oder Lizenz abgelaufen
#   "suspended" — manuell gesperrt durch Superadmin
#   "cancelled" — Abo gekündigt, läuft noch bis Lizenzende


class LizenzInfo(TypedDict):
    verein_id: int
    lizenz_typ: str           # FREE | BASIC | PRO | ENTERPRISE
    lizenz_status: str        # trial | active | expired | suspended | cancelled
    lizenz_bis: str | None    # ISO-Date oder None
    testphase_bis: str | None # ISO-Date oder None
    gesperrt: bool
    zahlungsstatus: str       # offen | bezahlt | fehlgeschlagen | storniert
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    # berechnete Felder
    ist_aktiv: bool           # True wenn Nutzung erlaubt
    tage_verbleibend: int | None
    ablauf_datum: date | None


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _tage_bis(d: date | None) -> int | None:
    if d is None:
        return None
    delta = (d - date.today()).days
    return delta


# ─── Lizenz-Status berechnen ──────────────────────────────────────────────────

def get_lizenz_info(verein_row: dict) -> LizenzInfo:
    """Berechnet den aktuellen Lizenz-Status aus einem verein-Dict.
    Kein DB-Aufruf — Eingabe ist bereits geladenes verein-Dict."""

    typ = (verein_row.get("lizenztyp") or "FREE").upper()
    if typ not in LIZENZ_TYPEN:
        typ = "FREE"

    status       = verein_row.get("lizenz_status") or "trial"
    gesperrt     = bool(verein_row.get("gesperrt", 0))
    lizenz_bis   = _parse_date(verein_row.get("lizenz_bis"))
    testphase    = _parse_date(verein_row.get("testphase_bis"))
    zahlungs_st  = verein_row.get("zahlungsstatus") or "offen"

    # Gesperrt hat höchste Priorität
    if gesperrt or not verein_row.get("aktiv", 1):
        return LizenzInfo(
            verein_id=verein_row["id"],
            lizenz_typ=typ,
            lizenz_status="suspended",
            lizenz_bis=verein_row.get("lizenz_bis"),
            testphase_bis=verein_row.get("testphase_bis"),
            gesperrt=True,
            zahlungsstatus=zahlungs_st,
            stripe_customer_id=verein_row.get("stripe_customer_id"),
            stripe_subscription_id=verein_row.get("stripe_subscription_id"),
            ist_aktiv=False,
            tage_verbleibend=None,
            ablauf_datum=None,
        )

    today = date.today()
    ablauf = None
    ist_aktiv = False

    if status == "trial":
        if testphase and testphase >= today:
            ist_aktiv = True
            ablauf = testphase
        else:
            # Testphase abgelaufen → expired
            status = "expired"

    elif status == "active":
        if lizenz_bis and lizenz_bis >= today:
            ist_aktiv = True
            ablauf = lizenz_bis
        else:
            status = "expired"

    elif status == "cancelled":
        # Abo gekündigt — läuft noch bis Lizenzende
        if lizenz_bis and lizenz_bis >= today:
            ist_aktiv = True
            ablauf = lizenz_bis
        else:
            status = "expired"

    elif status in ("expired", "suspended"):
        ist_aktiv = False

    return LizenzInfo(
        verein_id=verein_row["id"],
        lizenz_typ=typ,
        lizenz_status=status,
        lizenz_bis=verein_row.get("lizenz_bis"),
        testphase_bis=verein_row.get("testphase_bis"),
        gesperrt=gesperrt,
        zahlungsstatus=zahlungs_st,
        stripe_customer_id=verein_row.get("stripe_customer_id"),
        stripe_subscription_id=verein_row.get("stripe_subscription_id"),
        ist_aktiv=ist_aktiv,
        tage_verbleibend=_tage_bis(ablauf),
        ablauf_datum=ablauf,
    )


def feature_erlaubt(info: LizenzInfo, feature: str) -> bool:
    """Prüft ob ein bestimmtes Feature für diese Lizenz verfügbar ist."""
    if not info["ist_aktiv"]:
        return False
    typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["FREE"])
    feats = typ_def["features"]
    if "all" in feats:
        return True
    return feature in feats


def trainer_limit_erreicht(info: LizenzInfo, aktuelle_anzahl: int) -> bool:
    """True wenn das Trainer-Limit der Lizenz erreicht ist."""
    typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["FREE"])
    return aktuelle_anzahl >= typ_def["max_trainer"]


def spieler_limit_erreicht(info: LizenzInfo, aktuelle_anzahl: int) -> bool:
    """True wenn das Spieler-Limit der Lizenz erreicht ist."""
    typ_def = LIZENZ_TYPEN.get(info["lizenz_typ"], LIZENZ_TYPEN["FREE"])
    return aktuelle_anzahl >= typ_def["max_spieler"]


# ─── App-Gate ─────────────────────────────────────────────────────────────────

def enforce_license_gate() -> LizenzInfo | None:
    """Prüft die Lizenz des aktuellen Vereins und stoppt bei Bedarf die App.

    Superadmin wird niemals geblockt.
    Gibt LizenzInfo zurück (im session_state gecacht).
    Gibt None zurück für Superadmin (kein Limit).
    """
    from database import verein_by_id

    user = st.session_state.get("user", {})
    rolle = user.get("rolle", "Trainer")

    # Superadmin ist niemals eingeschränkt
    if rolle == "Superadmin":
        return None

    verein_id = user.get("verein_id")
    if not verein_id:
        return None

    # Cache — nur einmal pro Rerun laden
    cache_key = f"_lizenz_info_{verein_id}"
    if cache_key not in st.session_state:
        verein_row = verein_by_id(verein_id) or {}
        info = get_lizenz_info(verein_row)
        st.session_state[cache_key] = info
    else:
        info = st.session_state[cache_key]

    if info["lizenz_status"] == "suspended":
        _zeige_gesperrt_page()
        st.stop()

    if not info["ist_aktiv"]:
        _zeige_abgelaufen_page(info)
        st.stop()

    # Warnung: Ablauf nahe
    tage = info.get("tage_verbleibend")
    if tage is not None and 0 <= tage <= 7:
        status_label = "Testphase" if info["lizenz_status"] == "trial" else "Lizenz"
        if tage == 0:
            st.warning(f"⚠️ Deine {status_label} läuft **heute** ab.")
        else:
            st.warning(f"⚠️ Deine {status_label} läuft in **{tage} Tag{'en' if tage != 1 else ''}** ab.")

    return info


def invalidate_lizenz_cache(verein_id: int) -> None:
    """Cache leeren — nach Lizenzänderungen aufrufen."""
    key = f"_lizenz_info_{verein_id}"
    if key in st.session_state:
        del st.session_state[key]


# ─── Interne Gate-Seiten ──────────────────────────────────────────────────────

def _card(color: str, icon: str, titel: str, text: str) -> None:
    st.markdown(
        f'<div style="max-width:600px;margin:60px auto;padding:40px 44px;'
        f'background:#161b22;border:2px solid {color};border-radius:14px;text-align:center">'
        f'<div style="font-size:48px;margin-bottom:16px">{icon}</div>'
        f'<h2 style="color:#e6edf3;margin-bottom:8px">{titel}</h2>'
        f'<p style="color:#8b949e;font-size:14px;line-height:1.6">{text}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _zeige_gesperrt_page() -> None:
    _card(
        "#f85149", "🚫",
        "Konto gesperrt",
        "Dein Vereinskonto wurde deaktiviert. Bitte kontaktiere den Support: "
        "<a href='mailto:support@brucefootball.de' style='color:#58a6ff'>"
        "support@brucefootball.de</a>",
    )


def _zeige_abgelaufen_page(info: LizenzInfo) -> None:
    if info["lizenz_status"] == "trial":
        titel = "Testphase abgelaufen"
        text  = (
            "Deine kostenlose 14-Tage-Testphase ist abgelaufen. "
            "Wähle einen Tarif und aktiviere deine Lizenz, um weiterzumachen."
        )
    else:
        titel = "Lizenz abgelaufen"
        text  = (
            "Deine Lizenz ist abgelaufen. "
            "Bitte erneuere dein Abonnement, um wieder Zugriff zu erhalten."
        )
    _card("#d29922", "⏳", titel, text)
    st.markdown(
        '<p style="text-align:center;margin-top:8px">'
        '<a href="?section=lizenz" style="color:#58a6ff;font-size:14px">'
        '→ Zur Lizenz-Seite</a></p>',
        unsafe_allow_html=True,
    )
