"""Paid printed-rocket orders: price, shipping estimate and Stripe Checkout.

Rocket Builder shares one Stripe account with the Quiver Design Works store
(the-feve/quiverdesignworks-site, docs/stripe-shared-account.md). Every
Checkout Session and PaymentIntent made here carries metadata.store =
"rocket-builder"; the store's checkout, alerts and admin ignore anything
else, and this app's webhook ignores anything not tagged rocket-builder. The
store's Pirate Ship export lists paid rocket orders too, from the package
metadata set here (weight_oz, box_in, description).

Prices and shipping come from shop.json, never from the browser. Customers
pay on Stripe's hosted page (card data never reaches this server); Stripe
collects the shipping address and Washington sales tax.

Settings: STRIPE_SECRET_KEY (a restricted key: Checkout Sessions write) turns
paid orders on; STRIPE_WEBHOOK_SECRET checks the webhook's signature.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG = json.loads((Path(__file__).resolve().parent / "shop.json").read_text())
STORE_KEY = "store"
STORE_ID = CONFIG["store"]
INCH = 25.4


def enabled() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY"))


def price_each_cents(printed_mass_g: float, cfg: dict = CONFIG) -> int:
    p = cfg["price"]
    raw = p["baseCents"] + p["perGramCents"] * printed_mass_g
    step = p.get("roundToCents") or 1
    return int(math.ceil(raw / step) * step)


def package(parts: list[dict], quantity: int, cfg: dict = CONFIG) -> dict:
    """The box and packed weight for `quantity` rockets. Parts lie down in the
    box: the longest must fit its length, the widest (the aft part, with its
    fins) its height, and all of them about 1.3x their bounding volume."""
    ship = cfg["shipping"]
    longest = max(p["height_mm"] for p in parts) / INCH + 0.5
    widest = max(p.get("width_mm", 0) for p in parts) / INCH + 0.25
    volume = 1.3 * quantity * sum((p["height_mm"] / INCH) * (p.get("width_mm", 0) / INCH) ** 2 for p in parts)
    boxes = sorted(ship["boxes"], key=lambda b: b["length"] * b["width"] * b["height"])
    fits = [b for b in boxes if b["length"] >= longest and min(b["width"], b["height"]) >= widest
            and b["length"] * b["width"] * b["height"] >= volume]
    box = fits[0] if fits else boxes[-1]
    weight_oz = sum(p["mass_g"] for p in parts) * quantity / 28.3495 + box["weightOz"] + ship.get("paddingOz", 0)
    return {"box": {k: box[k] for k in ("name", "length", "width", "height")}, "weight_oz": round(weight_oz, 1),
            "oversize": not fits}


def shipping_cents(pkg: dict, cfg: dict = CONFIG) -> int:
    b = pkg["box"]
    cubic = b["length"] * b["width"] * b["height"]
    billable = max(pkg["weight_oz"], cubic / 166 * 16 if cubic > 1728 else 0)
    for oz, cents in cfg["shipping"]["rates"]:
        if billable <= oz:
            return cents
    return cfg["shipping"]["rates"][-1][1]


def quote(parts: list[dict], printed_mass_g: float, quantity: int, cfg: dict = CONFIG) -> dict:
    each = price_each_cents(printed_mass_g, cfg)
    pkg = package(parts, quantity, cfg)
    ship = shipping_cents(pkg, cfg)
    return {"each_cents": each, "quantity": quantity, "subtotal_cents": each * quantity, "shipping_cents": ship,
            "total_before_tax_cents": each * quantity + ship, "package": pkg,
            "shipping_name": cfg["shipping"]["displayName"], "handling_days": cfg["shipping"]["handlingDays"],
            "min_days": cfg["shipping"]["minDays"], "max_days": cfg["shipping"]["maxDays"],
            "price_rule": {"base_cents": cfg["price"]["baseCents"], "per_gram_cents": cfg["price"]["perGramCents"]},
            "paid_enabled": enabled()}


def session_params(order: dict, q: dict, origin: str, cfg: dict = CONFIG) -> dict:
    """Checkout Session parameters for a pending order (see the store's
    lib/checkout.js: same shape, its own tag)."""
    pkg = q["package"]
    b = pkg["box"]
    metadata = {STORE_KEY: STORE_ID, "order_id": order["id"], "order_name": order["name"],
                "weight_oz": str(pkg["weight_oz"]), "box_in": f"{b['length']}x{b['width']}x{b['height']}",
                "description": f"{q['quantity']}x printed rocket {order['name']}"[:200]}
    ship = cfg["shipping"]
    return {
        "mode": "payment",
        "line_items": [{
            "quantity": q["quantity"],
            "price_data": {
                "currency": cfg["currency"], "unit_amount": q["each_cents"], "tax_behavior": "exclusive",
                "product_data": {"name": f"Printed rocket: {order['design_name']}"[:250],
                                 "description": f"3D-printed parts, {order['material']}, colour: {order['color']}. "
                                                "Motor, parachute and glue not included."[:500],
                                 "tax_code": cfg["productTaxCode"], "metadata": {STORE_KEY: STORE_ID}},
            },
        }],
        "shipping_address_collection": {"allowed_countries": ship["countries"]},
        "automatic_tax": {"enabled": True},
        "adaptive_pricing": {"enabled": False},
        "billing_address_collection": "auto",
        "phone_number_collection": {"enabled": True},
        "customer_email": order["email"],
        "shipping_options": [{"shipping_rate_data": {
            "type": "fixed_amount", "display_name": ship["displayName"],
            "fixed_amount": {"amount": q["shipping_cents"], "currency": cfg["currency"]},
            "tax_behavior": "exclusive", "tax_code": ship["taxCode"],
            "delivery_estimate": {"minimum": {"unit": "business_day", "value": ship["minDays"] + ship["handlingDays"]},
                                  "maximum": {"unit": "business_day", "value": ship["maxDays"] + ship["handlingDays"]}},
        }}],
        "metadata": metadata,
        "payment_intent_data": {"metadata": metadata, "description": f"Rocket Builder order {order['name']}",
                                "statement_descriptor_suffix": cfg.get("statementDescriptorSuffix") or None},
        "client_reference_id": order["id"],
        "expires_at": int(time.time()) + 3600,  # an unpaid order is dropped after an hour
        "success_url": f"{origin}/?order={urllib.parse.quote(order['id'])}&paid=1",
        "cancel_url": f"{origin}/?order={urllib.parse.quote(order['id'])}&cancelled=1",
    }


def _form(params: dict, prefix: str = "") -> list[tuple[str, str]]:
    """Stripe's form encoding: a[b][0][c]=v. None is left out."""
    out = []
    items = params.items() if isinstance(params, dict) else enumerate(params)
    for k, v in items:
        key = f"{prefix}[{k}]" if prefix else str(k)
        if v is None:
            continue
        if isinstance(v, (dict, list, tuple)):
            out += _form(v, key)
        elif isinstance(v, bool):
            out.append((key, "true" if v else "false"))
        else:
            out.append((key, str(v)))
    return out


