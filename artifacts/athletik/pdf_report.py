"""
PDF Report generation — vollständiger Athletik-Bericht für alle Testmodule.
Verwendet fpdf2 (from fpdf import FPDF).

Hinweis: Nur Helvetica (Latin-1) wird verwendet — alle Texte werden vor der
Ausgabe durch _safe() gefiltert, um UnicodeEncodingException zu vermeiden.
"""

from fpdf import FPDF
from datetime import date
import io

from safety_texts import (
    PDF_FUSSZEILE,
    ZWECKBESTIMMUNG_TEXT,
    AMPEL_GRUEN,
    AMPEL_GELB,
    AMPEL_ROT,
    FMS_HINWEIS,
    TRAININGSPLAN_HINWEIS,
    KURZ_HINWEIS,
    ABBRUCH_HINWEIS,
)


# ─── Encoding-Schutz ─────────────────────────────────────────────────────────

def _safe(text) -> str:
    """
    Konvertiert beliebigen Text in Latin-1-kompatiblen String.
    Nicht darstellbare Zeichen werden durch ASCII-Alternativen ersetzt.
    """
    if text is None:
        return "-"
    replacements = {
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
        "\u00b0": " Grad", # degree sign
    }
    # Emojis und sonstige non-Latin-1-Zeichen entfernen
    for old, new in replacements.items():
        text = str(text).replace(old, new)
    # Alles was nicht Latin-1 ist, durch "?" ersetzen
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


# ─── Ampelfarben ──────────────────────────────────────────────────────────────
GREEN  = (39, 174, 96)
YELLOW = (230, 126, 34)
RED    = (231, 76, 60)
GREY   = (140, 150, 170)

def ampel(bewertung: str):
    """Gibt RGB-Tuple fuer Bewertungstext zurueck."""
    b = _safe(bewertung).lower()
    if any(x in b for x in ["sehr gut", "gut", "niedrig", "normalgewicht", "nach dem wachstum"]):
        return GREEN
    if any(x in b for x in ["mittel", "breitensport", "im wachstum", "vor dem wachstum"]):
        return YELLOW
    if any(x in b for x in ["hoch", "kritisch", "verbesserung", "untergewicht",
                              "uebergewicht", "bergewicht", "adipositas",
                              "handlungsbedarf", "schlecht", "mangelhaft"]):
        return RED
    return GREY


class AthletikReport(FPDF):
    BRAND   = (20, 90, 160)
    ACCENT  = (230, 50, 50)
    LIGHT   = (245, 247, 250)
    DARK    = (30, 30, 40)
    MID     = (80, 90, 110)
    WHITE   = (255, 255, 255)

    def header(self):
        self.set_fill_color(*self.BRAND)
        self.rect(0, 0, 210, 18, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.WHITE)
        self.cell(0, 10, "  BRUCE FOOTBALL PERFORMANCE DIAGNOSTICS", align="L")
        self.set_font("Helvetica", "", 7)
        self.set_xy(0, 6)
        self.cell(0, 8, f"Erstellt am {date.today().strftime('%d.%m.%Y')}  ", align="R")
        self.set_text_color(*self.DARK)
        self.ln(14)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*self.BRAND)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.MID)
        copyright_note = "(c) 2026 Broska Daroish. Alle Rechte vorbehalten."
        footer_text = "Seite %d  |  %s  |  %s" % (
            self.page_no(), copyright_note, _safe(PDF_FUSSZEILE))
        self.cell(0, 8, footer_text, align="C")

    def section_title(self, title: str):
        self.ln(3)
        self.set_fill_color(*self.BRAND)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, "  " + _safe(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)
        self.ln(1)

    def kv(self, key: str, value, w_key=65):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.MID)
        self.cell(w_key, 5, _safe(key) + ":", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK)
        self.cell(0, 5, _safe(value), new_x="LMARGIN", new_y="NEXT")

    def kv_color(self, key: str, value, color, w_key=65):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.MID)
        self.cell(w_key, 5, _safe(key) + ":", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.cell(0, 5, _safe(value), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)

    def metric_box(self, label: str, value: str, color=None):
        if color is None:
            color = GREY
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*self.LIGHT)
        self.rect(x, y, 58, 16, "F")
        self.set_fill_color(*color)
        self.rect(x, y, 3, 16, "F")
        self.set_xy(x + 5, y + 1)
        self.set_font("Helvetica", "", 6)
        self.set_text_color(*self.MID)
        self.cell(50, 4, _safe(label).upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_x(x + 5)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.DARK)
        self.cell(50, 9, _safe(value), new_x="RIGHT", new_y="TOP")
        self.set_xy(x + 61, y)

    def progress_bar(self, label: str, value: int, max_val: int = 3):
        pct = min(value / max_val, 1.0)
        col = GREEN if pct >= 0.75 else YELLOW if pct >= 0.5 else RED
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.DARK)
        self.cell(70, 5, _safe(label), new_x="RIGHT", new_y="TOP")
        x, y = self.get_x(), self.get_y() + 1
        self.set_fill_color(210, 215, 225)
        self.rect(x, y, 80, 3, "F")
        self.set_fill_color(*col)
        self.rect(x, y, 80 * pct, 3, "F")
        self.set_xy(x + 83, y - 1)
        self.set_font("Helvetica", "B", 8)
        self.cell(15, 5, "%d/%d" % (value, max_val), new_x="LMARGIN", new_y="NEXT")

    def row2(self, label: str, val_l, label2: str = "", val_r="",
              color_l=None, color_r=None):
        """Zwei KV-Paare nebeneinander."""
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.MID)
        self.cell(45, 5, _safe(label) + ":", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*(color_l or self.DARK))
        self.cell(45, 5, _safe(val_l), new_x="RIGHT", new_y="TOP")
        if label2:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*self.MID)
            self.cell(40, 5, _safe(label2) + ":", new_x="RIGHT", new_y="TOP")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*(color_r or self.DARK))
            self.cell(0, 5, _safe(val_r), new_x="LMARGIN", new_y="NEXT")
        else:
            self.ln(5)
        self.set_text_color(*self.DARK)

    def table_header(self, cols: list):
        """cols = [(label, width), ...]"""
        self.set_fill_color(*self.BRAND)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 7)
        for label, w in cols:
            self.cell(w, 6, _safe(label), border=0, fill=True)
        self.ln()
        self.set_text_color(*self.DARK)

    def table_row(self, vals: list, widths: list, fill: bool = False):
        self.set_fill_color(*self.LIGHT) if fill else self.set_fill_color(*self.WHITE)
        self.set_font("Helvetica", "", 7)
        for v, w in zip(vals, widths):
            self.cell(w, 5, _safe(v)[:35], fill=True)
        self.ln()

    def check_page_break(self, needed_mm=30):
        if self.get_y() > 270 - needed_mm:
            self.add_page()

    def cover_page(self, spieler: dict, vereinsname: str = "", saison: str = "",
                   athletik_score: int = 0, module_vorhanden: list = None,
                   logo_bytes: bytes | None = None, trainer_name: str = ""):
        """Erstes Blatt — professionelles Deckblatt mit Spieler-Stammdaten."""
        import io as _cio
        module_vorhanden = module_vorhanden or []

        # ── Blauer Header-Block ──────────────────────────────────────────────
        self.set_fill_color(*self.BRAND)
        self.rect(0, 0, 210, 60, "F")

        # Vereinslogo oben rechts im Header
        if logo_bytes:
            try:
                _logo_buf = _cio.BytesIO(logo_bytes)
                self.image(_logo_buf, x=170, y=8, h=20, keep_aspect_ratio=True)
            except Exception:
                pass

        # Verein / Organisation
        self.set_xy(15, 10)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.WHITE)
        self.cell(0, 7, _safe(vereinsname or "FOOTBALL ATHLETIK DIAGNOSTIK"))

        # Saison
        if saison:
            self.set_xy(15, 17)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(200, 215, 240)
            self.cell(0, 5, "Saison " + _safe(saison))

        # Spielername gross
        vorname  = spieler.get("vorname") or ""
        nachname = spieler.get("nachname") or spieler.get("name") or "-"
        fullname = ("%s %s" % (vorname, nachname)).strip()
        self.set_xy(15, 27)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*self.WHITE)
        self.cell(180, 12, _safe(fullname)[:36])

        # Position / Mannschaft
        pos = (spieler.get("hauptposition") or spieler.get("position") or "-")
        team = spieler.get("mannschaft") or "-"
        self.set_xy(15, 42)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(200, 215, 240)
        self.cell(0, 5, "%s  |  %s" % (_safe(pos), _safe(team)))

        # Trainer-Name (links unten im Header)
        if trainer_name:
            self.set_xy(15, 50)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(180, 200, 230)
            self.cell(0, 5, "Trainer: " + _safe(trainer_name))

        # Erstellt am
        self.set_xy(0, 50)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(180, 200, 230)
        self.cell(0, 5, "Erstellt am %s  " % date.today().strftime("%d.%m.%Y"), align="R")

        self.set_text_color(*self.DARK)
        self.set_y(68)

        # ── Spieler-Stammdaten ────────────────────────────────────────────────
        self.section_title("SPIELER-STAMMDATEN")
        neben = spieler.get("nebenposition") or ""
        pos_str = _safe(pos) + (" / " + _safe(neben) if neben else "")

        col_l_w = 95
        x0 = self.get_x()
        y0 = self.get_y()

        # Left column
        for key, val in [
            ("Name",            fullname),
            ("Geburtsdatum",    spieler.get("geburtsdatum") or "-"),
            ("Altersklasse",    spieler.get("altersklasse") or "-"),
            ("Spielbein",       spieler.get("spielbein") or "-"),
        ]:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*self.MID)
            self.cell(40, 6, _safe(key) + ":", new_x="RIGHT", new_y="TOP")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.DARK)
            self.cell(col_l_w - 40, 6, _safe(val), new_x="LMARGIN", new_y="NEXT")

        # Right column
        y_right = y0
        self.set_xy(x0 + col_l_w, y_right)
        for key, val in [
            ("Position",        pos_str),
            ("Mannschaft",      team),
            ("Leistungsniveau", spieler.get("leistungsniveau") or "-"),
            ("Trainingsstatus", spieler.get("trainingsstatus") or "-"),
        ]:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*self.MID)
            self.cell(38, 6, _safe(key) + ":", new_x="RIGHT", new_y="TOP")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.DARK)
            self.cell(57, 6, _safe(val)[:30], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x0 + col_l_w)

        self.set_x(x0)
        self.ln(6)

        # ── Athletik Score Banner ─────────────────────────────────────────────
        self.check_page_break(28)
        sc_col = GREEN if athletik_score >= 75 else YELLOW if athletik_score >= 50 else RED
        sx, sy = self.get_x(), self.get_y()
        self.set_fill_color(245, 247, 250)
        self.rect(sx, sy, 190, 22, "F")
        self.set_fill_color(*sc_col)
        self.rect(sx, sy, 5, 22, "F")
        self.set_xy(sx + 10, sy + 3)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.MID)
        self.cell(50, 5, "ATHLETIK-SCORE", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*sc_col)
        self.cell(40, 5, "%d / 100" % athletik_score)
        self.set_xy(sx + 110, sy + 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.MID)
        self.cell(0, 5, "ENTHALTENE TESTMODULE", new_x="LMARGIN", new_y="NEXT")
        self.set_x(sx + 110)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.DARK)
        self.multi_cell(85, 4, _safe(", ".join(module_vorhanden) or "-"))
        self.set_y(sy + 26)

        # ── Pflicht-Disclaimer ────────────────────────────────────────────────
        self.ln(4)
        self.disclaimer_box(_safe(KURZ_HINWEIS))
        self.add_page()

    def disclaimer_box(self, text: str, border_color=None):
        """Renders a highlighted notice box with optional coloured left border."""
        if border_color is None:
            border_color = (230, 126, 34)   # orange
        x, y = self.get_x(), self.get_y()
        # measure text height: ~4.5 mm per line at font size 7.5, 170 mm wide
        safe_text = _safe(text)
        # background
        self.set_fill_color(253, 246, 230)
        self.set_draw_color(*border_color)
        self.set_line_width(0.3)
        self.rect(x, y, 190, 8, "FD")
        # left accent bar
        self.set_fill_color(*border_color)
        self.rect(x, y, 3, 8, "F")
        # text
        self.set_xy(x + 5, y + 1)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80, 50, 10)
        self.cell(183, 6, safe_text[:155], new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)
        self.ln(2)

    def ampel_legend(self):
        """Renders a compact 3-column ampel explanation."""
        self.check_page_break(18)
        self.ln(2)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*self.MID)
        self.cell(0, 4, "AMPELFARBEN - ERKLAERUNG:", new_x="LMARGIN", new_y="NEXT")
        entries = [
            (GREEN,  "UNAUFFAELLIG",        _safe(AMPEL_GRUEN)[:85]),
            (YELLOW, "HANDLUNGSBEDARF",      _safe(AMPEL_GELB)[:85]),
            (RED,    "HANDLUNGSBEDARF HOCH", _safe(AMPEL_ROT)[:85]),
        ]
        for color, label, explain in entries:
            x, y = self.get_x(), self.get_y()
            self.set_fill_color(*color)
            self.rect(x, y + 1, 3, 5, "F")
            self.set_xy(x + 5, y)
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*self.DARK)
            self.cell(38, 6, label)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*self.MID)
            self.cell(0, 6, explain, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)
        self.ln(2)


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

