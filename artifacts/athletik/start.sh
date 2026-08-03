#!/usr/bin/env bash
# ============================================================
# Athletik App — Startskript für Produktion
#
# Wird aufgerufen von:
#   - Render:   startCommand in render.yaml
#   - Railway:  startCommand in railway.toml
#   - VPS:      direkt oder per systemd / supervisor
#   - Docker:   CMD in Dockerfile
#
# Lokal ausführen:
#   APP_ENV=production bash start.sh
# ============================================================

set -euo pipefail

# Standardwerte (werden überschrieben wenn Env-Var gesetzt)
PORT="${PORT:-8080}"
APP_ENV="${APP_ENV:-production}"
ATHLETIK_DATA_DIR="${ATHLETIK_DATA_DIR:-/data}"
LOG_LEVEL="${LOG_LEVEL:-WARNING}"

echo "[start.sh] APP_ENV=$APP_ENV  PORT=$PORT  DATA=$ATHLETIK_DATA_DIR"

# ── Verzeichnisse anlegen ────────────────────────────────────────────────────
mkdir -p \
  "$ATHLETIK_DATA_DIR/uploads/logos" \
  "$ATHLETIK_DATA_DIR/uploads/spielerbilder" \
  "$ATHLETIK_DATA_DIR/uploads/pdf" \
  "$ATHLETIK_DATA_DIR/uploads/exports" \
  "$ATHLETIK_DATA_DIR/uploads/backups" \
  "$ATHLETIK_DATA_DIR/uploads/docs" \
  "$ATHLETIK_DATA_DIR/logs"

# ── Streamlit starten ────────────────────────────────────────────────────────
exec streamlit run app.py \
  --server.port          "$PORT" \
  --server.address       "0.0.0.0" \
  --server.headless      true \
  --server.enableCORS    false \
  --server.enableXsrfProtection false \
  --server.maxUploadSize "${MAX_UPLOAD_MB:-10}" \
  --browser.gatherUsageStats false \
  --logger.level         "$LOG_LEVEL"
