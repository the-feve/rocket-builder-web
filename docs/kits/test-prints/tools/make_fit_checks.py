"""Quick fit-check sets: short slices of the real parts, one plate per motor size.

Printing a whole kit to test the body joints and the nose takes hours. These
are the same parts as the app builds (same fits, same strap), cut down to
the bit that matters, so a round of fit testing is a short print:

  1 nose_bottom      the nose's shoulder (with its tie bar) and a few mm of cone
  2 top_section      the top of the body tube: the nose's socket with the
                     shock-cord strap inside (no separate anchor section)
  3 joint_socket     the top of a lower body piece: the socket a body joint
                     slides into (taller rockets printed in pieces)
  4 joint_shoulder   the bottom of the piece above it: the shoulder

Fit 1 into 2 (nose) and 4 into 3 (body joint). Each size goes out as one
3MF with the four pieces laid out on the plate, plus the separate STLs, in
docs/kits/test-prints/fit-check/<size>/.

    python docs/kits/test-prints/tools/make_fit_checks.py [M13 M18 ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Axis, Mesher, Solid, export_stl

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / "fit-check"
sys.path.insert(0, str(ROOT / "geometry"))

from rocketgen.build import build_rocket  # noqa: E402
from rocketgen.export import half, render_png  # noqa: E402
from rocketgen.geom import intersect, meshes, one_solid  # noqa: E402
from rocketgen.params import DesignParams, compute_derived  # noqa: E402

SIZES = ("M13", "M18", "M24", "M29")
EXTRA = 6.0  # mm of plain tube or cone kept past each fit, to hold and to see the joint
GAP = 6.0  # between pieces on the plate


def slab(solid: Solid, z0: float, z1: float, what: str) -> Solid:
    """The part between heights z0 and z1 (local), moved down onto z = 0."""
    bb = solid.bounding_box()
    box = Solid.make_box(bb.size.X + 20, bb.size.Y + 20, z1 - z0).translate((bb.min.X - 10, bb.min.Y - 10, z0))
    piece = one_solid(intersect(solid, box), what)
    if not (piece.is_valid and meshes(piece)):
        raise RuntimeError(f"{what}: not a sound solid")
    return piece.translate((0, 0, -piece.bounding_box().min.Z))


def pieces(size: str) -> list[tuple[str, Solid]]:
    # A body long enough to need two pieces on a 200 mm printer, so there is a
    # body joint to cut; the nose, the top section and the joint are the same
    # as in any rocket of this size.
    p = DesignParams(motor=size, fin_shape="trapezoid", nose_shape="tangent_ogive", fin_count=3,
                     print_max_height=200, body_length=320)
    r = build_rocket(p)
    d = r.derived
    by = {q.name: q for q in r.parts}
    nose = by["Nose"].local
    top = by[r.strap["part"]]
    body_parts = sorted((q for q in r.parts if q.name == "Aft" or q.name.startswith(("Seg_", "Top_Seg"))),
                        key=lambda q: q.placement_z)
    aft, above = body_parts[0], body_parts[1]

    out = [("1_nose_bottom", slab(nose, 0, d.nose_shoulder_len + d.nose_joint_rise + EXTRA, f"{size} nose bottom"))]
    top_local = top.local
    h = top_local.bounding_box().max.Z
    strap_bot = r.strap["z_bot"] - top.placement_z - (top.assembled.translate((0, 0, -top.placement_z)).bounding_box().min.Z)
    out.append(("2_top_section", slab(top_local, max(0.0, strap_bot - EXTRA), h, f"{size} top section")))
    a = aft.local
    ah = a.bounding_box().max.Z
    socket = d.shoulder_len + d.inner_taper_rise
    out.append(("3_joint_socket", slab(a, ah - socket - EXTRA, ah, f"{size} joint socket")))
    out.append(("4_joint_shoulder", slab(above.local, 0, d.shoulder_len + d.joint_rise + EXTRA, f"{size} joint shoulder")))
    return out


def turned(s: Solid) -> Solid:
    """Half a turn about the piece's own axis, so the strap (built at +y)
    ends up in the half the preview keeps."""
    c = s.bounding_box().center()
    return s.rotate(Axis((c.X, c.Y, 0), (0, 0, 1)), 180)


def lay_out(items: list[tuple[str, Solid]]) -> list[tuple[str, Solid]]:
    """Side by side along x, centred on y."""
    placed, x = [], 0.0
    for name, s in items:
        bb = s.bounding_box()
        placed.append((name, s.translate((x - bb.min.X, -bb.center().Y, 0))))
        x += bb.size.X + GAP
    return placed


def main(sizes: list[str]) -> None:
    for size in sizes:
        d = compute_derived(DesignParams(motor=size))
        folder = OUT / size.lower()
        folder.mkdir(parents=True, exist_ok=True)
        items = lay_out(pieces(size))
        mesher = Mesher()
        for name, s in items:
            s.label = f"{size}_{name}"
            mesher.add_shape(s, linear_deflection=0.01, angular_deflection=0.1)
            export_stl(s, str(folder / f"{size}_{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
        mesher.write(str(folder / f"{size}-fit-check.3mf"))
        render_png([(half(turned(s)), (0.95, 0.40, 0.17)) for _, s in items], folder / "preview.png", elev=20, azim=90,
                   px=1100, title=f"{size} fit check, cut in half; right to left: 1 nose bottom, 2 top section, 3 socket, 4 shoulder")
        heights = ", ".join(f"{n.split('_', 1)[1]} {s.bounding_box().size.Z:.0f} mm" for n, s in items)
        (folder / "README.md").write_text(
            f"# {size} fit check\n\n"
            f"Short slices of the real {size} parts (Rocket Builder's current fits: body joint {d.fit_slip:.2f} mm, "
            f"nose {d.fit_nose:.2f} mm per side, 0.5 mm shoulder chamfer). Print `{size}-fit-check.3mf` (one plate, "
            f"as laid out, no supports) or the STLs.\n\n"
            f"- Push **1** (nose bottom) into **2** (top of the body tube, with the cord strap): the nose should slide "
            f"in by hand and come out with a firm pull.\n"
            f"- Push **4** (shoulder) into **3** (socket): a snug slide that you'd glue.\n\n"
            f"Heights: {heights}.\n\n"
            f"Tube inside diameter in the CAD: {d.body_id:.2f} mm; body shoulder {d.shoulder_od:.2f} mm; nose shoulder "
            f"{d.nose_shoulder_od:.2f} mm. Measure your prints and send the smallest socket inside diameter and the "
            f"largest shoulder outside diameter for each pair.\n")
        print(size, heights)


if __name__ == "__main__":
    main([a.upper() for a in sys.argv[1:]] or list(SIZES))
