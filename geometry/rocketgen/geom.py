"""Small build123d helpers shared by the part builders.

Profiles are lists of (r, z) points in the XZ half-plane (x = radius, y = 0),
revolved about world Z, matching the FeatureScript's `profilePlane`.
"""

from __future__ import annotations

import math
from collections import defaultdict

from build123d import Axis, Edge, Face, GeomType, Solid, Vector, Wire

Z_AXIS = Axis.Z


def xz_face(pts, y: float = 0.0) -> Face:
    """Closed polygon in the plane y = const, from (x, z) points."""
    return Face(Wire.make_polygon([Vector(x, y, z) for x, z in pts], close=True))


def revolve(pts) -> Solid:
    """sketchClosedPolygon + opRevolve 360 about Z."""
    return Solid.revolve(xz_face(pts), 360, Z_AXIS)


def cylinder(r: float, z0: float, z1: float) -> Solid:
    return revolve([(0, z0), (r, z0), (r, z1), (0, z1)])


def extrude_y_symmetric(pts, thickness: float) -> Solid:
    """XZ polygon extruded thickness/2 each way along Y (fins, ribs, tie bar)."""
    return Solid.extrude(xz_face(pts, -thickness / 2), Vector(0, thickness, 0))


def solids_of(shape) -> list[Solid]:
    return list(shape.solids()) if hasattr(shape, "solids") else [shape]


def one_solid(shape, what: str) -> Solid:
    """The FeatureScript unions everything into one body per part; check it."""
    s = solids_of(shape)
    if len(s) != 1:
        raise GeometryError(f"{what}: expected 1 solid, got {len(s)}")
    return s[0]


def edge_faces(solid) -> dict:
    """Edge -> list of adjacent faces."""
    out = defaultdict(list)
    for f in solid.faces():
        for e in f.edges():
            out[e].append(f)
    return out


def is_cylinder_r(face: Face, r: float, tol: float = 0.01) -> bool:
    if face.geom_type != GeomType.CYLINDER:
        return False
    # Face.radius can be None on some cylinders; ask OpenCascade directly.
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    return abs(BRepAdaptor_Surface(face.wrapped).Cylinder().Radius() - r) < tol


def edge_dir(e: Edge) -> Vector:
    d = e.end_point() - e.start_point()
    return d.normalized() if d.length > 1e-9 else Vector(0, 0, 0)


def rotated_z(shape, degrees: float):
    return shape.rotate(Z_AXIS, degrees)


class GeometryError(Exception):
    """A design that can't be built; message is meant for the user (regenError)."""


def arc3(p0, pm, p1) -> Edge:
    return Edge.make_three_point_arc(Vector(*p0), Vector(*pm), Vector(*p1))


def deg(x: float) -> float:
    return math.radians(x)


def as_shape(result):
    """build123d booleans can return a ShapeList; collapse it to one shape."""
    from build123d import Compound, ShapeList
    if isinstance(result, ShapeList):
        return result[0] if len(result) == 1 else Compound(list(result))
    return result


def intersect(a, b):
    return as_shape(a.intersect(b))


def slice_area(solid, z: float, h: float = 0.02) -> float:
    """Cross-section area at height z (volume of a thin slab / its height)."""
    sec = as_shape(solid.intersect(Solid.make_cylinder(1e4, h).translate((0, 0, z - h / 2))))
    return 0.0 if sec is None else sec.volume / h


def fillet_checked(solid, radius: float, edges, z_checks, min_area: float, what: str):
    """Fillet concave edges, then reject results OpenCascade reports as
    valid but are wrong: a concave fillet only adds material, so the
    volume must grow and no checked slice may drop below min_area (seen:
    a whole slice of the tube missing after a multi-edge fillet)."""
    out = one_solid(solid.fillet(radius, edges), what)
    if not out.is_valid or out.volume < solid.volume:
        raise GeometryError(f"{what}: fillet result is not a sound solid")
    for z in z_checks:
        if slice_area(out, z) < min_area - 0.05:
            raise GeometryError(f"{what}: fillet result is missing material at z = {z:.1f} mm")
    return out


def try_fillet(solid, radius: float, edges):
    """Cosmetic fillet (FeatureScript `try silent`): returns the filleted
    solid, or None if it can't be built or comes back unsound. A fillet
    changes the volume by less than radius^2 per mm of edge, so a bigger
    change means OpenCascade returned something wrong."""
    edges = list(edges)
    if not edges:
        return None
    try:
        out = solid.fillet(radius, edges)
        out = one_solid(out, "fillet")
    except Exception:
        return None
    bound = radius * radius * sum(e.length for e in edges) + 1e-6
    # Mesh first: some faces only show up as invalid once tessellated.
    if not meshes(out) or not out.is_valid or abs(out.volume - solid.volume) > bound:
        return None
    return out


def meshes(solid) -> bool:
    """Every face tessellates. Catches fillet faces OpenCascade accepts but
    can't mesh (seen on a lug top round), which would break STL export."""
    try:
        for f in solid.faces():
            f.tessellate(0.1, 0.3)
    except Exception:
        return False
    return True


def xy_wire_edges(items) -> Wire:
    """Wire in a z = const plane from ("line", p0, p1) / ("arc", p0, pm, p1)
    items, points given as (x, y, z)."""
    edges = []
    for it in items:
        if it[0] == "line":
            edges.append(Edge.make_line(Vector(*it[1]), Vector(*it[2])))
        else:
            edges.append(arc3(it[1], it[2], it[3]))
    return Wire(edges)
