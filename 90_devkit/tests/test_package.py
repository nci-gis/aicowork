# -*- coding: utf-8 -*-
"""Devkit tests: release artifacts, the leak gate, the development repository's
tree scan, and installing a built release (upgrade). Each test works on a temp
copy of the fictional example instance checked together with this kernel."""
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from aicowork.conform import audit
from aicowork.conform import checks
from aicowork_core import common as C
from aicowork.egress import gate as egress
from aicowork.inbox import ingest
from aicowork_core import manifest
from aicowork.instance import ops
from devkit import package
from aicowork.instance import upgrade
from aicowork.inbox import triage

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())
KERNEL = REPO / "99_system"
EXAMPLE = KERNEL / "conformance" / "fixtures" / "example-instance"
FIXTURES = KERNEL / "conformance" / "fixtures"
VERSION = (KERNEL / "VERSION").read_text(encoding="utf-8").strip()


def _git(base, *a):
    subprocess.run(["git", "-C", str(base), *a], check=True, capture_output=True)


@pytest.fixture
def inst(tmp_path, monkeypatch):
    base = tmp_path / f"i{os.getpid()}z"   # runtime name: never a literal in this file
    shutil.copytree(EXAMPLE, base)
    shutil.copytree(KERNEL, base / "99_system", ignore=shutil.ignore_patterns("fixtures", "MANIFEST.sha256"))
    monkeypatch.setenv("AICOWORK_ANCHOR_DIR", str(tmp_path / "anchors"))
    _git(base, "init", "-q")
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "add", "-A")
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "start")
    return base


