# -*- coding: utf-8 -*-
"""Tags are the link between items (Round 002): one tag shared by two notes links
them, a tag is also a group, a project's slug is its tag. `related:` is the explicit
pointer the inbox-triage skill defines. Both are frontmatter the owner can grep for;
this module reads them the one way for the CLI, the viewer and conformance."""
import re
from pathlib import Path

from aicowork_core import common as C

TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def tag_list(meta):
    """`tags:` as a list of strings — a list, or one string read as one tag."""
    v = meta.get("tags") if isinstance(meta, dict) else None
    if isinstance(v, list):
        return [str(t).strip() for t in v if str(t).strip()]
    return [str(v).strip()] if v not in (None, "") else []


def related_list(meta):
    """`related:` as a list of paths — a list, or one string."""
    v = meta.get("related") if isinstance(meta, dict) else None
    if isinstance(v, list):
        return [str(t).strip() for t in v if str(t).strip()]
    return [str(v).strip()] if v not in (None, "") else []


def bad_tags(meta):
    """Tags that are not slugs (lower-case letters, digits, hyphens)."""
    return [t for t in tag_list(meta) if not TAG_RE.match(t)]


def tag_table(base):
    """Every tag in the content folders with how many items carry it, open and in all.
    -> [{"tag", "open", "all"}], most open first."""
    base = Path(base)
    counts = {}
    for p in C.iter_md(base, C.FM_FOLDERS):
        meta, _, has = C.frontmatter(p)
        if not has:
            continue
        for t in set(tag_list(meta)):
            c = counts.setdefault(t, {"tag": t, "open": 0, "all": 0})
            c["all"] += 1
            c["open"] += 1 if C.is_open(meta.get("status")) else 0
    return sorted(counts.values(), key=lambda c: (-c["open"], -c["all"], c["tag"]))
