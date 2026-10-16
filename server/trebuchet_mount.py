"""Trebuchet Builder (the-feve/trebuchet_builder) runs inside this app, so the
one Fly machine hosts both (no second app to pay for).

The deploy checks that repo out into `trebuchet/` at the repo root (in the
image: /app/trebuchet). If it isn't there, the rocket app runs on its own and
/trebuchet/ is a 404. `TREBUCHET_DIR` overrides the location.

Served at /trebuchet/ on every host, and at / for trebuchet.* hosts
(trebuchet.quiverdesignworks.net once its DNS and certificate are set up).
The trebuchet page uses relative URLs, so it works under either.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("rocketgen.trebuchet")

PREFIX = "/trebuchet"


def trebuchet_dir() -> Path:
    env = os.environ.get("TREBUCHET_DIR")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "trebuchet"


def load_app():
    """The trebuchet FastAPI app, or None if its code isn't here."""
    root = trebuchet_dir()
    entry = root / "server" / "app.py"
    if not entry.is_file():
        log.info("Trebuchet Builder not found at %s; not mounting it.", root)
        return None
    # Appended, not prepended: this app's own modules (app, terms, ...) win.
    for p in (root / "geometry", root / "server"):
        if str(p) not in sys.path:
            sys.path.append(str(p))
    try:
        spec = importlib.util.spec_from_file_location("trebuchet_app", entry)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception:
        log.exception("Trebuchet Builder failed to load; not mounting it.")
        return None


class HostRouter:
    """ASGI middleware: requests for a hosted app's own host (trebuchet.*, and
    fit.* for Fit Test Builder) go to its mount, so
    trebuchet.quiverdesignworks.net/ is its page. `routes` maps a host prefix
    to a mount prefix."""

    def __init__(self, app, routes: dict[str, str] | None = None):
        self.app = app
        self.routes = routes or {"trebuchet.": PREFIX}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            host = dict(scope.get("headers") or []).get(b"host", b"").decode("latin-1")
            path = scope.get("path", "")
            for start, prefix in self.routes.items():
                if host.startswith(start):
                    if not (path == prefix or path.startswith(prefix + "/")):
                        scope = dict(scope, path=prefix + path, raw_path=(prefix + path).encode())
                    break
        await self.app(scope, receive, send)
