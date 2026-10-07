---
type: decision
date: 2026-10-01
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
---

# Module contract — how frameworks and rituals join

## Context

The Framework Adoption Contract (one folder, two fields, one signal, one prompt) was prose; `7habits` wording was baked into shared templates; extension was "edit the kernel".

## Decision

A module is `99_system/modules/<name>/` with a `module.yaml` (schema in the kernel): provides (templates, template fragments, skills, ≤ 2 fields, ≤ 1 signal, ≤ 1 prompt, lint rules) and permissions (read/write globs). Prose, templates and declarative checks only — no executable code in 0.0.1. Templates wrap module text in `<!-- module:<name> -->` blocks, dropped when the module is off. Instances enable modules in `aicowork.yaml`; `modules.lock` records hashes. Enforcement is **detect**: conformance L2 validates manifests and the signal cap; the audit flags writes outside declared paths. `7habits` is module #1.

## Why

Easy to extend without letting an extension hijack the system (PHILOSOPHY #4, #9).

## Revisit when

A module genuinely needs code — then decide how code modules are trusted.
