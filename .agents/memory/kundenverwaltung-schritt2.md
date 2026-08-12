---
name: Kundenverwaltung Schritt-2
description: What was built for SCHRITT 2 (Superadmin Kundenverwaltung) and key constraints
---

## What was built

- **DB migration**: `vereine` gets `kundennummer TEXT`, `vertragsbeginn`, `vertragsende`, `kuendigung_eingegangen`, `gekuendigt_zum`, `kuendigungsstatus`. `benutzer` gets `kundennummer TEXT`. New `audit_log` table.
- **Kundennummer format**: `APH-000001` — auto-assigned at migration time (existing records) and at registration time via `kundennummer_vergeben_verein()` / `kundennummer_vergeben_benutzer()`. `naechste_kundennummer()` reads MAX from both tables.
- **audit_log**: `(id, benutzer_id, aktion, details, superadmin_id, erstellt_am)` — never stores passwords/tokens. `audit_log_eintragen()` silently swallows errors (must not block main operations).
- **New DB functions**: `kunden_liste_laden()`, `kunde_vollstaendig_laden()`, `superadmin_email_aendern()`, `superadmin_benutzername_aendern()`, `vertragsfelder_setzen()`, `kundenstamm_aendern()`.
- **modules/kundenverwaltung.py**: `page_kundenverwaltung()` — list view with KPI bar + search/filter + card list; detail view with 4 expanders (A: Kundenkonto, B: Rechnungsadresse, C: Lizenz/Paket, D: Vertrag) + audit history. Session state key: `kunden_auswahl = (verein_id, benutzer_id)`.
- **app.py**: Nav `👥  Kundenverwaltung` for Superadmin only; route `elif section == "👥  Kundenverwaltung": page_kundenverwaltung()`.
- **Login deaktiviert**: `auth.py` now queries without `aktiv=1` filter, returns `{"konto_deaktiviert": True}` if `aktiv=0`. `app.py` login gate shows "⛔ Dein Konto ist derzeit deaktiviert. Bitte kontaktiere den Support unter support@aphsystem.de."

## Critical constraints (do not break)
- `LIZENZ_TYPEN` in `license.py` — packages BASIC/PRO with exact prices (`9.90/mo`, `99/yr`, `24.90/mo`, `249/yr`) must NEVER be changed.
- Paketwechsel: `lizenz_setzen()` only — uses existing function, never direct SQL UPDATE on lizenztyp outside it.
- `audit_log_eintragen()` must never raise — it wraps in try/except.
- E-Mail change always invalidates `email_verifiziert` and creates a new verification token.

**Why:**
SCHRITT-2 spec required all of the above for a production SaaS customer management system.
