# -*- coding: utf-8 -*-
"""Helpers shared by the command groups."""
from pathlib import Path


def _base(args):
    from aicowork_core.common import base_path
    return base_path(getattr(args, "base", None))


def _print_findings(findings, verbose=True):
    for f in findings:
        if verbose or f.level == "error":
            print(f"  {f.level:5}  {f.case:18} {f.path}  — {f.message}")


def _with_kernel(example, kernel):
    """The shipped example instance has no 99_system of its own; check it against
    this kernel through a temporary copy."""
    import shutil
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="aicowork-example-"))
    shutil.copytree(example, td / "x")
    # the kernel's manifest lists the fixtures, which this temp copy leaves out
    shutil.copytree(kernel, td / "x" / "99_system", ignore=shutil.ignore_patterns("fixtures", "MANIFEST.sha256"))
    return td / "x"
