"""
Stripe-Service — Bruce Football Performance Diagnostics.

Alle Stripe-API-Aufrufe laufen zentral hier durch.
Keine API-Keys im Quellcode — ausschließlich Umgebungsvariablen.

Für den Livebetrieb:
  1. pip install stripe (in requirements.txt ergänzen)
  2. STRIPE_SECRET_KEY und STRIPE_WEBHOOK_SECRET in .env / Umgebungsvariablen setzen
  3. Stripe-Produkte und -Preise anlegen (siehe GO_LIVE_CHECKLIST.md)
  4. STRIPE_PRICE_* Env-Vars mit echten Stripe Price-IDs befüllen
"""

from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Env-Vars ──────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_ENABLED         = bool(STRIPE_SECRET_KEY)

# Stripe Price-IDs — 4-Paket-System (Phase A1)
# Unterstützt beide Suffix-Varianten: _MONAT/_MONTHLY und _JAHR/_YEARLY,
# da Secrets historisch inkonsistent benannt wurden (Mischung DE/EN).
# Schlüssel entsprechen den LIZENZ_TYPEN-Keys aus license.py.

def _price_env(base: str, short: str) -> str:
    """Liest einen Stripe-Preis aus Env-Vars mit Fallback auf alternative Suffix-Schreibweise.

    short = 'monat' → prüft {base}_MONAT, dann {base}_MONTHLY
    short = 'jahr'  → prüft {base}_JAHR,  dann {base}_YEARLY
    """
    german  = "MONAT"   if short == "monat" else "JAHR"
    english = "MONTHLY" if short == "monat" else "YEARLY"
    return (
        os.environ.get(f"{base}_{german}",  "") or
        os.environ.get(f"{base}_{english}", "") or
        ""
    )


STRIPE_PRICES: dict[str, dict[str, str]] = {
    "TRAINER_BASIC": {
        "monat": _price_env("STRIPE_PRICE_TRAINER_BASIC", "monat"),
        "jahr":  _price_env("STRIPE_PRICE_TRAINER_BASIC", "jahr"),
    },
    "TRAINER_PRO": {
        "monat": _price_env("STRIPE_PRICE_TRAINER_PRO", "monat"),
        "jahr":  _price_env("STRIPE_PRICE_TRAINER_PRO", "jahr"),
    },
    "VEREIN_BASIC": {
        "monat": _price_env("STRIPE_PRICE_VEREIN_BASIC", "monat"),
        "jahr":  _price_env("STRIPE_PRICE_VEREIN_BASIC", "jahr"),
    },
    "VEREIN_PRO": {
        "monat": _price_env("STRIPE_PRICE_VEREIN_PRO", "monat"),
        "jahr":  _price_env("STRIPE_PRICE_VEREIN_PRO", "jahr"),
    },
}

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8501")


# ── Stripe-Instanz (lazy) ─────────────────────────────────────────────────────

_stripe = None


def _get_stripe():
    """Stripe-Modul mit API-Key initialisieren (lazy, damit Import nicht bricht)."""
    global _stripe
    if _stripe is None:
        try:
            import stripe as _s
            _s.api_key = STRIPE_SECRET_KEY
            _stripe = _s
        except ImportError:
            raise RuntimeError(
                "Das 'stripe'-Paket ist nicht installiert. "
                "Führe 'pip install stripe' aus und setze STRIPE_SECRET_KEY."
            )
    return _stripe


def stripe_verfuegbar() -> bool:
    """True wenn Stripe korrekt konfiguriert ist."""
    return bool(STRIPE_SECRET_KEY)


# ── Kunden ────────────────────────────────────────────────────────────────────

def customer_erstellen(
    email: str,
    name: str,
    verein_id: int,
    metadata: dict | None = None,
) -> str:
    """Erstellt einen neuen Stripe-Kunden. Gibt die Customer-ID zurück."""
    stripe = _get_stripe()
    customer = stripe.Customer.create(
        email=email,
        name=name,
        metadata={
            "verein_id": str(verein_id),
            **(metadata or {}),
        },
    )
    logger.info(f"Stripe-Kunde erstellt: {customer.id} für Verein {verein_id}")
    return customer.id


def customer_laden(customer_id: str) -> dict:
    """Lädt einen Stripe-Kunden."""
    stripe = _get_stripe()
    return stripe.Customer.retrieve(customer_id)


# ── Checkout / Abonnement ─────────────────────────────────────────────────────

