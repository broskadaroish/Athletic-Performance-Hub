"""Gezielte Regressionen für Trainingsplan-Editor V2 und Warm-up-Steuerung.

Verwendet eine temporäre SQLite-Datei. Bestehende Entwicklungsdaten bleiben
unberührt.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TMP_DB = Path(tempfile.mkdtemp(prefix="aph-editor-v2-")) / "editor_v2.db"
os.environ["ATHLETIK_DB_PATH"] = str(TMP_DB)

import database
from database import (
    get_conn,
    init_db,
    plan_eintrag_aktualisieren,
    plan_eintrag_verteilen,
    plan_laden_nach_version,
    plan_aktive_version,
    plan_version_aktivieren,
    plan_version_erstellen,
    plan_version_verwerfen,
    plan_versionen_laden,
    plan_warmup_speichern,
    trainingsplan_eintrag_speichern,
)
from pdf_report import generate_trainingsplan_pdf
from periodisierung import empfohlene_athletik_tage, trainingsplan_multi_erstellen
from warmup import (
    APH_STANDARD,
    FIFA_INDIVIDUELL,
    FIFA_KOMPLETT,
    KEIN_WARMUP,
    WARMUP_BEREICH,
    warmup_details,
    warmup_meta_lesen,
)

# config.py kann beim Import bereits einen anderen Pfad gesetzt haben.
database.DB_PATH = str(TMP_DB)
init_db()


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


with get_conn() as conn:
    p1 = conn.execute(
        "INSERT INTO spieler (name,vorname,nachname) VALUES ('Test Eins','Test','Eins')"
    ).lastrowid
    p2 = conn.execute(
        "INSERT INTO spieler (name,vorname,nachname) VALUES ('Test Zwei','Test','Zwei')"
    ).lastrowid

version = plan_version_erstellen(p1, "2026-08-21", "test", "Manuell", trainingszeit_min=60)
trainingsplan_eintrag_speichern(
    p1, "2026-08-21", 1, "Explosivität", "Squat Jump", "3", "6", "1×/Woche",
    tag=1, pause_sekunden=90,
    ausfuehrung="Explosiv springen, weich landen.", rpe=7,
    equipment="Körpergewicht", begruendung="Test", plan_id=version,
    notiz="Plan-Notiz",
)
entry = plan_laden_nach_version(version)[0]

# A: manueller Speicherpfad
check("A1 Ausführung speicherbar", entry["ausfuehrung"] == "Explosiv springen, weich landen.")
check("A2 Pause speicherbar", entry["pause_sekunden"] == 90)
check("A3 RPE speicherbar", entry["rpe"] == 7)
check("A4 Equipment speicherbar", entry["equipment"] == "Körpergewicht")
check("A5 Tag speicherbar", entry["tag"] == 1)
check("A6 Woche speicherbar", entry["woche"] == 1)

# B: bestehender Editor verwendet dieselbe Update-Funktion
plan_eintrag_aktualisieren(
    entry["id"], ausfuehrung="Stabil landen.", tag=2, woche=2
)
entry = plan_laden_nach_version(version)[0]
check("B7 Ausführung änderbar", entry["ausfuehrung"] == "Stabil landen.")
check("B8 Tag änderbar", entry["tag"] == 2)
check("B9 Woche änderbar", entry["woche"] == 2)

# C: Verteilung kopiert, respektiert Planlänge im UI und verhindert Duplikate im DB-Helfer.
result = plan_eintrag_verteilen(p1, version, entry["id"], [1, 2, 3, 4], [1, 2])
rows = [r for r in plan_laden_nach_version(version) if r["bereich"] != WARMUP_BEREICH]
coords = {(r["woche"], r["tag"]) for r in rows}
check("C10 nur eine Woche / Ausgangsblock bleibt", (2, 2) in coords)
check("C11 mehrere Wochen kopiert", all((w, 1) in coords for w in [1, 2, 3, 4]))
check("C12 alle gewählten Wochen vorhanden", all((w, 2) in coords for w in [1, 2, 3, 4]))
check("C13 nur ein Tag verteilbar", result["erstellt"] > 0)
check("C14 mehrere Tage verteilbar", len({tag for _, tag in coords}) == 2)
check("C15 keine Duplikate", plan_eintrag_verteilen(p1, version, entry["id"], [1, 2, 3, 4], [1, 2])["erstellt"] == 0)
check("C16 fremder Spieler nicht kopierbar", plan_eintrag_verteilen(p2, version, entry["id"], [1], [1])["erstellt"] == 0)
check("C17 Häufigkeit passend aktualisiert", any(r["haeufigkeit"] == "2×/Woche" for r in rows))

# D: alle Warm-up-Arten, Teil-2-Level und Legacy-Fallback
check("D18 APH Standard-Warm-up", plan_warmup_speichern(
    p1, version, 1, 1, APH_STANDARD, aph_dauer_min=10
))
check("D19 FIFA 11+ komplett", plan_warmup_speichern(p1, version, 1, 2, FIFA_KOMPLETT, 2))
check("D20 FIFA 11+ individuell", plan_warmup_speichern(p1, version, 2, 1, FIFA_INDIVIDUELL, 3, ["Teil 1", "Teil 3"]))
check("D21 FIFA Teil 2 Level 1", warmup_details(FIFA_KOMPLETT, 1)["dauer_min"] == 26)
check("D22 FIFA Teil 2 Level 2", "Level 2" in warmup_details(FIFA_KOMPLETT, 2)["hinweis"])
check("D23 FIFA Teil 2 Level 3", "Level 3" in warmup_details(FIFA_KOMPLETT, 3)["hinweis"])
check("D24 unterschiedliche Wochen speicherbar", plan_warmup_speichern(p1, version, 3, 1, APH_STANDARD))
check("D25 unterschiedliche Tage speicherbar", plan_warmup_speichern(p1, version, 3, 2, FIFA_KOMPLETT, 1))
check("D26 kein Warm-up speicherbar", plan_warmup_speichern(p1, version, 4, 1, KEIN_WARMUP))

plan_rows = plan_laden_nach_version(version)
warmups = [r for r in plan_rows if r["bereich"] == WARMUP_BEREICH]
aph = next(r for r in warmups if r["woche"] == 1 and r["tag"] == 1)
custom = next(r for r in warmups if r["woche"] == 2 and r["tag"] == 1)
none = next(r for r in warmups if r["woche"] == 4 and r["tag"] == 1)
check("D27 Legacy-Plan erhält APH-Fallback", warmup_meta_lesen(None)["legacy"] is True)
check("D28 individuelle Teile erhalten", warmup_meta_lesen(custom)["teile"] == ["Teil 1", "Teil 3"])
check("D29 kein Warm-up unterscheidet sich vom Legacy-Fallback", warmup_meta_lesen(none)["art"] == KEIN_WARMUP)
check("D30 gespeicherte APH-Dauer ist kanonisch", warmup_meta_lesen(aph)["aph_dauer_min"] == 10)
check("D31 UI-Details nutzen gespeicherte APH-Dauer", warmup_details(
    APH_STANDARD, aph_dauer_min=warmup_meta_lesen(aph)["aph_dauer_min"]
)["dauer_min"] == 10)

# E: PDF erhält dieselben gespeicherten Warm-up-Zeilen.
pdf = generate_trainingsplan_pdf(
    spieler={"vorname": "Test", "nachname": "Eins", "mannschaft": "U15", "hauptposition": "MF"},
    plan_rows=plan_rows,
    plangruppe="U14",
    plangruppen_config={"label": "Jugend", "max_saetze": 3, "haeuf_cap": "3×/Woche", "pause_offset": 0},
    legacy_warmup_min=10,
)
check("E32 PDF für gespeicherte Warm-ups erzeugbar", pdf.startswith(b"%PDF") and len(pdf) > 1000)

# F: Strukturierte Defizit-Scores bleiben im Plan- und Vereinsbelastungspfad nutzbar.
with get_conn() as conn:
    p3 = conn.execute(
        "INSERT INTO spieler (name,vorname,nachname) VALUES ('Test Drei','Test','Drei')"
    ).lastrowid

scores = {"Schnelligkeit": 3, "Rumpf": 2}
tage = empfohlene_athletik_tage(
    anzahl=1,
    verein_tage=["Dienstag", "Donnerstag"],
    spiel_tage=["Samstag"],
    alter=15,
    schwerpunkt_text=scores,
)
check("F33 Vereinsbelastung akzeptiert strukturierte Scores", len(tage) == 1)

dict_version = plan_version_erstellen(p3, "2026-08-21", "test", "Diagnostik")
dict_plan_count = trainingsplan_multi_erstellen(
    p3, scores, wochen=4, alter=15, plan_id=dict_version
)
dict_plan = plan_laden_nach_version(dict_version)
check("F34 Planerstellung akzeptiert strukturierte Scores", dict_plan_count > 0 and len(dict_plan) > 0)
check("F35 strukturierte Schnelligkeit erreicht den Plan", any(
    row["bereich"] == "Schnelligkeit" for row in dict_plan
))

# G: Neue Versionen bleiben bis zur erfolgreichen Planerzeugung ein Entwurf.
with get_conn() as conn:
    p4 = conn.execute(
        "INSERT INTO spieler (name,vorname,nachname) VALUES ('Test Vier','Test','Vier')"
    ).lastrowid

old_version = plan_version_erstellen(p4, "2026-08-21", "test", "Basis")
draft_version = plan_version_erstellen(
    p4, "2026-08-21", "test", "Diagnostik", status="ENTWURF"
)
check("G36 Entwurf ersetzt den aktiven Plan noch nicht", plan_aktive_version(p4)["id"] == old_version)
check("G37 erfolgreicher Entwurf wird atomar aktiviert", plan_version_aktivieren(p4, draft_version))
check("G38 Aktivierung archiviert erst dann den alten Plan", plan_aktive_version(p4)["id"] == draft_version)

failed_draft = plan_version_erstellen(
    p4, "2026-08-21", "test", "Diagnostik", status="ENTWURF"
)
check("G39 fehlgeschlagener Entwurf wird verworfen", plan_version_verwerfen(p4, failed_draft))
check("G40 verworfener Entwurf bleibt nicht in der Historie", all(
    version["id"] != failed_draft for version in plan_versionen_laden(p4)
))

print("\nGesamt: PASS")