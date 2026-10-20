"""The one-page mission card (classroom; owner approved 2026-10-19).

A printable US-Letter page for one built rocket: its name and side profile
(with the balance point and push point), the key numbers from the build
(height, liftoff mass, stability score, best motor and delay, predicted peak,
parachute, field size), a "My prediction" box, blanks for the measured
results (altitude from an angle, flight time, landing distance) and notes.
Rendered on the server from the build the designer just made, so the numbers
are the report's. The print stylesheet is black on white (works on a
black-and-white printer); on screen it uses the brand look (static/brand.css).
"""

from __future__ import annotations

import math
from html import escape

import brand
from rocketgen.body import nose_radius_at

FT = 3.28084
LABEL = {"tangent_ogive": "Ogive", "conical": "Cone", "elliptical": "Round", "parabolic": "Parabolic", "von_karman": "Von Kármán",
         "trapezoid": "Trapezoid", "delta": "Delta", "swept": "Swept", "clipped_delta": "Clipped delta", "rectangular": "Rectangle"}


def profile_svg(shape: dict, cg: float, cp: float) -> str:
    """Side view, nose on the left, to scale: body, nose, two fins (top and
    bottom), the motor cap, CG and CP marks and the overall length."""
    L, od = shape["length_mm"], shape["od_mm"]
    R, nose = od / 2, shape["nose_mm"]
    tail = shape.get("tail_mm") or L
    f = shape["fin"]
    W, pad = 700.0, 30.0
    k = (W - 2 * pad) / L
    span = f["span"] * k
    cy = 26 + span + R * k  # leave room above for the top fin and the labels
    H = cy + R * k + span + 52
    X = lambda mm: pad + mm * k
    # Nose outline (x from the tip), then the body to the tail.
    n = 40
    top = [(X(nose * i / n), cy - nose_radius_at(shape["nose_shape"], nose * i / n, nose, R) * k) for i in range(n + 1)]
    pts = top + [(X(tail), cy - R * k), (X(tail), cy + R * k)] + [(x, 2 * cy - y) for x, y in reversed(top)]
    body = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    # Fins: root along the body, ending at the tail; leading edge swept back by `sweep`.
    le = tail - f["root"]
    fin = lambda s: (f"M{X(le):.1f} {cy + s * R * k:.1f} L{X(le + f['sweep']):.1f} {cy + s * (R * k + span):.1f} "
                     f"L{X(le + f['sweep'] + f['tip']):.1f} {cy + s * (R * k + span):.1f} L{X(tail):.1f} {cy + s * R * k:.1f} Z")
    # Whatever reaches below the tail and isn't fin is the motor cap.
    fin_end = le + f["sweep"] + f["tip"]
    cap = ""
    if L - tail > 1 and L > fin_end + 0.5:
        cap = f'<rect x="{X(tail):.1f}" y="{cy - R * k * 0.8:.1f}" width="{(L - tail) * k:.1f}" height="{R * k * 1.6:.1f}" class="cap"/>'
    # Joint lines would need the segment list; the outline is enough for a card.
    mark = lambda x, cls, label, below: (
        f'<g class="{cls}"><circle cx="{X(x):.1f}" cy="{cy:.1f}" r="8"/>'
        f'<path d="M{X(x):.1f} {cy - 8:.1f} V{cy + 8:.1f} M{X(x) - 8:.1f} {cy:.1f} H{X(x) + 8:.1f}"/>'
        f'<line x1="{X(x):.1f}" y1="{cy + (R * k + 4 if below else -R * k - 4):.1f}" x2="{X(x):.1f}" '
        f'y2="{cy + (R * k + span + 14 if below else -R * k - span - 6):.1f}"/>'
        f'<text x="{X(x):.1f}" y="{cy + (R * k + span + 26 if below else -R * k - span - 10):.1f}">{label}</text></g>')
    dim_y = H - 14
    return (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Side view of the rocket, nose on the left, '
            f'{L:.0f} mm long, with the balance point (CG) {cg:.0f} mm and the push point (CP) {cp:.0f} mm from the nose tip.">'
            f'<path class="fin" d="{fin(-1)}"/><path class="fin" d="{fin(1)}"/>{cap}<path class="body" d="{body}"/>'
            f'{mark(cg, "cg", "CG balance point", False)}{mark(cp, "cp", "CP push point", True)}'
            f'<path class="dim" d="M{X(0):.1f} {dim_y - 5:.1f} V{dim_y + 5:.1f} M{X(0):.1f} {dim_y:.1f} H{X(L):.1f} '
            f'M{X(L):.1f} {dim_y - 5:.1f} V{dim_y + 5:.1f}"/>'
            f'<text class="dimt" x="{W / 2:.0f}" y="{dim_y - 4:.1f}">{L:.0f} mm ({L / 25.4:.1f} in) tall</text></svg>')


