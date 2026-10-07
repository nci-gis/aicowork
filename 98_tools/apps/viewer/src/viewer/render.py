# -*- coding: utf-8 -*-
"""Markdown -> safe HTML for the viewer drawer. Needs the markdown package
(viewer-only; the stdlib commands never import this module)."""
import markdown as md_lib
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from .security import url_ok, _ANY_SCHEME


class _UrlFilter(Treeprocessor):
    def run(self, root):
        for el in root.iter():
            if el.tag == "a" and not url_ok(el.get("href")):
                el.attrib.pop("href", None)
            if el.tag == "img":
                src = el.get("src") or ""
                if not url_ok(src) or _ANY_SCHEME.match(src.strip()):
                    # remote images are an exfiltration channel (the request
                    # itself leaks that the note was opened) — show a link instead
                    alt = el.get("alt") or "image"
                    el.tag = "a"
                    el.attrib.clear()
                    if url_ok(src):
                        el.set("href", src)
                    el.text = f"[image: {alt}]"


class SafeHtmlExtension(Extension):
    """Raw HTML in notes is shown as text, and link/image URLs are filtered."""
    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("html")
        md.treeprocessors.register(_UrlFilter(md), "aicowork_url_filter", 1)


def make_markdown():
    return md_lib.Markdown(extensions=["tables", "fenced_code", "sane_lists",
                                       "nl2br", SafeHtmlExtension()])
