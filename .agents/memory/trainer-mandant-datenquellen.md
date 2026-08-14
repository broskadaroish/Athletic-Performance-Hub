---
name: Trainer mit technischem Mandant — Datenquellen-Regeln
description: Welche Tabelle ist für welche Felder bei Einzeltrainer-Kunden (technischer Mandant) autoritativ.
---

# Trainer mit technischem Mandant — Datenquellen

## Regel
Für Einzeltrainer, die einen technischen Mandanten haben (`vereine.ist_technischer_mandant = 1`), gilt:

| Feld | Quelle |
|---|---|
| lizenztyp, lizenz_status, lizenz_bis, testphase_bis | `vereine` |
| vertragsbeginn, vertragsende, kuendigungsstatus, gekuendigt_zum, kuendigung_eingegangen | `vereine` |
| zahlungsstatus, abo_intervall, stripe_customer_id, stripe_subscription_id | `vereine` |
| cancel_at_period_end, subscription_current_period_end | `vereine` |
| **kundennummer** (sichtbar / fachlich) | **`benutzer`** |
| vorname, nachname, email, benutzername, rolle, aktiv | `benutzer` |

## Warum
`benutzer.lizenztyp` und `benutzer.kundennummer` für Trainer können Legacy-Altwerte enthalten (z. B. "BASIC" statt "TRAINER_BASIC", oder eine interne Mandanten-Kundennummer). Die führende Quelle ist immer `vereine` (technischer Mandant) — außer bei der sichtbaren Kundennummer, die IMMER aus `benutzer.kundennummer` kommt.

## Umsetzung (Stand nach Hotfixes)

### `database.py` — `kunden_liste_laden()`
Trainer-Branch: `LEFT JOIN vereine v2` mit `COALESCE(v2.field, b.field)` für alle Vertragsfelder.
`verein_id = NULL` bleibt (Detail-Load läuft über `benutzer_id`).

### `database.py` — `kunde_vollstaendig_laden(benutzer_id=...)`
Für Trainer mit `verein_id`: `v = _v_raw` (nicht mehr `v = None`).
`v.get("ist_technischer_mandant") == 1` zeigt der UI an, dass es ein Trainer-Konto ist.

### `modules/kundenverwaltung.py` — `_detail_c_lizenz()`, `_detail_d_vertrag()`
```python
ist_verein  = bool(v) and not v.get("ist_technischer_mandant")
hat_mandant = bool(v) and bool(v.get("ist_technischer_mandant"))
src = v if (ist_verein or hat_mandant) else b
entity_id = v["id"] if (ist_verein or hat_mandant) else b["id"]
```
Schreib-Handler: `lizenz_setzen(v["id"])` / `vertragsfelder_setzen(v["id"])` für `ist_verein or hat_mandant`.

### `modules/mein_vertrag.py` — `_laden()`
Nach `SELECT * FROM vereine`: wenn `ist_technischer_mandant`, `data["kundennummer"] = user.get("kundennummer")` (aus benutzer).

### `modules/mein_vertrag.py` — `_kunde_detail()`, `_detail_gefahrenbereich()`
`kn = b.get("kundennummer") or ...` wenn `v.get("ist_technischer_mandant")`.

## Vertragsende-Datumslogik (mein_vertrag.py)
Priorität an BEIDEN Stellen (Bestätigungsseite + `_sende_email`):
1. `gekuendigt_zum`
2. `subscription_current_period_end`
3. `testphase_bis` — nur wenn `lizenz_status == "trial"`
4. Fallbacktext

## SQLite-UNION ORDER BY
Bei UNION ALL mit JOIN im zweiten Branch: `ORDER BY kundennummer` schlägt fehl wenn der erste Branch `v.kundennummer` ohne expliziten Alias hat.
**Fix:** Immer `v.kundennummer AS kundennummer` in der ersten SELECT-Zeile verwenden.
