"""Fit-test coupons: the joint interfaces of a rocket without the rest of it.

For each body tube size, one socket ring (the top of a body segment: bore
plus the 45-degree countersink) and a set of shoulder plugs at different
radial clearances: "J" plugs use the body-joint shoulder length (glued
joints), "N" plugs the nose's shorter shoulder (must slide out at ejection).
Plugs are the real shoulder profile (body.py), with a short band of body
tube and a closed end with the label recessed into it, printed closed end
down (cup open upward); the socket prints upright, countersink on top, as a
segment does.
Labels are the clearance in hundredths of a mm: J10 = 0.10 mm radial.

    python -m rocketgen.fit_test --out fit_test/out
    python -m rocketgen.fit_test --sizes M18 M24 --joint 0.1 0.15 --nose 0.2 0.3

Writes one STL per coupon and one 3MF and one STEP plate per size (separate objects, laid
out on the bed) for Bambu Studio.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from build123d import Align, Axis, Compound, FontStyle, Mesher, Solid, Text, export_step, export_stl, extrude

from .body import body_segment, nose_cone, shoulder_foot
from .geom import extrude_y_symmetric, intersect, one_solid, revolve
from .thread import threaded_boss, threaded_cap
from .params import DesignParams, compute_derived

# name -> (motor, body OD override or None). The motor sizes at minimum
# diameter, plus BT60 (the common custom tube for M24 / M29).
SIZES = {
    "M13": ("M13", None),
    "M18": ("M18", None),
    "M24": ("M24", None),
    "M29": ("M29", None),
    "BT60": ("M29", 41.6),
}
JOINT_FITS = (0.05, 0.10, 0.15, 0.20)
NOSE_FITS = (0.15, 0.20, 0.25, 0.30)
CHAMFER = 0.5  # shoulder lead-in, see DesignParams.shoulder_chamfer
BAND = 5.0  # body tube above the joint on a plug
CAP = 1.6  # plug's closed end (on the bed), label recessed TEXT_H into it
TEXT_H = 0.6
FONT = "FreeSans"


@dataclass
class Coupon:
    name: str  # file name, e.g. M18_J10
    solid: Solid
    footprint: float  # x/y extent on the bed, for layout


def _label(text: str, size: float, z: float, x: float = 0.0, y: float = 0.0, h: float = TEXT_H):
    """Text h tall standing on z (raised on the socket's flag, cut into a plug's end)."""
    t = Text(text, font_size=size, font=FONT, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    return extrude(t, h).translate((x, y, z))


def socket(size: str) -> Coupon:
    """The top of a body segment: plain bore, 45-degree countersink on top,
    deep enough that a joint shoulder never bottoms out. A flag at the base
    carries the size."""
    motor, od = SIZES[size]
    d = compute_derived(DesignParams(motor=motor, body_od_override=od))
    h = d.shoulder_len + d.wall + 4.0
    ri, ro = d.body_id / 2, d.body_od / 2
    ring = revolve([(ri, 0), (ro, 0), (ro, h), (ri, h - d.wall)])
    flag_w, flag_l, flag_t = max(14.0, 0.6 * d.body_od), 9.0, 1.2
    y0 = ro - d.wall / 2
    flag = extrude_y_symmetric([(-flag_w / 2, 0), (flag_w / 2, 0), (flag_w / 2, flag_t), (-flag_w / 2, flag_t)], flag_l)
    flag = flag.translate((0, y0 + flag_l / 2, 0))
    text = _label(size, 4.5, flag_t, y=ro + flag_l / 2 - 0.5)
    solid = ring.fuse(flag).fuse(text).clean()
    return Coupon(f"{size}_socket", solid, max(d.body_od, flag_w) + 2 * flag_l)


def plug(size: str, fit: float, nose: bool, flip: bool = True) -> Coupon:
    """Shoulder (the real profile at this clearance) + 45-degree rise + a
    band of body tube + a closed end with the label recessed into it.
    Flipped (default) for printing: the closed end flat on the bed, the cup
    open upward, the label reading from below (owner's request: the
    shoulder-down orientation stood on a thin edge). flip=False is the
    seated orientation, shoulder at z = 0."""
    motor, od = SIZES[size]
    d = compute_derived(DesignParams(motor=motor, body_od_override=od, fit_joint=fit, fit_nose=fit,
                                     shoulder_chamfer=CHAMFER))
    sh = d.nose_shoulder_len if nose else d.shoulder_len
    r_sh = d.shoulder_od / 2
    ri_sh = r_sh - d.wall
    rise = d.joint_rise
    top = sh + rise + BAND
    ro, ri = d.body_od / 2, d.body_id / 2
    # Inside: the shoulder bore, a 45-degree step out to the body bore (prints
    # without support either way up), then the closed end.
    pts = [(ri_sh, 0), *shoulder_foot(r_sh, CHAMFER), (r_sh, sh), (ro, sh + rise), (ro, top), (0, top),
           (0, top - CAP), (ri, top - CAP), (ri, sh + rise + (ri - ri_sh)), (ri_sh, sh + rise)]
    body = revolve(pts)
    tag = f"{'N' if nose else 'J'}{round(fit * 100):02d}"
    text = _label(tag, min(4.5, 0.28 * d.body_od), top - TEXT_H, h=TEXT_H + 0.01)
    solid = body.cut(text).clean()
    if flip:
        solid = solid.rotate(Axis.X, 180).translate((0, 0, top))
    return Coupon(f"{size}_{tag}", solid, d.body_od)


def motor_cap_test(motor: str) -> list[Coupon]:
    """The motor end of an aft part: the threaded boss with a short length of
    motor bore above it (printed boss end down, as the aft is), and the motor
    cap (printed face down). Slide a real motor in from the top, screw the cap
    on, and check the lip covers only the casing."""
    d = compute_derived(DesignParams(motor=motor))
    t = d.thread
    # The boss itself, 8 mm longer above the tail (a fused tube came out invalid on M13).
    stub = threaded_boss(dict(t, overlap=t["overlap"] + 8.0)).translate((0, 0, -t["z_boss_end"]))
    cap = threaded_cap(t)
    cap = cap.translate((0, 0, -cap.bounding_box().min.Z))
    w = 2 * t["r_cap_max"] + 2
    return [Coupon(f"{motor}_cap_stub", stub, w), Coupon(f"{motor}_cap", cap, w)]


def validation_parts(motor: str, extra: float = 8.0) -> list[Coupon]:
    """Short pieces of the real parts with the website's fits, in their real
    print orientation (shoulder down): two body segments (one's shoulder in
    the other's socket), the bottom of the nose (shoulder, end cap, tie bar)
    and the motor cap test. `extra` mm of plain tube above each joint."""
    d = compute_derived(DesignParams(motor=motor))
    seg_len = d.shoulder_len + max(d.inner_taper_rise, d.joint_rise) + d.wall + extra
    seg = body_segment(d, seg_len)
    nose_h = d.nose_shoulder_len + d.nose_joint_rise + extra
    nose = nose_cone(d, "conical", 3.0 * d.cal)
    nose = one_solid(intersect(nose, revolve([(0, -1), (d.body_od, -1), (d.body_od, nose_h), (0, nose_h)])), "nose stub")
    out = [Coupon(f"{motor}_seg_a", seg, d.body_od + 2), Coupon(f"{motor}_seg_b", seg, d.body_od + 2),
           Coupon(f"{motor}_nose_stub", nose, d.body_od + 2)]
    return out + motor_cap_test(motor)


def coupons(size: str, joint=JOINT_FITS, nose=NOSE_FITS, flip: bool = True) -> list[Coupon]:
    return [socket(size)] + [plug(size, f, False, flip) for f in joint] + [plug(size, f, True, flip) for f in nose]


def layout(items: list[Coupon], gap: float = 6.0, cols: int = 3) -> list[tuple[Coupon, float, float]]:
    """Rows of `cols` (fewer if they'd pass 240 mm), centred on a Bambu
    X1C / P1S plate (256 mm)."""
    bed = min(240.0, cols * (max(c.footprint for c in items) + gap))
    placed, x, y, row_h = [], 0.0, 0.0, 0.0
    for c in items:
        if x and x + c.footprint > bed:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        placed.append((c, x + c.footprint / 2, y + c.footprint / 2))
        x += c.footprint + gap
        row_h = max(row_h, c.footprint)
    w = max(px + c.footprint / 2 for c, px, _ in placed)
    h = max(py + c.footprint / 2 for c, _, py in placed)
    off_x, off_y = 128 - w / 2, 128 - h / 2
    return [(c, px + off_x, py + off_y) for c, px, py in placed]


def write(size: str, out: Path, joint=JOINT_FITS, nose=NOSE_FITS) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    items = coupons(size, joint, nose)
    paths = []
    stl_dir = out / "stl"
    stl_dir.mkdir(exist_ok=True)
    for c in items:
        p = stl_dir / f"{c.name}.stl"
        export_stl(c.solid, p, tolerance=0.01, angular_tolerance=0.1)
        paths.append(p)
    mesher = Mesher()
    for c, x, y in layout(items):
        s = c.solid.translate((x, y, 0))
        s.label = c.name
        mesher.add_shape(s, linear_deflection=0.01, angular_deflection=0.1)
    p = out / f"fit_test_{size}.3mf"
    mesher.write(str(p))
    paths.append(p)
    # STEP too: Bambu Studio imports it as separate objects without the
    # warning it gives on this 3MF (owner, 2026-10-16).
    placed = []
    for c, x, y in layout(items):
        s = c.solid.translate((x, y, 0))
        s.label = c.name
        placed.append(s)
    p = out / f"fit_test_{size}.step"
    export_step(Compound(placed, label=f"fit_test_{size}"), p)
    paths.append(p)
    return paths


def write_plate(items: list[Coupon], path: Path, cols: int = 5) -> Path:
    """One STEP plate, coupons laid out and named."""
    placed = []
    for c, x, y in layout(items, cols=cols):
        s = c.solid.translate((x, y, 0))
        s.label = c.name
        placed.append(s)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(placed, label=path.stem), path)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sizes", nargs="+", default=list(SIZES), choices=list(SIZES))
    ap.add_argument("--joint", nargs="+", type=float, default=list(JOINT_FITS), help="body-joint radial clearances, mm")
    ap.add_argument("--nose", nargs="+", type=float, default=list(NOSE_FITS), help="nose radial clearances, mm")
    ap.add_argument("--out", type=Path, default=Path("fit_test/out"))
    ap.add_argument("--motor-caps", nargs="+", metavar="MOTOR",
                    help="instead: a threaded stub + motor cap for each motor size, on one STEP plate")
    ap.add_argument("--validate", nargs="+", metavar="MOTOR",
                    help="instead: short real parts (two segments, nose stub, motor cap + stub) per motor, one STEP plate")
    a = ap.parse_args(argv)
    if a.validate:
        items = [c for m in a.validate for c in validation_parts(m)]
        print(write_plate(items, a.out / "validation.step"))
        return 0
    if a.motor_caps:
        items = [c for m in a.motor_caps for c in motor_cap_test(m)]
        print(write_plate(items, a.out / "motor_cap_test.step"))
        return 0
    for size in a.sizes:
        for p in write(size, a.out, a.joint, a.nose):
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
