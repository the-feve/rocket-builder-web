"""Fit Test Builder (the-feve/3D_print_test_fitter) runs inside this app, like
Trebuchet Builder (trebuchet_mount.py): one Fly machine, no second app to pay for.

The deploy checks that repo out into `fittest/` at the repo root (in the
image: /app/fittest). If it isn't there, /fit/ is a 404. `FIT_DIR` overrides
the location. Its only geometry dependency, build123d, is already installed
for rocketgen; its package `fitgen` is imported from the checkout.

Served at /fit/ on every host, and at / for fit.* hosts (HostRouter). While
it's being dialled in, only admin accounts can open it (app.py's gate;
`ROCKETGEN_FIT=open` opens it to everyone). The page uses relative URLs, so
it works under either.

It shares this app's build lock, so a rocket and a coupon set never build at
once on the 1 GB machine.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("rocketgen.fit")

PREFIX = "/fit"


def fit_dir() -> Path:
    env = os.environ.get("FIT_DIR")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "fittest"


def load_module():
    """The Fit Test Builder server module (its FastAPI app is `.app`), or None
    if its code isn't here."""
    root = fit_dir()
    entry = root / "server" / "app.py"
    if not entry.is_file():
        log.info("Fit Test Builder not found at %s; not mounting it.", root)
        return None
    # Appended, not prepended: this app's own modules (app, ...) win. Its
    # server/ is loaded by path, not as a package, so it can't clash with ours.
    if str(root) not in sys.path:
        sys.path.append(str(root))
    try:
        spec = importlib.util.spec_from_file_location("fittest_app", entry)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        log.exception("Fit Test Builder failed to load; not mounting it.")
        return None
