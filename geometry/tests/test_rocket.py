"""Phase 0 checks for the M18 minimum-diameter rocket.

There is no Onshape export to compare against yet, so these check the port
against data/derived_printed_dimensions.csv, hand-computed values from the
FeatureScript's formulas, and geometric sanity (one closed solid per part,
no parts overlapping, no missing slices).
"""

from __future__ import annotations

import csv
import math
from functools import lru_cache

import pytest

from rocketgen.body import body_segment, nose_radius_at
from rocketgen.build import build_rocket
from rocketgen.fins import FinShape
from rocketgen.geom import as_shape, slice_area
from rocketgen.params import DATA_DIR, DesignParams, compute_derived

FIN_SHAPES = list(FinShape)


@lru_cache(maxsize=None)
def rocket(shape: FinShape = FinShape.CLIPPED_DELTA, **kw):
    return build_rocket(DesignParams(fin_shape=shape, **dict(kw)))


def csv_row(airframe: str) -> dict:
    with open(DATA_DIR / "derived_printed_dimensions.csv", newline="") as f:
        return next(r for r in csv.DictReader(f) if r["Airframe"] == airframe)


# ---- derived values -------------------------------------------------------

def test_bay_id_matches_csv_for_every_motor():
    for motor, airframe in [("M13", "M13-BT5"), ("M18", "M18-BT20"), ("M24", "M24-BT50"), ("M29", "M29-29T")]:
        d = compute_derived(DesignParams(motor=motor))
        assert d.bay_id == pytest.approx(float(csv_row(airframe)["bay_id_mm"]), abs=1e-9)


def test_min_diameter_m18_hand_values():
    d = compute_derived(DesignParams())
    # wall 1.5 mm (rocket_global_settings.csv). The CSV's body_od (20.8) is
    # from the old 1.2 mm wall, so body_od is checked against the rule.
    assert d.body_od == pytest.approx(d.bay_id + 2 * d.wall) == pytest.approx(21.4)
    assert d.body_id == pytest.approx(18.4)
    assert not d.has_mount
    assert d.shoulder_od == pytest.approx(18.36)
    assert d.shoulder_len == pytest.approx(0.75 * 21.4 - 4)
    assert d.joint_rise == pytest.approx(1.52)
    assert d.inner_taper_rise == pytest.approx((9.2 - (9.18 - 1.5)) / math.tan(math.radians(8)))
    assert d.zmax == 195


@pytest.mark.parametrize("shape,hang", [
    (FinShape.CLIPPED_DELTA, 10.0),  # HANDOFF: Clipped delta -> hang 10, bay 60
    (FinShape.TRAPEZOID, 10.0),
    # Swept: HANDOFF's 12.8 predates the grip ribs (r_cap_max +0.6 mm); by
    # hand with the ribs, the fin's lower edge at u = 4.075 is z = -4.41,
    # cap top -5.41, face -13.41.
    (FinShape.SWEPT, 13.41),
])
def test_motor_hang_and_bay(shape, hang):
    d = compute_derived(DesignParams(fin_shape=shape))
    assert d.thread["hang"] == pytest.approx(hang, abs=0.01)
    assert d.bay_len == pytest.approx(70 - hang, abs=0.01)
    assert d.thread["turns"] == pytest.approx(3.0)
    assert d.thread["p"] == 2.5


def test_larger_body_gets_inner_mount():
    d = compute_derived(DesignParams(body_od_override=33.7))
    assert d.has_mount
    assert d.mount_od == pytest.approx(21.4)


# ---- geometry -------------------------------------------------------------

