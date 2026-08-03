/**
 * Direct SQLite access to the Athletik database for the mobile API.
 * Uses better-sqlite3 for synchronous queries (externalized from ESM build).
 */
import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pbkdf2Sync, randomBytes, timingSafeEqual } from "node:crypto";

// ─── DB Path ────────────────────────────────────────────────────────────────
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_DB = path.resolve(
  __dirname,
  "../../../../artifacts/athletik/athletik.db",
);
const DB_PATH = process.env["ATHLETIK_DB_PATH"] ?? DEFAULT_DB;

// ─── Startup accessibility check ─────────────────────────────────────────────
/**
 * Checks whether the SQLite database file exists and is readable.
 * Call this once at startup and log the result — it gives a clear early-warning
 * before any request fails with an opaque error.
 */
export function checkDbAccessible(): { ok: boolean; path: string; error?: string } {
  if (!fs.existsSync(DB_PATH)) {
    return { ok: false, path: DB_PATH, error: `Datenbankdatei nicht gefunden: ${DB_PATH}` };
  }
  try {
    fs.accessSync(DB_PATH, fs.constants.R_OK);
  } catch {
    return { ok: false, path: DB_PATH, error: `Datenbankdatei nicht lesbar (fehlende Berechtigung): ${DB_PATH}` };
  }
  return { ok: true, path: DB_PATH };
}

// ─── SQLITE_BUSY retry helpers ────────────────────────────────────────────────
/** Synchronous sleep via Atomics — safe inside the Node.js main thread. */
function sleep(ms: number): void {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function isBusy(err: unknown): boolean {
  if (err && typeof err === "object") {
    const e = err as { code?: string; message?: string };
    return (
      e.code === "SQLITE_BUSY" ||
      e.code === "SQLITE_LOCKED" ||
      (e.message?.includes("database is locked") ?? false)
    );
  }
  return false;
}

/**
 * Runs `fn` up to `retries + 1` times, pausing `delayMs` ms between attempts
 * whenever the database is locked (SQLITE_BUSY / SQLITE_LOCKED).
 * Use for read-only queries; write functions should let callers handle busy errors.
 */
function withRetry<T>(fn: () => T, retries = 2, delayMs = 200): T {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return fn();
    } catch (err) {
      if (isBusy(err) && attempt < retries) {
        sleep(delayMs);
        continue;
      }
      throw err;
    }
  }
  // Unreachable, but satisfies TypeScript
  throw new Error("withRetry: exhausted attempts");
}

function db(): Database.Database {
  const conn = new Database(DB_PATH, { readonly: false });
  conn.pragma("journal_mode = WAL");
  conn.pragma("foreign_keys = ON");
  return conn;
}

// ─── Password verification (PBKDF2 + legacy SHA-256) ────────────────────────
function verifyPassword(plain: string, stored: string): boolean {
  if (stored.startsWith("pbkdf2:")) {
    // Format: pbkdf2:<iterations>:<salt>:<hash>
    const [, iters, salt, hash] = stored.split(":");
    const derived = pbkdf2Sync(
      plain,
      Buffer.from(salt, "hex"),
      parseInt(iters, 10),
      32,
      "sha256",
    )
      .toString("hex");
    try {
      return timingSafeEqual(Buffer.from(hash, "hex"), Buffer.from(derived, "hex"));
    } catch {
      return false;
    }
  }
  // Legacy SHA-256 without salt
  const { createHash } = require("crypto");
  const legacy = createHash("sha256").update(plain).digest("hex");
  return legacy === stored;
}

// ─── Auth ────────────────────────────────────────────────────────────────────
export interface AthletikUser {
  id: number;
  email: string;
  vorname: string;
  nachname: string;
  rolle: string;
  verein_id: number | null;
  verein_name: string | null;
  passwort_hash: string;
}

export function findUserByEmail(email: string): AthletikUser | null {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare(
          `SELECT b.id, b.email, b.vorname, b.nachname, b.rolle,
                  b.verein_id, b.passwort_hash, v.name AS verein_name
           FROM benutzer b
           LEFT JOIN vereine v ON b.verein_id = v.id
           WHERE b.email = ? AND b.aktiv = 1`,
        )
        .get(email) as AthletikUser | undefined;
      return row ?? null;
    } finally {
      conn.close();
    }
  });
}

