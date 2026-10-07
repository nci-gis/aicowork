# -*- coding: utf-8 -*-
"""`devkit fmt` — format the repository's Markdown with Prettier, one pinned version.

Prettier is a Node tool: it is fetched by `npx` on first use (the one network step
of the devkit, development machine only) and never becomes a dependency of anything
that ships. What it must not touch is listed in `.prettierignore` (templates with
{{placeholders}} in their frontmatter, generated fixtures). After formatting the
ring manifests are rewritten and the caller runs `aicowork verify`: the tests are
what prove a formatting change changed no meaning."""
import shutil
import subprocess
from pathlib import Path

PRETTIER = "prettier@3.9.9"     # pinned; bump on purpose, then run the full verify


def files(base):
    """Tracked Markdown files (git decides what is in the repository)."""
    r = subprocess.run(["git", "-C", str(base), "ls-files", "-z", "*.md"], capture_output=True, text=True)
    return [f for f in r.stdout.split("\0") if f]


def run(base, check=False):
    """-> (returncode, output). check=True lists files that would change, writes nothing."""
    base = Path(base)
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        return 2, "npx not found — install Node.js 20+ (development machine only); nothing was changed"
    targets = files(base)
    if not targets:
        return 0, "no Markdown files tracked"
    cmd = [npx, "--yes", PRETTIER, "--check" if check else "--write", "--log-level", "warn", *targets]
    r = subprocess.run(cmd, cwd=str(base), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()
