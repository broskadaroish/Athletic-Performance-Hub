#!/usr/bin/env python3
"""Isolierte Regressionen für Tarif-State und Stripe-Upgrade-Übergabe."""

from __future__ import annotations

import os
import sys
import inspect
from unittest.mock import patch

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import stripe_service
from modules import lizenz_page


passed = failed = 0


def check(name: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"✅ PASS  {name}")
    else:
        failed += 1
        print(f"❌ FAIL  {name}")


class _ColumnContext:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def run_checkout_mock(typ_key: str, periode_label: str) -> tuple[object, object]:
    """Führt _stripe_upgrade ohne Stripe-Netzwerk und ohne Datenbankmutation aus."""
    periode_key = lizenz_page._upgrade_periode_key(periode_label)
    checkout = patch(
        "stripe_service.checkout_session_erstellen",
        return_value="https://checkout.test/session",
    )
    price = patch(
        "stripe_service.get_price_id",
        return_value=f"price_{typ_key}_{periode_key}",
    )
    with (
        patch("stripe_service.stripe_verfuegbar", return_value=True),
        patch.object(lizenz_page.st, "columns", return_value=[_ColumnContext(), _ColumnContext()]),
        patch.object(lizenz_page.st, "radio", return_value=periode_label),
        patch.object(lizenz_page.st, "button", return_value=True),
        patch.object(lizenz_page.st, "success"),
        patch.object(lizenz_page.st, "link_button") as link_button,
        patch.object(lizenz_page.st, "warning"),
        patch.object(lizenz_page.st, "error"),
        patch("database.stripe_ids_setzen"),
        checkout as checkout_mock,
        price,
    ):
        lizenz_page._stripe_upgrade(
            typ_key,
            12345,
            {"stripe_customer_id": "cus_test_only"},
        )
    return checkout_mock, link_button


def main() -> int:
    # Die sichtbaren Werte werden in allen vier Kombinationen in die
    # kanonischen Intervallwerte übersetzt.
    for typ_key in ("TRAINER_BASIC", "TRAINER_PRO"):
        for label, expected in (("Monatlich", "monat"), ("Jährlich (2 Monate gratis)", "jahr")):
            check(
                f"{typ_key} {expected}: sichtbares Intervall bleibt kanonisch",
                lizenz_page._upgrade_periode_key(label) == expected,
            )
            checkout, link_button = run_checkout_mock(typ_key, label)
            checkout.assert_called_once_with(
                customer_id="cus_test_only",
                price_id=f"price_{typ_key}_{expected}",
                verein_id=12345,
                lizenztyp=typ_key,
                abo_intervall=expected,
            )
            check(
                f"{typ_key} {expected}: bestehender Checkout erhält Tarif + Intervall",
                checkout.call_count == 1,
            )
            check(
                f"{typ_key} {expected}: Checkout-URL wird als Linkbutton angeboten",
                link_button.call_count == 1
                and link_button.call_args.args[:2]
                == ("→ Zu Stripe Checkout", "https://checkout.test/session"),
            )

    original_prices = stripe_service.STRIPE_PRICES
    stripe_service.STRIPE_PRICES = {
        "TRAINER_BASIC": {"monat": "basic_m", "jahr": "basic_y"},
        "TRAINER_PRO": {"monat": "pro_m", "jahr": "pro_y"},
        "VEREIN_BASIC": {"monat": "verein_basic_m", "jahr": "verein_basic_y"},
        "VEREIN_PRO": {"monat": "verein_pro_m", "jahr": "verein_pro_y"},
    }
    try:
        for typ_key, expected in (
            ("TRAINER_BASIC", "basic_m"),
            ("TRAINER_PRO", "pro_m"),
            ("VEREIN_BASIC", "verein_basic_m"),
            ("VEREIN_PRO", "verein_pro_m"),
        ):
            check(
                f"get_price_id Monats-Price für {typ_key}",
                stripe_service.get_price_id(typ_key, "monat") == expected,
            )
        for typ_key, expected in (
            ("TRAINER_BASIC", "basic_y"),
            ("TRAINER_PRO", "pro_y"),
            ("VEREIN_BASIC", "verein_basic_y"),
            ("VEREIN_PRO", "verein_pro_y"),
        ):
            check(
                f"get_price_id Jahres-Price für {typ_key}",
                stripe_service.get_price_id(typ_key, "jahr") == expected,
            )
    finally:
        stripe_service.STRIPE_PRICES = original_prices

    with (
        patch("stripe_service.stripe_verfuegbar", return_value=True),
        patch.object(lizenz_page.st, "columns", return_value=[_ColumnContext(), _ColumnContext()]),
        patch.object(lizenz_page.st, "radio", return_value="Monatlich"),
        patch.object(lizenz_page.st, "button", return_value=True),
        patch("stripe_service.get_price_id", return_value="price_error_test"),
        patch(
            "stripe_service.checkout_session_erstellen",
            side_effect=RuntimeError("internal test detail"),
        ),
        patch("stripe_service.customer_erstellen"),
        patch("database.stripe_ids_setzen"),
        patch.object(lizenz_page.st, "success"),
        patch.object(lizenz_page.st, "link_button"),
        patch.object(lizenz_page.st, "warning"),
        patch.object(lizenz_page.st, "error") as error,
        patch.object(lizenz_page._log, "exception"),
    ):
        lizenz_page._stripe_upgrade("TRAINER_BASIC", 12345, {"stripe_customer_id": "cus_test_only"})
        check(
            "Checkout-Fehler zeigt generische sichtbare Meldung",
            error.call_count == 1
            and "Der Zahlungsvorgang konnte nicht gestartet werden." in error.call_args.args[0]
            and "internal test detail" not in error.call_args.args[0],
        )

    with (
        patch("stripe_service.stripe_verfuegbar", return_value=True),
        patch.object(lizenz_page.st, "columns", return_value=[_ColumnContext(), _ColumnContext()]),
        patch.object(lizenz_page.st, "radio", return_value="Jährlich (2 Monate gratis)"),
        patch.object(lizenz_page.st, "button", return_value=True),
        patch("stripe_service.get_price_id", return_value=None),
        patch.object(lizenz_page.st, "warning") as warning,
        patch.object(lizenz_page.st, "error"),
    ):
        lizenz_page._stripe_upgrade("TRAINER_PRO", 12345, {"stripe_customer_id": "cus_test_only"})
        check(
            "Fehlende Price-ID zeigt sichtbare Meldung",
            warning.call_count == 1
            and "Stripe-Price-ID noch nicht konfiguriert" in warning.call_args.args[0],
        )

    upgrade_source = inspect.getsource(lizenz_page._stripe_upgrade)
    check(
        "Upgrade aktiviert keine Lizenz lokal",
        "lizenz_setzen(" not in upgrade_source
        and "trainer_lizenz_setzen(" not in upgrade_source
        and "stripe_subscription_id" not in upgrade_source,
    )

    print(f"\n{passed} PASS, {failed} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())