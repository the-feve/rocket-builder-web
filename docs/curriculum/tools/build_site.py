#!/usr/bin/env python3
"""Build the lesson web pages served at /learn from docs/curriculum/.

    pip install markdown            # dev only; the server never imports it
    python3 docs/curriculum/tools/build_site.py          # worksheets HTML + web pages
    python3 docs/curriculum/tools/build_site.py --pdf    # also both worksheets PDFs (Playwright)

Two tracks, each a folder of markdown: elementary/ (grades 3–5) and middle/ (grades 6–8),
with README.md (overview), lesson-NN.md, safety.md, and worksheets.html (built here by
gen_ws.py). Writes server/static/learn/:

    index.html                       the chooser (from ../README.md)
    teachers.html                    standards and sources (from ../standards.md)
    <track>/index.html               the track overview
    <track>/lesson-NN.html, safety.html, worksheets.html (+ worksheets.pdf with --pdf)

learn.css there is hand-written and not touched. server/app.py serves these at /learn/,
/learn/teachers, /learn/<track>/ and /learn/<track>/<page>; keep its LEARN_TRACKS in step
with TRACKS below.

--pdf runs tools/worksheets_pdf.js with node; it needs the playwright package on
NODE_PATH and a Chromium in PLAYWRIGHT_BROWSERS_PATH.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CUR = HERE.parent                                   # docs/curriculum
ROOT = CUR.parent.parent                            # repo root
OUT = ROOT / "server" / "static" / "learn"
APP = "https://rocket.quiverdesignworks.net/"

TRACKS = {
    "elementary": {"grades": "Grades 3–5", "short": "Elementary", "lessons": 8,
                   "blurb": "Paper, straw and stomp rockets; Rocket Builder on the class projector."},
    "middle": {"grades": "Grades 6–8", "short": "Middle school", "lessons": 9,
               "blurb": "Paper rockets, then a 3D-printed rocket on a real motor, launched by an adult."},
}

# The Rocket Builder mark (docs/brand/logo/rb-mark-light.svg), ink follows the theme.
MARK = ('<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><defs><mask id="rb-learn-cut" '
        'maskUnits="userSpaceOnUse" x="-40" y="-40" width="80" height="80"><rect x="-40" y="-40" width="80" '
        'height="80" fill="#fff"/><path d="M-13 6L0 -9L13 6V11L0 -4L-13 11ZM-13 17L0 2L13 17V22L0 7L-13 22Z" '
        'fill="none" stroke="#000" stroke-width="2.6" stroke-linejoin="round"/><path d="M-8 -16H8" stroke="#000" '
        'stroke-width="1.6"/></mask></defs><g transform="translate(32 32) scale(1.23) translate(.35 -.35) rotate(45)">'
        '<path d="M0 -34C4.2 -29.6 6 -23.5 6 -16V12L3.5 16H-3.5L-6 12V-16C-6 -23.5 -4.2 -29.6 0 -34Z" '
        'fill="currentColor" mask="url(#rb-learn-cut)"/><path d="M-13 6L0 -9L13 6V11L0 -4L-13 11ZM-13 17L0 2L13 17V22L0 7L-13 22Z" '
        'fill="#F2652B"/></g></svg>')


# ---------------------------------------------------------------- markdown
def md_fix(text: str, track: str | None) -> str:
    """Rewrite the repo links in the markdown for the web pages."""
    base = f"/learn/{track}" if track else "/learn"
    text = re.sub(r"\]\((?:\.\./)?standards\.md\)", "](/learn/teachers)", text)
    text = re.sub(r"\]\(\.\./(elementary|middle)/(lesson-\d\d|safety)\.md\)", r"](/learn/\1/\2)", text)
    text = re.sub(r"\]\((elementary|middle)/(lesson-\d\d|safety)\.md\)", r"](/learn/\1/\2)", text)
    text = re.sub(r"\]\((elementary|middle)/README\.md\)", r"](/learn/\1/)", text)
    text = re.sub(r"\]\((lesson-\d\d|safety)\.md(#[\w-]+)?\)", lambda m: f"]({base}/{m.group(1)}{m.group(2) or ''})", text)
    text = re.sub(r"\]\(README\.md(#[\w-]+)?\)", lambda m: f"]({base}/{m.group(1) or ''})", text)
    text = re.sub(r"\]\(worksheets\.html\)", f"]({base}/worksheets)", text)
    # Bare app URLs, nar.org and apogeerockets.com addresses become links.
    text = re.sub(r"(?<!\]\()(?<!<)https://rocket\.quiverdesignworks\.net/?(?![\w/])",
                  f"[rocket.quiverdesignworks.net]({APP})", text)
    text = re.sub(r"(?<![\w./\[(])nar\.org\b", "[nar.org](https://www.nar.org/)", text)

    def apogee(m):
        url = m.group(0).rstrip(".")
        return f"[{url}](https://www.{url})" + m.group(0)[len(url):]
    text = re.sub(r"(?<![\w./\[(])apogeerockets\.com/[^\s),]+", apogee, text)
    return text


def md(text: str, track: str | None = None) -> str:
    return markdown.markdown(md_fix(text, track), extensions=["tables", "sane_lists", "toc"],
                             extension_configs={"toc": {"permalink": False}})


def link_app_mentions(body: str) -> str:
    """Link the first "Rocket Builder" in each h2 section to the app, unless the section
    already links to it. Never inside a heading or an existing link."""
    parts = re.split(r"(?=<h2\b)", body)
    out = []
    for part in parts:
        if APP in part:
            out.append(part)
            continue
        pieces = re.split(r"(<[^>]+>)", part)
        for pat in (r"Rocket Builder", r"\bthe app\b"):
            done = False
            depth_a = depth_h = 0
            for i, p in enumerate(pieces):
                if p.startswith("<"):
                    t = re.match(r"</?(\w+)", p)
                    name = t.group(1).lower() if t else ""
                    closing = p.startswith("</")
                    if name == "a":
                        depth_a += -1 if closing else 1
                    elif name in ("h1", "h2", "h3", "h4", "summary", "th"):
                        depth_h += -1 if closing else 1
                    continue
                if depth_a == 0 and depth_h == 0 and re.search(pat, p):
                    pieces[i] = re.sub(pat, lambda m: f'<a class="app" href="{APP}">{m.group(0)}</a>', p, count=1)
                    done = True
                    break
            if done:
                break
        out.append("".join(pieces))
    return "".join(out)


def polish(body: str) -> str:
    """Callouts, the answer key, the read-aloud box, the teacher-notes box and scrollable tables."""
    def call(kind, label):
        def f(m):
            return f'<div class="call {kind}"><span class="lab">{label}</span><p>{m.group(1)}</p></div>'
        return f
    body = re.sub(r"<p><strong>Safety:</strong>\s*(.*?)</p>", call("safety", "Safety"), body, flags=re.S)
    body = re.sub(r"<p><strong>Tips?:</strong>\s*(.*?)</p>", call("tip", "Tip"), body, flags=re.S)
    body = re.sub(r"<p><strong>Answer key</strong></p>\s*(<ol>.*?</ol>)",
                  r'<details class="answers"><summary>Answer key</summary>\1</details>', body, flags=re.S)
    body = body.replace("<blockquote>", '<blockquote class="aloud"><span class="lab">Read aloud</span>')
    body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    # The standards box at the top of a lesson, and the teacher notes at the end.
    body = re.sub(r'(<h2 id="standards">.*?)(?=<h2\b)', r'<section class="stdbox">\1</section>', body, count=1, flags=re.S)
    body = re.sub(r'(<h2 id="teacher-notes">.*?)(?=<h2\b|\Z)', r'<section class="call notes">\1</section>', body, count=1, flags=re.S)
    body = re.sub(r'(<h2 id="launch-day-rules">.*?)(?=<h2\b|\Z)', r'<section class="call safety rules">\1</section>', body, flags=re.S)
    return link_app_mentions(body)


# ---------------------------------------------------------------- page shell
def page(title: str, desc: str, main: str, current: str = "") -> str:
    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FFFDF8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12203A" media="(prefers-color-scheme: dark)">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="/static/brand/rb-favicon.svg" type="image/svg+xml">
<link rel="icon" href="/static/brand/rb-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/static/brand/rb-apple-touch-icon-180.png">
<link rel="preload" href="/static/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/static/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/static/learn/learn.css">
<script>try {{ const t = localStorage.getItem('theme'); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; }} catch {{}}</script>
</head>
<body>
<!-- Generated by docs/curriculum/tools/build_site.py from docs/curriculum/: edit those, then rebuild. -->
<a class="skip" href="#main">Skip to the lesson</a>
<header class="site">
  <a class="brand" href="/learn/" title="Rockets and Model Rocketry: free lessons">{MARK}<span>Rocket Builder <small>Learn</small></span></a>
  <nav aria-label="Lessons">{nav('/learn/elementary/', 'Grades 3–5', 'elementary')}{nav('/learn/middle/', 'Grades 6–8', 'middle')}{nav('/learn/teachers', 'Teachers', 'teachers')}</nav>
  <a class="btn launch" href="{APP}"><span class="long">Open Rocket Builder</span><span class="short">Open the app</span></a>
  <button id="theme" type="button">Dark mode</button>
</header>
<main id="main">
{main}
</main>
<footer class="site">
  <p><b>Rockets and Model Rocketry</b> is a set of free lessons from <a href="{APP}">Rocket Builder</a> by
  <a href="https://quiverdesignworks.net/">Quiver Design Works</a>, built on Washington's K–12 Science Learning Standards. Free to use in classrooms, co-ops and at home.</p>
  <p><a href="/learn/">All lessons</a> · <a href="/learn/elementary/">Grades 3–5</a> · <a href="/learn/middle/">Grades 6–8</a> · <a href="/learn/teachers">Standards and sources</a> · <a href="/sources">App sources</a></p>
  <p class="fine">Model rocket motors and Rocket Builder kits are rated 12+. Adults handle all motors and igniters.</p>
</footer>
<script>
(() => {{
  const btn = document.getElementById('theme'), root = document.documentElement, mq = matchMedia('(prefers-color-scheme: dark)');
  const light = () => (root.dataset.theme || (mq.matches ? 'dark' : 'light')) === 'light';
  const show = () => {{ btn.textContent = light() ? 'Dark mode' : 'Light mode'; }};
  btn.onclick = () => {{ const n = light() ? 'dark' : 'light'; root.dataset.theme = n; try {{ localStorage.setItem('theme', n); }} catch {{}} show(); }};
  mq.addEventListener?.('change', show); show();
  // Printing a lesson prints its answer key too.
  addEventListener('beforeprint', () => document.querySelectorAll('details').forEach(d => {{ d.dataset.was = d.open; d.open = true; }}));
  addEventListener('afterprint', () => document.querySelectorAll('details').forEach(d => {{ d.open = d.dataset.was === 'true'; }}));
}})();
</script>
</body>
</html>
"""


