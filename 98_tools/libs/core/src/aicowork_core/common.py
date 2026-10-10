# -*- coding: utf-8 -*-
"""Shared helpers for the stdlib-only commands (no installs).

Every function takes an explicit `base` folder so the same code checks the
owner's instance, the example instance, or a fresh rebuild in a temp folder.
"""
import datetime as dt
import hashlib
import os
import re
import subprocess
from pathlib import Path

from aicowork_core.contract import CIRCLES, EDITABLE_ROOTS, SKIP_NAMES
from aicowork_core.frontmatter import parse_frontmatter, parse_frontmatter_strict
from aicowork_core.yamlite import YamlError, loads as yaml_loads

VIS_RANK = {"public": 0, "internal": 1, "private": 2}   # higher = more sensitive
TYPES = ("event", "email", "persona", "project", "log", "note", "practice", "decision",
         "reminder")
REQUIRED_BY_TYPE = {
    "event": ("circle", "date"), "email": ("circle", "date"), "persona": ("circle",),
    "project": ("circle",), "practice": ("circle", "cadence"),
    "decision": ("circle", "date"), "log": ("date",), "note": (),
    "reminder": ("circle", "date", "repeat", "days"),
}
SKELETON = ("00_inbox", "01_events", "02_emails", "03_personas", "04_projects",
            "05_results", "06_logs/daily", "06_logs/weekly", "06_logs/triage", "07_archive",
            "08_practices", "09_decisions", "10_reminders", "99_system")   # 99_system last; REBUILD §1's list
# Frontmatter is checked in these folders (07_archive is retired material; 05_results
# holds deliverables of any format; 06_logs/<reports> are tool output).
FM_FOLDERS = ("01_events", "02_emails", "03_personas", "04_projects",
              "06_logs/daily", "06_logs/weekly", "08_practices", "09_decisions",
              "10_reminders")
NEVER_EXPORT = ("00_inbox/**", "06_logs/**", "INDEX.md")
PROTECTED = ("99_system/**", "policy.yaml", "aicowork.yaml", "CLAUDE.md", "AGENTS.md",
             "INSTRUCTIONS.md", "03_personas/me.md", ".githooks/**", ".claude/**", "98_tools/**",
             "modules.lock", ".gitattributes", ".gitignore")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def base_path(base=None):
    if base:
        return Path(base).resolve()
    from aicowork_core.config import BASE
    return BASE


def kernel_dir(base):
    return Path(base) / "99_system"


def hosts_dir(base):
    return Path(base) / "hosts"


def ring_roots(base):
    """The hash-locked ring folders: (label, path). Kernel = spec; hosts = host
    adapters (beside the kernel, not in it); tools = reference implementation."""
    base = Path(base)
    return [("kernel", kernel_dir(base)), ("hosts", hosts_dir(base)), ("tools", base / "98_tools")]


def rel(base, p):
    """Path relative to base, as the folder shows it — lexically first, so a symlink
    that points outside the folder is still named by where it sits (and reported
    by `links`), never followed into a crash."""
    try:
        return Path(p).absolute().relative_to(Path(base).absolute()).as_posix()
    except ValueError:
        return Path(p).resolve().relative_to(Path(base).resolve()).as_posix()


def links(base, folders=None):
    """Symbolic links under the given folders (default: the content folders) ->
    [(rel path, target, outside)]. CONVENTIONS "Reach": a link out of the folder
    is a reach error — reported, never followed; every walker here skips links."""
    base = Path(base)
    out = []
    for folder in folders or sorted(EDITABLE_ROOTS):
        root = base / folder
        if not root.is_dir() or root.is_symlink():
            if root.is_symlink():
                out.append((folder, os.readlink(root), True))
            continue
        for p in sorted(root.rglob("*")):
            if p.is_symlink():
                try:
                    inside = p.resolve().is_relative_to(base.resolve())
                except OSError:
                    inside = False
                out.append((rel(base, p), os.readlink(p), not inside))
    return out


def read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def frontmatter(p):
    text = read(p)
    meta, body = parse_frontmatter(text)
    return meta, body, text.startswith("---")


def visibility(meta):
    v = meta.get("visibility")
    return v if isinstance(v, str) and v in VIS_RANK else "private"


def glob_match(path, pattern):
    """POSIX-style glob with ** (any depth) — enough for policy/module globs."""
    rx = re.escape(pattern).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*") \
        .replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(rx, path) is not None


