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

import copy
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
        self.nose_z = parts["Nose"].assembled.center(CenterOf.MASS).Z  # where nose weight (clay) sits, roughly
        # For predict_length: the body between the aft part and the top body
        # part (the Seg_* parts) is what grows or shrinks; the aft part
        # stays, and the top part (with the cord strap), nose and parachute
        # slide with the top. A one-piece body (the strap in the aft part's
        # top) has no middle: new tube is added above the aft part and only
        # the nose and parachute slide (the ~1 g strap stays; close enough).
        masses = rocket.mass_g()
        joint = d.shoulder_len + d.joint_rise
        self.aft_top = rocket.seg_lens[0]
        body = [q.name for q in rocket.parts[:len(rocket.seg_lens)]]  # aft first, top last
        top = parts[body[-1]] if len(body) > 1 else None
        self.mid_len = max(top.placement_z + joint - self.aft_top, 0.0) if top else 0.0  # exposed height of the Seg_* parts
        mid = [(masses[n], parts[n].assembled.center(CenterOf.MASS).Z) for n in body[1:-1]]
        self.mid_m = sum(m for m, _ in mid)
        self.mid_z = sum(m * z for m, z in mid) / self.mid_m if mid else self.aft_top
        # g per mm of height: measured from the Seg_* parts (joints and lug included), else a plain tube
        # plus one joint overlap per printed section.
        tube = math.pi / 4 * (d.body_od ** 2 - d.body_id ** 2) * MATERIALS[p.material] / 1000.0
        self.mid_g_per_mm = (self.mid_m / self.mid_len if self.mid_m and self.mid_len > 20
                             else tube * d.zmax / max(d.zmax - joint, 1.0))
        sliding = ([top.name] if top else []) + ["Nose"]
        self.slides = [(masses[n], parts[n].assembled.center(CenterOf.MASS).Z) for n in sliding]
        self.fixed = [(masses[n], parts[n].assembled.center(CenterOf.MASS).Z) for n in parts
                      if n not in sliding and n != "Rod_Standoff" and n not in body[1:-1]]
        self.nose_weight_g = 0.0
        if p.nose_weight_g:
            self._add_nose_weight(p.nose_weight_g)

    def _add_nose_weight(self, grams: float) -> None:
        # Clay pressed into the nose: a point mass at the nose cone's own
        # centroid (nose_z, where the advice's clay estimate puts it too).
        # Pushed in from the shoulder it sits between there and the tip, so
        # the centroid is the cautious end: the real gain is a little more.
        # It flies with the rocket, so it counts in printed_mass_g (the flight
        # sim and parachute see it) and slides with the nose in predict_length.
        self.parts = self.parts + [(grams, self.nose_z)]
        self.slides = self.slides + [(grams, self.nose_z)]
        self.nose_weight_g += grams

    def with_nose_weight(self, grams: float) -> "Balance":
        """A copy of this balance carrying `grams` more nose weight (clay).
        The website caches one Balance per geometry; the nose weight is not
        geometry, so each request adds its own."""
        if not grams:
            return self
        b = copy.copy(self)
        b._add_nose_weight(grams)
        return b

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


    def predict(self, motor: Motor | None = None, recovery_mass_g: float | None = None,
                nose_g: float = 0.0, **fin_changes) -> float:
        """The margin if this rocket flew `motor`, carried `nose_g` grams of
        nose weight, or had its fins changed (fin_shape, fin_count,
        fin_scale, fin_span...), without rebuilding: the fin blades' mass and
        CP are swapped as in predicted_margin. The body is unchanged, so a
        fin change that would move the tail (more trailing fins) is
        approximate."""
        motor = motor or heaviest(self.params.motor)
        rec = recovery_allowance_g(self.body_od) if recovery_mass_g is None else recovery_mass_g
        moments = self.parts + [(motor.mass_g, self.motor_z), (rec, self.recovery_z)]
        cp = self.cp
        if fin_changes:
            changed = self.params.with_(**fin_changes)
            rho = MATERIALS[self.params.material] / 1000.0
            m0, z0 = _fin_blades(self.params, self.cal, rho)
            m1, z1 = _fin_blades(changed, self.cal, rho)
            moments += [(-m0, z0), (m1, z1)]
            cp = rocket_cp(changed, self.cal, self.body_od, self.z_tip)
        if nose_g:
            moments.append((nose_g, self.nose_z))
        return self._margin(cp, moments)[0]


    def predict_length(self, delta: float, motor: Motor | None = None, recovery_mass_g: float | None = None) -> float | None:
        """The margin if the rocket were `delta` mm taller (negative:
        shorter), without rebuilding: the middle of the body (the Seg_*
        parts) grows or shrinks at its measured weight per mm, and the top
        body part, nose and parachute slide with the top. None when shorter
        would cut into the aft part or top body part (no estimate then).
        Checked against rebuilds: within about 0.2 cal for changes of a few
        hundred mm."""
        new_len = self.mid_len + delta
        if new_len < 0:
            return None
        motor = motor or heaviest(self.params.motor)
        rec = recovery_allowance_g(self.body_od) if recovery_mass_g is None else recovery_mass_g
        mid_m = self.mid_g_per_mm * new_len
        moments = (self.fixed + [(motor.mass_g, self.motor_z), (mid_m, self.mid_z + delta / 2)]
                   + [(m, z + delta) for m, z in self.slides] + [(rec, self.recovery_z + delta)])
        z_tip = self.z_tip + delta
        cg = z_tip - sum(m * z for m, z in moments) / sum(m for m, _ in moments)
        R = self.body_od / 2
        cn_n, x_n = nose_cp(self.params.nose_shape, self.params.nose_fineness * self.cal, R)
        fin = fin_dimensions(self.params, self.cal)
        cn_f, x_f = fin_cp(self.params.fin_count, fin.root, fin.tip, fin.span, fin.sweep, R, z_tip - fin.root)
        return ((cn_n * x_n + cn_f * x_f) / (cn_n + cn_f) - cg) / self.cal

    def length_for(self, target: float, motor: Motor | None = None, recovery_mass_g: float | None = None,
                   limit: float = 1500.0) -> float | None:
        """The body length change (mm) that predict_length puts at `target`
        cal, or None if none within +-limit (or no shorter body is left)."""
        lo, hi = -min(limit, self.mid_len), limit
        f = lambda dl: self.predict_length(dl, motor, recovery_mass_g) - target
        if f(lo) * f(hi) > 0:
            return None
        for _ in range(50):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
        return (lo + hi) / 2


