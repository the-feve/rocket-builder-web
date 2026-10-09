"""Server tests: a default build, its preview and ZIP, stability, saved designs, friendly errors."""

import io

import pytest
import os
import tempfile
import zipfile

os.environ["ROCKETGEN_DB"] = os.path.join(tempfile.mkdtemp(), "designs.sqlite3")

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_options():
    o = client.get("/api/options").json()
    assert "M18" in o["motors"] and o["defaults"]["motor"] == "M18"


def test_build_preview_zip():
    r = client.post("/api/build", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    names = [p["name"] for p in body["parts"]]
    assert names[0] == "Aft" and "Nose" in names and "Motor_Cap" in names
    assert body["total_mass_g"] > 0 and body["summary"]
    glb = client.get(f"/api/builds/{body['id']}/preview.glb")
    assert glb.status_code == 200 and glb.content[:4] == b"glTF"
    z = zipfile.ZipFile(io.BytesIO(client.get(f"/api/builds/{body['id']}/rocket.zip").content))
    assert set(z.namelist()) == {f"{n}.stl" for n in names} | {"build_notes.txt", "design.json"}
    assert "Stable" in z.read("build_notes.txt").decode()
    st = body["stability"]
    assert st["ok"] and st["cg_mm"] < st["cp_mm"] < st["length_mm"]
    # The same design is served from the cache.
    assert client.post("/api/build", json={}).json()["id"] == body["id"]


def test_unbuildable_design_is_a_422_with_a_message():
    # Too short for the aft segment plus the anchor section under the nose
    # (M29's anchor section is the longest; the M18 one got shorter with the
    # 2026-10-09 strap and nose insert).
    r = client.post("/api/build", json={"motor": "M29", "body_length": 60})
    assert r.status_code == 422 and "Body length" in r.json()["detail"]


def test_out_of_bounds_input_is_rejected():
    assert client.post("/api/build", json={"fin_count": 7}).status_code == 422
    assert client.post("/api/build", json={"motor": "M99"}).status_code == 422


SMALL_FINS = {"custom_fin_size": True, "fin_root_chord": 25, "fin_span": 10, "fin_tip_chord": 12, "fin_sweep": 10}


def test_unstable_rocket_previews_but_no_zip():
    body = client.post("/api/build", json=SMALL_FINS).json()
    assert not body["stability"]["ok"]
    assert client.get(f"/api/builds/{body['id']}/preview.glb").status_code == 200
    r = client.get(f"/api/builds/{body['id']}/rocket.zip")
    assert r.status_code == 409 and "Unstable" in r.json()["detail"]
    # The flight inputs don't rebuild the geometry; a lighter motor is more stable.
    light = client.post("/api/build", json={**SMALL_FINS, "flight_motor": "A8"}).json()
    assert light["stability"]["margin_cal"] > body["stability"]["margin_cal"]
    assert client.post("/api/build", json={"flight_motor": "D12"}).status_code == 422  # not an 18 mm motor


def test_motor_picker_and_auto_sized_fins():
    body = client.post("/api/build", json={"motor": "M24", "target_altitude_m": 200}).json()
    assert body["stability"]["ok"] and body["dimensions"]["Fin span/sweep scale"] > 1
    f = body["flights"]
    assert {r["code"] for r in f["rows"]} == {"C11", "D12"} and f["recommended"] in ("C11", "D12")
    assert all(r["margin_cal"] >= 1 for r in f["rows"])


def test_saved_design_share_link_and_edit_key():
    saved = client.post("/api/designs", json={"name": "Orbis", "params": {"fin_count": 4}}).json()
    did, key = saved["id"], saved["edit_key"]
    got = client.get(f"/api/designs/{did}").json()
    assert got["name"] == "Orbis" and got["params"]["fin_count"] == 4 and "edit_key" not in got
    assert client.get(f"/d/{did}").status_code == 200
    # Only the saving browser (the edit key) can change it.
    assert client.patch(f"/api/designs/{did}", json={"name": "x"}).status_code == 403
    assert client.patch(f"/api/designs/{did}", json={"name": "Orbis 2"}, headers={"X-Edit-Key": key}).json()["name"] == "Orbis 2"
    upd = client.put(f"/api/designs/{did}", json={"name": "Orbis 2", "params": {"fin_count": 5}}, headers={"X-Edit-Key": key})
    assert upd.json()["params"]["fin_count"] == 5
    assert client.delete(f"/api/designs/{did}", headers={"X-Edit-Key": key}).status_code == 200
    assert client.get(f"/api/designs/{did}").status_code == 404
    assert client.post("/api/designs", json={"name": "bad", "params": {"fin_count": 9}}).status_code == 422


def test_healthz_and_rate_limit(monkeypatch):
    import app as server
    assert client.get("/healthz").json()["ok"]
    assert client.get("/static/vendor/three/build/three.module.js").status_code == 200
    monkeypatch.setattr(server, "SAVES_PER_HOUR", 2)
    server._hits.clear()
    body = {"name": "x", "params": {}}
    assert [client.post("/api/designs", json=body).status_code for _ in range(3)] == [200, 200, 429]
    server._hits.clear()


def test_beginner_overall_height():
    o = client.get("/api/options").json()["beginner"]
    assert o["fin_shapes"] == ["swept", "delta", "trapezoid"] and 150 < o["overall_length"] < 600
    for target, fins in [(400.0, "swept"), (o["overall_length"], "trapezoid")]:
        body = client.post("/api/build", json={"overall_length": target, "fin_shape": fins}).json()
        assert abs(body["stability"]["length_mm"] - target) <= 0.5, body["stability"]
        assert body["body_length_mm"] < target
    r = client.post("/api/build", json={"motor": "M29", "overall_length": 90})
    assert r.status_code == 422 and "too short" in r.json()["detail"]


def test_body_od_offset():
    o = client.get("/api/options").json()
    stock = o["stock_od"]["M18"]
    assert o["defaults"]["body_od_offset"] == 0
    b = client.post("/api/build", json={"body_od_offset": 5}).json()
    assert b["dimensions"]["Body OD"] == pytest.approx(stock + 10, abs=1e-6)
    assert b["dimensions"]["Inner motor mount"] == "yes"
    # Designs saved before the offset existed carry body_od_override.
    old = client.post("/api/build", json={"body_od_override": stock + 10}).json()
    assert old["dimensions"]["Body OD"] == pytest.approx(stock + 10, abs=1e-6)
    # A huge offset is refused with a message, not a server error.
    r = client.post("/api/build", json={"motor": "M29", "body_od_offset": 80})
    assert r.status_code == 422 and r.json()["detail"]
    assert client.post("/api/build", json={"body_od_offset": 81}).status_code == 422  # over the field's limit
    ra = client.get("/api/recovery_allowance", params={"motor": "M18", "body_od_offset": 5}).json()
    assert ra["recovery_mass_g"] > client.get("/api/recovery_allowance", params={"motor": "M18"}).json()["recovery_mass_g"]


def test_wall_thickness():
    o = client.get("/api/options").json()
    assert o["defaults"]["wall"] == 1.5
    thin = client.post("/api/build", json={"wall": 1.2}).json()["dimensions"]
    thick = client.post("/api/build", json={"wall": 2.0}).json()["dimensions"]
    # Same motor bay, thicker wall: the stock tube grows by twice the change.
    assert thick["Body OD"] - thin["Body OD"] == pytest.approx(1.6, abs=1e-6)
    assert thick["Body ID"] == pytest.approx(thick["Body OD"] - 4.0, abs=1e-6)
    assert thin["Body OD"] == pytest.approx(o["bay_id"]["M18"] + 2.4, abs=1e-3)
    # The offset is measured from the stock tube for that wall.
    off = client.post("/api/build", json={"wall": 2.0, "body_od_offset": 3}).json()["dimensions"]
    assert off["Body OD"] == pytest.approx(thick["Body OD"] + 6, abs=1e-6)
    assert client.post("/api/build", json={"wall": 0.5}).status_code == 422
