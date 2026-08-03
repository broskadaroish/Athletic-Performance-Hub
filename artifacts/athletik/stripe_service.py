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

# Stripe Price-IDs (müssen im Stripe-Dashboard angelegt werden)
STRIPE_PRICES: dict[str, dict[str, str]] = {
    "BASIC": {
        "monat": os.environ.get("STRIPE_PRICE_BASIC_MONAT", ""),
        "jahr":  os.environ.get("STRIPE_PRICE_BASIC_JAHR",  ""),
    },
    "PRO": {
        "monat": os.environ.get("STRIPE_PRICE_PRO_MONAT", ""),
        "jahr":  os.environ.get("STRIPE_PRICE_PRO_JAHR",  ""),
    },
    "ENTERPRISE": {
        "monat": os.environ.get("STRIPE_PRICE_ENT_MONAT", ""),
        "jahr":  os.environ.get("STRIPE_PRICE_ENT_JAHR",  ""),
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
) -> str:
    """Erstellt eine Stripe Checkout-Session. Gibt die URL zurück."""
    stripe = _get_stripe()
    params: dict = {
        "customer":          customer_id,
        "mode":              "subscription",
        "line_items":        [{"price": price_id, "quantity": 1}],
        "success_url":       success_url or f"{APP_BASE_URL}/app?checkout=success",
        "cancel_url":        cancel_url  or f"{APP_BASE_URL}/app?checkout=cancel",
        "metadata":          {"verein_id": str(verein_id)},
        "allow_promotion_codes": True,
    }
    if testphase_tage > 0:
        params["subscription_data"] = {"trial_period_days": testphase_tage}

    session = stripe.checkout.Session.create(**params)
    logger.info(f"Checkout-Session erstellt: {session.id} für Verein {verein_id}")
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
        if nick in ("BASIC", "PRO", "ENTERPRISE"):
            result["lizenz_typ"] = nick
        result["aktion"] = "tarif_aendern"

    logger.info(f"Webhook verarbeitet: {event_type} → Aktion: {result['aktion']}")
    return result


# ── Preis-Hilfsfunktionen ─────────────────────────────────────────────────────

def get_price_id(lizenz_typ: str, intervall: str = "monat") -> str | None:
    """Gibt die Stripe Price-ID für einen Lizenztyp zurück."""
    typ_prices = STRIPE_PRICES.get(lizenz_typ.upper(), {})
    price_id = typ_prices.get(intervall, "")
    return price_id if price_id else None
