---
type: decision
date: 2026-10-03
status: decided
claim: stance
tags: [aicowork, tooling, node, pnpm]
source: owner, 2026-10-03
---

# No `package.json` or pnpm in this repository yet

## Decision (owner)

The repository has no Node manifest: no `package.json`, no lockfile and no pnpm, neither at the root nor in `90_devkit/`. The repository keeps one way in: `aicowork …` for the core and `devkit …` for development.

Node is called only inside `devkit fmt`, through `npx prettier@<pinned>`. a2scaffold is run through `npx a2scaffold@<pinned>`, and always with `--dry-run` first.

## Why

A root `package.json` would buy a few shortcuts (`pnpm check`, `pnpm fmt`) at the cost of what the fixed point and this repository depend on:

- **Two ways to do one task.** `pnpm check` would sit beside `aicowork verify` and `devkit leakscan`, and the scripts would drift from the real commands.
- **Agents misread the repository.** An agent that sees `package.json` at the root reads it as a JavaScript project and installs, tests or builds accordingly.
- **The public first impression contradicts the README** ("plain text files"). It would add a lockfile thousands of lines long and could give GitHub the wrong language label.
- **The scripts are untested code.** They would shell out to uv and Python with quoting that differs between Windows and Linux.
- **Another toolchain to maintain** (lockfile churn, Dependabot, pnpm installation), and a longer setup for anyone who works on the kernel.

The risk the manifest would remove is small today:

- Prettier has no dependencies, so a pinned `npx` call is reproducible.
- VS Code's Prettier extension bundles Prettier and reads the root `.prettierrc`.
- a2scaffold's two dependencies with caret ranges drift only at the occasional, reviewed `sync`.

## Revisit when (any one)

- JavaScript in this repository needs building or testing, for example the viewer stops vendoring its scripts;
- three or more Node tools are in use;
- CI has to run a Node tool;
- two runs of a2scaffold produce different output.

Then the manifest goes into `90_devkit/`, contained and never shipped. It moves to the root only for real JavaScript code. Every option must pass the four-point test in `context/philosophy.md`.
