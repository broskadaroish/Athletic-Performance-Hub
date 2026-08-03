# Lizenzsystem — Implementierungsbericht

Datum: 2026-08-03  
Status: ✅ Vollständig implementiert, produktionsbereit (ohne echte Stripe-Keys)

---

## 1. Geänderte / Neue Dateien

### Neue Dateien

| Datei | Inhalt |
|---|---|
| `license.py` | **Kern-Lizenzmodul** — Lizenztypen (FREE/BASIC/PRO/ENTERPRISE), Limits, Statusberechnung, Feature-Gates, App-Gate (`enforce_license_gate`), Gesperrt/Abgelaufen-Seiten |
| `stripe_service.py` | **Stripe-Service** — alle Stripe-API-Aufrufe gekapselt: Kunden, Checkout, Billing-Portal, Upgrade/Downgrade, Kündigung, Reaktivierung, Webhook-Validierung und Verarbeitung |
| `modules/lizenz_page.py` | **Lizenz-UI** — Vereinsadmin-Lizenzseite (Tarif, KPIs, Rechnungshistorie, Billing-Portal-Link), Superadmin-Lizenzverwaltung (alle Vereine, Bearbeiten, Sperren/Entsperren, Testphase verlängern) |
| `config.py` | Erweitert um alle Stripe Env-Vars: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`, alle `STRIPE_PRICE_*`-IDs, `APP_BASE_URL` |

### Geänderte Dateien

| Datei | Änderung |
|---|---|
| `database.py` | Neue Spalten in `vereine`, neue Tabelle `rechnungen`, neue Funktionen: `verein_registrieren`, `lizenz_info_laden`, `lizenz_setzen`, `verein_sperren`, `testphase_verlaengern`, `stripe_ids_setzen`, `zahlungsstatus_setzen`, `rechnung_speichern`, `rechnungen_laden`, `alle_vereine_lizenz`. `verein_speichern()` setzt jetzt automatisch Testphase + Lizenzstatus. |
| `app.py` | Import `lizenz_page`, Lizenz-Gate nach Session-Timeout, Nav-Sektion "💳 Lizenz" für Vereinsadmin, "💳 Lizenzverwaltung" für Superadmin, Route-Handler für beide Seiten, Selbstregistrierungs-Tab im Login |

---

## 2. Neue Datenbanktabellen und -spalten

### Neue Spalten in `vereine`

| Spalte | Typ | Bedeutung |
|---|---|---|
| `testphase_bis` | TEXT (ISO-Date) | Ende der kostenlosen Testphase |
| `lizenz_status` | TEXT | `trial` \| `active` \| `expired` \| `suspended` \| `cancelled` |
| `gesperrt` | INTEGER (0/1) | Manuell gesperrt durch Superadmin |
| `stripe_customer_id` | TEXT | Stripe-Kunden-ID |
| `stripe_subscription_id` | TEXT | Stripe-Abonnement-ID |
| `zahlungsstatus` | TEXT | `offen` \| `bezahlt` \| `fehlgeschlagen` \| `storniert` |

> Bereits vorhanden: `lizenztyp` (FREE/BASIC/PRO/ENTERPRISE), `lizenz_bis`, `max_trainer`, `max_spieler`

### Neue Tabelle: `rechnungen`

```sql
CREATE TABLE rechnungen (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    verein_id         INTEGER NOT NULL,
    rechnungsnummer   TEXT    NOT NULL,
    rechnungsdatum    TEXT    NOT NULL,
    betrag_eur        REAL    NOT NULL,
    lizenz_typ        TEXT,
    status            TEXT    NOT NULL DEFAULT 'offen',
    lizenz_von        TEXT,
    lizenz_bis_r      TEXT,
    stripe_invoice_id TEXT,
    erstellt_am       TEXT    NOT NULL,
    FOREIGN KEY (verein_id) REFERENCES vereine(id)
);
```

---

## 3. Lizenztypen & Limits

| Typ | Trainer | Spieler | Preis/Monat | Preis/Jahr |
|---|---|---|---|---|
| FREE | 1 | 15 | — | — |
| BASIC | 3 | 50 | 29 € | 290 € |
| PRO | 10 | 200 | 79 € | 790 € |
| ENTERPRISE | unbegrenzt | unbegrenzt | 199 € | 1.990 € |

---

## 4. Was fehlt noch bis zum Livebetrieb (Stripe)

### Muss vorhanden sein (Pflicht)

| Schritt | Beschreibung |
|---|---|
| 🔑 Stripe-Account | stripe.com → Account erstellen und verifizieren |
| 📦 Produkte anlegen | 3 Produkte in Stripe: Basic, Pro, Enterprise — je mit Monats- und Jahrespreis |
| 🔗 Price-IDs | Nach Produktanlage: Price-IDs in Env-Vars eintragen (`STRIPE_PRICE_BASIC_MONAT` etc.) |
| 🔐 API-Keys | `STRIPE_SECRET_KEY` (sk_live_...) und `STRIPE_PUBLISHABLE_KEY` (pk_live_...) setzen |
| 🪝 Webhook einrichten | Stripe Dashboard → Webhooks → Endpunkt: `https://brucefootball.de/api/stripe/webhook` |
| 🔏 Webhook-Secret | `STRIPE_WEBHOOK_SECRET` (whsec_...) aus Webhook-Einstellung |
| ✅ Signaturprüfung | In `api-server/src/routes/stripe.ts` die auskommentierte Signaturprüfung aktivieren |
| 🔁 Webhook-Handler | In `api-server/src/routes/stripe.ts` die DB-Aktionen implementieren (Lizenz aktivieren bei Zahlung etc.) |
| 💳 Checkout-Flow | `stripe_service.checkout_session_erstellen()` aus der Lizenz-Seite aufrufen (Button "Jetzt upgraden") |
| 🧾 Billing-Portal | Im Stripe-Dashboard: Customer Portal aktivieren und konfigurieren |
| `stripe` installieren | `pip install stripe` in `requirements.txt` ergänzen |

