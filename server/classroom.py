"""Classroom features (owner approved 2026-10-19, for the /learn curriculum):

- /tools/altitude: the altitude-from-angle calculator (static/tools/altitude.html),
  also opened from the designer's ⋯ menu.
- /mission/<build id>: a printable one-page mission card for a built rocket (mission.py).
- Class sharing without student accounts (classes.py): a signed-in teacher makes
  a class and gets a code; students type the code and a first name or nickname
  to hand in the rocket on their screen; /classes is the teacher's page.

app.py includes `router(...)`, passing in the few helpers it needs, so this
module never imports app.py (and app.py's build and launch code stay as they are).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

import classes
import mission

STATIC = Path(__file__).resolve().parent / "static"

# A whole class usually shares one school address (NAT), so these are per
# address but sized for 30+ students handing in a few times each.
SUBMITS_PER_10_MIN = int(os.environ.get("ROCKETGEN_CLASS_SUBMITS_PER_10_MIN", 150))
LOOKUPS_PER_10_MIN = int(os.environ.get("ROCKETGEN_CLASS_LOOKUPS_PER_10_MIN", 300))
CLASSES_PER_HOUR = int(os.environ.get("ROCKETGEN_CLASSES_PER_HOUR", 20))


class ClassIn(BaseModel):
    name: str = Field("My class", max_length=classes.MAX_CLASS_NAME)


class ClosedIn(BaseModel):
    closed: bool = True


class SubmitIn(BaseModel):
    nickname: str = Field(..., max_length=40)
    build_id: str = Field(..., max_length=40)
    design_name: str = Field("My rocket", max_length=80)


def summary(b: dict) -> dict:
    """What a teacher sees about a handed-in rocket, from the server's own build
    (never from numbers the browser sends)."""
    p, st, fl = b["params"], b["stability"], b["flights"]
    best = next((r for r in fl["rows"] if r["code"] == fl["recommended"]), None)
    chute, field = b.get("parachute") or {}, b.get("field") or {}
    return {"motor_size": p["motor"], "height_mm": st["length_mm"], "fin_shape": p["fin_shape"], "fin_count": p["fin_count"],
            "nose_shape": p["nose_shape"], "margin_cal": st["margin_cal"], "status": st["status"], "ok": st["ok"],
            "recommended": best["motor"] if best else None, "apogee_m": best["apogee_m"] if best else None,
            "liftoff_g": best["liftoff_g"] if best else round(st["liftoff_mass_g"]),
            "nose_weight_g": p.get("nose_weight_g") or 0, "parachute_in": chute.get("size_in"),
            "field_m": field.get("recommended_m"), "mode": "beginner" if p.get("overall_length") is not None else "advanced"}


def router(current_user: Callable, rate_limit: Callable, get_build: Callable, shape: Callable,
           page_headers: dict) -> APIRouter:
    r = APIRouter()
    classes.purge(force=True)  # on startup; then at most hourly, from the class routes below

    def teacher(request: Request) -> dict:
        user = current_user(request)
        if not user:
            raise HTTPException(401, "Sign in (a grown-up account) to make and see classes.")
        classes.purge()
        return user

    def fail(ex: classes.ClassError):
        raise HTTPException(ex.status, str(ex)) from None

    # ---------- pages ----------
    @r.get("/tools/altitude")
    def altitude_page():
        """How high did it fly? Angle + baseline -> height, with the working shown."""
        return FileResponse(STATIC / "tools" / "altitude.html", headers=page_headers)

    @r.get("/classes")
    def classes_page():
        """A teacher's classes: make a code, see what students handed in."""
        return FileResponse(STATIC / "classes.html", headers=page_headers)

    @r.get("/mission/{build_id}", response_class=HTMLResponse)
    def mission_card(build_id: str, name: str = "My rocket", design: str | None = None):
        """A printable US-Letter mission card for a rocket built this visit."""
        try:
            b, g = get_build(build_id)
        except HTTPException:
            return HTMLResponse(mission.missing(), status_code=404, headers=page_headers)
        bal = g["balance"].with_nose_weight(b["params"].get("nose_weight_g") or 0)
        return HTMLResponse(mission.page(name[:80], b, {**shape(bal), "tail_mm": round(bal.z_tip, 1)}, g["report"], build_id,
                                         design if design and design.replace("-", "").replace("_", "").isalnum() else None),
                            headers=page_headers)

    # ---------- teachers ----------
    @r.get("/api/classes")
    def my_classes(request: Request):
        user = teacher(request)
        return {"classes": classes.list_for(user["id"]), "max_open": classes.MAX_OPEN_CLASSES,
                "max_submissions": classes.MAX_SUBMISSIONS, "retention_days": classes.RETENTION_DAYS}

    @r.post("/api/classes")
    def new_class(body: ClassIn, request: Request):
        user = teacher(request)
        rate_limit(request, "class", CLASSES_PER_HOUR, 3600)
        try:
            return classes.create(user["id"], body.name)
        except classes.ClassError as ex:
            fail(ex)

    def _mine(class_id: str, user: dict) -> dict:
        c = classes.get(class_id, user["id"])
        if not c:
            raise HTTPException(404, "No such class (it may have been deleted).")
        return c

    @r.get("/api/classes/{class_id}")
    def class_detail(class_id: str, request: Request):
        c = _mine(class_id, teacher(request))
        c["items"] = [{k: v for k, v in s.items() if k != "params"} for s in c["items"]]
        return c

    @r.post("/api/classes/{class_id}/close")
    def close_class(class_id: str, body: ClosedIn, request: Request):
        user = teacher(request)
        _mine(class_id, user)
        try:
            c = classes.set_closed(class_id, user["id"], body.closed)
        except classes.ClassError as ex:
            fail(ex)
        return {k: v for k, v in c.items() if k != "items"}

    @r.delete("/api/classes/{class_id}")
    def delete_class(class_id: str, request: Request):
        if not classes.delete(class_id, teacher(request)["id"]):
            raise HTTPException(404, "No such class.")
        return {"deleted": class_id}

    @r.delete("/api/classes/{class_id}/submissions/{sub_id}")
    def delete_submission(class_id: str, sub_id: str, request: Request):
        if not classes.delete_submission(class_id, sub_id, teacher(request)["id"]):
            raise HTTPException(404, "No such rocket in this class.")
        return {"deleted": sub_id}

    @r.get("/api/class-submissions/{sub_id}")
    def open_submission(sub_id: str, request: Request):
        """A handed-in design's settings, for the teacher to open in the designer (/?classsub=<id>)."""
        s = classes.submission_for_teacher(sub_id, teacher(request)["id"])
        if not s:
            raise HTTPException(404, "That rocket isn't in one of your classes any more.")
        return {"nickname": s["nickname"], "design_name": s["design_name"], "params": s["params"]}

    # ---------- students: no account, just the code and a nickname ----------
    @r.get("/api/join/{code}")
    def join_lookup(code: str, request: Request):
        rate_limit(request, "classcode", LOOKUPS_PER_10_MIN, 600)
        classes.purge()
        c = classes.lookup(code)
        if not c:
            raise HTTPException(404, "There's no class with that code. Check it with your teacher.")
        return c

    @r.post("/api/join/{code}")
    def join_submit(code: str, body: SubmitIn, request: Request):
        rate_limit(request, "classsubmit", SUBMITS_PER_10_MIN, 600)
        classes.purge()
        try:
            b, g = get_build(body.build_id)
        except HTTPException:
            raise HTTPException(404, "Press Build first, then hand in your rocket.") from None
        try:
            # Deliberately not logged: the nickname belongs to a child (see classes.py).
            return classes.submit(code, body.nickname, body.design_name, b["params"], summary(b))
        except classes.ClassError as ex:
            fail(ex)

    return r
