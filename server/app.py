"""The designer website: one page, one FastAPI server, synchronous builds.

    cd server && uvicorn app:app --reload        # then open http://127.0.0.1:8000

POST /api/build builds a rocket with rocketgen and caches the geometry under
a hash of the geometry parameters; the stability check (motor and recovery
masses) is cheap and is redone per request. The page then loads the GLB
preview and offers the ZIP of print-oriented STLs, unless the rocket is
unstable. Designs are saved in SQLite (designs.py) and shared by link.
"""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import threading
import zipfile
from collections import OrderedDict
from pathlib import Path

import numpy as np
import trimesh
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from build123d import export_stl
from rocketgen.build import build_rocket
from rocketgen.export import PART_COLORS
from rocketgen.fins import FinShape
from rocketgen.geom import GeometryError
from rocketgen.params import LUG_OPTIONS, MATERIALS, NOSE_SHAPES, DesignParams, compute_derived, load_motors
from rocketgen.stability import load_motor_masses, recovery_allowance_g, stability

import designs

STATIC = Path(__file__).resolve().parent / "static"
GENERATOR_VERSION = "0.1.0"
SCHEMA_VERSION = 1
MAX_CACHED = 40  # geometry builds kept in memory


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
    # Flight: not geometry. None = the heaviest common motor of the size, and the default allowance.
    motor_mass_g: float | None = Field(None, ge=1, le=500)
    recovery_mass_g: float | None = Field(None, ge=0, le=500)


FLIGHT_FIELDS = ("motor_mass_g", "recovery_mass_g")


app = FastAPI(title="Rocket Builder")
_geo: OrderedDict[str, dict] = OrderedDict()  # geometry key -> {"rocket", "glb", "report", "stls"}
_builds: dict[str, dict] = {}  # build id -> {"geo", "params", "stability"}
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


def _stls(rocket) -> dict[str, bytes]:
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for p in rocket.parts:
            path = Path(tmp) / f"{p.name}.stl"
            export_stl(p.local, path, tolerance=0.01, angular_tolerance=0.1)
            out[p.name] = path.read_bytes()
    return out


def _stability(st) -> dict:
    return {"cg_mm": round(st.cg, 1), "cp_mm": round(st.cp, 1), "margin_cal": round(st.margin_cal, 2),
            "length_mm": round(st.length, 1), "liftoff_mass_g": round(st.total_mass_g, 1),
            "motor_mass_g": st.motor_mass_g, "motor_example": st.motor_example,
            "recovery_mass_g": st.recovery_mass_g, "status": st.status, "ok": st.ok, "message": st.message}


def _zip(stls: dict[str, bytes], report: dict, stab: dict, params: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in stls.items():
            z.writestr(f"{name}.stl", data)
        lines = ["Rocket Builder build notes", "", report["summary"], ""]
        lines += [f"Note: {n}" for n in report["notes"]]
        lines += ["", "Stability (from the nose tip, mm):", f"  {stab['message']}",
                  f"  CG {stab['cg_mm']}, CP {stab['cp_mm']}, liftoff mass {stab['liftoff_mass_g']} g "
                  f"(motor {stab['motor_mass_g']} g, recovery {stab['recovery_mass_g']} g).",
                  "  Check it in OpenRocket with your actual motor, recovery and paint before flying.",
                  "  Follow the NAR Model Rocket Safety Code."]
        lines += ["", "Parts (STLs are in print orientation, resting on z = 0):"]
        lines += [f"  {p['name']}: {p['mass_g']} g, {p['height_mm']} mm tall" for p in report["parts"]]
        lines += ["", "Key dimensions (mm):"]
        lines += [f"  {k}: {round(v, 2) if isinstance(v, float) else v}" for k, v in report["dimensions"].items()]
        z.writestr("build_notes.txt", "\n".join(lines) + "\n")
        z.writestr("design.json", json.dumps({"generatorVersion": GENERATOR_VERSION, "schemaVersion": SCHEMA_VERSION,
                                              "params": params}, indent=2))
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
        "motor_masses": load_motor_masses(),
    }


@app.get("/api/recovery_allowance")
def recovery_allowance(motor: str = "M18", body_od_override: float | None = None):
    """The default recovery mass for the form's placeholder."""
    if motor not in load_motors():
        raise HTTPException(422, f"Unknown motor {motor!r}.")
    d = compute_derived(DesignParams(motor=motor, body_od_override=body_od_override))
    return {"recovery_mass_g": recovery_allowance_g(d.body_od)}


