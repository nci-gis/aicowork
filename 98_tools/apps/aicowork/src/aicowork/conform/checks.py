# -*- coding: utf-8 -*-
"""Conformance checks L1 (Shape) and L2 (Rules) — the reference runner for the
cases in 99_system/conformance/. Stdlib only.

A Finding is (level, case, path, message); level is "error" or "warn". A folder
conforms at a level when it has no "error" findings at or below that level.
"""
import json
import re
from collections import namedtuple
from pathlib import Path

from aicowork_core import common as C
from aicowork_core.contract import CIRCLES
from aicowork_core.frontmatter import parse_frontmatter_strict
from aicowork_core.contract import is_archived_kernel
from aicowork_core import recur

Finding = namedtuple("Finding", "level case path message")

WORD_BUDGET = 10000      # the six documents a person reads (owner decisions 2026-10-02, 2026-10-03)
# what the budget counts: the kernel's own documents (99_system/README.md lists them)
BUDGET_DOCS = ("PHILOSOPHY.md", "CONVENTIONS.md", "REBUILD.md", "conformance/SUITE.md", "host-contract.md",
               "instruction-file.md")
CORE_SIGNALS = ("inbox", "upcoming", "overdue_contacts", "daily_log_today")   # PHILOSOPHY #9
KERNEL_REQUIRED = ("PHILOSOPHY.md", "CONVENTIONS.md", "REBUILD.md", "VERSION",
                   "host-contract.md", "instruction-file.md", "aicowork.example.yaml",
                   "schemas/frontmatter.schema.json", "schemas/aicowork.schema.json",
                   "schemas/policy.schema.json", "schemas/module.schema.json",
                   "presets/corporate-strict.policy.yaml", "presets/personal-simple.policy.yaml")
TEMPLATES = ("daily-log", "weekly-review", "event", "email", "persona", "practice", "decision", "reminder")
# Host, IDE, model and provider names that must not appear in kernel-ring files.
HOST_NAMES = [r"device_[a-z_]+", r"\$HOME/mnt", r"/sessions/[^/\s]+/mnt", r"\bClaude\b",
              r"CLAUDE\.md", r"AGENTS\.md", r"(?<!AI-)\bCowork\b", r"\bCursor\b", r"\bCodex\b",
              r"\bCopilot\b", r"\bGemini\b", r"\bOpenAI\b", r"\bAnthropic\b", r"\bOllama\b",
              r"\bVS ?Code\b", r"\bObsidian\b", r"\.obsidian/", r"\.vscode/", r"\.claude/"]
SKILL_EGRESS = [r"\bcurl\b", r"\bwget\b", r"Invoke-WebRequest", r"https?://(?!example\.)",
                r"[A-Za-z0-9+/]{200,}={0,2}"]
UNTRUSTED_OPEN = re.compile(r"<<UNTRUSTED id=([A-Za-z0-9]+)>>")
UNTRUSTED_CLOSE = re.compile(r"<<END id=([A-Za-z0-9]+)>>")
MODULE_OPEN = re.compile(r"<!--\s*module:([a-z0-9-]+)\s*-->")
MODULE_CLOSE = re.compile(r"<!--\s*/module\s*-->")
NAME_RULES = {
    "01_events": re.compile(r"^\d{4}-\d{2}-\d{2}_[^\s/]+\.md$"),
    "02_emails": re.compile(r"^\d{4}-\d{2}-\d{2}_[^\s/]+\.md$"),
    "09_decisions": re.compile(r"^(\d{4}-\d{2}-\d{2}_[^\s/]+|backlog)\.md$"),
    "06_logs/daily": re.compile(r"^\d{4}-\d{2}-\d{2}\.md$"),
    "06_logs/weekly": re.compile(r"^\d{4}-W\d{2}\.md$"),
}


