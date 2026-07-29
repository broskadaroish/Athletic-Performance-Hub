"""
Testprotokoll PDF — leere Druckbogen fuer die papierbasierte Erfassung.
Keine Bewertung, keine Auswertung — reines Erfassungsformular.
Verwendet fpdf2 (Helvetica / Latin-1). Schwarz-Weiss-tauglich.
"""

from fpdf import FPDF
from datetime import date
import io


# ─── Encoding-Schutz ──────────────────────────────────────────────────────────

def _s(text) -> str:
    """Konvertiert beliebigen Text in Latin-1-sicheren String."""
    if text is None:
        return ""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2019": "'", "\u201c": '"',
        "\u201d": '"', "\u2026": "...", "\u2082": "2", "\u00d7": "x",
        "\u00fc": "ue", "\u00f6": "oe", "\u00e4": "ae",
        "\u00dc": "Ue", "\u00d6": "Oe", "\u00c4": "Ae",
        "\u00df": "ss", "\u00e9": "e", "\u00e8": "e", "\u00e0": "a",
        "\u00f1": "n",
    }
    for old, new in replacements.items():
        text = str(text).replace(old, new)
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


# ─── Test-Definitionen ────────────────────────────────────────────────────────

# Jeder Eintrag: name, beschreibung, felder (Liste von Dicts)
# Feld-Typen:
#   "single"      — ein Wertefeld (kein Versuch)
#   "attempts"    — V1 / V2 / V3 / Bestwert
#   "attempts_lr" — wie "attempts", aber 2 Zeilen (Rechts / Links)
#   "score"       — FMS-Score (0–3), optional bilateral
#   "fixed"       — festes Auswahlfeld (kein Versuch), z.B. Test-Typ

