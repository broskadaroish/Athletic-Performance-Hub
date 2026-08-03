import { Router, type IRouter } from "express";
import { GetMaintenanceStatusResponse } from "@workspace/api-zod";

const router: IRouter = Router();

// GET /maintenance — Wartungsmodus-Status
// Kontrolliert durch die Umgebungsvariable MAINTENANCE_MODE=1
router.get("/maintenance", (req, res): void => {
  const maintenance = process.env["MAINTENANCE_MODE"] === "1";
  const message = process.env["MAINTENANCE_MESSAGE"] ?? null;

  const result = GetMaintenanceStatusResponse.parse({ maintenance, message });
  res.json(result);
});

export default router;
