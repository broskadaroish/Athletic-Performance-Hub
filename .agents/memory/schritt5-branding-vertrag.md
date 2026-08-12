---
name: Branding & Vertrag Schritt-5
description: SCHRITT-5 Implementierung — Branding-Update, Mein Vertrag Seite, Online-Kündigungsflow, Superadmin-Kündigungen-Tab
---

## Was wurde gemacht

**Branding:** APP_NAME überall auf "Athletic Performance Hub" umgestellt (7 Stellen in app.py + lizenz_page.py). support@brucefootball.de → support@aphsystem.de.

**DB-Migration:** `kuendigung_grund TEXT` + `kuendigung_bestaetigung_am TEXT` zu **beiden** Tabellen (benutzer + vereine) via _migrate_db() hinzugefügt.

**Neue DB-Funktionen (database.py):**
- `kuendigung_einreichen(entity_id, ist_verein, grund)` → (bool, iso_str)
- `kuendigung_bestaetigen(entity_id, ist_verein, vertragsende, status)`
- `kuendigung_liste_laden(status_filter)` → beide Tabellen UNION'd

**Neues Modul:** `modules/mein_vertrag.py` → page_mein_vertrag()
- Read-only Vertragsfelder (Kundennummer, Paket, Preis aus LIZENZ_TYPEN, Vertragsbeginn/-ende, Status-Badge, Kündigungsstatus)
- 3-stufiger Kündigungsflow: Info → Grund+Bestätigung → Bestätigungsseite
- Sendet send_kuendigung_bestaetigung() E-Mail, fehlertolerante Ausführung

**Email:** `send_kuendigung_bestaetigung()` in email_service.py mit HTML+plain-text

**Navigation (app.py):**
- "📋  Mein Vertrag" im Nav für Trainer + Vereinsadmin
- Import + Section-Routing hinzugefügt

**Kundenverwaltung:** Tab-Split "Kunden" | "Kündigungen"; `_kuendigungen_uebersicht()` mit Filter, Detail-Ansicht und Bestätigungs/Beendet-Buttons für Superadmin

## Wichtige Constraints
- Ist-Verein-Erkennung: `rolle == "Vereinsadmin"` → vereine-Tabelle, sonst benutzer-Tabelle
- entity_id für Vereinsadmin = `user["verein_id"]`, für Trainer = `user["id"]`
- Preis-Lookup über `license.LIZENZ_TYPEN` (try/except falls nicht verfügbar)
- Doppelkündigung wird in kuendigung_einreichen() geblockt — gibt (False, "bereits_gekuendigt") zurück
