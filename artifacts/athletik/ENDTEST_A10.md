# A10 – Sandbox End-to-End Testplan

**Erstellt:** 2026-08-14  
**System:** Athletic Performance Hub (APH)  
**Umgebung:** Stripe Test-Modus (sk_test_… / whsec_…)  
**Datenbank:** SQLite — `artifacts/athletik/athletik.db`  
**Webhook-Endpunkt:** `https://aphsystem.de/api/stripe/webhook`  
**Scope:** Sandbox only — kein Live-Modus, keine echten Zahlungen

---

## Statusmodell-Referenz

| `lizenz_status` (DB) | Bedeutung |
|---|---|
| `trial` | Aktive 30-Tage-Testphase (kein Stripe-Abo nötig) |
| `active` | Bezahlte, aktive Lizenz |
| `cancelled` | Abo gekündigt, läuft noch bis `lizenz_bis` |
| `beendet` | Abo vollständig beendet — Zugang gesperrt, Daten bleiben |
| `expired` | Testphase oder Lizenz abgelaufen (on-the-fly berechnet) |
| `suspended` | Manuell gesperrt durch Superadmin |

| `zahlungsstatus` (DB) | Bedeutung |
|---|---|
| `offen` | Noch keine Zahlung eingegangen |
| `zahlungsmethode_hinterlegt` | Checkout abgeschlossen, Trial läuft |
| `bezahlt` | Zahlung bestätigt (invoice.paid) |
| `fehlgeschlagen` | Letzte Zahlung fehlgeschlagen |
| `beendet` | Abo beendet (subscription.deleted) |

---

## Pakete & Preise (Test-Modus)

| Paket | Typ | Trainer | Spieler | Monat | Jahr |
|---|---|---|---|---|---|
| TRAINER_BASIC | Einzeltrainer | 1 | 20 | 9,99 € | 99,00 € |
| TRAINER_PRO | Einzeltrainer | 1 | unbegrenzt | 14,99 € | 149,00 € |
| VEREIN_BASIC | Verein | 2 | 50 | 24,99 € | 249,00 € |
| VEREIN_PRO | Verein | 15 | unbegrenzt | 39,99 € | 399,00 € |

Stripe Price-IDs werden über Env-Vars konfiguriert:  
`STRIPE_PRICE_TRAINER_BASIC_MONAT`, `STRIPE_PRICE_TRAINER_BASIC_YEARLY`, usw.

---

## Voraussetzungen (alle Tests)

1. API-Server läuft: `pnpm --filter @workspace/api-server run dev`
2. Athletik-App läuft: `cd artifacts/athletik && bash start.sh`
3. Stripe CLI installiert: `stripe --version`
4. Stripe CLI im Test-Modus angemeldet: `stripe login`
5. Alle `STRIPE_PRICE_*`-Env-Vars auf gültige Stripe-Test-Price-IDs gesetzt
6. `STRIPE_SECRET_KEY=sk_test_…` und `STRIPE_WEBHOOK_SECRET=whsec_…` gesetzt
7. Stripe CLI Webhook-Forwarding aktiv:
   ```bash
   stripe listen --forward-to https://aphsystem.de/api/stripe/webhook
   ```
   > Den ausgegebenen `whsec_…`-Wert als `STRIPE_WEBHOOK_SECRET` setzen.

---

## SQL-Hilfsfunktion

```bash
# Abkürzung für alle DB-Queries in diesem Dokument:
alias aph_sql='sqlite3 artifacts/athletik/athletik.db'
```

---

## Tests 1–4: Registrierung aller vier Pakete

---

### TEST-001: Registrierung TRAINER_BASIC

**Testnummer:** 001  
**Name:** Neuregistrierung — Paket TRAINER_BASIC (Einzeltrainer Basic)  
**Kategorie:** Registrierung

**Voraussetzungen:**
- E-Mail-Adresse noch nicht in der DB vorhanden
- Streamlit-App erreichbar (Login-Seite sichtbar)

**Testschritte:**

1. Login-Seite öffnen → Tab „Registrieren"
2. Formular ausfüllen:
   - Vereins-/Trainerbezeichnung: `Test Trainer Basic`
   - E-Mail: `test.trainerbasic@sandbox.local`
   - Passwort: `Test1234!`
   - Paket: `TRAINER_BASIC`
3. Absenden

**Erwartetes Ergebnis:**

```sql
SELECT id, name, lizenztyp, lizenz_status, testphase_bis, max_trainer, max_spieler
FROM vereine WHERE name = 'Test Trainer Basic';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `TRAINER_BASIC` |
| `lizenz_status` | `trial` |
| `testphase_bis` | Datum = heute + 30 Tage |
| `max_trainer` | `1` |
| `max_spieler` | `20` |

UI zeigt: Willkommensmeldung, Dashboard erreichbar, Testphase-Banner sichtbar.

**Pass/Fail:** ✅ Pass wenn alle DB-Werte korrekt und UI zugänglich. ❌ Fail sonst.

---

### TEST-002: Registrierung TRAINER_PRO

**Testnummer:** 002  
**Name:** Neuregistrierung — Paket TRAINER_PRO (Einzeltrainer Pro)  
**Kategorie:** Registrierung

**Voraussetzungen:** E-Mail `test.trainerpro@sandbox.local` noch nicht vorhanden.

**Testschritte:**

1. Login-Seite → Tab „Registrieren"
2. Paket: `TRAINER_PRO`, E-Mail: `test.trainerpro@sandbox.local`
3. Absenden

**Erwartetes Ergebnis:**

```sql
SELECT lizenztyp, lizenz_status, testphase_bis, max_trainer, max_spieler
FROM vereine WHERE name LIKE '%TRAINER PRO%' OR lizenztyp='TRAINER_PRO'
ORDER BY id DESC LIMIT 1;
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `TRAINER_PRO` |
| `lizenz_status` | `trial` |
| `max_trainer` | `1` |
| `max_spieler` | `NULL` (unbegrenzt) |

