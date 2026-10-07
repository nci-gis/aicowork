---
type: decision
date: 2026-10-01
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, v0.0.1, kernel]
source: .agents/plan/v0.0.1-plan.md
---

# Viewer security model — loopback only, per-launch session, live edit kept

## Context

The 09/14 review rebuttal showed one exploit chain: no Host check (DNS rebinding) + path traversal on save + stored XSS. The owner wants live edit kept.

## Decision

The viewer binds to loopback only and refuses to start otherwise (no auth — the not-do list — so it must never face a network). Every request passes a guard: Host allow-list (421), per-launch session cookie set by the launch URL (401), same-origin JSON for writes (403/415). Paths go through `safe_path` (resolve, redirect detection, Windows name rules, roots after resolution). Markdown: raw HTML escaped, URL schemes allow-listed, no remote images, snippets escaped, no inline handlers, strict CSP. Live edit: `.md` in editable roots only, 1 MB cap, atomic write, mtime guard; kernel docs are readable, never editable.

## Why

Close the chain at every link; keep the one feature the owner uses daily.

## Revisit when

Anyone needs the viewer from another device — that needs real auth, which the not-do list forbids today.
