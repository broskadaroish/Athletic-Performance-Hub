---
name: Block B2-B8 Hardening
description: Alle technischen Entscheidungen und Fallstricke aus den Blöcken B2–B8 des APH-Hardening-Passes
---

# Block B2–B8 Hardening — Durable Notes

## B2 — Atomare Kundennummern
- UNIQUE partial index: `WHERE kundennummer IS NOT NULL` (SQLite erlaubt mehrere NULLs in UNIQUE-Indexes)
- `_naechste_kundennummer_in_conn(conn)` ist der Helfer für atomare Vergabe innerhalb einer Verbindung
- `kundennummer_vergeben_verein()` und `...benutzer()` nutzen jetzt eine einzige DB-Connection → race-condition-sicher
- Migrations-Guards in try/except: wenn Duplikate vorhanden → kein Absturz, nur stiller Skip

## B3 — Dashboard & Filter
- `dashboard_sa_kpis()` gibt neu: n_kunden_gesamt, n_trial, n_aktive_abos, n_gekuendigt, n_zahlungsproblem
- `kunden_liste_laden()` hat neuen Parameter `filter_zahlungsstatus`
- Für UNION-ALL-Queries: Trainer-Part (benutzer) hat kein `zahlungsstatus` → `NULL AS zahlungsstatus`
- "Trial"-Filter im Accountstatus-Dropdown prüft `lizenz_status == 'trial'`

## B4 — Stripe-Infoblock
- Section E = `_detail_e_stripe(daten)` — nur für Vereinskunden, kein API-Call, nur DB-Felder
- IDs werden auf 12 Zeichen gekürzt + "…"
- cancel_at_period_end aus vereine-Tabelle

## B5 — Fail-closed + Downgrade-Schutz
- `spieler_limit_erreicht()`: spieler-Tabelle hat KEIN `aktiv`-Feld → Query war `WHERE verein_id=? AND aktiv=1` (Exception → fail-closed True) → gefixt auf `WHERE verein_id=?`
- Fail-closed: except-Block gibt `True` zurück (Limit gilt als erreicht)
- Downgrade-Schutz in `_detail_c_lizenz()`: prüft akt. Trainer/Spieler-Anzahl vs. neue Package-Limits; blockiert mit Fehlermeldung wenn Überschreitung; Daten werden NIEMALS gelöscht (nur blockiert)

## B6 — Sperren/Entsperren
- `verein_sperren(verein_id, gesperrt: bool)` — setzt `gesperrt`-Feld (nicht `aktiv`)
- `benutzer_aktivieren(id, 0/1)` — für Benutzer-Sperren
- Kein separates `verein_entsperren()`; stattdessen `verein_sperren(id, False)`

## B7 — Audit-Log
- Neu geloggt: `rechnungsadresse_geaendert` (mit email+ort im Detail-Feld)
- Neu geloggt: `vertragsdaten_geaendert` (mit kstat, kzum, vende)
- Stripe-Abo-Check vor Kundenlöschung: Warning wenn stripe_subscription_id + lizenz_status in (active, trial)
- Stripe-Customer-Hinweis: bleibt in Stripe nach Löschung bestehen — manuelle Prüfung notwendig

## B8 — Testsuite
- Datei: `artifacts/athletik/tools/test_block_b.py`
- 35 Tests, alle PASS
- Nutzt die echte athletik.db (nicht Temp-DB) mit INSERT OR IGNORE für Testdaten mit IDs ≥ 9001
- B1-Regression: deaktiviert Test-SA temporär, prüft Guard auf echtem SA id=1, reaktiviert danach

**Why:** B-Serie ist ein einmaliger Hardening-Pass; die Testsuite ist der Regressionsschutz.
**How to apply:** Bei späteren Änderungen an license.py/database.py immer `python3 tools/test_block_b.py` laufen lassen.
