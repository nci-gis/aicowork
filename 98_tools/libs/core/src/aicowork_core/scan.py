# -*- coding: utf-8 -*-
"""Leak scanners and file selection, shared by every tool that lets something
leave the folder: export (owner), release builds (devkit). One implementation,
tested once: two copies would drift, and a weaker copy is an unreported leak.
Stdlib only."""
import re
from pathlib import Path

from aicowork_core import common as C

EXCLUDE_PARTS = {".git", ".venv", "data", "__pycache__", ".pytest_cache", "_scratch",
                 "_to_delete", "node_modules", ".agents"}
EXCLUDE_NAMES = {"Thumbs.db", "desktop.ini", ".DS_Store"}
EXCLUDE_SUFFIX = {".pyc", ".tmp", ".bak", ".zip", ".bundle", ".db"}

# scanner B — generic patterns that should never appear in a public artifact
GENERIC = [
    # RFC 2606 / 6761 reserved names (example.*, *.example, .invalid, .test) are
    # what fixtures and docs must use, so they are never a leak
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@(?![A-Za-z0-9.-]*\bexample\.(?:com|org|net)\b)"
                         r"(?![A-Za-z0-9.-]+\.(?:example|invalid|test)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("api token", re.compile(r"\b(?:sk|pk|ghp|gho|xox[abp])[-_][A-Za-z0-9]{20,}\b")),
    ("password assignment", re.compile(r"(?i)\b(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"\s]{6,}")),
    ("user path", re.compile(r"(?i)[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]{2,}")),
    ("home path", re.compile(r"/home/[a-z][a-z0-9_-]{2,}/")),
    # any other absolute drive path (D:\var\…, E:/work/…): a machine's layout is owner data
    ("drive path", re.compile(r"(?<![A-Za-z0-9<])[A-Za-z]:[\\/]+(?!Users\b)[A-Za-z0-9_.-]{2,}[\\/]+[A-Za-z0-9_.\\/-]*")),
]
# known-good third-party text (licence headers of vendored files) is scanned
# for tokens but not for the generic email pattern
GENERIC_SKIP = ("98_tools/apps/viewer/src/viewer/web/vendor/",)
DOC_SUFFIX = {".md", ".yaml", ".yml", ".txt", ".json", ".toml", ""}
FIXTURES = "99_system/conformance/fixtures/"


# ---------------- normalisation: the ways a token can be hidden (CONVENTIONS "Session rules" 5) ----------------
# look-alike letters that read as Latin: Cyrillic and Greek homoglyphs (a small, explicit table —
# not Unicode's whole confusables list; what is not here is "not claimed" in SECURITY)
CONFUSABLES = str.maketrans({
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0443": "y", "\u0445": "x",
    "\u0456": "i", "\u0458": "j", "\u04bb": "h", "\u0501": "d", "\u051b": "q", "\u0455": "s", "\u0461": "w",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M", "\u041d": "H", "\u041e": "O",
    "\u0420": "P", "\u0421": "C", "\u0422": "T", "\u0425": "X", "\u0406": "I", "\u0408": "J", "\u0405": "S",
    "\u03b1": "a", "\u03bf": "o", "\u03c1": "p", "\u03bd": "v", "\u03b9": "i", "\u03ba": "k", "\u03c5": "u",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I", "\u039a": "K",
    "\u039c": "M", "\u039d": "N", "\u039f": "O", "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
    "\u00ad": "",            # soft hyphen
})
_INVISIBLE = re.compile("[\u200b-\u200f\u2028-\u202e\u2060-\u2064\u2066-\u206f\ufeff\u00ad\u180e]")
_SOFT_BREAK = re.compile(r"(?<=\w)-?\r?\n(?=\w)")
_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])|(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{24,}(?![A-Za-z0-9_-])")
_MIXED = re.compile(r"[^\W\d_]+", re.UNICODE)


def normalise(text):
    """NFKC, invisible format characters removed, look-alike letters mapped to Latin."""
    import unicodedata
    return unicodedata.normalize("NFKC", text).translate(CONFUSABLES)


def _decoded(text):
    """percent-, entity- and base64-decoded forms of `text`, each run through normalise()."""
    import base64
    import html
    from urllib.parse import unquote
    out = []
    if "%" in text:
        out.append(("percent encoding", normalise(unquote(text))))
    if "&" in text:
        out.append(("HTML entities", normalise(html.unescape(text))))
    blobs = []
    for m in _B64.finditer(text):
        s = m.group(0)
        for fn in (base64.b64decode, base64.urlsafe_b64decode):
            try:
                raw = fn(s + "=" * (-len(s) % 4))
                dec = raw.decode("utf-8")
            except Exception:
                continue
            if dec and sum(c.isprintable() or c.isspace() for c in dec) / len(dec) > 0.9:
                blobs.append(dec)
                break
    if blobs:
        out.append(("base64", normalise("\n".join(blobs))))
    return out


def variants(text):
    """[(layer, text)] to scan: ("", plain) first, then the normalised text, the text
    with soft line breaks joined (as nothing, as a space), and the decoded forms."""
    norm = normalise(_INVISIBLE.sub("", text))
    out = [("", text), ("look-alike or invisible characters", norm)]
    if _SOFT_BREAK.search(norm):
        out.append(("a soft line break", _SOFT_BREAK.sub("", norm)))
        out.append(("a soft line break", _SOFT_BREAK.sub(" ", norm)))
    out += _decoded(norm)
    return out


def hidden_chars(text):
    """The report layer (L2-HIDDEN): characters a person cannot see, and words that
    mix scripts -> [(line, kind, shown)]. Emoji sequences joined by U+200D are
    legitimate and are not reported."""
    import unicodedata
    out = []
    for n, line in enumerate(text.split("\n"), 1):
        for i, ch in enumerate(line):
            if not _INVISIBLE.match(ch) and unicodedata.category(ch) != "Cf":
                continue
            if ch == "\u200d":                # ZWJ inside an emoji sequence: fine
                prev = line[i - 1] if i else ""
                nxt = line[i + 1] if i + 1 < len(line) else ""
                if any(unicodedata.category(c) == "So" or ord(c) >= 0x1F000 for c in (prev, nxt)):
                    continue
            out.append((n, "invisible character", f"U+{ord(ch):04X} {unicodedata.name(ch, '?')}"))
        for m in _MIXED.finditer(line):
            w = m.group(0)
            scripts = set()
            for c in w:
                o = ord(c)
                if o < 0x250 or 0x1E00 <= o <= 0x1EFF:
                    scripts.add("Latin")
                elif 0x370 <= o <= 0x3FF:
                    scripts.add("Greek")
                elif 0x400 <= o <= 0x52F:
                    scripts.add("Cyrillic")
            if len(scripts) > 1 and "Latin" in scripts:
                out.append((n, "mixed scripts", w))
    return out


def _skip(rel):
    parts = rel.parts
    return (any(p in EXCLUDE_PARTS for p in parts) or rel.name in EXCLUDE_NAMES
            or rel.suffix.lower() in EXCLUDE_SUFFIX)


def collect(base, items):
    base = Path(base)
    out = []
    for item in items:
        p = base / item
        if p.is_file():
            out.append(Path(item))
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                r = f.relative_to(base)
                if f.is_file() and not f.is_symlink() and not _skip(r):
                    out.append(r)
    return out


def _strings(data, min_len=6):
    return "\n".join(m.group(0).decode("latin-1") for m in re.finditer(rb"[\x20-\x7e]{%d,}" % min_len, data))


def scan_tokens(root, tokens, base_paths):
    """Scanner A: owner tokens + base-path variants, in names and contents."""
    pats = C.token_patterns(set(tokens) | set(base_paths))
    hits = []
    for f in sorted(Path(root).rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        r = f.relative_to(root).as_posix()
        data = f.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = _strings(data)
        for tok, rx in pats:
            if rx.search(r):
                hits.append((r, f"file name contains {tok!r}"))
            # the plain text first, then every way the text could hide the token
            # (CONVENTIONS "Session rules" 5; what is not undone: SECURITY "not claimed")
            for layer, variant in variants(text):
                if rx.search(variant):
                    hits.append((r, f"content contains {tok!r}" + (f" (hidden by {layer})" if layer else "")))
                    break
    return hits


def scan_generic(root):
    """Scanner B: e-mail addresses, secrets, personal paths."""
    hits = []
    for f in sorted(Path(root).rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        r = f.relative_to(root).as_posix()
        data = f.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = _strings(data)
        text = variants(text)[1][1] if len(variants(text)) > 1 else text   # NFKC, invisible chars gone
        for label, rx in GENERIC:
            if label == "email" and r.startswith(GENERIC_SKIP):
                continue
            if label == "drive path" and f.suffix.lower() not in DOC_SUFFIX:
                continue                       # code and tests use made-up paths; docs must not
            m = rx.search(text)
            if m:
                hits.append((r, f"{label}: {m.group(0)[:60]!r}"))
    return hits
