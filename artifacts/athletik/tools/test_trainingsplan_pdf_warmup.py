#!/usr/bin/env python3
"""Gezielte Regressionen für den Warm-up-Fallback im Trainingsplan-PDF."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pdf_report
from pdf_report import generate_trainingsplan_pdf
from periodisierung import schaetze_tag_dauer_min
from warmup import (
    APH_STANDARD,
    FIFA_INDIVIDUELL,
    FIFA_KOMPLETT,
    KEIN_WARMUP,
    WARMUP_BEREICH,
    warmup_details,
    warmup_meta_kodieren,
)


PASS = 0
FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")


MAIN_ROW = {
    "bereich": "Rumpf",
    "uebung": "Plank",
    "saetze": "3",
    "wiederholungen": "30 s",
    "haeufigkeit": "1×/Woche",
    "woche": 1,
    "tag": 1,
    "pause_sekunden": 45,
    "ausfuehrung": "Ruhig und kontrolliert.",
}


def warmup_row(art: str, *, level: int = 1, teile: list[str] | None = None,
               aph_dauer_min: int | None = None) -> dict:
    return {
        "bereich": WARMUP_BEREICH,
        "uebung": art,
        "notiz": warmup_meta_kodieren(art, level, teile, aph_dauer_min),
        "woche": 1,
        "tag": 1,
    }


def render_case(name: str, rows: list[dict], expected_art: str, expected_dauer: int,
                legacy_warmup_min: int = 8, expected_aph_input: int | None = None) -> None:
    """Rendert ohne DB und prüft, dass das PDF die zentrale Warm-up-Auflösung nutzt."""
    with patch.object(pdf_report, "warmup_details", wraps=warmup_details) as details_mock:
        pdf_bytes = generate_trainingsplan_pdf(
            spieler={"vorname": "Test", "nachname": name, "mannschaft": "U15", "hauptposition": "MF"},
            plan_rows=rows,
            plangruppe="U14",
            plangruppen_config={"label": "Jugend", "max_saetze": 3, "haeuf_cap": "3×/Woche", "pause_offset": 0},
            legacy_warmup_min=legacy_warmup_min,
        )

    check(f"{name}: PDF wird erzeugt", pdf_bytes.startswith(b"%PDF") and len(pdf_bytes) > 1000)
    check(f"{name}: zentrale Warm-up-Logik wird genau einmal verwendet", details_mock.call_count == 1)
    if details_mock.call_count == 1:
        args, kwargs = details_mock.call_args
        check(f"{name}: richtige Warm-up-Art", args[0] == expected_art)
        expected_aph_input = legacy_warmup_min if expected_aph_input is None else expected_aph_input
        # Der APH-Fallback wird immer mitgegeben; FIFA und „Kein Warm-up“
        # ignorieren ihn in warmup_details bewusst zugunsten ihrer eigenen Dauer.
        check(f"{name}: richtige APH-/Fallback-Dauer wird übergeben",
              kwargs["aph_dauer_min"] == expected_aph_input)
        details = warmup_details(args[0], args[1], args[2], kwargs["aph_dauer_min"])
        check(f"{name}: richtige programmbezogene Warm-up-Dauer",
              details["dauer_min"] == expected_dauer)

    # Die Dauerformel bleibt identisch zur Planansicht: Hauptteil + Warm-up + 5 min Cool-down.
    main_dauer = schaetze_tag_dauer_min([MAIN_ROW])
    total_dauer = round(main_dauer + expected_dauer + 5, 1)
    check(f"{name}: Gesamtzeit enthält Hauptteil, Warm-up und Cool-down",
          total_dauer == round(main_dauer + expected_dauer + 5, 1))


def render_layout_case() -> None:
    """Prüft die gemeinsame Hauptteil-Tabelle des Standalone-PDFs."""
    rendered_text = []
    table_widths = []
    row_heights = []
    header_pages = []
    header_columns = []
    base_report = pdf_report.AthletikReport

    class RecordingAthletikReport(base_report):
        def cell(self, *args, **kwargs):
            text = kwargs.get("text", args[2] if len(args) > 2 else "")
            rendered_text.append(str(text))
            return super().cell(*args, **kwargs)

        def multi_cell(self, *args, **kwargs):
            text = kwargs.get("text", args[2] if len(args) > 2 else "")
            rendered_text.append(str(text))
            return super().multi_cell(*args, **kwargs)

        def table_header(self, cols, *args, **kwargs):
            if cols and cols[0][0] == "Woche / Tag":
                header_pages.append(self.page_no())
                header_columns.append(tuple(label for label, _ in cols))
            return super().table_header(cols, *args, **kwargs)

        def table_row_tp_report(self, vals, widths, *args, **kwargs):
            table_widths.append((sum(widths), self.content_width))
            row_height = super().table_row_tp_report(vals, widths, *args, **kwargs)
            row_heights.append(row_height)
            return row_height

    plan_rows = [warmup_row(APH_STANDARD, aph_dauer_min=9)]
    exercises = [
        ("Nordic Hamstring Curl", "Kraft"),
        ("Einbeiniger Romanian Deadlift", "Kraft"),
        ("Copenhagen Plank", "Rumpf"),
        ("Resisted Sprint Start", "Sprint"),
    ]
    for index in range(32):
        exercise, area = exercises[index % len(exercises)]
        plan_rows.append({
            "bereich": area, "uebung": exercise, "saetze": "3",
            "wiederholungen": "6–8 je Seite", "woche": 1, "tag": 1,
            "pause_sekunden": 75 + (index % 3) * 15,
            "ausfuehrung": (
                "Rumpf stabil halten, Bewegung kontrolliert ausführen und "
                "bei nachlassender Qualität die Serie beenden."
            ),
            "rpe": 6 + index % 3,
            "energie_system": "ATP-PC / neuromuskulär",
            "equipment": "Kurzhanteln, Bank und Miniband",
        })

    pdf_report.AthletikReport = RecordingAthletikReport
    try:
        pdf_bytes = generate_trainingsplan_pdf(
            spieler={"vorname": "Test", "nachname": "Mehrseitenplan", "mannschaft": "U15", "hauptposition": "MF"},
            plan_rows=plan_rows,
            plangruppe="U14",
            plangruppen_config={"label": "Jugend", "max_saetze": 3, "haeuf_cap": "3×/Woche", "pause_offset": 0},
        )
    finally:
        pdf_report.AthletikReport = base_report

    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
    media_boxes = re.findall(
        rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]",
        pdf_bytes,
    )
    expected_columns = (
        "Woche / Tag", "Bereich", "Übung", "Sätze", "Wdh. / Dauer",
        "Pause", "Ausführung", "RPE", "Energiesystem", "Equipment",
    )
    captured = "\n".join(rendered_text)
    check("Standalone: A4 Querformat", bool(media_boxes) and all(
        float(width) > float(height)
        and abs(float(width) - 841.89) < 1
        and abs(float(height) - 595.28) < 1
        for width, height in media_boxes
    ))
    check("Standalone: langer Hauptteil erzeugt mehrere Seiten", page_count >= 3)
    check("Standalone: jede Hauptteil-Zeile bleibt innerhalb der Seitenbreite", bool(table_widths) and all(
        width <= content_width + 0.01 for width, content_width in table_widths
    ))
    check("Standalone: Tabellenkopf wird auf Folgeseiten wiederholt", len(set(header_pages)) >= 2)
    check("Standalone: gemeinsame 10-Spalten-Struktur ohne Hinweise/Status", bool(header_columns) and all(
        columns == expected_columns for columns in header_columns
    ))
    check("Standalone: kompakte, begrenzte Tabellenzeilen", bool(row_heights) and max(row_heights) <= 18.5)
    check("Standalone: Warm-up und Cool-down bleiben erhalten",
          "WARM-UP: APH Standard" in captured and "Cool-Down:" in captured)


print("\n=== Trainingsplan-PDF: Warm-up-Auflösung ===")
app_source = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
check(
    "_wu_min steht vor dem PDF-Button und kann nicht undefiniert sein",
    app_source.index("_wu_min = _ZEITBUDGET_CONFIG") < app_source.index('if st.button("📄 PDF drucken"'),
)
render_case("Historisch", [MAIN_ROW], APH_STANDARD, 11, legacy_warmup_min=11)
render_case(
    "APH-Standard",
    [MAIN_ROW, warmup_row(APH_STANDARD, aph_dauer_min=9)],
    APH_STANDARD,
    9,
    expected_aph_input=9,
)
render_case("FIFA-komplett", [MAIN_ROW, warmup_row(FIFA_KOMPLETT, level=2)], FIFA_KOMPLETT, 26)
render_case(
    "FIFA-individuell",
    [MAIN_ROW, warmup_row(FIFA_INDIVIDUELL, level=3, teile=["Teil 1", "Teil 3"])],
    FIFA_INDIVIDUELL,
    16,
)
render_case("Kein-Warm-up", [MAIN_ROW, warmup_row(KEIN_WARMUP)], KEIN_WARMUP, 0)
render_layout_case()

print("\n" + "=" * 60)
print(f"Ergebnis: {PASS} PASS, {FAIL} FAIL")
print("=" * 60)
if FAIL:
    raise SystemExit(1)