TEST_DEFS = {
    "anthropometrie": {
        "name": "Anthropometrie",
        "icon": "A",
        "beschreibung": "Koerperliche Grundmessungen. Alle Angaben handschriftlich eintragen.",
        "felder": [
            {"label": "Koerpergroesse",  "einheit": "cm",  "typ": "single"},
            {"label": "Koerpergewicht",  "einheit": "kg",  "typ": "single"},
            {"label": "Sitzhoehe",       "einheit": "cm",  "typ": "single"},
            {"label": "Beinlaenge",      "einheit": "cm",  "typ": "attempts_lr"},
            {"label": "Armspannweite",   "einheit": "cm",  "typ": "single"},
            {"label": "Koerperfett",     "einheit": "%",   "typ": "single"},
            {"label": "Muskelmasse",     "einheit": "%",   "typ": "single"},
        ],
    },
    "fms": {
        "name": "FMS (Functional Movement Screen)",
        "icon": "F",
        "beschreibung": "Score 0-3 pro Uebung. Bei bilateralen Tests: niedrigerer Seitenwert zaehlt fuer Gesamtscore.",
        "felder": [
            {"label": "1. Deep Squat",               "bilateral": False},
            {"label": "2. Hurdle Step",               "bilateral": True},
            {"label": "3. Inline Lunge",              "bilateral": True},
            {"label": "4. Shoulder Mobility",         "bilateral": True},
            {"label": "5. Active Straight Leg Raise", "bilateral": True},
            {"label": "6. Trunk Stability Push-Up",   "bilateral": False},
            {"label": "7. Rotary Stability",          "bilateral": True},
        ],
    },
    "y_balance": {
        "name": "Y-Balance Test",
        "icon": "Y",
        "beschreibung": "3 Versuche pro Richtung und Seite. Beinlaenge vor dem Test messen.",
        "felder": [
            {"label": "Beinlaenge",       "einheit": "cm",  "typ": "attempts_lr"},
            {"label": "Anterior",         "einheit": "cm",  "typ": "attempts_lr"},
            {"label": "Posteromedial",    "einheit": "cm",  "typ": "attempts_lr"},
            {"label": "Posterolateral",   "einheit": "cm",  "typ": "attempts_lr"},
        ],
    },
    "sprint": {
        "name": "Sprint-Diagnostik",
        "icon": "S",
        "beschreibung": "Zeiten in Sekunden. Bitte beste Zeit als Bestwert eintragen.",
        "felder": [
            {"label": "5 m",   "einheit": "s", "typ": "attempts"},
            {"label": "10 m",  "einheit": "s", "typ": "attempts"},
            {"label": "20 m",  "einheit": "s", "typ": "attempts"},
            {"label": "30 m",  "einheit": "s", "typ": "attempts"},
        ],
    },
    "sprung": {
        "name": "Sprung-Diagnostik",
        "icon": "J",
        "beschreibung": "Sprunghoehn in cm, Kontaktzeit in ms. 3 Versuche, Bestwert eintragen.",
        "felder": [
            {"label": "CMJ beidseits",       "einheit": "cm", "typ": "attempts"},
            {"label": "CMJ rechts",          "einheit": "cm", "typ": "attempts"},
            {"label": "CMJ links",           "einheit": "cm", "typ": "attempts"},
            {"label": "Squat Jump",          "einheit": "cm", "typ": "attempts"},
            {"label": "Drop Jump Hoehe",     "einheit": "cm", "typ": "attempts"},
            {"label": "Drop Jump Kontaktzt", "einheit": "ms", "typ": "attempts"},
            {"label": "Standweitsprung",     "einheit": "cm", "typ": "attempts"},
        ],
    },
    "agilitaet": {
        "name": "Agilitaet / Richtungswechsel",
        "icon": "AG",
        "beschreibung": "Zeiten in Sekunden. 505-Test bilateral (Rechts/Links).",
        "felder": [
            {"label": "505",      "einheit": "s",  "typ": "attempts_lr"},
            {"label": "5-10-5",   "einheit": "s",  "typ": "attempts"},
            {"label": "T-Test",   "einheit": "s",  "typ": "attempts"},
            {"label": "Illinois", "einheit": "s",  "typ": "attempts"},
        ],
    },
    "ausdauer": {
        "name": "Ausdauer (Yo-Yo-Test)",
        "icon": "AU",
        "beschreibung": "Yo-Yo Test Stufe I, II oder Intermittent Recovery. Distanz in Metern.",
        "felder": [
            {"label": "Test-Typ",     "einheit": "YoYo I / II / IR", "typ": "single"},
            {"label": "Distanz",      "einheit": "m",                "typ": "single"},
            {"label": "HF max",       "einheit": "bpm",              "typ": "single"},
            {"label": "RPE (1-10)",   "einheit": "1-10",             "typ": "single"},
        ],
    },
    "kraft": {
        "name": "Kraftdiagnostik",
        "icon": "K",
        "beschreibung": "Bankdruecken 1RM (direkt oder Epley-Schaetzung) und Rumpfkraftausdauer (Haltezeiten in Sekunden).",
        "felder": [],  # Spezielles Rendering — siehe _add_test_section
    },
}

TEST_REIHENFOLGE = ["anthropometrie", "fms", "y_balance", "sprint", "sprung", "agilitaet", "ausdauer", "kraft"]
TEST_NAMEN = {k: v["name"] for k, v in TEST_DEFS.items()}


# ─── PDF-Klasse ───────────────────────────────────────────────────────────────

