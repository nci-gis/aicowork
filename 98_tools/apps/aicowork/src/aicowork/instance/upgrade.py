# -*- coding: utf-8 -*-
"""Install a newer kernel, host pages and tools from a release into an instance.
Stdlib only. Never fetches: the owner downloads the release and points here.
Instance files are never touched, except `kernel_version` in aicowork.yaml."""
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from aicowork_core import common as C
from aicowork_core import manifest
from aicowork_core.scan import collect
# imported now, before any file is replaced: a module first loaded after the copy
# would be the NEW version next to OLD ones already loaded (rc.2 -> rc.3 crashed so)
from aicowork.instance.ops import make_executable

def _source_root(src, td):
    src = Path(src)
    if src.is_file() and src.suffix == ".zip":
        with zipfile.ZipFile(src) as z:
            z.extractall(td)
        return Path(td)
    return src


UPGRADE_ITEMS = ("99_system", "hosts", "98_tools", ".githooks", "aicowork.bat", "aicowork.sh")


def _vtuple(v):
    return C.version_key(v)


def instance_actions(root, to_version):
    """The release's UPGRADING.md section for this version: what the OWNER must
    change in the instance (new policy keys, renamed fields) — printed before
    anything is applied, never applied automatically."""
    f = Path(root) / "UPGRADING.md"
    if not f.is_file():
        return None
    text = C.read(f)
    m = re.search(r"(?ms)^## " + re.escape(to_version) + r"\b.*?(?=^## |\Z)", text)
    return m.group(0).strip() if m else None


RECORDS = "06_logs/upgrade"


def write_record(base, diff, moved, rings):
    """What this upgrade wrote, by hash, so `aicowork audit` can tell an upgrade
    from an edit (rc.3 upgrade test, U1): every added or changed file, the ring
    manifests, aicowork.yaml, and where removed files were archived. A file
    edited afterwards no longer matches its hash and is flagged as before.
    -> the record's path relative to base."""
    base = Path(base)
    files = list(diff["added"]) + list(diff["changed"])
    files += [f"{r}/{manifest.MANIFEST}" for r in rings if (base / r / manifest.MANIFEST).is_file()]
    if (base / "aicowork.yaml").is_file():
        files.append("aicowork.yaml")
    rec = {"from": diff["from"], "to": diff["to"], "source_sha256": diff.get("source_sha256"),
           "date": C.today().isoformat(),
           "files": {p: C.sha256_file(base / p) for p in sorted(set(files)) if (base / p).is_file()},
           "moved": moved}
    d = base / RECORDS
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{rec['date']}_{diff['from'] or 'old'}_to_{diff['to']}.json"
    f.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return f.relative_to(base).as_posix()


def upgrade(base, src, apply=False, expect_sha256=None, allow_downgrade=False):
    """Replace the kernel, hosts, tools, hooks and launchers with a release's.
    Instance files are never touched. -> dict with the diff.
    Refuses, never silently: a zip whose sha256 differs from the one the owner
    expects; a source that fails its own manifest; local drift in a ring (the
    owner's edits would be overwritten); a downgrade without --downgrade."""
    base = Path(base)
    src = Path(src)
    if expect_sha256:
        if not src.is_file():
            raise RuntimeError("--expect-sha256 needs a zip file as the source")
        got = C.sha256_file(src)
        if got.lower() != expect_sha256.lower():
            raise RuntimeError(f"source sha256 {got[:16]}… does not match the expected {expect_sha256[:16]}… — "
                               "wrong file, or a tampered download; nothing was changed")
    elif src.is_file():
        pass   # no expectation given: the diff still shows; the review names the sha
    with tempfile.TemporaryDirectory() as td:
        root = _source_root(src, td)
        rm = root / "RELEASE-MANIFEST.sha256"
        if rm.is_file():
            for line in C.read(rm).splitlines():
                if not line.strip():
                    continue
                h, _, p = line.partition("  ")
                if not (root / p).is_file() or C.sha256_file(root / p) != h:
                    raise RuntimeError(f"source does not match its manifest: {p}")
        rings = [r for r in UPGRADE_ITEMS if (root / r).exists()]
        if not any(r in rings for r in ("99_system", "98_tools")):
            raise RuntimeError("source has neither 99_system/ nor 98_tools/")
        diff = {"added": [], "changed": [], "removed": [], "from": C.read(C.kernel_dir(base) / "VERSION").strip(),
                "to": C.read(root / "VERSION").strip() or C.read(root / "99_system" / "VERSION").strip(),
                "source_sha256": C.sha256_file(src) if src.is_file() else None, "local_drift": [],
                "actions": None}
        diff["actions"] = instance_actions(root, diff["to"])
        if _vtuple(diff["to"]) < _vtuple(diff["from"]):
            diff["downgrade"] = True
            if apply and not allow_downgrade:
                raise RuntimeError(f"{diff['to']} is older than the installed {diff['from']} — pass --downgrade to do this on purpose")
        for _, r in C.ring_roots(base):
            if r.is_dir() and (r / manifest.MANIFEST).is_file():
                diff["local_drift"] += [f"{r.name}: {p}" for p in manifest.verify(r)]
        if apply and diff["local_drift"]:
            raise RuntimeError("local changes in a ring would be overwritten:\n  " + "\n  ".join(diff["local_drift"][:20])
                               + "\n  keep them (move the file to 07_archive/ or a module) or run `aicowork manifest --write` to accept them, then retry")
        for ring in rings:
            new = {f.as_posix() for f in collect(root, [ring])}
            old = {f.as_posix() for f in collect(base, [ring])}
            for p in sorted(new - old):
                diff["added"].append(p)
            for p in sorted(new & old):
                if C.sha256_file(root / p) != C.sha256_file(base / p):
                    diff["changed"].append(p)
            for p in sorted(old - new):
                diff["removed"].append(p)
        if not apply:
            return diff
        if C.is_git(base):
            _, st = C.git(base, "status", "--porcelain")
            if st.strip():
                raise RuntimeError("working tree is not clean — commit first, so the upgrade is one reviewable change")
            snap = base / "_scratch" / f"pre-upgrade-{C.today().isoformat()}.bundle"
            snap.parent.mkdir(parents=True, exist_ok=True)
            rc, msg = C.git(base, "bundle", "create", str(snap), "--all")
            if rc:
                raise RuntimeError(f"could not take the pre-upgrade bundle: {msg}")
            diff["bundle"] = str(snap)
        archive = base / "07_archive" / f"kernel-{diff['from'] or 'old'}"
        moved = {}
        for p in diff["removed"]:
            dst = archive / p
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(base / p), dst)          # never delete
            moved[p] = dst.relative_to(base).as_posix()
        for p in diff["added"] + diff["changed"]:
            (base / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / p, base / p)
        make_executable(base)
        for ring in rings:
            if (base / ring).is_dir() and ((base / ring / manifest.MANIFEST).is_file() or ring in ("99_system", "hosts")):
                manifest.write(base / ring)
        cfg = base / "aicowork.yaml"
        if cfg.is_file() and diff["to"]:
            text, n = re.subn(r"(?m)^kernel_version:\s*\S+", f"kernel_version: {diff['to']}", C.read(cfg))
            if n:
                cfg.write_text(text, encoding="utf-8", newline="\n")   # the one instance key an upgrade may touch
        diff["record"] = write_record(base, diff, moved, rings)
        return diff