**Pass/Fail:** ✅ Pass wenn `max_spieler IS NULL` und `lizenz_status='trial'`.

---

### TEST-003: Registrierung VEREIN_BASIC

**Testnummer:** 003  
**Name:** Neuregistrierung — Paket VEREIN_BASIC (Verein Basic)  
**Kategorie:** Registrierung

**Testschritte:**

1. Login-Seite → Tab „Registrieren"
2. Paket: `VEREIN_BASIC`, E-Mail: `test.vereinbasic@sandbox.local`
3. Absenden

**Erwartetes Ergebnis:**

```sql
SELECT lizenztyp, lizenz_status, max_trainer, max_spieler
FROM vereine WHERE lizenztyp='VEREIN_BASIC' ORDER BY id DESC LIMIT 1;
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `VEREIN_BASIC` |
| `max_trainer` | `2` |
| `max_spieler` | `50` |

**Pass/Fail:** ✅ Pass wenn alle Limits korrekt gesetzt.

---

### TEST-004: Registrierung VEREIN_PRO

**Testnummer:** 004  
**Name:** Neuregistrierung — Paket VEREIN_PRO (Verein Pro)  
**Kategorie:** Registrierung

**Testschritte:**

1. Login-Seite → Tab „Registrieren"
2. Paket: `VEREIN_PRO`, E-Mail: `test.vereinpro@sandbox.local`
3. Absenden

**Erwartetes Ergebnis:**

```sql
SELECT lizenztyp, lizenz_status, max_trainer, max_spieler
FROM vereine WHERE lizenztyp='VEREIN_PRO' ORDER BY id DESC LIMIT 1;
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `VEREIN_PRO` |
| `max_trainer` | `15` |
| `max_spieler` | `NULL` (unbegrenzt) |

**Pass/Fail:** ✅ Pass wenn `max_trainer=15` und `max_spieler IS NULL`.

---

## Tests 5–7: Checkout-Szenarien

---

### TEST-005: Checkout abbrechen

**Testnummer:** 005  
**Name:** Stripe Checkout — Abbruch durch Nutzer  
**Kategorie:** Checkout

**Voraussetzungen:**
- Testverein aus TEST-001 eingeloggt (Trial-Status)
- Lizenz-Seite erreichbar (💳 Lizenz im Menü)

**Testschritte:**

1. Als `test.trainerbasic@sandbox.local` einloggen
2. Navigation: „💳 Lizenz" → Upgrade-Button klicken
3. Stripe Checkout-Seite öffnet sich
4. Auf „← Zurück" / „Abbrechen" klicken (oder Browser-Back)
5. App zeigt `cancel_url`-Seite oder Dashboard

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, stripe_customer_id, stripe_subscription_id
FROM vereine WHERE id = <verein_id>;
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `trial` (unverändert) |
| `stripe_customer_id` | `NULL` oder unverändert |

Kein `checkout.session.completed`-Event in Stripe Logs.  
HTTP-Status der `cancel_url`: `200`.

**Pass/Fail:** ✅ Pass wenn `lizenz_status='trial'` und keine DB-Änderung.

---

### TEST-006: Checkout erfolgreich — Testkarte

**Testnummer:** 006  
**Name:** Stripe Checkout — erfolgreiche Zahlung mit Testkarte 4242  
**Kategorie:** Checkout

**Voraussetzungen:** Testverein aus TEST-001 eingeloggt.

**Testschritte:**

1. Lizenz-Seite → „Upgrade auf TRAINER_BASIC monatlich" klicken
2. Stripe Checkout: Kreditkarte `4242 4242 4242 4242`, Ablauf `12/34`, CVC `123`
3. „Jetzt zahlen" klicken
4. Stripe leitet zu `success_url` weiter

**Stripe CLI beobachten:**
```bash
# Stripe CLI zeigt folgende Events (in dieser Reihenfolge):
# checkout.session.completed
# customer.subscription.created
# invoice.paid  (0 € Trial-Invoice)
```

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, zahlungsstatus, stripe_customer_id, stripe_subscription_id,
       lizenztyp, abo_intervall, vertragsbeginn
FROM vereine WHERE id = <verein_id>;
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `trial` (Trial läuft noch) |
| `zahlungsstatus` | `zahlungsmethode_hinterlegt` |
| `stripe_customer_id` | `cus_…` (nicht leer) |
| `stripe_subscription_id` | `sub_…` (nicht leer) |
| `lizenztyp` | `TRAINER_BASIC` |
| `abo_intervall` | `monat` |
| `vertragsbeginn` | heutiges Datum |

API-Server Response: `HTTP 200 {"received": true}` für alle drei Events.

**Pass/Fail:** ✅ Pass wenn alle drei Events verarbeitet und DB-Werte korrekt.

---

### TEST-007: Stripe-Rückkehr ohne gültigen Session-Cookie

**Testnummer:** 007  
**Name:** Checkout-Rückkehr ohne Login-Session — kein automatischer Login  
**Kategorie:** Checkout / Sicherheit

**Voraussetzungen:** `success_url` bekannt (enthält `?checkout=success&session_id=...`).

**Testschritte:**

1. Browser-Cookies löschen (Incognito-Fenster öffnen)
2. `success_url` direkt im Browser aufrufen (ohne aktive Session)

**Erwartetes Ergebnis:**

- App zeigt Login-Seite (kein automatischer Login)
- Kein Zugriff auf geschützte Bereiche
- Kein Fehler, kein Stack-Trace sichtbar
- HTTP-Status: `200` (Login-Seite wird gerendert)

**Pass/Fail:** ✅ Pass wenn Login-Formular angezeigt wird und kein automatischer Zugang gewährt.

---

## Test 8: Vertragsanzeige

---

### TEST-008: Vertragsanzeige — Paket, Preis, Intervall, Datum

