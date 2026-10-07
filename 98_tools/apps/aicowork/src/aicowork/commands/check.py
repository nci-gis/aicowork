# -*- coding: utf-8 -*-
"""Checking an instance: conformance, audit, health, reach, manifests, the trust anchor, evidence."""
import datetime as dt  # noqa: F401
import json  # noqa: F401
import sys  # noqa: F401
from pathlib import Path  # noqa: F401

from aicowork_core.config import BASE, URL  # noqa: F401
from aicowork.instance import anchor  # noqa: F401
from aicowork.commands._shared import _base, _print_findings, _with_kernel  # noqa: F401


def cmd_conform(args):
    from aicowork.conform import audit
    from aicowork.conform import checks
    from aicowork_core import common as C
    base = _base(args)
    if args.case:
        if not args.since:
            print("--case needs --since <commit> (the state before the agent ran)")
            return 2
        fn = audit.L3.get(args.case)
        if not fn:
            print(f"unknown case {args.case}; one of {', '.join(audit.L3)}")
            return 2
        findings, info = fn(base, args.since), {}
    else:
        findings, info = checks.run(base, level=args.level)
    errors, warns = checks.summarize(findings)
    _print_findings(findings, verbose=not args.quiet)
    label = args.case or f"L{args.level}"
    verdict = "PASS" if not errors else "FAIL"
    print(f"conformance {label}: {verdict} — {len(errors)} error(s), {len(warns)} warning(s)"
          + (f", kernel {info['kernel_words']} words" if info.get("kernel_words") else "")
          + (f" ({info['translation_words']} in translations)" if info.get("translation_words") else ""))
    if args.report:
        lines = [f"- result: **{verdict}** ({len(errors)} errors, {len(warns)} warnings)", ""] + \
                [f"- {f.level} `{f.case}` `{f.path}` — {f.message}" for f in findings]
        p = C.write_report(base, "conformance", f"{C.today().isoformat()}_{label}.md",
                           f"Conformance {label} — {C.today().isoformat()}", lines)
        print(f"report: {p.relative_to(base)}")
    return 1 if errors else 0


def cmd_audit(args):
    from aicowork.conform import audit
    from aicowork.conform import checks
    from aicowork_core import common as C
    base = _base(args)
    try:
        findings = audit.audit(base, args.since, task=args.task, allow=args.allow or ())
    except RuntimeError as e:
        print(f"audit failed: {e}")
        return 2
    errors, warns = checks.summarize(findings)
    _print_findings(findings)
    verdict = "CLEAN" if not errors else "FLAGGED"
    print(f"audit since {args.since}: {verdict} — {len(errors)} error(s), {len(warns)} warning(s)")
    lines = [f"- since: `{args.since}`", f"- task: `{args.task or 'any'}`", f"- result: **{verdict}**", ""] + \
            [f"- {f.level} `{f.case}` `{f.path}` — {f.message}" for f in findings]
    p = C.write_report(base, "audit", f"{dt.datetime.now():%Y-%m-%d_%H%M%S}_audit.md",
                       f"Session audit — {C.today().isoformat()}", lines)
    print(f"report: {p.relative_to(base)}")
    return 1 if errors else 0


def cmd_doctor(args):
    from aicowork.instance import ops
    rows = ops.doctor(_base(args), quick=args.quick)
    mark = {"ok": "ok  ", "warn": "WARN", "error": "FAIL"}
    for level, area, msg in rows:
        if level != "ok" or not args.quick:
            print(f"  {mark[level]}  {area:12} {msg}")
    bad = sum(1 for r in rows if r[0] == "error")
    print(f"doctor: {'FAIL' if bad else 'OK'} — {bad} error(s), {sum(1 for r in rows if r[0] == 'warn')} warning(s)")
    return 1 if bad else 0


