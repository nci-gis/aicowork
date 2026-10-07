# -*- coding: utf-8 -*-
"""`aicowork audit-pack` — one folder of evidence for an InfoSec / MIS review
(for an independent reviewer). Every file is plain text; MANIFEST.sha256 at the end makes the pack
tamper-evident. Nothing here claims compliance: it maps evidence to controls."""
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from aicowork.conform import checks
from aicowork_core import common as C
from aicowork.egress import gate as egress
from aicowork_core import manifest
from aicowork.instance import ops


def sbom(base):
    """CycloneDX 1.5 JSON from 98_tools/uv.lock (the tools workspace) + the vendored JS."""
    base = Path(base)
    lock = C.read(base / "98_tools" / "uv.lock")
    comps = []
    for block in lock.split("[[package]]")[1:]:
        name = re.search(r'^name = "([^"]+)"', block, re.M)
        ver = re.search(r'^version = "([^"]+)"', block, re.M)
        if not name or not ver or name.group(1) == "aicowork-tools":
            continue
        hashes = re.findall(r'hash = "sha256:([0-9a-f]{64})"', block)
        comps.append({"type": "library", "name": name.group(1), "version": ver.group(1),
                      "purl": f"pkg:pypi/{name.group(1)}@{ver.group(1)}",
                      "hashes": [{"alg": "SHA-256", "content": h} for h in hashes[:1]]})
    vendor = base / "98_tools" / "apps" / "viewer" / "src" / "viewer" / "web" / "vendor" / "echarts.common.min.js"
    if vendor.is_file():
        comps.append({"type": "library", "name": "echarts", "version": "5.6.1",
                      "purl": "pkg:npm/echarts@5.6.1", "licenses": [{"license": {"id": "Apache-2.0"}}],
                      "hashes": [{"alg": "SHA-256", "content": C.sha256_file(vendor)}]})
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
            "metadata": {"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                         "component": {"type": "application", "name": "aicowork-tools",
                                       "version": C.read(C.kernel_dir(base) / "VERSION").strip()}},
            "components": comps}


def build(base, out=None, run_tests=True):
    base = Path(base)
    out = Path(out or base / "_scratch" / f"audit-pack-{C.today().isoformat()}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    notes = []

    def w(name, text):
        (out / name).write_text(text, encoding="utf-8", newline="\n")

    for src in ("SECURITY.md", "PRIVACY.md", "docs/controls.md", "docs/data-flow.md",
                "docs/dpia-lite.md", "hosts/claude-cowork-hardening.md", "99_system/conformance/SUITE.md"):
        if (base / src).is_file():
            shutil.copy2(base / src, out / Path(src).name)
        else:
            notes.append(f"missing: {src}")
    w("sbom.cdx.json", json.dumps(sbom(base), indent=1))
    f, info = checks.run(base, level=2)
    w("conformance-L2.txt", "\n".join(f"{x.level}\t{x.case}\t{x.path}\t{x.message}" for x in f)
      + f"\n# {len([x for x in f if x.level == 'error'])} errors, kernel {info.get('kernel_words')} words\n")
    w("doctor.txt", "\n".join(f"{lvl}\t{area}\t{msg}" for lvl, area, msg in ops.doctor(base)) + "\n")
    lines = []
    for _, root in C.ring_roots(base):
        if not root.is_dir():
            continue
        probs = manifest.verify(root)
        lines.append(f"{root.name}: {'matches' if not probs else '; '.join(probs[:10])}")
    w("manifests.txt", "\n".join(lines) + "\n")
    probs = egress.verify_receipts(base)
    w("receipts.txt", ("intact\n" if not probs else "\n".join(probs) + "\n")
      + f"entries: {len(egress._entries(base))}\n")
    r = ops.reach(base)
    w("reach.json", json.dumps({k: v for k, v in r.items() if k != "counts"}, indent=1, default=str))
    if (base / "policy.yaml").is_file():
        shutil.copy2(base / "policy.yaml", out / "policy.yaml")
    rc, head = C.git(base, "rev-parse", "HEAD")
    _, logline = C.git(base, "log", "-1", "--format=%H %ad %s", "--date=iso")
    w("provenance.txt", f"commit: {head.strip() if rc == 0 else 'n/a'}\n{logline}\n"
                        f"kernel: {C.read(C.kernel_dir(base) / 'VERSION').strip()}\n"
                        f"python: {sys.version.split()[0]}\nbuilt: {dt.datetime.now().isoformat(timespec='seconds')}\n")
    if run_tests:
        t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            str(base / "98_tools" / "apps" / "aicowork" / "tests")], capture_output=True, text=True)
        w("tests.txt", (t.stdout or "") + (t.stderr or ""))
    w("README.txt", "AI-Cowork audit pack — evidence mapped to controls (docs/controls.md), not a compliance claim.\n"
                    "Every file is listed with its SHA-256 in MANIFEST.sha256.\n" + "".join(f"note: {n}\n" for n in notes))
    mf = "\n".join(f"{C.sha256_file(p)}  {p.name}" for p in sorted(out.iterdir()) if p.is_file())
    w("MANIFEST.sha256", mf + "\n")
    return out, notes
