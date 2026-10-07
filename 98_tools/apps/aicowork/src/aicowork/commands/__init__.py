# -*- coding: utf-8 -*-
"""Command groups. Each module defines its `cmd_*` functions and one `register(add)`
that declares their subcommands; `aicowork.cli` collects them. A new command =
a function plus a few lines in its group's `register`."""
GROUPS = ("daily", "check", "egress", "instance")
