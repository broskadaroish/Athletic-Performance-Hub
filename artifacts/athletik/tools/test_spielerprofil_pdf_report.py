"""Regressionstest für den vollständigen Spielerprofil-PDF-Report.

Verwendet ausschließlich synthetische In-Memory-Daten. Der Test schützt das
Querformat, Unicode-sichere Textausgabe, die aktuellen Datenquellen sowie die
vollständige Planansicht – ohne externe Systemkommandos oder PDF-Tools.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pdf_report
from warmup import WARMUP_BEREICH, warmup_meta_kodieren


def _text_argument(args, kwargs, index: int) -> str:
    """Liest das Textargument aus einem fpdf2-Aufruf für die Inhalts-Regression."""
    if "text" in kwargs:
        return str(kwargs["text"])
    if "txt" in kwargs:
        return str(kwargs["txt"])
    return str(args[index]) if len(args) > index else ""


def _assert_pdf_structure(pdf_bytes: bytes) -> int:
    """Prüft Seiten und A4-Querformat direkt an der PDF-Struktur."""
    assert pdf_bytes.startswith(b"%PDF-"), "PDF-Kopf fehlt"
    objects = {
        int(match.group(1)): match.group(2)
        for match in re.finditer(
            rb"(\d+)\s+0\s+obj\s*(.*?)\s*endobj", pdf_bytes, re.DOTALL
        )
    }
    page_objects = [
        body for body in objects.values()
        if re.search(rb"/Type\s*/Page\b", body)
    ]
    assert len(page_objects) >= 4, "vollständiger Bericht braucht mehrere Seiten"

    # FPDF schreibt die MediaBox auf dem Pages-Knoten; alle Blattseiten erben sie.
    media_boxes = re.findall(
        rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]",
        pdf_bytes,
    )
    assert media_boxes, "Seitengröße fehlt im PDF"
    for width_raw, height_raw in media_boxes:
        width, height = float(width_raw), float(height_raw)
        assert width > height, "PDF muss A4 Querformat sein"
        assert abs(width - 841.89) < 1 and abs(height - 595.28) < 1, (
            "PDF muss A4-Maße im Querformat verwenden"
        )

    # Jede Page verweist auf einen nicht leeren Content-Stream: Schutz vor
    # unerwarteten Leerseiten ohne pdftotext/pdfinfo-Abhängigkeit.
    for page_number, page in enumerate(page_objects, start=1):
        content_ref = re.search(rb"/Contents\s+(\d+)\s+0\s+R", page)
        assert content_ref, "Content-Referenz fehlt auf Seite %d" % page_number
        content = objects.get(int(content_ref.group(1)), b"")
        stream = re.search(rb"stream\r?\n(.*?)\r?\nendstream", content, re.DOTALL)
        assert stream and len(stream.group(1)) > 40, (
            "unerwartete Leerseite: %d" % page_number
        )
    return len(page_objects)


def _long_realistic_plan_rows() -> list[dict]:
    """Erstellt genug typische Übungen für einen mehrseitigen Spielerplan."""
    rows = [
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
    ]
    exercises = [
        ("Nordic Hamstring Curl", "Kraft", "exzentrisch über drei Sekunden absenken, Hüfte stabil halten"),
        ("Einbeiniger Romanian Deadlift", "Kraft", "Becken waagerecht halten und kontrolliert aufrichten"),
        ("Copenhagen Plank", "Rumpf", "Körperlinie halten, Abduktion aktiv und ohne Hüftrotation ausführen"),
        ("Pogos vorwärts", "Plyometrie", "kurze Bodenkontakte, steifer Fuß und aktive Armführung"),
        ("Resisted Sprint Start", "Sprint", "ersten Schritt explosiv setzen, Rumpf nach vorn ausrichten"),
        ("Landmine Press", "Kraft", "Rippen unten halten und Schulterblatt kontrolliert nach oben führen"),
    ]
    for index in range(2, 32):
        exercise, area, execution = exercises[(index - 2) % len(exercises)]
        rows.append({
            "woche": 1 + index // 10,
            "tag": 1 + index % 3,
            "position": index,
            "bereich": area,
            "uebung": exercise,
            "saetze": "3",
            "wiederholungen": "6–8 je Seite",
            "pause_sekunden": 75 + (index % 3) * 15,
            "ausfuehrung": execution,
            "rpe": 6 + index % 3,
            "energie_system": "ATP-PC / neuromuskulär",
            "equipment": "Kurzhanteln, Bank und Miniband",
            "begruendung": (
                "Verbessert die für Richtungswechsel relevante einbeinige "
                "Kraftübertragung und kontrollierte Landestabilität."
            ),
            "trainerhinweis": (
                "Bei Qualitätsverlust Wiederholung beenden und die Technik "
                "vor der nächsten Serie erneut kurz demonstrieren."
            ),
            "spielerhinweis": "Schmerzfrei trainieren und Belastung direkt rückmelden.",
            "abgehakt": index % 4 == 0,
        })
    return rows


def run() -> None:
    unicode_text = "Rückkehr – Fußball: Größe, Übung, Straße, 5×6"
    normalized_unicode = pdf_report._safe(unicode_text)
    assert normalized_unicode == "Rückkehr - Fußball: Größe, Übung, Straße, 5x6"
    normalized_unicode.encode("latin-1")

    rendered_text = []
    plan_table_widths = []
    plan_row_heights = []
    plan_header_pages = []
    base_report = pdf_report.AthletikReport

    class RecordingAthletikReport(base_report):
        """Erfasst die zentral normalisierten Ausgabetexte ohne PDF-Parser."""

        def cell(self, *args, **kwargs):
            rendered_text.append(pdf_report._safe(_text_argument(args, kwargs, 2)))
            return super().cell(*args, **kwargs)

        def multi_cell(self, *args, **kwargs):
            rendered_text.append(pdf_report._safe(_text_argument(args, kwargs, 2)))
            return super().multi_cell(*args, **kwargs)

        def table_header(self, cols, *args, **kwargs):
            if cols and cols[0][0] == "Woche / Tag":
                plan_header_pages.append(self.page_no())
            return super().table_header(cols, *args, **kwargs)

        def table_row_tp_report(self, vals, widths, *args, **kwargs):
            plan_table_widths.append((sum(widths), self.content_width))
            row_height = super().table_row_tp_report(vals, widths, *args, **kwargs)
            plan_row_heights.append(row_height)
            return row_height

    pdf_report.AthletikReport = RecordingAthletikReport
    try:
        report = pdf_report.generate_report(
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
        plan_rows=_long_realistic_plan_rows(),
        plan_meta={
            "version_nr": 4, "datum": "2026-08-21",
            "modus": "Vereinsbelastung – Fußball",
            "schwerpunkt": "Rumpfkraft und Stabilität", "trainingszeit_min": 55,
            "notizen": "Rückkehr – Fußball: Größe, Übung und Straße berücksichtigen.",
            "wochenplanung_json": '{"planungsmodus":"vereinsbelastung","gewaehlte_athletik_tage":["Dienstag"]}',
        },
        athletik_score=72, risiko_label="Handlungsbedarf moderat",
        vereinsname="Testverein", saison="2026/27", trainer_name="Trainerin A",
        )
    finally:
        pdf_report.AthletikReport = base_report

    pages = _assert_pdf_structure(report)
    assert pages >= 10, "langer Trainingsplan muss mehrere Planseiten erzeugen"
    assert len(plan_table_widths) == 32, "jede Planübung muss als Tabellenzeile erscheinen"
    assert all(width <= content_width + 0.01 for width, content_width in plan_table_widths), (
        "Trainingsplantabelle darf nicht über die A4-Inhaltsbreite laufen"
    )
    assert len(set(plan_header_pages)) >= 2, (
        "Trainingsplan-Kopf muss auf jeder Folgeseite wiederholt werden"
    )
    assert max(plan_row_heights) <= 18.5, (
        "Hinweise dürfen keine unnötig hohen Tabellenzeilen erzeugen"
    )
    text = "\n".join(rendered_text)
    for expected in (
        "SPIROERGOMETRIE", "STUFENPROTOKOLL", "EINZELVERSUCHE",
        "INDIVIDUELLER TRAININGSPLAN", "Version 4", "Bulgarian Split Squat",
        "Warm-up:", "APH Standard", "TRAINERBEOBACHTUNGEN", "10.5 km/h",
        "6.8 mmol/l", "Dienstag", "Vereinsbelastung - Fußball",
        "Rückkehr - Fußball: Größe, Übung und Straße berücksichtigen.",
    ):
        assert expected in text, "PDF-Inhalt fehlt: %s" % expected

    print(
        "PASS: vollständiger Spielerprofil-PDF in A4 Querformat "
        "mit Unicode-Schutz und Mehrseiten-Plan (%d Seiten, ohne pdfinfo)" % pages
    )


if __name__ == "__main__":
    run()