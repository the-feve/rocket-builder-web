"""Server tests: a default build, its preview and ZIP, stability, saved designs, friendly errors."""

import io

import pytest
import os
import tempfile
import zipfile

os.environ["ROCKETGEN_DB"] = os.path.join(tempfile.mkdtemp(), "designs.sqlite3")
os.environ["ROCKETGEN_ORDERS_DIR"] = os.path.join(tempfile.mkdtemp(), "orders")

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


def test_beginner_heights_snap_to_ones_that_build():
    """/api/heights: the lowest M29 height builds at exactly that height, with
    the fins auto-sized to the limit (they trail further below the tail, so
    the body is shorter for the same height). Below the old plain-fin
    minimum the build fails. A printer too short for any M24 rocket reports
    the smallest that works."""
    h = client.get("/api/heights", params={"motor": "M29", "print_max_height": 200, "fin_shape": "trapezoid"}).json()
    lo = h["ranges"][0][0]
    assert len(h["ranges"]) == 1 and 280 < lo < 340 and h["ranges"][0][1] > 1500 and h["printer_min"] < 200
    ok = client.post("/api/build", json={"motor": "M29", "overall_length": lo, "fin_shape": "trapezoid"})
    assert ok.status_code == 200, ok.text
    assert abs(ok.json()["stability"]["length_mm"] - lo) <= 0.5
    bad = client.post("/api/build", json={"motor": "M29", "overall_length": 270, "fin_shape": "trapezoid"})
    assert bad.status_code == 422
    h = client.get("/api/heights", params={"motor": "M24", "print_max_height": 90}).json()
    assert h["ranges"] == [] and 90 < h["printer_min"] < 150
    assert client.get("/api/heights", params={"motor": "M99"}).status_code == 422
    # The default Beginner rocket is a height that works.
    o = client.get("/api/options").json()
    h = client.get("/api/heights").json()
    assert any(a <= o["beginner"]["overall_length"] <= b for a, b in h["ranges"])


def test_score_advice_outside_the_sweet_spot():
    """A tall Beginner M18 is over-stable: the build says what to change,
    with step numbers and predicted scores. The default rocket (1-2 cal)
    gets none."""
    st = client.post("/api/build", json={"overall_length": 600, "fin_shape": "trapezoid"}).json()["stability"]
    a = st["advice"]
    assert st["margin_cal"] > 3 and a["zone"] == "over"
    assert any("shorter" in i["text"] and "step 4" in i["text"] and i["est_cal"] for i in a["items"])
    o = client.get("/api/options").json()["beginner"]
    st = client.post("/api/build", json={"overall_length": o["overall_length"], "fin_shape": "trapezoid"}).json()["stability"]
    assert 1 <= st["margin_cal"] <= 2 and st["advice"] is None


def test_parachute_suggestion():
    """Every build suggests a standard chute size that lands it at a safe
    speed, links to it when the supplies list has that size, and says so in
    the build notes. A heavier rocket needs a bigger chute."""
    from rocketgen.flight import CHUTE_SIZES_IN, SAFE_DESCENT_MS, parachute
    r = client.post("/api/build", json={}).json()
    c = r["parachute"]
    assert c["size_in"] in CHUTE_SIZES_IN and c["size_in"] >= c["min_diameter_in"] and c["descent_ms"] <= SAFE_DESCENT_MS
    assert c["links"] and f'{c["size_in"]}"' in c["links"][0]["name"]
    z = zipfile.ZipFile(io.BytesIO(client.get(f"/api/builds/{r['id']}/rocket.zip").content))
    assert f"Parachute: {c['size_in']} in" in z.read("build_notes.txt").decode()
    assert parachute(400)["size_in"] > parachute(60)["size_in"] and parachute(5000)["size_in"] is None


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


def test_page_is_not_cached_stale():
    for path in ("/", "/d/anything"):
        r = client.get(path)
        assert r.status_code == 200 and r.headers["cache-control"] == "no-cache"


def test_accounts_signup_login_and_owned_designs():
    from fastapi.testclient import TestClient as TC
    a, b = TC(app), TC(app)  # two browsers
    assert a.post("/api/auth/signup", json={"email": "kid@example.com", "password": "rocket123"}).status_code == 400  # no age box
    assert a.post("/api/auth/signup", json={"email": "kid@example.com", "password": "short", "age_ok": True}).status_code == 400
    r = a.post("/api/auth/signup", json={"email": "Kid@Example.com", "password": "rocket123", "age_ok": True})
    assert r.status_code == 200 and r.json()["user"]["email"] == "kid@example.com"
    assert a.get("/api/auth/me").json()["user"]["email"] == "kid@example.com"
    assert a.post("/api/auth/signup", json={"email": "kid@example.com", "password": "rocket123", "age_ok": True}).status_code == 400

    # A design saved signed out (edit key) is claimed into the account; one saved signed in is owned.
    anon = TC(app).post("/api/designs", json={"name": "Old", "params": {}}).json()
    claim = a.post("/api/my/claim", json={"items": [{"id": anon["id"], "key": anon["edit_key"]}, {"id": anon["id"], "key": "wrong"}]})
    assert claim.json() == {"claimed": 1}
    mine = a.post("/api/designs", json={"name": "New", "params": {}}).json()
    names = [d["name"] for d in a.get("/api/my/designs").json()["designs"]]
    assert set(names) == {"Old", "New"}

    # Another browser: can't edit until it signs in to the same account, then can without the edit key.
    assert b.put(f"/api/designs/{mine['id']}", json={"name": "X", "params": {}}).status_code == 403
    assert b.post("/api/auth/login", json={"email": "kid@example.com", "password": "nope"}).status_code == 401
    assert b.post("/api/auth/login", json={"email": "KID@example.com", "password": "rocket123"}).status_code == 200
    assert b.put(f"/api/designs/{mine['id']}", json={"name": "Renamed", "params": {}}).json()["name"] == "Renamed"

    b.post("/api/auth/logout")
    assert b.get("/api/auth/me").json()["user"] is None
    assert b.get("/api/my/designs").status_code == 401