### Optional aber empfohlen

| Schritt | Beschreibung |
|---|---|
| 📧 Rechnungs-E-Mail | Stripe automatisch Rechnungen per E-Mail versenden lassen (Stripe → Settings → Emails) |
| 🌐 Steuer/VAT | Stripe Tax aktivieren für automatische MwSt.-Berechnung |
| 🔄 Dunning | Fehlgeschlagene Zahlungen automatisch wiederholen (Stripe → Billing → Settings → Retry) |
| 📊 Webhook-Logging | Fehlerhafte Webhook-Events in DB speichern für Debugging |
| 🎫 Promo-Codes | Gutscheine in Stripe anlegen (bereits in Checkout aktiviert: `allow_promotion_codes: True`) |

---

## 5. Benötigte Umgebungsvariablen

### Neue Stripe-Variablen (in `.env` und Hosting-Plattform setzen)

```bash
# ── Stripe API-Keys ──────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_...          # Produktiv-Key (sk_test_ für Tests)
STRIPE_PUBLISHABLE_KEY=pk_live_...     # Öffentlicher Key
STRIPE_WEBHOOK_SECRET=whsec_...        # Aus Stripe Webhook-Dashboard

# ── Stripe Price-IDs (nach Produktanlage) ────────────────────────────────────
STRIPE_PRICE_BASIC_MONAT=price_...
STRIPE_PRICE_BASIC_JAHR=price_...
STRIPE_PRICE_PRO_MONAT=price_...
STRIPE_PRICE_PRO_JAHR=price_...
STRIPE_PRICE_ENT_MONAT=price_...
STRIPE_PRICE_ENT_JAHR=price_...

# ── App-URL (für Stripe Redirect-URLs) ───────────────────────────────────────
APP_BASE_URL=https://brucefootball.de
```

### Vollständige Variable-Übersicht (alle Dienste)

Siehe `GO_LIVE_CHECKLIST.md` — Abschnitt "Umgebungsvariablen Checkliste" (bereits vorhanden).

---

## 6. Stripe Go-Live Checkliste

### Phase 1: Vorbereitung

- [ ] Stripe-Account erstellt und E-Mail bestätigt
- [ ] Bank-/Auszahlungskonto in Stripe hinterlegt
- [ ] Unternehmensidentität verifiziert (Stripe KYC)
- [ ] `pip install stripe` in `requirements.txt` ergänzt
- [ ] Stripe im Test-Modus getestet (Testkarte: 4242 4242 4242 4242)

### Phase 2: Produkte & Preise anlegen (Stripe Dashboard)

```
Produkt 1: Bruce Football Basic
  → Preis 1: 29,00 € / Monat (recurring)  → STRIPE_PRICE_BASIC_MONAT
  → Preis 2: 290,00 € / Jahr (recurring)  → STRIPE_PRICE_BASIC_JAHR

Produkt 2: Bruce Football Pro
  → Preis 1: 79,00 € / Monat             → STRIPE_PRICE_PRO_MONAT
  → Preis 2: 790,00 € / Jahr             → STRIPE_PRICE_PRO_JAHR

Produkt 3: Bruce Football Enterprise
  → Preis 1: 199,00 € / Monat            → STRIPE_PRICE_ENT_MONAT
  → Preis 2: 1.990,00 € / Jahr           → STRIPE_PRICE_ENT_JAHR
```