def any_match(path, patterns):
    return any(glob_match(path, p) for p in patterns)


def iter_md(base, folders):
    base = Path(base)
    for folder in folders:
        root = base / folder
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if p.name in SKIP_NAMES or p.is_symlink() or any(part.startswith(".") for part in p.relative_to(base).parts):
                continue
            yield p


def load_yaml(p):
    """-> (data, error)."""
    p = Path(p)
    if not p.is_file():
        return None, f"{p.name} not found"
    try:
        return yaml_loads(read(p)), None
    except YamlError as e:
        return None, f"{p.name}: {e}"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def files_in_order(root, pattern="*"):
    """Every file under root, in the order of its POSIX relative path. The same
    on every OS: sorting Path objects is case-insensitive on Windows and not on
    Linux, so a hash over a listing made that way differs between the two
    (review of rc.3, R5). Use it for anything hashed or written as a list."""
    root = Path(root)
    return sorted((p for p in root.rglob(pattern) if p.is_file() and not p.is_symlink()),
                  key=lambda p: p.relative_to(root).as_posix())


def git(base, *args, check=False):
    """Run git in base -> (returncode, stdout). git missing -> (127, '')."""
    try:
        r = subprocess.run(["git", "-C", str(base), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return 127, ""
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.returncode, r.stdout


def is_git(base):
    return git(base, "rev-parse", "--is-inside-work-tree")[0] == 0


def is_instance(base):
    """An instance has its owner config at the root. The kernel's development
    repository (kernel + hosts + tools, no owner data) does not."""
    return (Path(base) / "aicowork.yaml").is_file()


def deny_source(base, deny_from=None):
    """The instance whose names must never appear in what `base` ships. -> Path or None.
    In an instance it is the instance itself. In the development repository it is
    named, in this order: --deny-from, $AICOWORK_DENY_FROM, `git config aicowork.denyFrom`
    (an explicit --deny-from also overrides an instance's own; the environment and git
    config never do)
    (a local, uncommitted setting). The names stay in the private instance; the
    development repository never holds them. None = the gate cannot run (fail closed)."""
    base = Path(base)
    cand = deny_from
    if not cand and is_instance(base):            # an instance is its own deny source
        return base if (base / "03_personas" / "me.md").is_file() else None
    cand = cand or os.environ.get("AICOWORK_DENY_FROM")
    if not cand and is_git(base):
        rc, out = git(base, "config", "--get", "aicowork.denyFrom")
        cand = out.strip() if rc == 0 and out.strip() else None
    if cand:
        p = Path(cand)
        p = (p if p.is_absolute() else base / p).resolve()
        return p if (p / "03_personas" / "me.md").is_file() else None
    return base if (base / "03_personas" / "me.md").is_file() else None


def version_key(v):
    """Semantic-version order: 0.0.1-rc.1 < 0.0.1-rc.2 < 0.0.1 < 0.0.2."""
    m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", v or "")
    if not m:
        return (0, 0, 0, 0, ())
    pre = m.group(4)
    ids = tuple((0, int(x), "") if x.isdigit() else (1, 0, x) for x in pre.split(".")) if pre else ()
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), 0 if pre else 1, ids)


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$")


def today():
    return dt.date.today()


def owner_file_problem(base):
    """Why 03_personas/me.md cannot give the deny-list. -> str, or None when it can.
    Read with the one strict parser: a list it cannot read is never guessed at."""
    me = Path(base) / "03_personas" / "me.md"
    if not me.is_file():
        return "owner file 03_personas/me.md missing"
    meta, _, problems = parse_frontmatter_strict(read(me))
    if problems:
        return "03_personas/me.md frontmatter cannot be read: " + "; ".join(
            f"{p.cls}" + (f" line {p.line}" if p.line else "") + f": {p.detail}" for p in problems)
    if not meta:      # no frontmatter, or an empty one: there is no list to read, so nothing is known
        return "03_personas/me.md has no frontmatter (the deny-list `check_tokens:` lives there)"
    for key in ("check_tokens", "allow_tokens"):
        if meta.get(key) not in (None, "") and not isinstance(meta.get(key), list):
            return f"03_personas/me.md `{key}` is not a list like [Name, Org]"
    return None


