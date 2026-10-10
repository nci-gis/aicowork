# -*- coding: utf-8 -*-
"""CHANGELOG.md is written by a person; this checks that it was. A change to a
ring (the kernel, the host pages, the tools) between a base and HEAD must come
with a change to the first section of CHANGELOG.md (`## Unreleased`, or the
version heading the release commit turns it into). Shape only — the words are
the author's. The build checks the heading (`package.changelog_problems`)."""
import re
from pathlib import Path

from aicowork_core import common as C

RINGS = ("99_system/", "hosts/", "98_tools/")
MANIFEST_NAME = "MANIFEST.sha256"


def _first_section(text):
    """The text from the first `## ` heading to the next one (or the end); '' when none."""
    m = re.search(r"(?m)^## .*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"(?m)^## ", rest)
    return (m.group(0) + rest[:n.start()]) if n else (m.group(0) + rest)


def ring_changes(base, since):
    """Ring files that differ between `since` and HEAD, manifests left out (they
    only follow the files). -> sorted list of paths, or None when git cannot tell."""
    rc, out = C.git(base, "diff", "--name-only", since, "HEAD")
    if rc != 0:
        return None
    return sorted(p for p in out.splitlines()
                  if p.startswith(RINGS) and Path(p).name != MANIFEST_NAME)


def check(base, since):
    """-> list of reasons (empty = the CHANGELOG moved with the rings, or nothing moved)."""
    base = Path(base)
    changed = ring_changes(base, since)
    if changed is None:
        return [f"cannot compare with {since!r}: not a commit this clone knows (fetch it first)"]
    if not changed:
        return []
    rc, before = C.git(base, "show", f"{since}:CHANGELOG.md")
    before = before if rc == 0 else ""
    rc, after = C.git(base, "show", "HEAD:CHANGELOG.md")
    if rc != 0:
        return ["CHANGELOG.md is not committed at HEAD"]
    if _first_section(before) == _first_section(after):
        return [f"{len(changed)} ring file(s) changed since {since} but the first section of CHANGELOG.md did not "
                f"(`## Unreleased`): add what changed for the owner — e.g. {', '.join(changed[:3])}"]
    return []
