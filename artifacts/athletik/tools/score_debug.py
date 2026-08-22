"""Read-only Diagnose für die zentrale Leistungs-Score-Basis.

Beispiel:
    python tools/score_debug.py --spieler-id 42
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analytics import athletik_leistungsbewertung
from database import (
    spieler_by_id, fms_letzter, y_balance_letzter, sprint_letzter,
    sprung_letzter, agilitaet_letzter, ausdauer_letzter, kraft_letzter,
    spiro_test_letzter,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="APH Leistungs-Score Diagnose (read-only)")
    parser.add_argument("--spieler-id", type=int, required=True)
    args = parser.parse_args()

    spieler = spieler_by_id(args.spieler_id)
    if not spieler:
        parser.error(f"Spieler {args.spieler_id} wurde nicht gefunden.")

    pid = spieler["id"]
    bewertung = athletik_leistungsbewertung(
        fms_letzter(pid), y_balance_letzter(pid), sprint_letzter(pid),
        sprung_letzter(pid), agilitaet_letzter(pid), ausdauer_letzter(pid),
        spiro_row=spiro_test_letzter(pid), kraft_row=kraft_letzter(pid),
        geschlecht=spieler.get("geschlecht", "Männlich"),
        geburtsdatum=spieler.get("geburtsdatum"),
    )
    print(json.dumps({
        "spieler_id": pid,
        "spieler": spieler.get("name"),
        "leistungsbewertung": asdict(bewertung),
        "datenbasis": bewertung.datenbasis_text,
        "hinweis": "Das Werkzeug liest ausschließlich Daten und schreibt nichts in die Datenbank.",
    }, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())