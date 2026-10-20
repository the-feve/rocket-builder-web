"""Classroom features (2026-10-19): altitude calculator, nose weight, mission card, class codes."""

import io
import os
import sqlite3
import tempfile
import time
import zipfile
import uuid

import pytest

os.environ.setdefault("ROCKETGEN_DB", os.path.join(tempfile.mkdtemp(), "designs.sqlite3"))
os.environ.setdefault("ROCKETGEN_ORDERS_DIR", os.path.join(tempfile.mkdtemp(), "orders"))

from fastapi.testclient import TestClient  # noqa: E402

import classes  # noqa: E402
import classroom  # noqa: E402
import designs  # noqa: E402
import app as server  # noqa: E402
from app import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """Every TestClient is the same address ("testclient"), and the per-address
    limits (sign-ups 20 / 10 min, builds 30 / 10 min, ...) are in-memory and
    shared by the whole pytest process. test_app.py uses up most of the sign-up
    budget, so whether a teacher sign-up here got a 429 depended on how long the
    run had taken (a flaky failure in full runs, 2026-10-19). Start each test clean."""
    server._hits.clear()
    classes._last_purge = 0.0
    yield
    server._hits.clear()


def _teacher(email: str) -> TestClient:
    c = TestClient(app)
    name, _, domain = email.partition("@")
    email = f"{name}+{uuid.uuid4().hex[:8]}@{domain}"  # unique even if ROCKETGEN_DB is reused between runs
    r = c.post("/api/auth/signup", json={"email": email, "password": "correct horse", "age_ok": True})
    assert r.status_code == 200, r.text
    return c