def kernel_ring_files(kernel):
    """Files of the kernel ring: 99_system minus fixtures, the
    lock file and human READMEs."""
    kernel = Path(kernel)
    for p in sorted(kernel.rglob("*")):
        if not p.is_file():
            continue
        r = p.relative_to(kernel).as_posix()
        if (r.startswith("conformance/fixtures/")
                or r in ("MANIFEST.sha256",) or p.name.upper().startswith("README")):
            continue
        yield p


def translation_words(kernel):
    """Words of the kernel ring that are translations (templates/<lang>/ for
    lang != en). Reported beside the budget so the owner can decide whether
    translations count (plan A6) — the tool does not decide it."""
    kernel = Path(kernel)
    n = 0
    for p in kernel_ring_files(kernel):
        parts = p.relative_to(kernel).parts
        if len(parts) > 2 and parts[0] == "templates" and parts[1] != "en":
            n += len(re.findall(r"\S+", C.read(p)))
    return n


# ---------------- L1: shape ----------------

# what to do when a folder or section added by a later kernel is missing (UPGRADING.md)
ADDED_IN = {"10_reminders": "0.0.1-rc.4", "Reminders": "0.0.1-rc.4"}


def _added(name):
    v = ADDED_IN.get(name)
    return f" — new in kernel {v}: add it (UPGRADING.md, owner actions)" if v else ""


def l1_skeleton(base):
    out = []
    for d in C.SKELETON:
        if not (base / d).is_dir():
            out.append(Finding("error", "L1-SKELETON", d, "required folder missing" + _added(d)))
    idx = base / "INDEX.md"
    if not idx.is_file():
        out.append(Finding("error", "L1-SKELETON", "INDEX.md", "missing"))
    elif not re.search(r"^Last triage:", C.read(idx), re.M):
        out.append(Finding("error", "L1-SKELETON", "INDEX.md", "no 'Last triage:' footer line"))
    return out


INDEX_SECTIONS = ("Events", "Emails", "Personas", "Projects", "Practices", "Reminders", "Decisions",
                  "Recent results")


def l1_root(base):
    """Root files of REBUILD §1 beyond the footer: INDEX.md's sections, modules.lock."""
    out = []
    idx = base / "INDEX.md"
    if idx.is_file():
        heads = [l[3:].strip() for l in C.read(idx).splitlines() if l.startswith("## ")]
        for s in INDEX_SECTIONS:
            if not any(h == s or h.startswith(s + " ") for h in heads):
                out.append(Finding("error", "L1-ROOT", "INDEX.md", f"no '## {s}' section" + _added(s)))
    enabled, lock = enabled_modules(base), base / "modules.lock"
    if enabled and not lock.is_file():
        out.append(Finding("error", "L1-ROOT", "modules.lock", "missing (modules are enabled in aicowork.yaml)"))
    elif lock.is_file():
        try:
            names = json.loads(C.read(lock))
        except ValueError:
            names = None
        if not isinstance(names, dict):
            out.append(Finding("error", "L1-ROOT", "modules.lock", "not a JSON object {\"<module>\": \"<sha256>\"}"))
        else:
            out += [Finding("error", "L1-ROOT", "modules.lock", f"enabled module '{m}' is not locked")
                    for m in enabled if m not in names]
    return out


