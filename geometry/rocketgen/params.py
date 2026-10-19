"""Design parameters and derived values.

Mirrors the feature dialog (defaults and bounds) and `computeDerivedValues`
in src/RocketGenerator.fs (anchor-section branch). Units are mm throughout.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

from .fins import FinShape, fin_dimensions, fin_lowest_z_within

# Copied from OS_Rocket_Builder/data (the Onshape Variable Studios). Keep in sync.
DATA_DIR = Path(__file__).resolve().parent / "data"

NOSE_SHAPES = ("tangent_ogive", "conical", "elliptical", "parabolic", "von_karman")
LUG_OPTIONS = ("two", "aft_only", "none")
MATERIALS = {"PETG": 1.27, "ASA": 1.07, "PLA": 1.24}  # g/cm3

# The shock cord the printed attachment points are sized for (owner,
# 2026-10-18: braided elastic, as in hobby kits; Kevlar won't be offered).
# Flat braided elastic is 1/8 in wide on 13/18 mm rockets and 1/4 in on
# 24/29 mm ones, about 1 mm thick (the 1/4 in a little more); round 1/8 in
# elastic (about 3.2 mm) is just as common at every size. Keyed by the motor
# diameter so a fatter body (body OD offset) keeps its motor's cord.
SHOCK_CORDS = (  # (motor diameter up to, mm): cord, mm
    (21.0, {"flat_w": 3.2, "flat_t": 1.0, "round_d": 3.2}),
    (999.0, {"flat_w": 6.4, "flat_t": 1.2, "round_d": 3.2}),
)
CORD_PRINT_MARGIN = 0.4  # printed slots come out a little small, and elastic is fuzzy


def shock_cord(mtr_d: float) -> dict:
    """The cord for a motor size, and `pass_d`: the clear gap a cord pass
    needs (one round cord, or flat cord doubled back on itself, plus the
    print margin). The anchor strap's slot and the nose tie bar's room are
    both this deep."""
    cord = next(c for dmax, c in SHOCK_CORDS if mtr_d <= dmax)
    return {**cord, "pass_d": max(cord["round_d"], 2 * cord["flat_t"]) + CORD_PRINT_MARGIN}


def _mm(text: str) -> float:
    value, unit = text.split()
    assert unit == "mm", text
    return float(value)


def load_motors() -> dict[str, dict[str, float]]:
    """data/rocket_library_motors.csv -> {motor: {mtr_d, mtr_len, mtr_hang}}."""
    with open(DATA_DIR / "rocket_library_motors.csv", newline="") as f:
        return {
            row["Motor"]: {k: _mm(row[k]) for k in ("mtr_d", "mtr_len", "mtr_hang")}
            for row in csv.DictReader(f)
        }


def load_settings() -> dict[str, float]:
    """data/rocket_global_settings.csv (the VS - Global Settings studio)."""
    with open(DATA_DIR / "rocket_global_settings.csv", newline="") as f:
        return {row["Name"]: _mm(row["Value"]) for row in csv.DictReader(f)}


@dataclass(frozen=True)
class DesignParams:
    """The feature dialog. Defaults match the FeatureScript's."""

    motor: str = "M18"
    # Fins
    fin_shape: FinShape = FinShape.CLIPPED_DELTA
    fin_count: int = 3
    fin_thickness: float = 1.5
    fin_fillet: float = 3.5
    fin_fillet_upper: float = 1.0
    fin_tip_radius: float = 6.5
    custom_fin_size: bool = False
    fin_scale: float = 1.0  # the website's stability auto-size (standard sizes only); not in the FeatureScript
    wall: float | None = None  # tube, nose and mount wall; None = the settings CSV (1.5 mm). Website only.
    fin_root_chord: float = 40.0
    fin_span: float = 20.0
    fin_tip_chord: float = 20.0
    fin_sweep: float = 20.0
    # Nose
    nose_shape: str = "tangent_ogive"
    nose_fineness: float = 3.0
    # Body
    body_length: float = 250.0
    body_od_override: float | None = None  # None = minimum diameter
    print_max_height: float = 200.0
    # Launch lugs: "two" (aft + forward), "aft_only" or "none"
    launch_lugs: str = "two"
    rod_diameter: float = 3.175
    rod_standoff: bool = True
    pad_clearance: float = 15.0
    forward_lug_frac: float = 0.5
    # Material
    material: str = "PLA"
    # Critical fit dimensions (website, Advanced). None = the computed value,
    # as before. They let a result from a fit-test print be typed in.
    joint_clearance: float | None = None  # body shoulder into socket, radial; None = web_fits()
    nose_clearance: float | None = None  # nose shoulder into the top socket, radial; None = web_fits()
    shoulder_chamfer: float = 0.5  # 45-degree chamfer on each shoulder's bed edge (elephant's foot)
    shoulder_len: float | None = None  # body-to-body joint engagement; None = max(0.75 cal - 4, 10)
    nose_shoulder_len: float | None = None  # nose joint engagement; None = 70% of the body joint (min 7)
    thread_clearance: float | None = None  # motor cap thread, radial (crest to cap bore); None = 0.25
    thread_pitch: float | None = None  # None = 2.5 mm under 21 mm motors, else 3 mm
    thread_turns: int | None = None  # None = 3
    # Nose weight (modelling clay pressed into the nose cone), g. Not geometry:
    # only the mass and CG (stability.Balance) see it. Website (Advanced, 0-50);
    # the stability lessons add clay and watch the score and CG move.
    nose_weight_g: float = 0.0

    def with_(self, **kw) -> "DesignParams":
        return replace(self, **kw)


