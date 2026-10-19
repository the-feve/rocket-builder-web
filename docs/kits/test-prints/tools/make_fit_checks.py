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

from build123d import Axis, FontStyle, Plane, Solid, Text, export_stl, extrude

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
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MARK_DEPTH = 0.5  # engraved label depth; the walls are 1.5 mm


def engrave(solid: Solid, label: str, z: float, r_out: float, what: str) -> Solid:
    """Cut `label` MARK_DEPTH into the outside wall at height z, on the -y
    side (the cord strap is built at +y), reading upright from outside. The
    part's axis is the z axis."""
    face = Plane.XZ * Text(label, font_size=3.6, font_path=FONT, font_style=FontStyle.BOLD)
    # Through the wall, then trimmed to a ring MARK_DEPTH deep, so every
    # letter is cut equally deep into the curved surface.
    letters = extrude(face, amount=r_out + 2).translate((0, 0, z))
    ring = (Solid.make_cylinder(r_out + 2, 8).translate((0, 0, z - 4))
            .cut(Solid.make_cylinder(r_out - MARK_DEPTH, 8).translate((0, 0, z - 4))))
    return one_solid(solid.cut(intersect(letters, ring)), f"{what} label")


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

    num = size[1:]
    ro = d.body_od / 2
    nose_fit = d.nose_shoulder_len + d.nose_joint_rise
    out = [("1_nose_bottom", engrave(slab(nose, 0, nose_fit + EXTRA, f"{size} nose bottom"), f"{num}-1",
                                     nose_fit + EXTRA / 2 - 0.3, ro - 0.1, f"{size} nose bottom"))]
    top_local = top.local
    h = top_local.bounding_box().max.Z
    strap_bot = r.strap["z_bot"] - top.placement_z - (top.assembled.translate((0, 0, -top.placement_z)).bounding_box().min.Z)
    out.append(("2_top_section", engrave(slab(top_local, max(0.0, strap_bot - EXTRA), h, f"{size} top section"),
                                         f"{num}-2", EXTRA / 2, ro, f"{size} top section")))
    a = aft.local
    ah = a.bounding_box().max.Z
    socket = d.shoulder_len + d.inner_taper_rise
    out.append(("3_joint_socket", engrave(slab(a, ah - socket - EXTRA, ah, f"{size} joint socket"), f"{num}-3",
                                          EXTRA / 2, ro, f"{size} joint socket")))
    joint_fit = d.shoulder_len + d.joint_rise
    out.append(("4_joint_shoulder", engrave(slab(above.local, 0, joint_fit + EXTRA, f"{size} joint shoulder"),
                                            f"{num}-4", joint_fit + EXTRA / 2, ro, f"{size} joint shoulder")))
    return out


def write_3mf(items: list[tuple[str, Solid]], path: Path) -> None:
    """A plain 3MF: one mesh object per piece and one build item each, in
    place. (build123d's Mesher also writes a wrapper object per piece, which
    Bambu Studio imported as a second copy of every piece.)"""
    import zipfile
    objs, build = [], []
    for i, (name, s) in enumerate(items, 1):
        verts, tris = s.tessellate(0.01, 0.1)
        v = "".join(f'<vertex x="{p.X:.4f}" y="{p.Y:.4f}" z="{p.Z:.4f}"/>' for p in verts)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        objs.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{v}</vertices>'
                    f'<triangles>{t}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objs)}</resources><build>{"".join(build)}</build></model>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
             'content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
             'relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing'
             '-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.'
            'com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


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
        for name, s in items:
            export_stl(s, str(folder / f"{size}_{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
        write_3mf([(f"{size}_{n}", s) for n, s in items], folder / f"{size}-fit-check.3mf")
        render_png([(half(turned(s)), (0.95, 0.40, 0.17)) for _, s in items], folder / "preview.png", elev=20, azim=90,
                   px=1100, title=f"{size} fit check, cut in half; right to left: 1 nose bottom, 2 top section, 3 socket, 4 shoulder")
        heights = ", ".join(f"{n.split('_', 1)[1]} {s.bounding_box().size.Z:.0f} mm" for n, s in items)
        (folder / "README.md").write_text(
            f"# {size} fit check\n\n"
            f"Short slices of the real {size} parts (Rocket Builder's current fits: body joint {d.fit_slip:.2f} mm, "
            f"nose {d.fit_nose:.2f} mm per side, 0.5 mm shoulder chamfer). Print `{size}-fit-check.3mf` (one plate, "
            f"as laid out, no supports) or the STLs.\n\n"
            f"Each piece has its code engraved on the outside: **{size[1:]}-1** to **{size[1:]}-4**.\n\n"
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
