#!/bin/bash
# Post-merge setup — läuft automatisch nach jedem Task-Merge.
# Anforderungen: idempotent, non-interactive, fail-fast.
set -e

echo "=== Post-merge setup ==="

echo "Installing dependencies..."
pnpm install --frozen-lockfile

echo "Pushing database schema..."
pnpm --filter @workspace/db run push

echo "Running typecheck..."
pnpm run typecheck:libs

echo "=== Done ==="
