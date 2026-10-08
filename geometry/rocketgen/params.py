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

    def with_(self, **kw) -> "DesignParams":
        return replace(self, **kw)


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
    thread: dict = field(default_factory=dict)


def thread_geometry(mtr_d, mtr_hang, bay_id, mount_od, body_od, wall, fin) -> dict:
    """threadGeometry: the threaded motor cap and the boss it screws onto."""
    p = 2.5 if mtr_d < 21 else 3.0
    h = 0.35 * p
    turns = 3
    thread_clear = 0.25  # radial; fit_slip is far too tight for a printed thread
    cap_wall = 1.6
    cap_face_t = max(1.5, 0.08 * mtr_d)
    gap = 0.5  # boss end to the cap's floor

    r_root = mount_od / 2
    r_crest = r_root + h
    r_cap_in = r_crest + thread_clear
    r_cap_out = r_cap_in + cap_wall
    rib_r = 0.8
    rib_out = 0.6
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
        "nose_bore_r": mtr_d / 2 - 3.175,
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
    wall = settings["wall"]
    fit_slip = settings["fit_slip"]
    fit_press = settings["fit_press"]
    mtr_clear = settings["mtr_clear"]

    bay_id = mtr_d + 2 * mtr_clear
    min_body_od = bay_id + 2 * wall
    body_od = max(min_body_od, params.body_od_override) if params.body_od_override else min_body_od
    body_id = body_od - 2 * wall
    cal = body_od
    shoulder_od = body_id - 2 * fit_slip
    shoulder_len = max(0.75 * cal - 4.0, 10.0)
    mount_od = bay_id + 2 * wall

    fin = fin_dimensions(params, cal)
    thread = thread_geometry(mtr_d, mtr_hang, bay_id, mount_od, body_od, wall, fin)
    bay_len = mtr_len - thread["hang"]
    zmax = params.print_max_height - z_margin
    stop_depth = mtr_clear + 1.5
    block_thickness = stop_depth + 1.0
    has_mount = (body_id - mount_od) / 2 >= wall
    aft_socket_base = bay_len + block_thickness + ((body_id - bay_id) / 2 if has_mount else 0.0)
    joint_rise = (body_od - shoulder_od) / 2
    inner_taper_rise = (body_id / 2 - (shoulder_od / 2 - wall)) / math.tan(math.radians(8))

    return Derived(
        mtr_d=mtr_d, mtr_len=mtr_len, mtr_hang=mtr_hang, wall=wall, fit_slip=fit_slip,
        fit_press=fit_press, bay_id=bay_id, body_od=body_od, body_id=body_id, cal=cal,
        shoulder_od=shoulder_od, shoulder_len=shoulder_len, mount_od=mount_od,
        has_mount=has_mount, bay_len=bay_len, zmax=zmax, stop_depth=stop_depth,
        block_thickness=block_thickness, aft_socket_base=aft_socket_base,
        joint_rise=joint_rise, inner_taper_rise=inner_taper_rise, thread=thread,
    )