def _token_list(base, key):
    meta, _ = parse_frontmatter(read(Path(base) / "03_personas" / "me.md"))
    return {str(t).strip() for t in meta.get(key) or [] if str(t).strip()}


def check_tokens(base):
    """-> set of owner tokens from 03_personas/me.md, or None when the file is
    missing or cannot be read exactly (fail closed: the leak gates then refuse)."""
    if owner_file_problem(base):
        return None
    return _token_list(base, "check_tokens")


# words too generic to be owner tokens on their own (slug parts, title words)
GENERIC_WORDS = {"strategy", "cooperation", "master", "retail", "taskforce", "cowork", "habits", "project",
                 "projects", "review", "team", "work", "life", "plan", "note", "notes", "meeting", "daily",
                 "weekly", "report", "research", "owner", "instance", "kernel", "system", "data", "docs",
                 "index", "event", "events", "email", "emails", "persona", "personas", "practice", "decision",
                 "backlog", "archive", "inbox", "results", "logs", "home", "family", "friend", "health",
                 "self", "role", "roles", "chủ", "hệ", "manager", "leader", "member", "senior", "junior"}


def allow_tokens(base):
    """Owner-listed false positives of the automatic deny-list (`allow_tokens:` in me.md)."""
    if owner_file_problem(base):
        return set()     # nothing is allowed through on a file that cannot be read
    return _token_list(base, "allow_tokens")


def deny_list(base, projects=True):
    """The names that must never leave this instance, built from the instance itself
    (fail-closed: None when the owner file is missing). projects=False for an
    export of the owner's own notes, where project names are the content and
    the visibility label governs them; a *release* artifact must not name them.
    - `check_tokens` of me.md (the owner's explicit list);
    - the owner's name and org from the me.md identity line;
    - every persona: file stem, `# title`, and each title word of 4+ letters;
    - every project slug under 04_projects/, and each slug part of 4+ letters;
    minus GENERIC_WORDS and the owner's `allow_tokens`. -> (tokens, sources) where
    sources maps each token to where it came from, for the review file."""
    base = Path(base)
    explicit = check_tokens(base)
    if explicit is None:
        return None, {}
    src = {t: "check_tokens" for t in explicit}
    me = read(base / "03_personas" / "me.md")
    for key in ("Name", "Org"):
        m = re.search(r"^" + key + r":\s*\**([^·\n*]+)", me, re.M)
        if m:
            val = m.group(1).strip()
            if val:
                src.setdefault(val, f"me.md {key}")
    for p in sorted((base / "03_personas").glob("*.md")):
        if p.name in ("me.md", "README.md"):
            continue
        src.setdefault(p.stem, f"persona file {p.name}")
        t = read(p)
        m = re.search(r"^#\s+(.+?)\s*$", t, re.M)
        if m:
            title = re.sub(r"\s*[—–/(].*$", "", m.group(1)).strip()
            if title:
                src.setdefault(title, f"persona title {p.name}")
                for w in re.findall(r"[A-Za-zÀ-ỹ]{4,}", title):
                    src.setdefault(w, f"persona title word {p.name}")
    proj = base / "04_projects"
    if projects and proj.is_dir():
        for d in sorted(x for x in proj.iterdir() if x.is_dir()):
            src.setdefault(d.name, f"project slug {d.name}")
            for part in re.split(r"[-_.]", d.name):
                if len(part) >= 4 and not part.isdigit():
                    src.setdefault(part, f"project slug part {d.name}")

    # `allow_tokens` silences only what this function derived (a title word, a slug
    # part); the owner's explicit `check_tokens` and the Name/Org line stay denied
    # whatever it says — a field an agent can write must not widen what may leave
    allow = allow_tokens(base) - explicit - {t for t, where in src.items() if where.startswith("me.md ")}
    tokens = {t for t in src if t.lower() not in GENERIC_WORDS and t not in allow and len(t) >= 3}
    # the kernel's own fictional example instance is public by construction: its
    # names are never a leak (so the suite can use it as a stand-in owner)
    fx = kernel_dir(base) / "conformance" / "fixtures" / "example-instance"
    if fx.is_dir() and Path(base).resolve() != fx.resolve():
        tokens -= _fixture_tokens(fx)
    # likewise the kernel's own module and skill names (an owner may name a
    # project after the module it practises)
    for sub_ in ("modules", "skills"):
        d = kernel_dir(base) / sub_
        if d.is_dir():
            tokens -= {x.name for x in d.iterdir() if x.is_dir()}
    return tokens, {t: src[t] for t in tokens}


