#!/usr/bin/env python3
"""
Test: Spieler-Löschen-Abdeckung

Liest aus dem live SQLite-Schema alle Tabellen, die einen Fremdschlüssel auf
spieler(id) haben, und prüft, ob jede davon entweder:
  (a) ON DELETE CASCADE besitzt (SQLite kaskadiert automatisch), oder
  (b) in der manuellen Löschliste von spieler_loeschen() in database.py steht.

Der Test schlägt fehl, sobald eine neue Tabelle hinzukommt, die beide
Bedingungen nicht erfüllt — bevor das Problem in Produktion landet.

Aufruf: python3 tools/test_spieler_loeschen.py
"""

import sys
import os
import re
import sqlite3
import tempfile

# ── Pfade ─────────────────────────────────────────────────────────────────────

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_SRC = os.path.join(ROOT, "database.py")

# ── Test-Infrastruktur ────────────────────────────────────────────────────────

_pass = 0
_fail = 0


def ok(name: str) -> None:
    global _pass
    _pass += 1
    print(f"  ✅ PASS  {name}")


def fail(name: str, reason: str = "") -> None:
    global _fail
    _fail += 1
    print(f"  ❌ FAIL  {name}" + (f"\n         Grund: {reason}" if reason else ""))


def check(name: str, condition: bool, reason: str = "") -> None:
    if condition:
        ok(name)
    else:
        fail(name, reason)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _manual_list_from_source() -> list[str]:
    """Extrahiert die Tabellenliste aus spieler_loeschen() per Regex."""
    with open(DB_SRC, encoding="utf-8") as f:
        src = f.read()

    # Bereich zwischen 'def spieler_loeschen(' und dem nächsten 'def '
    m = re.search(
        r"def spieler_loeschen\(.*?\n(.*?)(?=\ndef |\Z)",
        src,
        re.DOTALL,
    )
    if not m:
        return []

    body = m.group(1)
    # Alle String-Literale in der for-Liste herausziehen
    return re.findall(r'"([a-z_]+)"', body)


