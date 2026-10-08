"""Aft segment (buildAftSegment + findFinRootEdges), world coordinates,
z = 0 at the tail.

Build order is the one the Onshape work proved: fins and their root and tip
fillets go onto a plain SOLID cylinder (nothing hollow nearby for a fillet
to wrap onto), then the threaded boss is unioned on, and only then is the
motor bay / bore / socket cavity cut out in one subtraction. The cavity
tool is (solid cylinder) minus (the hollow-tube revolve), so the cavity
math stays the known-good tube profile.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from build123d import Solid

from .fins import Fin, fin_outline
from .geom import (GeometryError, cylinder, edge_dir, edge_faces, extrude_y_symmetric,
                   fillet_checked, is_cylinder_r, one_solid, revolve, rotated_z)
from .params import Derived
from .thread import threaded_boss


@dataclass
class AftResult:
    solid: Solid
    notes: list[str] = field(default_factory=list)


def cavity_tool(d: Derived, seg_len: float) -> Solid:
    stop_r = d.bay_id / 2 - d.stop_depth
    block_top = d.bay_len + d.block_thickness
    stop_ring = [(stop_r, block_top), (stop_r, d.bay_len + d.stop_depth), (d.bay_id / 2, d.bay_len)]
    if d.has_mount:
        # Bulkhead: mount OD at bay_len out at 45 degrees to the body bore
        # (lower surface); motor bore at block_top out at 45 degrees to the
        # body bore at aft_socket_base (upper surface).
        cone_run = (d.body_id - d.mount_od) / 2
        pts = [
            (d.bay_id / 2, 0), (d.mount_od / 2, 0), (d.mount_od / 2, d.bay_len),
            (d.body_id / 2, d.bay_len + cone_run), (d.body_id / 2, 0), (d.body_od / 2, 0),
            (d.body_od / 2, seg_len), (d.body_id / 2, seg_len - d.wall),  # 45-degree socket countersink
            (d.body_id / 2, d.aft_socket_base), (d.bay_id / 2, block_top),
        ]
    else:
        pts = [
            (d.bay_id / 2, 0), (d.body_od / 2, 0), (d.body_od / 2, seg_len),
            (d.body_id / 2, seg_len - d.wall),  # 45-degree socket countersink
            (d.body_id / 2, block_top),
        ]
    hollow = revolve(pts + stop_ring)
    if d.has_mount:
        # Floor closing the annulus at the tail, so the mount is held at both ends.
        emb = d.wall / 2
        hollow = hollow.fuse(revolve([
            (d.mount_od / 2 - emb, 0), (d.body_id / 2 + emb, 0),
            (d.body_id / 2 + emb, d.wall), (d.mount_od / 2 - emb, d.wall),
        ]))
    return cylinder(d.body_od / 2, 0, seg_len).cut(hollow)


def find_fin_root_edges(solid: Solid, d: Derived, fin: Fin) -> tuple[list, list]:
    """Root edges (a planar fin face meeting the OD cylinder), split into
    side (the long verticals) and upper (the leading-edge root corner,
    forward half of the root only, so tail-rim edges on flush-tail fins are
    left out). Re-run before each fillet: every fillet changes the edges
    next to it."""
    side, upper = [], []
    r = d.body_od / 2
    for e, faces in edge_faces(solid).items():
        if len(faces) != 2:
            continue
        cyl = [f for f in faces if is_cylinder_r(f, r)]
        other = [f for f in faces if not is_cylinder_r(f, r)]
        if len(cyl) != 1 or len(other) != 1 or other[0].geom_type.name != "PLANE":
            continue
        # The tube's own tail and top faces are planes too; fin faces are not
        # perpendicular to Z.
        if abs(other[0].normal_at().Z) > 0.999:
            continue
        p0, p1 = e.start_point(), e.end_point()
        if abs(edge_dir(e).Z) > 0.7:
            side.append(e)
        elif min(p0.Z, p1.Z) > fin.root / 2:
            upper.append(e)
    return side, upper


def build_aft(d: Derived, seg_len: float, fin: Fin, fin_count: int) -> AftResult:
    notes: list[str] = []
    outline = fin_outline(fin)

    # The solid tube reaches below the lowest fin point when fins hang past
    # the tail, so the root fillet runs to the trailing edge; trimmed after.
    min_v = min(v for _, v in outline)
    tail_ext = -min_v + 1 if min_v < -0.01 else 0.0
    tube = cylinder(d.body_od / 2, -tail_ext, seg_len)

    # One fin blade straddling the XZ plane, root buried half a wall into
    # the tube so the union fuses with real overlap.
    fin_embed = d.wall / 2
    blade = extrude_y_symmetric([(d.body_od / 2 - fin_embed + u, v) for u, v in outline], fin.thickness)

    if fin.tip_radius > 0.01:
        cx, cz = d.body_od / 2 - fin_embed + fin.span, fin.root - fin.sweep
        tip_edges = [e for e in blade.edges()
                     if abs(e.center().X - cx) < 1e-6 and abs(e.center().Z - cz) < 1e-6]
        if not tip_edges:
            raise GeometryError("The fin tip corner edge couldn't be found to round it (geometry-selection bug).")
        try:
            blade = blade.fillet(fin.tip_radius, tip_edges)
        except Exception as ex:
            raise GeometryError("The fin tip corner radius couldn't be built. Reduce Tip corner radius, or set it to 0.") from ex
        notes.append(f"Tip corner radius built: {fin.tip_radius:.1f} mm.")

    one = blade
    if d.has_mount:
        # One rib behind each fin, tying the mount to the body wall; its top
        # runs at 45 degrees through the middle of the conical bulkhead.
        emb = d.wall / 2
        r_in, r_out = d.mount_od / 2 - emb, d.body_id / 2 + emb
        top_in = d.bay_len + (d.wall + d.block_thickness) / 2 - emb
        rib = extrude_y_symmetric([(r_in, 0), (r_out, 0), (r_out, top_in + (r_out - r_in)), (r_in, top_in)], fin.thickness)
        one = one.fuse(rib)

    body = tube
    for i in range(fin_count):
        body = body.fuse(rotated_z(one, i * 360 / fin_count))
    body = one_solid(body, "aft tube + fins")

    if fin.fillet > 0.01 or fin.fillet_upper > 0.01:
        # Slices through the fin root must keep at least the solid tube's area.
        tube_area = math.pi * (d.body_od / 2) ** 2
        z_checks = [fin.root * k for k in (0.1, 0.5, 0.9)] + [fin.root - 0.5, fin.root + 0.3, fin.root + 1.5]
        side, _ = find_fin_root_edges(body, d, fin)
        if not side:
            raise GeometryError("No fin root side edges were found to fillet (geometry-selection bug).")
        if fin.fillet > 0.01:
            try:
                body = fillet_checked(body, fin.fillet, side, z_checks, tube_area, "root fillet")
            except Exception as ex:
                raise GeometryError("The fin root fillet couldn't be built at this radius. Reduce Root fillet radius, or set it to 0.") from ex
        if fin.fillet_upper > 0.01:
            # Leading-edge root corner, re-found after the main fillet. Non-fatal.
            # OpenCascade has not built this one yet (see report.md): after
            # the main fillet the corner is a chain of split edges and the
            # fillet fails; one combined fillet "succeeds" but drops slices.
            _, upper = find_fin_root_edges(body, d, fin)
            if not upper:
                notes.append("Root fillet radius (leading edge): no leading-edge root edge found after the main root fillet -- left sharp.")
            else:
                try:
                    body = fillet_checked(body, fin.fillet_upper, upper, z_checks, tube_area, "leading-edge root fillet")
                except Exception:
                    notes.append(f"Root fillet radius (leading edge) couldn't be built ({len(upper)} edges found) -- left sharp.")

    if tail_ext > 0:
        trimmed = None
        for attempt in range(2):
            trim_r = d.body_od / 2 + attempt * 0.05
            try:
                cand = one_solid(body.cut(cylinder(trim_r, -tail_ext - 1, 0)), "tail trim")
                if cand.is_valid:
                    trimmed = cand
                    if attempt:
                        notes.append("Tail trim needed the 0.05 mm fallback (small step at the fin trailing edge).")
                    break
            except Exception:
                pass
        if trimmed is None:
            raise GeometryError("Couldn't trim the tube extension below the tail after the root fillet. Try a different Root fillet radius.")
        body = trimmed

    body = one_solid(body.fuse(threaded_boss(d.thread)), "aft + thread boss")
    body = one_solid(body.cut(cavity_tool(d, seg_len)), "aft cavity cut")
    return AftResult(body, notes)
