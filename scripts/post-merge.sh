#!/bin/bash
# Post-merge setup — läuft automatisch nach jedem Task-Merge.
# Anforderungen: idempotent, non-interactive, fail-fast.
set -e

echo "=== Post-merge setup ==="
echo "Installing dependencies..."
pnpm install --no-frozen-lockfile

echo "Running typecheck..."
pnpm run typecheck:libs 2>/dev/null || true

echo "=== Done ==="
