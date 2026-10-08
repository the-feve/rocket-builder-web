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
| `POST /api/build` | design params (JSON) → build id, part list with masses, build notes, key dimensions. Errors are 422 with a readable `detail`. |
| `GET /api/builds/{id}/preview.glb` | every part in its assembled position, for the 3D preview |
| `GET /api/builds/{id}/rocket.zip` | one STL per part in print orientation, `build_notes.txt`, `design.json` |

The form's bounds are the FeatureScript dialog's. Motor and settings data come from `../geometry/rocketgen/data/*.csv`. A build takes about 5–10 s; the same parameters are served from the cache.

The page is dark by default; **Light mode** in the header switches it, and the choice is remembered in the browser.

In the viewer: drag to rotate, scroll to zoom, right-drag to pan. **Exploded** separates the parts; **Section** cuts the rocket in half along its axis.
