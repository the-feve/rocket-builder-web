# Designer website

One FastAPI server and one page (`static/index.html`, three.js loaded from jsDelivr). No accounts, no database; builds are kept in memory until the server stops.

```
pip install -r requirements.txt     # installs ../geometry (rocketgen) too
uvicorn app:app --reload            # open http://127.0.0.1:8000
python -m pytest -q                 # server tests (about 10 s)
```

| Endpoint | What |
|---|---|
| `GET /api/options` | motors, fin and nose shapes, lug options, materials, form defaults |
| `POST /api/build` | design params (JSON) → build id, part list with masses, build notes, key dimensions, `stability`. Errors are 422 with a readable `detail`. |
| `GET /api/builds/{id}/preview.glb` | every part in its assembled position, for the 3D preview |
| `GET /api/builds/{id}/rocket.zip` | one STL per part in print orientation, `build_notes.txt`, `design.json`. 409 if the rocket is unstable. |
| `POST /api/designs` | `{name, params}` → saved design, with its `edit_key` (returned once) |
| `GET /api/designs/{id}` | a saved design; `/d/{id}` is its share link, which opens and builds it |
| `PUT` / `PATCH` / `DELETE /api/designs/{id}` | overwrite, rename, delete; need the `X-Edit-Key` header |

**Stability** (`rocketgen/stability.py`): CP by Barrowman (nose + fins), CG from the printed parts' centroids plus a loaded motor and a recovery allowance. With standard fin sizes, `build_stable` grows the fins' span and sweep (up to 2.5x) until the rocket is stable with the heaviest motor of its size; custom fins are left as typed. Under 1.0 caliber with the motor chosen under Flight (default: the heaviest) the preview still shows, with the CG (blue) and CP (red) marked, but the ZIP is withheld. Over 3 cal is a warning only.

**Motor picker** (`rocketgen/flight.py`, ported from OS_Rocket_Builder `tools/motor-picker.html`): every Estes motor that fits the bay (`rocketgen/data/web_motors.csv`, ThrustCurve.org data) is flown in a 1-D simulation; it must reach 5x thrust-to-weight, 15 m/s off the rod and 30 m, and be stable with its own mass. The one closest to the target altitude is recommended, with its delay. Clicking a row re-checks stability with that motor.

**Saved designs** (`designs.py`): SQLite at `ROCKETGEN_DB` (default `data/designs.sqlite3`). No accounts yet: saving returns an edit key that this browser keeps in localStorage with the design's id ("My rockets"); anyone with the link can open a design and save their own copy. Each design stores `generatorVersion` and `schemaVersion`.

The geometry of a build is cached in memory (the last 40) by a hash of the geometry parameters; the motor and recovery masses only redo the stability check.

The form's bounds are the FeatureScript dialog's. Motor and settings data come from `../geometry/rocketgen/data/*.csv`. A build takes about 5–10 s.

The page is dark by default; **Light mode** in the header switches it, and the choice is remembered in the browser.

In the viewer: drag to rotate, scroll to zoom, right-drag to pan. **Exploded** separates the parts; **Section** cuts the rocket in half along its axis.