export function loginUser(
  email: string,
  password: string,
): Omit<AthletikUser, "passwort_hash"> | null {
  const user = findUserByEmail(email);
  if (!user) return null;
  if (!verifyPassword(password, user.passwort_hash)) return null;
  const { passwort_hash: _ph, ...safe } = user;
  return safe;
}

// ─── Players ─────────────────────────────────────────────────────────────────
export interface AthletikPlayer {
  id: number;
  name: string;
  vorname: string;
  nachname: string;
  mannschaft: string | null;
  altersklasse: string | null;
  geburtsdatum: string | null;
  geschlecht: string | null;
  trainer_id: number | null;
  verein_id: number | null;
}

export function getPlayers(
  userId: number,
  rolle: string,
  vereinId: number | null,
): AthletikPlayer[] {
  return withRetry(() => {
    const conn = db();
    try {
      if (rolle === "Superadmin") {
        return conn
          .prepare("SELECT * FROM spieler ORDER BY name")
          .all() as AthletikPlayer[];
      }
      if (rolle === "Vereinsadmin") {
        return conn
          .prepare(
            "SELECT * FROM spieler WHERE verein_id = ? ORDER BY name",
          )
          .all(vereinId) as AthletikPlayer[];
      }
      // Trainer: only own players
      return conn
        .prepare(
          "SELECT * FROM spieler WHERE trainer_id = ? ORDER BY name",
        )
        .all(userId) as AthletikPlayer[];
    } finally {
      conn.close();
    }
  });
}

export function getPlayerById(id: number): AthletikPlayer | null {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare("SELECT * FROM spieler WHERE id = ?")
        .get(id) as AthletikPlayer | undefined;
      return row ?? null;
    } finally {
      conn.close();
    }
  });
}

// ─── Latest Tests ─────────────────────────────────────────────────────────────
export interface FmsRow {
  datum: string;
  score: number;
  bewertung: string;
  asymmetrie: string | null;
  deep_squat?: number;
  hurdle_links?: number;
  hurdle_rechts?: number;
  inline_links?: number;
  inline_rechts?: number;
  shoulder_links?: number;
  shoulder_rechts?: number;
  aslr_links?: number;
  aslr_rechts?: number;
  trunk?: number;
  rotary_links?: number;
  rotary_rechts?: number;
}

export function getFmsLast(spielerId: number): FmsRow | null {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare(
          "SELECT * FROM fms_test WHERE spieler_id = ? ORDER BY id DESC LIMIT 1",
        )
        .get(spielerId) as FmsRow | undefined;
      return row ?? null;
    } finally {
      conn.close();
    }
  });
}

export interface SprintRow {
  datum: string;
  beste_5m?: number;
  beste_10m?: number;
  beste_20m?: number;
  beste_30m?: number;
  bewertung_10m?: string;
  bewertung_30m?: string;
}

export function getSprintLast(spielerId: number): SprintRow | null {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare(
          "SELECT datum, beste_5m, beste_10m, beste_20m, beste_30m, bewertung_10m, bewertung_30m FROM sprint_test WHERE spieler_id = ? ORDER BY id DESC LIMIT 1",
        )
        .get(spielerId) as SprintRow | undefined;
      return row ?? null;
    } finally {
      conn.close();
    }
  });
}

export interface YbalanceRow {
  datum: string;
  composite_rechts: number;
  composite_links: number;
  asymmetrie: string | null;
  anterior_rechts?: number;
  anterior_links?: number;
  posteromedial_rechts?: number;
  posteromedial_links?: number;
  posterolateral_rechts?: number;
  posterolateral_links?: number;
}

export function getYbalanceLast(spielerId: number): YbalanceRow | null {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare(
          "SELECT datum, composite_rechts, composite_links, asymmetrie, anterior_rechts, anterior_links, posteromedial_rechts, posteromedial_links, posterolateral_rechts, posterolateral_links FROM y_balance_test WHERE spieler_id = ? ORDER BY id DESC LIMIT 1",
        )
        .get(spielerId) as YbalanceRow | undefined;
      return row ?? null;
    } finally {
      conn.close();
    }
  });
}

