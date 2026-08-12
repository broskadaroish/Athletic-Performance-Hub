---
name: SCHRITT 10 Rechtliche Seiten
description: Impressum, Datenschutz, AGB — Architektur, E-Mail-Austausch, Zugangswege
---

## Rechtliche Seiten — Architektur

### Datei
`artifacts/athletik/modules/legal_page.py` — enthält alle drei Funktionen:
- `page_impressum()` — Impressum gemäß § 5 DDG
- `page_datenschutz()` — Datenschutzerklärung (28 Abschnitte, DSGVO)
- `page_agb()` — AGB/Nutzungsbedingungen (28 Abschnitte)

### Zugangswege

**Pre-Login (ohne Anmeldung):**
- Login-Seite zeigt 3 Buttons: Impressum · Datenschutz · AGB
- Buttons setzen `st.session_state["_legal_show"] = "impressum"|"datenschutz"|"agb"`
- Handler in app.py VOR dem `if "user" not in st.session_state:` Block
- Handler rendert Seite + "← Zurück"-Button, dann `st.stop()`

**Nach Login (in der App):**
- Section "ℹ️  Über" ruft `page_ueber_software()` auf
- Dort Sub-Nav: Info | Impressum | Datenschutz | AGB (Buttons)
- Session-Key: `_ueber_sub` ∈ {info, impressum, datenschutz, agb}
- Sidebar-Footer enthält 3 Buttons die `nav_section` + `_ueber_sub` setzen

### E-Mail-Trennung
- `support@aphsystem.de` — sichtbar, für Support/Datenschutz/Anfragen
- `noreply@aphsystem.de` — nur System-E-Mails, SMTP-Logik NICHT geändert

### Private E-Mail vollständig entfernt
`Broska_daroish@hotmail.de` entfernt aus:
- `app.py` (APP_EMAIL konstante)
- `modules/lizenz_page.py` (Kontakt-Text beim Paket-Wechsel)
- `modules/mein_vertrag.py` (Admin-Benachrichtigung Fallback)

**Why:** Spec §4 — private E-Mail darf nicht als Support/Kontakt erscheinen
**How to apply:** Bei neuen Kontakt-Feldern immer support@aphsystem.de verwenden, nie hotmail

## Sidebar-Footer Impressum/Datenschutz/AGB — ENTFERNT

Die drei Sidebar-Buttons (Impressum, Datenschutz, AGB) aus der EINGELOGGTEN Sidebar wurden entfernt.

**Begründung:** Buttons setzten `st.session_state["nav_section"]` NACH der Widget-Instanziierung
→ StreamlitAPIException. Außerdem redundant, da die Seiten unter "ℹ️ Über" erreichbar sind.

**nav_section-Regel:** NIE `st.session_state["nav_section"]` direkt nach Widget-Erstellung schreiben.
Stattdessen `_nav_goto`-Pattern: `st.session_state["_nav_goto"] = target; st.rerun()`.
Handler bei Zeile ~9959 liest `_nav_goto` VOR Widget-Erstellung bei Zeile ~9979.

**Login-Seite:** Impressum/Datenschutz/AGB bleiben auf der öffentlichen Login-Seite (pre-login Zugang).
