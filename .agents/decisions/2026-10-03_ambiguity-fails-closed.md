---
type: decision
date: 2026-10-03
status: decided
claim: stance
tags: [aicowork, egress, ambiguity, review, rc.2]
source: owner, 2026-10-03, in session, after the review of 0.0.1-rc.2
---

# Ambiguity fails closed — classified, refused, and never scored

## Decision (owner)

Everything a note can say in two ways is handled in one of two tiers. Neither tier lets anything leave.

1. **Classified.** A pattern in `99_system/conformance/ambiguity.json` is an error. The note reads the fail-closed way and every export refuses until a person fixes it. There is no override: `--allow` names a content-scan hit, never an ambiguity.
2. **Unclassified but suspicious.** Anything outside the grammar (the YAML subset for frontmatter; exact, alternating, non-nested markers for private blocks) is an error as well. It is proposed for classification: **ambiguous** (a new class with a fixture, added in a kernel release) or **false alarm** (the grammar is widened).

Who decides:

- An agent may propose and add a class. That tightens the gate.
- Only the owner may declare a false alarm, remove a class or widen a grammar. That loosens the gate, so it needs a decision entry and a fixture.

**No confidence score.** The owner first proposed flagging unclassified cases at a confidence of 0.6 or more. The owner then accepted replacing that with a grammar check plus deterministic lookalike rules:

- A score that code computes is false precision (PHILOSOPHY #12).
- A score that a model computes makes the gate depend on a model, and asking a model about a note sends the note out: the check would itself be egress.

The same applies to public documents (class AMB-DOC-CLAIM in `90_devkit/src/devkit/claims.py`). An absolute claim that nothing leaves must name the model-call exception in the same passage, or the release build refuses. A false alarm there is recorded by the owner in `90_devkit/claims-reviewed.json`, with the reason and the date.

The published Python floor is **3.11**: the only version the tests run on (owner: option (b)). Where it is written: addendum 2 below.

## Why

The review of rc.2 reproduced seven findings. Four had the same root:

- frontmatter read by a second, lenient parser;
- private blocks found by counting markers;
- a prohibited marker checked after stripping;
- a leak scan of the working copy instead of what the commit holds.

In each, the tool guessed at text that could be read two ways, and the guess let data out. The fixed point's reader cannot tell a guess from a rule. "Safe without understanding" means the tool never guesses on their behalf.

## Classes at adoption

AMB-FM-FENCE, AMB-FM-SYNTAX, AMB-FM-VIS-KEY, AMB-FM-VIS-VALUE, AMB-PB-NEST, AMB-PB-ORPHAN, AMB-PB-NEAR (kernel); AMB-DOC-CLAIM (devkit).

## Candidates not yet classified (decide when evidence appears)

- A prohibited marker in other capitals or spacing. CONVENTIONS defines markers as exact strings; matching variants would flag ordinary prose.

## Revisit when

- a class produces a false alarm on real notes, or a person bypasses the gate to get past one;
- a host or editor writes a construct that the grammar refuses but that reads one way.

## Addenda (owner, 2026-10-03, after the second review of the rc.3 work)

1. **Commit trailers: a false alarm, recorded.** Scanner B flags the AI assistant's public bot address (the `noreply` address in `Co-Authored-By:` trailers) in every commit. The owner decided it is a false alarm, for that one address, in trailer lines of commit messages only. It is recorded by its SHA-256 in `90_devkit/leak-reviewed.json` (what, why, decided), so the address itself is never written into the repository; history is not rewritten. Any other address in a commit message, and this one anywhere else, still refuses.
2. **The Python floor is written once.** `requires-python` in `98_tools/pyproject.toml` (its members state the same value; a test checks it). The tools' entry point, launchers and hooks read it; documents point to it and never restate it. Reasons to keep 3.11 rather than move to 3.10: 3.10 reached end of life in October 2026, and the host that had only 3.10 can fetch 3.11 with `uv`.
3. **AMB-PB-NEAR covers an unclosed marker.** A comment that lost its `-->` (`<!-- 🔒 private --`) matched no class and exported the private text. The valid forms are now a closed list (the two markers and the export placeholder); anything else that opens a comment and carries a lock sign, or starts with `private`, is the class — closed or not.
