"""Body segments and the nose cone (buildBodySegment, buildNoseCone,
noseRadiusAt). Built in local coordinates, shoulder at z = 0, which is also
their print orientation; build.py moves them into place.
"""

from __future__ import annotations

import math

from build123d import Edge, Face, Solid, Vector, Wire

from .geom import GeometryError, Z_AXIS, arc3, extrude_y_symmetric, one_solid, revolve
from .params import Derived


def body_segment(d: Derived, seg_len: float) -> Solid:
    """Open tube, shoulder on the bottom. Outer wall chamfers out at 45
    degrees above the shoulder; inner wall tapers out at 8 degrees; the top
    edge has a countersink matching the next part's outer chamfer."""
    sh = d.shoulder_len
    inner_sh_r = d.shoulder_od / 2 - d.wall
    return revolve([
        (inner_sh_r, 0),
        (d.shoulder_od / 2, 0),
        (d.shoulder_od / 2, sh),
        (d.body_od / 2, sh + d.joint_rise),
        (d.body_od / 2, seg_len),
        (d.body_id / 2, seg_len - d.wall),
        (d.body_id / 2, sh + d.inner_taper_rise),
        (inner_sh_r, sh),
    ])


def nose_radius_at(shape: str, x: float, L: float, R: float) -> float:
    """x measured from the tip, 0..L; R is the base radius."""
    if shape == "conical":
        return R * x / L
    if shape == "tangent_ogive":
        rho = (R * R + L * L) / (2 * R)
        return math.sqrt(max(rho * rho - (L - x) ** 2, 0.0)) + R - rho
    if shape == "elliptical":
        frac = 1 - x / L
        return R * math.sqrt(max(1 - frac * frac, 0.0))
    if shape == "parabolic":
        frac = x / L
        return R * (2 * frac - frac * frac)
    if shape == "von_karman":
        theta = math.acos(1 - 2 * x / L)
        return (R / math.sqrt(math.pi)) * math.sqrt(max(theta - math.sin(2 * theta) / 2, 0.0))
    raise ValueError(f"Unknown nose shape {shape!r}")


def nose_cone(d: Derived, shape: str, nose_len: float) -> Solid:
    """Shoulder on the bottom, then the profile up to a true sharp tip.

    One two-sided cross-section (outer surface up to the tip, wall-offset
    inner surface back down) rather than a shell, so the tip stays a solid
    plug where the wall would be too thin. Polyline of 16 steps, as in the
    FeatureScript. The shoulder bottom is closed by a cap with a domed
    recess and a 2 x 2 mm tie bar for the shock cord.
    """
    sh = d.nose_shoulder_len
    R = d.body_od / 2
    L = nose_len
    wall = d.wall
    steps = 16
    base = sh + d.joint_rise

    outer = [(nose_radius_at(shape, L * i / steps, L, R), base + L - L * i / steps) for i in range(steps + 1)]
    outer.reverse()  # base -> tip
    inner = []
    for i in range(steps + 1):
        x = L * i / steps
        rc = nose_radius_at(shape, x, L, R) - wall
        if rc > 0:
            inner.append((rc, base + L - x))
    if len(inner) < 2:
        raise GeometryError("This nose is too thin for the current wall thickness. Increase nose fineness or reduce wall.")
    plug_z = inner[0][1]
    inner_sh_r = d.shoulder_od / 2 - wall
    pts = [(inner_sh_r, 0), (d.shoulder_od / 2, 0), (d.shoulder_od / 2, sh)]
    pts += outer
    pts.append((0, plug_z))
    pts += inner
    pts.append((inner_sh_r, sh))
    nose = revolve(pts)

    # Shoulder cap: plate with a spherical dome over a recess open from
    # below; both arcs share one centre on the axis so the shell is uniform.
    cap_t = 1.5
    cap_r = inner_sh_r + wall / 2
    rd = min(0.8 * inner_sh_r, inner_sh_r - cap_t - 0.3)
    hr = 0.8 * rd
    rho = (rd * rd + hr * hr) / (2 * hr)
    c = hr - rho
    rho_out = rho + cap_t
    r_out_base = math.sqrt(rho_out ** 2 - (cap_t - c) ** 2)
    alpha = math.atan2(rd, -c)
    beta = math.atan2(r_out_base, cap_t - c)
    P = lambda r, z: Vector(r, 0, z)  # noqa: E731
    edges = [
        Edge.make_line(P(rd, 0), P(cap_r, 0)),
        Edge.make_line(P(cap_r, 0), P(cap_r, cap_t)),
        Edge.make_line(P(cap_r, cap_t), P(r_out_base, cap_t)),
        arc3((r_out_base, 0, cap_t), (rho_out * math.sin(beta / 2), 0, c + rho_out * math.cos(beta / 2)), (0, 0, hr + cap_t)),
        Edge.make_line(P(0, hr + cap_t), P(0, hr)),
        arc3((0, 0, hr), (rho * math.sin(alpha / 2), 0, c + rho * math.cos(alpha / 2)), (rd, 0, 0)),
    ]
    cap = Solid.revolve(Face(Wire(edges)), 360, Z_AXIS)

    # Tie bar across the recess, ends buried where the outer dome is still
    # bar_h + 0.3 mm tall, never inside the recess edge.
    bar_h = 2.0
    z_clear = bar_h + 0.3
    r_buried = math.sqrt(rho_out ** 2 - (z_clear - c) ** 2)
    half = max(rd + 0.3, min(rd + 1, r_buried))
    bar = extrude_y_symmetric([(-half, 0), (half, 0), (half, bar_h), (-half, bar_h)], 2.0)
    return one_solid(nose.fuse(cap).fuse(bar), "nose")
