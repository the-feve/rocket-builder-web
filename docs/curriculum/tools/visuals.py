"""Diagrams and pictures for the rocketry lessons, shared by build_site.py (web pages) and
gen_ws.py (worksheets).

- icon(name): small line icons (24 x 24, 2 px, currentColor) in the brand's supply-icon style.
- art(name, caption): one of the hand-drawn activity pictures in docs/curriculum/art/, inlined.
- The learning pathways: track_path() (track overview), mini_path() (top of each lesson),
  tracks_map() (the /learn chooser), journey_svg() (the printable unit map in the worksheets).
- lesson_flow(): the time bar of a lesson's steps. glance(): the time / worksheet / app chips.
- standards_matrix() (track overview) and progression() (teachers page).

Phases and the adult plan-ahead milestones are written here; keep them in step with the track
READMEs ("Lessons at a glance", "Plan ahead").
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ART = Path(__file__).resolve().parent.parent / "art"

NIGHT, PAPER, ORANGE, SKY, RED, GREEN, GREY = "#12203A", "#FFFDF8", "#F2652B", "#3D8BFD", "#E5484D", "#2FB67C", "#6E6E73"

# ---------------------------------------------------------------- icons
# 24-unit grid, drawn with currentColor so they follow the theme. Orange, blue and red only
# where they mean something (motion, balance point, push point, parachute).
_ICONS = {
    "balloon": '<ellipse cx="12" cy="9" rx="6" ry="7"/><path d="M12 16l-1.6 2.2h3.2z"/><path d="M12 18.2c-2 1.8 2 3 0 4.8"/>',
    "straw": '<path d="M12 2c2 2 2.4 4 2.4 6v8H9.6V8C9.6 6 10 4 12 2z"/><path d="M9.6 12.5 7 16v2h2.6M14.4 12.5 17 16v2h-2.6"/>'
             '<path d="M12 18v5" stroke="{o}"/>',
    "angle": '<path d="M3 20h18"/><path d="M3 20 17 6"/><path d="M11 20a8 8 0 0 0-2.3-5.7"/><path d="M14 5h4v4" stroke="{o}"/>',
    "balance": '<path d="M2.5 12h13c2.8 0 5 .9 6 2-1 1.1-3.2 2-6 2h-13z" transform="translate(0 -2)"/>'
               '<path d="M2.5 10 1 6.5h3l3 3.5M2.5 14 1 17.5h3l3-3.5"/><path d="M12 10V3"/>'
               '<circle cx="12" cy="12" r="1.7" fill="{s}" stroke="none"/><circle cx="6.5" cy="12" r="1.7" fill="{r}" stroke="none"/>',
    "stomp": '<rect x="2" y="15" width="11" height="6" rx="2.5"/><path d="M13 18h4.5V9"/><path d="M15.5 9 17.5 3l2 6z"/>'
             '<path d="M7.5 3v8m-2.5-2.5 2.5 2.5 2.5-2.5" stroke="{o}"/>',
    "test": '<rect x="2" y="15" width="20" height="6" rx="1"/><path d="M6 15v2.5M10 15v3.5M14 15v2.5M18 15v3.5"/>'
            '<path d="M7 10a5 5 0 0 1 9.5-2.2" stroke="{o}"/><path d="M17.5 4.5l-.6 3.6-3.6-.8" stroke="{o}"/>',
    "parachute": '<path d="M3 10a9 7 0 0 1 18 0z" fill="{o}"/><path d="M3 10l9 8 9-8M12 10v8"/><rect x="10" y="18" width="4" height="4" rx=".5"/>',
    "launch": '<path d="M3 21c3-7 7-12 13-14.5" stroke-dasharray="2 2.6"/><path d="M21.5 2.5l-7 2-3 3.5 3.5 3.5 3.5-3z"/>'
              '<path d="M11.5 8 8.5 8.5 7.5 10.5l3 .5M15.5 12l-.5 3-2 1-.5-3"/>',
    "newton": '<path d="M11 12H3m3-3-3 3 3 3"/><path d="M13 12h8m-3-3 3 3-3 3" stroke="{o}"/><path d="M12 6v12" stroke-dasharray="2 2"/>',
    "forces": '<path d="M12 3c1.6 1.6 2.2 3.2 2.2 5.2V16H9.8V8.2C9.8 6.2 10.4 4.6 12 3z"/>'
              '<path d="M19 15V4m-2.3 2.3L19 4l2.3 2.3" stroke="{o}"/><path d="M5 7v11m-2.3-2.3L5 18l2.3-2.3"/>',
    "nose": '<path d="M6 21v-6c0-6 3-10 6-12 3 2 6 6 6 12v6z"/><path d="M2 8c2 0 3 1 3 3M22 8c-2 0-3 1-3 3" stroke-dasharray="2 2"/>',
    "motor": '<rect x="2" y="8" width="16" height="8" rx="1"/><path d="M18 10l3-1.5v7L18 14"/><path d="M7 8v8M12 8v8"/>',
    "laptop": '<rect x="4" y="4" width="16" height="11" rx="1.2"/><path d="M2 19.5h20l-2-4.5H4z"/>'
              '<path d="M8 11.5 14.5 7l1 1.3-6.5 4.5z"/><circle cx="11" cy="10" r="1" fill="{s}" stroke="none"/>',
    "inclinometer": '<path d="M3 7h18a9 9 0 0 1-18 0z"/><path d="M12 7l-3.2 9.5"/><circle cx="8.4" cy="17.6" r="1.6"/><path d="M1 4.5h22" stroke="{o}"/>',
    "flag": '<path d="M5 22V3"/><path d="M5 4h13l-2.5 4 2.5 4H5"/>',
    "glasses": '<circle cx="7" cy="14" r="4"/><circle cx="17" cy="14" r="4"/><path d="M11 14h2M3 13 2 9M21 13l1-4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "sheet": '<path d="M6 2.5h9l4 4V21.5H6z"/><path d="M15 2.5v4h4M9 11h7M9 14.5h7M9 18h4"/>',
    "print": '<path d="M6 9V3h12v6"/><rect x="2.5" y="9" width="19" height="8" rx="1.5"/><path d="M7 14h10v7.5H7z"/>',
    "people": '<circle cx="8" cy="7" r="3"/><path d="M2.5 21v-2.5A5.5 5.5 0 0 1 13.5 18.5V21"/><circle cx="17" cy="8.5" r="2.5"/><path d="M15.5 13.5A4.5 4.5 0 0 1 21.5 17.5V21"/>',
    "check": '<path d="M4.5 12.5l5 5 10-11"/>',
    "star": '<path d="M12 2.8l2.8 5.8 6.3.8-4.6 4.4 1.2 6.3L12 17l-5.7 3.1 1.2-6.3-4.6-4.4 6.3-.8z"/>',
}


def icon(name: str, size: int = 24, cls: str = "ico") -> str:
    body = _ICONS[name].format(o=ORANGE, s=SKY, r=RED)
    return (f'<svg class="{cls}" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{body}</svg>')


# ---------------------------------------------------------------- activity pictures
def art_svg(name: str, width: str | None = None) -> str:
    """The picture's SVG markup, ready to inline: no XML prolog or comments, and it scales to
    its box (the viewBox stays; width/height go)."""
    src = (ART / name).read_text(encoding="utf-8")
    src = re.sub(r"<\?xml[^>]*\?>\s*", "", src)
    src = re.sub(r"<!--.*?-->\s*", "", src, flags=re.S)
    src = re.sub(r"\s+xmlns:xlink=\"[^\"]*\"", "", src)

    def root(m):
        tag = re.sub(r'\s(width|height)="[^"]*"', "", m.group(0))
        style = f"width:{width};height:auto" if width else "width:100%;height:auto"
        return tag[:-1].rstrip() + f' style="{style}">'
    return re.sub(r"<svg\b[^>]*>", root, src, count=1).strip()


def art(name: str, caption: str = "") -> str:
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return f'<figure class="art">{art_svg(name)}{cap}</figure>'


# ---------------------------------------------------------------- pathway data
ICONS = {
    "elementary": {1: "balloon", 2: "straw", 3: "angle", 4: "balance", 5: "stomp", 6: "test", 7: "parachute", 8: "launch"},
    "middle": {1: "newton", 2: "forces", 3: "balance", 4: "nose", 5: "motor", 6: "laptop", 7: "parachute", 8: "inclinometer", 9: "launch"},
}
PHASES = {
    "elementary": [("Pushes and pulls", [1, 2, 3]), ("Design like an engineer", [4, 5, 6]), ("Fly and land", [7, 8])],
    "middle": [("Forces and motion", [1, 2]), ("Flying straight", [3, 4]), ("Energy and design", [5, 6]),
               ("Landing and launch", [7, 8, 9])],
}
# The 5-lesson unit for short time (elementary README, "Short on time?").
CORE = {"elementary": {1, 2, 4, 7, 8}, "middle": set()}
# Adult plan-ahead milestones (middle README, "Plan ahead (adult)"), by lesson.
PREP = {"middle": {1: "Order the pad, controller, wadding and motors", 5: "Find a field or a NAR club launch",
                   6: "Start printing (hours per part)", 7: "Assemble with an adult", 8: "Pick a backup launch day"}}


def glance_rows(readme_table: str) -> dict[int, dict[str, str]]:
    """The track README's "Lessons at a glance" table, by lesson number."""
    rows = [r.strip().strip("|").split("|") for r in readme_table.strip().splitlines() if r.startswith("|")]
    head = [h.strip() for h in rows[0]]
    out = {}
    for r in rows[2:]:
        cells = [c.strip() for c in r]
        m = re.search(r"\d+", cells[0])
        if m:
            out[int(m.group(0))] = dict(zip(head, cells))
    return out


