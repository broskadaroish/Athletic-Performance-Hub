"""
Lizenzsystem — Athletic Performance Hub.

Saubere Trennung von Lizenz-Logik und App-Code.
Alle Lizenzprüfungen laufen zentral hier durch.

4-Paket-System (Phase A1):
  TRAINER_BASIC  — 1 Trainer, 20 Spieler,      9,99 €/Monat
  TRAINER_PRO    — 1 Trainer, unbegrenzt,      14,99 €/Monat
  VEREIN_BASIC   — 2 Trainer, 50 Spieler,      24,99 €/Monat
  VEREIN_PRO     — 15 Trainer, unbegrenzt,     39,99 €/Monat

Testphase: 30 Tage kostenlos, keine Kreditkarte erforderlich.

Abwärtskompatibilität:
  Alte DB-Werte BASIC / PRO / Enterprise und Display-Werte (Basis, Standard,
  Premium …) werden über LIZENZ_TYPEN_COMPAT auf neue Keys abgebildet.
  Keine DB-Migration nötig.
"""

from __future__ import annotations

import os
from datetime import date
from typing import TypedDict

import streamlit as st

# ─── Zentrale Support-Adresse ───────────────────────────────────────────────────
# Einzige maßgebliche Stelle für die sichtbare Support-E-Mail in license.py.
# Produktive Wert wird über die Umgebungsvariable SUPPORT_EMAIL konfiguriert.
SUPPORT_EMAIL: str = os.environ.get("SUPPORT_EMAIL", "support@aphsystem.de")


# ─── Lizenztypen-Definition ────────────────────────────────────────────────────

class LizenzTypDef(TypedDict):
    label: str                   # Anzeigename in der UI
    kundentyp: str               # "Einzeltrainer" | "Verein"
    max_trainer: int | None      # None = unbegrenzt
    max_spieler: int | None      # None = unbegrenzt
    preis_monat: float           # EUR
    preis_jahr: float            # EUR
    stripe_price_monat: str      # Stripe Price-ID (leer = noch nicht konfiguriert)
    stripe_price_jahr: str       # Stripe Price-ID (leer = noch nicht konfiguriert)
    features: list[str]
    geeignet_fuer: list[str]


# Einzelner Featureset-Block für die beiden Trainer-Pakete (ohne Vereinsverwaltung)
_FEATURES_TRAINER_BASIC: list[str] = [
    "diagnostik_basis",
    "spielerprofil",
    "pdf_export",
    "excel_export",
    "verlauf",
    "trainingsplanung",
    "dashboard",
    "email_support",
]

_FEATURES_TRAINER_PRO: list[str] = [
    "diagnostik_basis",
    "diagnostik_erweitert",
    "diagnostik_spiro",
    "spielerprofil",
    "pdf_export",
    "excel_export",
    "verlauf",
    "verletzungsmanagement",
    "trainingsplanung",
    "periodisierung",
    "spielervergleich",
    "mannschaftsdashboard",
    "vereinslogo",
    "prioritaets_support",
]

_FEATURES_VEREIN_BASIC: list[str] = [
    "diagnostik_basis",
    "spielerprofil",
    "pdf_export",
    "excel_export",
    "verlauf",
    "trainingsplanung",
    "mannschaftsdashboard",
    "vereinsverwaltung",
    "vereinslogo",
    "dashboard",
    "email_support",
]

_FEATURES_VEREIN_PRO: list[str] = [
    "diagnostik_basis",
    "diagnostik_erweitert",
    "diagnostik_spiro",
    "spielerprofil",
    "pdf_export",
    "excel_export",
    "verlauf",
    "verletzungsmanagement",
    "trainingsplanung",
    "periodisierung",
    "spielervergleich",
    "mannschaftsdashboard",
    "vereinsverwaltung",
    "vereinslogo",
    "teamanalysen",
    "prioritaets_support",
]


