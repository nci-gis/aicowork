"""AI-Cowork reference tools — local viewer (dashboard, browse, live edit)."""
try:
    from importlib.metadata import version as _v
    __version__ = _v("aicowork-tools")
except Exception:            # running from source without installing (host sandbox)
    __version__ = "0.0.1"
