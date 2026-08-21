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


def hauptwerte_aus(test, **aenderungen):
    """Vollständige Haupttest-Payload für den transaktionalen Verlauf-Save."""
    felder = (
        "geraeteart", "protokoll_id", "testort", "tester", "mit_spiro", "mit_laktat",
        "raumtemperatur", "letzte_mahlzeit", "letzte_intensive_einheit",
        "akute_beschwerden", "koerpergewicht", "maximale_geschwindigkeit",
        "maximale_herzfrequenz", "vo2_peak", "vo2_max", "geschaetzte_vo2max",
        "vt1_geschwindigkeit", "vt1_herzfrequenz", "vt2_geschwindigkeit",
        "vt2_herzfrequenz", "laktatschwelle_methode", "schwelle_geschwindigkeit",
        "schwelle_herzfrequenz", "schwelle_laktat", "ruhelaktat",
        "laktat_blutentnahmeort", "laktat_messgeraet", "rpe_max",
        "abbruchgrund", "bemerkung",
    )
    werte = {feld: test.get(feld) for feld in felder}
    werte.update(aenderungen)
    return werte


def stufen_payload(stufe, **aenderungen):
    felder = (
        "stufennummer", "geschwindigkeit_kmh", "steigung_prozent", "dauer_sekunden",
        "strecke_meter", "herzfrequenz_bpm", "hf_durchschnitt", "vo2_absolut",
        "vo2_relativ", "vco2", "ve", "rer", "atemfrequenz", "sauerstoffpuls",
        "laktat_mmol_l", "rpe", "stufe_vollstaendig", "blutprobe_gueltig", "bemerkung",
    )
    werte = {"id": stufe["id"], **{feld: stufe.get(feld) for feld in felder}}
    werte.update(aenderungen)
    return werte


def nachbelastung_payload(nachwert, **aenderungen):
    werte = {
        "id": nachwert["id"],
        "zeitpunkt_minuten": nachwert.get("zeitpunkt_minuten"),
        "herzfrequenz_bpm": nachwert.get("herzfrequenz_bpm"),
        "laktat_mmol_l": nachwert.get("laktat_mmol_l"),
        "bemerkung": nachwert.get("bemerkung"),
    }
    werte.update(aenderungen)
    return werte