def generate_report(
    spieler,
    fms_row=None,
    y_row=None,
    anthro_row=None,
    sprint_row=None,
    sprung_row=None,
    agil_row=None,
    aus_row=None,
    kraft_row=None,
    spiro_row=None,
    verletzungen=None,
    athletik_score: int = 0,
    risiko_label: str = "-",
    defizite: list = None,
    plan_rows: list = None,
    beobachtungen: list = None,
    vereinsname: str = "",
    saison: str = "",
    logo_bytes: bytes | None = None,
    trainer_name: str = "",
    farbe_primaer: str | None = None,
) -> bytes:
    """
    Vollstaendiger Athletik-Bericht fuer alle Testmodule.
    Alle Row-Parameter sind optional -- fehlende Module werden uebersprungen.
    """
    defizite     = defizite    or []
    plan_rows    = plan_rows   or []
    verletzungen = verletzungen or []

    # Vorhandene Module ermitteln (fuer Deckblatt)
    _module_map = [
        ("Anthropometrie", anthro_row), ("FMS", fms_row), ("Y-Balance", y_row),
        ("Sprint", sprint_row), ("Sprung", sprung_row), ("Agilitaet", agil_row),
        ("Ausdauer", aus_row), ("Kraft", kraft_row), ("Spiroergometrie", spiro_row),
    ]
    _module_vorhanden = [n for n, v in _module_map if v]

    pdf = AthletikReport()
    # Dynamische Vereinsfarbe (hex → RGB)
    if farbe_primaer:
        try:
            _h = farbe_primaer.lstrip("#")
            if len(_h) == 6:
                pdf.BRAND = (int(_h[0:2], 16), int(_h[2:4], 16), int(_h[4:6], 16))
        except Exception:
            pass
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ════════════════════════════════════════════════════════════════════════════
    # DECKBLATT (eigene Seite)
    # ════════════════════════════════════════════════════════════════════════════
    pdf.cover_page(
        spieler=spieler,
        vereinsname=vereinsname,
        saison=saison,
        athletik_score=athletik_score,
        module_vorhanden=_module_vorhanden,
        logo_bytes=logo_bytes,
        trainer_name=trainer_name,
    )

    # ── Athletik-Kennzahlen ──────────────────────────────────────────────────
    pdf.section_title("ATHLETIK-KENNZAHLEN")
    pdf.ln(2)

    a_col = GREEN if athletik_score >= 75 else YELLOW if athletik_score >= 50 else RED
    pdf.metric_box("Athletik Score", "%d/100" % athletik_score, a_col)

    rl    = _safe(risiko_label).upper()
    r_col = RED if "HANDLUNGSBEDARF HOCH" in rl else YELLOW if "HANDLUNGSBEDARF" in rl else GREEN
    pdf.metric_box("Athletik-Status", risiko_label, r_col)

    if fms_row:
        f_col = GREEN if fms_row["score"] >= 15 else YELLOW if fms_row["score"] >= 13 else RED
        pdf.metric_box("FMS Score", "%d/21" % fms_row["score"], f_col)

    if y_row:
        avg_y = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        y_col = GREEN if avg_y >= 89 else YELLOW if avg_y >= 85 else RED
        pdf.metric_box("Y-Balance Oe", "%.1f %%" % avg_y, y_col)

    if sprint_row and sprint_row.get("beste_10m"):
        pdf.metric_box("10 m Sprint", "%.2f s" % sprint_row["beste_10m"],
                       ampel(sprint_row.get("bewertung_10m", "")))

    if sprung_row and sprung_row.get("cmj_beid"):
        pdf.metric_box("CMJ", "%.1f cm" % sprung_row["cmj_beid"],
                       ampel(sprung_row.get("bewertung_cmj", "")))

    if aus_row and aus_row.get("distanz_m"):
        pdf.metric_box("Yo-Yo Distanz", "%d m" % int(aus_row["distanz_m"]),
                       ampel(aus_row.get("bewertung", "")))

    if anthro_row and anthro_row.get("bmi"):
        pdf.metric_box("BMI", "%.1f" % anthro_row["bmi"],
                       ampel(anthro_row.get("bmi_kategorie", "")))

    if kraft_row:
        rm1 = kraft_row.get("direktes_1rm") or kraft_row.get("geschaetztes_1rm")
        if rm1:
            rel = kraft_row.get("relative_kraft_direkt") or kraft_row.get("relative_kraft_geschaetzt")
            k_col = GREEN if (rel and rel >= 1.5) else YELLOW if (rel and rel >= 1.0) else GREY
            lbl_k = "Bankdr. 1RM" if kraft_row.get("direktes_1rm") else "Bankdr. 1RM (Epley)"
            pdf.metric_box(lbl_k, "%.1f kg" % rm1, k_col)

    pdf.ln(22)
    pdf.ampel_legend()

    # ════════════════════════════════════════════════════════════════════════════
    # ANTHROPOMETRIE
    # ════════════════════════════════════════════════════════════════════════════
    if anthro_row:
        pdf.check_page_break(40)
        pdf.section_title("ANTHROPOMETRIE")
        pdf.row2("Testdatum",   anthro_row.get("datum", "-"),
                 "Groesse",     "%s cm" % anthro_row.get("groesse", "-"))
        bmi_kat = anthro_row.get("bmi_kategorie", "-")
        pdf.row2("Gewicht",     "%s kg" % anthro_row.get("gewicht", "-"),
                 "BMI",         "%.1f (%s)" % (anthro_row.get("bmi", 0), bmi_kat),
                 color_r=ampel(bmi_kat))
        if anthro_row.get("koerperfett"):
            kf_meth = anthro_row.get("koerperfett_methode") or ""
            kf_label = "Koerperfett%s" % ((" (%s)" % kf_meth) if kf_meth else "")
            pdf.row2(kf_label, "%s %%" % anthro_row.get("koerperfett"),
                     "Muskelmasse", "%s kg" % anthro_row.get("muskelmasse", "-"))
        if anthro_row.get("reifestatus"):
            pdf.kv("Reifestatus (Schaetzung)", anthro_row.get("reifestatus", "-"))
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # FMS
    # ════════════════════════════════════════════════════════════════════════════
    if fms_row:
        pdf.check_page_break(75)
        pdf.section_title("FMS - FUNCTIONAL MOVEMENT SCREEN")
        f_col2 = GREEN if fms_row["score"] >= 15 else YELLOW if fms_row["score"] >= 13 else RED
        pdf.row2("Testdatum",   fms_row.get("datum", "-"),
                 "Gesamtscore", "%d/21  (%s)" % (fms_row["score"], fms_row.get("bewertung","-")),
                 color_r=f_col2)
        pdf.row2("Asymmetrien", fms_row.get("asymmetrie", "-"),
                 "Schwerpunkt", fms_row.get("schwerpunkt", "-"))
        pdf.ln(2)

        # ── FMS Einzelwerte-Tabelle (Links / Rechts / Score / Asymmetrie) ──────
        # Spaltenbreiten: Muster 62 | Links 22 | Rechts 22 | Score 24 | Bemerkung 60
        pdf.table_header([
            ("Bewegungsmuster", 62), ("Links", 22), ("Rechts", 22),
            ("Score /3", 24), ("Bemerkung", 60),
        ])

        # (name, l_val, r_val, bilat_val)
        # bilat_val gesetzt fuer beidseitige Pattern (kein L/R)
        fms_detail = [
            ("Deep Squat",       None, None,
             fms_row.get("deep_squat", 0)),
            ("Hurdle Step",
             fms_row.get("hurdle_links",  0), fms_row.get("hurdle_rechts",  0), None),
            ("Inline Lunge",
             fms_row.get("inline_links",  0), fms_row.get("inline_rechts",  0), None),
            ("Shoulder Mob.",
             fms_row.get("shoulder_links",0), fms_row.get("shoulder_rechts",0), None),
            ("ASLR",
             fms_row.get("aslr_links",    0), fms_row.get("aslr_rechts",    0), None),
            ("Trunk Stability",  None, None,
             fms_row.get("trunk", 0)),
            ("Rotary Stability",
             fms_row.get("rotary_links",  0), fms_row.get("rotary_rechts",  0), None),
        ]

        for i, (name, l_val, r_val, bilat_val) in enumerate(fms_detail):
            fill = (i % 2 == 0)
            pdf.set_fill_color(*(pdf.LIGHT if fill else pdf.WHITE))

            if bilat_val is not None:
                score   = int(bilat_val or 0)
                l_str   = "-"
                r_str   = "-"
                has_asym = False
                asym_str = ""
            else:
                l_v      = int(l_val or 0)
                r_v      = int(r_val or 0)
                score    = min(l_v, r_v)
                l_str    = str(l_v)
                r_str    = str(r_v)
                has_asym = (l_v != r_v)
                asym_str = "! Asymmetrie" if has_asym else ""

            score_col = GREEN if score == 3 else YELLOW if score == 2 else RED

            # Muster
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*pdf.DARK)
            pdf.cell(62, 5, _safe(name), fill=fill)
            # Links / Rechts
            pdf.cell(22, 5, l_str, fill=fill, align="C")
            pdf.cell(22, 5, r_str, fill=fill, align="C")
            # Score (farbig)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*score_col)
            pdf.cell(24, 5, "%d/3" % score, fill=fill, align="C")
            # Bemerkung
            if has_asym:
                pdf.set_text_color(*RED)
                pdf.set_font("Helvetica", "B", 7)
            else:
                pdf.set_text_color(*pdf.MID)
                pdf.set_font("Helvetica", "", 7)
            pdf.cell(60, 5, _safe(asym_str), fill=fill,
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*pdf.DARK)

        pdf.ln(2)
        pdf.disclaimer_box(_safe(FMS_HINWEIS), border_color=(80, 100, 160))
        pdf.ln(1)

    # ════════════════════════════════════════════════════════════════════════════
    # Y-BALANCE
    # ════════════════════════════════════════════════════════════════════════════
    if y_row:
        pdf.check_page_break(55)
        pdf.section_title("Y-BALANCE TEST")
        avg_y2 = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        y_col2 = GREEN if avg_y2 >= 89 else YELLOW if avg_y2 >= 85 else RED
        pdf.row2("Testdatum",   y_row.get("datum", "-"),
                 "Schwerpunkt", y_row.get("schwerpunkt", "-"))
        pdf.row2("Asymmetrie",  y_row.get("asymmetrie", "-"),
                 "Composite Oe", "%.1f %%" % avg_y2, color_r=y_col2)
        pdf.ln(2)

        # ── Y-Balance Richtungs-Tabelle (Ant / PM / PL) ──────────────────────
        # Spalten: Richtung 58 | Rechts 32 | Links 32 | Differenz 30 | Hinweis 38
        pdf.table_header([
            ("Richtung", 58), ("Rechts (cm)", 32), ("Links (cm)", 32),
            ("Differenz", 30), ("Hinweis", 38),
        ])

        yb_directions = [
            ("Anterior (Ant)",
             y_row.get("anterior_rechts",      0),
             y_row.get("anterior_links",        0),
             y_row.get("diff_anterior",         None)),
            ("Posteromedial (PM)",
             y_row.get("posteromedial_rechts",  0),
             y_row.get("posteromedial_links",   0),
             y_row.get("diff_posteromedial",    None)),
            ("Posterolateral (PL)",
             y_row.get("posterolateral_rechts", 0),
             y_row.get("posterolateral_links",  0),
             y_row.get("diff_posterolateral",   None)),
        ]

        for i, (name, r_val, l_val, diff) in enumerate(yb_directions):
            fill  = (i % 2 == 0)
            r_val = float(r_val or 0)
            l_val = float(l_val or 0)
            diff  = float(diff) if diff is not None else abs(r_val - l_val)
            has_asym = diff >= 4.0

            pdf.set_fill_color(*(pdf.LIGHT if fill else pdf.WHITE))
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*pdf.DARK)
            pdf.cell(58, 5, _safe(name), fill=fill)
            pdf.cell(32, 5, "%.1f" % r_val, fill=fill, align="C")
            pdf.cell(32, 5, "%.1f" % l_val, fill=fill, align="C")
            # Differenz farbig
            diff_col = RED if diff >= 4.0 else YELLOW if diff >= 2.0 else GREEN
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*diff_col)
            pdf.cell(30, 5, "%.1f cm" % diff, fill=fill, align="C")
            # Hinweis
            if has_asym:
                pdf.set_text_color(*RED)
                pdf.set_font("Helvetica", "B", 7)
                hint = "! Asymmetrie"
            else:
                pdf.set_text_color(*pdf.MID)
                pdf.set_font("Helvetica", "", 7)
                hint = ""
            pdf.cell(38, 5, _safe(hint), fill=fill, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*pdf.DARK)

        # ── Composite-Zeile (hervorgehoben) ───────────────────────────────────
        comp_r    = float(y_row.get("composite_rechts", 0))
        comp_l    = float(y_row.get("composite_links",  0))
        comp_diff = abs(comp_r - comp_l)
        pdf.set_fill_color(*pdf.BRAND)
        pdf.set_text_color(*pdf.WHITE)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(58, 5, "Composite Score (%)", fill=True)
        pdf.cell(32, 5, "%.1f %%" % comp_r, fill=True, align="C")
        pdf.cell(32, 5, "%.1f %%" % comp_l, fill=True, align="C")
        comp_diff_col = RED if comp_diff >= 4 else YELLOW if comp_diff >= 2 else GREEN
        pdf.set_text_color(*comp_diff_col)
        pdf.cell(30, 5, "%.1f %%" % comp_diff, fill=True, align="C")
        pdf.set_text_color(*pdf.WHITE)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(38, 5, "", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*pdf.DARK)

        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # SPRINT
    # ════════════════════════════════════════════════════════════════════════════
    if sprint_row:
        pdf.check_page_break(35)
        pdf.section_title("SPRINT-DIAGNOSTIK")
        beschl = sprint_row.get("beschl_index")
        pdf.row2("Testdatum",     sprint_row.get("datum", "-"),
                 "Beschl.-Index", "%.3f" % beschl if beschl else "-")
        b5  = sprint_row.get("beste_5m")
        b10 = sprint_row.get("beste_10m")
        b20 = sprint_row.get("beste_20m")
        b30 = sprint_row.get("beste_30m")
        if b5 or b10:
            pdf.row2("5 m (bester)",  "%.2f s" % b5  if b5  else "-",
                     "10 m (bester)", "%.2f s" % b10 if b10 else "-",
                     color_r=ampel(sprint_row.get("bewertung_10m","")))
        if b20 or b30:
            pdf.row2("20 m (bester)", "%.2f s" % b20 if b20 else "-",
                     "30 m (bester)", "%.2f s" % b30 if b30 else "-",
                     color_r=ampel(sprint_row.get("bewertung_30m","")))
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # SPRUNG
    # ════════════════════════════════════════════════════════════════════════════
    if sprung_row:
        pdf.check_page_break(40)
        pdf.section_title("SPRUNG-DIAGNOSTIK")
        cmj_b = sprung_row.get("cmj_beid")
        pdf.row2("Testdatum",      sprung_row.get("datum", "-"),
                 "CMJ beidbeinig", "%.1f cm" % cmj_b if cmj_b else "-",
                 color_r=ampel(sprung_row.get("bewertung_cmj","")))
        cmj_r = sprung_row.get("cmj_rechts")
        cmj_l = sprung_row.get("cmj_links")
        if cmj_r or cmj_l:
            pdf.row2("CMJ rechts", "%.1f cm" % cmj_r if cmj_r else "-",
                     "CMJ links",  "%.1f cm" % cmj_l if cmj_l else "-")
        asym = sprung_row.get("cmj_asymmetrie")
        if asym:
            pdf.kv_color("Asymmetrie R/L", "%.1f %%" % asym,
                         RED if asym > 10 else GREEN)
        squat = sprung_row.get("squat_jump")
        swj   = sprung_row.get("standweit")
        if squat or swj:
            pdf.row2("Squat Jump",       "%.1f cm" % squat if squat else "-",
                     "Standweitsprung",  "%.1f cm" % swj   if swj   else "-")
        rsi = sprung_row.get("rsi")
        if rsi:
            pdf.kv_color("RSI (Drop Jump)", "%.2f" % rsi,
                         GREEN if rsi >= 1.5 else YELLOW if rsi >= 1.0 else RED)
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # AGILITAET
    # ════════════════════════════════════════════════════════════════════════════
    if agil_row:
        pdf.check_page_break(40)
        pdf.section_title("AGILITAET & RICHTUNGSWECHSEL")
        pdf.row2("Testdatum", agil_row.get("datum", "-"))
        t505_r = agil_row.get("t505_r")
        t505_l = agil_row.get("t505_l")
        if t505_r or t505_l:
            pdf.row2("505-Test rechts", "%.2f s" % t505_r if t505_r else "-",
                     "505-Test links",  "%.2f s" % t505_l if t505_l else "-")
            asym505 = agil_row.get("asym_505")
            if asym505:
                pdf.kv_color("Asymmetrie 505", "%.1f %%" % asym505,
                             RED if asym505 > 10 else GREEN)
        t5105 = agil_row.get("t5_10_5")
        if t5105:
            pdf.row2("5-10-5 Shuttle", "%.2f s" % t5105)
        tt = agil_row.get("t_test")
        if tt:
            pdf.row2("T-Test",   "%.2f s" % tt,
                     "Bewertung T-Test", agil_row.get("bew_t_test","-"),
                     color_r=ampel(agil_row.get("bew_t_test","")))
        ill = agil_row.get("illinois")
        if ill:
            pdf.row2("Illinois Agility", "%.2f s" % ill,
                     "Bewertung",        agil_row.get("bew_illinois","-"),
                     color_r=ampel(agil_row.get("bew_illinois","")))
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # AUSDAUER
    # ════════════════════════════════════════════════════════════════════════════
    if aus_row:
        pdf.check_page_break(35)
        pdf.section_title("AUSDAUER - YO-YO TEST")
        pdf.row2("Testdatum",  aus_row.get("datum", "-"),
                 "Test-Level", aus_row.get("test_typ", "-"))
        pdf.row2("Distanz",    "%d m" % int(aus_row.get("distanz_m", 0)),
                 "Bewertung",  aus_row.get("bewertung","-"),
                 color_r=ampel(aus_row.get("bewertung","")))
        vo2 = aus_row.get("vo2max")
        if vo2:
            pdf.kv("VO2max (Schaetzung)", "%.1f ml/kg/min" % vo2)
        hf = aus_row.get("hf_max")
        rpe = aus_row.get("rpe")
        if hf or rpe:
            pdf.row2("HF max", "%d bpm" % int(hf) if hf else "-",
                     "RPE (Borg)", str(rpe) if rpe else "-")
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # SPIROERGOMETRIE / STUFENTEST
    # ════════════════════════════════════════════════════════════════════════════
    if spiro_row:
        pdf.check_page_break(55)
        pdf.section_title("SPIROERGOMETRIE / STUFENTEST")

        _testtyp_labels = {
            "spiro_laufband":  "Laufband (Spiro)",
            "spiro_fahrrad":   "Fahrradergometer (Spiro)",
            "laktat_laufband": "Laufband (Laktat)",
            "laktat_fahrrad":  "Fahrradergometer (Laktat)",
        }
        testtyp_label = _testtyp_labels.get(spiro_row.get("testtyp", ""), spiro_row.get("testtyp", "-"))
        protokoll     = spiro_row.get("protokoll_name") or "-"
        tester        = spiro_row.get("tester") or "-"

        pdf.row2("Testdatum", spiro_row.get("datum", "-"), "Testtyp", testtyp_label)
        pdf.row2("Protokoll", protokoll, "Tester", tester)

        # VO2-Werte
        vo2_peak = spiro_row.get("vo2_peak")
        vo2_max  = spiro_row.get("vo2_max")
        vo2_sch  = spiro_row.get("geschaetzte_vo2max")
        if vo2_peak:
            v_col = GREEN if vo2_peak >= 55 else YELLOW if vo2_peak >= 45 else RED
            pdf.kv_color("VO2peak", "%.1f ml/kg/min" % vo2_peak, v_col)
        if vo2_max:
            v_col2 = GREEN if vo2_max >= 55 else YELLOW if vo2_max >= 45 else RED
            pdf.kv_color("VO2max (gemessen)", "%.1f ml/kg/min" % vo2_max, v_col2)
        if vo2_sch and not vo2_peak and not vo2_max:
            pdf.kv("VO2max (Schaetzung)", "%.1f ml/kg/min" % vo2_sch)

        # Maximale Leistung
        v_max = spiro_row.get("maximale_geschwindigkeit")
        hf_max = spiro_row.get("maximale_herzfrequenz")
        if v_max or hf_max:
            pdf.row2(
                "V max", "%.1f km/h" % v_max if v_max else "-",
                "HF max", "%d bpm" % int(hf_max) if hf_max else "-",
            )

        # Schwellenwerte
        pdf.ln(1)
        vt1_v  = spiro_row.get("vt1_geschwindigkeit")
        vt1_hf = spiro_row.get("vt1_herzfrequenz")
        vt2_v  = spiro_row.get("vt2_geschwindigkeit")
        vt2_hf = spiro_row.get("vt2_herzfrequenz")
        sw_v   = spiro_row.get("schwelle_geschwindigkeit")
        sw_hf  = spiro_row.get("schwelle_herzfrequenz")
        sw_lak = spiro_row.get("schwelle_laktat")

        if vt1_v or vt1_hf:
            pdf.row2(
                "VT1 (aerobe Schwelle)", "%.1f km/h" % vt1_v if vt1_v else "-",
                "VT1 Herzfrequenz",     "%d bpm" % int(vt1_hf) if vt1_hf else "-",
            )
        if vt2_v or vt2_hf:
            pdf.row2(
                "VT2 (anaerobe Schwelle)", "%.1f km/h" % vt2_v if vt2_v else "-",
                "VT2 Herzfrequenz",       "%d bpm" % int(vt2_hf) if vt2_hf else "-",
            )
        if sw_v or sw_hf:
            methode = spiro_row.get("laktatschwelle_methode") or "Laktatschwelle"
            pdf.row2(
                _safe(methode)[:30], "%.1f km/h" % sw_v if sw_v else "-",
                "Schwellen-HF",      "%d bpm" % int(sw_hf) if sw_hf else "-",
            )
            if sw_lak:
                pdf.kv("Schwellen-Laktat", "%.2f mmol/l" % sw_lak)

        # Ruhelaktat / RPE
        rul = spiro_row.get("ruhelaktat")
        rpe = spiro_row.get("rpe_max")
        if rul or rpe:
            pdf.row2(
                "Ruhelaktat", "%.2f mmol/l" % rul if rul else "-",
                "RPE max",    str(rpe) if rpe else "-",
            )

        # Bemerkung
        bem = spiro_row.get("bemerkung")
        if bem:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*pdf.MID)
            pdf.multi_cell(0, 5, "Bemerkung: " + _safe(str(bem)[:200]))
            pdf.set_text_color(*pdf.DARK)
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # KRAFTDIAGNOSTIK
    # ════════════════════════════════════════════════════════════════════════════
    if kraft_row:
        pdf.check_page_break(55)
        pdf.section_title("KRAFTDIAGNOSTIK")
        meth = "Direkt" if kraft_row.get("direktes_1rm") else "Epley-Schaetzung"
        pdf.row2("Testdatum", kraft_row.get("datum", "-"), "Methode", meth)

        rm1_d = kraft_row.get("direktes_1rm")
        rm1_e = kraft_row.get("geschaetztes_1rm")
        rel_d = kraft_row.get("relative_kraft_direkt")
        rel_e = kraft_row.get("relative_kraft_geschaetzt")

        if rm1_d:
            col_rd = GREEN if (rel_d and rel_d >= 1.5) else YELLOW if (rel_d and rel_d >= 1.0) else RED
            pdf.row2("Bankdruecken 1RM (direkt)", "%.1f kg" % rm1_d,
                     "Relative Kraft", "%.2f xKGW" % rel_d if rel_d else "-",
                     color_r=col_rd)
        if rm1_e and not rm1_d:
            col_re = GREEN if (rel_e and rel_e >= 1.5) else YELLOW if (rel_e and rel_e >= 1.0) else RED
            pdf.row2("Bankdruecken 1RM (Epley-Schaetzung)", "%.1f kg" % rm1_e,
                     "Relative Kraft", "%.2f xKGW" % rel_e if rel_e else "-",
                     color_r=col_re)

        vent  = kraft_row.get("ventral_sekunden")
        lat_r = kraft_row.get("lateral_rechts_sekunden")
        lat_l = kraft_row.get("lateral_links_sekunden")
        dors  = kraft_row.get("dorsal_sekunden")
        rumpf = kraft_row.get("rumpf_gesamt_sekunden")
        lat_asym = kraft_row.get("lateral_asymmetrie_prozent")

        if any([vent, lat_r, lat_l, dors, rumpf]):
            pdf.ln(1)
            if vent:
                pdf.row2("Ventral (Plank)", "%.0f s" % vent)
            if lat_r or lat_l:
                pdf.row2("Lateral rechts", "%.0f s" % lat_r if lat_r else "-",
                         "Lateral links",  "%.0f s" % lat_l if lat_l else "-")
            if dors:
                pdf.row2("Dorsal", "%.0f s" % dors)
            if rumpf:
                pdf.kv("Rumpf-Gesamtzeit", "%.0f s" % rumpf)
            if lat_asym:
                col_la = RED if lat_asym > 15 else YELLOW if lat_asym > 10 else GREEN
                pdf.kv_color("Laterale Asymmetrie", "%.1f %%" % lat_asym, col_la)
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # VERLETZUNGSHISTORIE
    # ════════════════════════════════════════════════════════════════════════════
    if verletzungen:
        pdf.check_page_break(20 + len(verletzungen) * 6)
        pdf.section_title("VERLETZUNGSHISTORIE")
        gesamt_ausfall = sum(v.get("ausfall_tage") or 0 for v in verletzungen)
        pdf.kv("Eintraege gesamt",   str(len(verletzungen)))
        pdf.kv("Ausfalltage gesamt", str(gesamt_ausfall))
        pdf.ln(1)
        cols = [("Datum",28),("Koerperteil",35),("Art",38),("Schwere",40),("Ausfall",18),("Notiz",31)]
        pdf.table_header(cols)
        widths = [c[1] for c in cols]
        fill = False
        for v in verletzungen:
            schwere = v.get("schwere","")
            vals = [
                v.get("datum","-"),
                v.get("koerperteil","-"),
                v.get("art","-"),
                schwere,
                "%d d" % (v.get("ausfall_tage",0) or 0),
                (v.get("notizen","") or "")[:30],
            ]
            pdf.table_row(vals, widths, fill)
            fill = not fill
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # TRAINERBEOBACHTUNGEN
    # ════════════════════════════════════════════════════════════════════════════
    if beobachtungen:
        beob_mit_inhalt = [
            b for b in beobachtungen
            if b.get("text_generiert") or b.get("freitext")
        ]
        if beob_mit_inhalt:
            pdf.check_page_break(25 + min(len(beob_mit_inhalt), 10) * 12)
            pdf.section_title("TRAINERBEOBACHTUNGEN")
            pdf.disclaimer_box(_safe(
                "Diese Eintraege wurden vom Trainer waehrend der Diagnostik erfasst. "
                "Beobachtungen dienen der Trainingssteuerung — sportliche Auswertung, kein Ersatz für ärztlichen Rat."
            ), border_color=(80, 100, 100))
            _test_lbl = {
                "fms": "FMS", "y_balance": "Y-Balance", "sprint": "Sprint",
                "sprung": "Sprung", "agilitaet": "Agilitaet", "ausdauer": "Ausdauer",
                "anthropometrie": "Anthropometrie", "kraft": "Kraftdiagnostik",
            }
            for b in beob_mit_inhalt[:12]:
                lbl = _test_lbl.get(b.get("test_id", ""), b.get("test_id", "-"))
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*pdf.MID)
                pdf.cell(0, 5, _safe("%s — %s:" % (lbl, b.get("datum", "-"))),
                         new_x="LMARGIN", new_y="NEXT")
                if b.get("text_generiert"):
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(*pdf.DARK)
                    pdf.multi_cell(0, 5, "  " + _safe(str(b["text_generiert"])[:220]))
                if b.get("freitext"):
                    pdf.set_font("Helvetica", "I", 7.5)
                    pdf.set_text_color(*pdf.MID)
                    pdf.cell(0, 5, "  Notiz: " + _safe(str(b["freitext"])[:160]),
                             new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*pdf.DARK)
                pdf.ln(1)
            pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # DEFIZITE & TRAININGSEMPFEHLUNGEN
    # ════════════════════════════════════════════════════════════════════════════
    if defizite:
        pdf.check_page_break(15 + len(defizite) * 7)
        pdf.section_title("ERKANNTE DEFIZITE")
        for d in defizite:
            is_krit = d.get("level") == "kritisch"
            col = RED if is_krit else YELLOW
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*col)
            pdf.cell(5,  6, "!" if is_krit else "o")
            pdf.cell(52, 6, _safe(str(d.get("bereich",""))[:30]) + ":")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*pdf.DARK)
            pdf.cell(0, 6, _safe(str(d.get("text",""))[:80]),
                     new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*pdf.DARK)
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # TRAININGSPLAN
    # ════════════════════════════════════════════════════════════════════════════
    if plan_rows:
        pdf.add_page()
        pdf.section_title("PERIODISIERUNGSPLAN (VOLLSTAENDIG)")
        pdf.disclaimer_box(_safe(TRAININGSPLAN_HINWEIS), border_color=(80, 100, 160))
        pdf.ln(1)
        cols = [("Wo.",10),("Phase",38),("Bereich",28),("Uebung",68),("Volumen",26),("Hz.",20)]
        pdf.table_header(cols)
        widths = [c[1] for c in cols]
        fill = False
        plan_display = sorted(plan_rows, key=lambda r: (int(r.get("woche") or 0), str(r.get("uebung") or "")))
        for row in plan_display:
            # Phase-Text kuerzen (Klammer-Zusatz entfernen fuer Platz)
            raw_phase = row.get("phase", row[1] if isinstance(row, (list, tuple)) else "-")
            phase_short = str(raw_phase).split("(")[0].strip()[:22]
            vals = [
                str(row.get("woche", row[0] if isinstance(row, (list, tuple)) else "-")),
                phase_short,
                row.get("bereich",    row[3] if isinstance(row, (list, tuple)) else "-"),
                row.get("uebung",     row[4] if isinstance(row, (list, tuple)) else "-"),
                row.get("volumen",    row[6] if isinstance(row, (list, tuple)) else "-"),
                row.get("haeufigkeit",row[7] if isinstance(row, (list, tuple)) else "-"),
            ]
            pdf.table_row(vals, widths, fill)
            fill = not fill

    # ════════════════════════════════════════════════════════════════════════════
    # ZUSAMMENFASSUNG & EMPFEHLUNGEN
    # ════════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("ZUSAMMENFASSUNG")

    # Modul-Uebersicht als Tabelle
    _modul_status = [
        ("Anthropometrie",  anthro_row,  lambda r: "%s kg / %.0f cm — BMI %.1f" % (r.get("gewicht","-"), r.get("groesse",0), r.get("bmi",0)) if r.get("groesse") else "-",
         lambda r: ampel(r.get("bmi_kategorie",""))),
        ("FMS",             fms_row,     lambda r: "Score %d/21" % r.get("score",0),
         lambda r: GREEN if r.get("score",0) >= 15 else YELLOW if r.get("score",0) >= 13 else RED),
        ("Y-Balance",       y_row,       lambda r: "Rechts %.1f%% / Links %.1f%%" % (r.get("composite_rechts",0), r.get("composite_links",0)),
         lambda r: GREEN if (r.get("composite_rechts",0)+r.get("composite_links",0))/2 >= 89 else YELLOW),
        ("Sprint",          sprint_row,  lambda r: "10m: %.2f s / 30m: %.2f s" % (r.get("beste_10m") or 0, r.get("beste_30m") or 0),
         lambda r: ampel(r.get("bewertung_10m",""))),
        ("Sprung",          sprung_row,  lambda r: "CMJ: %.1f cm" % r.get("cmj_beid",0) if r.get("cmj_beid") else "-",
         lambda r: ampel(r.get("bewertung_cmj",""))),
        ("Agilitaet",       agil_row,    lambda r: "T-Test: %.2f s" % r.get("t_test",0) if r.get("t_test") else ("505-Test: %.2f s" % r.get("t505_r",0) if r.get("t505_r") else "-"),
         lambda r: ampel(r.get("bew_t_test","") or r.get("bew_505",""))),
        ("Ausdauer",        aus_row,     lambda r: "Distanz: %d m / VO2max: %.1f" % (int(r.get("distanz_m",0)), r.get("vo2max") or 0),
         lambda r: ampel(r.get("bewertung",""))),
        ("Spiroergometrie", spiro_row,   lambda r: "VO2peak: %.1f ml/kg/min" % r.get("vo2_peak",0) if r.get("vo2_peak") else ("V max: %.1f km/h" % r.get("maximale_geschwindigkeit",0) if r.get("maximale_geschwindigkeit") else "-"),
         lambda r: GREEN if (r.get("vo2_peak") or 0) >= 55 else YELLOW if (r.get("vo2_peak") or 0) >= 45 else (GREY if not r.get("vo2_peak") else RED)),
        ("Kraftdiagnostik", kraft_row,   lambda r: "1RM: %.1f kg" % (r.get("direktes_1rm") or r.get("geschaetztes_1rm") or 0),
         lambda r: GREEN if (r.get("relative_kraft_direkt") or r.get("relative_kraft_geschaetzt") or 0) >= 1.5 else YELLOW),
    ]

    cols_sum = [("Modul",45),("Ergebnis (aktuell)",105),("Bewertung",40)]
    pdf.table_header(cols_sum)
    _wsum = [c[1] for c in cols_sum]
    fill = False
    for modul_name, row, val_fn, col_fn in _modul_status:
        if not row:
            continue
        try:
            val_str = val_fn(row)
            col     = col_fn(row)
        except Exception:
            val_str, col = "-", GREY
        pdf.set_fill_color(*pdf.LIGHT) if fill else pdf.set_fill_color(*pdf.WHITE)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*pdf.DARK)
        pdf.cell(_wsum[0], 5, _safe(modul_name), fill=True)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(_wsum[1], 5, _safe(val_str)[:55], fill=True)
        # Ampel-Klotz
        x_amp, y_amp = pdf.get_x(), pdf.get_y()
        pdf.set_fill_color(*col)
        pdf.rect(x_amp, y_amp + 0.5, 5, 4, "F")
        pdf.set_fill_color(*pdf.LIGHT) if fill else pdf.set_fill_color(*pdf.WHITE)
        pdf.cell(_wsum[2], 5, "", fill=True, new_x="LMARGIN", new_y="NEXT")
        fill = not fill

    # ── Defizite hervorheben ──────────────────────────────────────────────────
    if defizite:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*pdf.BRAND)
        pdf.cell(0, 6, "VORRANGIGE TRAININGSMASSNAHMEN:", new_x="LMARGIN", new_y="NEXT")
        for i, d in enumerate(defizite[:5], 1):
            is_krit = d.get("level") == "kritisch"
            c_txt   = RED if is_krit else YELLOW
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*c_txt)
            pdf.cell(8, 5, "%d." % i)
            pdf.cell(55, 5, _safe(str(d.get("bereich",""))[:28]) + ":")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*pdf.DARK)
            pdf.cell(0, 5, _safe(str(d.get("text",""))[:90]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*pdf.DARK)

    # ── Gesamtempfehlung ──────────────────────────────────────────────────────
    pdf.ln(3)
    pdf.section_title("EMPFEHLUNGEN")
    if athletik_score >= 75:
        empf = ("Sehr gutes Athletik-Profil. Gezielte Optimierung der verbleibenden Defizite empfohlen. "
                "Fokus auf Erhalt der Staerken und spezifische Leistungssteigerung in Schluesselbereichen.")
        empf_col = GREEN
    elif athletik_score >= 50:
        empf = ("Solides Athletik-Profil mit klaren Entwicklungsfeldern. Gezieltes Athletiktraining "
                "entlang der identifizierten Defizite empfohlen. Prioritaet auf Stabilitaet und "
                "Verletzungspraevention. Trainingsplan basiert auf individueller Befundanalyse.")
        empf_col = YELLOW
    else:
        empf = ("Deutlicher Handlungsbedarf festgestellt. Systematisches Athletiktraining mit hoher "
                "Prioritaet auf Verletzungspraevention und Bewegungsqualitaet empfohlen. "
                "Engmaschige Begleitung durch Atletiktrainer notwendig.")
        empf_col = RED

    x_e, y_e = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(*empf_col)
    pdf.set_line_width(0.5)
    pdf.rect(x_e, y_e, 190, 20, "FD")
    pdf.set_fill_color(*empf_col)
    pdf.rect(x_e, y_e, 5, 20, "F")
    pdf.set_xy(x_e + 8, y_e + 3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(182, 5, "Athletik-Score: %d/100" % athletik_score, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x_e + 8)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.multi_cell(182, 4, _safe(empf))
    pdf.set_y(y_e + 24)

    pdf.ln(3)
    pdf.disclaimer_box(_safe(ZWECKBESTIMMUNG_TEXT))

    return bytes(pdf.output())


# ─── Vergleichs-Report ────────────────────────────────────────────────────────

class _VergleichReport(AthletikReport):
    """PDF-Report für zwei Spieler im direkten Vergleich."""

    BLUE_A  = (31, 111, 235)   # Spieler A accent (matches UI #1f6feb)
    GREEN_B = (63, 185, 80)    # Spieler B accent (matches UI #3fb950)

    def __init__(self, name1: str, name2: str):
        super().__init__()
        self._n1 = _safe(name1)[:32]
        self._n2 = _safe(name2)[:32]

    def header(self):
        self.set_fill_color(*self.BRAND)
        self.rect(0, 0, 210, 18, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.WHITE)
        self.cell(0, 10, "  ATHLETIK-VERGLEICH", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_xy(0, 6)
        self.cell(0, 8, "Erstellt am %s  " % date.today().strftime("%d.%m.%Y"), align="R")
        self.set_text_color(*self.DARK)
        self.ln(14)

    def player_banner(self, sp1: dict, sp2: dict, sc1: int, sc2: int):
        """Zwei Spieler-Info-Karten nebeneinander."""
        def _info(sp, sc, accent):
            name   = _safe(sp.get("name") or sp.get("nachname") or "-")
            pos    = _safe(sp.get("hauptposition") or sp.get("position") or "-")
            team   = _safe(sp.get("mannschaft") or "-")
            status = _safe(sp.get("trainingsstatus") or "Volltraining")
            geb    = _safe(sp.get("geburtsdatum") or "-")
            col    = GREEN if sc >= 75 else YELLOW if sc >= 50 else RED
            return name, pos, team, status, geb, sc, col, accent

        x_start = self.get_x()
        y_start = self.get_y()
        W = 93   # card width

        for i, (sp, sc) in enumerate([(sp1, sc1), (sp2, sc2)]):
            name, pos, team, status, geb, score, sc_col, accent = _info(
                sp, sc,
                self.BLUE_A if i == 0 else self.GREEN_B,
            )
            x = x_start + i * (W + 4)
            # Card background
            self.set_fill_color(245, 247, 250)
            self.rect(x, y_start, W, 38, "F")
            # Accent bar at top
            self.set_fill_color(*accent)
            self.rect(x, y_start, W, 3, "F")
            # Player label
            self.set_xy(x + 3, y_start + 4)
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(*accent)
            self.cell(W - 6, 4, "SPIELER %s" % ("A" if i == 0 else "B"),
                      new_x="LMARGIN", new_y="NEXT")
            # Name
            self.set_x(x + 3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*self.DARK)
            self.cell(W - 6, 6, name[:26], new_x="LMARGIN", new_y="NEXT")
            # Info rows
            for label, val in [("Position", pos), ("Mannschaft", team), ("Status", status)]:
                self.set_x(x + 3)
                self.set_font("Helvetica", "B", 7)
                self.set_text_color(*self.MID)
                self.cell(28, 4, label + ":", new_x="RIGHT", new_y="TOP")
                self.set_font("Helvetica", "", 7)
                self.set_text_color(*self.DARK)
                self.cell(60, 4, val[:24], new_x="LMARGIN", new_y="NEXT")
            # Score
            self.set_x(x + 3)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*sc_col)
            self.cell(W - 6, 5, "Athletik-Score: %d/100" % score,
                      new_x="LMARGIN", new_y="NEXT")

        self.set_xy(x_start, y_start + 42)

    def compare_section(self, title: str):
        self.check_page_break(40)
        self.ln(3)
        self.set_fill_color(*self.BRAND)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, "  " + _safe(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)
        # Sub-header with player names
        self.set_fill_color(220, 228, 245)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*self.MID)
        self.cell(65, 5, "  KENNZAHL", fill=True)
        self.set_fill_color(220, 235, 255)
        self.set_text_color(*self.BLUE_A)
        self.cell(62, 5, "  A: " + self._n1[:24], fill=True)
        self.set_fill_color(220, 245, 225)
        self.set_text_color(*self.GREEN_B)
        self.cell(62, 5, "  B: " + self._n2[:24], fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)
        self._fill_toggle = False

    def compare_row(self, label: str, val1, val2="—", col1=None, col2=None):
        fill = getattr(self, "_fill_toggle", False)
        self._fill_toggle = not fill
        self.set_fill_color(*self.LIGHT) if fill else self.set_fill_color(*self.WHITE)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.MID)
        self.cell(65, 5, "  " + _safe(label)[:30], fill=True)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*(col1 or self.DARK))
        self.cell(62, 5, "  " + _safe(val1)[:28], fill=True)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*(col2 or self.DARK))
        self.cell(62, 5, "  " + _safe(val2)[:28], fill=True,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.DARK)