LIZENZ_TYPEN: dict[str, LizenzTypDef] = {
    "TRAINER_BASIC": {
        "label":              "Einzeltrainer Basic",
        "kundentyp":          "Einzeltrainer",
        "max_trainer":        1,
        "max_spieler":        20,
        "preis_monat":        9.99,
        "preis_jahr":         99.0,
        "stripe_price_monat": os.environ.get("STRIPE_PRICE_TRAINER_BASIC_MONAT", ""),
        "stripe_price_jahr":  os.environ.get("STRIPE_PRICE_TRAINER_BASIC_JAHR",  ""),
        "geeignet_fuer":      ["Einzeltrainer", "Jugendtrainer"],
        "features":           _FEATURES_TRAINER_BASIC,
    },
    "TRAINER_PRO": {
        "label":              "Einzeltrainer Pro",
        "kundentyp":          "Einzeltrainer",
        "max_trainer":        1,
        "max_spieler":        None,      # unbegrenzt
        "preis_monat":        14.99,
        "preis_jahr":         149.0,
        "stripe_price_monat": os.environ.get("STRIPE_PRICE_TRAINER_PRO_MONAT", ""),
        "stripe_price_jahr":  os.environ.get("STRIPE_PRICE_TRAINER_PRO_JAHR",  ""),
        "geeignet_fuer":      ["Einzeltrainer", "Akademie-Trainer"],
        "features":           _FEATURES_TRAINER_PRO,
    },
    "VEREIN_BASIC": {
        "label":              "Verein Basic",
        "kundentyp":          "Verein",
        "max_trainer":        2,
        "max_spieler":        50,
        "preis_monat":        24.99,
        "preis_jahr":         249.0,
        "stripe_price_monat": os.environ.get("STRIPE_PRICE_VEREIN_BASIC_MONAT", ""),
        "stripe_price_jahr":  os.environ.get("STRIPE_PRICE_VEREIN_BASIC_JAHR",  ""),
        "geeignet_fuer":      ["Kleine Vereine", "Jugendabteilungen"],
        "features":           _FEATURES_VEREIN_BASIC,
    },
    "VEREIN_PRO": {
        "label":              "Verein Pro",
        "kundentyp":          "Verein",
        "max_trainer":        15,
        "max_spieler":        None,      # unbegrenzt
        "preis_monat":        39.99,
        "preis_jahr":         399.0,
        "stripe_price_monat": os.environ.get("STRIPE_PRICE_VEREIN_PRO_MONAT", ""),
        "stripe_price_jahr":  os.environ.get("STRIPE_PRICE_VEREIN_PRO_JAHR",  ""),
        "geeignet_fuer":      ["Komplette Vereine", "Leistungszentren", "Akademien"],
        "features":           _FEATURES_VEREIN_PRO,
    },
}

# ─── Abwärtskompatibilität: alte Paket-Werte → neue Keys ──────────────────────
#
# Keine DB-Migration nötig. Alle Lesepfade rufen normalize_lizenz_typ() auf,
# das alte Werte on-the-fly auf gültige LIZENZ_TYPEN-Keys abbildet.
#
# Mapping-Logik:
#   BASIC      → TRAINER_BASIC  (alter 1-Trainer-Plan)
#   PRO        → VEREIN_PRO     (alter All-Inclusive-Plan)
#   Enterprise → VEREIN_PRO     (Custom-Plan, war immer Premium)
#   Basis      → TRAINER_BASIC  (alter Display-Wert aus Superadmin-UI)
#   Standard   → TRAINER_PRO    (alter Display-Wert)
#   Premium    → VEREIN_BASIC   (alter Display-Wert)

LIZENZ_TYPEN_COMPAT: dict[str, str] = {
    # Alte interne Keys (2-Paket-System)
    "BASIC":           "TRAINER_BASIC",
    "PRO":             "VEREIN_PRO",
    "ENTERPRISE":      "VEREIN_PRO",
    # Alte Display-Werte aus modules/vereine.py Selectbox
    "BASIS":           "TRAINER_BASIC",
    "STANDARD":        "TRAINER_PRO",
    "PREMIUM":         "VEREIN_BASIC",
    "TEST (30 TAGE)":  "TRAINER_BASIC",
    "FREE":            "TRAINER_BASIC",
}

_DEFAULT_LIZENZ_TYP = "TRAINER_BASIC"


