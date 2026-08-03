import { Router } from "express";
import jwt from "jsonwebtoken";
import {
  loginUser,
  getPlayers,
  getPlayerById,
  getFmsLast,
  getSprintLast,
  getYbalanceLast,
  saveFms,
  saveSprint,
  saveYbalance,
  computeAthletikScore,
} from "../lib/athletik-db.js";
import { logger } from "../lib/logger.js";

const router = Router();

const JWT_SECRET = process.env["SESSION_SECRET"] ?? "athletik-mobile-secret";

// ─── Auth middleware ──────────────────────────────────────────────────────────
interface JwtPayload {
  userId: number;
  email: string;
  rolle: string;
  verein_id: number | null;
}

function requireAuth(req: any, res: any, next: any) {
  const auth = req.headers["authorization"] as string | undefined;
  if (!auth?.startsWith("Bearer ")) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  const token = auth.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET) as JwtPayload;
    req.jwtUser = payload;
    next();
  } catch {
    res.status(401).json({ error: "Token ungültig oder abgelaufen" });
  }
}

// ─── POST /api/mobile/auth/login ──────────────────────────────────────────────
router.post("/mobile/auth/login", (req, res) => {
  const { email, password } = req.body ?? {};
  if (!email || !password) {
    res.status(400).json({ error: "E-Mail und Passwort erforderlich" });
    return;
  }

  try {
    const user = loginUser(email as string, password as string);
    if (!user) {
      res.status(401).json({ error: "E-Mail oder Passwort falsch" });
      return;
    }

    const payload: JwtPayload = {
      userId: user.id,
      email: user.email,
      rolle: user.rolle,
      verein_id: user.verein_id,
    };
    const token = jwt.sign(payload, JWT_SECRET, { expiresIn: "30d" });

    res.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        vorname: user.vorname ?? "",
        nachname: user.nachname ?? "",
        rolle: user.rolle,
        verein_id: user.verein_id ?? null,
        verein_name: user.verein_name ?? null,
      },
    });
  } catch (err) {
    logger.error({ err }, "Mobile login error");
    res.status(500).json({ error: "Datenbankfehler beim Login" });
  }
});

// ─── GET /api/mobile/players ──────────────────────────────────────────────────
router.get("/mobile/players", requireAuth, (req, res) => {
  const { userId, rolle, verein_id } = (req as any).jwtUser as JwtPayload;

  try {
    const players = getPlayers(userId, rolle, verein_id);

    const enriched = players.map((p) => {
      const fms = getFmsLast(p.id);
      const sprint = getSprintLast(p.id);
      const y = getYbalanceLast(p.id);
      const score = fms || y || sprint ? computeAthletikScore(fms, y, sprint) : null;
      const dates = [fms?.datum, sprint?.datum, y?.datum].filter(Boolean) as string[];
      const last_test_date = dates.length > 0 ? dates.sort().at(-1) ?? null : null;
      return {
        id: p.id,
        name: p.name,
        vorname: p.vorname ?? "",
        nachname: p.nachname ?? "",
        mannschaft: p.mannschaft ?? null,
        altersklasse: p.altersklasse ?? null,
        score,
        last_test_date,
      };
    });

    res.json({ players: enriched });
  } catch (err) {
    logger.error({ err }, "Mobile getPlayers error");
    res.status(500).json({ error: "Fehler beim Laden der Spieler" });
  }
});

// ─── GET /api/mobile/players/:id ─────────────────────────────────────────────
router.get("/mobile/players/:playerId", requireAuth, (req, res) => {
  const id = parseInt(req.params["playerId"] ?? "0", 10);
  if (!id) { res.status(400).json({ error: "Ungültige Spieler-ID" }); return; }

  try {
    const player = getPlayerById(id);
    if (!player) { res.status(404).json({ error: "Spieler nicht gefunden" }); return; }

    const fms = getFmsLast(id);
    const sprint = getSprintLast(id);
    const y = getYbalanceLast(id);
    const score = fms || y || sprint ? computeAthletikScore(fms, y, sprint) : null;

    res.json({
      player: {
        id: player.id,
        name: player.name,
        vorname: player.vorname ?? "",
        nachname: player.nachname ?? "",
        mannschaft: player.mannschaft ?? null,
        altersklasse: player.altersklasse ?? null,
        score,
        last_test_date: null,
      },
      score,
      tests: {
        fms: fms
          ? {
              datum: fms.datum,
              score: fms.score,
              bewertung: fms.bewertung,
              asymmetrie: fms.asymmetrie ?? null,
            }
          : null,
        sprint: sprint
          ? {
              datum: sprint.datum,
              beste_10m: sprint.beste_10m ?? null,
              beste_30m: sprint.beste_30m ?? null,
              bewertung_10m: sprint.bewertung_10m ?? null,
            }
          : null,
        ybalance: y
          ? {
              datum: y.datum,
              composite_rechts: y.composite_rechts,
              composite_links: y.composite_links,
              asymmetrie: y.asymmetrie ?? null,
            }
          : null,
      },
    });
  } catch (err) {
    logger.error({ err }, "Mobile getPlayer error");
    res.status(500).json({ error: "Fehler beim Laden des Spielers" });
  }
});