def l1_kernel(base):
    out, k = [], C.kernel_dir(base)
    for f in KERNEL_REQUIRED:
        if not (k / f).is_file():
            out.append(Finding("error", "L1-KERNEL", f"99_system/{f}", "required kernel file missing"))
    langs = [d.name for d in (k / "templates").iterdir()] if (k / "templates").is_dir() else []
    if "en" not in langs:
        out.append(Finding("error", "L1-KERNEL", "99_system/templates/en", "English templates missing"))
    for lang in langs:
        for t in TEMPLATES:
            if not (k / "templates" / lang / f"{t}.md").is_file():
                out.append(Finding("error", "L1-KERNEL", f"99_system/templates/{lang}/{t}.md", "template missing"))
    skills = k / "skills"
    for d in sorted(skills.iterdir()) if skills.is_dir() else []:
        s = d / "SKILL.md"
        if not s.is_file():
            out.append(Finding("error", "L1-KERNEL", f"99_system/skills/{d.name}", "no SKILL.md"))
            continue
        meta, body, has = C.frontmatter(s)
        if meta.get("name") != d.name:
            out.append(Finding("error", "L1-KERNEL", C.rel(base, s), "frontmatter name must equal the folder name"))
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d.name) or len(d.name) > 64:
            out.append(Finding("error", "L1-KERNEL", C.rel(base, s), "skill name must be lowercase-hyphen, <= 64 chars"))
        if not meta.get("description") or len(meta["description"]) > 1024:
            out.append(Finding("error", "L1-KERNEL", C.rel(base, s), "description missing or > 1024 chars"))
        raw = re.search(r"(?m)^description:[ \t]*(.*)$", C.read(s))
        if raw and raw.group(1)[:1] not in "\"'" and re.search(r"\s#", raw.group(1)):
            # YAML: " #" starts a comment — a host would see the description cut short
            out.append(Finding("error", "L1-KERNEL", C.rel(base, s), "description contains ' #' unquoted: YAML cuts it there; quote the value"))
        if "## Acceptance" not in body:
            out.append(Finding("error", "L1-KERNEL", C.rel(base, s), "no '## Acceptance' section"))
    return out


def validate_config(cfg):
    """aicowork.yaml against schemas/aicowork.schema.json (hand-written, stdlib)."""
    errs = []
    if not isinstance(cfg, dict):
        return ["top level must be a mapping"]
    known = {"schema", "kernel_version", "language", "modules", "apps", "server",
             "dashboard", "cadence", "security"}
    for k in cfg:
        if k not in known:
            errs.append(f"unknown key '{k}'")
    if cfg.get("schema") != 1:
        errs.append("schema must be 1")
    kv = cfg.get("kernel_version")
    if not (isinstance(kv, str) and C.VERSION_RE.match(kv)):
        errs.append("kernel_version must look like 0.0.1 (or 0.0.1-rc.1)")
    lang = cfg.get("language") or {}
    if not isinstance(lang, dict):
        errs.append("language must be a mapping")
    else:
        chat = lang.get("chat")
        if not (isinstance(chat, list) and chat and all(isinstance(c, str) and re.fullmatch(r"[a-z]{2}", c) for c in chat)):
            errs.append("language.chat must be a non-empty list of 2-letter codes")
        for k in ("content", "ui"):
            if k in lang and not (isinstance(lang[k], str) and re.fullmatch(r"[a-z]{2}", lang[k])):
                errs.append(f"language.{k} must be a 2-letter code")
        mods = lang.get("modules", {})
        if not isinstance(mods, dict) or not all(isinstance(v, str) and re.fullmatch(r"[a-z]{2}", v) for v in mods.values()):
            errs.append("language.modules must map module -> 2-letter code")
    if not isinstance(cfg.get("modules", []), list):
        errs.append("modules must be a list")
    for a in cfg.get("apps") or []:
        if not isinstance(a, dict) or not all(a.get(k) for k in ("id", "name", "kind", "target")):
            errs.append("each app needs id, name, kind, target")
        elif a["kind"] not in ("route", "service", "external"):
            errs.append(f"app {a['id']}: kind must be route|service|external")
        else:
            # the launcher only opens links: a route inside the viewer, a local service,
            # or an http(s) page — never a script scheme (red-team C)
            t = str(a["target"]).strip()
            if a["kind"] == "route" and not t.startswith("/"):
                errs.append(f"app {a['id']}: a route target starts with /")
            elif a["kind"] == "service" and not re.match(r"^https?://(127\.0\.0\.1|localhost|\[::1\])(:\d+)?(/|$)", t):
                errs.append(f"app {a['id']}: a service target is a loopback http(s) URL")
            elif a["kind"] == "external" and not re.match(r"^https?://", t, re.I):
                errs.append(f"app {a['id']}: an external target is an http(s) URL")
    srv = cfg.get("server") or {}
    if srv.get("host", "127.0.0.1") not in ("127.0.0.1", "localhost", "::1"):
        errs.append("server.host must be a loopback address")
    sec = cfg.get("security") or {}
    if sec and sec.get("preset") not in ("corporate-strict", "personal-simple"):
        errs.append("security.preset must be corporate-strict or personal-simple")
    return errs