def cmd_reach(args):
    from aicowork.instance import ops
    r = ops.reach(_base(args))
    if args.json:
        print(json.dumps({k: v for k, v in r.items() if k != "counts"}, indent=1, default=str))
        return 0
    pv = r["per_visibility"]
    print(f"the connected folder exposes {sum(pv.values())} notes to the model: "
          f"{pv['private']} private, {pv['internal']} internal, {pv['public']} public")
    if r["policy_error"]:
        print(f"  policy: {r['policy_error']}")
    if not r["surfaces"]:
        print("  no approved AI surface is listed in policy.yaml — every note reaches an unrecorded surface")
    for s in r["surfaces"]:
        print(f"  surface {s['id']}: may read up to {s['max_visibility']}; "
              f"{r['flagged'].get(s['id'], 0)} note(s) above that")
    for label, items in (("large files (>5 MB)", r["big"]), ("scratch/parked files", r["outside"])):
        if items:
            print(f"  {label}: {len(items)}, e.g. {items[0]}")
    for rel_, mk in r.get("stamped", []):
        print(f"  PROHIBITED  {rel_}: contains {mk!r} — must not be in this folder")
    return 1 if r.get("stamped") else 0


def cmd_manifest(args):
    from aicowork_core import common as C
    from aicowork_core import manifest
    base = _base(args)
    roots = [r for _, r in C.ring_roots(base)]
    if args.write:
        for r in roots:
            if r.is_dir():
                p, h = manifest.write(r)
                print(f"wrote {p.relative_to(base)} ({h[:16]})")
        return 0
    bad = 0
    for r in roots:
        probs = manifest.verify(r)
        bad += len(probs)
        print(f"{r.relative_to(base)}: {'matches' if not probs else f'{len(probs)} problem(s)'}")
        for p in probs[:20]:
            print(f"  {p}")
    return 1 if bad else 0


def cmd_anchor(args):
    from aicowork_core import manifest
    try:
        f, rec = anchor.anchor(_base(args), here=args.here)
    except RuntimeError as e:
        print(f"anchor: {e}", file=sys.stderr)
        return 2
    print(f"anchored {rec.get('commit', '')[:10]} kernel={str(rec.get('kernel_manifest'))[:12]} -> {f}")
    return 0