**Testnummer:** 008  
**Name:** Lizenz-UI — vollständige Vertragsanzeige nach Checkout  
**Kategorie:** UI / Vertragsanzeige

**Voraussetzungen:** TEST-006 abgeschlossen — Checkout erfolgreich.

**Testschritte:**

1. Als Vereinsadmin (TEST-001 Account) einloggen
2. Navigation: „💳 Lizenz"
3. Vertragsdetails prüfen

**Erwartetes Ergebnis (UI-Prüfpunkte):**

| Element | Erwarteter Wert |
|---|---|
| Paketname | „Einzeltrainer Basic" (oder `TRAINER_BASIC`) |
| Preis | „9,99 €/Monat" |
| Abrechnungsintervall | „Monatlich" |
| Nächste Abbuchung / Laufzeit | Datum aus `subscription_current_period_end` |
| Vertragsbeginn | Datum aus `vertragsbeginn` |
| Status-Badge | „Trial" oder „Aktiv" |

```sql
SELECT lizenztyp, abo_intervall, subscription_current_period_end,
       vertragsbeginn, lizenz_status
FROM vereine WHERE id = <verein_id>;
```

**Pass/Fail:** ✅ Pass wenn alle Felder in der UI mit DB-Werten übereinstimmen.

---

## Tests 9–12: Kündigung, Rücknahme, Subscription Deleted

---

### TEST-009: Kündigung während Trial

**Testnummer:** 009  
**Name:** Abo kündigen während Testphase — Zugang bleibt bis Trial-Ende  
**Kategorie:** Kündigung

**Voraussetzungen:** TEST-006 abgeschlossen (Trial aktiv, Abo vorhanden).

**Testschritte:**

1. Stripe CLI: Kündigung simulieren (cancel_at_period_end=true):
   ```bash
   stripe subscriptions update <sub_id> --cancel-at-period-end
   ```
2. Stripe sendet `customer.subscription.updated` mit `cancel_at_period_end=true`
3. Webhook empfangen und verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, cancel_at_period_end, gekuendigt_zum
FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `cancelled` |
| `cancel_at_period_end` | `1` |
| `gekuendigt_zum` | ISO-Datum (Ende der aktuellen Periode) |

UI zeigt: Hinweis „Ihr Abo endet am [Datum]". Kein Sperren bis `gekuendigt_zum`.

**Pass/Fail:** ✅ Pass wenn `lizenz_status='cancelled'` und `cancel_at_period_end=1`.

---

### TEST-010: Kündigung rückgängig machen (Reaktivierung)

**Testnummer:** 010  
**Name:** Kündigung zurücknehmen — Abo wieder auf aktiv  
**Kategorie:** Kündigung / Reaktivierung

**Voraussetzungen:** TEST-009 abgeschlossen (`lizenz_status='cancelled'`).

**Testschritte:**

1. Stripe CLI: Kündigung zurücknehmen:
   ```bash
   stripe subscriptions update <sub_id> --cancel-at-period-end=false
   ```
2. Stripe sendet `customer.subscription.updated` mit `cancel_at_period_end=false`
3. Webhook empfangen und verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, cancel_at_period_end, gekuendigt_zum
FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `trial` oder `active` (je nach Trial-Phase) |
| `cancel_at_period_end` | `0` |
| `gekuendigt_zum` | `NULL` (gecleart) |

**Pass/Fail:** ✅ Pass wenn `cancel_at_period_end=0` und `gekuendigt_zum IS NULL`.

---

### TEST-011: Kündigung eines aktiven Abos (nach Trial)

**Testnummer:** 011  
**Name:** Kündigung bei bezahltem aktivem Abo  
**Kategorie:** Kündigung