def head(base):
    return subprocess.run(["git", "-C", str(base), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def ids(findings, level="error"):
    return {f.case for f in findings if f.level == level}


# ---------------- package / leak gate / upgrade ----------------

def _release_base(inst):
    """A folder that looks like the repo: kernel + tools + owner file, manifests
    written and everything committed — the state `package` demands (preflight)."""
    shutil.copytree(REPO / "98_tools", inst / "98_tools",
                    ignore=shutil.ignore_patterns(".venv", "data", "__pycache__", ".pytest_cache"))
    if not (inst / "hosts").exists():
        shutil.copytree(REPO / "hosts", inst / "hosts", ignore=shutil.ignore_patterns("MANIFEST.sha256"))
    for doc in ("UPGRADING.md", "LICENSE"):
        if (REPO / doc).is_file() and not (inst / doc).exists():
            shutil.copy(REPO / doc, inst / doc)
    if not (inst / "99_system" / "conformance" / "fixtures").exists():   # a release ships its fixtures
        shutil.copytree(FIXTURES, inst / "99_system" / "conformance" / "fixtures")
    _seal(inst)
    return inst


def _seal(base):
    """Rewrite the ring manifests and commit: what a real release commit looks like."""
    for _, r in C.ring_roots(base):
        if r.is_dir():
            manifest.write(r)
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "add", "-A")
    subprocess.run(["git", "-C", str(base), "-c", "user.email=t@example.com", "-c", "user.name=t",
                    "commit", "-qm", "seal"], capture_output=True)


def test_kernel_artifact_has_no_code_and_passes_gate(inst, tmp_path):
    results = package.build(_release_base(inst), tmp_path / "out")
    for zp, hits in results:
        assert hits == [], (zp.name, hits[:5])
    with zipfile.ZipFile(tmp_path / "out" / f"aicowork-kernel-{VERSION}.zip") as z:
        names = z.namelist()
    assert "99_system/PHILOSOPHY.md" in names and not [n for n in names if n.endswith(".py")]
    assert [n for n in names if n.startswith("hosts/")]          # ships beside the kernel, marked H
    with zipfile.ZipFile(tmp_path / "out" / f"aicowork-kernel-{VERSION}.zip") as z:
        modes = {(i.external_attr >> 16) & 0o777 for i in z.infolist() if not i.filename.endswith("/")}
    assert modes == {0o644}                                     # drill 2026-10-01 Q29
    assert not [n for n in names if n.split("/")[-1] in package.INSTANCE_NAMES and not n.startswith(package.FIXTURES)]


def test_leak_gate_catches_token_email_secret(inst, tmp_path):
    base = _release_base(inst)
    # built at runtime so this test file itself never carries the literals
    # (the tools artifact ships the tests, and the gate would rightly flag them)
    token, mail, key = "Zorb" + "laxCo", "minh" + "@" + "realcorp.com", "AKIA" + "ABCDEFGHIJKLMNOP"
    me = base / "03_personas" / "me.md"
    me.write_text(C.read(me).replace("check_tokens: [", f"check_tokens: [{token}, "), encoding="utf-8")
    (base / "99_system" / "leak.md").write_text(f"{token} wrote to {mail} key {key}\n", encoding="utf-8")
    _seal(base)                                     # even a committed, manifested leak is caught
    (zp, hits), = package.build(base, tmp_path / "o", which=("kernel",))
    msgs = " ".join(m for _, m in hits)
    assert token in msgs and "email" in msgs and "aws key" in msgs
    assert zp.parent.name == "refused" and not (tmp_path / "o" / zp.name).exists()   # quarantined
    assert list((tmp_path / "o").glob("REVIEW-*.md"))


def test_leak_gate_deny_list_is_automatic(inst, tmp_path):
    # review checkpoint 1: a persona's name, the org, a project slug and a drive
    # path planted into a kernel file must be caught without the owner listing them
    base = _release_base(inst)
    (base / "03_personas" / "quang-le.md").write_text(
        "---\ntype: persona\nvisibility: private\ncircle: work\n---\n# Quang Le\n", encoding="utf-8")
    (base / "04_projects" / "zetacorp-migration").mkdir()
    (base / "04_projects" / "zetacorp-migration" / "index.md").write_text(
        "---\ntype: project\nvisibility: private\ncircle: work\n---\n# x\n", encoding="utf-8")
    (base / "99_system" / "tasks" / "weekly-review.md").write_text(
        C.read(base / "99_system" / "tasks" / "weekly-review.md")
        + "\nAsk Quang Le about the ZetaCorp migration, files in D:\\var\\_backup_\\x\n", encoding="utf-8")
    _seal(base)
    (zp, hits), = package.build(base, tmp_path / "o", which=("kernel",))
    msgs = " ".join(m for _, m in hits)
    assert "'Quang Le'" in msgs and "'zetacorp'" in msgs and "drive path" in msgs
    tokens, src = C.deny_list(base)
    assert "Quang Le" in tokens and src["quang-le"].startswith("persona file")
    assert "Example Co." not in tokens          # the kernel's own fictional example is public by construction
    assert "warehouse" not in C.deny_list(base, projects=False)[0]   # an export may name its own projects


def test_package_preflight_refuses_drift_and_dirty_tree(inst, tmp_path):
    base = _release_base(inst)
    (base / "99_system" / "PHILOSOPHY.md").write_text(C.read(base / "99_system" / "PHILOSOPHY.md") + "\nedit\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="manifest drift"):
        package.build(base, tmp_path / "o", which=("kernel",))
    assert not list((tmp_path / "o").glob("*.zip"))


def test_leak_gate_fails_closed_without_owner_file(inst, tmp_path):
    base = _release_base(inst)
    (base / "03_personas" / "me.md").unlink()
    _seal(base)
    with pytest.raises(RuntimeError, match="me.md"):
        package.build(base, tmp_path / "o", which=("kernel",))


# ---------------- the development repository (kernel + tools, no owner data) ----------------

def _owner_instance(inst):
    """A real instance carries the kernel's fixtures; give it one secret name."""
    shutil.copytree(FIXTURES, inst / "99_system" / "conformance" / "fixtures")
    secret = "Qx" + str(os.getpid()) + "corp"            # runtime: never a literal in this file
    me = inst / "03_personas" / "me.md"
    me.write_text(C.read(me).replace("check_tokens: [", "check_tokens: [" + secret + ", "), encoding="utf-8")
    return inst, secret


def _dev_repo(tmp_path):
    d = tmp_path / "devrepo"
    d.mkdir()
    shutil.copytree(KERNEL, d / "99_system", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "hosts", d / "hosts")
    shutil.copytree(REPO / "98_tools", d / "98_tools",
                    ignore=shutil.ignore_patterns(".venv", "data", "__pycache__", ".pytest_cache"))
    (d / "README.md").write_text("# AI-Cowork\nPublic front page.\n", encoding="utf-8")
    shutil.copy(REPO / "99_system" / "LICENSE", d / "LICENSE")
    _git(d, "init", "-q")
    _seal(d)
    return d


def test_dev_repo_package_needs_a_deny_source_and_uses_it(inst, tmp_path, monkeypatch):
    monkeypatch.delenv("AICOWORK_DENY_FROM", raising=False)
    owner, secret = _owner_instance(inst)
    dev = _dev_repo(tmp_path)
    assert not C.is_instance(dev) and C.is_instance(owner)
    with pytest.raises(RuntimeError, match="--deny-from"):            # fail closed: no names, no build
        package.build(dev, tmp_path / "o0", which=("kernel",))
    results = package.build(dev, tmp_path / "o1", deny_from=owner)     # clean: builds, root README published
    assert all(h == [] for _, h in results), results
    with zipfile.ZipFile(tmp_path / "o1" / f"aicowork-kernel-{package._version(dev)}.zip") as z:
        assert z.read("README.md").decode().startswith("# AI-Cowork")
    assert (dev / ".agents" / "releases" / "releases.jsonl").is_file()   # dev repo keeps its release log there
    # a name that lives only in the private instance is caught in the dev repo
    f = dev / "99_system" / "PHILOSOPHY.md"
    f.write_text(C.read(f) + "\nThanks to " + secret + ".\n", encoding="utf-8")
    _seal(dev)
    (zp, hits), = package.build(dev, tmp_path / "o2", which=("kernel",), deny_from=owner)
    assert zp.parent.name == "refused" and secret in " ".join(m for _, m in hits)
    review = next((tmp_path / "o2").glob("REVIEW-*.md")).read_text(encoding="utf-8")
    assert str(owner) not in review                                    # the instance path is not recorded
    # the same through git config, and the tree scan
    _git(dev, "config", "aicowork.denyFrom", str(owner))
    hits, src = package.scan_tree(dev)
    assert src == owner.resolve() and any(secret in m for _, m in hits)
    # development notes are part of the repository: scanned too, though never shipped
    (dev / ".agents").mkdir(exist_ok=True)
    (dev / ".agents" / "notes.md").write_text("met " + secret + "\n", encoding="utf-8")
    _git(dev, "add", "-A")
    hits, _ = package.scan_tree(dev)
    assert any(r.endswith(".agents/notes.md") for r, _ in hits)


def test_dev_repo_folder_name_is_not_a_token(inst, tmp_path, monkeypatch):
    """A clone of the public repository is a folder named after the project; the
    project's name in its own files is no leak (an instance folder's name still is)."""
    monkeypatch.delenv("AICOWORK_DENY_FROM", raising=False)
    owner, _ = _owner_instance(inst)
    dev = _dev_repo(tmp_path)
    named = tmp_path / "ai-cowork"
    shutil.move(dev, named)
    (named / "README.md").write_text("# AI-Cowork\nThe ai-cowork kernel.\n", encoding="utf-8")
    _seal(named)
    assert package.scan_tree(named)[0] == []
    assert package.scan_tree(named, deny_from=owner)[0] == []
    assert C.folder_name_token(owner) in package._gate_inputs(named, owner)[1]   # the instance path stays a token


def test_leakscan_without_deny_source_runs_generic_patterns_only(tmp_path, monkeypatch):
    """A contributor's clone names no private instance: `leakscan` never refuses — scanner A
    has no tokens, scanner B (generic patterns) runs in full; `package` still refuses (above)."""
    monkeypatch.delenv("AICOWORK_DENY_FROM", raising=False)
    dev = _dev_repo(tmp_path)
    hits, src = package.scan_tree(dev)
    assert hits == [] and src is None
    f = dev / "99_system" / "PHILOSOPHY.md"
    addr = "someone" + "@" + "gmail" + ".com"                                  # built at runtime: this file is scanned too
    f.write_text(C.read(f) + "\nWrite to " + addr + ".\n", encoding="utf-8")   # scanner B still bites
    _seal(dev)
    hits, _ = package.scan_tree(dev)
    assert any(r.endswith("PHILOSOPHY.md") and "email" in m for r, m in hits)


def test_upgrade_refuses_bad_sha_drift_and_downgrade(inst, tmp_path):
    base = _release_base(inst)
    (zp, hits), = package.build(base, tmp_path / "rel", which=("kernel",))
    assert hits == []
    with pytest.raises(RuntimeError, match="sha256"):
        upgrade.upgrade(base, zp, expect_sha256="0" * 64)
    d = upgrade.upgrade(base, zp, expect_sha256=C.sha256_file(zp))
    assert d["source_sha256"] == C.sha256_file(zp) and d["local_drift"] == [] and d["actions"]   # UPGRADING.md shipped
    # a local edit in a ring: the dry run names it, the apply refuses
    s = base / "99_system" / "skills" / "inbox-triage" / "SKILL.md"
    s.write_text(C.read(s) + "\nmy local tweak\n", encoding="utf-8")
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qam", "local")
    d = upgrade.upgrade(base, zp)
    assert any("inbox-triage" in x for x in d["local_drift"])
    with pytest.raises(RuntimeError, match="local changes"):
        upgrade.upgrade(base, zp, apply=True)
    # a downgrade needs saying so
    old = tmp_path / "old"
    shutil.copytree(base / "99_system", old / "99_system")
    (old / "99_system" / "VERSION").write_text("0.0.0\n", encoding="utf-8")
    (old / "VERSION").write_text("0.0.0\n", encoding="utf-8")
    manifest.write(base / "99_system")
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "add", "-A")
    _git(base, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "accept")
    assert upgrade.upgrade(base, old)["downgrade"]
    with pytest.raises(RuntimeError, match="older"):
        upgrade.upgrade(base, old, apply=True)
    upgrade.upgrade(base, old, apply=True, allow_downgrade=True)
    assert "kernel_version: 0.0.0" in C.read(base / "aicowork.yaml")


def test_artifacts_carry_their_ring_licence(inst, tmp_path):
    base = _release_base(inst)
    for lic in ("99_system/LICENSE", "98_tools/LICENSE", "hosts/LICENSE", "LICENSE"):
        assert "MIT License" in C.read(REPO / lic)
        shutil.copy(REPO / lic, base / lic)
    _seal(base)
    built = {zp.name: zp for zp, hits in package.build(base, tmp_path / "lic")}
    assert set(built) == {f"aicowork-{VERSION}.zip", f"aicowork-kernel-{VERSION}.zip", f"aicowork-tools-{VERSION}.zip"}
    for name, zp in built.items():
        with zipfile.ZipFile(zp) as z:
            names = set(z.namelist())
            if name == f"aicowork-{VERSION}.zip":
                # the one-download release: every ring carries its own licence, and the root one too
                assert {"99_system/LICENSE", "hosts/LICENSE", "98_tools/LICENSE", "98_tools/apps/aicowork/src/aicowork/cli.py", "98_tools/libs/core/src/aicowork_core/scan.py",
                        "99_system/VERSION", "LICENSE"} <= names
            else:
                assert "MIT License" in z.read("LICENSE").decode()


def test_release_build_makes_no_network_call(inst, tmp_path, monkeypatch):
    import socket
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: (_ for _ in ()).throw(AssertionError("dns")))
    base = _release_base(inst)
    (zp, hits), = package.build(base, tmp_path / "o", which=("kernel",))
    assert hits == []


