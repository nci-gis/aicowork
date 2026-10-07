# -*- coding: utf-8 -*-
"""Release artifacts and the leak gate (devkit: the kernel developer's tool, never shipped).
Stdlib only; builds on aicowork_core and nothing else.

Three artifacts per release, built from this folder with no git history:
  aicowork-<v>.zip          both below in one: what a new user downloads (`aicowork init`)
  aicowork-kernel-<v>.zip   99_system/ (spec only: no code) + hosts/ (marked H) + LICENSE/NOTICE/docs
  aicowork-tools-<v>.zip    98_tools/ (every tool, minus .venv/data/caches) + launchers + hooks
"Only the kernel is public, never the data" is enforced three ways: the file
list is an allow-list of kernel/tools paths, both scanners read the *built*
zip (file names and contents, text and binary strings), and the build refuses
when the owner file with its check_tokens is missing (fail closed).
"""
import hashlib
import json
import re
import subprocess
import shutil
import tempfile
import datetime as dt
import zipfile
from pathlib import Path

from aicowork_core import common as C
from aicowork_core import manifest
from aicowork_core.scan import (EXCLUDE_SUFFIX, FIXTURES, collect, scan_generic,  # noqa: F401
                                scan_tokens, _skip)

KERNEL_ITEMS = ["99_system", "hosts"]   # hosts/ ships beside the kernel, marked H (inventory Q2)
TOOLS_ITEMS = ["98_tools", "aicowork.bat", "aicowork.sh", ".githooks"]
RELEASE_DOCS = ["NOTICE.md", "THIRD_PARTY_LICENSES.md", "SECURITY.md", "CHANGELOG.md",
                "CONTRIBUTING.md", "PRIVACY.md", "UPGRADING.md", "docs", ".gitignore", ".gitattributes"]
INSTANCE_NAMES = {"aicowork.yaml", "policy.yaml", "INDEX.md", "modules.lock", "me.md"}

def _contributor_inputs(base, deny_src):
    """Gate inputs for a development repository that names no private instance: a
    contributor's clone holds no owner names, so scanner A has no tokens and scanner B
    (e-mail addresses, secrets, personal paths) runs in full. `leakscan` only — `package`
    keeps refusing without a private instance — and the maintainer's own push runs the
    gate again against theirs. -> (tokens, paths) or (None, None) for an instance."""
    if deny_src is not None or C.is_instance(base):
        return None, None
    return [], set()
CODE_SUFFIX = {".py", ".js", ".bat", ".sh", ".ps1", ".exe", ".dll"}

def _gate_inputs(base, deny_src):
    """(tokens, path strings) for scanner A, or (None, None) without an owner file."""
    tokens, _ = C.deny_list(deny_src) if deny_src else (None, {})
    if tokens is None:
        return None, None
    paths = set()
    for b in {Path(base), Path(deny_src)}:
        paths |= {str(b), b.as_posix()}
        # the folder name is a token for an instance (a private path), never for the
        # development repository: its folder is the project's public name (`ai-cowork`),
        # which every file may say
        if C.folder_name_token(b) and (b != Path(base) or C.is_instance(b)):
            paths.add(C.folder_name_token(b))
    return tokens, paths


def leak_gate(zip_path, base, deny_src=None):
    """Extract the built artifact and run both scanners. -> list of hits.
    Scanner A uses the automatic deny-list (personas, projects, org, owner) plus
    the owner's check_tokens, never only the four words a human remembered to list.
    deny_src: the instance that holds those names (default: base itself)."""
    base = Path(base)
    tokens, paths = _gate_inputs(base, deny_src or C.deny_source(base))
    if tokens is None:
        return [("03_personas/me.md", "no readable owner file to build the deny-list from — the leak gate fails closed")]
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(td)
        hits = [("A " + r, m) for r, m in scan_tokens(td, tokens, paths)]
        hits += [("B " + r, m) for r, m in scan_generic(td)]
        for f in Path(td).rglob("*"):
            r = f.relative_to(td).as_posix()
            # the fictional example instance is instance-shaped on purpose
            if f.is_file() and f.name in INSTANCE_NAMES and not r.startswith(FIXTURES):
                hits.append(("C " + r, "instance file inside a release artifact"))
    return hits


