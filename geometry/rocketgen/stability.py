"""Stability check: CG and CP, margin in calibers (spec §5.3).

Not in the FeatureScript; the website needs it because it is a public tool.

CP is Barrowman's (nose + fins; the body tube adds nothing). CG comes from
the printed parts' own centroids, plus a loaded motor (by default the
heaviest of the bay size: the least stable case) and an allowance for the
parachute or streamer and shock cord. Both are measured from the nose tip,
as OpenRocket reports them. A margin under 1 caliber is unstable: the
website shows the preview but won't hand out the STLs.

`build_stable` is the website's auto-size: standard (non-custom) fins are
scaled up until the rocket is stable with the heaviest motor of its size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from build123d import CenterOf

from .body import nose_radius_at
from .build import Rocket, build_rocket
from .fins import fin_dimensions, fin_outline
from .flight import Motor, heaviest
from .params import MATERIALS, DesignParams

MIN_MARGIN_CAL = 1.0
OVERSTABLE_CAL = 3.0
AUTO_SIZE_TARGET_CAL = 1.15  # aim a little above the limit; the fin estimate is approximate
MAX_FIN_SCALE = 2.5


def recovery_allowance_g(body_od: float) -> float:
    """Parachute or streamer, shroud lines and shock cord. Roughly 6 g at
    the 18 mm minimum diameter, scaling with the body."""
    return round(0.3 * body_od, 1)


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


def rocket_cp(params: DesignParams, cal: float, body_od: float, z_tip: float) -> float:
    R = body_od / 2
    cn_n, x_n = nose_cp(params.nose_shape, params.nose_fineness * cal, R)
    fin = fin_dimensions(params, cal)
    cn_f, x_f = fin_cp(params.fin_count, fin.root, fin.tip, fin.span, fin.sweep, R, z_tip - fin.root)
    return (cn_n * x_n + cn_f * x_f) / (cn_n + cn_f)


@dataclass
class Stability:
    cg: float  # mm from the nose tip
    cp: float
    margin_cal: float
    length: float
    total_mass_g: float
    motor_mass_g: float
    motor: str
    recovery_mass_g: float
    status: str  # "unstable", "stable" or "overstable"
    message: str

    @property
    def ok(self) -> bool:
        return self.margin_cal >= MIN_MARGIN_CAL


class Balance:
    """A built rocket's CP and printed-part moments, so the margin for any
    motor and recovery mass is cheap (no more OpenCascade calls)."""

    def __init__(self, rocket: Rocket):
        p, d = rocket.params, rocket.derived
        parts = {q.name: q for q in rocket.parts}
        self.params = p
        self.cal = d.cal
        self.body_od = d.body_od
        self.z_tip = parts["Nose"].assembled.bounding_box().max.Z  # the tail is z = 0
        self.length = self.z_tip - min(0.0, d.thread["z_lowest"])
        self.cp = rocket_cp(p, d.cal, d.body_od, self.z_tip)
        # The rod standoff stays on the pad.
        self.parts = [(m, parts[name].assembled.center(CenterOf.MASS).Z)
                      for name, m in rocket.mass_g().items() if name != "Rod_Standoff"]
        self.motor_z = -d.thread["hang"] + d.mtr_len / 2  # resting on the cap's face
        self.recovery_z = parts["Nose"].placement_z - d.cal  # packed just under the nose shoulder

    @property
    def printed_mass_g(self) -> float:
        return sum(m for m, _ in self.parts)

    def _margin(self, cp: float, moments: list) -> tuple[float, float, float]:
        total = sum(m for m, _ in moments)
        cg = self.z_tip - sum(m * z for m, z in moments) / total
        return (cp - cg) / self.cal, cg, total

    def check(self, motor: Motor | None = None, recovery_mass_g: float | None = None) -> Stability:
        motor = motor or heaviest(self.params.motor)
        rec = recovery_allowance_g(self.body_od) if recovery_mass_g is None else recovery_mass_g
        margin, cg, total = self._margin(self.cp, self.parts + [(motor.mass_g, self.motor_z), (rec, self.recovery_z)])
        name = f"loaded {motor.code}"
        if margin < MIN_MARGIN_CAL:
            status = "unstable"
            message = (f"Unstable: {margin:.2f} cal with a {name} (at least {MIN_MARGIN_CAL:.1f} is needed). "
                       "Make the fins larger, lengthen the body, or fly a lighter motor.")
        elif margin > OVERSTABLE_CAL:
            status = "overstable"
            message = f"Over-stable: {margin:.2f} cal with a {name}. It will fly, but weathercocks into the wind; smaller fins help."
        else:
            status = "stable"
            message = f"Stable: {margin:.2f} cal with a {name}."
        return Stability(cg=cg, cp=self.cp, margin_cal=margin, length=self.length, total_mass_g=total,
                         motor_mass_g=motor.mass_g, motor=motor.code, recovery_mass_g=rec, status=status, message=message)

    def predicted_margin(self, fin_scale: float) -> float:
        """The heaviest-motor margin if the fins were scaled to `fin_scale`
        without rebuilding: CP from the scaled fins; CG with the fin blades'
        mass swapped (planform x thickness, no fillets; the tail stays at z = 0)."""
        scaled = self.params.with_(fin_scale=fin_scale)
        rho = MATERIALS[self.params.material] / 1000.0
        m0, z0 = _fin_blades(self.params, self.cal, rho)
        m1, z1 = _fin_blades(scaled, self.cal, rho)
        moments = self.parts + [(-m0, z0), (m1, z1), (heaviest(self.params.motor).mass_g, self.motor_z),
                                (recovery_allowance_g(self.body_od), self.recovery_z)]
        return self._margin(rocket_cp(scaled, self.cal, self.body_od, self.z_tip), moments)[0]


def stability(rocket: Rocket, motor: Motor | None = None, recovery_mass_g: float | None = None) -> Stability:
    return Balance(rocket).check(motor, recovery_mass_g)


def _fin_blades(params: DesignParams, cal: float, rho: float) -> tuple[float, float]:
    """(mass g, centroid z) of all the fin blades, from the planform."""
    fin = fin_dimensions(params, cal)
    pts = fin_outline(fin)
    a = cz = 0.0
    for (u0, v0), (u1, v1) in zip(pts, pts[1:] + pts[:1]):
        c = u0 * v1 - u1 * v0
        a += c
        cz += (v0 + v1) * c
    return params.fin_count * abs(a) / 2 * fin.thickness * rho, cz / (3 * a)


def build_stable(params: DesignParams) -> Rocket:
    """build_rocket, then (standard fin sizes only) scale the fins up until
    the rocket is stable with the heaviest motor of its size. Usually one
    extra build; custom fins are left as typed and only reported."""
    rocket = build_rocket(params)
    if params.custom_fin_size:
        return rocket
    for _ in range(3):
        b = Balance(rocket)
        cur = rocket.params.fin_scale
        if b.check().ok or cur >= MAX_FIN_SCALE:
            break
        if b.predicted_margin(MAX_FIN_SCALE) < AUTO_SIZE_TARGET_CAL:
            k = MAX_FIN_SCALE
        else:
            lo, hi = cur, MAX_FIN_SCALE
            for _ in range(30):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if b.predicted_margin(mid) < AUTO_SIZE_TARGET_CAL else (lo, mid)
            k = hi
        k = min(MAX_FIN_SCALE, max(k, cur * 1.05))  # always make progress
        rocket = build_rocket(rocket.params.with_(fin_scale=round(k, 3)))
    k = rocket.params.fin_scale
    if k > 1:
        motor = f"the heaviest {params.motor} motor ({heaviest(params.motor).code})"
        rocket.notes.insert(0, f"Fin span and sweep enlarged {k:.2f}x so the rocket is stable with {motor}."
                            if Balance(rocket).check().ok else
                            f"Fin span and sweep enlarged to the {k:.2f}x limit, and the rocket is still unstable with "
                            f"{motor}. Try another fin shape or a longer body, or use custom fins.")
    return rocket
