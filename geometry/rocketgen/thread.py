"""Threaded motor cap and the boss it screws onto (threadGeometry,
sweepThreadRidge, buildThreadedBoss, buildThreadedCap).

A truncated-V thread with 45-degree flanks, so the boss (printed tail-down)
and the cap (printed face-down) need no supports. Ridges are swept along a
helix a pitch past each end, then trimmed by a revolved band with a
45-degree lead-in cone. The cap's ridge sits half a pitch off the boss's,
in its groove.
"""

from __future__ import annotations

import math

from build123d import Helix, Solid, Wire

from .geom import intersect, one_solid, revolve, xz_face


def sweep_thread_ridge(t: dict, z0: float, z1: float, r_base: float, male: bool) -> Solid:
    """One ridge from z0 (ridge centre at angle 0) up past z1. Wide side on
    r_base plus a 0.3 mm embed into that surface so the union fuses. Male
    ridges grow outward, female inward; both right-handed."""
    sgn = 1 if male else -1
    e = 0.3
    # The 45-degree flanks run on 0.1 mm past r_base: with the flank's
    # corner exactly on r_base its swept edge lies ON the base cylinder and
    # OpenCascade's union fails (Onshape coped). Same ridge outside r_base.
    e0 = 0.1
    hw = t["b"] / 2 + e0
    prof = xz_face([
        (r_base - sgn * e, z0 - hw),
        (r_base - sgn * e0, z0 - hw),
        (r_base + sgn * t["h"], z0 - t["c"] / 2),
        (r_base + sgn * t["h"], z0 + t["c"] / 2),
        (r_base - sgn * e0, z0 + hw),
        (r_base - sgn * e, z0 + hw),
    ])
    turns = math.ceil((z1 - z0) / t["p"])
    helix = Helix(pitch=t["p"], height=turns * t["p"], radius=r_base + sgn * t["h"] / 2, center=(0, 0, z0))
    # Frenet framing keeps the profile in the axial plane along a helix
    # (checked: swept volume matches Pappus to 0.1%).
    return Solid.sweep(prof, Wire(helix.edges()), is_frenet=True)


def threaded_boss(t: dict) -> Solid:
    """Boss + external thread, to be unioned onto the solid Aft before the
    cavity cut. Buried `overlap` into the tail."""
    boss = revolve([
        (t["boss_id_r"], t["overlap"]),
        (t["r_root"], t["overlap"]),
        (t["r_root"], t["z_boss_end"]),
        (t["boss_id_r"], t["z_boss_end"]),
    ])
    ridge = sweep_thread_ridge(t, t["z_boss_end"] - t["p"], t["cap_top"] + t["p"], t["r_root"], True)
    r_out = t["r_crest"] + 0.5
    band = revolve([
        (t["r_root"] - 1, t["z_boss_end"]),
        (t["r_root"], t["z_boss_end"]),
        (r_out, t["z_boss_end"] + (r_out - t["r_root"])),
        (r_out, t["cap_top"]),
        (t["r_root"] - 1, t["cap_top"]),
    ])
    return one_solid(boss.fuse(intersect(ridge, band)), "thread boss")


def threaded_cap(t: dict) -> Solid:
    """The cap, a separate part, in assembled position: a cup (floor bored
    for the nozzle, 60-degree chamfers on base and top outer edges) with an
    internal thread and vertical grip ribs."""
    z_bottom = t["z_face"] - t["cap_face_t"]
    cup = revolve([
        (t["nose_bore_r"], z_bottom),
        (t["r_cap_out"] - t["base_chamfer"], z_bottom),
        (t["r_cap_out"], z_bottom + t["base_chamfer_h"]),
        (t["r_cap_out"], t["cap_top"] - t["top_chamfer_h"]),
        (t["r_cap_out"] - t["top_chamfer"], t["cap_top"]),
        (t["r_cap_in"], t["cap_top"]),
        (t["r_cap_in"], t["z_face"]),
        (t["nose_bore_r"], t["z_face"]),
    ])

    z0 = t["z_boss_end"] - 1.5 * t["p"]
    ridge = sweep_thread_ridge(t, z0, t["cap_top"] + t["p"], t["r_cap_in"], False)
    r_in = t["r_root"] + t["thread_clear"] - 0.5
    band = revolve([
        (r_in, t["z_face"] - t["cap_face_t"] / 2),
        (t["r_cap_in"] + 1, t["z_face"] - t["cap_face_t"] / 2),
        (t["r_cap_in"] + 1, t["cap_top"]),
        (t["r_cap_in"], t["cap_top"]),
        (r_in, t["cap_top"] - (t["r_cap_in"] - r_in)),
    ])
    cap = cup.fuse(intersect(ridge, band))

    # Grip ribs: half-cylinders standing rib_out proud, both ends cut back
    # along the base and top chamfer cones so the chamfers stay visible.
    rib_c = t["r_cap_out"] + t["rib_out"] - t["rib_r"]
    ribs = None
    for i in range(t["n_ribs"]):
        a = 2 * math.pi * i / t["n_ribs"]
        rib = Solid.make_cylinder(t["rib_r"], t["cap_top"] - z_bottom).translate(
            (rib_c * math.cos(a), rib_c * math.sin(a), z_bottom))
        ribs = rib if ribs is None else ribs.fuse(rib)
    # The cut cones sit 0.01 mm inside the cap's chamfer cones: exactly
    # coincident cones make OpenCascade's union return an invalid solid.
    eps = 0.01
    base_slope = t["base_chamfer_h"] / t["base_chamfer"]
    cone_r0 = t["r_cap_out"] - t["base_chamfer"] - 1
    cone_r1 = t["r_cap_max"] + 1
    base_z0 = z_bottom - base_slope * 1 + eps
    base_cut = revolve([(cone_r0, base_z0), (cone_r1, base_z0), (cone_r1, base_z0 + base_slope * (cone_r1 - cone_r0))])
    top_slope = t["top_chamfer_h"] / t["top_chamfer"]
    top_r0 = t["r_cap_out"] - t["top_chamfer"] - 1
    top_z0 = t["cap_top"] + top_slope * 1 - eps
    top_cut = revolve([(top_r0, top_z0), (cone_r1, top_z0), (cone_r1, top_z0 - top_slope * (cone_r1 - top_r0))])
    ribs = ribs.cut(base_cut).cut(top_cut)
    return one_solid(cap.fuse(ribs), "motor cap")

