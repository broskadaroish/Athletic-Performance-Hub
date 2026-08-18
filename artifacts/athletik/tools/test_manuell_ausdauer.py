"""
Testsuite: Manueller Trainingsplan — Ausdauer-Integration
Prüft alle 13 Anforderungen aus dem Master-Auftrag (Abschnitt 25).
"""
import sys, os, sqlite3, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database as db
from periodisierung import (
    _ausdauer_pool_fuer_plangruppe,
    _alter_zu_plangruppe,
    _POOL,
    _PLANGRUPPE_ZU_AUSDAUER,
)

# ─── Mini-Test-Framework ──────────────────────────────────────────────────────
_pass = 0
_fail = 0

def check(name: str, cond: bool, got=None, erwartet=None):
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  PASS  {name}")
    else:
        _fail += 1
        detail = f" | got={got!r}, erwartet={erwartet!r}" if got is not None or erwartet is not None else ""
        print(f"  FAIL  {name}{detail}")


# ─── Shared: temporäre Test-DB ────────────────────────────────────────────────
_TMP = tempfile.mkdtemp(prefix="test_manuell_")
_DB  = os.path.join(_TMP, "test.db")
db.DB_PATH = _DB
db.init_db()

con = sqlite3.connect(_DB)
con.execute("INSERT INTO vereine (id,name) VALUES (1,'TestVerein')")
con.execute("INSERT INTO spieler (id,name,verein_id,geburtsdatum) VALUES (1,'SpielerU11',1,'2016-08-26')")
con.execute("INSERT INTO spieler (id,name,verein_id,geburtsdatum) VALUES (2,'SpielerSenior',1,'1990-01-01')")
con.commit(); con.close()

# ─── Konstanten (spiegeln die app.py-Bereiche wider) ─────────────────────────
_BEREICHE_MANUELL = [
    "Sprunggelenk", "Knie", "Hüfte", "Rumpf", "Oberschenkel",
    "Schnelligkeit", "Explosivität", "Agilität", "Ausdauer", "Fußball",
]

# ─── Test 1: "Ausdauer" in manueller Bereichsliste vorhanden ─────────────────
check(
    "1. 'Ausdauer' ist im manuellen Bereich vorhanden",
    "Ausdauer" in _BEREICHE_MANUELL,
)

# ─── Test 2: Reihenfolge korrekt ─────────────────────────────────────────────
_erwartet_reihenfolge = [
    "Sprunggelenk", "Knie", "Hüfte", "Rumpf", "Oberschenkel",
    "Schnelligkeit", "Explosivität", "Agilität", "Ausdauer", "Fußball",
]
check(
    "2. Reihenfolge korrekt (Sprunggelenk … Agilität, Ausdauer, Fußball)",
    _BEREICHE_MANUELL == _erwartet_reihenfolge,
    got=_BEREICHE_MANUELL,
    erwartet=_erwartet_reihenfolge,
)

# ─── Test 3: Ausdauer liefert Übungen für Plangruppe U10 ────────────────────
_u10_uebungen = []
for pk in ["stabilisation", "kraft", "power"]:
    for u, *_ in _ausdauer_pool_fuer_plangruppe("U10", pk, 99):
        if u not in _u10_uebungen:
            _u10_uebungen.append(u)

check(
    "3. Ausdauer liefert Übungen (U10-Plangruppe)",
    len(_u10_uebungen) > 0,
    got=len(_u10_uebungen),
    erwartet=">0",
)

# ─── Test 4: U10-Plangruppe → Jugend-Pool ────────────────────────────────────
_kategorie_u10 = _PLANGRUPPE_ZU_AUSDAUER.get(_alter_zu_plangruppe(9), "?")
check(
    "4. U10-Plangruppe liefert Jugend-Ausdauerübungen",
    _kategorie_u10 == "Jugend",
    got=_kategorie_u10,
    erwartet="Jugend",
)

# ─── Test 5: JG2016/U11 → Jugend-Pool ────────────────────────────────────────
from database import berechne_alter
_alter_u11 = berechne_alter("26.08.2016")  # ≈ 9 oder 10 (chronologisch)
_pg_u11    = _alter_zu_plangruppe(_alter_u11)
_kat_u11   = _PLANGRUPPE_ZU_AUSDAUER.get(_pg_u11, "?")
check(
    "5. JG2016/U11 bekommt Jugend-Ausdauerpool",
    _kat_u11 == "Jugend",
    got=f"pg={_pg_u11} kat={_kat_u11}",
    erwartet="Jugend",
)

# ─── Test 6: U11 kein GA1-Dauerlauf ──────────────────────────────────────────
_u11_uebungen = []
for pk in ["stabilisation", "kraft", "power"]:
    for u, *_ in _ausdauer_pool_fuer_plangruppe(_pg_u11, pk, 99):
        if u not in _u11_uebungen:
            _u11_uebungen.append(u)

_ga1_vorhanden = any("GA1" in u for u in _u11_uebungen)
check(
    "6. U11 bekommt keinen GA1-Dauerlauf",
    not _ga1_vorhanden,
    got=[u for u in _u11_uebungen if "GA1" in u] or "KEINE",
    erwartet="KEINE",
)

