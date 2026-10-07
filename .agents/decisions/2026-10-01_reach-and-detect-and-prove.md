---
type: decision
date: 2026-10-01
status: decided
revisit: 2026-12-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
---

# Reach is the boundary; the kernel detects and proves

## Context

Research on the first host (Claude Cowork) showed that folder-level permission files and hooks are not dependable there, that real controls are set by IT, and that file contents the agent opens are processed by the model provider.

## Decision

1. **Reach**: whatever sits in the connected folder can reach the model. `policy.yaml` lists approved AI surfaces with the highest visibility each may read; `aicowork reach` reports against them; material that must not reach a model stays outside the folder; every public statement names the model call as the egress.
2. **Detect and prove**: the kernel prevents what it owns (egress through the policy, plan-then-apply, never-delete, loopback viewer) and otherwise states what the host must enforce (`hosts/<host>-hardening.md`) and checks afterwards (`audit`, manifests, trust anchor, receipts). It never ships host permission files as a primary control.

## Why

Honest claims, and controls that survive a change of host.

## Revisit when

A host honours folder-level controls reliably (host spike) — they become a bonus, never the primary control.
