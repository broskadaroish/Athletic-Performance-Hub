"""
tools/test_ausdauer_trainingsplan.py
======================================
Prüft die Ausdauer-Trainingsplan-Generierung mit Temp-DB:
  - defizit_score() → "Ausdauer"-Bereich, nicht "Fußball"
  - _ausdauer_pool_fuer_plangruppe() → altersgerechte Übungen
  - trainingsplan_multi_erstellen() mit Ausdauer-Defizit → Ausdauer-Block im Plan
  - kein Ausdauer-Defizit → kein Ausdauer-Block

Temp-DB wird nach dem Test gelöscht (Produktiv-DB bleibt unberührt).
"""

import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")

# Temp-DB VOR anderen Imports anlegen, damit alle db.*-Calls dorthin zeigen
import database as db
_TMP_DIR = tempfile.mkdtemp(prefix="test_aus_plan_")
_DB_PATH = os.path.join(_TMP_DIR, "test.db")
_ORIG    = db.DB_PATH
db.DB_PATH = _DB_PATH
db.init_db()

from periodisierung import (
    defizit_score,
    trainingsplan_multi_erstellen,
    zyklus_erstellen,
    _ausdauer_pool_fuer_plangruppe,
    _PLANGRUPPE_ZU_AUSDAUER,
)

PASS = 0
FAIL = 0


def check(label, got, expected):
    global PASS, FAIL
    ok = got == expected
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got!r}" +
          ("" if ok else f", expected {expected!r}"))
    if ok:
        PASS += 1
    else:
        FAIL += 1


def _plan_uebungen(sid):
    """Liest alle gespeicherten Trainingsplan-Einträge für den Spieler."""
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM trainingsplan WHERE spieler_id = ?", (sid,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def _make_spieler(name="Testspieler", alter=10, verein_id=1):
    """Legt Minimaleinträge für Verein und Spieler an, gibt spieler_id zurück."""
    con = sqlite3.connect(_DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO vereine (id, name) VALUES (?, ?)", (verein_id, "TestVerein")
    )
    cur.execute(
        "INSERT INTO spieler (name, verein_id, geburtsdatum) VALUES (?, ?, ?)",
        (name, verein_id, "2014-01-01" if alter == 10 else "2002-01-01"),
    )
    sid = cur.lastrowid
    con.commit()
    con.close()
    return sid


# ── 1. defizit_score() Keyword-Mapping ────────────────────────────────────
print("\n=== 1. defizit_score() Keyword-Mapping ===")
s1 = defizit_score("Aerobe Ausdauer verbesserungswürdig")
check("'ausdauer'-Keyword → Ausdauer-Score", "Ausdauer" in s1, True)
check("'ausdauer'-Keyword → NICHT Fußball", "Fußball" not in s1, True)

s2 = defizit_score("Yo-Yo-IR Verbesserungsbedarf aerob")
check("'aerob'-Keyword → Ausdauer-Score", "Ausdauer" in s2, True)

s3 = defizit_score("Fußballtechnisch in Ordnung")
check("'fußball'-Keyword → Fußball-Score", "Fußball" in s3, True)
check("'fußball' ohne aerob → kein Ausdauer", "Ausdauer" not in s3, True)

s4 = defizit_score("Intermittierende Ausdauer kritisch")
check("'intermittier'-Keyword → Ausdauer", "Ausdauer" in s4, True)
s5 = defizit_score({"Ausdauer": 3})
check("Strukturierter Ausdauer-Score bleibt erhalten", s5.get("Ausdauer"), 3)


# ── 2. _ausdauer_pool_fuer_plangruppe() ───────────────────────────────────
print("\n=== 2. _ausdauer_pool_fuer_plangruppe() ===")
jugend_ex = _ausdauer_pool_fuer_plangruppe("U10", "stabilisation", 3)
check("Jugend-Pool nicht leer", len(jugend_ex) > 0, True)
ga1_in_jugend = any("GA1" in e[0] for e in jugend_ex)
check("Keine GA1-Übung im Jugend-Pool", ga1_in_jugend, False)

mittel_ex = _ausdauer_pool_fuer_plangruppe("U14", "kraft", 3)
check("Mittel-Pool nicht leer", len(mittel_ex) > 0, True)
int_in_mittel = any("Intervall" in e[0] or "15" in e[0] for e in mittel_ex)
check("Mittel-Pool enthält Intervall-Übung", int_in_mittel, True)

senior_ex = _ausdauer_pool_fuer_plangruppe("U18", "stabilisation", 4)
check("Senior-Pool nicht leer", len(senior_ex) > 0, True)
ga1_in_senior = any("GA1" in e[0] or "Dauerlauf" in e[0] or "Dauermethode" in e[0] for e in senior_ex)
check("Senior-Pool enthält GA1/Dauerlauf", ga1_in_senior, True)

ex0 = _ausdauer_pool_fuer_plangruppe("Senior", "power", 3, offset=0)
ex3 = _ausdauer_pool_fuer_plangruppe("Senior", "power", 3, offset=3)
check("Offset-Variation ändert Auswahl", ex0 != ex3, True)


# ── 3. trainingsplan_multi_erstellen mit Ausdauer-Defizit ─────────────────
print("\n=== 3. trainingsplan_multi_erstellen() — Ausdauer-Defizit ===")

