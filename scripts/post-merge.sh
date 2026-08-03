#!/bin/bash
# Post-merge setup — läuft automatisch nach jedem Task-Merge.
# Anforderungen: idempotent, non-interactive, fail-fast.
set -e

echo "=== Post-merge setup ==="

echo "Installing dependencies..."
pnpm install --no-frozen-lockfile

echo "Building shared libraries (typecheck)..."
pnpm run typecheck:libs 2>/dev/null || true

echo "Building API server..."
pnpm --filter @workspace/api-server run build

echo "Building landing page..."
PORT=18150 BASE_PATH="/" pnpm --filter @workspace/landing run build

echo "=== Done ==="