@pytest.mark.parametrize("shape", FIN_SHAPES)
def test_every_part_is_one_valid_solid(shape):
    r = rocket(shape)
    assert [p.name for p in r.parts] == ["Aft", "Anchor_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]
    for p in r.parts:
        assert p.assembled.is_valid, p.name
        assert len(p.assembled.solids()) == 1, p.name
        assert p.volume > 0, p.name


@pytest.mark.parametrize("shape", FIN_SHAPES)
def test_parts_do_not_overlap(shape):
    parts = rocket(shape).parts
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            x = as_shape(parts[i].assembled.intersect(parts[j].assembled))
            v = 0.0 if x is None else x.volume
            assert v < 0.01, f"{parts[i].name} overlaps {parts[j].name} by {v:.3f} mm3"


@pytest.mark.parametrize("shape", FIN_SHAPES)
def test_aft_has_no_missing_slices(shape):
    """OpenCascade can return a 'valid' solid with a slice missing; every
    slice of the aft tube must keep at least the plain tube wall."""
    r = rocket(shape)
    d = r.derived
    aft = r.parts[0].assembled
    annulus = math.pi * ((d.body_od / 2) ** 2 - (d.body_id / 2) ** 2)
    top = r.seg_lens[0] - d.wall - 0.1  # below the socket countersink
    z = 0.5
    while z < top:
        assert slice_area(aft, z) > annulus - 0.05, f"slice at z = {z}"
        z += 2.5


def test_aft_print_orientation_sits_on_bed():
    for p in rocket().parts:
        assert p.local.bounding_box().min.Z == pytest.approx(0, abs=1e-6)


def _pappus(pts):
    """Volume of a closed (r, z) polygon revolved 360 degrees about z."""
    a = cz = 0.0
    for (r0, z0), (r1, z1) in zip(pts, pts[1:] + pts[:1]):
        cross = r0 * z1 - r1 * z0
        a += cross
        cz += (r0 + r1) * cross
    a /= 2
    r_bar = cz / (6 * a)
    return abs(2 * math.pi * r_bar * a)


def test_body_segment_volume_matches_pappus():
    d = compute_derived(DesignParams())
    seg_len = 55.0
    sh = d.shoulder_len
    pts = [
        (d.shoulder_od / 2 - d.wall, 0), (d.shoulder_od / 2, 0), (d.shoulder_od / 2, sh),
        (d.body_od / 2, sh + d.joint_rise), (d.body_od / 2, seg_len), (d.body_id / 2, seg_len - d.wall),
        (d.body_id / 2, sh + d.inner_taper_rise), (d.shoulder_od / 2 - d.wall, sh),
    ]
    assert body_segment(d, seg_len).volume == pytest.approx(_pappus(pts), rel=1e-6)


@pytest.mark.parametrize("shape", ["tangent_ogive", "conical", "elliptical", "parabolic", "von_karman"])
def test_nose_profiles_meet_body_and_tip(shape):
    assert nose_radius_at(shape, 0, 64.2, 10.7) == pytest.approx(0, abs=1e-6)
    assert nose_radius_at(shape, 64.2, 64.2, 10.7) == pytest.approx(10.7, abs=1e-6)


def test_thread_cap_engages_boss():
    """Cap and boss overlap in height by the full 3 turns, without touching."""
    r = rocket()
    t = r.derived.thread
    assert t["cap_top"] - t["z_boss_end"] == pytest.approx(3 * t["p"])
    cap = next(p for p in r.parts if p.name == "Motor_Cap").assembled
    bb = cap.bounding_box()
    assert bb.max.Z == pytest.approx(t["cap_top"], abs=1e-3)
    assert bb.min.Z == pytest.approx(t["z_face"] - t["cap_face_t"], abs=1e-3)


def test_mass_estimate_is_plausible():
    m = rocket().mass_g()
    # An Estes Orbis-sized printed airframe: tens of grams.
    assert 25 < sum(m.values()) < 80


# ---- Phase 1: lugs, standoff, anchor strap ----------------------------------

@pytest.mark.parametrize("lugs,names", [
    ("none", ["Aft", "Anchor_Seg", "Nose", "Motor_Cap"]),
    ("aft_only", ["Aft", "Anchor_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]),
])
def test_lug_options(lugs, names):
    r = rocket(launch_lugs=lugs)
    assert [p.name for p in r.parts] == names
    assert all(p.assembled.is_valid for p in r.parts)


def test_lugs_add_material_on_one_line():
    bare = rocket(launch_lugs="none").parts[0].volume
    aft_only = rocket(launch_lugs="aft_only").parts[0].volume
    two = rocket().parts[0].volume  # forward lug lands on the Aft part at 250 mm
    assert bare < aft_only < two


def test_forward_lug_on_seg_2():
    r = rocket(body_length=400.0, forward_lug_frac=0.7)
    assert [p.name for p in r.parts] == ["Aft", "Seg_2", "Anchor_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]
    d = r.derived
    plain = body_segment(d, r.seg_lens[1]).volume
    assert r.parts[1].volume > plain + 20  # the forward lug


def test_anchor_strap_is_inside_the_bore():
    from rocketgen.anchor import anchor_strap_geometry
    r = rocket()
    d = r.derived
    seg = r.parts[1]
    assert seg.name == "Anchor_Seg"
    plain = body_segment(d, r.seg_lens[1]).volume
    assert seg.volume > plain + 20
    # Nothing added outside the body OD.
    bb = seg.assembled.bounding_box()
    assert max(bb.max.X, -bb.min.X, bb.max.Y, -bb.min.Y) <= d.body_od / 2 + 1e-3
    s = anchor_strap_geometry(d)
    assert r.seg_lens[-1] >= s["sec_len"] - 1e-9  # a short leftover is folded into it


@pytest.mark.parametrize("motor", ["M13", "M18", "M29"])
def test_anchor_strap_prints_without_supports(motor):
    """Every face pointing down more steeply than 45 degrees is buried in the
    wall; the cord channel behind the bar is clear for its full height."""
    from rocketgen.anchor import anchor_strap, anchor_strap_geometry
    d = compute_derived(DesignParams(motor=motor))
    s = anchor_strap_geometry(d)
    strap = anchor_strap(d, s)
    ri = d.body_id / 2
    from rocketgen.anchor import APEX_FILLET
    # The peak's round: on the bar, and again past the cord gap where it is buried.
    rounds = [f for f in strap.faces() if f.geom_type.name == "CYLINDER"
              and abs((f.radius or 0) - APEX_FILLET) < 1e-6]
    assert rounds, "the arch's peak is rounded"
    for f in strap.faces():
        if f in rounds:
            # The rounded peak is a short bridge: under 3 mm across.
            assert f.bounding_box().size.Y < 3.0
            continue
        if f.normal_at().Z < -0.72:
            assert all(math.hypot(v.X, v.Y) >= ri - 1e-3 for v in f.vertices()), "unsupported overhang"
    # Probe the cord gap: a 1 mm square rod down the middle, between bar and wall.
    from build123d import Solid
    probe = Solid.make_box(1, 1, 200).translate((ri - s["hole_depth"] / 2 - 0.5, -0.5, -50))
    hit = strap.intersect(probe)
    assert hit is None or not list(hit.solids())
    assert s["cord_width"] >= 9.0  # room to lace a flat shock cord
    # Nothing outside half a wall into the wall.
    bb = strap.bounding_box()
    assert max(bb.max.X, -bb.min.X, bb.max.Y, -bb.min.Y) <= ri + d.wall / 2 + 1e-3


def test_nose_shoulder_is_shorter_than_body_joints():
    r = rocket()
    d, p = r.derived, r.params
    assert d.nose_shoulder_len == pytest.approx(max(0.7 * d.shoulder_len, 7.0))
    assert d.nose_shoulder_len < d.shoulder_len
    nose = next(q for q in r.parts if q.name == "Nose")
    height = nose.local.bounding_box().size.Z
    assert height == pytest.approx(d.nose_shoulder_len + d.joint_rise + p.nose_fineness * d.cal, abs=0.05)


def test_rod_standoff_reaches_below_rocket():
    r = rocket()
    standoff = next(p for p in r.parts if p.name == "Rod_Standoff").assembled.bounding_box()
    t = r.derived.thread
    assert standoff.max.Z == pytest.approx(0, abs=1e-6)  # aft lug rests on it
    assert standoff.min.Z == pytest.approx(t["z_lowest"] - 15.0, abs=1e-6)  # 15 mm pad clearance


def test_rod_line_clears_motor_cap():
    from rocketgen.lugs import lug_geometry
    d = compute_derived(DesignParams())
    lug = lug_geometry(d, 3.175, True, 15.0)
    assert lug["center_r"] - lug["standoff_ro"] >= d.thread["r_cap_max"] + 0.5 - 1e-9


# ---- stability ------------------------------------------------------------

def test_nose_cp_matches_textbook_values():
    from rocketgen.stability import nose_cp
    L, R = 60.0, 10.0
    assert nose_cp("conical", L, R) == (2.0, pytest.approx(2 * L / 3, rel=1e-3))
    assert nose_cp("tangent_ogive", L, R)[1] == pytest.approx(0.466 * L, rel=0.02)
    assert nose_cp("elliptical", L, R)[1] == pytest.approx(L / 3, rel=1e-3)


def test_fin_cp_rectangular_fin():
    # Rectangular fin, no sweep: X = x_le + chord/4 (the quarter-chord point).
    from rocketgen.stability import fin_cp
    cn, x = fin_cp(3, 30, 30, 20, 0, 10, 100)
    assert x == pytest.approx(100 + 7.5) and cn > 0


def test_stability_default_and_trends():
    from rocketgen.flight import motors_for
    from rocketgen.stability import stability
    s = stability(rocket())
    assert 0.8 < s.margin_cal < 1.5 and s.ok and s.status == "stable" and s.motor == "C5"
    assert 0 < s.cg < s.length and 0 < s.cp < s.length
    # A lighter motor: more stable.
    a8 = next(m for m in motors_for("M18") if m.code == "A8")
    assert stability(rocket(), a8).margin_cal > s.margin_cal
    # The heaviest M24 at minimum diameter needs bigger fins than the standard ones.
    heavy = stability(rocket(motor="M24"))
    assert not heavy.ok and "Unstable" in heavy.message


def test_auto_size_fins_makes_the_heaviest_motor_stable():
    from rocketgen.stability import Balance, build_stable
    r = build_stable(DesignParams(motor="M24"))
    assert r.params.fin_scale > 1 and Balance(r).check().ok and "enlarged" in r.notes[0]
    assert build_stable(DesignParams()).params.fin_scale == 1  # already stable: untouched


def test_flight_sim_matches_the_motor_picker():
    # M18, 52 g without motor, 20.8 mm: the HTML picker's numbers.
    from rocketgen.flight import motors_for, pick, simulate
    flights = {f.motor.code: f for f in (simulate(m, 52, 20.8) for m in motors_for("M18"))}
    assert flights["C6"].apogee == pytest.approx(357, abs=3) and flights["C6"].ok
    assert not flights["A8"].ok and "Too heavy for this motor" in flights["A8"].problems
    assert pick(list(flights.values()), 150).motor.code == "B6"


# ---- overall height (the website's beginner mode) --------------------------

@pytest.mark.parametrize("shape,kw", [
    (FinShape.CLIPPED_DELTA, {}),                                     # default M18, one body part + anchor
    (FinShape.SWEPT, {"fin_scale": 1.5}),                             # fins trail below the tail
    (FinShape.TRAPEZOID, {"body_length": 420.0}),                     # three body parts (two joints)
    (FinShape.DELTA, {"motor": "M24", "nose_fineness": 4.0}),
])
def test_overall_length_matches_the_built_rocket(shape, kw):
    from rocketgen.build import overall_length
    from rocketgen.stability import Balance
    r = rocket(shape, **kw)
    assert overall_length(r.params) == pytest.approx(Balance(r).length, abs=0.05)


def test_body_length_for_hits_the_target():
    from rocketgen.build import body_length_for, overall_length
    from rocketgen.geom import GeometryError
    for motor, target in [("M18", 330.0), ("M18", 520.0), ("M24", 600.0), ("M13", 250.0)]:
        p = DesignParams(motor=motor, fin_shape=FinShape.SWEPT)
        b = body_length_for(p, target)
        assert overall_length(p.with_(body_length=b)) == pytest.approx(target, abs=0.1)
    with pytest.raises(GeometryError, match="too short"):
        body_length_for(DesignParams(motor="M29"), 60.0)


@pytest.mark.parametrize("motor,wall", [("M13", 0.8), ("M13", 3.0), ("M29", 0.8), ("M29", 3.0)])
def test_wall_thickness_builds(motor, wall):
    """The website's wall field: thin and thick walls build sound parts, and
    the stock tube is the motor bay plus two walls."""
    from rocketgen.geom import meshes
    r = rocket(motor=motor, wall=wall)
    d = r.derived
    assert d.wall == wall and d.body_od == pytest.approx(d.bay_id + 2 * wall)
    assert d.body_id == pytest.approx(d.body_od - 2 * wall)
    for p in r.parts:
        assert p.assembled.is_valid and meshes(p.assembled), p.name


def test_height_ranges_match_the_build():
    """The website snaps Beginner heights to these ranges, so the lowest one
    must build and the one below it must not (here: the aft segment is too
    short for the M24 motor bay)."""
    from rocketgen.build import body_length_for, height_ranges, min_printer_height, plan_rocket
    from rocketgen.geom import GeometryError
    from rocketgen.stability import Balance
    p = DesignParams(motor="M24", fin_shape=FinShape("trapezoid"))
    ranges = height_ranges(p, 150, 400)
    lo = ranges[0][0]
    assert ranges == [[lo, 400]] and 180 < lo < 260
    r = build_rocket(p.with_(body_length=body_length_for(p, lo)))
    assert r.parts and Balance(r).length == pytest.approx(lo, abs=0.1)
    with pytest.raises(GeometryError, match="Aft segment"):
        plan_rocket(p.with_(body_length=body_length_for(p, lo - 1)))
    # A printer too short for any M24 rocket.
    ph = min_printer_height(p)
    assert 80 < ph < 150
    assert height_ranges(p.with_(print_max_height=ph - 1), 80, 1000) == []


def test_score_advice_estimates_match_rebuilds():
    """The score advice's height estimate (no rebuild) lands close to a real
    rebuild at that height, and the advice suggests shortening an
    over-stable rocket and nothing inside the 1-2 cal sweet spot."""
    from rocketgen.build import body_length_for
    from rocketgen.flight import motors_for
    from rocketgen.stability import Balance, advice
    p = DesignParams(motor="M18", fin_shape=FinShape("trapezoid"))
    b = Balance(build_rocket(p.with_(body_length=body_length_for(p, 600))))
    st = b.check()
    assert st.margin_cal > 3
    est = b.predict_length(450 - b.length)
    real = Balance(build_rocket(p.with_(body_length=body_length_for(p, 450)))).check().margin_cal
    assert est == pytest.approx(real, abs=0.15)
    a = advice(b, st, motors_for("M18"), beginner=True)
    assert a["zone"] == "over" and a["items"][0]["kind"] == "shorter" and "step 4" in a["items"][0]["text"]
    assert 1.0 <= a["items"][0]["est_cal"] <= 2.0
    # Nose weight: grams that bring an unstable rocket to about 1.5 cal.
    assert b.predict(nose_g=0) == pytest.approx(st.margin_cal, abs=1e-6)
    assert b.predict(nose_g=20) > st.margin_cal
    ok = Balance(build_rocket(p.with_(body_length=body_length_for(p, 312), fin_scale=1.15)))
    if 1.0 <= ok.check().margin_cal <= 2.0:
        assert advice(ok, ok.check(), motors_for("M18"), beginner=True) is None


def test_critical_fit_overrides():
    """The website's Advanced fit boxes: None keeps the computed values; set,
    they reach the joint, the nose and the motor thread, and the parts build."""
    from rocketgen.geom import meshes
    base = compute_derived(DesignParams())
    assert base.fit_slip == 0.02 and base.thread["thread_clear"] == 0.25 and base.thread["p"] == 2.5
    r = rocket(joint_clearance=0.18, shoulder_len=15.0, nose_shoulder_len=9.0,
               thread_clearance=0.35, thread_pitch=3.0, thread_turns=4)
    d, t = r.derived, r.derived.thread
    assert d.fit_slip == 0.18 and d.shoulder_od == pytest.approx(d.body_id - 0.36)
    assert (d.shoulder_len, d.nose_shoulder_len) == (15.0, 9.0)
    assert t["thread_clear"] == 0.35 and t["p"] == 3.0
    assert t["cap_top"] - t["z_boss_end"] == pytest.approx(4 * 3.0)
    assert t["r_cap_in"] == pytest.approx(t["r_crest"] + 0.35)
    for p in r.parts:
        assert p.assembled.is_valid and meshes(p.assembled), p.name
    nose = next(q for q in r.parts if q.name == "Nose")
    assert nose.local.bounding_box().size.Z == pytest.approx(9.0 + d.joint_rise + r.params.nose_fineness * d.cal, abs=0.05)
    # A longer body joint alone: the nose follows it (70%).
    assert compute_derived(DesignParams(shoulder_len=20.0)).nose_shoulder_len == pytest.approx(14.0)