// ─── POST /api/mobile/players/:id/fms ────────────────────────────────────────
router.post("/mobile/players/:playerId/fms", requireAuth, (req, res) => {
  const playerId = parseInt(req.params["playerId"] ?? "0", 10);
  if (!playerId) { res.status(400).json({ error: "Ungültige Spieler-ID" }); return; }

  const b = req.body ?? {};
  try {
    const result = saveFms({
      spieler_id: playerId,
      datum: b.datum ?? new Date().toISOString().slice(0, 10),
      deep_squat: Number(b.deep_squat ?? 0),
      hurdle_l: Number(b.hurdle_l ?? 0),
      hurdle_r: Number(b.hurdle_r ?? 0),
      inline_l: Number(b.inline_l ?? 0),
      inline_r: Number(b.inline_r ?? 0),
      shoulder_l: Number(b.shoulder_l ?? 0),
      shoulder_r: Number(b.shoulder_r ?? 0),
      aslr_l: Number(b.aslr_l ?? 0),
      aslr_r: Number(b.aslr_r ?? 0),
      trunk: Number(b.trunk ?? 0),
      rotary_l: Number(b.rotary_l ?? 0),
      rotary_r: Number(b.rotary_r ?? 0),
    });

    const fms = getFmsLast(playerId);
    const sprint = getSprintLast(playerId);
    const y = getYbalanceLast(playerId);
    const score = computeAthletikScore(fms, y, sprint);
    const sub_score = result.score;

    res.json({ score, sub_score, message: `FMS gespeichert: ${result.score}/21 (${result.bewertung})` });
  } catch (err) {
    logger.error({ err }, "Mobile submitFms error");
    res.status(500).json({ error: "Fehler beim Speichern des FMS-Tests" });
  }
});

// ─── POST /api/mobile/players/:id/sprint ─────────────────────────────────────
router.post("/mobile/players/:playerId/sprint", requireAuth, (req, res) => {
  const playerId = parseInt(req.params["playerId"] ?? "0", 10);
  if (!playerId) { res.status(400).json({ error: "Ungültige Spieler-ID" }); return; }

  const b = req.body ?? {};
  try {
    const result = saveSprint({
      spieler_id: playerId,
      datum: b.datum ?? new Date().toISOString().slice(0, 10),
      best_10m: Number(b.best_10m ?? 0),
      best_30m: Number(b.best_30m ?? b.best_10m ?? 0),
    });

    const fms = getFmsLast(playerId);
    const sprint = getSprintLast(playerId);
    const y = getYbalanceLast(playerId);
    const score = computeAthletikScore(fms, y, sprint);

    res.json({ score, message: `Sprint gespeichert: 10m ${b.best_10m}s (${result.bewertung_10m})` });
  } catch (err) {
    logger.error({ err }, "Mobile submitSprint error");
    res.status(500).json({ error: "Fehler beim Speichern des Sprint-Tests" });
  }
});

// ─── POST /api/mobile/players/:id/ybalance ───────────────────────────────────
router.post("/mobile/players/:playerId/ybalance", requireAuth, (req, res) => {
  const playerId = parseInt(req.params["playerId"] ?? "0", 10);
  if (!playerId) { res.status(400).json({ error: "Ungültige Spieler-ID" }); return; }

  const b = req.body ?? {};
  try {
    const result = saveYbalance({
      spieler_id: playerId,
      datum: b.datum ?? new Date().toISOString().slice(0, 10),
      ant_r: Number(b.ant_r ?? 0),
      ant_l: Number(b.ant_l ?? 0),
      pm_r: Number(b.pm_r ?? 0),
      pm_l: Number(b.pm_l ?? 0),
      pl_r: Number(b.pl_r ?? 0),
      pl_l: Number(b.pl_l ?? 0),
      leg_length_r: b.leg_length_r != null ? Number(b.leg_length_r) : null,
      leg_length_l: b.leg_length_l != null ? Number(b.leg_length_l) : null,
    });

    const fms = getFmsLast(playerId);
    const sprint = getSprintLast(playerId);
    const y = getYbalanceLast(playerId);
    const score = computeAthletikScore(fms, y, sprint);
    const sub_score = Math.round((result.composite_rechts + result.composite_links) / 2);

    res.json({ score, sub_score, message: `Y-Balance gespeichert: ${result.asymmetrie}` });
  } catch (err) {
    logger.error({ err }, "Mobile submitYbalance error");
    res.status(500).json({ error: "Fehler beim Speichern des Y-Balance-Tests" });
  }
});

export default router;
