"""Generate the printable worksheets for one track of the rocketry lessons.

    python3 docs/curriculum/tools/gen_ws.py middle     docs/curriculum/middle/worksheets.html
    python3 docs/curriculum/tools/gen_ws.py elementary docs/curriculum/elementary/worksheets.html

build_site.py runs both. Static HTML for US Letter; inline SVG drawings, so nothing to fetch
except the brand fonts.
"""
import math
import sys

import diagrams  # tools/diagrams.py: the shared labelled drawings

pages = []
TRACK = {"name": "middle", "line": "Grades 6–8"}


def page(code, title, body, sub="", kind="ws", track="all"):
    badge = f'<span class="badge">{code}</span>' if code else ""
    tag = {"all": "", "12": '<span class="trk t12">12+ only</span>',
           "older": '<span class="trk">Extension</span>', "adult": '<span class="trk">Teachers</span>'}.get(track, "")
    name = '' if kind != "ws" else '<div class="name">Name <span class="blank w3"></span> Date <span class="blank w15"></span></div>'
    pages.append(f'''<section class="page {kind}">
<header class="ph"><div class="brandline"><span class="mark">{fletch_svg()}</span>Rocket Builder <small>by Quiver Design Works</small></div><div class="unit">Rockets &amp; Model Rocketry · {TRACK["line"]}</div></header>{name}
<h2>{badge}{title}{tag if code else ""}</h2>{f'<p class="sub">{sub}</p>' if sub else ''}
{body}
<footer class="pf"><span>Rocket Builder by Quiver Design Works · rocket.quiverdesignworks.net/learn</span><span class="pn"></span></footer>
</section>''')


def fletch_svg():
    return ('<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M3 21 L17 7" stroke="#12203A" stroke-width="2" fill="none"/>'
            '<path d="M17 7 L21 3 L20 8 Z" fill="#F2652B"/><path d="M3 21 L4 15 L7 17 Z M3 21 L9 20 L7 17 Z" fill="#3D8BFD"/></svg>')


def lines(n, cls=""):
    return f'<div class="lines {cls}">' + '<div class="ln"></div>' * n + '</div>'


def table(headers, rows, widths=None, cls="", first_col=None):
    """rows: int (blank rows) or list of lists of cell html."""
    ws = widths or [None] * len(headers)
    cols = "".join(f'<col style="width:{w}">' if w else "<col>" for w in ws)
    th = "".join(f"<th>{h}</th>" for h in headers)
    if isinstance(rows, int):
        body_rows = []
        for i in range(rows):
            cells = [first_col[i] if first_col else ""] + [""] * (len(headers) - 1)
            body_rows.append(cells)
    else:
        body_rows = rows
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body_rows)
    return f'<table class="dt {cls}"><colgroup>{cols}</colgroup><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>'


def grid(w=7.3, h=2.6, cols=20, rows=10, xlabel="", ylabel="", title="Title:"):
    """A blank graph grid (inline SVG so it prints without background graphics)."""
    W, H = 1000, int(1000 * h / w)
    ml, mb, mt, mr = 60, 50, 30, 10
    gw, gh = W - ml - mr, H - mb - mt
    out = [f'<svg class="grid" viewBox="0 0 {W} {H}" style="width:{w}in;height:{h}in" aria-label="graph grid">']
    out.append(f'<text x="{ml}" y="20" class="gt">{title} ______________________________________</text>')
    for i in range(cols + 1):
        x = ml + gw * i / cols
        out.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{mt+gh}" class="gl{" g5" if i % 5 == 0 else ""}"/>')
    for j in range(rows + 1):
        y = mt + gh * j / rows
        out.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+gw}" y2="{y:.1f}" class="gl{" g5" if (rows-j) % 5 == 0 else ""}"/>')
    out.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+gh}" class="ax"/><line x1="{ml}" y1="{mt+gh}" x2="{ml+gw}" y2="{mt+gh}" class="ax"/>')
    out.append(f'<text x="{ml+gw/2}" y="{H-8}" class="al" text-anchor="middle">{xlabel}</text>')
    out.append(f'<text x="18" y="{mt+gh/2}" class="al" text-anchor="middle" transform="rotate(-90 18 {mt+gh/2})">{ylabel}</text>')
    out.append('</svg>')
    return "".join(out)


def box(title, inner, cls=""):
    return f'<div class="box {cls}"><h3>{title}</h3>{inner}</div>'


def vocab(words):
    return '<p class="vocab"><b>Words:</b> ' + " · ".join(words) + "</p>"


NIGHT, ORANGE, SKY, RED, GREEN, GREY = "#12203A", "#F2652B", "#3D8BFD", "#E5484D", "#2FB67C", "#6E6E73"


def arrow_defs(p):
    return (f'<defs><marker id="{p}a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker>'
            f'<marker id="{p}o" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{ORANGE}"/></marker>'
            f'<marker id="{p}n" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{NIGHT}"/></marker>'
            f'<marker id="{p}s" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{SKY}"/></marker>'
            f'<marker id="{p}r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{RED}"/></marker>'
            f'<marker id="{p}g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{GREY}"/></marker></defs>')


def v_rocket(cx=60, top=30, bot=150, w=20):
    """Vertical rocket outline, nose up."""
    l, r = cx - w / 2, cx + w / 2
    nose_b = top + 30
    return (f'<path d="M{l} {nose_b} C{l} {top+12} {cx-3} {top+2} {cx} {top} C{cx+3} {top+2} {r} {top+12} {r} {nose_b} Z" class="rk"/>'
            f'<rect x="{l}" y="{nose_b}" width="{w}" height="{bot-nose_b}" class="rk"/>'
            f'<path d="M{l} {bot-34} L{l-16} {bot-4} L{l-16} {bot+6} L{l} {bot} Z" class="rkf"/>'
            f'<path d="M{r} {bot-34} L{r+16} {bot-4} L{r+16} {bot+6} L{r} {bot} Z" class="rkf"/>'
            f'<line x1="{cx}" y1="{bot-30}" x2="{cx}" y2="{bot+3}" class="rkf2"/>')


def forces_svg(answers=False, pid="f"):
    panels = ["1. On the pad", "2. Boost (motor on)", "3. Coast (motor off)", "4. Under the parachute"]
    W = 760
    out = [f'<svg class="fig" viewBox="0 0 {W} 260" style="width:7.3in" aria-label="four flight phases">{arrow_defs(pid)}']
    for i, label in enumerate(panels):
        x0 = i * 190
        cx = x0 + 95
        out.append(f'<rect x="{x0+4}" y="4" width="182" height="252" rx="8" class="panel"/>')
        out.append(f'<text x="{cx}" y="24" text-anchor="middle" class="pt">{label}</text>')
        if i == 0:
            out.append(f'<line x1="{cx+14}" y1="50" x2="{cx+14}" y2="222" class="rod"/>')
            out.append(f'<rect x="{cx-40}" y="222" width="80" height="8" class="pad"/>')
            out.append(v_rocket(cx, 60, 200))
        elif i == 1:
            out.append(v_rocket(cx, 60, 180))
            out.append(f'<path d="M{cx-7} 184 Q{cx} 236 {cx+7} 184 Z" fill="{ORANGE}" opacity=".85"/>')
        elif i == 2:
            out.append(v_rocket(cx, 60, 180))
            out.append(f'<path d="M{cx-3} 186 q-6 14 0 24 q6 12 0 24" stroke="{GREY}" stroke-width="3" fill="none" stroke-dasharray="4 4"/>')
        else:
            out.append(f'<path d="M{cx-60} 90 Q{cx} 20 {cx+60} 90 Z" class="chute"/>')
            for dx in (-60, -20, 20, 60):
                out.append(f'<line x1="{cx+dx}" y1="90" x2="{cx}" y2="140" class="shroud"/>')
            out.append(f'<g transform="translate({cx} 140) rotate(90) translate({-cx} -140)">{v_rocket(cx, 100, 180, 16)}</g>')
        if answers:
            A = lambda x1, y1, x2, y2, c, t, tx, ty, anchor="start": (
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="4" marker-end="url(#{pid}{ {ORANGE:"o",NIGHT:"n",SKY:"s",GREY:"g",RED:"r"}[c]})"/>'
                f'<text x="{tx}" y="{ty}" class="fl" fill="{c}" text-anchor="{anchor}">{t}</text>')
            if i == 0:
                out.append(A(cx - 36, 120, cx - 36, 175, NIGHT, "weight", cx - 40, 190, "end"))
                out.append(A(cx + 40, 205, cx + 40, 145, GREY, "", 0, 0))
                out.append(f'<text x="{cx}" y="250" class="fl" text-anchor="middle" fill="{GREY}">pad pushes up = weight</text>')
            elif i == 1:
                out.append(A(cx + 36, 140, cx + 36, 45, ORANGE, "thrust", cx + 40, 60))
                out.append(A(cx - 34, 120, cx - 34, 165, NIGHT, "weight", cx - 38, 175, "end"))
                out.append(A(cx - 34, 60, cx - 34, 90, GREY, "drag", cx - 38, 75, "end"))
            elif i == 2:
                out.append(A(cx - 34, 120, cx - 34, 165, NIGHT, "weight", cx - 38, 175, "end"))
                out.append(A(cx + 36, 60, cx + 36, 95, GREY, "drag", cx + 40, 80))
                out.append(f'<text x="{cx}" y="250" class="fl" text-anchor="middle" fill="{NIGHT}">no thrust: slowing down</text>')
            else:
                out.append(A(cx, 70, cx, 32, GREY, "drag", cx + 6, 40))
                out.append(A(cx + 30, 160, cx + 30, 205, NIGHT, "weight", cx + 34, 205))
                out.append(f'<text x="{cx}" y="248" class="fl" text-anchor="middle" fill="{NIGHT}">balanced: steady speed</text>')
    out.append("</svg>")
    return "".join(out)


def stability_svg(pid="s", gap_cal=2):
    # horizontal rocket, nose left; 1 cal = 40 px
    y0, y1 = 70, 110
    cg, cp = 300, 300 + 40 * gap_cal
    out = [f'<svg class="fig" viewBox="0 0 640 200" style="width:6.6in" aria-label="balance point in front of push point">{arrow_defs(pid)}',
           f'<path d="M120 {y0} C80 {y0} 40 82 20 90 C40 98 80 {y1} 120 {y1} Z" class="rk"/>',
           f'<rect x="120" y="{y0}" width="420" height="40" class="rk"/>',
           f'<path d="M455 {y0} L520 20 L548 20 L540 {y0} Z" class="rkf"/><path d="M455 {y1} L520 160 L548 160 L540 {y1} Z" class="rkf"/>',
           f'<rect x="540" y="78" width="10" height="24" class="rk"/>',
           f'<circle cx="{cg}" cy="90" r="9" fill="{SKY}"/><circle cx="{cp}" cy="90" r="9" fill="{RED}"/>',
           f'<line x1="{cg}" y1="80" x2="{cg}" y2="40" stroke="{SKY}" stroke-width="2"/><text x="{cg}" y="34" text-anchor="middle" class="fl" fill="{SKY}">balance point (CG)</text>',
           f'<line x1="{cp}" y1="100" x2="{cp}" y2="140" stroke="{RED}" stroke-width="2"/><text x="{cp}" y="156" text-anchor="middle" class="fl" fill="{RED}">push point (CP)</text>',
           f'<line x1="{cg}" y1="184" x2="{cp}" y2="184" stroke="{NIGHT}" stroke-width="2" marker-start="url(#{pid}n)" marker-end="url(#{pid}n)"/>',
           f'<line x1="{cg}" y1="168" x2="{cg}" y2="192" stroke="{NIGHT}"/><line x1="{cp}" y1="168" x2="{cp}" y2="192" stroke="{NIGHT}"/>',
           f'<text x="{cp+12}" y="190" class="fl">gap = {gap_cal} body widths = score {gap_cal} cal</text>',
           f'<line x1="150" y1="{y0}" x2="150" y2="{y1}" stroke="{ORANGE}" stroke-width="2" marker-start="url(#{pid}o)" marker-end="url(#{pid}o)"/>',
           f'<text x="158" y="{y1+22}" class="fl" fill="{ORANGE}">1 cal = body width</text>',
           f'<line x1="120" y1="28" x2="40" y2="28" stroke="{GREY}" stroke-width="2" marker-end="url(#{pid}g)"/><text x="124" y="32" class="fl" fill="{GREY}">flies this way</text>',
           '</svg>']
    return "".join(out)