def sections(path: Path) -> tuple[str, dict[str, str]]:
    """The text before the first h2, and each h2 section's body by heading."""
    text = path.read_text(encoding="utf-8")
    head, *chunks = re.split(r"\n(?=## )", text)
    secs = {}
    for chunk in chunks:
        h, _, body = chunk.partition("\n")
        secs[h[3:].strip()] = body.strip()
    return head, secs


# ---------------------------------------------------------------- lessons
def read_lesson(track: str, n: int) -> dict:
    slug = f"lesson-{n:02d}"
    text = (CUR / track / f"{slug}.md").read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    m = re.match(r"# Lesson (\d+): (.*)", first)
    assert m and int(m.group(1)) == n, f"{track}/{slug}.md must start with '# Lesson {n}: …'"
    meta, _, body = rest.strip().partition("\n\n")
    codes = re.findall(r"^\| \*\*([^*]+)\*\*", body.split("## I can", 1)[0], flags=re.M)
    return {"track": track, "slug": slug, "num": n, "title": m.group(2).strip(), "meta": meta, "body": body,
            "codes": [c for c in codes if "(" not in c and not re.match(r"\d\.|[A-Z]{2,4}\.", c)]}


def lesson_page(d: dict, prev: dict | None, nxt: dict | None) -> str:
    tr, cfg = d["track"], TRACKS[d["track"]]
    meta = md(d["meta"], tr).removeprefix("<p>").removesuffix("</p>")
    body = polish(md(d["body"], tr))
    toc = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body))

    def card(x, rel, label):
        if not x:
            return f'<a class="pn {rel}" href="/learn/{tr}/"><span class="lab">{label}</span>Back to the overview</a>'
        return (f'<a class="pn {rel}" href="/learn/{tr}/{x["slug"]}" rel="{rel}"><span class="lab">{label}</span>'
                f'<span class="tag">Lesson {x["num"]}</span> {html.escape(x["title"])}</a>')

    main = f"""<article class="lesson {tr}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/learn/">Rockets and Model Rocketry</a> <span aria-hidden="true">›</span> <a href="/learn/{tr}/">{cfg['grades']}</a> <span aria-hidden="true">›</span> Lesson {d['num']} of {cfg['lessons']}</nav>
<p class="daytag"><span class="tag big">Lesson {d['num']}</span> <span class="tag grade">{cfg['grades']}</span></p>
<h1>{html.escape(d['title'])}</h1>
<p class="meta">{meta}</p>
<p class="tools"><a class="btn ink" href="/learn/{tr}/worksheets.pdf">Worksheets (PDF)</a> <a class="btn outline" href="{APP}">Open Rocket Builder</a> <button class="btn outline" type="button" onclick="print()">Print this lesson</button></p>
<details class="toc"><summary>On this page</summary><ol>{toc}</ol></details>
{body}
</article>
<nav class="prevnext" aria-label="Lessons">{card(prev, 'prev', '← Previous')}{card(nxt, 'next', 'Next →')}</nav>
<p class="back"><a href="/learn/{tr}/">← Back to the {cfg['grades'].lower()} overview</a></p>"""
    return page(f"Lesson {d['num']}: {d['title']} · {cfg['grades']} · Rocket Builder Learn",
                f"{cfg['short']} rocketry lesson {d['num']} of {cfg['lessons']} ({cfg['grades'].lower()}): {d['title']}. "
                f"Standards: {', '.join(d['codes'])}.", main)