# U10-Spieler (alter=10 → Jugend)
sid_u10 = _make_spieler("U10-Spieler", alter=10)
n = trainingsplan_multi_erstellen(
    spieler_id=sid_u10,
    schwerpunkt_text="Aerobe Ausdauer stark verbesserungsbedürftig. Yo-Yo-IR Verbesserungsbedarf.",
    alter=10,
    wochen=4,
    saison_phase="Vorsaison",
)
check("Plan erstellt (n>0 Einträge)", n > 0, True)
eintraege = _plan_uebungen(sid_u10)
bereiche = {e["bereich"] for e in eintraege}
check("Ausdauer-Bereich im Plan", "Ausdauer" in bereiche, True)
aus_ex = [e["uebung"] for e in eintraege if e["bereich"] == "Ausdauer"]
print(f"    → Ausdauer-Übungen (Jugend): {aus_ex[:3]}")
ga1_in_plan = any("GA1" in u or "Dauerlauf" in u for u in aus_ex)
check("Keine GA1/Dauerlauf im Jugend-Plan", ga1_in_plan, False)

# Senior-Spieler (alter=25 → Senior)
sid_sr = _make_spieler("Senior-Spieler", alter=25)
n2 = trainingsplan_multi_erstellen(
    spieler_id=sid_sr,
    schwerpunkt_text="Ausdauer-Defizit — aerobe Basis zu schwach.",
    alter=25,
    wochen=4,
    saison_phase="Vorsaison",
)
check("Senior-Plan erstellt", n2 > 0, True)
eintraege_sr = _plan_uebungen(sid_sr)
bereiche_sr = {e["bereich"] for e in eintraege_sr}
check("Senior-Plan enthält Ausdauer-Bereich", "Ausdauer" in bereiche_sr, True)
aus_ex_sr = [e["uebung"] for e in eintraege_sr if e["bereich"] == "Ausdauer"]
print(f"    → Ausdauer-Übungen (Senior): {aus_ex_sr[:3]}")
ga1_in_sr = any("GA1" in u or "Dauerlauf" in u or "RSA" in u or "Intervall" in u for u in aus_ex_sr)
check("Senior-Plan enthält GA1/Dauerlauf/RSA/Intervall", ga1_in_sr, True)

# Strukturierter Ausdauer-Score muss auch den Periodisierungspfad erreichen.
sid_structured = _make_spieler("Strukturierte-Ausdauer", alter=10)
structured_plan = trainingsplan_multi_erstellen(
    spieler_id=sid_structured,
    schwerpunkt_text={"Ausdauer": 3},
    alter=10,
    wochen=4,
)
check("Strukturierter Ausdauer-Plan erstellt", structured_plan > 0, True)
structured_rows = _plan_uebungen(sid_structured)
check("Strukturierter Score erzeugt Ausdauer-Block", any(
    row["bereich"] == "Ausdauer" for row in structured_rows
), True)

sid_cycle = _make_spieler("Strukturierter-Zyklus", alter=10)
structured_cycle = zyklus_erstellen(
    sid_cycle, {"Ausdauer": 3}, wochen=4, alter=10
)
check("Strukturierter Ausdauer-Zyklus enthält Ausdauer", any(
    row["bereich"] == "Ausdauer" for row in structured_cycle
), True)


# ── 4. kein Ausdauer-Defizit → kein Ausdauer-Block ────────────────────────
print("\n=== 4. kein Ausdauer-Defizit → kein Ausdauer-Block ===")
sid_kein = _make_spieler("Kein-Aus-Spieler", alter=16)
n3 = trainingsplan_multi_erstellen(
    spieler_id=sid_kein,
    schwerpunkt_text="Hamstring-Defizit. Explosivität verbesserungsbedürftig.",
    alter=16,
    wochen=4,
    saison_phase="Vorsaison",
)
check("Plan erstellt (n>0)", n3 > 0, True)
eintraege_kein = _plan_uebungen(sid_kein)
aus_kein = [e for e in eintraege_kein if e["bereich"] == "Ausdauer"]
check("Kein Ausdauer-Defizit → kein Ausdauer-Block", len(aus_kein), 0)


# ── 5. Kombinierter Kern + Ausdauer-Defizit ────────────────────────────────
print("\n=== 5. Kombinierter Kern + Ausdauer-Defizit ===")
sid_kombi = _make_spieler("Kombi-Spieler", alter=14)
n4 = trainingsplan_multi_erstellen(
    spieler_id=sid_kombi,
    schwerpunkt_text="Rumpf-Stabilität schwach. Ausdauer intermittierend unzureichend.",
    alter=14,
    wochen=4,
    saison_phase="Vorsaison",
)
eintraege_kombi = _plan_uebungen(sid_kombi)
bereiche_kombi = {e["bereich"] for e in eintraege_kombi}
check("Kombi-Plan enthält Rumpf", "Rumpf" in bereiche_kombi, True)
check("Kombi-Plan enthält Ausdauer", "Ausdauer" in bereiche_kombi, True)


# ── Aufräumen ────────────────────────────────────────────────────────────────
db.DB_PATH = _ORIG
import shutil
shutil.rmtree(_TMP_DIR, ignore_errors=True)


# ── Ergebnis ─────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Ergebnis: {PASS} PASS  |  {FAIL} FAIL")
if FAIL:
    sys.exit(1)
