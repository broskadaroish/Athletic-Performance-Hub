/**
 * Stripe Webhook Empfänger — APH System
 *
 * Öffentlicher POST-Endpunkt: /api/stripe/webhook
 * Produktions-URL:            https://aphsystem.de/api/stripe/webhook
 *
 * Verarbeitete Events (6):
 *   checkout.session.completed
 *   customer.subscription.created
 *   customer.subscription.updated
 *   customer.subscription.deleted
 *   invoice.paid
 *   invoice.payment_failed
 *
 * Sicherheit:
 *   - Stripe-Signatur wird mit STRIPE_WEBHOOK_SECRET geprüft
 *   - STRIPE_SECRET_KEY und STRIPE_WEBHOOK_SECRET werden NIEMALS geloggt
 *   - Idempotenz: jedes Stripe-Event wird genau einmal verarbeitet (stripe_events-Tabelle)
 *   - Tarif-Zuordnung ausschließlich über Stripe Price-IDs aus Env-Vars — nie über Namen/Betrag
 *
 * Hinweis: app.ts registriert express.raw({ type: "application/json" }) VOR express.json()
 * für diesen Pfad, damit req.body als Buffer ankommt und die Signaturprüfung funktioniert.
 */
import { Router, type IRouter, type Request, type Response } from "express";
import { logger } from "../lib/logger";
import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";

const router: IRouter = Router();

// ── DB-Verbindung (gleiche SQLite-Datei wie die Athletik-App) ─────────────────
const __dirnameHere = path.dirname(fileURLToPath(import.meta.url));
// Nach esbuild-Bundling liegt dist/index.mjs im dist/-Verzeichnis:
//   workspace/artifacts/api-server/dist  →  ../../../  →  workspace/
// Daher 3 Ebenen hoch, nicht 4 (wie fälschlicherweise im Original).
const DEFAULT_DB = path.resolve(
  __dirnameHere,
  "../../../artifacts/athletik/athletik.db",
);
const DB_PATH = process.env["ATHLETIK_DB_PATH"] ?? DEFAULT_DB;

function getDb(): Database.Database {
  const conn = new Database(DB_PATH, { readonly: false });
  conn.pragma("journal_mode = WAL");
  conn.pragma("foreign_keys = ON");
  return conn;
}

// ── One-time DB schema extensions ─────────────────────────────────────────────
// Fügt fehlende Spalten und die Idempotenz-Tabelle hinzu.
// Läuft beim ersten Webhook-Aufruf — idempotent und migrationssicher.

let _dbInitialized = false;

function ensureDbExtensions(): void {
  if (_dbInitialized) return;
  const conn = getDb();
  try {
    // Idempotenz-Tabelle für Stripe Events
    conn.exec(`
      CREATE TABLE IF NOT EXISTS stripe_events (
        event_id     TEXT PRIMARY KEY,
        event_type   TEXT,
        processed_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `);
    // Neue vereine-Spalten — ALTER TABLE schlägt still fehl wenn bereits vorhanden
    for (const [col, def] of [
      ["cancel_at_period_end",            "INTEGER DEFAULT 0"],
      ["subscription_current_period_end", "TEXT"],
    ] as [string, string][]) {
      try {
        conn.exec(`ALTER TABLE vereine ADD COLUMN ${col} ${def}`);
      } catch {
        // Spalte existiert bereits — kein Fehler
      }
    }
    _dbInitialized = true;
    logger.info("Stripe DB-Erweiterungen initialisiert");
  } finally {
    conn.close();
  }
}

// ── Tarif-Zuordnung über Stripe Price-IDs ─────────────────────────────────────
// Unterstützt beide Suffix-Varianten: _MONAT/_MONTHLY und _JAHR/_YEARLY,
// da die Secrets inkonsistent benannt wurden (mix DE/EN).

type LizenzTyp = "TRAINER_BASIC" | "TRAINER_PRO" | "VEREIN_BASIC" | "VEREIN_PRO";

