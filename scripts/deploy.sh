#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but was not found in PATH" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required but is not available" >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Edit PORT or IMAGE there if needed."
fi

DEPLOY_MODE="${DEPLOY_MODE:-image}"

if [ "$DEPLOY_MODE" = "build" ]; then
  docker compose up -d --build --remove-orphans
else
  docker compose pull
  docker compose up -d --no-build --remove-orphans
fi

docker compose ps

PORT="$(awk -F= '/^PORT=/{print $2}' .env 2>/dev/null || true)"
PORT="${PORT:-8080}"

echo
echo "Health check:"
echo "  curl http://localhost:${PORT}/health"
