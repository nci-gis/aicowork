# 90_devkit/ — the kernel developer's tools

_Development repository only. **Never part of a release**: the release build refuses any `90_`–`95_` folder, and nothing in `98_tools/` may import from here (tested)._

| Command                | Does                                                                                                                                                                                                                                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `devkit package`       | builds `aicowork-<v>.zip` (kernel + tools), `aicowork-kernel-<v>.zip` (specification only), `aicowork-tools-<v>.zip`; refuses a drifted or uncommitted tree; runs both leak scanners on every zip; writes a review file; logs clean builds in `.agents/releases/`          |
| `devkit leakscan`      | every tracked file of this repository through both leak scanners (the git hooks run it on every commit and push)                                                                                                                                                           |
| `devkit fixtures`      | regenerates the fictional conformance fixtures under `99_system/conformance/fixtures/`                                                                                                                                                                                     |
| `devkit fmt [--check]` | formats the repository's Markdown with Prettier (one pinned version, fetched by `npx`, needs Node 20+; development machine only); `.prettierignore` keeps templates and fixtures out; run `aicowork verify` afterwards — the tests prove the formatting changed no meaning |

Run: `PYTHONPATH=90_devkit/src python -m devkit <command>` (the tools' Python `98_tools/.venv`, or any Python that `98_tools/pyproject.toml` accepts). Standard library only; builds on `aicowork_core` (`98_tools/libs/core/`) and nothing else.

The deny-list (the names that must never ship) comes from **your own private instance**, never from this repository: `git config aicowork.denyFrom <instance folder>` once, or `--deny-from <folder>`. Without it, `package` and `leakscan` refuse.

Tests: `PYTHONPATH=90_devkit/src 98_tools/.venv/bin/python -m pytest 90_devkit/tests`. Licence: MIT — `LICENSE` in this folder.
