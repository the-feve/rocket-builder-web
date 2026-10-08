"""Launch lugs and the rod standoff (lugGeometry, buildRodStandoff,
planForwardLug, buildOneLug, lugEdgeFillets).

Lugs are kept as light as possible: a short ring (rod + 0.3 mm radial
clearance, 0.8 mm wall) on a narrow stem flared into the body and the ring
by small concave arcs, all on one line at `angle` so the rod runs straight
through. The stem lets the ring stand off the body to clear the motor cap.
The aft lug sits on the tail (z = 0 up); the forward lug has a 45-degree
underside sloping into the body so it prints without supports.
"""

from __future__ import annotations

import math

from build123d import Face, Solid, Vector

from .geom import GeometryError, as_shape, extrude_y_symmetric, one_solid, rotated_z, try_fillet, xy_wire_edges
from .params import Derived


def lug_geometry(d: Derived, rod_diameter: float, rod_standoff: bool, pad_clearance: float) -> dict:
    bore_r = rod_diameter / 2 + 0.3
    ring_wall = 0.8  # two 0.4 mm perimeters
    r_in = d.body_od / 2 - d.wall / 2  # neck buried half a wall into the body
    # The ring just clears the body, unless the rod would then hit the
    # motor cap below the tail: then the rod line moves out to clear the
    # cap's ribs by 0.5 mm, plus the standoff's wall when that part is on.
    rod_r = rod_diameter / 2
    standoff_wall = 1.2
    standoff_ri = rod_r - d.fit_press  # snug on the rod
    cap_clear_r = d.thread["r_cap_max"] + 0.5 + (standoff_ri + standoff_wall if rod_standoff else rod_r)
    center_r = max(d.body_od / 2 + ring_wall + bore_r, cap_clear_r)
    outer_r = center_r + bore_r + ring_wall
    return {
        "len": 6.35,  # ~0.25", sturdier than the 3 mm first print
        "bore_r": bore_r,
        "ring_r": bore_r + ring_wall,
        "fillet_r": 1.5,  # concave blends at the body and the ring
        "neck_half_w": 1.5,  # 3 mm wide stem
        "r_in": r_in,
        "center_r": center_r,
        "outer_r": outer_r,
        "ramp": outer_r - r_in,  # height of the forward lug's 45-degree underside
        "standoff_ri": standoff_ri,
        "standoff_ro": standoff_ri + standoff_wall,
        # Down past the rocket's lowest point by the pad clearance.
        "standoff_h": -d.thread["z_lowest"] + pad_clearance if rod_standoff else 8.0,
        "standoff_slit": 1.2 * rod_r,  # snap-on opening, a bit narrower than the rod
    }


def rod_standoff(lug: dict, angle: float) -> Solid:
    """C-clip around the launch rod, just under the aft lug (z = -h .. 0),
    its opening facing away from the rocket. A separate part: it stands on
    the blast deflector and the aft lug rests on its top."""
    h = lug["standoff_h"]
    c = lug["center_r"]
    ring = Solid.make_cylinder(lug["standoff_ro"], h).translate((c, 0, -h))
    hole = Solid.make_cylinder(lug["standoff_ri"], h + 2).translate((c, 0, -h - 1))
    w = lug["standoff_slit"]
    slit = Solid.make_box(lug["standoff_ro"] + 1, w, h + 2).translate((c, -w / 2, -h - 1))
    return rotated_z(one_solid(ring.cut(hole).cut(slit), "rod standoff"), angle)


def plan_forward_lug(forward_lug_frac: float, body_parts: list[dict], lug: dict) -> dict:
    """{index (into body_parts), z0 (top of its ramp), z1 (its top)}: centred
    at the fraction of the body tube's length, shifted to sit wholly on one
    part, 1 mm clear of its ends and (on the aft part) above the aft lug."""
    gap = 1.0
    zc = forward_lug_frac * body_parts[-1]["hi"]
    index = len(body_parts) - 1
    for i, p in enumerate(body_parts):
        if p["lo"] <= zc < p["hi"]:
            index = i
            break
    part = body_parts[index]
    min_lo = lug["len"] + 5 if index == 0 else part["lo"] + gap
    lo = max(zc - lug["len"] / 2 - lug["ramp"], min_lo)
    hi = lo + lug["ramp"] + lug["len"]
    if hi > part["hi"] - gap:
        hi = part["hi"] - gap
        lo = hi - lug["len"] - lug["ramp"]
    if lo < min_lo:
        raise GeometryError("No room for the forward launch lug on the body part at that position. "
                            "Move the forward lug position, lengthen the body, or choose Aft only.")
    return {"index": index, "z0": lo + lug["ramp"], "z1": hi}


