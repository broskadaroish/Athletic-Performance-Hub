---
name: Block B1 Superadmin-Guards
description: Serverseitige Guards für letzten-SA-Schutz und Mandantentrennung in database.py; caller-Kontext-Pattern für benutzer_aktualisieren()
---

## Regel
Drei Funktionen in database.py wurden mit serverseitigen Guards versehen.

**Why:** Es gab einen realen Produktionsvorfall, bei dem kein Superadmin mehr in der DB vorhanden war. Die Guards verhindern diesen Zustand dauerhaft.

## benutzer_loeschen() — Guard
- Prüft vor DELETE: wenn Zielbenutzer Superadmin UND COUNT(aktive SAs) ≤ 1 → return (False, Fehlermeldung)
- Guard greift innerhalb der DB-Transaktion (atomar)

## benutzer_aktivieren() — Guard
- Prüft vor UPDATE wenn aktiv=0: wenn Zielbenutzer Superadmin UND COUNT(aktive SAs) ≤ 1 → raise ValueError
- Nur Deaktivierung (aktiv=0) wird geprüft; Aktivierung ist immer erlaubt

## benutzer_aktualisieren() — caller-Kontext-Pattern
Signatur: `benutzer_aktualisieren(..., *, caller_rolle=None, caller_verein_id=None)`

- caller_rolle=None → vertrauenswürdiger interner Aufruf, keine Prüfung (Rückwärtskompatibilität)
- Rolleneskalation: rolle='Superadmin' && caller_rolle != 'Superadmin' → raise PermissionError
- Mandantentrennung: caller_rolle nicht Superadmin → Ziel-verein_id muss == caller_verein_id

## Call Sites aktualisiert
- modules/benutzerverwaltung.py: übergibt caller_rolle=rolle, caller_verein_id=meine_verein_id
- modules/trainerportal.py: übergibt caller_rolle=admin_rolle, caller_verein_id=admin_user.get("verein_id")
- Alle benutzer_aktivieren()-Aufrufe in UI: try/except ValueError → st.error

## How to apply
Bei jedem neuen Aufruf von benutzer_aktualisieren() aus UI-Code: immer caller_rolle + caller_verein_id aus st.session_state["user"] mitgeben. Interner/Migrations-Code kann None lassen.
