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


# Recovery: hobby parachutes are sold by flat diameter in inches.
CHUTE_SIZES_IN = (12, 15, 18, 24, 30, 36)
CHUTE_CD = 0.75  # a flat plastic or nylon hobby chute, on its flat diameter
SAFE_DESCENT_MS = 4.5  # about 15 ft/s: lands without damage, doesn't drift far
AIR_DENSITY = 1.225


def descent_rate(mass_g: float, diameter_in: float) -> float:
    """Steady descent speed (m/s) under a flat chute of this diameter."""
    area = math.pi * (diameter_in * 0.0254 / 2) ** 2
    return math.sqrt(2 * mass_g / 1000 * 9.81 / (AIR_DENSITY * CHUTE_CD * area))


def parachute(descent_mass_g: float) -> dict:
    """The smallest standard chute that brings `descent_mass_g` (the rocket
    after the motor has burned) down at a safe speed, and how fast. Light
    rockets can use a streamer instead."""
    need_in = math.sqrt(8 * descent_mass_g / 1000 * 9.81 / (math.pi * AIR_DENSITY * CHUTE_CD * SAFE_DESCENT_MS ** 2)) / 0.0254
    size = next((s for s in CHUTE_SIZES_IN if s >= need_in), None)
    return {"descent_mass_g": round(descent_mass_g, 1), "min_diameter_in": round(need_in, 1), "size_in": size,
            "descent_ms": round(descent_rate(descent_mass_g, size), 1) if size else None,
            "streamer_ok": descent_mass_g < 40}


WIND_MS = 4.5  # about 10 mph: a typical launch-day breeze (the NAR code's limit is 20 mph)


def field_size(motor_cls: str, apogee_m: float, descent_ms: float | None) -> dict:
    """Launch field for a flight: the NAR Safety Code's minimum side for the
    motor class, and how far the rocket drifts downwind under its parachute
    from apogee in a 10 mph breeze (the pad goes near the upwind edge, so
    the field must be at least that long). Recommended = the larger."""
    nar = FIELD_M.get(motor_cls, max(FIELD_M.values()))
    drift = apogee_m / descent_ms * WIND_MS if descent_ms else None
    rec = max(nar, math.ceil(drift / 10) * 10) if drift else nar
    return {"nar_min_m": nar, "drift_m": None if drift is None else round(drift), "wind_ms": WIND_MS,
            "recommended_m": rec, "apogee_m": round(apogee_m), "descent_ms": descent_ms}


MPH = 0.44704  # m/s
MAX_WIND_MPH = 20  # the NAR Safety Code: don't launch in winds over 20 mph


