---
name: SCHRITT 9 Datensicherheit
description: Datensicherheit, Persistenz, Mandantentrennung — was implementiert wurde und warum
---

## Bereits vorhanden (keine Änderung nötig)
- `init_db()` — rein idempotent (CREATE TABLE IF NOT EXISTS, kein DROP)
- `*.db` in `.gitignore` ausgeschlossen
- `PRAGMA foreign_keys = ON` in `get_conn()`
- `spieler_laden()` — rollenbezogen gefiltert (verein_id/trainer_id)
- `db_komplett_zuruecksetzen()` — Checkbox + Eingabe "RESET" als Doppelschutz
- Session-State isoliert über `st.session_state`
- Backup-Tool: `tools/backup.py` (SQLite Online-Backup-API, Integrität-Check, Retention)

## Neu implementiert

### `database.py` (Ende der Datei)
- `spieler_mandant_pruefen(spieler_id, benutzer_id, rolle, verein_id) → bool`
  — IDOR-Schutz; Superadmin: immer True; Vereinsadmin: verein_id-Match; Trainer: trainer_id oder verein_id-Match
- `backup_status_laden() → dict`
  — DB-Erreichbarkeit prüft Datei-Existenz VOR SQLite-Connect (verhindert auto-create); liest aus `uploads/backups/`, gibt Anzahl/letztes Datum/Größe zurück
- `db_backup_erstellen() → (bool, str)`
  — ruft `tools/backup.py` via subprocess auf; kein Import-Coupling; Timeout 120s

### `lizenz_scheduler.py`
- `_backup_ausfuehren()` — neue Funktion, try/except, non-blocking
- `_scheduler_loop()` — ruft `_backup_ausfuehren()` nach `lizenz_check_ausfuehren()` auf; täglich

### `app.py`
- Imports: `backup_status_laden, db_backup_erstellen, spieler_mandant_pruefen`
- Ersetzt spärlichen "### Datenbank"-Block in Export-Backup-Expander durch vollständiges "### 🛡️ Datensicherheit"-Dashboard: 3-KPI-Zeile (DB-Status, letztes Backup, Anzahl), manueller Backup-Button, Backup-Verlauf-Liste

## Schlüssel-Quirks
- `backup_status_laden()` prüft `_P(DB_PATH).exists()` bevor SQLite-Connect — sonst würde SQLite eine neue leere Datei anlegen und `db_erreichbar=True` liefern, obwohl keine echte DB da ist
- `spieler` Tabelle hat kein `aktiv`-Feld (nur `name, verein_id, trainer_id` als Minimalfelder im Test-INSERT)
- Tests in `tests/test_schritt9_datensicherheit.py` — 18 Tests, alle grün

**Why:** IDOR zwischen Mandanten ist nur über spieler_by_id() möglich, da spieler_laden() bereits gefiltert ist — aber defensive Überprüfung schützt falls zukünftig andere Einstiegspunkte entstehen.
