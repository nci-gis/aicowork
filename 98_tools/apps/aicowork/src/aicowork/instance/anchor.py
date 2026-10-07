# -*- coding: utf-8 -*-
"""The trust anchor: commit, ring manifest hashes and the egress receipt head,
recorded OUTSIDE the folder on the owner's host, so a later change to the
folder by an agent cannot also rewrite the record it is checked against."""
import json
import os
import sys
from pathlib import Path

from aicowork_core import common as C
from aicowork_core.manifest import manifest_hash
from aicowork_core.anchor import (anchor_dir, anchor_file, foreign_profile, last_anchor,   # noqa: F401
                                  steering_hashes, steering_drift, egress_bound_problem, EGRESS_BOUND)

def anchor(base, here=False):
    """Append the current state to the anchor file outside the folder.
    Refuses when the profile looks foreign (agent VM, remote mount) unless the
    owner passes here=True: an anchor the agent can write proves nothing."""
    base = Path(base)
    reason = foreign_profile(base)
    if reason and not here:
        raise RuntimeError(f"refusing to anchor: {reason}. Run `aicowork anchor` from the owner's own "
                           "terminal on the host the folder lives on (or pass --here if this IS that host).")
    rc, head = C.git(base, "rev-parse", "HEAD")
    from aicowork.egress import gate as egress   # receipts are the app's
    rec = {"date": C.today().isoformat(), "commit": head.strip() if rc == 0 else None,
           "kernel_manifest": manifest_hash(C.kernel_dir(base)),
           "hosts_manifest": manifest_hash(C.hosts_dir(base)),
           "tools_manifest": manifest_hash(base / "98_tools"),
           "receipts_head": egress.receipts_head(base),
           # every file that steers the agent (CONVENTIONS "Visibility & egress")
           "steering": steering_hashes(base)}
    f = anchor_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec) + "\n")
    return f, rec


def check_anchor(base):
    """-> list of (level, message)."""
    base = Path(base)
    a = last_anchor(base)
    reason = foreign_profile(base)
    if a is None:
        if reason:
            return [("warn", f"trust anchor not checkable from here — {reason}; anchors live on the owner's "
                             "host: run `aicowork doctor` there (do not create one from this session)")]
        return [("warn", "no trust anchor yet — run `aicowork anchor` from the owner's own terminal, "
                         f"not from an agent session (stored in {anchor_dir()})")]
    out = []
    if reason:
        out.append(("warn", f"an anchor exists in this profile, but {reason}: it is inside the agent's reach "
                            "and proves nothing — check from the owner's host"))
    if a.get("commit") and C.is_git(base):
        rc, _ = C.git(base, "merge-base", "--is-ancestor", a["commit"], "HEAD")
        if rc == 1:
            out.append(("error", f"anchored commit {a['commit'][:10]} is no longer in history — was history rewritten?"))
    state, drifted = steering_drift(base)
    if state == "legacy":
        out.append(("warn", "the anchor predates the policy binding — run `aicowork anchor` on your own computer; egress refuses until then"))
    for n in drifted:
        out.append(("error" if n in EGRESS_BOUND else "warn",
                    f"{n} changed since the owner anchored it" + (" — egress refuses" if n in EGRESS_BOUND else
                                                                   " — re-anchor if that was you")))
    from aicowork.egress import gate as egress   # receipts are the app's
    head = egress.receipts_head(base)
    if a.get("receipts_head") and head != a["receipts_head"]:
        chain = egress.verify_receipts(base)
        if chain or not egress.receipt_in_chain(base, a["receipts_head"]):
            out.append(("error", "egress receipts changed before the anchored head"))
    return out