def _plain(md_text: str) -> str:
    return html.escape(re.sub(r"[*_]", "", md_text))


def phase_of(track: str, n: int) -> tuple[int, str]:
    for i, (name, nums) in enumerate(PHASES[track]):
        if n in nums:
            return i, name
    raise KeyError(n)


def track_path(track: str, lessons: list[dict], glance: dict[int, dict[str, str]]) -> str:
    """The learning pathway on a track overview: lessons in phases along a dashed flight line,
    each with its icon, big idea and hands-on activity."""
    legs = []
    for pi, (name, nums) in enumerate(PHASES[track]):
        stops = []
        for n in nums:
            d = lessons[n - 1]
            g = glance.get(n, {})
            core = ' <span class="core" title="In the 5-lesson short unit">★</span>' if n in CORE[track] else ""
            prep = PREP.get(track, {}).get(n)
            prep_html = f'<span class="prep">{icon("people", 16)}Adult: {html.escape(prep)}</span>' if prep else ""
            stops.append(
                f'<li><a href="/learn/{track}/{d["slug"]}" title="Lesson {n}: {html.escape(d["title"])}">'
                f'<span class="stop">{n}</span>{icon(ICONS[track][n], 34)}'
                f'<b>{_plain(g.get("Big idea", d["title"]))}{core}</b><small>{_plain(g.get("Hands-on", ""))}</small></a>{prep_html}</li>')
        legs.append(f'<li class="leg p{pi}" style="--k:{len(nums)}"><span class="legname">{html.escape(name)}</span>'
                    f'<ol start="{nums[0]}">{"".join(stops)}</ol></li>')
    key = ""
    if CORE[track]:
        key = '<p class="pathkey"><span class="core">★</span> In the 5-lesson short unit.</p>'
    if PREP.get(track):
        key += f'<p class="pathkey">{icon("people", 16)} Things an adult does ahead of time.</p>'
    return (f'<figure class="pathwrap"><ol class="path {track}" aria-label="Learning pathway">{"".join(legs)}</ol>'
            f'{key}</figure>')


