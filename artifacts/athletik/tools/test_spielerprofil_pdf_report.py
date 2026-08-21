"""Regressionstest für den vollständigen Spielerprofil-PDF-Report.

Verwendet ausschließlich synthetische In-Memory-Daten. Der Test schützt das
Querformat, die aktuellen Datenquellen sowie die vollständige Planansicht.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pdf_report import generate_report
from warmup import WARMUP_BEREICH, warmup_meta_kodieren


def run() -> None:
    report = generate_report(
        spieler={
            "vorname": "Mara", "nachname": "Mustermann",
            "geburtsdatum": "2010-05-10", "hauptposition": "Zentrales Mittelfeld",
            "mannschaft": "U17", "altersklasse": "U17", "spielbein": "Rechts",
        },
        anthro_row={
            "datum": "2026-08-20", "groesse": 172, "gewicht": 61.5, "bmi": 20.8,
            "bmi_kategorie": "Normalgewicht", "koerperfett": 16.2,
            "koerperfett_methode": "JP11", "muskelmasse": 47.1,
            "sitzhoehe": 88, "beinlaenge": 91, "armspannweite": 174,
            "phv_offset": 0.3, "reifestatus": "post-PHV",
        },
        fms_row={
            "datum": "2026-08-20", "score": 15, "bewertung": "Gut",
            "asymmetrie": "Keine", "schwerpunkt": "Stabilität",
            "deep_squat": 2, "hurdle_links": 2, "hurdle_rechts": 3,
            "inline_links": 2, "inline_rechts": 2, "shoulder_links": 3,
            "shoulder_rechts": 3, "aslr_links": 2, "aslr_rechts": 2,
            "trunk": 3, "rotary_links": 2, "rotary_rechts": 3,
        },
        y_row={
            "datum": "2026-08-20", "composite_rechts": 91.2, "composite_links": 89.8,
            "asymmetrie": "unauffällig", "schwerpunkt": "Kontrolle",
            "anterior_rechts": 62, "anterior_links": 60, "diff_anterior": 2,
            "posteromedial_rechts": 95, "posteromedial_links": 94,
            "diff_posteromedial": 1, "posterolateral_rechts": 92,
            "posterolateral_links": 91, "diff_posterolateral": 1,
        },
        sprint_row={
            "datum": "2026-08-20", "beste_5m": 1.06, "beste_10m": 1.86,
            "beste_20m": 3.20, "beste_30m": 4.45, "beschl_index": 0.174,
            "bewertung_10m": "Gut", "bewertung_30m": "Gut",
        },
        sprung_row={
            "datum": "2026-08-20", "cmj_beid": 37.5, "cmj_rechts": 20.1,
            "cmj_links": 19.7, "cmj_asymmetrie": 2.0, "squat_jump": 32.5,
            "standweit": 195, "bewertung_cmj": "Gut",
        },
        agil_row={
            "datum": "2026-08-20", "t505_r": 2.52, "t505_l": 2.58, "asym_505": 2.4,
            "t5_10_5": 4.80, "t_test": 10.21, "bew_t_test": "Gut",
            "illinois": 16.2, "bew_illinois": "Gut", "modified_t_test": 5.1,
            "pro_agility": 4.8, "arrowhead_r": 8.1, "arrowhead_l": 8.3,
            "zigzag": 6.2, "balsom": 8.8,
        },
        aus_row={
            "datum": "2026-08-20", "test_typ": "Yo-Yo IR1", "distanz_m": 1840,
            "bewertung": "Gut", "vo2max": 52.1, "hf_max": 195, "rpe": 8,
        },
        kraft_row={
            "datum": "2026-08-20", "direktes_1rm": 75, "relative_kraft_direkt": 1.23,
            "ventral_sekunden": 95, "lateral_rechts_sekunden": 76,
            "lateral_links_sekunden": 73, "dorsal_sekunden": 88,
            "rumpf_gesamt_sekunden": 332, "lateral_asymmetrie_prozent": 3.9,
        },
        kraft_versuche=[
            {"uebung": "Bankdrücken", "versuchsnummer": 1, "gewicht": 70,
             "wiederholungen": 1, "gueltig": True},
            {"uebung": "Plank", "versuchsnummer": 1, "zeit_sekunden": 95, "gueltig": True},
        ],
        spiro_row={
            "datum": "2026-08-20", "testtyp": "spiro_laufband",
            "protokoll_name": "Bruce", "protokoll_geraeteart": "Laufband",
            "tester": "Trainerin A", "dauer_minuten": 18, "vo2_peak": 54.2,
            "maximale_geschwindigkeit": 16.0, "maximale_herzfrequenz": 198,
            "vt1_geschwindigkeit": 10.5, "vt1_herzfrequenz": 162,
            "vt2_geschwindigkeit": 13.5, "vt2_herzfrequenz": 181,
            "ruhelaktat": 1.2, "rpe_max": 9,
        },
        spiro_bewertung={"status": "bruce_referenzvergleich", "referenzwert": 50.0,
                          "abweichung": 4.2, "quelle": "Bruce-Protokoll"},
        spiro_stufen=[
            {"stufennummer": 1, "dauer_sekunden": 180, "geschwindigkeit_kmh": 8.0,
             "herzfrequenz_bpm": 140, "laktat_mmol_l": 1.8, "vo2_relativ": 33.4, "rpe": 3},
            {"stufennummer": 2, "dauer_sekunden": 360, "geschwindigkeit_kmh": 10.5,
             "herzfrequenz_bpm": 162, "laktat_mmol_l": 2.4, "vo2_relativ": 42.1, "rpe": 5},
        ],
        spiro_nachbelastung=[{
            "zeitpunkt_minuten": 3, "herzfrequenz_bpm": 168, "laktat_mmol_l": 6.8,
            "bemerkung": "Belastungsende dokumentiert.",
        }],
        verletzungen=[{
            "datum": "2026-05-10", "koerperteil": "Sprunggelenk", "art": "Distorsion",
            "schwere": "leicht", "ausfall_tage": 7, "notizen": "vollständig belastbar",
        }],
        beobachtungen=[{
            "test_id": "sprint", "datum": "2026-08-20",
            "text_generiert": "Körperspannung im Antritt stabil.", "freitext": "Weiter beobachten.",
        }],
        defizite=[{
            "level": "moderat", "bereich": "Rumpfkraft", "text": "Seitliche Stabilität gezielt trainieren.",
        }],
        plan_rows=[
            {
                "woche": 1, "tag": 1, "position": 0, "bereich": WARMUP_BEREICH,
                "uebung": "APH Standard", "saetze": "-", "wiederholungen": "8 min",
                "pause_sekunden": 0, "ausfuehrung": "aktivierend", "rpe": 2,
                "energie_system": "Aktivierung", "equipment": "Körpergewicht",
                "notiz": warmup_meta_kodieren("APH Standard", aph_dauer_min=8),
            },
            {
                "woche": 1, "tag": 1, "position": 1, "bereich": "Kraft",
                "uebung": "Bulgarian Split Squat", "saetze": "3",
                "wiederholungen": "8 je Seite", "pause_sekunden": 90,
                "ausfuehrung": "kontrolliert", "rpe": 7, "energie_system": "ATP-PC",
                "equipment": "Kurzhanteln", "begruendung": "Einbeinige Stabilität",
                "trainerhinweis": "Knieachse kontrollieren", "spielerhinweis": "beidseitig",
                "abgehakt": 1,
            },
        ],
        plan_meta={
            "version_nr": 4, "datum": "2026-08-21", "modus": "Vereinsbelastung",
            "schwerpunkt": "Rumpfkraft und Stabilität", "trainingszeit_min": 55,
            "notizen": "Belastung nach dem Punktspiel anpassen.",
            "wochenplanung_json": '{"planungsmodus":"vereinsbelastung","gewaehlte_athletik_tage":["Dienstag"]}',
        },
        athletik_score=72, risiko_label="Handlungsbedarf moderat",
        vereinsname="Testverein", saison="2026/27", trainer_name="Trainerin A",
    )

    with tempfile.TemporaryDirectory(prefix="spielerprofil-pdf-") as tmp:
        pdf_path = Path(tmp) / "report.pdf"
        text_path = Path(tmp) / "report.txt"
        pdf_path.write_bytes(report)
        info = subprocess.run(
            ["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True
        ).stdout
        pages_match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
        pages = int(pages_match.group(1)) if pages_match else 0
        assert pages >= 4, "vollständiger Bericht braucht mehrere Seiten"
        page_texts = []
        for page_number in range(1, pages + 1):
            page_info = subprocess.run(
                ["pdfinfo", "-f", str(page_number), "-l", str(page_number), str(pdf_path)],
                check=True, capture_output=True, text=True,
            ).stdout
            size_match = re.search(
                r"^Page.*?size:\s+([0-9.]+) x ([0-9.]+) pts",
                page_info, re.MULTILINE | re.IGNORECASE,
            )
            assert size_match, "Seitengröße fehlt auf Seite %d" % page_number
            width, height = map(float, size_match.groups())
            assert width > height, "Seite %d muss A4 Querformat sein" % page_number
            page_text = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", "-f", str(page_number), "-l",
                 str(page_number), str(pdf_path), "-"],
                check=True, capture_output=True, text=True,
            ).stdout
            assert len(page_text.strip()) > 40, "unerwartete Leerseite: %d" % page_number
            page_texts.append(page_text)
        subprocess.run(
            ["pdftotext", "-enc", "UTF-8", str(pdf_path), str(text_path)],
            check=True, capture_output=True, text=True,
        )
        text = text_path.read_text(encoding="utf-8") + "\n".join(page_texts)
    for expected in (
        "SPIROERGOMETRIE", "STUFENPROTOKOLL", "EINZELVERSUCHE",
        "INDIVIDUELLER TRAININGSPLAN", "Version 4", "Bulgarian Split Squat",
        "Warm-up:", "APH Standard", "TRAINERBEOBACHTUNGEN", "10.5 km/h",
        "6.8 mmol/l", "Dienstag",
    ):
        assert expected in text, "PDF-Inhalt fehlt: %s" % expected

    print("PASS: vollständiger Spielerprofil-PDF im Querformat (%d Seiten)" % pages)


if __name__ == "__main__":
    run()