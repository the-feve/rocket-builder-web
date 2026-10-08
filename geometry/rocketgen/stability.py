"""Stability check: CG and CP, margin in calibers (spec §5.3).

Not in the FeatureScript; the website needs it because it is a public tool.

CP is Barrowman's (nose + fins; the body tube adds nothing). CG comes from
the printed parts' own centroids, plus the heaviest common motor of the
chosen size (loaded, the least stable case) and an allowance for the
parachute or streamer and shock cord. Both are measured from the nose tip,
as OpenRocket reports them. A margin under 1 caliber is unstable: the
website shows the preview but won't hand out the STLs.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass

from build123d import CenterOf

from .body import nose_radius_at
from .fins import fin_dimensions
from .params import DATA_DIR

MIN_MARGIN_CAL = 1.0
OVERSTABLE_CAL = 3.0


def load_motor_masses() -> dict[str, dict]:
    """data/web_motor_masses.csv: website-only, not a Variable Studio."""
    with open(DATA_DIR / "web_motor_masses.csv", newline="") as f:
        return {r["Motor"]: {"loaded_g": float(r["loaded_g"]), "example": r["example"]} for r in csv.DictReader(f)}


def recovery_allowance_g(body_od: float) -> float:
    """Parachute or streamer, shroud lines and shock cord. Roughly 6 g at
    the 18 mm minimum diameter, scaling with the body."""
    return round(0.3 * body_od, 1)


@dataclass
class Stability:
    cg: float  # mm from the nose tip
    cp: float
    margin_cal: float
    length: float
    total_mass_g: float
    motor_mass_g: float
    motor_example: str
    recovery_mass_g: float
    status: str  # "unstable", "stable" or "overstable"
    message: str

    @property
    def ok(self) -> bool:
        return self.margin_cal >= MIN_MARGIN_CAL


def nose_cp(shape: str, L: float, R: float, steps: int = 400) -> tuple[float, float]:
    """(CN, X) for the nose: CN = 2 for any shape; X = L - V / A_base."""
    dx = L / steps
    vol = sum(math.pi * nose_radius_at(shape, (i + 0.5) * dx, L, R) ** 2 * dx for i in range(steps))
    return 2.0, L - vol / (math.pi * R * R)


def fin_cp(n: int, root: float, tip: float, span: float, sweep: float, R: float, x_le: float) -> tuple[float, float]:
    """(CN, X) for a fin set, Barrowman. `sweep` is the root-to-tip
    leading-edge offset (aft positive), `x_le` the root leading edge's
    distance from the nose tip."""
    d = 2 * R
    lf = math.hypot(span, sweep + tip / 2 - root / 2)  # mid-chord line
    cn = (1 + R / (span + R)) * (4 * n * (span / d) ** 2) / (1 + math.sqrt(1 + (2 * lf / (root + tip)) ** 2))
    x = (x_le + sweep * (root + 2 * tip) / (3 * (root + tip))
         + (root + tip - root * tip / (root + tip)) / 6)
    return cn, x


def stability(rocket, motor_mass_g: float | None = None, recovery_mass_g: float | None = None) -> Stability:
    """None for either mass means the default: the heaviest common motor of
    the size, and `recovery_allowance_g`."""
    p, d = rocket.params, rocket.derived
    parts = {q.name: q for q in rocket.parts}
    nose = parts["Nose"].assembled
    z_tip = nose.bounding_box().max.Z
    z_tail = 0.0  # the aft segment's tail; the cap and fin tips may hang lower
    R = d.body_od / 2

    # CP
    nose_len = p.nose_fineness * d.cal
    cn_n, x_n = nose_cp(p.nose_shape, nose_len, R)
    fin = fin_dimensions(p, d.cal)
    cn_f, x_f = fin_cp(p.fin_count, fin.root, fin.tip, fin.span, fin.sweep, R, z_tip - (z_tail + fin.root))
    cp = (cn_n * x_n + cn_f * x_f) / (cn_n + cn_f)

    # CG: printed parts (the rod standoff stays on the pad), motor, recovery.
    masses = rocket.mass_g()
    moments = [(m, parts[name].assembled.center(CenterOf.MASS).Z)
               for name, m in masses.items() if name != "Rod_Standoff"]
    motor = load_motor_masses()[p.motor]
    hang = d.thread["hang"]
    motor_g = motor["loaded_g"] if motor_mass_g is None else motor_mass_g
    motor_name = f"loaded {motor['example']}" if motor_mass_g is None else f"{motor_g:g} g motor"
    moments.append((motor_g, -hang + d.mtr_len / 2))  # resting on the cap's face
    rec = recovery_allowance_g(d.body_od) if recovery_mass_g is None else recovery_mass_g
    nose_base = parts["Nose"].placement_z
    moments.append((rec, nose_base - d.cal))  # packed just under the nose shoulder
    total = sum(m for m, _ in moments)
    cg_z = sum(m * z for m, z in moments) / total
    cg = z_tip - cg_z

    margin = (cp - cg) / d.cal
    if margin < MIN_MARGIN_CAL:
        status = "unstable"
        message = (f"Unstable: {margin:.2f} cal with a {motor_name} (at least {MIN_MARGIN_CAL:.1f} is needed). "
                   "Make the fins larger (custom fin size), lengthen the body, or use a lighter motor.")
    elif margin > OVERSTABLE_CAL:
        status = "overstable"
        message = f"Over-stable: {margin:.2f} cal. It will fly, but weathercocks into the wind; smaller fins help."
    else:
        status = "stable"
        message = f"Stable: {margin:.2f} cal with a {motor_name}."
    return Stability(cg=cg, cp=cp, margin_cal=margin, length=z_tip - min(0.0, d.thread["z_lowest"]),
                     total_mass_g=total, motor_mass_g=motor_g, motor_example=motor["example"],
                     recovery_mass_g=rec, status=status, message=message)