class TestprotokollPDF(FPDF):
    """Schwarz-Weiss-tauglicher Druckbogen fuer den Papiereinsatz."""

    GR_DARK  = (30, 30, 30)
    GR_MID   = (90, 90, 90)
    GR_LIGHT = (215, 215, 215)
    GR_PALE  = (240, 240, 240)
    WHITE    = (255, 255, 255)

    # Spaltenbreiten fuer "attempts"-Tabellen
    W_LABEL = 54
    W_UNIT  = 16
    W_V     = 27
    W_BEST  = 29   # W_LABEL + W_UNIT + 3*W_V + W_BEST = 180

    def header(self):
        self.set_fill_color(*self.GR_DARK)
        self.rect(0, 0, 210, 16, "F")
        self.set_y(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.WHITE)
        self.cell(0, 10, "  ATHLETIK DIAGNOSTIK  -  TESTPROTOKOLL", align="L")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, f"Druckdatum: {date.today().strftime('%d.%m.%Y')}  ", align="R")
        self.set_text_color(*self.GR_DARK)
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.GR_MID)
        self.cell(
            0, 8,
            f"Seite {self.page_no()}  |  Dieses Formular dient ausschliesslich der Datenerfassung. Keine Diagnose.",
            align="C",
        )

    # ── Hilfs-Methoden ────────────────────────────────────────────────────────

    def _section_header(self, title: str):
        """Test-Abschnitts-Kopf (dunkles Band)."""
        self.ln(3)
        self.set_fill_color(*self.GR_DARK)
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {_s(title)}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.GR_DARK)

    def _beschreibung(self, text: str):
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*self.GR_MID)
        self.cell(0, 5, _s(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.GR_DARK)
        self.ln(1)

    def _checkbox_row(self, text: str):
        """Kleine Checkbox-Zeile."""
        self.set_font("Helvetica", "", 8)
        x0 = self.get_x()
        y0 = self.get_y()
        self.set_draw_color(*self.GR_MID)
        self.rect(x0, y0 + 1, 4, 4)
        self.set_x(x0 + 6)
        self.cell(0, 6, _s(text), new_x="LMARGIN", new_y="NEXT")

    def _lined_box(self, label: str, height: float = 14, lines: int = 2):
        """Freie Schreibzeilen-Box mit Label."""
        self.ln(2)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*self.GR_MID)
        self.cell(0, 5, _s(label), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*self.GR_DARK)
        x0 = self.get_x()
        y0 = self.get_y()
        w = 190
        lh = height / lines
        # Zeichne Linien innerhalb der Box
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.2)
        self.rect(x0, y0, w, height)
        for i in range(1, lines):
            self.line(x0, y0 + i * lh, x0 + w, y0 + i * lh)
        self.set_y(y0 + height + 1)

    def _table_header(self, cols: list[tuple]):
        """Tabellenkopf: cols = list of (label, width)."""
        self.set_fill_color(*self.GR_LIGHT)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*self.GR_DARK)
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.2)
        for label, w in cols:
            self.cell(w, 6, _s(label), border=1, fill=True, align="C")
        self.ln()

    def _table_row(self, label: str, unit: str, typ: str,
                   seite: str | None = None, bold_label: bool = False):
        """Eine Tabellenzeile fuer Messwerte (leer zum Eintragen)."""
        h = 8
        self.set_font("Helvetica", "B" if bold_label else "", 8)
        self.set_fill_color(*self.WHITE)
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.2)

        if typ == "single":
            # Label | Einheit | Wertefeld
            self.cell(self.W_LABEL, h, f"  {_s(label)}", border="LTB")
            self.cell(self.W_UNIT,  h, _s(unit),         border="TB",  align="C")
            self.cell(190 - self.W_LABEL - self.W_UNIT, h, "",          border="RTB")
            self.ln()

        elif typ in ("attempts", "attempts_lr"):
            # Wenn attempts_lr: erst Rechts-Zeile, dann Links-Zeile
            sides = [None] if typ == "attempts" else ["Rechts", "Links"]
            for side in sides:
                lbl = f"  {_s(label)}"
                if side:
                    lbl = f"  {_s(label)} ({side})"
                self.set_font("Helvetica", "B" if bold_label else "", 8)
                self.cell(self.W_LABEL, h, lbl,       border="LTB")
                self.cell(self.W_UNIT,  h, _s(unit),  border="TB",  align="C")
                self.cell(self.W_V,     h, "",         border="TLB", align="C")
                self.cell(self.W_V,     h, "",         border="TLB", align="C")
                self.cell(self.W_V,     h, "",         border="TLB", align="C")
                self.cell(self.W_BEST,  h, "",         border="TRB", align="C")
                self.ln()

    def _fms_header(self):
        self._table_header([
            ("Uebung", 90),
            ("Score (0-3)", 33),
            ("Links", 33),
            ("Rechts", 34),
        ])

    def _fms_row(self, label: str, bilateral: bool):
        h = 8
        self.set_font("Helvetica", "", 8)
        self.set_fill_color(*self.WHITE)
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.2)
        self.cell(90, h, f"  {_s(label)}", border=1)
        if bilateral:
            self.cell(33, h, "", border=1, align="C")
            self.cell(33, h, "", border=1, align="C")
            self.cell(34, h, "", border=1, align="C")
        else:
            # Score in der Score-Spalte, L und R grau hinterlegen
            self.cell(33, h, "", border=1, align="C")
            self.set_fill_color(*self.GR_PALE)
            self.cell(33, h, "(nicht bilateral)", border=1, fill=True, align="C")
            self.cell(34, h, "",                  border=1, fill=True, align="C")
            self.set_fill_color(*self.WHITE)
        self.ln()

    def _spieler_block(self, spieler: dict | None):
        """Spieler-Infoblock oben auf jeder Protokollseite."""
        self.set_draw_color(*self.GR_MID)
        self.set_line_width(0.3)
        y0 = self.get_y()
        bw = 190

        if spieler:
            # Vorgefuellt mit Spielerdaten
            self.set_fill_color(*self.GR_PALE)
            self.rect(10, y0, bw, 20, "DF")
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 6, f"  {_s(spieler.get('name', '—'))}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 8)
            geb    = spieler.get("geburtsdatum") or "—"
            team   = spieler.get("mannschaft")   or "—"
            pos    = spieler.get("hauptposition") or spieler.get("position") or "—"
            bein   = spieler.get("spielbein")     or "—"
            pid    = spieler.get("id", "—")
            zeile2 = f"  Geb.: {_s(geb)}   |   Mannschaft: {_s(team)}   |   Position: {_s(pos)}   |   Spielbein: {_s(bein)}   |   ID: {pid}"
            self.cell(0, 5, zeile2, new_x="LMARGIN", new_y="NEXT")
            self.set_y(y0 + 22)
        else:
            # Leere Felder zum Ausfuellen
            self.set_fill_color(*self.GR_PALE)
            self.rect(10, y0, bw, 26, "DF")
            labels = [
                ("Name:", 60), ("Mannschaft:", 60), ("Datum:", 60),
            ]
            x = 10
            for lbl, w in labels:
                self.set_xy(x, y0 + 2)
                self.set_font("Helvetica", "B", 7.5)
                self.set_text_color(*self.GR_MID)
                self.cell(25, 5, _s(lbl))
                self.set_draw_color(*self.GR_MID)
                self.set_line_width(0.3)
                self.line(x + 25, y0 + 10, x + w - 3, y0 + 10)
                x += w
            x = 10
            labels2 = [
                ("Trainer:", 60), ("Jahrgang:", 60), ("Datum Test:", 60),
            ]
            for lbl, w in labels2:
                self.set_xy(x, y0 + 14)
                self.set_font("Helvetica", "B", 7.5)
                self.set_text_color(*self.GR_MID)
                self.cell(25, 5, _s(lbl))
                self.set_draw_color(*self.GR_MID)
                self.set_line_width(0.3)
                self.line(x + 25, y0 + 22, x + w - 3, y0 + 22)
                x += w
            self.set_text_color(*self.GR_DARK)
            self.set_y(y0 + 28)

    def _maybe_page_break(self, needed_mm: float = 40):
        """Neue Seite wenn nicht genuegend Platz."""
        if self.get_y() + needed_mm > 280:
            self.add_page()