def launch_profile(m: Motor, rocket_mass_g: float, diameter_mm: float, chute_in: float | None,
                   wind_ms: float = WIND_MS, delay: int | None = None, cd: float = 0.65, rod_m: float = 0.91) -> dict:
    """A whole flight in two dimensions, for the launch page: up the rod,
    boost and coast, the ejection charge at burnout + delay, then down under
    the parachute, with the wind blowing along +x.

    Off the rod the rocket points into its own airflow (a stable rocket
    weathercocks), so a crosswind tilts it upwind while the motor burns; the
    parachute then carries it downwind. Drag on the open chute (flat Cd on
    its flat diameter) acts on the speed through the air, so it falls at
    `descent_rate` and drifts at about the wind speed. `rocket_mass_g` is
    the rocket without the motor; it lands with the motor's empty casing.
    Returns the sampled path (every 0.05 s: t, x, h, phase), the events and
    the landing distance (negative = upwind of the pad)."""
    area = math.pi * (diameter_mm / 2000) ** 2
    chute_area = math.pi * (chute_in * 0.0254 / 2) ** 2 if chute_in else 0.0
    m0, prop = (rocket_mass_g + m.mass_g) / 1000, m.prop_g / 1000
    thrust = thrust_fn(m)
    if delay is None:
        delay = simulate(m, rocket_mass_g, diameter_mm, cd, rod_m).delay
    t_eject = m.burn + delay
    dt, every = 0.002, 25
    t = x = h = vx = vh = burnt = 0.0
    chute_open = 0.0  # 0 → 1 over half a second after ejection
    on_rod, path, events = True, [], {}
    step = 0
    while t < 600:
        f = thrust(t)
        mass = m0 - prop * min(burnt / m.impulse, 1.0)
        ax_air, ah_air = vx - wind_ms, vh  # velocity through the air
        speed_air = math.hypot(ax_air, ah_air)
        if on_rod:
            ux, uh = 0.0, 1.0
        elif speed_air > 1e-6:
            ux, uh = ax_air / speed_air, ah_air / speed_air
        else:
            ux, uh = 0.0, 1.0
        if t >= t_eject:
            chute_open = min(1.0, (t - t_eject) / 0.5)
        cda = cd * area + (CHUTE_CD * chute_area * chute_open)
        drag = 0.5 * RHO * cda * speed_air
        ax = f * ux / mass - drag * ax_air / mass
        ah = f * uh / mass - drag * ah_air / mass - G0
        if on_rod:
            ax = vx = 0.0
            if h <= 0 and ah < 0:  # waiting for thrust to beat weight
                ah = vh = 0.0
        vx += ax * dt
        vh += ah * dt
        x += vx * dt
        h += vh * dt
        burnt += f * dt
        t += dt
        step += 1
        if on_rod and h >= rod_m:
            on_rod = False
            events["rod"] = {"t": round(t, 2), "speed_ms": round(vh, 1)}
        if "burnout" not in events and t >= m.burn:
            events["burnout"] = {"t": round(t, 2), "h": round(h, 1), "x": round(x, 1)}
        if "apogee" not in events and t > m.burn and vh <= 0:
            events["apogee"] = {"t": round(t, 2), "h": round(h, 1), "x": round(x, 1)}
        if "eject" not in events and t >= t_eject:
            events["eject"] = {"t": round(t, 2), "h": round(h, 1), "x": round(x, 1),
                               "speed_ms": round(math.hypot(vx, vh), 1)}
        phase = "rod" if on_rod else "boost" if t < m.burn else "coast" if t < t_eject else "chute"
        if step % every == 0:
            path.append([round(t, 2), round(x, 2), round(max(h, 0.0), 2), phase])
        if t > 0.1 and h <= 0 and not on_rod:
            break
    landing = {"t": round(t, 1), "x": round(x, 1), "speed_ms": round(abs(vh), 1)}
    path.append([round(t, 2), round(x, 2), 0.0, "landed"])
    events["landing"] = landing
    eject = events.get("eject")
    apo = events.get("apogee", {"h": 0.0})
    warnings = []
    if eject and apo["h"] and eject["h"] < 0.5 * apo["h"] and eject["t"] > events["apogee"]["t"]:
        warnings.append("The ejection comes late, well after the top: pick a shorter delay.")
    if eject and eject["speed_ms"] > 25:
        warnings.append(f"The parachute opens at {eject['speed_ms']:.0f} m/s, which can tear it or zip the body tube: "
                        "a delay closer to the coast time is gentler.")
    if wind_ms > MAX_WIND_MPH * MPH + 1e-9:
        warnings.append("The NAR Safety Code says don't launch in winds over 20 mph.")
    return {"motor": f"{m.code}-{delay}", "code": m.code, "cls": m.cls, "delay_s": delay, "wind_ms": round(wind_ms, 2),
            "chute_in": chute_in, "apogee_m": round(apo["h"], 1), "events": events, "path": path,
            "landing_m": landing["x"], "field": launch_field(m.cls, path), "warnings": warnings}


def launch_field(motor_cls: str, path: list) -> dict:
    """The field this flight needs: the NAR minimum side for the motor class
    (square, pad in the middle), or, when the rocket drifts further, a field
    reaching from the pad to past the landing spot with 25 % to spare for
    gusts. The pad goes near the upwind edge, a quarter of the NAR side in."""
    nar = FIELD_M.get(motor_cls, max(FIELD_M.values()))
    far_down = max(0.0, max(p[1] for p in path))
    far_up = max(0.0, -min(p[1] for p in path))
    up_margin = max(nar / 4, far_up * 1.25)
    length = max(nar, math.ceil((up_margin + far_down * 1.25) / 10) * 10)
    return {"nar_min_m": nar, "length_m": length, "width_m": nar, "pad_from_upwind_m": round(up_margin),
            "downwind_m": round(far_down), "upwind_m": round(far_up)}
