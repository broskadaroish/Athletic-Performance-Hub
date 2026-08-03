#!/usr/bin/env python3
"""
SQLite → PostgreSQL Datenmigration
====================================
Überträgt das gesamte Athletik-Datenbankschema und alle Daten von SQLite
nach PostgreSQL. Danach kann DATABASE_URL gesetzt werden und die App
läuft direkt gegen PostgreSQL.

Voraussetzungen:
  pip install psycopg2-binary

Aufruf:
  # 1. PostgreSQL-URL setzen
  export DATABASE_URL=postgresql://user:password@host:5432/athletik

  # 2. Skript ausführen (aus dem artifacts/athletik/-Verzeichnis)
  python tools/migrate_to_pg.py

  # 3. Mit anderer SQLite-Quelldatei:
  ATHLETIK_DB_PATH=/pfad/zur/athletik.db python tools/migrate_to_pg.py

Hinweise:
  - Das Skript ist idempotent: bereits migrierte Zeilen werden übersprungen
    (INSERT … ON CONFLICT DO NOTHING).
  - SQLite-Spaltentypen werden automatisch auf PostgreSQL-Typen gemappt.
  - BLOBs (Logo, Fotos) werden als bytea migriert.
  - Das Skript erstellt keine Fremdschlüssel oder Indizes — diese werden
    von init_db() bzw. _create_indexes() angelegt wenn die App startet.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Skript-Verzeichnis = tools/, übergeordnetes Verzeichnis = App-Root
APP_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(APP_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("migrate_to_pg")

# ── Konfiguration ────────────────────────────────────────────────────────────
SQLITE_PATH  = os.environ.get("ATHLETIK_DB_PATH", str(APP_ROOT / "athletik.db"))
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    log.error("DATABASE_URL ist nicht gesetzt. Abbruch.")
    sys.exit(1)

# Railway/Render nutzen postgres:// — psycopg2 braucht postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

# ── SQLite-Typ → PostgreSQL-Typ ───────────────────────────────────────────────
_TYPE_MAP: dict[str, str] = {
    "INTEGER":  "BIGINT",
    "INT":      "BIGINT",
    "REAL":     "DOUBLE PRECISION",
    "FLOAT":    "DOUBLE PRECISION",
    "NUMERIC":  "NUMERIC",
    "TEXT":     "TEXT",
    "BLOB":     "BYTEA",
    "BOOLEAN":  "BOOLEAN",
    "DATE":     "TEXT",   # als TEXT gespeichert in SQLite
    "DATETIME": "TEXT",
    "":         "TEXT",   # kein Typ in SQLite → TEXT
}


def _pg_type(sqlite_type: str) -> str:
    upper = sqlite_type.upper().split("(")[0].strip()
    return _TYPE_MAP.get(upper, "TEXT")


def _get_tables(conn_sq: sqlite3.Connection) -> list[str]:
    rows = conn_sq.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def _get_columns(conn_sq: sqlite3.Connection, table: str):
    """Gibt (name, type, notnull, pk) zurück."""
    return conn_sq.execute(f"PRAGMA table_info({table})").fetchall()


def _create_pg_table(cur_pg, table: str, columns) -> None:
    col_defs = []
    for col in columns:
        cid, name, ctype, notnull, dflt, pk = col
        pg_type = _pg_type(ctype)
        # Primärschlüssel: SERIAL wenn INTEGER PRIMARY KEY (SQLite autoincrement)
        if pk == 1 and pg_type == "BIGINT":
            col_def = f'"{name}" BIGSERIAL PRIMARY KEY'
        else:
            not_null = " NOT NULL" if notnull else ""
            col_def = f'"{name}" {pg_type}{not_null}'
        col_defs.append(col_def)

    ddl = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)})'
    cur_pg.execute(ddl)
    log.info("  Tabelle erstellt / bereits vorhanden: %s", table)


def _migrate_table(conn_sq: sqlite3.Connection, cur_pg, table: str, columns) -> int:
    col_names = [c[1] for c in columns]
    quoted    = [f'"{n}"' for n in col_names]
    placeholders = ", ".join(["%s"] * len(col_names))
    insert_sql = (
        f'INSERT INTO "{table}" ({", ".join(quoted)}) '
        f'VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    )

    rows = conn_sq.execute(f'SELECT {", ".join(quoted)} FROM "{table}"').fetchall()
    count = 0
    for row in rows:
        # bytes aus SQLite bleiben bytes; memoryview für psycopg2 OK
        values = [bytes(v) if isinstance(v, (bytes, memoryview)) else v for v in row]
        cur_pg.execute(insert_sql, values)
        count += 1
    return count


def main() -> None:
    log.info("Starte Migration: %s → %s", SQLITE_PATH, DATABASE_URL[:40] + "…")

    # ── SQLite öffnen ────────────────────────────────────────────────────────
    if not Path(SQLITE_PATH).exists():
        log.error("SQLite-Datei nicht gefunden: %s", SQLITE_PATH)
        sys.exit(1)

    conn_sq = sqlite3.connect(SQLITE_PATH)
    conn_sq.row_factory = sqlite3.Row

    # ── PostgreSQL öffnen ────────────────────────────────────────────────────
    try:
        import psycopg2
    except ImportError:
        log.error("psycopg2 nicht installiert. Bitte: pip install psycopg2-binary")
        sys.exit(1)

    conn_pg = psycopg2.connect(DATABASE_URL)
    conn_pg.autocommit = False
    cur_pg = conn_pg.cursor()

    tables = _get_tables(conn_sq)
    log.info("%d Tabellen gefunden: %s", len(tables), ", ".join(tables))

    total_rows = 0
    for table in tables:
        columns = _get_columns(conn_sq, table)
        log.info("Migriere: %s (%d Spalten)", table, len(columns))
        try:
            _create_pg_table(cur_pg, table, columns)
            n = _migrate_table(conn_sq, cur_pg, table, columns)
            log.info("  → %d Zeilen übertragen", n)
            total_rows += n
        except Exception as exc:
            conn_pg.rollback()
            log.error("Fehler bei Tabelle %s: %s", table, exc)
            raise

    conn_pg.commit()
    conn_sq.close()
    conn_pg.close()

    log.info("✅ Migration abgeschlossen — %d Zeilen insgesamt.", total_rows)
    log.info(
        "Nächster Schritt: DATABASE_URL in den Env-Vars setzen und App neu starten.\n"
        "Die App ruft dann init_db() gegen PostgreSQL auf und legt fehlende Tabellen an."
    )


if __name__ == "__main__":
    main()
