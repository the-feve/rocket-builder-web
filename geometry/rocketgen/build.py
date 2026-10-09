"""build_rocket(params): the RocketGenerator feature's main body.

Returns every part in two placements: `local` (print orientation, sitting
on z = 0) and `assembled` (stacked as in the Onshape Part Studio).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from build123d import Solid

from .aft import build_aft
from .body import body_segment, nose_cone
from .fins import fin_dimensions
from .geom import GeometryError
from .anchor import add_anchor_strap, anchor_strap_geometry
from .lugs import add_lug, lug_geometry, plan_forward_lug, rod_standoff
from .params import LUG_OPTIONS, MATERIALS, NOSE_SHAPES, DesignParams, Derived, compute_derived
from .thread import threaded_cap


@dataclass
class Part:
    name: str
    assembled: Solid
    placement_z: float  # assembled = local moved up by this

    @property
    def local(self) -> Solid:
        """Print orientation, resting on z = 0."""
        s = self.assembled.translate((0, 0, -self.placement_z))
        return s.translate((0, 0, -s.bounding_box().min.Z))

    @property
    def volume(self) -> float:
        return self.assembled.volume


@dataclass
class Rocket:
    params: DesignParams
    derived: Derived
    parts: list[Part]
    seg_lens: list[float]
    notes: list[str] = field(default_factory=list)

    def mass_g(self) -> dict[str, float]:
        rho = MATERIALS[self.params.material] / 1000.0  # g/mm3
        return {p.name: p.volume * rho for p in self.parts}

    def summary(self) -> str:
        m = self.mass_g()
        detail = ", ".join(f"{k} {v:.1f} g" for k, v in m.items())
        t = self.derived.thread
        return (f"Estimated printed mass ({self.params.material}, solid): {sum(m.values()):.1f} g "
                f"[{detail}]. Motor hangs out {t['hang']:.1f} mm for {t['turns']:.1f} turns of {t['p']:.1f} mm thread.")


def seg_part_name(i: int, n_parts: int) -> str:
    return "Anchor_Seg" if i == n_parts - 1 else f"Seg_{i + 1}"


def plan_segments(params: DesignParams, d: Derived) -> list[float]:
    """Base segment is the printer's usable height; the rest of the body is
    split the same way, ending in the short anchor section under the nose.
    A leftover too short to be a segment is folded into the anchor section."""
    zmax = d.zmax
    joint_len = d.shoulder_len + d.joint_rise
    sec_len = anchor_strap_geometry(d)["sec_len"]
    remaining = params.body_length - sec_len
    if remaining < 10:
        raise GeometryError("Body length is too short for the aft segment plus the anchor section under the nose. Increase body length.")
    seg_lens = []
    while remaining > 1e-9:
        this = min(remaining, zmax)
        seg_lens.append(this)
        remaining -= this
    anchor_len = sec_len
    if len(seg_lens) > 1 and seg_lens[-1] < d.shoulder_len + d.inner_taper_rise + joint_len + 5:
        anchor_len += seg_lens.pop()
        if anchor_len > zmax:
            raise GeometryError("The anchor section under the nose would be taller than the printer's usable Z height. Adjust body length or printer max height.")
    seg_lens.append(anchor_len)
    return seg_lens


def overall_length(params: DesignParams) -> float:
    """Nose tip to the lowest point (motor cap face or fin tips), without
    building any solids. Matches stability.Balance.length for the same
    params: the body parts stack to body_length minus one joint overlap per
    joint above the aft part, and the nose tip sits nose_len above the
    top of the body (the nose shoulder fills the last joint)."""
    d = compute_derived(params)
    seg_lens = plan_segments(params, d)
    joint_len = d.shoulder_len + d.joint_rise
    z_tip = sum(seg_lens) - (len(seg_lens) - 1) * joint_len + params.nose_fineness * d.cal
    return z_tip - min(0.0, d.thread["z_lowest"])


def body_length_for(params: DesignParams, overall: float) -> float:
    """The body_length that makes the rocket `overall` mm long (the
    website's beginner mode asks for overall height). The number of body
    segments depends on the body length, so step until it settles."""
    b = params.body_length
    for _ in range(12):
        try:
            nb = b + overall - overall_length(params.with_(body_length=b))
        except GeometryError:
            raise GeometryError(f"An overall height of {overall:.0f} mm is too short for the {params.motor} motor bay "
                                "and nose. Make the rocket taller.") from None
        if abs(nb - b) < 0.05:
            return round(nb, 1)
        b = nb
    return round(b, 1)


def build_rocket(params: DesignParams) -> Rocket:
    if params.nose_shape not in NOSE_SHAPES:
        raise ValueError(f"Unknown nose shape {params.nose_shape!r}")
    if params.fin_count not in (3, 4, 5):
        raise ValueError("Fin count must be 3, 4 or 5")
    if params.launch_lugs not in LUG_OPTIONS:
        raise ValueError(f"Launch lugs must be one of {LUG_OPTIONS}")
    d = compute_derived(params)
    seg_lens = plan_segments(params, d)
    joint_len = d.shoulder_len + d.joint_rise
    seg_len = seg_lens[0]
    fin = fin_dimensions(params, d.cal)
    if seg_len < fin.root + 10:
        raise GeometryError("Aft segment is too short for this fin root chord. Increase body length, shorten the fins, or raise the printer max height.")
    if seg_len < d.aft_socket_base + joint_len:
        raise GeometryError("Aft segment is too short for the motor bay plus a full-depth socket above it. Increase body length or raise the printer max height.")

    # Every body part's id and exposed z-range, planned up front so the
    # forward lug can be placed before anything is built.
    n_parts = len(seg_lens)
    body_parts = [{"lo": 0.0, "hi": seg_len, "placement_z": 0.0}]
    top_z = seg_len
    for i in range(1, n_parts):
        # Seat the top of this part's outer chamfer flush with the previous part's top edge.
        placement_z = top_z - joint_len
        body_parts.append({"lo": top_z, "hi": placement_z + seg_lens[i], "placement_z": placement_z})
        top_z = placement_z + seg_lens[i]

    # Lugs between fins 0 and 1, on one line; the anchor strap at 90 degrees.
    lug_angle = 180 / params.fin_count
    anchor_angle = 90.0
    lug = None if params.launch_lugs == "none" else lug_geometry(d, params.rod_diameter, params.rod_standoff,
                                                                  params.pad_clearance)
    fwd = plan_forward_lug(params.forward_lug_frac, body_parts, lug) if params.launch_lugs == "two" else None

    aft = build_aft(d, seg_len, fin, params.fin_count)
    notes = list(aft.notes)
    solid = aft.solid
    if lug:
        solid = add_lug(solid, d, lug, 0.0, lug["len"], False, lug_angle)
    if fwd and fwd["index"] == 0:
        solid = add_lug(solid, d, lug, fwd["z0"], fwd["z1"], True, lug_angle)
    parts = [Part("Aft", solid, 0.0)]

    strap = anchor_strap_geometry(d)
    for i in range(1, n_parts):
        solid = body_segment(d, seg_lens[i])
        if i == n_parts - 1:
            solid = add_anchor_strap(solid, d, strap, anchor_angle, seg_lens[i] - strap["sec_len"])
        placement_z = body_parts[i]["placement_z"]
        solid = solid.translate((0, 0, placement_z))
        if fwd and fwd["index"] == i:
            solid = add_lug(solid, d, lug, fwd["z0"], fwd["z1"], True, lug_angle)
        parts.append(Part(seg_part_name(i, n_parts), solid, placement_z))

    nose_len = params.nose_fineness * d.cal
    if nose_len + joint_len > d.zmax:
        raise GeometryError("This nose (fineness x caliber + shoulder) is taller than the printer's usable Z height. Lower the nose fineness or raise the printer max height.")
    nose_z = top_z - joint_len
    parts.append(Part("Nose", nose_cone(d, params.nose_shape, nose_len).translate((0, 0, nose_z)), nose_z))
    # The cap prints face-down, which is how it is built; its placement is 0.
    parts.append(Part("Motor_Cap", threaded_cap(d.thread), 0.0))
    if lug and params.rod_standoff:
        parts.append(Part("Rod_Standoff", rod_standoff(lug, lug_angle), 0.0))
    for p in parts:
        if not p.assembled.is_valid:
            raise GeometryError(f"The {p.name} part came out as an unsound solid (geometry-engine bug); "
                                "try slightly different settings and report this design.")
    return Rocket(params, d, parts, seg_lens, notes)
