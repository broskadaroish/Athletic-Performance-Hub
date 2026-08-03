import { Router, type IRouter } from "express";
import contactRouter from "./contact";
import maintenanceRouter from "./maintenance";
import stripeRouter from "./stripe";
import healthRouter from "./health.js";
import mobileRouter from "./mobile.js";

const router: IRouter = Router();

router.use(healthRouter);
router.use(contactRouter);
router.use(maintenanceRouter);
router.use(stripeRouter);
router.use(mobileRouter);

export default router;
