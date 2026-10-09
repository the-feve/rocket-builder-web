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
import logging
import os
import tempfile
import threading
import time
import zipfile
from collections import OrderedDict, defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from build123d import export_stl
from rocketgen.export import PART_COLORS
from rocketgen.fins import FinShape
from rocketgen.geom import GeometryError
from rocketgen.params import LUG_OPTIONS, MATERIALS, NOSE_SHAPES, DesignParams, compute_derived, load_motors
from rocketgen.flight import FIELD_M, motors_for, pick, simulate
from rocketgen.build import body_length_for, overall_length
from rocketgen.stability import Balance, build_stable, recovery_allowance_g

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
    # Beginner mode: the overall height (nose tip to fin tips / motor cap);
    # when set, body_length is worked out from it and the typed one ignored.
    overall_length: float | None = Field(None, ge=80, le=2500)
    body_od_override: float | None = Field(None, ge=5, le=200)
    print_max_height: float = Field(200.0, ge=50, le=500)
    launch_lugs: str = "two"
    rod_diameter: float = Field(3.175, ge=2, le=13)
    rod_standoff: bool = True
    pad_clearance: float = Field(15.0, ge=0, le=100)
    forward_lug_frac: float = Field(0.5, ge=0.2, le=0.95)
    material: str = "PLA"
    # Flight: not geometry. flight_motor None = the heaviest motor of the size;
    # recovery_mass_g None = the default allowance.
    flight_motor: str | None = None
    recovery_mass_g: float | None = Field(None, ge=0, le=500)
    target_altitude_m: float = Field(150.0, ge=10, le=3000)
    drag_cd: float = Field(0.65, ge=0.2, le=1.5)
    launch_rod_m: float = Field(0.91, ge=0.3, le=3)


BEGINNER_FINS = ["swept", "delta", "trapezoid"]

FLIGHT_FIELDS = ("flight_motor", "recovery_mass_g", "target_altitude_m", "drag_cd", "launch_rod_m")


log = logging.getLogger("rocketbuilder")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Public-internet guards. A build holds the one OpenCascade lock for 5-10 s,
# so a visitor waits at most BUILD_WAIT_S for their turn, and each address
# gets a budget of new (uncached) builds and saves.
BUILD_WAIT_S = float(os.environ.get("ROCKETGEN_BUILD_WAIT_S", 60))
BUILDS_PER_10_MIN = int(os.environ.get("ROCKETGEN_BUILDS_PER_10_MIN", 30))
SAVES_PER_HOUR = int(os.environ.get("ROCKETGEN_SAVES_PER_HOUR", 60))

app = FastAPI(title="Rocket Builder")
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def _client(request: Request) -> str:
    # Behind Cloudflare and Fly's proxy the socket address is the proxy's.
    h = request.headers
    return h.get("cf-connecting-ip") or h.get("fly-client-ip") or (request.client.host if request.client else "?")


def _rate_limit(request: Request, kind: str, limit: int, window_s: float):
    now = time.monotonic()
    q = _hits[(kind, _client(request))]
    while q and now - q[0] > window_s:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many requests from your address; wait a few minutes and try again.")
    q.append(now)
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
        "body_length_mm": round(rocket.params.body_length, 1),
        "parts": parts,
        "total_mass_g": round(sum(masses.values()), 1),
        "summary": rocket.summary(),
        "notes": list(rocket.notes),
        "dimensions": {
            "Body OD": d.body_od, "Body ID": d.body_id, "Motor bay ID": d.bay_id,
            "Inner motor mount": "yes" if d.has_mount else "no (minimum diameter)",
            "Shoulder OD": d.shoulder_od, "Shoulder length": d.shoulder_len,
            "Motor hang-out": t["hang"], "Thread pitch": t["p"], "Thread turns": t["turns"],
            "Body length": round(rocket.params.body_length, 1),
            "Body segments": len(rocket.seg_lens),
            "Fin span/sweep scale": rocket.params.fin_scale,
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
            "motor_mass_g": st.motor_mass_g, "motor": st.motor,
            "recovery_mass_g": st.recovery_mass_g, "status": st.status, "ok": st.ok, "message": st.message}


def _zip(stls: dict[str, bytes], report: dict, stab: dict, params: dict, flights: dict | None = None) -> bytes:
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
        if flights:
            lines += ["", f"Motors (target {flights['target_m']:g} m; recommended: {flights['recommended'] or 'none'}):"]
            lines += [f"  {r['motor']}: {r['apogee_m']} m, {r['margin_cal']} cal, "
                      + ("OK" if not r["problems"] else ", ".join(r["problems"])) for r in flights["rows"]]
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
        # Beginner mode: motor, printer height, overall height, nose shape and
        # one of three standard fin shapes; everything else stays at defaults.
        "beginner": {"fin_shapes": BEGINNER_FINS, "fin_shape": BEGINNER_FINS[2],
                     "overall_length": round(overall_length(DesignParams(fin_shape=FinShape(BEGINNER_FINS[2]))))},
        "flight_motors": {size: [{"code": m.code, "cls": m.cls, "mass_g": m.mass_g, "out_of_production": m.out_of_production}
                                 for m in motors_for(size)] for size in load_motors()},
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


