# -*- coding: utf-8 -*-
"""The trust anchor, read side: where it lives, whether this profile is the
owner's, and the hashes of the files that steer the agent.

A hash is only worth what the place it lives in is worth. Inside the folder
(a note, `index.db`, git) the agent can rewrite the hash with the file; the
anchor lives OUTSIDE the folder in the owner's profile, so a change to the
folder cannot also rewrite the record it is checked against. Writing an
anchor (and the egress receipt head it records) is the command line's job
(`aicowork anchor`, `decide`); the viewer only reads it. Standard library only.
"""
import json
import os
import sys
from pathlib import Path

from aicowork_core import common as C

# the files whose content steers an agent session: every one is bound to the anchor
STEERING_FILES = ("policy.yaml", "aicowork.yaml#security", "INSTRUCTIONS.md", "CLAUDE.md", "AGENTS.md",
                  "03_personas/me.md#check_tokens", "03_personas/me.md#allow_tokens", "modules.lock")
# drift here stops egress (the policy and the preset decide what may leave)
EGRESS_BOUND = ("policy.yaml", "aicowork.yaml#security")


def anchor_dir():
    if os.environ.get("AICOWORK_ANCHOR_DIR"):
        return Path(os.environ["AICOWORK_ANCHOR_DIR"])
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(root) / "aicowork" / "anchors"
    return Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "aicowork" / "anchors"


# Filesystems through which a folder reaches a machine that is not where it
# lives: an agent VM, a container, a remote box. A profile there is not the
# owner's host profile, so an anchor written there is inside the agent's reach
# (and usually thrown away with the session). drvfs (WSL) is the owner's own
# machine and is deliberately not listed.
FOREIGN_FS = ("fuse", "9p", "virtiofs", "cifs", "smb3", "smbfs", "nfs")


def _mount_fstype(path):
    """Filesystem type of the mount holding `path` (Linux only), else None."""
    mi = Path("/proc/self/mountinfo")
    if not sys.platform.startswith("linux") or not mi.is_file():
        return None
    target = str(Path(path).resolve())
    best, fstype = "", None
    for line in C.read(mi).splitlines():
        left, _, right = line.partition(" - ")
        f = left.split()
        if len(f) < 5 or not right:
            continue
        mp = f[4].replace("\\040", " ")
        if (target == mp or target.startswith(mp.rstrip("/") + "/")) and len(mp) > len(best):
            best, fstype = mp, right.split()[0]
    return fstype


def foreign_profile(base):
    """-> reason (str) when this process is probably NOT the owner on the host
    the folder lives on — so an anchor written here would sit inside the agent's
    reach. None when the profile looks like the owner's. An explicit
    AICOWORK_ANCHOR_DIR is the owner's decision and always wins."""
    if os.environ.get("AICOWORK_ANCHOR_DIR"):
        return None
    if os.environ.get("SANDBOX_RUNTIME"):
        return "this process runs inside a sandbox (SANDBOX_RUNTIME is set)"
    fs = _mount_fstype(base)
    if fs and fs.split(".")[0].startswith(FOREIGN_FS):
        return f"the folder is mounted into this machine over {fs!r} — this profile is not the owner's host"
    return None


def anchor_file(base):
    return anchor_dir() / f"{C.sha256_text(str(Path(base).resolve()).lower())[:16]}.jsonl"


def last_anchor(base):
    f = anchor_file(base)
    if not f.is_file():
        return None
    lines = [l for l in C.read(f).splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def steering_hashes(base):
    """{name: sha256 or None} for every steering file (None = absent). A `#part`
    name hashes one part of a file, read the way the tools read it, so a
    comment or a reordering elsewhere in that file is not drift."""
    base = Path(base)
    out = {}
    for name in STEERING_FILES:
        file_, _, part = name.partition("#")
        p = base / file_
        if not p.is_file():
            out[name] = None
            continue
        if not part:
            out[name] = C.sha256_file(p)
        elif part == "security":
            cfg, _ = C.load_yaml(p)
            sec = (cfg or {}).get("security") if isinstance(cfg, dict) else None
            out[name] = C.sha256_text(json.dumps(sec, sort_keys=True, ensure_ascii=False))
        elif part == "check_tokens":
            toks = C.check_tokens(base)
            out[name] = C.sha256_text(json.dumps(sorted(toks), ensure_ascii=False)) if toks is not None else None
        elif part == "allow_tokens":
            # what the owner lets through the derived deny-list is steering too: an agent
            # that widens it must show as drift (2026-10-09)
            out[name] = C.sha256_text(json.dumps(sorted(C.allow_tokens(base)), ensure_ascii=False))
    return out


def steering_drift(base):
    """-> (state, drifted). state: 'none' (no anchor), 'unchecked' (anchor not
    readable from this profile), 'legacy' (an anchor from before steering files
    were recorded), 'ok', 'drift'. drifted: the names that differ."""
    a = last_anchor(base)
    if a is None:
        return ("unchecked" if foreign_profile(base) else "none"), []
    want = a.get("steering")
    if not isinstance(want, dict):
        return "legacy", []
    have = steering_hashes(base)
    drifted = [n for n in STEERING_FILES if want.get(n) != have.get(n)]
    return ("drift" if drifted else "ok"), drifted


def egress_bound_problem(base):
    """Why egress must refuse (CONVENTIONS "Visibility & egress": a `decided:`
    is in force only while the policy matches the anchor). -> str, or None."""
    state, drifted = steering_drift(base)
    if state in ("none", "unchecked", "legacy"):
        what = {"none": "no trust anchor records this policy",
                "unchecked": "the trust anchor lives on the owner's host and is not readable from here",
                "legacy": "the trust anchor predates the policy binding"}[state]
        return (f"{what} — run `aicowork anchor` (or `aicowork decide`) from the owner's own terminal "
                "on the host the folder lives on; until then the policy reads as undecided")
    bad = [n for n in drifted if n in EGRESS_BOUND]
    if bad:
        return (f"{', '.join(bad)} changed since the owner anchored it — if you changed it yourself, "
                "run `aicowork anchor` on your own computer; otherwise find out who did")
    return None
