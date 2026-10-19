"""Server tests: a default build, its preview and ZIP, stability, saved designs, friendly errors."""

import io
import json

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
    assert set(z.namelist()) == {f"{n}.stl" for n in names} | {"build_notes.txt", "design.json", "LICENSE.txt"}
    # Personal-use licence: in the ZIP, at the top of the notes, in design.json and in every STL's header.
    assert "may NOT" in z.read("LICENSE.txt").decode() and "MakerWorld" in z.read("LICENSE.txt").decode()
    assert "Personal use only" in z.read("build_notes.txt").decode()[:400] and "license" in json.loads(z.read("design.json"))
    assert all(z.read(f"{n}.stl")[:80].startswith(b"(c)") and b"Personal use only" in z.read(f"{n}.stl")[:80] for n in names)
    assert "MakerWorld" in client.get("/terms").text
    assert "Stable" in z.read("build_notes.txt").decode()
    # STEP option (Advanced): one STEP per part, same notes and licence.
    r = client.get(f"/api/builds/{body['id']}/rocket_step.zip")
    assert r.status_code == 200 and 'rocket_' in r.headers["content-disposition"] and '_step.zip' in r.headers["content-disposition"]
    zs = zipfile.ZipFile(io.BytesIO(r.content))
    assert set(zs.namelist()) == {f"{n}.step" for n in names} | {"build_notes.txt", "design.json", "LICENSE.txt"}
    for n in names:
        step = zs.read(f"{n}.step")
        assert step.startswith(b"ISO-10303-21;") and b"Personal use only" in step[:600] and (b"MANIFOLD_SOLID_BREP" in step or b"BREP_WITH_VOIDS" in step), n  # the hollow nose has voids
    assert "STEPs are in print orientation" in zs.read("build_notes.txt").decode()
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


