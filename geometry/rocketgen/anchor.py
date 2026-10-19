"""Shock-cord strap (anchorStrapGeometry, buildAnchorStrap).

The strap sits on the inside wall at the top of the body's top piece, just
under the nose's socket, so it can be reached through the open top with the
nose off. Since 2026-10-19 (owner's request) that piece is whichever body
part is on top: the fin can itself when the body prints in one piece, else
the top body segment. Before, the body always ended in a separate short
"anchor section" (the FeatureScript's anchor-section branch) just to hold
the strap: one more joint, shoulder and print. The strap and its clearances
are unchanged; only where it lives moved. The cord's lower end is clipped on
with a snap swivel or tied round the bar, through the open top.

The strap is a straight bar across the bore, a chord from wall to wall,
standing hole_depth off the wall at its middle. The cord drops in from the
open top behind the bar and comes back up in front (2026-10-09, owner's
request; the FeatureScript's bar runs vertically with the cord threaded
sideways).

It prints upright with no supports. Seen from the axis, the bar's underside
is a 45-degree pointed arch springing from the wall at both ends, where the
bar thins to nothing against the curved wall, so every layer sits on the
wall or on the layer below. 2 mm of bar stands above the arch's apex, which is rounded (APEX_FILLET)
so it isn't a stress riser. The
ends run half a wall into the wall and never break through the outside.
"""

from __future__ import annotations

import math

from build123d import Face, Solid, Vector, Wire

from .geom import cylinder, intersect, one_solid, rotated_z, try_fillet
from .params import Derived, shock_cord

APEX_FILLET = 1.5  # radius of the round at the arch's peak


def anchor_strap_geometry(d: Derived) -> dict:
    ri = d.body_id / 2
    # Cord gap between the bar and the wall, at the middle: deep enough for a
    # round 1/8 in elastic or a flat one doubled back (params.SHOCK_CORDS);
    # it was 2.5 mm, sized for thin Kevlar, which elastic won't go through.
    hole_depth = shock_cord(d.mtr_d)["pass_d"]
    t = 2.0  # bar thickness: five 0.4 mm perimeters
    above_apex = 2.0  # bar height above the arch's apex
    gap = 2.0  # clear space between the strap and the nose's shoulder
    embed = d.wall / 2
    front = ri - hole_depth - t  # the bar's front face (distance from the axis)
    spring = math.sqrt(ri * ri - front * front)  # where the front face meets the wall
    # The arch springs just below the top of the 8-degree inner taper (the
    # taper barely narrows the cord gap there) and above the outer joint chamfer.
    # (Segment-local, shoulder at z = 0: the lowest the strap can sit in a
    # body segment. It is placed higher whenever the piece is longer, always
    # keeping `gap` under the nose's shoulder: strap_shift.)
    z_spring = max(d.shoulder_len + d.inner_taper_rise - 2.0, d.shoulder_len + d.joint_rise + 1.0)
    height = spring + above_apex  # spring line to the bar's top
    z_out_top = z_spring + height
    # The bar's top sits this far below the piece's top edge: the gap, then
    # the nose's shoulder + chamfer.
    top_drop = gap + d.nose_shoulder_len + d.nose_joint_rise
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
        "height": height,
        "gap": gap,
        "top_drop": top_drop,
        # The shortest body segment that can be the top piece (what the
        # separate anchor section's length was): strap, gap, nose socket.
        "sec_len": z_out_top + top_drop,
        # The shortest fin can that can be the top piece (a one-piece body).
        # Its strap stands above the motor stop (aft_socket_base: where the
        # plain bore starts) by as much as it would in a segment seated on
        # that socket, so a one-piece body keeps the open bore under the strap
        # (wadding, parachute) that the shortest aft + anchor section had,
        # and the shortest rocket that builds is the same height as before.
        "aft_len": d.aft_socket_base + z_out_top + top_drop,
    }


def strap_shift(s0: dict, seg_len: float) -> float:
    """How far above its lowest place (s0's z_spring, segment-local) the
    strap goes in a top piece `seg_len` long, so its top stays `gap` under
    the nose's shoulder. On the fin can (z = 0 at the tail) this is at least
    aft_socket_base, by plan_rocket's check against s0["aft_len"]."""
    return seg_len - s0["sec_len"]


def _yz_prism(pts, x0: float, x1: float) -> Solid:
    """Closed (y, z) polygon extruded along X from x0 to x1."""
    face = Face(Wire.make_polygon([Vector(x0, y, z) for y, z in pts], close=True))
    return Solid.extrude(face, Vector(x1 - x0, 0, 0))


def add_anchor_strap(segment, d: Derived, s0: dict, angle: float, z_shift: float):
    """Union the strap onto the top body piece (its local coordinates: the
    fin can's are world). Built on +X, then rotated. `z_shift` is
    strap_shift(): the strap moves up by it, keeping its place under the nose."""
    strap = anchor_strap(d, s0, z_shift)
    return one_solid(segment.fuse(rotated_z(strap, angle)), "top body piece + strap")


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
    strap = one_solid(slab.cut(gap).cut(arch), "anchor strap")
    # Round the arch's peak: a sharp notch where the bar is thinnest is a
    # stress riser under cord load (owner, 2026-10-09). The rounded top is a
    # ~2 mm bridge, which prints fine. Cosmetic-style: skipped if it won't build.
    apex = [ed for ed in strap.edges()
            if abs(ed.center().Y) < 1e-6 and abs(ed.center().Z - (z0 + Y)) < 1e-6]
    if apex:
        strap = try_fillet(strap, APEX_FILLET, apex) or strap
    return strap
