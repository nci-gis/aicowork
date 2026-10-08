# -*- coding: utf-8 -*-
"""Egress gate: policy validation, backup, export, hash-chained receipts.
Stdlib only. Spec: CONVENTIONS "Visibility & egress".

Execution is a pure function of the written policy (PHILOSOPHY #11): nothing
here guesses. A policy that does not validate stops every command.
"""
import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from aicowork_core import ambiguity as A
from aicowork_core.contract import is_archived_kernel
from aicowork_core import common as C
from aicowork_core.contract import CIRCLES

ACCEPTS_MIN_RANK = {"public": 0, "internal": 1, "all": 2}    # highest sensitivity accepted
RECEIPTS = "receipts.jsonl"


class PolicyError(RuntimeError):
    pass


def validate_policy(pol, base=None):
    """Strict check against schemas/policy.schema.json. -> list of errors."""
    errs = []
    if not isinstance(pol, dict):
        return ["policy must be a mapping"]
    allowed = {"schema", "preset", "decided", "distribution", "never_export", "destinations", "ai_surfaces", "remotes", "compliance"}
    for k in pol:
        if k not in allowed:
            errs.append(f"unknown key '{k}'")
    for k in ("schema", "preset", "destinations", "ai_surfaces"):
        if k not in pol:
            errs.append(f"missing '{k}'")
    if pol.get("schema") != 1:
        errs.append("schema must be 1")
    if pol.get("preset") not in ("corporate-strict", "personal-simple"):
        errs.append("preset must be corporate-strict or personal-simple")
    if "decided" in pol and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(pol["decided"])):
        errs.append("decided must be YYYY-MM-DD")
    ids = set()
    for d in pol.get("destinations") or []:
        if not isinstance(d, dict):
            errs.append("each destination must be a mapping")
            continue
        extra = set(d) - {"id", "kind", "path", "accepts", "below", "allow_circles", "note"}
        if extra:
            errs.append(f"destination {d.get('id')}: unknown keys {', '.join(sorted(extra))}")
        for k in ("id", "kind", "path", "accepts", "below"):
            if not d.get(k):
                errs.append(f"destination {d.get('id', '?')}: missing '{k}'")
        if d.get("id") in ids:
            errs.append(f"duplicate destination id {d.get('id')}")
        ids.add(d.get("id"))
        if d.get("kind") not in ("backup", "export"):
            errs.append(f"destination {d.get('id')}: kind must be backup or export")
        if d.get("accepts") not in ACCEPTS_MIN_RANK:
            errs.append(f"destination {d.get('id')}: accepts must be public, internal or all")
        if d.get("below") not in ("drop", "encrypt"):
            errs.append(f"destination {d.get('id')}: below must be drop or encrypt")
        for c in d.get("allow_circles") or []:
            if c not in CIRCLES:
                errs.append(f"destination {d.get('id')}: unknown circle {c}")
        if base and d.get("path") and not foreign_path(d["path"]):
            p = dest_path(base, d)
            if p == Path(base).resolve() or Path(base).resolve() in p.parents:
                errs.append(f"destination {d.get('id')}: path is inside the folder")
        if pol.get("preset") == "corporate-strict" and d.get("kind") == "export" and d.get("accepts") == "all":
            errs.append(f"destination {d.get('id')}: corporate-strict forbids exporting everything")
    for s in pol.get("ai_surfaces") or []:
        if not isinstance(s, dict) or not s.get("id") or s.get("max_visibility") not in ("private", "internal", "public", "none"):
            errs.append("each ai_surface needs id and max_visibility (private|internal|public|none)")
    dist = pol.get("distribution", "private")
    if dist not in ("private", "controlled"):
        errs.append("distribution must be private or controlled")
    elif dist == "private":
        if pol.get("remotes"):
            errs.append("distribution: private forbids git remotes (remotes must be empty)")
        for d in pol.get("destinations") or []:
            if isinstance(d, dict) and d.get("kind") == "export":
                errs.append(f"destination {d.get('id')}: distribution: private forbids export destinations")
    comp = pol.get("compliance")
    if comp is not None:
        if not isinstance(comp, dict) or set(comp) - {"prohibited_markers"}:
            errs.append("compliance: only `prohibited_markers` is allowed")
        elif not all(isinstance(m, str) and len(m) >= 2 for m in comp.get("prohibited_markers") or []):
            errs.append("compliance.prohibited_markers: each marker is a string of 2+ characters")
    for key in ("never_export", "remotes"):
        if key in pol and not isinstance(pol[key], list):
            errs.append(f"{key} must be a list")
    return errs


