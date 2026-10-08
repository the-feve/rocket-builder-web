"""Shock-cord anchor section (anchorStrapGeometry, buildAnchorStrap).

The body's last section, right under the nose, is kept short so a strap on
its inside wall can be reached through the open top with the nose off.

The strap is a bridge on the wall: two pads buried half a wall into it and
a bar standing hole_depth off it; the cord threads behind the bar. In
section (depth x in from the bore, z up) the gap is a hexagon -- 45-degree
ramp in, straight, 45-degree ramp back -- and the bar is that outline
offset by t, so every face is vertical or 45 degrees and it prints
shoulder-down with no supports. The profile's four bends are rounded and
its side edges get a 0.6 mm round.
"""

from __future__ import annotations

import math

from .geom import edge_faces, extrude_y_symmetric, one_solid, rotated_z, try_fillet
from .params import Derived


def anchor_strap_geometry(d: Derived) -> dict:
    hole_depth = 2.5  # cord gap between the bar and the wall
    t = 1.6  # bar thickness: four 0.4 mm perimeters
    gap = 2.0
    # Top: where a 3 mm straight gap would put it if the strap started above
    # the taper (this sets the section's length). Bottom: at the foot of the
    # taper, 1 mm above the outer joint chamfer so the buried pad can't break
    # through the outside.
    z_out_top = d.shoulder_len + d.inner_taper_rise + gap + 2 * t * math.sqrt(2) + 2 * hole_depth + 3.0
    z_out_bot = d.shoulder_len + d.joint_rise + 1.0
    return {
        "hole_depth": hole_depth,
        "t": t,
        "bend_r": 2.5,  # inside radius of the profile's bends
        "width": 4.0,  # across the bore
        "embed": d.wall / 2,
        "z_out_bot": z_out_bot,
        "z_hole_bot": z_out_bot + t * math.sqrt(2),
        "z_hole_top": z_out_top - t * math.sqrt(2),
        "z_out_top": z_out_top,
        # Strap, then the gap, then the nose's shoulder + chamfer.
        "sec_len": z_out_top + gap + d.shoulder_len + d.joint_rise,
    }


def add_anchor_strap(segment, d: Derived, s0: dict, angle: float, z_shift: float):
    """Union the strap onto the anchor segment (local coordinates). Built on
    +X, then rotated. `z_shift` is how much longer the section is than
    sec_len; the strap moves up by it, keeping its place under the nose."""
    s = dict(s0)
    for k in ("z_out_bot", "z_hole_bot", "z_hole_top", "z_out_top"):
        s[k] = s0[k] + z_shift
    ri = d.body_id / 2
    e = s["embed"]
    D = s["hole_depth"] + s["t"]
    pt = lambda x, z: (ri - x, z)  # (depth in from the bore, z) -> (radius, z)  # noqa: E731

    bar = extrude_y_symmetric([pt(-e, s["z_out_bot"] - e), pt(D, s["z_out_bot"] + D),
                               pt(D, s["z_out_top"] - D), pt(-e, s["z_out_top"] + e)], s["width"])
    e2 = e + 0.2
    hd = s["hole_depth"]
    hole = extrude_y_symmetric([pt(-e2, s["z_hole_bot"] - e2), pt(hd, s["z_hole_bot"] + hd),
                                pt(hd, s["z_hole_top"] - hd), pt(-e2, s["z_hole_top"] + e2)], s["width"] + 2)
    bar = one_solid(bar.cut(hole), "anchor strap")

    # Round the four bends (edges running across the bar, found by their
    # midpoints), then the side edges. Cosmetic: skipped if they won't build.
    bends = [
        (pt(D, s["z_out_bot"] + D), s["bend_r"] + s["t"]),
        (pt(D, s["z_out_top"] - D), s["bend_r"] + s["t"]),
        (pt(hd, s["z_hole_bot"] + hd), s["bend_r"]),
        (pt(hd, s["z_hole_top"] - hd), s["bend_r"]),
    ]
    for (x, z), r in bends:
        edges = [ed for ed in bar.edges()
                 if abs(ed.center().X - x) < 1e-6 and abs(ed.center().Z - z) < 1e-6 and abs(ed.center().Y) < 1e-6]
        if len(edges) == 1:
            bar = try_fillet(bar, r, edges) or bar
    sides = [f for f in bar.faces() if f.geom_type.name == "PLANE" and abs(abs(f.normal_at().Y) - 1) < 1e-6]
    ef = edge_faces(bar)
    side_edges = list({e for f in sides for e in f.edges() if len(ef[e]) == 2})
    bar = try_fillet(bar, 0.6, side_edges) or bar
    return one_solid(segment.fuse(rotated_z(bar, angle)), "anchor segment + strap")
