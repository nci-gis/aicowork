# -*- coding: utf-8 -*-
"""The import rules of 98_tools/ and 90_devkit/, checked on the source (static).

- libs/ import nothing from any tool (only the standard library and each other);
- an app imports libs only: never another app, never the devkit;
- the devkit imports libs only: never an app;
- nothing that ships (98_tools/) imports anything from a development folder (90_-95_).
Why: one implementation of each security-relevant piece (leak scanners, safe
paths), no hidden coupling between tools, and an instance without the devkit
or without the viewer still works."""
import ast
from pathlib import Path

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())
TOOLS = REPO / "98_tools"
LIBS = {p.name for p in TOOLS.glob("libs/*/src/*") if p.is_dir()}           # e.g. aicowork_core
APPS = {p.name for p in TOOLS.glob("apps/*/src/*") if p.is_dir()}           # e.g. aicowork, viewer
DEV = {p.name for p in REPO.glob("9[0-5]_*/src/*") if p.is_dir()}           # e.g. devkit


def _top_imports(py):
    for n in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            yield from (a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            yield n.module.split(".")[0]


def _check(srcs, allowed_own, forbidden):
    bad = []
    for src in srcs:
        for py in src.rglob("*.py"):
            own = py.relative_to(src).parts[0]
            for top in _top_imports(py):
                if top in forbidden and top != own:
                    bad.append(f"{py.relative_to(REPO).as_posix()}: imports {top}")
    return bad


def test_layout_is_what_the_rules_assume():
    assert "aicowork_core" in LIBS and {"aicowork", "viewer"} <= APPS


def test_libs_import_no_tool():
    assert _check(TOOLS.glob("libs/*/src"), LIBS, APPS | DEV) == []


def test_apps_import_libs_only():
    for app_src in TOOLS.glob("apps/*/src"):
        own = {p.name for p in app_src.iterdir() if p.is_dir()}
        assert _check([app_src], own, (APPS - own) | DEV) == []


def test_devkit_imports_libs_only():
    assert _check(REPO.glob("9[0-5]_*/src"), DEV, APPS) == []