def mini_path(track: str, n: int, lessons: list[dict]) -> str:
    """The "you are here" strip at the top of a lesson page."""
    pi, phase = phase_of(track, n)
    dots = []
    for d in lessons:
        k = d["num"]
        state = ' aria-current="step"' if k == n else ""
        cls = "done" if k < n else ("here" if k == n else "")
        dots.append(f'<li class="{cls} p{phase_of(track, k)[0]}"><a href="/learn/{track}/{d["slug"]}"{state} '
                    f'title="Lesson {k}: {html.escape(d["title"])}"><span>{k}</span></a></li>')
    return (f'<nav class="minipath" aria-label="Where this lesson sits"><ol>{"".join(dots)}</ol>'
            f'<p><span class="phase p{pi}">{html.escape(phase)}</span> Lesson {n} of {len(lessons)}</p></nav>')


def tracks_map() -> str:
    """The /learn chooser's picture of the two tracks side by side."""
    lanes = [
        ("elementary", "Grades 3–5", "/learn/elementary/", [
            ("balloon", "Balloon and straw rockets", "Lessons 1–3"),
            ("balance", "Fins and balance", "Lesson 4"),
            ("stomp", "Design and test a stomp rocket", "Lessons 5–6"),
            ("parachute", "Parachutes", "Lesson 7"),
            ("launch", "Launch day", "Lesson 8"),
        ], "Paper and air only. Rocket Builder on the projector."),
        ("middle", "Grades 6–8", "/learn/middle/", [
            ("newton", "Forces with paper rockets", "Lessons 1–4"),
            ("motor", "Motors and energy", "Lesson 5"),
            ("laptop", "Design in Rocket Builder", "Lesson 6"),
            ("print", "Print and build (12+)", "Lessons 6–8"),
            ("launch", "Adult-run launch and report", "Lesson 9"),
        ], "Real motors, always handled by an adult."),
    ]
    out = ['<figure class="tracksmap" aria-label="The two tracks at a glance">']
    for tr, grades, href, steps, note in lanes:
        items = "".join(f'<li>{icon(ic, 30)}<b>{html.escape(t)}</b><small>{html.escape(s)}</small></li>' for ic, t, s in steps)
        out.append(f'<div class="lane {tr}"><a class="lanehead" href="{href}"><span class="tag big">{grades}</span></a>'
                   f'<ol>{items}</ol><p class="lanenote">{html.escape(note)}</p></div>')
    out.append('<figcaption>Same big ideas, two depths. Mixed ages: run the elementary lessons together and give older '
               'students the middle-school worksheets and the printed rocket.</figcaption></figure>')
    return "".join(out)