def generate_vergleich_pdf(
    sp1: dict, sp2: dict,
    sc1: int = 0, sc2: int = 0,
    fms1=None,   fms2=None,
    y1=None,     y2=None,
    spr1=None,   spr2=None,
    spg1=None,   spg2=None,
    agil1=None,  agil2=None,
    aus1=None,   aus2=None,
    kraft1=None, kraft2=None,
) -> bytes:
    """Vergleichs-PDF für zwei Spieler — Score-Banner + Testwerte-Tabelle."""

    pdf = _VergleichReport(
        name1=sp1.get("name") or sp1.get("nachname") or "Spieler A",
        name2=sp2.get("name") or sp2.get("nachname") or "Spieler B",
    )
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Player banners + scores ───────────────────────────────────────────────
    pdf.section_title("SPIELER-VERGLEICH")
    pdf.ln(2)
    pdf.player_banner(sp1, sp2, sc1, sc2)
    pdf.ln(2)
    pdf.disclaimer_box(_safe(KURZ_HINWEIS))

    # ── FMS ───────────────────────────────────────────────────────────────────
    if fms1 or fms2:
        pdf.compare_section("FMS - FUNCTIONAL MOVEMENT SCREEN")
        def _fms_score_str(r):
            if not r: return "—"
            return "%d/21 (%s)" % (r["score"], r.get("bewertung", "-"))
        def _fms_col(r):
            if not r: return GREY
            return GREEN if r["score"] >= 15 else YELLOW if r["score"] >= 13 else RED
        pdf.compare_row("Gesamtscore", _fms_score_str(fms1), _fms_score_str(fms2),
                        _fms_col(fms1), _fms_col(fms2))
        for attr, label in [
            ("asymmetrie", "Asymmetrie"),
            ("schwerpunkt", "Schwerpunkt"),
            ("datum",       "Testdatum"),
        ]:
            pdf.compare_row(label,
                            (fms1 or {}).get(attr, "—"),
                            (fms2 or {}).get(attr, "—"))

    # ── Y-Balance ─────────────────────────────────────────────────────────────
    if y1 or y2:
        pdf.compare_section("Y-BALANCE TEST")
        def _yavg(r):
            if not r: return None
            return (r["composite_rechts"] + r["composite_links"]) / 2
        def _ycol(r):
            a = _yavg(r)
            if a is None: return GREY
            return GREEN if a >= 89 else YELLOW if a >= 85 else RED
        a1, a2 = _yavg(y1), _yavg(y2)
        pdf.compare_row("Ø Composite",
                        "%.1f %%" % a1 if a1 else "—",
                        "%.1f %%" % a2 if a2 else "—",
                        _ycol(y1), _ycol(y2))
        pdf.compare_row("Composite Rechts",
                        "%.1f %%" % (y1 or {}).get("composite_rechts", 0) if y1 else "—",
                        "%.1f %%" % (y2 or {}).get("composite_rechts", 0) if y2 else "—")
        pdf.compare_row("Composite Links",
                        "%.1f %%" % (y1 or {}).get("composite_links", 0) if y1 else "—",
                        "%.1f %%" % (y2 or {}).get("composite_links", 0) if y2 else "—")
        pdf.compare_row("Asymmetrie",
                        (y1 or {}).get("asymmetrie", "—"),
                        (y2 or {}).get("asymmetrie", "—"))
        pdf.compare_row("Testdatum",
                        (y1 or {}).get("datum", "—"),
                        (y2 or {}).get("datum", "—"))

    # ── Sprint ────────────────────────────────────────────────────────────────
    if spr1 or spr2:
        pdf.compare_section("SPRINT-DIAGNOSTIK")
        def _t(r, field):
            v = (r or {}).get(field)
            return "%.2f s" % v if v else "—"
        def _scol(r, bew_field):
            return ampel((r or {}).get(bew_field, ""))
        pdf.compare_row("10 m (bester)",
                        _t(spr1, "beste_10m"), _t(spr2, "beste_10m"),
                        _scol(spr1, "bewertung_10m"), _scol(spr2, "bewertung_10m"))
        pdf.compare_row("30 m (bester)",
                        _t(spr1, "beste_30m"), _t(spr2, "beste_30m"),
                        _scol(spr1, "bewertung_30m"), _scol(spr2, "bewertung_30m"))
        pdf.compare_row("5 m (bester)",  _t(spr1, "beste_5m"),  _t(spr2, "beste_5m"))
        pdf.compare_row("20 m (bester)", _t(spr1, "beste_20m"), _t(spr2, "beste_20m"))
        pdf.compare_row("Testdatum",
                        (spr1 or {}).get("datum", "—"),
                        (spr2 or {}).get("datum", "—"))

    # ── Sprung ────────────────────────────────────────────────────────────────
    if spg1 or spg2:
        pdf.compare_section("SPRUNG-DIAGNOSTIK")
        def _cm(r, f):
            v = (r or {}).get(f)
            return "%.1f cm" % v if v else "—"
        def _cmj_col(r):
            return ampel((r or {}).get("bewertung_cmj", ""))
        pdf.compare_row("CMJ beidbeinig",
                        _cm(spg1, "cmj_beid"), _cm(spg2, "cmj_beid"),
                        _cmj_col(spg1), _cmj_col(spg2))
        pdf.compare_row("CMJ rechts",  _cm(spg1, "cmj_rechts"),  _cm(spg2, "cmj_rechts"))
        pdf.compare_row("CMJ links",   _cm(spg1, "cmj_links"),   _cm(spg2, "cmj_links"))
        def _asym_col(r):
            a = (r or {}).get("cmj_asymmetrie")
            return RED if (a and float(a) > 10) else GREEN if a else GREY
        def _asym_str(r):
            a = (r or {}).get("cmj_asymmetrie")
            return "%.1f %%" % a if a else "—"
        pdf.compare_row("Asymmetrie L/R",
                        _asym_str(spg1), _asym_str(spg2),
                        _asym_col(spg1), _asym_col(spg2))
        pdf.compare_row("Squat Jump",       _cm(spg1, "squat_jump"), _cm(spg2, "squat_jump"))
        pdf.compare_row("Standweitsprung",  _cm(spg1, "standweit"),  _cm(spg2, "standweit"))
        def _rsi(r):
            v = (r or {}).get("rsi")
            return "%.2f" % v if v else "—"
        def _rsi_col(r):
            v = (r or {}).get("rsi")
            return (GREEN if v >= 1.5 else YELLOW if v >= 1.0 else RED) if v else GREY
        pdf.compare_row("RSI", _rsi(spg1), _rsi(spg2), _rsi_col(spg1), _rsi_col(spg2))
        pdf.compare_row("Testdatum",
                        (spg1 or {}).get("datum", "—"),
                        (spg2 or {}).get("datum", "—"))

    # ── Agilität ──────────────────────────────────────────────────────────────
    if agil1 or agil2:
        pdf.compare_section("AGILITAET & RICHTUNGSWECHSEL")
        def _s(r, f):
            v = (r or {}).get(f)
            return "%.2f s" % v if v else "—"
        def _505col(r):
            return ampel((r or {}).get("bew_505", ""))
        def _ttest_col(r):
            return ampel((r or {}).get("bew_t_test", ""))
        pdf.compare_row("505-Test rechts",  _s(agil1, "t505_r"),   _s(agil2, "t505_r"))
        pdf.compare_row("505-Test links",   _s(agil1, "t505_l"),   _s(agil2, "t505_l"))
        def _asym505(r):
            a = (r or {}).get("asym_505")
            return "%.1f %%" % a if a else "—"
        def _asym505col(r):
            a = (r or {}).get("asym_505")
            return (RED if float(a) > 10 else GREEN) if a else GREY
        pdf.compare_row("Asymmetrie 505",
                        _asym505(agil1), _asym505(agil2),
                        _asym505col(agil1), _asym505col(agil2))
        pdf.compare_row("T-Test",
                        _s(agil1, "t_test"), _s(agil2, "t_test"),
                        _ttest_col(agil1), _ttest_col(agil2))
        pdf.compare_row("5-10-5 Shuttle",  _s(agil1, "t5_10_5"),  _s(agil2, "t5_10_5"))
        pdf.compare_row("Illinois Agility",_s(agil1, "illinois"),  _s(agil2, "illinois"))
        pdf.compare_row("Testdatum",
                        (agil1 or {}).get("datum", "—"),
                        (agil2 or {}).get("datum", "—"))

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    if aus1 or aus2:
        pdf.compare_section("AUSDAUER - YO-YO TEST")
        def _dist(r):
            v = (r or {}).get("distanz_m")
            return "%d m" % int(v) if v else "—"
        def _dist_col(r):
            return ampel((r or {}).get("bewertung", ""))
        def _vo2(r):
            v = (r or {}).get("vo2max")
            return "%.1f ml/kg/min" % v if v else "—"
        pdf.compare_row("Erzielte Distanz",
                        _dist(aus1), _dist(aus2),
                        _dist_col(aus1), _dist_col(aus2))
        pdf.compare_row("VO2max (Schaetzung)", _vo2(aus1), _vo2(aus2))
        pdf.compare_row("Bewertung",
                        (aus1 or {}).get("bewertung", "—"),
                        (aus2 or {}).get("bewertung", "—"))
        pdf.compare_row("Testdatum",
                        (aus1 or {}).get("datum", "—"),
                        (aus2 or {}).get("datum", "—"))

    # ── Kraftdiagnostik ───────────────────────────────────────────────────────
    if kraft1 or kraft2:
        pdf.compare_section("KRAFTDIAGNOSTIK")
        def _rm1(r):
            if not r: return "—"
            v = r.get("direktes_1rm") or r.get("geschaetztes_1rm")
            return "%.1f kg" % v if v else "—"
        def _rm1_col(r):
            if not r: return GREY
            rel = r.get("relative_kraft_direkt") or r.get("relative_kraft_geschaetzt")
            return (GREEN if rel >= 1.5 else YELLOW if rel >= 1.0 else RED) if rel else GREY
        def _rel(r):
            if not r: return "—"
            rel = r.get("relative_kraft_direkt") or r.get("relative_kraft_geschaetzt")
            return "%.2f xKGW" % rel if rel else "—"
        pdf.compare_row("Bankdr. 1RM (direkt/Epley)",
                        _rm1(kraft1), _rm1(kraft2),
                        _rm1_col(kraft1), _rm1_col(kraft2))
        pdf.compare_row("Relative Kraft", _rel(kraft1), _rel(kraft2))
        def _s_k(r, f):
            v = (r or {}).get(f)
            return "%.0f s" % v if v else "—"
        pdf.compare_row("Ventral (Plank)", _s_k(kraft1,"ventral_sekunden"), _s_k(kraft2,"ventral_sekunden"))
        pdf.compare_row("Lateral rechts",  _s_k(kraft1,"lateral_rechts_sekunden"), _s_k(kraft2,"lateral_rechts_sekunden"))
        pdf.compare_row("Lateral links",   _s_k(kraft1,"lateral_links_sekunden"),  _s_k(kraft2,"lateral_links_sekunden"))
        pdf.compare_row("Dorsal",          _s_k(kraft1,"dorsal_sekunden"),          _s_k(kraft2,"dorsal_sekunden"))
        def _asym_k(r):
            a = (r or {}).get("lateral_asymmetrie_prozent")
            return "%.1f %%" % a if a else "—"
        def _asym_k_col(r):
            a = (r or {}).get("lateral_asymmetrie_prozent")
            return (RED if a > 15 else YELLOW if a > 10 else GREEN) if a else GREY
        pdf.compare_row("Lat. Asymmetrie", _asym_k(kraft1), _asym_k(kraft2),
                        _asym_k_col(kraft1), _asym_k_col(kraft2))
        pdf.compare_row("Testdatum",
                        (kraft1 or {}).get("datum", "—"),
                        (kraft2 or {}).get("datum", "—"))

    pdf.ln(4)
    pdf.ampel_legend()

    return bytes(pdf.output())


