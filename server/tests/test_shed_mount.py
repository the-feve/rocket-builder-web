"""ShedCAD hosted inside this app (server/shed_mount.py).

The ShedCAD checkout (shed/, or SHED_DIR) only exists on deploys; without it the
mount tests are skipped. To run them locally: SHED_DIR=/path/to/Shed_builder pytest.
"""

import asyncio
import os
import tempfile

import pytest

os.environ.setdefault("ROCKETGEN_DB", os.path.join(tempfile.mkdtemp(), "designs.sqlite3"))
os.environ.setdefault("ROCKETGEN_ORDERS_DIR", os.path.join(tempfile.mkdtemp(), "orders"))

from fastapi.testclient import TestClient

import app as rocket
import shed_mount
import trebuchet_mount


def test_host_router_sends_shed_hosts_to_the_mount():
    seen = []

    async def inner(scope, receive, send):
        seen.append(scope["path"])

    router = trebuchet_mount.HostRouter(inner, {"trebuchet.": "/trebuchet", "shed.": shed_mount.PREFIX})
    for host, path in [(b"shed.quiverdesignworks.net", "/"), (b"shed.quiverdesignworks.net", "/api/schema"),
                       (b"shed.quiverdesignworks.net", "/shed/api/schema"), (b"rocket.quiverdesignworks.net", "/")]:
        asyncio.run(router({"type": "http", "path": path, "headers": [(b"host", host)]}, None, None))
    assert seen == ["/shed/", "/shed/api/schema", "/shed/api/schema", "/"]


def test_missing_checkout_means_no_mount(monkeypatch, tmp_path):
    monkeypatch.setenv("SHED_DIR", str(tmp_path))
    assert shed_mount.load_app() is None


needs_shed = pytest.mark.skipif(rocket.SHED is None, reason="shed/ not checked out")


@needs_shed
def test_shed_served_under_prefix_and_host():
    c = TestClient(rocket.app)
    assert c.get("/shed", follow_redirects=False).headers["location"] == "/shed/"
    page = c.get("/shed/")
    assert page.status_code == 200 and "ShedCAD" in page.text
    schema = c.get("/shed/api/schema").json()
    assert schema["hosted"] is True
    r = c.post("/shed/api/generate", json={"params": schema["defaults"]})
    assert r.status_code == 200 and r.json()["summary"]["total_cost"] > 0
    assert "ShedCAD" in c.get("/", headers={"host": "shed.quiverdesignworks.net"}).text
    assert c.get("/shed/api/schema", headers={"host": "shed.quiverdesignworks.net"}).json()["hosted"] is True
    assert "Rocket Builder" in c.get("/").text


@needs_shed
def test_shed_keeps_nothing_on_the_server():
    c = TestClient(rocket.app)
    # the local-app routes that write files are off when hosted
    assert c.post("/shed/api/designs/test", json={"params": {}}).status_code == 404
    assert c.post("/shed/api/materials", json={"boards": []}).status_code == 404
    assert c.post("/shed/api/settings", json={}).status_code == 404
    assert c.get("/shed/api/designs").status_code == 404
    # examples with a street address (the owner's own site plans) aren't offered
    for name in c.get("/shed/api/schema").json()["examples"]:
        site = c.get("/shed/api/examples/" + name).json()["params"]["site"]
        assert not site.get("location")