def test_development_folders_never_ship(inst, tmp_path):
    base = _release_base(inst)
    (base / "90_devkit").mkdir()
    (base / "90_devkit" / "x.md").write_text("dev only\n", encoding="utf-8")
    _seal(base)
    for zp, _ in package.build(base, tmp_path / "o"):
        with zipfile.ZipFile(zp) as z:
            assert not [n for n in z.namelist() if n.split("/")[0][:3] in {f"9{i}_" for i in range(6)}]
    old = package.TOOLS_ITEMS[:]
    try:
        package.TOOLS_ITEMS.append("90_devkit")       # someone adds it to the allow-list by mistake
        with pytest.raises(RuntimeError, match="never ship"):
            package.build(base, tmp_path / "o2", which=("tools",))
    finally:
        package.TOOLS_ITEMS[:] = old


# ---------------- the hooks scan what leaves, not what the working copy shows (review of rc.2) ----------------

def _tiny_repo(tmp_path):
    d = tmp_path / "tiny"
    d.mkdir()
    _git(d, "init", "-q")
    (d / "note.md").write_text("harmless\n", encoding="utf-8")
    _git(d, "add", "-A")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "start")
    return d


def test_tree_scan_reads_the_index_not_the_working_copy(inst, tmp_path):
    owner, secret = _owner_instance(inst)
    d = _tiny_repo(tmp_path)
    (d / "note.md").write_text("met " + secret + "\n", encoding="utf-8")
    _git(d, "add", "note.md")                                        # staged …
    (d / "note.md").write_text("harmless\n", encoding="utf-8")        # … and hidden in the working copy
    hits, _ = package.scan_tree(d, deny_from=owner)
    assert any(secret in m for _, m in hits)
    _git(d, "add", "note.md")                                        # staged clean again
    (d / "draft.md").write_text("met " + secret + "\n", encoding="utf-8")   # untracked: not in the commit
    assert package.scan_tree(d, deny_from=owner)[0] == []


