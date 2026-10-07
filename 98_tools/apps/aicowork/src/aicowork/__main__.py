"""`python3 -m aicowork <cmd>` — runs the stdlib-only commands without installing anything."""
import sys

import aicowork  # noqa: F401  (run from source: puts the shared library beside it on the path)
from aicowork_core import pyfloor

_why = pyfloor.problem()          # the floor is written once: requires-python in 98_tools/pyproject.toml
if _why:
    sys.exit(_why)

from aicowork.cli import main  # noqa: E402

sys.exit(main() or 0)