def test_print_order_with_coupon_and_admin(monkeypatch):
    import app as appmod
    from fastapi.testclient import TestClient as TC
    monkeypatch.setenv("ROCKETGEN_COUPON_CODES", "LAUNCHDAY")
    monkeypatch.setattr(appmod, "ADMIN_EMAILS", {"owner@example.com"})
    monkeypatch.setattr(appmod, "SYNC_TOKEN", "sync-secret")
    ship = {"name": "Pat", "line1": "1 Main St", "city": "Ellensburg", "state": "WA", "zip": "98926"}
    order = {"design_name": "Zoomer", "params": {}, "quantity": 2, "color": "Red", "shipping": ship, "coupon": "launchday"}

    kid = TC(app)
    assert kid.post("/api/orders", json=order).status_code == 401  # must sign in
    kid.post("/api/auth/signup", json={"email": "parent@example.com", "password": "rocket123", "age_ok": True})
    assert kid.post("/api/orders", json={**order, "coupon": ""}).status_code == 402
    assert kid.post("/api/orders", json={**order, "coupon": "WRONG"}).status_code == 402
    r = kid.post("/api/orders", json=order)
    assert r.status_code == 200, r.text
    oid = r.json()["id"]
    assert oid.startswith("RB-") and r.json()["price"] == 0
    assert [o["id"] for o in kid.get("/api/my/orders").json()["orders"]] == [oid]

    # The order folder has the STLs and the batch sheet.
    import orders
    o = orders.get(oid)
    files = {f.name for f in orders.folder(o).iterdir()}
    assert {"ORDER.txt", "order.json", "design.json", "build_notes.txt", "Aft.stl", "Nose.stl"} <= files
    assert "Ellensburg, WA 98926" in (orders.folder(o) / "ORDER.txt").read_text()
    # Named with the motor size and the customer's code (same code on every order from one account).
    assert o["name"] == f"{oid}_M18_{o['customer']}" and orders.folder(o).name == o["name"]
    assert len(o["customer"]) == 7 and o["customer"].startswith("C") and o["email"] not in o["name"]

    # Only the owner (signed in) or the PC sync (token) sees all orders.
    assert kid.get("/api/admin/orders").status_code == 403
    sync = TC(app)
    assert sync.get("/api/admin/orders", headers={"Authorization": "Bearer nope"}).status_code == 403
    listing = sync.get("/api/admin/orders", headers={"Authorization": "Bearer sync-secret"}).json()
    assert oid in [x["id"] for x in listing["orders"]]
    z = sync.get(f"/api/admin/orders/{oid}/files.zip", headers={"Authorization": "Bearer sync-secret"})
    assert z.status_code == 200 and zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert f'filename="{o["name"]}.zip"' in z.headers["content-disposition"]
    owner = TC(app)
    owner.post("/api/auth/signup", json={"email": "owner@example.com", "password": "rocket123", "age_ok": True})
    assert owner.post(f"/api/admin/orders/{oid}/status", json={"status": "shipped"}).json()["status"] == "shipped"
    assert owner.post(f"/api/admin/orders/{oid}/status", json={"status": "lost"}).status_code == 400
    assert kid.get("/api/my/orders").json()["orders"][0]["status"] == "shipped"
    assert owner.get("/admin").status_code == 200


def test_account_prefs_skip_tutorial():
    from fastapi.testclient import TestClient as TC
    a = TC(app)
    a.post("/api/auth/signup", json={"email": "prefs@example.com", "password": "rocket123", "age_ok": True})
    assert a.get("/api/auth/me").json()["user"]["prefs"] == {}
    assert a.post("/api/my/prefs", json={"skip_tutorial": True}).json()["prefs"] == {"skip_tutorial": True}
    b = TC(app)
    assert b.post("/api/my/prefs", json={"skip_tutorial": True}).status_code == 401
    r = b.post("/api/auth/login", json={"email": "prefs@example.com", "password": "rocket123"})
    assert r.json()["user"]["prefs"]["skip_tutorial"] is True


def test_order_supplies_page():
    import re
    import supplies
    r = client.get("/ordersupplies")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-cache"
    g = supplies.gear()
    n = sum(len(c["items"]) for c in g["categories"])
    assert r.text.count(f"tag={g['storeId']}") == n + len(g["starterKit"]["items"])
    for k in g["starterKit"]["items"]:  # kit entries must be items on the list
        assert any(it["asin"] == k["asin"] for c in g["categories"] for it in c["items"]), k["asin"]
    links = client.get("/api/options").json()["motor_links"]
    assert links["B4-4"][0]["url"].endswith(f"tag={g['storeId']}") and "C6-5" in links
    assert supplies.DISCLOSURE in r.text
    assert "$" not in re.sub(r"<style>.*?</style>", "", r.text, flags=re.S)  # no prices
    seen = set()
    for c in g["categories"]:
        for it in c["items"]:
            assert supplies.ASIN.match(it["asin"]) and it["asin"] not in seen and it["name"] and it["note"]
            seen.add(it["asin"])
    assert client.get("/api/options").json()["supplies_url"] == "/ordersupplies"
