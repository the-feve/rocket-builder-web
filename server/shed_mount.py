"""ShedCAD (the-feve/Shed_builder) runs inside this app, like Trebuchet Builder and
Fit Test Builder: one Fly machine, no second app to pay for.

The deploy checks that repo out into `shed/` at the repo root (in the image:
/app/shed). If it isn't there, /shed/ is a 404. `SHED_DIR` overrides the
location.

ShedCAD's web app (shedcad/webapp.py) is plain ASGI and standard library only.
It runs in "hosted" mode: each visitor's designs, materials list and images
stay in their own browser, and the server keeps nothing per visitor - it builds
the model, proxies the address / imagery / parcel lookups (rate-limited per
address) and caches imagery tiles in /tmp. Its floor-plan import uses the
optional OpenCV / ezdxf / pillow-heif / pypdfium2 modules from its
requirements-blueprint.txt, which the Dockerfile installs when the checkout is
there.

Served at /shed/ on every host, and at / for shed.* hosts (HostRouter). The
page uses relative URLs, so it works under either.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("rocketgen.shed")

PREFIX = "/shed"


def shed_dir() -> Path:
    env = os.environ.get("SHED_DIR")
    return Path(env) if env else Path(__file__).resolve().parent.parent / "shed"


def load_app():
    """ShedCAD's ASGI app (hosted mode), or None if its code isn't here."""
    root = shed_dir()
    if not (root / "shedcad" / "webapp.py").is_file():
        log.info("ShedCAD not found at %s; not mounting it.", root)
        return None
    # Appended, not prepended: this app's own modules win. ShedCAD's package
    # name (shedcad) doesn't clash with anything here.
    if str(root) not in sys.path:
        sys.path.append(str(root))
    try:
        webapp = importlib.import_module("shedcad.webapp")
        return webapp.create_app(hosted=True)
    except Exception:
        log.exception("ShedCAD failed to load; not mounting it.")
        return None
