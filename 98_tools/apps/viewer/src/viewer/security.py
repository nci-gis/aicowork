# -*- coding: utf-8 -*-
"""Security primitives for the local viewer. Pure functions, stdlib only.

Threat model (SECURITY.md): the viewer is a loopback-only web app that reads
and writes the owner's files. The attackers that matter are (a) a web page the
owner visits (DNS rebinding, CSRF), (b) hostile content inside a note or mail
(stored XSS — the sanitiser itself is in render.py, which needs the markdown package), (c) a crafted path (traversal, junctions, Windows name tricks).
Each function below closes one of those; tests live in 98_tools/apps/viewer/tests/. Path safety
and atomic writes are shared with every tool (aicowork_core.fsafe).
"""
import re
import secrets


# ---------- host / origin ----------

def allowed_hosts(port):
    """Host header values a legitimate browser tab can send. Anything else is
    a DNS-rebinding attempt (the page's own domain resolving to 127.0.0.1)."""
    return {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}


def origin_ok(origin, host):
    """Browsers always send Origin on cross-site POST. Missing = not a browser
    (still needs the session cookie); present = must be this exact origin."""
    return origin is None or origin == f"http://{host}"


def new_token():
    return secrets.token_urlsafe(24)


SECURITY_HEADERS = {
    # inline style attributes are used for circle colours; scripts are not inline
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Frame-Options": "DENY",
}

# ---------- paths ----------

from aicowork_core.fsafe import PathRejected, safe_path, atomic_write, exclusive_create  # noqa: F401  (re-used here)

# ---------- markdown ----------

_SAFE_SCHEME = re.compile(r"^(https?:|mailto:)", re.I)
_ANY_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def url_ok(url):
    """http(s), mailto, or scheme-less (relative / fragment). Everything else
    (javascript:, data:, vbscript:, file:) is dropped."""
    u = (url or "").strip()
    return bool(_SAFE_SCHEME.match(u)) or not _ANY_SCHEME.match(u)


def escape_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


# FTS5 snippet markers that cannot occur in normal text
SNIP_OPEN, SNIP_CLOSE = "\x02", "\x03"


def safe_snippet(raw):
    """Escape an FTS snippet, then turn the private markers back into <mark>."""
    return escape_html(raw or "").replace(SNIP_OPEN, "<mark>").replace(SNIP_CLOSE, "</mark>")

# ---------- quick-add input ----------

_RELATED_OK = re.compile(r"^[\w\-./ ]{1,200}$", re.UNICODE)
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def clean_title(s, limit=200):
    return _CONTROL.sub(" ", s or "").strip()[:limit]


def clean_related(items, limit=5):
    out = []
    for r in items or []:
        r = str(r).strip().replace("\\", "/")
        if not _RELATED_OK.match(r) or ".." in r or r.startswith("/"):
            raise PathRejected(f"bad related path: {r!r}")
        out.append(r)
    if len(out) > limit:
        raise PathRejected(f"at most {limit} related items")
    return out
