# 98_tools/ — the small programs (optional)

_Reference implementation: one way to check and run an instance of the kernel in `99_system/`. Not the definition of it; you may skip these entirely (`aicowork init --no-tools`, or copy only `99_system/`) or write your own._

```
98_tools/
  libs/core/       aicowork_core — the shared library every tool builds on
  apps/aicowork/   the command line: create, check, back up, export, upgrade an instance
  apps/viewer/     a local, offline dashboard in your browser (127.0.0.1 only)
  pyproject.toml, uv.lock   one environment for all of them (98_tools/.venv, made by uv)
```

**Python:** the version in `pyproject.toml` (`requires-python`) — the one place it is written; tested on that version. With `uv` it is fetched for you; without `uv`, the launcher and the command line say plainly when yours is too old.

| You have | You can run                                                                                                                                                                         |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python   | every command except the viewer: `aicowork …` through the launcher at the top of the folder, or with nothing installed `PYTHONPATH=98_tools/apps/aicowork/src python -m aicowork …` |
| `uv`     | everything: the launcher runs `uv run --locked --project 98_tools --package aicowork`, which installs the command line only; `aicowork viz` adds the viewer the first time it runs  |

The `aicowork` commands make **no network connection** (tested: `apps/aicowork/tests/test_nonet.py`). With `uv`, the launcher installs the locked packages once — `uv` may download them, and a Python, the first time; that is `uv`, not the commands. What an assistant reads in the folder goes to its AI service: that is the host's model call, not these tools. An app builds on `libs/` only, never on another app (tested: `apps/aicowork/tests/test_layering.py`).

**Adding a tool**: a Python application goes to `apps/<name>/` (its own README, `pyproject.toml`, `src/`, `tests/`; it joins the workspace by itself), shared code to `libs/`. A tool that is not Python sits beside `apps/` with its own README. Anything an agent may run stays standard-library only. How these are built: `REBUILD.md`. Which check covers which risk: `../docs/controls.md`. Licence: MIT — `LICENSE` in this folder.
