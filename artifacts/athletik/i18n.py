"""
Bruce Football Performance Diagnostics — Mehrsprachigkeit
Unterstützte Sprachen: Deutsch (de) / Englisch (en)
Verwendung:  from i18n import t, SPRACHEN
             t("speichern")  → "Speichern" / "Save"
"""
import streamlit as st

SPRACHEN = {
    "de": "🇩🇪 Deutsch",
    "en": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 English",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Navigation ────────────────────────────────────────────────────────────
    "nav_startseite":    {"de": "🏠  Startseite",      "en": "🏠  Dashboard"},
    "nav_spieler":       {"de": "👤  Spieler",          "en": "👤  Players"},
    "nav_diagnostik":    {"de": "🔬  Diagnostik",       "en": "🔬  Diagnostics"},
    "nav_training":      {"de": "📅  Training",          "en": "📅  Training"},
    "nav_entwicklung":   {"de": "📈  Entwicklung",       "en": "📈  Development"},
    "nav_vergleich":     {"de": "⚖️  Vergleich",         "en": "⚖️  Comparison"},
    "nav_mannschaft":    {"de": "👥  Mannschaft",        "en": "👥  Team"},
    "nav_protokoll":     {"de": "🖨️  Protokoll",         "en": "🖨️  Protocol"},
    "nav_anleitungen":   {"de": "📄  Anleitungen",       "en": "📄  Instructions"},
    "nav_einstellungen": {"de": "⚙️  Einstellungen",    "en": "⚙️  Settings"},
    "nav_ueber":         {"de": "ℹ️  Über",              "en": "ℹ️  About"},

    # ── Spieler-Sub-Navigation ────────────────────────────────────────────────
    "sub_verwaltung":    {"de": "👥 Verwaltung",         "en": "👥 Management"},
    "sub_profil":        {"de": "🏃 Profil & Diagnostik","en": "🏃 Profile & Diagnostics"},
    "sub_anthropometrie":{"de": "📐 Anthropometrie",     "en": "📐 Anthropometry"},

    # ── Diagnostik-Sub-Navigation ─────────────────────────────────────────────
    "sub_diag_overview": {"de": "🏠 Übersicht",          "en": "🏠 Overview"},
    "sub_fms":           {"de": "📝 FMS",                "en": "📝 FMS"},
    "sub_ybalance":      {"de": "📏 Y-Balance",          "en": "📏 Y-Balance"},
    "sub_sprint":        {"de": "⚡ Sprint",              "en": "⚡ Sprint"},
    "sub_sprung":        {"de": "🦘 Sprung",              "en": "🦘 Jump"},
    "sub_agilitaet":     {"de": "🔀 Agilität",           "en": "🔀 Agility"},
    "sub_ausdauer":      {"de": "🫁 Ausdauer",           "en": "🫁 Endurance"},
    "sub_kraft":         {"de": "💪 Kraft",               "en": "💪 Strength"},

    # ── Training-Sub-Navigation ───────────────────────────────────────────────
    "sub_trainingsplan": {"de": "📅 Trainingsplan",       "en": "📅 Training Plan"},
    "sub_periodisierung":{"de": "🔄 Periodisierung",      "en": "🔄 Periodisation"},

    # ── Allgemeine Buttons ────────────────────────────────────────────────────
    "speichern":         {"de": "💾 Speichern",           "en": "💾 Save"},
    "loeschen":          {"de": "🗑️ Löschen",             "en": "🗑️ Delete"},
    "abbrechen":         {"de": "Abbrechen",               "en": "Cancel"},
    "zurueck":           {"de": "← Zurück",                "en": "← Back"},
    "generieren":        {"de": "⚡ Generieren",           "en": "⚡ Generate"},
    "herunterladen":     {"de": "⬇ Herunterladen",        "en": "⬇ Download"},
    "exportieren":       {"de": "📤 Exportieren",          "en": "📤 Export"},
    "aktualisieren":     {"de": "🔄 Aktualisieren",        "en": "🔄 Refresh"},
    "hinzufuegen":       {"de": "➕ Hinzufügen",           "en": "➕ Add"},
    "bearbeiten":        {"de": "✏️ Bearbeiten",           "en": "✏️ Edit"},
    "bestaetigen":       {"de": "✅ Bestätigen",           "en": "✅ Confirm"},

    # ── Spielerverwaltung ─────────────────────────────────────────────────────
    "spieler_neu":       {"de": "➕ Neu anlegen",          "en": "➕ New Player"},
    "spieler_bearbeiten":{"de": "✏️ Bearbeiten",          "en": "✏️ Edit"},
    "spieler_alle":      {"de": "📋 Alle Spieler",        "en": "📋 All Players"},
    "vorname":           {"de": "Vorname",                 "en": "First Name"},
    "nachname":          {"de": "Nachname",                "en": "Last Name"},
    "geburtsdatum":      {"de": "Geburtsdatum (TT.MM.JJJJ)", "en": "Date of Birth (DD.MM.YYYY)"},
    "geschlecht":        {"de": "Geschlecht",              "en": "Gender"},
    "maennlich":         {"de": "Männlich",                "en": "Male"},
    "weiblich":          {"de": "Weiblich",                "en": "Female"},
    "divers":            {"de": "Divers",                  "en": "Other"},
    "altersklasse":      {"de": "Altersklasse",            "en": "Age Group"},
    "hauptposition":     {"de": "Hauptposition",           "en": "Main Position"},
    "nebenposition":     {"de": "Nebenposition",           "en": "Secondary Position"},
    "spielbein":         {"de": "Spielbein",               "en": "Preferred Foot"},
    "leistungsniveau":   {"de": "Leistungsniveau",         "en": "Performance Level"},
    "mannschaft":        {"de": "Mannschaft / Verein",     "en": "Team / Club"},
    "trainingsstatus":   {"de": "Trainingsstatus",         "en": "Training Status"},

    # ── Einstellungen ─────────────────────────────────────────────────────────
    "einst_allgemein":   {"de": "⚙️ Allgemein",           "en": "⚙️ General"},
    "einst_zweck":       {"de": "📋 Zweckbestimmung",     "en": "📋 Purpose"},
    "einst_checklisten": {"de": "✅ Checklisten",         "en": "✅ Checklists"},
    "einst_export":      {"de": "💾 Export & Backup",     "en": "💾 Export & Backup"},
    "einst_datenschutz": {"de": "🔒 Datenschutz",        "en": "🔒 Privacy"},
    "einst_sprache":     {"de": "🌐 Sprache",             "en": "🌐 Language"},
    "vereinsname":       {"de": "Vereinsname",             "en": "Club Name"},
    "saison":            {"de": "Aktuelle Saison",         "en": "Current Season"},

    # ── Testprotokoll ─────────────────────────────────────────────────────────
    "spieler":           {"de": "Spieler",                 "en": "Player"},
    "datum":             {"de": "Datum",                   "en": "Date"},
    "ergebnis":          {"de": "Ergebnis",                "en": "Result"},
    "bewertung":         {"de": "Bewertung",               "en": "Rating"},
    "bemerkung":         {"de": "Bemerkung",               "en": "Notes"},
    "alter":             {"de": "Alter",                   "en": "Age"},
    "test":              {"de": "Test",                    "en": "Test"},
    "woche":             {"de": "Woche",                   "en": "Week"},
    "phase":             {"de": "Phase",                   "en": "Phase"},
    "pause":             {"de": "Pause",                   "en": "Rest"},
    "saetze":            {"de": "Sätze",                   "en": "Sets"},
    "wiederholungen":    {"de": "Wiederholungen",          "en": "Reps"},
    "uebung":            {"de": "Übung",                   "en": "Exercise"},
    "bereich":           {"de": "Bereich",                 "en": "Area"},

    # ── Checklisten-UI ────────────────────────────────────────────────────────
    "chk_eigene_punkte": {"de": "Eigene Punkte pro Test", "en": "Custom Checklist Points"},
    "chk_standard_default": {"de": "Standard-Checkliste (alle Tests)", "en": "Default Checklist (all tests)"},
    "chk_kein_coaching": {"de": "Kein Coaching — nur beobachten",     "en": "No coaching — observe only"},
    "chk_abbruch_erklaert": {"de": "Abbruchsignal erklärt",           "en": "Stop signal explained"},

    # ── Status / Ampel ────────────────────────────────────────────────────────
    "sehr_gut":          {"de": "Sehr gut",                "en": "Excellent"},
    "gut":               {"de": "Gut",                     "en": "Good"},
    "mittel":            {"de": "Mittel",                  "en": "Average"},
    "verbesserung":      {"de": "Verbesserungsbedarf",     "en": "Needs improvement"},
    "handlungsbedarf":   {"de": "Handlungsbedarf",         "en": "Action required"},
    "kein_test":         {"de": "Kein Test",               "en": "Not tested"},

    # ── Trainingsplan ─────────────────────────────────────────────────────────
    "plan_erstellen":    {"de": "⚡ Trainingsplan erstellen", "en": "⚡ Generate Training Plan"},
    "plan_laenge":       {"de": "Planlänge",                  "en": "Plan Duration"},
    "wochen":            {"de": "Wochen",                     "en": "Weeks"},
    "haeufigkeit":       {"de": "Häufigkeit",                 "en": "Frequency"},
    "ausfuehrung":       {"de": "Ausführung",                 "en": "Execution"},

    # ── Über die Software ─────────────────────────────────────────────────────
    "ueber_software":    {"de": "Software",                "en": "Software"},
    "ueber_entwickler":  {"de": "Entwickler",              "en": "Developer"},
    "ueber_kontakt":     {"de": "Kontakt",                 "en": "Contact"},
    "ueber_copyright":   {"de": "Copyright",               "en": "Copyright"},
    "ueber_kontaktieren":{"de": "📧 Entwickler kontaktieren","en": "📧 Contact Developer"},
    "urheberrecht":      {"de": "⚖️ Urheberrecht",         "en": "⚖️ Copyright Notice"},
    "version":           {"de": "Version",                 "en": "Version"},

    # ── Fehler / Hinweise ─────────────────────────────────────────────────────
    "kein_spieler":      {"de": "Kein Spieler ausgewählt.","en": "No player selected."},
    "keine_daten":       {"de": "Noch keine Daten vorhanden.", "en": "No data available yet."},
    "gespeichert":       {"de": "✅ Gespeichert.",          "en": "✅ Saved."},
    "fehler":            {"de": "❌ Fehler:",               "en": "❌ Error:"},
}


def t(key: str) -> str:
    """Gibt den übersetzten Text für den aktuellen Sprachcode zurück.
    Falls der Schlüssel nicht gefunden wird, wird der Schlüssel selbst zurückgegeben."""
    lang = st.session_state.get("lang", "de")
    entry = _TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("de", key))


def get_lang() -> str:
    """Gibt den aktuellen Sprachcode zurück."""
    return st.session_state.get("lang", "de")


def set_lang(lang_code: str) -> None:
    """Setzt die aktive Sprache."""
    if lang_code in SPRACHEN:
        st.session_state["lang"] = lang_code
