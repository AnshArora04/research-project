#!/usr/bin/env bash
# PPD Explorer — bake data, then launch FastAPI server.
#
# Usage:  ./run.sh                    # default: localhost:8000
#         PORT=8080 ./run.sh          # custom port
#         HOST=0.0.0.0 ./run.sh       # expose to LAN
#         SKIP_BAKE=1 ./run.sh        # skip bake (faster restart)

set -euo pipefail

cd "$(dirname "$0")"

PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
PY=".venv/bin/python"
UVICORN=".venv/bin/uvicorn"

if [[ ! -x "$PY" ]]; then
  echo "✗ .venv not found at .venv/ — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

if [[ "${SKIP_BAKE:-0}" != "1" ]]; then
  echo "▸ Baking data → web/static/ppd-data.js"
  "$PY" -m web.bake_data
  echo
fi

echo "▸ Starting uvicorn at http://${HOST}:${PORT}"
exec "$UVICORN" web.server:app --host "$HOST" --port "$PORT" --reload
