# Philosophy — aicowork

> Canonical. The principles that decide close calls when the rules do not
> cover the case. Summarised in the root instruction files; this is the
> authoritative version.
>
> Principles 1–5 came with the scaffold and were kept because each already
> decided something here (see the examples). 6–9 are this repository's own.
> The kernel's principles for _users_ are `99_system/PHILOSOPHY.md`; these are
> for _developing_ it.

---

## The working model

> Inherited from the tool that generated this file. Keep it if it describes
> how this project works with an agent; delete it if it does not. It is a
> stance, not a rule — nothing below is enforced by it.

**The human is the loop.** The agent is instrumentation inside a person's
cycle of understanding: it reads, drafts, verifies and proposes; the person
directs, decides and promotes. That is why this directory is split the way it
is. `memory/` is where the agent writes, `context/` is what a human has
promoted, and `plan/promotions.md` is the record of each crossing.

Two things follow, and both can be checked in a diff:

- **A finding is a draft until a human has read it.** An agent that discovers
  canon is wrong writes a memory and flags it. It does not fix canon.
- **Verification is the agent's job, not trust.** Before acting on a review, a
  plan, or an instruction that contradicts what the code says, reproduce it.

The scaffold that generated this directory states, in its own philosophy,
what this working model claims, how tested each claim is, and what would
falsify it.
The part it does not yet claim: that the person comes out of the loop knowing
their own repository better. Nothing here measures that. If this project finds
a way to, write it down.

## 1. Ask before assuming

The human partner knows the project intent better than the agent does. When
a change could alter public behaviour, a contract, or a convention, confirm
before writing code.

**In practice**: surface the ambiguity, state the assumption you would make,
and continue with everything the ambiguity does not block.

## 2. Small steps, frequent checks

Incremental edits with test runs beat large rewrites. Every step should be
independently reviewable and independently revertible.

**In practice**: no "WIP" merges to the main branch. Each change lands green.

## 3. Stability over speed

Knowledge is promoted only after it is validated. A pattern seen once is an
observation; a pattern seen repeatedly is a convention.

**In practice**: findings go to `.agents/memory/` first. Promotion to
`.agents/context/` requires human review and a log entry in
`.agents/plan/promotions.md`.

## 4. Explicit over implicit

No hidden fallbacks, no silent network access, no magic defaults. If the
tool is about to do something the reader did not ask for, it should ask.

**In practice**: fail with a message that names the fix, rather than
guessing what was meant.

## 5. Preserve what works

Existing contracts, dependencies, and conventions stay intact unless the
human decides otherwise. Prefer built-ins over new dependencies.

**In practice**: adding a dependency is a decision to raise, not a detail to
slip into a diff.

## 6. The fixed point decides

The assumed reader of the kernel knows nothing about AI and trusts whoever
published it ([FIXED-POINT.md](../FIXED-POINT.md)). A change that makes the
kernel harder for that person, or safe only for an expert, is wrong however
elegant it is.

**In practice**: defaults fail closed; a guarantee only the tools can keep is
not a guarantee of the kernel; the files-only path must keep working.
If a change would break the fixed point, the choice is between keeping the
point and starting a new repository — never bending it here.

**A tool or convenience earns its place only if all four hold**: each task
still has one way to do it; a newcomer's setup gets no longer; no agent can
misread what this repository is because of it; removing it breaks nothing.

## 7. No owner data, ever — this repository will be public

Nothing here may name a real person, organisation, team, customer, product,
path, e-mail address or classification stamp. Removing a name later does not
remove it from history.

**In practice**: examples use the fictional example instance or reserved
names; `devkit leakscan` runs on every commit and push and refuses; that
includes `.agents/memory/`.

## 8. Claims need evidence; tests prove

Every claim carries a label (Stance, Untested, Sourced, Measured), as in the
kernel's PHILOSOPHY #12. A change is done when a test or a recorded check
shows it — not when it looks right.

**In practice**: a refactor or a formatting run ends with `aicowork verify`;
a bug found becomes a test first.

## 9. A person ships

The tools build, check, record and refuse. Publishing, tagging and every
decision with consequences outside this folder are the owner's.

**In practice**: `devkit package` writes a review file and stops; nothing in
this repository pushes, publishes or deletes on its own.

---

## How to change this file

`.agents/context/` is human-owned and authoritative. Agents must not edit it
directly — see the authority rules in [AGENTS.md](../AGENTS.md).

To propose a change: write the finding to `.agents/memory/`, flag it for
review, and let the human promote it.