class StripeError(Exception):
    pass


def stripe_post(path: str, params: dict) -> dict:
    req = urllib.request.Request(f"https://api.stripe.com/v1/{path}", data=urllib.parse.urlencode(_form(params)).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['STRIPE_SECRET_KEY']}",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:300]
        raise StripeError(f"Stripe said {e.code}: {msg}") from None
    except urllib.error.URLError as e:
        raise StripeError(f"Couldn't reach Stripe: {e.reason}") from None


def create_session(order: dict, q: dict, origin: str) -> dict:
    return stripe_post("checkout/sessions", session_params(order, q, origin))


def verify_webhook(payload: bytes, header: str, secret: str, tolerance: int = 300, now: float | None = None) -> dict:
    """The event, if the Stripe-Signature header matches (HMAC-SHA256 of
    "<t>.<payload>" with the endpoint's signing secret, within 5 minutes)."""
    parts = dict(kv.split("=", 1) for kv in header.split(",") if "=" in kv)
    sigs = [v for k, v in (kv.split("=", 1) for kv in header.split(",") if "=" in kv) if k == "v1"]
    try:
        t = int(parts.get("t", ""))
    except ValueError:
        raise ValueError("No timestamp in the signature header.") from None
    if abs((now or time.time()) - t) > tolerance:
        raise ValueError("Webhook timestamp is too old.")
    expected = hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in sigs):
        raise ValueError("Webhook signature doesn't match.")
    return json.loads(payload)


def sign_for_tests(payload: bytes, secret: str, t: int | None = None) -> str:
    t = int(time.time()) if t is None else t
    return f"t={t},v1=" + hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
