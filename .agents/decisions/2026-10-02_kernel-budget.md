---
type: decision
date: 2026-10-02
status: decided
revisit: 2027-01-01
claim: stance
tags: [aicowork, kernel, budget]
source: owner, in session 2026-10-02 (plan A6)
---

# Kernel budget: prose ≤ 10,000 words; machine files exempt

## Context

The budget was 12,000 words over all kernel files. After the kernel became English-only it stood at 11,161, of which ~9,650 were prose (CONVENTIONS 2,351 · skills 1,958 · REBUILD 1,195 · PHILOSOPHY 1,188 · conformance 1,130 · templates 585 · host contract 431 · instruction file 347 · tasks 239 · modules) and ~1,516 machine-read (schemas 926 · presets 364 · example config 226).

## Decision

The budget measures what it is for — a person reading the kernel in one sitting: **Markdown under `99_system/` (fixtures and READMEs excluded) ≤ 10,000 words.** Schemas, presets and the example config are not counted; conformance validates them. `aicowork conform` (L2-BUDGET) enforces it. Growing past it needs a new decision entry.

Options not taken: keep 12,000 over everything (counts JSON as reading); raise to 15,000 (room for 0.0.2, but the kernel drifts away from the fixed point's reader).

## Consequence

Headroom is about 400 words (9,584 at the decision). The next sizeable kernel addition (a language module's rules, team mode) must cut elsewhere first — CONVENTIONS and the skills are the largest.

## Addendum (owner, 2026-10-03, before rc.3)

The budget counts the kernel's **documents** only — the five files `99_system/README.md` lists as what the kernel answers: `PHILOSOPHY.md` (why), `CONVENTIONS.md` (what), `REBUILD.md` (how), `conformance/SUITE.md` (what "proper" means) and `host-contract.md` (what a host must provide). The instruction file, skills, tasks, templates and modules are not counted; neither are machine-read files. The limit stays 10,000 words. At this addendum the five documents hold about 6,660 words (the old count, over all kernel Markdown, was 9,981).

Later the same day the owner added the instruction file: every session reads it first, so it is counted too, and `99_system/README.md` lists the six documents the budget counts. The `modules.lock` ordering sentence was made exact in the same change (kernel safety audit, row 12).
