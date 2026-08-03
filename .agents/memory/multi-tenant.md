---
name: Multi-Tenant System
description: Vollständige Multi-Tenant-Implementierung (Superadmin/Vereinsadmin/Trainer) — Architekturentscheidungen und Besonderheiten
---

## Kernarchitektur

- **3 Rollen**: Superadmin (alle Vereine), Vereinsadmin (ein Verein), Trainer (eigene Spieler)
- **Datentrennung**: `spieler.trainer_id` + `spieler.verein_id`; `spieler_laden()` filtert nach Rolle
- **Session**: `st.session_state["user"]` ist nach Login-Gate immer vorhanden; `_akt_user()` als sicherer Accessor

## Login-Gate

- Liegt NACH `st.set_page_config` (Streamlit-Pflicht) und NACH CSS-Injection, aber VOR Zweckbestimmungs-Gate
- Erkennt Erstinstallation (keine Benutzer in DB) → zeigt Setup-Formular statt Login
- `benutzer_laden()` wird direkt im Login-Gate aufgerufen (kein `_akt_user()` da noch kein User)

## Datenbankfunktionen

- `spieler_laden(benutzer_id, rolle, verein_id)` — rollenbasierte Filterung
- `spieler_speichern(..., trainer_id=None, verein_id=None)` — neue optionale Parameter
- `_migrate_multitenant()` — idempotent; legt vereine/benutzer-Tabellen an; wird in `init_db()` aufgerufen
- Passwörter: SHA-256 in `database._pw_hash()` und `auth.hash_password()` (identisch)

## Dateien

- `auth.py` — Login-Funktion (direkte DB-Verbindung via DB_PATH, kein get_conn())
- `modules/benutzerverwaltung.py` — Vereinsadmin sieht nur eigenen Verein
- `modules/vereine.py` — nur Superadmin

## Bestehende Daten (wichtig!)

Nach `_migrate_multitenant()` haben bestehende Spieler `trainer_id=NULL, verein_id=NULL`.
**Problem**: Trainer sehen NULL-Spieler nicht (Filter nach `trainer_id=benutzer_id`).
**Workaround**: `_akt_user()` liefert `rolle="Superadmin"` als Fallback → Superadmin sieht alles.
**Echte Lösung**: Nach Erstanmeldung des Superadmins alle NULL-Spieler dem Standard-Verein zuweisen (noch nicht implementiert).

**Why:** Datenisolation ist das Kern-Sicherheitsversprechen des Multi-Tenant-Systems.
**How to apply:** Jede neue Spieler-Abfrage muss über `spieler_laden()` laufen, nie direktes SQL ohne Rollenfilter.
