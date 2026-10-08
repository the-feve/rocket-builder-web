# Rocket Builder Web

A website for designing a 3D-printable model rocket and downloading print-ready STLs. The plan is in `docs/web_platform_spec.md`.

The geometry is a Python port, on build123d (OpenCascade), of the Onshape FeatureScript generator in [OS_Rocket_Builder](https://github.com/the-feve/OS_Rocket_Builder) (`src/RocketGenerator.fs`). That generator stays the reference design.

| Folder | What |
|---|---|
| `geometry/` | `rocketgen`, the geometry engine: parameters in, one solid per part out, STL export. See `geometry/README.md` and `geometry/report.md`. |
| `server/` | The designer website: FastAPI + one page with a three.js preview. See `server/README.md`. |
| `docs/` | Platform spec and plan |

## Status

- **Phase 0 (spike):** done.
- **Phase 1 (feature parity with the FeatureScript):** done, apart from two cosmetic items listed in `geometry/report.md`.
- **Phase 2 (local web prototype):** done. Form → build → 3D preview (exploded, section) → ZIP of print-oriented STLs. Dark theme by default, with a light-mode toggle.
- **Next: Phase 3,** hosted beta: stability check, saved designs and share links, sign-in, deployed.

```
cd geometry && pip install -e ".[test]" && python -m pytest -q
python -m rocketgen.cli --fins swept --out out/m18_swept --png

cd ../server && pip install -r requirements.txt && uvicorn app:app --reload   # open http://127.0.0.1:8000
```
