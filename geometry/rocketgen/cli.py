"""rocketgen CLI: build a rocket and write STLs (and optional previews).

    python -m rocketgen.cli --motor M18 --fins swept --out out/m18_swept --png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_rocket
from .export import export_parts, render_rocket
from .fins import FinShape
from .geom import GeometryError
from .params import LUG_OPTIONS, NOSE_SHAPES, DesignParams


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--motor", default="M18")
    ap.add_argument("--fins", default=FinShape.CLIPPED_DELTA.value, choices=[s.value for s in FinShape])
    ap.add_argument("--fin-count", type=int, default=3, choices=(3, 4, 5))
    ap.add_argument("--nose", default="tangent_ogive", choices=NOSE_SHAPES)
    ap.add_argument("--fineness", type=float, default=3.0)
    ap.add_argument("--body-length", type=float, default=250.0)
    ap.add_argument("--body-od", type=float, default=None, help="custom body OD (default: minimum diameter)")
    ap.add_argument("--leading-fillet", type=float, default=1.0)
    ap.add_argument("--lugs", default="two", choices=LUG_OPTIONS)
    ap.add_argument("--rod", type=float, default=3.175, help="launch rod diameter, mm")
    ap.add_argument("--no-standoff", action="store_true", help="leave out the rod standoff part")
    ap.add_argument("--pad-clearance", type=float, default=15.0)
    ap.add_argument("--forward-lug", type=float, default=0.5, help="forward lug position, fraction of the body")
    ap.add_argument("--material", default="PLA", choices=("PLA", "PETG", "ASA"))
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--png", action="store_true", help="also write preview renders (needs matplotlib)")
    a = ap.parse_args(argv)

    params = DesignParams(motor=a.motor, fin_shape=FinShape(a.fins), fin_count=a.fin_count, nose_shape=a.nose,
                          nose_fineness=a.fineness, body_length=a.body_length, body_od_override=a.body_od,
                          fin_fillet_upper=a.leading_fillet, launch_lugs=a.lugs, rod_diameter=a.rod,
                          rod_standoff=not a.no_standoff, pad_clearance=a.pad_clearance,
                          forward_lug_frac=a.forward_lug, material=a.material)
    try:
        rocket = build_rocket(params)
    except GeometryError as ex:
        print(f"Can't build this rocket: {ex}", file=sys.stderr)
        return 2
    for p in export_parts(rocket, a.out):
        print(p)
    if a.png:
        for p in render_rocket(rocket, a.out):
            print(p)
    print(rocket.summary())
    for note in rocket.notes:
        print("Note:", note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