def scan_tree(base, deny_from=None):
    """Scanners A and B over every tracked file of `base` (the development
    repository's pre-commit and pre-publish check: the repository itself, history
    aside, must already be publishable). -> (hits, deny_src) or (None, None)."""
    base = Path(base)
    deny_src = C.deny_source(base, deny_from)
    tokens, paths = _gate_inputs(base, deny_src)
    if tokens is None:
        tokens, paths = _contributor_inputs(base, deny_src)
    if tokens is None:
        return None, None
    with tempfile.TemporaryDirectory() as snap, tempfile.TemporaryDirectory() as td:
        if C.is_git(base):
            # the index, not the working tree: what is scanned is exactly what the
            # next commit holds (a staged secret hidden by a clean working copy is caught)
            rc, _ = C.git(base, "checkout-index", "--all", "--force", f"--prefix={Path(snap).as_posix()}/")
            if rc:
                raise RuntimeError("git checkout-index failed — the leak scan cannot read what would be committed")
            src = Path(snap)
            files = [f.relative_to(src) for f in C.files_in_order(src)]
        else:
            src = base
            files = collect(base, [p.name for p in base.iterdir()])
        for f in files:
            if _scannable(f) and (src / f).is_file():
                (Path(td) / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src / f, Path(td) / f)
        hits = [("A " + r, m) for r, m in scan_tokens(td, tokens, paths)]
        hits += [("B " + r, m) for r, m in scan_generic(td)]
    return hits, deny_src


# every tracked file, .agents/ included: the repository itself must be publishable
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}


def _scannable(rel):
    rel = Path(rel)
    return not (SKIP_PARTS & set(rel.parts)) and rel.suffix.lower() not in EXCLUDE_SUFFIX


