"""Fit Test Builder hosted inside this app (server/fit_mount.py)."""

import asyncio
import os
import tempfile

import pytest

os.environ.setdefault("ROCKETGEN_DB", os.path.join(tempfile.mkdtemp(), "designs.sqlite3"))
os.environ.setdefault("ROCKETGEN_ORDERS_DIR", os.path.join(tempfile.mkdtemp(), "orders"))

from fastapi.testclient import TestClient

import app as rocket
import fit_mount
import trebuchet_mount


def test_host_router_sends_fit_hosts_to_the_mount():
    seen = []

    async def inner(scope, receive, send):
        seen.append(scope["path"])

    router = trebuchet_mount.HostRouter(inner, routes={"trebuchet.": "/trebuchet", "fit.": "/fit"})
    for host, path in [(b"fit.quiverdesignworks.net", "/"), (b"fit.quiverdesignworks.net", "/api/build"),
                       (b"fit.quiverdesignworks.net", "/fit/api/build"), (b"trebuchet.quiverdesignworks.net", "/"),
                       (b"rocket.quiverdesignworks.net", "/fit/")]:
        asyncio.run(router({"type": "http", "path": path, "headers": [(b"host", host)]}, None, None))
    assert seen == ["/fit/", "/fit/api/build", "/fit/api/build", "/trebuchet/", "/fit/"]


def test_missing_checkout_means_no_mount(monkeypatch, tmp_path):
    monkeypatch.setenv("FIT_DIR", str(tmp_path))
    assert fit_mount.load_module() is None


needs_fit = pytest.mark.skipif(rocket.FIT is None, reason="fittest/ not checked out")


@needs_fit
def test_fit_served_under_prefix_and_host():
    c = TestClient(rocket.app)
    assert c.get("/fit", follow_redirects=False).headers["location"] == "/fit/"
    r = c.get("/fit/")
    assert "Fit Test Builder" in r.text and "x-robots-tag" not in r.headers  # public since 2026-10-18
    assert "Fit Test Builder" in c.get("/", headers={"host": "fit.quiverdesignworks.net"}).text
    assert rocket.FIT._lock is rocket._lock
    assert c.get("/fit/static/vendor/three/build/three.module.js").status_code == 200
    r = c.post("/fit/api/build", json={"shape": "round", "sizes": [8], "clearances": [0.2], "lengths": [6]})
    assert r.status_code == 200 and r.json()["report"]["count"] == 2
    assert "Rocket Builder" in c.get("/").text
    assert c.get("/healthz").json()["ok"]


@needs_fit
def test_admin_only_switch(monkeypatch):
    c = TestClient(rocket.app)
    monkeypatch.setattr(rocket, "FIT_ADMIN_ONLY", True)
    assert c.get("/fit/").status_code == 404
    assert c.get("/", headers={"host": "fit.quiverdesignworks.net"}).status_code == 404
    r = c.post("/api/auth/signup", json={"email": "fit-admin@example.com", "password": "correct horse 42", "age_ok": True})
    assert r.status_code == 200, r.text
    monkeypatch.setattr(rocket, "ADMIN_EMAILS", {"fit-admin@example.com"})
    assert "Fit Test Builder" in c.get("/fit/").text
