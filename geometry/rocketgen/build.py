"""build_rocket(params): the RocketGenerator feature's main body.

Returns every part in two placements: `local` (print orientation, sitting
on z = 0) and `assembled` (stacked as in the Onshape Part Studio).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from build123d import Solid

from .aft import build_aft
from .body import body_segment, nose_cone, nose_recess
from .fins import fin_dimensions
from .geom import GeometryError
from .anchor import add_anchor_strap, anchor_strap_geometry, strap_shift
from .lugs import add_lug, lug_geometry, plan_forward_lug, rod_standoff
from .params import LUG_OPTIONS, MATERIALS, NOSE_SHAPES, DesignParams, Derived, compute_derived, shock_cord
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
    # Where the shock-cord strap is: {"part", "angle_deg", "z_bot", "z_top"}
    # (assembled z of its spring line and its top).
    strap: dict = field(default_factory=dict)

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
    """Body parts from the tail up: "Aft" (the fin can), "Seg_2"... in the
    middle, "Top_Seg" on top (it carries the shock-cord strap). A one-piece
    body is just "Aft", with the strap in its top. Until 2026-10-19 the top
    piece was always a separate short "Anchor_Seg"."""
    if i == 0:
        return "Aft"
    return "Top_Seg" if i == n_parts - 1 else f"Seg_{i + 1}"


def plan_segments(params: DesignParams, d: Derived) -> list[float]:
    """Printed lengths of the body parts, aft first; they add up to
    body_length. A body that fits the printer is one piece: the fin can,
    with the shock-cord strap in its top (plan_rocket checks it is long
    enough). A longer one has the printer's usable height as its aft part
    and the rest split the same way; the top piece carries the strap, so it
    is at least the strap's sec_len, taken from the piece below if the
    leftover is shorter.

    (Before 2026-10-19 the body always ended in a separate short anchor
    section holding the strap, so a body that fitted the printer was still
    two prints and one more joint.)"""
    zmax = d.zmax
    sec_len = anchor_strap_geometry(d)["sec_len"]
    remaining = params.body_length
    if remaining <= zmax + 1e-9:
        return [remaining]
    if sec_len > zmax:
        raise GeometryError("The top body section (the shock-cord strap under the nose's socket) would be taller than "
                            "the printer's usable Z height. Raise the printer max height.")
    seg_lens = []
    while remaining > zmax + 1e-9:
        seg_lens.append(zmax)
        remaining -= zmax
    seg_lens.append(remaining)
    if seg_lens[-1] < sec_len:
        short = sec_len - seg_lens[-1]
        seg_lens[-2] -= short
        seg_lens[-1] = sec_len
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
    too_short = GeometryError(f"An overall height of {overall:.0f} mm is too short for the {params.motor} motor bay "
                              "and nose. Make the rocket taller.")
    b = params.body_length
    for _ in range(12):
        try:
            nb = b + overall - overall_length(params.with_(body_length=b))
        except GeometryError:
            raise too_short from None
        if abs(nb - b) < 0.05:
            break
        b = nb
    # overall_length no longer raises for a body too short to hold anything
    # (it did while the body always ended in an anchor section; 2026-10-19):
    # refuse nonsense here, and leave a near miss to plan_rocket's message.
    if nb < 10:
        raise too_short
    return round(nb, 1)


@dataclass
class Plan:
    """Everything build_rocket works out before making any solid."""
    d: Derived
    seg_lens: list[float]
    joint_len: float
    fin: object
    body_parts: list[dict]
    lug: dict | None
    fwd: dict | None
    nose_len: float
    nose_joint: float


def plan_rocket(params: DesignParams) -> Plan:
    """build_rocket's checks without building solids (milliseconds), so the
    website can tell which heights will build before anyone presses Build.
    Raises the same GeometryError messages build_rocket would."""
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
    if len(seg_lens) == 1 and seg_len < anchor_strap_geometry(d)["aft_len"] - 1e-9:
        raise GeometryError("Aft segment is too short for the motor bay plus the shock-cord strap and the nose's "
                            "socket above it. Increase body length.")
    if seg_len < fin.root + 10:
        raise GeometryError("Aft segment is too short for this fin root chord. Increase body length, shorten the fins, or raise the printer max height.")
    if len(seg_lens) > 1 and seg_len < d.aft_socket_base + joint_len:
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

    lug = None if params.launch_lugs == "none" else lug_geometry(d, params.rod_diameter, params.rod_standoff,
                                                                  params.pad_clearance)
    fwd = plan_forward_lug(params.forward_lug_frac, body_parts, lug) if params.launch_lugs == "two" else None

    nose_len = params.nose_fineness * d.cal
    nose_joint = d.nose_shoulder_len + d.nose_joint_rise
    if nose_len + nose_joint > d.zmax:
        raise GeometryError("This nose (fineness x caliber + shoulder) is taller than the printer's usable Z height. Lower the nose fineness or raise the printer max height.")
    return Plan(d, seg_lens, joint_len, fin, body_parts, lug, fwd, nose_len, nose_joint)


def height_ok(params: DesignParams, overall: float, fin_scales: tuple[float, ...] = (1.0,)) -> bool:
    """Whether a rocket `overall` mm tall builds with these settings (the
    plan checks only; body_length is worked out as the website does), at
    every one of `fin_scales`. Auto-sized fins trail further below the tail
    as they grow, which shortens the body for the same height, so the
    website checks both ends of the auto-size range (the checks only get
    stricter as the fins grow)."""
    try:
        for k in fin_scales:
            p = params.with_(fin_scale=k)
            b = body_length_for(p, overall)
            if not 50 <= b <= 2000:  # the form's Body length limits
                return False
            plan_rocket(p.with_(body_length=b))
        return True
    except GeometryError:
        return False


def height_ranges(params: DesignParams, lo: int = 80, hi: int = 2500,
                  fin_scales: tuple[float, ...] = (1.0,), step: int = 5) -> list[list[int]]:
    """The overall heights (whole mm, lo..hi) that build, as [first, last]
    ranges. Usually one range: too short leaves no room in the aft segment
    for the motor bay and fins; the top is the body-length limit. Heights in
    between that can't be split into printable segments show up as gaps.
    Scans every `step` mm and finds each edge to the mm (a gap narrower than
    `step` could be missed; 1 mm sweeps of every motor found none at all)."""
    ok = {}

    def good(h: int) -> bool:
        if h not in ok:
            ok[h] = height_ok(params, h, fin_scales)
        return ok[h]

    coarse = list(range(lo, hi, step)) + [hi]
    for a, b in zip(coarse, coarse[1:]):
        if good(a) != good(b):  # an edge in (a, b]: walk it
            for h in range(a + 1, b):
                good(h)
    out: list[list[int]] = []
    prev = False
    for h in sorted(ok):  # between two good checked heights, all are taken as good
        if ok[h]:
            if prev:
                out[-1][1] = h
            else:
                out.append([h, h])
        prev = ok[h]
    return out


def min_printer_height(params: DesignParams, lo: int = 50, hi: int = 500,
                       fin_scales: tuple[float, ...] = (1.0,)) -> int | None:
    """The lowest printer max height (whole mm) at which some overall height
    builds; None if even `hi` doesn't."""
    def any_height(ph: int) -> bool:
        p = params.with_(print_max_height=ph)
        return any(height_ok(p, h, fin_scales) for h in range(80, 1001, 5))
    if not any_height(hi):
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if any_height(mid) else (mid + 1, hi)
    return lo


