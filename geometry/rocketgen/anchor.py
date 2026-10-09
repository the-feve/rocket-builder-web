"""Shock-cord anchor section (anchorStrapGeometry, buildAnchorStrap).

The body's last section, right under the nose, is kept short so a strap on
its inside wall can be reached through the open top with the nose off.

The strap is a straight bar across the bore, a chord from wall to wall,
standing hole_depth off the wall at its middle. The cord drops in from the
open top behind the bar and comes back up in front (2026-10-09, owner's
request; the FeatureScript's bar runs vertically with the cord threaded
sideways).

It prints upright with no supports. Seen from the axis, the bar's underside
is a 45-degree pointed arch springing from the wall at both ends, where the
bar thins to nothing against the curved wall, so every layer sits on the
wall or on the layer below. 2 mm of bar stands above the arch's apex. The
ends run half a wall into the wall and never break through the outside.
"""

from __future__ import annotations

import math

from build123d import Face, Solid, Vector, Wire

from .geom import cylinder, intersect, one_solid, rotated_z
from .params import Derived


def anchor_strap_geometry(d: Derived) -> dict:
    ri = d.body_id / 2
    hole_depth = 2.5  # cord gap between the bar and the wall, at the middle
    t = 2.0  # bar thickness: five 0.4 mm perimeters
    above_apex = 2.0  # bar height above the arch's apex
    gap = 2.0  # clear space between the strap and the nose's shoulder
    embed = d.wall / 2
    front = ri - hole_depth - t  # the bar's front face (distance from the axis)
    spring = math.sqrt(ri * ri - front * front)  # where the front face meets the wall
    # The arch springs just below the top of the 8-degree inner taper (the
    # taper barely narrows the cord gap there) and above the outer joint chamfer.
    z_spring = max(d.shoulder_len + d.inner_taper_rise - 2.0, d.shoulder_len + d.joint_rise + 1.0)
    z_out_top = z_spring + spring + above_apex
    return {
        "hole_depth": hole_depth,
        "t": t,
        "embed": embed,
        "front": front,
        "spring": spring,  # half the bar's length along its front face
        "cord_width": 2 * math.sqrt(ri * ri - (ri - hole_depth) ** 2),  # the gap behind the bar, across
        "z_spring": z_spring,
        "z_out_bot": z_spring,
        "z_out_top": z_out_top,
        # Strap, then the gap, then the nose's shoulder + chamfer.
        "sec_len": z_out_top + gap + d.nose_shoulder_len + d.joint_rise,
    }


def _yz_prism(pts, x0: float, x1: float) -> Solid:
    """Closed (y, z) polygon extruded along X from x0 to x1."""
    face = Face(Wire.make_polygon([Vector(x0, y, z) for y, z in pts], close=True))
    return Solid.extrude(face, Vector(x1 - x0, 0, 0))


def add_anchor_strap(segment, d: Derived, s0: dict, angle: float, z_shift: float):
    """Union the strap onto the anchor segment (local coordinates). Built on
    +X, then rotated. `z_shift` is how much longer the section is than
    sec_len; the strap moves up by it, keeping its place under the nose."""
    strap = anchor_strap(d, s0, z_shift)
    return one_solid(segment.fuse(rotated_z(strap, angle)), "anchor segment + strap")


def anchor_strap(d: Derived, s0: dict, z_shift: float = 0.0) -> Solid:
    """The strap on its own, centred on +X (segment-local coordinates)."""
    ri = d.body_id / 2
    e, hd, front, Y = s0["embed"], s0["hole_depth"], s0["front"], s0["spring"]
    z0 = s0["z_spring"] + z_shift
    zt = s0["z_out_top"] + z_shift
    # Everything in front of the wall's outer half (r <= ri + e) between the
    # bar's front face and the wall...
    slab = intersect(Solid.make_box(ri + e + 1 - front, 2 * (ri + e), zt - z0).translate((front, -(ri + e), z0)),
                     cylinder(ri + e, z0 - 1, zt + 1))
    # ...less the cord gap behind the bar (it reaches 0.05 mm into the wall:
    # a face lying exactly on the bore breaks the union with the segment)...
    gap = intersect(Solid.make_box(ri + 2 - (front + s0["t"]), 2 * ri + 2, zt - z0 + 20)
                    .translate((front + s0["t"], -ri - 1, z0 - 10)),
                    cylinder(ri + 0.05, z0 - 10, zt + 10))
    # ...and less everything under the 45-degree pointed arch.
    arch = _yz_prism([(-Y, z0 - 1), (Y, z0 - 1), (Y, z0), (0, z0 + Y), (-Y, z0)], front - 1, ri + e + 1)
    return one_solid(slab.cut(gap).cut(arch), "anchor strap")
