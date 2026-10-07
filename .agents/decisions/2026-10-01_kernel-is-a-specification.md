---
type: decision
date: 2026-10-01
status: decided
revisit: 2026-12-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
supersedes: 09_decisions/2026-08-28_kernel-vs-instance-boundary.md (the ring boundary only)
---

# The kernel is a specification, not software

## Context

The 28/08 ADR drew the kernel as `99_system/ + 98_tools/`. Planning v0.0.1 showed that this made "a proper AI-Cowork" mean "runs our Python", which ties the idea to one implementation and, through the tools, to one kind of host.

## Options considered

1. Keep kernel = docs + tools. 2. Kernel = docs only, tools a separate optional ring, conformance defines "proper". 3. Kernel = tools, docs as README.

## Decision

Option 2. Four rings: kernel (`99_system/`), reference implementation (`98_tools/`, versioned separately as `aicowork-tools`), host adapters (`hosts/` at the root — moved out of `99_system/` 2026-10-01 after review, see Addendum; the root instruction file), instance (never public). Membership test in PHILOSOPHY "The kernel". Conformance suite (L1 shape, L2 rules, L3 behaviour) defines "proper". The kernel's own development notes live in `.agents/` (no ring, never shipped).
**Signed off by the owner 2026-10-01**: the PHILOSOPHY text "The kernel" and principle #12 "claims need evidence", each as its own decision (as the review proposed), before any merge of `dev`.

## Why

With the kernel anyone can rebuild a proper AI-Cowork on any host with any model, and any tool that passes conformance is equally valid. That is the property no other tool on the market offers; binding the kernel to our code would give it away.

## Revisit when

2026-12-01, or when a second implementation or a second host exists.

## Addendum 2026-10-01 — host adapters leave `99_system/`

Review `05_results/2026-10/2026-10-01_v0.0.1-plan-review.md` finding 3: a folder named by the kernel but failing membership criterion 1 (host-independent) made the ring boundary depend on an exclusion list in the tools. `hosts/` is now a top-level folder with its own `MANIFEST.sha256`; the kernel ring is all of `99_system/` minus fixtures. Shipping `hosts/` inside the kernel zip (inventory Q2) stays the draft answer and remains the owner's call.
