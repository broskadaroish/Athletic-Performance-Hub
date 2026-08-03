"""
Lizenzsystem — Bruce Football Performance Diagnostics.

Saubere Trennung von Lizenz-Logik und App-Code.
Alle Lizenzprüfungen laufen hier durch.

Lizenztypen: BASIC | PRO
Testphase:   30 Tage kostenlos, keine Kreditkarte erforderlich
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
    preis_monat: float   # EUR
    preis_jahr: float    # EUR
    stripe_price_monat: str   # Stripe Price-ID Platzhalter
    stripe_price_jahr: str    # Stripe Price-ID Platzhalter
    features: list[str]
    geeignet_fuer: list[str]


LIZENZ_TYPEN: dict[str, LizenzTypDef] = {
    "BASIC": {
        "label":               "Basic",
        "max_trainer":         1,
        "max_spieler":         40,
        "preis_monat":         9.90,
        "preis_jahr":          99.0,
        "stripe_price_monat":  os.environ.get("STRIPE_PRICE_BASIC_MONAT", "price_basic_monat_placeholder"),
        "stripe_price_jahr":   os.environ.get("STRIPE_PRICE_BASIC_JAHR",  "price_basic_jahr_placeholder"),
        "geeignet_fuer": [
            "Einzeltrainer",
            "Jugendtrainer",
            "Kleine Vereine",
        ],
        "features": [
            "diagnostik_basis",
            "spielerprofil",
            "pdf_export",
            "excel_export",
            "verlauf",
            "trainingsplanung",
            "dashboard",
            "email_support",
        ],
    },
    "PRO": {
        "label":               "Pro",
        "max_trainer":         9999,   # unbegrenzt
        "max_spieler":         9999,   # unbegrenzt
        "preis_monat":         24.90,
        "preis_jahr":          249.0,
        "stripe_price_monat":  os.environ.get("STRIPE_PRICE_PRO_MONAT", "price_pro_monat_placeholder"),
        "stripe_price_jahr":   os.environ.get("STRIPE_PRICE_PRO_JAHR",  "price_pro_jahr_placeholder"),
        "geeignet_fuer": [
            "Komplette Vereine",
            "Mehrere Mannschaften",
            "Leistungszentren",
        ],
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
            "vereinsverwaltung",
            "vereinslogo",
            "teamanalysen",
            "prioritaets_support",
        ],
    },
}

# Feature-Labels für die UI
FEATURE_LABELS: dict[str, str] = {
    "diagnostik_basis":      "Alle Athletiktests",
    "diagnostik_erweitert":  "Erweiterte Diagnostik (Y-Balance, Agilität)",
    "diagnostik_spiro":      "Spiroergometrie / VO₂max",
    "spielerprofil":         "Spielerprofile & Verlauf",
    "pdf_export":            "PDF-Berichte",
    "excel_export":          "Excel-Export",
    "verlauf":               "Leistungsverlauf & Trends",
    "verletzungsmanagement": "Belastungsmanagement",
    "trainingsplanung":      "Trainingspläne",
    "periodisierung":        "Periodisierung",
    "spielervergleich":      "Spieler-Vergleich",
    "mannschaftsdashboard":  "Mannschafts-Dashboard",
    "vereinsverwaltung":     "Vereinsverwaltung",
    "vereinslogo":           "Vereinslogo in PDFs",
    "teamanalysen":          "Teamanalysen",
    "dashboard":             "Dashboard",
    "email_support":         "E-Mail Support",
    "prioritaets_support":   "Prioritäts-Support",
}

TESTPHASE_TAGE = 30   # Tage kostenlose Testphase bei Neuregistrierung

# ─── Status-Typen ─────────────────────────────────────────────────────────────

# lizenz_status Werte in der DB:
#   "trial"     — aktive Testphase
#   "active"    — bezahlte aktive Lizenz
#   "expired"   — Testphase oder Lizenz abgelaufen
#   "suspended" — manuell gesperrt durch Superadmin
#   "cancelled" — Abo gekündigt, läuft noch bis Lizenzende


class LizenzInfo(TypedDict):
    verein_id: int
    lizenz_typ: str           # BASIC | PRO
    lizenz_status: str        # trial | active | expired | suspended | cancelled
    lizenz_bis: str | None    # ISO-Date oder None
    testphase_bis: str | None # ISO-Date oder None
    gesperrt: bool
    zahlungsstatus: str       # offen | bezahlt | fehlgeschlagen | storniert
    tage_verbleibend: int | None
    ablauf_datum: date | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None


def get_lizenz_info(verein_row: dict) -> LizenzInfo:
    """Berechnet den vollständigen Lizenz-Status eines Vereins."""
    from functools import lru_cache

    verein_id = verein_row.get("id", 0)
    cache_key = f"_lizenz_info_{verein_id}"

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    heute = date.today()

    lizenz_typ     = (verein_row.get("lizenztyp") or "BASIC").upper()
    lizenz_status  = verein_row.get("lizenz_status") or "trial"
    gesperrt       = bool(verein_row.get("gesperrt", 0))
    zahlungsstatus = verein_row.get("zahlungsstatus") or "offen"

    # Normalize: FREE → BASIC, ENTERPRISE → PRO (Altdaten-Kompatibilität)
    if lizenz_typ not in LIZENZ_TYPEN:
        lizenz_typ = "BASIC"

    # Ablaufdatum bestimmen
    ablauf_datum: date | None = None
    tage_verbleibend: int | None = None

    if lizenz_status == "trial":
        raw = verein_row.get("testphase_bis")
        if raw:
            try:
                ablauf_datum = date.fromisoformat(str(raw)[:10])
                tage_verbleibend = (ablauf_datum - heute).days
            except ValueError:
                pass
    else:
        raw = verein_row.get("lizenz_bis")
        if raw:
            try:
                ablauf_datum = date.fromisoformat(str(raw)[:10])
                tage_verbleibend = (ablauf_datum - heute).days
            except ValueError:
                pass

    # Abgelaufen-Check
    if tage_verbleibend is not None and tage_verbleibend < 0:
        lizenz_status = "expired"

    if gesperrt:
        lizenz_status = "suspended"

    info: LizenzInfo = {
        "verein_id":              verein_id,
        "lizenz_typ":             lizenz_typ,
        "lizenz_status":          lizenz_status,
        "lizenz_bis":             verein_row.get("lizenz_bis"),
        "testphase_bis":          verein_row.get("testphase_bis"),
        "gesperrt":               gesperrt,
        "zahlungsstatus":         zahlungsstatus,
        "tage_verbleibend":       tage_verbleibend,
        "ablauf_datum":           ablauf_datum,
        "stripe_customer_id":     verein_row.get("stripe_customer_id"),
        "stripe_subscription_id": verein_row.get("stripe_subscription_id"),
    }

    st.session_state[cache_key] = info
    return info


def enforce_license_gate() -> None:
    """
    Prüft den Lizenzstatus bei jedem Re-Run.
    Blockiert die App bei gesperrten oder abgelaufenen Lizenzen.
    Superadmins werden nie blockiert.
    """
    user = st.session_state.get("user", {})
    if not user:
        return  # nicht eingeloggt — Login-Gate greift

    if user.get("rolle") == "Superadmin":
        return  # Superadmin immer durch

    verein_id = user.get("verein_id")
    if not verein_id:
        return

    cache_key = f"_lizenz_info_{verein_id}"
    if cache_key not in st.session_state:
        try:
            from database import lizenz_info_laden
            verein_row = lizenz_info_laden(verein_id) or {}
        except Exception:
            return
        info = get_lizenz_info(verein_row)
    else:
        info = st.session_state[cache_key]

    if info["lizenz_status"] == "suspended":
        _zeige_gesperrt_page()
        st.stop()

    if info["lizenz_status"] == "expired":
        _zeige_abgelaufen_page(info)
        st.stop()


def feature_erlaubt(feature: str, lizenz_typ: str) -> bool:
    """Prüft ob ein Feature im aktuellen Lizenztyp enthalten ist."""
    typ_def = LIZENZ_TYPEN.get(lizenz_typ.upper())
    if not typ_def:
        return False
    feats = typ_def["features"]
    return "all" in feats or feature in feats


def trainer_limit_erreicht(verein_id: int, lizenz_typ: str) -> bool:
    """Gibt True zurück wenn das Trainer-Limit erreicht ist."""
    try:
        from database import get_conn
        with get_conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1 AND rolle='Trainer'",
                (verein_id,)
            ).fetchone()[0]
        typ_def = LIZENZ_TYPEN.get(lizenz_typ.upper(), LIZENZ_TYPEN["BASIC"])
        return count >= typ_def["max_trainer"]
    except Exception:
        return False


def spieler_limit_erreicht(verein_id: int, lizenz_typ: str) -> bool:
    """Gibt True zurück wenn das Spieler-Limit erreicht ist."""
    try:
        from database import get_conn
        with get_conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=? AND aktiv=1",
                (verein_id,)
            ).fetchone()[0]
        typ_def = LIZENZ_TYPEN.get(lizenz_typ.upper(), LIZENZ_TYPEN["BASIC"])
        return count >= typ_def["max_spieler"]
    except Exception:
        return False


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
            "Deine kostenlose 30-Tage-Testphase ist abgelaufen. "
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