def _tile(label: str, value: str, sub: str = "") -> str:
    return f'<div class="tile"><span class="rb-label">{label}</span><b>{value}</b>{f"<small>{sub}</small>" if sub else ""}</div>'


def page(name: str, b: dict, shape: dict, report: dict, build_id: str, design_id: str | None = None) -> str:
    p, st, fl = b["params"], b["stability"], b["flights"]
    best = next((r for r in fl["rows"] if r["code"] == fl["recommended"]), None)
    chute, field = b.get("parachute") or {}, b.get("field") or {}
    cal = st["margin_cal"]
    verdict = ("Too wobbly: not safe to fly" if not st["ok"] else "Just right" if cal <= 2 else "Very stable" if cal <= 3 else "Too stable")
    L = st["length_mm"]
    tiles = [
        _tile("Height", f"{L:.0f} mm", f"{L / 25.4:.1f} in · {L / 10:.0f} cm"),
        _tile("Liftoff mass", f"{best['liftoff_g'] if best else round(st['liftoff_mass_g'])} g",
              f"with the {escape(best['motor'])} and parachute" if best else f"with a loaded {escape(st['motor'])}"),
        _tile("Stability score", f"{cal:.2f} cal", f"{verdict} (1 to 2 is the sweet spot)"),
        _tile("Best motor", escape(best["motor"]) if best else "None yet",
              f"delay {best['delay_s']} s: the nose pops {best['delay_s']} s after the motor stops pushing" if best
              else "No motor of this size passes the safety checks"),
        _tile("Predicted peak", f"{best['apogee_m']} m" if best else "–", f"{round(best['apogee_m'] * FT)} ft" if best else ""),
        _tile("Parachute", f"{chute['size_in']} in" if chute.get("size_in") else "Extra large",
              ("A streamer works better in this narrow body. " if chute.get("streamer_recommended") else "")
              + (f"Falls about {chute['descent_ms']} m/s" if chute.get("descent_ms") else "")),
        _tile("Launch field", f"{field['recommended_m']} m" if field else "–",
              f"{round(field['recommended_m'] * FT)} ft on each side, at least" if field else ""),
    ]
    nw = p.get("nose_weight_g") or 0
    tiles.append(_tile("Nose weight", f"{nw:g} g clay", "pressed into the nose tip") if nw else
                 _tile("Body width", f"{shape['od_mm']:.0f} mm", f"{p['fin_count']} {LABEL.get(p['fin_shape'], p['fin_shape']).lower()} fins"))
    spec = (f"{escape(p['motor'])} motor size · {p['fin_count']} {escape(LABEL.get(p['fin_shape'], p['fin_shape']))} fins · "
            f"{escape(LABEL.get(p['nose_shape'], p['nose_shape']))} nose · {len(report['parts'])} printed parts, "
            f"{report['total_mass_g']:.0f} g of plastic")
    link = f"rocket.quiverdesignworks.net/d/{escape(design_id)}" if design_id else "rocket.quiverdesignworks.net"
    warn = ("" if st["ok"] else '<p class="warn"><b>Not stable yet.</b> Don\'t fly this one: change it in Rocket Builder until '
            "the score is at least 1 (a taller rocket, bigger fins or some clay in the nose).</p>")
    tan_row = "".join(f"<td>{a}°</td>" for a in range(15, 80, 5))
    tan_val = "".join(f"<td>{math.tan(math.radians(a)):.2f}</td>" for a in range(15, 80, 5))
    rows = "".join(f'<tr><th scope="row">{i}</th><td></td><td></td><td></td><td></td><td></td><td></td></tr>' for i in (1, 2, 3))
    return f"""<!doctype html>
<html lang="en">
<head>
{brand.HEAD}
<meta name="robots" content="noindex">
<title>Mission card · {escape(name)} · Rocket Builder</title>
<style>
  /* One US-Letter page. Screen: the brand look; print: black on white. */
  @page {{ size: letter; margin: 0.45in; }}
  .bar {{ display:flex; flex-wrap:wrap; gap:8px 12px; align-items:center; max-width:8.5in; margin:16px auto 0; padding:0 16px; }}
  .bar button {{ padding:9px 18px; border-radius:8px; border:0; background:var(--cta); color:var(--cta-ink); font:700 15px var(--font-head); cursor:pointer; }}
  .bar .hint {{ color:var(--muted); font-size:13.5px; }}
  .sheet {{ max-width:7.6in; margin:14px auto 40px; padding:0.35in 0.4in; background:var(--panel); border:1px solid var(--line);
    border-radius:12px; color:var(--ink); font-size:12.5px; line-height:1.35; }}
  .mhead {{ display:grid; grid-template-columns:1fr auto; gap:4px 18px; align-items:end; border-bottom:2px solid var(--ink); padding-bottom:6px; }}
  .kicker {{ display:flex; align-items:center; gap:7px; font:700 11px/1 var(--font-head); letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }}
  .kicker svg {{ width:20px; height:20px; }}
  .mhead h1 {{ font-size:26px; margin:4px 0 2px; overflow-wrap:anywhere; }}
  .spec {{ color:var(--muted); font-size:12px; }}
  .who {{ display:grid; gap:7px; font-size:12px; min-width:2.4in; }}
  .who span {{ display:flex; gap:6px; }} .who i {{ flex:1; border-bottom:1px solid var(--ink); font-style:normal; }}
  figure {{ margin:8px 0 2px; }}
  figure svg {{ width:100%; height:auto; max-height:2.1in; display:block; }}
  svg .body {{ fill:var(--card); stroke:var(--ink); stroke-width:1.6; }}
  svg .fin {{ fill:var(--rb-paper-300); stroke:var(--ink); stroke-width:1.4; }}
  svg .cap {{ fill:var(--rb-night-300); stroke:var(--ink); stroke-width:1.2; }}
  svg .cg circle {{ fill:#fff; stroke:var(--rb-sky); stroke-width:2.4; }} svg .cg path, svg .cg line {{ stroke:var(--rb-sky); stroke-width:1.6; }}
  svg .cp circle {{ fill:var(--rb-red); stroke:var(--rb-red); stroke-width:2; }} svg .cp path {{ stroke:#fff; stroke-width:1.6; }} svg .cp line {{ stroke:var(--rb-red); stroke-width:1.6; }}
  svg text {{ font:600 14px var(--font-body); fill:var(--ink); text-anchor:middle; }}
  svg .dim {{ stroke:var(--muted); stroke-width:1.2; fill:none; }} svg .dimt {{ fill:var(--muted); font-weight:500; }}
  .warn {{ margin:6px 0; padding:6px 10px; border:2px solid var(--rb-red); border-radius:6px; }}
  .tiles {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:6px; margin:8px 0; }}
  .tile {{ border:1px solid var(--line); border-radius:8px; padding:6px 8px; background:var(--card); }}
  .tile b {{ display:block; font:700 19px/1.15 var(--font-head); margin:2px 0 1px; }}
  .tile small {{ display:block; color:var(--muted); font-size:10.5px; line-height:1.25; }}
  h2 {{ font-size:14px; margin:10px 0 4px; text-transform:uppercase; letter-spacing:.08em; }}
  .box {{ border:1.5px solid var(--ink); border-radius:8px; padding:8px 10px; }}
  .line {{ display:flex; gap:6px; align-items:flex-end; margin:9px 0 0; }} .line i {{ flex:1; border-bottom:1px solid var(--ink); min-height:1em; }}
  .two {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:11.5px; }}
  .results th, .results td {{ border:1px solid var(--ink); padding:3px 5px; text-align:center; vertical-align:middle; }}
  .results thead th {{ font-weight:600; font-size:10.5px; line-height:1.2; background:var(--card); }}
  .results tbody td {{ height:34px; }}
  .tan {{ margin:5px 0 0; font-size:10.5px; }} .tan td {{ border:1px solid var(--line); padding:1px 3px; text-align:center; }}
  .help {{ font-size:11px; color:var(--muted); margin:4px 0 0; }}
  .notes .line {{ margin-top:13px; }}
  .foot {{ display:flex; justify-content:space-between; gap:10px; margin-top:10px; padding-top:5px; border-top:1px solid var(--line); font-size:10.5px; color:var(--muted); }}
  @media (max-width:640px) {{ .sheet {{ margin:10px 8px 30px; padding:14px 12px; }} .mhead {{ grid-template-columns:1fr; }}
    .tiles {{ grid-template-columns:1fr 1fr; }} .two {{ display:block; }} .tan {{ width:100%; }} .results {{ font-size:10px; }}
    .results-wrap, .tan-wrap {{ overflow-x:auto; }} }}
  @media print {{
    :root {{ --ink:#000; --muted:#333; --line:#999; --card:#fff; --panel:#fff; --bg:#fff; color-scheme:light; }}
    html, body {{ background:#fff !important; color:#000; }}
    .rb-header, .bar, .rb-footer {{ display:none !important; }}
    .sheet {{ max-width:none; margin:0; padding:0; border:0; border-radius:0; font-size:11.5px; }}
    .tiles {{ grid-template-columns:repeat(4, 1fr); }} .two {{ display:grid; grid-template-columns:1fr 1fr; }} .mhead {{ grid-template-columns:1fr auto; }}
    svg .body, svg .fin, svg .cap {{ fill:#fff; stroke:#000; }} svg .fin {{ fill:#ddd; }} svg .cap {{ fill:#bbb; }}
    svg .cg circle {{ fill:#fff; stroke:#000; }} svg .cg path, svg .cg line {{ stroke:#000; }}
    svg .cp circle {{ fill:#000; stroke:#000; }} svg .cp line {{ stroke:#000; stroke-dasharray:3 2; }}
    svg text {{ fill:#000; }} svg .dim {{ stroke:#000; }} svg .dimt {{ fill:#000; }}
    .warn {{ border-color:#000; }}
    .results thead th {{ background:#eee; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    .tile, .box, table {{ break-inside:avoid; }}
    .results tbody td {{ height:28px; }} figure svg {{ max-height:1.8in; }} .notes .line {{ margin-top:11px; }}
  }}
</style>
</head>
<body>
{brand.header("Mission card")}
<div class="bar"><button type="button" onclick="print()">Print this card</button>
  <span class="hint">One US-Letter page; prints fine in black and white. Fill in the blanks at the launch.</span></div>
<main class="sheet">
  <div class="mhead">
    <div><span class="kicker">{brand.MARK.replace("{mid}", "mc-cut")}Rocket Builder · Mission card</span>
      <h1>{escape(name)}</h1><div class="spec">{spec}</div></div>
    <div class="who"><span>Pilot / team <i></i></span><span>Launch date <i></i></span><span>Weather and wind <i></i></span></div>
  </div>
  <figure>{profile_svg(shape, st["cg_mm"], st["cp_mm"])}</figure>
  <p class="help">CG (balance point) and CP (push point) are measured from the nose tip, with a loaded {escape(st["motor"])}. The CG must be in front of the CP.
  Check it for real: balance your finished rocket, motor in, on one finger.</p>
  {warn}
  <div class="tiles">{"".join(tiles)}</div>
  <div class="two">
    <section><h2>My prediction</h2>
      <div class="box">
        <div class="line">I think it will fly <i></i> m high,</div>
        <div class="line">because <i></i></div>
        <div class="line"><i></i></div>
        <div class="line">Rocket Builder says {f"{best['apogee_m']} m" if best else "—"}. Mine was off by <i></i> m.</div>
      </div></section>
    <section><h2>How to measure the height</h2>
      <div class="box">
        <p style="margin:0">Stand a measured distance from the pad. Sight the top of the flight with your inclinometer and read the angle.</p>
        <p style="margin:5px 0 0"><b>height = tan(angle) × distance + eye height</b></p>
        <p style="margin:4px 0 0"><b>At 45°, the height equals how far you walked.</b> More tools: rocket.quiverdesignworks.net/tools/altitude</p>
        <div class="tan-wrap"><table class="tan"><tr><th>angle</th>{tan_row}</tr><tr><th>tan</th>{tan_val}</tr></table></div>
      </div></section>
  </div>
  <h2>Measured results</h2>
  <div class="results-wrap"><table class="results">
    <thead><tr><th>Flight</th><th>Motor</th><th>Angle at the top (°)</th><th>Distance from pad (m)</th>
      <th>Height (m)<br>tan × distance + eye</th><th>Flight time (s)<br>liftoff to landing</th><th>Landed how far from the pad (m)</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
  <section class="notes"><h2>Notes</h2>
    <div class="line">What went well? <i></i></div><div class="line">What would I change? <i></i></div><div class="line"><i></i></div>
  </section>
  <div class="foot"><span>Fly with a grown-up and follow the NAR Model Rocket Safety Code. Numbers are estimates from Rocket Builder.</span><span>{link}</span></div>
</main>
<footer class="rb-footer"><a href="/">Rocket Builder</a> by <a href="https://quiverdesignworks.net/">Quiver Design Works</a></footer>
</body>
</html>"""


def missing() -> str:
    """The card's build has gone (builds live in memory; a restart clears them)."""
    return f"""<!doctype html>
<html lang="en"><head>{brand.HEAD}<meta name="robots" content="noindex"><title>Mission card · Rocket Builder</title></head>
<body>{brand.header("Mission card")}
<main class="rb-main"><h1>Build the rocket again</h1>
<p class="lede">This mission card's rocket isn't on the server any more (it keeps builds for a while, and forgets them after an update).
Go back to Rocket Builder, press <b>Build</b>, then choose <b>Mission card</b> from the download menu (▾).</p>
<p><a href="/">← Back to Rocket Builder</a></p></main></body></html>"""