def _git_bytes(base, *args, stdin=None):
    r = subprocess.run(["git", "-C", str(base), *args], input=stdin, capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {args[0]}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def pushed_revs(base, updates, remote=None):
    """git rev-list arguments for what a push sends: each local tip, minus what
    the receiving remote already has — its sha for the ref, and its own
    remote-tracking branches when `remote` is a configured remote. Another
    remote's branches are NOT excluded: history it holds may be new to this one
    (review of rc.3, R2). A push to a bare URL excludes nothing but the remote sha.
    updates: [(local sha, remote sha)] as git hands them to pre-push."""
    pos, neg = [], []
    for local, remote_sha in updates:
        if set(local) == {"0"}:
            continue                                         # a deletion sends nothing
        pos.append(local)
        if set(remote_sha) != {"0"} and C.git(base, "cat-file", "-e", remote_sha)[0] == 0:
            neg.append("^" + remote_sha)
    if not pos:
        return []
    rc, names = C.git(base, "remote")
    if remote and rc == 0 and remote in names.split():
        neg += ["--not", f"--remotes={remote}"]
    return pos + neg


LEAK_REVIEWED = "90_devkit/leak-reviewed.json"
_TRAILER = re.compile(r"^co-authored-by:.*<([^<>\s]+)>\s*$", re.I)


def reviewed_trailer_addresses(base):
    """SHA-256 of the addresses the owner reviewed as false alarms in commit
    trailers (90_devkit/leak-reviewed.json). Unreadable file -> nothing reviewed."""
    try:
        data = json.loads((Path(base) / LEAK_REVIEWED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {e["sha256"] for e in data.get("commit_trailer_addresses", [])
            if isinstance(e, dict) and isinstance(e.get("sha256"), str) and e.get("decided")}


def drop_reviewed_trailers(msg, reviewed):
    """A commit message without the trailer lines whose address the owner reviewed.
    Only `Co-Authored-By:` lines, only listed addresses: everything else is scanned."""
    keep = []
    for line in msg.splitlines():
        m = _TRAILER.match(line.strip())
        if m and hashlib.sha256(m.group(1).lower().encode("utf-8")).hexdigest() in reviewed:
            continue
        keep.append(line)
    return "\n".join(keep) + ("\n" if msg.endswith("\n") else "")


def scan_pushed(base, updates, deny_from=None, remote=None):
    """Scanners A and B over every blob and commit message a push would send —
    not only the tip: a secret added in one commit and removed in the next is
    still in the history that leaves. -> (hits, deny_src) or (None, None)."""
    base = Path(base)
    deny_src = C.deny_source(base, deny_from)
    tokens, paths = _gate_inputs(base, deny_src)
    if tokens is None:
        tokens, paths = _contributor_inputs(base, deny_src)
    if tokens is None:
        return None, None
    revs = pushed_revs(base, updates, remote)
    if not revs:
        return [], deny_src
    objs = _git_bytes(base, "rev-list", "--objects", *revs).decode("utf-8", "replace").splitlines()
    named = [(l.split(" ", 1)[0], l.split(" ", 1)[1]) for l in objs if " " in l]
    kinds = _git_bytes(base, "cat-file", "--batch-check", stdin="\n".join(s for s, _ in named).encode() + b"\n")
    blobs = [(s, p) for (s, p), k in zip(named, kinds.decode().splitlines()) if k.split()[1:2] == ["blob"] and _scannable(p)]
    with tempfile.TemporaryDirectory() as td:
        if blobs:
            data = _git_bytes(base, "cat-file", "--batch", stdin="\n".join(s for s, _ in blobs).encode() + b"\n")
            pos = 0
            for sha, path in blobs:
                head_end = data.index(b"\n", pos)
                size = int(data[pos:head_end].split()[2])
                body = data[head_end + 1:head_end + 1 + size]
                pos = head_end + 1 + size + 1
                f = Path(td) / sha[:12] / path
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(body)
        log = _git_bytes(base, "log", "--format=%H%n%B%x00", *revs).decode("utf-8", "replace")
        reviewed = reviewed_trailer_addresses(base)
        for entry in log.split("\0"):
            sha, _, msg = entry.strip("\n").partition("\n")
            if sha:
                (Path(td) / f"commit-{sha[:12]}.txt").write_text(drop_reviewed_trailers(msg, reviewed), encoding="utf-8", newline="\n")
        hits = [("A " + r, m) for r, m in scan_tokens(td, tokens, paths)]
        hits += [("B " + r, m) for r, m in scan_generic(td)]
    return hits, deny_src


CRLF_SUFFIX = {".bat", ".cmd"}      # .gitattributes: eol=crlf (cmd.exe needs it)


def _artifact_bytes(base, rel):
    """The bytes a release carries for one file: as committed, with the line
    endings .gitattributes gives it — CRLF for Windows scripts, whatever the
    working copy of the machine that builds the release holds (review of rc.3, D4)."""
    data = (Path(base) / rel).read_bytes()
    if Path(rel).suffix.lower() in CRLF_SUFFIX:
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data


def _version(base):
    return C.read(C.kernel_dir(base) / "VERSION").strip() or "0.0.0"


def _pep440(v):
    """0.0.1-rc.3 -> 0.0.1rc3: VERSION as Python packaging writes it."""
    return re.sub(r"-(a|b|rc)\.?(\d+)$", r"\1\2", v)


def version_problems(base):
    """The tools' package versions and uv.lock must say what 99_system/VERSION says:
    every launcher runs `uv run --locked`, so a stale lock breaks every user's tools
    (rc.3 readiness B3). Read as text — no uv call, no network. -> [reason]."""
    base = Path(base)
    tools = base / "98_tools"
    if not (tools / "pyproject.toml").is_file():
        return []
    v = _version(base)
    want, out, names = _pep440(v), [], []
    for f in sorted(tools.glob("**/pyproject.toml")):
        if ".venv" in f.parts:
            continue
        text = C.read(f)
        name = re.search(r'(?m)^name\s*=\s*"([^"]+)"', text)
        ver = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
        if name:
            names.append(name.group(1))
        if not ver or ver.group(1) != want:
            out.append(f"{f.relative_to(base).as_posix()}: version {ver.group(1) if ver else '(none)'} "
                       f"is not VERSION {v} ({want}) — set it, then run `uv lock` in 98_tools")
    lock = tools / "uv.lock"
    if lock.is_file():
        locked = dict(re.findall(r'(?m)^\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"', C.read(lock)))
        for n in names:
            if locked.get(n) != want:
                out.append(f"98_tools/uv.lock: {n} {locked.get(n, '(missing)')} is not {want} — run `uv lock` in "
                           "98_tools (every launcher runs `uv run --locked`)")
    return out


def preflight(base, deny_src=None):
    """Why a build must not happen now. -> list of reasons (empty = go).
    Nothing here can be skipped from the CLI: a release is built from a
    committed, manifest-clean tree or not at all."""
    base = Path(base)
    reasons = []
    v = _version(base)
    if not C.VERSION_RE.match(v):
        reasons.append(f"99_system/VERSION {v!r} is not a version (0.0.1, 0.0.1-rc.1)")
    for label, root in C.ring_roots(base):
        if root.is_dir() and (root / manifest.MANIFEST).is_file():
            probs = manifest.verify(root)
            if probs:
                reasons.append(f"{label} manifest drift ({len(probs)}): " + "; ".join(probs[:5])
                               + " — review the change, then `aicowork manifest --write` and commit")
        elif root.is_dir():
            reasons.append(f"{label}: no {manifest.MANIFEST} — run `aicowork manifest --write`")
    if C.is_git(base):
        _, st = C.git(base, "status", "--porcelain")
        own_log = _release_log(base).parent.relative_to(base).as_posix() + "/"
        dirty = [l[3:] for l in st.splitlines() if l.strip() and not l[3:].startswith(("_scratch/", "_to_delete/", "_tmp/", own_log))]   # the tool's own log
        if dirty:
            reasons.append(f"working tree has {len(dirty)} uncommitted change(s), e.g. {dirty[0]} — commit first")
    reasons += version_problems(base)
    if not C.is_instance(base):
        from devkit import fixtures
        if Path(base).resolve() == fixtures.KERNEL.parent.resolve():
            stale = fixtures.differences()
            if stale:
                reasons.append(f"{len(stale)} conformance fixture(s) differ from what the generator writes, e.g. "
                               f"{stale[0]} — run `devkit fixtures` (the example follows VERSION) and commit")
        from devkit import claims
        for rel, sentence in claims.scan(base):
            reasons.append(f"{claims.CLASS} {rel}: {sentence[:120]!r} — an absolute claim that nothing leaves "
                           "must name the model-call exception in the same passage (reword it, or the owner "
                           f"records a false alarm in {claims.REVIEWED})")
    if deny_src is None:
        reasons.append("no deny-list: 03_personas/me.md missing" if C.is_instance(base) else
                       "no deny-list: this is the development repository, which holds no owner names — "
                       "name the private instance that does: --deny-from <instance folder> "
                       "(or once: git config aicowork.denyFrom <instance folder>)")
    return reasons


def _release_log(base):
    """Instance: 06_logs/release/. Development repository: .agents/releases/ (committed, never shipped)."""
    base = Path(base)
    if C.is_instance(base):
        return base / "06_logs" / "release" / "releases.jsonl"
    return base / ".agents" / "releases" / "releases.jsonl"


def last_release(base):
    f = _release_log(base)
    if not f.is_file():
        return None
    lines = [l for l in C.read(f).splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def write_review(base, out_dir, v, results, reasons, tokens_src, deny_src=None):
    """REVIEW-<v>-<date>.md beside the artifacts: everything a human needs to
    decide whether to ship. The tool never ships; a person does."""
    base = Path(base)
    rc, head = C.git(base, "rev-parse", "--short", "HEAD")
    prev = last_release(base)
    lines = [f"# Release review — {v} — {C.today().isoformat()}", "",
             "**Ship decision: a person.** This tool builds and checks; it never publishes.",
             f"- commit: `{head.strip() if rc == 0 else 'no git'}`",
             f"- deny-list: {len(tokens_src)} token(s) — check_tokens + personas + projects + org/owner (`allow_tokens:` in me.md silences a false positive)"
             + ("" if deny_src is None or Path(deny_src).resolve() == base.resolve() else " — read from the private instance named by --deny-from (path not recorded here)"),
             f"- previous recorded release: {prev['version'] + ' ' + prev['date'] if prev else 'none'}", ""]
    sugg = C.suggested_tokens(deny_src) if deny_src else []
    if sugg:
        lines += ["## Names the gate does NOT know (owner: move real ones into `check_tokens`)",
                  "Tags on your personas and projects that are not on the deny-list. Team, product, customer and site "
                  "names that live only in prose are invisible to the scanners until you list them:",
                  "`" + "`, `".join(sugg[:60]) + "`", ""]
    if reasons:
        lines += ["## REFUSED — preflight", *[f"- {r}" for r in reasons], ""]
    for zp, hits, files in results:
        lines += [f"## {zp.name}", f"- files: {len(files)} · sha256 `{C.sha256_file(zp)}`"]
        if hits:
            lines += ["- **LEAK GATE: FAILED** — artifact moved to `refused/`; nothing to publish",
                      *[f"  - `{r}` — {m}" for r, m in hits]]
        else:
            lines.append("- leak gate: clean (scanner A tokens, scanner B generic, C instance files)")
        if prev and zp.name in prev.get("artifacts", {}):
            old = set(prev["artifacts"][zp.name].get("files", []))
            new = set(f.as_posix() for f in files)
            lines.append(f"- vs {prev['version']}: +{len(new - old)} added, -{len(old - new)} removed"
                         + (": " + ", ".join(sorted(new - old)[:20]) if new - old else ""))
        lines.append("")
    lines += ["## Before publishing (owner)", "1. Read this file and the CHANGELOG; record the decision in your instance's `09_decisions/`.",
              "2. `git tag -s v" + v + "` on the commit above (signed).",
              ("3. A release candidate goes to the testers you choose, privately: `aicowork-" + v + ".zip` and its `.sha256` file."
               if "-" in v else
               "3. Push the development repository and the tag; create the release; attach the zips and their `.sha256` files."),
              "4. New users: unzip `aicowork-" + v + ".zip`, run `aicowork init <folder>`. Existing instances: `aicowork upgrade <zip> --expect-sha256 <published>`."]
    f = Path(out_dir) / f"REVIEW-{v}-{C.today().isoformat()}.md"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return f


def build(base, out_dir=None, which=("full", "kernel", "tools"), check=True, deny_from=None):
    """-> list of (artifact path, hits). With check=True (always, from the CLI):
    preflight must pass, every artifact goes through the leak gate, a failed
    artifact is moved to refused/, a review file is written, a clean build is
    recorded in 06_logs/release/."""
    base = Path(base)
    v = _version(base)
    out_dir = Path(out_dir or base / "_scratch" / "release")
    out_dir.mkdir(parents=True, exist_ok=True)
    deny_src = C.deny_source(base, deny_from) if check else None
    reasons = preflight(base, deny_src) if check else []
    if reasons:
        write_review(base, out_dir, v, [], reasons, {}, deny_src)
        raise RuntimeError("preflight failed:\n  " + "\n  ".join(reasons))
    results, full = [], []
    for kind in which:
        # full = kernel + tools in one zip: what a new user downloads and unzips once
        # (two zips unzipped into one folder collide on README, LICENSE, VERSION)
        ring_items = {"kernel": KERNEL_ITEMS, "tools": TOOLS_ITEMS, "full": KERNEL_ITEMS + TOOLS_ITEMS}[kind]
        items = ring_items + [d for d in RELEASE_DOCS if (base / d).exists()]
        files = collect(base, items)
        dev_only = sorted({f.parts[0] for f in files if re.match(r"^9[0-5]_", f.parts[0])})
        if dev_only:   # 90_–95_ are development folders: never in a release, whatever the item list says
            raise RuntimeError(f"release would contain development folder(s) {dev_only} — 90_–95_ never ship")
        if kind == "kernel":
            code = [f for f in files if f.suffix.lower() in CODE_SUFFIX]
            if code:
                raise RuntimeError(f"kernel artifact would contain code: {code[0]} — the kernel is a specification")
        # the public README is published at the artifact root. Development repository:
        # its root README.md. Instance: docs/README.md (the instance's own root README never ships)
        if not C.is_instance(base) and (base / "README.md").is_file():
            front = Path("README.md")
        else:
            front = Path("docs/README.md") if Path("docs/README.md") in files else None
        # each ring folder carries its own licence and the artifact gets it at its root;
        # the full artifact takes the repository's root LICENSE (the same MIT text), so a
        # public tree unzipped from it is licensed where GitHub and people look first
        lic = {"kernel": Path("99_system/LICENSE"), "tools": Path("98_tools/LICENSE"), "full": Path("LICENSE")}[kind]
        for need in [lic] + [Path(r) / "LICENSE" for r in ("99_system", "hosts", "98_tools")]:
            if not (base / need).is_file():
                raise RuntimeError(f"{need} missing — a release artifact must carry its licence")
        mf_text = "\n".join(f"{C.sha256_bytes(_artifact_bytes(base, f))}  {f.as_posix()}" for f in files)
        if front:
            mf_text += f"\n{C.sha256_file(base / front)}  README.md"
        if lic:
            mf_text += f"\n{C.sha256_file(base / lic)}  LICENSE"
        mf_text += "\n"
        zp = out_dir / (f"aicowork-{v}.zip" if kind == "full" else f"aicowork-{kind}-{v}.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                # fixed modes: 0644, 0755 only for scripts (a release must not mark docs executable)
                zi = zipfile.ZipInfo.from_file(base / f, f.as_posix())
                exe = f.suffix in (".sh",) or f.parts[0] == ".githooks"
                zi.external_attr = ((0o100755 if exe else 0o100644) & 0xFFFF) << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, _artifact_bytes(base, f))
            extra = [("RELEASE-MANIFEST.sha256", mf_text), ("VERSION", v + "\n")]
            if front:
                extra.append(("README.md", C.read(base / front)))
            if lic:
                extra.append(("LICENSE", C.read(base / lic)))
            for name, body in extra:
                zi = zipfile.ZipInfo(name, date_time=dt.datetime.now().timetuple()[:6])
                zi.external_attr = (0o100644 & 0xFFFF) << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, body)
        (out_dir / f"{zp.name}.sha256").write_text(f"{C.sha256_file(zp)}  {zp.name}\n", encoding="utf-8", newline="\n")
        hits = leak_gate(zp, base, deny_src) if check else []
        if hits:
            # nothing publishable may remain where a hand might pick it up
            q = out_dir / "refused"
            q.mkdir(exist_ok=True)
            for suffix in ("", ".sha256"):
                src = out_dir / (zp.name + suffix)
                if src.exists():
                    shutil.move(str(src), q / src.name)
            zp = q / zp.name
        results.append((zp, hits))
        full.append((zp, hits, files))
    if check:
        _, src_map = C.deny_list(deny_src)
        write_review(base, out_dir, v, full, [], src_map, deny_src)
        if not any(h for _, h, _ in full):
            rc, head = C.git(base, "rev-parse", "HEAD")
            rec = {"version": v, "date": C.today().isoformat(), "commit": head.strip() if rc == 0 else None,
                   "artifacts": {zp.name: {"sha256": C.sha256_file(zp), "files": [f.as_posix() for f in files]}
                                 for zp, _, files in full}}
            log = _release_log(base)
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return results
