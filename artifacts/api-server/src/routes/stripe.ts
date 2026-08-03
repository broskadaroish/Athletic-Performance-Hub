/**
 * Stripe Webhook Empfänger
 *
 * Für den Livebetrieb:
 *   1. STRIPE_SECRET_KEY und STRIPE_WEBHOOK_SECRET als Env-Vars setzen
 *   2. npm install stripe
 *   3. Signature-Prüfung aktivieren (auskommentierter Code unten)
 *   4. Event-Handler für relevante Events implementieren
 *      (customer.subscription.created, invoice.payment_succeeded, etc.)
 */
import { Router, type IRouter } from "express";
import { logger } from "../lib/logger";

const router: IRouter = Router();

router.post("/stripe/webhook", async (req, res): Promise<void> => {
  const body = req.body as { type?: string; id?: string };

  // ── Stripe-Signaturprüfung (aktivieren wenn STRIPE_WEBHOOK_SECRET gesetzt) ──
  // const sig = req.headers["stripe-signature"];
  // if (!sig || !process.env.STRIPE_WEBHOOK_SECRET) {
  //   res.status(400).json({ error: "Keine Webhook-Signatur" });
  //   return;
  // }
  // import Stripe from "stripe";
  // const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
  // let event: Stripe.Event;
  // try {
  //   event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  // } catch (err) {
  //   req.log.warn({ err }, "Ungültige Webhook-Signatur");
  //   res.status(400).json({ error: "Signaturprüfung fehlgeschlagen" });
  //   return;
  // }

  logger.info({ type: body.type, id: body.id }, "Stripe Webhook empfangen");

  // ── Event-Handler ──────────────────────────────────────────────────────────
  switch (body.type) {
    case "customer.subscription.created":
      // TODO: Verein in DB aktivieren, Zugang freischalten
      break;

    case "customer.subscription.deleted":
      // TODO: Verein-Zugang deaktivieren
      break;

    case "invoice.payment_succeeded":
      // TODO: Zahlung bestätigen, Abonnement verlängern
      break;

    case "invoice.payment_failed":
      // TODO: Trainer benachrichtigen, Zugang einschränken
      break;

    default:
      logger.debug({ type: body.type }, "Unbehandeltes Stripe Event");
  }

  res.status(200).json({ received: true });
});

export default router;