# ─── Abschnitte pro Test ──────────────────────────────────────────────────────

def _add_test_section(pdf: TestprotokollPDF, test_id: str):
    """Fuegt einen vollstaendigen Test-Abschnitt hinzu."""
    td = TEST_DEFS.get(test_id)
    if not td:
        return

    # Platzcheck: mindestens 60mm fuer einen Abschnitt
    pdf._maybe_page_break(60)

    # Abschnitts-Header
    pdf._section_header(td["name"])
    pdf._beschreibung(td["beschreibung"])

    # Checkbox "nicht durchgefuehrt"
    pdf._checkbox_row("Test nicht durchgefuehrt (begruenden Sie im Bemerkungsfeld)")
    pdf.ln(1)

    if test_id == "fms":
        pdf._fms_header()
        for f in td["felder"]:
            pdf._fms_row(f["label"], f["bilateral"])

    elif test_id in ("anthropometrie", "y_balance", "sprint", "sprung", "agilitaet", "ausdauer"):
        # Tabellenkopf
        attempt_cols = [
            ("Messung", pdf.W_LABEL),
            ("Einheit", pdf.W_UNIT),
            ("Versuch 1", pdf.W_V),
            ("Versuch 2", pdf.W_V),
            ("Versuch 3", pdf.W_V),
            ("Bestwert",  pdf.W_BEST),
        ]
        pdf._table_header(attempt_cols)
        for f in td["felder"]:
            pdf._table_row(f["label"], f.get("einheit", ""), f["typ"])

    elif test_id == "kraft":
        # ── A: Bankdrücken 1RM ──────────────────────────────────────────────────
        pdf._beschreibung("A) Bankdruecken 1RM  |  Methode: Direkt / Epley-Schaetzung ankreuzen")
        pdf._checkbox_row("Methode: Direkter 1RM-Test (Sicherung durch 2 Trainer erforderlich)")
        pdf._checkbox_row("Methode: Submaximaltest mit Epley-Schaetzung (empfohlen)")
        pdf.ln(1)
        bd_cols = [
            ("Messung", pdf.W_LABEL),
            ("Einheit", pdf.W_UNIT),
            ("Versuch 1", pdf.W_V),
            ("Versuch 2", pdf.W_V),
            ("Versuch 3", pdf.W_V),
            ("Bestwert",  pdf.W_BEST),
        ]
        pdf._table_header(bd_cols)
        pdf._table_row("Testgewicht Bankdruecken", "kg", "attempts")
        pdf._table_row("Wiederholungen (2-10 WH)", "WH", "single")
        pdf._table_row("Direktes 1RM", "kg", "single")
        pdf._table_row("Geschaetztes 1RM (Epley)", "kg", "single")
        pdf._table_row("Relative Kraft  (1RM / Koerpergew.)", "xKGW", "single")
        pdf.ln(3)

        # ── B: Rumpfkraftausdauer ──────────────────────────────────────────────
        pdf._beschreibung("B) Rumpfkraftausdauer — Haltezeiten in Sekunden")
        rumpf_cols = [
            ("Uebung / Variante", pdf.W_LABEL + pdf.W_UNIT),
            ("Versuch 1 (s)", pdf.W_V),
            ("Versuch 2 (s)", pdf.W_V),
            ("Bestwert (s)", pdf.W_V + pdf.W_BEST),
        ]
        pdf._table_header(rumpf_cols)
        rh = 8
        for lbl in ["Ventral (Plank) beidbeinig", "Lateral rechts", "Lateral links", "Dorsal"]:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_fill_color(*pdf.WHITE)
            pdf.set_draw_color(*pdf.GR_MID)
            pdf.set_line_width(0.2)
            pdf.cell(pdf.W_LABEL + pdf.W_UNIT, rh, f"  {_s(lbl)}", border="LTB")
            pdf.cell(pdf.W_V,              rh, "", border="TLB")
            pdf.cell(pdf.W_V,              rh, "", border="TLB")
            pdf.cell(pdf.W_V + pdf.W_BEST, rh, "", border="TRB")
            pdf.ln()
        # Summenzeile
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*pdf.GR_PALE)
        pdf.cell(pdf.W_LABEL + pdf.W_UNIT, rh, "  Rumpf-Gesamtzeit", border=1, fill=True)
        pdf.cell(pdf.W_V,              rh, "", border=1, fill=True)
        pdf.cell(pdf.W_V,              rh, "", border=1, fill=True)
        pdf.cell(pdf.W_V + pdf.W_BEST, rh, "", border=1, fill=True)
        pdf.ln()
        pdf.set_fill_color(*pdf.WHITE)

    # Trainerbeobachtungen
    pdf._maybe_page_break(30)
    pdf._lined_box("Trainerbeobachtungen:", height=14, lines=2)

    # Bemerkungen
    pdf._lined_box("Bemerkungen:", height=12, lines=2)
    pdf.ln(3)


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

def generate_testprotokoll(
    test_ids: list[str],
    spieler_liste: list[dict] | None = None,
    variante: str = "leer",
) -> bytes:
    """
    Erzeugt das Testprotokoll-PDF.

    variante="leer"      → leeres Formular (ein Satz Seiten)
    variante="spieler"   → pro Spieler eine eigene Seite / Abschnitt
    """
    pdf = TestprotokollPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(10, 18, 10)
    pdf.set_font("Helvetica", "", 9)

    ordered = [tid for tid in TEST_REIHENFOLGE if tid in test_ids]

    if variante == "leer" or not spieler_liste:
        pdf.add_page()
        pdf._spieler_block(None)
        for tid in ordered:
            _add_test_section(pdf, tid)

    else:
        for spieler in spieler_liste:
            pdf.add_page()
            pdf._spieler_block(spieler)
            for tid in ordered:
                _add_test_section(pdf, tid)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