def test_push_scan_reads_every_pushed_commit(inst, tmp_path):
    owner, secret = _owner_instance(inst)
    d = _tiny_repo(tmp_path)
    base_tip = head(d)
    (d / "note.md").write_text("met " + secret + "\n", encoding="utf-8")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qam", "add")
    (d / "note.md").write_text("harmless again\n", encoding="utf-8")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qam", "clean the tip")
    assert package.scan_tree(d, deny_from=owner)[0] == []            # the tip is clean …
    zero = "0" * 40
    hits, _ = package.scan_pushed(d, [(head(d), zero)], deny_from=owner)
    assert any(secret in m for _, m in hits)                          # … the history that leaves is not
    # what the remote already has is not sent again; a deletion sends nothing
    assert package.scan_pushed(d, [(base_tip, zero)], deny_from=owner)[0] == []
    assert package.pushed_revs(d, [(zero, base_tip)]) == []
    # a commit message is history too
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "--allow-empty", "-qm", "thanks " + secret)
    hits, _ = package.scan_pushed(d, [(head(d), zero)], deny_from=owner)
    assert any(r.startswith("A commit-") for r, _ in hits)


# ---------------- second review of the rc.3 work: R1, R2, O1 ----------------

def test_push_scan_does_not_trust_another_remotes_history(inst, tmp_path):
    """R2: history that ANOTHER remote already has may be new to the one receiving
    the push. Only the receiving remote's own branches count as already sent."""
    owner, secret = _owner_instance(inst)
    d = _tiny_repo(tmp_path)
    (d / "note.md").write_text("met " + secret + "\n", encoding="utf-8")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qam", "add")
    (d / "note.md").write_text("harmless again\n", encoding="utf-8")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qam", "clean the tip")
    tip, zero = head(d), "0" * 40
    _git(d, "remote", "add", "other", str(tmp_path / "elsewhere.git"))
    _git(d, "update-ref", "refs/remotes/other/main", tip)            # another remote has it all
    for receiving in (None, "fresh", str(tmp_path / "bare.git")):    # a bare URL, an unknown name, none
        hits, _ = package.scan_pushed(d, [(tip, zero)], deny_from=owner, remote=receiving)
        assert any(secret in m for _, m in hits), receiving
    # pushing to the remote that already holds it sends nothing new
    assert package.scan_pushed(d, [(tip, zero)], deny_from=owner, remote="other")[0] == []