def cmd_verify(args):
    """The single gate hooks and CI call: tests, conformance, manifests, receipts."""
    import subprocess
    from aicowork.conform import checks
    from aicowork_core import common as C
    from aicowork.egress import gate as egress
    from aicowork_core import manifest
    base = _base(args)
    ok = True
    example = C.kernel_dir(base) / "conformance" / "fixtures" / "example-instance"
    for label, target in (("instance", base), ("example instance", example)):
        if not target.is_dir():
            print(f"  skip  {label}: not found")
            continue
        if label == "instance" and not C.is_instance(base):
            print("  skip  instance: this is the development repository (no owner data); "
                  "`devkit leakscan` checks it instead")
            continue
        if target == example and not (target / "99_system").exists():
            f, _ = checks.run(_with_kernel(target, C.kernel_dir(base)), level=2)
        else:
            f, _ = checks.run(target, level=2)
        errs, _ = checks.summarize(f)
        print(f"  {'ok  ' if not errs else 'FAIL'}  conformance L2 on {label}: {len(errs)} error(s)")
        if errs and label == "example instance":
            _print_findings(errs)
        ok &= not errs or (label == "instance" and args.allow_instance)
    for _, r in C.ring_roots(base):
        if not r.is_dir():
            continue
        probs = manifest.verify(r)
        print(f"  {'ok  ' if not probs else 'FAIL'}  manifest {r.name}: {len(probs)} problem(s)")
        ok &= not probs
    probs = egress.verify_receipts(base)
    print(f"  {'ok  ' if not probs else 'FAIL'}  receipts: {len(probs)} problem(s)")
    ok &= not probs
    if not args.fast:
        import importlib.util
        import os
        import shutil
        suites = (sorted((base / "98_tools").glob("libs/*/tests")) + sorted((base / "98_tools").glob("apps/*/tests"))
                  + sorted(base.glob("9[0-5]_*/tests")))       # the devkit's, in the development repository
        # the tests need pytest and the viewer's packages; the launcher installs the command
        # line only, so with uv the suites run in the whole tools environment (dev group too)
        runner, env = [sys.executable], None
        complete = all(importlib.util.find_spec(m) is not None for m in ("pytest", "fastapi"))
        tools = base / "98_tools"
        if not complete and shutil.which("uv") and (tools / "pyproject.toml").is_file():
            runner = ["uv", "run", "--locked", "--project", str(tools), "python"]
            env = dict(os.environ, UV_LINK_MODE="copy")
        for tests in suites:
            tool = tests.parent.name
            if runner[0] == sys.executable and importlib.util.find_spec("pytest") is None:
                print(f"  FAIL  tests {tool}: pytest is not installed here — install uv (it sets up the tests' packages), then run verify again")
                ok = False
                continue
            if runner[0] == sys.executable and tool == "viewer" and importlib.util.find_spec("fastapi") is None:
                print(f"  skip  tests {tool}: needs the viewer's packages — install uv, then run verify again")
                continue
            r = subprocess.run([*runner, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tests)],
                               capture_output=True, text=True, cwd=str(tests.parent), env=env)
            tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or ["?"]
            print(f"  {'ok  ' if r.returncode == 0 else 'FAIL'}  tests {tool}: {tail[0]}")
            ok &= r.returncode == 0
    print("verify: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def cmd_audit_pack(args):
    from aicowork.conform import evidence
    out, notes = evidence.build(_base(args), args.out, run_tests=not args.no_tests)
    for n in notes:
        print(f"  note: {n}")
    print(f"audit pack: {out}  ({len(list(out.iterdir()))} files, see MANIFEST.sha256)")
    return 0


def cmd_sbom(args):
    from aicowork.conform import evidence
    doc = evidence.sbom(_base(args))
    text = json.dumps(doc, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out} ({len(doc['components'])} components)")
    else:
        print(text)
    return 0


def register(add):
    p = add("conform", cmd_conform, "run the conformance suite (alias: lint)")
    p.add_argument("--level", type=int, default=2, choices=[1, 2])
    p.add_argument("--case", help="score an L3 case after an agent ran: L3-TRIAGE, L3-BRIEF, L3-WEEKLY, L3-REDTEAM")
    p.add_argument("--since", help="commit before the agent ran (for --case)")
    p.add_argument("--report", action="store_true", help="write 06_logs/conformance/<date>_<level>.md")
    p.add_argument("--quiet", action="store_true", help="print errors only")
    p = add("audit", cmd_audit, "check what changed since a commit against the session rules")
    p.add_argument("--since", required=True)
    p.add_argument("--task", choices=["triage", "brief", "weekly"])
    p.add_argument("--allow", action="append", metavar="GLOB", help="owner-acknowledged path (repeatable)")
    p = add("doctor", cmd_doctor, "health of this instance")
    p.add_argument("--quick", action="store_true")
    p = add("reach", cmd_reach, "what the connected folder exposes to the model")
    p.add_argument("--json", action="store_true")

    p = add("manifest", cmd_manifest, "verify (or --write) MANIFEST.sha256 of kernel, hosts and tools")
    p.add_argument("--write", action="store_true")
    p = add("anchor", cmd_anchor, "record commit + manifest hashes outside the folder (trust anchor; owner, on the host)")
    p.add_argument("--here", action="store_true",
                   help="this IS the owner's host, though the folder looks mounted (override the refusal)")

    p = add("verify", cmd_verify, "the gate: conformance, manifests, receipts, tests")
    p.add_argument("--fast", action="store_true", help="skip the test suite")
    p.add_argument("--allow-instance", action="store_true", help="do not fail on the owner's instance findings")
    p = add("audit-pack", cmd_audit_pack, "evidence folder for an InfoSec review (hashed)")
    p.add_argument("--out", metavar="DIR")
    p.add_argument("--no-tests", action="store_true")
    p = add("sbom", cmd_sbom, "CycloneDX SBOM of the tools (from uv.lock + vendored JS)")
    p.add_argument("--out", metavar="FILE")
