# REBUILD — the reference implementation (`98_tools/`)

_Ring: reference implementation. One way to implement the kernel in `99_system/`; not the definition of it. Anyone may write another — it is valid if the instances it produces pass conformance. Changes whenever tooling changes._

## Layout

```
98_tools/                  the ring: one LICENSE, one MANIFEST.sha256
  pyproject.toml uv.lock   one uv workspace (members libs/*, apps/*): one lock, one .venv here
  libs/core/               aicowork_core — shared library, standard library only
  apps/aicowork/           the command line (standard library + aicowork_core)
  apps/viewer/             the local web app (FastAPI, uv)
90_devkit/                 the kernel developer's tool — development repository only, never ships
```

**Import rules** (tested: `apps/aicowork/tests/test_layering.py`): libraries import no tool; an app imports libraries only, never another app; the devkit imports libraries only; nothing in `98_tools/` imports a `90_`–`95_` folder. One implementation of each security-relevant piece (leak scanners, safe paths) serves every tool.

### `libs/core/` — `aicowork_core`

`config` (base folder: the nearest parent with `00_inbox/`, else the development repository; `AICOWORK_BASE` overrides; runtime knobs from the instance `aicowork.yaml`: code defaults → file → `AICOWORK_<SECTION>_<KEY>` env; runtime misconfig warns, security misconfig refuses), `contract` (CIRCLES, folder map, SKIP_NAMES, EDITABLE_ROOTS — code only, CONVENTIONS is their source), `frontmatter` (the subset parser; strips trailing `# comments`), `recur` (reminders: the occurrence rules of CONVENTIONS "Reminders" — windows, upcoming/due/overdue/expired, pure functions), `fsafe` (`safe_path` rejects `..`, absolute/UNC/drive, ADS, device names, trailing dot/space, and anything redirected by symlink/junction/8.3 name; `atomic_write`; `exclusive_create`), `yamlite` (the YAML subset of CONVENTIONS "Instance config"), `manifest` (ring locks), `scan` (leak scanners A/B and release file selection — used by export and by release builds), `common` (git, hashes, versions, the deny-list).

### `apps/aicowork/` — the command line

Entry point `aicowork = aicowork.cli:main`; also `python -m aicowork` with `98_tools/apps/aicowork/src` on `PYTHONPATH` (how an agent runs it inside a host sandbox without installing anything; the package puts `libs/core/src` on the path itself). `cryptography` is an optional extra (`seal`) for `below: encrypt`, refused cleanly without it.

- `commands/` — one module per group (`daily`, `check`, `egress`, `instance`), each with its `cmd_*` functions and one `register(add)`; **extension point**: a function plus a few lines in its group.
- `conform/` — `checks` (L1/L2), `audit` (L3 runner, session audit), `evidence` (audit pack, SBOM).
- `egress/` — `gate` (policy validation, backup, export, receipts, content scan), `seal` (AES-256-GCM).
- `inbox/` — `ingest` (untrusted-content quarantine), `triage` (plan-then-apply).
- `instance/` — `ops` (init, doctor, reach, new, folder READMEs), `anchor` (trust anchor outside the folder), `upgrade`.

### `apps/viewer/` — the local web app

Builds on `aicowork_core` only. `uv run --locked --project 98_tools aicowork viz` starts it; `aicowork viz` from plain Python hands over to uv.

