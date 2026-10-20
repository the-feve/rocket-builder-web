"""Labelled line drawings for the rocketry lessons, in the Rocket Builder brand style.

Each figure is inline SVG that uses the `dg-` classes in DG_CSS (included by learn.css, the
worksheets and the teacher guides), so the same drawing works on the web, in print and in black
and white: every arrow carries a word label, and drag is dashed.

In a lesson's markdown, put a figure on its own line with blank lines around it:

    <!-- figure: balloon-setup -->

build_site.py swaps it for <figure class="dg">…</figure> with the caption below. FIGURES lists them.
"""
from __future__ import annotations

import math

NIGHT, ORANGE, SKY, RED, GREEN, GREY = "#12203A", "#F2652B", "#3D8BFD", "#E5484D", "#2FB67C", "#6E6E73"

DG_CSS = """
.dg-o{fill:none;stroke:#12203A;stroke-width:2.4;stroke-linejoin:round;stroke-linecap:round}
.dg-w{fill:#FFFDF8;stroke:#12203A;stroke-width:2.4;stroke-linejoin:round}
.dg-f{fill:#DDEAFF;stroke:#12203A;stroke-width:2.4;stroke-linejoin:round}
.dg-p{fill:#FDE3D6;stroke:#12203A;stroke-width:2.4;stroke-linejoin:round}
.dg-g{fill:#E2D9C6;stroke:#12203A;stroke-width:2.4;stroke-linejoin:round}
.dg-n{fill:#12203A}
.dg-thin{fill:none;stroke:#12203A;stroke-width:1.4}
.dg-lead{fill:none;stroke:#6E6E73;stroke-width:1.3}
.dg-dash{fill:none;stroke:#3D8BFD;stroke-width:2.4;stroke-dasharray:9 7;stroke-linecap:round}
.dg-arc{fill:none;stroke:#12203A;stroke-width:2;stroke-dasharray:9 7;stroke-linecap:round}
.dg-t{font:500 15px Inter,system-ui,sans-serif;fill:#12203A}
.dg-tb{font:700 15px Inter,system-ui,sans-serif;fill:#12203A}
.dg-ts{font:500 12.5px Inter,system-ui,sans-serif;fill:#6E6E73}
.dg-th{font:700 17px "Space Grotesk",Inter,sans-serif;fill:#12203A}
.dg-cl{font:700 14px "Space Grotesk",Inter,sans-serif;fill:#FFFDF8}
"""

_n = [0]


def _svg(w, h, body, label):
    return (f'<svg class="dg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


# ---------------------------------------------------------------- primitives
def arrow(x1, y1, x2, y2, kind="thrust", label="", lx=None, ly=None, anchor="start"):
    """A force or motion arrow with a solid head. kind: thrust, gravity, drag, air, lift, move, dim."""
    col, wid, dash = {"thrust": (ORANGE, 6, ""), "gravity": (NIGHT, 6, ""), "drag": (GREY, 5, "8 6"),
                      "air": (SKY, 4, "7 6"), "lift": (GREEN, 5, ""), "move": (ORANGE, 3.5, ""),
                      "dim": (NIGHT, 1.6, "")}[kind]
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = 9 + wid * 1.6 if kind != "dim" else 9
    hw = 5 + wid * 0.9 if kind != "dim" else 4.5
    bx, by = x2 - hl * math.cos(ang), y2 - hl * math.sin(ang)
    px, py = -math.sin(ang) * hw, math.cos(ang) * hw
    head = f'<path d="M{x2:.1f} {y2:.1f}L{bx + px:.1f} {by + py:.1f}L{bx - px:.1f} {by - py:.1f}Z" fill="{col}"/>'
    o = f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{col}" stroke-width="{wid}"' \
        + (f' stroke-dasharray="{dash}"' if dash else "") + "/>" + head
    if kind == "dim":   # a head at both ends
        ax, ay = x1 + hl * math.cos(ang), y1 + hl * math.sin(ang)
        o = (f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{col}" stroke-width="{wid}"/>' + head
             + f'<path d="M{x1:.1f} {y1:.1f}L{ax + px:.1f} {ay + py:.1f}L{ax - px:.1f} {ay - py:.1f}Z" fill="{col}"/>')
    if label:
        o += text(lx if lx is not None else x2 + 8, ly if ly is not None else y2, label, anchor, "tb", col if kind != "dim" else NIGHT)
    return o


def text(x, y, s, anchor="start", cls="t", fill=None):
    f = f' style="fill:{fill}"' if fill else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="dg-{cls}"{f}>{s}</text>'


def lines(x, y, rows, anchor="start", cls="t", gap=18):
    return "".join(text(x, y + i * gap, r, anchor, cls) for i, r in enumerate(rows))


def callout(x, y, letter):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" class="dg-n"/>' + text(x, y + 5, letter, "middle", "cl")


def lead(x1, y1, x2, y2):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="dg-lead"/>'


def tagged(x, y, letter, tx, ty):
    """A letter callout at (tx, ty) with a leader to the point (x, y)."""
    return lead(x, y, tx, ty) + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="dg-n"/>' + callout(tx, ty, letter)


def paper_rocket(cx, top, length, w=26, angle=0, fins=True, clay=None, dots=False, fill="w"):
    """A paper rocket, nose at (cx, top) pointing up, then rotated by angle (degrees, clockwise)."""
    l, r, nb, bot = cx - w / 2, cx + w / 2, top + w * 1.3, top + length
    o = [f'<path d="M{l} {nb}L{cx} {top}L{r} {nb}Z" class="dg-{fill}"/>',
         f'<rect x="{l}" y="{nb}" width="{w}" height="{bot - nb}" class="dg-{fill}"/>']
    if fins:
        fl = min(44, length * .32)
        o.append(f'<path d="M{l} {bot - fl}L{l - w * .8} {bot - 3}L{l - w * .8} {bot + 9}L{l} {bot}Z" class="dg-f"/>'
                 f'<path d="M{r} {bot - fl}L{r + w * .8} {bot - 3}L{r + w * .8} {bot + 9}L{r} {bot}Z" class="dg-f"/>'
                 f'<line x1="{cx}" y1="{bot - fl + 4}" x2="{cx}" y2="{bot + 4}" class="dg-o"/>')
    if clay == "nose":
        o.append(f'<ellipse cx="{cx}" cy="{nb - 3}" rx="{w * .28}" ry="{w * .3}" fill="#9A6B3F" stroke="{NIGHT}" stroke-width="1.5"/>')
    if clay == "tail":
        o.append(f'<ellipse cx="{cx}" cy="{bot - 12}" rx="{w * .32}" ry="{w * .3}" fill="#9A6B3F" stroke="{NIGHT}" stroke-width="1.5"/>')
    if dots:
        cg, cp = top + length * .5, top + length * .72
        o.append(f'<circle cx="{cx}" cy="{cg}" r="7" fill="{SKY}" stroke="{NIGHT}" stroke-width="1.5"/>'
                 f'<circle cx="{cx}" cy="{cp}" r="7" fill="{RED}" stroke="{NIGHT}" stroke-width="1.5"/>'
                 f'<path d="M{cx - 4} {cp - 4}l8 8M{cx + 4} {cp - 4}l-8 8" stroke="#fff" stroke-width="1.6"/>')
    g = "".join(o)
    return f'<g transform="rotate({angle} {cx} {top + length / 2})">{g}</g>' if angle else g


def person(x, y, h=120, arm=None, look=None):
    """A stick figure standing at foot point (x, y). arm: (dx, dy) of the hand from the shoulder."""
    hr = h * .09
    neck, hip = y - h + 2 * hr, y - h * .45
    o = [f'<circle cx="{x}" cy="{y - h + hr}" r="{hr}" class="dg-w"/>',
         f'<path d="M{x} {neck}L{x} {hip}M{x} {hip}L{x - h * .14} {y}M{x} {hip}L{x + h * .14} {y}" class="dg-o"/>']
    sh = neck + h * .08
    ax, ay = arm or (h * .25, h * .12)
    o.append(f'<path d="M{x} {sh}L{x + ax} {sh + ay}M{x} {sh}L{x - h * .16} {sh + h * .2}" class="dg-o"/>')
    return "".join(o), (x + ax, sh + ay), (x, y - h + hr)


def chair(x, y, h=110, flip=False):
    s = -1 if flip else 1
    return (f'<path d="M{x} {y}L{x} {y - h * .5}L{x + s * h * .5} {y - h * .5}L{x + s * h * .5} {y}'
            f'M{x} {y - h * .5}L{x} {y - h}" class="dg-o" style="stroke-width:5"/>')


def ground(x1, x2, y):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dg-o"/>' + "".join(
        f'<line x1="{x}" y1="{y}" x2="{x - 8}" y2="{y + 8}" class="dg-lead"/>' for x in range(int(x1) + 10, int(x2), 22))


