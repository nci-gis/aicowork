# -*- coding: utf-8 -*-
"""Plain-file compatibility (plan D7): the folder must open cleanly in any
Markdown editor (Obsidian, VS Code, Notepad). No integration packages — just
checks that what an editor needs is true of the kernel and the example."""
import re
from pathlib import Path
from urllib.parse import unquote

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())
KERNEL = REPO / "99_system"
EXAMPLE = KERNEL / "conformance" / "fixtures" / "example-instance"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def test_example_relative_links_resolve():
    broken = []
    for md in EXAMPLE.rglob("*.md"):
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            p = (md.parent / unquote(target.split("#")[0])).resolve()
            if not p.exists():
                broken.append(f"{md.relative_to(EXAMPLE)} -> {target}")
    assert broken == []


def test_kernel_needs_no_wikilinks_or_editor_syntax():
    offenders = []
    for md in list(KERNEL.glob("templates/*/*.md")) + list(KERNEL.glob("skills/*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        if re.search(r"\[\[[^\]]+\]\]", text) or "```dataview" in text:
            offenders.append(md.relative_to(KERNEL).as_posix())
    assert offenders == []


def test_frontmatter_is_plain_yaml_block():
    """Editors read frontmatter only as the very first block, fenced by ---."""
    for md in EXAMPLE.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        # README (human note), the inbox (raw drops) and root INDEX.md (the
        # catalog) carry no frontmatter by contract
        if md.name == "README.md" or md.parent.name == "00_inbox" or md.parent == EXAMPLE:
            continue
        assert text.startswith("---\n"), md
        assert "\n---\n" in text[4:], md


def test_editor_folders_are_ignored():
    gi = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert ".obsidian/" in gi and ".vscode/" in gi
