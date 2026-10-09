"""Shock-cord anchor section (anchorStrapGeometry, buildAnchorStrap).

The body's last section, right under the nose, is kept short so a strap on
its inside wall can be reached through the open top with the nose off.

The strap is a horizontal bridge across a vertical cord channel, so the cord
drops straight down behind the bar from the open top and comes back up in
front (2026-10-09, owner's request; the FeatureScript's bar runs vertically
with the cord threaded sideways). Seen from the axis: two pads, half buried
in the wall, carry a bar that stands hole_depth off the wall.

It prints upright with no supports: its whole underside is a 45-degree cone
rising inward from the bore wall, the underside of the bar between the pads
is a 45-degree pointed arch, and every other face is vertical or faces up.
Its back is trimmed to the bore cylinder plus half a wall, so on small tubes
it follows the curve and never breaks through the outside.
"""

from __future__ import annotations

from build123d import Face, Solid, Vector, Wire

from .geom import cylinder, intersect, one_solid, revolve, rotated_z
from .params import Derived


def anchor_strap_geometry(d: Derived) -> dict:
    hole_depth = 2.5  # cord gap between the bar and the wall
    t = 2.0  # bar thickness (radial): five 0.4 mm perimeters
    width = min(8.0, max(4.0, 0.4 * d.body_id))  # cord channel, across the bore
    pad = 2.5  # each pad, beside the channel
    gap = 2.0  # clear space between the strap and the nose's shoulder
    above_bar = 3.0  # bar height above the arch's apex
    embed = d.wall / 2
    depth = hole_depth + t
    # The cone under the strap meets the bore wall here: just below the top
    # of the 8-degree inner taper, so the taper barely narrows the channel,
    # and its buried edge (embed lower) stays above the outer joint chamfer.
    z_cone = max(d.shoulder_len + d.inner_taper_rise - 2.0, d.shoulder_len + d.joint_rise + 1.0 + embed)
    z_arch = z_cone + depth  # bar underside at the channel's edges (the cone's height at the bar's face)
    z_out_top = z_arch + width / 2 + above_bar
    return {
        "hole_depth": hole_depth,
        "t": t,
        "depth": depth,
        "width": width,
        "half_span": width / 2 + pad,
        "embed": embed,
        "z_cone": z_cone,
        "z_arch": z_arch,
        "z_out_bot": z_cone - embed,  # lowest (buried) point
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
    s = dict(s0)
    for k in ("z_cone", "z_arch", "z_out_bot", "z_out_top"):
        s[k] = s0[k] + z_shift
    ri = d.body_id / 2
    e, D, hd, w, a = s["embed"], s["depth"], s["hole_depth"], s["width"], s["half_span"]
    z0, zt = s["z_out_bot"], s["z_out_top"]

    # Everything above a 45-degree cone that rises inward from the bore wall,
    # and no further out than half a wall.
    above_cone = revolve([(0, s["z_cone"] + ri), (ri + e, z0), (ri + e, zt), (0, zt)])
    envelope = Solid.make_box(D + e + 3.0, 2 * a, zt - z0 + 1.0).translate((ri - D, -a, z0 - 0.5))
    block = intersect(envelope, above_cone)

    # The cord channel between the bar and the wall, open top and bottom. It
    # reaches 0.05 mm into the wall: a face lying exactly on the bore breaks
    # the union with the segment (an unsound solid) where the bore is straight.
    channel = intersect(Solid.make_box(hd + e + 3.0, w, zt - z0 + 20.0).translate((ri - hd, -w / 2, z0 - 10.0)),
                        cylinder(ri + 0.05, z0 - 10.0, zt + 10.0))
    # The bar's underside between the pads: a 45-degree pointed arch.
    za = s["z_arch"]
    arch = _yz_prism([(-w / 2, z0 - 1.0), (w / 2, z0 - 1.0), (w / 2, za), (0, za + w / 2), (-w / 2, za)],
                     ri - D - 1.0, ri - hd + 0.01)
    return one_solid(block.cut(channel).cut(arch), "anchor strap")
