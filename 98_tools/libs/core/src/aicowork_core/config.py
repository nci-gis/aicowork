# -*- coding: utf-8 -*-
"""Where the base folder is, and the instance's settings. Stdlib only.

Three kinds of value live here and they are deliberately treated differently:

* **Contract** — CIRCLES, the kind->folder map, SKIP_NAMES, EDITABLE_ROOTS
  (`contract.py`). Defined in code only. CONVENTIONS.md is their source of truth and every
  .md file's frontmatter is written against them; renaming a circle from a
  config file would silently orphan the `circle:` field in every file.
* **Runtime knobs** — dashboard windows, cadence days. Tunable from the
  instance's `aicowork.yaml`; a wrong value warns and the default stands.
* **Security knobs** — `server` (host/port) and `security`. A wrong value
  lands in SECURITY_ERRORS and the tools refuse to run (fail closed).

Precedence: code default -> aicowork.yaml -> AICOWORK_<SECTION>_<KEY> env var.
The base folder is the nearest folder above this file that holds `00_inbox/`
(an instance) or else `99_system/` (the development repository); AICOWORK_BASE
overrides it.
"""
import os
from pathlib import Path

from aicowork_core.yamlite import YamlError, loads as _yaml_loads

_HERE = Path(__file__).resolve()


def _find_base() -> Path:
    env = os.environ.get("AICOWORK_BASE")
    if env and (Path(env) / "00_inbox").is_dir():
        return Path(env).resolve()
    ups = list(_HERE.parents)
    for p in ups:                                   # the instance these tools sit in
        if (p / "00_inbox").is_dir():
            return p
    for p in ups:                                   # the development repository
        if (p / "99_system").is_dir() and (p / "98_tools").is_dir():
            return p
    for parent in Path.cwd().resolve().parents:
        if (parent / "00_inbox").is_dir():
            return parent
    return Path.cwd().resolve()   # best effort; doctor warns


BASE = _find_base()


def release_root():
    """The folder these tools came in: an unzipped release, the development
    repository, or an instance (each has 99_system/ beside 98_tools/)."""
    for p in _HERE.parents:
        if (p / "99_system").is_dir() and (p / "98_tools").is_dir():
            return p
    return None
CONFIG_PATH = BASE / "aicowork.yaml"
SETTINGS_PATH = CONFIG_PATH                     # name kept for __main__'s banner

# The only source of truth for runtime values; 99_system/aicowork.example.yaml
# documents the same numbers.
_DEFAULTS = {
    "server":    {"host": "127.0.0.1", "port": 8765},
    "dashboard": {"horizon_days": 14, "hot_days": 2,
                  "energy_days": 30, "max_events_per_day": 2,
                  "lessons_shown": 3, "lessons_served": 30},
    "cadence":   {"daily": 1, "weekly": 7, "biweekly": 14,
                  "monthly": 31, "quarterly": 92},
}


def _typed_like(default, value):
    """True if value can stand in for default. bool is a subclass of int, so
    `port = true` must not sneak past an int check."""
    if isinstance(default, bool) != isinstance(value, bool):
        return False
    return isinstance(value, type(default))


LOOPBACK = ("127.0.0.1", "localhost", "::1")
_TOP_KEYS = {"schema", "kernel_version", "language", "modules", "apps",
             "server", "dashboard", "cadence", "security"}
_STRICT = {"server"}          # sections whose errors refuse to start


def read_instance_config(path=None):
    """-> (raw dict, error str | None). Never raises."""
    path = Path(path) if path else CONFIG_PATH
    if not path.is_file():
        return {}, None
    try:
        raw = _yaml_loads(path.read_text(encoding="utf-8"))
    except (YamlError, UnicodeDecodeError, OSError) as e:
        return {}, f"{path.name}: {e}"
    if not isinstance(raw, dict):
        return {}, f"{path.name}: top level must be a mapping"
    return raw, None


def _load_settings():
    """Layer aicowork.yaml then env vars over _DEFAULTS.
    -> (cfg, raw, warnings, security_errors). Never raises."""
    cfg = {s: dict(v) for s, v in _DEFAULTS.items()}
    warn, errors = [], []
    raw, err = read_instance_config()
    if err:
        # an unreadable file could hide a security choice: fail closed
        errors.append(f"{err} — fix the file (the tools will not run on a guess)")
        raw = {}
    for key in raw:
        if key not in _TOP_KEYS:
            warn.append(f"aicowork.yaml: unknown key '{key}' - ignored")
    for section in cfg:
        values = raw.get(section)
        if values is None:
            continue
        sink = errors if section in _STRICT else warn
        if not isinstance(values, dict):
            sink.append(f"aicowork.yaml: '{section}' must be a mapping")
            continue
        for key, value in values.items():
            if key not in cfg[section]:
                sink.append(f"aicowork.yaml: unknown key {section}.{key}")
                continue
            default = cfg[section][key]
            if not _typed_like(default, value):
                sink.append(f"aicowork.yaml: {section}.{key} should be "
                            f"{type(default).__name__} - kept default {default!r}")
                continue
            cfg[section][key] = value

    for section, values in cfg.items():
        for key in values:
            env_name = f"AICOWORK_{section}_{key}".upper()
            env = os.environ.get(env_name)
            if env is None:
                continue
            try:
                values[key] = type(values[key])(env)
            except (TypeError, ValueError):
                warn.append(f"{env_name}={env!r} is not a "
                            f"{type(values[key]).__name__} - ignored")
    if cfg["server"]["host"] not in LOOPBACK:
        errors.append(f"server.host = {cfg['server']['host']!r} is not a loopback "
                      "address; the viewer only binds to 127.0.0.1 / localhost / ::1")
    if not 1024 <= cfg["server"]["port"] <= 65535:
        errors.append(f"server.port = {cfg['server']['port']} is outside 1024-65535")
    return cfg, raw, warn, errors


SETTINGS, INSTANCE, SETTINGS_WARNINGS, SECURITY_ERRORS = _load_settings()

LANGUAGE = INSTANCE.get("language") if isinstance(INSTANCE.get("language"), dict) else {}
APPS = [a for a in (INSTANCE.get("apps") or []) if isinstance(a, dict)]
UI_LANG = LANGUAGE.get("ui") if LANGUAGE.get("ui") in ("en", "vi") else "en"

HOST = SETTINGS["server"]["host"]
PORT = SETTINGS["server"]["port"]
URL = f"http://{HOST}:{PORT}"

HORIZON_DAYS = SETTINGS["dashboard"]["horizon_days"]        # "upcoming" window
HOT_DAYS = SETTINGS["dashboard"]["hot_days"]                # calendar chip goes hot
ENERGY_DAYS = SETTINGS["dashboard"]["energy_days"]          # energy chart lookback
MAX_EVENTS_PER_DAY = SETTINGS["dashboard"]["max_events_per_day"]
LESSONS_SHOWN = SETTINGS["dashboard"]["lessons_shown"]      # collapsed rows
LESSONS_SERVED = SETTINGS["dashboard"]["lessons_served"]    # rows sent to the UI

CADENCE_DAYS = SETTINGS["cadence"]
