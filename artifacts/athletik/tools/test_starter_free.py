"""Isolierte Regressionen für die einmalige STARTER_FREE-Testphase."""

from __future__ import annotations

import os
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, timedelta

# Die Datei soll sowohl aus artifacts/athletik als auch aus tools/ direkt
# ausführbar sein, ohne einen externen PYTHONPATH vorauszusetzen.
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import database as db
from license import LIZENZ_TYPEN, get_lizenz_info, ist_starter_lizenz
from modules.lizenz_page import (
    _limit_label,
    _sa_normalize,
    _upgrade_target_laden,
    _upgrade_target_setzen,
)


TMP = tempfile.mkdtemp(prefix="test_starter_free_")
PATH = os.path.join(TMP, "starter.db")
ORIGINAL_PATH = db.DB_PATH
db.DB_PATH = PATH
db.init_db()

passed = failed = 0


def check(name: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"✅ PASS  {name}")
    else:
        failed += 1
        print(f"❌ FAIL  {name}")


def raises_value_error(callback) -> bool:
    try:
        callback()
    except ValueError:
        return True
    return False


def stripe_prices_with_env(updates: dict[str, str]) -> dict[str, str]:
    """Lädt license.py isoliert mit einem kontrollierten Env-Satz."""
    names = [
        "STRIPE_PRICE_TRAINER_BASIC_MONAT",
        "STRIPE_PRICE_TRAINER_BASIC_MONTHLY",
        "STRIPE_PRICE_TRAINER_BASIC_JAHR",
        "STRIPE_PRICE_TRAINER_BASIC_YEARLY",
        "STRIPE_PRICE_TRAINER_PRO_MONAT",
        "STRIPE_PRICE_TRAINER_PRO_MONTHLY",
        "STRIPE_PRICE_TRAINER_PRO_JAHR",
        "STRIPE_PRICE_TRAINER_PRO_YEARLY",
        "STRIPE_PRICE_VEREIN_BASIC_MONAT",
        "STRIPE_PRICE_VEREIN_BASIC_MONTHLY",
        "STRIPE_PRICE_VEREIN_BASIC_JAHR",
        "STRIPE_PRICE_VEREIN_BASIC_YEARLY",
        "STRIPE_PRICE_VEREIN_PRO_MONAT",
        "STRIPE_PRICE_VEREIN_PRO_MONTHLY",
        "STRIPE_PRICE_VEREIN_PRO_JAHR",
        "STRIPE_PRICE_VEREIN_PRO_YEARLY",
    ]
    env = os.environ.copy()
    for name in names:
        env.pop(name, None)
    env.update(updates)
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            (
                "import json, license; "
                "print(json.dumps({"
                "'monat': license.LIZENZ_TYPEN['TRAINER_BASIC']['stripe_price_monat'], "
                "'jahr': license.LIZENZ_TYPEN['TRAINER_BASIC']['stripe_price_jahr'], "
                "'starter_monat': license.LIZENZ_TYPEN['STARTER_FREE']['stripe_price_monat'], "
                "'starter_jahr': license.LIZENZ_TYPEN['STARTER_FREE']['stripe_price_jahr']"
                "}))"
            ),
        ],
        cwd=APP_ROOT,
        env=env,
        text=True,
    )
    return json.loads(output)


