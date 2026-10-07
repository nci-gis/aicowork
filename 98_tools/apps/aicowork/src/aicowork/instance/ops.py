# -*- coding: utf-8 -*-
"""Day-to-day commands: init, new, today, reach, retention, purge, modules,
skills pack, doctor. Stdlib only."""
import datetime as dt
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from aicowork.conform import checks
from aicowork_core import common as C
from aicowork.egress import gate as egress
from aicowork_core import manifest
from aicowork.instance import anchor

from aicowork_core.config import release_root  # noqa: E402
TOOL_KERNEL = (release_root() or Path(".")) / "99_system"   # the kernel this tool ships with

# ---------------- templates ----------------

TEMPLATE_DEST = {
    "daily-log": "06_logs/daily/{date}.md",
    "weekly-review": "06_logs/weekly/{week}.md",
    "event": "01_events/{date}_{slug}.md",
    "email": "02_emails/{date}_{slug}.md",
    "persona": "03_personas/{slug}.md",
    "practice": "08_practices/{slug}.md",
    "decision": "09_decisions/{date}_{slug}.md",
    "reminder": "10_reminders/{slug}.md",
}
WEEKDAYS = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "vi": ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]}
MODULE_BLOCK = re.compile(r"<!--\s*module:([a-z0-9-]+)\s*-->(.*?)<!--\s*/module\s*-->", re.S)


def iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def apply_modules(text, enabled):
    """Keep the content of blocks for enabled modules, drop the rest."""
    def repl(m):
        return m.group(2) if m.group(1) in enabled else ""
    text = MODULE_BLOCK.sub(repl, text)
    return re.sub(r"\n{3,}", "\n\n", text)


def instance_langs(base):
    cfg, _ = C.load_yaml(Path(base) / "aicowork.yaml")
    lang = (cfg or {}).get("language") or {}
    tl = (lang.get("modules") or {}).get("templates") or lang.get("content") or "en"
    return tl, [m for m in ((cfg or {}).get("modules") or []) if isinstance(m, str)]


def render_template(base, name, date=None, lang=None, title=None):
    base = Path(base)
    tl, mods = instance_langs(base)
    lang = lang or tl
    src = C.kernel_dir(base) / "templates" / lang / f"{name}.md"
    if not src.is_file():
        src = C.kernel_dir(base) / "templates" / "en" / f"{name}.md"
    if not src.is_file():
        raise FileNotFoundError(f"no template '{name}'")
    d = date or C.today()
    wd = WEEKDAYS.get(lang, WEEKDAYS["en"])[d.weekday()]
    text = apply_modules(C.read(src), set(mods))
    text = (text.replace("{{YYYY-MM-DD}}", d.isoformat()).replace("{{YYYY-Www}}", iso_week(d))
                .replace("{{weekday}}", wd).replace("{{thứ}}", wd))
    if title:
        text = re.sub(r"^# \{\{[^}]+\}\}", f"# {title}", text, count=1, flags=re.M)
    return text


def new(base, name, slug=None, date=None, lang=None, title=None):
    if name not in TEMPLATE_DEST:
        raise ValueError(f"unknown template '{name}' (one of: {', '.join(TEMPLATE_DEST)})")
    d = date or C.today()
    if "{slug}" in TEMPLATE_DEST[name] and not slug:
        raise ValueError(f"'{name}' needs --slug")
    rel = TEMPLATE_DEST[name].format(date=d.isoformat(), week=iso_week(d), slug=slug or "")
    p = Path(base) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    from aicowork_core.fsafe import exclusive_create
    exclusive_create(p, render_template(base, name, d, lang, title))
    return p

# ---------------- init ----------------

