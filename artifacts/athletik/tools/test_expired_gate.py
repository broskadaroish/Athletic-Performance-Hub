#!/usr/bin/env python3
"""Regressionen für die sichere Vertragsnavigation abgelaufener Kunden."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from license import _abgelaufen_zugang_erlaubt, get_lizenz_info


passed = failed = 0


def check(label: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"✅ PASS  {label}")
    else:
        failed += 1
        print(f"❌ FAIL  {label}")


def expired_info(lizenztyp: str) -> dict:
    return get_lizenz_info(
        {
            "id": 1,
            "lizenztyp": lizenztyp,
            "lizenz_status": "trial",
            "testphase_bis": "2000-01-01",
            "aktiv": 1,
            "gesperrt": 0,
        }
    )


def main() -> int:
    for lizenztyp in ("TRAINER_BASIC", "TRAINER_PRO", "STARTER_FREE", "VEREIN_BASIC"):
        check(
            f"{lizenztyp}: abgelaufene Trial wird als expired bewertet",
            expired_info(lizenztyp)["lizenz_status"] == "expired",
        )

    check(
        "Mein Vertrag ist über die Pending-Navigation erreichbar",
        _abgelaufen_zugang_erlaubt({"_nav_goto": "📋  Mein Vertrag"}),
    )
    check(
        "Mein Vertrag bleibt nach dem Rerun erreichbar",
        _abgelaufen_zugang_erlaubt({"nav_section": "📋  Mein Vertrag"}),
    )
    check(
        "Profil bleibt im sicheren Ablaufzugang erreichbar",
        _abgelaufen_zugang_erlaubt({"nav_section": "👤  Mein Profil"}),
    )
    check(
        "Fachbereich bleibt im Ablaufzugang gesperrt",
        not _abgelaufen_zugang_erlaubt({"nav_section": "🔬  Diagnostik"}),
    )
    check(
        "Startseite öffnet den Ablaufzugang nicht",
        not _abgelaufen_zugang_erlaubt({"nav_section": "🏠  Startseite"}),
    )

    license_source = (ROOT / "license.py").read_text(encoding="utf-8")
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    check(
        "Ablauf-Gate verweist nicht mehr auf die entfernte Lizenz-Seite",
        "Zur Lizenz-Seite" not in license_source
        and "?section=lizenz" not in license_source,
    )
    check(
        "Ablauf-Gate bietet Paket auswählen / Mein Vertrag",
        "📋 Paket auswählen / Mein Vertrag" in license_source
        and 'st.session_state["_nav_goto"] = "📋  Mein Vertrag"' in license_source,
    )
    check(
        "Beendete Abos erhalten über denselben Button keinen Navigations-Leerlauf",
        'info["lizenz_status"] in ("expired", "beendet")' in license_source,
    )
    check(
        "Ablauf-Gate erklärt Datenerhalt und Paketwahl",
        "Deine Daten bleiben gespeichert." in license_source
        and "Wähle ein Paket, um APH weiter zu nutzen" in license_source,
    )
    check(
        "Ablaufzugang beschränkt die App auf sichere Bereiche",
        'if st.session_state.get("_lizenz_abgelaufen"):' in app_source
        and '("👤  Mein Profil", "📋  Mein Vertrag", "ℹ️  Über")' in app_source,
    )
    check(
        "Fachliche Seitendaten laden bei Ablauf nicht",
        'alle_spieler = [] if st.session_state.get("_lizenz_abgelaufen")' in app_source,
    )
    check(
        "Superadmin-Lizenzverwaltung bleibt unverändert",
        '"💳  Lizenzverwaltung"' in app_source
        and 'elif section == "💳  Lizenzverwaltung":' in app_source,
    )

    print(f"\n{passed} PASS, {failed} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())