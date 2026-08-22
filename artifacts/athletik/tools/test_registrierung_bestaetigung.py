"""Regressionen für Registrierung, Verifizierung und Bestätigungsansicht."""

from __future__ import annotations

import ast
import os
import shutil
import sys
import tempfile


APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import auth
import database as db


TMP = tempfile.mkdtemp(prefix="test_registrierung_bestaetigung_")
PATH = os.path.join(TMP, "registrierung.db")
ORIGINAL_DB_PATH = db.DB_PATH
ORIGINAL_AUTH_DB_PATH = auth.DB_PATH
db.DB_PATH = PATH
auth.DB_PATH = PATH
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


def _pruefe_pending_konto(
    *,
    benutzer_id: int,
    email: str,
    passwort: str,
    label: str,
) -> None:
    before = db.benutzer_by_id(benutzer_id) or {}
    check(
        f"{label}: Registrierung startet unverifiziert und wartet auf Freischaltung",
        not before.get("email_verifiziert") and not before.get("aktiv"),
    )
    token = db.email_token_erzeugen(benutzer_id)
    check(
        f"{label}: Resend-Cooldown bleibt nach Token-Erzeugung aktiv",
        not db.email_token_resend_erlaubt(benutzer_id),
    )
    check(
        f"{label}: E-Mail-Verifizierung akzeptiert den vorhandenen Token",
        db.email_token_validieren(token) == benutzer_id,
    )
    after = db.benutzer_by_id(benutzer_id) or {}
    check(
        f"{label}: E-Mail-Verifizierung aktiviert das Konto nicht",
        bool(after.get("email_verifiziert")) and not after.get("aktiv"),
    )
    login_result = auth.login(email, passwort)
    check(
        f"{label}: Login bleibt bis zur Freischaltung blockiert",
        isinstance(login_result, dict)
        and bool(login_result.get("wartend_auf_freischaltung")),
    )


def _app_quelltext_pruefen() -> None:
    source = open(os.path.join(APP_ROOT, "app.py"), encoding="utf-8").read()
    tree = ast.parse(source)
    state_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_registrierung_erfolg_speichern"
    )
    state_dict = next(
        node
        for node in ast.walk(state_function)
        if isinstance(node, ast.Dict)
    )
    state_keys = {
        key.value
        for key in state_dict.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    expected = (
        "✅ Registrierung erfolgreich",
        "Wir haben dir eine Bestätigungs-E-Mail geschickt.",
        "E-Mail gesendet an:",
        "Keine E-Mail erhalten? Bitte prüfe auch deinen Spam-Ordner.",
        "📧 E-Mail erneut senden",
        "🔐 Zur Anmeldung",
        "✅ **E-Mail-Adresse bestätigt**",
        "Dein Konto wartet jetzt auf die Freischaltung durch APH.",
    )
    check(
        "Bestätigungsansicht enthält alle vorgesehenen Hinweise und Aktionen",
        all(text in source for text in expected),
    )
    check(
        "Alle Registrierungswege öffnen dieselbe persistente Bestätigungsansicht",
        source.count("_registrierung_erfolg_speichern(") == 4,
    )
    check(
        "Bestätigungs-State speichert weder Passwort noch Token",
        state_keys == {"benutzer_id", "email", "email_gesendet"},
    )


def main() -> int:
    _app_quelltext_pruefen()

    for paket in ("STARTER_FREE", "TRAINER_BASIC", "TRAINER_PRO"):
        email = f"{paket.lower()}@trainer.test"
        bid = db.trainer_registrieren(
            "Trainer",
            paket,
            email,
            "sicheres-passwort",
            benutzername=f"trainer_{paket.lower()}",
            lizenztyp=paket,
        )
        _pruefe_pending_konto(
            benutzer_id=bid,
            email=email,
            passwort="sicheres-passwort",
            label=paket,
        )

    verein_fuer_beitritt = None
    for paket in ("VEREIN_BASIC", "VEREIN_PRO"):
        email = f"{paket.lower()}@verein.test"
        verein_id, bid = db.verein_registrieren(
            f"Verein {paket}",
            "Vereins",
            "Admin",
            email,
            "sicheres-passwort",
            benutzername=f"verein_{paket.lower()}",
            lizenztyp=paket,
        )
        _pruefe_pending_konto(
            benutzer_id=bid,
            email=email,
            passwort="sicheres-passwort",
            label=paket,
        )
        if paket == "VEREIN_PRO":
            verein_fuer_beitritt = verein_id

    beitritt_email = "beitritt@verein.test"
    beitritt_id = db.trainer_verein_beitreten(
        verein_fuer_beitritt,
        "Beitritts",
        "Trainer",
        beitritt_email,
        "sicheres-passwort",
        benutzername="beitritt_trainer",
    )
    _pruefe_pending_konto(
        benutzer_id=beitritt_id,
        email=beitritt_email,
        passwort="sicheres-passwort",
        label="Trainer-Vereinsbeitritt",
    )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        db.DB_PATH = ORIGINAL_DB_PATH
        auth.DB_PATH = ORIGINAL_AUTH_DB_PATH
        shutil.rmtree(TMP, ignore_errors=True)