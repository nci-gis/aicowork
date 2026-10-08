---
type: decision
date: 2026-10-08
status: decided
claim: stance
tags: [aicowork, apps, viewer, surface, egress, rc.5]
source: owner, 2026-10-06 (plan 2 for rc.4, item P7); written by the agent on the owner's delegation, 2026-10-08
---

# aicowork is the kernel, a host and the viewer; everything else is an app registered by link

## Decision (owner)

**aicowork = kernel + host + viewer.** Nothing else is part of it.

- The **kernel** (`99_system/`) states what must hold, in text.
- A **host** (`hosts/<host>.md`) is where the agent runs; it reads the folder and follows the kernel's skills.
- The **viewer** (`98_tools/apps/viewer/`) is the owner's window on the folder: loopback only, per-launch session, read mostly; its few writes (Done on a reminder, quick-add, a triage plan applied) are the owner's clicks and are audited.

**Everything else is an app, registered by link** under `apps:` in `aicowork.yaml` (id, name, kind, target, circle; from rc.6 a `command:` for a `service`). An app is not part of aicowork: the kernel does not describe it, conformance does not judge it, the viewer only shows its tile and opens its target.

Two rules follow for any app or surface:

1. **Reading is a surface.** An app that reads the folder is an AI surface or a tool like any other: it is named under `ai_surfaces:` in `policy.yaml` when a model is behind it, and the files it opens are within its reach (CONVENTIONS "Reach").
2. **Writing is audited.** An app that writes into the folder writes notes like an agent does: valid frontmatter, `visibility: private`, `created_by`, and `source: app:<id>`; `aicowork audit` sees the change like any other, and the leak and ambiguity gates apply before anything leaves.

## Why

Plan 2 for rc.4 asked where the viewer ends and where "a tool that uses the folder" begins. Without a line, every useful program drifts into the kernel (word budget, conformance cases, a host page) or into the viewer (a growing single app). With the line, the kernel stays a specification, the viewer stays one window, and the folder stays the contract that every app writes against.

## Consequences

- rc.6 adds `apps` kind `service` with `command:` and `aicowork app <id>` (started from the owner's terminal, never by an agent), and the `source: app:<id>` convention.
- A triage plan applied from the viewer is a viewer write: audited, same rules as `aicowork triage --apply`.
- A future app that needs a kernel rule is a sign the rule belongs to the kernel, not that the app does.

## Revisit when

- an app needs to write outside the frontmatter contract;
- a second viewer appears (then "the viewer" is a host-contract item, not a program).