# ─── Trainingsplan-PDF (Standalone) ──────────────────────────────────────────

_WARMUP_ROWS = [
    ("Aktivierungslauf",          "5 min",       "Leichtes Joggen, Seitwarts-, Ruckwartslaufe"),
    ("Huftkreisen beidbeinig",    "2x10",        "Kontrolliert, langsam"),
    ("World's Greatest Stretch",  "2x5/Seite",   "Tief und kontrolliert"),
    ("Leg Swings vor/ruck",       "2x10/Seite",  "Freies Pendeln, zunehmende Amplitude"),
    ("Leg Swings seitlich",       "2x10/Seite",  "Lateral, gestreckt"),
    ("Glute Bridge",              "2x10",        "Langsam, Becken oben halten 2 s"),
    ("Mini-Band Walk",            "2x10 m",      "Lateral, Knie leicht gebeugt"),
]

_TAG_NAMEN = {1: "Tag 1 - Montag", 2: "Tag 2 - Mittwoch", 3: "Tag 3 - Freitag",
              4: "Tag 4 - Samstag", 0: "Alle Tage"}

_QUELLEN = (
    "Quellen: Faigenbaum & Myer (2010) Youth Resistance Training — Pediatric Exercise Science; "
    "Lloyd et al. (2014) Position Statement on Youth Resistance Training — BJSM; "
    "NSCA Youth Resistance Training Position Statement (2009)."
)