FRESH_INDEX = {
    "en": "# INDEX — Live Catalog\n\nUpdated on every inbox triage. Newest first within each section.\n\n"
          "## Events\n\n## Emails\n\n## Personas\n\n## Projects\n\n## Practices\n\n## Reminders\n\n## Decisions\n\n## Recent results\n\n---\nLast triage: —\n",
    "vi": "# INDEX — Danh mục sống\n\nCập nhật mỗi lần phân loại inbox. Mới nhất xếp trên.\n\n"
          "## Events / Sự kiện\n\n## Emails\n\n## Personas\n\n## Projects / Dự án\n\n## Practices / Thực hành\n\n## Reminders / Nhắc việc\n\n"
          "## Decisions / Quyết định\n\n"
          "## Recent results / Kết quả gần đây\n\n---\nLast triage: —\n",
}
# exactly the lists of 99_system/REBUILD.md §1 (tested: an init and a rebuild make the same folder)
GITIGNORE = ("# OS noise\nThumbs.db\ndesktop.ini\n.DS_Store\n~$*\n*.tmp\n*.bak\n\n# local scratch\n_scratch/\n"
             "_to_delete/\n_tmp/\n\n# tool caches (rebuilt on demand)\n.venv/\n98_tools/apps/viewer/data/\n__pycache__/\n.pytest_cache/\n\n"
             "# a git bundle is a whole copy of the repository; backups go to a policy destination\n*.bundle\n")
GITATTRIBUTES = ("* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n"
                 "*.pdf binary\n*.pptx binary\n*.zip binary\n*.bundle binary\n")
TOOLS_RING = ("98_tools", "aicowork.bat", "aicowork.sh", ".githooks")   # = devkit package.TOOLS_ITEMS; never 90_–95_
ME_TEMPLATE = ("---\ntype: persona\nvisibility: private\ncircle: work\ndate: {date}\nstatus: active\n"
               "check_tokens: []   # your name, org, login, folder name — the leak check refuses to ship them\n---\n"
               "# Me\n\nName: · Org: · Timezone: · Languages:\n\n## Roles\n"
               "<!-- see 99_system/modules/7habits/roles.template.md -->\n")


