"""
B1-Guard-Tests — Letzter-Superadmin-Schutz + Mandantentrennung
Läuft gegen eine temporäre In-Memory-Kopie der DB-Logik (kein Produktionsdaten-Eingriff).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3, tempfile, shutil
os.environ.setdefault("DB_PATH", ":memory:")

# ─── Temporäre Test-DB aufsetzen ──────────────────────────────────────────────
import database as _db

_orig_get_conn = _db.get_conn

_TEST_DB_PATH = tempfile.mktemp(suffix=".db")

def _test_get_conn():
    conn = sqlite3.connect(_TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

_db.get_conn = _test_get_conn

# Schema initialisieren
with _test_get_conn() as c:
    # Minimalschema für Tests
    c.executescript("""
        CREATE TABLE IF NOT EXISTS benutzer (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            verein_id     INTEGER,
            vorname       TEXT NOT NULL DEFAULT '',
            nachname      TEXT NOT NULL DEFAULT '',
            email         TEXT NOT NULL UNIQUE,
            passwort_hash TEXT NOT NULL DEFAULT 'x',
            rolle         TEXT NOT NULL DEFAULT 'Trainer',
            aktiv         INTEGER NOT NULL DEFAULT 1,
            benutzername  TEXT,
            telefon       TEXT,
            lizenz        TEXT,
            kundennummer  TEXT
        );
        CREATE TABLE IF NOT EXISTS spieler (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER,
            verein_id  INTEGER,
            vorname    TEXT,
            nachname   TEXT
        );
        CREATE TABLE IF NOT EXISTS vereine (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
    """)

# ─── Fixtures einfügen ────────────────────────────────────────────────────────
with _test_get_conn() as c:
    # Vereine
    c.execute("INSERT INTO vereine (id, name) VALUES (1, 'Verein A')")
    c.execute("INSERT INTO vereine (id, name) VALUES (2, 'Verein B')")
    # Superadmin (einziger)
    c.execute("INSERT INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (1, NULL, 'sa@test.de', 'Superadmin', 1)")
    # Zweiter Superadmin (für Mehrzahl-Tests)
    c.execute("INSERT INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (2, NULL, 'sa2@test.de', 'Superadmin', 1)")
    # Trainer in Verein A
    c.execute("INSERT INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (3, 1, 'trainer@a.de', 'Trainer', 1)")
    # Vereinsadmin in Verein A
    c.execute("INSERT INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (4, 1, 'vadmin@a.de', 'Vereinsadmin', 1)")
    # Trainer in Verein B
    c.execute("INSERT INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (5, 2, 'trainer@b.de', 'Trainer', 1)")

# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────
PASS = "✅ BESTANDEN"
FAIL = "❌ FEHLGESCHLAGEN"
results = []

def check(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    results.append((name, passed, detail))
    print(f"{status} | {name}" + (f"\n         → {detail}" if detail else ""))

def aktive_superadmins() -> int:
    with _test_get_conn() as c:
        return c.execute("SELECT COUNT(*) FROM benutzer WHERE rolle='Superadmin' AND aktiv=1").fetchone()[0]

# ─── TEST 1: Letzter aktiver Superadmin löschen → blockiert ──────────────────
# Erst SA2 deaktivieren, sodass SA1 der letzte ist
with _test_get_conn() as c:
    c.execute("UPDATE benutzer SET aktiv=0 WHERE id=2")

try:
    ok, msg = _db.benutzer_loeschen(1)  # SA1 ist jetzt der letzte
    check("T1: Letzter SA löschen → blockiert", not ok and "letzte" in msg.lower(), msg)
except Exception as e:
    check("T1: Letzter SA löschen → blockiert", False, f"Unerwarteter Fehler: {e}")

# ─── TEST 2: Letzter aktiver Superadmin deaktivieren → blockiert ─────────────
try:
    _db.benutzer_aktivieren(1, 0)  # SA1 = letzter aktiver SA
    check("T2: Letzter SA deaktivieren → blockiert", False, "Guard hat NICHT ausgelöst!")
except ValueError as e:
    check("T2: Letzter SA deaktivieren → blockiert", "letzte" in str(e).lower(), str(e))
except Exception as e:
    check("T2: Letzter SA deaktivieren → blockiert", False, f"Falscher Fehlertyp: {type(e).__name__}: {e}")

# ─── TEST 3: SA2 reaktivieren; jetzt beide aktiv → SA1 darf deaktiviert werden ─
with _test_get_conn() as c:
    c.execute("UPDATE benutzer SET aktiv=1 WHERE id=2")

try:
    _db.benutzer_aktivieren(1, 0)  # Jetzt 2 aktive SAs → erlaubt
    n = aktive_superadmins()
    check("T3: Einer von 2 SAs deaktivieren → erlaubt", n == 1, f"Noch aktive SAs: {n}")
except ValueError as e:
    check("T3: Einer von 2 SAs deaktivieren → erlaubt", False, str(e))
finally:
    # SA1 wieder aktivieren für Folgetests
    with _test_get_conn() as c:
        c.execute("UPDATE benutzer SET aktiv=1 WHERE id=1")

# ─── TEST 4: SA2 löschen bei 2 aktiven SAs → erlaubt ────────────────────────
# SA2 hat keine Spieler → darf gelöscht werden
with _test_get_conn() as c:
    c.execute("UPDATE benutzer SET aktiv=1 WHERE id=1 OR id=2")

ok, msg = _db.benutzer_loeschen(2)
check("T4: Einer von 2 SAs löschen → erlaubt", ok, msg)
# SA2 wiederherstellen
with _test_get_conn() as c:
    c.execute("INSERT OR REPLACE INTO benutzer (id, verein_id, email, rolle, aktiv) VALUES (2, NULL, 'sa2@test.de', 'Superadmin', 1)")

# ─── TEST 5: Trainer kann fremden Mandanten nicht ändern ─────────────────────
try:
    _db.benutzer_aktualisieren(
        5, 2, "Neu", "Name", "trainer@b.de", "Trainer",
        caller_rolle="Trainer",
        caller_verein_id=1,  # Verein A, aber Ziel in Verein B
    )
    check("T5: Trainer → fremder Mandant → blockiert", False, "Guard hat NICHT ausgelöst!")
except PermissionError as e:
    check("T5: Trainer → fremder Mandant → blockiert", "mandant" in str(e).lower() or "zugriff" in str(e).lower(), str(e))
except Exception as e:
    check("T5: Trainer → fremder Mandant → blockiert", False, f"Falscher Fehlertyp: {type(e).__name__}: {e}")

# ─── TEST 6: Vereinsadmin kann fremden Mandanten nicht ändern ────────────────
try:
    _db.benutzer_aktualisieren(
        5, 2, "Hacked", "User", "trainer@b.de", "Trainer",
        caller_rolle="Vereinsadmin",
        caller_verein_id=1,  # Verein A, aber Ziel in Verein B
    )
    check("T6: Vereinsadmin → fremder Mandant → blockiert", False, "Guard hat NICHT ausgelöst!")
except PermissionError as e:
    check("T6: Vereinsadmin → fremder Mandant → blockiert", "mandant" in str(e).lower() or "zugriff" in str(e).lower(), str(e))
except Exception as e:
    check("T6: Vereinsadmin → fremder Mandant → blockiert", False, f"Falscher Fehlertyp: {type(e).__name__}: {e}")

# ─── TEST 7: Trainer versucht Rollenescalation zu Superadmin ─────────────────
try:
    _db.benutzer_aktualisieren(
        3, 1, "Trainer", "A", "trainer@a.de", "Superadmin",  # Zielrolle: Superadmin
        caller_rolle="Trainer",
        caller_verein_id=1,
    )
    check("T7: Trainer → Superadmin-Rolle → blockiert", False, "Guard hat NICHT ausgelöst!")
except PermissionError as e:
    check("T7: Trainer → Superadmin-Rolle → blockiert", "eskalation" in str(e).lower() or "superadmin" in str(e).lower(), str(e))
except Exception as e:
    check("T7: Trainer → Superadmin-Rolle → blockiert", False, f"Falscher Fehlertyp: {type(e).__name__}: {e}")

# ─── TEST 8: Vereinsadmin versucht Rollenescalation zu Superadmin ─────────────
try:
    _db.benutzer_aktualisieren(
        4, 1, "Admin", "A", "vadmin@a.de", "Superadmin",
        caller_rolle="Vereinsadmin",
        caller_verein_id=1,
    )
    check("T8: Vereinsadmin → Superadmin-Rolle → blockiert", False, "Guard hat NICHT ausgelöst!")
except PermissionError as e:
    check("T8: Vereinsadmin → Superadmin-Rolle → blockiert", "eskalation" in str(e).lower() or "superadmin" in str(e).lower(), str(e))
except Exception as e:
    check("T8: Vereinsadmin → Superadmin-Rolle → blockiert", False, f"Falscher Fehlertyp: {type(e).__name__}: {e}")

# ─── TEST 9: Superadmin kann eigenen Mandanten (fremden Verein) ändern ────────
try:
    _db.benutzer_aktualisieren(
        5, 2, "Trainer", "B", "trainer@b.de", "Trainer",
        caller_rolle="Superadmin",
        caller_verein_id=None,  # Superadmin hat kein eigenes verein
    )
    check("T9: Superadmin → beliebiger Mandant → erlaubt", True)
except Exception as e:
    check("T9: Superadmin → beliebiger Mandant → erlaubt", False, str(e))

# ─── TEST 10: Superadmin kann Trainer zum Vereinsadmin hochstufen ─────────────
try:
    _db.benutzer_aktualisieren(
        3, 1, "Trainer", "A", "trainer@a.de", "Vereinsadmin",
        caller_rolle="Superadmin",
        caller_verein_id=None,
    )
    # Zurücksetzen
    _db.benutzer_aktualisieren(
        3, 1, "Trainer", "A", "trainer@a.de", "Trainer",
        caller_rolle="Superadmin",
        caller_verein_id=None,
    )
    check("T10: Superadmin → Rolle Vereinsadmin vergeben → erlaubt", True)
except Exception as e:
    check("T10: Superadmin → Rolle Vereinsadmin vergeben → erlaubt", False, str(e))

# ─── TEST 11: Trainer kann eigenen Mandanten (gleiche verein_id) ändern ───────
try:
    _db.benutzer_aktualisieren(
        3, 1, "Trainer", "A", "trainer@a.de", "Trainer",
        caller_rolle="Trainer",
        caller_verein_id=1,  # gleicher Mandant
    )
    check("T11: Trainer → eigener Mandant → erlaubt", True)
except Exception as e:
    check("T11: Trainer → eigener Mandant → erlaubt", False, str(e))

# ─── ERGEBNIS ─────────────────────────────────────────────────────────────────
print()
print("=" * 60)
n_ok   = sum(1 for _, ok, _ in results if ok)
n_fail = sum(1 for _, ok, _ in results if not ok)
print(f"ERGEBNIS: {n_ok}/{len(results)} bestanden, {n_fail} fehlgeschlagen")
print("=" * 60)

# Aufräumen
os.unlink(_TEST_DB_PATH)

if n_fail > 0:
    sys.exit(1)