def generate_trainingsplan_pdf(
    spieler: dict,
    plan_rows: list,
    plangruppe: str,
    plangruppen_config: dict,
    alters_ersatz: dict | None = None,
    vereinsname: str = "",
) -> bytes:
    """
    Druckbarer Trainingsplan-PDF fuer einen Spieler.
    Zeigt Altersgruppe, vollstaendigen Wochenplan, Warm-Up, Substitutionshinweise
    und wissenschaftliche Quellen. Gleicher Stil wie AthletikReport.
    """
    alters_ersatz = alters_ersatz or {}

    pdf = AthletikReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Kopf ─────────────────────────────────────────────────────────────────
    vorname  = spieler.get("vorname") or ""
    nachname = spieler.get("nachname") or spieler.get("name") or "-"
    fullname = ("%s %s" % (vorname, nachname)).strip()
    team     = spieler.get("mannschaft") or "-"
    pos      = spieler.get("hauptposition") or spieler.get("position") or "-"
    geb      = spieler.get("geburtsdatum") or "-"

    # Blauer Cover-Block (kompakter als Vollbericht)
    pdf.set_fill_color(*pdf.BRAND)
    pdf.rect(0, 0, 210, 48, "F")

    pdf.set_xy(15, 8)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*pdf.WHITE)
    pdf.cell(0, 6, _safe(vereinsname or "FOOTBALL ATHLETIK"))

    pdf.set_xy(15, 15)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(180, 11, _safe(fullname)[:36])

    pdf.set_xy(15, 28)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(200, 215, 240)
    pdf.cell(0, 5, "%s  |  %s  |  Geb.: %s" % (_safe(pos), _safe(team), _safe(geb)))

    pdf.set_xy(0, 38)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(180, 200, 230)
    pdf.cell(0, 5, "Erstellt am %s  " % date.today().strftime("%d.%m.%Y"), align="R")

    pdf.set_text_color(*pdf.DARK)
    pdf.set_y(55)

    # ── Trainingsplan-Titel ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*pdf.BRAND)
    pdf.cell(0, 7, "INDIVIDUELLER TRAININGSPLAN", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*pdf.DARK)
    pdf.ln(1)

    # ── Altersgruppen-Badge ──────────────────────────────────────────────────
    pg_label = plangruppen_config.get("label", plangruppe)
    pdf.check_page_break(22)
    bx, by = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(230, 240, 255)
    pdf.rect(bx, by, 190, 18, "F")
    pdf.set_fill_color(*pdf.BRAND)
    pdf.rect(bx, by, 4, 18, "F")
    pdf.set_xy(bx + 8, by + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*pdf.BRAND)
    pdf.cell(60, 5, "ALTERSGRUPPE: %s" % _safe(plangruppe), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(bx + 8)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*pdf.DARK)
    pdf.cell(0, 5, _safe(pg_label), new_x="LMARGIN", new_y="NEXT")
    # Config-Details
    pdf.set_x(bx + 8)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*pdf.MID)
    max_saetze_str = str(plangruppen_config.get("max_saetze", "-"))
    if plangruppen_config.get("max_saetze", 99) >= 99:
        max_saetze_str = "ohne Begrenzung"
    freq_cap = plangruppen_config.get("haeuf_cap") or "ohne Begrenzung"
    pause_off = plangruppen_config.get("pause_offset", 0)
    details = "Max. Saetze: %s  |  Frequenz: %s  |  Pausenzuschlag: +%d s" % (
        _safe(max_saetze_str), _safe(str(freq_cap)), pause_off)
    pdf.cell(0, 4, _safe(details), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*pdf.DARK)
    pdf.ln(3)

    # ── Disclaimer ───────────────────────────────────────────────────────────
    pdf.disclaimer_box(_safe(TRAININGSPLAN_HINWEIS), border_color=(80, 100, 160))

    # ── Substitutionshinweise ────────────────────────────────────────────────
    # Zeige, welche Ubungen im Plan altersangepasste Ersetzungen sind
    plan_uebungen = {str(r.get("uebung", "")).strip() for r in plan_rows if r.get("uebung")}
    substitutionen = []
    for original_uebung, gruppen_map in alters_ersatz.items():
        if plangruppe in gruppen_map:
            ersatz = gruppen_map[plangruppe]
            if ersatz is None:
                # Ubung wird weggelassen
                substitutionen.append((original_uebung, None))
            else:
                ersatz_name = ersatz[0] if isinstance(ersatz, (tuple, list)) else str(ersatz)
                if ersatz_name.strip() in plan_uebungen:
                    substitutionen.append((original_uebung, ersatz_name))

    if substitutionen:
        pdf.check_page_break(20)
        pdf.section_title("ALTERSANPASSUNGEN (ERSATZ-UBUNGEN)")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*pdf.DARK)
        pdf.cell(0, 5,
                 "Folgende Ubungen wurden fuer die Altersgruppe %s automatisch angepasst:" % _safe(plangruppe),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        cols_sub = [("Original-Ubung", 80), ("Ersatz-Ubung (altersangepasst)", 90), ("Hinweis", 20)]
        pdf.table_header(cols_sub)
        fill = False
        for original, ersatz_name in substitutionen:
            if ersatz_name is None:
                hint = "entfernt"
                ersatz_str = "- entfernt -"
            else:
                hint = "ersetzt"
                ersatz_str = ersatz_name
            pdf.table_row(
                [_safe(original), _safe(ersatz_str), _safe(hint)],
                [c[1] for c in cols_sub],
                fill,
            )
            fill = not fill
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*pdf.MID)
        pdf.cell(0, 4, _safe(_QUELLEN), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*pdf.DARK)
        pdf.ln(3)

    # ── Plan-Ubersicht ───────────────────────────────────────────────────────
    if not plan_rows:
        pdf.section_title("KEIN TRAININGSPLAN VORHANDEN")
        return bytes(pdf.output())

    # Strukturiere nach Woche > Tag
    from collections import defaultdict
    wochen: dict = defaultdict(lambda: defaultdict(list))
    for row in plan_rows:
        woche_nr = int(row.get("woche") or 1)
        tag_nr   = int(row.get("tag") or 1)
        wochen[woche_nr][tag_nr].append(row)

    for woche_nr in sorted(wochen.keys()):
        is_deload = (woche_nr % 4 == 0)
        woche_label = "WOCHE %d%s" % (woche_nr, " - DELOAD" if is_deload else "")

        pdf.check_page_break(30)
        pdf.add_page() if pdf.get_y() > 200 else None
        pdf.section_title(woche_label)

        if is_deload:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*pdf.MID)
            pdf.cell(0, 5,
                     "Deload-Woche: Reduziertes Volumen und Intensitat zur Regeneration. Technikfokus.",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*pdf.DARK)
            pdf.ln(1)

        tags_in_woche = sorted(wochen[woche_nr].keys())
        for tag_nr in tags_in_woche:
            tag_label = _NAMEN_SICHER.get(tag_nr, "Tag %d" % tag_nr)

            pdf.check_page_break(30)

            # Tag-Header
            pdf.set_fill_color(220, 232, 248)
            tx, ty = pdf.get_x(), pdf.get_y()
            pdf.rect(tx, ty, 190, 7, "F")
            pdf.set_fill_color(*pdf.BRAND)
            pdf.rect(tx, ty, 3, 7, "F")
            pdf.set_xy(tx + 6, ty + 0.5)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*pdf.BRAND)
            pdf.cell(0, 6, _safe(tag_label))
            pdf.set_text_color(*pdf.DARK)
            pdf.ln(8)

            # Warm-Up (kompakt)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*pdf.MID)
            pdf.cell(0, 5, "WARM-UP (8-10 min, fussballspezifisch):", new_x="LMARGIN", new_y="NEXT")
            wu_cols = [("Ubung", 65), ("Volumen", 25), ("Hinweis", 100)]
            pdf.table_header(wu_cols)
            wu_fill = False
            for wu_name, wu_vol, wu_hint in _WARMUP_ROWS:
                pdf.table_row([_safe(wu_name), _safe(wu_vol), _safe(wu_hint)],
                               [c[1] for c in wu_cols], wu_fill)
                wu_fill = not wu_fill
            pdf.ln(2)

            # Hauptteil-Ubungen
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*pdf.MID)
            pdf.cell(0, 5, "HAUPTTEIL:", new_x="LMARGIN", new_y="NEXT")
            cols_ueb = [("Bereich", 28), ("Ubung", 68), ("Satze", 14), ("Wdh./Dauer", 28),
                        ("Pause (s)", 20), ("Ausfuhrung", 32)]
            pdf.table_header(cols_ueb)
            ueb_fill = False
            tag_rows = wochen[woche_nr][tag_nr]
            # Sort by Bereich
            for row in sorted(tag_rows, key=lambda r: str(r.get("bereich", ""))):
                bereich    = str(row.get("bereich", "-"))
                uebung     = str(row.get("uebung", "-"))
                saetze     = str(row.get("saetze", "-"))
                wdh        = str(row.get("wiederholungen", row.get("haeufigkeit", "-")))
                pause      = str(row.get("pause_sekunden", "-"))
                ausfuehr   = str(row.get("ausfuehrung", "-"))
                # Trim Ausfuhrungsprefix for PDF (keep to max 30 chars)
                if len(ausfuehr) > 30:
                    ausfuehr = ausfuehr[:28] + ".."
                pdf.table_row(
                    [_safe(bereich), _safe(uebung), _safe(saetze),
                     _safe(wdh), _safe(pause), _safe(ausfuehr)],
                    [c[1] for c in cols_ueb],
                    ueb_fill,
                )
                ueb_fill = not ueb_fill

            # Cool-Down-Hinweis
            pdf.ln(1)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*pdf.MID)
            pdf.cell(0, 5,
                     "Cool-Down: 5-10 min Stretching der trainierten Muskelgruppen "
                     "(Huftbeuger, Oberschenkel, Rumpf).",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*pdf.DARK)
            pdf.ln(3)

    # ── Quellen ──────────────────────────────────────────────────────────────
    pdf.check_page_break(20)
    pdf.ln(3)
    pdf.set_draw_color(*pdf.BRAND)
    pdf.set_line_width(0.3)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*pdf.MID)
    pdf.multi_cell(0, 4, _safe(_QUELLEN))
    pdf.set_text_color(*pdf.DARK)

    return bytes(pdf.output())


# Sicherere Tag-Namen ohne Umlaute fuer PDF
_NAMEN_SICHER = {
    1: "Tag 1 - Montag",
    2: "Tag 2 - Mittwoch",
    3: "Tag 3 - Freitag",
    4: "Tag 4 - Samstag",
    0: "Alle Tage",
}
