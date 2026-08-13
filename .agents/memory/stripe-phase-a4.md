---
name: Stripe Webhook Phase A4
description: Implementierungsdetails, Fallstricke und Entscheidungen für den Stripe Webhook im API-Server
---

## Kritischer Pfad-Fallstrick (esbuild)

Nach esbuild-Bundling (`dist/index.mjs`) zeigt `fileURLToPath(import.meta.url)` in ALLEN
Source-Dateien auf dasselbe `dist/`-Verzeichnis. Deshalb muss jede SQLite-Pfad-Berechnung
in `artifacts/api-server/` **3 Ebenen hoch** (`../../../`) — nicht 4:

```
workspace/artifacts/api-server/dist  →  ../../../  →  workspace/
```

Der originale `stripe.ts` hatte `../../../../` (4 Ebenen) — das war falsch.
Referenz-Implementierung: `athletik-db.ts` (nutzt korrekt `../../../`).

**Why:** Esbuild fasst alle Module zu einer einzigen `dist/index.mjs` zusammen.
Alle `import.meta.url`-Ausdrücke expandieren zur Dist-Datei, nicht zum Source-Pfad.

## express.raw() vor express.json() für Stripe Webhook

In `app.ts` muss die Middleware-Reihenfolge zwingend so sein:

```typescript
// ZUERST: raw body für Stripe-Webhook-Pfad
app.use("/api/stripe/webhook", express.raw({ type: "application/json" }));
// DANN: JSON-Parsing für alle anderen Routen
app.use(express.json());
```

**Why:** Stripe-Signaturprüfung benötigt den unveränderten Request Body als Buffer.
`express.json()` parst ihn zu einem JS-Objekt — danach ist Signaturprüfung unmöglich.

## Secret-Namens-Mischung (DE/EN-Suffixe)

Gesetzte Secrets sind inkonsistent benannt (historisch):
- `STRIPE_PRICE_TRAINER_BASIC_MONAT` (Deutsch!)
- `STRIPE_PRICE_TRAINER_PRO_MONTHLY` (Englisch!)
- etc.

Lösung: `_price_env(base, short)` Hilfsfunktion in `stripe_service.py` und
`lizenzTypAusPrice()` in `stripe.ts` prüfen beide Varianten:
- `_MONAT` / `_MONTHLY` für "monat"
- `_JAHR` / `_YEARLY` für "jahr"

## Idempotenz via stripe_events-Tabelle

Tabelle wird beim ersten Webhook-Aufruf automatisch angelegt (nach Signaturprüfung):
```sql
CREATE TABLE IF NOT EXISTS stripe_events (
  event_id     TEXT PRIMARY KEY,
  event_type   TEXT,
  processed_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

Stripe Event-IDs beginnen mit `evt_`. Beim zweiten Aufruf mit derselben ID: 200 zurück,
keine weitere DB-Änderung.

## Neue vereine-Spalten (via Migration in ensureDbExtensions)

- `cancel_at_period_end INTEGER DEFAULT 0`
- `subscription_current_period_end TEXT`

Werden via `ALTER TABLE` mit try/except (bereits vorhanden = kein Fehler) hinzugefügt.

## STRIPE_WEBHOOK_SECRET fehlt noch!

Muss vom Nutzer im Stripe-Dashboard erstellt werden:
- URL: `https://aphsystem.de/api/stripe/webhook`
- Events: `checkout.session.completed`, `customer.subscription.created/updated/deleted`,
  `invoice.paid`, `invoice.payment_failed`
- Signing Secret als `STRIPE_WEBHOOK_SECRET` Env-Var setzen

Ohne dieses Secret läuft der Webhook im Dev-Modus (keine Signaturprüfung).

## Alle 6 Events und ihre DB-Aktionen

| Event | DB-Aktion |
|---|---|
| `checkout.session.completed` | lizenz_status=active, IDs speichern |
| `customer.subscription.created` | lizenztyp + intervall + status setzen |
| `customer.subscription.updated` | lizenztyp + status + cancel_at_period_end |
| `customer.subscription.deleted` | lizenz_status=expired |
| `invoice.paid` / `invoice.payment_succeeded` | zahlungsstatus=bezahlt, lizenz_status=active |
| `invoice.payment_failed` | zahlungsstatus=fehlgeschlagen |
