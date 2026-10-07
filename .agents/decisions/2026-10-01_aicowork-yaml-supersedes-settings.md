---
type: decision
date: 2026-10-01
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
supersedes: 09_decisions/2026-08-27_settings-vs-contract.md (the file format and location only)
---

# aicowork.yaml replaces settings.toml (the contract stays in code)

## Context

The owner asked for one visible config for language, modules and security. `settings.toml` lived inside the kernel folder, although the values are the owner's; `registry.yaml` likewise. The 27/08 ADR rejected YAML because PyYAML is not a dependency.

## Decision

One file `aicowork.yaml` at the instance root (schema in the kernel, example `99_system/aicowork.example.yaml`). Parsed by a small stdlib YAML subset (`98_tools/src/aicowork/yamlite.py`) — no PyYAML, because agent-side tools must run in a host sandbox with no installs. Runtime knobs warn and fall back; `server` and `security` fail closed. Apps move from `registry.yaml` into `apps:`. What the 27/08 ADR got right stays: the contract (circles, folder map, editable roots, never-content names) is not configurable.
Both old files are archived in `07_archive/2026-10-01_*`.

## Why

The owner's choices belong to the instance ring; one file is easier to read and audit; the subset keeps the parser small enough to review.

## Revisit when

A needed setting cannot be expressed in the subset.