# ---------------------------------------------------------------- lesson page pieces
def glance(meta_html: str) -> str:
    """'<strong>Time:</strong> about 45 minutes. <strong>Worksheet:</strong> …' as icon chips."""
    parts = re.split(r"<strong>([^<:]+):</strong>", meta_html)
    if len(parts) < 3:
        return f'<p class="meta">{meta_html}</p>'
    icons = {"time": "clock", "worksheet": "sheet", "worksheets": "sheet", "rocket builder": "laptop"}
    chips = []
    for key, val in zip(parts[1::2], parts[2::2]):
        val = val.strip().removesuffix(".")
        chips.append(f'<li>{icon(icons.get(key.lower(), "star"), 22)}<span><span class="lab">{html.escape(key)}</span>{val}</span></li>')
    return f'<ul class="glance">{"".join(chips)}</ul>'


_KIND = [("learn", r"\b(learn|teach|hook)\b"), ("wrap", r"\bwrap\b"),
         ("plan", r"\b(plan|define|imagine|predict|before you go|choose|safety code)\b")]


def lesson_flow(steps: list[tuple[str, str, str, int | None]]) -> str:
    """A bar of the lesson's steps, as wide as their minutes: (id, number, name, minutes)."""
    timed = [s for s in steps if s[3]]
    if len(timed) < 2 or len(timed) != len(steps):
        return ""
    total = sum(s[3] for s in steps)
    segs = []
    for sid, num, name, mins in steps:
        kind = next((k for k, pat in _KIND if re.search(pat, name, re.I)), "do")
        short = re.sub(r"^(Do|Investigate|Part [AB]):\s*", "", name)
        short = short[0].upper() + short[1:]
        segs.append(f'<li class="{kind}" style="flex:{mins}"><a href="#{sid}"><span class="n">{num}</span>'
                    f'<span class="t">{html.escape(short)}</span><span class="m">{mins} min</span></a></li>')
    return (f'<figure class="flow"><ol aria-label="Lesson steps and minutes">{"".join(segs)}</ol>'
            f'<figcaption>{total} minutes · <span class="k learn">learn</span> <span class="k plan">plan</span> '
            f'<span class="k do">hands-on</span> <span class="k wrap">wrap up</span></figcaption></figure>')


