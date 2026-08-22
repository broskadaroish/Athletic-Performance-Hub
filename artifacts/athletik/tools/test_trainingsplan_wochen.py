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
    TRAININGSPLAN_WOCHEN_OPTIONEN,
    trainingsplan_wochen_optionen,
)
from periodisierung import trainingsplan_multi_erstellen, zyklus_erstellen
from database import periodisierung_laden


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


# Die gültige Auswahl ist zentral: Starter kann nur zwei Wochen übernehmen,
# sieht aber alle verfügbaren Optionen; bezahlte Pakete sehen alle Optionen.
check(
    "Starter kann ausschließlich zwei Wochen auswählen",
    trainingsplan_wochen_optionen("STARTER_FREE") == (2,),
)
check(
    "Starter sieht alle vier Planlängen",
    TRAININGSPLAN_WOCHEN_OPTIONEN == (2, 4, 6, 8),
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
check(
    "Starter zeigt die gesperrten Planlängen sichtbar an",
    "TRAININGSPLAN_WOCHEN_OPTIONEN" in APP_SOURCE
    and "_plan_gesperrte_optionen" in APP_SOURCE
    and "_locked_woche" in APP_SOURCE
    and "Premium" in APP_SOURCE,
)
check(
    "Starter erhält einen klaren Upgrade-Hinweis",
    "Im Starter-Tarif nicht enthalten" in APP_SOURCE
    and "Längere Trainingspläne sind ab Einzeltrainer Basic verfügbar." in APP_SOURCE,
)
check(
    "Pakete ansehen führt zu Mein Vertrag",
    'st.session_state["_nav_goto"] = "📋  Mein Vertrag"' in APP_SOURCE
    and 'key="plan_wochen_upgrade_btn"' in APP_SOURCE,
)

# Periodisierung verwendet dieselbe zentrale Wochenlogik und schützt den
# Schreibpfad zusätzlich anhand des tatsächlichen Vereins des Spielers.
check(
    "Periodisierung verwendet die zentrale Lizenzhilfe",
    "trainingsplan_wochen_optionen(" in APP_SOURCE
    and "_perio_wochen_optionen" in APP_SOURCE,
)
check(
    "Periodisierung zeigt Starter-Sperren sichtbar an",
    "_perio_gesperrte_optionen" in APP_SOURCE
    and "_perio_locked_cols" in APP_SOURCE
    and "Premium" in APP_SOURCE,
)
check(
    "Periodisierung nutzt den richtigen Upgrade-Hinweis",
    "Längere Periodisierungen sind ab Einzeltrainer Basic verfügbar." in APP_SOURCE
    and 'key="perio_wochen_upgrade_btn"' in APP_SOURCE,
)
check(
    "Starter erzeugt und speichert eine 2-Wochen-Periodisierung",
    len(zyklus_erstellen(starter_spieler, {"Rumpf": 3}, wochen=2, alter=15)) > 0
    and {int(row["woche"]) for row in periodisierung_laden(starter_spieler)} == {1, 2},
)
for wochen in (4, 6, 8):
    check(
        f"Starter blockiert manipulierte {wochen}-Wochen-Periodisierung serverseitig",
        raises_value_error(
            lambda wochen=wochen: zyklus_erstellen(
                starter_spieler, {"Rumpf": 3}, wochen=wochen, alter=15
            )
        ),
    )
for paket in ("TRAINER_BASIC", "TRAINER_PRO", "VEREIN_BASIC", "VEREIN_PRO"):
    _perio_paid_spieler = spieler_fuer_paket(paket, f"Periodisierung-{paket}")
    _perio_paid_plan = zyklus_erstellen(
        _perio_paid_spieler, {"Rumpf": 3}, wochen=2, alter=15
    )
    check(
        f"{paket} erstellt eine 2-Wochen-Periodisierung",
        _perio_paid_plan and max(int(row["woche"]) for row in _perio_paid_plan) == 2,
    )
for wochen in (4, 6, 8):
    _perio_bestand_spieler = spieler_fuer_paket(
        "TRAINER_PRO", f"Periodisierung-Bestand-{wochen}"
    )
    _perio_bestand_plan = zyklus_erstellen(
        _perio_bestand_spieler, {"Rumpf": 3}, wochen=wochen, alter=15
    )
    check(
        f"Bestehende {wochen}-Wochen-Periodisierung funktioniert weiter",
        _perio_bestand_plan
        and {int(row["woche"]) for row in _perio_bestand_plan}
        == set(range(1, wochen + 1)),
    )

print("Gesamt: PASS")