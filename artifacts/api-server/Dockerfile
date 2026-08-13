# ============================================================
# APH API-Server — Produktions-Dockerfile
#
# Build-Kontext: Workspace-Root (Monorepo-Wurzel)
# Aufruf via docker-compose.yml in artifacts/athletik/
#
# Externe Abhängigkeiten zur Laufzeit:
#   - better-sqlite3  (native .node-Addon → muss im Image kompiliert werden)
#   - stripe          (runtime require() → muss in node_modules liegen)
#
# Build-Kontext enthält nur Pakete, die api-server direkt benötigt.
# ============================================================

FROM node:24-alpine

# Build-Tools für native Module (better-sqlite3 kompiliert ein .node-Addon)
RUN apk add --no-cache python3 make g++

# pnpm — gleiche Version wie im Workspace
RUN corepack enable && corepack prepare pnpm@10.26.1 --activate

WORKDIR /app

# ── Workspace-Konfiguration (eigene Layer für besseres Caching) ───────────────
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./

# ── Nur die Workspace-Pakete, die api-server direkt benötigt ──────────────────
# @workspace/api-zod  — Zod-Schemata (statischer Import, wird gebundelt)
# @workspace/db       — Drizzle/PostgreSQL (lazy import in contact.ts)
COPY lib/api-zod/    ./lib/api-zod/
COPY lib/db/         ./lib/db/

# ── Der api-server selbst ─────────────────────────────────────────────────────
COPY artifacts/api-server/ ./artifacts/api-server/

# Abhängigkeiten installieren (inkl. native Module kompilieren)
# --filter @workspace/api-server... zieht transitiv alle Workspace-Deps mit
RUN pnpm install --frozen-lockfile --filter @workspace/api-server...

# Build: esbuild bündelt alles außer external (better-sqlite3, stripe, *.node)
RUN pnpm --filter @workspace/api-server run build

# ── Laufzeit-Konfiguration ────────────────────────────────────────────────────
ENV NODE_ENV=production

WORKDIR /app/artifacts/api-server

EXPOSE 8083

# Health-Route /healthz ist in app.ts registriert
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:' + (process.env.PORT||8083) + '/healthz', r => process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "--enable-source-maps", "dist/index.mjs"]
