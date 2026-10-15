"""Copies new Rocket Builder print orders from the website to a folder on this PC.

Each order lands in  <dest>/<batch>/<order id>/  with its STLs, ORDER.txt
(the batch sheet: customer, shipping, parts checklist) and order.json.
Orders whose status changed are fetched again so ORDER.txt stays current.

Needs only Python 3 (no packages). Run it by hand or every few minutes with
Windows Task Scheduler (see tools/README.md):

    python sync_orders.py --dest "C:\\RocketOrders"

The site address and token come from --server / --token, or the
ROCKET_SERVER / ROCKET_SYNC_TOKEN environment variables. The token is the
ROCKETGEN_SYNC_TOKEN secret set on Fly.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def get(url: str, token: str) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "rocket-order-sync"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--server", default=os.environ.get("ROCKET_SERVER", "https://rocket.quiverdesignworks.net"))
    ap.add_argument("--token", default=os.environ.get("ROCKET_SYNC_TOKEN", ""))
    ap.add_argument("--dest", default=os.environ.get("ROCKET_ORDERS_DIR", str(Path.home() / "RocketOrders")))
    a = ap.parse_args()
    if not a.token:
        print("No token: pass --token or set ROCKET_SYNC_TOKEN (the ROCKETGEN_SYNC_TOKEN secret on Fly).")
        return 2
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    state_file = dest / ".sync_state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"orders": {}}

    try:
        listing = json.loads(get(f"{a.server.rstrip('/')}/api/admin/orders", a.token))
    except urllib.error.HTTPError as e:
        print(f"The site said {e.code}: {e.read().decode(errors='replace')[:200]}")
        return 1
    except urllib.error.URLError as e:
        print(f"Couldn't reach {a.server}: {e.reason}. (It may be waking up; try again in a minute.)")
        return 1

    fetched = 0
    for o in listing["orders"]:
        seen = state["orders"].get(o["id"])
        target = dest / o["batch"] / o.get("name", o["id"])  # RB-…_<motor>_<customer code>
        if seen == o["updated_at"] and target.is_dir():
            continue
        data = get(f"{a.server.rstrip('/')}/api/admin/orders/{o['id']}/files.zip", a.token)
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if "/" not in name and "\\" not in name and not name.startswith("."):
                    (target / name).write_bytes(z.read(name))
        state["orders"][o["id"]] = o["updated_at"]
        fetched += 1
        print(f"{'New' if seen is None else 'Updated'}: {o['id']} ({o['status']}) {o['design_name']} x{o['quantity']} -> {target}")

    state_file.write_text(json.dumps(state, indent=2))
    print(f"{fetched} order(s) copied; {len(listing['orders'])} on the site." if fetched else "No new orders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
