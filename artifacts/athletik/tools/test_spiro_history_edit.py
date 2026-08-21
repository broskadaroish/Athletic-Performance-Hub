#!/usr/bin/env python3
"""Regressionstest für atomare Korrekturen historischer Spiro-Messpunkte."""

import importlib.util
import os
import sqlite3
import sys
import tempfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_SOURCE = os.path.join(ROOT, "database.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def load_database():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    spec = importlib.util.spec_from_file_location("test_spiro_history_database", DB_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DB_PATH = path
    module.init_db()
    return module, path


def check(label, condition):
    print(f"  {'PASS' if condition else 'FAIL'}  {label}")
    return bool(condition)


def main():
    db, db_path = load_database()
    passed = True
    try:
        with db.get_conn() as conn:
            conn.execute("INSERT INTO vereine (name) VALUES ('Testverein')")
            for name in ("Spieler Eins", "Spieler Zwei"):
                conn.execute(
                    "INSERT INTO spieler (name, geschlecht, leistungsniveau, verein_id) VALUES (?, 'Männlich', 'Leistungssport', 1)",
                    (name,),
                )

        test_id = db.spiro_test_speichern(
            1, "2026-08-20", "spiro_laufband", geraeteart="Laufband",
            maximale_geschwindigkeit=16.0, bemerkung="vorher",
        )
        db.spiro_stufen_speichern(test_id, [{
            "stufennummer": 1, "geschwindigkeit_kmh": 10.0, "herzfrequenz_bpm": 155,
            "laktat_mmol_l": 2.2, "stufe_vollstaendig": True, "blutprobe_gueltig": True,
        }])
        db.spiro_nachbelastung_speichern(test_id, [{
            "zeitpunkt_minuten": 3, "herzfrequenz_bpm": 130, "laktat_mmol_l": 4.0,
        }])

        passed &= check(
            "Fremdspieler kann Haupttest und Messpunkte nicht ändern",
            not db.spiro_test_update_mit_messpunkten(
                test_id, 2, "2026-08-21", "spiro_laufband", [], [],
                geraeteart="Laufband", maximale_geschwindigkeit=18.0,
            ),
        )
        unchanged = db.spiro_history_edit(1)[0]
        passed &= check("Fremd-Update lässt Haupttest unverändert", unchanged["datum"] == "2026-08-20")
        passed &= check(
            "Fremd-Update lässt Stufen unverändert",
            db.spiro_stufen_laden(test_id)[0]["geschwindigkeit_kmh"] == 10.0,
        )
        passed &= check(
            "Fremd-Update lässt Nachbelastung unverändert",
            db.spiro_nachbelastung_laden(test_id)[0]["zeitpunkt_minuten"] == 3,
        )

        neue_stufen = [{
            "stufennummer": 1, "geschwindigkeit_kmh": 10.5, "steigung_prozent": 1.0,
            "dauer_sekunden": 180, "strecke_meter": 525, "herzfrequenz_bpm": 158,
            "hf_durchschnitt": 153, "vo2_relativ": 42.3, "vo2_absolut": 3.1,
            "vco2": 3.2, "ve": 98.4, "rer": 1.03, "atemfrequenz": 42,
            "sauerstoffpuls": 19.7, "laktat_mmol_l": 2.5, "rpe": 6,
            "stufe_vollstaendig": True, "blutprobe_gueltig": False, "bemerkung": "korrigiert",
        }]
        neue_nb = [{
            "zeitpunkt_minuten": 5, "herzfrequenz_bpm": 122, "laktat_mmol_l": 5.2,
            "bemerkung": "Peak",
        }]
        passed &= check(
            "Eigener Test aktualisiert Haupttest und Messpunkte",
            db.spiro_test_update_mit_messpunkten(
                test_id, 1, "2026-08-21", "spiro_laufband", neue_stufen, neue_nb,
                geraeteart="Laufband", maximale_geschwindigkeit=18.0, bemerkung="nachher",
            ),
        )
        updated = db.spiro_history_edit(1)[0]
        stage = db.spiro_stufen_laden(test_id)[0]
        after = db.spiro_nachbelastung_laden(test_id)[0]
        passed &= check("Haupttest wurde aktualisiert", updated["datum"] == "2026-08-21" and updated["maximale_geschwindigkeit"] == 18.0)
        passed &= check("Alle korrigierten Stufenwerte wurden gespeichert", stage["vo2_relativ"] == 42.3 and stage["blutprobe_gueltig"] == 0 and stage["bemerkung"] == "korrigiert")
        passed &= check("Nachbelastungswerte wurden gespeichert", after["zeitpunkt_minuten"] == 5 and after["laktat_mmol_l"] == 5.2 and after["bemerkung"] == "Peak")

        try:
            db.spiro_test_update_mit_messpunkten(
                test_id, 1, "2026-08-22", "spiro_laufband",
                [{"stufennummer": None}], neue_nb,
                geraeteart="Laufband", maximale_geschwindigkeit=19.0,
            )
        except sqlite3.IntegrityError:
            rollback_ausgeloest = True
        else:
            rollback_ausgeloest = False
        rollback_haupttest = db.spiro_history_edit(1)[0]
        rollback_stufe = db.spiro_stufen_laden(test_id)[0]
        rollback_nachbelastung = db.spiro_nachbelastung_laden(test_id)[0]
        passed &= check("Ungültiger Kinddatensatz löst Transaktions-Rollback aus", rollback_ausgeloest)
        passed &= check(
            "Rollback bewahrt Haupttest und alle Messpunkte",
            rollback_haupttest["datum"] == "2026-08-21"
            and rollback_stufe["geschwindigkeit_kmh"] == 10.5
            and rollback_nachbelastung["zeitpunkt_minuten"] == 5,
        )

        passed &= check("Sicheres Löschen akzeptiert nur eigene Test-ID", db.spiro_test_loeschen_sicher(test_id, 1))
        with db.get_conn() as conn:
            child_count = conn.execute(
                "SELECT COUNT(*) FROM spiro_stufe WHERE spiro_test_id=? UNION ALL SELECT COUNT(*) FROM spiro_nachbelastung WHERE spiro_test_id=?",
                (test_id, test_id),
            ).fetchall()
        passed &= check("Löschen entfernt weiterhin alle Kinddaten", all(row[0] == 0 for row in child_count))
    finally:
        os.unlink(db_path)

    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()