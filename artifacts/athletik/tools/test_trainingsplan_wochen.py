"""Regressionen für Planlängen und STARTER_FREE-Trainingspläne.

Verwendet ausschließlich eine temporäre SQLite-Datenbank.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TMP_DB = Path(tempfile.mkdtemp(prefix="aph-planwochen-")) / "planwochen.db"
os.environ["ATHLETIK_DB_PATH"] = str(TMP_DB)

import database
from database import (
    get_conn,
    init_db,
    plan_laden_nach_version,
    plan_version_aktivieren,
    plan_version_erstellen,
    trainingsplan_eintrag_speichern,
)
from license import (
    STARTER_MAX_TRAININGSPLAN_WOCHEN,
    trainingsplan_wochen_optionen,
)
from periodisierung import trainingsplan_multi_erstellen


database.DB_PATH = str(TMP_DB)
init_db()


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


def raises_value_error(callback) -> bool:
    try:
        callback()
    except ValueError:
        return True
    return False


def spieler_fuer_paket(lizenztyp: str, suffix: str) -> int:
    with get_conn() as conn:
        verein_id = conn.execute(
            """INSERT INTO vereine (name, aktiv, lizenztyp, lizenz_status)
               VALUES (?, 1, ?, 'trial')""",
            (f"Planwochen {suffix}", lizenztyp),
        ).lastrowid
        return conn.execute(
            """INSERT INTO spieler (name, vorname, nachname, verein_id)
               VALUES (?, 'Plan', 'Test', ?)""",
            (f"Plan {suffix}", verein_id),
        ).lastrowid


def entwurf_mit_plan(spieler_id: int, wochen: int) -> int:
    plan_id = plan_version_erstellen(
        spieler_id,
        "2026-08-22",
        "Regression",
        "Diagnostik",
        status="ENTWURF",
    )
    anzahl = trainingsplan_multi_erstellen(
        spieler_id,
        {"Rumpf": 3, "Schnelligkeit": 2},
        wochen=wochen,
        alter=15,
        plan_id=plan_id,
    )
    plan = plan_laden_nach_version(plan_id)
    check(
        f"{wochen}-Wochen-Plan wird vollständig erzeugt",
        anzahl > 0 and {int(row["woche"]) for row in plan} == set(range(1, wochen + 1)),
    )
    return plan_id


# Die Paket-Auswahl ist zentral: Starter nur zwei Wochen, alle anderen Pakete
# erhalten die bestehende Auswahl ergänzt um zwei Wochen.
check(
    "Starter sieht ausschließlich zwei Wochen",
    trainingsplan_wochen_optionen("STARTER_FREE") == (2,),
)
for paket in ("TRAINER_BASIC", "TRAINER_PRO", "VEREIN_BASIC", "VEREIN_PRO"):
    check(
        f"{paket} sieht 2, 4, 6 und 8 Wochen",
        trainingsplan_wochen_optionen(paket) == (2, 4, 6, 8),
    )

# STARTER_FREE kann zwei Wochen erzeugen und der serverseitige Guard blockiert
# nachträglich manipulierte dritte Wochen weiterhin.
starter_spieler = spieler_fuer_paket("STARTER_FREE", "Starter")
starter_plan = entwurf_mit_plan(starter_spieler, 2)
check(
    "Starter-Entwurf wird mit zwei Wochen aktiviert",
    plan_version_aktivieren(starter_spieler, starter_plan),
)
check(
    "Starter blockiert eine manipulierte dritte Woche serverseitig",
    raises_value_error(
        lambda: trainingsplan_eintrag_speichern(
            starter_spieler,
            "2026-08-22",
            STARTER_MAX_TRAININGSPLAN_WOCHEN + 1,
            "Rumpf",
            "Plank",
            "3",
            "30 Sekunden",
            "2×/Woche",
            plan_id=starter_plan,
        )
    ),
)

# Jede bezahlte Paketfamilie kann die neue 2-Wochen-Option tatsächlich nutzen.
for paket in ("TRAINER_BASIC", "TRAINER_PRO", "VEREIN_BASIC", "VEREIN_PRO"):
    spieler_id = spieler_fuer_paket(paket, paket)
    plan_id = entwurf_mit_plan(spieler_id, 2)
    check(f"{paket} aktiviert einen 2-Wochen-Plan", plan_version_aktivieren(spieler_id, plan_id))

# Die bestehenden höheren Generator-Konfigurationen bleiben unabhängig von einem
# konkreten Paket verfügbar.
for wochen in (4, 6, 8):
    spieler_id = spieler_fuer_paket("TRAINER_PRO", f"Pro-{wochen}")
    entwurf_mit_plan(spieler_id, wochen)

check(
    "Ungültige Planlänge fällt nicht still auf acht Wochen zurück",
    raises_value_error(
        lambda: trainingsplan_multi_erstellen(
            starter_spieler,
            {"Rumpf": 3},
            wochen=3,
            alter=15,
        )
    ),
)

APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
check(
    "Planlängen-Auswahl verwendet die zentrale Lizenzhilfe",
    "trainingsplan_wochen_optionen(" in APP_SOURCE,
)

print("Gesamt: PASS")