def load_policy(base):
    pol, err = C.load_yaml(Path(base) / "policy.yaml")
    if err:
        raise PolicyError(f"{err} — egress refuses to run without a valid policy")
    errs = validate_policy(pol, base)
    if errs:
        raise PolicyError("policy.yaml is invalid — egress refuses to run:\n  " + "\n  ".join(errs))
    return pol


def foreign_path(raw):
    """True for a Windows absolute path (D:\\x, D:/x, \\\\server\\share) seen from a
    non-Windows process — e.g. an agent VM reading the owner's policy. Such a
    destination cannot be inside a POSIX folder, and cannot be written from here."""
    s = str(raw)
    win = bool(re.match(r"^[A-Za-z]:[\\/]", s)) or s.startswith("\\\\")
    return win and sys.platform != "win32"


def distribution(pol):
    """private unless the policy says controlled (fail-closed)."""
    return "controlled" if (pol or {}).get("distribution") == "controlled" else "private"


def require_decided(pol, base=None):
    """PHILOSOPHY #11: an egress runs only against a policy the owner decided — and
    (CONVENTIONS "Visibility & egress") only while that policy still matches the
    owner's trust anchor: a `decided:` line an agent can keep while rewriting the
    rest of the file is not a decision."""
    if not pol.get("decided"):
        raise PolicyError("policy.yaml is undecided — the owner adds `decided: YYYY-MM-DD` once, "
                          "deliberately; egress refuses until then")
    if base is not None:
        from aicowork_core.anchor import egress_bound_problem
        problem = egress_bound_problem(base)
        if problem:
            raise PolicyError(f"policy.yaml is not bound: {problem}")


def dest_path(base, d):
    if foreign_path(d["path"]):
        raise PolicyError(f"destination {d.get('id')}: {d['path']} is a Windows path — "
                          "run this on the Windows host, not from a sandbox")
    p = Path(str(d["path"]).replace("\\", "/"))
    return (p if p.is_absolute() else Path(base) / p).resolve()


def destination(pol, dest_id, kind):
    for d in pol.get("destinations") or []:
        if d.get("id") == dest_id:
            if d.get("kind") != kind:
                raise PolicyError(f"destination {dest_id} is a {d.get('kind')} destination, not {kind}")
            return d
    listed = ", ".join(d["id"] for d in pol.get("destinations") or [] if d.get("kind") == kind) or "none"
    raise PolicyError(f"no {kind} destination '{dest_id}' in policy.yaml (listed: {listed})")

# ---------------- receipts ----------------

def _receipts_file(base):
    return Path(base) / "06_logs" / "egress" / RECEIPTS


def _entries(base):
    f = _receipts_file(base)
    if not f.is_file():
        return []
    return [json.loads(l) for l in C.read(f).splitlines() if l.strip()]


def receipts_head(base):
    e = _entries(base)
    return e[-1]["hash"] if e else None


def receipt_in_chain(base, h):
    return any(x.get("hash") == h for x in _entries(base))


def _hash_entry(entry):
    body = {k: v for k, v in entry.items() if k != "hash"}
    return C.sha256_text(json.dumps(body, sort_keys=True, ensure_ascii=False))


