# -*- coding: utf-8 -*-
"""Untrusted-content quarantine for 00_inbox/ (plan C4). Stdlib only.

For every text item in the inbox: strip invisible/bidi characters and HTML
comments (hiding places for injected instructions), neutralise any marker the
text itself tries to fake, wrap the body in <<UNTRUSTED id=nonce>> ...
<<END id=nonce>> with a random nonce the author of the text cannot know, and
list phrases that look like instructions to an AI. Spotlighting is defence in
depth, not a guarantee: the model can still be talked out of it.
"""
import re
import secrets
from pathlib import Path

from aicowork_core import common as C

TEXT_EXT = {".md", ".txt", ".eml", ".html", ".htm", ".csv", ".json", ".ics", ""}
INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿­\U000e0000-\U000e007f]")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
SUSPICIOUS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"disregard (the|your) (rules|instructions|system prompt)",
    r"you are now", r"new instructions", r"system prompt",
    r"\b(set|change|raise|make)\b.{0,40}\bvisibility\b", r"visibility\s*(:|to)?\s*(public|internal)",
    r"\bexport\b.{0,30}\b(everything|every|all|them)\b|\b(everything|every file|all files)\b.{0,30}\bexport\b",
    r"policy\.yaml", r"99_system", r"instruction file", r"CLAUDE\.md|AGENTS\.md",
    r"\bcurl\b|\bwget\b|Invoke-WebRequest", r"api[_-]?key", r"upload (this|the) file",
    r"send (this|the|all) (file|files|data|notes) to", r"base64",
    r"do not (tell|inform) the (user|owner)", r"quietly|silently|secretly",
    r"\b(delete|remove|erase|wipe|purge)\b.{0,40}\b(folder|files?|archive|history|(?:0\d|10)_\w+)",
    r"\bpurge\b", r"\bmove every\b|\bmove all\b", r"rm -rf", r"\bforce\b.{0,20}\b(push|history)",
    r"squash all commits", r"git (push|remote)|add remote|push all branches",
    r"0\.0\.0\.0", r"module\.yaml", r"skills?/[\w-]+/SKILL\.md", r"03_personas/me\.md",
    r"\bI approve\b|from the owner|\bI am the (new )?owner", r"no approvals?|without asking",
    r"<script|onerror\s*=|javascript:", r"!\[[^\]]*\]\(https?://", r"\]\(https?://[^)]*\?",
    r"\bDevMode\b|\bjailbreak", r"\.exe\b|‮", r"run (it|the payload|this)",
    r"email all|e-?mail (it|them|everything) to",
    r"((?:0\d|10)_\w+|folder|archive|files).{0,60}\b(delete|remove|erase|wipe)\b",
]
_SUS = [re.compile(p, re.I) for p in SUSPICIOUS]


def neutralise(text):
    text = INVISIBLE.sub("", text)
    text = HTML_COMMENT.sub("", text)
    return text.replace("<<UNTRUSTED", "‹‹UNTRUSTED").replace("<<END", "‹‹END")


def flags(text):
    return sorted({m.group(0) for rx in _SUS for m in rx.finditer(text)})


def wrap(text):
    """-> (wrapped text, nonce, flags). Keeps a leading frontmatter block outside."""
    fm, body = "", text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm, body = text[:end + 4] + "\n", text[end + 4:].lstrip("\n")
    hidden = []
    if HTML_COMMENT.search(body):
        hidden.append("hidden HTML comment (removed)")
    if INVISIBLE.search(body):
        hidden.append("invisible/bidi characters (removed)")
    # flag on the raw text too, so what was hidden is still reported
    found = sorted(set(flags(body)) | set(hidden))
    clean = neutralise(body)
    nonce = secrets.token_hex(6)
    return (f"{fm}<<UNTRUSTED id={nonce}>>\n{clean.rstrip()}\n<<END id={nonce}>>\n",
            nonce, found)


_WRAPPED = re.compile(r"\A(?:---\n.*?\n---\n)?<<UNTRUSTED id=([0-9a-f]{12})>>\n.*\n<<END id=\1>>\n?\Z", re.S)


def is_wrapped(text):
    """Only our own wrapper counts: one pair, our nonce format, around the whole
    body, and no other marker inside. A text that merely *contains* a marker is
    an attempt to fake one and is wrapped again (its markers neutralised)."""
    m = _WRAPPED.match(text.replace("\r\n", "\n"))
    return bool(m) and text.count("<<UNTRUSTED") == 1 and text.count("<<END") == 1


def ingest(base, dry_run=False):
    """-> list of (relpath, status, flags)."""
    base = Path(base)
    inbox = base / "00_inbox"
    out = []
    for p in sorted(inbox.iterdir()) if inbox.is_dir() else []:
        if not p.is_file() or p.name in C.SKIP_NAMES or p.name.startswith("."):
            continue
        if p.suffix.lower() not in TEXT_EXT:
            out.append((C.rel(base, p), "binary — not wrapped", []))
            continue
        text = C.read(p)
        if is_wrapped(text):
            out.append((C.rel(base, p), "already wrapped", flags(text)))
            continue
        wrapped, nonce, fl = wrap(text)
        if not dry_run:
            C.atomic_write(p, wrapped)
        out.append((C.rel(base, p), f"wrapped (id={nonce})", fl))
    return out
