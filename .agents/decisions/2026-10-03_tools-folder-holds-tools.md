---
type: decision
date: 2026-10-03
status: decided
claim: tested
tags: [aicowork, tools, rings]
source: owner, 2026-10-03, while the development repository was still new
---

# `98_tools/` holds tools, one subfolder each

## Decision (owner)

`98_tools/` is the place for the reference tools, each in its own subfolder. It replaces the rule of 2026-10-02 that every further tool gets a sibling `9N_<name>/` folder.

## Layout

- `98_tools/aicowork/`: the command line. Standard library only, Python ≥ 3.9. Sub-packages `core`, `conform`, `egress`, `inbox`, `instance`, `release`.
- `98_tools/viewer/`: the local web app (uv, FastAPI). It builds on `aicowork.core`.
- The folder carries one LICENSE and one MANIFEST. Each tool carries its own README, `pyproject.toml`, `src/` and `tests/`.

## Why

- **The "stdlib-only" claim was not true.** Before the split, the command line imported the viewer package for its configuration, path safety and frontmatter parser. Now those pieces live in `aicowork.core`, and the viewer imports from there. The dependency runs one way only.
- **One place for tools.** A person browsing the release finds every tool in one folder.
- **Cheap now.** The development repository had just started with a fresh history, so nothing downstream depended on the old paths yet.

## Evidence

- 72 command-line tests pass with only `pytest` installed (no FastAPI); 64 viewer tests pass.
- `test_nonet` asserts that the command line never imports the viewer.

## Revisit when

A third tool arrives that does not build on `aicowork.core`, or a tool needs its own licence.

## Addendum, same day: libs / apps / devkit (owner)

The first split left two problems. Release-building commands still shipped to every instance. And export (core) imported its leak scanners from the release code. The owner chose this layout:

```
98_tools/            ships (optional at init); one uv workspace, one .venv
  libs/core/         aicowork_core — shared library, stdlib only
  apps/aicowork/     command line (commands/ grouped, each group registers itself)
  apps/viewer/       web app
97_scripts/          reserved (name only, in CONVENTIONS)
90_devkit/           kernel developer only — never ships
```

Rules:

- Libraries import no tool.
- Apps import libraries only, never another app.
- The devkit imports libraries only.
- Nothing that ships depends on `90_`–`95_`, and the build refuses those folders.

All of these are tested (`test_layering.py`, `test_development_folders_never_ship`).

Why a library and not a copy of the code: the devkit and export need the same leak scanners and the same deny-list. Two copies would drift, and the weaker copy would be an unreported leak.

Why `libs/` is inside `98_tools/` and not in a top-level `90_libs/`:

- Numbers 96–99 stay "ships" and 90–95 stay "never ships".
- The library is a member of the one uv workspace.
- An instance without tools needs no library.

Why the devkit is not a workspace member (tested): an instance has no devkit, and the lock must still pass `--locked` there.

A real coupling the layering test found: the library's manifest module imported the app's egress receipts for the trust anchor. The anchor moved to the app (`aicowork.instance.anchor`).