def panel(x, y, w, h, title=""):
    o = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#FFFDF8" stroke="#E2D9C6" stroke-width="2"/>'
    if title:
        o += text(x + 12, y + 26, title, "start", "th")
    return o


def step_badge(x, y, n):
    return (f'<path d="M{x + 4} {y}h20l4 4v20l-4 4h-20l-4-4v-20Z" fill="{ORANGE}"/>'
            + text(x + 14, y + 20, str(n), "middle", "th"))


def bottle(x, y, w=60, h=110, angle=0):
    """A plastic bottle lying or standing, base at (x, y) bottom-left, cap at the top."""
    g = (f'<path d="M{x} {y}L{x} {y - h * .62}Q{x} {y - h * .78} {x + w * .32} {y - h * .86}L{x + w * .32} {y - h}'
         f'L{x + w * .68} {y - h}L{x + w * .68} {y - h * .86}Q{x + w} {y - h * .78} {x + w} {y - h * .62}L{x + w} {y}Z" class="dg-f"/>'
         f'<rect x="{x + w * .26}" y="{y - h - 9}" width="{w * .48}" height="11" rx="2" class="dg-g"/>')
    return f'<g transform="rotate({angle} {x} {y})">{g}</g>' if angle else g


# ---------------------------------------------------------------- figures
def balloon_setup():
    W, H = 760, 330
    o = [chair(40, 270, 150), chair(720, 270, 150, flip=True), ground(10, 750, 270)]
    o.append(f'<line x1="40" y1="120" x2="720" y2="120" class="dg-thin" style="stroke-width:2"/>')
    o.append(f'<rect x="300" y="113" width="120" height="14" rx="4" class="dg-w"/>')                       # straw
    o.append(f'<ellipse cx="360" cy="168" rx="92" ry="34" class="dg-p"/>')                                     # balloon
    o.append(f'<path d="M268 168 L252 158 L252 178 Z" class="dg-p"/>')                                          # neck
    o.append(f'<rect x="318" y="122" width="12" height="28" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.5"/>'
             f'<rect x="392" y="122" width="12" height="28" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.5"/>')  # tape
    o.append(f'<rect x="232" y="160" width="18" height="16" rx="3" class="dg-g"/>')                            # clip
    o.append(f'<rect x="96" y="112" width="8" height="16" fill="{ORANGE}"/>')                                   # start mark
    o.append(arrow(230, 210, 120, 210, "air", "air rushes out", 175, 236, "middle"))
    o.append(arrow(470, 210, 610, 210, "thrust", "thrust", 540, 236, "middle"))
    o.append(arrow(104, 296, 300, 296, "dim", "") + text(202, 320, "measure from the start line", "middle", "ts"))
    o += [tagged(70, 120, "A", 70, 70), tagged(360, 113, "B", 360, 66), tagged(400, 190, "C", 470, 166),
          tagged(320, 136, "D", 286, 66), tagged(241, 160, "E", 222, 116), tagged(100, 112, "F", 140, 70)]
    return _svg(W, H, "".join(o), "Balloon rocket on a string between two chairs")


