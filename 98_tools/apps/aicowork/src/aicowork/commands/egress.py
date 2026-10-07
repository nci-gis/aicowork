# -*- coding: utf-8 -*-
"""The only ways a copy leaves the folder, and the owner-only erasure."""
import datetime as dt  # noqa: F401
import json  # noqa: F401
import sys  # noqa: F401
from pathlib import Path  # noqa: F401

from aicowork_core import common as C
from aicowork_core.config import BASE, URL  # noqa: F401
from aicowork.commands._shared import _base, _print_findings, _with_kernel  # noqa: F401


def cmd_backup(args):
    from aicowork.egress import gate as egress
    try:
        res = egress.backup(_base(args), args.dest, dry_run=args.dry_run)
    except egress.PolicyError as e:
        print(f"backup refused: {e}")
        return 1
    print(json.dumps(res, indent=1))
    return 0


def cmd_export(args):
    from aicowork.egress import gate as egress
    try:
        res = egress.export(_base(args), args.dest, max_visibility=args.max_visibility,
                            only_private=args.only == "private", dry_run=args.dry_run, allow=args.allow or (),
                            passphrase_file=args.passphrase_file)
    except egress.PolicyError as e:
        print(f"export refused: {e}")
        return 1
    if args.dry_run:
        for r, v, n in res["files"]:
            print(f"  + {r} ({v}{f', {n} private block(s) stripped' if n else ''})")
        for r, why in res["skipped"]:
            print(f"  - {r}: {why}")
        for r, m in res["hits"]:
            print(f"  {'ALLOWED' if (r, m) not in res['blocking'] else 'HIT    '} {r}: {m}")
        for r in res.get("sealed", []):
            print(f"  S {r}  (sealed: above the destination's level)")
        for r in res.get("sidecars", []):
            print(f"  S {r}.private.sealed  (its private blocks, sealed)")
        print(f"dry run: {len(res['files'])} would be exported to {res['out']}; "
              f"{len(res['blocking'])} blocking hit(s); {res['dropped_keys']} frontmatter keys would be dropped; nothing written")
    else:
        print(f"exported {res['count']} file(s) -> {res['out']}  receipt {res['receipt'][:16]}")
        if res.get("hidden_char_warnings"):
            print(f"  WARN {res['hidden_char_warnings']} hidden character(s) left in {len(res['hidden_char_files'])} file(s) "
                  f"({', '.join(res['hidden_char_files'][:3])}) — recorded in the receipt; `aicowork doctor` lists them")
    return 0


def cmd_unseal(args):
    from aicowork.egress import seal as S
    try:
        if args.passphrase_file:
            pw = Path(args.passphrase_file).read_text(encoding="utf-8").splitlines()[0].strip()
        elif sys.stdin.isatty():
            import getpass
            pw = getpass.getpass("passphrase: ")
        else:
            print("unseal: needs a passphrase (terminal or --passphrase-file)", file=sys.stderr)
            return 2
        data, head = S.unseal(Path(args.file).read_bytes(), pw)
    except (S.SealError, OSError) as e:
        print(f"unseal: {e}", file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).write_bytes(data)
        print(f"opened {head['aad']} -> {args.out}")
    else:
        sys.stdout.write(data.decode("utf-8", errors="replace"))
    return 0


def cmd_verify_receipts(args):
    from aicowork.egress import gate as egress
    probs = egress.verify_receipts(_base(args))
    for p in probs:
        print(f"  {p}")
    print("receipt chain: " + ("BROKEN" if probs else "intact"))
    return 1 if probs else 0


def cmd_retention(args):
    from aicowork.instance import ops
    rows = ops.retention(_base(args), args.days)
    for path, key, date, days in rows:
        print(f"  {path}: {key} {date} ({'overdue' if days < 0 else f'in {days} days'})")
    print(f"{len(rows)} file(s) due for review within {args.days} days")
    return 0


def cmd_purge(args):
    from aicowork.instance import ops
    print(f"PURGE erases {args.path} for good (git history and old backups still hold it until rotated).")
    confirm = input("type the path again to confirm: ").strip()
    try:
        rec = ops.purge(_base(args), args.path, args.reason, confirm)
    except (PermissionError, ValueError) as e:
        print(f"purge refused: {e}")
        return 1
    print(f"purged; tombstone {rec['content_sha256'][:16]} in 06_logs/purge/tombstones.jsonl")
    return 0


def cmd_decide(args):
    from aicowork.egress import gate
    from aicowork.instance import ops
    base = _base(args)
    pol, _ = C.load_yaml(base / "policy.yaml")
    pol = pol if isinstance(pol, dict) else {}
    print("policy.yaml — what you decide now (PHILOSOPHY #11: once, in a calm moment):")
    print(f"  preset:        {pol.get('preset')}")
    print(f"  distribution:  {gate.distribution(pol)}")
    for d in pol.get("destinations") or []:
        if isinstance(d, dict):
            print(f"  destination:   {d.get('id')} ({d.get('kind')}) -> {d.get('path')}  accepts {d.get('accepts')}, below: {d.get('below')}")
    print(f"  ai_surfaces:   {', '.join(map(str, pol.get('ai_surfaces') or [])) or '(none)'}")
    print(f"  remotes:       {', '.join(map(str, pol.get('remotes') or [])) or '(none)'}")
    try:
        confirm = input("type today's date (YYYY-MM-DD) to decide it: ") if sys.stdin.isatty() else ""
        day = ops.decide(base, confirm, here=args.here)
    except (PermissionError, ValueError) as e:
        print(f"decide refused: {e}")
        return 1
    # the decision is bound the moment it is made: the same owner terminal writes the anchor
    from aicowork.instance import anchor
    try:
        f, rec = anchor.anchor(base, here=args.here)
    except RuntimeError as e:
        print(f"decided: {day} written to policy.yaml, but not anchored — {e}")
        return 1
    print(f"decided: {day} written to policy.yaml and anchored ({f.name}: policy and {len(rec['steering']) - 1} other "
          "steering files) — commit it (`chore: decide policy.yaml`)")
    return 0


def register(add):
    p = add("backup", cmd_backup, "git bundle to a policy-listed backup destination")
    p.add_argument("--dest", required=True)
    p.add_argument("--dry-run", action="store_true")
    p = add("export", cmd_export, "export through the gate to a policy-listed destination")
    p.add_argument("--dest", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-visibility", choices=["public", "internal", "private"])
    p.add_argument("--only", choices=["private"])
    p.add_argument("--passphrase-file", metavar="FILE",
                   help="below: encrypt — the owner's passphrase, first line of a file OUTSIDE the folder (else typed at a terminal)")
    p.add_argument("--allow", action="append", metavar="PATH",
                   help="export this file despite a content-scan hit (recorded in the receipt); repeatable")
    p = add("unseal", cmd_unseal, "open a sealed export file with the owner's passphrase (to stdout or --out)", base=False)
    p.add_argument("file")
    p.add_argument("--out", metavar="FILE")
    p.add_argument("--passphrase-file", metavar="FILE")

    add("verify-receipts", cmd_verify_receipts, "check the egress receipt hash chain")
    p = add("retention", cmd_retention, "files whose expires/review_by is due")
    p.add_argument("--days", type=int, default=30)
    p = add("decide", cmd_decide, "HUMAN-ONLY, on the host: the owner decides policy.yaml (writes `decided:`)")
    p.add_argument("--here", action="store_true", help="this IS the owner's host, although it looks like a sandbox")
    p = add("purge", cmd_purge, "HUMAN-ONLY erasure with a hash-only tombstone")
    p.add_argument("path")
    p.add_argument("--reason", required=True)
