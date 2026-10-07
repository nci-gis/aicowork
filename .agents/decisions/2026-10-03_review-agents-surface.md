---
type: decision
date: 2026-10-03
status: decided
claim: untested
tags: [aicowork, agents, a2scaffold, simplicity]
source: owner, 2026-10-03
review_by: 2026-10-31
---

# Review the `.agents/` surface on 2026-10-31

## Decision (owner)

Adopting a2scaffold added about 23 files to `.agents/`: PDCA, DoD, cycles, promotions, reference, prompts and memory. Every file an agent may load competes with the task for context. Files that nobody uses are reading cost, and they leave room for misreading.

On 2026-10-31, or earlier if an agent session is visibly slowed by them:

- Every part of `.agents/` that has **not been used** since adoption moves to `.agents/archive/` (never deleted). The candidates are rounds in `plan/cycles/`, `plan/DoD.md`, `prompts/` and the `reference/` files that no session opened. The record of the review goes to `plan/promotions.md`.
- The heart `.agents/AGENTS.md` stays **under 100 lines**, as it says itself.
- `a2scaffold sync --dry-run` must still report a clean state after the archiving. If it would recreate archived files, those are recorded as kept-but-unused rather than fought.

The measure is use, not merit: a good process that nobody follows is noise for the next agent.
