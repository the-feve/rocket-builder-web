"""Phase 2 local prototype: one page, one FastAPI server, synchronous builds.

    cd web/server && uvicorn app:app --reload        # then open http://127.0.0.1:8000

POST /api/build builds a rocket with rocketgen and caches the result under a
hash of the parameters; the page then loads the GLB preview and offers the
ZIP of print-oriented STLs. No accounts, no storage beyond this process.
"""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import threading
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from build123d import export_stl
from rocketgen.build import build_rocket
from rocketgen.export import PART_COLORS
from rocketgen.fins import FinShape
from rocketgen.geom import GeometryError
from rocketgen.params import LUG_OPTIONS, MATERIALS, NOSE_SHAPES, DesignParams, load_motors

STATIC = Path(__file__).resolve().parent / "static"
GENERATOR_VERSION = "0.0.1"


class BuildRequest(BaseModel):
    """The design form. Bounds are the FeatureScript dialog's."""

    motor: str = "M18"
    fin_shape: FinShape = FinShape.CLIPPED_DELTA
    fin_count: int = Field(3, ge=3, le=5)
    fin_thickness: float = Field(1.5, ge=0.4, le=12)
    fin_fillet: float = Field(3.5, ge=0, le=20)
    fin_fillet_upper: float = Field(1.0, ge=0, le=10)
    fin_tip_radius: float = Field(6.5, ge=0, le=50)
    custom_fin_size: bool = False
    fin_root_chord: float = Field(40.0, ge=5, le=500)
    fin_span: float = Field(20.0, ge=3, le=300)
    fin_tip_chord: float = Field(20.0, ge=1, le=500)
    fin_sweep: float = Field(20.0, ge=0, le=500)
    nose_shape: str = "tangent_ogive"
    nose_fineness: float = Field(3.0, ge=2, le=5)
    body_length: float = Field(250.0, ge=50, le=2000)
    body_od_override: float | None = Field(None, ge=5, le=200)
    print_max_height: float = Field(200.0, ge=50, le=500)
    launch_lugs: str = "two"
    rod_diameter: float = Field(3.175, ge=2, le=13)
    rod_standoff: bool = True
    pad_clearance: float = Field(15.0, ge=0, le=100)
    forward_lug_frac: float = Field(0.5, ge=0.2, le=0.95)
    material: str = "PLA"


app = FastAPI(title="Rocket Builder (local prototype)")
_builds: dict[str, dict] = {}  # build id -> {"glb", "zip", "report"}
_lock = threading.Lock()  # one OpenCascade build at a time


def _report(rocket) -> dict:
    d, t = rocket.derived, rocket.derived.thread
    masses = rocket.mass_g()
    parts = [{"name": p.name, "color": PART_COLORS[i % len(PART_COLORS)], "volume_mm3": round(p.volume, 1),
              "mass_g": round(masses[p.name], 1),
              "height_mm": round(p.local.bounding_box().size.Z, 1)} for i, p in enumerate(rocket.parts)]
    return {
        "parts": parts,
        "total_mass_g": round(sum(masses.values()), 1),
        "summary": rocket.summary(),
        "notes": list(rocket.notes),
        "dimensions": {
            "Body OD": d.body_od, "Body ID": d.body_id, "Motor bay ID": d.bay_id,
            "Inner motor mount": "yes" if d.has_mount else "no (minimum diameter)",
            "Shoulder OD": d.shoulder_od, "Shoulder length": d.shoulder_len,
            "Motor hang-out": t["hang"], "Thread pitch": t["p"], "Thread turns": t["turns"],
            "Body segments": len(rocket.seg_lens),
        },
    }


def _glb(rocket) -> bytes:
    scene = trimesh.Scene()
    for p in rocket.parts:  # the page colours parts by name
        verts, tris = p.assembled.tessellate(0.05, 0.2)
        mesh = trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in verts]), np.array(tris), process=False)
        scene.add_geometry(mesh, node_name=p.name, geom_name=p.name)
    return scene.export(file_type="glb")


def _zip(rocket, report: dict, params: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        with tempfile.TemporaryDirectory() as tmp:
            for p in rocket.parts:
                path = Path(tmp) / f"{p.name}.stl"
                export_stl(p.local, path, tolerance=0.01, angular_tolerance=0.1)
                z.write(path, f"{p.name}.stl")
        lines = ["Rocket Builder build notes", "", report["summary"], ""]
        lines += [f"Note: {n}" for n in report["notes"]]
        lines += ["", "Parts (STLs are in print orientation, resting on z = 0):"]
        lines += [f"  {p['name']}: {p['mass_g']} g, {p['height_mm']} mm tall" for p in report["parts"]]
        lines += ["", "Key dimensions (mm):"]
        lines += [f"  {k}: {round(v, 2) if isinstance(v, float) else v}" for k, v in report["dimensions"].items()]
        z.writestr("build_notes.txt", "\n".join(lines) + "\n")
        z.writestr("design.json", json.dumps({"generatorVersion": GENERATOR_VERSION, "params": params}, indent=2))
    return buf.getvalue()


@app.get("/api/options")
def options():
    return {
        "motors": sorted(load_motors()),
        "fin_shapes": [s.value for s in FinShape],
        "nose_shapes": list(NOSE_SHAPES),
        "launch_lugs": list(LUG_OPTIONS),
        "materials": list(MATERIALS),
        "defaults": BuildRequest().model_dump(mode="json"),
    }


@app.post("/api/build")
def build(req: BuildRequest):
    params = req.model_dump(mode="json")
    if req.motor not in load_motors():
        raise HTTPException(422, f"Unknown motor {req.motor!r}.")
    if req.material not in MATERIALS:
        raise HTTPException(422, f"Unknown material {req.material!r}.")
    key = hashlib.sha256(json.dumps([GENERATOR_VERSION, params], sort_keys=True).encode()).hexdigest()[:16]
    if key not in _builds:
        with _lock:
            try:
                rocket = build_rocket(DesignParams(**{**params, "fin_shape": req.fin_shape}))
            except (GeometryError, ValueError) as ex:
                raise HTTPException(422, str(ex))
            except Exception as ex:  # an OpenCascade failure: never a bare 500
                raise HTTPException(422, f"The geometry engine could not build this design ({type(ex).__name__}). "
                                         "Try slightly different settings.")
            report = _report(rocket)
            _builds[key] = {"glb": _glb(rocket), "zip": _zip(rocket, report, params), "report": report}
    return {"id": key, **_builds[key]["report"]}


def _get(build_id: str) -> dict:
    if build_id not in _builds:
        raise HTTPException(404, "Build not found; press Build again.")
    return _builds[build_id]


@app.get("/api/builds/{build_id}/preview.glb")
def preview(build_id: str):
    return Response(_get(build_id)["glb"], media_type="model/gltf-binary")


@app.get("/api/builds/{build_id}/rocket.zip")
def download(build_id: str):
    return Response(_get(build_id)["zip"], media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="rocket_{build_id}.zip"'})


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
