# copilot-instructions.md — aicowork

<!-- a2scaffold:start -->

> Loaded by GitHub Copilot for every request in this repository. Copilot does
> not expand imports, so this stub restates what the others import.

## Shared knowledge base

`.agents/` holds the directory layout, authority rules, load order, and the
pair-programming workflow. Treat it as part of these instructions.
This harness does not expand `@` imports, so **open it first**:
[AGENTS.md](../.agents/AGENTS.md).

<!-- a2scaffold:end -->

<!--
Seeded once, then yours. This section sits outside the generated block, so
re-running `a2scaffold` will not touch it. Replace the placeholders below with
your project's real principles and keep them in step with the canonical list in
`.agents/context/philosophy.md`.
-->

## Read first

[FIXED-POINT.md](../.agents/FIXED-POINT.md) — the main philosophy of this repository. Every change is judged against it; if a change would break it, the choice is to keep it or to start a new repository.

## Philosophy

These principles decide the close calls. The full version — with rationale
and worked examples — lives in
[philosophy.md](../.agents/context/philosophy.md).

1. **Ask before assuming.** The human partner owns intent. Confirm before
   changing public behaviour.
2. **Small steps, frequent checks.** Incremental edits with test runs beat
   large rewrites.
3. **Stability over speed.** Knowledge is promoted only after it is
   validated, never on first sighting.
4. **Explicit over implicit.** No hidden fallbacks, no silent network
   access, no magic defaults.
5. **Preserve what works.** Existing contracts and conventions stay intact
   unless the human decides otherwise.

6. **The fixed point decides.** The kernel's assumed reader knows nothing
   about AI; defaults fail closed ([FIXED-POINT.md](../.agents/FIXED-POINT.md)).
7. **No owner data, ever.** This repository will be public; `devkit leakscan`
   refuses any real name, path or e-mail on every commit and push.
8. **Claims need evidence; tests prove.** A change ends with `aicowork verify`.
9. **A person ships.** The tools build and check; publishing is the owner's.

## This repository

Copilot does not follow imports, so the essentials are restated here; the
full rules are [project.md](../.agents/context/project.md).

- `99_system/` is the kernel: a specification, no code, no host names,
  ≤ 10,000 words of prose. Each rule change comes with its conformance case.
- `98_tools/` (libs, apps) ships; `90_devkit/` and `.agents/` never do.
  Apps import libraries only; nothing imports the devkit.
- After a change: `aicowork manifest --write`, `devkit fmt`, `aicowork verify`.