# ---------------------------------------------------------------- track overview
def track_page(tr: str, lessons: list[dict]) -> str:
    cfg = TRACKS[tr]
    head, s = sections(CUR / tr / "README.md")
    intro = head.split("\n", 1)[1].strip()          # drop the h1
    glance = s["Lessons at a glance"]
    glance = re.sub(r"^\| (\d+) \|", lambda m: f"| [{m.group(1)}](/learn/{tr}/lesson-{int(m.group(1)):02d}) |", glance, flags=re.M)
    smap = re.sub(r"^\| (\d+) ([^|]+)\|", lambda m: f"| [{m.group(1)} {m.group(2).strip()}](/learn/{tr}/lesson-{int(m.group(1)):02d}) |",
                  s["Standards map"], flags=re.M)
    cards = "".join(
        f'<li><a href="/learn/{tr}/{d["slug"]}"><span class="tag">Lesson {d["num"]}</span>'
        f'<b>{html.escape(d["title"])}</b><span class="hands">{html.escape(", ".join(d["codes"]))}</span></a></li>'
        for d in lessons)
    rest = "".join(f'<section id="{re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-")}"><h2>{k}</h2>{polish(md(v, tr))}</section>'
                   for k, v in s.items() if k not in ("Lessons at a glance", "Standards map"))
    ws_pages = "14 pages" if tr == "elementary" else "21 pages"
    main = f"""<div class="hero">
  <p class="eyebrow">Free lessons · {cfg['grades']} · {cfg['lessons']} lessons · Washington science standards</p>
  <h1>Rockets: {cfg['short'].lower()} track</h1>
  {polish(md(intro, tr))}
  <div class="ctas">
    <a class="btn print" href="/learn/{tr}/worksheets.pdf" download="rocketry-worksheets-{tr}.pdf">Print the worksheets (PDF)<small>{ws_pages}, US Letter, answer key at the end</small></a>
    <a class="btn outline big" href="/learn/{tr}/lesson-01">Start with Lesson 1 →</a>
    <a class="btn outline big" href="/learn/{tr}/safety">Safety page</a>
  </div>
</div>
<section id="lessons"><h2>The {cfg['lessons']} lessons</h2>
<ol class="days">{cards}</ol>
{polish(md(glance, tr))}
</section>
<section id="standards-map"><h2>Standards map</h2>{polish(md(smap, tr))}</section>
{rest}"""
    return page(f"Rockets for {cfg['grades'].lower()}: free lessons · Rocket Builder",
                f"Free rocketry lessons for {cfg['grades'].lower()}, mapped to Washington's K–12 Science Learning Standards (NGSS). "
                + cfg["blurb"], main, tr)