def _build_temp_db() -> sqlite3.Connection:
    """Legt eine In-Memory-Datenbank an, indem database.py's init_db() aufgerufen wird.

    Da init_db() den konfigurierten DB_PATH verwendet, arbeiten wir mit einer
    temporären Datei, damit keine echten Daten berührt werden.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return tmp.name


def _fk_tables_from_schema(conn: sqlite3.Connection) -> dict[str, bool]:
    """Gibt {tabelle: hat_cascade} für alle Tabellen zurück, die einen FK
    auf spieler(id) haben.  has_cascade=True bedeutet ON DELETE CASCADE."""
    result: dict[str, bool] = {}

    tables = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()

    for tname, sql in tables:
        if sql is None:
            continue
        sql_lower = sql.lower()

        # Enthält der CREATE TABLE-Text einen FK auf spieler(id)?
        # Muster: references spieler(id)   oder   references "spieler"("id")
        if not re.search(r"references\s+[\"']?spieler[\"']?\s*\([\"']?id[\"']?\)", sql_lower):
            continue

        # Hat dieser FK auch ON DELETE CASCADE?
        # Wir suchen den FK-Ausdruck und prüfen, ob danach CASCADE steht.
        has_cascade = bool(
            re.search(
                r"references\s+[\"']?spieler[\"']?\s*\([\"']?id[\"']?\)[^\n,)]*on\s+delete\s+cascade",
                sql_lower,
            )
        )
        result[tname] = has_cascade

    return result


# ── Haupt-Tests ───────────────────────────────────────────────────────────────

def test_manual_list_nicht_leer():
    lst = _manual_list_from_source()
    check(
        "spieler_loeschen() enthält mindestens eine Tabelle",
        len(lst) >= 1,
        f"Gefunden: {lst}",
    )
    return lst


def test_schema_abdeckung(manual_list: list[str]):
    """Kerntest: Jede Tabelle mit spieler_id-FK muss abgedeckt sein."""
    # In-Memory-DB via direktem sqlite3 + database.py-SQL aufbauen
    import importlib.util

    # database.py importieren mit einer temporären DB-Datei
    tmp_path = _build_temp_db()
    try:
        # Env-Variable setzen, damit get_conn() unsere Temp-DB nutzt
        os.environ["_TEST_DB_PATH"] = tmp_path

        # Modul laden (frisch, damit die Env-Var greift)
        spec = importlib.util.spec_from_file_location("database_test", DB_SRC)
        db_mod = importlib.util.module_from_spec(spec)

        # DB_PATH in database.py lesen und temporär überschreiben
        # (database.py liest DB_PATH einmal beim Import — wir patchen vorher)
        import builtins
        _orig_open = builtins.open  # type: ignore[attr-defined]

        # Wir patchen DB_PATH direkt im Modul nach dem Laden
        spec.loader.exec_module(db_mod)

        # DB_PATH auf Temp-Datei umbiegen
        db_mod.DB_PATH = tmp_path

        # Schema initialisieren
        db_mod.init_db()

        # Echte Verbindung für Schema-Analyse
        raw = sqlite3.connect(tmp_path)
        fk_map = _fk_tables_from_schema(raw)
        raw.close()

    finally:
        os.remove(tmp_path)
        os.environ.pop("_TEST_DB_PATH", None)

    if not fk_map:
        fail("Schema enthält FK-Tabellen", "Keine Tabellen mit spieler(id)-FK gefunden — DB leer?")
        return

    manual_set = set(manual_list)

    fehlend = []
    cascade_only = []
    manuell_abgedeckt = []
    redundant = []

    for tabelle, has_cascade in sorted(fk_map.items()):
        in_manual = tabelle in manual_set
        if has_cascade:
            cascade_only.append(tabelle)
            if in_manual:
                redundant.append(tabelle)  # kein Fehler, aber informativ
        else:
            if in_manual:
                manuell_abgedeckt.append(tabelle)
            else:
                fehlend.append(tabelle)

    # Bericht
    print()
    print("  ── Tabellen mit spieler(id)-FK ──────────────────────────────")
    print(f"  ON DELETE CASCADE (automatisch):  {cascade_only or ['—']}")
    print(f"  Manuell gelöscht:                 {manuell_abgedeckt or ['—']}")
    if redundant:
        print(f"  (Redundant in manueller Liste):   {redundant}  [kein Fehler]")
    if fehlend:
        print(f"  ⚠ NICHT ABGEDECKT:               {fehlend}")
    print()

    check(
        "Alle FK-Tabellen ohne CASCADE sind in spieler_loeschen() gelistet",
        len(fehlend) == 0,
        "Fehlende Tabellen: " + ", ".join(fehlend)
        + " — bitte in spieler_loeschen() ergänzen oder ON DELETE CASCADE hinzufügen",
    )

    # Zusatz: Warnung wenn manuell gelistete Tabelle gar nicht im Schema
    gelistet_aber_inexistent = [t for t in manual_list if t not in fk_map]
    if gelistet_aber_inexistent:
        print(
            f"  ℹ  Tabellen in manueller Liste, aber kein FK auf spieler(id) "
            f"gefunden: {gelistet_aber_inexistent}"
        )


def test_loeschen_funktioniert():
    """Smoke-Test: Spieler anlegen, Daten einfügen, löschen — kein FK-Fehler."""
    import importlib.util

    tmp_path = _build_temp_db()
    try:
        spec = importlib.util.spec_from_file_location("database_smoke", DB_SRC)
        db_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_mod)
        db_mod.DB_PATH = tmp_path
        db_mod.init_db()

        # Verein + Trainer anlegen (FK-Voraussetzung)
        raw = sqlite3.connect(tmp_path)
        raw.execute("PRAGMA foreign_keys = ON")
        raw.execute(
            "INSERT INTO vereine (id, name, email, kundennummer) VALUES (1,'TV Test','t@t.de','APH-000001')"
        )
        raw.execute(
            "INSERT INTO benutzer (id, email, vorname, nachname, passwort_hash, rolle, verein_id) "
            "VALUES (1,'tr@t.de','Test','Trainer','x','trainer',1)"
        )
        raw.execute(
            "INSERT INTO spieler (id, name, verein_id, trainer_id) VALUES (1,'Max Muster',1,1)"
        )
        # Datensätze in allen manuell gelisteten Tabellen anlegen
        manual_list = _manual_list_from_source()
        inserted = []
        for tbl in manual_list:
            try:
                raw.execute(f"INSERT INTO {tbl} (spieler_id) VALUES (1)")
                inserted.append(tbl)
            except Exception:
                pass  # Tabelle hat Pflichtfelder — überspringen, kein Fehler
        raw.commit()
        raw.close()

        # Nun spieler_loeschen() aufrufen
        try:
            db_mod.spieler_loeschen(1)
            ok("spieler_loeschen() wirft keinen FK-Fehler")
        except Exception as exc:
            fail("spieler_loeschen() wirft keinen FK-Fehler", str(exc))
    finally:
        os.remove(tmp_path)


# ── Einstiegspunkt ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍  Test: Spieler-Löschen-FK-Abdeckung\n")

    manual_list = test_manual_list_nicht_leer()
    test_schema_abdeckung(manual_list)
    test_loeschen_funktioniert()

    print(f"\n{'─'*55}")
    print(f"  Ergebnis: {_pass} PASS  |  {_fail} FAIL")
    print(f"{'─'*55}\n")
    sys.exit(0 if _fail == 0 else 1)