def balloon_steps():
    W, H = 760, 210
    o = []
    for i, (t, d) in enumerate([("Thread", "string through the straw"), ("Tie", "string tight, 4 m or more"),
                                ("Blow up", "pinch or clip the end"), ("Tape", "balloon to the straw")]):
        x = 8 + i * 188
        o.append(panel(x, 6, 178, 196) + step_badge(x + 10, 16, i + 1) + text(x + 46, 36, t, "start", "th"))
        o.append(text(x + 89, 190, d, "middle", "ts"))
        cx = x + 89
        if i == 0:
            o.append(f'<line x1="{x + 14}" y1="110" x2="{x + 164}" y2="110" class="dg-thin" style="stroke-width:2"/>'
                     f'<rect x="{cx - 40}" y="103" width="80" height="14" rx="4" class="dg-w"/>'
                     + arrow(cx + 50, 90, cx + 74, 90, "move"))
        elif i == 1:
            o.append(chair(x + 22, 168, 90) + chair(x + 156, 168, 90, flip=True)
                     + f'<line x1="{x + 22}" y1="96" x2="{x + 156}" y2="96" class="dg-thin" style="stroke-width:2"/>')
        elif i == 2:
            o.append(f'<ellipse cx="{cx + 6}" cy="112" rx="52" ry="24" class="dg-p"/><path d="M{cx - 46} 112 L{cx - 58} 104 L{cx - 58} 120 Z" class="dg-p"/>'
                     f'<rect x="{cx - 72}" y="104" width="14" height="16" rx="3" class="dg-g"/>')
        else:
            o.append(f'<line x1="{x + 14}" y1="78" x2="{x + 164}" y2="78" class="dg-thin" style="stroke-width:2"/>'
                     f'<rect x="{cx - 40}" y="71" width="80" height="14" rx="4" class="dg-w"/>'
                     f'<ellipse cx="{cx}" cy="122" rx="56" ry="26" class="dg-p"/>'
                     f'<rect x="{cx - 28}" y="84" width="9" height="22" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.3"/>'
                     f'<rect x="{cx + 19}" y="84" width="9" height="22" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.3"/>')
    return _svg(W, H, "".join(o), "Four steps to set up a balloon rocket")


def straw_build():
    W, H = 760, 230
    o = []
    steps = [("Roll", "paper strip around a pencil"), ("Close", "fold the top twice, tape"),
             ("Fins", "tape 3 small fins"), ("Launch", "slide on a straw, one puff")]
    for i, (t, d) in enumerate(steps):
        x = 8 + i * 188
        cx = x + 89
        o.append(panel(x, 6, 178, 216) + step_badge(x + 10, 16, i + 1) + text(x + 46, 36, t, "start", "th")
                 + text(cx, 210, d, "middle", "ts"))
        if i == 0:
            o.append(f'<g transform="rotate(-20 {cx} 120)"><rect x="{cx - 70}" y="96" width="140" height="44" class="dg-w"/>'
                     f'<rect x="{cx - 76}" y="112" width="152" height="12" rx="3" fill="#F0B44C" stroke="{NIGHT}" stroke-width="2"/>'
                     f'<path d="M{cx - 76} 112 L{cx - 90} 118 L{cx - 76} 124 Z" class="dg-g"/></g>'
                     + arrow(cx + 20, 168, cx - 30, 168, "move"))
        elif i == 1:
            o.append(f'<rect x="{cx - 12}" y="78" width="24" height="100" class="dg-w"/>'
                     f'<path d="M{cx - 12} 78 L{cx + 12} 78 L{cx + 12} 66 L{cx - 12} 72 Z" class="dg-w"/>'
                     f'<rect x="{cx - 16}" y="70" width="32" height="10" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.3"/>'
                     + text(cx + 22, 76, "tape", "start", "ts") + text(cx + 22, 92, "airtight", "start", "ts"))
        elif i == 2:
            o.append(paper_rocket(cx, 56, 120, 24))
        else:
            o.append(paper_rocket(cx, 46, 110, 22) + f'<rect x="{cx - 3}" y="120" width="6" height="64" class="dg-g"/>'
                     + arrow(cx + 26, 116, cx + 26, 56, "move"))
    return _svg(W, H, "".join(o), "How to build a straw rocket")


def straw_forces():
    W, H = 760, 330
    o = []
    for i, t in enumerate(["1. Launch", "2. Going up", "3. Top (apogee)", "4. Coming down"]):
        x = 8 + i * 188
        cx = x + 89
        o.append(panel(x, 6, 178, 316, t))
        if i == 0:
            o.append(paper_rocket(cx, 110, 110, 22) + f'<rect x="{cx - 3}" y="200" width="6" height="90" class="dg-g"/>'
                     + arrow(cx + 46, 230, cx + 46, 120, "thrust", "thrust", cx + 46, 112, "middle")
                     + arrow(cx - 46, 150, cx - 46, 240, "gravity", "gravity", cx - 46, 262, "middle"))
        elif i == 1:
            o.append(paper_rocket(cx, 100, 110, 22)
                     + arrow(cx - 46, 150, cx - 46, 240, "gravity", "gravity", cx - 46, 262, "middle")
                     + arrow(cx + 46, 90, cx + 46, 150, "drag", "drag", cx + 46, 172, "middle")
                     + text(cx, 300, "slowing down", "middle", "ts"))
        elif i == 2:
            o.append(paper_rocket(cx, 110, 110, 22, angle=90)
                     + arrow(cx, 200, cx, 270, "gravity", "gravity", cx, 292, "middle")
                     + text(cx, 70, "stops for a moment", "middle", "ts"))
        else:
            o.append(paper_rocket(cx, 110, 110, 22, angle=180)
                     + arrow(cx - 46, 150, cx - 46, 240, "gravity", "gravity", cx - 46, 262, "middle")
                     + arrow(cx + 46, 240, cx + 46, 170, "drag", "drag", cx + 46, 160, "middle"))
    return _svg(W, H, "".join(o), "Forces on a straw rocket in four parts of its flight")


def squeeze_launcher():
    W, H = 760, 370
    o = [ground(10, 750, 262)]
    o.append(f'<rect x="40" y="196" width="230" height="66" class="dg-g"/>')
    bx, by = 226, 171
    # Protractor (half disc) taped to the box, centred on the straw's base; the bottle lies in front of it.
    o.append(f'<path d="M{bx - 70} {by + 25} A70 70 0 0 1 {bx + 70} {by + 25} Z" fill="#FFFDF8" stroke="{NIGHT}" stroke-width="1.6"/>')
    for a in range(0, 181, 15):
        r1, r2 = 70, 60 if a % 45 else 52
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        o.append(f'<line x1="{bx + r1 * ca:.1f}" y1="{by + 25 - r1 * sa:.1f}" x2="{bx + r2 * ca:.1f}" y2="{by + 25 - r2 * sa:.1f}" class="dg-thin"/>')
    o.append(f'<path d="M70 192 L70 150 L180 150 Q196 150 204 162 L214 162 L214 180 L204 180 Q196 192 180 192 Z" class="dg-f"/>'
             f'<rect x="214" y="160" width="12" height="22" rx="2" class="dg-g"/>')
    ex, ey = bx + 150 * math.cos(math.radians(45)), by - 150 * math.sin(math.radians(45))
    o.append(f'<line x1="{bx}" y1="{by}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#E2D9C6" stroke-width="7"/>'
             f'<line x1="{bx}" y1="{by}" x2="{ex:.1f}" y2="{ey:.1f}" class="dg-thin"/>')
    o.append(paper_rocket(ex + 18, ey - 80, 95, 18, angle=45))
    o.append(text(bx + 46, by - 2, "45°", "start", "tb"))
    o.append(f'<path d="M{ex + 60:.0f} {ey - 40:.0f} Q560 -60 735 255" class="dg-dash"/>' + text(600, 60, "flight path", "middle", "ts"))
    o.append(arrow(bx, 288, 735, 288, "dim") + text(480, 280, "distance: launch spot to where it first lands", "middle", "ts"))
    o += [tagged(120, 170, "A", 100, 110), tagged(bx + 56, by + 12, "B", 330, 170), tagged(ex + 10, ey - 40, "C", ex - 70, ey - 70)]
    o.append(text(60, 240, "box", "start", "ts"))
    return _svg(W, H, '<g transform="translate(0 64)">' + "".join(o) + "</g>", "A squeeze-bottle launcher held at 45 degrees on a protractor")