SWEET_SPOT = (MIN_MARGIN_CAL, 2.0)  # the page's green "just right" zone
TARGET_CAL = 1.5


def advice(bal: Balance, st: Stability, motors: list[Motor], beginner: bool,
           motor: Motor | None = None, stock_od: float | None = None) -> dict | None:
    """What to change to bring the score into the 1-2 cal sweet spot, best
    first, each with the predicted score where it can be worked out without
    rebuilding (motor, nose weight, fins, body width). None inside the sweet
    spot. `beginner`: only the Beginner steps' levers, with step numbers;
    `stock_od`: the motor size's minimum body OD (for the body-width tip)."""
    m = st.margin_cal
    if SWEET_SPOT[0] <= m <= SWEET_SPOT[1]:
        return None
    p = bal.params
    low = m < SWEET_SPOT[0]
    items: list[dict] = []

    def add(text: str, est: float | None = None, kind: str = ""):
        if low and est is not None and est < SWEET_SPOT[0]:
            text += " Not enough on its own: combine it with another change."
        items.append({"text": text, "est_cal": None if est is None else round(est, 2), "kind": kind})

    def step(n: int) -> str:
        return f" (step {n})" if beginner else ""

    rows = sorted(((x, bal.predict(x, st.recovery_mass_g)) for x in motors), key=lambda r: r[0].mass_g)
    current = motor or heaviest(p.motor)
    shapes = ["swept", "delta", "trapezoid"] if beginner else ["swept", "delta", "trapezoid", "clipped_delta", "rectangular"]
    if low:
        # Taller first: it's the usual fix and always in reach (the body length isn't capped like the fins).
        dl = bal.length_for(TARGET_CAL, motor, st.recovery_mass_g)
        if dl is not None and 0 < dl <= 400:
            dl = math.ceil(dl / 10) * 10
            e = bal.predict_length(dl, motor, st.recovery_mass_g)
            add(f"Make the rocket taller{step(4)}: about {dl:.0f} mm taller (around {bal.length + dl:.0f} mm in all) "
                f"gives about {e:.1f} cal. A longer body moves the balance point forward, away from the fins.", e, "taller")
        else:
            e = bal.predict_length(200, motor, st.recovery_mass_g)
            add(f"Making it taller{step(4)} helps, but not enough on its own: 200 mm taller only gets about {e:.1f} cal. "
                "Start with the other changes below.", None, "taller")
        if not p.custom_fin_size:
            best = max(((sh, bal.predict(fin_shape=sh, fin_scale=MAX_FIN_SCALE)) for sh in shapes if sh != p.fin_shape),
                       key=lambda r: r[1], default=None)
            if best and best[1] > m + 0.1:
                add(f"Try {best[0].replace('_', ' ')} fins{step(5)}: they reach about {best[1]:.1f} cal when they grow to full size.",
                    best[1], "fins")
        else:
            for k in (1.25, 1.5, 2.0):
                e = bal.predict(fin_span=p.fin_span * k, fin_sweep=p.fin_sweep * k)
                if e >= TARGET_CAL or k == 2.0:
                    add(f"Make the fins bigger: span and sweep {int((k - 1) * 100)}% larger gives about {e:.1f} cal "
                        "(or untick Custom fin size and they grow by themselves).", e, "fins")
                    break
        if not beginner and p.fin_count < 5:
            e = bal.predict(fin_count=p.fin_count + 1)
            add(f"Use {p.fin_count + 1} fins instead of {p.fin_count}: about {e:.1f} cal.", e, "fins")
        lighter = [(x, e) for x, e in rows if e >= SWEET_SPOT[0] and x.mass_g < current.mass_g]
        if lighter:
            x, e = lighter[-1]  # the heaviest one that's still stable: the most altitude
            add(f"Fly a lighter motor: with a {x.code} the score is about {e:.1f} cal. The motor sits at the back, "
                "so a lighter one moves the balance point forward. (A bigger motor size does the opposite.)", e, "motor")
        for g in range(1, 201):
            e = bal.predict(motor, st.recovery_mass_g, nose_g=g)
            if e >= TARGET_CAL:
                if g <= max(40, bal.printed_mass_g * 0.4):
                    add(f"Add about {g} g of modelling clay inside the tip of the nose cone: about {e:.1f} cal. "
                        "It makes the rocket heavier, so it flies a little lower.", e, "noseweight")
                break
        if stock_od and bal.body_od > stock_od + 0.5:
            e = m * bal.body_od / stock_od
            add(f"Make the body skinnier (Body OD offset 0, {stock_od:.0f} mm across): about {e:.1f} cal. "
                "The score counts in body widths, so a thinner body scores higher.", e, "od")
    else:
        dl = bal.length_for(TARGET_CAL, motor, st.recovery_mass_g)
        if dl is not None and dl < 0:
            dl = -math.floor(-dl / 10) * 10
            e = bal.predict_length(dl, motor, st.recovery_mass_g)
            add(f"Make the rocket shorter{step(4)}: about {-dl:.0f} mm shorter (around {bal.length + dl:.0f} mm in all) "
                f"gives about {e:.1f} cal. A shorter body moves the balance point back toward the fins.", e, "shorter")
        elif bal.mid_len > 20:
            dl = -bal.mid_len
            e = bal.predict_length(dl, motor, st.recovery_mass_g)
            add(f"Make the rocket shorter{step(4)}: down to about {bal.length + dl:.0f} mm (about as short as this motor "
                f"size allows) gives about {e:.1f} cal. A shorter body moves the balance point back toward the fins.", e, "shorter")
        else:
            add(f"It's already about as short as this motor size allows{step(4)}, so try the changes below.", kind="shorter")
        if not p.custom_fin_size:
            opts = [(sh, bal.predict(fin_shape=sh, fin_scale=1.0)) for sh in shapes if sh != p.fin_shape]
            fit = [r for r in opts if r[1] >= SWEET_SPOT[0]]
            if fit:
                sh, e = min(fit, key=lambda r: abs(r[1] - TARGET_CAL))
                if e < m - 0.1 and m - e >= 0.3 * (m - SWEET_SPOT[1]):  # skip a tip that barely helps
                    add(f"Try {sh.replace('_', ' ')} fins{step(5)}: about {e:.1f} cal.", e, "fins")
        else:
            e = bal.predict(fin_span=p.fin_span * 0.75, fin_sweep=p.fin_sweep * 0.75)
            add(f"Make the fins smaller: span and sweep 25% smaller gives about {e:.1f} cal.", e, "fins")
        if not beginner and p.fin_count > 3:
            e = bal.predict(fin_count=p.fin_count - 1)
            add(f"Use {p.fin_count - 1} fins instead of {p.fin_count}: about {e:.1f} cal.", e, "fins")
        heavier = [(x, e) for x, e in rows if x.mass_g > current.mass_g]
        if heavier:
            x, e = heavier[-1]
            add(f"A heavier motor lowers the score: with a {x.code} it is about {e:.1f} cal.", e, "motor")
        add(f"A bigger motor size{step(2)} also lowers the score (a heavier motor at the back), and flies higher.", kind="motorsize")
        if not beginner:
            add("A wider body (Body OD offset) lowers the score too: it counts in body widths.", kind="od")
    if low:
        intro = (f"{m:.2f} cal is under 1, so it could wobble or tumble. "
                 "The balance point needs to move forward (toward the nose), or the push point back (toward the fins). Things that help:")
    elif m > 3.0:
        intro = (f"{m:.2f} cal is more than it needs: it will turn into the wind like a weathervane. "
                 "The balance point is far in front of the push point. To get closer to 1-2 cal:")
    else:
        intro = f"{m:.2f} cal is fine to fly, a bit above the 1-2 sweet spot. If you want it closer:"
    return {"zone": "low" if low else "over" if m > 3.0 else "high", "intro": intro, "items": items}


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