def checkout_session_erstellen(
    customer_id: str,
    price_id: str,
    verein_id: int,
    success_url: str | None = None,
    cancel_url: str | None = None,
    testphase_tage: int = 0,
    payment_method_types: list[str] | None = None,
    lizenztyp: str | None = None,
    abo_intervall: str | None = None,
) -> str:
    """Erstellt eine Stripe Checkout-Session. Gibt die Session-URL zurück.

    Immer mode="subscription".  Zahlungsmethode wird stets beim Checkout
    hinterlegt (payment_method_collection="always"), damit nach der Testphase
    die automatische Abbuchung funktioniert.

    lizenztyp / abo_intervall:
        Werden in session.metadata gespeichert, damit der Webhook nach
        checkout.session.completed den APH-Tarif eindeutig zuordnen kann.
        Zusätzlich zu verein_id — niemals aus Frontend-Daten übernehmen.

    payment_method_types:
        None  → Stripe wählt automatisch (Card + alle Dashboard-aktivierten
                Methoden, inkl. PayPal sobald im Stripe-Dashboard aktiviert).
        Liste → z. B. ["card", "paypal"] für explizite Auswahl.
                PayPal läuft vollständig über Stripe — keine eigene PayPal-API
                nötig.  Aktivierung: Stripe-Dashboard → Payment Methods → PayPal.

    Sicherheit:
        - STRIPE_SECRET_KEY wird nie geloggt.
        - Keine Price-IDs im Log (nur Session-ID und verein_id).
    """
    stripe = _get_stripe()

    # Metadata: verein_id ist Pflicht für die Webhook-Kundenzuordnung.
    # lizenztyp + abo_intervall ermöglichen Tarif-Bestätigung im Webhook.
    meta: dict[str, str] = {"verein_id": str(verein_id)}
    if lizenztyp:
        meta["lizenztyp"] = lizenztyp
    if abo_intervall:
        meta["abo_intervall"] = abo_intervall

    params: dict = {
        "customer":                  customer_id,
        # client_reference_id: stabile interne ID — robuster als E-Mail-Adresse
        "client_reference_id":       str(verein_id),
        "mode":                      "subscription",
        "line_items":                [{"price": price_id, "quantity": 1}],
        "success_url":               success_url or f"{APP_BASE_URL}/app?checkout=success",
        "cancel_url":                cancel_url  or f"{APP_BASE_URL}/app?checkout=cancel",
        "metadata":                  meta,
        "allow_promotion_codes":     True,
        # Zahlungsmethode immer sammeln — auch während der Testphase.
        # Ohne dies könnte die erste Abbuchung nach Trial-Ende fehlschlagen.
        "payment_method_collection": "always",
    }

    # Explizite Zahlungsmethoden-Liste (None = Stripe automatic)
    # PayPal-Vorbereitung: payment_method_types=["card", "paypal"] übergeben,
    # sobald PayPal im Stripe-Dashboard aktiviert ist.
    if payment_method_types is not None:
        params["payment_method_types"] = payment_method_types

    if testphase_tage > 0:
        params["subscription_data"] = {
            "trial_period_days": testphase_tage,
            # Metadata auf Subscription-Ebene für spätere Webhook-Events
            "metadata": meta,
            # Nach Trial-Ende: Abo kündigen statt stillen Fehlschlag,
            # wenn keine Zahlungsmethode hinterlegt wurde.
            "trial_settings": {
                "end_behavior": {"missing_payment_method": "cancel"}
            },
        }

    session = stripe.checkout.Session.create(**params)
    logger.info(
        "Checkout-Session erstellt: %s | Verein %d | Tarif: %s/%s | Trial: %d Tage",
        session.id, verein_id,
        lizenztyp or "–", abo_intervall or "–",
        testphase_tage,
    )
    return session.url


def billing_portal_erstellen(
    customer_id: str,
    return_url: str | None = None,
) -> str:
    """Erstellt eine Stripe Billing-Portal-Session. Gibt die URL zurück.
    Das Billing-Portal erlaubt dem Kunden Upgrade, Downgrade und Kündigung."""
    stripe = _get_stripe()
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url or f"{APP_BASE_URL}/app?section=lizenz",
    )
    return session.url


# ── Abonnement-Verwaltung ─────────────────────────────────────────────────────

def subscription_laden(subscription_id: str) -> dict:
    """Lädt ein Stripe-Abonnement."""
    stripe = _get_stripe()
    return stripe.Subscription.retrieve(subscription_id)


