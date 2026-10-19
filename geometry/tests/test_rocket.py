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

from rocketgen.body import body_segment, nose_cone, nose_radius_at
from rocketgen.build import build_rocket
from rocketgen.fins import FinShape
from rocketgen.geom import as_shape, intersect, slice_area
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
    assert d.shoulder_od == pytest.approx(18.04)  # 0.18 mm per side (web_fits)
    assert d.shoulder_len == pytest.approx(0.75 * 21.4 - 4)
    assert d.joint_rise == pytest.approx(1.68)
    assert d.inner_taper_rise == pytest.approx((9.2 - (9.02 - 1.5)) / math.tan(math.radians(8)))
    assert d.zmax == 195


@pytest.mark.parametrize("shape,hang", [
    (FinShape.CLIPPED_DELTA, 10.0),  # HANDOFF: Clipped delta -> hang 10, bay 60
    (FinShape.TRAPEZOID, 10.0),
    # Swept: the cap's top sits 1 mm below the fin's lower edge at the cap's
    # outer radius, so a slimmer cap hangs less. 13.41 with the FeatureScript's
    # 1.6 mm wall and 0.6 mm ribs; 12.76 with the website's 1.2 / 0.4 (2026-10-16).
    (FinShape.SWEPT, 12.76),
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
    assert [p.name for p in r.parts] == ["Aft", "Top_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]
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
        (d.shoulder_od / 2 - d.wall, 0), (d.shoulder_od / 2 - d.shoulder_chamfer, 0),
        (d.shoulder_od / 2, d.shoulder_chamfer), (d.shoulder_od / 2, sh),
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
    ("none", ["Aft", "Top_Seg", "Nose", "Motor_Cap"]),
    ("aft_only", ["Aft", "Top_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]),
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
    assert [p.name for p in r.parts] == ["Aft", "Seg_2", "Top_Seg", "Nose", "Motor_Cap", "Rod_Standoff"]
    d = r.derived
    plain = body_segment(d, r.seg_lens[1]).volume
    assert r.parts[1].volume > plain + 20  # the forward lug


def test_anchor_strap_is_inside_the_bore():
    from rocketgen.anchor import anchor_strap_geometry
    r = rocket()
    d = r.derived
    seg = r.parts[1]
    assert seg.name == "Top_Seg" and r.strap["part"] == "Top_Seg"
    plain = body_segment(d, r.seg_lens[1]).volume
    assert seg.volume > plain + 20
    # Nothing added outside the body OD.
    bb = seg.assembled.bounding_box()
    assert max(bb.max.X, -bb.min.X, bb.max.Y, -bb.min.Y) <= d.body_od / 2 + 1e-3
    s = anchor_strap_geometry(d)
    assert r.seg_lens[-1] >= s["sec_len"] - 1e-9  # a short leftover is taken from the piece below


# One-piece bodies (2026-10-19): the kits' Starter (M18 300 mm) and Mini
# (M13 190 mm) on a 256 mm printer, and a fat M18 with the inner motor mount.
ONE_PIECE = [
    dict(motor="M18", print_max_height=256, fin_shape=FinShape.TRAPEZOID, body_length=224.3),
    dict(motor="M13", print_max_height=256, fin_shape=FinShape.TRAPEZOID, body_length=129.3, forward_lug_frac=0.95),
    dict(motor="M18", print_max_height=256, body_od_override=33.7, body_length=180.0),
]


@pytest.mark.parametrize("i", range(len(ONE_PIECE)))
def test_one_piece_body_carries_the_strap(i):
    """A body that fits the printer is one print, the fin can, with the
    shock-cord strap in its top (owner, 2026-10-19: no separate anchor
    section). The strap sits in the plain bore, its top at least `gap`
    under the nose's shoulder, and the cord slot behind the bar is open from
    the part's top edge to below the strap; every part is sound (meshed,
    not just is_valid) and nothing overlaps."""
    from build123d import Solid

    from rocketgen.anchor import anchor_strap_geometry
    from rocketgen.geom import meshes
    kw = dict(ONE_PIECE[i])
    r = rocket(kw.pop("fin_shape", FinShape.CLIPPED_DELTA), **kw)
    d = r.derived
    names = [p.name for p in r.parts]
    assert names[:2] == ["Aft", "Nose"] and "Anchor_Seg" not in names and len(r.seg_lens) == 1
    assert r.seg_lens == [r.params.body_length]
    for p in r.parts:
        assert p.assembled.is_valid and len(p.assembled.solids()) == 1 and meshes(p.assembled), p.name
    for a in range(len(r.parts)):
        for b in range(a + 1, len(r.parts)):
            x = as_shape(r.parts[a].assembled.intersect(r.parts[b].assembled))
            assert x is None or x.volume < 0.01, f"{names[a]} overlaps {names[b]}"
    s = anchor_strap_geometry(d)
    st = r.strap
    aft, nose = r.parts[0], next(p for p in r.parts if p.name == "Nose")
    assert st["part"] == "Aft"
    assert st["z_top"] == pytest.approx(nose.assembled.bounding_box().min.Z - s["gap"], abs=1e-6)
    assert st["z_bot"] >= d.aft_socket_base + s["z_spring"] - 1e-6  # well above the motor stop
    # The strap is there: the bore is partly filled at mid-strap, not above or below it.
    ri = d.body_id / 2
    inner = math.pi * ((ri + d.wall / 2) ** 2 - ri ** 2)

    def inside_area(z):
        cut = as_shape(aft.assembled.intersect(Solid.make_cylinder(ri + d.wall / 2, 0.2).translate((0, 0, z))))
        return cut.volume / 0.2

    assert inside_area((st["z_bot"] + st["z_top"]) / 2) > inner + 5
    for z in (st["z_bot"] - 3, st["z_top"] + 0.5):
        assert inside_area(z) == pytest.approx(inner, abs=0.5)
    # The cord slot (strap at 90 degrees: on +Y) is open from the top edge down past the strap.
    y = ri - s["hole_depth"] / 2
    top = r.seg_lens[0]
    probe = Solid.make_box(1, 1, top - st["z_bot"] + 6).translate((-0.5, y - 0.5, st["z_bot"] - 5))
    hit = aft.assembled.intersect(probe)
    assert hit is None or as_shape(hit) is None or as_shape(hit).volume < 1e-6


def test_body_parts_split():
    """The body is one print when it fits the printer; otherwise the aft
    part is the printer's height and the top part (the strap) at least
    sec_len, taken from the piece below if the leftover is shorter. The
    printed lengths always add up to body_length."""
    from rocketgen.anchor import anchor_strap_geometry
    from rocketgen.build import plan_segments, seg_part_name
    p = DesignParams(print_max_height=200)
    d = compute_derived(p)
    sec = anchor_strap_geometry(d)["sec_len"]
    assert plan_segments(p.with_(body_length=195.0), d) == [195.0]
    two = plan_segments(p.with_(body_length=200.0), d)
    assert two == pytest.approx([200.0 - sec, sec])
    assert plan_segments(p.with_(body_length=300.0), d) == pytest.approx([195.0, 105.0])
    many = plan_segments(p.with_(body_length=600.0), d)
    assert len(many) == 4 and sum(many) == pytest.approx(600.0) and max(many) <= 195.0 + 1e-9
    assert many[-1] >= sec
    assert [seg_part_name(i, 4) for i in range(4)] == ["Aft", "Seg_2", "Seg_3", "Top_Seg"]
    assert seg_part_name(0, 1) == "Aft"


def test_one_piece_body_too_short_for_the_strap():
    from rocketgen.anchor import anchor_strap_geometry
    from rocketgen.build import plan_rocket
    from rocketgen.geom import GeometryError
    p = DesignParams(motor="M18", fin_shape=FinShape.TRAPEZOID)
    need = anchor_strap_geometry(compute_derived(p))["aft_len"]
    plan_rocket(p.with_(body_length=need))
    with pytest.raises(GeometryError, match="shock-cord strap"):
        plan_rocket(p.with_(body_length=need - 1))


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


@pytest.mark.parametrize("motor", ["M13", "M18", "M24", "M24L", "M29"])
def test_anchor_strap_fits_the_shock_cord(motor):
    """Elastic shock cord (params.SHOCK_CORDS) goes down the slot behind the
    bar: a round cord, or a flat one doubled back, across a wide enough
    stretch of the slot; and the open bore in front of the bar leaves room
    for the parachute to come out."""
    from rocketgen.anchor import anchor_strap_geometry
    from rocketgen.params import CORD_PRINT_MARGIN, shock_cord
    d = compute_derived(DesignParams(motor=motor))
    s = anchor_strap_geometry(d)
    cord = shock_cord(d.mtr_d)
    ri = d.body_id / 2
    back = s["front"] + s["t"]  # the bar's back face, from the axis

    def width_at_depth(depth):  # across the slot, where it is at least `depth` deep
        return 2 * math.sqrt(max(0.0, ri ** 2 - (back + depth) ** 2))

    assert s["hole_depth"] >= cord["round_d"] + CORD_PRINT_MARGIN - 1e-9
    assert width_at_depth(cord["round_d"]) >= cord["round_d"] + 1.0
    assert width_at_depth(2 * cord["flat_t"]) >= cord["flat_w"] + 1.0
    assert ri + s["front"] >= 0.55 * d.body_id  # bore left in front of the bar


@pytest.mark.parametrize("motor", ["M13", "M18", "M24", "M29"])
def test_nose_tie_bar_has_room_for_the_cord(motor):
    """A round 3 mm cord bent round the tie bar (up one side, over the top,
    down the other) clears the nose; the nose is one sound solid and every
    slice of its shoulder keeps at least the plain shoulder wall."""
    from build123d import Plane, Solid
    d = compute_derived(DesignParams(motor=motor))
    nose = nose_cone(d, "tangent_ogive", 3.0 * d.cal)
    assert nose.is_valid and len(list(nose.solids())) == 1
    r_cord, bend = 1.5, 3.0  # cord radius; bend radius of its centre line round the bar (2 x 2 mm, centre z = 1)
    torus = Solid.make_torus(bend, r_cord, Plane.YZ).translate((0, 0, 1.0))
    top = intersect(torus, Solid.make_box(10, 40, 20).translate((-5, -20, 1.0)))
    legs = [Solid.make_cylinder(r_cord, 10).translate((0, y, -9.0)) for y in (-bend, bend)]
    probe = top.fuse(*legs)
    hit = nose.intersect(probe)
    assert hit is None or as_shape(hit).volume < 0.01, f"cord probe hits the nose ({as_shape(hit).volume:.2f} mm3)"
    sh_r_out, sh_r_in = d.shoulder_od / 2, d.shoulder_od / 2 - d.wall
    annulus = math.pi * (sh_r_out ** 2 - sh_r_in ** 2)
    for z in [0.5 + i * (d.nose_shoulder_len - 1) / 8 for i in range(9)]:
        assert slice_area(nose, z) > annulus - 0.05, f"nose shoulder slice at z = {z:.2f}"


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


def test_lug_bore_is_4mm_for_eighth_inch_rod():
    # Owner, 2026-10-18: the 3.775 mm bore was a little too snug on a 1/8 in rod.
    from build123d import Solid
    from rocketgen.lugs import LUG_BORE_CLEARANCE, lug_geometry
    d = compute_derived(DesignParams())
    lug = lug_geometry(d, 3.175, True, 15.0)
    assert 2 * lug["bore_r"] == pytest.approx(4.0, abs=1e-9)
    assert 2 * lug_geometry(d, 6.35, True, 15.0)["bore_r"] == pytest.approx(6.35 + 2 * LUG_BORE_CLEARANCE)
    assert lug["standoff_ri"] == pytest.approx(3.175 / 2 - d.fit_press)  # the clip still grips the rod
    # The built aft (both lugs on it): a 3.98 mm rod along the rod line
    # passes clean through, a 4.1 mm one doesn't.
    r = rocket()
    aft = r.parts[0].assembled
    a = math.radians(180 / r.params.fin_count)
    c = (lug["center_r"] * math.cos(a), lug["center_r"] * math.sin(a))
    h = aft.bounding_box().max.Z + 10

    def rod(dia):
        return Solid.make_cylinder(dia / 2, h + 10).translate((c[0], c[1], -10))

    def overlap(dia):
        x = as_shape(aft.intersect(rod(dia)))
        return 0.0 if x is None else x.volume

    assert overlap(3.98) < 1e-6
    assert overlap(4.1) > 0.01


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


def test_nose_weight_moves_the_cg_forward():
    """Clay in the nose (DesignParams.nose_weight_g, the stability lessons):
    the CG moves toward the nose, the score goes up, the rocket is heavier,
    and it matches the advice's own clay estimate (Balance.predict nose_g)."""
    import copy

    from rocketgen.stability import Balance
    r = rocket()
    b0 = Balance(r)
    s0 = b0.check()
    b10 = b0.with_nose_weight(10)
    s10 = b10.check()
    assert s10.cg < s0.cg and s10.margin_cal > s0.margin_cal + 0.1
    assert s10.total_mass_g == pytest.approx(s0.total_mass_g + 10)
    assert b10.printed_mass_g == pytest.approx(b0.printed_mass_g + 10) and b10.nose_weight_g == 10
    assert s10.margin_cal == pytest.approx(b0.predict(nose_g=10), abs=1e-6)
    assert b0.check().margin_cal == s0.margin_cal and b0.with_nose_weight(0) is b0  # the cached balance is untouched
    # From the params (the CLI / build_stable path) it's the same.
    r10 = copy.copy(r)
    r10.params = r.params.with_(nose_weight_g=10)
    assert Balance(r10).check().margin_cal == pytest.approx(s10.margin_cal)
    # It slides with the nose when the body is made longer.
    assert b10.predict_length(100) > b0.predict_length(100)


def test_flight_sim_matches_the_motor_picker():
    # M18, 52 g without motor, 20.8 mm: the HTML picker's numbers.
    from rocketgen.flight import motors_for, pick, simulate
    flights = {f.motor.code: f for f in (simulate(m, 52, 20.8) for m in motors_for("M18"))}
    assert flights["C6"].apogee == pytest.approx(357, abs=3) and flights["C6"].ok
    assert not flights["A8"].ok and "Too heavy for this motor" in flights["A8"].problems
    assert pick(list(flights.values()), 150).motor.code == "B6"


# ---- overall height (the website's beginner mode) --------------------------

@pytest.mark.parametrize("shape,kw", [
    (FinShape.CLIPPED_DELTA, {}),                                     # default M18, aft + top part
    (FinShape.TRAPEZOID, {"print_max_height": 256}),                  # one-piece body (strap in the aft)
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
    assert base.fit_slip == 0.18 and base.fit_nose == 0.15
    assert base.thread["thread_clear"] == 0.25 and base.thread["p"] == 2.5
    r = rocket(joint_clearance=0.2, nose_clearance=0.17, shoulder_len=15.0, nose_shoulder_len=9.0,
               thread_clearance=0.35, thread_pitch=3.0, thread_turns=4)
    d, t = r.derived, r.derived.thread
    assert d.fit_slip == 0.2 and d.shoulder_od == pytest.approx(d.body_id - 0.4)
    assert d.fit_nose == 0.17 and d.nose_shoulder_od == pytest.approx(d.body_id - 0.34)
    assert (d.shoulder_len, d.nose_shoulder_len) == (15.0, 9.0)
    assert t["thread_clear"] == 0.35 and t["p"] == 3.0
    assert t["cap_top"] - t["z_boss_end"] == pytest.approx(4 * 3.0)
    assert t["r_cap_in"] == pytest.approx(t["r_crest"] + 0.35)
    for p in r.parts:
        assert p.assembled.is_valid and meshes(p.assembled), p.name
    nose = next(q for q in r.parts if q.name == "Nose")
    assert nose.local.bounding_box().size.Z == pytest.approx(9.0 + d.nose_joint_rise + r.params.nose_fineness * d.cal, abs=0.05)
    # A longer body joint alone: the nose follows it (70%).
    assert compute_derived(DesignParams(shoulder_len=20.0)).nose_shoulder_len == pytest.approx(14.0)


def test_launch_profile_shows_unsafe_flights():
    """The launch page's flight: stable rockets fly as before; a negative
    margin tumbles (spins, barely climbs, crashes); a margin under 1 wobbles
    and flies lower; a too-heavy rocket crawls off the rod into the wind."""
    from rocketgen import flight as fl
    b6 = next(m for m in fl.load_flight_motors() if m.code == "B6")
    stable = fl.launch_profile(b6, 50, 23, 12, fl.WIND_MS)
    assert fl.launch_profile(b6, 50, 23, 12, fl.WIND_MS, margin_cal=1.5, length_mm=300)["path"] == stable["path"]
    assert not stable["dangers"]
    tumble = fl.launch_profile(b6, 50, 23, 12, fl.WIND_MS, margin_cal=-0.5, length_mm=300)
    assert tumble["turns"] >= 2 and tumble["apogee_m"] < 0.3 * stable["apogee_m"]
    assert {"tumble", "crash"} <= {d["kind"] for d in tumble["dangers"]}
    wobble = fl.launch_profile(b6, 50, 23, 12, fl.WIND_MS, margin_cal=0.5, length_mm=300)
    assert wobble["apogee_m"] < stable["apogee_m"] and "wobble" in {d["kind"] for d in wobble["dangers"]}
    a8 = next(m for m in fl.load_flight_motors() if m.code == "A8")
    heavy = fl.launch_profile(a8, 80, 23, 12, fl.WIND_MS, margin_cal=1.5, length_mm=300)
    assert {"slow", "windturn"} <= {d["kind"] for d in heavy["dangers"]} and heavy["landing_m"] < 0  # tipped upwind


def test_launch_profile_angle_streamer_and_forces():
    """Classroom options on the launch page: a tilted rod sends the rocket
    downwind (into the wind when negative) and leaves the vertical flight
    unchanged at 0°; a streamer brings a light rocket down at 6-9 m/s, faster
    than a chute, and drifts less; the per-point forces add up (thrust while
    burning, drag about equal to the weight under the chute)."""
    from rocketgen import flight as fl
    b6 = next(m for m in fl.load_flight_motors() if m.code == "B6")
    base = fl.launch_profile(b6, 50, 23, 12, 0.0)
    assert fl.launch_profile(b6, 50, 23, 12, 0.0, angle_deg=0.0)["path"] == base["path"]
    tilt = fl.launch_profile(b6, 50, 23, 12, 0.0, angle_deg=20)
    into = fl.launch_profile(b6, 50, 23, 12, 0.0, angle_deg=-20)
    assert tilt["landing_m"] > 30 and into["landing_m"] < -30 and abs(base["landing_m"]) < 1
    assert tilt["apogee_m"] < base["apogee_m"] and tilt["path"][0][3:] == ["rod", 20.0]  # on the rod, tilted
    assert tilt["events"]["rod"]["speed_ms"] >= base["events"]["rod"]["speed_ms"] - 0.3
    # Streamers: the assumed Cd gives the usual 6-9 m/s for light rockets.
    assert 6 <= fl.streamer_descent_rate(30, fl.streamer_size("M13")) <= 9
    assert 6 <= fl.streamer_descent_rate(80, fl.streamer_size("M24")) <= 9
    assert fl.streamer_size("M18") == (1, 24) and fl.streamer_size("M29") == (2, 36)
    chute = fl.launch_profile(b6, 25, 18, 12, fl.WIND_MS)
    stre = fl.launch_profile(b6, 25, 18, 12, fl.WIND_MS, streamer_in=(1, 24))
    assert stre["streamer_in"] == [1, 24] and stre["chute_in"] is None
    assert 6 <= stre["events"]["landing"]["speed_ms"] <= 9.5 < 9.5 + chute["events"]["landing"]["speed_ms"]
    assert stre["events"]["landing"]["speed_ms"] > chute["events"]["landing"]["speed_ms"]
    assert abs(stre["landing_m"]) < abs(chute["landing_m"])  # comes down sooner, drifts less
    # Forces and graph samples, one per path point.
    S, cols = base["samples"], base["sample_cols"]
    assert len(S) == len(base["path"]) and cols == list(fl.SAMPLE_COLS)
    i = {c: k for k, c in enumerate(cols)}
    burn = [s for p, s in zip(base["path"], S) if p[3] == "boost"]
    assert burn and all(s[i["thrust_n"]] > 0 for s in burn) and max(s[i["accel_ms2"]] for s in burn) > 50
    coast = [s for p, s in zip(base["path"], S) if p[3] == "coast"]
    assert all(s[i["thrust_n"]] == 0 and s[i["accel_ms2"]] < -9 for s in coast)
    assert 50 + b6.mass_g - b6.prop_g < S[0][i["mass_g"]] < 50 + b6.mass_g and S[-1][i["mass_g"]] == pytest.approx(50 + b6.mass_g - b6.prop_g, abs=0.2)
    down = [s for p, s in zip(base["path"], S) if p[3] == "chute"][-5:]
    for s in down:  # steady descent: drag holds up the weight
        assert s[i["drag_h_n"]] == pytest.approx(s[i["weight_n"]], rel=0.05) and abs(s[i["accel_ms2"]]) < 0.5
    top = max(range(len(S)), key=lambda k: S[k][i["speed_ms"]])
    assert S[top][i["speed_ms"]] == pytest.approx(fl.simulate(b6, 50, 23).max_speed, rel=0.03)


def test_motor_cap_lip_covers_the_casing():
    """The cap's retention lip reaches 1.75 mm in from the motor's OD (inside
    the ~2.5 mm cardboard casing wall), so the nozzle hole is the motor
    diameter less 3.5 mm."""
    from rocketgen.params import CAP_LIP, DesignParams, compute_derived
    assert CAP_LIP == 1.75
    for motor, mtr_d in (("M13", 13), ("M18", 18), ("M24", 24), ("M29", 29)):
        d = compute_derived(DesignParams(motor=motor))
        assert abs(2 * d.thread["nose_bore_r"] - (mtr_d - 3.5)) < 1e-6



def test_printed_fit_defaults():
    """Fits from the fit-test prints (owner, 2026-10-16/18: the CAD 0.02 mm
    printed far too tight). M13's short nose shoulder gets the short pair."""
    from rocketgen.params import web_fits
    for motor, joint, nose in (("M13", 0.16, 0.14), ("M18", 0.18, 0.15), ("M24", 0.18, 0.15), ("M29", 0.18, 0.15)):
        d = compute_derived(DesignParams(motor=motor))
        assert (d.fit_slip, d.fit_nose) == (joint, nose), motor
        assert web_fits(d.nose_shoulder_len) == (joint, nose)
        assert d.shoulder_od == pytest.approx(d.body_id - 2 * joint)
        assert d.nose_shoulder_od == pytest.approx(d.body_id - 2 * nose)
        assert d.shoulder_chamfer == 0.5


def test_shoulder_chamfer():
    """The shoulders' bed edge is chamfered 0.5 mm so elephant's foot doesn't bind."""
    from build123d import Solid
    r = rocket(motor="M18")
    d = r.derived
    for name, sh_od in (("Nose", d.nose_shoulder_od), ("Top_Seg", d.shoulder_od)):
        part = next(p for p in r.parts if p.name == name).local
        bb = part.bounding_box()
        z0 = bb.min.Z
        bottom = as_shape(part.intersect(Solid.make_box(100, 100, 0.1).translate((-50, -50, z0))))
        mid = as_shape(part.intersect(Solid.make_box(100, 100, 0.1).translate((-50, -50, z0 + 2))))
        assert bottom.bounding_box().size.X == pytest.approx(sh_od - 0.8, abs=0.05), name  # top of the 0.1 mm slab
        assert mid.bounding_box().size.X == pytest.approx(sh_od, abs=0.05), name


def test_ejection_delay_rounds_down():
    """The suggested delay is the longest one that isn't longer than the
    coast (Apogee, Peak of Flight #520: late ejection is the dangerous one)."""
    from rocketgen.flight import motors_for, simulate
    for size in ("M13", "M18", "M24"):
        for m in motors_for(size):
            f = simulate(m, 40 if size != "M24" else 70, 18)
            shorter = [d for d in m.delays if d <= f.coast + 1e-9]
            assert f.delay == (max(shorter) if shorter else min(m.delays)), m.code