- `config.py` — the viewer's own locations on top of `aicowork_core.config`: `AICOWORK_DATA` for the cache dir, readable roots, `/raw` extension lists, save size limit.
- `security.py` — Host allow-list, Origin check, Markdown sanitiser (raw HTML escaped; only http/https/mailto/relative URLs; remote images become links), snippet escaping, quick-add input rules; path safety is `aicowork_core.fsafe`.
- `scanner.py` — rglob `*.md` in content folders into index rows. `lessons()` skips HTML-comment blocks and bare labels.
- `store.py` — SQLite FTS5 at `<data>/index.db`; incremental mtime sync; derived cache. `SCHEMA_VERSION` + `PRAGMA user_version`: any column change drops and rebuilds the cache — never migrate. **It holds no trust hash, by design**: the cache sits inside the folder and the agent's reach, so a hash there is one more marker the agent can rewrite (or delete with the cache). Hashes that are checked live in the trust anchor outside the folder (`aicowork_core.anchor`); the viewer only reads it (`/api/data` → `anchor`).
- `api.py` — middleware `guard` on every request: Host must be loopback:port (421); `/api/*` and `/raw` need the per-launch session cookie, set by the launch URL `/?t=<token>` (401); non-GET must be same-origin JSON (403/415); security headers incl. `script-src 'self'`. Routes: `/api/data` (with the calendar's current month ±1 as `occurrences`, and the trust-anchor state), `/api/occurrences?from=&to=` (≤ 3 months: events and reminder windows), `/api/search`, `/api/item` GET (readable roots: content folders, `99_system/`, `INDEX.md`) / POST (editable roots only, `.md`, ≤ 1 MB, mtime guard, atomic), `/api/quickadd`, `/api/reminder/done` (`10_reminders/` only, sets `last_done` and adds the skipped windows to `missed`, nothing else, date ≤ today and ≥ `date:`, mtime guard, atomic), `/raw` (content folders, extension allow-list, never html/svg/js).
- `web/` — static UI. No inline script or handlers: markup carries `data-act` / `data-change` / `data-input`, one delegated listener dispatches. All libs vendored in `web/vendor/` (ECharts 5.6.1, Apache-2.0).

### `90_devkit/` — release building (never ships)

`python -m devkit package|leakscan|fixtures` with `90_devkit/src` on `PYTHONPATH`, using the tools' Python (`98_tools/.venv`) or any Python that `98_tools/pyproject.toml` accepts. Not a member of the uv workspace on purpose: an instance has no devkit and must still pass `uv run --locked`. `package` builds `aicowork-<v>.zip` (kernel + tools), `aicowork-kernel-<v>.zip` (specification only, no code) and `aicowork-tools-<v>.zip` from an allow-list; refuses a drifted or dirty tree, any `90_`–`95_` folder, and code in the kernel zip; runs both scanners on every built zip with the deny-list read from the owner's private instance.

### Tests

Each tool's `tests/` (pytest; the devkit's in `90_devkit/tests/`). `conftest.py` builds a throwaway base folder and cache before anything is imported; the real instance is never touched. The library's and the command line's tests need only `pytest`; `aicowork verify` runs every suite present.

### Launchers

`aicowork.bat` / `aicowork.sh` at the top: with `uv`, `uv run --locked --project 98_tools --package aicowork --extra seal aicowork …` (the command line only; `viz` runs the viewer's package the same way, on first use); without it, a Python that `libs/core/src/aicowork_core/pyfloor.py` accepts, with `98_tools/apps/aicowork/src` on `PYTHONPATH` (everything but `viz`). The Python version is written once, as `requires-python` in `pyproject.toml`; `pyfloor.py` reads it there, and the launchers and git hooks ask it rather than repeat the number. Without `98_tools/` they say so and stop: the kernel works with files alone.

## Smoke test

1. `aicowork verify` — tests + conformance L1/L2 on the example instance + kernel manifest + leak gate. Exit 0.
2. `aicowork inbox "test note"` → a file appears in `00_inbox/` (never overwrites one from the same second).
3. `aicowork viz` → the browser opens the launch URL; items are visible, searchable, editable (mtime guard holds). Opening `http://127.0.0.1:8765/` without the launch link shows "No session".
4. Delete `<data>/index.db` → restart → the index rebuilds identically.
5. Pull the network → the UI still works (no CDN); `pytest 98_tools/apps/aicowork/tests/test_nonet.py` passes.
6. Put `server: {host: 0.0.0.0}` in `aicowork.yaml` → the viewer refuses to start. Put `dashboard: {hot_days: true}` → it starts on the default and prints a warning.
7. Add `#lesson test [smoke]` to today's daily log → the Lessons card shows it; an unfilled template contributes zero lessons.
