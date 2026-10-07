# Project — what this repository is and its rules

> Canonical (human-curated). Loaded every session through `.agents/AGENTS.md`.
> Changing it is a human decision, logged in `plan/promotions.md`.

This repository develops the **AI-Cowork kernel** (`99_system/`, a specification), its host pages (`hosts/`) and its reference tools (`98_tools/`). It is **not an instance**: there is no owner data here and there must never be. Releases are built here and installed into instances with `aicowork init` / `aicowork upgrade`.

Read first: `README.md` (public front page), `99_system/PHILOSOPHY.md`, `99_system/CONVENTIONS.md` "Rings", `CONTRIBUTING.md`, `.agents/FIXED-POINT.md` (the main philosophy: read it first; never shipped), `.agents/plan/v0.0.1-plan.md` (current work).

Rules:

- **No owner data, ever.** No real names of people, organisations, teams, customers or products; no real paths, e-mail addresses or classification stamps. Examples use the fictional example instance (`99_system/conformance/fixtures/`) or reserved names (`example.com`, `<First Last>`). `devkit leakscan` checks every tracked file against the owner's private instance (`git config aicowork.denyFrom <instance>`); the git hooks run it on every commit and push.
- A kernel change passes the membership test (PHILOSOPHY "The kernel"), comes with its conformance case, stays within the 10,000-word prose budget, and contains no code and no host names.
- A tools change has a test in that tool's `tests/`. Layout and import rules: `98_tools/README.md`, `98_tools/REBUILD.md` (libs ← apps; libs ← devkit; never app → app, never anything → `90_devkit`). Anything an agent may run stays standard-library only; no network calls.
- Markdown: `devkit fmt` before committing prose changes (Prettier, pinned; templates and fixtures are excluded).
- After changing a ring: `aicowork manifest --write`, then `aicowork verify` (every test suite, conformance on the example instance, manifests). One environment: `uv sync --project 98_tools`.
- Never delete — move to `.agents/archive/` or let git history keep it. Commit with a conventional prefix (`feat:` `fix:` `docs:` `test:` `chore:` `release:`).
- A person ships. `devkit package` (`90_devkit/`) builds and checks; publishing is the owner's step (`docs/publishing.md`).

## Where things live

| Path                                             | What                                                             | Ships?                                                                                                         |
| ------------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `99_system/`                                     | the kernel (specification)                                       | yes                                                                                                            |
| `hosts/`                                         | host adapters                                                    | yes                                                                                                            |
| `98_tools/`                                      | reference tools: `libs/`, `apps/`                                | yes (optional at init)                                                                                         |
| `90_devkit/`                                     | release building, leak scan, fixtures, `fmt`                     | **never**                                                                                                      |
| `.agents/`                                       | this knowledge base, plans, decisions, release log, agent memory | **never** in a release — but it is in this repository, which will be public: leak-scanned like everything else |
| `.claude/`, `.github/`, `CLAUDE.md`, `AGENTS.md` | harness stubs and guardrails for working on this repository      | never in a release                                                                                             |
