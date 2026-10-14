"""Print orders: someone signed in asks for a printed copy of their rocket.

Each order gets an id like RB-20261014-001 and belongs to a batch, the day it
came in (B20261014), so a day's prints can be planned together. Its files go
to ORDERS_DIR/<batch>/<order id>/:

    ORDER.txt        the batch sheet: order, customer, shipping, parts to print
    order.json       the same, machine-readable
    *.stl            the parts, in print orientation
    build_notes.txt  from the rocket ZIP
    design.json      the design, to rebuild it later

The order record itself is in the designs SQLite file (`orders` table).
tools/sync_orders.py copies new order folders to the owner's PC.

Payment isn't built yet: an order needs a valid coupon code
(ROCKETGEN_COUPON_CODES, comma-separated) and is then free.
"""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import designs

ORDERS_DIR = Path(os.environ.get("ROCKETGEN_ORDERS_DIR", Path(__file__).resolve().parent / "data" / "orders"))
STATUSES = ("new", "printing", "shipped", "cancelled")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    batch TEXT NOT NULL,
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
)
"""


def _db():
    con = designs._db()
    con.execute(_SCHEMA)
    return con


def coupon_codes() -> set[str]:
    return {c.strip().upper() for c in os.environ.get("ROCKETGEN_COUPON_CODES", "").split(",") if c.strip()}


def coupon_ok(code: str | None) -> bool:
    return bool(code) and code.strip().upper() in coupon_codes()


def folder(order: dict) -> Path:
    return ORDERS_DIR / order["batch"] / order["id"]


def _public(row) -> dict:
    return {"id": row["id"], "batch": row["batch"], "email": row["email"], "status": row["status"],
            "created_at": row["created_at"], "updated_at": row["updated_at"], **json.loads(row["data"])}


def _sheet(o: dict) -> str:
    s = o["shipping"]
    when = datetime.fromtimestamp(o["created_at"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"ROCKET BUILDER PRINT ORDER {o['id']}", f"Batch {o['batch']}   Received {when}   Status {o['status']}", "",
             f"Rocket: {o['design_name']}" + (f"   (saved design /d/{o['design_id']})" if o.get("design_id") else ""),
             f"Quantity: {o['quantity']}   Filament: {o['material']}   Colour: {o['color']}",
             f"Price: ${o['price']:.2f}" + (f" (coupon {o['coupon']})" if o.get("coupon") else ""), "",
             "Customer", f"  {o['email']}", "", "Ship to", f"  {s['name']}", f"  {s['line1']}"]
    if s.get("line2"):
        lines.append(f"  {s['line2']}")
    lines += [f"  {s['city']}, {s['state']} {s['zip']}", f"  {s.get('country') or 'USA'}"]
    if s.get("phone"):
        lines.append(f"  Phone {s['phone']}")
    if o.get("notes"):
        lines += ["", "Notes from the customer", f"  {o['notes']}"]
    lines += ["", f"Parts to print (x{o['quantity']} each):"]
    lines += [f"  [ ] {p['name']}.stl  {p['height_mm']} mm tall, {p['mass_g']} g" for p in o["parts"]]
    st = o["stability"]
    lines += ["", f"Stability: {st['margin_cal']} cal ({st['status']}) with a loaded {st.get('motor', '')}",
              f"Recommended motor: {o.get('recommended_motor') or 'none'}", "",
              "Build notes, design.json and the STLs are in this folder."]
    return "\n".join(lines) + "\n"


def create(*, user: dict, design_name: str, design_id: str | None, params: dict, quantity: int, material: str,
           color: str, shipping: dict, notes: str, coupon: str | None, price: float, rocket_zip: bytes,
           parts: list[dict], stability: dict, recommended_motor: str | None) -> dict:
    now = time.time()
    day = datetime.fromtimestamp(now, timezone.utc).strftime("%Y%m%d")
    data = {"design_name": design_name, "design_id": design_id, "params": params, "quantity": quantity,
            "material": material, "color": color, "shipping": shipping, "notes": notes,
            "coupon": coupon.strip().upper() if coupon else None, "price": price,
            "parts": [{"name": p["name"], "height_mm": p["height_mm"], "mass_g": p["mass_g"]} for p in parts],
            "stability": stability, "recommended_motor": recommended_motor}
    with _db() as con:
        con.execute("BEGIN IMMEDIATE")  # the day's sequence number can't be taken twice
        n = con.execute("SELECT COUNT(*) FROM orders WHERE batch = ?", (f"B{day}",)).fetchone()[0] + 1
        order_id = f"RB-{day}-{n:03d}"
        con.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (order_id, f"B{day}", user["id"], user["email"], "new", json.dumps(data), now, now))
    order = get(order_id)
    write_folder(order, rocket_zip)
    return order


def write_folder(order: dict, rocket_zip: bytes) -> Path:
    d = folder(order)
    d.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(rocket_zip)) as z:
        for name in z.namelist():
            if "/" not in name and not name.startswith("."):
                (d / name).write_bytes(z.read(name))
    (d / "order.json").write_text(json.dumps(order, indent=2))
    (d / "ORDER.txt").write_text(_sheet(order))
    return d


def get(order_id: str) -> dict | None:
    with _db() as con:
        row = con.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _public(row) if row else None


def list_for_user(user_id: str) -> list[dict]:
    with _db() as con:
        rows = con.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    return [_public(r) for r in rows]


def list_all(since: float = 0) -> list[dict]:
    with _db() as con:
        rows = con.execute("SELECT * FROM orders WHERE updated_at > ? ORDER BY created_at DESC", (since,)).fetchall()
    return [_public(r) for r in rows]


def set_status(order_id: str, status: str) -> dict | None:
    if status not in STATUSES:
        raise ValueError(f"Status must be one of {', '.join(STATUSES)}.")
    with _db() as con:
        con.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (status, time.time(), order_id))
    order = get(order_id)
    if order and folder(order).is_dir():  # keep the sheet in step
        (folder(order) / "order.json").write_text(json.dumps(order, indent=2))
        (folder(order) / "ORDER.txt").write_text(_sheet(order))
    return order


def folder_zip(order: dict) -> bytes:
    """The order folder as a ZIP (for the admin page and the PC sync)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder(order).glob("*")):
            if f.is_file():
                z.write(f, f.name)
    return buf.getvalue()
