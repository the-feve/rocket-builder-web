"""Motor library and a quick flight simulation: which motor to fly.

Ported from the Rocket Motor Picker (OS_Rocket_Builder tools/motor-picker.html).
Estes motors per bay size from ThrustCurve.org, in data/web_motors.csv
(website-only, not a Variable Studio). One-dimensional vertical flight:
thrust curve, drag, propellant burn-off; then the safety checks the NAR
code implies (thrust-to-weight, speed off the rod, a recoverable apogee).
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache

from .params import DATA_DIR

G0, RHO = 9.80665, 1.225
MIN_THRUST_TO_WEIGHT = 5.0
MIN_ROD_SPEED = 15.0  # m/s
MIN_APOGEE = 30.0  # m
FIELD_M = {"1/4A": 15, "1/2A": 15, "A": 30, "B": 60, "C": 120, "D": 150, "E": 300, "F": 300}  # NAR minimum field side


@dataclass(frozen=True)
class Motor:
    code: str
    size: str
    cls: str
    impulse: float  # N s
    avg_thrust: float  # N
    peak_thrust: float | None
    burn: float  # s
    prop_g: float
    mass_g: float  # loaded
    delays: tuple[int, ...]
    out_of_production: bool
    mass_estimated: bool


@lru_cache(maxsize=1)
def load_flight_motors() -> tuple[Motor, ...]:
    with open(DATA_DIR / "web_motors.csv", newline="") as f:
        return tuple(Motor(r["code"], r["size"], r["cls"], float(r["impulse_ns"]), float(r["avg_thrust_n"]),
                           float(r["peak_thrust_n"]) if r["peak_thrust_n"] else None, float(r["burn_s"]),
                           float(r["prop_g"]), float(r["mass_g"]), tuple(int(d) for d in r["delays"].split()),
                           bool(r["out_of_production"]), bool(r["mass_estimated"])) for r in csv.DictReader(f))


def motors_for(size: str) -> list[Motor]:
    return [m for m in load_flight_motors() if m.size == size]


def heaviest(size: str) -> Motor:
    """The least stable case for a bay size: its heaviest loaded motor."""
    return max(motors_for(size), key=lambda m: m.mass_g)


def thrust_fn(m: Motor):
    """Quick rise to the peak (first 5 % of the burn), decay to a sustain
    level by 25 %, sustain to burnout; the sustain level makes the area
    equal the total impulse. Flat average thrust when there's no peak."""
    tb, total, fp = m.burn, m.impulse, m.peak_thrust
    flat = lambda t: total / tb if t < tb else 0.0  # noqa: E731
    if not fp:
        return flat
    t1, t2 = 0.05 * tb, 0.25 * tb
    fs = (total - 0.5 * fp * t1 - 0.5 * fp * (t2 - t1)) / (0.5 * (t2 - t1) + (tb - t2))
    if not fs > 0:
        return flat

    def f(t):
        if t >= tb:
            return 0.0
        if t < t1:
            return fp * t / t1
        if t < t2:
            return fp + (fs - fp) * (t - t1) / (t2 - t1)
        return fs
    return f


@dataclass
class Flight:
    motor: Motor
    apogee: float  # m
    rod_speed: float  # m/s
    max_speed: float
    coast: float  # s, burnout to apogee
    delay: int  # the motor's listed delay nearest the coast time
    thrust_to_weight: float
    problems: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems


def simulate(m: Motor, rocket_mass_g: float, diameter_mm: float, cd: float = 0.65, rod_m: float = 0.91) -> Flight:
    area = math.pi * (diameter_mm / 2000) ** 2
    m0, prop = (rocket_mass_g + m.mass_g) / 1000, m.prop_g / 1000
    thrust = thrust_fn(m)
    dt = 0.002
    t = h = v = burnt = v_max = 0.0
    rod_v = None
    while t < 120:
        f = thrust(t)
        mass = m0 - prop * min(burnt / m.impulse, 1.0)
        a = (f - 0.5 * RHO * cd * area * v * abs(v)) / mass - G0
        if h <= 0 and v <= 0 and a < 0:  # still on the pad
            a = v = 0.0
        v += a * dt
        h += v * dt
        burnt += f * dt
        t += dt
        if rod_v is None and h >= rod_m:
            rod_v = v
        v_max = max(v_max, v)
        if t > m.burn and v <= 0:
            break
    coast = max(0.0, t - m.burn)
    delay = min(m.delays, key=lambda d: abs(d - coast))
    tw = m.avg_thrust / (m0 * G0)
    problems = []
    if tw < MIN_THRUST_TO_WEIGHT:
        problems.append("Too heavy for this motor")
    if (rod_v or 0.0) < MIN_ROD_SPEED:
        problems.append("Slow off the rod")
    if h < MIN_APOGEE:
        problems.append("Too low for recovery")
    return Flight(m, max(0.0, h), rod_v or 0.0, v_max, coast, delay, tw, problems)


def pick(flights: list[Flight], target_m: float) -> Flight | None:
    """The safe flight closest to the target altitude (on a log scale)."""
    ok = [f for f in flights if f.ok and f.apogee > 0]
    return min(ok, key=lambda f: abs(math.log(f.apogee / target_m)), default=None)