def safety_page(tr: str) -> str:
    cfg = TRACKS[tr]
    text = (CUR / tr / "safety.md").read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    main = f"""<article class="lesson">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/learn/">Rockets and Model Rocketry</a> <span aria-hidden="true">›</span> <a href="/learn/{tr}/">{cfg['grades']}</a> <span aria-hidden="true">›</span> Safety</nav>
<p class="daytag"><span class="tag big red">Safety</span> <span class="tag grade">{cfg['grades']}</span></p>
<h1>{html.escape(first.lstrip('# ').strip())}</h1>
{polish(md(rest, tr))}
</article>
<p class="back"><a href="/learn/{tr}/">← Back to the {cfg['grades'].lower()} overview</a></p>"""
    desc = ("Paper-rocket safety rules for grades 3–5." if tr == "elementary" else
            "Safety for grades 6–8: classroom rules, the NAR Model Rocket Safety Code in plain words, launch field sizes and launch day rules.")
    return page(f"Safety · {cfg['grades']} · Rocket Builder Learn", desc, main, tr)


def teachers_page() -> str:
    text = (CUR / "standards.md").read_text(encoding="utf-8")
    first, _, rest = text.partition("\n")
    main = f"""<article class="lesson">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/learn/">Rockets and Model Rocketry</a> <span aria-hidden="true">›</span> For parents and teachers</nav>
<p class="daytag"><span class="tag big">Teachers</span></p>
<h1>{html.escape(first.lstrip('# ').strip())}</h1>
{polish(md(rest))}
</article>
<p class="back"><a href="/learn/">← Back to the lessons</a></p>"""
    return page("Washington standards and sources · Rocket Builder Learn",
                "How the free rocketry lessons line up with Washington's K–12 Science Learning Standards (NGSS), "
                "WA Science 2026, and the math and ELA standards, with sources and further resources.", main, "teachers")


