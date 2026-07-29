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
                              "uebergewicht", "bergewicht", "adipositas"]):
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
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.WHITE)
        self.cell(0, 10, "  FOOTBALL ATHLETIK DIAGNOSTIK", align="L")
        self.set_font("Helvetica", "", 8)
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
        footer_text = "Seite %d  |  %s" % (self.page_no(), _safe(PDF_FUSSZEILE))
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
    verletzungen=None,
    athletik_score: int = 0,
    risiko_label: str = "-",
    defizite: list = None,
    plan_rows: list = None,
) -> bytes:
    """
    Vollstaendiger Athletik-Bericht fuer alle Testmodule.
    Alle Row-Parameter sind optional -- fehlende Module werden uebersprungen.
    """
    defizite    = defizite   or []
    plan_rows   = plan_rows  or []
    verletzungen = verletzungen or []

    pdf = AthletikReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ════════════════════════════════════════════════════════════════════════════
    # DECKBLATT
    # ════════════════════════════════════════════════════════════════════════════

    pdf.section_title("SPIELERINFORMATIONEN")
    vorname  = spieler.get("vorname") or ""
    nachname = spieler.get("nachname") or spieler.get("name") or "-"
    fullname = ("%s %s" % (vorname, nachname)).strip()
    haupt    = spieler.get("hauptposition") or spieler.get("position") or "-"
    neben    = spieler.get("nebenposition") or ""
    pos_str  = haupt + (" / " + neben if neben else "")

    pdf.kv("Name",            fullname)
    pdf.kv("Position",        pos_str)
    pdf.kv("Spielbein",       spieler.get("spielbein") or "-")
    pdf.kv("Mannschaft",      spieler.get("mannschaft") or "-")
    pdf.kv("Geburtsdatum",    spieler.get("geburtsdatum") or "-")
    pdf.kv("Altersklasse",    spieler.get("altersklasse") or "-")
    pdf.kv("Leistungsniveau", spieler.get("leistungsniveau") or "-")
    pdf.kv("Trainingsstatus", spieler.get("trainingsstatus") or "-")
    pdf.ln(3)

    # ── Pflicht-Disclaimer ───────────────────────────────────────────────────
    pdf.disclaimer_box(_safe(KURZ_HINWEIS))

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
            pdf.row2("Koerperfett", "%s %%" % anthro_row.get("koerperfett"),
                     "Muskelmasse", "%s kg" % anthro_row.get("muskelmasse", "-"))
        if anthro_row.get("reifestatus"):
            pdf.kv("Reifestatus (Schaetzung)", anthro_row.get("reifestatus", "-"))
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════════
    # FMS
    # ════════════════════════════════════════════════════════════════════════════
    if fms_row:
        pdf.check_page_break(55)
        pdf.section_title("FMS - FUNCTIONAL MOVEMENT SCREEN")
        f_col2 = GREEN if fms_row["score"] >= 15 else YELLOW if fms_row["score"] >= 13 else RED
        pdf.row2("Testdatum",   fms_row.get("datum", "-"),
                 "Gesamtscore", "%d/21  (%s)" % (fms_row["score"], fms_row.get("bewertung","-")),
                 color_r=f_col2)
        pdf.row2("Asymmetrien", fms_row.get("asymmetrie", "-"),
                 "Schwerpunkt", fms_row.get("schwerpunkt", "-"))
        pdf.ln(1)
        patterns = [
            ("Deep Squat",           fms_row.get("deep_squat", 0)),
            ("Hurdle Step (min)",     min(fms_row.get("hurdle_links",0), fms_row.get("hurdle_rechts",0))),
            ("Inline Lunge (min)",    min(fms_row.get("inline_links",0), fms_row.get("inline_rechts",0))),
            ("Shoulder Mob. (min)",   min(fms_row.get("shoulder_links",0), fms_row.get("shoulder_rechts",0))),
            ("ASLR (min)",            min(fms_row.get("aslr_links",0), fms_row.get("aslr_rechts",0))),
            ("Trunk Stability",       fms_row.get("trunk", 0)),
            ("Rotary Stab. (min)",    min(fms_row.get("rotary_links",0), fms_row.get("rotary_rechts",0))),
        ]
        for name, val in patterns:
            pdf.progress_bar(name, val, 3)
        pdf.ln(1)
        pdf.disclaimer_box(_safe(FMS_HINWEIS), border_color=(80, 100, 160))
        pdf.ln(1)

    # ════════════════════════════════════════════════════════════════════════════
    # Y-BALANCE
    # ════════════════════════════════════════════════════════════════════════════
    if y_row:
        pdf.check_page_break(35)
        pdf.section_title("Y-BALANCE TEST")
        avg_y2 = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        y_col2 = GREEN if avg_y2 >= 89 else YELLOW if avg_y2 >= 85 else RED
        pdf.row2("Testdatum",        y_row.get("datum", "-"),
                 "Composite Rechts", "%.1f %%" % y_row["composite_rechts"])
        pdf.row2("Composite Links",  "%.1f %%" % y_row["composite_links"],
                 "Composite Oe",     "%.1f %%" % avg_y2,
                 color_r=y_col2)
        pdf.row2("Asymmetrie",       y_row.get("asymmetrie", "-"),
                 "Schwerpunkt",      y_row.get("schwerpunkt", "-"))
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
        pdf.section_title("12-WOCHEN-PERIODISIERUNGSPLAN (AUSZUG)")
        pdf.disclaimer_box(_safe(TRAININGSPLAN_HINWEIS), border_color=(80, 100, 160))
        pdf.ln(1)
        cols = [("Wo.",12),("Phase",42),("Bereich",32),("Uebung",62),("Vol.",22),("Hz.",20)]
        pdf.table_header(cols)
        widths = [c[1] for c in cols]
        fill = False
        for row in plan_rows[:30]:
            vals = [
                row.get("woche", row[0] if isinstance(row, (list, tuple)) else "-"),
                row.get("phase",      row[1] if isinstance(row, (list, tuple)) else "-"),
                row.get("bereich",    row[3] if isinstance(row, (list, tuple)) else "-"),
                row.get("uebung",     row[4] if isinstance(row, (list, tuple)) else "-"),
                row.get("volumen",    row[6] if isinstance(row, (list, tuple)) else "-"),
                row.get("haeufigkeit",row[7] if isinstance(row, (list, tuple)) else "-"),
            ]
            pdf.table_row(vals, widths, fill)
            fill = not fill

    return bytes(pdf.output())