def _lug_outline(d: Derived, lug: dict, z: float) -> Face:
    """Ring + stem seen from above, at height z, on +X. The stem's flat
    sides run along y = +-w and flare into the body (radius R) and the ring
    (radius a) through fillet arcs of radius f. If the ring is too close to
    the body for both flares, the stem is as wide as the ring (no ring
    flare). Closes just inside the body wall so the union fuses."""
    R = d.body_od / 2
    a = lug["ring_r"]
    f = lug["fillet_r"]
    C = (lug["center_r"], 0.0)
    w = lug["neck_half_w"]
    px = math.sqrt((R + f) ** 2 - (w + f) ** 2)
    x3 = lug["center_r"] - math.sqrt((a + f) ** 2 - (w + f) ** 2)
    ring_flare = x3 > px
    if not ring_flare:
        w = a
        px = math.sqrt((R + f) ** 2 - (a + f) ** 2)

    def unit(vx, vy):
        n = math.hypot(vx, vy)
        return vx / n, vy / n

    sides = []
    for s in (1, -1):
        P = (px, s * (w + f))
        T1 = (P[0] * R / (R + f), P[1] * R / (R + f))
        T2 = (px, s * w)
        P2 = (x3, s * (w + f))
        T4 = (C[0] + (P2[0] - C[0]) * a / (a + f), C[1] + (P2[1] - C[1]) * a / (a + f))
        T3 = (x3, s * w) if ring_flare else (lug["center_r"], s * a)
        u = unit(T1[0] - P[0] + T2[0] - P[0], T1[1] - P[1] + T2[1] - P[1])
        mid = (P[0] + u[0] * f, P[1] + u[1] * f)
        u2 = unit(x3 - P2[0] + T4[0] - P2[0], s * w - P2[1] + T4[1] - P2[1])
        mid2 = (P2[0] + u2[0] * f, P2[1] + u2[1] * f)
        Q = (T1[0] * lug["r_in"] / R, T1[1] * lug["r_in"] / R)
        sides.append(dict(T1=T1, T2=T2, T3=T3, T4=T4, mid=mid, mid2=mid2, Q=Q))

    p3 = lambda q: (q[0], q[1], z)  # noqa: E731
    A, B = sides
    items = [("arc", p3(A["T1"]), p3(A["mid"]), p3(A["T2"])), ("line", p3(A["T2"]), p3(A["T3"]))]
    end_a, end_b = A["T3"], B["T3"]
    if ring_flare:
        items.append(("arc", p3(A["T3"]), p3(A["mid2"]), p3(A["T4"])))
        end_a, end_b = A["T4"], B["T4"]
    items += [("line", p3(end_a), p3(C)), ("line", p3(C), p3(end_b))]
    if ring_flare:
        items.append(("arc", p3(B["T4"]), p3(B["mid2"]), p3(B["T3"])))
    items += [
        ("line", p3(B["T3"]), p3(B["T2"])),
        ("arc", p3(B["T2"]), p3(B["mid"]), p3(B["T1"])),
        ("line", p3(B["T1"]), p3(B["Q"])),
        ("line", p3(B["Q"]), p3(A["Q"])),
        ("line", p3(A["Q"]), p3(A["T1"])),
    ]
    return Face(xy_wire_edges(items))


def add_lug(part: Solid, d: Derived, lug: dict, z0: float, z1: float, with_ramp: bool, angle: float) -> Solid:
    """buildOneLug: a lug (rounded on its own, see round_lug_block) unioned
    onto `part` (world coordinates), then bored."""
    z_bottom = z0 - lug["ramp"] if with_ramp else z0
    height = z1 - z_bottom
    stem = Solid.extrude(_lug_outline(d, lug, z_bottom), Vector(0, 0, height))
    ring = Solid.make_cylinder(lug["ring_r"], height).translate((lug["center_r"], 0, z_bottom))
    block = as_shape(stem.fuse(ring))
    if with_ramp:
        # Everything below a 45-degree plane from the body surface (r_in at
        # z_bottom) to the ring's outer edge (outer_r at z0).
        r_in, outer_r = lug["r_in"], lug["outer_r"]
        cut = extrude_y_symmetric([(r_in - 1, z_bottom - 1), (outer_r + 1, z_bottom - 1), (outer_r + 1, z0 + 1)],
                                  2 * (lug["ring_r"] + 6))
        block = block.cut(cut)
    block = round_lug_block(one_solid(as_shape(block).clean(), "lug block"), d, z1, with_ramp)
    bore = Solid.make_cylinder(lug["bore_r"], height + 2).translate((lug["center_r"], 0, z_bottom - 1))
    block, bore = rotated_z(block, angle), rotated_z(bore, angle)
    out = one_solid(part.fuse(block), "lug union").cut(bore)
    return one_solid(out, "lug bore")


def round_lug_block(block: Solid, d: Derived, z1: float, with_ramp: bool) -> Solid:
    """lugEdgeFillets, done on the lug block alone before the union: the
    top edges (and on the forward lug the 45-degree underside's edges) that
    lie outside the body get a 1 mm round, or 0.6 mm if 1 mm won't build.

    On the merged part OpenCascade failed every one of these at any radius
    (or built faces that couldn't be meshed), so this differs from Onshape
    in two ways: the concave edges where the lug meets the body stay sharp,
    and so does the forward lug's 3 mm underside-to-body fillet. Cosmetic:
    whatever won't build is skipped.
    """
    R = d.body_od / 2

    def outside(e):
        return min(math.hypot(p.X, p.Y) for p in (e.start_point(), e.end_point(), e.center())) > R - 1e-3

    def round_faces(solid, pick):
        faces = [f for f in solid.faces() if f.geom_type.name == "PLANE" and pick(f)]
        edges = [e for f in faces for e in f.edges() if outside(e)]
        for r in (1.0, 0.6):
            out = try_fillet(solid, r, edges)
            if out is not None:
                return out
        return solid

    block = round_faces(block, lambda f: f.normal_at().Z > 1 - 1e-6 and abs(f.center().Z - z1) < 0.01)
    if with_ramp:
        ramp_n = Vector(1, 0, -1).normalized()  # built on +X, rotated afterwards
        block = round_faces(block, lambda f: abs(f.normal_at().dot(ramp_n) - 1) < 1e-6)
    return block
