"""
PDF Report generation — produces a professional 2-page player assessment report.
Uses fpdf2 (pip install fpdf2).
"""

from fpdf import FPDF
from datetime import date
import io


class AthletikReport(FPDF):
    BRAND_COLOR = (20, 90, 160)   # dark blue
    ACCENT      = (230, 50, 50)   # red accent
    LIGHT_BG    = (245, 247, 250)
    DARK_TEXT   = (30, 30, 40)
    MID_TEXT    = (80, 90, 110)

    def header(self):
        # Header bar
        self.set_fill_color(*self.BRAND_COLOR)
        self.rect(0, 0, 210, 18, "F")
        self.set_y(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "  ⚽  FOOTBALL ATHLETIK DIAGNOSTIK", align="L")
        self.set_font("Helvetica", "", 9)
        self.set_xy(0, 6)
        self.cell(0, 8, f"Erstellt am {date.today().strftime('%d.%m.%Y')}  ", align="R")
        self.set_text_color(*self.DARK_TEXT)
        self.ln(14)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*self.BRAND_COLOR)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.MID_TEXT)
        self.cell(0, 8, f"Seite {self.page_no()} — Vertraulich — Football Athletik Diagnostik System", align="C")

    def section_title(self, title: str):
        self.ln(3)
        self.set_fill_color(*self.BRAND_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"  {title}", fill=True, ln=True)
        self.set_text_color(*self.DARK_TEXT)
        self.ln(2)

    def kv(self, key: str, value: str, width_key=65):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.MID_TEXT)
        self.cell(width_key, 6, key + ":", ln=False)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK_TEXT)
        self.cell(0, 6, str(value), ln=True)

    def metric_box(self, label: str, value: str, status: str = "ok"):
        colours = {"ok": (39, 174, 96), "warn": (230, 126, 34), "bad": (231, 76, 60)}
        col = colours.get(status, colours["ok"])
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*self.LIGHT_BG)
        self.rect(x, y, 58, 18, "F")
        self.set_fill_color(*col)
        self.rect(x, y, 3, 18, "F")
        self.set_xy(x + 5, y + 2)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*self.MID_TEXT)
        self.cell(50, 5, label.upper(), ln=True)
        self.set_x(x + 5)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.DARK_TEXT)
        self.cell(50, 9, str(value), ln=False)
        self.set_xy(x + 62, y)

    def progress_bar(self, label: str, value: int, max_val: int = 100):
        pct = min(value / max_val, 1.0)
        if pct >= 0.75:
            col = (39, 174, 96)
        elif pct >= 0.5:
            col = (230, 126, 34)
        else:
            col = (231, 76, 60)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.DARK_TEXT)
        self.cell(70, 6, label, ln=False)
        x, y = self.get_x(), self.get_y() + 1
        bar_w = 80
        self.set_fill_color(220, 225, 235)
        self.rect(x, y, bar_w, 4, "F")
        self.set_fill_color(*col)
        self.rect(x, y, bar_w * pct, 4, "F")
        self.set_xy(x + bar_w + 3, y - 1)
        self.set_font("Helvetica", "B", 9)
        self.cell(20, 6, f"{value}/{max_val}", ln=True)


