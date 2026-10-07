# viewer — the local dashboard

_A small web app on your own computer: today, signals, keep-an-eye, circle balance, calendar, search, inbox, lessons; light editing with a change guard. It listens on 127.0.0.1 only, loads nothing from the internet, and refuses to start on any other address._

Start it with `aicowork viz` (the launcher runs it through `uv`). Directly: `uv run --locked --project 98_tools python -m viewer`.

Needs `uv` (which provides the Python that `98_tools/pyproject.toml` asks for); the packages are pinned in `pyproject.toml` and locked in `98_tools/uv.lock`. It builds on the shared library `aicowork_core` (`../../libs/core/`), never on the command line app: the base folder, the instance settings and the folder contract are defined there once.

Security model, routes and the smoke test: `../../REBUILD.md`. Tests: `uv run --locked --project 98_tools pytest 98_tools/apps/viewer/tests`.