def _build(**kw) -> dict:
    r = client.post("/api/build", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_altitude_calculator_page():
    r = client.get("/tools/altitude")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-cache"
    t = r.text
    assert "At 45°, the height equals how far you walked" in t
    assert "tan(angle) × distance" in t and "eye height" in t.lower() and "Spotter 2" in t
    assert "/static/brand.css" in t and "embed" in t  # the brand, and the designer's dialog mode


def test_nose_weight_moves_the_cg_and_adds_mass():
    assert client.get("/api/options").json()["defaults"]["nose_weight_g"] == 0
    a = _build()
    b = _build(nose_weight_g=10)
    assert b["id"] != a["id"]
    sa, sb = a["stability"], b["stability"]
    assert sb["cg_mm"] < sa["cg_mm"] and sb["cp_mm"] == sa["cp_mm"]  # the CG dot moves toward the nose; the CP stays
    assert sb["margin_cal"] > sa["margin_cal"] and sb["liftoff_mass_g"] == round(sa["liftoff_mass_g"] + 10, 1)
    assert sb["nose_weight_g"] == 10 and "nose weight" in sb["message"] and "nose weight" not in sa["message"]
    assert b["total_mass_g"] == a["total_mass_g"]  # the printed parts are the same geometry
    rows = lambda r: {x["code"]: x for x in r["flights"]["rows"]}
    for code, x in rows(a).items():  # heavier: lower with every motor
        assert rows(b)[code]["apogee_m"] <= x["apogee_m"] and rows(b)[code]["liftoff_g"] > x["liftoff_g"], code
    notes = zipfile.ZipFile(io.BytesIO(client.get(f"/api/builds/{b['id']}/rocket.zip").content)).read("build_notes.txt").decode()
    assert "Nose weight: 10 g of modelling clay" in notes
    assert "Nose weight" not in zipfile.ZipFile(io.BytesIO(client.get(f"/api/builds/{a['id']}/rocket.zip").content)).read("build_notes.txt").decode()
    assert client.post("/api/build", json={"nose_weight_g": 60}).status_code == 422
    # Saved designs keep it.
    d = client.post("/api/designs", json={"name": "Clay", "params": {"nose_weight_g": 7}}).json()
    assert client.get(f"/api/designs/{d['id']}").json()["params"]["nose_weight_g"] == 7


def test_mission_card():
    b = _build(nose_weight_g=5)
    r = client.get(f"/mission/{b['id']}", params={"name": "Zoomer <3", "design": "abc123"})
    assert r.status_code == 200
    t = r.text
    assert "Zoomer &lt;3" in t and "<svg" in t and "CG balance point" in t and "CP push point" in t
    for words in ("My prediction", "Measured results", "Angle at the top", "Flight time", "Landed how far", "Notes",
                  "Stability score", "Best motor", "Predicted peak", "Parachute", "Launch field", "5 g clay",
                  "size: letter", "@media print", "rocket.quiverdesignworks.net/d/abc123",
                  "At 45°, the height equals how far you walked"):
        assert words in t, words
    best = next(x for x in b["flights"]["rows"] if x["code"] == b["flights"]["recommended"])
    assert best["motor"] in t and f"{best['apogee_m']} m" in t
    assert f"{b['stability']['margin_cal']:.2f} cal" in t
    gone = client.get("/mission/nosuchbuild")
    assert gone.status_code == 404 and "Build the rocket again" in gone.text


def test_designer_has_the_classroom_links():
    t = client.get("/").text
    for words in ('id="classjoin"', 'id="myclasses"', 'id="altcalc"', 'id="missioncard"', 'id="launchsim"',
                  'name="nose_weight_g"', "/static/classroom.js", "rbDesigner"):
        assert words in t, words
    js = client.get("/static/classroom.js").text
    assert "Don't use your full name" in js and "/api/join/" in js and "/mission/" in js and "classsub" in js
    assert "Class sharing" in client.get("/terms").text and "180 days" in client.get("/terms").text


def test_teacher_routes_need_sign_in():
    anon = TestClient(app)
    assert anon.get("/api/classes").status_code == 401
    assert anon.post("/api/classes", json={"name": "x"}).status_code == 401
    assert anon.get("/api/classes/abc").status_code == 401
    assert anon.post("/api/classes/abc/close", json={"closed": True}).status_code == 401
    assert anon.delete("/api/classes/abc").status_code == 401
    assert anon.delete("/api/classes/abc/submissions/x").status_code == 401
    assert anon.get("/api/class-submissions/x").status_code == 401
    page = anon.get("/classes")
    assert page.status_code == 200 and "My classes" in page.text and "noindex" in page.text


def test_class_code_hand_in_list_and_delete(monkeypatch):
    t = _teacher("teacher1@example.com")
    c = t.post("/api/classes", json={"name": "Room 12"}).json()
    code = c["code"]
    assert len(code) == 6 and set(code) <= set(classes.CODE_ALPHABET) and not set(code) & set("0O1IL")
    assert c["expires_at"] - c["created_at"] == 180 * 86400 and not c["closed"]
    # A student: no account, any device. The code is forgiving about case and spaces.
    kid = TestClient(app)
    look = kid.get(f"/api/join/{code[:3].lower()} {code[3:]}")
    assert look.status_code == 200 and look.json() == {"code": code, "name": "Room 12", "open": True}
    assert kid.get("/api/join/ZZZZZZ").status_code == 404
    b = _build()
    r = kid.post(f"/api/join/{code}", json={"nickname": "Ava", "build_id": b["id"], "design_name": "Zoomer_M18_300mm_3xTrapezoid_Ogive"})
    assert r.status_code == 200, r.text
    assert r.json()["replaced"] is False and r.json()["class"] == "Room 12"
    # Must be a real build on the server, and a nickname, not an email, phone or full sentence.
    assert kid.post(f"/api/join/{code}", json={"nickname": "Ava", "build_id": "nope"}).status_code == 404
    for bad in ("ava@example.com", "", "Ava 5551234", "x" * 21, "<script>"):
        assert kid.post(f"/api/join/{code}", json={"nickname": bad, "build_id": b["id"]}).status_code in (400, 422), bad
    # Handing in again with the same nickname replaces it.
    b2 = _build(nose_weight_g=3)
    r = kid.post(f"/api/join/{code}", json={"nickname": "ava", "build_id": b2["id"], "design_name": "Zoomer 2"})
    assert r.json()["replaced"] is True
    kid.post(f"/api/join/{code}", json={"nickname": "Ben K.", "build_id": b["id"]})
    # The teacher's list: name, summary, stability, recommended motor.
    lst = t.get("/api/classes").json()["classes"]
    assert [x["submissions"] for x in lst if x["id"] == c["id"]] == [2]
    d = t.get(f"/api/classes/{c['id']}").json()
    items = {s["nickname"]: s for s in d["items"]}
    assert set(items) == {"ava", "Ben K."} and "params" not in items["ava"]
    s = items["ava"]["summary"]
    assert s["motor_size"] == "M18" and s["margin_cal"] == b2["stability"]["margin_cal"] and s["nose_weight_g"] == 3
    assert s["recommended"] and s["apogee_m"] > 0 and s["ok"] is True
    assert items["ava"]["design_name"] == "Zoomer 2"
    # Open in the designer: the teacher gets the settings; nobody else does.
    sub = t.get(f"/api/class-submissions/{items['ava']['id']}").json()
    assert sub["params"]["nose_weight_g"] == 3 and sub["nickname"] == "ava"
    other = _teacher("teacher2@example.com")
    assert other.get(f"/api/class-submissions/{items['ava']['id']}").status_code == 404
    assert other.get(f"/api/classes/{c['id']}").status_code == 404
    assert other.delete(f"/api/classes/{c['id']}").status_code == 404
    assert other.delete(f"/api/classes/{c['id']}/submissions/{items['ava']['id']}").status_code == 404
    # Delete one rocket.
    assert t.delete(f"/api/classes/{c['id']}/submissions/{items['Ben K.']['id']}").status_code == 200
    assert len(t.get(f"/api/classes/{c['id']}").json()["items"]) == 1
    # Closing stops hand-ins (the rockets stay); reopening takes them again.
    assert t.post(f"/api/classes/{c['id']}/close", json={"closed": True}).json()["closed"] is True
    assert kid.get(f"/api/join/{code}").json()["open"] is False
    assert kid.post(f"/api/join/{code}", json={"nickname": "Cy", "build_id": b["id"]}).status_code == 409
    assert t.post(f"/api/classes/{c['id']}/close", json={"closed": False}).json()["closed"] is False
    # Per-class cap.
    monkeypatch.setattr(classes, "MAX_SUBMISSIONS", 2)
    assert kid.post(f"/api/join/{code}", json={"nickname": "Cy", "build_id": b["id"]}).status_code == 200
    full = kid.post(f"/api/join/{code}", json={"nickname": "Dee", "build_id": b["id"]})
    assert full.status_code == 409 and "most" in full.json()["detail"]
    assert kid.post(f"/api/join/{code}", json={"nickname": "Cy", "build_id": b["id"]}).status_code == 200  # replacing still works
    # Deleting the class deletes everything handed in.
    assert t.delete(f"/api/classes/{c['id']}").status_code == 200
    assert kid.get(f"/api/join/{code}").status_code == 404
    with sqlite3.connect(designs.DB_PATH) as con:
        assert con.execute("SELECT COUNT(*) FROM class_submissions WHERE class_id = ?", (c["id"],)).fetchone()[0] == 0


def test_class_limits_per_teacher_and_rate_limit(monkeypatch):
    t = _teacher("teacher3@example.com")
    monkeypatch.setattr(classes, "MAX_OPEN_CLASSES", 2)
    a = t.post("/api/classes", json={"name": "A"}).json()
    t.post("/api/classes", json={"name": "B"})
    r = t.post("/api/classes", json={"name": "C"})
    assert r.status_code == 409 and "open classes" in r.json()["detail"]
    t.post(f"/api/classes/{a['id']}/close", json={"closed": True})  # a closed class doesn't count
    assert t.post("/api/classes", json={"name": "C"}).status_code == 200
    assert t.post(f"/api/classes/{a['id']}/close", json={"closed": False}).status_code == 409  # can't reopen past the limit
    # Hand-ins are rate limited per address (sized for a whole class behind one school address).
    monkeypatch.setattr(classroom, "SUBMITS_PER_10_MIN", 0)
    b = _build()
    r = TestClient(app).post(f"/api/join/{a['code']}", json={"nickname": "Eve", "build_id": b["id"]})
    assert r.status_code == 429


def test_classes_are_deleted_after_180_days():
    t = _teacher("teacher4@example.com")
    old = t.post("/api/classes", json={"name": "Last year"}).json()
    new = t.post("/api/classes", json={"name": "This year"}).json()
    b = _build()
    assert TestClient(app).post(f"/api/join/{old['code']}", json={"nickname": "Fay", "build_id": b["id"]}).status_code == 200
    with sqlite3.connect(designs.DB_PATH) as con:
        con.execute("UPDATE classes SET created_at = ? WHERE id = ?", (time.time() - 181 * 86400, old["id"]))
        con.execute("UPDATE class_submissions SET created_at = ? WHERE class_id = ?", (time.time() - 181 * 86400, old["id"]))
    # Hidden at once, even before the purge runs...
    assert TestClient(app).get(f"/api/join/{old['code']}").status_code == 404
    assert [c["name"] for c in t.get("/api/classes").json()["classes"]] == ["This year"]
    # ...and the purge deletes the rows (at startup, then at most hourly).
    assert classes.purge(force=True) >= 1
    with sqlite3.connect(designs.DB_PATH) as con:
        assert con.execute("SELECT COUNT(*) FROM classes WHERE id = ?", (old["id"],)).fetchone()[0] == 0
        assert con.execute("SELECT COUNT(*) FROM class_submissions WHERE class_id = ?", (old["id"],)).fetchone()[0] == 0
        assert con.execute("SELECT COUNT(*) FROM classes WHERE id = ?", (new["id"],)).fetchone()[0] == 1
    # Nothing about a student but the nickname is stored.
    with sqlite3.connect(designs.DB_PATH) as con:
        cols = {r[1] for r in con.execute("PRAGMA table_info(class_submissions)")}
    assert cols == {"id", "class_id", "nickname", "design_name", "params", "summary", "created_at", "updated_at"}
