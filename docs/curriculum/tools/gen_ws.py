"""Generate docs/curriculum/worksheets.html (static, printable)."""
import math
import sys

OUT = sys.argv[1]

pages = []


def page(code, title, body, sub="", kind="ws", track="all"):
    badge = f'<span class="badge">{code}</span>' if code else ""
    tag = {"all": '<span class="trk">All ages</span>', "12": '<span class="trk t12">12+ only</span>',
           "older": '<span class="trk">Grades 7–8</span>', "adult": '<span class="trk">Grown-ups</span>'}.get(track, "")
    name = '' if kind != "ws" else '<div class="name">Name <span class="blank w3"></span> Date <span class="blank w15"></span></div>'
    pages.append(f'''<section class="page {kind}">
<header class="ph"><div class="brandline"><span class="mark">{fletch_svg()}</span>Rocket Builder · Rockets &amp; Model Rocketry</div>{name}</header>
<h2>{badge}{title}{tag if code else ""}</h2>{f'<p class="sub">{sub}</p>' if sub else ''}
{body}
<footer class="pf"><span>Rocket Builder by Quiver Design Works · rocket.quiverdesignworks.net</span><span class="pn"></span></footer>
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
    out = [f'<svg class="fig" viewBox="0 0 600 185" style="width:4.3in" aria-label="inside a model rocket motor">{arrow_defs(pid)}']
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


# ---------------- COVER ----------------
contents = [
    ("W1", "Balloon rocket data", "Day 1"), ("W2", "Forces and launch angles", "Day 2"), ("W3", "Swing test", "Day 3"),
    ("W4", "Drag test", "Day 4"), ("W5", "Motor codes and impulse", "Day 5"), ("W6", "Design log", "Day 6"),
    ("W7", "Parachute drop test", "Day 7"), ("W8", "Altitude tracking", "Day 8"), ("T", "Inclinometer template", "Day 8"),
    ("W9", "Safety rules", "Day 9"), ("W9b", "Graph your week", "Day 9"), ("W9c", "Launch checklists", "Day 9"),
    ("L", "Paper-rocket launch log", "Day 10"), ("F", "Flight log (printed rocket)", "Day 10"),
    ("C", "Capstone planner and rubric", "Day 10"), ("Q", "Quick checks, Days 1–10", "Any day"), ("K", "Answer keys", "Grown-ups"),
]
ONLY12 = {"W5b": "Grades 7–8", "F": "12+ only", "K": "Grown-ups"}
cover = f'''<div class="cover">
<p class="kicker">A 2-week home-school unit · grades 3–8</p>
<h1>Rockets &amp; Model Rocketry</h1>
<p class="lede">Worksheets, data sheets, the inclinometer template and launch logs. Goes with <b>Rocket Builder by Quiver Design Works</b>, a free app at rocket.quiverdesignworks.net.</p>
<svg class="arc" viewBox="0 0 700 150" aria-hidden="true"><path d="M20 140 Q300 -60 680 120" fill="none" stroke="{SKY}" stroke-width="3" stroke-dasharray="10 8"/>
<g transform="translate(250 50) rotate(-6)"><path d="M150 -9 C170 -9 186 -4 196 0 C186 4 170 9 150 9 Z" fill="{ORANGE}"/><rect x="40" y="-9" width="110" height="18" fill="{NIGHT}"/><path d="M62 -9 L40 -30 L28 -30 L40 -9 Z M62 9 L40 30 L28 30 L40 9 Z" fill="{SKY}"/><path d="M40 -4 Q14 0 40 4 Z" fill="{ORANGE}" opacity=".7"/></g></svg>
{table(["", "Page", "Use on", "Who"], [[f"<b>{c}</b>", t, d, ONLY12.get(c, "All ages")] for c, t, d in contents], ["0.6in", None, "1.1in", "1.1in"], cls="toc")}
<div class="note"><b>Printing:</b> US Letter, portrait, scale 100% ("actual size"), so the inclinometer comes out the right size. Turn on "background graphics" if you want the coloured bands. Print the answer keys only for the grown-up.</div>
<div class="note"><b>Two tracks:</b> <b>under 12</b> (about grades 3–6) flies paper-style rockets only (balloon, straw, paper and stomp rockets; fizzy rockets with an adult) and uses Rocket Builder on screen. <b>12+</b> also designs, prints and flies a Rocket Builder rocket on a real motor. Every page is for all ages unless it says <b>12+ only</b>.</div>
<div class="note warn"><b>Safety:</b> model rocket motors are rated 12+, and grown-ups handle all motors and igniters. Wear safety glasses for straw, stomp and fizzy rockets. Follow the NAR Model Rocket Safety Code.</div>
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
<p class="hint">Average = (trial 1 + trial 2 + trial 3) ÷ 3. Grades 3–4: circle the longest trial instead.</p>
<h3>Think about it</h3>
<ol class="qs">
<li>Newton's <b>third</b> law: the balloon pushes air out the back. What pushes the balloon forward?{lines(1)}</li>
<li>Newton's <b>second</b> law: in Part B, the push was the same. What happened when you added paper clips? Why?{lines(2)}</li>
<li>Newton's <b>first</b> law: why did the straw stay still until you let go? Why did it stop at the end?{lines(2)}</li>
<li>Rocket Builder: press <b>▶ Watch it launch</b>. Write three things you noticed.{lines(2)}</li>
</ol>
<div class="ext"><b>Grades 7–8:</b> a balloon pushes with 0.1 N on a 10 g (0.010 kg) rocket. Ignoring friction, a = F ÷ m = ______ m/s². With 10 g of paper clips added: a = ______ m/s².</div>'''
page("W1", "Balloon rocket data", w1, "Day 1 · Newton's three laws")

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
<li><b>12+:</b> the <b>power</b> bar (thrust ÷ weight) for my rocket says ______ ×. Is it 5× or more? ______</li></ol>'''
page("W2", "Forces and launch angles", w2, "Day 2 · The four forces")

# ---------------- W3 ----------------
w3 = f'''{vocab(["stable", "unstable", "balance point (CG)", "push point (CP)", "caliber", "stability score"])}
{stability_svg("sa")}
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
page("W3", "Swing test", w3, "Day 3 · Stability: balance point and push point")

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
<div class="ext"><b>Grades 7–8:</b> drag = ½ × 1.2 × speed² × Cd × area. A rocket with area 0.00071 m² and Cd 0.65 at 40 m/s: drag ≈ ______ N. In Rocket Builder (Advanced → Flight → Advanced), predicted altitude with Cd 0.5: ______ m; Cd 0.8: ______ m.</div>'''
page("W4", "Drag test", w4, "Day 4 · Drag and shape")

# ---------------- W5 ----------------
classes = table(["Class", "1/4A", "1/2A", "A", "B", "C", "D", "E", "F"],
                [["Total impulse up to (N·s)", "0.625", "1.25", "2.5", "5", "10", "20", "40", "80"],
                 ["Smallest field (NAR)", "15 m", "15 m", "30 m", "60 m", "120 m", "150 m", "300 m", "300 m"]], ["1.7in"] + [None]*8, cls="small")
w5 = f'''{vocab(["propellant", "nozzle", "delay", "ejection charge", "igniter", "total impulse", "impulse class", "thrust-to-weight"])}
{motor_svg("ma")}
<p class="hint"><b>Motor rockets are 12+, and only grown-ups handle motors and igniters.</b> This drawing shows the inside of a motor. Never open one.</p>
{classes}
<h3>1. Decode the motor codes</h3>
{table(["Code", "Impulse class", "Average thrust (N)", "Delay (s)", "Smallest field"], [[c, "", "", "", ""] for c in ["A8-3", "B6-4", "C6-5", "D12-5"]])}
<h3>2. Impulse = average thrust × burn time</h3>
{table(["Motor", "Average thrust (N)", "Burn time (s)", "Total impulse (N·s)", "Class"], [["a", "3", "0.8", "", ""], ["b", "5", "0.9", "", ""], ["c", "10", "1.7", "", ""], ["d", "15", "3.4", "", ""]])}
<h3>3. Rocket Builder and fizzy rockets (everyone)</h3>
<p>The best motor for my design is ______ and it should fly about ______ m high. Fizzy rockets: the amount of water that worked best was ______ tsp.</p>
<h3>4. Thrust-to-weight (grades 5–8; it must be 5 or more)</h3>
<p class="hint">100 g weighs about 1 N. So a rocket of 80 g weighs about 0.8 N.</p>
<ol class="qs">
<li>Rocket + motor = 80 g. Motor average thrust = 5 N. Weight = ______ N. Thrust ÷ weight = ______. Pass? ______</li>
<li>Rocket + motor = 120 g. Motor average thrust = 4.7 N. Weight = ______ N. Thrust ÷ weight = ______. Pass? ______</li>
</ol>'''
page("W5", "Motor codes and impulse", w5, "Day 5 · Motors, thrust and impulse")

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
page("W5b", "Thrust curve", w5b, "Day 5 · Grade 7–8 extension: impulse is the area under the thrust curve", track="older")

# ---------------- W6 ----------------
w6 = f'''<div class="row"><div class="col">{vocab(["criteria", "constraints", "iteration", "prototype", "trend", "model"])}
<p><b>Criteria</b> (what it must do): score 1–2 cal (2–3 OK) · a motor gets ✓ Good · height fits our field · <span class="blank w2"></span></p>
<p><b>Constraints</b> (limits): printer height ______ mm · field size ______ m · <span class="blank w2"></span></p></div>
<div class="col narrow">{cycle_svg()}</div></div>
{table(["#", "Height (mm)", "Fin shape", "Nose", "Score (cal)", "Fins grew? ✓", "Best motor", "Altitude (m)", "Power (×)", "Off rod (m/s)"], 8, ["0.3in", "0.75in", "0.85in", "0.75in", "0.6in", "0.6in", "0.75in", "0.75in", "0.6in", None], first_col=[str(i) for i in range(1, 9)])}
{grid(7.3, 2.0, 30, 10, "height (mm)", "score (cal)", "Line graph: height vs score")}
<p><b>The trend:</b> as the height went up, the score <span class="blank w4"></span></p>
<h3>Decision table: score each design 1 (poor) to 3 (great)</h3>
{table(["Design #", "Stability (1–2 cal is best)", "Altitude fits our field", "Looks", "Print time (12+)", "Total"], 3, first_col=["", "", ""])}
<p><b>I chose design # ______ because</b> <span class="blank w5"></span></p>
<p><b>▶ Watch it launch:</b> it went up about ______ m and landed about ______ m from the pad.</p>'''
page("W6", "Design log", w6, "Day 6 · The engineering design cycle with Rocket Builder")

# ---------------- W7 ----------------
w7 = f'''<div class="row"><div class="col">{vocab(["recovery", "canopy", "shroud lines", "descent rate", "terminal speed", "drift"])}
<p><b>Drop height:</b> ______ m &nbsp; <b>Weight on each parachute:</b> <span class="blank w15"></span></p>
<p class="hint">Descent rate (m/s) = drop height ÷ average time</p></div>
<div class="col narrow">{chute_svg("ca")}</div></div>
{table(["Parachute", "Trial 1 (s)", "Trial 2 (s)", "Trial 3 (s)", "Average time (s)", "Descent rate (m/s)"], 4, first_col=["No parachute", "20 cm", "30 cm", "40 cm"])}
<p><b>Part B (optional), 30 cm parachute:</b></p>
{table(["Washers", "Trial 1 (s)", "Trial 2 (s)", "Trial 3 (s)", "Average time (s)", "Descent rate (m/s)"], 3, first_col=["1", "2", "4"])}
{grid(7.3, 1.65, 25, 7, "canopy size (cm)", "average fall time (s)", "Line graph:")}
<h3>Your rocket's parachute (Rocket Builder)</h3>
<p>Parachute size: ______ inches. Descent speed: ______ m/s. Predicted altitude: ______ m.</p>
<p>Time to come down = altitude ÷ descent speed = ______ s. &nbsp; Drift in a 10 mph (4.5 m/s) breeze = time × 4.5 = ______ m.</p>
<ol class="qs"><li>Practice: a rocket reaches 120 m and falls at 4 m/s. Time = ______ s. Drift = ______ m. Is a 60 m field big enough? ______</li>
<li>Why not just use the biggest parachute you can find?{lines(1)}</li></ol>'''
page("W7", "Parachute drop test", w7, "Day 7 · Parachutes and descent rate")

# ---------------- W8 ----------------
w8 = f'''<div class="row"><div class="col">{triangle_svg("ta")}</div><div class="col fixed">{tan_table()}</div></div>
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
<li><b>Grades 7–8:</b> with a 50 m baseline, an angle of 45° gives ______ m and 47° gives ______ m. At 75°: ______ m; at 77°: ______ m. Which angle is more sensitive to a 2° mistake? <span class="blank w15"></span></li></ol>'''
page("W8", "Altitude tracking", w8, "Day 8 · Measuring height with angles")

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
page("T", "Inclinometer template", tmpl, "Day 8 · Print at 100% (actual size)", kind="ws tmpl")

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
<div class="note"><b>Paper-rocket rules (everyone):</b> glasses on · never aim at anyone · wait for "launch!" · a grown-up runs fizzy rockets · never chase a rocket into a road, tree or power line.<br>
<b>Motor rockets (12+):</b> grown-ups handle motors, igniters and the key · 15 ft back · count down from 5 · misfire: key out, wait 60 s · wind under 20 mph · never catch a rocket.</div>
<h3>1. Is it safe?</h3>
{table(["Story", "Safe or not safe?", "Which rule?"], [[st, "", ""] for st in stories], [None, "1.1in", "1.9in"])}
<h3>2. Launch team jobs</h3>
{table(["Job", "Who (grown-up or kid?)", "Name"], [[j, "", ""] for j in ["Countdown caller", "Stomper (paper rockets)", "Trackers (inclinometers)", "Recorder (launch log)", "Recovery crew", "12+: Launch Control Officer (key, button)", "12+: Range Safety Officer (checks the rocket)", "12+: loads the motor and igniter"]], [None, "1.6in", "1.9in"])}"""
page("W9", "Safety rules", w9, "Day 9 · Paper-rocket rules and the NAR Model Rocket Safety Code")

w9c = f"""<h3>1. Weather check (everyone)</h3>
<p>Forecast wind: ______ mph. Under 20 mph? ______ (Less wind is better: under 10 mph means less drift.) &nbsp; Rain? ______</p>
<h3>2. Paper-rocket launch checklist (everyone)</h3>
{checklist(["Safety glasses for everyone", "Stomp rocket, spare rockets and the launcher tube", "Straw rockets and straws", "Fizzy rocket supplies and water (the grown-up keeps the tablets)", "My best drop-test parachute", "Two inclinometers, a tape measure, two stopwatches", "Launch log on a clipboard, pencils", "Rocket Builder open on a tablet or phone, for ▶ Watch it launch", "Water, hats, sunscreen"])}
<div class="pagebreak-hint">The rest of this page is for the <b>12+ printed-rocket track</b>.</div>
<h3>3. Field check (12+)</h3>
<p>Field size: ______ m by ______ m. &nbsp; Rocket Builder's suggested field: ______ m. Big enough? ______ &nbsp; If not: a smaller motor that still gets a ✓, or a club launch.</p>
<h3>4. Preflight checklist (12+)</h3>
<div class="row"><div class="col">{checklist(["Weighed: ______ g (app said ______ g)", "Fins firm, no cracks", "Nose slides off smoothly", "Shock cord (braided flat elastic) tied tightly at both ends", "Parachute not torn, lines not tangled"])}</div>
<div class="col">{checklist(["Balance point with motor (a grown-up puts it in, no igniter): ______ mm from the tip (app CG ______ mm)", "Swing test: nose leads", "Motor taken out again by a grown-up", "Launch box packed; motors, igniters and key with the grown-up"])}</div></div>"""
page("W9c", "Launch checklists", w9c, "Day 9 · Get ready for launch day")

w9b = f'''<p><b>My data set:</b> <span class="blank w4"></span> (from Day ______)</p>
<p><b>Graph type:</b> bar graph / line graph / scatter plot (circle one). &nbsp; Remember: a title, labels on both axes, units, and evenly spaced numbers.</p>
{grid(7.3, 5.2, 30, 20, "", "", "Title:")}
<p><b>Mean</b> of one group of trials: ( ______ + ______ + ______ ) ÷ 3 = ______ &nbsp;&nbsp; <b>Range</b> = ______ − ______ = ______</p>
<ol class="qs"><li>As <span class="blank w15"></span> went up, <span class="blank w15"></span> went <span class="blank w15"></span>.</li>
<li>One thing that might have made my data less accurate is{lines(1)}</li>
<li><b>Grades 7–8:</b> draw a line of best fit by eye. Is the relationship a straight line? Where does it bend?{lines(1)}</li></ol>'''
page("W9b", "Graph your week", w9b, "Day 9 · Data and graphing")

# ---------------- Flight log ----------------
llog = f"""<p><b>Date:</b> ______ &nbsp; <b>Place:</b> <span class="blank w2"></span> &nbsp; <b>Wind:</b> ______ mph &nbsp; <b>Tracker 1 baseline:</b> ______ m &nbsp; <b>Tracker 2 baseline:</b> ______ m</p>
{table(["#", "Rocket or launcher", "What I changed", "My guess (m)", "Tracker 1 angle", "Tracker 2 angle", "Height (m)", "Notes"], 14, ["0.3in", "1.2in", "1.25in", "0.65in", "0.65in", "0.65in", "0.65in", None], cls="tall", first_col=[str(i) for i in range(1, 15)])}
<p class="hint">Height = baseline × multiplier + eye height (the multiplier table is on W8 and the template). Average the two trackers. Grades 3–4: write the angles and let a grown-up help with the multiplying.</p>
<ol class="qs"><li>Which launch went highest? What was different about it?{lines(1)}</li>
<li>How close were your guesses? Did they get better as the day went on?{lines(1)}</li></ol>"""
page("L", "Paper-rocket launch log", llog, "Day 10 · Stomp, straw and fizzy rockets")

flog_rows = ["Rocket name", "Date and time", "Place", "Wind (mph) and direction", "Temperature", "Rocket mass, no motor (g)",
             "Motor (a grown-up loads it)", "Parachute size", "Predicted altitude (m)", "Tracker 1: baseline (m) and angle",
             "Tracker 2: baseline (m) and angle", "Measured altitude (m)", "Liftoff to parachute (s)", "Parachute to landing (s)",
             "Landed how far from the pad?", "Did it fly straight?", "Parachute opened near the top?", "Condition after landing", "Notes"]
flog = f'''{table(["", "Flight 1", "Flight 2", "Flight 3"], [[r, "", "", ""] for r in flog_rows], ["2.1in", None, None, None], cls="log")}
<p class="hint">Altitude = baseline × multiplier (or × tan of the angle) + eye height. Average the trackers. Difference = predicted − measured.</p>
<div class="note warn"><b>Launch day rules:</b> grown-ups handle motors, igniters and the key · glasses on, at least 15 ft back · count down from 5 · misfire: key out, wait 60 s · never chase a rocket into trees, roads or power lines · never catch it.</div>'''
page("F", "Flight log (printed rocket)", flog, "Day 10 · Launch day, 12+ track", track="12")

# ---------------- Capstone ----------------
parts = [("1. Mission", "What did you set out to do?", 1), ("2. Design", "Your Rocket Builder rocket with the blue and red dots and its score, and why you chose it (use Day 6 data). You can add your best paper rocket.", 2),
         ("3. The science", "(a) Newton's 3rd law and thrust · (b) why the balance point is in front of the push point · (c) how a parachute works.", 2),
         ("4. Guess vs launch", "Table or graph: your guesses and the heights you measured (12+: the app's prediction and the real flight).", 1), ("5. What happened and why", "Reasons for any differences.", 2),
         ("6. Next time", "One change, and what you predict it will do.", 1), ("7. Safety", "Two rules your team followed and why they matter.", 1)]
cap = "".join(f'<div class="cp"><b>{t}</b> <span class="hint">{h}</span>{lines(n)}</div>' for t, h, n in parts)
rub = table(["", "4 Excellent", "3 Good", "2 Getting there", "1 Just starting", "Score"], [
    ["<b>Science</b>", "Explains Newton's 3rd law, stability and parachutes correctly, in own words, with examples", "All three, small mistakes", "One or two", "Missing or mostly incorrect", ""],
    ["<b>Design process</b>", "Several iterations with data; one change at a time; data justifies the choice", "Iterations and a reason", "A design, little data", "No reasons", ""],
    ["<b>Data and math</b>", "Launch log complete; heights correct; compared with the prediction (gr. 7–8: % difference)", "Mostly complete; small errors", "Some data; calculation incomplete", "Little or no data", ""],
    ["<b>Explaining results</b>", "Two or more sensible reasons; a testable next step", "One reason and a next step", "A reason or a next step", "Neither", ""],
    ["<b>Communication and safety</b>", "Clear, labelled pictures and graphs; two safety rules and why", "Clear, one piece missing", "Hard to follow in places", "Most parts missing", ""],
], ["1.15in", "1.9in", None, None, None, "0.5in"], cls="rubric")
capstone = f'''<p>Make a poster, slides, a written report or a 3–5 minute talk. Plan each part here.</p>{cap}
<h3>Rubric</h3>{rub}
<p class="hint"><b>Total ______ / 20.</b> 17–20 mission accomplished · 13–16 solid flight · 9–12 needs another iteration · below 9 back to the pad.</p>'''
page("C", "Capstone planner and rubric", capstone, "Day 10 · Mission report")

# ---------------- Quick checks ----------------
QC = [
    ("Day 1", ["A rocket pushes gas down. The gas pushes the rocket up. Which of Newton's laws is this?", "Two balloon rockets get the same push. One has 10 paper clips. Which speeds up more?", "A rocket sits on the launch pad. Why doesn't it move until the motor fires?", "True or false: a rocket needs air to push against.", "Write F = m × a in words."]),
    ("Day 2", ["Which force always points straight down?", "Which force always points opposite to the motion?", "During the coast, which forces act on the rocket?", "Thrust is 6 N and weight is 1 N. Is thrust at least 5 times the weight?", "Under a parachute the rocket falls at a steady speed. Balanced or unbalanced?"]),
    ("Day 3", ["Which dot must be in front: blue (balance point) or red (push point)?", "Name two ways to move the push point backward.", "Body 2 cm wide; push point 3 cm behind the balance point. Score?", "Is a score of 0.5 cal OK to fly?", "What happens to a 4 cal rocket on a windy day?"]),
    ("Day 4", ["Name three things that make drag bigger.", "Twice as fast: how much bigger is the drag?", "In a fair test, how many variables do you change at once?", "Which has more drag: a flat nose or a pointed nose?", "Why not put huge fins on every rocket?"]),
    ("Day 5", ["In B6-4, what do the B, the 6 and the 4 mean?", "5 N average for 2 s: total impulse? Class?", "Which has more total push, C or B? About how much more?", "Rocket with motor weighs 1.2 N; thrust 5 N. At least 5 times?", "Who puts the igniter in the motor?"]),
]
QC2 = [
    ("Day 6", ["Put in order: test, ask, create, improve, imagine, plan.", "What's the difference between a criterion and a constraint?", "Why change only one thing at a time?", "Your design scores 0.8 cal. Name two things you could change.", "Your rocket scores 3.6 cal. Is that a problem?"]),
    ("Day 7", ["A parachute falls 3 m in 1.5 s. Descent rate?", "Bigger canopy, same weight: faster or slower?", "At a steady speed, which two forces are balanced?", "Rocket Builder aims for about what descent speed?", "From 100 m at 4 m/s in a 4.5 m/s wind: how far does it drift?"]),
    ("Day 8", ["30 m from a flagpole, looking up at 45°. How tall (no eye height)?", "Baseline 50 m, angle 60° (multiplier 1.73). How high?", "Which side of the triangle is the baseline?", "Why add your eye height?", "Should you ever look at the sun through the straw?"]),
    ("Day 9", ["How far back for a D motor or smaller?", "After a misfire, what two things happen before anyone goes to the pad?", "Highest wind speed you can launch in?", "Who handles motors and igniters?", "Trials 4 m, 5 m, 6 m: mean? range?"]),
    ("Day 10", ["Order: apogee, liftoff, burnout, landing, parachute opens.", "What makes the rocket go up, using Newton's 3rd law?", "Two trackers measured 12 m and 14 m. Average?", "Predicted 150 m, flew 120 m. How many metres short? (Gr. 7–8: what percent?)", "Who takes the spent motor out?"]),
]


def qc_page(groups, title):
    body = '<div class="qcgrid">' + "".join(
        f'<div class="qc"><h3>{d}</h3><ol>' + "".join(f"<li>{q}<span class='qa'></span></li>" for q in qs) + "</ol></div>" for d, qs in groups) + "</div>"
    page("Q", title, body, "Answer on the line. Answers are in the day's lesson plan and in the answer keys.")


qc_page(QC, "Quick checks, Days 1–5")
qc_page(QC2, "Quick checks, Days 6–10")

# ---------------- Answer keys ----------------
def key(title, items):
    return f'<div class="key"><h3>{title}</h3><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


k1 = (key("W1 Balloon rocket", [
    "Data varies. Expect: bigger balloons go further (more air = a longer push). More paper clips go less far (more mass, same push = less acceleration).",
    "Q1: the air pushes back on the balloon (action and reaction). Q2: it went less far / slower; the same force on more mass gives less acceleration. Q3: no unbalanced force until the air rushed out (law 1); friction on the string and air drag finally stopped it.",
    "Grades 7–8: 0.1 ÷ 0.010 = 10 m/s²; 0.1 ÷ 0.020 = 5 m/s²."])
      + key("W2 Forces", [
          "1 On the pad: weight down, the pad pushes up (equal). 2 Boost: big thrust up; weight and drag down. 3 Coast: weight and drag both down; no thrust. 4 Parachute: weight down, drag up (equal).",
          "Balanced: 1 and 4. Unbalanced: 2 and 3.",
          "Launch angle: about 40–45° usually goes furthest. Watch it launch order: liftoff 1, boost 2, coast 3, top 4, parachute 5. Power bar (12+): the app's thrust ÷ weight; it passes at 5× or more."])
      + f'<div class="center">{forces_svg(True, "fk")}</div>'
      + key("W3 Swing test", [
          "Data varies. Usually C (fins + nose clay) is most stable: its balance point is furthest in front of its push point. A often tumbles; D is often wobbly.",
          "Nose clay moves the balance point forward (a bigger gap); tail clay moves it back, toward or behind the push point.",
          "4.5 ÷ 3 = 1.5 cal: just right."])
      + key("W4 Drag test", [
          "Data varies. The flat nose usually goes least far (most drag). Cone and round are often close; small differences may be luck: more trials, a fairer launcher.",
          "Fin trade-off: no fins wobble and land short; medium fins fly straight; very large fins fly straight but may lose a little distance from drag and weight.",
          "Grades 7–8: 0.5 × 1.2 × 1600 × 0.65 × 0.00071 ≈ 0.44 N. Lower Cd gives a higher predicted altitude."]))
page("K", "Answer keys (1 of 3)", k1, "For grown-ups", kind="ws key", track="adult")

k2 = (key("W5 Motor codes and impulse", [
    "Decode: A8-3 = A, 8 N, 3 s, 30 m · B6-4 = B, 6 N, 4 s, 60 m · C6-5 = C, 6 N, 5 s, 120 m · D12-5 = D, 12 N, 5 s, 150 m.",
    "Impulse: a 3 × 0.8 = 2.4 N·s, A · b 5 × 0.9 = 4.5 N·s, B · c 10 × 1.7 = 17 N·s, D · d 15 × 3.4 = 51 N·s, F.",
    "Thrust-to-weight: 0.8 N; 5 ÷ 0.8 ≈ 6.3; pass. 1.2 N; 4.7 ÷ 1.2 ≈ 3.9; does not pass (too heavy for this motor).",
    "Part 3: the motor and height come from the app's How high will it go? card. Fizzy rockets: data varies; look for a sensible reason (room for gas to build pressure vs. enough water for the tablet to fizz fast)."])
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
          "Too big a parachute: the rocket hangs in the air longer and drifts further (trees, roads, outside the field)."])
      + key("W8 Altitude tracking", [
          "Practice 1: 25 × 0.84 + 1.3 = 22.3 m. Practice 2: 80 × 1.43 + 1.5 ≈ 116 m. Scale drawing: about 7 squares = 14 m (tan 35° × 20 m = 14 m).",
          "Errors: angle reading (string swinging), baseline measured wrong, not catching the very top, the rocket drifting toward or away from you, eye height forgotten.",
          "Grades 7–8: 50.0 m and 53.6 m; 186.6 m and 216.6 m. Steep angles (75°) are much more sensitive."]))
page("K", "Answer keys (2 of 3)", k2, "For grown-ups", kind="ws key", track="adult")

qa = {
    "Day 1": ["Third law.", "The one with no paper clips.", "Forces are balanced; it stays put until thrust (law 1).", "False.", "Force equals mass times acceleration."],
    "Day 2": ["Weight.", "Drag.", "Weight and drag (no thrust).", "Yes: 6 ÷ 1 = 6.", "Balanced."],
    "Day 3": ["Blue (balance point).", "Bigger fins, swept-back fins, a longer body.", "1.5 cal.", "No: wobbly, can't download.", "It weathercocks into the wind."],
    "Day 4": ["Speed, frontal area, blunt shape, roughness.", "About 4 times.", "One.", "Flat nose.", "Extra drag and weight; can be over-stable."],
    "Day 5": ["Class B, about 6 N average thrust, 4 s delay.", "10 N·s, class C.", "C, up to about twice.", "No: about 4.2.", "A grown-up."],
    "Day 6": ["Ask, imagine, plan, create, test, improve.", "Criterion = what it must do; constraint = a limit.", "To know which change caused the result.", "Taller, bigger fins, lighter motor, nose weight.", "Yes, over-stable: weathercocks."],
    "Day 7": ["2 m/s.", "Slower.", "Drag and weight.", "About 4.5 m/s or less (3–5 m/s).", "25 s × 4.5 ≈ 113 m."],
    "Day 8": ["30 m.", "About 87 m (+ eye height).", "Along the ground, you to the base.", "The angle is measured from your eye.", "Never."],
    "Day 9": ["15 feet (5 m).", "Key out, wait 60 seconds.", "20 mph.", "A grown-up.", "Mean 5 m; range 2 m."],
    "Day 10": ["Liftoff, burnout, apogee, parachute opens, landing.", "Motor pushes gas down; gas pushes rocket up (stomp: air pushes it off).", "13 m.", "30 m; 20%.", "A grown-up, after it cools."],
}
k3 = (key("W9 Safety rules", [
    "Stories: 1 safe (glasses on) · 2 not safe (never aim at anyone) · 3 not safe (a grown-up handles the tablets; never lean over a canister) · 4 safe (key with the grown-up; 15 ft back) · 5 not safe (misfire: key out, wait 60 s; grown-ups handle motors) · 6 not safe (no launches over 20 mph) · 7 not safe (never recover from tall trees) · 8 safe (count down out loud) · 9 not safe (never open or change a motor) · 10 not safe (never catch a rocket).",
    "Jobs: countdown caller, stomper, trackers, recorder and recovery crew = kids (recovery only when the grown-up says so). LCO, RSO and loading motors/igniters = grown-ups (12+ track)."])
      + key("W9b Graph your week", ["Check: title, both axes labelled with units, even scale, correct plotting, a sensible trend sentence. Grades 7–8: drop-test speed goes with 1 ÷ √area, so it curves rather than falling in a straight line."])
      + '<div class="key"><h3>Quick checks</h3><div class="qak">' + "".join(
          f'<p><b>{d}:</b> ' + " ".join(f"{i+1}. {a}" for i, a in enumerate(v)) + "</p>" for d, v in qa.items()) + "</div></div>"
      + key("Flight log and capstone", ["Use the rubric. Check the altitude math: baseline × multiplier + eye height, averaged over trackers; percent difference = (predicted − measured) ÷ predicted × 100."]))
page("K", "Answer keys (3 of 3)", k3, "For grown-ups", kind="ws key", track="adult")

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
.ph{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--night);padding-bottom:5px;margin-bottom:8px;font-size:9pt}
.brandline{display:flex;align-items:center;gap:6px;font-weight:600;letter-spacing:.02em}
.name{color:var(--night)}
.blank{display:inline-block;border-bottom:1px solid var(--night);height:1em;vertical-align:baseline}
.blank.w15{width:.9in}.blank.w2{width:1.3in}.blank.w3{width:2in}.blank.w4{width:2.8in}.blank.w5{width:4.2in}
h2{font-size:19pt;margin:2px 0 0;display:flex;align-items:center;gap:10px;line-height:1.15}
.badge{background:var(--orange);color:#fff;font-size:12pt;padding:2px 9px;border-radius:6px;font-weight:700}
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

html = f'''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rocketry Worksheets</title>
<meta name="description" content="Printable worksheets, data sheets, inclinometer template, launch logs and answer keys for the Rockets and Model Rocketry home-school unit (grades 3–8), which goes with Rocket Builder by Quiver Design Works.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../brand/tokens.css">
<style>{CSS}</style>
</head>
<body>
{chr(10).join(pages)}
</body>
</html>
'''
with open(OUT, "w") as f:
    f.write(html)
print("pages:", len(pages))