def angle_paths():
    W, H = 760, 270
    o = [ground(10, 750, 230)]
    x0, rmax, vs = 60, 620, .55
    for a, c, dash in ((30, SKY, False), (45, ORANGE, False), (60, GREEN, True), (75, NIGHT, True)):
        r = rmax * math.sin(math.radians(2 * a))
        h = r * math.tan(math.radians(a)) / 4 * vs
        o.append(f'<path d="M{x0} 230 Q{x0 + r / 2:.0f} {230 - 2 * h:.0f} {x0 + r:.0f} 230" fill="none" stroke="{c}" stroke-width="3.5"'
                 + (' stroke-dasharray="9 6"' if dash else "") + "/>")
        o.append(text(x0 + r / 2, 230 - h - 8, f"{a}°", "middle", "tb", c if c != NIGHT else None))
    o.append(text(700, 40, "45° goes farthest.", "end", "tb") + text(700, 60, "30° and 60° land near the same spot;", "end", "ts")
             + text(700, 76, "steeper goes higher but shorter.", "end", "ts"))
    return _svg(W, H, "".join(o), "Flight paths at 30, 45, 60 and 75 degrees")


def balance_point():
    W, H = 760, 230
    o = [panel(6, 6, 360, 218, "Find the balance point"), panel(392, 6, 362, 218, "Blue in front of red")]
    o.append(paper_rocket(186, 40, 200, 28, angle=90))
    o.append(f'<path d="M186 156 l-12 44 h24 Z" class="dg-w"/>' + text(186, 214, "your finger", "middle", "ts"))
    o.append(f'<circle cx="186" cy="140" r="7" fill="{SKY}" stroke="{NIGHT}" stroke-width="1.5"/>')
    o.append(text(186, 76, "balance point (blue dot)", "middle", "tb", "#1D5BC4") + lead(186, 82, 186, 132))
    o.append(paper_rocket(573, 20, 200, 28, angle=90, dots=True))
    o.append(text(690, 176, "nose →", "middle", "ts"))
    o.append(lead(573, 140, 573, 176) + text(573, 192, "balance point", "middle", "tb", "#1D5BC4"))
    o.append(lead(529, 140, 520, 86) + text(520, 78, "push point", "middle", "tb", "#C22E33"))
    return _svg(W, H, "".join(o), "Balancing a rocket on a finger; the blue balance point in front of the red push point")


def swing_test():
    W, H = 760, 350
    o = [ground(10, 750, 300)]
    p, hand, head = person(250, 300, 170, arm=(22, -78))
    o.append(p)
    hx, hy = hand
    o.append(f'<ellipse cx="{hx}" cy="{hy + 30}" rx="230" ry="46" class="dg-dash"/>')
    rx, ry = hx + 170, hy + 70
    o.append(f'<line x1="{hx}" y1="{hy}" x2="{rx}" y2="{ry - 2}" class="dg-thin" style="stroke-width:1.8"/>')
    o.append(paper_rocket(rx, ry - 60, 120, 20, angle=-90))
    o.append(arrow(rx - 70, ry - 30, rx - 130, ry - 30, "move") + text(rx - 100, ry - 42, "nose leads", "middle", "tb"))
    o.append(text(rx, ry + 40, "string about 1 m long", "middle", "ts"))
    o.append(arrow(250, 326, 540, 326, "dim") + text(395, 346, "nobody within 3 m", "middle", "ts"))
    o.append(panel(560, 130, 192, 150, "Tie it here"))
    o.append(paper_rocket(656, 140, 150, 22, angle=90))
    o.append(f'<line x1="656" y1="216" x2="656" y2="168" class="dg-thin" style="stroke-width:2"/>'
             f'<circle cx="656" cy="216" r="6" fill="{SKY}" stroke="{NIGHT}" stroke-width="1.5"/>'
             + text(656, 268, "at the balance point", "middle", "ts"))
    return _svg(W, H, "".join(o), "Swing test: swing the rocket in a circle on a string tied at its balance point")


def rocket_versions():
    W, H = 760, 270
    o = []
    for i, (k, t, f, c) in enumerate([("A", "no fins", False, None), ("B", "fins", True, None),
                                      ("C", "fins + clay in nose", True, "nose"), ("D", "fins + clay in tail", True, "tail")]):
        x = 8 + i * 188
        o.append(panel(x, 6, 178, 256) + callout(x + 24, 30, k) + text(x + 44, 35, t, "start", "tb"))
        o.append(paper_rocket(x + 89, 56, 170, 30, fins=f, clay=c))
    return _svg(W, H, "".join(o), "Four test rockets: A no fins, B fins, C clay in the nose, D clay in the tail")


def weathervane():
    W, H = 760, 270
    o = [panel(6, 6, 370, 258, "Stable: tail swings back"), panel(386, 6, 368, 258, "Unstable: it tumbles")]
    for x0, stable in ((190, True), (570, False)):
        cg, cp = (110, 165) if stable else (165, 110)
        o.append(f'<g transform="rotate(-25 {x0} 135)">{paper_rocket(x0, 55, 160, 26)}'
                 f'<circle cx="{x0}" cy="{cg}" r="7" fill="{SKY}" stroke="{NIGHT}" stroke-width="1.5"/>'
                 f'<circle cx="{x0}" cy="{cp}" r="7" fill="{RED}" stroke="{NIGHT}" stroke-width="1.5"/></g>')
        o.append(arrow(x0 + 150, 196, x0 + 70, 196, "air", "air from the side", x0 + 110, 226, "middle"))
        o.append(text(x0 - 150, 60, "blue in front of red" if stable else "red in front of blue", "start", "ts"))
    o.append(text(190, 252, "air pushes the tail back in line", "middle", "ts") + text(570, 252, "air swings the nose away", "middle", "ts"))
    return _svg(W, H, "".join(o), "When the push point is behind the balance point, air swings the tail back in line")


