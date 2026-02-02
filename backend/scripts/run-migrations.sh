#! /usr/bin/env bash
# Run Alembic migrations from the backend directory.
# Use: ./scripts/run-migrations.sh (from backend/) or bash backend/scripts/run-migrations.sh (from project root)

set -e

cd "$(dirname "$0")/.."

if command -v uv &>/dev/null; then
  uv run alembic upgrade head
elif python -c "import alembic" 2>/dev/null; then
  python -m alembic upgrade head
else
  echo "Run migrations using one of:"
  echo "  uv run alembic upgrade head     (from backend/ with uv)"
  echo "  python -m alembic upgrade head  (from backend/ with venv activated)"
  echo "  docker compose run --rm prestart  (runs all prestart including migrations)"
  exit 1
fi