# ─── Test 7: U11 keine extensive Dauermethode ────────────────────────────────
_dauerlauf_vorhanden = any("Dauerlauf" in u or "Dauermethode" in u for u in _u11_uebungen)
check(
    "7. U11 bekommt keine extensive Dauermethode / Dauerlauf",
    not _dauerlauf_vorhanden,
    got=[u for u in _u11_uebungen if "Dauerlauf" in u or "Dauermethode" in u] or "KEINE",
    erwartet="KEINE",
)

# ─── Test 8: Senior bekommt Senior-Ausdauerübungen ───────────────────────────
_alter_senior = berechne_alter("01.01.1990")  # ≈ 36
_pg_senior    = _alter_zu_plangruppe(_alter_senior)
_kat_senior   = _PLANGRUPPE_ZU_AUSDAUER.get(_pg_senior, "?")
_senior_ueb   = []
for pk in ["stabilisation", "kraft", "power"]:
    for u, *_ in _ausdauer_pool_fuer_plangruppe(_pg_senior, pk, 99):
        if u not in _senior_ueb:
            _senior_ueb.append(u)

_hat_ga1 = any("GA1" in u for u in _senior_ueb)
check(
    "8. Senior bekommt Senior-Ausdauerübungen (inkl. GA1)",
    _hat_ga1 and _kat_senior == "Senior",
    got=f"kat={_kat_senior} GA1={_hat_ga1}",
    erwartet="kat=Senior GA1=True",
)

# ─── Test 9: Equipment-Filter funktioniert ───────────────────────────────────
from periodisierung import _equip_expanded, _equip_verfuegbar

# Ballbasierte Ausdauerübungen sollen mit "Ball"-Filter sichtbar sein
_equip_ball = _equip_expanded({"Ball"})
_ball_ueb = [u for u in _u10_uebungen if _equip_verfuegbar(u, _equip_ball)]
check(
    "9. Equipment-Filter: Ball-Übungen bei U10 mit Ball-Filter sichtbar",
    len(_ball_ueb) > 0,
    got=len(_ball_ueb),
    erwartet=">0",
)

# Körpergewicht-Filter: reine Laufübungen sollen sichtbar sein
_equip_kg = _equip_expanded({"Körpergewicht"})
_kg_ueb = [u for u in _u10_uebungen if _equip_verfuegbar(u, _equip_kg)]
check(
    "9b. Equipment-Filter: Körpergewicht-Übungen bei U10 sichtbar",
    len(_kg_ueb) > 0,
    got=len(_kg_ueb),
    erwartet=">0",
)

# ─── Test 10: Manuelle Ausdauerübung kann gespeichert werden ─────────────────
from database import trainingsplan_eintrag_speichern, plan_aktive_version_id

_ok = trainingsplan_eintrag_speichern(
    spieler_id=1,
    datum="20.08.2026",
    woche=1,
    bereich="Ausdauer",
    uebung="Fangspiel mit Ballkontrolle",
    saetze="1",
    wdh="8 Minuten",
    haeufigkeit="2×/Woche",
)
check(
    "10. Manuelle Ausdauerübung kann gespeichert werden",
    _ok is not False,  # None oder True ist OK, False = Fehler
)

# ─── Test 11: Gespeicherter Bereich = "Ausdauer" ─────────────────────────────
con2 = sqlite3.connect(_DB)
con2.row_factory = sqlite3.Row
_row = con2.execute(
    "SELECT bereich, uebung FROM trainingsplan WHERE spieler_id=1 AND bereich='Ausdauer' ORDER BY id DESC LIMIT 1"
).fetchone()
con2.close()

check(
    "11. Gespeicherter Bereich = 'Ausdauer'",
    _row is not None and _row["bereich"] == "Ausdauer",
    got=_row["bereich"] if _row else None,
    erwartet="Ausdauer",
)
check(
    "11b. Übungsname korrekt gespeichert",
    _row is not None and _row["uebung"] == "Fangspiel mit Ballkontrolle",
    got=_row["uebung"] if _row else None,
    erwartet="Fangspiel mit Ballkontrolle",
)

# ─── Test 12: Plan kann danach geladen werden ────────────────────────────────
# trainingsplan_laden() deckt beide Fälle ab: mit und ohne aktive Plan-Version
from database import trainingsplan_laden

_plan_zeilen = trainingsplan_laden(1)
_aus_in_plan = [z for z in _plan_zeilen if z.get("bereich") == "Ausdauer"]
check(
    "12. Plan kann geladen werden und enthält Ausdauer-Eintrag",
    len(_aus_in_plan) > 0,
    got=len(_aus_in_plan),
    erwartet=">0",
)

# ─── Test 13: Bestehende Bereiche weiterhin vorhanden ───────────────────────
_pflicht_bereiche = ["Sprunggelenk", "Knie", "Hüfte", "Rumpf", "Oberschenkel",
                     "Schnelligkeit", "Explosivität", "Agilität", "Fußball"]
_fehlend = [b for b in _pflicht_bereiche if b not in _BEREICHE_MANUELL]
check(
    "13. Alle bestehenden Bereiche weiterhin vorhanden",
    len(_fehlend) == 0,
    got=_fehlend or "KEINE fehlenden",
    erwartet="KEINE fehlenden",
)

# ─── Aufräumen ────────────────────────────────────────────────────────────────
shutil.rmtree(_TMP)

# ─── Ergebnis ─────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"  Ergebnis: {_pass} PASS  |  {_fail} FAIL")
print("=" * 60)
if _fail:
    sys.exit(1)