# Printed fits (radial, per side, mm), from fit-test coupons on a Bambu P1S
# in PLA (2026-10-16). The settings CSV's fit_slip (0.02) is the CAD value
# and prints far too tight (owner, 2026-10-18: first M13 and M18 kit test
# prints "way too tight"). Body joints: 0.15 a little snug, 0.20 a little
# loose on M18-M29, so 0.18. Nose: 0.15 on M18-M29. M13's short shoulders
# (nose shoulder under SHORT_NOSE_SHOULDER) grip harder per mm: joint 0.16
# just right; nose 0.12 too tight, 0.15 too loose, so 0.14.
# Round 2 (owner, 2026-10-19, M13/M18/M24 kit prints): every body joint and
# nose still a bit tight. Measured worst case: sockets print 0.21-0.35 mm
# under on diameter, shoulders 0.10-0.20 mm over, so the parts touch or
# overlap by up to ~0.2 mm on diameter at the seam. All four gaps +20 %
# (owner's call): 0.18 -> 0.22, 0.15 -> 0.18, 0.16 -> 0.19, 0.14 -> 0.17.
WEB_FIT_JOINT = 0.22
WEB_FIT_NOSE = 0.18
WEB_FIT_JOINT_SHORT = 0.19
WEB_FIT_NOSE_SHORT = 0.17
SHORT_NOSE_SHOULDER = 8.0


def web_fits(nose_shoulder_len: float) -> tuple[float, float]:
    """Default (joint, nose) radial clearances for a nose shoulder this long."""
    if nose_shoulder_len < SHORT_NOSE_SHOULDER:
        return WEB_FIT_JOINT_SHORT, WEB_FIT_NOSE_SHORT
    return WEB_FIT_JOINT, WEB_FIT_NOSE


@dataclass
class Derived:
    """computeDerivedValues' result."""

    mtr_d: float
    mtr_len: float
    mtr_hang: float
    wall: float
    fit_slip: float
    fit_press: float
    bay_id: float
    body_od: float
    body_id: float
    cal: float
    shoulder_od: float
    shoulder_len: float
    mount_od: float
    has_mount: bool
    bay_len: float
    zmax: float
    stop_depth: float
    block_thickness: float
    aft_socket_base: float
    joint_rise: float
    inner_taper_rise: float
    nose_shoulder_len: float = 0.0
    thread: dict = field(default_factory=dict)
    fit_nose: float = 0.0
    nose_shoulder_od: float = 0.0
    nose_joint_rise: float = 0.0
    shoulder_chamfer: float = 0.0


# Motor cap retention lip: how far the cap's floor reaches in over the motor's
# rear end, from the motor's OD. The FeatureScript's 1/8 in (3.175 mm) made
# the nozzle hole too small; 2.5 mm (2026-10-18) still looked small on the
# kit caps. The owner measured an 18 mm casing wall at about 2.5 mm and asked
# for a 1.5-2 mm lip (2026-10-19): 1.75 still sits well inside the casing
# wall, clear of the nozzle. The hole is mtr_d - 2 * CAP_LIP across.
CAP_LIP = 1.75


