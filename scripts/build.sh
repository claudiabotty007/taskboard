#!/usr/bin/env bash
# Build one or both Taskboard backends on Linux.
#   ./scripts/build.sh [python|node|all]
# Always prepares .venv (pytest drives the tests of both backends), then packages
# dist/taskboard-<backend>-linux.tar.gz containing the backend plus the frontend.
set -euo pipefail

BACKEND="${1:-all}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
VENV="$ROOT/.venv"
PYTHON="${PYTHON:-python3}"

setup_venv() {
  [ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check -r "$ROOT/requirements-dev.txt"
}

package() { # package <backend-name> <source-dir>
  local name="taskboard-$1-linux"
  local out="$DIST/$name"
  rm -rf "$out" "$out.tar.gz"
  mkdir -p "$out"
  cp -r "$2" "$out/backend"
  cp -r "$ROOT/frontend" "$out/frontend"
  find "$out" -name __pycache__ -type d -prune -exec rm -rf {} +
  tar -czf "$out.tar.gz" -C "$DIST" "$name"
  echo "Built $out.tar.gz"
}

build_python() {
  echo "==> Building Python backend"
  "$VENV/bin/python" -m compileall -q "$ROOT/backend-python"
  package python "$ROOT/backend-python"
}

build_node() {
  echo "==> Building Node backend"
  npm ci --prefix "$ROOT/backend-node" --no-audit --no-fund
  package node "$ROOT/backend-node"
}

case "$BACKEND" in
  python) setup_venv; build_python ;;
  node)   setup_venv; build_node ;;
  all)    setup_venv; build_python; build_node ;;
  *) echo "usage: $0 [python|node|all]" >&2; exit 2 ;;
esac