def main():
    db, db_path = load_database()
    passed = True
    try:
        with db.get_conn() as conn:
            conn.execute("INSERT INTO vereine (name) VALUES ('Testverein Eins')")
            conn.execute("INSERT INTO vereine (name) VALUES ('Testverein Zwei')")
            for name, verein_id in (("Spieler Eins", 1), ("Spieler Zwei", 1), ("Spieler Drei", 2)):
                conn.execute(
                    "INSERT INTO spieler (name, geschlecht, leistungsniveau, verein_id) VALUES (?, 'Männlich', 'Leistungssport', ?)",
                    (name, verein_id),
                )

        test_id = db.spiro_test_speichern(
            1, "2026-08-20", "spiro_laufband", geraeteart="Laufband",
            maximale_geschwindigkeit=14.0, maximale_herzfrequenz=180,
            vo2_peak=52.5, vo2_max=50.2,
            laktatschwelle_methode="Fixer Wert 2 mmol/l", bemerkung="vorher",
        )
        db.spiro_stufen_speichern(test_id, [
            {
                "stufennummer": 1, "geschwindigkeit_kmh": 10.0, "herzfrequenz_bpm": 150,
                "laktat_mmol_l": 1.0, "stufe_vollstaendig": True, "blutprobe_gueltig": True,
            },
            {
                "stufennummer": 2, "geschwindigkeit_kmh": 14.0, "herzfrequenz_bpm": 180,
                "laktat_mmol_l": 5.0, "stufe_vollstaendig": True, "blutprobe_gueltig": True,
            },
        ])
        db.spiro_nachbelastung_speichern(test_id, [
            {"zeitpunkt_minuten": 3, "herzfrequenz_bpm": 130, "laktat_mmol_l": 4.0},
            {"zeitpunkt_minuten": 5, "herzfrequenz_bpm": 120, "laktat_mmol_l": 5.0},
        ])

        passed &= check(
            "Fremdspieler kann Haupttest und Messpunkte nicht ändern",
            not db.spiro_test_update_mit_messpunkten(
                test_id, 2, "2026-08-21", "spiro_laufband", [], [],
                geraeteart="Laufband", maximale_geschwindigkeit=18.0,
            ),
        )
        unchanged = db.spiro_history_edit(1)[0]
        passed &= check("Fremd-Update lässt Haupttest unverändert", unchanged["datum"] == "2026-08-20")
        stufen_vorher = db.spiro_stufen_laden(test_id)
        nachbelastung_vorher = db.spiro_nachbelastung_laden(test_id)
        stufe_eins, stufe_zwei = stufen_vorher
        nachbelastung_eins, nachbelastung_zwei = nachbelastung_vorher

        passed &= check(
            "Fremder Spieler kann einzelne Stufe nicht ändern",
            not db.spiro_stufe_aktualisieren(
                stufe_eins["id"], test_id, 2, {"geschwindigkeit_kmh": 11.0},
                benutzer_id=2, rolle="Trainer", verein_id=1,
            ),
        )
        passed &= check(
            "Falscher Mandant kann einzelne Stufe nicht ändern",
            not db.spiro_stufe_aktualisieren(
                stufe_eins["id"], test_id, 1, {"geschwindigkeit_kmh": 11.0},
                benutzer_id=3, rolle="Vereinsadmin", verein_id=2,
            ),
        )
        passed &= check(
            "Genau die gewählte Stufen-ID wird geändert",
            db.spiro_stufe_aktualisieren(
                stufe_zwei["id"], test_id, 1,
                {
                    "geschwindigkeit_kmh": 16.0, "steigung_prozent": 1.0,
                    "dauer_sekunden": 180, "strecke_meter": 800,
                    "herzfrequenz_bpm": 185, "hf_durchschnitt": 179,
                    "vo2_relativ": 42.3, "vo2_absolut": 3.1, "vco2": 3.2,
                    "ve": 98.4, "rer": 1.03, "atemfrequenz": 42,
                    "sauerstoffpuls": 19.7, "laktat_mmol_l": 3.0, "rpe": 6,
                    "stufe_vollstaendig": True, "blutprobe_gueltig": True,
                    "bemerkung": "korrigiert",
                },
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            ),
        )
        stufen_nach_update = db.spiro_stufen_laden(test_id)
        test_nach_update = db.spiro_history_edit(1)[0]
        passed &= check(
            "Unberührte Stufe behält ihre ID und Werte",
            stufen_nach_update[0]["id"] == stufe_eins["id"]
            and stufen_nach_update[0]["geschwindigkeit_kmh"] == 10.0,
        )
        passed &= check(
            "Geänderte Stufe behält ihre ID",
            stufen_nach_update[1]["id"] == stufe_zwei["id"]
            and stufen_nach_update[1]["geschwindigkeit_kmh"] == 16.0,
        )
        passed &= check(
            "Geschwindigkeit und HF aktualisieren stufenbasierte Maximalwerte",
            test_nach_update["maximale_geschwindigkeit"] == 16.0
            and test_nach_update["maximale_herzfrequenz"] == 185.0,
        )
        passed &= check(
            "2-mmol-Interpolation wird aus den korrigierten Stufen aktualisiert",
            test_nach_update["schwelle_geschwindigkeit"] == 13.0
            and test_nach_update["schwelle_herzfrequenz"] == 167.5
            and test_nach_update["schwelle_laktat"] == 2.0,
        )
        passed &= check(
            "Direkt gemessene VO₂-Werte bleiben unverändert",
            test_nach_update["vo2_peak"] == 52.5 and test_nach_update["vo2_max"] == 50.2,
        )
        passed &= check(
            "Nachbelastung aktualisiert nur die gewählte ID",
            db.spiro_nachbelastung_aktualisieren(
                nachbelastung_zwei["id"], test_id, 1,
                {"zeitpunkt_minuten": 6, "herzfrequenz_bpm": 116,
                 "laktat_mmol_l": 5.4, "bemerkung": "Peak"},
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            ),
        )
        passed &= check(
            "Falscher Mandant kann Nachbelastung nicht ändern",
            not db.spiro_nachbelastung_aktualisieren(
                nachbelastung_eins["id"], test_id, 1, {"herzfrequenz_bpm": 99},
                benutzer_id=3, rolle="Vereinsadmin", verein_id=2,
            ),
        )
        nachbelastung_nach_update = db.spiro_nachbelastung_laden(test_id)
        passed &= check(
            "Unberührte Nachbelastung bleibt erhalten",
            nachbelastung_nach_update[0]["id"] == nachbelastung_eins["id"]
            and nachbelastung_nach_update[0]["zeitpunkt_minuten"] == 3,
        )
        passed &= check(
            "Geänderte Nachbelastung behält ihre ID",
            nachbelastung_nach_update[1]["id"] == nachbelastung_zwei["id"]
            and nachbelastung_nach_update[1]["zeitpunkt_minuten"] == 6,
        )
        stale_hauptwerte = hauptwerte_aus(
            test_nach_update,
            maximale_geschwindigkeit=16.0,
            maximale_herzfrequenz=185.0,
            laktatschwelle_methode="Fixer Wert 4 mmol/l",
            schwelle_geschwindigkeit=13.0,
            schwelle_herzfrequenz=167.5,
            schwelle_laktat=2.0,
        )
        stufen_batch = [
            stufen_payload(stufen_nach_update[0]),
            stufen_payload(stufen_nach_update[1], geschwindigkeit_kmh=18.0,
                           herzfrequenz_bpm=190.0, laktat_mmol_l=5.0),
        ]
        nachbelastung_batch = [
            nachbelastung_payload(nachbelastung_nach_update[0]),
            nachbelastung_payload(nachbelastung_nach_update[1], zeitpunkt_minuten=7),
        ]
        passed &= check(
            "Transaktionaler Verlauf-Save behält IDs und leitet finale Werte ab",
            db.spiro_test_update_mit_einzelmesspunkten(
                test_id, 1, "2026-08-20", "spiro_laufband",
                stufen_batch, nachbelastung_batch,
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
                **stale_hauptwerte,
            )
            and [s["id"] for s in db.spiro_stufen_laden(test_id)]
                == [stufe_eins["id"], stufe_zwei["id"]]
            and db.spiro_history_edit(1)[0]["maximale_geschwindigkeit"] == 18.0
            and db.spiro_history_edit(1)[0]["maximale_herzfrequenz"] == 190.0
            and db.spiro_history_edit(1)[0]["schwelle_geschwindigkeit"] == 16.0
            and db.spiro_history_edit(1)[0]["schwelle_herzfrequenz"] == 180.0
            and db.spiro_history_edit(1)[0]["schwelle_laktat"] == 4.0
            and db.spiro_history_edit(1)[0]["vo2_peak"] == 52.5
            and db.spiro_nachbelastung_laden(test_id)[1]["zeitpunkt_minuten"] == 7,
        )
        stand_vor_rollback = db.spiro_history_edit(1)[0]
        stufen_vor_rollback = db.spiro_stufen_laden(test_id)
        nachbelastung_vor_rollback = db.spiro_nachbelastung_laden(test_id)
        ungueltige_stufen = [
            stufen_payload(stufen_vor_rollback[0], geschwindigkeit_kmh=11.0),
            stufen_payload(stufen_vor_rollback[1], stufennummer=None),
        ]
        passed &= check(
            "Fehlerhafte spätere Stufe rollt Haupttest und alle Messpunkte zurück",
            not db.spiro_test_update_mit_einzelmesspunkten(
                test_id, 1, "2026-08-30", "spiro_laufband",
                ungueltige_stufen,
                [nachbelastung_payload(nachwert) for nachwert in nachbelastung_vor_rollback],
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
                **hauptwerte_aus(stand_vor_rollback, bemerkung="darf nicht speichern"),
            )
            and db.spiro_history_edit(1)[0]["datum"] == stand_vor_rollback["datum"]
            and db.spiro_history_edit(1)[0]["bemerkung"] == stand_vor_rollback["bemerkung"]
            and db.spiro_stufen_laden(test_id)[0]["geschwindigkeit_kmh"]
                == stufen_vor_rollback[0]["geschwindigkeit_kmh"]
            and db.spiro_nachbelastung_laden(test_id)[1]["zeitpunkt_minuten"]
                == nachbelastung_vor_rollback[1]["zeitpunkt_minuten"],
        )
        passed &= check(
            "Einzelnes Löschen einer Nachbelastung lässt andere erhalten",
            db.spiro_nachbelastung_loeschen(
                nachbelastung_zwei["id"], test_id, 1,
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            )
            and [e["id"] for e in db.spiro_nachbelastung_laden(test_id)] == [nachbelastung_eins["id"]],
        )
        passed &= check(
            "4-mmol-Interpolation wird aus den korrigierten Stufen aktualisiert",
            db.spiro_stufe_aktualisieren(
                stufe_zwei["id"], test_id, 1, {"laktat_mmol_l": 5.0},
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            )
            and db.spiro_history_edit(1)[0]["schwelle_geschwindigkeit"] == 16.0
            and db.spiro_history_edit(1)[0]["schwelle_laktat"] == 4.0,
        )
        passed &= check(
            "Fehlende Laktatbasis wird als nicht verfügbar gespeichert",
            db.spiro_stufe_aktualisieren(
                stufe_zwei["id"], test_id, 1, {"laktat_mmol_l": 1.5},
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            )
            and db.spiro_history_edit(1)[0]["schwelle_geschwindigkeit"] is None
            and db.spiro_history_edit(1)[0]["schwelle_laktat"] is None,
        )
        passed &= check(
            "Einzelnes Löschen einer Stufe lässt Haupttest und andere Stufen erhalten",
            db.spiro_stufe_loeschen(
                stufe_zwei["id"], test_id, 1,
                benutzer_id=1, rolle="Vereinsadmin", verein_id=1,
            )
            and [s["id"] for s in db.spiro_stufen_laden(test_id)] == [stufe_eins["id"]]
            and db.spiro_history_edit(1)[0]["maximale_geschwindigkeit"] == 10.0
            and db.spiro_history_edit(1)[0]["maximale_herzfrequenz"] == 150.0,
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