def _key(*parts) -> str:
    return hashlib.sha256(json.dumps([GENERATOR_VERSION, *parts], sort_keys=True).encode()).hexdigest()[:16]


def _geometry(geo_params: dict, req: BuildRequest) -> str:
    key = _key(geo_params)
    with _lock:
        if key in _geo:
            _geo.move_to_end(key)
            return key
        try:
            rocket = build_rocket(DesignParams(**{**geo_params, "fin_shape": req.fin_shape}))
        except (GeometryError, ValueError) as ex:
            raise HTTPException(422, str(ex))
        except Exception as ex:  # an OpenCascade failure: never a bare 500
            raise HTTPException(422, f"The geometry engine could not build this design ({type(ex).__name__}). "
                                     "Try slightly different settings.")
        _geo[key] = {"rocket": rocket, "glb": _glb(rocket), "report": _report(rocket), "stls": None}
        while len(_geo) > MAX_CACHED:
            _geo.popitem(last=False)
    return key


@app.post("/api/build")
def build(req: BuildRequest):
    params = req.model_dump(mode="json")
    if req.motor not in load_motors():
        raise HTTPException(422, f"Unknown motor {req.motor!r}.")
    if req.material not in MATERIALS:
        raise HTTPException(422, f"Unknown material {req.material!r}.")
    geo_params = {k: v for k, v in params.items() if k not in FLIGHT_FIELDS}
    geo = _geometry(geo_params, req)
    st = _stability(stability(_geo[geo]["rocket"], req.motor_mass_g, req.recovery_mass_g))
    build_id = _key(params)
    _builds[build_id] = {"geo": geo, "params": params, "stability": st}
    return {"id": build_id, **_geo[geo]["report"], "stability": st}


def _get(build_id: str) -> tuple[dict, dict]:
    b = _builds.get(build_id)
    if not b or b["geo"] not in _geo:
        raise HTTPException(404, "Build not found; press Build again.")
    return b, _geo[b["geo"]]


@app.get("/api/builds/{build_id}/preview.glb")
def preview(build_id: str):
    return Response(_get(build_id)[1]["glb"], media_type="model/gltf-binary")


@app.get("/api/builds/{build_id}/rocket.zip")
def download(build_id: str):
    b, g = _get(build_id)
    if not b["stability"]["ok"]:
        raise HTTPException(409, b["stability"]["message"])
    if g["stls"] is None:
        with _lock:
            g["stls"] = _stls(g["rocket"])
    return Response(_zip(g["stls"], g["report"], b["stability"], b["params"]), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="rocket_{build_id}.zip"'})


# ---------- saved designs and share links ----------

class DesignIn(BaseModel):
    name: str = Field("My rocket", min_length=1, max_length=80)
    params: BuildRequest


class DesignRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@app.post("/api/designs")
def save_design(d: DesignIn):
    """A new saved design. The edit key comes back once; the page keeps it
    in this browser and sends it to rename or overwrite. Until sign-in
    exists, it is the only proof of ownership."""
    return designs.create(d.name, d.params.model_dump(mode="json"), GENERATOR_VERSION, SCHEMA_VERSION)


@app.get("/api/designs/{design_id}")
def load_design(design_id: str):
    row = designs.get(design_id)
    if not row:
        raise HTTPException(404, "That design link doesn't exist.")
    return row


@app.put("/api/designs/{design_id}")
def update_design(design_id: str, d: DesignIn, x_edit_key: str = Header("")):
    _owned(design_id, x_edit_key)
    return designs.update(design_id, d.name, d.params.model_dump(mode="json"), GENERATOR_VERSION, SCHEMA_VERSION)


@app.patch("/api/designs/{design_id}")
def rename_design(design_id: str, d: DesignRename, x_edit_key: str = Header("")):
    _owned(design_id, x_edit_key)
    return designs.rename(design_id, d.name)


@app.delete("/api/designs/{design_id}")
def delete_design(design_id: str, x_edit_key: str = Header("")):
    _owned(design_id, x_edit_key)
    designs.delete(design_id)
    return {"deleted": design_id}


def _owned(design_id: str, key: str):
    if not designs.get(design_id):
        raise HTTPException(404, "That design doesn't exist.")
    if not designs.check_key(design_id, key):
        raise HTTPException(403, "This design was saved from another browser; use Save as new to keep a copy.")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/d/{design_id}")
def shared(design_id: str):
    """A share link: the page loads the design and builds it."""
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