// ─── Score computation ────────────────────────────────────────────────────────
const RATING_SCORES: Array<[string, number]> = [
  ["hervorragend", 90],
  ["sehr gut", 82],
  ["gut", 70],
  ["überdurchschnittlich", 62],
  ["durchschnittlich", 50],
  ["unterdurchschnittlich", 30],
  ["schlecht", 15],
];

function sprintSubScore(bewertung: string | null | undefined): number | null {
  if (!bewertung) return null;
  const lower = bewertung.toLowerCase();
  for (const [key, val] of RATING_SCORES) {
    if (lower.includes(key)) return val;
  }
  return null;
}

function fmsSubScore(score: number, asymmetrie: string | null | undefined): number {
  let sub = Math.round((score / 21) * 100);
  if (asymmetrie?.includes("Asymmetrie")) sub = Math.max(0, sub - 10);
  return sub;
}

function yBalanceSubScore(
  compR: number,
  compL: number,
  asymmetrie: string | null | undefined,
): number {
  const avg = (compR + compL) / 2;
  let sub = Math.round(Math.min(100, Math.max(0, ((avg - 70) / 30) * 100)));
  if (asymmetrie?.includes("Asymmetrie")) sub = Math.max(0, sub - 10);
  return sub;
}

export function computeAthletikScore(
  fmsRow: FmsRow | null,
  yRow: YbalanceRow | null,
  sprintRow: SprintRow | null,
): number {
  const weights: Record<string, number> = { fms: 18, y: 18, sprint: 13 };
  const subScores: Record<string, number> = {};

  if (fmsRow) subScores["fms"] = fmsSubScore(fmsRow.score, fmsRow.asymmetrie);
  if (yRow)
    subScores["y"] = yBalanceSubScore(
      yRow.composite_rechts,
      yRow.composite_links,
      yRow.asymmetrie,
    );
  if (sprintRow) {
    const bew = sprintRow.bewertung_10m ?? sprintRow.bewertung_30m ?? null;
    const s = sprintSubScore(bew);
    if (s !== null) subScores["sprint"] = s;
  }

  const keys = Object.keys(subScores);
  if (keys.length === 0) return 0;

  const totalWeight = keys.reduce((acc, k) => acc + (weights[k] ?? 0), 0);
  const weightedSum = keys.reduce(
    (acc, k) => acc + (subScores[k] ?? 0) * (weights[k] ?? 0),
    0,
  );
  return totalWeight > 0 ? Math.round(weightedSum / totalWeight) : 0;
}

// ─── FMS save ────────────────────────────────────────────────────────────────
export interface FmsInput {
  spieler_id: number;
  datum: string;
  deep_squat: number;
  hurdle_l: number;
  hurdle_r: number;
  inline_l: number;
  inline_r: number;
  shoulder_l: number;
  shoulder_r: number;
  aslr_l: number;
  aslr_r: number;
  trunk: number;
  rotary_l: number;
  rotary_r: number;
}

function fmsBewertung(score: number): string {
  if (score >= 18) return "Hervorragend";
  if (score >= 14) return "Gut";
  if (score >= 10) return "Durchschnittlich";
  return "Verbesserungsbedarf";
}

function fmsAsymmetrie(input: FmsInput): string {
  const pairs: Array<[number, number]> = [
    [input.hurdle_l, input.hurdle_r],
    [input.inline_l, input.inline_r],
    [input.shoulder_l, input.shoulder_r],
    [input.aslr_l, input.aslr_r],
    [input.rotary_l, input.rotary_r],
  ];
  const asym = pairs.some(([l, r]) => Math.abs(l - r) >= 1);
  return asym ? "Asymmetrie erkannt" : "Keine Asymmetrie";
}