function lizenzTypAusPrice(priceId: string): LizenzTyp | null {
  if (!priceId) return null;
  const e = (k: string): string => process.env[k] ?? "";

  const mapping: Array<[string[], LizenzTyp]> = [
    [
      [e("STRIPE_PRICE_TRAINER_BASIC_MONAT"),  e("STRIPE_PRICE_TRAINER_BASIC_MONTHLY"),
       e("STRIPE_PRICE_TRAINER_BASIC_JAHR"),   e("STRIPE_PRICE_TRAINER_BASIC_YEARLY")],
      "TRAINER_BASIC",
    ],
    [
      [e("STRIPE_PRICE_TRAINER_PRO_MONAT"),    e("STRIPE_PRICE_TRAINER_PRO_MONTHLY"),
       e("STRIPE_PRICE_TRAINER_PRO_JAHR"),     e("STRIPE_PRICE_TRAINER_PRO_YEARLY")],
      "TRAINER_PRO",
    ],
    [
      [e("STRIPE_PRICE_VEREIN_BASIC_MONAT"),   e("STRIPE_PRICE_VEREIN_BASIC_MONTHLY"),
       e("STRIPE_PRICE_VEREIN_BASIC_JAHR"),    e("STRIPE_PRICE_VEREIN_BASIC_YEARLY")],
      "VEREIN_BASIC",
    ],
    [
      [e("STRIPE_PRICE_VEREIN_PRO_MONAT"),     e("STRIPE_PRICE_VEREIN_PRO_MONTHLY"),
       e("STRIPE_PRICE_VEREIN_PRO_JAHR"),      e("STRIPE_PRICE_VEREIN_PRO_YEARLY")],
      "VEREIN_PRO",
    ],
  ];

  for (const [ids, typ] of mapping) {
    if ((ids.filter(Boolean) as string[]).includes(priceId)) return typ;
  }
  return null;   // Price-ID keinem Paket zugeordnet
}

// ── Abrechnungsintervall aus Price-ID bestimmen ────────────────────────────────
function intervallAusPrice(priceId: string): "monat" | "jahr" | null {
  if (!priceId) return null;
  const e = (k: string): string => process.env[k] ?? "";

  const monatIds = [
    e("STRIPE_PRICE_TRAINER_BASIC_MONAT"),  e("STRIPE_PRICE_TRAINER_BASIC_MONTHLY"),
    e("STRIPE_PRICE_TRAINER_PRO_MONAT"),    e("STRIPE_PRICE_TRAINER_PRO_MONTHLY"),
    e("STRIPE_PRICE_VEREIN_BASIC_MONAT"),   e("STRIPE_PRICE_VEREIN_BASIC_MONTHLY"),
    e("STRIPE_PRICE_VEREIN_PRO_MONAT"),     e("STRIPE_PRICE_VEREIN_PRO_MONTHLY"),
  ].filter(Boolean) as string[];

  const jahrIds = [
    e("STRIPE_PRICE_TRAINER_BASIC_JAHR"),   e("STRIPE_PRICE_TRAINER_BASIC_YEARLY"),
    e("STRIPE_PRICE_TRAINER_PRO_JAHR"),     e("STRIPE_PRICE_TRAINER_PRO_YEARLY"),
    e("STRIPE_PRICE_VEREIN_BASIC_JAHR"),    e("STRIPE_PRICE_VEREIN_BASIC_YEARLY"),
    e("STRIPE_PRICE_VEREIN_PRO_JAHR"),      e("STRIPE_PRICE_VEREIN_PRO_YEARLY"),
  ].filter(Boolean) as string[];

  if (monatIds.includes(priceId)) return "monat";
  if (jahrIds.includes(priceId)) return "jahr";
  return null;
}

// ── Hilfsfunktionen ────────────────────────────────────────────────────────────

function isoDate(ts: number | null | undefined): string | null {
  if (!ts) return null;
  return new Date(ts * 1000).toISOString().slice(0, 10);
}

function subLizenzStatus(
  status: string,
  cancelAtPeriodEnd: boolean,
): string {
  if (status === "trialing")                           return "trial";
  if (status === "active" && !cancelAtPeriodEnd)       return "active";
  if (status === "active" && cancelAtPeriodEnd)        return "cancelled";
  if (status === "past_due" || status === "unpaid")    return "active"; // noch aktiv, zahlung ausstehend
  return "expired";
}

// ── Event-Typen ────────────────────────────────────────────────────────────────

interface StripeEvent {
  id: string;
  type: string;
  data: { object: Record<string, unknown> };
}

interface SubscriptionObj {
  id?: string;
  status?: string;
  customer?: string;
  current_period_end?: number;
  cancel_at_period_end?: boolean;
  items?: { data?: Array<{ price?: { id?: string } }> };
  metadata?: Record<string, string>;
}

// ── Webhook-Endpunkt ───────────────────────────────────────────────────────────