def motor_svg(pid="m"):
    x0, y0, h = 40, 50, 60
    segs = [("nozzle", 60, "#C9C2B5"), ("propellant", 200, "#F9C9B3"), ("delay", 110, "#DDE6F5"), ("ejection charge", 50, "#9AA3B5"), ("cap", 30, "#C9C2B5")]
    out = [f'<svg class="fig" viewBox="0 0 600 185" style="width:3.6in" aria-label="inside a model rocket motor">{arrow_defs(pid)}']
    x = x0
    for i, (name, w, col) in enumerate(segs):
        out.append(f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" fill="{col}" stroke="{NIGHT}" stroke-width="1.5"/>')
        if name == "nozzle":
            out.append(f'<path d="M{x} {y0+18} L{x+w} {y0+26} L{x+w} {y0+h-26} L{x} {y0+h-18} Z" fill="#fff" stroke="{NIGHT}"/>')
        ty = 36 if i % 2 == 0 else 140
        ly = y0 if i % 2 == 0 else y0 + h
        out.append(f'<line x1="{x+w/2}" y1="{ly}" x2="{x+w/2}" y2="{ty+(4 if i%2==0 else -14)}" stroke="{GREY}"/>')
        out.append(f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" class="fl">{name}</text>')
        x += w
    out.append(f'<rect x="{x0}" y="{y0}" width="{x-x0}" height="{h}" fill="none" stroke="{NIGHT}" stroke-width="3"/>')
    out.append(f'<line x1="{x0-6}" y1="{y0+h/2}" x2="{x0-34}" y2="{y0+h/2}" stroke="{ORANGE}" stroke-width="4" marker-end="url(#{pid}o)"/>')
    out.append(f'<text x="{x0+250}" y="{y0+h+68}" text-anchor="middle" class="fl" fill="{GREY}">hot gas rushes out of the nozzle, so the rocket is pushed the other way: toward the nose</text>')
    out.append(f'<text x="{x+8}" y="{y0+h/2+5}" class="fl" fill="{GREY}">nose end</text>')
    out.append("</svg>")
    return "".join(out)


def chute_svg(pid="c"):
    return (f'<svg class="fig" viewBox="0 0 300 230" style="width:2.6in" aria-label="parachute drop test">{arrow_defs(pid)}'
            f'<path d="M40 80 Q150 -10 260 80 Z" class="chute"/>'
            + "".join(f'<line x1="{x}" y1="80" x2="150" y2="170" class="shroud"/>' for x in (40, 110, 190, 260)) +
            f'<rect x="138" y="170" width="24" height="14" rx="3" fill="{GREY}"/>'
            f'<line x1="150" y1="58" x2="150" y2="14" stroke="{GREY}" stroke-width="4" marker-end="url(#{pid}g)"/><text x="158" y="22" class="fl" fill="{GREY}">drag</text>'
            f'<line x1="150" y1="188" x2="150" y2="224" stroke="{NIGHT}" stroke-width="4" marker-end="url(#{pid}n)"/><text x="158" y="218" class="fl">weight</text>'
            f'<text x="6" y="34" class="fl">canopy</text><line x1="40" y1="38" x2="72" y2="58" stroke="{GREY}"/><text x="6" y="150" class="fl">shroud lines</text><text x="172" y="182" class="fl">washers</text>'
            '</svg>')


def triangle_svg(pid="t"):
    return (f'<svg class="fig" viewBox="0 0 520 280" style="width:100%;max-width:4.7in" aria-label="height from baseline and angle">{arrow_defs(pid)}'
            f'<line x1="10" y1="240" x2="510" y2="240" stroke="{NIGHT}" stroke-width="2"/>'
            f'<circle cx="60" cy="176" r="9" fill="none" stroke="{NIGHT}" stroke-width="2"/><line x1="60" y1="185" x2="60" y2="215" stroke="{NIGHT}" stroke-width="2"/>'
            f'<line x1="60" y1="215" x2="50" y2="240" stroke="{NIGHT}" stroke-width="2"/><line x1="60" y1="215" x2="70" y2="240" stroke="{NIGHT}" stroke-width="2"/>'
            f'<line x1="60" y1="195" x2="76" y2="186" stroke="{NIGHT}" stroke-width="2"/>'
            f'<line x1="66" y1="176" x2="440" y2="34" stroke="{SKY}" stroke-width="2" stroke-dasharray="7 5"/>'
            f'<line x1="66" y1="176" x2="440" y2="176" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="4 4"/>'
            f'<path d="M126 176 A60 60 0 0 0 122 154" fill="none" stroke="{ORANGE}" stroke-width="3"/><text x="132" y="168" class="fl" fill="{ORANGE}">angle</text>'
            f'<line x1="440" y1="240" x2="440" y2="44" stroke="{NIGHT}" stroke-width="2" stroke-dasharray="3 4"/>'
            f'<path d="M434 40 L440 18 L446 40 Z" fill="{ORANGE}"/><rect x="434" y="40" width="12" height="18" fill="{ORANGE}"/>'
            f'<rect x="430" y="232" width="20" height="8" fill="{GREY}"/><text x="458" y="262" class="fl">pad</text>'
            f'<line x1="66" y1="254" x2="430" y2="254" stroke="{NIGHT}" stroke-width="1.5" marker-start="url(#{pid}n)" marker-end="url(#{pid}n)"/>'
            f'<text x="250" y="272" text-anchor="middle" class="fl">baseline (measure it)</text>'
            f'<text x="452" y="110" class="fl">height</text><text x="452" y="128" class="fl">above eye</text>'
            f'<text x="452" y="200" class="fl">+ eye</text><text x="452" y="216" class="fl">height</text>'
            f'<line x1="446" y1="176" x2="462" y2="176" stroke="{NIGHT}"/>'
            '</svg>')


def cycle_svg():
    steps = ["Ask", "Imagine", "Plan", "Create", "Test", "Improve"]
    cx, cy, r = 95, 82, 60
    out = ['<svg class="fig" viewBox="0 0 190 166" style="width:1.75in" aria-label="design cycle">',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{SKY}" stroke-width="2" stroke-dasharray="6 5"/>']
    for i, s in enumerate(steps):
        a = -math.pi / 2 + i * 2 * math.pi / 6
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        out.append(f'<rect x="{x-34}" y="{y-11}" width="68" height="22" rx="11" fill="#fff" stroke="{ORANGE}" stroke-width="2"/>')
        out.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" class="fl" style="font-size:11px">{i+1}. {s}</text>')
    out.append("</svg>")
    return "".join(out)


TAN = [(5, .09), (10, .18), (15, .27), (20, .36), (25, .47), (30, .58), (35, .70), (40, .84), (45, 1.00),
       (50, 1.19), (55, 1.43), (60, 1.73), (65, 2.14), (70, 2.75), (75, 3.73), (80, 5.67)]
for a, t in TAN:
    assert abs(math.tan(math.radians(a)) - t) < 0.006, (a, t)


def tan_table():
    half = len(TAN) // 2
    rows = []
    for i in range(half):
        a1, t1 = TAN[i]
        a2, t2 = TAN[i + half]
        rows.append([f"{a1}°", f"{t1:.2f}", f"{a2}°", f"{t2:.2f}"])
    return table(["Angle", "Multiplier", "Angle", "Multiplier"], rows, cls="tan")


def inclinometer_svg():
    # mm units. pivot at (cx, cy); 0° straight down; up to 90° each side.
    W, H = 180, 104
    cx, cy, R = 90, 12, 82
    o = [f'<svg class="incl" viewBox="0 0 {W} {H}" style="width:{W}mm;height:{H}mm" aria-label="inclinometer template">']
    # cut outline: top strip + semicircle
    o.append(f'<path d="M{cx-R-4} {cy-8} L{cx+R+4} {cy-8} L{cx+R+4} {cy} A{R+4} {R+4} 0 0 1 {cx-R-4} {cy} Z" fill="#fff" stroke="{NIGHT}" stroke-width=".4" stroke-dasharray="2 1.2"/>')
    o.append(f'<rect x="{cx-R}" y="{cy-7}" width="{2*R}" height="5" fill="#FDE3D6" stroke="{ORANGE}" stroke-width=".3"/>')
    o.append(f'<text x="{cx}" y="{cy-3.4}" text-anchor="middle" style="font-size:3.2px;font-weight:600" fill="{NIGHT}">TAPE THE STRAW HERE, ALONG THIS EDGE</text>')
    for deg in range(0, 91):
        for side in (-1, 1):
            if deg == 0 and side == -1:
                continue
            a = math.radians(deg) * side
            L = 7 if deg % 10 == 0 else 4.5 if deg % 5 == 0 else 2.5
            x1, y1 = cx + R * math.sin(a), cy + R * math.cos(a)
            x2, y2 = cx + (R - L) * math.sin(a), cy + (R - L) * math.cos(a)
            sw = .45 if deg % 10 == 0 else .3
            o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{NIGHT}" stroke-width="{sw}"/>')
            if deg % 10 == 0 and deg < 90:
                lx, ly = cx + (R - 11) * math.sin(a), cy + (R - 11) * math.cos(a)
                o.append(f'<text x="{lx:.2f}" y="{ly+1.3:.2f}" text-anchor="middle" style="font-size:3.6px;font-weight:700" fill="{ORANGE if deg==45 else NIGHT}">{deg}</text>')
    for r in (R - 7, R - 16):
        o.append(f'<path d="M{cx-r} {cy} A{r} {r} 0 0 0 {cx+r} {cy}" fill="none" stroke="{GREY}" stroke-width=".2"/>')
    o.append(f'<line x1="{cx}" y1="{cy+55}" x2="{cx}" y2="{cy+R-14}" stroke="{SKY}" stroke-width=".35" stroke-dasharray="1.5 1"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="1.2" fill="{NIGHT}"/><text x="{cx+3}" y="{cy+4.5}" style="font-size:3px" fill="{NIGHT}">pivot: poke a hole, thread the string</text>')
    o.append(f'<text x="{cx}" y="{cy+40}" text-anchor="middle" style="font-size:4.2px;font-weight:700" fill="{NIGHT}">ANGLE OF ELEVATION</text>')
    o.append(f'<text x="{cx}" y="{cy+46}" text-anchor="middle" style="font-size:3.1px" fill="{GREY}">Read where the string crosses the scale.</text>')
    o.append(f'<text x="{cx}" y="{cy+50.5}" text-anchor="middle" style="font-size:3.1px" fill="{GREY}">Level = 0°. Never look at the sun.</text>')
    o.append("</svg>")
    return "".join(o)


def scale_bar():
    return ('<svg viewBox="0 0 104 9" style="width:104mm;height:9mm" aria-label="10 cm test bar">'
            '<rect x="2" y="2" width="100" height="4" fill="none" stroke="#12203A" stroke-width=".4"/>'
            + "".join(f'<line x1="{2+i*10}" y1="2" x2="{2+i*10}" y2="{7 if i%5==0 else 6}" stroke="#12203A" stroke-width=".3"/>' for i in range(11)) +
            '</svg><div class="hint">This bar should measure exactly 10 cm. If not, print again at 100% ("actual size").</div>')


def checklist(items):
    return '<ul class="check">' + "".join(f"<li><span class=cb></span>{i}</li>" for i in items) + "</ul>"




def middle():
    """The middle-school (grades 6–8) worksheets."""
    # ---------------- COVER ----------------
    contents = [
        ("W1", "Balloon rocket data", "Lesson 1"), ("W2", "Forces and launch angles", "Lesson 2"), ("W3", "Swing test", "Lesson 3"),
        ("W4", "Drag test", "Lesson 4"), ("W5", "Motor codes and impulse", "Lesson 5"), ("W5b", "Thrust curve", "Lesson 5"),
        ("W6", "Design log", "Lesson 6"), ("W7", "Parachutes and landing energy", "Lesson 7"), ("W8", "Altitude tracking", "Lesson 8"),
        ("T", "Inclinometer template", "Lesson 8"), ("W8b", "Safety rules", "Lesson 8"), ("W8c", "Launch checklists", "Lesson 8"),
        ("W9", "Graph your data", "Lesson 9"), ("F", "Flight log (printed rocket)", "Lesson 9"),
        ("C", "Mission report planner and rubric", "Lesson 9"), ("Q", "Quick checks, Lessons 1–9", "Any lesson"), ("K", "Answer keys", "Teachers"),
    ]
    WHO = {"W5b": "Extension", "F": "12+ (adult launches)", "K": "Teachers"}
    cover = f'''<div class="cover">
    <p class="kicker">Middle school · grades 6–8 · 9 lessons</p>
    <h1>Rockets &amp; Model Rocketry</h1>
    <p class="lede">Worksheets, data sheets, the inclinometer template, the flight log and the mission report planner. Goes with <b>Rocket Builder by Quiver Design Works</b>, a free app at rocket.quiverdesignworks.net. Lesson plans: rocket.quiverdesignworks.net/learn/middle.</p>
    <svg class="arc" viewBox="0 0 700 150" aria-hidden="true"><path d="M20 140 Q300 -60 680 120" fill="none" stroke="{SKY}" stroke-width="3" stroke-dasharray="10 8"/>
    <g transform="translate(250 50) rotate(-6)"><path d="M150 -9 C170 -9 186 -4 196 0 C186 4 170 9 150 9 Z" fill="{ORANGE}"/><rect x="40" y="-9" width="110" height="18" fill="{NIGHT}"/><path d="M62 -9 L40 -30 L28 -30 L40 -9 Z M62 9 L40 30 L28 30 L40 9 Z" fill="{SKY}"/><path d="M40 -4 Q14 0 40 4 Z" fill="{ORANGE}" opacity=".7"/></g></svg>
    {table(["", "Page", "Use in", "Who"], [[f"<b>{c}</b>", t, d, WHO.get(c, "Everyone")] for c, t, d in contents], ["0.6in", None, "1.1in", "1.5in"], cls="toc")}
    <div class="note"><b>Printing:</b> US Letter, portrait, scale 100% ("actual size"), so the inclinometer comes out the right size. Turn on "background graphics" for the coloured bands. Print the answer keys for the teacher only.</div>
    <div class="note"><b>Standards:</b> Washington State K–12 Science Learning Standards (NGSS): MS-PS2-1, MS-PS2-2, MS-PS2-4, MS-PS3-1, MS-PS3-2, MS-PS3-5, MS-ETS1-1 to 4. The lesson plans list the standards for each page.</div>
    <div class="note warn"><b>Safety:</b> model rocket motors and kits are rated 12+, and adults handle all motors and igniters. Students under 12 do every page and take launch-day jobs away from the pad. Glasses on for straw and stomp rockets. Follow the NAR Model Rocket Safety Code.</div>
    </div>'''
    page("", "", cover, kind="cover")

    # ---------------- W1 ----------------
    w1 = f'''{vocab(["force", "mass", "inertia", "acceleration", "action and reaction", "thrust"])}
    <p><b>Question:</b> Does more air make it go further? Does more weight make it go less far?</p>
    <p><b>My guess:</b> <span class="blank w5"></span></p>
    <h3>Part A: more air (same mass)</h3>
    {table(["Balloon size", "Circumference (cm)", "Trial 1 (cm)", "Trial 2 (cm)", "Trial 3 (cm)", "Average (cm)"], 3, ["1.1in"]*1 + [None]*5, first_col=["Small", "Medium", "Large"])}
    <h3>Part B: more mass (same air)</h3>
    {table(["Paper clips", "Circumference (cm)", "Trial 1 (cm)", "Trial 2 (cm)", "Trial 3 (cm)", "Average (cm)"], 3, ["1.1in"]*1 + [None]*5, first_col=["0", "5", "10"])}
    <p class="hint">Mean = (trial 1 + trial 2 + trial 3) ÷ 3. Only the mass changes in Part B: that makes it a fair test.</p>
    <h3>Think about it</h3>
    <ol class="qs">
    <li>Newton's <b>third</b> law: the balloon pushes air out the back. What pushes the balloon forward?{lines(1)}</li>
    <li>Newton's <b>second</b> law: in Part B, the push was the same. What happened when you added paper clips? Why?{lines(2)}</li>
    <li>Newton's <b>first</b> law: why did the straw stay still until you let go? Why did it stop at the end?{lines(2)}</li>
    <li>Rocket Builder: press <b>▶ Watch it launch</b>. Write three things you noticed.{lines(2)}</li>
    </ol>
    <div class="ext"><b>Extension:</b> a balloon pushes with 0.1 N on a 10 g (0.010 kg) rocket. Ignoring friction, a = F ÷ m = ______ m/s². With 10 g of paper clips added: a = ______ m/s².</div>'''
    page("W1", "Balloon rocket data", w1, "Lesson 1 · Newton's three laws")

    # ---------------- W2 ----------------
    w2 = f'''{vocab(["thrust", "weight", "drag", "lift", "balanced", "unbalanced", "apogee"])}
    <h3>Part 1: draw the forces</h3>
    <p>Draw an arrow for each force on the rocket and label it: <b class="o">thrust</b>, <b>weight</b>, <b class="g">drag</b>. Make bigger forces longer arrows.</p>
    {forces_svg(False, "fa")}
    <p>Which pictures show <b>balanced</b> forces? <span class="blank w2"></span> &nbsp; Which show <b>unbalanced</b>? <span class="blank w2"></span></p>
    <h3>Part 2: launch-angle test (straw rockets)</h3>
    {table(["Angle", "Trial 1 (cm)", "Trial 2 (cm)", "Trial 3 (cm)", "Average (cm)"], 5, first_col=["15°", "30°", "45°", "60°", "75°"])}
    {grid(7.3, 1.4, 25, 7, "launch angle (degrees)", "distance (cm)", "Bar graph:")}
    <ol class="qs"><li>Which angle went furthest? Why do you think so?{lines(1)}</li>
    <li>Rocket Builder: press <b>▶ Watch it launch</b>. Number these in the order you see them: ___ coast &nbsp;___ liftoff &nbsp;___ parachute &nbsp;___ top (apogee) &nbsp;___ boost</li>
    <li>The <b>power</b> bar (thrust ÷ weight) for my rocket says ______ ×. Is it 5× or more? ______</li></ol>'''
    page("W2", "Forces and launch angles", w2, "Lesson 2 · The forces in a rocket flight")

    # ---------------- W3 ----------------
    w3 = f'''{vocab(["stable", "unstable", "balance point (CG)", "push point (CP)", "caliber", "stability score"])}
    {diagrams.cg_cp_calibers()}
    <p class="hint">The blue dot (balance point) must be <b>in front of</b> the red dot (push point). Score (cal) = (push point distance − balance point distance) ÷ body width. 1–2 cal is just right.</p>
    <p><b>Body width</b> of my test rocket: <span class="blank w15"></span> cm &nbsp;(= 1 cal)</p>
    {table(["Version", "Change", "Balance point from tip (cm)", "Push point from tip (cm)", "Gap (cm)", "Score (cal)", "Swing test: stable, wobbly or tumbles?"],
           [["A", "no fins, no clay"] + [""]*5, ["B", "fins, no clay"] + [""]*5, ["C", "fins + clay in nose"] + [""]*5, ["D", "fins + clay at tail"] + [""]*5],
           ["0.6in", "1.3in", None, None, "0.6in", "0.6in", "1.5in"], cls="tall")}
    <ol class="qs">
    <li>Which version was the most stable? Use your scores to explain.{lines(2)}</li>
    <li>Why did clay in the nose help, but clay at the tail hurt?{lines(2)}</li>
    <li>A rocket is 3 cm wide. Its push point is 4.5 cm behind its balance point. Score = ______ cal. Is that just right, wobbly, or too stable? <span class="blank w2"></span></li>
    <li>In Rocket Builder, my rocket's score is ______ cal. The fins are <span class="blank w2"></span> shaped.</li>
    </ol>'''
    page("W3", "Swing test", w3, "Lesson 3 · Stability: balance point and push point")

    # ---------------- W4 ----------------
    w4 = f'''{vocab(["drag", "streamlined", "frontal area", "drag coefficient", "variable", "fair test", "trade-off"])}
    <p><b>The variable I'm changing:</b> nose shape. <b>Things I keep the same:</b> <span class="blank w4"></span></p>
    <h3>Test 1: nose shapes (launch angle: ______°)</h3>
    {table(["Nose", "Mass (g, optional)", "Trial 1 (cm)", "Trial 2 (cm)", "Trial 3 (cm)", "Average (cm)"], 3, first_col=["Flat", "Cone", "Round"])}
    {grid(7.3, 2.0, 25, 8, "nose shape", "average distance (cm)", "Bar graph:")}
    <h3>Test 2: fins</h3>
    {table(["Fins", "Trial 1 (cm)", "Trial 2 (cm)", "Trial 3 (cm)", "Average (cm)", "Straight or wobbly?"], 4, first_col=["None", "3 small", "3 medium", "4 large"])}
    <ol class="qs">
    <li>Which nose had the least drag? How do you know?{lines(1)}</li>
    <li>Was the difference big, or could it be luck? What would make you more sure?{lines(1)}</li>
    <li>Explain the fin trade-off using your data.{lines(2)}</li>
    </ol>
    <div class="ext"><b>Extension (Advanced mode):</b> drag = ½ × 1.2 × speed² × Cd × area. A rocket with area 0.00071 m² and Cd 0.65 at 40 m/s: drag ≈ ______ N. In Rocket Builder (Advanced → Flight → Advanced), predicted altitude with Cd 0.5: ______ m; Cd 0.8: ______ m.</div>'''
    page("W4", "Drag test", w4, "Lesson 4 · Drag and shape")

    # ---------------- W5 ----------------
    classes = table(["Class", "1/4A", "1/2A", "A", "B", "C", "D", "E", "F"],
                    [["Total impulse up to (N·s)", "0.625", "1.25", "2.5", "5", "10", "20", "40", "80"],
                     ["Smallest field (NAR)", "15 m", "15 m", "30 m", "60 m", "120 m", "150 m", "300 m", "300 m"]], ["1.7in"] + [None]*8, cls="small")
    w5 = f'''{vocab(["propellant", "nozzle", "delay", "ejection charge", "igniter", "total impulse", "impulse class", "thrust-to-weight"])}
    {motor_svg("ma")}
    <p class="hint"><b>Motor rockets are 12+, and only adults handle motors and igniters.</b> This drawing shows the inside of a motor. Never open one.</p>
    {classes}
    <h3>1. Decode the motor codes</h3>
    {table(["Code", "Impulse class", "Average thrust (N)", "Delay (s)", "Smallest field"], [[c, "", "", "", ""] for c in ["A8-3", "B6-4", "C6-5", "D12-5"]])}
    <h3>2. Impulse = average thrust × burn time</h3>
    {table(["Motor", "Average thrust (N)", "Burn time (s)", "Total impulse (N·s)", "Class"], [["a", "3", "0.8", "", ""], ["b", "5", "0.9", "", ""], ["c", "10", "1.7", "", ""], ["d", "15", "3.4", "", ""]])}
    <h3>3. Rocket Builder: How high will it go?</h3>
    <p>The best motor for my design is ______. It should reach ______ m, at a top speed of about ______ m/s.</p>
    <h3>4. Thrust-to-weight (it must be 5 or more)</h3>
    <p class="hint">100 g weighs about 1 N. So a rocket of 80 g weighs about 0.8 N.</p>
    <ol class="qs">
    <li>Rocket + motor = 80 g. Motor average thrust = 5 N. Weight = ______ N. Thrust ÷ weight = ______. Pass? ______</li>
    <li>Rocket + motor = 120 g. Motor average thrust = 4.7 N. Weight = ______ N. Thrust ÷ weight = ______. Pass? ______</li>
    </ol>
    <h3>5. Where is the energy?</h3>
    <p>Write the energy at each point: <b>stored (propellant)</b>, <b>kinetic (motion)</b>, <b>potential (height)</b>, <b>heat (drag)</b>. On the pad: <span class="blank w2"></span> Boost: <span class="blank w2"></span> Apogee: <span class="blank w2"></span></p>'''
    page("W5", "Motor codes and impulse", w5, "Lesson 5 · Motors, impulse and energy")

    thrust = [(0, 0), (0.05, 12), (0.1, 9.5), (0.2, 5), (0.3, 4), (0.4, 4), (0.5, 4), (0.6, 4), (0.7, 4), (0.8, 4), (0.85, 4), (0.9, 0)]
    w5b = f'''<p>This table is a <b>thrust curve</b> for a B motor, rounded from a measured one. Thrust is how hard the motor pushes at each moment.</p>
    {table(["Time (s)"] + [str(t) for t, _ in thrust], [["Thrust (N)"] + [str(f) for _, f in thrust]], ["0.9in"] + [None]*len(thrust), cls="small")}
    <ol class="qs">
    <li>Plot the points on the grid and join them with straight lines. Time along the bottom (each small square = 0.02 s), thrust up the side (each small square = 0.5 N).</li>
    </ol>
    {grid(7.3, 3.8, 45, 26, "time (s): each square = 0.02 s", "thrust (N): each square = 0.5 N", "Thrust curve, B motor")}
    <ol class="qs" start="2">
    <li>What is the <b>peak</b> (highest) thrust? ______ N. When? ______ s</li>
    <li>The <b>area under the curve</b> is the total impulse. Find it by splitting the shape into triangles and rectangles (or count squares: each small square = 0.02 × 0.5 = 0.01 N·s). Total impulse ≈ ______ N·s. Class: ______</li>
    <li>Average thrust = total impulse ÷ burn time (0.86 s) = ______ N. Why is the code's middle number a little different?{lines(1)}</li>
    <li><b>F = m × a at liftoff.</b> Rocket + C6 motor: mass 0.086 kg, measured average thrust 4.7 N. Weight = 0.086 × 9.8 = ______ N. Net force = ______ N. Acceleration = ______ m/s².</li>
    </ol>'''
    page("W5b", "Thrust curve", w5b, "Lesson 5 · Extension: impulse is the area under the thrust curve", track="older")

    # ---------------- W6 ----------------
    w6 = f'''<div class="row"><div class="col">{vocab(["criteria", "constraints", "iteration", "prototype", "trend", "model"])}
    <p><b>Criteria</b> (what it must do): score 1–2 cal (2–3 OK) · a motor gets ✓ Good · height fits our field · <span class="blank w2"></span></p>
    <p><b>Constraints</b> (limits): printer height ______ mm · field size ______ m · safety and environment: <span class="blank w2"></span></p></div>
    <div class="col narrow">{cycle_svg()}</div></div>
    {table(["#", "Height (mm)", "Fin shape", "Nose", "Score (cal)", "Fins grew? ✓", "Best motor", "Altitude (m)", "Power (×)", "Off rod (m/s)"], 8, ["0.3in", "0.75in", "0.85in", "0.75in", "0.6in", "0.6in", "0.75in", "0.75in", "0.6in", None], first_col=[str(i) for i in range(1, 9)])}
    {grid(7.3, 2.0, 30, 10, "height (mm)", "score (cal)", "Line graph: height vs score")}
    <p><b>The trend:</b> as the height went up, the score <span class="blank w4"></span></p>
    <h3>Decision table: score each design 1 (poor) to 3 (great)</h3>
    {table(["Design #", "Stability (1–2 cal is best)", "Altitude fits our field", "Looks", "Print time", "Total"], 3, first_col=["", "", ""])}
    <p><b>I chose design # ______ because</b> <span class="blank w5"></span></p>
    <p><b>Advanced (custom fins):</b> span 15 mm ______ cal · 20 mm ______ · 25 mm ______ · 30 mm ______. The score crosses 1.0 at about ______ mm.</p>
    <p><b>▶ Watch it launch:</b> it went up about ______ m and landed about ______ m from the pad.</p>'''
    page("W6", "Design log", w6, "Lesson 6 · Design with a computer model")

    # ---------------- W7 ----------------
    w7 = f'''<div class="row"><div class="col">{vocab(["recovery", "canopy", "shroud lines", "descent rate", "terminal speed", "drift"])}
    <p><b>Drop height:</b> ______ m &nbsp; <b>Weight on each parachute:</b> <span class="blank w15"></span></p>
    <p class="hint">Descent rate (m/s) = drop height ÷ average time</p></div>
    <div class="col narrow">{chute_svg("ca")}</div></div>
    {table(["Parachute", "Trial 1 (s)", "Trial 2 (s)", "Trial 3 (s)", "Average time (s)", "Descent rate (m/s)"], 4, first_col=["No parachute", "20 cm", "30 cm", "40 cm"])}
    <h3>Landing energy: KE = ½ × mass × speed²</h3>
    <div class="row"><div class="col">{table(["Speed (m/s)", "2", "4", "8", "16"], [["KE of 0.08 kg (J)", "", "", "", ""]], ["1.3in", None, None, None, None], cls="small")}
    {table(["Mass (g)", "40", "80", "160"], [["KE at 4 m/s (J)", "", "", ""]], ["1.3in", None, None, None], cls="small")}
    <p class="hint">Plot KE (up) against speed (along). Which graph would be a straight line: KE vs speed, or KE vs mass?</p></div>
    <div class="col">{grid(3.9, 2.3, 16, 10, "speed (m/s)", "KE (J)", "KE vs speed")}</div></div>
    <h3>Your rocket's parachute (Rocket Builder)</h3>
    <p>Parachute size: ______ inches. Descent speed: ______ m/s. Predicted altitude: ______ m.</p>
    <p>Time to come down = altitude ÷ descent speed = ______ s. &nbsp; Drift in a 10 mph (4.5 m/s) breeze = time × 4.5 = ______ m.</p>
    <ol class="qs"><li>Practice: a rocket reaches 120 m and falls at 4 m/s. Time = ______ s. Drift = ______ m. Is a 60 m field big enough? ______</li>
    <li>Why not just use the biggest parachute you can find?{lines(1)}</li></ol>'''
    page("W7", "Parachutes and landing energy", w7, "Lesson 7 · Parachutes and landing energy")

    # ---------------- W8 ----------------
    w8 = f'''<div class="row"><div class="col">{diagrams.inclinometer_trig()}</div><div class="col fixed">{tan_table()}</div></div>
    <p class="formula">height = baseline × multiplier + eye height</p>
    <h3>1. How tall is it? (tree, flagpole or house)</h3>
    {table(["Object", "Baseline (m)", "Angle 1", "Angle 2", "Angle 3", "Average angle", "Multiplier", "Eye height (m)", "Height (m)"], 2, ["1.1in"] + [None]*8, cls="tall")}
    <h3>2. Practice</h3>
    <ol class="qs">
    <li>Baseline 25 m, angle 40°, eye height 1.3 m. Height = ______ m.</li>
    <li>Baseline 80 m, angle 55°, eye height 1.5 m. Height = ______ m.</li>
    <li>Scale drawing: on the back, draw a baseline of 10 squares (1 square = 2 m). Draw a 35° angle at one end and a line straight up at the other. How many squares tall? ______ = ______ m.</li>
    </ol>
    <h3>3. Track a stomp rocket</h3>
    {table(["Launch", "Tracker", "Baseline (m)", "Angle", "Multiplier", "Height (m)", "Average of trackers (m)"], 4, first_col=["1", "1", "2", "2"])}
    <ol class="qs" start="4"><li>Name two things that could make a height measurement wrong.{lines(1)}</li>
    <li><b>Extension (tangent):</b> with a 50 m baseline, an angle of 45° gives ______ m and 47° gives ______ m. At 75°: ______ m; at 77°: ______ m. Which angle is more sensitive to a 2° mistake? <span class="blank w15"></span></li></ol>'''
    page("W8", "Altitude tracking", w8, "Lesson 8 · Measuring height with angles")

    # ---------------- Inclinometer template ----------------
    tmpl = f'''<ol class="steps">
    <li>Print at <b>100%</b>. Check the 10 cm bar with a ruler. Glue onto cardstock and cut along the dashed line.</li>
    <li>Tape a drinking straw along the top edge, on the orange band.</li>
    <li>Poke a small hole at the pivot dot. Thread about 25 cm of string through it and tape the end at the back.</li>
    <li>Tie a small weight (a washer or nut) to the string so it hangs below the scale.</li>
    <li>Look through the straw at the top of the object. Pinch the string against the card, then read the angle.</li>
    </ol>
    <div class="center">{inclinometer_svg()}</div>
    <div class="center">{scale_bar()}</div>
    <div class="row"><div class="col">{tan_table()}</div><div class="col"><div class="note"><b>Check it:</b> look through the straw at something at your own eye height. The string should hang on 0°. <br><br><b>Tip:</b> make two, so two trackers can measure every launch from different sides.<br><br><b>Never</b> look at the sun through the straw.</div></div></div>'''
    page("T", "Inclinometer template", tmpl, "Lesson 8 · Print at 100% (actual size)", kind="ws tmpl")

    # ---------------- W9 ----------------
    stories = [
        "Zoe puts on safety glasses before the stomp rocket launch.",
        "Max aims his straw rocket at his little sister.",
        "Lily drops the fizzy tablet in the canister herself and leans over it to watch.",
        "Sam's dad keeps the launch key in his pocket until everyone is at least 15 feet back.",
        "The motor rocket didn't launch, so Mia ran straight to the pad to look at it.",
        "It's a 25 mph wind, but the family really wants to fly today.",
        "The rocket landed in a tall tree, so Leo started climbing up to get it.",
        "Ava counts down from 5 out loud, and everyone watches the rocket.",
        "Uncle Jo wants a higher flight, so he tries to open the motor and add more fuel.",
        "Noah runs under the parachute to catch the rocket before it lands.",
    ]
    w9 = f"""{vocab(["safety code", "launch controller", "safety key", "misfire", "LCO", "RSO", "preflight check"])}
    <div class="note"><b>Classroom rockets:</b> glasses on · never aim at anyone · wait for "launch!" · an adult runs the fizzy demo · never chase a rocket into a road, tree or power line.<br>
    <b>Motor rockets (12+):</b> adults handle motors, igniters and the key · 15 ft back · count down from 5 · misfire: key out, wait 60 s · wind under 20 mph · never catch a rocket.</div>
    <h3>1. Is it safe?</h3>
    {table(["Story", "Safe or not safe?", "Which rule?"], [[st, "", ""] for st in stories], [None, "1.1in", "1.9in"])}
    <h3>2. Launch team jobs</h3>
    {table(["Job", "Who (adult or student?)", "Name"], [[j, "", ""] for j in ["Countdown caller", "Stomper (warm-up stomp rockets)", "Trackers (inclinometers)", "Recorder (flight log)", "Timers", "Recovery crew", "Launch Control Officer (key, button)", "Range Safety Officer (checks the rocket)", "Loads the motor and igniter"]], [None, "1.6in", "1.9in"])}"""
    page("W8b", "Safety rules", w9, "Lesson 8 · The NAR Model Rocket Safety Code and classroom rules")

    w9c = f"""<h3>1. Weather check</h3>
    <p>Forecast wind: ______ mph. Under 20 mph? ______ (Under 10 mph means less drift.) &nbsp; Rain? ______ &nbsp; Burn ban or very dry grass? ______</p>
    <h3>2. Field check</h3>
    <p>Field size: ______ m by ______ m. &nbsp; Rocket Builder's suggested field: ______ m. Big enough? ______ &nbsp; If not: a smaller motor that still gets a ✓, or a club launch.</p>
    <h3>3. Preflight checklist (printed rocket, with an adult)</h3>
    <div class="row"><div class="col">{checklist(["Weighed, no motor: ______ g (app said ______ g)", "Fins firm, no cracks", "Shock cord (braided flat elastic) tied tightly at both ends", "Parachute not torn, lines not tangled, folded to slide in easily", "Nose fit (coin test, during assembly): ______ nickels (target ______)"])}</div>
    <div class="col">{checklist(["Balance point with a motor in (an adult puts it in, no igniter): CG ______ mm from the tip", "App's CP: ______ mm. CP − CG = ______ mm. Body width ______ mm", "<b>GO</b> only if CP − CG is at least one body width", "Motor taken out again by an adult", "Prediction written on the flight log"])}</div></div>
    <h3>4. Launch box</h3>
    {checklist(["Safety glasses for everyone", "Inclinometers, tape measure, stopwatches, flight log on a clipboard", "Rocket, spare wadding, warm-up stomp rockets", "Adult only: motors, igniters, the safety key", "Pad, rod, blast deflector, controller, fresh batteries", "Bucket of water or extinguisher; water, hats, sunscreen"])}"""
    page("W8c", "Launch checklists", w9c, "Lesson 8 · Get ready for launch day")

    w9b = f'''<p><b>My data set:</b> <span class="blank w4"></span> (from Lesson ______, or prediction vs flight)</p>
    <p><b>Graph type:</b> bar graph / line graph / scatter plot (circle one). &nbsp; Remember: a title, labels on both axes, units, and evenly spaced numbers.</p>
    {grid(7.3, 5.2, 30, 20, "", "", "Title:")}
    <p><b>Mean</b> of one group of trials: ( ______ + ______ + ______ ) ÷ 3 = ______ &nbsp;&nbsp; <b>Range</b> = ______ − ______ = ______</p>
    <ol class="qs"><li>As <span class="blank w15"></span> went up, <span class="blank w15"></span> went <span class="blank w15"></span>.</li>
    <li>One thing that might have made my data less accurate is{lines(1)}</li>
    <li>Draw a line of best fit by eye. Is the relationship a straight line? Where does it bend?{lines(1)}</li></ol>'''
    page("W9", "Graph your data", w9b, "Lesson 9 · Data and graphing")

    # ---------------- Flight log ----------------
    flog_rows = ["Rocket name", "Date and time", "Place", "Wind (mph) and direction", "Temperature", "Rocket mass, no motor (g)",
                 "Motor (an adult loads it)", "Parachute size", "Predicted altitude (m), written before the flight", "Tracker 1: baseline (m) and angle",
                 "Tracker 2: baseline (m) and angle", "Measured altitude (m)", "Liftoff to parachute (s)", "Parachute to landing (s)",
                 "Landed how far from the pad?", "Did it fly straight?", "Parachute opened near the top?", "Condition after landing", "Percent difference from the prediction"]
    flog = f'''{table(["", "Flight 1", "Flight 2", "Flight 3"], [[r, "", "", ""] for r in flog_rows], ["2.1in", None, None, None], cls="log")}
    <p class="hint">Altitude = baseline × multiplier (or × tan of the angle) + eye height. Average the trackers. Percent difference = (predicted − measured) ÷ predicted × 100.</p>
    <div class="note warn"><b>Launch day rules:</b> adults handle motors, igniters and the key · glasses on, at least 15 ft back · count down from 5 · misfire: key out, wait 60 s · never chase a rocket into trees, roads or power lines · never catch it.</div>'''
    page("F", "Flight log (printed rocket)", flog, "Lesson 9 · Launch day: predict, fly, compare", track="12")

    # ---------------- Capstone ----------------
    parts = [("1. Mission", "What did you set out to do?", 1), ("2. Design", "Your Rocket Builder rocket with the blue (CG) and red (CP) dots and its score, and why you chose it (use your Lesson 6 data).", 2),
             ("3. The science", "(a) Newton's 3rd law and thrust · (b) why the balance point is in front of the push point · (c) how a parachute works.", 2),
             ("4. Prediction vs flight", "Table or graph: the app's prediction and the measured altitude, with the percent difference.", 1), ("5. What happened and why", "Reasons for any differences.", 2),
             ("6. Next time", "One change, and what you predict it will do.", 1), ("7. Safety", "Two rules your team followed and why they matter.", 1)]
    cap = "".join(f'<div class="cp"><b>{t}</b> <span class="hint">{h}</span>{lines(n)}</div>' for t, h, n in parts)
    rub = table(["", "4 Excellent", "3 Good", "2 Getting there", "1 Just starting", "Score"], [
        ["<b>Science</b>", "Explains Newton's 3rd law, stability and parachutes correctly, in own words, with examples", "All three, small mistakes", "One or two", "Missing or mostly incorrect", ""],
        ["<b>Design process</b>", "Several iterations with data; one change at a time; data justifies the choice", "Iterations and a reason", "A design, little data", "No reasons", ""],
        ["<b>Data and math</b>", "Flight log complete; heights correct; percent difference from the prediction", "Mostly complete; small errors", "Some data; calculation incomplete", "Little or no data", ""],
        ["<b>Explaining results</b>", "Two or more sensible reasons; a testable next step", "One reason and a next step", "A reason or a next step", "Neither", ""],
        ["<b>Communication and safety</b>", "Clear, labelled pictures and graphs; two safety rules and why", "Clear, one piece missing", "Hard to follow in places", "Most parts missing", ""],
    ], ["1.15in", "1.9in", None, None, None, "0.5in"], cls="rubric")
    capstone = f'''<p>Make a poster, slides, a written report or a 3–5 minute talk. Plan each part here.</p>{cap}
    <h3>Rubric</h3>{rub}
    <p class="hint"><b>Total ______ / 20.</b> 17–20 mission accomplished · 13–16 solid flight · 9–12 needs another iteration · below 9 back to the pad.</p>'''
    page("C", "Mission report planner and rubric", capstone, "Lesson 9 · Mission report")

    # ---------------- Quick checks ----------------
    QC = [
        ("Lesson 1", ["A rocket pushes gas down; the gas pushes the rocket up. Which law?", "Same push, one balloon carries 10 clips. Which accelerates more, and why?", "True or false: a rocket needs air to push against.", "Trials 3.2 m, 3.6 m, 3.4 m. Mean?"]),
        ("Lesson 2", ["During the coast, which forces act on the rocket?", "Thrust 6 N, weight 1 N, drag 0.5 N. Net force?", "Thrust 6 N on a 1.2 N rocket: at least 5 times?", "Steady speed under a parachute: balanced?"]),
        ("Lesson 3", ["Which must be in front: CG or CP?", "Body 2 cm wide; CP 3 cm behind the CG. Score?", "Is 0.5 cal OK to fly?", "Name two ways to raise the score."]),
        ("Lesson 4", ["Name three things that make drag bigger.", "Twice as fast: how much more drag?", "Why must the three test rockets weigh the same?", "Why not put huge fins on every rocket?"]),
        ("Lesson 5", ["In B6-4, what do the B, the 6 and the 4 mean?", "5 N average for 2 s: impulse and class?", "Rocket + motor 1.2 N, thrust 5 N: pass the 5× rule?", "The rocket slows while coasting. Where does its kinetic energy go?"]),
    ]
    QC2 = [
        ("Lesson 6", ["Criterion vs constraint: what's the difference?", "Why change one thing at a time?", "Your design scores 0.8 cal. Two fixes?", "Your design scores 3.6 cal. Problem?"]),
        ("Lesson 7", ["A parachute falls 3 m in 1.5 s. Descent rate?", "At terminal speed, which forces are balanced?", "Landing speed doubles from 4 to 8 m/s. Kinetic energy?", "From 100 m at 4 m/s in a 4.5 m/s wind: drift?"]),
        ("Lesson 8", ["How far back for a D motor or smaller?", "After a misfire: which two things before anyone goes to the pad?", "Baseline 50 m, 60° (×1.73), eye 1.5 m. Height?", "The CG is 10 mm behind the app's CP. Go or no-go?"]),
        ("Lesson 9", ["Order: apogee, liftoff, burnout, landing, parachute opens.", "Trackers: 119 m and 138 m. Mean?", "Predicted 150 m, measured 120 m. Percent difference?", "Where is gravitational potential energy greatest?"]),
    ]


    def qc_page(groups, title):
        body = '<div class="qcgrid">' + "".join(
            f'<div class="qc"><h3>{d}</h3><ol>' + "".join(f"<li>{q}<span class='qa'></span></li>" for q in qs) + "</ol></div>" for d, qs in groups) + "</div>"
        page("Q", title, body, "Answer on the line. Answers are in each lesson plan and in the answer keys.")


    qc_page(QC, "Quick checks, Lessons 1–5")
    qc_page(QC2, "Quick checks, Lessons 6–9")

    # ---------------- Answer keys ----------------
    def key(title, items):
        return f'<div class="key"><h3>{title}</h3><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


    k1 = (key("W1 Balloon rocket", [
        "Data varies. Expect: bigger balloons go further (more air = a longer push). More paper clips go less far (more mass, same push = less acceleration).",
        "Q1: the air pushes back on the balloon (action and reaction). Q2: it went less far / slower; the same force on more mass gives less acceleration. Q3: no unbalanced force until the air rushed out (law 1); friction on the string and air drag finally stopped it.",
        "Extension: 0.1 ÷ 0.010 = 10 m/s²; 0.1 ÷ 0.020 = 5 m/s²."])
          + key("W2 Forces", [
              "1 On the pad: weight down, the pad pushes up (equal). 2 Boost: big thrust up; weight and drag down. 3 Coast: weight and drag both down; no thrust. 4 Parachute: weight down, drag up (equal).",
              "Balanced: 1 and 4. Unbalanced: 2 and 3.",
              "Launch angle: about 40–45° usually goes furthest. Watch it launch order: liftoff 1, boost 2, coast 3, top 4, parachute 5. Power bar: the app's thrust ÷ weight; it passes at 5× or more."])
          + f'<div class="center">{forces_svg(True, "fk")}</div>'
          + key("W3 Swing test", [
              "Data varies. Usually C (fins + nose clay) is most stable: its balance point is furthest in front of its push point. A often tumbles; D is often wobbly.",
              "Nose clay moves the balance point forward (a bigger gap); tail clay moves it back, toward or behind the push point.",
              "4.5 ÷ 3 = 1.5 cal: just right."])
          + key("W4 Drag test", [
              "Data varies. The flat nose usually goes least far (most drag). Cone and round are often close; small differences may be luck: more trials, a fairer launcher.",
              "Fin trade-off: no fins wobble and land short; medium fins fly straight; very large fins fly straight but may lose a little distance from drag and weight.",
              "Extension: 0.5 × 1.2 × 1600 × 0.65 × 0.00071 ≈ 0.44 N. Lower Cd gives a higher predicted altitude."]))
    page("K", "Answer keys (1 of 3)", k1, "For teachers", kind="ws key", track="adult")

    k2 = (key("W5 Motor codes and impulse", [
        "Decode: A8-3 = A, 8 N, 3 s, 30 m · B6-4 = B, 6 N, 4 s, 60 m · C6-5 = C, 6 N, 5 s, 120 m · D12-5 = D, 12 N, 5 s, 150 m.",
        "Impulse: a 3 × 0.8 = 2.4 N·s, A · b 5 × 0.9 = 4.5 N·s, B · c 10 × 1.7 = 17 N·s, D · d 15 × 3.4 = 51 N·s, F.",
        "Thrust-to-weight: 0.8 N; 5 ÷ 0.8 ≈ 6.3; pass. 1.2 N; 4.7 ÷ 1.2 ≈ 3.9; does not pass (too heavy for this motor).",
        "Part 3: from the app's How high will it go? card. Part 5: pad = stored (propellant); boost = kinetic and potential growing (and heat); apogee = mostly potential."])
          + key("W5b Thrust curve", [
              "Peak 12 N at about 0.05 s.",
              "Area ≈ 0.3 + 0.54 + 0.73 + 0.45 + 2.2 + 0.1 ≈ 4.3 N·s: a B motor (2.51–5).",
              "Average ≈ 4.3 ÷ 0.86 ≈ 5.0 N. The code's number is rounded, and each real motor differs a little.",
              "Weight ≈ 0.84 N; net ≈ 3.9 N; a ≈ 3.9 ÷ 0.086 ≈ 45 m/s² (about 4½ g)."])
          + key("W6 Design log", [
              "Data varies with the app version and choices. Typical trend: with the same fins, taller rockets score higher. Very short rockets show “fins grew” and a score just above 1.",
              "Sample (M18, standard fins, body 350 mm, about 400 mm tall): clipped delta 2.0, trapezoid 1.7, swept 1.7, delta 1.4, rectangle 0.7 cal (the app would enlarge the rectangle's fins). Swept-back fins move the push point further back.",
              "Choice: any design meeting the criteria, with a reason drawn from the data."])
          + key("W7 Parachute drop test", [
              "Data varies. Bigger canopies fall slower; more washers fall faster; no parachute lands in well under a second.",
              "Practice: 120 ÷ 4 = 30 s; 30 × 4.5 = 135 m. A 60 m field is not big enough for the drift.",
              "Too big a parachute: the rocket hangs in the air longer and drifts further (trees, roads, outside the field).",
              "Landing energy (0.08 kg): 2 m/s 0.16 J · 4 m/s 0.64 J · 8 m/s 2.56 J · 16 m/s 10.24 J (a curve: double the speed, 4× the energy). At 4 m/s: 40 g 0.32 J · 80 g 0.64 J · 160 g 1.28 J (a straight line through zero)."])
          + key("W8 Altitude tracking", [
              "Practice 1: 25 × 0.84 + 1.3 = 22.3 m. Practice 2: 80 × 1.43 + 1.5 ≈ 116 m. Scale drawing: about 7 squares = 14 m (tan 35° × 20 m = 14 m).",
              "Errors: angle reading (string swinging), baseline measured wrong, not catching the very top, the rocket drifting toward or away from you, eye height forgotten.",
              "Extension: 50.0 m and 53.6 m; 186.6 m and 216.6 m. Steep angles (75°) are much more sensitive."]))
    page("K", "Answer keys (2 of 3)", k2, "For teachers", kind="ws key", track="adult")

    qa = {
        "Lesson 1": ["Third law.", "No clips: same force, less mass, more acceleration.", "False.", "3.4 m."],
        "Lesson 2": ["Weight and drag.", "4.5 N up.", "Yes, just: 6 ÷ 1.2 = 5.", "Yes."],
        "Lesson 3": ["The CG.", "1.5 cal.", "No.", "Bigger or swept fins, longer body, nose weight."],
        "Lesson 4": ["Speed, frontal area, blunt shape, roughness.", "About 4 times.", "Fair test: only the nose changes.", "Drag and weight; over-stable."],
        "Lesson 5": ["Class B, about 6 N, 4 s delay.", "10 N·s, C.", "No: about 4.2.", "Mostly into potential energy; some into heat (drag)."],
        "Lesson 6": ["Must do vs a limit.", "To know which change caused the result.", "Taller, bigger/swept fins, nose weight, lighter motor.", "Over-stable: weathercocks."],
        "Lesson 7": ["2 m/s.", "Drag and weight.", "4 times bigger.", "About 113 m."],
        "Lesson 8": ["15 ft (5 m).", "Key out; wait 60 s.", "About 88 m.", "No-go."],
        "Lesson 9": ["Liftoff, burnout, apogee, parachute, landing.", "128.5 m.", "20%.", "At apogee."],
    }
    k3 = (key("W8b Safety rules", [
        "Stories: 1 safe (glasses on) · 2 not safe (never aim at anyone) · 3 not safe (an adult handles the tablets; never lean over a canister) · 4 safe (key with the adult; 15 ft back) · 5 not safe (misfire: key out, wait 60 s; adults handle motors) · 6 not safe (no launches over 20 mph) · 7 not safe (never recover from tall trees) · 8 safe (count down out loud) · 9 not safe (never open or change a motor) · 10 not safe (never catch a rocket).",
        "Jobs: countdown caller, stomper, trackers, recorder, timers and recovery crew = students (recovery only when the adult says so). LCO, RSO and loading motors and igniters = adults."])
          + key("W8c Launch checklists", ["GO only if the measured CG (motor in) is at least one body width in front of the app's CP. Nose fit: about 4–5 nickels for an M18 Starter rocket; the build notes give each size's target."])
          + key("W9 Graph your data", ["Check: title, both axes labelled with units, even scale, correct plotting, a sensible trend sentence. Drop-test speed goes with 1 ÷ √area, so it curves rather than falling in a straight line."])
          + '<div class="key"><h3>Quick checks</h3><div class="qak">' + "".join(
              f'<p><b>{d}:</b> ' + " ".join(f"{i+1}. {a}" for i, a in enumerate(v)) + "</p>" for d, v in qa.items()) + "</div></div>"
          + key("Flight log and mission report", ["Use the rubric. Check the altitude math: baseline × multiplier + eye height, averaged over trackers; percent difference = (predicted − measured) ÷ predicted × 100."]))
    page("K", "Answer keys (3 of 3)", k3, "For teachers", kind="ws key", track="adult")


CSS = r"""
/* Brand core from ../brand/tokens.css (linked above), with the fixed hex values as fallbacks for print or offline use. */
:root{--night:var(--rb-night,#12203A);--paper:var(--rb-paper,#F6F1E7);--orange:var(--rb-orange,#F2652B);--sky:var(--rb-sky,#3D8BFD);--red:var(--rb-red,#E5484D);--green:var(--rb-green,#2FB67C);--grey:var(--rb-grey,#6E6E73);
--line:#C9CDD6;--tint:#EEF4FF;--otint:#FDE9DF;}
*{box-sizing:border-box}
html{background:var(--paper)}
body{margin:0;background:var(--paper);color:var(--night);font:10.5pt/1.38 Inter,system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
h1,h2,h3,.badge,.brandline,.formula{font-family:"Space Grotesk",Inter,system-ui,sans-serif}
.page{width:8.5in;height:11in;margin:.3in auto;padding:.5in .55in .45in;background:#fff;position:relative;overflow:hidden;
 box-shadow:0 2px 14px rgba(18,32,58,.14);display:flex;flex-direction:column}
.page>*{flex-shrink:0}
.ph{display:flex;justify-content:space-between;align-items:center;background:var(--night);color:var(--paper);margin:-.5in -.55in 0;padding:.13in .55in .11in;font-size:9pt;
 border-bottom:5px solid var(--orange);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.brandline{display:flex;align-items:center;gap:7px;font:700 11pt "Space Grotesk",sans-serif;letter-spacing:.01em}
.brandline small{font:600 6.5pt "Space Grotesk",sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#A9B4C8;margin-left:4px}
.ph .mark svg path:first-child{stroke:#F6F1E7}
.ph .unit{font:600 7.5pt "Space Grotesk",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#A9B4C8}
.name{display:flex;justify-content:flex-end;gap:6px;margin:8px 0 6px;font-size:9.5pt}
.dgw svg.dg{display:block;width:100%;height:auto;margin:4px 0}
.name{color:var(--night)}
.blank{display:inline-block;border-bottom:1px solid var(--night);height:1em;vertical-align:baseline}
.blank.w15{width:.9in}.blank.w2{width:1.3in}.blank.w3{width:2in}.blank.w4{width:2.8in}.blank.w5{width:4.2in}
h2{font-size:19pt;margin:2px 0 0;display:flex;align-items:center;gap:10px;line-height:1.15}
.badge{background:var(--orange);color:var(--night);font-size:12pt;padding:3px 9px;font-weight:700;clip-path:polygon(5px 0,calc(100% - 5px) 0,100% 5px,100% calc(100% - 5px),calc(100% - 5px) 100%,5px 100%,0 calc(100% - 5px),0 5px)}
.trk{margin-left:auto;font:600 8.5pt Inter,sans-serif;color:var(--night);border:1.5px solid var(--sky);border-radius:20px;padding:1px 9px;white-space:nowrap}
.trk.t12{border-color:var(--orange);background:var(--otint);color:var(--night)}
.pagebreak-hint{margin:8px 0 2px;padding:3px 8px;border-top:2px dashed var(--orange);font-size:9pt;color:var(--grey)}
.sub{margin:2px 0 6px;color:var(--grey);font-size:9.5pt}
h3{font-size:11.5pt;margin:9px 0 4px;color:var(--night);border-left:4px solid var(--sky);padding-left:6px}
p{margin:4px 0}
.vocab{font-size:9pt;background:var(--tint);padding:4px 8px;border-radius:5px}
.hint{font-size:9pt;color:var(--grey)}
.o{color:var(--orange)}.g{color:var(--grey)}
table.dt{width:100%;border-collapse:collapse;margin:4px 0;table-layout:fixed;font-size:9pt}
.dt th{background:var(--night);color:#fff;font-weight:600;padding:3px 5px;text-align:left;font-size:8.5pt;line-height:1.2}
.dt td{border:1px solid var(--line);padding:3px 5px;height:.27in;vertical-align:middle}
.dt.tall td{height:.36in}
.dt.small td{height:auto;padding:2px 4px;text-align:center}.dt.small td:first-child{text-align:left;font-weight:600}
.dt.tan td{height:auto;padding:1px 6px;text-align:center}
.dt.toc td{height:auto;padding:3px 6px}
.dt.log td{height:.37in}.dt.log td:first-child{font-size:8.5pt;font-weight:600;background:#F7F8FA}
.dt.rubric td{height:auto;font-size:8pt;vertical-align:top;line-height:1.25}
.lines .ln{border-bottom:1px solid var(--line);height:.3in}
ol.qs{margin:4px 0;padding-left:20px}ol.qs li{margin:3px 0}
ol.steps{margin:4px 0 6px;padding-left:20px;font-size:9.5pt}
.ext{border:1.5px dashed var(--sky);border-radius:6px;padding:5px 8px;font-size:9pt;margin-top:6px}
.note{background:var(--tint);border-radius:6px;padding:6px 9px;font-size:9pt;margin:6px 0}
.note.warn{background:var(--otint);border-left:4px solid var(--orange)}
.formula{text-align:center;font-weight:700;font-size:12pt;color:var(--orange);margin:2px 0}
svg.grid{display:block;margin:4px 0}
svg.grid .gl{stroke:#D7DBE3;stroke-width:1}svg.grid .gl.g5{stroke:#AEB5C2;stroke-width:1.3}
svg.grid .ax{stroke:var(--night);stroke-width:2.2}svg.grid .al{font-size:17px;fill:var(--night)}svg.grid .gt{font-size:16px;fill:var(--night);font-weight:600}
svg.fig{display:block;margin:4px auto}
.fig .rk{fill:#fff;stroke:var(--night);stroke-width:2.2}.fig .rkf{fill:#DDE6F5;stroke:var(--night);stroke-width:2.2}.fig .rkf2{stroke:var(--night);stroke-width:2}
.fig .panel{fill:#FAFBFD;stroke:var(--line)}.fig .pt{font:600 14px Inter,sans-serif;fill:var(--night)}
.fig .fl{font:600 13px Inter,sans-serif;fill:var(--night)}
.fig .rod{stroke:var(--grey);stroke-width:2}.fig .pad{fill:var(--grey)}
.fig .chute{fill:#FDE3D6;stroke:var(--orange);stroke-width:2.2}.fig .shroud{stroke:var(--grey);stroke-width:1.3}
.row{display:flex;gap:14px;align-items:flex-start}.col{flex:1;min-width:0}.col.narrow{flex:0 0 auto}.col.fixed{flex:0 0 2.75in}.col.fixed .dt th{font-size:8pt}
.center{text-align:center}.center svg{display:inline-block}
ul.check{list-style:none;padding:0;margin:2px 0;font-size:9pt}ul.check li{display:flex;gap:6px;margin:5px 0}
.cb{flex:0 0 12px;height:12px;border:1.5px solid var(--night);border-radius:2px;margin-top:2px}
.cp{margin:2px 0 4px}.cp .hint{display:inline}
.qcgrid{display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}
.qc ol{margin:0;padding-left:18px;font-size:9pt}.qc li{margin:2px 0}
.qc .qa{display:block;border-bottom:1px solid var(--line);height:.24in}
.key h3{margin-top:7px}.key ul{margin:2px 0;padding-left:18px;font-size:9pt}.key li{margin:2px 0}
.qak p{font-size:8.6pt;margin:2px 0}
.pf{margin-top:auto;display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:4px;font-size:7.5pt;color:var(--grey)}
.page{counter-increment:pg}.pn::after{content:"Page " counter(pg)}
body{counter-reset:pg}
.cover h1{font-size:40pt;margin:.12in 0 .05in;line-height:1.05}
.cover .kicker{color:var(--orange);font:700 11pt "Space Grotesk",sans-serif;text-transform:uppercase;letter-spacing:.08em;margin-top:.2in}
.cover .lede{font-size:12pt;max-width:6in}
.cover svg.arc{width:100%;height:1.1in;margin:0 0 .05in}
.page.cover{background:#fff}
.page.cover .ph .name{display:none}
.page.cover h2{display:none}
.tmpl .incl{display:inline-block}
@page{size:Letter;margin:0}
@media print{
 html,body{background:#fff}
 .page{margin:0;box-shadow:none;height:10.98in;break-after:page;page-break-after:always}
 .page:last-child{break-after:auto;page-break-after:auto}
 .dt th{-webkit-print-color-adjust:exact;print-color-adjust:exact}
 .badge{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
@media screen and (max-width:8.6in){.page{transform-origin:top left}}
"""

# ======================================================================================
# Elementary (grades 3–5): big type, pictures, little writing.
# ======================================================================================
BROWN = "#9A6B3F"


def e_rocket(cx, top, bot, w=26, fins=True, clay=None, dots=False, pid="er"):
    """A paper rocket, nose up. clay: None, "nose" or "tail". dots: blue balance and red push points."""
    l, r = cx - w / 2, cx + w / 2
    nb = top + 34
    o = [f'<path d="M{l} {nb} L{cx} {top} L{r} {nb} Z" class="rk"/>',
         f'<rect x="{l}" y="{nb}" width="{w}" height="{bot - nb}" class="rk"/>']
    if fins:
        o.append(f'<path d="M{l} {bot - 40} L{l - 20} {bot - 4} L{l - 20} {bot + 8} L{l} {bot} Z" class="rkf"/>'
                 f'<path d="M{r} {bot - 40} L{r + 20} {bot - 4} L{r + 20} {bot + 8} L{r} {bot} Z" class="rkf"/>')
    if clay == "nose":
        o.append(f'<ellipse cx="{cx}" cy="{nb - 6}" rx="7" ry="8" fill="{BROWN}"/>')
    if clay == "tail":
        o.append(f'<ellipse cx="{cx}" cy="{bot - 10}" rx="9" ry="8" fill="{BROWN}"/>')
    if dots:
        mid = (top + bot) / 2
        o.append(f'<circle cx="{cx}" cy="{mid - 8}" r="7" fill="none" stroke="{SKY}" stroke-width="3" stroke-dasharray="3 2"/>'
                 f'<circle cx="{cx}" cy="{mid + 30}" r="7" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="3 2"/>')
    return "".join(o)


def balloon_svg():
    return (f'<svg class="fig" viewBox="0 0 640 170" style="width:6.4in" aria-label="balloon rocket on a string">{arrow_defs("eb")}'
            f'<rect x="10" y="40" width="14" height="110" fill="{GREY}"/><rect x="616" y="40" width="14" height="110" fill="{GREY}"/>'
            f'<line x1="24" y1="60" x2="616" y2="60" stroke="{NIGHT}" stroke-width="2"/>'
            f'<rect x="300" y="55" width="90" height="10" rx="3" fill="#fff" stroke="{NIGHT}" stroke-width="2"/>'
            f'<ellipse cx="345" cy="95" rx="75" ry="28" fill="#FDE3D6" stroke="{ORANGE}" stroke-width="3"/>'
            f'<path d="M270 95 L258 86 L258 104 Z" fill="{ORANGE}"/>'
            f'<line x1="300" y1="65" x2="320" y2="70" stroke="{NIGHT}"/><line x1="390" y1="65" x2="370" y2="70" stroke="{NIGHT}"/>'
            + "".join(f'<circle cx="{240 - i * 22}" cy="{95 + (i % 2) * 8 - 4}" r="{6 - i}" fill="none" stroke="{SKY}" stroke-width="2"/>' for i in range(4))
            + f'<line x1="250" y1="140" x2="150" y2="140" stroke="{SKY}" stroke-width="4" marker-end="url(#ebs)"/><text x="200" y="164" text-anchor="middle" class="fl" fill="{SKY}">air goes this way</text>'
            f'<line x1="400" y1="140" x2="520" y2="140" stroke="{ORANGE}" stroke-width="4" marker-end="url(#ebo)"/><text x="460" y="164" text-anchor="middle" class="fl" fill="{ORANGE}">balloon goes this way</text>'
            f'<text x="330" y="30" text-anchor="middle" class="fl">straw on the string</text></svg>')


def three_panels_svg():
    labels = ["1. Launch", "2. Going up", "3. Coming down"]
    o = [f'<svg class="fig" viewBox="0 0 660 300" style="width:7.2in" aria-label="three parts of a straw rocket flight">']
    for i, lab in enumerate(labels):
        x0 = i * 220
        cx = x0 + 110
        o.append(f'<rect x="{x0 + 6}" y="4" width="208" height="292" rx="10" class="panel"/>')
        o.append(f'<text x="{cx}" y="32" text-anchor="middle" class="pt" style="font-size:20px">{lab}</text>')
        if i == 0:
            o.append(f'<line x1="{cx}" y1="200" x2="{cx}" y2="270" stroke="{GREY}" stroke-width="5"/>')
            o.append(e_rocket(cx, 120, 230, 22))
        elif i == 1:
            o.append(e_rocket(cx, 80, 190, 22))
            o.append(f'<path d="M{cx - 8} 250 l0 20 M{cx} 248 l0 26 M{cx + 8} 250 l0 20" stroke="{GREY}" stroke-width="2" stroke-dasharray="4 4"/>')
        else:
            o.append(f'<g transform="rotate(180 {cx} 160)">{e_rocket(cx, 100, 210, 22)}</g>')
    o.append("</svg>")
    return "".join(o)


def angle_svg():
    cx, cy, R = 70, 200, 170
    o = [f'<svg class="fig" viewBox="0 0 400 220" style="width:3.6in" aria-label="launch angles">',
         f'<line x1="{cx}" y1="{cy}" x2="{cx + R + 20}" y2="{cy}" stroke="{NIGHT}" stroke-width="2"/>',
         f'<path d="M{cx + 60} {cy} A60 60 0 0 0 {cx} {cy - 60}" fill="none" stroke="{GREY}" stroke-width="1.5"/>']
    for a, c in ((30, SKY), (45, ORANGE), (60, GREEN)):
        x, y = cx + R * math.cos(math.radians(a)), cy - R * math.sin(math.radians(a))
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
                 f'<text x="{x + 8:.0f}" y="{y + 4:.0f}" class="fl" fill="{c}" style="font-size:20px">{a}°</text>')
    o.append(f'<rect x="{cx - 50}" y="{cy - 6}" width="44" height="22" rx="6" fill="#DDE6F5" stroke="{NIGHT}" stroke-width="2"/>'
             f'<text x="{cx - 28}" y="{cy + 34}" text-anchor="middle" class="fl">bottle</text></svg>')
    return "".join(o)


def stomp_svg():
    return (f'<svg class="fig" viewBox="0 0 300 170" style="width:2.6in" aria-label="stomp rocket launcher">'
            f'<rect x="20" y="130" width="120" height="30" rx="14" fill="#DDE6F5" stroke="{NIGHT}" stroke-width="2"/>'
            f'<path d="M140 145 L200 145 L200 70" fill="none" stroke="{GREY}" stroke-width="10"/>'
            f'<g transform="rotate(0)">{e_rocket(200, 6, 90, 18)}</g>'
            f'<path d="M50 104 l10 20 M80 100 l0 24 M110 104 l-10 20" stroke="{ORANGE}" stroke-width="3"/>'
            f'<text x="80" y="96" text-anchor="middle" class="fl">stomp!</text></svg>')


def big_boxes(labels, h="1.0in"):
    return '<div class="ebox">' + "".join(f'<div style="height:{h}"><span>{l}</span></div>' for l in labels) + "</div>"


def circle_one(*opts):
    return '<span class="c1">' + "".join(f"<span>{o}</span>" for o in opts) + "</span>"


def ticks(*opts):
    return " ".join(f'<span class="tk"><span class="cb"></span>{o}</span>' for o in opts)


def bars(cols, ylab, rows=8, w=5.4, h=2.4):
    """A big blank bar chart with labelled columns."""
    W, H = 1000, int(1000 * h / w)
    ml, mb, mt = 70, 60, 20
    gw, gh = W - ml - 20, H - mb - mt
    o = [f'<svg class="grid ebars" viewBox="0 0 {W} {H}" style="width:{w}in;height:{h}in" aria-label="bar graph">']
    for j in range(rows + 1):
        y = mt + gh * j / rows
        o.append(f'<line x1="{ml}" y1="{y:.0f}" x2="{ml + gw}" y2="{y:.0f}" class="gl g5"/>')
    o.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + gh}" class="ax"/><line x1="{ml}" y1="{mt + gh}" x2="{ml + gw}" y2="{mt + gh}" class="ax"/>')
    n = len(cols)
    for i, c in enumerate(cols):
        x = ml + gw * (i + .5) / n
        o.append(f'<rect x="{x - 45:.0f}" y="{mt}" width="90" height="{gh}" fill="none" stroke="#C9CDD6" stroke-dasharray="6 6"/>'
                 f'<text x="{x:.0f}" y="{H - 22}" text-anchor="middle" class="al" style="font-size:30px;font-weight:600">{c}</text>')
    o.append(f'<text x="24" y="{mt + gh / 2}" class="al" style="font-size:26px" text-anchor="middle" transform="rotate(-90 24 {mt + gh / 2})">{ylab}</text></svg>')
    return "".join(o)


def card45_svg():
    s = 300
    return (f'<svg class="fig" viewBox="0 0 {s + 20} {s + 20}" style="width:3.1in;height:3.1in" aria-label="45 degree sighting card">'
            f'<rect x="10" y="10" width="{s}" height="{s}" fill="#fff" stroke="{NIGHT}" stroke-width="2" stroke-dasharray="8 6"/>'
            f'<line x1="10" y1="{s + 10}" x2="{s + 10}" y2="10" stroke="{ORANGE}" stroke-width="3" stroke-dasharray="10 6"/>'
            f'<text x="{s / 2 + 30}" y="{s / 2 - 10}" class="fl" fill="{ORANGE}" transform="rotate(-45 {s / 2 + 30} {s / 2 - 10})" text-anchor="middle" style="font-size:16px">fold here, then sight up this edge</text>'
            f'<text x="{s / 2 - 10}" y="{s - 8}" class="fl" text-anchor="middle" style="font-size:16px">hold this edge level</text>'
            f'<text x="30" y="40" class="fl" style="font-size:16px">cut on the dashed line</text></svg>')


def elementary():
    """The elementary (grades 3–5) worksheets: one per lesson plus cards, pledge and certificate."""
    contents = [("E1", "Balloon rocket", "Lesson 1"), ("E2", "Straw rocket forces", "Lesson 2"), ("E3", "Launch angles", "Lesson 3"),
                ("E4", "Swing test", "Lesson 4"), ("E5", "Design plan", "Lesson 5"), ("E6", "Test and improve", "Lesson 6"),
                ("E7", "Parachute drop", "Lesson 7"), ("E8", "Launch log", "Lesson 8"), ("P", "Parts of a rocket", "Any lesson"),
                ("S", "Safety pledge", "Lesson 1"), ("45", "45° sighting cards", "Lesson 8"), ("★", "Rocket Scientist certificate", "Lesson 8"),
                ("K", "Answer key", "Teachers")]
    cover = f'''<div class="cover">
    <p class="kicker">Elementary · grades 3–5 · 8 lessons</p>
    <h1>Rockets &amp; Model Rocketry</h1>
    <p class="lede">Worksheets for paper rockets: balloon, straw and stomp rockets and parachutes. Goes with <b>Rocket Builder by Quiver Design Works</b> (rocket.quiverdesignworks.net), used on the class projector. Lesson plans: rocket.quiverdesignworks.net/learn/elementary.</p>
    <svg class="arc" viewBox="0 0 700 150" aria-hidden="true"><path d="M20 140 Q300 -60 680 120" fill="none" stroke="{SKY}" stroke-width="3" stroke-dasharray="10 8"/>
    <g transform="translate(250 50) rotate(-6)"><path d="M150 -9 C170 -9 186 -4 196 0 C186 4 170 9 150 9 Z" fill="{ORANGE}"/><rect x="40" y="-9" width="110" height="18" fill="{NIGHT}"/><path d="M62 -9 L40 -30 L28 -30 L40 -9 Z M62 9 L40 30 L28 30 L40 9 Z" fill="{SKY}"/></g></svg>
    {table(["", "Page", "Use in"], [[f"<b>{c}</b>", t, d] for c, t, d in contents], ["0.6in", None, "1.4in"], cls="toc")}
    <div class="note"><b>Printing:</b> US Letter, portrait, 100%. One page per student per lesson. Print the answer key for the teacher only.</div>
    <div class="note"><b>Standards:</b> Washington State K–12 Science Learning Standards (NGSS): 3-PS2-1, 3-PS2-2, 4-PS3-1, 5-PS2-1, 3-5-ETS1-1 to 3. Each lesson plan lists its standards.</div>
    <div class="note warn"><b>Safety:</b> paper and air rockets only. Model rocket motors are rated 12+ and only adults handle them. Glasses on for straw and stomp rockets.</div>
    </div>'''
    page("", "", cover, kind="cover")

    e1 = f'''<div class="words"><b>force</b>: a push or a pull · <b>thrust</b>: the push that moves a rocket</div>
    <div class="dgw" style="max-width:5.2in;margin:0 auto">{diagrams.balloon_setup()}</div>
    <p class="big"><b>My guess:</b> which balloon will go farther? {circle_one("small balloon", "big balloon")}</p>
    {table(["Balloon", "Try 1", "Try 2", "Try 3", "Farthest"], [["<b>Small</b>", "", "", "", ""], ["<b>Big</b>", "", "", "", ""]], ["1.3in", None, None, None, None], cls="etab")}
    <p class="big">Colour a bar for the <b>farthest</b> try.</p>
    {bars(["small", "big"], "metres", 6, 4.4, 2.0)}
    <p class="big">The air pushes {circle_one("forward", "backward")}. The balloon goes {circle_one("forward", "backward")}.</p>
    <p class="big">Holding it still, the pushes are {circle_one("balanced", "unbalanced")}.</p>'''
    page("E1", "Balloon rocket", e1, "Lesson 1 · Every push has a push back")

    e2 = f'''<div class="words"><b>gravity</b>: Earth&#39;s pull, always down · <b>drag</b>: air pushing back · <b>apogee</b>: the highest point</div>
    <p class="big">Draw an arrow for each push or pull. <b class="o">Orange</b> = thrust (push up). <b style="color:{SKY}">Blue</b> = gravity (pull down).</p>
    {three_panels_svg()}
    <p class="big">Gravity pulls {circle_one("up", "down")}.</p>
    <p class="big">My evidence: every time, my rocket {circle_one("came back down", "kept going up")}.</p>
    <p class="big">The highest point is called the {circle_one("apogee", "launch")}.</p>
    <p class="big"><b>Rocket Builder:</b> number the parts in order as you watch: ___ coast &nbsp; ___ liftoff &nbsp; ___ parachute &nbsp; ___ top</p>'''
    page("E2", "Straw rocket forces", e2, "Lesson 2 · Up and down")

    e3 = f'''<div class="words"><b>angle</b>: how much it tilts, in degrees (°) · <b>pattern</b>: something that happens the same way again and again</div>
    <div class="row"><div class="col narrow">{angle_svg()}</div><div class="col">
    {table(["Angle", "Try 1", "Try 2"], [["<b>30°</b>", "", ""], ["<b>45°</b>", "", ""], ["<b>60°</b>", "", ""], ["<b>75°</b>", "", ""]], ["1in", None, None], cls="etab")}</div></div>
    {bars(["30°", "45°", "60°", "75°"], "distance", 6, 6.6, 2.8)}
    <p class="big"><b>Predict before you test 75°:</b> it will go {circle_one("farther than 60°", "shorter than 60°")}</p>
    <p class="big"><b>Was I right?</b> {circle_one("yes", "no")}</p>
    <p class="big"><b>The pattern:</b> {circle_one("steeper is always farther", "the best angle is in the middle")}</p>'''
    page("E3", "Launch angles", e3, "Lesson 3 · Find the pattern")

    vs = [("A", "no fins", False, None), ("B", "fins", True, None), ("C", "fins + clay in nose", True, "nose"), ("D", "fins + clay in tail", True, "tail")]
    cells = "".join(f'<div class="vcard"><svg class="fig" viewBox="0 0 120 200" style="width:1.2in;height:2in">{e_rocket(60, 10, 175, 26, f, c)}</svg>'
                    f'<p><b>{k}</b> {d}</p><p>{ticks("straight", "wobbly", "tumbles")}</p></div>' for k, d, f, c in vs)
    e4 = f'''<div class="words"><b>fins</b>: the rocket&#39;s feathers · <b>balance point</b>: where it balances (blue dot) · <b>push point</b>: where the air pushes (red dot)</div>
    <p class="big">Swing each rocket. Tick what it did.</p>
    <div class="vgrid">{cells}</div>
    <div class="row"><div class="col narrow"><svg class="fig" viewBox="0 0 120 220" style="width:1.1in">{e_rocket(60, 10, 195, 30, True, None, True)}</svg></div>
    <div class="col"><p class="big"><b>Colour the dots.</b> The balance point is <b style="color:{SKY}">blue</b>. The push point is <b style="color:{RED}">red</b>.</p>
    <p class="big">The <b style="color:{SKY}">blue</b> dot must be {circle_one("in front (nearer the nose)", "behind")}.</p>
    <p class="big"><b>Rocket Builder:</b> our score was ______. Green? {circle_one("yes", "no")}</p>
    <p class="big">Fins work like the {circle_one("feathers on an arrow", "wheels on a car")}.</p></div></div>'''
    page("E4", "Swing test", e4, "Lesson 4 · Fins and balance")

    e5 = f'''<div class="note"><b>Problem:</b> design a paper rocket that flies straight off the stomp launcher and lands in the target zone.</div>
    <div class="row"><div class="col"><p class="big"><b>Criteria</b> (it must…)</p>{checklist(["fly nose-first", "land in the zone", "still work after 3 launches"])}</div>
    <div class="col"><p class="big"><b>Constraints</b> (my limits)</p>{checklist(["1 sheet of paper", "1 index card", "50 cm of tape", "15 minutes"])}</div>
    <div class="col narrow">{stomp_svg()}</div></div>
    {big_boxes(["Idea 1: draw it", "Idea 2: draw it"], "2.5in")}
    {table(["", "Flies straight?", "Lands in the zone?", "Strong?"], [["<b>Idea 1</b>", "", "", ""], ["<b>Idea 2</b>", "", "", ""]], ["1.1in", None, None, None], cls="etab")}
    <p class="big">I picked idea {circle_one("1", "2")} because <span class="blank w4"></span></p>'''
    page("E5", "Design plan", e5, "Lesson 5 · Be an engineer")

    e6 = f'''{table(["Launch", "Straight or wobbly?", "In the zone?", "Still works?"], [[f"<b>{i}</b>", ticks("straight", "wobbly"), ticks("yes", "no"), ticks("yes", "no")] for i in (1, 2)], ["0.8in", None, None, None], cls="etab")}
    <div class="row"><div class="col narrow"><svg class="fig" viewBox="0 0 140 230" style="width:1.3in">{e_rocket(70, 10, 200, 34)}
    <text x="100" y="30" class="fl" style="font-size:15px">nose</text><text x="94" y="120" class="fl" style="font-size:15px">body</text><text x="96" y="218" class="fl" style="font-size:15px">fins</text></svg></div>
    <div class="col"><p class="big"><b>Circle the failure point</b> on the rocket: the part that didn't work.</p>
    <p class="big">I changed <b>one</b> thing: {ticks("nose", "fins", "length", "weight")}</p></div></div>
    <p class="big"><b>After my fix:</b></p>
    {table(["Launch", "Straight or wobbly?", "In the zone?", "Still works?"], [[f"<b>{i}</b>", ticks("straight", "wobbly"), ticks("yes", "no"), ticks("yes", "no")] for i in (3, 4)], ["0.8in", None, None, None], cls="etab")}
    <p class="big">Did my change help? {circle_one("yes", "no", "a little")}</p>'''
    page("E6", "Test and improve", e6, "Lesson 6 · Fair tests and failure points")

    e7 = f'''<div class="words"><b>parachute</b>: catches air to slow a fall · <b>drag</b>: air pushing back · <b>gravity</b>: pulls down</div>
    <div class="row"><div class="col narrow">{chute_svg("ec")}</div><div class="col">
    {table(["", "Drop 1 (seconds)", "Drop 2 (seconds)"], [["<b>No parachute</b>", "", ""], ["<b>Small (20 cm)</b>", "", ""], ["<b>Big (40 cm)</b>", "", ""], ["<b>Streamer</b>", "", ""]], ["1.6in", None, None], cls="etab")}
    <p class="big">Circle the <b>slowest</b> one in the table.</p></div></div>
    <p class="big">A bigger parachute falls {circle_one("faster", "slower")}.</p>
    <p class="big">Gravity pulls {circle_one("up", "down")}. Drag from the air pushes {circle_one("up", "down")}.</p>
    <p class="big">Every parachute had the same washers, so the test was {circle_one("fair", "not fair")}.</p>
    <p class="big"><b>Rocket Builder:</b> the parachute for a real rocket is ______ inches.</p>'''
    page("E7", "Parachute drop", e7, "Lesson 7 · Coming down gently")

    e8 = f'''<p class="big">I stood ______ m from the launcher. My job: {ticks("countdown", "stomper", "tracker", "recorder", "recovery")}</p>
    {table(["#", "Stomp", "My guess: above or below 45°?", "What happened?"], [[f"<b>{i}</b>", ticks("soft", "medium", "hard"), ticks("above", "below"), ticks("above", "below")] for i in range(1, 6)], ["0.45in", "2.2in", None, None], cls="etab")}
    <p class="big">A harder stomp made the rocket go {circle_one("faster and higher", "slower and lower")}. It had {circle_one("more", "less")} energy.</p>
    <p class="big">The parachute rocket's parachute opened: {circle_one("yes", "no")}</p>
    <p class="big"><b>Rocket Builder</b> predicted ______ m for a real rocket with a motor.</p>
    <p class="big"><b>My best flight</b> (first, next, last): <span class="blank w5"></span></p>'''
    page("E8", "Launch log", e8, "Lesson 8 · Launch day")

    parts = [("nose cone", 40), ("body tube", 120), ("fins", 205), ("parachute", None)]
    psvg = (f'<svg class="fig" viewBox="0 0 520 260" style="width:6in" aria-label="parts of a paper rocket">'
            f'<g transform="rotate(90 130 130)">{e_rocket(130, 10, 240, 40)}</g>'
            f'<path d="M380 120 Q450 40 520 120 Z" class="chute" transform="translate(-60 0)"/>'
            + "".join(f'<line x1="{x}" y1="120" x2="400" y2="190" class="shroud"/>' for x in (320, 360, 420, 460))
            + f'<rect x="392" y="190" width="16" height="10" fill="{GREY}"/>'
            + "".join(f'<rect x="{x}" y="200" width="110" height="40" rx="6" fill="#fff" stroke="{NIGHT}" stroke-width="2"/>' for x in (12, 140, 268, 396))
            + "</svg>")
    pp = f'''<p class="big">Write the name of each part in a box. <b>Word bank:</b> nose cone · body tube · fins · parachute</p>
    {psvg}
    <p class="big">The <b>fins</b> keep the rocket {circle_one("flying straight", "going fast")}.</p>
    <p class="big">The <b>parachute</b> helps it {circle_one("go higher", "land gently")}.</p>
    <p class="big">The <b>nose cone</b> is pointed so the air flows {circle_one("smoothly around it", "into it")}.</p>'''
    page("P", "Parts of a rocket", pp, "Any lesson")

    sp = f'''<p class="big">I will keep everyone safe. I promise to:</p>
    {checklist(["wear safety glasses for straw and stomp rockets", "never aim a rocket at a person, an animal or a window", "wait for the countdown: 3, 2, 1, launch!", "stand behind the line until the adult says “clear”", "never chase a rocket into a road, a tree or a power line", "never look at the sun", "leave real rocket motors to adults (they are for ages 12+)"])}
    <p class="big" style="margin-top:.4in">Signed <span class="blank w4"></span></p>
    <div class="note warn" style="margin-top:.3in">Model rocket motors and kits are rated 12+. In our class we fly paper and air rockets.</div>'''
    page("S", "Safety pledge", sp, "Lesson 1 · Read it together, then sign")

    cards = '<div class="cards">' + card45_svg() * 2 + "</div>" + f'<div class="dgw">{diagrams.sight45()}</div>'
    c45 = f'''<p class="big">Cut out a square and fold it corner to corner. Hold the bottom edge <b>level</b> and look up the folded edge: that line goes up at <b>45°</b>.</p>
    {cards}
    <p class="big">If you stand <b>10 m</b> from the launcher and the rocket goes <b>above</b> your 45° line, it went higher than 10 m.</p>'''
    page("45", "45° sighting cards", c45, "Lesson 8 · Cut out, fold, track")

    cert = f'''<div class="cert"><p class="kicker">Rocket Builder · Rockets &amp; Model Rocketry</p>
    <h1>Rocket Scientist</h1>
    <p class="big">This certifies that</p>
    <p class="certname"></p>
    <p class="big">designed, built, tested and launched rockets like a real engineer, and knows that every push has a push back, gravity pulls down, and fins keep a rocket flying straight.</p>
    <svg class="arc" viewBox="0 0 700 150" aria-hidden="true"><path d="M20 140 Q300 -60 680 120" fill="none" stroke="{SKY}" stroke-width="3" stroke-dasharray="10 8"/>
    <g transform="translate(250 50) rotate(-6)"><path d="M150 -9 C170 -9 186 -4 196 0 C186 4 170 9 150 9 Z" fill="{ORANGE}"/><rect x="40" y="-9" width="110" height="18" fill="{NIGHT}"/><path d="M62 -9 L40 -30 L28 -30 L40 -9 Z M62 9 L40 30 L28 30 L40 9 Z" fill="{SKY}"/></g></svg>
    <p class="big">Date <span class="blank w2"></span> &nbsp;&nbsp; Teacher <span class="blank w3"></span></p></div>'''
    page("", "", cert, kind="cover certp")

    def key(title, items):
        return f'<div class="key"><h3>{title}</h3><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"
    k = (key("E1 Balloon rocket", ["Data varies; the big balloon usually goes farther (a longer push).", "The air pushes backward; the balloon goes forward. Held still: balanced."])
         + key("E2 Straw rocket forces", ["Launch and going up: orange thrust arrow up, blue gravity arrow down (thrust longer while pushing). Coming down: blue gravity arrow down.", "Gravity pulls down; it always came back down; apogee. Order: liftoff 1, coast 2, top 3, parachute 4."])
         + key("E3 Launch angles", ["Data varies; about 45° (often a bit less) usually goes farthest; 75° goes shorter than 60°.", "Pattern: the best angle is in the middle."])
         + key("E4 Swing test", ["Usually A tumbles, B may wobble, C flies straight, D wobbles or tumbles.", "The blue (balance point) dot is in front, nearer the nose. Fins work like the feathers on an arrow."])
         + key("E5 Design plan", ["Any two different ideas; a reason that uses the criteria."])
         + key("E6 Test and improve", ["Common failure points: a leaky nose, crooked or loose fins, fins too far forward. One change at a time."])
         + key("E7 Parachute drop", ["Slowest: the big parachute. No parachute is fastest; the streamer is in between.", "Bigger falls slower. Gravity pulls down; drag pushes up. Same washers: fair. Rocket Builder: often 12–18 inches."])
         + key("E8 Launch log", ["Harder stomp: faster and higher, more energy. Above the 45° line from 10 m means higher than 10 m."])
         + key("Parts of a rocket", ["Boxes left to right: nose cone, body tube, fins, parachute. Fins keep it flying straight; the parachute helps it land gently; the nose lets air flow smoothly around it."]))
    page("K", "Answer key", k, "For teachers", kind="ws key", track="adult")


ELEM_CSS = r"""
.page.ws p.big, .page.ws .big{font-size:15pt;line-height:1.5;margin:11px 0}
.page.ws h2{font-size:22pt}
.etab td{height:.55in;font-size:12pt}.etab th{font-size:11pt;padding:5px 7px}
.c1{display:inline-flex;gap:10px;flex-wrap:wrap;margin-left:4px}.c1 span{border:1.5px solid var(--night);border-radius:20px;padding:1px 12px;font-weight:600}
.tk{display:inline-flex;align-items:center;gap:5px;margin-right:12px;white-space:nowrap}.tk .cb{flex:0 0 15px;height:15px;margin:0}
.ebox{display:flex;gap:14px;margin:8px 0}.ebox div{flex:1;border:2px dashed var(--sky);border-radius:10px;position:relative}.ebox span{position:absolute;top:6px;left:10px;font-weight:600;color:var(--grey)}
.vgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:center}.vcard{border:1.5px solid var(--line);border-radius:10px;padding:6px 4px}
.vcard p{margin:3px 0;font-size:12pt}.vcard .tk{display:flex;margin:4px 0 0 18%}
.words{font-size:13pt;background:var(--tint);border-radius:8px;padding:8px 12px;margin:6px 0 10px}.words b{color:var(--orange)}
.cards{display:grid;grid-template-columns:1fr 1fr;justify-items:center;gap:0}
.page.ws ul.check{font-size:13pt}.page.ws ul.check li{margin:9px 0}.page.ws ul.check .cb{flex-basis:16px;height:16px}
.cert{border:6px double var(--orange);border-radius:16px;padding:.5in .45in;text-align:center;margin-top:.4in}
.cert h1{font-size:46pt;margin:.1in 0}.cert .kicker{color:var(--orange);font:700 12pt "Space Grotesk",sans-serif;text-transform:uppercase;letter-spacing:.08em}
.certname{border-bottom:2px solid var(--night);height:.6in;margin:.15in .6in .25in}
.page.certp .ph .name{display:none}.page.certp h2{display:none}
"""


TRACKS = {
    "middle": {"line": "Grades 6–8", "build": middle, "css": "",
               "title": "Rocketry Worksheets: Grades 6–8",
               "desc": "Printable worksheets, the inclinometer template, safety pages, the flight log, the mission report planner and answer keys for the middle-school rocketry lessons (grades 6–8), which go with Rocket Builder by Quiver Design Works."},
    "elementary": {"line": "Grades 3–5", "build": elementary, "css": ELEM_CSS,
                   "title": "Rocketry Worksheets: Grades 3–5",
                   "desc": "Printable worksheets for the elementary paper-rocket lessons (grades 3–5): balloon, straw and stomp rockets, parachutes, 45-degree sighting cards, a safety pledge, a certificate and the answer key."},
}


def build(track: str) -> str:
    """Return the worksheets page for one track."""
    cfg = TRACKS[track]
    pages.clear()
    TRACK.update(name=track, line=cfg["line"])
    cfg["build"]()
    return f'''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{cfg["title"]}</title>
<meta name="description" content="{cfg["desc"]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../brand/tokens.css">
<style>{CSS}{diagrams.DG_CSS}{cfg["css"]}</style>
</head>
<body class="{track}">
{chr(10).join(pages)}
</body>
</html>
'''


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in TRACKS:
        sys.exit("usage: gen_ws.py middle|elementary OUT.html")
    text = build(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(text)
    print(sys.argv[1], "pages:", len(pages))