def build_rocket(params: DesignParams) -> Rocket:
    plan = plan_rocket(params)
    d, seg_lens, joint_len, fin = plan.d, plan.seg_lens, plan.joint_len, plan.fin
    body_parts, lug, fwd = plan.body_parts, plan.lug, plan.fwd
    seg_len = seg_lens[0]
    n_parts = len(seg_lens)
    top_z = body_parts[-1]["hi"]

    # Lugs between fins 0 and 1, on one line; the cord strap at 90 degrees.
    lug_angle = 180 / params.fin_count
    anchor_angle = 90.0
    strap = anchor_strap_geometry(d)

    aft = build_aft(d, seg_len, fin, params.fin_count)
    notes = list(aft.notes)
    solid = aft.solid
    if n_parts == 1:  # one-piece body: the strap goes in the fin can's top
        solid = add_anchor_strap(solid, d, strap, anchor_angle, strap_shift(strap, seg_len))
    if lug:
        solid = add_lug(solid, d, lug, 0.0, lug["len"], False, lug_angle)
    if fwd and fwd["index"] == 0:
        solid = add_lug(solid, d, lug, fwd["z0"], fwd["z1"], True, lug_angle)
    parts = [Part("Aft", solid, 0.0)]

    for i in range(1, n_parts):
        solid = body_segment(d, seg_lens[i])
        if i == n_parts - 1:
            solid = add_anchor_strap(solid, d, strap, anchor_angle, strap_shift(strap, seg_lens[i]))
        placement_z = body_parts[i]["placement_z"]
        solid = solid.translate((0, 0, placement_z))
        if fwd and fwd["index"] == i:
            solid = add_lug(solid, d, lug, fwd["z0"], fwd["z1"], True, lug_angle)
        parts.append(Part(seg_part_name(i, n_parts), solid, placement_z))

    top = parts[-1]
    z_bot = top.placement_z + strap["z_spring"] + strap_shift(strap, seg_lens[-1])
    strap_at = {"part": top.name, "angle_deg": anchor_angle, "z_bot": z_bot, "z_top": z_bot + strap["height"]}
    notes.append(f"Shock-cord strap: inside the top of {top.name}, its bar {top_z - strap_at['z_top']:.0f} mm below the "
                 "top edge (just under the nose's shoulder). With the nose off, clip the cord on with a snap swivel "
                 "or tie it round the bar.")

    nose_len, nose_joint = plan.nose_len, plan.nose_joint
    nose_z = top_z - nose_joint
    parts.append(Part("Nose", nose_cone(d, params.nose_shape, nose_len).translate((0, 0, nose_z)), nose_z))
    side_gap = nose_recess(d)[0] - 1.0  # beside the nose's tie bar
    if side_gap < shock_cord(d.mtr_d)["pass_d"] - 1e-6:
        notes.append(f"The nose shoulder is narrow at this wall thickness: the gap beside its tie bar is {side_gap:.1f} mm, "
                     "so tie on a cord thinner than that (flat 1/8 in elastic, not round).")
    # The cap prints face-down, which is how it is built; its placement is 0.
    parts.append(Part("Motor_Cap", threaded_cap(d.thread), 0.0))
    if lug and params.rod_standoff:
        parts.append(Part("Rod_Standoff", rod_standoff(lug, lug_angle), 0.0))
    for p in parts:
        if not p.assembled.is_valid:
            raise GeometryError(f"The {p.name} part came out as an unsound solid (geometry-engine bug); "
                                "try slightly different settings and report this design.")
    return Rocket(params, d, parts, seg_lens, notes, strap_at)