def append_receipt(base, record, summary_lines):
    """Append-only, hash-chained JSONL + a human-readable Markdown page."""
    f = _receipts_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(record, prev_hash=receipts_head(base), ts=dt.datetime.now().isoformat(timespec="seconds"))
    entry["hash"] = _hash_entry(entry)
    with open(f, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    name = f"{C.today().isoformat()}_{record['action']}_{record['dest']}_{entry['hash'][:8]}.md"
    C.write_report(base, "egress", name, f"Egress receipt — {record['action']} → {record['dest']}",
                   summary_lines + ["", f"hash: `{entry['hash']}`", f"prev: `{entry['prev_hash']}`"])
    return entry


def verify_receipts(base):
    """-> list of problems; empty = chain intact."""
    out, prev = [], None
    for i, e in enumerate(_entries(base), 1):
        if e.get("prev_hash") != prev:
            out.append(f"entry {i}: prev_hash does not match entry {i - 1}")
        if _hash_entry(e) != e.get("hash"):
            out.append(f"entry {i}: content does not match its hash")
        prev = e.get("hash")
    return out

# ---------------- backup ----------------

def backup(base, dest_id, dry_run=False):
    base = Path(base)
    pol = load_policy(base)
    d = destination(pol, dest_id, "backup")
    target_dir = dest_path(base, d)
    if not C.is_git(base):
        raise PolicyError("backup needs a git repository (it writes a git bundle)")
    rc, head = C.git(base, "rev-parse", "HEAD")
    out = target_dir / f"aicowork-{C.today().isoformat()}-{head.strip()[:8]}.bundle"
    # a dry run runs every gate the real run runs; it differs only in writing nothing
    require_decided(pol, base)
    if dry_run:
        return {"dest": dest_id, "file": str(out), "dry_run": True}
    target_dir.mkdir(parents=True, exist_ok=True)
    rc, msg = C.git(base, "bundle", "create", str(out), "--all")
    if rc:
        raise PolicyError(f"git bundle failed: {msg}")
    rc, msg = C.git(base, "bundle", "verify", str(out))
    if rc:
        raise PolicyError(f"bundle does not verify: {msg}")
    sha = C.sha256_file(out)
    entry = append_receipt(base, {"action": "backup", "dest": dest_id, "commit": head.strip(),
                                  "file": out.name, "sha256": sha, "policy_decided": pol.get("decided")},
                           [f"- destination: `{dest_id}` ({target_dir})", f"- bundle: `{out.name}`",
                            f"- sha256: `{sha}`", f"- commit: `{head.strip()}`",
                            "- verified with `git bundle verify`"])
    return {"dest": dest_id, "file": str(out), "sha256": sha, "receipt": entry["hash"]}

# ---------------- export ----------------

def _export_candidates(base, pol):
    base = Path(base)
    never = list(C.NEVER_EXPORT) + list(pol.get("never_export") or [])
    for p in sorted(base.rglob("*.md")):
        if p.is_symlink():
            continue                        # CONVENTIONS "Reach": never followed
        r = C.rel(base, p)
        top = r.split("/")[0]
        if top not in C.EDITABLE_ROOTS or p.name in C.SKIP_NAMES or is_archived_kernel(r):
            continue                        # archived kernel text is not a note: it never leaves
        if C.any_match(r, never):
            continue
        yield p, r


def plan_export(base, dest_id, max_visibility=None, only_private=False, with_sealed=False):
    """-> (dest, selected[(path, rel, vis)], skipped[(rel, reason)]); with
    with_sealed=True also sealed[(path, rel, vis)]: files above the destination's
    level that `below: encrypt` sends sealed instead of dropping them."""
    pol = load_policy(base)
    if distribution(pol) == "private":
        raise PolicyError("distribution: private — this instance is never published; export refuses")
    d = destination(pol, dest_id, "export")
    limit = ACCEPTS_MIN_RANK[d["accepts"]]
    if max_visibility:
        limit = min(limit, C.VIS_RANK[max_visibility])          # may only tighten
    if only_private and d["accepts"] != "all":
        raise PolicyError(f"--only private needs a destination that accepts all (this one accepts {d['accepts']})")
    circles = d.get("allow_circles")
    selected, skipped, sealed = [], [], []
    for p, r in _export_candidates(base, pol):
        meta, _, _ = C.frontmatter(p)
        vis = C.visibility(meta)
        if meta.get("circle") not in C.CIRCLES:
            skipped.append((r, "missing or invalid circle"))
        elif circles and meta.get("circle") not in circles:
            skipped.append((r, f"circle {meta.get('circle')} not allowed"))
        elif only_private and vis != "private":
            skipped.append((r, "not private"))
        elif not only_private and C.VIS_RANK[vis] > limit:
            if d.get("below") == "encrypt":
                sealed.append((p, r, vis))
            else:
                skipped.append((r, f"visibility {vis} above what the destination accepts"))
        else:
            selected.append((p, r, vis))
    if with_sealed:
        return d, selected, skipped, sealed
    return d, selected, skipped


# frontmatter keys that may leave with an exported note; everything else
# (source paths, provenance, roles, cadence, tags, check_tokens, …) stays home
EXPORT_KEYS = ("type", "visibility", "circle", "date", "time", "status", "claim")
FM_RX = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def reduce_frontmatter(text):
    """Keep only EXPORT_KEYS in a note's frontmatter (mechanical, line-based:
    a key's nested lines go with it). -> (text, dropped key count)."""
    m = FM_RX.match(text)
    if not m:
        return text, 0
    keep, dropped, keeping = [], 0, False
    for line in m.group(1).split("\n"):
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if km:
            keeping = km.group(1) in EXPORT_KEYS
            dropped += 0 if keeping else 1
        if keeping or (not km and line.startswith((" ", "\t")) and keeping):
            keep.append(line)
    return "---\n" + "\n".join(keep) + "\n---\n" + text[m.end():], dropped


def prohibited_markers(pol):
    return list(((pol or {}).get("compliance") or {}).get("prohibited_markers") or [])


def marker_hits(base, pol=None, roots=None):
    """Files in the content folders that contain a prohibited marker (exact,
    case-sensitive). The inbox is included: a stamped document must be reported
    the moment it lands. -> [(rel, marker)]."""
    base = Path(base)
    if pol is None:
        pol = C.load_yaml(base / "policy.yaml")[0] or {}
    markers = prohibited_markers(pol)
    if not markers:
        return []
    hits = []
    for top in roots or sorted(set(C.EDITABLE_ROOTS) | {"00_inbox"}):
        d = base / top
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.is_symlink() or p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".db"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in markers:
                if m in text:
                    hits.append((C.rel(base, p), m))
                    break
    return hits


def content_scan(base, files):
    """The release leak gate's scanners, over what is about to be exported:
    the automatic deny-list (owner, org, personas, projects) and the generic
    patterns (e-mails, secrets, machine paths). -> [(rel, message)]."""
    from aicowork_core import scan
    base = Path(base)
    tokens, _ = C.deny_list(base, projects=False)
    if tokens is None:
        return [("03_personas/me.md", (C.owner_file_problem(base) or "owner file unreadable") + " — the content scan fails closed")]
    with tempfile.TemporaryDirectory() as td:
        for r, text in files:
            p = Path(td) / r
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="\n")
        paths = {str(base), base.as_posix()}
        if C.folder_name_token(base):
            paths.add(C.folder_name_token(base))
        hits = scan.scan_tokens(td, tokens, paths) + scan.scan_generic(td)
    return hits


