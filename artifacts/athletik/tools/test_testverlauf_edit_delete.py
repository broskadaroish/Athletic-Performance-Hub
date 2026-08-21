#!/usr/bin/env python3
"""Regressionstest: historische Tests werden ausschließlich per ID mutiert."""

import importlib.util
import os
import sys
import tempfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_SOURCE = os.path.join(ROOT, "database.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
passed = failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}")


def load_database():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    spec = importlib.util.spec_from_file_location("test_history_database", DB_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DB_PATH = path
    module.init_db()
    return module, path


def main():
    db, db_path = load_database()
    try:
        with db.get_conn() as conn:
            conn.execute("INSERT INTO vereine (name) VALUES ('Testverein')")
            conn.execute(
                "INSERT INTO spieler (name, geschlecht, leistungsniveau, verein_id) "
                "VALUES ('Spieler Eins', 'Männlich', 'Leistungssport', 1)"
            )
            conn.execute(
                "INSERT INTO spieler (name, geschlecht, leistungsniveau, verein_id) "
                "VALUES ('Spieler Zwei', 'Männlich', 'Leistungssport', 1)"
            )
            conn.execute(
                """INSERT INTO sprint_test (
                    spieler_id, datum, v1_5m, v2_5m, v3_5m,
                    v1_10m, v2_10m, v3_10m, v1_20m, v2_20m, v3_20m,
                    v1_30m, v2_30m, v3_30m
                ) VALUES (1, '20.08.2026', 1.10, 1.08, 1.09,
                          1.90, 1.85, 1.88, 3.10, 3.05, 3.08,
                          4.30, 4.25, 4.28)"""
            )
            conn.execute(
                """INSERT INTO sprung_test (
                    spieler_id, datum, cmj_beid, v1_cmj_beid, v2_cmj_beid, v3_cmj_beid
                ) VALUES (1, '20.08.2026', 42, 40, 41, 42)"""
            )
            conn.execute(
                "INSERT INTO sprung_test (spieler_id, datum, cmj_beid) VALUES (1, '22.08.2026', 40)"
            )
            conn.execute(
                """INSERT INTO agilitaet_test (
                    spieler_id, datum, t_test, v1_t_test, v2_t_test, v3_t_test,
                    modified_t_test, v1_modified_t_test, v2_modified_t_test, v3_modified_t_test
                ) VALUES (1, '20.08.2026', 10, 10, 10.1, 9.9, 11, 11, 11.1, 10.9)"""
            )
            conn.execute(
                "INSERT INTO agilitaet_test (spieler_id, datum, t_test) VALUES (1, '22.08.2026', 11)"
            )
        record = db.sprint_history_edit(1)[0]
        record_id = record["id"]
        check("History-Loader liefert eindeutige ID", isinstance(record_id, int))

        check(
            "Fremdspieler kann Test nicht aktualisieren",
            not db.sprint_update(record_id, 2, "21.08.2026",
                                 1.0, None, None, 1.8, None, None,
                                 3.0, None, None, 4.1, None, None),
        )
        unchanged = db.sprint_history_edit(1)[0]
        check("Fremd-Update verändert Datum nicht", unchanged["datum"] == "20.08.2026")

        check(
            "Eigener Test wird per ID aktualisiert",
            db.sprint_update(record_id, 1, "21.08.2026",
                             1.0, None, None, 1.8, None, None,
                             3.0, None, None, 4.1, None, None),
        )
        updated = db.sprint_history_edit(1)[0]
        check("Update schreibt neues Datum", updated["datum"] == "21.08.2026")
        check("Bestzeit wird aus Rohversuch neu berechnet", updated["beste_10m"] == 1.8)

        check("Fremdspieler kann Test nicht löschen", not db.sprint_loeschen(record_id, 2))
        check("Test bleibt nach Fremd-Löschung erhalten", len(db.sprint_history_edit(1)) == 1)
        check("Eigener Test wird per ID gelöscht", db.sprint_loeschen(record_id, 1))
        check("Gelöschter Test ist nicht mehr in History", db.sprint_history_edit(1) == [])

        jump = db.sprung_history_edit(1)[0]
        jump_id = jump["id"]
        check("Sprung-Loader liefert Versuche", jump["v1_cmj_beid"] == 40)
        check(
            "Sprung-Update bewahrt unberührte Versuche",
            db.sprung_update(jump_id, 1, "21.08.2026", 43, None, None, None, None, None, None)
            and db.sprung_history_edit(1)[0]["v1_cmj_beid"] == 40,
        )
        check("Sprung-Datumskollision wird erkannt",
              db.testverlauf_datum_kollision("sprung", jump_id, 1, "22.08.2026"))
        check("Sprung-Update bei Datumskollision bricht sicher ab",
              not db.sprung_update(jump_id, 1, "22.08.2026", 43, None, None, None, None, None, None))

        agility = db.agilitaet_history_edit(1)[0]
        agility_id = agility["id"]
        check("Agilitäts-Loader liefert erweiterte Versuche",
              agility["v1_modified_t_test"] == 11)
        check(
            "Agilitäts-Update bewahrt erweiterte Versuche",
            db.agilitaet_update(agility_id, 1, "21.08.2026", 5, 5, 6, 9, 12)
            and db.agilitaet_history_edit(1)[0]["v1_modified_t_test"] == 11,
        )
        check("Agilitäts-Datumskollision wird erkannt",
              db.testverlauf_datum_kollision("agilitaet", agility_id, 1, "22.08.2026"))
        check("Agilitäts-Update bei Datumskollision bricht sicher ab",
              not db.agilitaet_update(agility_id, 1, "22.08.2026", 5, 5, 6, 9, 12))
    finally:
        os.unlink(db_path)

    print(f"\nErgebnis: {passed} PASS, {failed} FAIL")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()