def stomp_launcher():
    W, H = 760, 300
    o = [ground(10, 750, 270)]
    o.append(f'<path d="M40 268 L40 222 Q40 214 48 214 L170 214 Q186 214 196 230 L212 234 L212 252 L196 256 Q186 268 170 268 Z" class="dg-f"/>')
    o.append(f'<path d="M212 236 L420 236 L420 120" fill="none" stroke="#E2D9C6" stroke-width="18" stroke-linejoin="round"/>'
             f'<path d="M212 227 L411 227 L411 120 M212 245 L429 245 L429 120" class="dg-o"/>')
    o.append(f'<rect x="204" y="224" width="22" height="24" fill="#B8B0A0" stroke="{NIGHT}" stroke-width="1.5"/>')
    o.append(paper_rocket(420, 30, 110, 26))
    o.append(arrow(300, 236, 395, 236, "air") + arrow(420, 210, 420, 152, "air"))
    o.append(f'<path d="M80 178 l12 26 M110 172 l0 30 M140 178 l-12 26" stroke="{ORANGE}" stroke-width="4"/>' + text(110, 164, "stomp!", "middle", "tb"))
    o.append(arrow(600, 150, 480, 70, "thrust", "the rocket shoots up", 560, 170, "middle"))
    o += [tagged(110, 240, "A", 70, 140), tagged(320, 245, "B", 320, 290), tagged(215, 236, "D", 236, 190), tagged(420, 100, "C", 360, 60)]
    return _svg(W, H, "".join(o), "Stomp-rocket launcher: a bottle taped to a pipe")


def stomp_build():
    W, H = 760, 230
    o = []
    for i, (t, d) in enumerate([("Roll", "paper around the pipe"), ("Nose", "twist and tape airtight"),
                                ("Fins", "cut from the index card"), ("Name", "write it, then test")]):
        x = 8 + i * 188
        cx = x + 89
        o.append(panel(x, 6, 178, 216) + step_badge(x + 10, 16, i + 1) + text(x + 46, 36, t, "start", "th") + text(cx, 210, d, "middle", "ts"))
        if i == 0:
            o.append(f'<rect x="{cx - 9}" y="56" width="18" height="130" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="2"/>'
                     f'<rect x="{cx - 34}" y="80" width="68" height="90" class="dg-w" opacity=".9"/>' + arrow(cx + 44, 120, cx + 44, 150, "move"))
        elif i == 1:
            o.append(f'<rect x="{cx - 16}" y="90" width="32" height="96" class="dg-w"/><path d="M{cx - 16} 90 L{cx} 58 L{cx + 16} 90 Z" class="dg-w"/>'
                     f'<rect x="{cx - 18}" y="70" width="36" height="10" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.3"/>')
        elif i == 2:
            o.append(f'<rect x="{cx - 60}" y="60" width="120" height="76" class="dg-w"/>'
                     f'<path d="M{cx - 50} 128 L{cx - 50} 76 L{cx - 10} 128 Z M{cx + 10} 128 L{cx + 10} 76 L{cx + 50} 128 Z" class="dg-f" style="stroke-dasharray:5 4"/>'
                     + text(cx, 160, "cut 3", "middle", "tb"))
        else:
            o.append(paper_rocket(cx, 50, 140, 28) + text(cx, 140, "ZOE", "middle", "tb"))
    return _svg(W, H, "".join(o), "How to build a stomp rocket")


def parachute_build():
    W, H = 760, 250
    o = []
    for i, (t, d) in enumerate([("Cut", "a square of plastic bag"), ("Tape", "a string to each corner"),
                                ("Tie", "4 strings to the washers"), ("Drop", "hold the middle, let go")]):
        x = 8 + i * 188
        cx = x + 89
        o.append(panel(x, 6, 178, 236) + step_badge(x + 10, 16, i + 1) + text(x + 46, 36, t, "start", "th") + text(cx, 230, d, "middle", "ts"))
        if i == 0:
            o.append(f'<rect x="{cx - 50}" y="60" width="100" height="100" class="dg-p"/>' + arrow(cx - 50, 176, cx + 50, 176, "dim")
                     + text(cx, 198, "20, 30 or 40 cm", "middle", "ts"))
        elif i == 1:
            o.append(f'<rect x="{cx - 50}" y="60" width="100" height="100" class="dg-p"/>'
                     + "".join(f'<rect x="{px - 7}" y="{py - 7}" width="14" height="14" fill="#E2D9C6" stroke="{NIGHT}" stroke-width="1.3"/>'
                               f'<line x1="{px}" y1="{py}" x2="{px + dx}" y2="{py + 30}" class="dg-thin"/>'
                               for px, py, dx in ((cx - 50, 60, -14), (cx + 50, 60, 14), (cx - 50, 160, -14), (cx + 50, 160, 14))))
        elif i == 2:
            o.append(f'<path d="M{cx - 60} 90 Q{cx} 50 {cx + 60} 90 Z" class="dg-p"/>'
                     + "".join(f'<line x1="{cx + dx}" y1="90" x2="{cx}" y2="170" class="dg-thin"/>' for dx in (-60, -20, 20, 60))
                     + f'<circle cx="{cx}" cy="178" r="9" class="dg-g"/><circle cx="{cx}" cy="188" r="9" class="dg-g"/>' + text(cx + 16, 192, "washers", "start", "ts"))
        else:
            o.append(f'<path d="M{cx - 50} 102 Q{cx} 52 {cx + 50} 102 Z" class="dg-p"/>'
                     + "".join(f'<line x1="{cx + dx}" y1="102" x2="{cx}" y2="166" class="dg-thin"/>' for dx in (-50, -17, 17, 50))
                     + f'<circle cx="{cx}" cy="172" r="8" class="dg-g"/>'
                     + arrow(cx + 66, 120, cx + 66, 196, "gravity", "gravity", cx + 66, 214, "middle")
                     + arrow(cx - 66, 150, cx - 66, 72, "drag", "drag", cx - 66, 64, "middle"))
    return _svg(W, H, "".join(o), "How to make a parachute")


