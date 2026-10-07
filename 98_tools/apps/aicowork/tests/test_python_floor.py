# -*- coding: utf-8 -*-
"""The Python floor is written once: `requires-python` in 98_tools/pyproject.toml
(owner, 2026-10-03; decision ambiguity-fails-closed, addendum 2). Everything else
reads it (pyfloor.py) or points to it, and no document restates it — a number
copied into many places is how rc.2 came to claim a version it never tested."""
import re
import subprocess
import sys
from pathlib import Path

from aicowork_core import pyfloor

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())
TOOLS = REPO / "98_tools"
ROOT_FLOOR = re.compile(r'(?m)^requires-python\s*=\s*">=(\d+)\.(\d+)"')
# a stated version requirement: "Python ≥ 3.11", "Python 3.11+", "Python 3.11 or newer", "py>=3.11"
CLAIM = re.compile(r"Python\s*(?:≥|>=)\s*3\.\d+|Python\s+3\.\d+\s*(?:\+|or newer|or later|and newer)"
                   r"|py\s*>=\s*3\.\d+|version_info\s*<\s*\(3,", re.I)


def _pyprojects():
    return [p for p in TOOLS.glob("**/pyproject.toml") if ".venv" not in p.parts]


def test_one_value_in_every_pyproject():
    values = {}
    for p in _pyprojects():
        m = ROOT_FLOOR.search(p.read_text(encoding="utf-8"))
        assert m, f"{p.relative_to(REPO)}: no requires-python"
        values[p.relative_to(REPO).as_posix()] = (int(m.group(1)), int(m.group(2)))
    assert len(set(values.values())) == 1, values


def test_the_guard_reads_that_value():
    want = tuple(int(x) for x in ROOT_FLOOR.search((TOOLS / "pyproject.toml").read_text(encoding="utf-8")).groups())
    assert pyfloor.floor() == want
    assert pyfloor.problem() is None                                   # the suite runs on the floor or above
    older = (want[0], want[1] - 1)
    msg = pyfloor.problem(older)
    assert msg.startswith(f"Python {older[0]}.{older[1]} found") and f"{want[0]}.{want[1]} or newer" in msg


def test_the_guard_runs_as_a_script():
    """Launchers and hooks run it by path to choose an interpreter: exit 0 = usable."""
    r = subprocess.run([sys.executable, str(TOOLS / "libs/core/src/aicowork_core/pyfloor.py")], capture_output=True, text=True)
    assert r.returncode == 0 and r.stderr == ""


def test_no_file_restates_the_floor():
    """Documents point to pyproject.toml; launchers, hooks and the entry point ask
    pyfloor.py. History stays as written: CHANGELOG.md and .agents/ are records."""
    files = [REPO / "aicowork.sh", REPO / "aicowork.bat", *(REPO / ".githooks").glob("*")]
    files += [p for p in REPO.rglob("*") if p.is_file() and p.suffix in (".md", ".py", ".toml", ".sh", ".bat")
              and not ({".venv", "node_modules", ".git", ".agents", "_scratch", "__pycache__"} & set(p.relative_to(REPO).parts))]
    found = []
    for p in sorted(set(files)):
        rel = p.relative_to(REPO).as_posix()
        if rel in ("CHANGELOG.md", "98_tools/apps/aicowork/tests/test_python_floor.py"):
            continue
        for m in CLAIM.finditer(p.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{rel}: {m.group(0)}")
    assert not found, found
