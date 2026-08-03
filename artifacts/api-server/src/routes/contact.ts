import { Router, type IRouter } from "express";
import { db } from "@workspace/db";
import { contactsTable, leadsTable } from "@workspace/db";
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
