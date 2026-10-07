# -*- coding: utf-8 -*-
"""Public claims (devkit: the kernel developer's tool, never shipped). Stdlib only.

The fixed point: every public statement names the model-call exception. An
absolute claim that nothing leaves — "nothing leaves", "never sent", "cannot
send" — is ambiguous to the reader the release is written for unless the same
passage says what does leave: what the assistant reads goes to its provider.

Class AMB-DOC-CLAIM. Deterministic: a claim is an absolute word followed, in
the same clause, by a verb of leaving; it passes when the paragraph, the one
before or the one after names the exception. Anything else is refused until a
person rewords it, or the owner records it as a false alarm in
90_devkit/claims-reviewed.json (file, the exact sentence, why, decided)."""
import json
import re
from pathlib import Path

CLASS = "AMB-DOC-CLAIM"
CLAIM = re.compile(r"\b(nothing|never|cannot|can't|can not|no (?:data|files?|cop(?:y|ies)|notes?|documents?))\b"
                   r"[^.;:!?|\n]{0,60}?\b(leaves?|leaving|sen[dt]s?|sending|uploads?|uploading|goes out|go out)\b", re.I)
EXCEPTION = re.compile(r"\bmodel\b|\bprovider\b|AI service|\bexcept\b|apart from|named egress", re.I)
_PARA = re.compile(r"\n\s*\n|\n(?=\s*(?:[-*]|\d+\.)\s)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s|\n")
REVIEWED = "90_devkit/claims-reviewed.json"


def public_docs(base):
    """The Markdown a release carries, and the repository's front page."""
    base = Path(base)
    out = [base / "README.md"] + [p for p in base.glob("*.md") if p.name not in ("CLAUDE.md", "AGENTS.md")]
    for d in ("docs", "hosts", "99_system", "98_tools"):
        out += [p for p in sorted((base / d).rglob("*.md"))
                if not ({".venv", "node_modules", "fixtures"} & set(p.relative_to(base).parts))]
    return sorted({p for p in out if p.is_file()})


def _sentence(para, m):
    starts = [x.end() for x in _SENTENCE_END.finditer(para, 0, m.start())]
    end = _SENTENCE_END.search(para, m.end())
    return para[(starts[-1] if starts else 0):(end.start() + 1 if end else len(para))].strip()


def reviewed(base):
    """Owner-decided false alarms: {(file, sentence)}."""
    f = Path(base) / REVIEWED
    if not f.is_file():
        return set()
    data = json.loads(f.read_text(encoding="utf-8"))
    return {(e["file"], e["sentence"]) for e in data.get("false_alarms", [])
            if e.get("decided") and e.get("why")}


def scan(base, files=None):
    """-> [(rel, sentence)]: absolute claims of non-egress with no exception nearby."""
    base = Path(base)
    ok, hits = reviewed(base), []
    for p in files or public_docs(base):
        rel = p.relative_to(base).as_posix()
        paras = _PARA.split(p.read_text(encoding="utf-8"))
        for i, para in enumerate(paras):
            near = "\n".join(paras[max(0, i - 1):i + 2])
            if EXCEPTION.search(near):
                continue
            for m in CLAIM.finditer(para):
                s = _sentence(para, m)
                if (rel, s) not in ok:
                    hits.append((rel, s))
    return hits
