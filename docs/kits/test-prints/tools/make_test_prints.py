"""Test-print sets for the three proposed kits (docs/kits/README.md, Kit designs).

Builds each kit through the server's own build path (POST /api/build, then
GET /api/builds/{id}/rocket.zip, via FastAPI's TestClient: no web server, no
network), so the STLs are byte for byte what the app's Download gives. For
each kit it writes, under docs/kits/test-prints/<kit>/:

  A_nose.stl, B_anchor_section.stl, ... (letters as in the assembly guide)
  <kit>-rocket.zip   the app's ZIP, unchanged
  design.json        the app's saved-design file (Open file in the app)
  README.md          parameters, parts, print settings, motors, assembly order
  preview.png        the parts laid out (skip with --no-preview)

Rerun it after any geometry change, from the repo root:

    pip install -e geometry -r server/requirements.txt   # once
    python docs/kits/test-prints/tools/make_test_prints.py [--no-preview] [starter-m18 ...]

About a minute per kit (plus about a minute per preview).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
# The server keeps saved designs and orders on disk: point it at a throwaway place.
_tmp = tempfile.mkdtemp()
os.environ.setdefault("ROCKETGEN_DB", os.path.join(_tmp, "designs.sqlite3"))
os.environ.setdefault("ROCKETGEN_ORDERS_DIR", os.path.join(_tmp, "orders"))

from fastapi.testclient import TestClient  # noqa: E402

import app as server  # noqa: E402

# docs/kits/README.md, Kit designs: Beginner settings, printer max height
# 256 mm, trapezoid fins, tangent-ogive nose, 3 fins, PLA, auto-sized fins.
KITS = [
    {"dir": "starter-m18", "name": "Starter kit (M18, 18 mm motors)", "motor": "M18", "overall_length": 300},
    {"dir": "big-m24", "name": "Big kit (M24, 24 mm motors)", "motor": "M24", "overall_length": 360},
    {"dir": "mini-m13", "name": "Mini kit (M13, 13 mm motors)", "motor": "M13", "overall_length": 190},
]
COMMON = {"print_max_height": 256, "fin_shape": "trapezoid", "nose_shape": "tangent_ogive", "fin_count": 3,
          "material": "PLA"}

# Part names in the app -> the assembly guide's letters (docs/assembly/tools/scene_defs.js).
LETTERS = {"Nose": ("A", "nose"), "Anchor_Seg": ("B", "anchor_section"), "Aft": ("D", "fin_can"),
           "Motor_Cap": ("E", "motor_cap"), "Rod_Standoff": ("F", "rod_standoff")}
PART_TEXT = {
    "Nose": "Nose cone. Its tie bar inside the shoulder takes the shock cord's top end.",
    "Anchor_Seg": "Anchor section: the body tube's top piece, with the strap the shock cord ties to.",
    "Seg": "Middle body section.",
    "Aft": "Fin can: fins, motor bay, launch lugs and the threaded tail.",
    "Motor_Cap": "Motor cap: screws onto the tail and holds the motor in.",
    "Rod_Standoff": "Rod standoff: clips onto the launch rod under the aft lug, so the motor cap clears the blast deflector.",
}
PRINT_TIPS = {
    "Nose": "Tip up, shoulder on the bed. The shoulder's bed edge can bulge: sand it before fitting.",
    "Anchor_Seg": "Upright, as exported (strap prints without supports). Sand the bed edge of the shoulder.",
    "Seg": "Upright, as exported.",
    "Aft": "Upright on the tail, as exported; the fins stand vertical and the forward lug's 45-degree underside needs no support.",
    "Motor_Cap": "Flat face on the bed, as exported. 0.16 mm layers give a smoother thread if it binds.",
    "Rod_Standoff": "Upright, as exported. Tall and thin: add a 3-5 mm brim.",
}


def part_label(name: str, seg_index: int) -> tuple[str, str]:
    if name.startswith("Seg_"):
        return "C", f"body_section_{name.split('_')[1]}" if seg_index > 1 else "body_section"
    return LETTERS[name]


def form(kit: dict, defaults: dict) -> dict:
    """What the page's params() sends in Beginner mode: the defaults, plus
    motor, printer, height, fin and nose shape."""
    return {**defaults, **COMMON, "motor": kit["motor"], "overall_length": kit["overall_length"]}


def render_preview(rocket, labels: dict, path: Path, title: str):
    from rocketgen.export import PART_COLORS, render_png
    shapes, x = [], 0.0
    ordered = sorted(enumerate(rocket.parts), key=lambda ip: labels[ip[1].name][1])
    for i, p in ordered:
        bb = p.local.bounding_box()
        s = p.local.translate((x - bb.min.X, -bb.center().Y, -bb.min.Z))
        shapes.append((s, PART_COLORS[i % len(PART_COLORS)]))
        x += bb.size.X + 12
    order = "  ".join(labels[p.name][0] for _, p in ordered)
    render_png(shapes, path, elev=12, azim=-90, px=1100, title=f"{title}: parts {order}, left to right")


def fmt_list(xs):
    return ", ".join(xs) if xs else "none"


def write_readme(kit, folder, params, body, files, heights, z_margin):
    st, fl, chute, field = body["stability"], body["flights"], body["parachute"], body["field"]
    ok = [r for r in fl["rows"] if not r["problems"]]
    rec = next((r for r in fl["rows"] if r["code"] == fl["recommended"]), None)
    cord = "flat 1/8 in (3 mm) braided elastic" if params["motor"] in ("M13", "M18") else "flat 1/4 in (6 mm) braided elastic"
    length_m = st["length_mm"] / 1000
    L = [f"# {kit['name']}: test prints", "",
         f"Generated by `tools/make_test_prints.py` through the app's own build path (Rocket Builder "
         f"{server.GENERATOR_VERSION}); the STLs are the ones in `{kit['dir']}-rocket.zip`, which is what the app's "
         "Download gives. Open `design.json` with **Open file** in the app to see or change this design.", ""]
    if kit.get("adjusted"):
        L += [f"**Adjusted from the kit README:** {kit['adjusted']}", ""]
    L += ["## Design", "",
          "| Setting | Value |", "|---|---|",
          f"| Mode | Beginner |",
          f"| Motor size | {params['motor']} |",
          f"| Overall height (asked / built) | {params['overall_length']} mm / {st['length_mm']} mm |",
          f"| Printer max height | {params['print_max_height']} mm |",
          f"| Fins | {params['fin_count']} x {params['fin_shape']}, auto-sized (span/sweep scale {body['dimensions']['Fin span/sweep scale']}) |",
          f"| Nose | {params['nose_shape'].replace('_', ' ')}, fineness {params['nose_fineness']} |",
          f"| Body | OD {body['dimensions']['Body OD']:.1f} mm, wall {params['wall']} mm, length {body['body_length_mm']} mm |",
          f"| Launch lugs | {params['launch_lugs']} (aft + forward), 1/8 in rod, 4.0 mm bore; rod standoff on |",
          f"| Filament | {params['material']} |", "",
          "## Parts", "",
          "Heights and masses are the generator's (solid plastic; a real print with infill is lighter, so weigh it). "
          f"Every part must fit under the printer's {params['print_max_height']} mm "
          f"(the generator keeps {z_margin:g} mm spare).", "",
          "| Letter | File | Part | Print height | Solid mass |", "|---|---|---|---|---|"]
    parts = sorted(body["parts"], key=lambda p: files[p["name"]][1])  # A, B, C..., D, E, F
    for p in parts:
        letter, fname = files[p["name"]]
        L.append(f"| **{letter}** | `{fname}` | {PART_TEXT['Seg' if p['name'].startswith('Seg_') else p['name']]} "
                 f"| {p['height_mm']} mm | {p['mass_g']} g |")
    L += [f"| | | **Total printed** | tallest {max(heights):.1f} mm | **{body['total_mass_g']} g** |", "",
          "## Print settings", "",
          "- **Material:** PLA (the masses and flight numbers assume PLA, 1.24 g/cm3). PETG works but is a little heavier.",
          "- **Nozzle and layers:** 0.4 mm nozzle, 0.2 mm layers (0.16 mm for the motor cap if its thread binds).",
          f"- **Walls:** 4 perimeters (at least 1.6 mm), so the {params['wall']} mm tube walls and the fins print solid. "
          "Top/bottom 5 layers.",
          "- **Infill:** 20 % gyroid (only the thick bits have any: the tail, the cap, the nose tip).",
          "- **Orientation:** as exported (each STL already rests on z = 0 in its print orientation). Do not rotate.",
          "- **Supports:** none. The overhangs (forward lug underside, anchor strap, nose tie bar recess) are 45 degrees "
          "or bridged by design.",
          "- **Bed adhesion:** clean PEI or glue stick; brim only on the rod standoff (F).", ""]
    L += ["| Part | Orientation note |", "|---|---|"]
    for p in parts:
        L.append(f"| {files[p['name']][0]} | {PRINT_TIPS['Seg' if p['name'].startswith('Seg_') else p['name']]} |")
    L += ["", "## Flying it", "",
          f"- **Stability:** {st['margin_cal']} calibers with the {st['motor']} (the heaviest {params['motor']} motor) "
          f"and the default recovery allowance ({st['recovery_mass_g']} g): {st['status']}. CG {st['cg_mm']} mm and "
          f"CP {st['cp_mm']} mm from the nose tip; liftoff mass {st['liftoff_mass_g']} g.",
          f"- **Recommended motor (app, target {fl['target_m']:g} m):** "
          + (f"**{rec['motor']}**, predicted apogee **{rec['apogee_m']} m ({round(rec['apogee_m'] * 3.281)} ft)**, "
             f"{rec['margin_cal']} cal." if rec else "none."),
          f"- **Motors that pass the app's checks:** {fmt_list(['%s (%d m)' % (r['motor'], r['apogee_m']) for r in ok])}.",
          "",
          "| Motor | Apogee | Margin | Verdict |", "|---|---|---|---|"]
    for r in fl["rows"]:
        L.append(f"| {r['motor']}{' (out of production)' if r['out_of_production'] else ''} | {r['apogee_m']} m | "
                 f"{r['margin_cal']} cal | {'OK' if not r['problems'] else ', '.join(r['problems'])} |")
    chute_line = (f"**{chute['size_in']} in** parachute (at least {chute['min_diameter_in']:g} in): about "
                  f"{chute['descent_ms']} m/s down with {chute['descent_mass_g']:g} g")
    if chute.get("streamer_ok"):
        chute_line += "; light enough for a streamer instead"
    L += ["", f"- **Recovery:** {chute_line}.",
          f"- **Shock cord:** {cord}, {2 * length_m:.1f}-{3 * length_m:.1f} m long (2-3 x the rocket's "
          f"{st['length_mm']:.0f} mm). Round 1/8 in elastic also fits.",
          ]
    if field:
        L.append(f"- **Field:** at least {field['recommended_m']} m on a side with the {field['motor']} "
                 f"(NAR minimum {field['nar_min_m']} m).")
    L += ["- Weigh the printed parts and re-run the design in the app (Advanced: mass overrides) before the first flight.",
          "", "## Assembly order", "",
          "Follow `docs/assembly/assembly-guide.html` (or the PDF). In short:", "",
          "1. Check every part: sand the bed-edge lip off the shoulders and the start of the tail thread; no cracks.",
          "2. Dry-fit the joints: B and D slide together, A's shoulder slides into B (only the motor cap E is threaded).",
          "3. Tie the shock cord behind B's anchor strap, and its other end to A's tie bar; tie the parachute on near A.",
          "4. Wadding, then fold in the parachute and cord; fit A.",
          "5. Motor in (nozzle end last), screw on E.",
          "6. At the pad: F clips onto the rod, and the rocket's lugs slide down onto it until the aft lug sits on F.", ""]
    (folder / "README.md").write_text("\n".join(L))


def main():
    import logging
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("kits", nargs="*", help="kit folders to build (default: all)")
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args()
    client = TestClient(server.app)
    defaults = client.get("/api/options").json()["defaults"]
    from rocketgen.params import load_settings
    z_margin = load_settings()["z_margin"]
    summary = []
    for kit in KITS:
        if a.kits and kit["dir"] not in a.kits:
            continue
        params = form(kit, defaults)
        h = client.get("/api/heights", params={"motor": params["motor"], "print_max_height": params["print_max_height"],
                                                "fin_shape": params["fin_shape"], "nose_shape": params["nose_shape"]}).json()
        if not any(lo <= params["overall_length"] <= hi for lo, hi in h["ranges"]):
            raise SystemExit(f"{kit['dir']}: {params['overall_length']} mm isn't in the app's heights {h['ranges']}")
        r = client.post("/api/build", json=params)
        if r.status_code != 200:
            raise SystemExit(f"{kit['dir']}: build failed: {r.text}")
        body = r.json()
        st = body["stability"]
        if not st["ok"]:
            raise SystemExit(f"{kit['dir']}: unstable: {st['message']}")
        heights = [p["height_mm"] for p in body["parts"]]
        if max(heights) > params["print_max_height"]:
            raise SystemExit(f"{kit['dir']}: a part is {max(heights)} mm tall, over the printer's {params['print_max_height']}")
        zbytes = client.get(f"/api/builds/{body['id']}/rocket.zip").content
        folder = OUT / kit["dir"]
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.stl"):
            old.unlink()
        (folder / f"{kit['dir']}-rocket.zip").write_bytes(zbytes)
        segs = [p["name"] for p in body["parts"] if p["name"].startswith("Seg_")]
        files = {}
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
            for p in body["parts"]:
                letter, stem = part_label(p["name"], len(segs))
                fname = f"{letter}_{stem}.stl"
                files[p["name"]] = (letter, fname)
                (folder / fname).write_bytes(z.read(f"{p['name']}.stl"))
        design = {"format": "rocket-builder-design", "schemaVersion": 1, "name": kit["name"].split(" (")[0],
                  "mode": "beginner", "params": params}
        (folder / "design.json").write_text(json.dumps(design, indent=2) + "\n")
        write_readme(kit, folder, params, body, files, heights, z_margin)
        if not a.no_preview:
            rocket = server._geo[server._builds[body["id"]]["geo"]]["rocket"]
            render_preview(rocket, files, folder / "preview.png", kit["name"])
        rec = next((x for x in body["flights"]["rows"] if x["code"] == body["flights"]["recommended"]), None)
        summary.append((kit["dir"], st["length_mm"], body["total_mass_g"], st["margin_cal"],
                        rec and rec["motor"], rec and rec["apogee_m"], [files[p["name"]][1] for p in body["parts"]]))
        print(f"{kit['dir']}: {st['length_mm']} mm, {body['total_mass_g']} g, {st['margin_cal']} cal, "
              f"recommended {rec and rec['motor']} ({rec and rec['apogee_m']} m), parts {heights}", flush=True)
    return summary


if __name__ == "__main__":
    main()