def l2_index_clean(base):
    """L2-INDEX-CLEAN: INDEX.md is read first in every session, outside any untrusted
    marker — a line that reads like an instruction (the ingest phrase list) is an
    injection that triage copied, not a title."""
    from aicowork.inbox.ingest import flags
    idx = base / "INDEX.md"
    out = []
    if not idx.is_file():
        return out
    for n, line in enumerate(C.read(idx).splitlines(), 1):
        hits = flags(line)
        if hits:
            out.append(Finding("error", "L2-INDEX-CLEAN", "INDEX.md",
                               f"line {n} reads like an instruction ({', '.join(hits[:3])}) — rewrite the title in your own words"))
    return out


def l2_policy_bound(base):
    """L2-POLICY-BOUND: a decided policy matches the owner's trust anchor (and so do
    the other steering files it lists). No anchor: a warning here, a refusal in egress."""
    from aicowork_core.anchor import EGRESS_BOUND, steering_drift
    pol, err = C.load_yaml(base / "policy.yaml")
    if err or not isinstance(pol, dict) or not pol.get("decided"):
        return []
    state, drifted = steering_drift(base)
    if state == "none":
        return [Finding("warn", "L2-POLICY-BOUND", "policy.yaml", "decided but not anchored — egress refuses until "
                        "`aicowork anchor` runs on the owner's computer")]
    if state in ("unchecked", "legacy"):
        return [Finding("warn", "L2-POLICY-BOUND", "policy.yaml", "anchor not checkable from here" if state == "unchecked"
                        else "the anchor predates the policy binding — re-anchor")]
    return [Finding("error" if n in EGRESS_BOUND else "warn", "L2-POLICY-BOUND", n.split("#")[0],
                    f"{n} changed since the owner anchored it") for n in drifted]


def l1_config(base):
    cfg, err = C.load_yaml(base / "aicowork.yaml")
    if err:
        return [Finding("error", "L1-CONFIG", "aicowork.yaml", err)]
    return [Finding("error", "L1-CONFIG", "aicowork.yaml", e) for e in validate_config(cfg)]


def l1_me(base):
    problem = C.owner_file_problem(base)
    if problem:
        return [Finding("error", "L1-ME", "03_personas/me.md", f"{problem} (the leak gate needs its check_tokens and refuses until then)")]
    toks = C.check_tokens(base)
    if not toks:
        return [Finding("warn", "L1-ME", "03_personas/me.md", "no check_tokens list")]
    return []


def check_frontmatter(meta, has_fm):
    """-> list of (level, message) for one file's frontmatter."""
    if not has_fm:
        return [("error", "no frontmatter")]
    out = []
    t = meta.get("type")
    if t not in C.TYPES:
        return [("error", f"type {t!r} is not one of {', '.join(C.TYPES)}")]
    for k in C.REQUIRED_BY_TYPE[t]:
        if not meta.get(k):
            out.append(("error", f"{t} needs '{k}'"))
    if meta.get("circle") and meta["circle"] not in CIRCLES:
        out.append(("error", f"circle {meta['circle']!r} is not one of {', '.join(CIRCLES)}"))
    v = meta.get("visibility")
    if v is None or v == "":
        out.append(("warn", "no visibility (treated as private)"))
    elif not isinstance(v, str) or v not in C.VIS_RANK:
        out.append(("error", f"visibility {v!r} is invalid (treated as private)"))
    for k in ("date", "last_contact", "until", "expires", "review_by", "last_done"):
        val = meta.get(k)
        if val and not C.DATE.match(str(val)[:10]) and "{{" not in str(val):
            out.append(("error", f"{k} {val!r} is not YYYY-MM-DD"))
    if meta.get("cadence") and meta["cadence"] not in ("daily", "weekly", "biweekly", "monthly", "quarterly"):
        out.append(("error", f"cadence {meta['cadence']!r} is invalid"))
    for k, allowed in (("created_by", ("human", "agent")), ("trust", ("untrusted", "reviewed")),
                       ("claim", ("stance", "untested", "sourced", "measured"))):
        if meta.get(k) and meta[k] not in allowed:
            out.append(("error", f"{k} must be one of {', '.join(allowed)}"))
    if meta.get("claim") == "measured" and not meta.get("source"):
        out.append(("error", "claim: measured needs a source"))
    if t == "reminder":
        # dates are reported above; recur adds repeat/days/status/until-before-date
        out += [("error", m) for m in recur.validate(meta) if "is not a date" not in m]
    return out


