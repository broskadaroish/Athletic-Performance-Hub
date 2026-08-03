---
name: License system architecture
description: Complete SaaS license system added to Athletik app — files, DB schema, gate logic, Stripe readiness
---

# Lizenzsystem — Architektur

## Neue Dateien
- `license.py` — license types, limits, status calc, enforce_license_gate(), feature_erlaubt()
- `stripe_service.py` — all Stripe API calls wrapped, uses env vars only, no real keys
- `modules/lizenz_page.py` — Vereinsadmin + Superadmin license UI

## DB-Änderungen in database.py
- Neue vereine-Spalten: testphase_bis, lizenz_status, gesperrt, stripe_customer_id, stripe_subscription_id, zahlungsstatus
- Neue Tabelle: rechnungen (billing history)
- Neue Funktionen: verein_registrieren, lizenz_info_laden, lizenz_setzen, verein_sperren, testphase_verlaengern, stripe_ids_setzen, zahlungsstatus_setzen, rechnung_speichern, rechnungen_laden, alle_vereine_lizenz

## Gate-Logik
- enforce_license_gate() called in app.py after session_timeout check
- Superadmin NEVER blocked
- suspended/inactive → Sperr-Seite + st.stop()
- expired → Ablauf-Seite mit Lizenz-Link + st.stop()
- trial warning when ≤7 days remain

## Self-registration
- verein_registrieren() in database.py → creates club + Vereinsadmin + 14d trial
- Registration tab added to Streamlit login page

## Nav additions in app.py
- "💳  Lizenz" for Vereinsadmin
- "💳  Lizenzverwaltung" for Superadmin

## Stripe status
- All code prepared, no real keys; `stripe` pip package NOT yet installed
- Webhook handler in api-server/src/routes/stripe.ts has stub switch/case — DB calls to wire after keys are real
- See LIZENZSYSTEM_BERICHT.md for full go-live checklist

**Why:** Clean separation (license.py ↔ stripe_service.py ↔ lizenz_page.py) makes adding/changing plans trivial — edit LIZENZ_TYPEN dict only.