def index_page() -> str:
    head, s = sections(CUR / "README.md")
    pick = s["Pick a track"]
    table, _, after = pick.partition("\n\n")
    cards = "".join(f"""<a class="chooser {tr}" href="/learn/{tr}/"><span class="tag big">{cfg['grades']}</span>
<b>{cfg['short']}</b><span>{cfg['lessons']} lessons. {cfg['blurb']}</span><span class="go">Open the {cfg['short'].lower()} lessons →</span></a>"""
                    for tr, cfg in TRACKS.items())
    main = f"""<div class="hero">
  <p class="eyebrow">Free lessons · Grades 3–8 · Washington science standards</p>
  <h1>Rockets and Model Rocketry</h1>
  <p class="lead">Free rocket science lessons in two versions: one for elementary school and one for middle school.
  Each lesson lists its Washington K–12 Science Learning Standards (NGSS), "I can…" goals, materials, steps, a quick check
  with answers and teacher notes, with printable worksheets.</p>
</div>
<nav class="choose" aria-label="Pick a track">{cards}
<a class="chooser teachers" href="/learn/teachers"><span class="tag big">Parents &amp; teachers</span><b>Standards and sources</b>
<span>The Washington standards behind each lesson, the new WA Science 2026 codes, math and ELA links, and free resources.</span><span class="go">Read the standards page →</span></a></nav>
<section id="compare"><h2>Which track?</h2>{polish(md(table + "\n\n" + after)).replace('<blockquote class="aloud"><span class="lab">Read aloud</span>', '<blockquote class="call safety"><span class="lab">Safety first</span>')}</section>
<section id="rocket-builder" class="rb"><h2>Use it with Rocket Builder</h2>
<p><a href="{APP}">Rocket Builder</a> is the free web app these lessons use. It runs in the browser on a computer or tablet, with no account or install.</p>
<div class="two">
  <div class="card"><span class="tag">Grades 3–5</span><h3>A class tool on the projector</h3>
  <p>Build a rocket, point at the blue balance point and the red push point, and press <b>▶ Watch it launch</b>. On screen only.</p></div>
  <div class="card"><span class="tag">Grades 6–8</span><h3>Design, print and fly (12+)</h3>
  <p>Beginner mode first, then Advanced. Download and 3D-print the rocket (or order it printed) and fly it with an adult handling the motor.</p></div>
</div>
<p><a class="btn launch" href="{APP}">Open Rocket Builder</a></p>
</section>"""
    return page("Rockets and Model Rocketry: free lessons for grades 3–8 · Rocket Builder",
                "Free rocketry lessons for grades 3–5 and 6–8, mapped to Washington's K–12 Science Learning Standards (NGSS): "
                "paper rockets for elementary, 3D-printed model rockets with an adult for middle school.", main, "index")


