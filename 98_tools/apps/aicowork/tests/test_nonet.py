# -*- coding: utf-8 -*-
"""No-network proof for our own code (plan C7). Two parts:
1. static: no module of the tools imports a network library, except the viewer
   (which listens on loopback only — uvicorn/fastapi);
2. dynamic: the stdlib commands run with every non-loopback connect blocked.
This covers the reference implementation, not the agent host: the model call
is the named egress (CONVENTIONS "Reach")."""
import ast
import shutil
import subprocess
import socket
from pathlib import Path

import pytest

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())
TOOLS = REPO / "98_tools"
# every tool's source that is present: libs, apps, and the devkit in the development repository
SRCS = sorted(TOOLS.glob("libs/*/src")) + sorted(TOOLS.glob("apps/*/src")) + sorted(REPO.glob("90_devkit/src"))
NET = {"socket", "urllib.request", "urllib3", "http.client", "requests", "httpx", "aiohttp",
       "ftplib", "smtplib", "telnetlib", "xmlrpc.client", "ssl"}
VIEWER_ALLOWED = {"viewer/__main__.py"}      # uvicorn binds 127.0.0.1 (refuses anything else)


def _imports(py):
    tree = ast.parse(py.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            yield n.module


def test_no_network_imports():
    bad = []
    for src in SRCS:
        for py in src.rglob("*.py"):
            rel = py.relative_to(src).as_posix()
            for mod in _imports(py):
                if any(mod == m or mod.startswith(m + ".") for m in NET) and rel not in VIEWER_ALLOWED:
                    bad.append(f"{rel}: {mod}")
    assert bad == []


@pytest.fixture
def no_network(monkeypatch):
    real = socket.socket.connect

    def guarded(self, addr):
        host = addr[0] if isinstance(addr, tuple) else str(addr)
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise AssertionError(f"network call to {host!r}")
        return real(self, addr)
    monkeypatch.setattr(socket.socket, "connect", guarded)
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("create_connection")))
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda host, *a, **k: (_ for _ in ()).throw(AssertionError(f"dns {host}")))


def test_commands_run_offline(no_network, tmp_path, monkeypatch):
    from aicowork.conform import checks
    from aicowork.instance import ops, anchor
    from aicowork.egress import gate as egress
    monkeypatch.setenv("AICOWORK_ANCHOR_DIR", str(tmp_path / "anchors"))
    repo = TOOLS.parent
    base = tmp_path / "i"
    shutil.copytree(repo / "99_system" / "conformance" / "fixtures" / "example-instance", base)
    shutil.copytree(repo / "99_system", base / "99_system", ignore=shutil.ignore_patterns("fixtures"))
    checks.run(base, level=2)
    ops.reach(base)
    ops.new(base, "daily-log")
    anchor.anchor(base)                       # a dry run runs the binding gate too (C34)
    egress.export(base, "share-public", dry_run=True)
    from aicowork_core import manifest
    manifest.write(base / "99_system")
    subprocess.run(["git", "-C", str(base), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(base), "-c", "user.email=t@example.com", "-c", "user.name=t", "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(base), "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "s"], check=True)
    assert manifest.verify(base / "99_system") == []
