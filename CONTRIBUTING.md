# Contributing

AI-Cowork has two parts with different rules. Know which one you are changing (CONVENTIONS "Rings").

## The kernel (`99_system/`) — the specification

- A change must pass the **membership test** (PHILOSOPHY "The kernel"): host-independent, Notepad-readable, rebuild-necessary, owner-independent, testable.
- Every rule change comes with its conformance case in `99_system/conformance/SUITE.md`, a new case ID for a new rule (IDs never change meaning), and a decision entry explaining why.
- The kernel stays under its word budget (CONVENTIONS "Rings"). Adding words means removing words, or a decision entry that raises the budget.
- No executable code in the kernel. No third-party skills. No host names outside `hosts/`.
- PHILOSOPHY changes almost never; a proposal to change it is a discussion first, a pull request second.

## The reference tools (`98_tools/`)

- They are _one_ implementation of the kernel. Another implementation is welcome if its instances pass conformance.
- Anything an agent may run stays **stdlib-only** (the Python version: `requires-python` in `98_tools/pyproject.toml`, written nowhere else). Only the viewer may use dependencies, bounded in `pyproject.toml` and locked in `uv.lock`.
- Every behaviour change has a test. Security fixes have a test that fails without the fix.
- No network calls in the commands. `98_tools/apps/aicowork/tests/test_nonet.py` must keep passing. Say "the commands", not "the tools": the launcher's `uv` may download the locked packages once.

## This repository holds no owner data

Examples use the fictional example instance or reserved names (`example.com`). Turn the hooks on once per clone; every commit and push is then leak-scanned:

```
git config core.hooksPath .githooks
```

Without a private instance, `leakscan` runs the generic patterns only (e-mail addresses, secrets, personal paths), which is all a contributor's clone can leak. A maintainer who runs an instance points the scanners at it once, locally (`git config aicowork.denyFrom <your instance folder>`); `devkit package` needs that and refuses otherwise. The developer's tools live here, in `90_devkit/` (never shipped).

## Before you open a pull request

```
aicowork verify          # tests, conformance L2 on the example instance, manifests, receipts
devkit leakscan          # every tracked file through both leak scanners   (PYTHONPATH=90_devkit/src python -m devkit …)
devkit package           # the release zips build and both leak scanners are clean
```

## Host pages (`hosts/<host>.md`)

A new host is supported when its page records every host-contract item with a date and host version, and the kernel needed **no change** to pass conformance L3 there.
