"""
PDF-Export für Testanleitungen — Football Athletik Diagnostik.
Erzeugt druckbare Coaching-Anleitungen aus test_help.py.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
from datetime import date

from fpdf import FPDF

from test_help import TEST_HELP, SICHERHEITSHINWEIS_ALLGEMEIN, COMPLIANCE_HINWEIS
from safety_texts import PDF_FUSSZEILE


# ─── Encoding-Schutz ─────────────────────────────────────────────────────────

_REPLACEMENTS = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2012": "-",   # figure dash
    "\u2010": "-",   # hyphen
    "\u2019": "'",   # right single quotation mark
    "\u2018": "'",   # left single quotation mark
    "\u201c": '"',   # left double quotation mark
    "\u201d": '"',   # right double quotation mark
    "\u2026": "...", # ellipsis
    "\u2082": "2",   # subscript 2 (VO2max)
    "\u00d7": "x",   # multiplication sign
    "\u00b2": "2",   # superscript 2
    "\u00b3": "3",   # superscript 3
    "\u2248": "~",   # approximately equal
    "\u00b0": " Grad",  # degree sign
    "\u2080": "0",   # subscript 0
    "\u2081": "1",   # subscript 1
}


def _safe(text) -> str:
    """Konvertiert beliebigen Text in Latin-1-kompatiblen String."""
    if text is None:
        return "-"
    s = str(text)
    for old, new in _REPLACEMENTS.items():
        s = s.replace(old, new)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _sanitize_svg(svg_content: str) -> str:
    """Bereinigt SVG-Inhalt für fpdf2-Kompatibilität."""
    for old, new in _REPLACEMENTS.items():
        svg_content = svg_content.replace(old, new)
    # Entferne Zeichen außerhalb Latin-1
    svg_content = svg_content.encode("latin-1", errors="replace").decode("latin-1")
    return svg_content


# ─── Farben ──────────────────────────────────────────────────────────────────

BRAND  = (20, 90, 160)
ACCENT = (230, 50, 50)
LIGHT  = (245, 247, 250)
DARK   = (30, 30, 40)
MID    = (80, 90, 110)
WHITE  = (255, 255, 255)
GREEN  = (39, 174, 96)
YELLOW = (200, 140, 30)
RED    = (200, 60, 50)
ORANGE = (200, 100, 30)


# ─── PDF-Klasse ──────────────────────────────────────────────────────────────

class AnleitungPDF(FPDF):
    """FPDF-Subklasse für Testanleitungs-Dokumente."""

    _doc_title: str = "Testanleitungen"

    def header(self):
        self.set_fill_color(*BRAND)
        self.rect(0, 0, 210, 16, "F")
        self.set_y(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.cell(0, 10, "  FOOTBALL ATHLETIK DIAGNOSTIK  |  Testanleitungen", align="L")
        self.set_font("Helvetica", "", 7)
        self.set_xy(0, 5)
        self.cell(0, 7, f"Erstellt am {date.today().strftime('%d.%m.%Y')}  ", align="R")
        self.set_text_color(*DARK)
        self.ln(13)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*BRAND)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 6.5)
        self.set_text_color(*MID)
        self.cell(0, 8, f"Seite {self.page_no()}  |  {_safe(PDF_FUSSZEILE)}", align="C")

    def section_title(self, title: str, color=BRAND):
        self.ln(3)
        self.set_fill_color(*color)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, "  " + _safe(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*DARK)
        self.ln(1)

    def label_value(self, label: str, value, indent: int = 0):
        x0 = self.get_x() + indent
        self.set_x(x0)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*MID)
        self.cell(42 - indent, 5, _safe(label) + ":", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*DARK)
        # Multi-line if needed
        self.multi_cell(0, 5, _safe(value), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*DARK)

    def bullet_list(self, items: list, indent: int = 6):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*DARK)
        for item in items:
            x = self.get_x()
            self.set_x(x + indent)
            # bullet dot
            self.cell(4, 5, chr(149), new_x="RIGHT", new_y="TOP")
            self.multi_cell(0, 5, _safe(item), new_x="LMARGIN", new_y="NEXT")

    def info_box(self, text: str, bg=(235, 245, 255), border_color=BRAND):
        self.ln(1)
        self.set_fill_color(*bg)
        self.set_draw_color(*border_color)
        self.set_line_width(0.4)
        x, y = self.get_x(), self.get_y()
        # Draw left border
        self.set_fill_color(*bg)
        self.rect(x, y, 190, 0, "")  # placeholder height
        self.set_x(x + 4)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*DARK)
        self.multi_cell(183, 4.5, _safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def warning_box(self, text: str):
        self.ln(1)
        self.set_fill_color(255, 243, 205)
        self.set_draw_color(*ORANGE)
        self.set_line_width(0.5)
        x, y = self.get_x(), self.get_y()
        # Colored left stripe
        self.set_fill_color(*ORANGE)
        h_est = max(10, len(_safe(text)) // 80 * 4.5 + 6)
        self.rect(x, y, 3, h_est, "F")
        self.set_fill_color(255, 248, 220)
        self.rect(x + 3, y, 187, h_est, "F")
        self.set_x(x + 6)
        self.set_y(y + 1.5)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*ORANGE)
        self.cell(20, 4, "HINWEIS:", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*DARK)
        self.multi_cell(0, 4.5, _safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def embed_svg(self, svg_path: str, w: float = 140) -> bool:
        """
        Versucht SVG einzubetten. Gibt True zurück wenn erfolgreich.
        Bereinigt SVG-Inhalt vor dem Einbetten.
        """
        if not os.path.isfile(svg_path):
            return False
        try:
            with open(svg_path, "r", encoding="utf-8", errors="replace") as f:
                svg_content = f.read()
            svg_content = _sanitize_svg(svg_content)
            with tempfile.NamedTemporaryFile(
                suffix=".svg", delete=False, mode="w", encoding="latin-1", errors="replace"
            ) as tmp:
                tmp.write(svg_content)
                tmp_path = tmp.name
            try:
                x = (210 - w) / 2
                self.image(tmp_path, x=x, y=self.get_y(), w=w)
                self.ln(4)
            finally:
                os.unlink(tmp_path)
            return True
        except Exception:
            return False


# ─── Test-Seite rendern ──────────────────────────────────────────────────────

def _render_test(pdf: AnleitungPDF, test_id: str, assets_base: str = "assets") -> None:
    """Rendert eine vollständige Testanleitung auf einem neuen PDF-Abschnitt."""
    data = TEST_HELP.get(test_id)
    if data is None:
        return

    # ── Deckzeile ─────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(*BRAND)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe(data["name"]), fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)

    # Kurzbeschreibung
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*MID)
    pdf.multi_cell(0, 5, _safe(data.get("kurzbeschreibung", "")), align="C")
    pdf.ln(3)
    pdf.set_text_color(*DARK)

    # ── Zwei-Spalten: Basisinfo + SVG ─────────────────────────────────────────
    col_w = 90
    y_before_cols = pdf.get_y()

    # Linke Spalte — Basisinfos
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(*LIGHT)
    pdf.cell(col_w, 6, "  Testübersicht", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    for label, key in [
        ("Ziel", "ziel"),
        ("Material", "material"),
        ("Messwert", "messwert"),
        ("Einheit", "einheit"),
        ("Versuche", "versuche"),
        ("Pause", "pause"),
    ]:
        val = data.get(key, "")
        if val:
            pdf.set_x(10)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*MID)
            pdf.cell(28, 5, _safe(label) + ":", new_x="RIGHT", new_y="TOP")
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*DARK)
            # wrap into left column width
            pdf.multi_cell(col_w - 28, 5, _safe(val), new_x="LMARGIN", new_y="NEXT")

    y_after_left = pdf.get_y()

    # Rechte Spalte — SVG-Skizze
    svg_path_rel = data.get("bild_pfad", "")
    if svg_path_rel:
        # Build absolute path
        base_dir = os.path.join(os.path.dirname(__file__))
        svg_abs = os.path.join(base_dir, svg_path_rel)
        if os.path.isfile(svg_abs):
            x_right = 10 + col_w + 5
            y_svg = y_before_cols
            # Save position, move to right column
            pdf.set_xy(x_right, y_svg)
            try:
                with open(svg_abs, "r", encoding="utf-8", errors="replace") as f:
                    svg_content = f.read()
                svg_content = _sanitize_svg(svg_content)
                with tempfile.NamedTemporaryFile(
                    suffix=".svg", delete=False, mode="w",
                    encoding="latin-1", errors="replace"
                ) as tmp:
                    tmp.write(svg_content)
                    tmp_path = tmp.name
                try:
                    pdf.image(tmp_path, x=x_right, y=y_svg, w=95)
                finally:
                    os.unlink(tmp_path)
            except Exception:
                # Fallback: show path as note
                pdf.set_xy(x_right, y_svg + 10)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(*MID)
                pdf.cell(95, 5, _safe(f"Skizze: {svg_path_rel}"), align="C")

    pdf.set_y(max(y_after_left, y_before_cols + 40) + 4)
    pdf.set_text_color(*DARK)

    # ── Aufbau & Aufwärmung ───────────────────────────────────────────────────
    pdf.section_title("Aufbau & Vorbereitung")
    if data.get("aufbau"):
        pdf.label_value("Aufbau", data["aufbau"])
    if data.get("aufwaermung"):
        pdf.label_value("Aufwarmung", data["aufwaermung"])

    # ── Durchführung ──────────────────────────────────────────────────────────
    pdf.section_title("Durchfuhrung")
    if data.get("durchfuehrung"):
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, _safe(data["durchfuehrung"]))
        pdf.ln(1)

    # ── Trainerhinweis ────────────────────────────────────────────────────────
    if data.get("trainerhinweis"):
        pdf.section_title("Trainerhinweis", color=(40, 120, 60))
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, _safe(data["trainerhinweis"]))
        pdf.ln(1)

    # ── Gültig / Ungültig ─────────────────────────────────────────────────────
    if data.get("gueltiger_versuch") or data.get("ungueltiger_versuch"):
        pdf.section_title("Gultige und ungultige Versuche")
        if data.get("gueltiger_versuch"):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*GREEN)
            pdf.cell(0, 5, "Gultig:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*DARK)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 5, _safe(data["gueltiger_versuch"]))
        if data.get("ungueltiger_versuch"):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*RED)
            pdf.cell(0, 5, "Ungultig:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*DARK)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 5, _safe(data["ungueltiger_versuch"]))
        pdf.ln(1)

    # ── Häufige Fehler ────────────────────────────────────────────────────────
    fehler = data.get("fehler", [])
    if fehler:
        pdf.section_title("Haufige Fehler")
        pdf.bullet_list(fehler)

    # ── Sicherheitshinweis ────────────────────────────────────────────────────
    sicherheit = data.get("sicherheit", "")
    if sicherheit:
        pdf.ln(2)
        pdf.set_fill_color(255, 235, 235)
        pdf.set_draw_color(*RED)
        pdf.set_line_width(0.5)
        x, y = pdf.get_x(), pdf.get_y()
        h_est = max(12, len(_safe(sicherheit)) // 90 * 4.5 + 8)
        pdf.set_fill_color(*RED)
        pdf.rect(x, y, 3, h_est, "F")
        pdf.set_fill_color(255, 240, 240)
        pdf.rect(x + 3, y, 187, h_est, "F")
        pdf.set_x(x + 6)
        pdf.set_y(y + 2)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*RED)
        pdf.cell(25, 4, "SICHERHEIT:", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 4.5, _safe(sicherheit), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ── Quelle ────────────────────────────────────────────────────────────────
    quelle = data.get("quelle", "")
    if quelle:
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MID)
        pdf.cell(0, 5, "Quelle: " + _safe(quelle), new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*DARK)


# ─── Deckblatt ────────────────────────────────────────────────────────────────

def _render_cover(pdf: AnleitungPDF, test_names: list[str]) -> None:
    """Optionales Deckblatt mit Inhaltsverzeichnis."""
    pdf.add_page()
    pdf.ln(10)

    # Haupttitel
    pdf.set_fill_color(*BRAND)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 14, "TESTANLEITUNGEN", fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*WHITE)
    pdf.set_fill_color(*BRAND)
    pdf.cell(0, 8, "Football Athletik Diagnostik", fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)
    pdf.set_text_color(*DARK)

    # Datum
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID)
    pdf.cell(0, 6, f"Erstellt am {date.today().strftime('%d. %B %Y')}", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Enthaltene Tests
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, "  Enthaltene Tests:", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for i, name in enumerate(test_names, 1):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(20)
        pdf.set_fill_color(*BRAND)
        pdf.set_text_color(*WHITE)
        pdf.cell(7, 6, str(i), fill=True, align="C", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(*DARK)
        pdf.set_fill_color(*LIGHT)
        pdf.cell(0, 6, "  " + _safe(name), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.ln(12)

    # Allgemeiner Sicherheitshinweis
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*LIGHT)
    pdf.cell(0, 6, "  Allgemeiner Sicherheitshinweis:", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 5, _safe(SICHERHEITSHINWEIS_ALLGEMEIN))
    pdf.ln(3)

    # Compliance
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(*MID)
    pdf.multi_cell(0, 4.5, _safe(COMPLIANCE_HINWEIS))


# ─── Öffentliche API ─────────────────────────────────────────────────────────

def generate_anleitung_pdf(
    test_ids: list[str],
    mit_deckblatt: bool = True,
) -> bytes:
    """
    Erstellt ein PDF mit Testanleitungen für die angegebenen Test-IDs.

    Args:
        test_ids: Liste von Test-IDs aus TEST_HELP (z.B. ["sprint", "agility"])
        mit_deckblatt: Ob ein Deckblatt mit Inhaltsverzeichnis eingefügt wird.

    Returns:
        PDF als bytes.
    """
    pdf = AnleitungPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(10, 20, 10)

    # Nur existierende Test-IDs verwenden
    valid_ids = [tid for tid in test_ids if tid in TEST_HELP]

    if mit_deckblatt and valid_ids:
        names = [TEST_HELP[tid]["name"] for tid in valid_ids]
        _render_cover(pdf, names)

    for tid in valid_ids:
        _render_test(pdf, tid)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ─── Test-ID Mapping ─────────────────────────────────────────────────────────

ALL_TEST_IDS: list[str] = list(TEST_HELP.keys())

TEST_LABELS: dict[str, str] = {
    tid: TEST_HELP[tid]["name"] for tid in ALL_TEST_IDS
}
