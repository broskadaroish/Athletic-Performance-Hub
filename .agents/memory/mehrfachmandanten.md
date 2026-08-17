---
name: Mehrfachmandanten-Architektur
description: trainer_mandanten Tabelle, Schutzregeln, Mandant-Auswahlscreen, DB-Funktionen
---

# Mehrfachmandanten-Architektur

## Regel
`trainer_mandanten` ist additiv hinzugefügt. `benutzer.verein_id` wird **niemals** entfernt oder NULL gesetzt — es ist ein Legacy-FK den Dutzende Queries nutzen. `trainer_mandanten` ergänzt es, ersetzt es nicht.

**Why:** Rückwärtskompatibilität. Alle bestehenden Filterlöger (spieler.verein_id, trainer_id etc.) laufen über benutzer.verein_id. Kein Regressionrisiko durch additive Erweiterung.

## Tabelle
```sql
trainer_mandanten(id, benutzer_id FK→benutzer, verein_id FK→vereine,
                  rolle_im_verein TEXT DEFAULT 'Trainer',
                  aktiv INT DEFAULT 1, beigetreten_am TEXT,
                  UNIQUE(benutzer_id, verein_id))
```

## Migration (idempotent)
`INSERT OR IGNORE INTO trainer_mandanten ... SELECT id, verein_id, rolle, 1, ... FROM benutzer WHERE verein_id IS NOT NULL AND rolle NOT IN ('Superadmin')`

Läuft jedes Mal in `_migrate_multitenant()` — kein Marker-Gate nötig, da INSERT OR IGNORE idempotent ist. `trainer_verein_beitreten()` fügt nach dem INSERT in benutzer auch einen Eintrag in trainer_mandanten ein.

## DB-Funktionen (database.py)
- `trainer_mandanten_fuer_benutzer(bid)` → aktive Mandanten des Benutzers
- `trainer_mandant_hinzufuegen(bid, vid, rolle)` → add/reactivate (ON CONFLICT DO UPDATE)
- `trainer_mandant_entfernen(bid, vid, *, caller_rolle, caller_verein_id)` → setzt aktiv=0; Vereinsadmin nur eigener Verein, sonst PermissionError
- `trainer_mandanten_fuer_verein(vid)` → alle aktiven Trainer eines Vereins
- `alle_trainer_mit_mandanten()` → Superadmin-Übersicht mit GROUP_CONCAT
- `benutzer_email_existiert(email)` → bool, case-insensitiv

## Atomare Inserts (kein init_db()-Restart nötig)
`benutzer_speichern()` und `trainer_verein_beitreten()` fügen nach dem benutzer-INSERT atomisch einen trainer_mandanten-Eintrag ein (INSERT OR IGNORE). Gilt für rolle IN ('Trainer', 'Vereinsadmin') mit verein_id != NULL. Superadmin und verein_id=NULL: kein Eintrag.

## Mandant-Auswahlscreen (app.py)
Eingefügt nach `enforce_license_gate()`, vor dem Zweckbestimmungs-Gate.  
Nur für `rolle == "Trainer"` mit mehreren echten Mandanten (nicht technischer Mandant).  
Session-State-Schlüssel: `_mandant_gewaehlt` (bool), `_aktiver_mandant_id` (int).  
"Mandant wechseln"-Button in der Sidebar löscht beide Keys → Auswahlscreen erscheint erneut.

## Sidebar-Wechsel
Nur sichtbar wenn `_aktiver_mandant_id` gesetzt und `_mandant_gewaehlt=True` und Trainer hat ≥2 echte Mandanten. Resettet `_mandant_gewaehlt` und `_aktiver_mandant_id`.

## Beitrittsformular (app.py)
E-Mail-Check vor `trainer_verein_beitreten()`: wenn Email existiert → `st.info` mit Hinweis zum Login statt Fehlermeldung von der DB. Nutzt `benutzer_email_existiert()`.

## Trainerportal (modules/trainerportal.py)
- Trainer-Karte: zeigt Mandanten-Badges wenn Trainer in >1 echtem Verein
- Edit-Form: neuer Tab "🏢 Mandanten" — zeigt alle aktiven Mandanten, Entfernen-Button für Vereinsadmin/Superadmin, Hinzufügen-Dropdown für Superadmin
- page_mein_profil(): neuer Abschnitt "Meine Vereine" mit Wechseln-Button

## Schutzregeln (nicht verletzen)
1. Kein UPDATE/NULL auf benutzer.verein_id
2. Alle DB-Migrationen idempotent (INSERT OR IGNORE)
3. Stripe komplett unberührt
4. trainer_mandant_entfernen() setzt aktiv=0, löscht NIE — Spieler/Tests bleiben beim Verein

## How to apply
Bei allen neuen Filtern: prüfe ob `trainer_mandanten` genutzt werden muss (z.B. "alle Trainer eines Vereins holen"). Bei benutzer.verein_id-Abfragen: kein Regressionrisiko — Feld bleibt immer gesetzt.