def subscription_kuendigen(
    subscription_id: str,
    sofort: bool = False,
) -> dict:
    """Kündigt ein Abonnement.
    sofort=False → läuft bis Periodenende (empfohlen)
    sofort=True  → sofortige Kündigung
    """
    stripe = _get_stripe()
    if sofort:
        sub = stripe.Subscription.cancel(subscription_id)
    else:
        sub = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
    logger.info(f"Abonnement gekündigt: {subscription_id} (sofort={sofort})")
    return sub


def subscription_reaktivieren(subscription_id: str) -> dict:
    """Reaktiviert ein gekündigtes Abonnement (falls noch im Abrechnungszeitraum)."""
    stripe = _get_stripe()
    sub = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=False,
    )
    logger.info(f"Abonnement reaktiviert: {subscription_id}")
    return sub


# ── Kündigung via Stripe (A6) ──────────────────────────────────────────────────

def kuendigung_vormerken(subscription_id: str) -> dict:
    """Setzt cancel_at_period_end=True in Stripe — Subscription läuft bis Periodenende.

    Wirft RuntimeError oder stripe.error.StripeError bei Fehler.
    Gibt das aktualisierte Subscription-Objekt zurück (cancel_at_period_end, current_period_end etc.).
    """
    stripe = _get_stripe()
    sub = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True,
    )
    logger.info("Stripe-Kündigung vorgemerkt: %s (cancel_at_period_end=True)", subscription_id)
    return sub


def kuendigung_widerrufen_stripe(subscription_id: str) -> dict:
    """Setzt cancel_at_period_end=False in Stripe — Subscription läuft normal weiter.

    Wirft RuntimeError oder stripe.error.StripeError bei Fehler.
    Gibt das aktualisierte Subscription-Objekt zurück.
    """
    stripe = _get_stripe()
    sub = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=False,
    )
    logger.info("Stripe-Kündigung zurückgenommen: %s (cancel_at_period_end=False)", subscription_id)
    return sub


def subscription_upgraden(
    subscription_id: str,
    neuer_price_id: str,
) -> dict:
    """Wechselt den Tarif (Upgrade oder Downgrade).
    Abrechnung wird sofort anteilig angepasst."""
    stripe = _get_stripe()
    sub = stripe.Subscription.retrieve(subscription_id)
    item_id = sub["items"]["data"][0]["id"]

    updated = stripe.Subscription.modify(
        subscription_id,
        items=[{"id": item_id, "price": neuer_price_id}],
        proration_behavior="always_invoice",
    )
    logger.info(f"Abonnement gewechselt: {subscription_id} → {neuer_price_id}")
    return updated


# ── Webhooks ──────────────────────────────────────────────────────────────────

def webhook_event_validieren(payload: bytes, sig_header: str) -> dict:
    """Validiert und gibt ein Stripe-Webhook-Event zurück.
    Wirft stripe.error.SignatureVerificationError bei ungültiger Signatur."""
    stripe = _get_stripe()
    return stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )


def webhook_event_verarbeiten(event: dict) -> dict:
    """Verarbeitet ein Stripe-Webhook-Event und gibt Aktions-Dict zurück.

    Rückgabe:
        {
          "aktion": str,          # was zu tun ist
          "verein_id": int|None,
          "customer_id": str|None,
          "subscription_id": str|None,
          "lizenz_typ": str|None,
          "lizenz_bis": str|None,  # ISO-Date
          "zahlungsstatus": str,
        }
    """
    event_type  = event.get("type", "")
    data_obj    = event.get("data", {}).get("object", {})
    metadata    = data_obj.get("metadata", {})
    verein_id   = int(metadata.get("verein_id", 0)) or None
    customer_id = data_obj.get("customer")
    sub_id      = data_obj.get("subscription") or data_obj.get("id")

    result: dict = {
        "aktion":          "ignore",
        "verein_id":       verein_id,
        "customer_id":     customer_id,
        "subscription_id": sub_id,
        "lizenz_typ":      None,
        "lizenz_bis":      None,
        "zahlungsstatus":  "offen",
    }

    if event_type == "checkout.session.completed":
        # Checkout erfolgreich → Abonnement starten
        result["aktion"] = "abo_starten"
        result["zahlungsstatus"] = "bezahlt"

    elif event_type == "invoice.payment_succeeded":
        # Zahlung erfolgreich → Lizenz verlängern
        import datetime
        period_end = data_obj.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
        if period_end:
            lizenz_bis = datetime.datetime.fromtimestamp(period_end).date().isoformat()
            result["lizenz_bis"] = lizenz_bis
        result["aktion"] = "zahlung_bestaetigen"
        result["zahlungsstatus"] = "bezahlt"

    elif event_type == "invoice.payment_failed":
        # Zahlung fehlgeschlagen → Status aktualisieren
        result["aktion"] = "zahlung_fehlgeschlagen"
        result["zahlungsstatus"] = "fehlgeschlagen"

    elif event_type == "customer.subscription.deleted":
        # Abonnement beendet → Lizenz deaktivieren
        result["aktion"] = "abo_beenden"
        result["zahlungsstatus"] = "storniert"

    elif event_type == "customer.subscription.updated":
        # Tarif geändert
        plan = data_obj.get("items", {}).get("data", [{}])[0].get("plan", {})
        nick = plan.get("nickname", "").upper()
        # Neue 4-Paket-Keys und Legacy-Keys normalisieren
        from license import normalize_lizenz_typ
        normed = normalize_lizenz_typ(nick)
        result["lizenz_typ"] = normed
        result["aktion"] = "tarif_aendern"

    logger.info(f"Webhook verarbeitet: {event_type} → Aktion: {result['aktion']}")
    return result