def l1_frontmatter(base):
    out = []
    for p in C.iter_md(base, C.FM_FOLDERS):
        meta, _, has = C.frontmatter(p)
        unread = [x for x in parse_frontmatter_strict(C.read(p))[2] if x.cls in ("AMB-FM-FENCE", "AMB-FM-SYNTAX")]
        if unread:
            out.append(Finding("error", "L1-FRONTMATTER", C.rel(base, p),
                               f"frontmatter cannot be read ({unread[0].cls}; L2-AMBIGUITY gives the fix) — read as private"))
            continue
        for level, msg in check_frontmatter(meta, has):
            out.append(Finding(level, "L1-FRONTMATTER", C.rel(base, p), msg))
    for p in C.iter_md(base, ("05_results",)):
        meta, _, has = C.frontmatter(p)
        if not has:
            out.append(Finding("warn", "L1-FRONTMATTER", C.rel(base, p), "result without frontmatter"))
    return out


def l1_names(base):
    out = []
    for folder, rx in NAME_RULES.items():
        root = base / folder
        if not root.is_dir():
            continue
        for p in sorted(root.iterdir()):
            if p.is_file() and p.suffix == ".md" and p.name not in C.SKIP_NAMES and not rx.match(p.name):
                out.append(Finding("error", "L1-NAMES", C.rel(base, p), f"name does not match {folder} pattern"))
    projects = base / "04_projects"
    for d in sorted(projects.iterdir()) if projects.is_dir() else []:
        if d.is_dir() and not (d / "index.md").is_file():
            level = "error" if any(d.glob("*.md")) else "warn"
            out.append(Finding(level, "L1-NAMES", C.rel(base, d), "project has no index.md (README.md is never content)"))
    return out


# ---------------- L2: rules ----------------

def enabled_modules(base):
    cfg, _ = C.load_yaml(base / "aicowork.yaml")
    return [m for m in ((cfg or {}).get("modules") or []) if isinstance(m, str)]


def validate_module(manifest, folder_name):
    errs = []
    if not isinstance(manifest, dict):
        return ["module.yaml must be a mapping"]
    for k in ("name", "version", "language", "description", "provides", "permissions"):
        if k not in manifest:
            errs.append(f"missing '{k}'")
    if manifest.get("name") != folder_name:
        errs.append("name must equal the folder name")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
        errs.append("version must look like 0.0.1")
    prov = manifest.get("provides") or {}
    extra = set(prov) - {"templates", "template_fragments", "skills", "fields", "signal", "prompt", "lint_rules"}
    if extra:
        errs.append(f"unknown provides keys: {', '.join(sorted(extra))}")
    if len(prov.get("fields") or []) > 2:
        errs.append("Framework Adoption Contract: at most 2 fields")
    if isinstance(prov.get("signal"), list):
        errs.append("Framework Adoption Contract: at most 1 signal")
    if prov.get("prompt") not in (None, "daily", "weekly"):
        errs.append("Framework Adoption Contract: prompt must be daily, weekly or empty")
    perm = manifest.get("permissions") or {}
    if not isinstance(perm.get("read"), list) or not isinstance(perm.get("write"), list):
        errs.append("permissions needs read and write lists")
    for g in (perm.get("write") or []):
        if C.any_match("99_system/x", [g]) or g.startswith(("99_system", "policy", "aicowork.yaml")):
            errs.append(f"a module may not write {g}")
    return errs


