# -*- coding: utf-8 -*-
"""Safe file handling shared by every tool: resolve a client- or agent-supplied
relative path inside the base folder (or refuse), write atomically, create
without overwriting. Stdlib only."""
import os
import re
import secrets
from pathlib import Path


_RESERVED = {"con", "prn", "aux", "nul",
             *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
_BAD_CHARS = re.compile(r'[:*?"<>|\x00-\x1f]')


class PathRejected(ValueError):
    pass


def safe_path(base, rel, roots=None, root_files=()):
    """Resolve a client-supplied relative path inside `base`, or raise.

    Rejects: absolute/drive/UNC/`\\\\?\\` paths, `..`, NTFS alternate data
    streams and other reserved characters, DOS device names, components
    ending in dot or space, and anything that resolves somewhere other than
    its lexical location (symlinks, junctions, 8.3 short names). The root is
    taken from the path *after* these checks, so `01_events/../99_system`
    cannot pass a root allow-list.
    """
    if not isinstance(rel, str) or not rel.strip():
        raise PathRejected("empty path")
    norm = rel.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("//") or re.match(r"^[A-Za-z]:", norm):
        raise PathRejected("absolute path")
    parts = [p for p in norm.split("/") if p not in ("", ".")]
    if not parts:
        raise PathRejected("empty path")
    for part in parts:
        if part == "..":
            raise PathRejected("parent reference")
        if _BAD_CHARS.search(part):
            raise PathRejected("reserved character")
        if part[-1] in ". ":
            raise PathRejected("trailing dot or space")
        if part.split(".")[0].lower() in _RESERVED:
            raise PathRejected("device name")
    base = Path(base).resolve()
    lexical = base.joinpath(*parts)
    resolved = lexical.resolve()
    if not resolved.is_relative_to(base) or resolved == base:
        raise PathRejected("outside base")
    if os.path.normcase(str(resolved)) != os.path.normcase(str(lexical)):
        raise PathRejected("path is redirected (symlink, junction or short name)")
    if len(parts) == 1:
        if parts[0] not in root_files:
            raise PathRejected("root file not allowed")
    elif roots is not None and parts[0] not in roots:
        raise PathRejected("root not allowed")
    return resolved


def atomic_write(path, text, encoding="utf-8"):
    """Write via a temp file in the same folder, then os.replace: a crash
    mid-write leaves the old file intact instead of a truncated one."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    try:
        with open(tmp, "w", encoding=encoding, newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def exclusive_create(path, text, encoding="utf-8"):
    """Create a new file, never overwrite an existing one (mode 'x')."""
    with open(path, "x", encoding=encoding, newline="") as f:
        f.write(text)