def normalize_lizenz_typ(
    raw: str | None,
    ist_technischer_mandant: bool | int | None = None,
) -> str:
    """Normalisiert einen rohen DB-Wert (alt oder neu) auf einen gültigen LIZENZ_TYPEN-Key.

    Immer sicher aufzurufen — gibt niemals einen Key zurück, der nicht in
    LIZENZ_TYPEN enthalten ist.  Unbekannte Werte landen bei TRAINER_BASIC.

    Parameter:
        raw                     Roher lizenztyp-Wert aus der DB.
        ist_technischer_mandant Wenn übergeben, wird für die Legacy-Keys
                                BASIC / PRO / Enterprise der richtige Kundentyp
                                gewählt (1 = Einzeltrainer, 0 = Verein).
                                None = kein Kontext → kontextfreier Fallback.

    Kontextabhängiges Mapping (ist_technischer_mandant bekannt):
        BASIC      + Einzeltrainer → TRAINER_BASIC
        BASIC      + Verein        → VEREIN_BASIC
        PRO        + Einzeltrainer → TRAINER_PRO
        PRO        + Verein        → VEREIN_PRO
        Enterprise + Einzeltrainer → TRAINER_PRO
        Enterprise + Verein        → VEREIN_PRO

    Kontextfreies Fallback-Mapping (kein ist_technischer_mandant):
        Wie in LIZENZ_TYPEN_COMPAT definiert (BASIC→TRAINER_BASIC,
        PRO→VEREIN_PRO, Enterprise→VEREIN_PRO).

    Reihenfolge:
      1. Leer/None → Default
      2. Exakter Treffer in LIZENZ_TYPEN → direkt zurückgeben
      3. Kontext bekannt → kontextabhängiges Mapping für BASIC/PRO/Enterprise
      4. Kontextfreier LIZENZ_TYPEN_COMPAT-Lookup
      5. Fallback → Default
    """
    if not raw:
        return _DEFAULT_LIZENZ_TYP
    upper = raw.strip().upper()

    # Schritt 2: neuer Key → direkt zurückgeben
    if upper in LIZENZ_TYPEN:
        return upper

    # Schritt 3: Kontext-gesteuertes Mapping für Legacy-Keys
    if ist_technischer_mandant is not None:
        is_trainer = bool(ist_technischer_mandant)
        _context_map: dict[str, str] = {
            "BASIC":      "TRAINER_BASIC" if is_trainer else "VEREIN_BASIC",
            "PRO":        "TRAINER_PRO"   if is_trainer else "VEREIN_PRO",
            "ENTERPRISE": "TRAINER_PRO"   if is_trainer else "VEREIN_PRO",
        }
        if upper in _context_map:
            return _context_map[upper]

    # Schritt 4: kontextfreier Fallback (Display-Werte und sonstige Legacy-Keys)
    mapped = LIZENZ_TYPEN_COMPAT.get(upper)
    if mapped and mapped in LIZENZ_TYPEN:
        return mapped

    return _DEFAULT_LIZENZ_TYP


# ─── Feature-Labels für die UI ────────────────────────────────────────────────

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
#   "expired"   — Testphase oder Lizenz abgelaufen (on-the-fly berechnet, kein DB-Write)
#   "suspended" — manuell gesperrt durch Superadmin
#   "cancelled" — Abo gekündigt, läuft noch bis Lizenzende
#   "beendet"   — Abo vollständig beendet (Stripe subscription.deleted) — Zugang gesperrt
#   "geloescht" — endgültig anonymisierter Kundendatensatz (nicht reaktivierbar)


class LizenzInfo(TypedDict):
    verein_id: int
    lizenz_typ: str            # TRAINER_BASIC | TRAINER_PRO | VEREIN_BASIC | VEREIN_PRO
    lizenz_status: str         # trial | active | expired | suspended | cancelled
    lizenz_bis: str | None     # ISO-Date oder None
    testphase_bis: str | None  # ISO-Date oder None
    gesperrt: bool
    zahlungsstatus: str        # offen | bezahlt | fehlgeschlagen | storniert
    tage_verbleibend: int | None
    ablauf_datum: date | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    cancel_at_period_end: bool  # Abo läuft noch, aber Kündigung ist aktiv
    gekuendigt_zum: str | None  # ISO-Date: Ende des laufenden Abrechnungszeitraums


def get_lizenz_info(verein_row: dict) -> LizenzInfo:
    """Berechnet den vollständigen Lizenz-Status eines Vereins.

    Normalisiert den rohen lizenztyp-Wert aus der DB automatisch auf einen
    gültigen 4-Paket-Key über normalize_lizenz_typ().
    """
    verein_id = verein_row.get("id", 0)
    cache_key = f"_lizenz_info_{verein_id}"

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    heute = date.today()

    lizenz_typ     = normalize_lizenz_typ(
        verein_row.get("lizenztyp"),
        ist_technischer_mandant=verein_row.get("ist_technischer_mandant"),
    )
    raw_status     = str(verein_row.get("lizenz_status") or "trial").lower()
    # Anonymisierte Kundenzeilen bleiben ein endgültiger Sonderfall: Sie werden
    # wegen Rechnungs-FKs aufbewahrt, haben aber kein wiederherstellbares Konto.
    ist_anonymisiert = (
        str(verein_row.get("kundennummer") or "").strip() == "[gelöscht]"
        or raw_status in ("geloescht", "gelöscht")
    )
    lizenz_status  = "geloescht" if ist_anonymisiert else raw_status
    gesperrt       = bool(verein_row.get("gesperrt", 0))
    zahlungsstatus = verein_row.get("zahlungsstatus") or "offen"

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

    # Abgelaufen-Check (on-the-fly — kein DB-Update)
    if not ist_anonymisiert and tage_verbleibend is not None and tage_verbleibend < 0:
        lizenz_status = "expired"

    if not ist_anonymisiert and gesperrt:
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
        "cancel_at_period_end":   bool(verein_row.get("cancel_at_period_end", 0)),
        "gekuendigt_zum":         verein_row.get("gekuendigt_zum"),
    }

    st.session_state[cache_key] = info
    return info