# ── Preis-Hilfsfunktionen ─────────────────────────────────────────────────────

def get_price_id(lizenz_typ: str, intervall: str = "monat") -> str | None:
    """Gibt die Stripe Price-ID für einen Lizenztyp und ein Intervall zurück.

    Akzeptiert alte und neue Paket-Keys — normalize_lizenz_typ() wird intern
    verwendet, damit BASIC/PRO/Enterprise auf die neuen Keys gemappt werden.

    Rückgabe:
        str   — konfigurierte Stripe Price-ID aus der Umgebungsvariablen
        None  — Env-Var ist leer oder fehlt (noch nicht konfiguriert)

    Raises:
        ValueError — bei unbekanntem Lizenztyp ODER ungültigem Intervall.
                     (Env-Var fehlt → None, nicht ValueError.)
    """
    from license import normalize_lizenz_typ, LIZENZ_TYPEN, LIZENZ_TYPEN_COMPAT

    # Rohwert-Prüfung: ist der Key überhaupt bekannt?
    # normalize_lizenz_typ() gibt bei unbekannten Werten den Default zurück —
    # deshalb muss die Validierung VOR der Normalisierung stattfinden.
    _known_raw = frozenset(LIZENZ_TYPEN) | frozenset(LIZENZ_TYPEN_COMPAT)
    _upper = (lizenz_typ or "").strip().upper()
    if not lizenz_typ or _upper not in _known_raw:
        raise ValueError(
            f"Unbekannter Lizenztyp: {lizenz_typ!r}. "
            f"Erlaubt (neue Keys): {sorted(LIZENZ_TYPEN)}"
        )

    normed = normalize_lizenz_typ(lizenz_typ)

    # Doppelte Absicherung falls normalize etwas Unerwartetes zurückgibt
    if normed not in STRIPE_PRICES:
        raise ValueError(
            f"Lizenztyp {lizenz_typ!r} → normalisiert zu {normed!r}, "
            f"aber kein Stripe-Preis konfiguriert. Erlaubt: {sorted(STRIPE_PRICES)}"
        )

    # Ungültiges Intervall → sofort ablehnen
    erlaubte_intervalle = ("monat", "jahr")
    if intervall not in erlaubte_intervalle:
        raise ValueError(
            f"Unbekanntes Intervall: {intervall!r}. "
            f"Erlaubt: {erlaubte_intervalle}"
        )

    price_id = STRIPE_PRICES[normed].get(intervall, "")
    return price_id if price_id else None


# ── Aktive-Subscription-Guard (A9) ────────────────────────────────────────────

