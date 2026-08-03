import { Router, type IRouter } from "express";
import healthRouter from "./health";
import contactRouter from "./contact";
import maintenanceRouter from "./maintenance";
import stripeRouter from "./stripe";

const router: IRouter = Router();

router.use(healthRouter);
router.use(contactRouter);
router.use(maintenanceRouter);
router.use(stripeRouter);

export default router;
