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
- **Phase 3 (hosted beta):** in progress.
  - Done: stability check (Barrowman CP, CG from the parts + motor + recovery; under 1.0 cal the ZIP is withheld), saved designs and share links (`/d/<id>`, SQLite, edit key per browser until sign-in exists), `Dockerfile`.
  - Open: the Docker image hasn't been built yet (Docker Hub rate-limited the cloud sandbox); sign-in (replaces the edit key with an owner); deploying it. Both wait on the hosting choice, which goes with the owner's personal-site move off Squarespace.

```
cd geometry && pip install -e ".[test]" && python -m pytest -q
python -m rocketgen.cli --fins swept --out out/m18_swept --png

cd ../server && pip install -r requirements.txt && uvicorn app:app --reload   # open http://127.0.0.1:8000
```

Or in Docker, from the repo root: `docker build -t rocket-builder . && docker run -p 8000:8000 -v rocket-data:/data rocket-builder`.
