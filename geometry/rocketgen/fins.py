"""Fin sizes and planform (finParams, finDimensions, finOutline, finLowestZWithin)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class FinShape(str, Enum):
    CLIPPED_DELTA = "clipped_delta"
    TRAPEZOID = "trapezoid"
    SWEPT = "swept"
    DELTA = "delta"
    RECTANGULAR = "rectangular"


# Caliber ratios, spec.md > Fin shapes and count.
FIN_PARAMS = {
    FinShape.TRAPEZOID: dict(root_cal=2.0, tip_ratio=0.50, span_cal=1.00, sweep_cal=1.00),
    FinShape.CLIPPED_DELTA: dict(root_cal=2.0, tip_ratio=0.25, span_cal=1.10, sweep_cal=1.50),
    FinShape.SWEPT: dict(root_cal=1.8, tip_ratio=0.60, span_cal=1.00, sweep_cal=1.60),
    FinShape.DELTA: dict(root_cal=2.0, tip_ratio=0.0, span_cal=1.00, sweep_cal=2.00),
    FinShape.RECTANGULAR: dict(root_cal=1.5, tip_ratio=1.00, span_cal=0.80, sweep_cal=0.0),
}


@dataclass(frozen=True)
class Fin:
    shape: FinShape
    root: float
    span: float
    tip: float
    sweep: float
    thickness: float
    fillet: float
    fillet_upper: float
    tip_radius: float


def fin_dimensions(params, cal: float) -> Fin:
    """Final fin size. Custom sizes are used as typed; otherwise caliber
    ratios, with span scaled by sqrt(3 / fin count), all times `fin_scale`
    (the website's stability auto-size, 1 in the FeatureScript)."""
    common = dict(
        shape=FinShape(params.fin_shape),
        thickness=params.fin_thickness,
        fillet=params.fin_fillet,
        fillet_upper=params.fin_fillet_upper,
        tip_radius=params.fin_tip_radius,
    )
    if params.custom_fin_size:
        return Fin(root=params.fin_root_chord, span=params.fin_span, tip=params.fin_tip_chord,
                   sweep=params.fin_sweep, **common)
    p = FIN_PARAMS[common["shape"]]
    k = getattr(params, "fin_scale", 1.0)
    root = p["root_cal"] * cal * k
    tip = p["tip_ratio"] * root
    if common["shape"] == FinShape.DELTA:
        tip = max(tip, 3.0)  # zero tip gets a 3 mm flat so it prints
    return Fin(root=root, span=p["span_cal"] * cal * math.sqrt(3 / params.fin_count) * k, tip=tip,
               sweep=p["sweep_cal"] * cal * k, **common)


def fin_outline(fin: Fin) -> list[tuple[float, float]]:
    """Planform as (u, v): u spanwise from the body surface, v axial from
    the tail. A tip hanging below the tail gets a 4 mm flat at its lowest
    corner so the rocket stands level on its fin tips."""
    root_te = (0.0, 0.0)
    root_le = (0.0, fin.root)
    tip_le = (fin.span, fin.root - fin.sweep)
    tip_te = (fin.span, fin.root - fin.sweep - fin.tip)
    if tip_te[1] >= 0:
        return [root_te, root_le, tip_le, tip_te]
    flat_w = min(4.0, fin.span / 2)
    return [root_te, root_le, tip_le, tip_te, (fin.span - flat_w, tip_te[1])]


def fin_lowest_z_within(fin: Fin, body_od: float, wall: float, r: float) -> float:
    """Lowest z of the fin outline within world radius r (0 if the fin never
    reaches below the tail there). Same root embed as the aft build."""
    u_max = r - (body_od / 2 - wall / 2)
    pts = fin_outline(fin)
    z_min = 0.0
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        for q in (a, b):
            if q[0] <= u_max:
                z_min = min(z_min, q[1])
        if (a[0] - u_max) * (b[0] - u_max) < 0:
            z_min = min(z_min, a[1] + (b[1] - a[1]) * (u_max - a[0]) / (b[0] - a[0]))
    return z_min
