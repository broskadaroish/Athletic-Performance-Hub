"""
check_spec.py — Prüft ob alle lokalen .py-Dateien und Paket-Unterordner
in der local_modules-Liste von athletik.spec eingetragen sind.

Verwendung:
    python installer/check_spec.py
    (vom App-Verzeichnis aus aufrufen, oder vom installer/-Ordner)

Rückgabecodes:
    0 — alles vollständig, Build darf fortfahren
    1 — fehlende Einträge gefunden, Build wird abgebrochen
"""

import ast
import re
import sys
from pathlib import Path

# ── Pfade ermitteln ────────────────────────────────────────────────────────────
THIS_FILE = Path(__file__).resolve()
INSTALLER_DIR = THIS_FILE.parent
APP_DIR = INSTALLER_DIR.parent
SPEC_FILE = INSTALLER_DIR / "athletik.spec"

# Dateien/Ordner, die bewusst NICHT in local_modules erscheinen müssen
EXCLUDED_FILES = {
    "app.py",        # Streamlit-Einstiegspunkt, kein importiertes Modul
    "launcher.py",   # PyInstaller-Launcher, liegt im installer/-Ordner
}
EXCLUDED_PREFIXES = ("backup_",)  # Backup-Dateien ignorieren


def extract_local_modules(spec_text: str) -> list[str]:
    """Liest die local_modules-Liste aus dem Spec-Text heraus."""
    # Suche: local_modules = [ ... ] (mehrzeilig)
    match = re.search(
        r"local_modules\s*=\s*(\[.*?\])",
        spec_text,
        re.DOTALL,
    )
    if not match:
        print("FEHLER: local_modules-Liste in athletik.spec nicht gefunden.")
        sys.exit(1)
    try:
        return ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError) as exc:
        print(f"FEHLER: local_modules konnte nicht geparst werden: {exc}")
        sys.exit(1)


def collect_expected_modules() -> list[str]:
    """
    Ermittelt alle Module, die in local_modules stehen müssen:
    - Jede .py-Datei im App-Verzeichnis (außer Ausschlüssen) → Modulname
    - Jeder Unterordner mit __init__.py → Paketname + alle darin enthaltenen .py
    """
    expected: list[str] = []

    # ── Top-Level .py-Dateien ──────────────────────────────────────────────────
    for py_file in sorted(APP_DIR.glob("*.py")):
        if py_file.name in EXCLUDED_FILES:
            continue
        if any(py_file.name.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        expected.append(py_file.stem)

    # ── Paket-Unterordner (mit __init__.py) ───────────────────────────────────
    for subdir in sorted(APP_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        init = subdir / "__init__.py"
        if not init.exists():
            continue
        pkg = subdir.name
        expected.append(pkg)  # das Paket selbst: z. B. "modules"
        for py_file in sorted(subdir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            if any(py_file.name.startswith(p) for p in EXCLUDED_PREFIXES):
                continue
            expected.append(f"{pkg}.{py_file.stem}")  # z. B. "modules.vereine"

    return expected


def main() -> int:
    if not SPEC_FILE.exists():
        print(f"FEHLER: Spec-Datei nicht gefunden: {SPEC_FILE}")
        return 1

    spec_text = SPEC_FILE.read_text(encoding="utf-8")
    registered = set(extract_local_modules(spec_text))
    expected = collect_expected_modules()

    missing = [m for m in expected if m not in registered]

    if not missing:
        print("  Spec-Prüfung bestanden: alle lokalen Module sind eingetragen.")
        return 0

    print()
    print("=" * 60)
    print("  FEHLER: Fehlende Einträge in local_modules (athletik.spec)")
    print("=" * 60)
    for m in missing:
        print(f"    \"{m}\",")
    print()
    print("  Bitte die obigen Module in die local_modules-Liste in")
    print(f"  {SPEC_FILE.name} eintragen und den Build erneut starten.")
    print("=" * 60)
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
