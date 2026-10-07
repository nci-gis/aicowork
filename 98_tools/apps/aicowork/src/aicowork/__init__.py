"""AI-Cowork command line (app): instance lifecycle, checks, egress. Standard library only."""

def _find_core():
    """Run without installs (`python -m ...` with only this package's src on the
    path, as an agent does in a host sandbox): put the shared library beside it on
    the path. Installed through uv, aicowork_core is already importable."""
    import sys
    from pathlib import Path
    try:
        import aicowork_core  # noqa: F401
        return
    except ImportError:
        pass
    for p in Path(__file__).resolve().parents:
        lib = p / "98_tools" / "libs" / "core" / "src" if p.name != "98_tools" else p / "libs" / "core" / "src"
        if (lib / "aicowork_core").is_dir():
            sys.path.insert(0, str(lib))
            return


_find_core()

try:
    from importlib.metadata import version as _v
    __version__ = _v("aicowork")
except Exception:            # running from source without installing (host sandbox)
    __version__ = "0.0.1"