def main() -> int:
    trainer_id = db.trainer_registrieren(
        "Starter", "Tester", "starter-free@test.invalid", "sicheres-passwort",
        benutzername="starterfree",
        lizenztyp="STARTER_FREE",
    )
    with db.get_conn() as conn:
        verein = conn.execute(
            "SELECT * FROM vereine WHERE id=(SELECT verein_id FROM benutzer WHERE id=?)",
            (trainer_id,),
        ).fetchone()
        verein_id = int(verein["id"])
        invoice_count = conn.execute(
            "SELECT COUNT(*) FROM rechnungsadressen WHERE benutzer_id=?", (trainer_id,)
        ).fetchone()[0]
        benutzer_kundennummer = conn.execute(
            "SELECT kundennummer FROM benutzer WHERE id=?", (trainer_id,)
        ).fetchone()["kundennummer"]

    check("Starter ist ein kanonischer eigener Lizenztyp", ist_starter_lizenz("STARTER_FREE"))
    check("FREE bleibt nicht Starter", not ist_starter_lizenz("FREE", True))
    check("Starter hat ein Trainerlimit von 1", LIZENZ_TYPEN["STARTER_FREE"]["max_trainer"] == 1)
    check("Starter hat ein Spielerlimit von 5", LIZENZ_TYPEN["STARTER_FREE"]["max_spieler"] == 5)
    check("Starter startet als Trial", verein["lizenz_status"] == "trial")
    check(
        "Starter-Testphase dauert 30 Tage",
        verein["testphase_bis"] == (date.today() + timedelta(days=30)).isoformat(),
    )
    check("Starter legt keinen Stripe-Kunden an", not verein["stripe_customer_id"])
    check("Starter legt keine Stripe-Subscription an", not verein["stripe_subscription_id"])
    check("Starter legt keine Rechnungsadresse an", invoice_count == 0)
    monthly = stripe_prices_with_env({
        "STRIPE_PRICE_TRAINER_BASIC_MONTHLY": "price_monthly_test",
    })
    yearly = stripe_prices_with_env({
        "STRIPE_PRICE_TRAINER_BASIC_YEARLY": "price_yearly_test",
    })
    legacy_month = stripe_prices_with_env({
        "STRIPE_PRICE_TRAINER_BASIC_MONAT": "price_monat_test",
    })
    legacy_year = stripe_prices_with_env({
        "STRIPE_PRICE_TRAINER_BASIC_JAHR": "price_jahr_test",
    })
    priority = stripe_prices_with_env({
        "STRIPE_PRICE_TRAINER_BASIC_MONAT": "price_primary_month",
        "STRIPE_PRICE_TRAINER_BASIC_MONTHLY": "price_fallback_month",
        "STRIPE_PRICE_TRAINER_BASIC_JAHR": "price_primary_year",
        "STRIPE_PRICE_TRAINER_BASIC_YEARLY": "price_fallback_year",
    })
    check("MONTHLY wird als Monats-Price erkannt", monthly["monat"] == "price_monthly_test")
    check("YEARLY wird als Jahres-Price erkannt", yearly["jahr"] == "price_yearly_test")
    check("MONAT funktioniert weiterhin", legacy_month["monat"] == "price_monat_test")
    check("JAHR funktioniert weiterhin", legacy_year["jahr"] == "price_jahr_test")
    check(
        "MONAT/JAHR haben Priorität vor MONTHLY/YEARLY",
        priority["monat"] == "price_primary_month"
        and priority["jahr"] == "price_primary_year",
    )
    check(
        "STARTER_FREE bleibt ohne Stripe-Price",
        not monthly["starter_monat"] and not yearly["starter_jahr"],
    )
    check(
        "TRAINER_PRO mit max_spieler=None zeigt unbegrenzt Spieler",
        _limit_label(LIZENZ_TYPEN["TRAINER_PRO"]["max_spieler"]) == "unbegrenzt",
    )
    check(
        "Paketkarten zeigen niemals None Spieler",
        f"{_limit_label(LIZENZ_TYPEN['TRAINER_PRO']['max_spieler'])} Spieler"
        == "unbegrenzt Spieler",
    )
    upgrade_state = {}
    _upgrade_target_setzen("TRAINER_BASIC", upgrade_state)
    check(
        "Basic-Tarif bleibt über Reruns ausgewählt",
        _upgrade_target_laden(upgrade_state) == "TRAINER_BASIC",
    )
    _upgrade_target_setzen("TRAINER_PRO", upgrade_state)
    check(
        "Pro-Tarif bleibt über Reruns ausgewählt",
        _upgrade_target_laden(upgrade_state) == "TRAINER_PRO",
    )
    check(
        "Upgrade-State verwendet einen stabilen gemeinsamen Key",
        "_aph_upgrade_target" in open(
            os.path.join(APP_ROOT, "modules", "lizenz_page.py"),
            encoding="utf-8",
        ).read(),
    )
    kunden = db.kunden_liste_laden()
    lizenz_trainer = db.alle_trainer_lizenz()
    starter_kunde = next(
        (row for row in kunden if row.get("benutzer_id") == trainer_id),
        None,
    )
    starter_lizenz = next(
        (row for row in lizenz_trainer if row.get("id") == trainer_id),
        None,
    )
    check(
        "Starter erscheint einmalig in der Kundenverwaltung",
        starter_kunde is not None
        and starter_kunde["kundentyp"] == "Einzeltrainer"
        and sum(1 for row in kunden if row.get("benutzer_id") == trainer_id) == 1,
    )
    check(
        "Starter erscheint in der Lizenzverwaltung als Einzeltrainer",
        starter_lizenz is not None
        and starter_lizenz["lizenztyp"] == "STARTER_FREE"
        and starter_lizenz["vertrag_verein_id"] == verein_id,
    )
    check(
        "Starter behält die vorhandene Kundennummer",
        starter_kunde is not None
        and starter_kunde["kundennummer"] == benutzer_kundennummer,
    )
    check(
        "Starter-Testphase und Ablaufdatum werden zentral geführt",
        starter_lizenz is not None
        and starter_lizenz["lizenz_status"] == "trial"
        and starter_lizenz["testphase_bis"] == verein["testphase_bis"],
    )
    starter_admin_zeile = next(
        row for row in _sa_normalize([], lizenz_trainer)
        if row["_id"] == trainer_id
    )
    check(
        "Lizenzverwaltung zeigt Starter-Ablauf und verbleibende Tage",
        starter_admin_zeile["lizenz_bis"] == verein["testphase_bis"]
        and starter_admin_zeile["_tage"] == 30
        and starter_admin_zeile["_display_status"] == "testphase",
    )
    kpis = db.dashboard_sa_kpis()
    check(
        "Superadmin-Kennzahlen zählen Starter als Kunden und Testphase",
        kpis["n_kunden_gesamt"] == 1 and kpis["n_trial"] == 1,
    )

    for i in range(5):
        db.spieler_speichern(
            f"Spieler{i}", "Test", "01.01.2010", "m",
            "Mittelfeld", "", "U16", "Rechts", "Verein", "A", "aktiv",
            trainer_id=trainer_id, verein_id=verein_id,
        )
    check(
        "Sechster Spieler wird serverseitig blockiert",
        raises_value_error(
            lambda: db.spieler_speichern(
                "Spieler6", "Test", "02.01.2010", "m", "Mittelfeld", "", "U16",
                "Rechts", "Verein", "A", "aktiv", trainer_id=trainer_id, verein_id=verein_id,
            )
        ),
    )
    with db.get_conn() as conn:
        other_verein = conn.execute(
            """INSERT INTO vereine (name, aktiv, lizenztyp, lizenz_status)
               VALUES ('Quellverein', 1, 'TRAINER_BASIC', 'trial')"""
        ).lastrowid
        fremder_spieler = conn.execute(
            "INSERT INTO spieler (name, verein_id) VALUES ('Verschiebung Test', ?)",
            (other_verein,),
        ).lastrowid
    check(
        "Spieler-Verschiebung über das Starterlimit wird blockiert",
        raises_value_error(
            lambda: db.spieler_trainer_zuweisen(fremder_spieler, None, verein_id)
        ),
    )
    check(
        "Zweiter Trainer wird serverseitig blockiert",
        raises_value_error(
            lambda: db.benutzer_speichern(
                verein_id, "Zweiter", "Trainer", "zweiter-trainer@test.invalid",
                "sicheres-passwort", "Trainer", benutzername="zweiterstarter",
            )
        ),
    )

    player_id = db.spieler_laden()[0]["id"]
    plan_id = db.plan_version_erstellen(player_id, str(date.today()), status="ENTWURF")
    db.trainingsplan_eintrag_speichern(
        player_id, str(date.today()), 1, "Kraft", "Kniebeuge", "3", "8", "2x",
        tag=1, plan_id=plan_id,
    )
    db.trainingsplan_eintrag_speichern(
        player_id, str(date.today()), 1, "Kraft", "Rudern", "3", "8", "2x",
        tag=2, plan_id=plan_id,
    )
    check(
        "Dritter Trainingstag pro Woche wird serverseitig blockiert",
        raises_value_error(
            lambda: db.trainingsplan_eintrag_speichern(
                player_id, str(date.today()), 1, "Kraft", "Ausfallschritt", "3", "8", "2x",
                tag=3, plan_id=plan_id,
            )
        ),
    )
    db.trainingsplan_eintrag_speichern(
        player_id, str(date.today()), 2, "Kraft", "Step-up", "3", "8", "2x",
        tag=1, plan_id=plan_id,
    )
    check(
        "Dritte Planwoche wird serverseitig blockiert",
        raises_value_error(
            lambda: db.trainingsplan_eintrag_speichern(
                player_id, str(date.today()), 3, "Kraft", "Rudern", "3", "8", "2x",
                tag=1, plan_id=plan_id,
            )
        ),
    )
    check(
        "Warm-up kann keine dritte Planwoche umgehen",
        raises_value_error(
            lambda: db.plan_warmup_speichern(
                player_id, plan_id, 3, 1, "APH-Standard"
            )
        ),
    )
    rows = db.trainingsplan_laden(player_id)
    tag2_row = next(row for row in rows if row["woche"] == 1 and row["tag"] == 2)
    db.plan_eintrag_aktualisieren(tag2_row["id"], tag=3)
    week2_row = next(row for row in db.trainingsplan_laden(player_id) if row["woche"] == 2)
    check(
        "Planbearbeitung kann keinen dritten Tag umgehen",
        raises_value_error(
            lambda: db.plan_eintrag_aktualisieren(week2_row["id"], woche=1, tag=2)
        ),
    )
    check("Zweiwöchiger Starter-Plan ist aktivierbar", db.plan_version_aktivieren(player_id, plan_id))

    expired = dict(verein)
    expired["testphase_bis"] = (date.today() - timedelta(days=1)).isoformat()
    info = get_lizenz_info(expired)
    check("Abgelaufener Starter wird als expired bewertet", info["lizenz_status"] == "expired")
    check(
        "Bezahlpakete bleiben unverändert definiert",
        LIZENZ_TYPEN["TRAINER_BASIC"]["preis_monat"] == 9.99
        and LIZENZ_TYPEN["TRAINER_PRO"]["preis_monat"] == 14.99,
    )
    app_source = open(
        os.path.join(APP_ROOT, "app.py"), encoding="utf-8"
    ).read()
    contract_source = open(
        os.path.join(APP_ROOT, "modules", "mein_vertrag.py"), encoding="utf-8"
    ).read()
    license_source = open(
        os.path.join(APP_ROOT, "license.py"), encoding="utf-8"
    ).read()
    check(
        "Starter-Sperrbutton navigiert zu Mein Vertrag",
        'st.session_state["_nav_goto"] = "📋  Mein Vertrag"' in app_source,
    )
    check(
        "Mein Vertrag zeigt Basic und Pro als Starter-Ziele",
        '(\"TRAINER_BASIC\", \"TRAINER_PRO\")' in contract_source,
    )
    check(
        "Mein Vertrag enthält den Starter-Upgradebereich",
        "Paket wechseln / Upgrade" in contract_source,
    )
    check(
        "Starter-Sperrtext erlaubt Upgrade sofort",
        "Upgrade auf Basic oder Pro" in license_source
        and "nach Ablauf deiner Testphase" not in license_source,
    )
    check(
        "Kundennavigation enthält keinen separaten Lizenzbereich",
        '_MAIN_SECTIONS = _MAIN_SECTIONS + ["💳  Lizenz"]' not in app_source,
    )
    check(
        "Abgelaufener Starter behält Profil, Vertrag und Über",
        '("👤  Mein Profil", "📋  Mein Vertrag", "ℹ️  Über")' in app_source
        and '"💳  Lizenz"' not in app_source.split(
            'if st.session_state.get("_lizenz_abgelaufen"):', 1
        )[1].split("with st.sidebar:", 1)[0],
    )
    check(
        "Superadmin-Lizenzverwaltung bleibt erhalten",
        '"💳  Lizenzverwaltung"' in app_source
        and 'elif section == "💳  Lizenzverwaltung":' in app_source,
    )

    print(f"\n{passed} PASS, {failed} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        db.DB_PATH = ORIGINAL_PATH
        shutil.rmtree(TMP, ignore_errors=True)