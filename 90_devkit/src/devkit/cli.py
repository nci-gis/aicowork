# -*- coding: utf-8 -*-
"""`devkit` — the kernel developer's commands. Never shipped (90_devkit/).

    PYTHONPATH=90_devkit/src python -m devkit <command>      (no installs)

Commands: package (release zips through the leak gate), leakscan (every tracked
file of the development repository), fixtures (regenerate the fictional
conformance fixtures), fmt (Markdown formatting, Prettier pinned). Builds on aicowork_core only — never on the apps."""
import argparse
import sys
from pathlib import Path


def _base(args):
    from aicowork_core.common import base_path
    return base_path(getattr(args, "base", None))


def cmd_package(args):
    from devkit import package
    base = _base(args)
    which = tuple(args.only.split(",")) if args.only else ("full", "kernel", "tools")
    try:
        results = package.build(base, args.out, which=which, deny_from=args.deny_from)
    except RuntimeError as e:
        print(f"package refused: {e}")
        return 1
    bad = 0
    for zp, hits in results:
        print(f"built {zp}  [{zp.stat().st_size // 1024} KB]")
        for r, m in hits:
            print(f"  LEAK  {r}  — {m}")
        bad += len(hits)
    out = Path(args.out or base / "_scratch" / "release")
    reviews = sorted(out.glob("REVIEW-*.md"))
    if bad:
        print(f"LEAK GATE FAILED — {bad} hit(s); artifacts moved to refused/ — review: {reviews[-1] if reviews else '-'}")
        return 1
    print(f"leak gate: clean on the built artifacts — review file: {reviews[-1] if reviews else '-'} (ship decision: a person)")
    return 0


def cmd_leakscan(args):
    """The development repository's own check: every tracked file through both scanners."""
    from devkit import package
    base = _base(args)
    hits, src = package.scan_tree(base, args.deny_from)
    if hits is not None and args.pushed:
        # pre-push hands "<local ref> <local sha> <remote ref> <remote sha>" lines on stdin
        updates = [(f[1], f[3]) for f in (l.split() for l in sys.stdin.read().splitlines()) if len(f) == 4]
        pushed, _ = package.scan_pushed(base, updates, args.deny_from, args.remote)
        hits += [(r.replace(" ", " pushed ", 1), m) for r, m in pushed]
    if hits is None:
        print("leakscan refused: no deny-list — pass --deny-from <private instance> "
              "(or once: git config aicowork.denyFrom <instance folder>)")
        return 1
    for r, m in hits:
        print(f"  LEAK  {r}  — {m}")
    where = ('generic patterns only, no private instance named (a contributor\'s clone holds no owner names; '
             'the maintainer\'s push runs this again against theirs)' if src is None else
             'deny-list from ' + ('this folder' if src.resolve() == base.resolve() else 'the instance named by --deny-from'))
    print(f"leakscan: {'clean' if not hits else str(len(hits)) + ' hit(s)'} — {where}")
    return 1 if hits else 0


def cmd_fixtures(args):
    from devkit import fixtures
    if args.check:
        diff = fixtures.differences()
        for rel in diff:
            print(f"  differs  {rel}")
        print("fixtures: " + ("the generator reproduces the committed fixtures" if not diff
                              else f"{len(diff)} file(s) differ from what the generator writes"))
        return 1 if diff else 0
    fixtures.write()
    print("fixtures written under 99_system/conformance/fixtures/ — review the diff, then `aicowork manifest --write`")
    return 0


def cmd_changelog(args):
    from devkit import changelog
    base = _base(args)
    reasons = changelog.check(base, args.since)
    for r in reasons:
        print(f"  {r}")
    print("changelog: " + ("the first section moved with the rings (or nothing in a ring changed)" if not reasons
                           else "needs a line — see above"))
    return 1 if reasons else 0


def cmd_fmt(args):
    from devkit import fmt
    base = _base(args)
    rc, out = fmt.run(base, check=args.check)
    if out:
        print(out)
    if args.check:
        print("fmt: " + ("all Markdown formatted" if rc == 0 else "files above need `devkit fmt`"))
        return rc
    if rc:
        return rc
    from aicowork_core import common as C, manifest
    for _, root in C.ring_roots(base):
        if root.is_dir() and (root / manifest.MANIFEST).is_file():
            manifest.write(root)
    print("fmt: formatted; ring manifests rewritten — now run `aicowork verify` (the tests prove no meaning changed) and review `git diff`")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="devkit", description="AI-Cowork devkit — release building and checks (development repository only).")
    sub = parser.add_subparsers(dest="cmd")

    def add(name, fn, help):
        p = sub.add_parser(name, help=help)
        p.set_defaults(fn=fn)
        p.add_argument("--base", metavar="DIR", help="development repository (default: the one this devkit is in)")
        return p

    p = add("package", cmd_package, "build release artifacts + run the leak gate")
    p.add_argument("--out", metavar="DIR")
    p.add_argument("--only", help="full, kernel, tools, or a comma list (default: all three)")
    p.add_argument("--deny-from", metavar="DIR",
                   help="the private instance whose names must not ship (default: git config aicowork.denyFrom)")
    p = add("leakscan", cmd_leakscan, "scan what the next commit holds (the git index) with both leak scanners")
    p.add_argument("--deny-from", metavar="DIR", help="the private instance that holds the names (default: git config aicowork.denyFrom)")
    p.add_argument("--pushed", action="store_true",
                   help="also scan every blob and commit message a push sends (reads the pre-push lines on stdin)")
    p.add_argument("--remote", metavar="NAME",
                   help="with --pushed: the remote receiving the push (pre-push's $1); only its own branches count as already sent")
    p = add("fixtures", cmd_fixtures, "regenerate the fictional conformance fixtures")
    p.add_argument("--check", action="store_true", help="only list fixtures the generator would change")
    p = add("fmt", cmd_fmt, "format the repository's Markdown with Prettier (pinned; see .prettierignore)")
    p.add_argument("--check", action="store_true", help="only list files that would change")
    p = add("changelog", cmd_changelog, "check that a ring change since a base commit came with a CHANGELOG line")
    p.add_argument("--since", metavar="REF", required=True, help="the base commit or branch to compare HEAD with (CI: the pull request's base)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    if not getattr(args, "fn", None):
        parser.print_help()
        return 0
    return args.fn(args)