**Voraussetzungen:**
- Abo aktiv (`lizenz_status='active'`), d. h. Trial beendet und Zahlung eingegangen
- Oder Test Clock verwendet um Trial zu beenden (siehe Abschnitt „Stripe Test Clock")

**Testschritte:**

1. Sicherstellen: `lizenz_status='active'` in DB
2. Stripe CLI: Kündigung:
   ```bash
   stripe subscriptions update <sub_id> --cancel-at-period-end
   ```
3. Webhook `customer.subscription.updated` verarbeiten

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, cancel_at_period_end, lizenz_bis, gekuendigt_zum
FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `cancelled` |
| `cancel_at_period_end` | `1` |
| `lizenz_bis` | Datum der letzten Periode (nicht gelöscht) |

App noch zugänglich bis `lizenz_bis`.

**Pass/Fail:** ✅ Pass wenn `lizenz_status='cancelled'` und Zugang noch möglich.

---

### TEST-012: Subscription vollständig beendet (`subscription.deleted`)

**Testnummer:** 012  
**Name:** `customer.subscription.deleted` — Zugang sperren, Daten erhalten  
**Kategorie:** Kündigung / Webhook

**Voraussetzungen:** Aktives oder gekündigtes Abo vorhanden.

**Testschritte:**

1. Stripe CLI: Abo sofort beenden:
   ```bash
   stripe subscriptions cancel <sub_id>
   ```
   oder via Test Clock Trial-Ablauf abwarten (siehe Abschnitt „Stripe Test Clock")
2. Stripe sendet `customer.subscription.deleted`
3. Webhook verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT lizenz_status, zahlungsstatus, cancel_at_period_end
FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenz_status` | `beendet` |
| `zahlungsstatus` | `beendet` |
| `cancel_at_period_end` | `0` |

UI zeigt Ablauf-Seite (`_zeige_abgelaufen_page()`). Spielerdaten in DB vorhanden:
```sql
SELECT COUNT(*) FROM spieler WHERE verein_id = <verein_id>;
-- Erwartet: > 0 (Daten bleiben erhalten)
```

**Pass/Fail:** ✅ Pass wenn `lizenz_status='beendet'` und Daten erhalten.

---

## Tests 13–15: Payment Failure, Recovery, Trial-Ende

---

### TEST-013: Payment Failure — Zahlung fehlgeschlagen

**Testnummer:** 013  
**Name:** `invoice.payment_failed` — Status auf fehlgeschlagen setzen  
**Kategorie:** Payment Failure

**Voraussetzungen:** Abo mit gültiger Stripe-Customer-ID.

**Testschritte:**

1. Stripe CLI: Payment-Failure-Event auslösen:
   ```bash
   stripe trigger invoice.payment_failed \
     --add invoice:customer=<customer_id>
   ```
   Alternativ: Testkarte `4000 0000 0000 0341` (wird immer abgelehnt) bei nächster Verlängerung verwenden.

**Erwartetes Ergebnis:**

```sql
SELECT zahlungsstatus, letzte_zahlung_fehlgeschlagen
FROM vereine WHERE stripe_customer_id = '<customer_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `zahlungsstatus` | `fehlgeschlagen` |
| `letzte_zahlung_fehlgeschlagen` | Timestamp (nicht NULL) |
| `lizenz_status` | `active` (Zugang bleibt zunächst!) |

API-Server Log: `WARN: Stripe-Zahlung fehlgeschlagen`

**Pass/Fail:** ✅ Pass wenn `zahlungsstatus='fehlgeschlagen'` und Account nicht sofort gesperrt.

---

### TEST-014: Payment Recovery — Zahlung nachgeholt

**Testnummer:** 014  
**Name:** `invoice.paid` nach Failure — Lizenz wieder aktiv  
**Kategorie:** Payment Recovery

**Voraussetzungen:** TEST-013 abgeschlossen (`zahlungsstatus='fehlgeschlagen'`).

**Testschritte:**

1. Stripe CLI: Erfolgreiche Zahlung simulieren:
   ```bash
   stripe trigger invoice.paid \
     --add invoice:customer=<customer_id> \
     --add invoice:amount_paid=999
   ```
2. Webhook `invoice.paid` wird verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT zahlungsstatus, lizenz_status, lizenz_bis
FROM vereine WHERE stripe_customer_id = '<customer_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `zahlungsstatus` | `bezahlt` |
| `lizenz_status` | `active` |
| `lizenz_bis` | Neues Datum (verlängert) |

**Pass/Fail:** ✅ Pass wenn `zahlungsstatus='bezahlt'` und `lizenz_status='active'`.

---

### TEST-015: Trial-Ende simulieren (Test Clock)

**Testnummer:** 015  
**Name:** Trial läuft ab — App sperrt sich nach `testphase_bis`  
**Kategorie:** Trial-Ende

**Voraussetzungen:**
- Testverein ohne Stripe-Abo (reine Trial-Phase)
- Stripe Test Clock erstellt (siehe Abschnitt „Stripe Test Clock")

**Testschritte:**

1. DB: `testphase_bis` manuell auf gestern setzen (nur für Sandbox!):
   ```bash
   sqlite3 artifacts/athletik/athletik.db \
     "UPDATE vereine SET testphase_bis = date('now', '-1 day') WHERE id = <verein_id>;"
   ```
2. App neu laden (Re-Run in Streamlit)
3. `enforce_license_gate()` berechnet `lizenz_status='expired'` on-the-fly

**Erwartetes Ergebnis:**

- UI zeigt Ablauf-Seite (`_zeige_abgelaufen_page()`)
- Navigation gesperrt (`st.stop()` wurde aufgerufen)
- DB-Wert `lizenz_status` bleibt `trial` (on-the-fly-Berechnung, kein DB-Write)

```sql
SELECT lizenz_status FROM vereine WHERE id = <verein_id>;
-- Erwartet: 'trial' (DB nicht verändert — nur UI-Berechnung)
```

**Pass/Fail:** ✅ Pass wenn Ablauf-Seite sichtbar und kein Zugang zu geschützten Seiten.

---

## Tests 16–18: Paketwechsel

---

### TEST-016: Upgrade Basic → Pro

**Testnummer:** 016  
**Name:** Paketwechsel TRAINER_BASIC → TRAINER_PRO  
**Kategorie:** Paketwechsel

**Voraussetzungen:** TEST-006 abgeschlossen, `lizenz_status='active'`.

**Testschritte:**

1. Stripe CLI: Subscription auf Pro-Price-ID umstellen:
   ```bash
   stripe subscriptions update <sub_id> \
     --items[0][price]=<STRIPE_PRICE_TRAINER_PRO_MONAT>
   ```
2. Stripe sendet `customer.subscription.updated`
3. Webhook verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT lizenztyp, abo_intervall, lizenz_status
FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `TRAINER_PRO` |
| `abo_intervall` | `monat` |
| `lizenz_status` | `active` |

**Pass/Fail:** ✅ Pass wenn `lizenztyp='TRAINER_PRO'`.

---

### TEST-017: Downgrade Pro → Basic

**Testnummer:** 017  
**Name:** Paketwechsel TRAINER_PRO → TRAINER_BASIC (Downgrade)  
**Kategorie:** Paketwechsel

**Voraussetzungen:** TEST-016 abgeschlossen (`lizenztyp='TRAINER_PRO'`).

**Testschritte:**

1. Stripe CLI: Subscription auf Basic-Price-ID umstellen:
   ```bash
   stripe subscriptions update <sub_id> \
     --items[0][price]=<STRIPE_PRICE_TRAINER_BASIC_MONAT>
   ```
2. Webhook `customer.subscription.updated` verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT lizenztyp, lizenz_status FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `lizenztyp` | `TRAINER_BASIC` |
| `lizenz_status` | `active` |

**Pass/Fail:** ✅ Pass wenn `lizenztyp='TRAINER_BASIC'`.

---

### TEST-018: Intervallwechsel Monat → Jahr

**Testnummer:** 018  
**Name:** Abrechnungsintervall Monat → Jahr wechseln  
**Kategorie:** Paketwechsel

**Voraussetzungen:** Aktives monatliches Abo.

**Testschritte:**

1. Stripe CLI: Auf Jahres-Price umstellen:
   ```bash
   stripe subscriptions update <sub_id> \
     --items[0][price]=<STRIPE_PRICE_TRAINER_BASIC_YEARLY>
   ```
2. Webhook `customer.subscription.updated` verarbeitet

**Erwartetes Ergebnis:**

```sql
SELECT abo_intervall, lizenztyp FROM vereine WHERE stripe_subscription_id = '<sub_id>';
```

| Spalte | Erwarteter Wert |
|---|---|
| `abo_intervall` | `jahr` |
| `lizenztyp` | `TRAINER_BASIC` (unverändert) |

**Pass/Fail:** ✅ Pass wenn `abo_intervall='jahr'`.

---

## Tests 19–23: Idempotenz & Sicherheit

---

### TEST-019: Idempotenz — doppelter Webhook wird ignoriert

**Testnummer:** 019  
**Name:** Gleiche Event-ID zweimal senden — zweite Verarbeitung übersprungen  
**Kategorie:** Idempotenz / Sicherheit

**Voraussetzungen:** Webhook-Endpunkt erreichbar, `stripe_events`-Tabelle vorhanden.

**Testschritte:**

1. Stripe CLI: Beliebiges Event auslösen, z. B.:
   ```bash
   stripe trigger customer.subscription.updated
   ```
2. Event-ID notieren (aus Stripe CLI Output oder Dashboard): `evt_…`
3. Webhook manuell ein zweites Mal senden (Stripe Dashboard → Webhooks → Resend)
   oder via curl (mit gültiger Signatur, gleiche Event-ID):
   ```bash
   # Stripe CLI resend (empfohlen):
   stripe events resend evt_<id>
   ```

**Erwartetes Ergebnis:**

```sql
SELECT COUNT(*) FROM stripe_events WHERE event_id = 'evt_<id>';
-- Erwartet: 1 (genau einmal eingetragen)
```

API-Server Log für zweiten Aufruf:
```
INFO: Stripe Event bereits verarbeitet — übersprungen
```

HTTP Response auf zweiten Aufruf: `200 {"received": true}`

**Pass/Fail:** ✅ Pass wenn `stripe_events` genau einen Eintrag hat und Log-Meldung korrekt.

---

### TEST-020: Ungültige Signatur → HTTP 400

**Testnummer:** 020  
**Name:** Webhook mit falscher Signatur — Anfrage abgewiesen  
**Kategorie:** Sicherheit

**Testschritte:**

1. Webhook-Endpunkt mit manipuliertem Signature-Header aufrufen:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" \
     -X POST https://aphsystem.de/api/stripe/webhook \
     -H "Content-Type: application/json" \
     -H "stripe-signature: t=1234567890,v1=invalidsignaturehere" \
     -d '{"id":"evt_fake","type":"checkout.session.completed","data":{"object":{}}}'
   ```

**Erwartetes Ergebnis:**

- HTTP Status: `400`
- Response Body: `{"error": "Signaturprüfung fehlgeschlagen"}`
- DB: keine Änderungen
- API-Server Log: `WARN: Stripe Webhook: Signaturprüfung fehlgeschlagen`

**Pass/Fail:** ✅ Pass wenn HTTP 400 zurückgegeben und keine DB-Schreibvorgänge.

---

### TEST-021: Fehlendes Webhook-Secret → HTTP 503 (Fail-Closed)

**Testnummer:** 021  
**Name:** `STRIPE_WEBHOOK_SECRET` nicht konfiguriert — Endpunkt verweigert alle Anfragen  
**Kategorie:** Sicherheit / Fail-Closed

**Testschritte:**

1. Temporär: `STRIPE_WEBHOOK_SECRET` aus Env entfernen (API-Server neu starten)
2. Beliebigen Webhook-Aufruf senden:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" \
     -X POST https://aphsystem.de/api/stripe/webhook \
     -H "Content-Type: application/json" \
     -d '{"id":"evt_test","type":"checkout.session.completed"}'
   ```

**Erwartetes Ergebnis:**

- HTTP Status: `503`
- Response Body: `{"error": "Webhook nicht konfiguriert"}`
- DB: keine Änderungen
- API-Server Log: `ERROR: STRIPE_WEBHOOK_SECRET oder STRIPE_SECRET_KEY nicht konfiguriert`

**Aufräumen:** `STRIPE_WEBHOOK_SECRET` wiederherstellen, API-Server neu starten.

**Pass/Fail:** ✅ Pass wenn HTTP 503 und keinerlei DB-Schreibvorgang erfolgte.

---

### TEST-022: `checkout=success` ohne Cookie — kein automatischer Login

**Testnummer:** 022  
**Name:** `success_url` ohne Session-Cookie aufrufen — Weiterleitung zur Login-Seite  
**Kategorie:** Sicherheit / Session

*Entspricht TEST-007 — wurde als eigener Test zur Sicherheit separat dokumentiert.*

**Testschritte:**

1. `success_url` aus Stripe-Checkout notieren (Form: `https://aphsystem.de/app?checkout=success&…`)
2. Neues Incognito-Fenster öffnen (kein Cookie)
3. URL direkt aufrufen

**Erwartetes Ergebnis:**

- Login-Formular wird angezeigt
- Kein automatischer Zugang zur App
- Kein Error, kein Stack-Trace
- HTTP-Status der Seite: `200`

**Pass/Fail:** ✅ Pass wenn Login-Seite erscheint und kein Dashboard sichtbar.

---

### TEST-023: Reload mit gültigem Session-Cookie — Session bleibt erhalten

**Testnummer:** 023  
**Name:** Browser-Reload nach Login — Session nicht verloren  
**Kategorie:** Session

**Testschritte:**

1. Als Vereinsadmin einloggen
2. Vollständigen Browser-Reload durchführen (F5 / Cmd+R)
3. Prüfen ob Session noch aktiv ist

**Erwartetes Ergebnis:**

- Nach Reload: Dashboard direkt sichtbar (kein erneuter Login erforderlich)
- Session-Cookie im Browser noch vorhanden
- `st.session_state["user"]` nach Reload korrekt befüllt

**Pass/Fail:** ✅ Pass wenn nach Reload direkt Dashboard angezeigt wird.

---

## Tests 24–25: Superadmin-Funktionen

---

### TEST-024: Superadmin-Vertragsstatus korrekt angezeigt

**Testnummer:** 024  
**Name:** Superadmin-Dashboard zeigt korrekten Lizenzstatus aller Vereine  
**Kategorie:** Superadmin

**Voraussetzungen:**
- Superadmin-Account vorhanden
- Mindestens ein Testverein mit `lizenz_status='active'` und einer mit `lizenz_status='beendet'`

**Testschritte:**

1. Als Superadmin einloggen
2. Navigation: „💳 Lizenzverwaltung"
3. Alle Vereine aus TEST-001 bis TEST-012 sollten mit korrektem Status aufgelistet sein

**Erwartetes Ergebnis:**

```sql
SELECT id, name, lizenztyp, lizenz_status, zahlungsstatus,
       stripe_customer_id, cancel_at_period_end
FROM vereine ORDER BY id;
```

UI zeigt für jeden Verein:
- Korrekte Paket-Bezeichnung
- Korrekter Status-Badge (Trial / Aktiv / Gekündigt / Beendet)
- Korrekte Zahlungsstatus-Anzeige
- Korrekte Stripe-IDs (wenn vorhanden)

Superadmin kann Testphase verlängern — Button vorhanden und funktional.

**Pass/Fail:** ✅ Pass wenn alle Status-Badges mit DB-Werten übereinstimmen.

---

### TEST-025: Keine Doppel-Subscription nach erneutem Checkout

**Testnummer:** 025  
**Name:** Zweiter Checkout-Versuch erzeugt keine zweite Subscription  
**Kategorie:** Datenkonsistenz

**Voraussetzungen:** TEST-006 abgeschlossen — Verein hat bereits `stripe_subscription_id`.

**Testschritte:**

1. Als Vereinsadmin einloggen (mit bestehender Subscription)
2. Erneut Upgrade-Button auf Lizenz-Seite klicken
3. Prüfen ob Stripe Billing-Portal geöffnet wird (statt neuem Checkout)
4. Falls trotzdem neuer Checkout: Stripe-Dashboard prüfen

**Erwartetes Ergebnis:**

```sql
SELECT COUNT(*) FROM vereine WHERE stripe_customer_id = '<customer_id>';
-- Erwartet: 1 (nicht doppelt)
```

Stripe Dashboard: genau ein aktives Abo pro Customer.

Im Stripe Dashboard:  
- Klick auf Customer `cus_…` → Subscriptions: genau **1** aktives Abo

**Pass/Fail:** ✅ Pass wenn Customer nur eine aktive Subscription hat.

---

## Stripe Test Clock — Anleitung

### Warum Test Clocks?

Trial-Perioden (30 Tage) und Abrechnungszyklen (1 Monat / 1 Jahr) können in der
Sandbox ohne echtes Warten simuliert werden. Stripe Test Clocks ermöglichen das
Vorspulen der Zeit für einen einzelnen Customer.

### Voraussetzungen

- Stripe-Dashboard im **Test-Modus** (Schalter oben links: „Test mode")
- Customer noch ohne Test Clock (Test Clocks müssen beim Customer-Anlegen aktiviert werden)

### Schritt-für-Schritt

#### 1. Test Clock erstellen

1. Stripe Dashboard → **Customers** → **+ New**
2. Im Modal: „**Advanced**" aufklappen → „**Use test clock**" aktivieren
3. Startzeit setzen: heute (oder gewünschtes Startdatum)
4. Customer anlegen

Alternativ via Stripe API:
```bash
stripe clocks create --frozen-time $(date +%s)
```

#### 2. Subscription für Test-Clock-Customer erstellen

1. In der App: Checkout mit dem Test-Clock-Customer starten
2. Stripe Checkout verwendet automatisch den Clock-Customer
3. Subscription wird unter dem Test-Clock-Customer angelegt

#### 3. Zeit vorspulen (Advance)

**Stripe Dashboard:**
1. Customers → Test-Clock-Customer öffnen
2. Tab „**Test clock**" → „**Advance time**"
3. Zieldatum eingeben (z. B. Trial-Ende: heute + 30 Tage + 1 Tag)
4. „Advance" klicken

**Stripe CLI:**
```bash
# Clock-ID aus Dashboard oder API:
stripe clocks advance <clock_id> --frozen-time <unix_timestamp>
```

**Beispiel: Trial-Ende simulieren**
```bash
# Trial endet in 30 Tagen — auf Tag 31 vorspulen
TRIAL_END=$(date -d "+31 days" +%s)
stripe clocks advance clk_<id> --frozen-time $TRIAL_END
```

#### 4. Erwartete Stripe Events beim Vorspulen

| Event | Auslöser |
|---|---|
| `invoice.payment_succeeded` / `invoice.paid` | Erste kostenpflichtige Rechnung |
| `customer.subscription.updated` | Trial endet, Abo wechselt auf `active` |
| `invoice.payment_failed` | Wenn Karte ungültig |
| `customer.subscription.deleted` | Wenn Dunning fehlschlägt |

#### 5. Renewal simulieren

```bash
# Auf Datum der nächsten Abrechnungsperiode vorspulen
RENEWAL=$(date -d "+31 days" +%s)
stripe clocks advance clk_<id> --frozen-time $RENEWAL
```

Erwartet: `invoice.paid` mit `amount_paid > 0` → DB: `zahlungsstatus='bezahlt'`, `lizenz_bis` verlängert.

#### 6. Nützliche Stripe-Dokumentationsseiten

- Test Clocks Overview: https://stripe.com/docs/billing/testing/test-clocks
- Test Clocks API: https://stripe.com/docs/api/test_clocks
- Testing Subscriptions: https://stripe.com/docs/billing/testing
- Stripe CLI: https://stripe.com/docs/stripe-cli

---

## VPS-Prüfbefehle (Read-Only)

> ⚠️ **Wichtig:** Ausschließlich SELECT-Queries — kein UPDATE, INSERT, DELETE auf Produktionsdaten.

### Verbindung zum VPS

```bash
ssh user@aphsystem.de
# Datenbank-Pfad auf dem VPS:
export APH_DB="/data/athletik.db"
```

### 1. Gesamtübersicht aller Lizenzstatus

```bash
sqlite3 $APH_DB "
SELECT id, name, lizenztyp, lizenz_status, zahlungsstatus,
       testphase_bis, lizenz_bis, cancel_at_period_end,
       CASE WHEN stripe_customer_id IS NOT NULL THEN '✓' ELSE '—' END AS hat_stripe
FROM vereine
ORDER BY id;
"
```

### 2. Alle Vereine mit Stripe-Abo (aktiv oder gekündigt)

```bash
sqlite3 $APH_DB "
SELECT id, name, lizenztyp, lizenz_status, zahlungsstatus,
       stripe_customer_id, stripe_subscription_id,
       abo_intervall, vertragsbeginn, lizenz_bis, gekuendigt_zum
FROM vereine
WHERE stripe_customer_id IS NOT NULL
ORDER BY id;
"
```

### 3. Idempotenz-Tabelle — verarbeitete Webhook-Events

```bash
sqlite3 $APH_DB "
SELECT event_id, event_type, processed_at
FROM stripe_events
ORDER BY processed_at DESC
LIMIT 50;
"
```

### 4. Rechnungshistorie

```bash
sqlite3 $APH_DB "
SELECT r.id, v.name AS verein, r.rechnungsnummer, r.rechnungsdatum,
       r.betrag_eur, r.lizenz_typ, r.status, r.stripe_invoice_id
FROM rechnungen r
JOIN vereine v ON r.verein_id = v.id
ORDER BY r.erstellt_am DESC
LIMIT 50;
"
```

### 5. Fehlgeschlagene Zahlungen

```bash
sqlite3 $APH_DB "
SELECT id, name, zahlungsstatus, letzte_zahlung_fehlgeschlagen,
       stripe_customer_id
FROM vereine
WHERE zahlungsstatus = 'fehlgeschlagen'
   OR zahlungsstatus = 'beendet';
"
```

### 6. Trial-Abläufe in den nächsten 7 Tagen

```bash
sqlite3 $APH_DB "
SELECT id, name, lizenztyp, lizenz_status, testphase_bis,
       CAST(julianday(testphase_bis) - julianday('now') AS INTEGER) AS tage_verbleibend
FROM vereine
WHERE lizenz_status = 'trial'
  AND testphase_bis IS NOT NULL
  AND julianday(testphase_bis) - julianday('now') <= 7
  AND julianday(testphase_bis) - julianday('now') >= 0
ORDER BY testphase_bis;
"
```

### 7. Vereine ohne Stripe-Customer nach Trial-Ablauf

```bash
sqlite3 $APH_DB "
SELECT id, name, lizenztyp, testphase_bis
FROM vereine
WHERE stripe_customer_id IS NULL
  AND (testphase_bis < date('now') OR lizenz_status IN ('expired','beendet'))
ORDER BY testphase_bis;
"
```

### 8. DB-Schema-Check — alle Spalten in `vereine`

```bash
sqlite3 $APH_DB "PRAGMA table_info(vereine);"
```

**Erwartete Pflicht-Spalten:**

| Spalte | Erwartet |
|---|---|
| `lizenz_status` | TEXT |
| `zahlungsstatus` | TEXT |
| `stripe_customer_id` | TEXT |
| `stripe_subscription_id` | TEXT |
| `testphase_bis` | TEXT |
| `lizenz_bis` | TEXT |
| `abo_intervall` | TEXT |
| `cancel_at_period_end` | INTEGER |
| `subscription_current_period_end` | TEXT |
| `vertragsbeginn` | TEXT |
| `letzte_zahlung_fehlgeschlagen` | TEXT |
| `gekuendigt_zum` | TEXT |

### 9. Webhook API-Server Logs (VPS)

```bash
# Docker Compose Log-Zugriff (letzten 100 Zeilen):
docker compose logs --tail=100 api-server | grep -E "(stripe|webhook|ERROR|WARN)"
```

### 10. API-Server-Health-Check (Read-Only)

```bash
curl -s https://aphsystem.de/api/health | python3 -m json.tool
# Erwartet: {"status": "ok"} oder ähnliches
```

---

## Abschlussbericht-Template

Datum: ___________  
Tester: ___________  
Umgebung: Stripe Test-Modus / Sandbox  

---

### 1. Phasen-Status (A5.2–A9)

| Phase | Beschreibung | Status |
|---|---|---|
| A5.2 | Webhook-Signaturprüfung implementiert | ☐ Abgeschlossen / ☐ Ausstehend |
| A6 | Checkout-Flow: customer.subscription.created | ☐ Abgeschlossen / ☐ Ausstehend |
| A7 | Kündigung & Reaktivierung (cancel_at_period_end) | ☐ Abgeschlossen / ☐ Ausstehend |
| A8 | Payment Failure & Recovery | ☐ Abgeschlossen / ☐ Ausstehend |
| A9 | Paketwechsel (Upgrade/Downgrade/Intervall) | ☐ Abgeschlossen / ☐ Ausstehend |

**Anmerkungen zu Phasen:**

```
_______________________________________________
```

---

### 2. Geänderte Dateien

| Datei | Art der Änderung | Getestet |
|---|---|---|
| `artifacts/api-server/src/routes/stripe.ts` | Webhook-Handler | ☐ |
| `artifacts/athletik/license.py` | Lizenz-Logik | ☐ |
| `artifacts/athletik/database.py` | DB-Funktionen | ☐ |
| `artifacts/athletik/stripe_service.py` | Stripe-API-Calls | ☐ |
| `artifacts/athletik/modules/lizenz_page.py` | Lizenz-UI | ☐ |
| `artifacts/athletik/config.py` | Env-Vars | ☐ |

**Weitere geänderte Dateien:**

```
_______________________________________________
```

---

### 3. DB-Spalten — Vollständigkeitsprüfung

```bash
sqlite3 artifacts/athletik/athletik.db "PRAGMA table_info(vereine);" | grep -E \
  "lizenz_status|zahlungsstatus|stripe_customer_id|stripe_subscription_id|\
testphase_bis|lizenz_bis|abo_intervall|cancel_at_period_end|\
subscription_current_period_end|vertragsbeginn|letzte_zahlung_fehlgeschlagen|gekuendigt_zum"
```

Alle 12 Spalten vorhanden: ☐ Ja / ☐ Nein — fehlende Spalten:

```
_______________________________________________
```

---

### 4. Stripe Events — alle 6 Handler implementiert

| Event | Handler in stripe.ts | Getestet |
|---|---|---|
| `checkout.session.completed` | ✓ Zeile 267 | ☐ |
| `customer.subscription.created` | ✓ Zeile 301 | ☐ |
| `customer.subscription.updated` | ✓ Zeile 337 | ☐ |
| `customer.subscription.deleted` | ✓ Zeile 385 | ☐ |
| `invoice.paid` | ✓ Zeile 406 | ☐ |
| `invoice.payment_failed` | ✓ Zeile 445 | ☐ |

---

### 5. Statuswerte — alle getestet

| `lizenz_status` | Test-Nr. | Pass/Fail |
|---|---|---|
| `trial` | 001–004, 006 | ☐ / ☐ |
| `active` | 006 (nach Trial), 014 | ☐ / ☐ |
| `cancelled` | 009, 011 | ☐ / ☐ |
| `beendet` | 012 | ☐ / ☐ |
| `expired` | 015 | ☐ / ☐ |
| `suspended` | (manuell via Superadmin) | ☐ |

| `zahlungsstatus` | Test-Nr. | Pass/Fail |
|---|---|---|
| `zahlungsmethode_hinterlegt` | 006 | ☐ / ☐ |
| `bezahlt` | 014 | ☐ / ☐ |
| `fehlgeschlagen` | 013 | ☐ / ☐ |
| `beendet` | 012 | ☐ / ☐ |

---

### 6. Testergebnisse — alle 25 Tests

| Nr. | Testname | Ergebnis | Notiz |
|---|---|---|---|
| 001 | Registrierung TRAINER_BASIC | ☐ Pass / ☐ Fail | |
| 002 | Registrierung TRAINER_PRO | ☐ Pass / ☐ Fail | |
| 003 | Registrierung VEREIN_BASIC | ☐ Pass / ☐ Fail | |
| 004 | Registrierung VEREIN_PRO | ☐ Pass / ☐ Fail | |
| 005 | Checkout abbrechen | ☐ Pass / ☐ Fail | |
| 006 | Checkout erfolgreich | ☐ Pass / ☐ Fail | |
| 007 | Rückkehr ohne Cookie | ☐ Pass / ☐ Fail | |
| 008 | Vertragsanzeige korrekt | ☐ Pass / ☐ Fail | |
| 009 | Kündigung Trial | ☐ Pass / ☐ Fail | |
| 010 | Kündigung Rücknahme | ☐ Pass / ☐ Fail | |
| 011 | Kündigung aktives Abo | ☐ Pass / ☐ Fail | |
| 012 | subscription.deleted | ☐ Pass / ☐ Fail | |
| 013 | Payment Failure | ☐ Pass / ☐ Fail | |
| 014 | Payment Recovery | ☐ Pass / ☐ Fail | |
| 015 | Trial-Ende | ☐ Pass / ☐ Fail | |
| 016 | Upgrade Basic→Pro | ☐ Pass / ☐ Fail | |
| 017 | Downgrade Pro→Basic | ☐ Pass / ☐ Fail | |
| 018 | Monat→Jahr | ☐ Pass / ☐ Fail | |
| 019 | Idempotenz (Doppel-Webhook) | ☐ Pass / ☐ Fail | |
| 020 | Ungültige Signatur | ☐ Pass / ☐ Fail | |
| 021 | Fehlendes Secret (503) | ☐ Pass / ☐ Fail | |
| 022 | success_url ohne Cookie | ☐ Pass / ☐ Fail | |
| 023 | Reload mit Cookie | ☐ Pass / ☐ Fail | |
| 024 | Superadmin-Vertragsstatus | ☐ Pass / ☐ Fail | |
| 025 | Keine Doppel-Subscription | ☐ Pass / ☐ Fail | |

**Gesamt:** _____ / 25 bestanden

---

### 7. Bekannte Abweichungen / Offene Punkte

```
_______________________________________________
_______________________________________________
_______________________________________________
```

---

### 8. Stripe Test Clock verwendet

☐ Ja — Clock-ID: `clk_` _______________  
☐ Nein — manuelle DB-Manipulation für Trial-Ende (TEST-015)

---

### 9. Empfehlung

☐ **Freigabe für Live-Modus** — alle 25 Tests bestanden, keine kritischen Abweichungen  
☐ **Nicht freigegeben** — folgende Tests fehlgeschlagen:

```
_______________________________________________
```

---

### 10. Unterschriften

Tester: _____________________  Datum: ___________

Review: _____________________  Datum: ___________