def drop_test():
    W, H = 760, 320
    o = [ground(10, 750, 296)]
    o.append(f'<path d="M150 296 L170 220 L230 220 L250 296 M162 258 H238" class="dg-o" style="stroke-width:4"/>' + text(200, 312, "step stool", "middle", "ts"))
    p, hand, head = person(200, 220, 150, arm=(40, -60))
    o.append(p)
    hx, hy = hand
    o.append(f'<path d="M{hx - 44} {hy + 26} Q{hx} {hy - 14} {hx + 44} {hy + 26} Z" class="dg-p"/>'
             + "".join(f'<line x1="{hx + dx}" y1="{hy + 26}" x2="{hx}" y2="{hy + 78}" class="dg-thin"/>' for dx in (-44, -14, 14, 44))
             + f'<circle cx="{hx}" cy="{hy + 84}" r="7" class="dg-g"/>')
    o.append(arrow(hx + 70, hy + 84, hx + 70, 296, "dim") + text(hx + 80, (hy + 380) / 2, "drop height:", "start", "tb")
             + text(hx + 80, (hy + 380) / 2 + 18, "about 2 m", "start", "t"))
    p2, h2, _ = person(560, 296, 120, arm=(-26, 6))
    o.append(p2 + f'<rect x="{h2[0] - 14}" y="{h2[1] - 10}" width="20" height="26" rx="4" class="dg-g"/>'
             + text(560, 150, "timer: start on “drop!”,", "middle", "ts") + text(560, 166, "stop when it lands", "middle", "ts"))
    o.append(f'<rect x="20" y="20" width="250" height="34" rx="6" fill="#FCE3E3" stroke="{RED}" stroke-width="2"/>'
             + text(145, 42, "An adult does the dropping", "middle", "tb"))
    return _svg(W, H, "".join(o), "Parachute drop test: an adult drops it, a student times it")


def sight45():
    W, H = 760, 420
    gy = 390
    o = [ground(10, 750, gy)]
    p, hand, head = person(180, gy, 130, arm=(24, -8))
    o.append(p)
    ex, ey = head[0] + 12, head[1]
    lx = ex + 200
    o.append(f'<path d="M{ex} {ey} L{ex + 34} {ey} L{ex + 34} {ey - 34} Z" class="dg-w"/>')
    o.append(f'<line x1="{ex}" y1="{ey}" x2="{lx + 40}" y2="{ey - 240}" stroke="{ORANGE}" stroke-width="2.5" stroke-dasharray="10 7"/>')
    o.append(text(ex + 120, ey - 150, "45° line", "end", "tb", "#B8471B"))
    o.append(text(ex - 20, ey - 40, "card: bottom edge level", "end", "ts"))
    o.append(f'<rect x="{lx - 18}" y="{gy - 12}" width="36" height="12" class="dg-g"/>' + text(lx + 26, gy - 14, "launcher", "start", "ts"))
    o.append(f'<line x1="{lx}" y1="{gy - 12}" x2="{lx}" y2="20" class="dg-lead" style="stroke-dasharray:4 5"/>')
    o.append(paper_rocket(lx, 4, 42, 16) + text(lx + 22, 26, "above the line:", "start", "tb") + text(lx + 22, 44, "higher than 10 m", "start", "t"))
    o.append(paper_rocket(lx, ey - 150, 50, 14, fins=True) + text(lx + 22, ey - 126, "below the line:", "start", "tb") + text(lx + 22, ey - 108, "lower than 10 m", "start", "t"))
    o.append(arrow(180, gy + 18, lx - 20, gy + 18, "dim") + text((180 + lx) / 2, gy - 8, "10 m (measure it)", "middle", "tb"))
    o.append(panel(540, 230, 210, 140, "Fold a square"))
    o.append(f'<rect x="560" y="266" width="70" height="70" class="dg-w"/><line x1="560" y1="336" x2="630" y2="266" stroke="{ORANGE}" stroke-width="3" stroke-dasharray="7 5"/>'
             + arrow(640, 302, 664, 302, "move") + f'<path d="M674 336 L674 270 L734 336 Z" class="dg-w"/>'
             + text(645, 360, "corner to corner", "middle", "ts"))
    return _svg(W, H, "".join(o), "A 45 degree sighting card: if the rocket goes above the line, it is higher than your distance")


def flight_phases():
    W, H = 760, 340
    o = []
    for i, t in enumerate(["1. On the pad", "2. Boost", "3. Coast", "4. Parachute"]):
        x = 8 + i * 188
        cx = x + 89
        o.append(panel(x, 6, 178, 326, t))
        if i == 0:
            o.append(paper_rocket(cx, 100, 140, 24) + f'<line x1="{cx + 18}" y1="60" x2="{cx + 18}" y2="270" class="dg-thin"/>'
                     f'<rect x="{cx - 40}" y="268" width="80" height="10" class="dg-g"/>'
                     + arrow(cx - 50, 150, cx - 50, 240, "gravity", "weight", cx - 50, 300, "middle")
                     + arrow(cx + 50, 250, cx + 50, 160, "move", "pad", cx + 50, 300, "middle")
                     + text(cx + 50, 316, "pushes up", "middle", "ts"))
        elif i == 1:
            o.append(paper_rocket(cx, 90, 140, 24) + f'<path d="M{cx - 8} 242 Q{cx} 296 {cx + 8} 242 Z" fill="{ORANGE}"/>'
                     + arrow(cx + 50, 240, cx + 50, 80, "thrust", "thrust", cx + 50, 300, "middle")
                     + arrow(cx - 50, 150, cx - 50, 240, "gravity", "weight", cx - 50, 300, "middle")
                     + arrow(cx - 50, 60, cx - 50, 110, "drag", "", 0, 0) + text(cx - 50, 130, "drag", "middle", "tb", GREY))
        elif i == 2:
            o.append(paper_rocket(cx, 90, 140, 24)
                     + arrow(cx - 50, 150, cx - 50, 240, "gravity", "weight", cx - 50, 300, "middle")
                     + arrow(cx + 50, 60, cx + 50, 120, "drag", "drag", cx + 50, 140, "middle")
                     + text(cx, 320, "no thrust: slowing", "middle", "ts"))
        else:
            o.append(f'<path d="M{cx - 60} 110 Q{cx} 50 {cx + 60} 110 Z" class="dg-p"/>'
                     + "".join(f'<line x1="{cx + dx}" y1="110" x2="{cx}" y2="170" class="dg-thin"/>' for dx in (-60, -20, 20, 60))
                     + paper_rocket(cx, 140, 100, 18, angle=90)
                     + arrow(cx, 100, cx, 52, "drag", "drag", cx + 24, 64)
                     + arrow(cx + 50, 220, cx + 50, 280, "gravity", "weight", cx + 50, 300, "middle")
                     + text(cx, 320, "balanced: steady speed", "middle", "ts"))
    return _svg(W, H, "".join(o), "Forces on a model rocket on the pad, in boost, in coast and under the parachute")