def test_reviewed_trailer_address_only_in_trailers(inst, tmp_path):
    """O1: the owner reviewed the bot's no-reply address as a false alarm, for
    Co-Authored-By trailers only (by hash: the address is never written here)."""
    owner, _ = _owner_instance(inst)
    d = _tiny_repo(tmp_path)
    shutil.copytree(REPO / "90_devkit", d / "90_devkit", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    bot = "noreply" + "@" + "anthropic.com"
    other = "someone" + "@" + "corp-mail.net"
    zero = "0" * 40
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "--allow-empty", "-qm",
         "fix: x\n\nCo-Authored-By: Bot <" + bot + ">")
    assert package.scan_pushed(d, [(head(d), zero)], deny_from=owner)[0] == []
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "--allow-empty", "-qm",
         "fix: y\n\nwrite to " + bot)                                # not a trailer: still a hit
    assert package.scan_pushed(d, [(head(d), zero)], deny_from=owner)[0]
    _git(d, "reset", "-q", "--hard", "HEAD~1")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "--allow-empty", "-qm",
         "fix: z\n\nCo-Authored-By: Someone <" + other + ">")       # another address: still a hit
    assert package.scan_pushed(d, [(head(d), zero)], deny_from=owner)[0]


def test_pre_commit_scans_what_it_adds(inst, tmp_path):
    """R1 + X: the hook writes the ring manifests and adds them; the leak scan must
    read the index after that, and a ring may not hold untracked files (the
    manifest would name a file the commit does not hold)."""
    owner, secret = _owner_instance(inst)
    d = _dev_repo(tmp_path)
    shutil.copytree(REPO / ".githooks", d / ".githooks")
    shutil.copytree(REPO / "90_devkit", d / "90_devkit", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    shutil.copy2(REPO / ".gitattributes", d / ".gitattributes")
    _git(d, "config", "aicowork.denyFrom", str(owner))
    _git(d, "add", "-A")
    _git(d, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "start", "--no-verify")
    _git(d, "config", "core.hooksPath", ".githooks")
    env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""))
    (d / "98_tools" / ("untracked-" + secret + ".md")).write_text("harmless body\n", encoding="utf-8")
    readme = d / "98_tools" / "README.md"
    readme.write_text(C.read(readme) + "\nA small change.\n", encoding="utf-8")
    _git(d, "add", "98_tools/README.md")
    r = subprocess.run(["git", "-C", str(d), "-c", "user.email=t@example.com", "-c", "user.name=t",
                        "commit", "-qm", "docs: change"], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "untracked" in r.stderr                  # refused before writing a manifest
    rc = subprocess.run(["git", "-C", str(d), "show", "HEAD:98_tools/MANIFEST.sha256"], capture_output=True, text=True)
    assert secret not in rc.stdout
    _git(d, "add", "98_tools")                                            # now staged: the scan of the index sees it
    r = subprocess.run(["git", "-C", str(d), "-c", "user.email=t@example.com", "-c", "user.name=t",
                        "commit", "-qm", "docs: change"], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and secret in (r.stdout + r.stderr)


def test_fixtures_generator_reproduces_the_committed_fixtures():
    """O5: the committed files are the fixtures; the generator must write exactly them."""
    from devkit import fixtures
    assert fixtures.differences() == []


def test_preflight_refuses_versions_that_disagree(inst, tmp_path):
    """rc.3 readiness B3: VERSION, the tools' package versions and uv.lock say the
    same, or no release is built (a stale lock breaks every `uv run --locked`)."""
    base = _release_base(inst)
    assert package.version_problems(base) == []
    (base / "99_system" / "VERSION").write_text("0.0.1-rc.9\n", encoding="utf-8")
    probs = package.version_problems(base)
    assert any("pyproject.toml" in p and "0.0.1rc9" in p for p in probs)
    assert any(p.startswith("98_tools/uv.lock") for p in probs)
    for f in (base / "98_tools").glob("**/pyproject.toml"):
        if ".venv" not in f.parts:
            f.write_text(C.read(f).replace(f'version = "{package._pep440(VERSION)}"', 'version = "0.0.1rc9"'), encoding="utf-8")
    probs = package.version_problems(base)
    assert probs and all(p.startswith("98_tools/uv.lock") for p in probs)          # the lock is what is left
    lock = base / "98_tools" / "uv.lock"
    lock.write_text(C.read(lock).replace(f'version = "{package._pep440(VERSION)}"', 'version = "0.0.1rc9"'), encoding="utf-8")
    assert package.version_problems(base) == []
