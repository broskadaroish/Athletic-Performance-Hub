"""Regressionen für die Katalogauswahl im Trainingsplan-Editor."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TMP_DB = Path(tempfile.mkdtemp(prefix="aph-editor-catalog-")) / "editor_catalog.db"
os.environ["ATHLETIK_DB_PATH"] = str(TMP_DB)

import database
from database import (
    get_conn,
    init_db,
    plan_eintrag_aktualisieren,
    plan_laden_nach_version,
    plan_version_erstellen,
    trainingsplan_eintrag_speichern,
)
from periodisierung import katalog_uebungen_fuer_bereich

database.DB_PATH = str(TMP_DB)
init_db()


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


with get_conn() as conn:
    spieler_id = conn.execute(
        "INSERT INTO spieler (name, vorname, nachname) VALUES ('Katalog Test', 'Katalog', 'Test')"
    ).lastrowid

version_id = plan_version_erstellen(spieler_id, "2026-08-21", "test", "Manuell")
trainingsplan_eintrag_speichern(
    spieler_id, "2026-08-21", 1, "Rumpf", "Plank", "3", "40 Sekunden", "3×/Woche",
    tag=1, plan_id=version_id,
)
entry = plan_laden_nach_version(version_id)[0]

# 1–2: Bereichsabhängiger, zentraler Katalog und bestehende Vorauswahl.
rumpf_katalog = katalog_uebungen_fuer_bereich("Rumpf", "U14")
knie_katalog = katalog_uebungen_fuer_bereich("Knie", "U14")
check("Katalogübung wird im ursprünglichen Bereich vorausgewählt", entry["uebung"] in rumpf_katalog)
check("Bereichswechsel liefert einen anderen passenden Katalog", rumpf_katalog != knie_katalog and len(knie_katalog) > 0)

# 3–4: Katalog- und freie Übungsnamen nutzen unverändert den bestehenden Speicherpfad.
neue_kataloguebung = next(name for name in rumpf_katalog if name != entry["uebung"])
plan_eintrag_aktualisieren(entry["id"], bereich="Rumpf", uebung=neue_kataloguebung)
entry = plan_laden_nach_version(version_id)[0]
check("Ausgewählte Katalogübung wird korrekt gespeichert", entry["uebung"] == neue_kataloguebung)

eigene_uebung = "Eigene Rotationsübung"
plan_eintrag_aktualisieren(entry["id"], bereich="Rumpf", uebung=eigene_uebung)
entry = plan_laden_nach_version(version_id)[0]
check("Freie eigene Übung wird korrekt gespeichert", entry["uebung"] == eigene_uebung)

# 5–6: Nicht katalogisierte Namen bleiben erhalten, solange nicht gespeichert wird.
check("Unbekannte bestehende Übung bleibt als freie Eingabe erhalten", entry["uebung"] not in rumpf_katalog)
entry_ohne_speichern = plan_laden_nach_version(version_id)[0]
check("Abbrechen oder kein Speichern verändert den Eintrag nicht", entry_ohne_speichern["uebung"] == eigene_uebung)

APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
check("Editor verwendet den zentralen Katalog-Helper", "katalog_uebungen_fuer_bereich(_e_bereich, _tv_pg)" in APP_SOURCE)
check("Editor bietet die freie Eingabe an", 'key=_e_custom_key' in APP_SOURCE)
check("Bereich und Übungswahl stehen vor dem Speicherformular", APP_SOURCE.index("_e_katalog = katalog_uebungen_fuer_bereich") < APP_SOURCE.index('with st.form(f"form_edit_{eid}"', APP_SOURCE.index("_e_katalog = katalog_uebungen_fuer_bereich")))

print("Gesamt: PASS")