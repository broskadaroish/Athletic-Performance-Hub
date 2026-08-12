---
name: Auth Schritt-1 overhaul
description: Full implementation of SCHRITT-1 spec — auth/registration overhaul with email verification, sessions, billing addresses, SMTP, password reset, username reminder.
---

## What was implemented

All 14 sections of the SCHRITT-1 spec are implemented:

1. **Registration extended** — 5-tab login gate (Anmelden, Verein reg, Trainer reg, Passwort vergessen, Benutzername vergessen). Both registration forms have benutzername field + full Rechnungsadresse expander (Firma, Vor-/Nachname, Straße, Hausnummer, PLZ, Ort, Land, Rechnungs-Email, Telefon, USt-ID).

2. **Email verification** — `email_verifiziert` column + `email_token` columns in benutzer. DB functions: `email_token_erzeugen`, `email_token_resend_erlaubt` (5min rate limit), `email_token_validieren` (invalidates after first use). Verified via `?verify=TOKEN` URL param.

3. **IONOS SMTP** — `email_service.py` with SSL/TLS port 465. Env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SUPPORT_EMAIL`. SMTP_PASSWORD never logged.

4. **Superadmin test-mail** — Bottom of benutzerverwaltung.py; error messages never expose SMTP_PASSWORD or raw auth errors.

5. **normalize_email** — `database.normalize_email(email)` = `email.strip().lower()`. Called in: `benutzer_speichern`, `verein_registrieren`, `trainer_registrieren`, `benutzer_aktualisieren`, `benutzer_sperre_pruefen` (via `normalize_email`), `pw_reset_token_erzeugen`, `benutzername_reminder_laden`. Also in auth.py login().

6. **Session persistence** — `sessions` table (token, benutzer_id, erstellt_am, letzte_aktivitaet, ablauf_am, aktiv). DB functions: `session_erstellen`, `session_validieren`, `session_beenden`, `session_bereinigen`. Cookie: `ath_sid` via `streamlit-cookies-controller`. Env vars: `SESSION_IDLE_TIMEOUT` (default 3600s), `SESSION_MAX_LIFETIME` (default 86400s).

7. **"sündigen" text** — Not found. Only `kündigen` exists in lizenz_page.py:290 (correct German). No fix needed.

8. **Password reset** — `pw_reset_token_erzeugen` (1h expiry), `pw_reset_token_validieren`, `pw_reset_anwenden` (invalidates token after use). URL flow: `?reset=TOKEN`. No plaintext password in email.

9. **Username reminder** — `benutzername_reminder_laden(email)` — only sends if email is verified + account active. `send_username_reminder()` in email_service.py.

10. **Password storage** — Already PBKDF2-SHA256 + salt (260k iterations). Legacy SHA-256 auto-upgraded on login. No change needed.

11. **Superadmin auth status** — Per-user expander in benutzerverwaltung.py shows: E-Mail bestätigt (✅/❌), Registriert am, Letzter Login, Account-Status, Lizenz-Status. Also "Bestätigungs-E-Mail senden" button for unverified accounts.

12. **Player name translation** — i18n.py `t()` only handles fixed UI string keys. Player names never passed through it. No fix needed.

13. **Tests** — Manual checklist of 22 scenarios provided to user.

14. **Report** — 10 spec questions answered.

## Key DB migrations added

- `benutzer`: benutzername, email_verifiziert, email_token, email_token_ablauf, email_token_gesendet_am, pw_reset_token, pw_reset_ablauf
- `sessions`: new table
- `rechnungsadressen`: new table
- Existing users migrated to email_verifiziert=1 (no lockout)

## Critical rules

**Why:** normalize_email must be called EXACTLY the same way everywhere (only strip+lower, no dot removal, no +alias removal) to prevent split-account bugs.

**How to apply:** Always call `from database import normalize_email` and use `normalize_email(input)` before any DB lookup on email. Never use `email.lower()` directly in new code.

**Session cookie:** `ath_sid` is set with `secure=True, same_site="Strict"` — Streamlit Cloud / Replit proxy breaks this if not HTTPS. If cookie doesn't persist, check that the app is served over HTTPS.

**Admin-created accounts** always get `email_verifiziert=1` (keyword-only param to `benutzer_speichern`). Self-registrations get `email_verifiziert=0`.

**SMTP_PASSWORD** must NEVER appear in logs, error messages, or Streamlit UI. email_service.py enforces this — catch `RuntimeError` for missing password, catch generic `Exception` for SMTP errors and show only a generic message.
