# -*- coding: utf-8 -*-
"""A small, strict YAML subset — stdlib only.

Supported (CONVENTIONS "Instance config"):
  * block mappings and block lists, nested by indentation (spaces only)
  * flow lists `[a, b]` and flow mappings `{a: 1, b: x}` on one line
  * scalars: plain or single/double quoted strings, ints, true/false, null/~
  * `# comments` (after whitespace or at line start)
Rejected with a line number: tabs, anchors/aliases (&, *), tags (!), multi-line
strings (| >), multiple documents (--- / ...), duplicate keys.

Why not PyYAML: the agent-side tools must run inside a host sandbox with no
installs, and a small parser is auditable. The subset is the whole contract.
"""
import re

__all__ = ["loads", "load", "YamlError"]


class YamlError(ValueError):
    def __init__(self, msg, line=None):
        self.line = line
        super().__init__(f"line {line}: {msg}" if line else msg)


_INT = re.compile(r"^[-+]?\d+$")
_KEY = re.compile(r"^([A-Za-z0-9_][\w.\-]*)\s*:(\s+|$)(.*)$")


_ESC = {"\\": "\\", '"': '"', "/": "/", "0": "\0", "a": "\a", "b": "\b", "t": "\t", "\t": "\t",
        "n": "\n", "v": "\v", "f": "\f", "r": "\r", "e": "\x1b", " ": " ", "N": "\x85",
        "_": "\xa0", "L": "\u2028", "P": "\u2029"}
_HEX = {"x": 2, "u": 4, "U": 8}


def _close_quote(s, i):
    """Index of the quote that closes the one at s[i], or -1. YAML's own rules:
    in "…" a backslash escapes the next character; in '…' a quote is written
    twice. (Reading `\"` as the end of a string splits a value in two.)"""
    q, j = s[i], i + 1
    while j < len(s):
        ch = s[j]
        if q == '"' and ch == "\\":
            j += 2
            continue
        if ch == q:
            if q == "'" and s[j + 1:j + 2] == "'":
                j += 2
                continue
            return j
        j += 1
    return -1


def _unquote(t, ln):
    """The value of a whole quoted scalar t, decoded exactly; anything unclear raises."""
    if t[0] == "'":
        return t[1:-1].replace("''", "'")
    out, i, body = [], 0, t[1:-1]
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        nxt = body[i + 1:i + 2]
        if nxt in _ESC:
            out.append(_ESC[nxt])
            i += 2
        elif nxt in _HEX:
            n = _HEX[nxt]
            digits = body[i + 2:i + 2 + n]
            if len(digits) != n or not re.fullmatch(r"[0-9A-Fa-f]+", digits):
                raise YamlError(f"bad escape \\{nxt}{digits} in a quoted string", ln)
            out.append(chr(int(digits, 16)))
            i += 2 + n
        else:
            raise YamlError(f"unknown escape \\{nxt} in a quoted string", ln)
    return "".join(out)


def _strip_comment(s):
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in ("'", '"') and (i == 0 or s[i - 1] in " [{,:"):
            j = _close_quote(s, i)
            if j < 0:                       # unterminated: keep the rest; _scalar reports it
                out.append(s[i:])
                break
            out.append(s[i:j + 1])
            i = j + 1
            continue
        if ch == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _scalar(tok, ln):
    t = tok.strip()
    if t == "":
        return None
    if t[0] in "&*!|>":
        raise YamlError(f"unsupported YAML feature {t[0]!r} (subset only)", ln)
    if t[0] in ("'", '"'):
        j = _close_quote(t, 0)
        if j < 0:
            raise YamlError("unterminated quoted string", ln)
        if j != len(t) - 1:
            raise YamlError("text after a closing quote", ln)
        return _unquote(t, ln)
    low = t.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if _INT.match(t):
        return int(t)
    return t


def _split_flow(body, ln):
    items, depth, cur, i = [], 0, [], 0
    while i < len(body):
        ch = body[i]
        if ch in ("'", '"'):
            j = _close_quote(body, i)
            if j < 0:
                raise YamlError("unbalanced flow collection", ln)
            cur.append(body[i:j + 1])
            i = j + 1
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    if depth:
        raise YamlError("unbalanced flow collection", ln)
    if "".join(cur).strip():
        items.append("".join(cur))
    return [i.strip() for i in items]


