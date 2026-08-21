"""Kleine Regressionstests für die gemeinsame aktive-Spieler-Suche."""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")
with open(APP_PATH, encoding="utf-8") as handle:
    _tree = ast.parse(handle.read(), filename=APP_PATH)


def _load_function(name):
    node = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), APP_PATH, "exec"), namespace)
    return namespace[name]


_suchname = _load_function("_spieler_suchname")
_suchtreffer_node = next(
    n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "_spieler_suchtreffer"
)
_suchtreffer_code = compile(
    ast.Module(body=[_suchtreffer_node], type_ignores=[]), APP_PATH, "exec"
)
_namespace = {"_spieler_suchname": _suchname}
exec(_suchtreffer_code, _namespace)
_suchtreffer = _namespace["_spieler_suchtreffer"]


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  {status}  {name}")
    if not condition:
        raise AssertionError(name)


spieler = [
    {"id": 1, "vorname": "Devin", "nachname": "Daroish", "name": "Devin Daroish"},
    {"id": 2, "vorname": "Lion", "nachname": "Daroish", "name": "Lion Daroish"},
    {"id": 3, "vorname": "Mia", "nachname": "Beispiel", "name": "Mia Beispiel"},
]

check("Vorname case-insensitive", [p["id"] for p in _suchtreffer(spieler, "dev")] == [1])
check("Nachname Teilstring", [p["id"] for p in _suchtreffer(spieler, "daro")] == [1, 2])
check("Vollständiger Name", [p["id"] for p in _suchtreffer(spieler, "lion daroish")] == [2])
check("Leere Suche zeigt berechtigte Liste", len(_suchtreffer(spieler, "")) == 3)
check("Kein Treffer sauber", _suchtreffer(spieler, "unbekannt") == [])
check(
    "Kein fremder Spieler ohne Übergabe in der sicheren Liste",
    [p["id"] for p in _suchtreffer(spieler[:2], "mia")] == [],
)

with open(APP_PATH, encoding="utf-8") as handle:
    _source = handle.read()
check("Globaler State bleibt global_player_id", 'st.session_state["global_player_id"] = auswahl["id"]' in _source)
_inline_helper = _source.split("def _inline_spielerwechsel", 1)[1].split(
    "\n\n# ─── Plotly", 1
)[0]
check(
    "Inline-Wechsel lädt ausschließlich die berechtigte Spielerliste",
    'spieler_laden(\n            _akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"]' in _inline_helper,
)
check(
    "Inline-Wechsel namespacet seinen offenen Suchzustand",
    'offen_key = f"_aktiver_spieler_suche_offen_{bereich}"' in _inline_helper,
)
for bereich in ("diagnostik", "training", "entwicklung", "vergleich", "dokumente"):
    check(
        f"{bereich}: gemeinsamer Inline-Wechsel wird verwendet",
        f'_inline_spielerwechsel("{bereich}")' in _source,
    )

_mobile_route = "\n".join(
    _source.split(f'elif section == "{section}":', 1)[1].split(
        'elif section == "', 1
    )[0]
    for section in (
        "🔬  Diagnostik",
        "📅  Training",
        "📈  Entwicklung",
        "⚖️  Vergleich",
        "📄  Dokumente",
    )
)
check(
    "Betroffene Mobilseiten haben keinen separaten Direktselektor mehr",
    "inject_mobile_player_selector" not in _mobile_route,
)

MOBILE_PATH = os.path.join(os.path.dirname(__file__), "..", "mobile.py")
with open(MOBILE_PATH, encoding="utf-8") as handle:
    _mobile_source = handle.read()
check(
    "Mobiler Kopfbereich navigiert nicht mehr zur Spielerverwaltung",
    'st.session_state["_nav_goto"] = "👤  Spieler"' not in _mobile_source,
)
print("  Ergebnis: 15 PASS, 0 FAIL")