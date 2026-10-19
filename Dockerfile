# The designer website: rocketgen + the FastAPI server, one container.
#   docker build -t rocket-builder .
#   docker run -p 8000:8000 -v rocket-data:/data rocket-builder     # open http://127.0.0.1:8000
# Trebuchet Builder, Fit Test Builder and ShedCAD ride along: the deploy checks
# out the-feve/trebuchet_builder into trebuchet/, the-feve/3D_print_test_fitter
# into fittest/ and the-feve/Shed_builder into shed/ first
# (server/trebuchet_mount.py, fit_mount.py, shed_mount.py).
# Building by hand without them: `mkdir trebuchet fittest shed` (the rocket app
# then runs on its own).
FROM python:3.12-slim-bookworm

# OpenCascade (via the OCP wheels) needs these shared libraries even headless.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY geometry/pyproject.toml geometry/README.md geometry/
COPY geometry/rocketgen geometry/rocketgen
COPY server/requirements.txt server/
RUN cd server && pip install --no-cache-dir -r requirements.txt
# ShedCAD's optional floor-plan import modules (OpenCV etc.), only when its
# checkout is there. server/requirements.txt is listed too so the COPY always
# has a source; the [t] glob lets the ShedCAD file be missing.
COPY server/requirements.txt shed/requirements-blueprint.tx[t] /tmp/shedreq/
RUN if [ -f /tmp/shedreq/requirements-blueprint.txt ]; then \
      pip install --no-cache-dir -r /tmp/shedreq/requirements-blueprint.txt \
      || echo "ShedCAD floor-plan modules not installed; tracing by hand still works"; \
    fi; rm -rf /tmp/shedreq
COPY server server
COPY trebuchet trebuchet
COPY fittest fittest
COPY shed shed

ENV ROCKETGEN_DB=/data/designs.sqlite3 PORT=8000
VOLUME /data
WORKDIR /app/server
# One worker: builds are serialised by a lock and cached in this process.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