def thread_geometry(mtr_d, mtr_hang, bay_id, mount_od, body_od, wall, fin,
                    pitch=None, turns=None, thread_clear=None) -> dict:
    """threadGeometry: the threaded motor cap and the boss it screws onto.
    pitch / turns / thread_clear: the website's Advanced overrides (None =
    the FeatureScript's values)."""
    p = pitch or (2.5 if mtr_d < 21 else 3.0)
    h = 0.35 * p
    turns = turns or 3
    if thread_clear is None:
        thread_clear = 0.25  # radial; fit_slip is far too tight for a printed thread
    # Website: 1.2 mm (three 0.4 mm perimeters) and 0.4 mm ribs, for a more
    # compact cap (owner, 2026-10-16; the FeatureScript has 1.6 and 0.6).
    cap_wall = 1.2
    cap_face_t = max(1.5, 0.08 * mtr_d)
    gap = 0.5  # boss end to the cap's floor

    r_root = mount_od / 2
    r_crest = r_root + h
    r_cap_in = r_crest + thread_clear
    r_cap_out = r_cap_in + cap_wall
    rib_r = 0.8
    rib_out = 0.4
    r_cap_max = r_cap_out + rib_out

    # At least 2 mm below the tail (clear of the root fillets), and 1 mm
    # below any fin within the cap's outer radius.
    cap_top = min(-2.0, fin_lowest_z_within(fin, body_od, wall, r_cap_max) - 1.0)
    z_face = min(cap_top - turns * p - gap, -mtr_hang)
    z_boss_end = z_face + gap
    base_chamfer = min(1.0, cap_face_t * 0.5)
    return {
        "p": p,
        "h": h,
        "b": 0.85 * p,
        "c": 0.15 * p,
        "thread_clear": thread_clear,
        "boss_id_r": bay_id / 2,
        "r_root": r_root,
        "r_crest": r_crest,
        "r_cap_in": r_cap_in,
        "r_cap_out": r_cap_out,
        "r_cap_max": r_cap_max,
        "rib_r": rib_r,
        "rib_out": rib_out,
        "n_ribs": max(4, math.floor(2 * math.pi * r_cap_out / 10.0)),
        "overlap": 1.5,
        "cap_top": cap_top,
        "z_boss_end": z_boss_end,
        "z_face": z_face,
        "cap_face_t": cap_face_t,
        "base_chamfer": base_chamfer,
        "base_chamfer_h": base_chamfer * math.tan(math.radians(60)),
        "top_chamfer": 1.0,
        "top_chamfer_h": 1.0 * math.tan(math.radians(60)),
        "nose_bore_r": mtr_d / 2 - CAP_LIP,
        "hang": -z_face,
        "turns": (cap_top - z_boss_end) / p,
        "z_lowest": min(z_face - cap_face_t, fin_lowest_z_within(fin, body_od, wall, 1e6)),
    }


def compute_derived(params: DesignParams, motors=None, settings=None) -> Derived:
    motors = motors or load_motors()
    settings = settings or load_settings()
    if params.motor not in motors:
        raise ValueError(f"Unknown motor {params.motor!r}; choose one of {sorted(motors)}")
    m = motors[params.motor]
    mtr_d, mtr_len, mtr_hang = m["mtr_d"], m["mtr_len"], m["mtr_hang"]
    z_margin = settings["z_margin"]
    wall = params.wall if params.wall else settings["wall"]
    fit_press = settings["fit_press"]
    mtr_clear = settings["mtr_clear"]

    bay_id = mtr_d + 2 * mtr_clear
    min_body_od = bay_id + 2 * wall
    body_od = max(min_body_od, params.body_od_override) if params.body_od_override else min_body_od
    body_id = body_od - 2 * wall
    cal = body_od
    shoulder_len = params.shoulder_len or max(0.75 * cal - 4.0, 10.0)
    # The nose's insert is 30% shorter than a body joint's (owner's request,
    # 2026-10-09: a shorter transition); body-to-body joints keep the full length.
    nose_shoulder_len = params.nose_shoulder_len or max(0.7 * shoulder_len, 7.0)
    default_joint, default_nose = web_fits(nose_shoulder_len)
    fit_slip = default_joint if params.joint_clearance is None else params.joint_clearance
    fit_nose = default_nose if params.nose_clearance is None else params.nose_clearance
    shoulder_od = body_id - 2 * fit_slip
    nose_shoulder_od = body_id - 2 * fit_nose
    mount_od = bay_id + 2 * wall

    fin = fin_dimensions(params, cal)
    thread = thread_geometry(mtr_d, mtr_hang, bay_id, mount_od, body_od, wall, fin,
                             params.thread_pitch, params.thread_turns, params.thread_clearance)
    bay_len = mtr_len - thread["hang"]
    zmax = params.print_max_height - z_margin
    stop_depth = mtr_clear + 1.5
    block_thickness = stop_depth + 1.0
    has_mount = (body_id - mount_od) / 2 >= wall
    aft_socket_base = bay_len + block_thickness + ((body_id - bay_id) / 2 if has_mount else 0.0)
    joint_rise = (body_od - shoulder_od) / 2
    nose_joint_rise = (body_od - nose_shoulder_od) / 2
    inner_taper_rise = (body_id / 2 - (shoulder_od / 2 - wall)) / math.tan(math.radians(8))

    return Derived(
        mtr_d=mtr_d, mtr_len=mtr_len, mtr_hang=mtr_hang, wall=wall, fit_slip=fit_slip,
        fit_press=fit_press, bay_id=bay_id, body_od=body_od, body_id=body_id, cal=cal,
        shoulder_od=shoulder_od, shoulder_len=shoulder_len, mount_od=mount_od,
        has_mount=has_mount, bay_len=bay_len, zmax=zmax, stop_depth=stop_depth,
        block_thickness=block_thickness, aft_socket_base=aft_socket_base,
        joint_rise=joint_rise, inner_taper_rise=inner_taper_rise, nose_shoulder_len=nose_shoulder_len, thread=thread,
        fit_nose=fit_nose, nose_shoulder_od=nose_shoulder_od, nose_joint_rise=nose_joint_rise,
        shoulder_chamfer=max(params.shoulder_chamfer, 0.0),
    )