def hat_aktive_subscription(verein_id: int) -> tuple[bool, str | None]:
    """Prüft ob für einen Verein bereits eine aktive Stripe-Subscription existiert.

    Liest stripe_subscription_id aus der DB und fragt Stripe nach dem Status.

    Rückgabe:
        (True,  subscription_id) — Subscription hat Status 'active' oder 'trialing'
        (False, subscription_id) — Subscription existiert, ist aber inaktiv
        (False, None)            — keine Subscription-ID in DB
    """
    try:
        from database import lizenz_info_laden
        row = lizenz_info_laden(verein_id) or {}
    except Exception as e:
        logger.warning(f"DB-Fehler beim Subscription-Check (verein_id={verein_id}): {e}")
        return False, None

    sub_id = row.get("stripe_subscription_id")
    if not sub_id:
        return False, None

    if not STRIPE_ENABLED:
        # Stripe nicht konfiguriert — DB-Status als Fallback nutzen
        db_status = row.get("lizenz_status", "")
        return db_status in ("active", "trial"), sub_id

    try:
        stripe = _get_stripe()
        sub = stripe.Subscription.retrieve(sub_id)
        status = sub.get("status", "")
        logger.debug(f"Subscription-Check verein={verein_id}: {sub_id} → {status}")
        return status in ("active", "trialing"), sub_id
    except Exception as e:
        logger.warning(
            f"Stripe-Subscription-Check fehlgeschlagen (verein_id={verein_id}, "
            f"sub_id={sub_id}): {e}"
        )
        return False, sub_id


# ── Paket-/Intervallwechsel (A9) ───────────────────────────────────────────────

def paket_wechseln(
    subscription_id: str,
    neue_price_id: str,
    sofort: bool = True,
) -> dict:
    """Wechselt das Paket (Upgrade oder Downgrade) einer bestehenden Subscription.

    sofort=True  (Upgrade):  sofortiger Wechsel mit anteiliger Abrechnung.
                             Stripe erstellt sofort eine Proration-Invoice.
    sofort=False (Downgrade): Wechsel ohne Proration; Abrechnungszyklus bleibt
                              unverändert (billing_cycle_anchor='unchanged').

    Gibt das aktualisierte Subscription-Objekt zurück.
    Wirft stripe.error.StripeError oder RuntimeError bei Fehler.
    """
    stripe = _get_stripe()
    sub = stripe.Subscription.retrieve(subscription_id)
    item_id = sub["items"]["data"][0]["id"]

    if sofort:
        updated = stripe.Subscription.modify(
            subscription_id,
            items=[{"id": item_id, "price": neue_price_id}],
            proration_behavior="always_invoice",
        )
        logger.info(
            "Upgrade durchgeführt: %s → price=%s (sofort, with_proration)",
            subscription_id, neue_price_id,
        )
    else:
        updated = stripe.Subscription.modify(
            subscription_id,
            items=[{"id": item_id, "price": neue_price_id}],
            proration_behavior="none",
            billing_cycle_anchor="unchanged",
        )
        logger.info(
            "Downgrade vorgemerkt: %s → price=%s (ohne Proration)",
            subscription_id, neue_price_id,
        )
    return updated


def intervall_wechseln(
    subscription_id: str,
    neue_price_id: str,
) -> dict:
    """Wechselt das Abrechnungsintervall zum Periodenende (monat ↔ jahr).

    Keine Sofortabbuchung — Wechsel ohne Proration, bestehender Zyklus bleibt.
    Gibt das aktualisierte Subscription-Objekt zurück.
    Wirft stripe.error.StripeError oder RuntimeError bei Fehler.
    """
    stripe = _get_stripe()
    sub = stripe.Subscription.retrieve(subscription_id)
    item_id = sub["items"]["data"][0]["id"]

    updated = stripe.Subscription.modify(
        subscription_id,
        items=[{"id": item_id, "price": neue_price_id}],
        proration_behavior="none",
        billing_cycle_anchor="unchanged",
    )
    logger.info(
        "Intervall gewechselt: %s → price=%s (zum Periodenende)",
        subscription_id, neue_price_id,
    )
    return updated


def get_price_id_or_raise(lizenz_typ: str, intervall: str = "monat") -> str:
    """Wie get_price_id(), aber wirft ValueError wenn die Price-ID nicht konfiguriert ist.

    Für Checkout-Flows — stellt sicher, dass keine leere Price-ID an Stripe gesendet wird.
    """
    price_id = get_price_id(lizenz_typ, intervall)
    if not price_id:
        from license import normalize_lizenz_typ
        normed  = normalize_lizenz_typ(lizenz_typ)
        env_key = f"STRIPE_PRICE_{normed}_{intervall.upper()}"
        raise ValueError(
            f"Stripe Price-ID nicht konfiguriert. "
            f"Umgebungsvariable '{env_key}' ist leer oder fehlt. "
            f"Bitte in den Stripe-Einstellungen hinterlegen."
        )
    return price_id