def private_blocks(text):
    """The private blocks of a note, markers included. Markers outside the
    grammar (nesting, orphans, lookalikes) -> ValueError (ambiguity.Ambiguous)."""
    return [text[a:b] for a, b in A.private_spans(text)]


def strip_private(text):
    """Remove private blocks mechanically. -> (text, count). Markers outside the
    grammar -> ValueError: a block that cannot be found exactly is never guessed at."""
    spans = A.private_spans(text)
    out, pos = [], 0
    for a, b in spans:
        out += [text[pos:a], A.PLACEHOLDER]
        pos = b
    return "".join(out) + text[pos:], len(spans)


def ambiguity_hits(base, pol):
    """Every ambiguity in the notes an export considers (selected or not): one
    refuses the whole export, so nothing is read two ways on the way out. -> [str]."""
    classes = A.load_classes(C.kernel_dir(base))
    return [f"{r}: {A.advice(p, classes)}" for path, r in _export_candidates(base, pol)
            for p in A.problems(C.read(path))]


def export(base, dest_id, max_visibility=None, only_private=False, dry_run=False, allow=(), passphrase_file=None):
    """Export through the gate. Every file is reduced (frontmatter), stripped
    (private blocks) and then SCANNED; a hit refuses the whole export unless the
    owner named that file in `allow` — and then the hit is written into the
    receipt. Nothing leaves silently."""
    base = Path(base)
    d, selected, skipped, sealed = plan_export(base, dest_id, max_visibility, only_private, with_sealed=True)
    pol_ = load_policy(base)
    unclear = ambiguity_hits(base, pol_)
    if unclear:
        raise PolicyError("a note can be read two ways — nothing was exported; fix each one "
                          "(99_system/conformance/ambiguity.json):\n  " + "\n  ".join(unclear))
    # a prohibited marker never leaves — not in plain text, not sealed, not inside a
    # private block: the whole original file is checked, before anything is stripped
    stamped = [(r, f"prohibited marker {m!r}") for p, r, _ in selected + sealed
               for m in prohibited_markers(pol_) if m in C.read(p)]
    if stamped:
        raise PolicyError("a file carries a prohibited marker — it must not be in this folder, let alone leave it:\n  "
                          + "\n  ".join(f"{r}: {m}" for r, m in stamped))
    encrypt = d.get("below") == "encrypt"
    out_dir = dest_path(base, d) / f"aicowork-export-{dt.datetime.now():%Y%m%d-%H%M%S}"
    require_decided(pol_, base)          # a dry run too: it must tell the truth about the real run
    files, blocks, dropped_total, sidecars = [], 0, 0, []
    for p, r, vis in selected:
        raw = C.read(p).replace("\r\n", "\n")    # one line ending: reduce_frontmatter reads \n fences
        try:
            text, n = strip_private(raw)
        except ValueError as e:
            raise PolicyError(f"{r}: {e} — fix the file; nothing was exported")
        if encrypt and n:
            sidecars.append((r, "\n\n".join(private_blocks(raw))))
        text, dropped = reduce_frontmatter(text)
        files.append((r, vis, text, n, dropped))
        blocks += n
        dropped_total += dropped
    hits = content_scan(base, [(r, t) for r, _, t, _, _ in files])
    allowed = {h for h in hits if h[0] in set(allow)}
    blocking = [h for h in hits if h not in allowed]
    if dry_run:
        return {"dest": dest_id, "out": str(out_dir), "files": [(r, v, n) for r, v, _, n, _ in files],
                "skipped": skipped, "hits": hits, "blocking": blocking, "dropped_keys": dropped_total,
                "sealed": [r for _, r, _ in sealed], "sidecars": [r for r, _ in sidecars], "dry_run": True}
    if blocking:
        raise PolicyError("content scan found what must not leave — nothing was exported:\n  "
                          + "\n  ".join(f"{r}: {m}" for r, m in blocking)
                          + "\n  (fix the file, or name it with --allow <path> to export it anyway; the hit is then recorded in the receipt)")
    blobs = []
    if encrypt and (sealed or sidecars):
        # everything is sealed in memory BEFORE anything is written: no half-export
        from aicowork.egress import seal as S
        try:
            pw = S.passphrase(base, passphrase_file)
            for p, r, vis in sealed:
                blobs.append((r + S.SUFFIX, S.seal(C.read(p).encode("utf-8"), pw, r), "file", vis))
            for r, text in sidecars:
                blobs.append((r + ".private" + S.SUFFIX, S.seal(text.encode("utf-8"), pw, r + ".private"), "private-blocks", "private"))
        except S.SealError as e:
            raise PolicyError(f"below: encrypt — {e}")
    manifest = []
    for r, vis, text, n, dropped in files:
        target = out_dir / r
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        manifest.append({"path": r, "visibility": vis, "sha256": C.sha256_text(text), "stripped_blocks": n,
                         "dropped_keys": dropped, "allowed_hits": [m for rr, m in allowed if rr == r]})
    for name, blob, kind, vis in blobs:
        target = out_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        manifest.append({"path": name, "visibility": vis, "sealed": kind,
                         "sha256": hashlib.sha256(blob).hexdigest()})
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    pol = load_policy(base)
    # the report layer (L2-HIDDEN): what left with characters a person cannot see — allowed, never silent
    from aicowork_core.scan import hidden_chars
    hidden = {r: len(hidden_chars(C.read(p))) for p, r, _ in selected if hidden_chars(C.read(p))}
    entry = append_receipt(base, {"action": "export", "dest": dest_id, "accepts": d["accepts"], "below": d["below"],
                                  "hidden_char_warnings": sum(hidden.values()), "hidden_char_files": sorted(hidden),
                                  "max_visibility": max_visibility, "only_private": only_private,
                                  "count": len(manifest), "skipped": len(skipped), "stripped_blocks": blocks,
                                  "files": manifest, "policy_decided": pol.get("decided"),
                                  "allowed_hits": sorted(allowed), "sealed": len(blobs),
                                  "kdf": "scrypt n=32768 r=8 p=1, AES-256-GCM" if blobs else None},
                           [f"- destination: `{dest_id}` ({out_dir})",
                            f"- mode: accepts `{d['accepts']}`, below `{d['below']}`"
                            + (f", tightened to `{max_visibility}`" if max_visibility else ""),
                            f"- exported: {len(manifest)} files, {blocks} private blocks stripped, {dropped_total} frontmatter keys dropped",
                            f"- content scan: {len(hits)} hit(s), {len(allowed)} allowed by the owner by name"
                            + ("".join(f"\n  - `{r}` — {m}" for r, m in sorted(allowed)) if allowed else ""),
                            f"- sealed (owner's passphrase; not content-scanned): {len(blobs)} file(s)",
                            f"- hidden characters: {sum(hidden.values())} in {len(hidden)} file(s)"
                            + ("".join(f"\n  - `{r}`: {n}" for r, n in sorted(hidden.items())) if hidden else ""),
                            f"- skipped: {len(skipped)} files", "", "| file | visibility | sha256 |", "|---|---|---|"]
                           + [f"| {m['path']} | {m['visibility']} | `{m['sha256'][:16]}` |" for m in manifest])
    return {"dest": dest_id, "out": str(out_dir), "count": len(manifest), "receipt": entry["hash"],
            "hidden_char_warnings": sum(hidden.values()), "hidden_char_files": sorted(hidden)}
