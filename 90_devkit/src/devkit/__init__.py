"""AI-Cowork devkit: building and checking releases. The kernel developer's tool:
lives in 90_devkit/, never ships, builds only on aicowork_core."""

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
