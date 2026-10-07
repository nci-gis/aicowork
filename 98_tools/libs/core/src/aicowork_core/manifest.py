# -*- coding: utf-8 -*-
"""Ring locks (plan C3). Stdlib only. The trust anchor that records them outside
the folder is the app's (aicowork.instance.anchor).

MANIFEST.sha256 lists `<sha256>  <path>` for every file of a ring folder
(99_system/, hosts/ or 98_tools/). An agent that edits its own instructions, skills or
tools shows up as drift. Because an agent can also rewrite the manifest and
even .git inside the folder, the *anchor* — the manifest hash and the current
commit — is also written to a file OUTSIDE the connected folder, in the
owner's user profile. Tamper-evident, not tamper-proof: anyone who can write
the user profile can move the anchor too.
"""
from pathlib import Path

from aicowork_core import common as C

MANIFEST = "MANIFEST.sha256"
SKIP_DIRS = {".venv", "data", "__pycache__", ".pytest_cache", "node_modules"}


def ring_files(root):
    root = Path(root)
    for p in C.files_in_order(root):
        if p.name == MANIFEST:
            continue
        parts = p.relative_to(root).parts
        if any(x in SKIP_DIRS for x in parts) or p.suffix == ".pyc" or p.name.endswith(".tmp"):
            continue
        yield p


def build(root):
    root = Path(root)
    lines = [f"{C.sha256_file(p)}  {p.relative_to(root).as_posix()}" for p in ring_files(root)]
    return "\n".join(lines) + "\n"


def write(root):
    p = Path(root) / MANIFEST
    text = build(root)
    p.write_text(text, encoding="utf-8", newline="\n")
    return p, C.sha256_text(text)


def verify(root):
    """-> list of problems (empty = matches)."""
    root = Path(root)
    mf = root / MANIFEST
    if not mf.is_file():
        return [f"{MANIFEST} missing"]
    want = {}
    for line in C.read(mf).splitlines():
        if line.strip():
            h, _, path = line.partition("  ")
            want[path] = h
    have = {p.relative_to(root).as_posix(): C.sha256_file(p) for p in ring_files(root)}
    out = []
    for path in sorted(set(want) | set(have)):
        if path not in have:
            out.append(f"missing: {path}")
        elif path not in want:
            out.append(f"not in manifest: {path}")
        elif want[path] != have[path]:
            out.append(f"changed: {path}")
    return out


def manifest_hash(root):
    mf = Path(root) / MANIFEST
    return C.sha256_text(C.read(mf)) if mf.is_file() else None


# ---------------- trust anchor ----------------
