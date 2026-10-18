"""Build the example rockets for the assembly guide with rocketgen and write,
per rocket, a GLB (every part in its assembled position, one node per part,
named as in the app) and a JSON of the dimensions the renderer needs to
place the shock cord, parachute, motor and so on.

Run from anywhere (needs the geometry package installed: pip install -e
geometry trimesh):

    python docs/assembly/tools/build_meshes.py            # -> docs/assembly/tools/.build/

Units are mm, z up, z = 0 at the tail of the aft part (as in rocketgen).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

from rocketgen.anchor import anchor_strap_geometry
from rocketgen.build import body_length_for
from rocketgen.fins import FinShape
from rocketgen.lugs import lug_geometry
from rocketgen.params import DesignParams
from rocketgen.stability import build_stable

OUT = Path(__file__).resolve().parent / ".build"

# The rockets drawn in the guide. "m18": the app's Beginner default (M18,
# trapezoid fins, 200 mm printer, default height). "m24": an M24 tall enough
# for two body sections plus the anchor section.
ROCKETS = {
    "m18": dict(params=DesignParams(motor="M18", fin_shape=FinShape.TRAPEZOID), overall=None),
    "m24": dict(params=DesignParams(motor="M24", fin_shape=FinShape.TRAPEZOID, nose_shape="tangent_ogive"), overall=480),
}


def mesh(solid, tol=0.05):
    verts, tris = solid.tessellate(tol, 0.2)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in verts]), np.array(tris), process=True)


def build(key: str, spec: dict) -> None:
    params = spec["params"]
    if spec["overall"]:
        params = params.with_(body_length=body_length_for(params, spec["overall"]))
    rocket = build_stable(params)
    d, t = rocket.derived, rocket.derived.thread
    scene = trimesh.Scene()
    parts = []
    for p in rocket.parts:
        scene.add_geometry(mesh(p.assembled), node_name=p.name, geom_name=p.name)
        bb = p.assembled.bounding_box()
        parts.append({"name": p.name, "placement_z": p.placement_z, "zmin": bb.min.Z, "zmax": bb.max.Z,
                      "height": p.local.bounding_box().size.Z})
    OUT.mkdir(parents=True, exist_ok=True)
    scene.export(OUT / f"{key}.glb")

    # Where the shock cord attaches.
    strap = anchor_strap_geometry(d)
    anchor = next(p for p in rocket.parts if p.name == "Anchor_Seg")
    seg_len = rocket.seg_lens[-1]
    z_shift = seg_len - strap["sec_len"]
    nose = next(p for p in rocket.parts if p.name == "Nose")
    info = {
        "key": key,
        "motor": params.motor,
        "fin_count": params.fin_count,
        "fin_scale": rocket.params.fin_scale,
        "body_od": d.body_od, "body_id": d.body_id, "bay_id": d.bay_id, "bay_len": d.bay_len,
        "mtr_d": d.mtr_d, "mtr_len": d.mtr_len,
        "shoulder_od": d.shoulder_od, "shoulder_len": d.shoulder_len, "nose_shoulder_len": d.nose_shoulder_len,
        "joint_rise": d.joint_rise, "has_mount": d.has_mount,
        "fit_slip": d.fit_slip,
        "thread": {k: t[k] for k in ("p", "turns", "hang", "z_face", "cap_top", "r_cap_out", "nose_bore_r", "z_boss_end")},
        "lug_angle_deg": 180 / params.fin_count,
        "lug": {k: v for k, v in lug_geometry(d, params.rod_diameter, params.rod_standoff, params.pad_clearance).items()},
        "rod_diameter": params.rod_diameter,
        "strap": {
            "angle_deg": 90.0,
            "front": strap["front"], "t": strap["t"], "hole_depth": strap["hole_depth"],
            "cord_width": strap["cord_width"], "spring": strap["spring"],
            "z_bot": anchor.placement_z + strap["z_spring"] + z_shift,
            "z_top": anchor.placement_z + strap["z_out_top"] + z_shift,
        },
        "nose": {"placement_z": nose.placement_z, "tie_bar_z": nose.placement_z + 1.0,
                 "tip_z": nose.assembled.bounding_box().max.Z},
        "parts": parts,
        "notes": rocket.notes,
        "summary": rocket.summary(),
    }
    (OUT / f"{key}.json").write_text(json.dumps(info, indent=2))
    print(key, [p["name"] for p in parts], f"length {info['nose']['tip_z'] - min(p['zmin'] for p in parts):.0f} mm")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(ROCKETS)
    for k in keys:
        build(k, ROCKETS[k])
