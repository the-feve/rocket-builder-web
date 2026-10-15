"""Trebuchet Builder hosted inside this app (server/trebuchet_mount.py)."""

import asyncio
import os
import tempfile

import pytest

os.environ.setdefault("ROCKETGEN_DB", os.path.join(tempfile.mkdtemp(), "designs.sqlite3"))
os.environ.setdefault("ROCKETGEN_ORDERS_DIR", os.path.join(tempfile.mkdtemp(), "orders"))

from fastapi.testclient import TestClient

import app as rocket
import trebuchet_mount


def test_host_router_prefixes_trebuchet_hosts_only():
    seen = []

    async def inner(scope, receive, send):
        seen.append(scope["path"])

    router = trebuchet_mount.HostRouter(inner)
    for host, path in [(b"trebuchet.quiverdesignworks.net", "/"), (b"trebuchet.quiverdesignworks.net", "/api/plan"),
                       (b"trebuchet.quiverdesignworks.net", "/trebuchet/api/plan"), (b"rocket.quiverdesignworks.net", "/")]:
        asyncio.run(router({"type": "http", "path": path, "headers": [(b"host", host)]}, None, None))
    assert seen == ["/trebuchet/", "/trebuchet/api/plan", "/trebuchet/api/plan", "/"]


def test_missing_checkout_means_no_mount(monkeypatch, tmp_path):
    monkeypatch.setenv("TREBUCHET_DIR", str(tmp_path))
    assert trebuchet_mount.load_app() is None


needs_trebuchet = pytest.mark.skipif(rocket.TREBUCHET is None, reason="trebuchet/ not checked out")


@needs_trebuchet
def test_trebuchet_served_under_prefix_and_host():
    c = TestClient(rocket.app)
    assert c.get("/trebuchet", follow_redirects=False).headers["location"] == "/trebuchet/"
    assert "Trebuchet Builder" in c.get("/trebuchet/").text
    r = c.post("/trebuchet/api/plan", json={})
    assert r.status_code == 200 and r.json()["throw"]["ok"]
    page = c.get("/", headers={"host": "trebuchet.quiverdesignworks.net"}).text
    assert "Trebuchet Builder" in page
    assert "Rocket Builder" in c.get("/").text and "Trebuchet Builder</h1>" not in c.get("/").text
    assert c.get("/healthz").json()["ok"]
