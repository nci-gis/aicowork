# -*- coding: utf-8 -*-
"""Plan-then-apply for risky triage operations (plan C4) — the LLM proposes,
code executes. Stdlib only.

A plan is a JSON file (Notepad-readable):
    {"moves": [{"from": "00_inbox/a.txt", "to": "01_events/2026-01-02_x.md"}, ...]}
Rules enforced here, whatever the plan says: sources only in 00_inbox/,
destinations only in content folders, no overwrite, no `..`/junction tricks,
at most MAX_MOVES moves and MAX_BYTES per file. Default is a dry run.
"""
import json
import os
from pathlib import Path

from aicowork_core import common as C
from aicowork_core.fsafe import PathRejected, safe_path
from aicowork_core.frontmatter import parse_frontmatter_strict, set_field

MAX_MOVES = 100
MAX_BYTES = 20_000_000
DEST_ROOTS = {"01_events", "02_emails", "03_personas", "04_projects", "05_results",
              "07_archive", "08_practices", "09_decisions", "10_reminders"}


class PlanError(ValueError):
    pass


def load_plan(path):
    try:
        plan = json.loads(C.read(path))
    except json.JSONDecodeError as e:
        raise PlanError(f"plan is not valid JSON: {e}")
    if not isinstance(plan, dict) or not isinstance(plan.get("moves"), list):
        raise PlanError('plan must be {"moves": [{"from": ..., "to": ...}, ...]}')
    return plan


def check_plan(base, plan):
    """-> list of (src Path, dst Path); raises PlanError on the first bad move."""
    base = Path(base)
    moves = plan["moves"]
    if len(moves) > MAX_MOVES:
        raise PlanError(f"{len(moves)} moves; at most {MAX_MOVES} per plan")
    seen, out = set(), []
    for i, m in enumerate(moves, 1):
        if not isinstance(m, dict) or set(m) - {"from", "to", "type", "circle", "note"}:
            raise PlanError(f"move {i}: only from/to/type/circle/note are allowed")
        try:
            src = safe_path(base, m.get("from", ""), roots={"00_inbox"})
            dst = safe_path(base, m.get("to", ""), roots=DEST_ROOTS)
        except PathRejected as e:
            raise PlanError(f"move {i}: {e}")
        if not src.is_file():
            raise PlanError(f"move {i}: source {m['from']} does not exist")
        if src.name in C.SKIP_NAMES:
            raise PlanError(f"move {i}: {src.name} is not an inbox item")
        if dst.exists() or str(dst).lower() in seen:
            raise PlanError(f"move {i}: destination {m['to']} already exists (no overwrite)")
        if src.stat().st_size > MAX_BYTES:
            raise PlanError(f"move {i}: source larger than {MAX_BYTES} bytes")
        seen.add(str(dst).lower())
        out.append((src, dst))
    return out


def apply(base, plan_path, do_apply=False):
    base = Path(base)
    moves = check_plan(base, load_plan(plan_path))
    lines = [f"- `{C.rel(base, s)}` → `{C.rel(base, d)}`" for s, d in moves]
    if not do_apply:
        return moves, None
    forced = []
    for s, d in moves:
        d.parent.mkdir(parents=True, exist_ok=True)
        os.replace(s, d)
        was = force_private(d)
        if was:
            forced.append(f"- `{C.rel(base, d)}`: `visibility: {was}` set to `private` (a sender's label is not the owner's)")
    report = C.write_report(base, "audit", f"{C.today().isoformat()}_triage-apply_{len(moves)}.md",
                            f"Triage plan applied — {len(moves)} moves",
                            [f"plan: `{Path(plan_path).name}`", ""] + lines + ([""] + forced if forced else []))
    return moves, report


def force_private(path):
    """CONVENTIONS "Visibility & egress": a file leaving 00_inbox/ is private whatever
    frontmatter it carried — the executor sets it, so a sender's `visibility:
    public` never becomes the owner's. A `.md` whose frontmatter cannot be read is
    left as it is (it reads as private anyway). -> the value replaced, or None."""
    path = Path(path)
    if path.suffix.lower() != ".md":
        return None
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    meta, _, problems = parse_frontmatter_strict(text)
    if not text.startswith("---") or any(p.cls in ("AMB-FM-FENCE", "AMB-FM-SYNTAX") for p in problems):
        return None
    was = meta.get("visibility")
    if was == "private":
        return None
    try:
        new = set_field(text, "visibility", "private")
    except ValueError:
        return None
    from aicowork_core.fsafe import atomic_write
    atomic_write(path, new)
    return was if was else "(unset)"