# ---------------------------------------------------------------- standards
STRANDS = [("Forces and motion", "PS2", "f"), ("Energy", "PS3", "e"), ("Engineering design", "ETS1", "g")]


def _strand(code: str) -> str:
    for _, key, cls in STRANDS:
        if key in code:
            return cls
    return "f"


def standards_matrix(track: str, smap_md: str) -> str:
    """The track's standards map as a grid of dots: performance expectations down the side,
    lessons across. A ring means a partial or connection-only match."""
    hits: dict[str, dict[int, bool]] = {}
    nlessons = 0
    for row in smap_md.splitlines():
        m = re.match(r"\|\s*(\d+)\s[^|]*\|([^|]*)\|", row)
        if not m:
            continue
        n = int(m.group(1))
        nlessons = max(nlessons, n)
        for part in m.group(2).split(","):
            cm = re.match(r"\s*((?:MS|\d(?:-\d)?)-[A-Z]+\d-\d)\s*(\(.*\))?", part)
            if cm:
                hits.setdefault(cm.group(1), {})[n] = not cm.group(2)
    order = {"f": 0, "e": 1, "g": 2}
    codes = sorted(hits, key=lambda c: (order[_strand(c)], c))
    head = "".join(f'<th scope="col"><a href="/learn/{track}/lesson-{n:02d}">{n}</a></th>' for n in range(1, nlessons + 1))
    rows = []
    for c in codes:
        cells = []
        for n in range(1, nlessons + 1):
            if n in hits[c]:
                full = hits[c][n]
                cells.append(f'<td><span class="dot {"full" if full else "part"}" title="{c}, Lesson {n}'
                             f'{"" if full else " (partial or connection)"}"></span></td>')
            else:
                cells.append("<td></td>")
        rows.append(f'<tr class="s-{_strand(c)}"><th scope="row">{c}</th>{"".join(cells)}</tr>')
    legend = "".join(f'<span class="s-{cls}"><span class="dot full"></span>{name}</span>' for name, _, cls in STRANDS)
    return (f'<figure class="smatrix"><div class="tbl"><table><thead><tr><th scope="col">Standard</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div><figcaption>Lessons across, standards down. {legend}'
            f'<span><span class="dot part"></span>partial or connection</span></figcaption></figure>')


def progression(standards_md: str) -> str:
    """Teachers page: how the grade 3–5 performance expectations grow into the grade 6–8 ones,
    strand by strand, with the lessons that teach each (from the PE tables in standards.md)."""
    found: dict[str, list[tuple[str, str, str]]] = {"elementary": [], "middle": []}
    for track, title in (("elementary", "### Elementary track"), ("middle", "### Middle-school track")):
        block = standards_md.split(title, 1)[1].split("\n### ", 1)[0]
        for row in block.splitlines():
            m = re.match(r"\|\s*\*\*([^*]+)\*\*\s*\|[^|]*\|([^|]*)\|[^|]*\|([^|]*)\|", row)
            if m:
                found[track].append((m.group(1).strip(), m.group(2).strip(), m.group(3).strip()))

    def chip(track, code, text, lessons):
        nums = re.findall(r"\d+", lessons)
        links = " ".join(f'<a href="/learn/{track}/lesson-{int(k):02d}">{k}</a>' for k in nums)
        note = " (partial)" if "partial" in lessons else (" (connection)" if "connection" in lessons else "")
        return (f'<li class="s-{_strand(code)}" title="{html.escape(text)}"><b>{code}</b>'
                f'<span>Lessons {links}{note}</span></li>')
    rows = []
    for name, key, cls in STRANDS:
        el = "".join(chip("elementary", *x) for x in found["elementary"] if key in x[0])
        ms = "".join(chip("middle", *x) for x in found["middle"] if key in x[0])
        rows.append(f'<div class="strand s-{cls}"><h3>{name}</h3><ul class="el">{el}</ul>'
                    f'<span class="grow" aria-hidden="true">→</span><ul class="ms">{ms}</ul></div>')
    return (f'<figure class="progression"><div class="cols" aria-hidden="true"><span>Grades 3–5</span><span></span><span>Grades 6–8</span></div>'
            f'{"".join(rows)}<figcaption>Each strand starts in the elementary track and grows in the middle-school track. '
            f'Hover a code for its official text; the numbers link to the lessons.</figcaption></figure>')


