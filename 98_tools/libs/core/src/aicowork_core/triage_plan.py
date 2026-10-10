# -*- coding: utf-8 -*-
"""Plan-then-apply for risky triage operations (plan C4) — the LLM proposes,
code executes. Stdlib only; shared by the `aicowork triage` command and the
viewer's Review/Apply card (rc.6, E7), so there is one set of rules.

A plan is a JSON file (Notepad-readable):
    {"moves": [{"from": "00_inbox/a.txt", "to": "01_events/2026-01-02_x.md"}, ...]}
Rules enforced here, whatever the plan says: sources only in 00_inbox/,
destinations only in content folders, no overwrite, no `..`/junction tricks,
at most MAX_MOVES moves and MAX_BYTES per file. Default is a dry run.

An agent that must not apply a plan itself writes it to `06_logs/triage/<date>_<n>_plan.json`
and stops; the owner applies it (the command, or the viewer). An applied plan is
renamed `*_applied.json`, a dismissed one `*_dismissed.json`: the file stays as the record.
"""
import json
import os
import re
from pathlib import Path

from aicowork_core import common as C
from aicowork_core.fsafe import PathRejected, atomic_write, safe_path
from aicowork_core.frontmatter import parse_frontmatter_strict, set_field

MAX_MOVES = 100
MAX_BYTES = 20_000_000
DEST_ROOTS = {"01_events", "02_emails", "03_personas", "04_projects", "05_results",
              "07_archive", "08_practices", "09_decisions", "10_reminders"}
PLAN_DIR = "06_logs/triage"
PLAN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*_plan\.json$")


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
        if C.rel(base, dst).startswith(tuple(f + "/" for f in C.FM_FOLDERS)):
            # where L1-FRONTMATTER judges the result, the agent prepares the note in the
            # inbox (frontmatter, markers) and the owner only moves it — a raw item would
            # land without a `type` (05_results/ and 07_archive/ take any file)
            meta, _, has = C.frontmatter(src)
            if not has or not meta.get("type"):
                raise PlanError(f"move {i}: {m['from']} has no frontmatter with a type — "
                                "the agent prepares the note before the owner moves it")
        seen.add(str(dst).lower())
        out.append((src, dst))
    return out


def apply(base, plan_path, do_apply=False):
    """Check (and with do_apply, execute) a plan. -> (moves, report path or None).
    A plan under 06_logs/triage/ is renamed *_applied.json once applied."""
    base = Path(base)
    plan_path = Path(plan_path)
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
                            [f"plan: `{plan_path.name}`", ""] + lines + ([""] + forced if forced else []))
    _retire(base, plan_path, "applied")
    return moves, report


def _retire(base, plan_path, how):
    """Rename a pending plan under 06_logs/triage/ to *_<how>.json (never delete)."""
    plan_path = Path(plan_path)
    try:
        inside = plan_path.resolve().parent == (Path(base) / PLAN_DIR).resolve()
    except OSError:
        inside = False
    if inside and PLAN_NAME.match(plan_path.name):
        new = plan_path.with_name(plan_path.name[:-len("_plan.json")] + f"_{how}.json")
        if not new.exists():
            os.replace(plan_path, new)
            return new
    return None


def dismiss(base, plan_path):
    """The owner declines a pending plan: nothing moves; the file is kept as *_dismissed.json."""
    new = _retire(base, plan_path, "dismissed")
    if new is None:
        raise PlanError("not a pending plan under 06_logs/triage/")
    return new


def plan_path(base, name):
    """A pending plan by its file name (client-supplied: validated, inside PLAN_DIR)."""
    if not PLAN_NAME.match(name or ""):
        raise PlanError("not a plan name (<date>_<n>_plan.json)")
    try:
        p = safe_path(base, f"{PLAN_DIR}/{name}", roots={"06_logs"})
    except PathRejected as e:
        raise PlanError(str(e))
    if not p.is_file():
        raise PlanError(f"no pending plan {name}")
    return p


def list_plans(base):
    """Pending plans under 06_logs/triage/, oldest first: each checked against the
    rules so the owner sees either the moves or why it cannot run."""
    base = Path(base)
    d = base / PLAN_DIR
    if not d.is_dir():
        return []
    out = []
    for p in sorted(x for x in d.iterdir() if x.is_file() and not x.is_symlink() and PLAN_NAME.match(x.name)):
        row = {"name": p.name, "path": C.rel(base, p), "moves": [], "error": None,
               "mtime": p.stat().st_mtime}
        try:
            plan = load_plan(p)
            checked = check_plan(base, plan)
            raw = {str(m.get("from")): m for m in plan["moves"] if isinstance(m, dict)}
            for s, dst in checked:
                m = raw.get(C.rel(base, s), {})
                row["moves"].append({"from": C.rel(base, s), "to": C.rel(base, dst),
                                     "type": m.get("type"), "circle": m.get("circle"), "note": m.get("note")})
        except PlanError as e:
            row["error"] = str(e)
        out.append(row)
    return out


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
    atomic_write(path, new)
    return was if was else "(unset)"
