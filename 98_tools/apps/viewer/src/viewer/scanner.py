# -*- coding: utf-8 -*-
"""Reading and parsing the base folder's markdown files. Pure functions, no state."""
import datetime as dt
import json
import re
from pathlib import Path

from aicowork_core.frontmatter import read_text, parse_frontmatter, md_title, parse_date  # noqa: F401
from .config import BASE, ALL_FOLDERS, CIRCLES, SKIP_NAMES


def disk_state():
    """{relpath: (default_kind, mtime_ns, size)} for every indexable .md file."""
    state = {}
    for kind, folder in ALL_FOLDERS.items():
        root = BASE / folder
        if not root.is_dir():
            continue
        for p in root.rglob("*.md"):
            if p.name in SKIP_NAMES or p.is_symlink():    # a link is reported by the tools, never read here
                continue
            st = p.stat()
            rel = str(p.relative_to(BASE)).replace("\\", "/")
            state[rel] = (kind, st.st_mtime_ns, st.st_size)
    return state


LIST_FIELDS = {"tags", "days"}


def _s(v):
    """A frontmatter value as the index stores it: a non-empty string, or None
    (lists and nested mappings are not scalars and are never coerced)."""
    return v if isinstance(v, str) and v else None


def parse_file(rel, default_kind):
    """Parse one file into an index row dict (includes body for FTS)."""
    p = BASE / rel
    meta, body = parse_frontmatter(read_text(p))
    # a list only where the field is a list; anywhere else a list (or a mapping)
    # is not a value the index can store, so the field is empty (review of rc.3, R6)
    meta = {k: (v if k in LIST_FIELDS and isinstance(v, list) else _s(v)) for k, v in meta.items()}
    circle = meta.get("circle") or ""
    kind = meta.get("type") if _s(meta.get("type")) in ALL_FOLDERS else default_kind
    is_reminder = meta.get("type") == "reminder"
    qc = q_counts(body)
    return {
        "path": rel,
        "kind": kind,
        "title": md_title(body, p.stem.replace("-", " ").replace("_", " ")),
        "circle": circle if circle in CIRCLES else None,
        # v1.3: may this file leave the machine? fail-closed — anything that is
        # not exactly one of the three levels is treated as private.
        "visibility": (meta.get("visibility") if meta.get("visibility")
                       in ("private", "internal", "public") else "private"),
        "date": meta.get("date") or None,
        "time": meta.get("time") or None,
        "status": meta.get("status") or None,
        "tags": ",".join(str(t) for t in meta.get("tags")) if isinstance(meta.get("tags"), list) else "",
        # v1.2 fields (see 99_system/CONVENTIONS.md)
        "cadence": meta.get("cadence") or None,
        "until": str(meta.get("until")) if meta.get("until") else None,
        # reminders (CONVENTIONS "Reminders"), only for `type: reminder`: `days`
        # as JSON, so a list and a scalar stay what they were ("15, 16" is invalid)
        "repeat": (meta.get("repeat") or None) if is_reminder else None,
        "days": (json.dumps(meta["days"]) if is_reminder and meta.get("days") not in (None, "") else None),
        "last_done": (meta.get("last_done") or None) if is_reminder else None,
        "last_contact": meta.get("last_contact") or None,
        "role": meta.get("role") or None,
        "energy": _int_or_none(meta.get("energy"), 1, 5),
        "q": _int_or_none(meta.get("q"), 1, 4),
        "q1": qc[1], "q2": qc[2], "q3": qc[3], "q4": qc[4],
        "lessons": lessons(body, meta.get("date"), BASE),
        "body": body,
    }


def scan_inbox():
    root = BASE / "00_inbox"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir()
                  if p.is_file() and p.name not in SKIP_NAMES)


def scan_results(limit=8):
    root = BASE / "05_results"
    if not root.is_dir():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink() and p.name not in SKIP_NAMES]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [{
        "name": p.name,
        "path": str(p.relative_to(BASE)).replace("\\", "/"),
        "is_md": p.suffix.lower() == ".md",
        "modified": dt.date.fromtimestamp(p.stat().st_mtime).isoformat(),
    } for p in files[:limit]]


def last_triage():
    m = re.search(r"Last triage:\s*([^|\n]+)", read_text(BASE / "INDEX.md"))
    return m.group(1).strip() if m else "unknown"


def _int_or_none(v, lo, hi):
    try:
        n = int(str(v))
        return n if lo <= n <= hi else None
    except (ValueError, TypeError):
        return None


_Q_TAG = re.compile(r"#q([1-4])\b", re.IGNORECASE)


def q_counts(body):
    """Inline Eisenhower tags on task lines: '#q1'..'#q4' (Habit 3).
    Returns {1: n, 2: n, 3: n, 4: n}."""
    c = {1: 0, 2: 0, 3: 0, 4: 0}
    for m in _Q_TAG.finditer(body):
        c[int(m.group(1))] += 1
    return c


def lesson_context(text, base=None):
    """The trailing `[context]` of a lesson line (inbox-triage step 6). -> (text without
    it, path or None): a path when it names an existing file inside the folder (E8),
    else the label stays in the text and the path is None."""
    m = re.search(r"\s*\[([^\[\]]{1,200})\]\s*$", text)
    if not m or base is None:
        return text, None
    label = m.group(1).strip()
    if not label or "\\" in label or label.startswith(("/", "~")) or ".." in label.split("/"):
        return text, None
    p = Path(base) / label
    try:
        inside = p.resolve().is_relative_to(Path(base).resolve())
    except (OSError, ValueError):
        inside = False
    if inside and p.is_file() and not p.is_symlink():
        return text[:m.start()].rstrip(), label
    return text, None


def lessons(body, date, base=None):
    """Lines tagged #lesson anywhere -> [(date, text, context)] for the lessons index;
    `context` is the path a trailing `[context]` names when such a file exists (E8).

    HTML comments are skipped: templates explain the tag inside <!-- --> blocks,
    and an instruction about lessons is not itself a lesson."""
    out = []
    in_comment = False
    for line in body.splitlines():
        stripped = line.strip()
        if in_comment:
            in_comment = "-->" not in stripped
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped
            continue
        if "#lesson" in line.lower():
            text = re.sub(r"#lesson\b", "", line, flags=re.IGNORECASE)
            text = re.sub(r"\s+", " ", text).strip().lstrip("-*").strip()
            # A bare label ("One lesson:") is an unfilled template placeholder,
            # not a lesson — indexing it would junk up the Lessons card.
            if text and not text.endswith(":"):
                text, ctx = lesson_context(text, base)
                out.append((str(date or ""), text, ctx))
    return out


DEFAULT_APPS = [
    {"id": "dashboard", "name": "Dashboard (Today + Launcher)", "kind": "route",
     "target": "/", "circle": "all"},
    {"id": "browse", "name": "Browse & Search", "kind": "route",
     "target": "/browse", "circle": "all"},
]


def load_registry():
    """Apps from the instance's aicowork.yaml `apps:` (PHILOSOPHY #4); the two
    built-in routes when the instance lists none."""
    from .config import APPS
    apps = [{k: str(v) for k, v in a.items()} for a in APPS] or DEFAULT_APPS
    return [a for a in apps if a.get("id") and a.get("name")]
