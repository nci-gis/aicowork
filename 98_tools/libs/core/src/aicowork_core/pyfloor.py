# -*- coding: utf-8 -*-
"""The one Python version check. The version itself is written once, as
`requires-python` in 98_tools/pyproject.toml; this reads it from there and
says plainly when the running Python is older.

Run as a script by the launchers and git hooks to choose an interpreter
(exit 0 = good enough, exit 1 = a one-line reason on stderr), and imported by
the `aicowork` entry point. Kept to syntax that every Python 3 can parse, so
that an old interpreter prints the message instead of a SyntaxError."""
import os
import re
import sys

URL = "https://www.python.org/downloads/"
_HERE = os.path.dirname(os.path.abspath(__file__))
PYPROJECT = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "..", "pyproject.toml"))


def floor(pyproject=PYPROJECT):
    """-> (major, minor) from `requires-python = ">=X.Y"`, or None when the file
    is not there (a files-only copy) or states no such floor."""
    try:
        with open(pyproject, encoding="utf-8") as f:
            text = f.read()
    except Exception:                       # missing, unreadable, or an old Python's open()
        return None
    m = re.search(r'(?m)^requires-python\s*=\s*">=\s*(\d+)\.(\d+)', text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def problem(version=None, pyproject=PYPROJECT):
    """-> a one-line reason this Python is too old, or None when it is fine."""
    need = floor(pyproject)
    have = tuple(version or sys.version_info[:2])
    if need is None or have >= need:
        return None
    return ("Python %d.%d found; the AI-Cowork tools need %d.%d or newer (see 98_tools/pyproject.toml): %s"
            % (have[0], have[1], need[0], need[1], URL))


if __name__ == "__main__":
    why = problem()
    if why:
        sys.stderr.write(why + "\n")
        sys.exit(1)
