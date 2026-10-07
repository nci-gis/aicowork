# -*- coding: utf-8 -*-
"""Ambiguity: text that could be read two ways where the wrong reading could
let data out. The classes are the kernel's (99_system/conformance/ambiguity.json);
this is their reference detector. Pure functions, stdlib only.

Nothing here guesses what the owner meant. A file with a problem is read the
fail-closed way and every export refuses until a person fixes it."""
import json
import re
from pathlib import Path

from aicowork_core.frontmatter import Problem, parse_frontmatter_strict

PRIVATE_OPEN = "<!-- 🔒 private -->"
PRIVATE_CLOSE = "<!-- /🔒 -->"
PLACEHOLDER = "<!-- (private passage removed on export) -->"
_MARKER = re.compile(re.escape(PRIVATE_OPEN) + "|" + re.escape(PRIVATE_CLOSE))
_OPEN = re.compile(r"<!--")
_LOCKS = ("🔒", "🔐", "🔏", "🔓")
_PRIVATE_WORD = re.compile(r"^\s*/?\s*private\b", re.I)


class Ambiguous(ValueError):
    """Raised where a reading must not proceed; .problems lists why."""

    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join(describe(p) for p in problems))


def _line(text, pos):
    return text.count("\n", 0, pos) + 1


def _comments(text):
    """Every `<!--` in the text, closed or not -> (start, whole, inner).
    The valid forms are a closed list (the two markers and the placeholder);
    anything else that opens a comment is judged by what it contains, so a
    marker that lost its `-->` is caught too (review of rc.3, finding R4). An
    unclosed comment runs to the next `<!--` or the end of the text."""
    starts = [m.start() for m in _OPEN.finditer(text)]
    for i, s in enumerate(starts):
        for exact in (PRIVATE_OPEN, PRIVATE_CLOSE, PLACEHOLDER):
            if text.startswith(exact, s):
                yield s, exact, exact[4:-3]
                break
        else:
            nxt = starts[i + 1] if i + 1 < len(starts) else len(text)
            end = text.find("-->", s + 4, nxt)
            if end == -1:
                yield s, text[s:nxt], text[s + 4:nxt]
            else:
                yield s, text[s:end + 3], text[s + 4:end]


def private_block_problems(text):
    """The grammar: exact markers only, open and close strictly alternating,
    starting with an open — no nesting, no orphan, no lookalike."""
    out, depth, opened_at = [], 0, None
    for m in _MARKER.finditer(text):
        if m.group(0) == PRIVATE_OPEN:
            if depth:
                out.append(Problem("AMB-PB-NEST", _line(text, m.start()),
                                   f"a private block opens inside the one opened on line {_line(text, opened_at)}"))
            else:
                opened_at = m.start()
            depth += 1
        else:
            if not depth:
                out.append(Problem("AMB-PB-ORPHAN", _line(text, m.start()), "a private block closes, but none is open"))
            else:
                depth -= 1
    if depth:
        out.append(Problem("AMB-PB-ORPHAN", _line(text, opened_at), "a private block opens here and is never closed"))
    for start, whole, inner in _comments(text):
        if whole in (PRIVATE_OPEN, PRIVATE_CLOSE, PLACEHOLDER):
            continue
        if any(lk in inner for lk in _LOCKS) or _PRIVATE_WORD.match(inner):
            out.append(Problem("AMB-PB-NEAR", _line(text, start),
                               f"{whole[:60]!r} looks like a private-block marker but is not one"))
    return sorted(out, key=lambda p: (p.line or 0, p.cls))


def private_spans(text):
    """-> [(start, end)] of every private block, markers included.
    Raises Ambiguous when the markers do not follow the grammar."""
    problems = private_block_problems(text)
    if problems:
        raise Ambiguous(problems)
    spans, start = [], None
    for m in _MARKER.finditer(text):
        if m.group(0) == PRIVATE_OPEN:
            start = m.start()
        else:
            spans.append((start, m.end()))
    return spans


def problems(text):
    """Every ambiguity in one note: frontmatter, then private blocks."""
    _, _, fm = parse_frontmatter_strict(text)
    return list(fm) + private_block_problems(text)


def describe(p):
    return f"{p.cls}" + (f" line {p.line}" if p.line else "") + f": {p.detail}"


def load_classes(kernel):
    """-> {class id: class} from conformance/ambiguity.json ({} when unreadable)."""
    f = Path(kernel) / "conformance" / "ambiguity.json"
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {c["id"]: c for c in data.get("classes", []) if isinstance(c, dict) and "id" in c}


def advice(p, classes):
    """One line for a person: where, what, and the fix the kernel gives for it."""
    fix = (classes.get(p.cls) or {}).get("fix", "")
    return describe(p) + (f" — fix: {fix}" if fix else "")