def cg_cp_calibers():
    W, H = 760, 220
    y0, y1 = 80, 120
    cg, cp = 330, 330 + 2 * 40
    o = [f'<path d="M140 {y0} C100 {y0} 60 92 30 100 C60 108 100 {y1} 140 {y1} Z" class="dg-w"/>',
         f'<rect x="140" y="{y0}" width="420" height="40" class="dg-w"/>',
         f'<path d="M470 {y0} L540 26 L568 26 L560 {y0} Z" class="dg-f"/><path d="M470 {y1} L540 174 L568 174 L560 {y1} Z" class="dg-f"/>',
         f'<rect x="560" y="88" width="16" height="24" class="dg-g"/>' + text(600, 104, "heavy motor", "start", "ts"),
         f'<circle cx="{cg}" cy="100" r="9" fill="{SKY}" stroke="{NIGHT}" stroke-width="1.5"/>',
         f'<circle cx="{cp}" cy="100" r="9" fill="{RED}" stroke="{NIGHT}" stroke-width="1.5"/><path d="M{cp - 5} 95l10 10M{cp + 5} 95l-10 10" stroke="#fff" stroke-width="2"/>',
         lead(cg, 88, cg, 50) + text(cg, 42, "CG (balance point)", "middle", "tb", "#1D5BC4"),
         lead(cp, 112, cp, 150) + text(cp, 166, "CP (push point)", "middle", "tb", "#C22E33"),
         arrow(cg, 196, cp, 196, "dim") + text(cp + 12, 202, "gap = 2 body widths = 2 cal", "start", "tb"),
         arrow(170, y0, 170, y1, "dim") + text(180, 140, "1 cal = body width", "start", "ts"),
         arrow(150, 30, 60, 30, "move") + text(160, 35, "flies this way", "start", "ts")]
    return _svg(W, H, "".join(o), "Stability margin: the CG is 2 body widths in front of the CP")


def inclinometer_trig():
    W, H = 760, 320
    o = [ground(10, 750, 280)]
    p, hand, head = person(80, 280, 130, arm=(24, -10))
    o.append(p)
    ex, ey = head[0] + 10, head[1]
    tx = 560
    ang = math.atan2(ey - 40, tx - ex)
    o.append(f'<line x1="{ex}" y1="{ey}" x2="{tx}" y2="40" stroke="{SKY}" stroke-width="2.5" stroke-dasharray="9 6"/>')
    o.append(f'<line x1="{ex}" y1="{ey}" x2="{tx}" y2="{ey}" class="dg-lead" style="stroke-dasharray:5 5"/>')
    o.append(f'<path d="M{ex + 70} {ey} A70 70 0 0 0 {ex + 70 * math.cos(ang):.1f} {ey - 70 * math.sin(ang):.1f}" fill="none" stroke="{ORANGE}" stroke-width="3"/>'
             + text(ex + 80, ey - 12, "angle", "start", "tb", "#B8471B"))
    o.append(f'<line x1="{tx}" y1="280" x2="{tx}" y2="44" class="dg-thin" style="stroke-dasharray:4 5"/>')
    o.append(paper_rocket(tx, 18, 40, 12, fins=False))
    o.append(f'<rect x="{tx - 16}" y="270" width="32" height="10" class="dg-g"/>' + text(tx, 300, "pad", "middle", "ts"))
    o.append(arrow(80, 304, tx - 18, 304, "dim") + text(320, 298, "baseline (measure it)", "middle", "tb"))
    o.append(arrow(tx + 16, 44, tx + 16, ey - 2, "dim") + text(tx + 28, 120, "height above eye =", "start", "tb")
             + text(tx + 28, 138, "baseline × tan(angle)", "start", "t"))
    o.append(arrow(tx + 16, ey + 2, tx + 16, 278, "dim") + text(tx + 28, (ey + 280) / 2 + 5, "+ eye height", "start", "t"))
    return _svg(W, H, "".join(o), "Measuring height with an angle: height = baseline times tan(angle) plus eye height")


def energy_path():
    W, H = 760, 300
    o = [ground(10, 750, 270), f'<path d="M80 270 Q300 -40 520 40 Q620 70 660 240" class="dg-arc"/>']
    o.append(f'<circle cx="80" cy="262" r="7" fill="{ORANGE}" stroke="{NIGHT}" stroke-width="1.5"/>'
             + text(100, 250, "On the pad", "start", "tb") + text(100, 266, "energy stored in the propellant", "start", "ts"))
    o.append(f'<circle cx="150" cy="168" r="7" fill="{ORANGE}" stroke="{NIGHT}" stroke-width="1.5"/>'
             + text(170, 176, "Boost", "start", "tb") + text(170, 192, "the motor transfers energy:", "start", "ts")
             + text(170, 207, "kinetic and potential grow", "start", "ts"))
    o.append(f'<circle cx="430" cy="24" r="7" fill="{ORANGE}" stroke="{NIGHT}" stroke-width="1.5"/>'
             + text(430, 54, "Apogee", "middle", "tb") + text(430, 70, "most potential energy", "middle", "ts"))
    o.append(text(250, 120, "Coast: kinetic → potential", "start", "ts") + text(250, 135, "(and heat from drag)", "start", "ts"))
    o.append(f'<circle cx="640" cy="170" r="7" fill="{ORANGE}" stroke="{NIGHT}" stroke-width="1.5"/>'
             + text(624, 176, "Parachute", "end", "tb") + text(624, 192, "drag takes energy away", "end", "ts"))
    return _svg(W, H, "".join(o), "Where the energy is during a flight")


