"""`python -m devkit <command>`."""
import sys

from devkit.cli import main

sys.exit(main() or 0)
