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
  echo "✗ .venv not found at .venv/ — run: python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

PARQUET="output_python/ppd_plan_level_clean.parquet"
if [[ ! -f "$PARQUET" ]]; then
  echo "✗ Data file missing: $PARQUET"
  echo "  The parquet is normally tracked in git. Try: git pull (or re-clone the repo)."
  echo "  If you really need to regenerate it, run notebooks/01_create_mapping_table.ipynb"
  echo "  through notebooks/05_clean_ppd.ipynb in order — but most users never need to."
  exit 1
fi

if [[ "${SKIP_BAKE:-0}" != "1" ]]; then
  echo "▸ Baking data → web/static/ppd-data.js"
  "$PY" -m web.bake_data
  echo
fi

echo "▸ Starting uvicorn at http://${HOST}:${PORT}"
exec "$UVICORN" web.server:app --host "$HOST" --port "$PORT" --reload