def folder_rows(kernel_dir):
    """The CONVENTIONS "Folders" table: {folder: (purpose, naming)} — the single
    source the folder READMEs are written from."""
    t = C.read(Path(kernel_dir) / "CONVENTIONS.md")
    rows = {}
    # content folders only; cell padding is free (a Markdown formatter aligns tables)
    for m in re.finditer(r"(?m)^\|\s*`((?:0\d|10)_[a-z_]+)/`\s*\|([^|]+)\|([^|]+)\|", t):
        rows[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return rows


def folder_readme(folder, purpose, naming):
    return (f"# {folder}/\n{purpose[0].upper() + purpose[1:]}.\n\n"
            + (f"Files: {naming}.\n\n" if naming not in ("—", "-", "anything") else
               ("Files: anything.\n\n" if naming == "anything" else ""))
            + "Rules: `99_system/CONVENTIONS.md`.\n")


def write_folder_readmes(base, overwrite=False):
    """README.md in each top-level 00_–10_ folder from CONVENTIONS. Never touches
    an existing README unless overwrite. -> list of written paths."""
    base = Path(base)
    out = []
    for folder, (purpose, naming) in folder_rows(C.kernel_dir(base)).items():
        d = base / folder
        if not d.is_dir():
            continue
        p = d / "README.md"
        if p.exists() and not overwrite:
            continue
        p.write_text(folder_readme(folder, purpose, naming), encoding="utf-8", newline="\n")
        out.append(C.rel(base, p))
    return out


def make_executable(base):
    """Git hooks and the shell launcher must be executable, or git skips the hooks
    with only a hint. A zip unpacked by a program (not `unzip`) loses the bit."""
    import stat
    base = Path(base)
    for f in [base / "aicowork.sh", *sorted((base / ".githooks").glob("*"))]:
        if f.is_file():
            f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def init(target, preset="corporate-strict", lang="en", kernel=None, tools=True):
    """Create a fresh instance. Never overwrites a file. -> list of created paths.
    tools=True also copies the tools ring this program came with (98_tools/,
    launchers, hooks), so the new instance can check itself and later upgrade."""
    target = Path(target).resolve()
    kernel = Path(kernel or TOOL_KERNEL)
    created = []

    def put(rel, text):
        p = target / rel
        if p.exists():
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        created.append(rel)

    if not (target / "99_system").exists():
        # the whole kernel, fixtures included, so the copy matches its release
        # MANIFEST.sha256 byte for byte (and later upgrades diff cleanly)
        shutil.copytree(kernel, target / "99_system", ignore=shutil.ignore_patterns("__pycache__"))
        created.append("99_system/")
    hosts = Path(kernel).parent / "hosts"
    if hosts.is_dir() and not (target / "hosts").exists():
        # host adapters ship beside the kernel; the instance needs them to connect a host
        shutil.copytree(hosts, target / "hosts", ignore=shutil.ignore_patterns("__pycache__"))
        created.append("hosts/")
    src_root = Path(kernel).parent
    if tools and (src_root / "98_tools").is_dir() and src_root.resolve() != target:
        ign = shutil.ignore_patterns("__pycache__", ".venv", "data", ".pytest_cache", "*.pyc")
        for item in TOOLS_RING:
            s_, d_ = src_root / item, target / item
            if not s_.exists() or d_.exists():
                continue
            if s_.is_dir():
                shutil.copytree(s_, d_, ignore=ign)
            else:
                shutil.copy2(s_, d_)
            created.append(item + ("/" if s_.is_dir() else ""))
    make_executable(target)
    rows = folder_rows(target / "99_system")
    for d in C.SKELETON[:-1] + ("07_archive/00_inbox-originals",):
        (target / d).mkdir(parents=True, exist_ok=True)
        if d in rows:
            put(f"{d}/README.md", folder_readme(d, *rows[d]))
        elif not any((target / d).iterdir()):
            put(f"{d}/.gitkeep", "")
    created += write_folder_readmes(target)          # parents like 06_logs/ too; never overwrites
    put("INDEX.md", FRESH_INDEX.get(lang, FRESH_INDEX["en"]))
    cfg = C.read(target / "99_system" / "aicowork.example.yaml")
    cfg = re.sub(r"(?m)^  chat: \[en\]", f"  chat: [{lang}]" if lang == "en" else f"  chat: [{lang}, en]", cfg)
    # templates only in a language the kernel ships (English; others come as modules)
    tl = lang if (target / "99_system" / "templates" / lang).is_dir() else "en"
    cfg = re.sub(r"(?m)^(\s+)(content|ui): en\b", lambda m: f"{m.group(1)}{m.group(2)}: {lang}", cfg)
    cfg = re.sub(r"(?m)^(\s+)templates: en\b", lambda m: f"{m.group(1)}templates: {tl}", cfg)
    cfg = cfg.replace("preset: corporate-strict", f"preset: {preset}")
    kv = C.read(target / "99_system" / "VERSION").strip()
    if kv:
        cfg = re.sub(r"(?m)^kernel_version:\s*\S+", f"kernel_version: {kv}", cfg)
    put("aicowork.yaml", cfg)
    if not (target / "modules.lock").exists():       # REBUILD §1: one hash per enabled module
        modules_lock(target, write=True)
        created.append("modules.lock")
    # copied undecided: only the owner adds `decided:` (PHILOSOPHY #11); egress refuses until then
    put("policy.yaml", C.read(target / "99_system" / "presets" / f"{preset}.policy.yaml"))
    me_t = target / "99_system" / "templates" / "en" / "owner.md"
    put("03_personas/me.md", (C.read(me_t) if me_t.is_file() else ME_TEMPLATE).replace("{{YYYY-MM-DD}}", C.today().isoformat())
        .replace("{date}", C.today().isoformat()))
    put(".gitignore", GITIGNORE)
    put(".gitattributes", GITATTRIBUTES)
    instr = C.read(target / "99_system" / "instruction-file.md")
    put("INSTRUCTIONS.md", instr)
    fresh_repo = not C.is_git(target) and shutil.which("git")
    if fresh_repo:
        C.git(target, "init", "-q")
        created.append(".git/")
    errs = egress.validate_policy(C.load_yaml(target / "policy.yaml")[0], target)
    if errs:
        raise egress.PolicyError("policy.yaml does not validate:\n  " + "\n  ".join(errs))
    if fresh_repo:
        # REBUILD §1 ends with one commit. The host's git identity if it has one; else a
        # repository-local one that names the tool, never the owner (the kernel sets none)
        _, who = C.git(target, "config", "user.email")
        ident = [] if who.strip() else ["-c", "user.name=aicowork init", "-c", "user.email=init@aicowork.invalid"]
        C.git(target, "add", "-A")
        rc, _ = C.git(target, *ident, "commit", "-q", "--no-verify", "-m",
                      f"chore: init instance from kernel {kv or 'unknown'}")
        if rc == 0:
            created.append("(commit) chore: init instance from kernel")
    return created

# ---------------- hidden characters (CONVENTIONS "Reach"; L2-HIDDEN) ----------------

def hidden_findings(base):
    """[(rel, line, kind, shown)] over the content notes — what a person cannot see."""
    from aicowork_core.scan import hidden_chars
    base = Path(base)
    out = []
    for p in C.iter_md(base, C.FM_FOLDERS + ("05_results", "07_archive")):
        for line, kind, shown in hidden_chars(C.read(p)):
            out.append((C.rel(base, p), line, kind, shown))
    return out


def hidden_report(base):
    """Write 06_logs/conformance/<date>_hidden-chars.md when there is anything to
    show. -> (report rel path, hits, files) or None."""
    found = hidden_findings(base)
    if not found:
        return None
    base = Path(base)
    lines = ["Characters a person cannot see, or words that mix scripts, in the content folders. They are not",
             "refused by themselves: look at each one (or ask your assistant to) and decide. Exporting a file",
             "that still has them is allowed and recorded in the receipt.", ""]
    lines += [f"- `{r}` line {n}: {kind} — `{shown}`" for r, n, kind, shown in found]
    p = C.write_report(base, "conformance", f"{C.today().isoformat()}_hidden-chars.md",
                       f"Hidden characters — {len(found)} in {len({r for r, *_ in found})} file(s)", lines)
    return C.rel(base, p), len(found), len({r for r, *_ in found})


# ---------------- reach ----------------

def reach(base):
    """What the connected folder exposes to the model, flagged against ai_surfaces."""
    base = Path(base)
    pol, err = C.load_yaml(base / "policy.yaml")
    surfaces = (pol or {}).get("ai_surfaces") or []
    counts, big, outside, per_vis = {}, [], [], {"private": [], "internal": [], "public": []}
    for p in base.rglob("*"):
        if not p.is_file() or p.is_symlink() or ".git" in p.parts or ".venv" in p.parts or "__pycache__" in p.parts:
            continue
        r = C.rel(base, p)
        top = r.split("/")[0]
        if p.stat().st_size > 5_000_000:
            big.append(r)
        if top.startswith("_") or top in ("data",):
            outside.append(r)
        if p.suffix == ".md" and top in C.EDITABLE_ROOTS:
            meta, _, _ = C.frontmatter(p)
            v = C.visibility(meta)
            per_vis[v].append(r)
            key = (meta.get("type") or "?", meta.get("circle") or "?", v)
            counts[key] = counts.get(key, 0) + 1
    flagged = {}
    for s in surfaces:
        mv = s.get("max_visibility")
        if mv == "none":
            flagged[s.get("id")] = sum(len(v) for v in per_vis.values())
        elif mv in C.VIS_RANK:
            flagged[s.get("id")] = sum(len(per_vis[v]) for v in per_vis if C.VIS_RANK[v] > C.VIS_RANK[mv])
    return {"counts": counts, "per_visibility": {k: len(v) for k, v in per_vis.items()},
            "surfaces": surfaces, "flagged": flagged, "big": big, "outside": outside,
            "policy_error": err, "stamped": egress.marker_hits(base, pol or {}),
            # CONVENTIONS "Reach": a link out of the folder is reported, never followed
            "links": C.links(base)}

# ---------------- retention / purge ----------------

def retention(base, horizon_days=30):
    base, t = Path(base), C.today()
    out = []
    for p in C.iter_md(base, C.FM_FOLDERS + ("05_results", "07_archive")):
        meta, _, _ = C.frontmatter(p)
        for key in ("expires", "review_by"):
            v = meta.get(key)
            if v and C.DATE.match(str(v)):
                d = dt.date.fromisoformat(str(v))
                if (d - t).days <= horizon_days:
                    out.append((C.rel(base, p), key, str(v), (d - t).days))
    return sorted(out, key=lambda x: x[3])


def decide(base, confirm_text, here=False):
    """The owner decides policy.yaml: writes `decided: <today>`, once. Human-only and
    host-side, like `anchor`: it refuses without an interactive terminal and inside an
    agent's sandbox, because `decided:` is the last door before any egress (PHILOSOPHY
    #11; owner, 2026-10-03). The owner types today's date to confirm. -> the date."""
    from aicowork.instance.anchor import foreign_profile
    base = Path(base)
    reason = foreign_profile(base)
    if reason and not here:
        raise PermissionError(f"refusing to decide the policy: {reason}. Run `aicowork decide` from the owner's "
                              "own terminal on the host the folder lives on (or pass --here if this IS that host)")
    if not sys.stdin.isatty():
        raise PermissionError("decide is human-only: it needs an interactive terminal (an agent never writes `decided:`)")
    f = base / "policy.yaml"
    pol, err = C.load_yaml(f)
    if err or not isinstance(pol, dict):
        raise ValueError(f"policy.yaml cannot be read: {err or 'not a mapping'}")
    if pol.get("decided"):
        raise ValueError(f"policy.yaml is already decided ({pol['decided']}); to change a decision, edit the file "
                         "by hand, deliberately, and commit it")
    errs = egress.validate_policy(pol, base)
    if errs:
        raise ValueError("policy.yaml is not valid — fix it first: " + "; ".join(errs))
    today = C.today().isoformat()
    if confirm_text.strip() != today:
        raise PermissionError("the date typed is not today's — nothing was decided")
    text = C.read(f)
    line = f"decided: {today}"
    if re.search(r"(?m)^#\s*decided:.*$", text):
        text = re.sub(r"(?m)^#\s*decided:.*$", line, text, count=1)
    elif re.search(r"(?m)^preset:.*$", text):
        text = re.sub(r"(?m)^(preset:.*)$", r"\1\n" + line, text, count=1)
    else:
        text = line + "\n" + text
    f.write_text(text, encoding="utf-8", newline="\n")
    return today


def purge(base, relpath, reason, confirm_text):
    """Human-only erasure with a hash-only tombstone. Refuses without a TTY."""
    base = Path(base)
    if not sys.stdin.isatty():
        raise PermissionError("purge is human-only: it needs an interactive terminal (agents may never run it)")
    from aicowork_core.fsafe import safe_path
    p = safe_path(base, relpath, roots=C.EDITABLE_ROOTS)
    if confirm_text != relpath:
        raise PermissionError("confirmation text did not match the path — nothing was purged")
    sha = C.sha256_file(p)
    p.unlink()
    rec = {"date": C.today().isoformat(), "path_sha256": C.sha256_text(relpath), "content_sha256": sha,
           "reason": reason}
    d = base / "06_logs" / "purge"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "tombstones.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec

def uncommitted(base):
    """-> paths with uncommitted changes (untracked files listed one by one)."""
    _, st = C.git(base, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    out, parts, i = [], st.split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.append(entry[3:])
        if entry[0] in "RC":            # a rename or copy names its source next: not a second change
            i += 1
    return out


def git_state(base):
    """doctor's git line. It names what is uncommitted (up to five paths). An egress
    receipt is written after the backup or export it records, so it can never be
    inside that copy: alone, it is expected — commit it with `log:` (review of rc.2, F1/F2)."""
    paths = uncommitted(base)
    receipts = [p for p in paths if p.startswith("06_logs/egress/")]
    other = [p for p in paths if p not in receipts]
    if other:
        more = f", … and {len(other) - 5} more" if len(other) > 5 else ""
        tail = f" (plus the egress receipt{'s' if len(receipts) > 1 else ''} in 06_logs/egress/)" if receipts else ""
        return ("warn", "git", f"{len(other)} uncommitted change(s): {', '.join(other[:5])}{more}{tail}")
    if receipts:
        return ("ok", "git", "only the receipt of the last backup or export is uncommitted — commit it: "
                             "git add 06_logs/egress && git commit -m \"log: egress receipt\"")
    return ("ok", "git", "0 uncommitted change(s)")


# ---------------- modules / skills ----------------

def modules_lock(base, write=False):
    base = Path(base)
    _, enabled = instance_langs(base)
    lock = {}
    for name in enabled:
        d = C.kernel_dir(base) / "modules" / name
        files = C.files_in_order(d) if d.is_dir() else []
        lock[name] = C.sha256_text("".join(f"{C.sha256_file(f)} {f.relative_to(d).as_posix()}\n" for f in files))
    p = base / "modules.lock"
    if write:
        p.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return lock, []
    if not p.is_file():
        return lock, ["modules.lock missing (run `aicowork modules --lock`)"]
    old = json.loads(C.read(p))
    return lock, [f"module {m} changed since it was locked" for m in lock if old.get(m) != lock[m]] + \
                 [f"module {m} locked but no longer enabled" for m in old if m not in lock]


def skills_pack(base, out_dir=None):
    """Account-level thin stubs: each only points at the audited file in the folder."""
    base = Path(base)
    out_dir = Path(out_dir or base / "_scratch" / "skills")
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for s in sorted((C.kernel_dir(base) / "skills").glob("*/SKILL.md")):
        meta, _, _ = C.frontmatter(s)
        name = s.parent.name
        stub = (f"---\nname: {name}\ndescription: {meta.get('description', '')}\n---\n\n"
                f"# {name} (stub)\n\nRead and follow `99_system/skills/{name}/SKILL.md` in the connected "
                "AI-Cowork folder, exactly as written there. If that file is missing, stop and say so. "
                "This stub holds no procedure of its own, so it can never drift from the audited file.\n")
        z = out_dir / f"{name}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{name}/SKILL.md", stub)
        made.append(z)
    return made

# ---------------- reminders ----------------

def reminder_states(base, today=None, horizon=None, cfg=None):
    """-> [(rel path, title, state dict)] for every reminder shown in "Keep an eye"
    (CONVENTIONS "Reminders"); invalid ones are left to conformance."""
    from aicowork_core import recur
    from aicowork_core.frontmatter import md_title
    base = Path(base)
    today = today or C.today()
    if horizon is None:
        dash = (cfg or {}).get("dashboard") if isinstance(cfg, dict) else None
        h = (dash or {}).get("horizon_days") if isinstance(dash, dict) else None
        horizon = h if isinstance(h, int) and h >= 0 else 14
    out = []
    for p in C.iter_md(base, ("10_reminders",)):
        meta, body, _ = C.frontmatter(p)
        if meta.get("type") != "reminder":
            continue
        s = recur.state(recur.parse_rule(meta), today, horizon)
        if s:
            out.append((C.rel(base, p), md_title(body, p.stem), s))
    return out


def reminder_line(base, cfg=None):
    """doctor's reminders line: how many are due and overdue today."""
    if not (Path(base) / "10_reminders").is_dir():
        return ("warn", "reminders", "10_reminders/ missing — new in kernel 0.0.1-rc.4 (UPGRADING.md, owner actions)")
    rows = reminder_states(base, cfg=cfg)
    n = {k: sum(1 for _, _, s in rows if s["state"] == k) for k in ("due", "overdue", "expired")}
    return ("warn" if any(n.values()) else "ok", "reminders",
            f"{n['due']} due, {n['overdue']} overdue, {n['expired']} expired")


# ---------------- doctor ----------------

def doctor(base, quick=False):
    """-> list of (level, area, message). level: error | warn | ok."""
    base = Path(base)
    out = []
    from aicowork_core.config import SECURITY_ERRORS, SETTINGS_WARNINGS
    cfg, err = C.load_yaml(base / "aicowork.yaml")
    if err:
        out.append(("error", "config", err))
    else:
        out += [("error", "config", e) for e in checks.validate_config(cfg)]
    out += [("error", "security", e) for e in SECURITY_ERRORS]
    out += [("warn", "config", w) for w in SETTINGS_WARNINGS]
    try:
        pol = egress.load_policy(base)
        if not pol.get("decided"):
            out.append(("warn", "policy", "policy.yaml is undecided — egress refuses until the owner adds `decided: YYYY-MM-DD`"))
        else:
            from aicowork_core.anchor import egress_bound_problem
            problem = egress_bound_problem(base)
            out.append(("error", "policy", f"policy.yaml drifted: {problem}") if problem and "changed since" in problem
                       else ("warn", "policy", f"policy.yaml decided but not bound: {problem}") if problem
                       else ("ok", "policy", "policy.yaml valid, decided and bound to the trust anchor"))
    except egress.PolicyError as e:
        out.append(("error", "policy", str(e).splitlines()[0]))
    for label, root in C.ring_roots(base):
        if (root / manifest.MANIFEST).is_file():
            probs = manifest.verify(root)
            out.append(("error", label, f"manifest drift: {len(probs)} file(s), e.g. {probs[0]}") if probs
                       else ("ok", label, "manifest matches"))
        elif root.exists():
            out.append(("warn", label, "no MANIFEST.sha256 (run `aicowork manifest --write`)"))
    for level, msg in anchor.check_anchor(base):
        out.append((level, "anchor", msg))
    kv = C.read(C.kernel_dir(base) / "VERSION").strip()
    if cfg and cfg.get("kernel_version") and kv and str(cfg["kernel_version"]) != kv:
        out.append(("warn", "version", f"instance built for kernel {cfg['kernel_version']}, folder has {kv}"))
    inbox = [p for p in (base / "00_inbox").iterdir() if p.is_file() and p.name not in C.SKIP_NAMES] \
        if (base / "00_inbox").is_dir() else []
    out.append(("warn" if inbox else "ok", "inbox", f"{len(inbox)} untriaged item(s)"))
    out.append(reminder_line(base, cfg))
    if quick:
        return out
    probs = egress.verify_receipts(base)
    out.append(("error", "receipts", probs[0]) if probs else ("ok", "receipts", "egress receipt chain intact"))
    stamped = egress.marker_hits(base)
    for rel_, mk in stamped[:10]:
        out.append(("error", "compliance", f"{rel_} contains prohibited marker {mk!r} — it must not be in this folder; move it out (never into 07_archive/)"))
    if not stamped and egress.prohibited_markers(C.load_yaml(base / "policy.yaml")[0]):
        out.append(("ok", "compliance", "no prohibited marker in the content folders"))
    r = reach(base)
    pv = r["per_visibility"]
    out.append(("ok", "reach", f"{sum(pv.values())} notes reachable: {pv['private']} private, "
                               f"{pv['internal']} internal, {pv['public']} public"))
    if not r["surfaces"]:
        out.append(("warn", "reach", "policy lists no approved AI surface — record which host may read this folder"))
    for sid, n in r["flagged"].items():
        if n:
            out.append(("warn", "reach", f"{n} note(s) above what surface '{sid}' may read — move them out of the folder"))
    for rel_, target, outside_ in r["links"]:
        out.append(("error" if outside_ else "warn", "reach",
                    f"{rel_} is a symbolic link to {target}" + (" — outside the folder: the host may read through it; remove the link"
                                                               if outside_ else " (inside the folder; tools skip it)")))
    hidden = hidden_report(base)
    if hidden:
        out.append(("warn", "hidden", f"{hidden[1]} hidden or mixed-script character(s) in {hidden[2]} file(s) — see {hidden[0]}; "
                                      f"or ask your assistant: \"check the hidden-chars log {hidden[0]}\""))
    f, info = checks.run(base, level=2)
    errs, warns = checks.summarize(f)
    out.append(("error" if errs else "ok", "conformance", f"L2: {len(errs)} error(s), {len(warns)} warning(s), "
                                                            f"kernel {info.get('kernel_words')} words"))
    rstr = str(base).lower()
    if "onedrive" in rstr or "dropbox" in rstr or "google drive" in rstr:
        out.append(("warn", "path", "folder is inside a sync client; hosts have truncated files there — use a plain local path"))
    if C.is_git(base):
        out.append(git_state(base))
        _, remotes = C.git(base, "remote")
        pol_ = C.load_yaml(base / "policy.yaml")[0] or {}
        private = egress.distribution(pol_) == "private"
        allowed = set() if private else set(pol_.get("remotes") or [])
        for rmt in remotes.split():
            if rmt not in allowed:
                out.append(("error", "git", f"remote '{rmt}' exists but " + (
                    "distribution is private — this instance is never published" if private
                    else "is not listed in policy.yaml remotes")))
        if private:
            out.append(("ok", "distribution", "private — never published (no remotes, no exports, backups only)"))
    last = [e for e in egress._entries(base) if e.get("action") == "backup"]
    if last:
        age = (C.today() - dt.date.fromisoformat(last[-1]["ts"][:10])).days
        out.append(("warn" if age > 7 else "ok", "backup", f"last backup {age} day(s) ago"))
    else:
        out.append(("warn", "backup", "no backup receipt yet"))
    idx = C.read(base / "INDEX.md")
    m = re.search(r"Last triage:\s*(\d{4}-\d{2}-\d{2})", idx)
    if m and inbox and (C.today() - dt.date.fromisoformat(m.group(1))).days > 7:
        out.append(("warn", "index", f"last triage {m.group(1)} and the inbox is not empty"))
    budget = sum(len(C.read(base / f)) for f in ("INSTRUCTIONS.md", "CLAUDE.md", "INDEX.md", "aicowork.yaml")
                 if (base / f).is_file()) + len(C.read(C.kernel_dir(base) / "CONVENTIONS.md"))
    out.append(("ok" if budget < 60_000 else "warn", "cold-start", f"{budget:,} bytes read at session start"))
    return out
