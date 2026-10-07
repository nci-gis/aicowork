---
type: decision
date: 2026-10-01
status: decided
revisit: 2026-12-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
supersedes: 09_decisions/2026-08-28_kernel-vs-instance-boundary.md (non-goal 'no repo split')
---

# Public kernel repo with fresh history; two release artifacts

## Context

The 28/08 ADR deferred a repo split until two users edited the kernel. The owner has now decided to publish the kernel as open source — while this repository's history holds personal, family and work material.

## Decision

The public repository is built from release artifacts, **never** from this repository's history. Each release produces `aicowork-kernel-<v>.zip` (specification only; the build refuses if it would contain code) and `aicowork-tools-<v>.zip`; both pass two leak scanners on the built zip; the build fails closed without `03_personas/me.md`. This instance consumes new kernels through `aicowork upgrade` (bundle first, removed files archived, instance files untouched). A pre-push hook refuses any remote not listed in `policy.yaml`.
Publication itself waits for gate G1. Licence decided 2026-10-01: the kernel and host adapters are **MIT**; the reference tools' licence is still pending.

## Why

"Only the kernel is public, never the data" has to be a mechanism, not a promise.

## Revisit when

After the first public release, or if a second maintainer needs the kernel history.

## Addendum (owner, 2026-10-08, at 0.0.1-rc.4)

**The development repository itself becomes the public repository** (`nci-gis/ai-cowork`), with the same layout (`.agents/`, `90_devkit/` included) and a history that starts again from one commit of the rc.4 tree. The reason for building the public repository from artifacts only was that the kernel then lived inside the owner's instance, whose history held private material; since 2026-10-01 the kernel has had its own repository with no owner data (every commit and push leak-scanned, C32), so that reason no longer holds. What stays: instances consume release artifacts through `aicowork upgrade` and never push to the kernel repository (pre-push); the zips still carry no `.agents/` or history; the deny-list for `package` still comes from a private instance, never from the repository. What changes: `leakscan` runs the generic patterns alone when no private instance is named (the repository legitimately contains the example instance's fictional names), so a contributor's commit hooks run; the repository root carries `LICENSE` (MIT) and the full artifact takes it. The old development repository is bundled to the owner's backup destination and archived, not deleted.