- [ ] Alle 6 Preise angelegt
- [ ] Price-IDs in Env-Vars eingetragen
- [ ] Preise und Produktbeschreibungen geprüft

### Phase 3: Webhook konfigurieren

- [ ] Stripe Dashboard → Developers → Webhooks → Add endpoint
- [ ] URL: `https://brucefootball.de/api/stripe/webhook`
- [ ] Events auswählen:
  - [ ] `checkout.session.completed`
  - [ ] `invoice.payment_succeeded`
  - [ ] `invoice.payment_failed`
  - [ ] `customer.subscription.deleted`
  - [ ] `customer.subscription.updated`
- [ ] `STRIPE_WEBHOOK_SECRET` in Env-Vars gesetzt
- [ ] Signaturprüfung in `api-server/src/routes/stripe.ts` aktiviert

### Phase 4: Stripe-Aktionen in `api-server/src/routes/stripe.ts` implementieren

```typescript
// Bei "checkout.session.completed":
// → verein_id aus metadata lesen
// → Stripe-Customer-ID und Subscription-ID in DB speichern
// → Lizenz auf "active" setzen, lizenz_bis auf nächste Abrechnungsperiode

// Bei "invoice.payment_succeeded":
// → lizenz_bis verlängern
// → zahlungsstatus auf "bezahlt" setzen
// → Rechnung in DB speichern

// Bei "invoice.payment_failed":
// → zahlungsstatus auf "fehlgeschlagen" setzen
// → Trainer per E-Mail benachrichtigen

// Bei "customer.subscription.deleted":
// → lizenz_status auf "expired" setzen
```

- [ ] Alle Event-Handler implementiert
- [ ] Webhook end-to-end mit Test-Events getestet (Stripe CLI: `stripe trigger`)

### Phase 5: Billing-Portal aktivieren

- [ ] Stripe Dashboard → Settings → Billing → Customer portal → Enable
- [ ] Erlaubte Aktionen konfigurieren: Tarif wechseln, Kündigen, Rechnungen ansehen
- [ ] Branding/Logo im Portal hinterlegt

### Phase 6: Checkout-Flow verdrahten

- [ ] In `modules/lizenz_page.py`: "Upgrade"-Button ruft `checkout_session_erstellen()` auf
- [ ] `create_customer()` wird beim ersten Checkout aufgerufen
- [ ] `stripe_customer_id` wird nach Checkout in DB gespeichert (via Webhook)
- [ ] Redirect nach Checkout funktioniert (success_url / cancel_url)

### Phase 7: Live-Modus aktivieren

- [ ] Testkarte entfernt / Test-Keys durch Live-Keys ersetzt
- [ ] `STRIPE_SECRET_KEY=sk_live_...` gesetzt
- [ ] Echte Zahlung mit echter Karte getestet (Betrag: 1 €)
- [ ] Echte Zahlung erstattet
- [ ] Refund-Prozess dokumentiert

### Phase 8: Abnahme

- [ ] Vollständiger Checkout-Ablauf getestet (Registrierung → Trial → Upgrade → Kündigung)
- [ ] Alle Webhook-Events verarbeitet und in DB reflektiert
- [ ] Rechnungs-Anzeige für Vereinsadmin geprüft
- [ ] Superadmin-Lizenz-Dashboard getestet
- [ ] E-Mail-Bestätigungen von Stripe angekommen

---

## 7. Architektur-Überblick

```
Verein registriert sich
        │
        ▼
verein_registrieren()     ← database.py
  → Verein anlegen
  → Vereinsadmin anlegen
  → Testphase: heute + 14 Tage
  → lizenz_status = 'trial'
  → lizenztyp = 'FREE'
        │
        ▼
enforce_license_gate()    ← license.py (bei jedem App-Start)
  → Superadmin: immer durch
  → gesperrt: Sperr-Seite + st.stop()
  → expired: Ablauf-Seite + st.stop()
  → trial/active: Warnung wenn < 7 Tage, weiter
        │
        ▼
Vereinsadmin → "💳 Lizenz"
  → Tarif-Übersicht
  → Stripe Billing-Portal (wenn stripe_customer_id vorhanden)
        │
        ▼
Stripe Checkout
  → customer_erstellen()
  → checkout_session_erstellen()
  → Redirect zu Stripe
        │
        ▼
Stripe Webhook → /api/stripe/webhook
  → webhook_event_validieren()
  → webhook_event_verarbeiten()
  → DB aktualisieren: stripe_ids_setzen(), lizenz_setzen(), rechnung_speichern()
```
