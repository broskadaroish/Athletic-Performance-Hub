import { pgTable, serial, text, timestamp, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

// ── Kontaktanfragen ──────────────────────────────────────────────────────────
export const contactsTable = pgTable("contacts", {
  id:         serial("id").primaryKey(),
  name:       text("name").notNull(),
  email:      text("email").notNull(),
  subject:    text("subject"),
  message:    text("message").notNull(),
  phone:      text("phone"),
  gelesen:    boolean("gelesen").default(false),
  createdAt:  timestamp("created_at").defaultNow().notNull(),
});

export const insertContactSchema = createInsertSchema(contactsTable).omit({ id: true, createdAt: true });
export type InsertContact = z.infer<typeof insertContactSchema>;
export type Contact = typeof contactsTable.$inferSelect;

// ── Demo-Anfragen / Leads ────────────────────────────────────────────────────
export const leadsTable = pgTable("leads", {
  id:            serial("id").primaryKey(),
  name:          text("name").notNull(),
  email:         text("email").notNull(),
  vereinsname:   text("vereinsname").notNull(),
  telefon:       text("telefon"),
  spieleranzahl: text("spieleranzahl"),
  nachricht:     text("nachricht"),
  plan:          text("plan"),          // starter | professional | enterprise
  status:        text("status").default("neu"),  // neu | kontaktiert | gewonnen | verloren
  gelesen:       boolean("gelesen").default(false),
  createdAt:     timestamp("created_at").defaultNow().notNull(),
});

export const insertLeadSchema = createInsertSchema(leadsTable).omit({ id: true, createdAt: true });
export type InsertLead = z.infer<typeof insertLeadSchema>;
export type Lead = typeof leadsTable.$inferSelect;