def enforce_license_gate() -> None:
    """Prüft den Lizenzstatus bei jedem Re-Run.

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
        _zeige_gesperrt_page(rolle=user.get("rolle"))
        st.stop()

    if info["lizenz_status"] in ("expired", "beendet"):
        _zeige_abgelaufen_page(info)
        st.stop()


def feature_erlaubt(
    feature: str,
    lizenz_typ: str,
    ist_technischer_mandant: bool | int | None = None,
) -> bool:
    """Prüft ob ein Feature im aktuellen Lizenztyp enthalten ist.

    Akzeptiert alte und neue Paket-Keys.  Bei Legacy-Keys (BASIC/PRO/Enterprise)
    wird ist_technischer_mandant zur korrekten Auflösung genutzt.
    """
    normed  = normalize_lizenz_typ(lizenz_typ, ist_technischer_mandant)
    typ_def = LIZENZ_TYPEN.get(normed)
    if not typ_def:
        return False
    feats = typ_def["features"]
    return "all" in feats or feature in feats


def trainer_limit_erreicht(
    verein_id: int,
    lizenz_typ: str,
    ist_technischer_mandant: bool | int | None = None,
) -> bool:
    """Gibt True zurück wenn das Trainer-Limit erreicht ist.

    None in max_trainer bedeutet unbegrenzt → gibt immer False zurück.
    Akzeptiert alte und neue Paket-Keys.  Bei Legacy-Keys wird
    ist_technischer_mandant zur korrekten Auflösung genutzt.
    """
    try:
        from database import get_conn
        with get_conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1 AND rolle='Trainer'",
                (verein_id,)
            ).fetchone()[0]
        normed  = normalize_lizenz_typ(lizenz_typ, ist_technischer_mandant)
        typ_def = LIZENZ_TYPEN.get(normed, LIZENZ_TYPEN[_DEFAULT_LIZENZ_TYP])
        max_t   = typ_def["max_trainer"]
        if max_t is None:       # unbegrenzt
            return False
        return count >= max_t
    except Exception:
        # B5: fail-closed — bei DB-Fehler KEIN Zugang gewähren (Limit gilt als erreicht)
        return True


def spieler_limit_erreicht(
    verein_id: int,
    lizenz_typ: str,
    ist_technischer_mandant: bool | int | None = None,
) -> bool:
    """Gibt True zurück wenn das Spieler-Limit erreicht ist.

    None in max_spieler bedeutet unbegrenzt → gibt immer False zurück.
    Akzeptiert alte und neue Paket-Keys.  Bei Legacy-Keys wird
    ist_technischer_mandant zur korrekten Auflösung genutzt.
    """
    try:
        from database import get_conn
        with get_conn() as conn:
            # spieler hat keine aktiv-Spalte → alle Spieler des Vereins zählen
            count = conn.execute(
                "SELECT COUNT(*) FROM spieler WHERE verein_id=?",
                (verein_id,)
            ).fetchone()[0]
        normed  = normalize_lizenz_typ(lizenz_typ, ist_technischer_mandant)
        typ_def = LIZENZ_TYPEN.get(normed, LIZENZ_TYPEN[_DEFAULT_LIZENZ_TYP])
        max_s   = typ_def["max_spieler"]
        if max_s is None:       # unbegrenzt
            return False
        return count >= max_s
    except Exception:
        # B5: fail-closed — bei DB-Fehler KEIN Zugang gewähren (Limit gilt als erreicht)
        return True


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


def _zeige_gesperrt_page(rolle: str | None = None) -> None:
    """Zeigt die Gesperrt-Karte mit rollenabhängigem Text.

    - vereinsadmin / verein  → Vereinskonto
    - trainer / einzeltrainer → Trainerkonto
    - sonst                   → neutraler Fallback
    """
    _rolle = (rolle or "").lower()
    if _rolle in ("vereinsadmin", "verein"):
        konto_art = "Vereinskonto"
    elif _rolle in ("trainer", "einzeltrainer"):
        konto_art = "Trainerkonto"
    else:
        konto_art = "Konto"

    _card(
        "#f85149", "🚫",
        "Konto gesperrt",
        f"Dein {konto_art} wurde deaktiviert. Bitte kontaktiere den APH-Support: "
        f"<a href='mailto:{SUPPORT_EMAIL}' style='color:#58a6ff;word-break:break-all'>"
        f"{SUPPORT_EMAIL}</a>",
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
