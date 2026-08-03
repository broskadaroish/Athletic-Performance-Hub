/**
 * Stripe Webhook Empfänger — Bruce Football Performance Diagnostics
 *
 * Aktivierung für Livebetrieb:
 *   1. STRIPE_SECRET_KEY und STRIPE_WEBHOOK_SECRET als Env-Vars setzen
 *   2. pnpm --filter @workspace/api-server add stripe
 *   3. Webhook-URL in Stripe-Dashboard: POST /api/stripe/webhook
 *      Events: checkout.session.completed, customer.subscription.updated,
 *              customer.subscription.deleted, invoice.payment_failed,
 *              invoice.payment_succeeded
 */
import { Router, type IRouter } from "express";
import { logger } from "../lib/logger";
import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";

const router: IRouter = Router();

// ── DB-Verbindung (gleiche SQLite-Datei wie die Athletik-App) ─────────────────
const __dirnameHere = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_DB = path.resolve(
  __dirnameHere,
  "../../../../artifacts/athletik/athletik.db",
);
const DB_PATH = process.env["ATHLETIK_DB_PATH"] ?? DEFAULT_DB;

function getDb() {
  const conn = new Database(DB_PATH, { readonly: false });
  conn.pragma("journal_mode = WAL");
  conn.pragma("foreign_keys = ON");
  return conn;
}

// ── Hilfsfunktionen ────────────────────────────────────────────────────────────

function lizenzTypAusPrice(priceId: string): "BASIC" | "PRO" | null {
  const basicIds = [
    process.env["STRIPE_PRICE_BASIC_MONAT"],
    process.env["STRIPE_PRICE_BASIC_JAHR"],
  ].filter(Boolean) as string[];
  const proIds = [
    process.env["STRIPE_PRICE_PRO_MONAT"],
    process.env["STRIPE_PRICE_PRO_JAHR"],
  ].filter(Boolean) as string[];
  if (basicIds.includes(priceId)) return "BASIC";
  if (proIds.includes(priceId)) return "PRO";
  return null;
}

function iso(ts: number | null | undefined): string | null {
  if (!ts) return null;
  return new Date(ts * 1000).toISOString().slice(0, 10);
}

// ── Webhook-Endpunkt ───────────────────────────────────────────────────────────

