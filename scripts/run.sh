#!/usr/bin/env bash
# Start a backend locally (serves the frontend too).
#   ./scripts/run.sh [python|node]      env: PORT (default 8000), HOST, TASKBOARD_DATA_FILE
set -euo pipefail

BACKEND="${1:-python}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PORT="${PORT:-8000}"

case "$BACKEND" in
  python) exec "$ROOT/.venv/bin/python" "$ROOT/backend-python/run.py" ;;
  node)   exec node "$ROOT/backend-node/src/server.js" ;;
  *) echo "usage: $0 [python|node]" >&2; exit 2 ;;
esac