router.post("/stripe/webhook", (req: Request, res: Response): void => {
  const webhookSecret = process.env["STRIPE_WEBHOOK_SECRET"];
  const stripeKey     = process.env["STRIPE_SECRET_KEY"];

  let event: StripeEvent;

  // ── Signaturprüfung ───────────────────────────────────────────────────────────
  if (webhookSecret && stripeKey) {
    const sig = req.headers["stripe-signature"] as string | undefined;
    if (!sig) {
      logger.warn("Stripe Webhook: fehlende stripe-signature Header");
      res.status(400).json({ error: "Fehlende Stripe-Webhook-Signatur" });
      return;
    }
    try {
      // Dynamic require — stripe ist optional bis STRIPE_SECRET_KEY gesetzt ist.
      // req.body ist hier ein Buffer dank express.raw() in app.ts.
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const Stripe = require("stripe");
      const stripe = new Stripe(stripeKey, { apiVersion: "2024-06-20" });
      event = stripe.webhooks.constructEvent(
        req.body as Buffer,
        sig,
        webhookSecret,
      ) as StripeEvent;
    } catch (err) {
      // Signatur ungültig — Schlüssel wird NICHT geloggt
      logger.warn(
        { errType: (err as Error).constructor?.name },
        "Stripe Webhook: Signaturprüfung fehlgeschlagen",
      );
      res.status(400).json({ error: "Signaturprüfung fehlgeschlagen" });
      return;
    }
  } else {
    // Entwicklungsmodus — Signatur wird übersprungen
    const raw = req.body;
    event = (Buffer.isBuffer(raw)
      ? (JSON.parse(raw.toString("utf-8")) as StripeEvent)
      : (raw as StripeEvent));
    logger.warn(
      "Stripe Webhook: Signaturprüfung deaktiviert (STRIPE_WEBHOOK_SECRET nicht gesetzt)",
    );
  }

  const eventId   = event.id   ?? "unknown";
  const eventType = event.type ?? "";

  logger.info({ eventId, eventType }, "Stripe Webhook empfangen");

  // DB-Erweiterungen nur einmalig initialisieren — nach erfolgreicher Signaturprüfung
  ensureDbExtensions();

  const conn = getDb();
  try {
    // ── Idempotenz: bereits verarbeitete Events überspringen ───────────────────
    const already = conn
      .prepare("SELECT 1 FROM stripe_events WHERE event_id = ?")
      .get(eventId);
    if (already) {
      logger.info({ eventId, eventType }, "Stripe Event bereits verarbeitet — übersprungen");
      res.status(200).json({ received: true });
      return;
    }

    const obj = event.data.object;

    switch (eventType) {

      // ── 1. Checkout abgeschlossen ──────────────────────────────────────────────
      case "checkout.session.completed": {
        const meta       = (obj["metadata"] as Record<string, string> | undefined) ?? {};
        const vereinId   = Number(meta["verein_id"]) || null;
        const customerId = obj["customer"] as string | null;
        const subId      = obj["subscription"] as string | null;

        if (!vereinId) {
          logger.warn({ eventId }, "checkout.session.completed: keine verein_id in metadata — Event ignoriert");
          break;
        }
        // Tarif wird über customer.subscription.created/updated gesetzt.
        // Hier: IDs + Aktivierung. Keine Tarif-Änderung allein auf Basis dieses Events.
        conn.prepare(`
          UPDATE vereine
             SET lizenz_status          = 'active',
                 zahlungsstatus         = 'bezahlt',
                 stripe_customer_id     = COALESCE(?, stripe_customer_id),
                 stripe_subscription_id = COALESCE(?, stripe_subscription_id)
           WHERE id = ?
        `).run(customerId, subId, vereinId);

        logger.info({ vereinId, eventId }, "Checkout abgeschlossen — Lizenz aktiviert");
        break;
      }

      // ── 2. Abonnement erstellt ─────────────────────────────────────────────────
      case "customer.subscription.created": {
        const sub         = obj as SubscriptionObj;
        const subId       = sub.id ?? "";
        const priceId     = sub.items?.data?.[0]?.price?.id ?? "";
        const lizenzTyp   = lizenzTypAusPrice(priceId);
        const intervall   = intervallAusPrice(priceId);
        const status      = sub.status ?? "";
        const cancelAtEnd = Boolean(sub.cancel_at_period_end);
        const periodEnd   = isoDate(sub.current_period_end);
        const customerId  = sub.customer ?? "";
        const lizenzStatus = subLizenzStatus(status, cancelAtEnd);

        conn.prepare(`
          UPDATE vereine
             SET stripe_subscription_id          = ?,
                 stripe_customer_id              = COALESCE(?, stripe_customer_id),
                 lizenz_status                   = ?,
                 lizenztyp                       = COALESCE(?, lizenztyp),
                 abo_intervall                   = COALESCE(?, abo_intervall),
                 lizenz_bis                      = COALESCE(?, lizenz_bis),
                 subscription_current_period_end = COALESCE(?, subscription_current_period_end),
                 cancel_at_period_end            = ?
           WHERE stripe_customer_id = ? OR stripe_subscription_id = ?
        `).run(
          subId, customerId, lizenzStatus,
          lizenzTyp, intervall,
          periodEnd, periodEnd,
          cancelAtEnd ? 1 : 0,
          customerId, subId,
        );

        logger.info({ subId, lizenzTyp, intervall, lizenzStatus, eventId }, "Abonnement erstellt");
        break;
      }

      // ── 3. Abonnement aktualisiert (Upgrade/Downgrade/Verlängerung/Kündigung) ──
      case "customer.subscription.updated": {
        const sub         = obj as SubscriptionObj;
        const subId       = sub.id ?? "";
        const priceId     = sub.items?.data?.[0]?.price?.id ?? "";
        const lizenzTyp   = lizenzTypAusPrice(priceId);
        const intervall   = intervallAusPrice(priceId);
        const status      = sub.status ?? "";
        const cancelAtEnd = Boolean(sub.cancel_at_period_end);
        const periodEnd   = isoDate(sub.current_period_end);
        const customerId  = sub.customer ?? "";
        const lizenzStatus = subLizenzStatus(status, cancelAtEnd);

        conn.prepare(`
          UPDATE vereine
             SET lizenz_status                   = ?,
                 lizenztyp                       = COALESCE(?, lizenztyp),
                 abo_intervall                   = COALESCE(?, abo_intervall),
                 lizenz_bis                      = COALESCE(?, lizenz_bis),
                 subscription_current_period_end = COALESCE(?, subscription_current_period_end),
                 cancel_at_period_end            = ?,
                 stripe_subscription_id          = ?
           WHERE stripe_subscription_id = ? OR stripe_customer_id = ?
        `).run(
          lizenzStatus,
          lizenzTyp, intervall,
          periodEnd, periodEnd,
          cancelAtEnd ? 1 : 0, subId,
          subId, customerId,
        );

        logger.info({ subId, lizenzTyp, lizenzStatus, cancelAtEnd, eventId }, "Abonnement aktualisiert");
        break;
      }

      // ── 4. Abonnement beendet → Zugang entziehen, Daten behalten ─────────────
      case "customer.subscription.deleted": {
        const subId     = obj["id"] as string;
        const periodEnd = isoDate(obj["current_period_end"] as number | undefined);

        conn.prepare(`
          UPDATE vereine
             SET lizenz_status        = 'expired',
                 lizenz_bis           = COALESCE(?, lizenz_bis),
                 cancel_at_period_end = 0
           WHERE stripe_subscription_id = ?
        `).run(periodEnd, subId);

        // Konto und Kundendaten bleiben erhalten — nur kostenpflichtige Features gesperrt
        logger.info({ subId, eventId }, "Abonnement beendet — Lizenz auf expired gesetzt");
        break;
      }

      // ── 5. Rechnung bezahlt (invoice.paid ist der empfohlene Event-Name) ───────
      case "invoice.paid":
      case "invoice.payment_succeeded": {
        const customerId = obj["customer"] as string;
        interface InvObj {
          lines?: { data?: Array<{ period?: { end?: number }; price?: { id?: string } }> };
        }
        const inv       = obj as InvObj;
        const periodEnd = isoDate(inv.lines?.data?.[0]?.period?.end);

        conn.prepare(`
          UPDATE vereine
             SET zahlungsstatus                  = 'bezahlt',
                 lizenz_status                   = 'active',
                 lizenz_bis                      = COALESCE(?, lizenz_bis),
                 subscription_current_period_end = COALESCE(?, subscription_current_period_end)
           WHERE stripe_customer_id = ?
        `).run(periodEnd, periodEnd, customerId);

        logger.info({ customerId, periodEnd, eventId }, "Zahlung bestätigt");
        break;
      }

      // ── 6. Zahlung fehlgeschlagen → Status markieren, KEIN Account-Löschen ───
      case "invoice.payment_failed": {
        const customerId = obj["customer"] as string;

        conn.prepare(`
          UPDATE vereine
             SET zahlungsstatus = 'fehlgeschlagen'
           WHERE stripe_customer_id = ?
        `).run(customerId);

        // Benutzerkonto und Daten bleiben unberührt — nur Status für Support sichtbar
        logger.warn({ customerId, eventId }, "Stripe-Zahlung fehlgeschlagen");
        break;
      }

      default:
        logger.debug({ eventType, eventId }, "Unbehandeltes Stripe Event — wird ignoriert");
    }

    // ── Als verarbeitet markieren (Idempotenz) ────────────────────────────────
    conn
      .prepare("INSERT OR IGNORE INTO stripe_events (event_id, event_type) VALUES (?, ?)")
      .run(eventId, eventType);

  } catch (err) {
    // Fehler beim Verarbeiten — HTTP 200 trotzdem, damit Stripe nicht wiederholt sendet.
    // Fehlerdetails im Log nachvollziehbar.
    logger.error(
      { errMsg: (err as Error).message, eventType, eventId },
      "Fehler beim Verarbeiten des Stripe Events",
    );
  } finally {
    conn.close();
  }

  res.status(200).json({ received: true });
});

export default router;