def test_launch_field_size():
    """The field is the NAR minimum for the recommended motor's class, or
    longer when the rocket drifts further than that under its parachute in a
    10 mph breeze; it's in the build notes too."""
    from rocketgen.flight import FIELD_M, WIND_MS
    r = client.post("/api/build", json={}).json()
    f, best = r["field"], next(x for x in r["flights"]["rows"] if x["code"] == r["flights"]["recommended"])
    assert f["nar_min_m"] == FIELD_M[best["cls"]] and f["motor"] == best["motor"]
    assert f["drift_m"] == round(best["apogee_m"] / r["parachute"]["descent_ms"] * WIND_MS)
    assert f["recommended_m"] == max(f["nar_min_m"], -(-f["drift_m"] // 10) * 10)
    z = zipfile.ZipFile(io.BytesIO(client.get(f"/api/builds/{r['id']}/rocket.zip").content))
    assert f"Launch field: at least {f['recommended_m']} m" in z.read("build_notes.txt").decode()


def test_launch_simulator():
    """The launch page flies the recommended motor in the wind the user sets:
    it goes up, opens the chute, lands downwind (further in more wind), and
    the field covers the landing spot and is never under the NAR minimum."""
    r = client.post("/api/build", json={}).json()
    page = client.get("/launch")
    assert page.status_code == 200 and "Launch simulator" in page.text
    calm = client.get(f"/api/builds/{r['id']}/launch?wind_mph=0").json()
    windy = client.get(f"/api/builds/{r['id']}/launch?wind_mph=15").json()
    assert calm["code"] == r["flights"]["recommended"] and calm["safe"]
    ev = calm["events"]
    assert ev["rod"]["t"] < ev["burnout"]["t"] < ev["apogee"]["t"] < ev["landing"]["t"] and ev["eject"]["t"] < ev["landing"]["t"]
    assert abs(calm["landing_m"]) < 1 and calm["field"]["length_m"] == calm["field"]["nar_min_m"]
    sh = calm["shape"]  # side-view proportions for the page's drawing
    assert sh["length_mm"] > sh["nose_mm"] > sh["od_mm"] > 0 and sh["fin"]["root"] > 0 and sh["fin_count"] == 3
    assert windy["landing_m"] > 20 and windy["apogee_m"] < calm["apogee_m"]  # weathercocks, then drifts
    f = windy["field"]
    assert f["length_m"] >= f["pad_from_upwind_m"] + windy["landing_m"] and f["width_m"] == f["nar_min_m"]
    assert ev["landing"]["speed_ms"] <= r["parachute"]["descent_ms"] + 0.3
    other = next(m for m in calm["motors"] if m["code"] != calm["code"])
    alt = client.get(f"/api/builds/{r['id']}/launch?motor={other['code']}&delay={other['delays'][0]}").json()
    assert alt["code"] == other["code"] and alt["delay_s"] == other["delays"][0]
    assert client.get(f"/api/builds/{r['id']}/launch?wind_mph=50").status_code == 422
    assert client.get(f"/api/builds/{r['id']}/launch?delay=99").status_code == 422
    assert client.get("/api/builds/nope/launch").status_code == 404
    assert "The NAR Safety Code" in client.get(f"/api/builds/{r['id']}/launch?wind_mph=25").json()["warnings"][-1]


def test_unsafe_rocket_still_launches_and_says_why():
    """An unstable design (or a motor that fails) still flies in the simulator,
    marked unsafe, with plain-words reasons and its attitude along the path."""
    body = client.post("/api/build", json=SMALL_FINS).json()
    assert not body["stability"]["ok"]
    out = client.get(f"/api/builds/{body['id']}/launch?wind_mph=10")
    assert out.status_code == 200
    d = out.json()
    assert not d["safe"] and d["margin_cal"] < 1
    assert {x["kind"] for x in d["dangers"]} & {"tumble", "wobble"}
    assert all(len(p) == 5 for p in d["path"])  # t, x, h, phase, attitude
    good = client.post("/api/build", json={}).json()
    calm = client.get(f"/api/builds/{good['id']}/launch?wind_mph=0").json()
    assert calm["safe"] and not [x for x in calm["dangers"] if x["level"] == "danger"]


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
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)  # paid orders off: no coupon is a 402
    monkeypatch.setattr(appmod, "ADMIN_EMAILS", {"owner@example.com"})
    monkeypatch.setattr(appmod, "SYNC_TOKEN", "sync-secret")
    monkeypatch.setattr(appmod, "ORDERING_OPEN", True)
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


def test_ordering_closed_to_public_until_opened(monkeypatch):
    """ROCKETGEN_ORDERING unset: customers get "coming soon", admins can still
    place (and so test) orders; opening it lets everyone order."""
    import app as appmod
    from fastapi.testclient import TestClient as TC
    monkeypatch.setenv("ROCKETGEN_COUPON_CODES", "LAUNCHDAY")
    monkeypatch.setattr(appmod, "ADMIN_EMAILS", {"boss@example.com"})
    monkeypatch.setattr(appmod, "ORDERING_OPEN", False)
    ship = {"name": "Pat", "line1": "1 Main St", "city": "Ellensburg", "state": "WA", "zip": "98926"}
    order = {"design_name": "Zoomer", "params": {}, "quantity": 1, "color": "Red", "shipping": ship, "coupon": "LAUNCHDAY"}
    assert TC(app).get("/api/options").json()["ordering_open"] is False

    customer = TC(app)
    r = customer.post("/api/auth/signup", json={"email": "fan@example.com", "password": "rocket123", "age_ok": True})
    assert r.json()["user"]["can_order"] is False
    r = customer.post("/api/orders", json=order)
    assert r.status_code == 403 and "coming soon" in r.json()["detail"]

    boss = TC(app)
    assert boss.post("/api/auth/signup", json={"email": "boss@example.com", "password": "rocket123", "age_ok": True}).json()["user"]["can_order"] is True
    assert boss.get("/api/auth/me").json()["user"]["can_order"] is True
    assert boss.post("/api/orders", json=order).status_code == 200

    monkeypatch.setattr(appmod, "ORDERING_OPEN", True)
    assert customer.get("/api/auth/me").json()["user"]["can_order"] is True
    assert customer.post("/api/orders", json=order).status_code == 200


def test_paid_order_through_stripe_checkout(monkeypatch):
    """Without a coupon the order waits for payment and the reply carries a
    Stripe Checkout URL (priced from shop.json, tagged rocket-builder, with a
    shipping estimate). A signed checkout.session.completed marks it paid
    with Stripe's address; other stores' events and bad signatures don't."""
    import json as _json
    import app as appmod
    import orders
    import shop
    from fastapi.testclient import TestClient as TC
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(appmod, "SYNC_TOKEN", "sync-secret")
    monkeypatch.setattr(appmod, "ORDERING_OPEN", True)
    sent = {}

    def fake_session(order, q, origin):
        sent.update(order=order, q=q, params=shop.session_params(order, q, origin))
        return {"id": "cs_test_123", "url": "https://checkout.stripe.com/c/pay/cs_test_123"}
    monkeypatch.setattr(shop, "create_session", fake_session)

    kid = TC(app)
    kid.post("/api/auth/signup", json={"email": "payer@example.com", "password": "rocket123", "age_ok": True})
    built = kid.post("/api/build", json={}).json()
    q = kid.get("/api/orders/quote", params={"build_id": built["id"], "quantity": 2}).json()
    assert q["each_cents"] == shop.price_each_cents(built["total_mass_g"]) and q["subtotal_cents"] == 2 * q["each_cents"]
    assert q["shipping_cents"] > 0 and q["package"]["weight_oz"] > 2 * built["total_mass_g"] / 28.35 and q["paid_enabled"]
    r = kid.post("/api/orders", json={"design_name": "Zoomer", "params": {}, "quantity": 2, "color": "Blue"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["checkout_url"].startswith("https://checkout.stripe.com/") and d["status"] == "awaiting_payment"
    p = sent["params"]
    assert p["metadata"]["store"] == "rocket-builder" == p["payment_intent_data"]["metadata"]["store"]
    assert p["line_items"][0]["price_data"]["unit_amount"] == q["each_cents"] and p["line_items"][0]["quantity"] == 2
    assert p["shipping_options"][0]["shipping_rate_data"]["fixed_amount"]["amount"] == q["shipping_cents"]
    assert p["metadata"]["order_id"] == d["id"] and p["metadata"]["weight_oz"] and p["metadata"]["box_in"]
    assert ("line_items[0][price_data][product_data][metadata][store]", "rocket-builder") in shop._form(p)
    # Waiting orders stay off the admin list and the PC sync.
    sync = {"Authorization": "Bearer sync-secret"}
    assert d["id"] not in [o["id"] for o in kid.get("/api/admin/orders", headers=sync).json()["orders"]]

    def event(kind, store="rocket-builder", status="paid"):
        return _json.dumps({"type": kind, "data": {"object": {
            "id": "cs_test_123", "payment_status": status, "payment_intent": "pi_1", "amount_total": 4321,
            "total_details": {"amount_tax": 321, "amount_shipping": 850},
            "customer_details": {"email": "payer@example.com", "phone": "+15095550100", "name": "Pat"},
            "collected_information": {"shipping_details": {"name": "Pat Doe", "address": {
                "line1": "1 Main St", "city": "Ellensburg", "state": "WA", "postal_code": "98926", "country": "US"}}},
            "metadata": {"store": store, "order_id": d["id"]}}}}).encode()
    hook = TC(app)
    bad = event("checkout.session.completed")
    assert hook.post("/api/stripe-webhook", content=bad, headers={"stripe-signature": "t=1,v1=nope"}).status_code == 400
    other = event("checkout.session.completed", store="quiver-design-works")
    assert hook.post("/api/stripe-webhook", content=other, headers={"stripe-signature": shop.sign_for_tests(other, "whsec_test")}).json() == {"ignored": True}
    assert orders.get(d["id"])["status"] == "awaiting_payment"
    ok = event("checkout.session.completed")
    assert hook.post("/api/stripe-webhook", content=ok, headers={"stripe-signature": shop.sign_for_tests(ok, "whsec_test")}).status_code == 200
    o = orders.get(d["id"])
    assert o["status"] == "new" and o["shipping"]["zip"] == "98926" and o["paid"]["total_cents"] == 4321
    assert "Paid $43.21" in (orders.folder(o) / "ORDER.txt").read_text()
    assert d["id"] in [x["id"] for x in kid.get("/api/admin/orders", headers=sync).json()["orders"]]
    # A repeat delivery changes nothing; an expired checkout only affects unpaid orders.
    assert orders.mark_paid(d["id"], {}) is None and orders.mark_expired(d["id"]) is None


def test_shop_pricing_and_webhook_signature():
    import shop
    cfg = {**shop.CONFIG, "price": {"baseCents": 1200, "perGramCents": 15, "roundToCents": 50}}
    assert shop.price_each_cents(45.2, cfg) == 1900  # 1200 + 678 = 1878 -> 1900
    small = shop.package([{"height_mm": 195, "width_mm": 60, "mass_g": 29}, {"height_mm": 70, "width_mm": 21, "mass_g": 6}], 1)
    big = shop.package([{"height_mm": 195, "width_mm": 60, "mass_g": 29}, {"height_mm": 70, "width_mm": 21, "mass_g": 6}], 5)
    assert small["box"]["length"] >= 195 / 25.4 and shop.shipping_cents(big) >= shop.shipping_cents(small)
    payload = b'{"type":"x"}'
    assert shop.verify_webhook(payload, shop.sign_for_tests(payload, "s"), "s") == {"type": "x"}
    with pytest.raises(ValueError):
        shop.verify_webhook(payload, shop.sign_for_tests(payload, "s", t=1), "s")  # too old
    with pytest.raises(ValueError):
        shop.verify_webhook(payload, shop.sign_for_tests(payload, "other"), "s")


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
    rocket = r.text.split('id="trebuchet"')[0]  # the Trebuchet section follows when it's mounted
    assert 'id="rocket"' in rocket and rocket.count(f"tag={g['storeId']}") == n + len(g["starterKit"]["items"])
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


def test_supplies_page_has_a_trebuchet_section(monkeypatch):
    """With Trebuchet Builder mounted, /ordersupplies gets a Trebuchet section
    built from its own list (ids prefixed t-), with jump links to both."""
    import sys
    import types
    import supplies
    fake = types.SimpleNamespace(
        gear=lambda: {"storeId": "quiverdesig09-20", "categories": [
            {"id": "filament", "title": "Filament", "intro": "PLA.", "items": [
                {"name": "PLA 1 kg", "note": "Any colour.", "search": "pla filament 1kg", "pick": True}]}]},
        amazon_url=lambda it, store: f"https://www.amazon.com/s?k=x&tag={store}", _icon=lambda cid: "<svg></svg>")
    monkeypatch.setitem(sys.modules, "treb_supplies", fake)
    html = client.get("/ordersupplies").text
    assert 'href="#rocket"' in html and 'href="#trebuchet"' in html
    treb = html.split('id="trebuchet"')[1]
    assert 'id="t-filament"' in treb and "PLA 1 kg" in treb and "Find on Amazon" in treb
    monkeypatch.delitem(sys.modules, "treb_supplies")
    monkeypatch.setattr(supplies, "_treb", lambda: None)
    assert 'id="trebuchet"' not in client.get("/ordersupplies").text  # rocket only, when it isn't mounted


def test_sources_page_and_links():
    """Sources and References is served and linked from the guide and the
    report's build notes and the launch simulator."""
    r = client.get("/sources")
    assert r.status_code == 200 and "Sources and references" in r.text
    for ref in ("Barrowman", "thrustcurve.org", "Model Rocket Safety Code", "openrocket.info", "Our choice"):
        assert ref in r.text
    page = client.get("/").text
    assert page.count('href="/sources"') >= 2 and "/sources#launch" in client.get("/launch").text


def test_launch_view_in_designer_and_printer_picker():
    """The designer has the Watch it launch button and the in-view launch panel
    (launch.html?embed=1), and a printer picker next to the max height."""
    page = client.get("/").text
    assert 'id="launchbtn"' in page and 'id="launchpane"' in page and "&embed=1" in page
    assert 'id="printer_pick"' in page and 'value="256"' in page
    assert "classList.add('embed')" in client.get("/launch").text


def test_critical_fit_fields():
    o = client.get("/api/options").json()
    assert o["fit_defaults"] == {"joint_clearance": 0.18, "nose_clearance": 0.15, "joint_clearance_short": 0.16,
                                 "nose_clearance_short": 0.14, "short_nose_shoulder": 8.0,
                                 "thread_clearance": 0.25, "thread_turns": 3}
    for k in ("joint_clearance", "nose_clearance", "shoulder_len", "nose_shoulder_len", "thread_clearance", "thread_pitch", "thread_turns"):
        assert o["defaults"][k] is None  # blank = Rocket Builder's computed value
    r = client.post("/api/build", json={"joint_clearance": 0.9})
    assert r.status_code == 422
    r = client.post("/api/build", json={"thread_turns": 1})
    assert r.status_code == 422


def test_learn_pages():
    """The rocketry lessons at /learn (static pages from docs/curriculum/tools/build_site.py):
    a chooser, a teachers page and two tracks."""
    r = client.get("/learn", follow_redirects=False)
    assert r.status_code in (307, 308) and r.headers["location"] == "/learn/"
    r = client.get("/learn/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    for text in ("Rockets and Model Rocketry", "/learn/elementary/", "/learn/middle/", "/learn/teachers",
                 "Grades 3–5", "Grades 6–8", "Use it with Rocket Builder", "https://rocket.quiverdesignworks.net/"):
        assert text in r.text, text
    r = client.get("/learn/teachers")
    assert r.status_code == 200
    for text in ("Washington State K–12 Science Learning Standards", "WA Science 2026", "S.MS.PS2.2",
                 "3-PS2-1", "MS-ETS1-4", "apogeerockets.com"):
        assert text in r.text, text
    for track, count, codes in (("elementary", 8, ("3-PS2-1", "5-PS2-1", "3-5-ETS1-3")),
                                ("middle", 9, ("MS-PS2-2", "MS-PS3-1", "MS-ETS1-4"))):
        r = client.get(f"/learn/{track}", follow_redirects=False)
        assert r.status_code == 308 and r.headers["location"] == f"/learn/{track}/"
        r = client.get(f"/learn/{track}/")
        assert r.status_code == 200
        for text in ("Standards map", f"/learn/{track}/lesson-{count:02d}", f"/learn/{track}/worksheets.pdf",
                     f"/learn/{track}/safety", *codes):
            assert text in r.text, (track, text)
        for n in range(1, count + 1):
            r = client.get(f"/learn/{track}/lesson-{n:02d}")
            assert r.status_code == 200, (track, n)
            for text in ("Standards", "I can", "Materials", "Check for understanding", "Answer key",
                         "Teacher notes", f'href="/learn/{track}/"', "Open Rocket Builder"):
                assert text in r.text, (track, n, text)
        assert client.get(f"/learn/{track}/lesson-02.html").status_code == 200
        assert client.get(f"/learn/{track}/worksheets").status_code == 200
        r = client.get(f"/learn/{track}/worksheets.pdf")
        assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
    assert "NAR Model Rocket Safety Code" in client.get("/learn/middle/safety").text
    assert "Paper rockets only" in client.get("/learn/elementary/safety").text


def test_learn_old_addresses_redirect_to_middle_school():
    """The first unit's /learn/day-NN, /learn/safety and /learn/worksheets(.pdf) still work."""
    for old, new in (("day-01", "lesson-01"), ("day-03", "lesson-03"), ("day-03.html", "lesson-03"), ("day-08", "lesson-08"),
                     ("day-09", "lesson-08"), ("day-10", "lesson-09"), ("safety", "safety"),
                     ("worksheets", "worksheets"), ("worksheets.pdf", "worksheets.pdf")):
        r = client.get(f"/learn/{old}", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == f"/learn/middle/{new}", old
        assert client.get(f"/learn/{old}").status_code == 200, old


def test_learn_unknown_pages_404():
    for page in ("day-11", "day-1", "index", "learn.css", "..%2Fapp.py", "..%2F..%2Fapp.py", "worksheets.pdf.html",
                 "high", "high/", "elementary/lesson-09", "middle/lesson-10", "middle/lesson-1", "middle/index",
                 "middle/learn.css", "elementary/day-01", "middle/..%2Findex.html"):
        assert client.get(f"/learn/{page}").status_code == 404, page
    assert client.get("/learn/../app.py").status_code == 404
    assert client.get("/learn/middle/../../app.py").status_code == 404


def test_secondary_pages_use_the_brand():
    """/sources, /ordersupplies, /terms and /admin share static/brand.css and the branded header."""
    assert client.get("/static/brand.css").status_code == 200
    for path in ("/sources", "/ordersupplies", "/terms", "/admin"):
        html = client.get(path).text
        assert '/static/brand.css' in html and 'class="rb-header"' in html and "Quiver Design Works" in html, path


def test_me_says_whether_the_account_is_the_owner(monkeypatch):
    """/api/auth/me carries is_admin, so the page shows the owner the order-desk links."""
    import app as rocket
    page = client.get("/").text
    assert 'data-admin hidden' in page and "quiverdesignworks.net/admin/orders" in page
    c = TestClient(rocket.app)
    import uuid
    email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    assert c.post("/api/auth/signup", json={"email": email, "password": "rocket123", "age_ok": True}).status_code == 200
    assert c.get("/api/auth/me").json()["user"]["is_admin"] is False
    monkeypatch.setattr(rocket, "ADMIN_EMAILS", {email})
    assert c.get("/api/auth/me").json()["user"]["is_admin"] is True