def launch_site():
    W, H = 760, 330
    o = [f'<rect x="6" y="6" width="748" height="318" rx="10" fill="#DCF3E8" stroke="{GREEN}" stroke-width="2"/>']
    px, py = 380, 150
    o.append(f'<circle cx="{px}" cy="{py}" r="70" fill="none" stroke="{RED}" stroke-width="2.5" stroke-dasharray="8 6"/>'
             + text(px, py - 78, "15 ft (5 m): nobody inside when armed", "middle", "ts"))
    o.append(f'<rect x="{px - 10}" y="{py - 10}" width="20" height="20" class="dg-g"/>' + text(px, py + 30, "pad", "middle", "tb"))
    o.append(f'<line x1="120" y1="280" x2="640" y2="280" stroke="{NIGHT}" stroke-width="3" stroke-dasharray="14 8"/>' + text(380, 304, "spectator line (class stays behind it)", "middle", "tb"))
    o.append(f'<rect x="{px - 16}" y="232" width="32" height="20" rx="4" class="dg-w"/>' + text(px + 22, 247, "controller + key (adult)", "start", "ts"))
    o.append(f'<line x1="{px}" y1="{py + 10}" x2="{px}" y2="232" class="dg-thin" style="stroke-dasharray:3 3"/>')
    for x, y, t in ((110, 150, "tracker 1"), (650, 150, "tracker 2")):
        o.append(f'<circle cx="{x}" cy="{y}" r="9" class="dg-w"/>' + text(x, y + 28, t, "middle", "ts"))
    o.append(arrow(119, 150, px - 14, 150, "dim") + text(240, 142, "baseline", "middle", "ts"))
    o.append(arrow(80, 40, 200, 40, "air", "wind", 140, 30, "middle"))
    o.append(text(560, 44, "no trees, power lines,", "middle", "ts") + text(560, 60, "roads or dry grass", "middle", "ts"))
    return _svg(W, H, "".join(o), "Launch site layout: pad, 15-foot circle, spectator line and trackers")


def nickel_test():
    W, H = 760, 330
    o = [panel(6, 6, 748, 318, "Nose fit: the coin breakout test")]
    bx = 360
    o.append(f'<rect x="{bx - 22}" y="50" width="44" height="120" class="dg-w"/>' + text(bx - 34, 100, "body section,", "end", "ts") + text(bx - 34, 116, "held nose-down", "end", "ts"))
    o.append(f'<rect x="{bx - 16}" y="150" width="32" height="20" class="dg-f" style="stroke-dasharray:4 3"/><path d="M{bx - 22} 170 Q{bx} 222 {bx + 22} 170 Z" class="dg-f"/>'
             + text(bx + 34, 196, "nose, shoulder pushed in", "start", "ts"))
    o.append(f'<line x1="{bx}" y1="210" x2="{bx}" y2="236" class="dg-thin" style="stroke-width:2"/>' + text(bx + 10, 228, "cord tied to the nose's tie bar", "start", "ts"))
    o.append(f'<path d="M{bx - 34} 236 h68 l6 72 h-80 Z" class="dg-w"/>' + text(bx - 46, 270, "zip bag", "end", "ts"))
    for i in range(5):
        o.append(f'<ellipse cx="{bx}" cy="{296 - i * 9}" rx="22" ry="5" class="dg-g"/>')
    o.append(text(bx + 60, 270, "add nickels (5 g each) until the nose pulls out", "start", "tb")
             + text(bx + 60, 290, "M18 Starter: about 4–5; the build notes give each size", "start", "ts"))
    return _svg(W, H, "".join(o), "Coin breakout test for the nose fit")


FIGURES = {
    "balloon-setup": (balloon_setup, "The setup. A string tied tight between two chairs · B straw on the string · C balloon · D tape · E clip holds the air in · F start line."),
    "balloon-steps": (balloon_steps, "Setting up, step by step."),
    "straw-build": (straw_build, "Building a straw rocket."),
    "straw-forces": (straw_forces, "The forces in each part of the flight. Orange: thrust. Navy: gravity (weight). Dashed grey: drag."),
    "squeeze-launcher": (squeeze_launcher, "The angle test. A squeeze bottle with a straw sealed into the cap · B protractor on a box · C straw rocket."),
    "angle-paths": (angle_paths, "What to expect: the paths at each angle."),
    "balance-point": (balance_point, "Find the balance point on a finger. The blue dot (balance point) must be in front of the red dot (push point)."),
    "swing-test": (swing_test, "The swing test: string tied at the balance point, swing it in a circle, watch the nose."),
    "rocket-versions": (rocket_versions, "The four test rockets."),
    "weathervane": (weathervane, "Why the rule works: if the push point is behind the balance point, the air swings the tail back in line, like a weathervane."),
    "stomp-launcher": (stomp_launcher, "The stomp launcher. A 2-litre bottle · B pipe · C paper rocket slid over the pipe · D duct tape, airtight."),
    "stomp-build": (stomp_build, "Building a stomp rocket."),
    "parachute-build": (parachute_build, "Making a parachute."),
    "drop-test": (drop_test, "The drop test."),
    "sight45": (sight45, "Tracking with a 45° card: stand 10 m from the launcher and look up the folded edge."),
    "flight-phases": (flight_phases, "Forces in the four parts of a flight. Balanced on the pad and under the parachute; unbalanced in boost and coast."),
    "cg-cp": (cg_cp_calibers, "Stability margin in calibers: the gap between the CG and the CP, divided by the body width."),
    "inclinometer-trig": (inclinometer_trig, "Height from a baseline and an angle."),
    "energy-path": (energy_path, "The energy story of a flight."),
    "launch-site": (launch_site, "Laying out a launch: the pad, the 15-foot circle, the spectator line and two trackers."),
    "nickel-test": (nickel_test, "The coin breakout test, done during assembly before the body sections are glued."),
}


def figure(name: str) -> str:
    fn, cap = FIGURES[name]
    return f'<figure class="dg" id="fig-{name}">{fn()}<figcaption>{cap}</figcaption></figure>'


if __name__ == "__main__":   # a gallery page, to look at every drawing
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "diagrams.html"
    body = "".join(f"<h2>{k}</h2>{figure(k)}" for k in FIGURES)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f'<!doctype html><meta charset="utf-8"><style>body{{font-family:Inter,sans-serif;max-width:800px;margin:auto;background:#F6F1E7}}'
                f'svg.dg{{width:100%;height:auto;background:#FFFDF8}}{DG_CSS}</style>{body}')
    print("wrote", out)