def _build_to_length(params: DesignParams, overall: float | None):
    """build_stable, sized to an overall height when one is given. Auto-sized
    fins can change how far the fin tips trail below the tail, so when they
    do, rebuild once at the corrected body length, starting from the fin
    scale already found (normally no further scaling)."""
    if overall is None:
        return build_stable(params)
    rocket = build_stable(params.with_(body_length=body_length_for(params, overall)))
    if abs(Balance(rocket).length - overall) > 0.5:
        p = rocket.params
        rocket = build_stable(p.with_(body_length=body_length_for(p, overall)))
    return rocket


def _geometry(geo_params: dict, req: BuildRequest, request: Request) -> str:
    key = _key(geo_params)
    try:
        _geo.move_to_end(key)  # cached: no lock, no rate limit
        return key
    except KeyError:
        pass
    _rate_limit(request, "build", BUILDS_PER_10_MIN, 600)
    if not _lock.acquire(timeout=BUILD_WAIT_S):
        raise HTTPException(503, "The builder is busy with other rockets; try again in a minute.")
    try:
        if key in _geo:  # built by another request while this one waited
            return key
        t0 = time.monotonic()
        try:
            rocket = _build_to_length(DesignParams(**{**{k: v for k, v in geo_params.items() if k != "overall_length"},
                                                     "fin_shape": req.fin_shape}), req.overall_length)
        except (GeometryError, ValueError) as ex:
            raise HTTPException(422, str(ex))
        except Exception as ex:  # an OpenCascade failure: never a bare 500
            log.exception("build failed: %s", json.dumps(geo_params, sort_keys=True))
            raise HTTPException(422, f"The geometry engine could not build this design ({type(ex).__name__}). "
                                     "Try slightly different settings.")
        _geo[key] = {"rocket": rocket, "balance": Balance(rocket), "glb": _glb(rocket), "report": _report(rocket), "stls": None}
        while len(_geo) > MAX_CACHED:
            _geo.popitem(last=False)
        log.info("built %s in %.1f s (fin scale %s)", key, time.monotonic() - t0, rocket.params.fin_scale)
    finally:
        _lock.release()
    return key


@app.post("/api/build")
def build(req: BuildRequest, request: Request):
    params = req.model_dump(mode="json")
    if req.motor not in load_motors():
        raise HTTPException(422, f"Unknown motor {req.motor!r}.")
    if req.material not in MATERIALS:
        raise HTTPException(422, f"Unknown material {req.material!r}.")
    motors = {m.code: m for m in motors_for(req.motor)}
    if req.flight_motor is not None and req.flight_motor not in motors:
        raise HTTPException(422, f"{req.flight_motor} doesn't fit the {req.motor} motor bay.")
    geo_params = {k: v for k, v in params.items() if k not in FLIGHT_FIELDS}
    geo = _geometry(geo_params, req, request)
    bal: Balance = _geo[geo]["balance"]
    st = _stability(bal.check(motors.get(req.flight_motor), req.recovery_mass_g))
    flights = _flights(bal, list(motors.values()), req)
    build_id = _key(params)
    _builds[build_id] = {"geo": geo, "params": params, "stability": st, "flights": flights}
    return {"id": build_id, **_geo[geo]["report"], "stability": st, "flights": flights}


def _flights(bal: Balance, motors: list, req: BuildRequest) -> dict:
    """The motor picker: every motor of the bay size flown, each with its own
    stability margin; the safe, stable one closest to the target altitude."""
    rec = recovery_allowance_g(bal.body_od) if req.recovery_mass_g is None else req.recovery_mass_g
    rows, safe = [], []
    for m in motors:
        f = simulate(m, bal.printed_mass_g + rec, bal.body_od, req.drag_cd, req.launch_rod_m)
        st = bal.check(m, req.recovery_mass_g)
        problems = list(f.problems) + ([] if st.ok else ["Unstable"])
        if not problems:
            safe.append(f)
        rows.append({"motor": f"{m.code}-{f.delay}", "code": m.code, "cls": m.cls, "apogee_m": round(f.apogee),
                     "rod_speed_ms": round(f.rod_speed, 1), "thrust_to_weight": round(f.thrust_to_weight, 1),
                     "coast_s": round(f.coast, 1), "delay_s": f.delay, "margin_cal": round(st.margin_cal, 2),
                     "liftoff_g": round(st.total_mass_g), "field_m": FIELD_M[m.cls], "problems": problems,
                     "out_of_production": m.out_of_production, "mass_estimated": m.mass_estimated})
    best = pick(safe, req.target_altitude_m)
    return {"target_m": req.target_altitude_m, "rows": rows, "recommended": best and best.motor.code}


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
    return Response(_zip(g["stls"], g["report"], b["stability"], b["params"], b["flights"]), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="rocket_{build_id}.zip"'})


# ---------- saved designs and share links ----------

class DesignIn(BaseModel):
    name: str = Field("My rocket", min_length=1, max_length=80)
    params: BuildRequest


class DesignRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@app.post("/api/designs")
def save_design(d: DesignIn, request: Request):
    """A new saved design. The edit key comes back once; the page keeps it
    in this browser and sends it to rename or overwrite. Until sign-in
    exists, it is the only proof of ownership."""
    _rate_limit(request, "save", SAVES_PER_HOUR, 3600)
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


@app.get("/healthz")
def healthz():
    """Fly's health check: the process is up and the designs database opens."""
    designs.get("healthz")
    return {"ok": True, "generatorVersion": GENERATOR_VERSION}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/d/{design_id}")
def shared(design_id: str):
    """A share link: the page loads the design and builds it."""
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
