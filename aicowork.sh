#!/usr/bin/env bash
# AI-Cowork launcher — delegates everything to the Python CLI in 98_tools/
# Usage: ./aicowork.sh [doctor | init <folder> | viz | inbox "content" | --help]
# With uv: uv picks (or fetches) a Python that 98_tools/pyproject.toml accepts and
# installs the command line only; `viz` adds the viewer the first time it runs.
# Without uv: a Python the tools accept runs every command except the viewer
# (standard library only); pyfloor.py says plainly when yours is too old.
set -euo pipefail
export AICOWORK_CALLER_DIR="$PWD"
cd "$(dirname "$0")"
if [ ! -d 98_tools/apps/aicowork ]; then
  echo "this folder has no tools (98_tools/): the kernel works with files alone; see 99_system/README.md"; exit 1
fi
if command -v uv >/dev/null 2>&1; then
  export UV_LINK_MODE=copy
  exec uv run --locked --project 98_tools --package aicowork --extra seal aicowork "$@"
fi
FLOOR=98_tools/libs/core/src/aicowork_core/pyfloor.py
why="no Python found"
for PY in python3 python; do
  command -v "$PY" >/dev/null 2>&1 || continue
  if out=$("$PY" "$FLOOR" 2>&1); then
    PYTHONPATH="$PWD/98_tools/apps/aicowork/src" exec "$PY" -m aicowork "$@"
  fi
  case "$out" in Python*) why="$out" ;; esac
done
echo "$why — get Python at https://www.python.org/downloads/, or uv (https://docs.astral.sh/uv/), which fetches it for you."
exit 1