def generate_report(spieler, fms_row, y_row, athletik_score: int,
                    risiko_label: str, defizite: list, plan_rows: list) -> bytes:
    """
    Generate a PDF report and return it as bytes.

    Parameters
    ----------
    spieler     : sqlite3.Row  (id, name, geburtsdatum, position, spielbein, mannschaft)
    fms_row     : sqlite3.Row | None
    y_row       : sqlite3.Row | None
    athletik_score : int 0–100
    risiko_label   : str
    defizite    : list[dict]
    plan_rows   : list[sqlite3.Row]  (woche,phase,ziel,bereich,uebung,…)
    """
    pdf = AthletikReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Player info ─────────────────────────────────────────────────────────
    pdf.section_title("Spielerinformationen")
    pdf.kv("Name",       spieler["name"])
    pdf.kv("Position",   spieler["position"] or "—")
    pdf.kv("Spielbein",  spieler["spielbein"] or "—")
    pdf.kv("Mannschaft", spieler["mannschaft"] or "—")
    pdf.kv("Geburtsdatum", spieler["geburtsdatum"] or "—")
    pdf.ln(4)

    # ── Key metrics ──────────────────────────────────────────────────────────
    pdf.section_title("Athletik-Kennzahlen")
    pdf.ln(2)
    x_start = pdf.get_x()

    a_status = "ok" if athletik_score >= 75 else "warn" if athletik_score >= 50 else "bad"
    pdf.metric_box("Athletik Score", f"{athletik_score}/100", a_status)

    fms_score = fms_row["score"] if fms_row else "—"
    f_status = "ok" if (fms_row and fms_row["score"] >= 15) else "warn" if (fms_row and fms_row["score"] >= 13) else "bad"
    pdf.metric_box("FMS Score", f"{fms_score}/21", f_status)

    comp_avg = "—"
    y_status = "ok"
    if y_row:
        avg = (y_row["composite_rechts"] + y_row["composite_links"]) / 2
        comp_avg = f"{avg:.1f}%"
        y_status = "ok" if avg >= 89 else "warn" if avg >= 85 else "bad"
    pdf.metric_box("Y-Balance Ø", comp_avg, y_status)
    pdf.ln(22)

    # ── Risk ─────────────────────────────────────────────────────────────────
    pdf.section_title("Verletzungsrisiko")
    pdf.set_font("Helvetica", "B", 11)
    is_high = "HOCH" in risiko_label.upper()
    is_mid  = "MITTEL" in risiko_label.upper()
    col = (231, 76, 60) if is_high else (230, 126, 34) if is_mid else (39, 174, 96)
    pdf.set_text_color(*col)
    pdf.cell(0, 8, risiko_label, ln=True)
    pdf.set_text_color(*pdf.DARK_TEXT)
    pdf.ln(2)

    # ── FMS detail ────────────────────────────────────────────────────────────
    if fms_row:
        pdf.section_title("FMS Testergebnisse")
        pdf.kv("Testdatum",   fms_row["datum"])
        pdf.kv("Gesamtscore", f"{fms_row['score']} / 21  ({fms_row['bewertung']})")
        pdf.kv("Asymmetrien", fms_row["asymmetrie"])
        pdf.kv("Schwerpunkt", fms_row["schwerpunkt"])
        pdf.ln(2)
        # Pattern bars
        patterns = {
            "Deep Squat":         fms_row["deep_squat"],
            "Hurdle Step (min)":  min(fms_row["hurdle_links"], fms_row["hurdle_rechts"]),
            "Inline Lunge (min)": min(fms_row["inline_links"], fms_row["inline_rechts"]),
            "Shoulder (min)":     min(fms_row["shoulder_links"], fms_row["shoulder_rechts"]),
            "ASLR (min)":         min(fms_row["aslr_links"], fms_row["aslr_rechts"]),
            "Trunk Stability":    fms_row["trunk"],
            "Rotary Stab. (min)": min(fms_row["rotary_links"], fms_row["rotary_rechts"]),
        }
        for name, val in patterns.items():
            pdf.progress_bar(name, val, 3)
        pdf.ln(3)

    # ── Y-Balance detail ──────────────────────────────────────────────────────
    if y_row:
        pdf.section_title("Y-Balance Testergebnisse")
        pdf.kv("Testdatum",          y_row["datum"])
        pdf.kv("Composite Rechts",   f"{y_row['composite_rechts']} %")
        pdf.kv("Composite Links",    f"{y_row['composite_links']} %")
        pdf.kv("Asymmetrie",         y_row["asymmetrie"])
        pdf.kv("Trainingsschwerpunkt", y_row["schwerpunkt"])
        pdf.ln(2)

    # ── Defizite ──────────────────────────────────────────────────────────────
    if defizite:
        pdf.section_title("Erkannte Defizite")
        for d in defizite:
            icon = "▶" if d["level"] == "kritisch" else "○"
            pdf.set_font("Helvetica", "B", 9)
            col = (231, 76, 60) if d["level"] == "kritisch" else (230, 126, 34)
            pdf.set_text_color(*col)
            pdf.cell(5, 6, icon)
            pdf.set_text_color(*pdf.DARK_TEXT)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(50, 6, d["bereich"] + ":", ln=False)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, d["text"], ln=True)
        pdf.set_text_color(*pdf.DARK_TEXT)
        pdf.ln(3)

    # ── Training plan (first 12 rows) ─────────────────────────────────────────
    if plan_rows:
        pdf.add_page()
        pdf.section_title("Individueller Trainingsplan (12-Wochen-Zyklus)")
        # Table header
        pdf.set_fill_color(*pdf.BRAND_COLOR)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        cols = [("Woche", 14), ("Phase", 40), ("Bereich", 30), ("Übung", 60), ("Vol.", 24), ("Hz.", 22)]
        for label, w in cols:
            pdf.cell(w, 7, label, border=0, fill=True)
        pdf.ln()
        pdf.set_text_color(*pdf.DARK_TEXT)
        fill = False
        for row in plan_rows[:24]:
            pdf.set_fill_color(245, 247, 250) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "", 7)
            vals = [str(row[0]), str(row[1]), str(row[3]), str(row[4]), str(row[6]), str(row[7])]
            widths = [14, 40, 30, 60, 24, 22]
            for v, w in zip(vals, widths):
                pdf.cell(w, 6, v[:30], fill=True)
            pdf.ln()
            fill = not fill

    output = io.BytesIO()
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