def _value(tok, ln):
    t = tok.strip()
    if t.startswith("["):
        if not t.endswith("]"):
            raise YamlError("flow list must close on the same line", ln)
        return [_value(i, ln) for i in _split_flow(t[1:-1], ln)]
    if t.startswith("{"):
        if not t.endswith("}"):
            raise YamlError("flow mapping must close on the same line", ln)
        out = {}
        for item in _split_flow(t[1:-1], ln):
            m = re.match(r"^([A-Za-z0-9_][\w.\-]*)\s*:\s*(.*)$", item)
            if not m:
                raise YamlError(f"bad flow mapping item {item!r}", ln)
            if m.group(1) in out:
                raise YamlError(f"duplicate key {m.group(1)!r}", ln)
            out[m.group(1)] = _value(m.group(2), ln)
        return out
    return _scalar(t, ln)


def _lines(text):
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[:len(raw) - len(raw.lstrip())]:
            raise YamlError("tab in indentation", n)
        s = _strip_comment(raw)
        if not s.strip():
            continue
        if s.strip() in ("---", "..."):
            raise YamlError("multiple documents are not supported", n)
        out.append((n, len(s) - len(s.lstrip(" ")), s.strip()))
    return out


def _parse_block(lines, i, indent):
    """Parse the block starting at lines[i] whose indentation is `indent`."""
    if i >= len(lines):
        return None, i
    ln, ind, s = lines[i]
    if s.startswith("- ") or s == "-":
        return _parse_list(lines, i, ind)
    return _parse_map(lines, i, ind)


def _child(lines, i, parent_indent, ln):
    """Value on the following, more-indented lines (or None)."""
    if i < len(lines) and lines[i][1] > parent_indent:
        return _parse_block(lines, i, lines[i][1])
    # a list may sit at the same indent as its key ("key:\n- a")
    if i < len(lines) and lines[i][1] == parent_indent and lines[i][2].startswith("- "):
        return _parse_list(lines, i, parent_indent)
    return None, i


def _parse_map(lines, i, indent):
    out = {}
    while i < len(lines):
        ln, ind, s = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise YamlError("unexpected indentation", ln)
        if s.startswith("- "):
            break
        m = _KEY.match(s)
        if not m:
            raise YamlError(f"expected 'key: value', got {s!r}", ln)
        key, rest = m.group(1), m.group(3)
        if key in out:
            raise YamlError(f"duplicate key {key!r}", ln)
        i += 1
        if rest.strip():
            out[key] = _value(rest, ln)
        else:
            out[key], i = _child(lines, i, indent, ln)
    return out, i


def _parse_list(lines, i, indent):
    out = []
    while i < len(lines):
        ln, ind, s = lines[i]
        if ind < indent or not (s.startswith("- ") or s == "-"):
            if ind > indent:
                raise YamlError("unexpected indentation", ln)
            break
        if ind > indent:
            raise YamlError("unexpected indentation", ln)
        item = s[1:].strip()
        i += 1
        if not item:
            val, i = _child(lines, i, indent, ln)
            out.append(val)
        elif _KEY.match(item):
            # "- key: v" starts a mapping whose other keys sit at indent+2
            sub_indent = indent + 2
            fake = [(ln, sub_indent, item)]
            j = i
            while j < len(lines) and lines[j][1] >= sub_indent:
                fake.append(lines[j])
                j += 1
            val, k = _parse_map(fake, 0, sub_indent)
            if k != len(fake):
                raise YamlError("bad mapping inside list item", fake[k][0])
            out.append(val)
            i = j
        else:
            out.append(_value(item, ln))
    return out, i


def loads(text):
    lines = _lines(text or "")
    if not lines:
        return {}
    val, i = _parse_block(lines, 0, lines[0][1])
    if i != len(lines):
        raise YamlError("could not parse the rest of the file", lines[i][0])
    return val


def load(path):
    with open(path, encoding="utf-8") as f:
        return loads(f.read())
