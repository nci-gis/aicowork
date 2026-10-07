---
type: decision
date: 2026-10-02
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, licence, release]
source: owner, in session 2026-10-02
---

# Licences per ring; the instance carries none

## Decision (owner)

- The kernel (`99_system/`), the host adapters (`hosts/`) and the reference tools (`98_tools/`, with launchers and hooks) are each **MIT**, with a `LICENSE` file inside the ring folder. Copyright line: "AI-Cowork contributors".
- This repository is a private instance: **no licence** at its root. The release artifacts get their ring's licence at their root (`package`), so a published zip is never unlicensed.
- Third-party: the vendored Apache ECharts keeps Apache-2.0 (NOTICE.md, THIRD_PARTY_LICENSES.md).

Supersedes the "tools licence pending" state of `2026-10-01_licence-signoff-and-private-instance.md`.
