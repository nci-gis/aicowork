# -*- coding: utf-8 -*-
"""Creating an instance, installing a release, carrying names, modules, host skill stubs."""
import datetime as dt  # noqa: F401
import json  # noqa: F401
import sys  # noqa: F401
from pathlib import Path  # noqa: F401

from aicowork_core.config import BASE, URL  # noqa: F401
from aicowork.commands._shared import _base, _print_findings, _with_kernel  # noqa: F401


def cmd_init(args):
    from aicowork.instance import ops
    target = Path(args.target)
    if not target.is_absolute():
        # the launchers change to their own folder; a relative target means where the user was
        import os
        target = Path(os.environ.get("AICOWORK_CALLER_DIR") or ".") / target
    target = target.resolve()
    try:
        created = ops.init(target, preset=args.preset, lang=args.lang, tools=not args.no_tools)
    except Exception as e:
        print(f"init failed: {e}")
        return 1
    for c in created:
        print(f"  created {c}")
    print(f"instance ready at {target}\n"
          "next, in that folder:\n"
          "  1. fill 03_personas/me.md (Name, Org, check_tokens: the names that must never be shared)\n"
          "  2. read policy.yaml; add `decided: <today>` when you agree (until then nothing is copied anywhere)\n"
          "  3. copy INSTRUCTIONS.md into your host's instruction file (hosts/README.md says where)\n"
          "  4. commit what you changed:   git add -A && git commit -m \"chore: fill me.md\"\n"
          "     (the first time, git asks who you are: in this folder, git config user.name \"<First Last>\""
          " and git config user.email \"<you@example.com>\")"
          + ("\n  5. git config core.hooksPath .githooks   (the hooks refuse a leak before it is committed or pushed)\n"
             "  6. ./aicowork.sh doctor   (on Windows: aicowork.bat doctor)" if (target / ".githooks").is_dir() else ""))
    return 0


def cmd_upgrade(args):
    from aicowork.instance import upgrade
    try:
        diff = upgrade.upgrade(_base(args), args.source, apply=args.apply,
                               expect_sha256=args.expect_sha256, allow_downgrade=args.downgrade)
    except RuntimeError as e:
        print(f"upgrade refused: {e}")
        return 1
    print(f"kernel {diff['from']} -> {diff['to']}: +{len(diff['added'])} ~{len(diff['changed'])} "
          f"-{len(diff['removed'])} (removed files go to 07_archive/, never deleted)"
          + (f"  source sha256 {diff['source_sha256'][:16]}…" if diff.get("source_sha256") else ""))
    for k in ("added", "changed", "removed"):
        for p in diff[k][:30]:
            print(f"  {k[0]} {p}")
    for d in diff["local_drift"][:20]:
        print(f"  LOCAL  {d}  — your edit; an apply would overwrite it (refused)")
    if diff.get("downgrade"):
        print("  DOWNGRADE — older than what is installed")
    if diff.get("actions"):
        print("\n--- instance actions for this version (owner, by hand) ---\n" + diff["actions"] + "\n---")
    if not args.apply:
        print("dry run — add --apply (needs a clean git tree; takes a bundle first); then run `aicowork doctor`")
    else:
        print("applied — now run `aicowork doctor` and commit `chore: upgrade kernel " + diff["to"] + "`")
    return 0


def cmd_denylist(args):
    """Print the instance's whole deny-list as one `check_tokens:` line, so it can be
    carried into a new instance's me.md before the old personas and projects go."""
    from aicowork_core import common as C
    tokens, src = C.deny_list(_base(args))
    if tokens is None:
        print("no 03_personas/me.md here — nothing to list")
        return 1
    if args.verbose:
        for t in sorted(tokens, key=str.lower):
            print(f"  {t:30} {src.get(t, '')}")
    print("check_tokens: [" + ", ".join(sorted(tokens, key=str.lower)) + "]")
    return 0


def cmd_modules(args):
    from aicowork.instance import ops
    lock, probs = ops.modules_lock(_base(args), write=args.lock)
    for name, h in lock.items():
        print(f"  {name}: {h[:16]}")
    for p in probs:
        print(f"  WARN {p}")
    return 1 if probs and not args.lock else 0


def cmd_skills(args):
    from aicowork.instance import ops
    for z in ops.skills_pack(_base(args), args.out):
        print(f"  {z}")
    print("upload each zip as a skill in the host (see hosts/<host>.md); each stub only points into the folder")
    return 0


def register(add):
    p = add("init", cmd_init, "create a fresh instance (never overwrites)", base=False)
    p.add_argument("target")
    p.add_argument("--preset", default="corporate-strict", choices=["corporate-strict", "personal-simple"])
    p.add_argument("--lang", default="en", choices=["en", "vi"])
    p.add_argument("--no-tools", action="store_true", help="copy the kernel and host pages only, not 98_tools/ and its launchers")
    p = add("upgrade", cmd_upgrade, "replace kernel/tools from a release (dry run by default)")
    p.add_argument("source", help="release zip or folder (the owner fetches it; the tools never do)")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--expect-sha256", metavar="HEX", help="the published sha256 of the zip; refuse on mismatch")
    p.add_argument("--downgrade", action="store_true", help="allow installing an older version, on purpose")
    p = add("denylist", cmd_denylist, "print this instance's deny-list as a check_tokens line (to carry into a new me.md)")
    p.add_argument("--verbose", action="store_true", help="also show where each name comes from")
    p = add("modules", cmd_modules, "check (or --lock) enabled modules")
    p.add_argument("--lock", action="store_true")
    p = add("skills", cmd_skills, "build account-level skill stubs (zips) for a host")
    p.add_argument("--out")
