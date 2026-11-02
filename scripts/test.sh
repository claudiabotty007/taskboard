#!/usr/bin/env bash
# Run the test suites on Linux (run ./scripts/build.sh first).
#   ./scripts/test.sh [python|node|all] [extra pytest args...]
# python -> full pytest suite against the Python backend
# node   -> npm test + the pytest contract tests against the Node backend
# JUnit XML goes to reports/ for Jenkins.
set -euo pipefail

BACKEND="${1:-all}"
shift || true
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

[ -x "$PY" ] || { echo "No .venv found - run scripts/build.sh first" >&2; exit 1; }
mkdir -p "$ROOT/reports"
cd "$ROOT"

run_python() {
  "$PY" -m pytest --backend python --junitxml=reports/pytest-python.xml "$@"
}

run_node() {
  npm test --prefix backend-node
  "$PY" -m pytest -m contract --backend node --junitxml=reports/pytest-node.xml "$@"
}

case "$BACKEND" in
  python) run_python "$@" ;;
  node)   run_node "$@" ;;
  all)    run_python "$@"; run_node "$@" ;;
  *) echo "usage: $0 [python|node|all] [pytest args...]" >&2; exit 2 ;;
esac