# ---------------------------------------------------------------- printable unit map
def journey_svg(track: str, titles: dict[int, str], width_in: float = 7.3) -> str:
    """The unit map for the worksheets: the lessons as stops on a flight path, in two rows, with
    a box to tick after each one. Print-safe colours, inline SVG."""
    nums = [n for _, ns in PHASES[track] for n in ns]
    per_row = (len(nums) + 1) // 2
    W, H = 1000, 560
    xs = [90 + i * (820 / (per_row - 1)) for i in range(per_row)]
    pos = {}
    for i, n in enumerate(nums):
        row, col = divmod(i, per_row)
        x = xs[col] if row == 0 else xs[per_row - 1 - col]
        pos[n] = (x, 150 if row == 0 else 410)
    o = [f'<svg class="fig journey" viewBox="0 0 {W} {H}" style="width:{width_in}in" role="img" '
         f'aria-label="Unit map: the lessons in order">']
    # The dashed flight line: along the top row, a U-turn on the right, back along the bottom.
    pts = [pos[n] for n in nums]
    d = f"M{pts[0][0]:.0f} {pts[0][1]}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 == y1:
            d += f" L{x1:.0f} {y1}"
        else:
            d += f" C{x0 + 110:.0f} {y0} {x1 + 110:.0f} {y1} {x1:.0f} {y1}"
    o.append(f'<path d="{d}" fill="none" stroke="{SKY}" stroke-width="4" stroke-dasharray="14 10" stroke-linecap="round"/>')
    phase_fill = ["#DDEAFF", "#FDE6DA", "#DCF3E8", "#FBEFD6"]
    for pi, (name, ns) in enumerate(PHASES[track]):
        for n in ns:
            x, y = pos[n]
            o.append(f'<circle cx="{x:.0f}" cy="{y}" r="44" fill="{phase_fill[pi]}" stroke="{NIGHT}" stroke-width="3"/>')
            body = _ICONS[ICONS[track][n]].format(o=ORANGE, s=SKY, r=RED)
            o.append(f'<g transform="translate({x - 26:.0f} {y - 26}) scale(2.17)" fill="none" stroke="{NIGHT}" stroke-width="1.6" '
                     f'stroke-linecap="round" stroke-linejoin="round">{body}</g>')
            o.append(f'<path d="M{x - 64:.0f} {y - 58} h28 l6 6 v16 l-6 6 h-28 l-6 -6 v-16 z" fill="{ORANGE}"/>'
                     f'<text x="{x - 50:.0f}" y="{y - 38}" text-anchor="middle" font-size="22" font-weight="700" fill="{NIGHT}">{n}</text>')
            words = titles[n].split()
            lines, cur = [], ""
            for w in words:
                if len(cur) + len(w) + 1 > 17 and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            lines.append(cur)
            for k, line in enumerate(lines[:3]):
                o.append(f'<text x="{x:.0f}" y="{y + 70 + k * 22}" text-anchor="middle" font-size="19" font-weight="600" '
                         f'fill="{NIGHT}">{html.escape(line)}</text>')
            o.append(f'<rect x="{x + 30:.0f}" y="{y - 60}" width="26" height="26" rx="4" fill="#fff" stroke="{NIGHT}" stroke-width="2.5"/>')
    # Phase key along the bottom.
    kx = 40
    for pi, (name, ns) in enumerate(PHASES[track]):
        o.append(f'<rect x="{kx}" y="{H - 28}" width="22" height="22" rx="11" fill="{phase_fill[pi]}" stroke="{NIGHT}" stroke-width="2"/>'
                 f'<text x="{kx + 30}" y="{H - 11}" font-size="18" fill="{NIGHT}">{html.escape(name)}</text>')
        kx += 44 + len(name) * 9.5
    o.append("</svg>")
    return "".join(o)
