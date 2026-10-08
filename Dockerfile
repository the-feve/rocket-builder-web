# The designer website: rocketgen + the FastAPI server, one container.
#   docker build -t rocket-builder .
#   docker run -p 8000:8000 -v rocket-data:/data rocket-builder     # open http://127.0.0.1:8000
FROM python:3.12-slim-bookworm

# OpenCascade (via the OCP wheels) needs these shared libraries even headless.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY geometry/pyproject.toml geometry/README.md geometry/
COPY geometry/rocketgen geometry/rocketgen
COPY server/requirements.txt server/
RUN cd server && pip install --no-cache-dir -r requirements.txt
COPY server server

ENV ROCKETGEN_DB=/data/designs.sqlite3 PORT=8000
VOLUME /data
WORKDIR /app/server
# One worker: builds are serialised by a lock and cached in this process.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