def l2_modules(base):
    out, signals = [], len(CORE_SIGNALS)
    mods_dir = C.kernel_dir(base) / "modules"
    for d in sorted(mods_dir.iterdir()) if mods_dir.is_dir() else []:
        if not d.is_dir():
            continue
        m, err = C.load_yaml(d / "module.yaml")
        errs = [err] if err else validate_module(m, d.name)
        out += [Finding("error", "L2-MODULES", C.rel(base, d / "module.yaml"), e) for e in errs]
    for name in enabled_modules(base):
        m, err = C.load_yaml(mods_dir / name / "module.yaml")
        if err:
            out.append(Finding("error", "L2-MODULES", "aicowork.yaml", f"enabled module '{name}' not found"))
            continue
        if (m.get("provides") or {}).get("signal"):
            signals += 1
    if signals > 5:
        out.append(Finding("error", "L2-SIGNALS", "aicowork.yaml",
                           f"{signals} dashboard signals (core {len(CORE_SIGNALS)} + modules); PHILOSOPHY #9 caps at 5"))
    for lang_dir in sorted((C.kernel_dir(base) / "templates").glob("*")):
        for t in sorted(lang_dir.glob("*.md")):
            text = C.read(t)
            if len(MODULE_OPEN.findall(text)) != len(MODULE_CLOSE.findall(text)):
                out.append(Finding("error", "L2-MODULES", C.rel(base, t), "unbalanced <!-- module --> blocks"))
    return out


def l2_kernel_hygiene(base):
    out, k = [], C.kernel_dir(base)
    host_rx = [re.compile(p, re.I) for p in HOST_NAMES]   # case-insensitive, as SUITE says
    toks = C.check_tokens(base) or set()
    owner = C.token_patterns(toks | {str(base), base.as_posix()})
    words = 0
    for p in kernel_ring_files(k):
        r = C.rel(base, p)
        text = C.read(p)
        if p.relative_to(k).as_posix() in BUDGET_DOCS:   # what a person reads in one sitting
            words += len(re.findall(r"\S+", text))
        for rx in host_rx:
            m = rx.search(text)
            if m:
                out.append(Finding("error", "L2-HOST-NAMES", r, f"names a host/tool: {m.group(0)!r} (move it to hosts/)"))
                break
        for tok, rx in owner:
            if rx.search(text):
                out.append(Finding("error", "L2-OWNER", r, f"owner-identifying token {tok!r} in a kernel file"))
        if r.startswith("99_system/skills/"):
            for pat in SKILL_EGRESS:
                m = re.search(pat, text)
                if m:
                    out.append(Finding("error", "L2-SKILLS", r, f"skill text contains a network/encoded pattern: {m.group(0)[:40]!r}"))
    if words > WORD_BUDGET:
        out.append(Finding("error", "L2-BUDGET", "99_system", f"kernel prose is {words} words; budget {WORD_BUDGET} (decision entry to grow)"))
    return out, words


def l2_markers(base):
    out = []
    for p in C.iter_md(base, C.FM_FOLDERS + ("00_inbox", "05_results", "07_archive")):
        text = C.read(p)
        opens, closes = UNTRUSTED_OPEN.findall(text), UNTRUSTED_CLOSE.findall(text)
        if sorted(opens) != sorted(closes):
            out.append(Finding("error", "L2-MARKERS", C.rel(base, p), "untrusted markers are unbalanced or ids do not match"))
        if text.count("<!-- 🔒 private -->") != text.count("<!-- /🔒 -->"):
            out.append(Finding("error", "L2-MARKERS", C.rel(base, p), "private-block markers are unbalanced"))
    return out


