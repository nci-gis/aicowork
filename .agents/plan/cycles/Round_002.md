# Round 002: Finding things — classify, link, group (the first feature after 0.0.1)

**Status**: Planning
**Part of**: standalone — opens when Round 001 is Complete (0.0.1 shipped)
**Date started**: —
**Date completed**: —

## Goal

The owner's argument (2026-10-10): a proof needs at least a usable product — "something that looks nice" does not earn the trust the fixed point speaks of; first impressions do. After weeks of real use the viewer's lists held everything ever filed (fixed in Round 001 by an "open" default), and the next gap is finding the related item: a decision behind a project, the mail behind an event, the lesson behind a practice. The kernel already has `tags` as a core key and `INDEX.md` as the catalogue; neither links anything.

This round defines and ships the smallest thing that lets an owner find related items — and measures that it does — without moving the fixed point: no new egress, nothing an agent can write that raises visibility, nothing the kernel claims that files alone cannot keep.

## Plan

Questions the design has to answer first (a decision record, owner's):

- [ ] What is the link: `tags` (already a core key), explicit `related:` paths, or both? What does a files-only instance do with it (REBUILD, conformance)?
- [ ] What is a group: a tag, a project slug, a circle — and does INDEX.md show it, or only the viewer?
- [ ] Who writes links: the agent at triage (then L3-TRIAGE scores it), the owner, both?
- [ ] The measure: the three real "could not find it" cases, recorded before the work starts (backlog, trigger), and the same three found after.

Then, in order:

- [ ] 1. Decision record (owner) and the kernel sentences it needs — within the budget.
- [ ] 2. Conformance case for the link (a dangling link is an error or a warning — decide).
- [ ] 3. The viewer: a related-items strip on an item, grouping in Browse; counts stay "open".
- [ ] 4. Triage skill: the agent proposes links in its plan; the owner applies.
- [ ] 5. Measure with the three recorded cases; the second-person tester tries one.

## Do

(not started)

## Check

- [ ] The three recorded cases are found in the viewer and by hand (INDEX.md or `grep`) in a files-only instance.
- [ ] No new dashboard signal (PHILOSOPHY #9); no new egress; L2 unchanged for instances without links.

## Act

**Learnings**: —

**Promotions**: —