# ---------------------------------------------------------------- worksheets
FONT_FACE = ('<style>@font-face{font-family:"Inter";src:url(/static/fonts/inter.woff2) format("woff2");font-weight:100 900;font-display:swap}'
             '@font-face{font-family:"Space Grotesk";src:url(/static/fonts/space-grotesk.woff2) format("woff2");font-weight:300 700;font-display:swap}'
             '.wsbar{font:500 14px/1.3 Inter,system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;'
             'justify-content:center;padding:10px 16px;background:#12203A;color:#F6F1E7}'
             '.wsbar a{color:#F6F1E7}.wsbar a.dl{background:#F2652B;color:#12203A;font-weight:600;text-decoration:none;padding:6px 12px;border-radius:8px}'
             '@media print{.wsbar{display:none}}</style>')


def worksheets_page(tr: str) -> str:
    src = (CUR / tr / "worksheets.html").read_text(encoding="utf-8")
    src = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", src)
    src = re.sub(r'<link href="https://fonts\.googleapis\.com[^>]*>\s*', "", src)
    src = re.sub(r'<link rel="stylesheet" href="\.\./\.\./brand/tokens\.css">', FONT_FACE, src)
    assert not re.search(r'(href|src)="(https?:|\.\./)', src), "worksheets.html links something new: update build_site.py"
    bar = (f'<div class="wsbar"><a href="/learn/{tr}/">← {TRACKS[tr]["grades"]} lessons</a><span>Print at 100% with background graphics on.</span>'
           f'<a class="dl" href="/learn/{tr}/worksheets.pdf">Download the PDF</a></div>')
    src = re.sub(r"<body([^>]*)>", lambda m: f"<body{m.group(1)}>\n<!-- Generated by docs/curriculum/tools/build_site.py from docs/curriculum/{tr}/worksheets.html. -->\n" + bar, src, count=1)
    return src


def main():
    for tr in TRACKS:     # the worksheets first: gen_ws.py writes docs/curriculum/<track>/worksheets.html
        subprocess.run([sys.executable, str(HERE / "gen_ws.py"), tr, str(CUR / tr / "worksheets.html")], check=True)
    files = {"index.html": index_page(), "teachers.html": teachers_page()}
    for tr, cfg in TRACKS.items():
        lessons = [read_lesson(tr, n) for n in range(1, cfg["lessons"] + 1)]
        files[f"{tr}/index.html"] = track_page(tr, lessons)
        files[f"{tr}/safety.html"] = safety_page(tr)
        files[f"{tr}/worksheets.html"] = worksheets_page(tr)
        for i, d in enumerate(lessons):
            files[f"{tr}/{d['slug']}.html"] = lesson_page(d, lessons[i - 1] if i else None, lessons[i + 1] if i + 1 < len(lessons) else None)
    for name, text in files.items():
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_text(text, encoding="utf-8")
        print("wrote", (OUT / name).relative_to(ROOT))
    if "--pdf" in sys.argv:
        for tr in TRACKS:
            pdf = OUT / tr / "worksheets.pdf"
            subprocess.run(["node", str(HERE / "worksheets_pdf.js"), str(OUT / tr / "worksheets.html"),
                            str(ROOT / "server" / "static"), str(pdf)], check=True, env=os.environ)
            print("wrote", pdf.relative_to(ROOT))


if __name__ == "__main__":
    main()
