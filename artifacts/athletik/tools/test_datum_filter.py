"""
Testsuite: Datumsformat-Robustheit / Mannschaftsfilter „Spieler ohne Test > 30 Tage"
20 Tests gemäß Master-Auftrag APH-HOTFIX-DATUMSFORMAT.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from database import parse_datum_safe

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
        detail = f" | got={got!r}, erwartet={erwartet!r}" if (got is not None or erwartet is not None) else ""
        print(f"  FAIL  {name}{detail}")

# ─── Hilfsfunktionen (spiegeln app.py-Logik wider) ───────────────────────────

def _days_since(d) -> "int | None":
    _pd = parse_datum_safe(d)
    return (date.today() - _pd).days if _pd else None

def _test_faellig(x) -> bool:
    """Spieler im >30-Tage-Filter: True wenn ALLE Tests fehlen oder >30 Tage alt."""
    if not x or not x.get("datum"):
        return True
    _d = parse_datum_safe(x["datum"])
    return _d is None or (date.today() - _d).days > 30

def _filter_faellig(player_data: list) -> bool:
    """all()-Version des Filters: Spieler erscheint wenn ALLE 5 Tests >30 Tage / fehlen."""
    tests = [player_data.get(k) for k in ["fms", "sprint", "yb", "agil", "aus"]]
    return all(_test_faellig(x) for x in tests)

def _datum_iso(d: str) -> str:
    return d  # ISO = YYYY-MM-DD

def _datum_de(d: str) -> str:
    # Konvertiert YYYY-MM-DD → DD.MM.YYYY für Tests
    from datetime import datetime
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y")

TODAY = date.today()
DATE_FRESH  = (TODAY - timedelta(days=10)).isoformat()   # 10 Tage alt → frisch
DATE_OLD    = (TODAY - timedelta(days=45)).isoformat()   # 45 Tage alt → veraltet

# ─── Tests 1–6: parse_datum_safe Basisverhalten ──────────────────────────────
check(
    "1. parse YYYY-MM-DD",
    parse_datum_safe("2026-08-18") == date(2026, 8, 18),
    got=parse_datum_safe("2026-08-18"),
    erwartet=date(2026, 8, 18),
)

check(
    "2. parse DD.MM.YYYY",
    parse_datum_safe("18.08.2026") == date(2026, 8, 18),
    got=parse_datum_safe("18.08.2026"),
    erwartet=date(2026, 8, 18),
)

check(
    "3. None → None",
    parse_datum_safe(None) is None,
    got=parse_datum_safe(None),
    erwartet=None,
)

check(
    "4. '' → None",
    parse_datum_safe("") is None,
    got=parse_datum_safe(""),
    erwartet=None,
)

check(
    "5. ungültiges Datum → None, kein Crash",
    parse_datum_safe("abc") is None,
    got=parse_datum_safe("abc"),
    erwartet=None,
)

check(
    "6. ISO und DE-Datum ergeben dasselbe date",
    parse_datum_safe("2026-08-18") == parse_datum_safe("18.08.2026"),
    got=(parse_datum_safe("2026-08-18"), parse_datum_safe("18.08.2026")),
)

# ─── Tests 7–10: >30-Tage-Filter mit beiden Formaten ────────────────────────
_old_iso = DATE_OLD
_old_de  = _datum_de(DATE_OLD)
_fresh_iso = DATE_FRESH
_fresh_de  = _datum_de(DATE_FRESH)

check(
    "7. >30-Tage-Filter mit ISO-Format — alter Test erkannt",
    _days_since(_old_iso) > 30,
    got=_days_since(_old_iso),
    erwartet=">30",
)

check(
    "8. >30-Tage-Filter mit DE-Format — alter Test erkannt",
    _days_since(_old_de) > 30,
    got=_days_since(_old_de),
    erwartet=">30",
)

check(
    "9. Frischer Test mit ISO-Format — NICHT >30 Tage",
    _days_since(_fresh_iso) <= 30,
    got=_days_since(_fresh_iso),
    erwartet="<=30",
)

check(
    "10. Frischer Test mit DE-Format — NICHT >30 Tage",
    _days_since(_fresh_de) <= 30,
    got=_days_since(_fresh_de),
    erwartet="<=30",
)

# ─── Test 11: Gemischte historische Formate ──────────────────────────────────
_dates_mixed = ["2026-01-15", "15.03.2026", "2025-12-01", "01.11.2025"]
_parsed_mixed = [parse_datum_safe(d) for d in _dates_mixed]
check(
    "11. Gemischte historische Formate — alle geparst",
    all(_p is not None for _p in _parsed_mixed),
    got=_parsed_mixed,
)

# ─── Test 12: Mehrere Tests → neuestes echtes Datum ─────────────────────────
_daten = ["31.12.2025", "2026-01-02", "2025-06-15"]
_parsed = [parse_datum_safe(d) for d in _daten]
_neuestes = max(_p for _p in _parsed if _p)
check(
    "12. Mehrere Tests → neuestes echtes Datum (02.01.2026)",
    _neuestes == date(2026, 1, 2),
    got=_neuestes,
    erwartet=date(2026, 1, 2),
)

# ─── Test 13: Spieler ohne Test → erscheint im Filter ────────────────────────
_player_kein_test = {"fms": None, "sprint": None, "yb": None, "agil": None, "aus": None}
check(
    "13. Spieler ohne Test → erscheint im >30-Tage-Filter",
    _filter_faellig(_player_kein_test),
    got=_filter_faellig(_player_kein_test),
    erwartet=True,
)

# ─── Test 14: Ungültiger Einzeltest → kein Crash, Seite läuft weiter ─────────
try:
    _r14 = _test_faellig({"datum": "UNGUELTIG-ABC"})
    check(
        "14. Ungültiger Testdatensatz crasht nicht (parse_datum_safe → None → faellig=True)",
        _r14 is True,  # ungültig → kein parsebares Datum → gilt als fehlend
        got=_r14,
        erwartet=True,
    )
except Exception as e:
    check("14. Ungültiger Testdatensatz crasht nicht", False, got=str(e))

# ─── Tests 15–19: Alle relevanten Testarten — beide Formate ──────────────────
_test_module = [
    ("15. FMS",        "2026-08-10", "10.08.2026"),
    ("16. Sprint",     "2026-07-01", "01.07.2026"),
    ("17. Y-Balance",  "2026-05-20", "20.05.2026"),
    ("18. Agilität",   "2026-06-15", "15.06.2026"),
    ("19. Ausdauer",   "2026-08-01", "01.08.2026"),
]
for _lbl, _iso, _de in _test_module:
    _p_iso = parse_datum_safe(_iso)
    _p_de  = parse_datum_safe(_de)
    check(
        f"{_lbl} — ISO und DE-Format ergeben gleiches Datum",
        _p_iso is not None and _p_iso == _p_de,
        got=(_p_iso, _p_de),
    )

# ─── Test 20: Sprung — beide Formate, Dashboard-relevant ────────────────────
_sprung_iso = parse_datum_safe("2026-08-15")
_sprung_de  = parse_datum_safe("15.08.2026")
check(
    "20. Sprung — ISO und DE-Format, Dashboard-kompatibel",
    _sprung_iso == _sprung_de == date(2026, 8, 15),
    got=(_sprung_iso, _sprung_de),
)

# ─── Bonus: Zeitstempel-Suffix wird korrekt abgeschnitten ─────────────────────
_ts1 = parse_datum_safe("2026-08-18 14:30")
_ts2 = parse_datum_safe("18.08.2026 (14:30)")
check(
    "B1. Zeitstempel-Suffix YYYY-MM-DD HH:MM → korrekt geparst",
    _ts1 == date(2026, 8, 18),
    got=_ts1,
)
check(
    "B2. Zeitstempel-Suffix DD.MM.YYYY (HH:MM) → korrekt geparst",
    _ts2 == date(2026, 8, 18),
    got=_ts2,
)

# ─── Ergebnis ─────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"  Ergebnis: {_pass} PASS  |  {_fail} FAIL")
print("=" * 60)
if _fail:
    sys.exit(1)
