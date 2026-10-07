# -*- coding: utf-8 -*-
"""Reading notes: the frontmatter every tool parses the same way. Pure functions.

Frontmatter is the YAML subset of CONVENTIONS "Instance config", parsed by the
one strict parser (yamlite). Anything it cannot read is not guessed at: the
file reads as having no frontmatter (so it is private) and the problem is
reported with its ambiguity class (99_system/conformance/ambiguity.json)."""
import datetime as dt
from collections import namedtuple

from aicowork_core.yamlite import YamlError, _strip_comment, loads

# one problem: ambiguity class id, line number in the file (1-based, or None), detail
Problem = namedtuple("Problem", "cls line detail")

VIS_KEY = "visibility"
VIS_VALUES = ("private", "internal", "public")


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _split(text):
    """-> (block or None, body, problems). The opening line and the closing line
    must each be exactly `---`; a file that only looks fenced is a problem."""
    lines = text.split("\n")
    if lines[0].rstrip() != "---":
        if text.lstrip("﻿ \t\r\n").startswith("---"):
            return None, text, [Problem("AMB-FM-FENCE", 1, "the file looks fenced, but its first line is not exactly `---`")]
        return None, text, []
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), []
        if lines[i].startswith("---"):
            break
    return None, text, [Problem("AMB-FM-FENCE", 1, "the frontmatter is not closed by a line that is exactly `---`")]


def _flat(v):
    """yamlite values -> the strings every reader compares against."""
    if v is None:
        return ""
    if v is True or v is False:
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return [_flat(x) if not isinstance(x, (dict, list)) else x for x in v]
    return v


def _distance(a, b):
    """Edit distance (Levenshtein), small strings only."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _vis_lookalikes(data, top=True):
    """Keys that look like `visibility` but are not it at the top level."""
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            low = str(k).lower()
            if k == VIS_KEY and not top:
                out.append(f"`{k}` nested under another key")
            elif k != VIS_KEY and (low == VIS_KEY or _distance(low, VIS_KEY) <= 2):
                out.append(f"`{k}` looks like `visibility`")
            out += _vis_lookalikes(v, top=False)
    elif isinstance(data, list):
        for x in data:
            out += _vis_lookalikes(x, top=False)
    return out


def parse_frontmatter_strict(text):
    """-> (meta, body, problems). On a fence or syntax problem meta is {} (the
    file reads as private); on a visibility problem `visibility` is removed
    (it reads as private). Problems carry the ambiguity class."""
    block, body, problems = _split(text)
    if block is None:
        return {}, body, problems
    try:
        data = loads(block)
    except YamlError as e:
        line = e.line + 1 if e.line else None   # +1: the opening fence
        return {}, body, [Problem("AMB-FM-SYNTAX", line, str(e).split(": ", 1)[-1] if e.line else str(e))]
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return {}, body, [Problem("AMB-FM-SYNTAX", 2, "the frontmatter is not a list of `key: value` lines")]
    meta = {k: _flat(v) for k, v in data.items()}
    for detail in _vis_lookalikes(data):
        problems.append(Problem("AMB-FM-VIS-KEY", None, detail))
    vis = data.get(VIS_KEY)
    if VIS_KEY in data and vis is not None and vis not in VIS_VALUES:
        problems.append(Problem("AMB-FM-VIS-VALUE", None, f"visibility {vis!r} is not exactly private, internal or public"))
    if any(p.cls == "AMB-FM-VIS-KEY" for p in problems):
        meta.pop(VIS_KEY, None)
    return meta, body, problems


def parse_frontmatter(text):
    """-> (meta, body). Strict: see parse_frontmatter_strict."""
    meta, body, _ = parse_frontmatter_strict(text)
    return meta, body


def set_field(text, key, value):
    """Set one top-level frontmatter key, keeping every other byte: the order,
    other lines, a trailing ` # comment` on that line, LF or CRLF. Replaces the
    `key:` line, or inserts it before the closing fence. Raises ValueError when
    the text has no frontmatter. Used by "mark done" (reminders)."""
    lines = text.split("\n")
    if lines[0].rstrip() != "---":                  # the same fences as _split
        raise ValueError("no frontmatter")
    end = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            end = i
            break
        if lines[i].startswith("---"):
            break
    if end is None:
        raise ValueError("frontmatter is not closed")
    eol = "\r" if lines[end].endswith("\r") else ""
    prefix = f"{key}:"
    for i in range(1, end):
        raw = lines[i][:-1] if lines[i].endswith("\r") else lines[i]
        if raw.startswith(prefix) and (len(raw) == len(prefix) or raw[len(prefix)] in " \t"):
            after = raw[len(prefix):]
            rest = after.lstrip(" \t")
            val = _strip_comment(rest)
            tail = rest[len(val):] if val else after      # spacing before `#` kept
            comment = tail if "#" in tail else ""
            lines[i] = f"{prefix} {value}{comment}" + ("\r" if lines[i].endswith("\r") else "")
            return "\n".join(lines)
    lines.insert(end, f"{prefix} {value}{eol}")
    return "\n".join(lines)


def md_title(body, fallback):
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def parse_date(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None