export function saveFms(input: FmsInput): { score: number; bewertung: string; asymmetrie: string } {
  const score =
    input.deep_squat +
    Math.min(input.hurdle_l, input.hurdle_r) +
    Math.min(input.inline_l, input.inline_r) +
    Math.min(input.shoulder_l, input.shoulder_r) +
    Math.min(input.aslr_l, input.aslr_r) +
    input.trunk +
    Math.min(input.rotary_l, input.rotary_r);
  const bewertung = fmsBewertung(score);
  const asymmetrie = fmsAsymmetrie(input);
  const schwerpunkt = score >= 14 ? "Keine Auffälligkeiten" : "Beweglichkeit";

  const conn = db();
  try {
    conn
      .prepare(
        `INSERT INTO fms_test
         (spieler_id,datum,deep_squat,hurdle_links,hurdle_rechts,inline_links,
          inline_rechts,shoulder_links,shoulder_rechts,aslr_links,aslr_rechts,
          trunk,rotary_links,rotary_rechts,score,bewertung,asymmetrie,schwerpunkt)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      )
      .run(
        input.spieler_id,
        input.datum,
        input.deep_squat,
        input.hurdle_l,
        input.hurdle_r,
        input.inline_l,
        input.inline_r,
        input.shoulder_l,
        input.shoulder_r,
        input.aslr_l,
        input.aslr_r,
        input.trunk,
        input.rotary_l,
        input.rotary_r,
        score,
        bewertung,
        asymmetrie,
        schwerpunkt,
      );
  } finally {
    conn.close();
  }
  return { score, bewertung, asymmetrie };
}

// ─── Sprint save ──────────────────────────────────────────────────────────────
export interface SprintInput {
  spieler_id: number;
  datum: string;
  best_10m: number;
  best_30m: number;
}

function sprintBewertung10m(t: number): string {
  if (t <= 1.60) return "Hervorragend";
  if (t <= 1.72) return "Gut";
  if (t <= 1.85) return "Durchschnittlich";
  if (t <= 2.00) return "Unterdurchschnittlich";
  return "Schlecht";
}

function sprintBewertung30m(t: number): string {
  if (t <= 3.90) return "Hervorragend";
  if (t <= 4.10) return "Gut";
  if (t <= 4.35) return "Durchschnittlich";
  if (t <= 4.65) return "Unterdurchschnittlich";
  return "Schlecht";
}

export function saveSprint(input: SprintInput): { bewertung_10m: string; bewertung_30m: string } {
  const bew10 = sprintBewertung10m(input.best_10m);
  const bew30 = sprintBewertung30m(input.best_30m);
  const beschl = input.best_30m > 0 ? Math.round(((input.best_30m - input.best_10m) / input.best_30m) * 100) : 0;
  const defizite = bew10 === "Schlecht" || bew30 === "Schlecht" ? "Maximale Sprintgeschwindigkeit" : "Keine";

  const conn = db();
  try {
    conn
      .prepare(
        `INSERT INTO sprint_test
         (spieler_id,datum,
          v1_5m,v2_5m,v3_5m,beste_5m,
          v1_10m,v2_10m,v3_10m,beste_10m,
          v1_20m,v2_20m,v3_20m,beste_20m,
          v1_30m,v2_30m,v3_30m,beste_30m,
          v1_40m,v2_40m,v3_40m,beste_40m,
          beschl_index,bewertung_10m,bewertung_30m,defizite)
         VALUES (?,?,0,0,0,0,?,?,?,?,0,0,0,0,?,?,?,?,0,0,0,0,?,?,?,?)`,
      )
      .run(
        input.spieler_id,
        input.datum,
        input.best_10m, input.best_10m, input.best_10m, input.best_10m,
        input.best_30m, input.best_30m, input.best_30m, input.best_30m,
        beschl, bew10, bew30, defizite,
      );
  } finally {
    conn.close();
  }
  return { bewertung_10m: bew10, bewertung_30m: bew30 };
}

// ─── Push Notifications ───────────────────────────────────────────────────────

/** Ensure the push-token columns exist (idempotent migration). */
export function migratePushTokenColumns(): void {
  const conn = db();
  try {
    // Add push_token column if missing
    const cols = conn.pragma(`table_info(benutzer)`) as Array<{ name: string }>;
    const names = cols.map((c) => c.name);
    if (!names.includes("push_token")) {
      conn.exec(`ALTER TABLE benutzer ADD COLUMN push_token TEXT`);
    }
    if (!names.includes("push_notifications_enabled")) {
      conn.exec(`ALTER TABLE benutzer ADD COLUMN push_notifications_enabled INTEGER NOT NULL DEFAULT 1`);
    }
  } finally {
    conn.close();
  }
}

export function savePushToken(userId: number, token: string): void {
  const conn = db();
  try {
    conn
      .prepare(`UPDATE benutzer SET push_token = ? WHERE id = ?`)
      .run(token, userId);
  } finally {
    conn.close();
  }
}

export function setNotificationsEnabled(userId: number, enabled: boolean): void {
  const conn = db();
  try {
    conn
      .prepare(`UPDATE benutzer SET push_notifications_enabled = ? WHERE id = ?`)
      .run(enabled ? 1 : 0, userId);
  } finally {
    conn.close();
  }
}

export function getNotificationsEnabled(userId: number): boolean {
  return withRetry(() => {
    const conn = db();
    try {
      const row = conn
        .prepare(`SELECT push_notifications_enabled FROM benutzer WHERE id = ?`)
        .get(userId) as { push_notifications_enabled: number } | undefined;
      return (row?.push_notifications_enabled ?? 1) === 1;
    } finally {
      conn.close();
    }
  });
}

/** Returns all active push tokens for trainers (and admins) in a Verein. */
export function getTrainerPushTokens(vereinId: number): string[] {
  return withRetry(() => {
    const conn = db();
    try {
      const rows = conn
        .prepare(
          `SELECT push_token FROM benutzer
           WHERE verein_id = ? AND push_token IS NOT NULL
             AND push_notifications_enabled = 1 AND aktiv = 1`,
        )
        .all(vereinId) as Array<{ push_token: string }>;
      return rows.map((r) => r.push_token).filter(Boolean);
    } finally {
      conn.close();
    }
  });
}

// ─── Y-Balance save ───────────────────────────────────────────────────────────
export interface YbalanceInput {
  spieler_id: number;
  datum: string;
  ant_r: number;
  ant_l: number;
  pm_r: number;
  pm_l: number;
  pl_r: number;
  pl_l: number;
  leg_length_r?: number | null;
  leg_length_l?: number | null;
}

function computeComposite(ant: number, pm: number, pl: number, legLen: number | null | undefined): number {
  if (legLen && legLen > 0) {
    return Math.round(((ant + pm + pl) / (legLen * 3)) * 100 * 10) / 10;
  }
  // Without leg length: use raw average
  return Math.round(((ant + pm + pl) / 3) * 10) / 10;
}

export function saveYbalance(input: YbalanceInput): { composite_rechts: number; composite_links: number; asymmetrie: string } {
  const compR = computeComposite(input.ant_r, input.pm_r, input.pl_r, input.leg_length_r);
  const compL = computeComposite(input.ant_l, input.pm_l, input.pl_l, input.leg_length_l);

  const diff_a = Math.abs(input.ant_r - input.ant_l);
  const diff_pm = Math.abs(input.pm_r - input.pm_l);
  const diff_pl = Math.abs(input.pl_r - input.pl_l);
  const asymDiff = Math.abs(compR - compL);
  const asymmetrie = asymDiff > 4 ? "Asymmetrie erkannt" : "Keine Asymmetrie";
  const schwerpunkt = asymDiff > 4 ? "Stabilität / Y-Balance" : "Keine Auffälligkeiten";

  const conn = db();
  try {
    conn
      .prepare(
        `INSERT INTO y_balance_test
         (spieler_id,datum,anterior_rechts,anterior_links,posteromedial_rechts,
          posteromedial_links,posterolateral_rechts,posterolateral_links,
          diff_anterior,diff_posteromedial,diff_posterolateral,
          composite_rechts,composite_links,asymmetrie,schwerpunkt)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      )
      .run(
        input.spieler_id,
        input.datum,
        input.ant_r, input.ant_l,
        input.pm_r, input.pm_l,
        input.pl_r, input.pl_l,
        diff_a, diff_pm, diff_pl,
        compR, compL,
        asymmetrie, schwerpunkt,
      );
  } finally {
    conn.close();
  }
  return { composite_rechts: compR, composite_links: compL, asymmetrie };
}
