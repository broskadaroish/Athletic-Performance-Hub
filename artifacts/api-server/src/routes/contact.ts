import { Router, type IRouter } from "express";
import { SubmitContactBody, SubmitContactResponse, SubmitLeadBody, SubmitLeadResponse } from "@workspace/api-zod";

const router: IRouter = Router();

// POST /contact — Kontaktformular
router.post("/contact", async (req, res): Promise<void> => {
  const parsed = SubmitContactBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const { name, email, subject, message, phone } = parsed.data;

  // Lazy import — @workspace/db (PostgreSQL) wird erst beim ersten Aufruf initialisiert,
  // nicht beim Server-Start. Verhindert, dass DATABASE_URL beim Start zwingend nötig ist,
  // wenn ausschließlich SQLite-Routen (z. B. Stripe-Webhook) genutzt werden.
  const { db, contactsTable } = await import("@workspace/db");

  await db.insert(contactsTable).values({
    name,
    email,
    subject: subject ?? null,
    message,
    phone: phone ?? null,
  });

  req.log.info({ email }, "Kontaktanfrage eingegangen");

  const result = SubmitContactResponse.parse({
    success: true,
    message: "Vielen Dank! Wir melden uns innerhalb von 1–2 Werktagen.",
  });
  res.status(201).json(result);
});

// POST /leads — Demo-Anfrage
router.post("/leads", async (req, res): Promise<void> => {
  const parsed = SubmitLeadBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.message });
    return;
  }

  const { name, email, vereinsname, telefon, spieleranzahl, nachricht, plan } = parsed.data;

  const { db, leadsTable } = await import("@workspace/db");

  await db.insert(leadsTable).values({
    name,
    email,
    vereinsname,
    telefon: telefon ?? null,
    spieleranzahl: spieleranzahl ?? null,
    nachricht: nachricht ?? null,
    plan: plan ?? null,
  });

  req.log.info({ email, vereinsname, plan }, "Demo-Anfrage eingegangen");

  const result = SubmitLeadResponse.parse({
    success: true,
    message: "Demo-Anfrage erhalten! Wir kontaktieren dich in Kürze.",
  });
  res.status(201).json(result);
});

export default router;
