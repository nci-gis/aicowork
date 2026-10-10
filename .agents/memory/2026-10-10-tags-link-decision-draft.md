# Draft decision record: tags are the link between items (Round 002, 0.0.1-rc.7)

**Date**: 2026-10-10
**Agent**: Claude (Claude Code session)
**Confidence**: Medium (the shape is derived from what the kernel already has; the measure is not yet run)
**Status**: Kernel sentences written on the owner's "proceed B" (2026-10-10, CONVENTIONS "Core keys", SUITE L1-FRONTMATTER, inbox-triage); the record itself is for the owner to place in `decisions/`
**Source**: the owner, 2026-10-10: after weeks of use, the viewer showed everything ever filed (Round 001 fixed the default), and the next gap is finding the related item; "a proof needs at least an MVP". Round 002.
**Review-by**: when the three measured cases are run (Round 002, Check)

## Problem

Nothing links one note to another. `INDEX.md` lists; search finds words; a decision behind a project or the mail behind an event is found by memory. The kernel already carries `tags` as a core key (CONVENTIONS "Core keys"; schema: a list or a string; the event, email, persona and watch-result templates have it), the viewer stores it, and one fixture note uses it. Nothing reads it.

## The four questions, answered for the MVP

1. **What is the link?** Two things the kernel already has, read together: `tags` — one tag shared by two items is the link, and a tag is also the group; and `related:` — the explicit pointer the inbox-triage skill already defines (a path or a list of paths, set by quick-add, used to file under a project). No new key. The viewer shows both: items sharing a tag, items a note points at, and items pointing at it (back-links). A dangling `related:` path is a warning, never an error. A tag is a lower-case slug (`[a-z0-9][a-z0-9-]*`), so that `grep -l 'tags:.*\bplanning\b'` finds it in a files-only instance exactly as the viewer does.
2. **What is a group?** A tag. Circle and type already group; a project slug is a tag by convention (the agent tags items about a project with its slug). INDEX.md does not change in this round: the viewer groups, the files carry the truth.
3. **Who writes links?** The agent proposes tags when it files (inbox-triage: "tags the item shares with what it relates to; a project's slug when it is about that project"), in the note it prepares — so a plan carries them, the owner applies, L3-TRIAGE sees them in the filed frontmatter. The owner edits tags like any frontmatter. Tags never raise visibility and never leave: on export the frontmatter is reduced to `type visibility circle date time status claim` (CONVENTIONS "Visibility & egress") — `tags` is not in that list, so the link stays home.
4. **The measure.** Before the viewer work: the owner records three real "could not find it" cases (item, what was looked for, how long). After: the same three, found through a tag in the viewer, and by `grep` in the files. Round 002 Check.

## What changes where

- **Kernel** (owner; a few sentences, budget 8,004 of 10,000): CONVENTIONS "Core keys": `tags` — lower-case slugs; a tag shared by two items is the link between them, and a project's slug is its tag. SUITE L1-FRONTMATTER: `tags` is a list of such slugs (a string is read as one tag). inbox-triage: the sentence in 3 above.
- **Tools**: conformance checks the slug shape (warning, not error, for existing instances); the viewer gets a Tags section in the sidebar (open counts), a tag filter in Browse, and a "Related" strip on an item — open items sharing a tag, nearest date first; `aicowork tags` lists tags with counts for a files-only check.
- **Not in the MVP**: `related:` paths, tag renames, tag suggestions from text, anything in INDEX.md.

## Against the fixed point

- Fail closed: a tag is data; nothing reads it as an instruction. Private by default: tags never export. Nothing deleted. No new egress, no new dashboard signal (PHILOSOPHY #9: the sidebar section is navigation, not a signal). A files-only instance keeps the guarantee: the link is text in the file.
- Not claimed: that tags find everything. The measure says what they find.

## Promotion candidate?

- [ ] `context/`: no
- [x] `decisions/`: yes — the owner places it as `2026-10-10_tags-are-the-link.md` once the four answers are decided.