router.post("/stripe/webhook", async (req, res): Promise<void> => {
  const webhookSecret = process.env["STRIPE_WEBHOOK_SECRET"];
  const stripeKey = process.env["STRIPE_SECRET_KEY"];

  type StripeEvent = { type: string; data: { object: Record<string, unknown> } };
  let event: StripeEvent;

  if (webhookSecret && stripeKey) {
    const sig = req.headers["stripe-signature"] as string | undefined;
    if (!sig) {
      res.status(400).json({ error: "Keine Webhook-Signatur" });
      return;
    }
    try {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const Stripe = require("stripe");
      const stripe = new Stripe(stripeKey, { apiVersion: "2024-06-20" });
      event = stripe.webhooks.constructEvent(req.body as Buffer, sig, webhookSecret) as StripeEvent;
    } catch (err) {
      logger.warn({ err }, "Ungültige Stripe-Webhook-Signatur");
      res.status(400).json({ error: "Signaturprüfung fehlgeschlagen" });
      return;
    }
  } else {
    // Entwicklungsmodus — Signatur überspringen
    event = req.body as StripeEvent;
  }

  logger.info({ type: event.type }, "Stripe Webhook empfangen");
  const obj = event.data.object;

  try {
    const conn = getDb();

    switch (event.type) {
      // ── Checkout abgeschlossen → Lizenz aktivieren ───────────────────────────
      case "checkout.session.completed": {
        const vereinId = Number((obj["metadata"] as Record<string, string>)?.["verein_id"]);
        const customerId = obj["customer"] as string;
        const subscriptionId = obj["subscription"] as string;
        if (!vereinId) break;

        conn.prepare(
          `UPDATE vereine
              SET lizenz_status          = 'active',
                  zahlungsstatus         = 'bezahlt',
                  stripe_customer_id     = ?,
                  stripe_subscription_id = ?,
                  lizenz_bis             = date('now', '+1 month')
            WHERE id = ?`
        ).run(customerId, subscriptionId, vereinId);

        logger.info({ vereinId, customerId }, "Lizenz aktiviert nach Checkout");
        break;
      }

      // ── Abonnement aktualisiert (Upgrade/Downgrade/Verlängerung) ────────────
      case "customer.subscription.updated": {
        const subscriptionId = obj["id"] as string;
        type SubObj = { items?: { data?: Array<{ price?: { id?: string } }> }; status?: string; current_period_end?: number; cancel_at_period_end?: boolean; customer?: string };
        const sub = obj as SubObj;
        const priceId = sub.items?.data?.[0]?.price?.id ?? "";
        const lizenzTyp = lizenzTypAusPrice(priceId);
        const status = sub.status ?? "";
        const periodEnd = iso(sub.current_period_end);
        const cancelAtPeriodEnd = Boolean(sub.cancel_at_period_end);

        const lizenzStatus =
          status === "active" && !cancelAtPeriodEnd ? "active"
          : status === "active" && cancelAtPeriodEnd ? "cancelled"
          : status === "trialing" ? "trial"
          : "expired";

        conn.prepare(
          `UPDATE vereine
              SET lizenz_status          = ?,
                  lizenztyp              = COALESCE(?, lizenztyp),
                  lizenz_bis             = COALESCE(?, lizenz_bis),
                  stripe_subscription_id = ?
            WHERE stripe_subscription_id = ? OR stripe_customer_id = ?`
        ).run(lizenzStatus, lizenzTyp, periodEnd, subscriptionId, subscriptionId, sub.customer ?? "");

        logger.info({ subscriptionId, lizenzStatus }, "Abonnement aktualisiert");
        break;
      }

      // ── Abonnement gelöscht → Zugang deaktivieren ────────────────────────────
      case "customer.subscription.deleted": {
        const subscriptionId = obj["id"] as string;
        const periodEnd = iso(obj["current_period_end"] as number | undefined);
        conn.prepare(
          `UPDATE vereine
              SET lizenz_status = 'expired',
                  lizenz_bis    = COALESCE(?, lizenz_bis)
            WHERE stripe_subscription_id = ?`
        ).run(periodEnd, subscriptionId);
        logger.info({ subscriptionId }, "Abonnement gelöscht");
        break;
      }

      // ── Zahlung fehlgeschlagen ────────────────────────────────────────────────
      case "invoice.payment_failed": {
        const customerId = obj["customer"] as string;
        conn.prepare(
          `UPDATE vereine SET zahlungsstatus = 'fehlgeschlagen' WHERE stripe_customer_id = ?`
        ).run(customerId);
        logger.warn({ customerId }, "Stripe-Zahlung fehlgeschlagen");
        break;
      }

      // ── Rechnung bezahlt → Status bestätigen ─────────────────────────────────
      case "invoice.payment_succeeded": {
        const customerId = obj["customer"] as string;
        type InvObj = { lines?: { data?: Array<{ period?: { end?: number } }> } };
        const periodEnd = iso((obj as InvObj).lines?.data?.[0]?.period?.end);
        conn.prepare(
          `UPDATE vereine
              SET zahlungsstatus = 'bezahlt',
                  lizenz_status  = 'active',
                  lizenz_bis     = COALESCE(?, lizenz_bis)
            WHERE stripe_customer_id = ?`
        ).run(periodEnd, customerId);
        logger.info({ customerId }, "Zahlung bestätigt");
        break;
      }

      default:
        logger.debug({ type: event.type }, "Unbehandeltes Stripe Event");
    }

    conn.close();
  } catch (err) {
    logger.error({ err, type: event.type }, "Fehler beim Verarbeiten des Stripe Events");
    // 200 zurückgeben — Stripe soll nicht wiederholt senden
  }

  res.status(200).json({ received: true });
});

export default router;