def l2_ambiguity(base):
    """Every note in the content folders against conformance/ambiguity.json. The
    inbox is left out: what lands there is raw, and private by definition; so is the
    kernel text `upgrade` archived (07_archive/kernel-*/), which is not a note."""
    from aicowork_core import ambiguity as A
    classes = A.load_classes(C.kernel_dir(base))
    out = []
    if not classes:
        out.append(Finding("error", "L2-AMBIGUITY", "99_system/conformance/ambiguity.json", "missing or unreadable"))
    for p in C.iter_md(base, tuple(sorted(C.EDITABLE_ROOTS - {"00_inbox"}))):
        if is_archived_kernel(C.rel(base, p)):
            continue                        # retired kernel text (templates with {{…}}), not a note
        for x in A.problems(C.read(p)):
            out.append(Finding("error", "L2-AMBIGUITY", C.rel(base, p), A.advice(x, classes)))
    return out


def l2_policy(base):
    from aicowork.egress.gate import validate_policy
    pol, err = C.load_yaml(base / "policy.yaml")
    if err:
        return [Finding("error", "L2-POLICY", "policy.yaml", err)]
    return [Finding("error", "L2-POLICY", "policy.yaml", e) for e in validate_policy(pol, base)]


def l2_reach_link(base):
    """L2-REACH-LINK: no symbolic link in the content folders points outside the folder."""
    return [Finding("error" if outside else "warn", "L2-REACH-LINK", rel_,
                    f"symbolic link to {target}" + (" — outside the folder" if outside else " (inside the folder)"))
            for rel_, target, outside in C.links(base)]


def l2_hidden(base):
    """L2-HIDDEN (warning): invisible or mixed-script characters in a content note,
    listed in 06_logs/conformance/<date>_hidden-chars.md for a person to look at."""
    from aicowork.instance.ops import hidden_findings
    found = hidden_findings(base)
    by_file = {}
    for r, n, kind, shown in found:
        by_file.setdefault(r, []).append(f"line {n}: {kind} {shown}")
    return [Finding("warn", "L2-HIDDEN", r, "; ".join(v[:3]) + (f" (+{len(v) - 3})" if len(v) > 3 else "")
                    + " — see 06_logs/conformance/<date>_hidden-chars.md (`aicowork doctor` writes it)")
            for r, v in by_file.items()]


def l2_compliance(base):
    from aicowork.egress import gate as egress
    pol, err = C.load_yaml(base / "policy.yaml")
    if err:
        return []
    return [Finding("error", "L2-COMPLIANCE", r, f"contains prohibited marker {m!r} — must not be in this folder")
            for r, m in egress.marker_hits(base, pol)]


def l2_manifest(base):
    from aicowork_core import manifest
    out = []
    for label, root in C.ring_roots(base):
        mf = root / "MANIFEST.sha256"
        if not mf.is_file():
            continue
        for problem in manifest.verify(root):
            out.append(Finding("error", "L2-MANIFEST", C.rel(base, mf), f"{label}: {problem}"))
    return out


def run(base, level=2):
    """-> (findings, info)."""
    base = Path(base).resolve()
    f = []
    f += l1_skeleton(base) + l1_root(base) + l1_kernel(base) + l1_config(base) + l1_me(base)
    f += l1_frontmatter(base) + l1_names(base)
    info = {}
    if level >= 2:
        hyg, words = l2_kernel_hygiene(base)
        info["kernel_words"] = words
        info["translation_words"] = translation_words(C.kernel_dir(base))
        f += (l2_modules(base) + hyg + l2_markers(base) + l2_ambiguity(base) + l2_policy(base) + l2_policy_bound(base)
              + l2_index_clean(base) + l2_reach_link(base) + l2_hidden(base) + l2_compliance(base) + l2_manifest(base))
    return f, info


def summarize(findings):
    errors = [x for x in findings if x.level == "error"]
    warns = [x for x in findings if x.level == "warn"]
    return errors, warns
