---
type: decision
date: 2026-10-01
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
---

# Retention — archive by default, human-only purge

## Context

"Never delete" conflicts with erasure duties (a person's request, a legal requirement).

## Decision

Never delete stays the rule for everyone, including agents: archive to `07_archive/`. `expires` / `review_by` feed a retention report. True erasure is `aicowork purge`: human-only (refuses without an interactive terminal), removes one file, appends a tombstone with hashes only to `06_logs/purge/`. Every place that promises erasure says that git history and old backups keep the content until rotated.

## Why

Keep the audit trail whole, and still be able to honour a real erasure duty, deliberately.

## Revisit when

A legal review requires history rewriting or backup rotation procedures.