def _tags(p):
    """Frontmatter tags of a note (3+ chars) — team, product and site names tend to live there."""
    if not p.is_file():
        return set()
    m = re.search(r"^tags:\s*\[(.*?)\]", read(p), re.M)
    return {t.strip().strip("\"'") for t in m.group(1).split(",") if len(t.strip()) >= 3} if m else set()


def _fixture_tokens(fx):
    try:
        return _raw_names(fx)
    except OSError:
        return set()


def _raw_names(base):
    """Names found in an instance without the generic/allow filtering (helper)."""
    base = Path(base)
    out = set()
    me = base / "03_personas" / "me.md"
    if me.is_file():
        out |= check_tokens(base) or set()
        for key in ("Name", "Org"):
            m = re.search(r"^" + key + r":\s*\**([^·\n*]+)", read(me), re.M)
            if m and m.group(1).strip():
                out.add(m.group(1).strip())
    for p in (base / "03_personas").glob("*.md") if (base / "03_personas").is_dir() else []:
        if p.name in ("me.md", "README.md"):
            continue
        out.add(p.stem)
        m = re.search(r"^#\s+(.+?)\s*$", read(p), re.M)
        if m:
            title = re.sub(r"\s*[—–/(].*$", "", m.group(1)).strip()
            out.add(title)
            out |= set(re.findall(r"[A-Za-zÀ-ỹ]{4,}", title))
    proj = base / "04_projects"
    for d in (x for x in proj.iterdir() if x.is_dir()) if proj.is_dir() else []:
        out.add(d.name)
        out |= {part for part in re.split(r"[-_.]", d.name) if len(part) >= 4 and not part.isdigit()}
    return out


def suggested_tokens(base):
    """Tags on personas and projects that are NOT on the deny-list: team, product
    and site names tend to hide there, next to plain words. Too noisy to deny
    automatically; shown to the owner, who moves the real names into check_tokens."""
    base = Path(base)
    tokens, _ = deny_list(base)
    tokens = tokens or set()
    tags = set()
    for p in (base / "03_personas").glob("*.md") if (base / "03_personas").is_dir() else []:
        if p.name not in ("me.md", "README.md"):
            tags |= _tags(p)
    proj = base / "04_projects"
    for d in (x for x in proj.iterdir() if x.is_dir()) if proj.is_dir() else []:
        tags |= _tags(d / "index.md")
    low = {t.lower() for t in tokens}
    return sorted(t for t in tags if t.lower() not in low and t.lower() not in GENERIC_WORDS)


def folder_name_token(base):
    """The instance folder name is a token only when it is distinctive
    (6+ chars and not a plain lowercase word); otherwise it would flag every file."""
    name = Path(base).name
    return name if len(name) >= 6 and not re.fullmatch(r"[a-z]+", name) else None


def token_patterns(tokens):
    pats = []
    for tok in sorted(t for t in tokens if t):
        if tok.isalnum():
            pats.append((tok, re.compile(r"(?<![A-Za-z0-9])" + re.escape(tok) + r"(?![A-Za-z0-9])", re.I)))
        else:
            pats.append((tok, re.compile(re.escape(tok), re.I)))
    return pats


def atomic_write(p, text):
    from aicowork_core.fsafe import atomic_write as _aw
    _aw(p, text)


def write_report(base, sub, name, title, lines, meta=None):
    """Plain-text report under 06_logs/<sub>/ — the audit trail is files."""
    d = Path(base) / "06_logs" / sub
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    fm = {"type": "log", "visibility": "private", "date": today().isoformat(),
          "created_by": "agent" if os.environ.get("AICOWORK_AGENT") else "human"}
    fm.update(meta or {})
    head = "---\n" + "".join(f"{k}: {v}\n" for k, v in fm.items()) + "---\n"
    p.write_text(head + f"# {title}\n\n" + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return p


# A note's `status` is free text in the kernel; these values mean the item is closed
# for the owner's day-to-day view (owner, 2026-10-10). The viewer's default filter and
# `aicowork tags` read it; the kernel says nothing about it.
CLOSED_STATUSES = frozenset({"done", "archived", "cancelled", "superseded", "deferred"})


def is_open(status):
    return (str(status or "")).strip().lower() not in CLOSED_STATUSES
