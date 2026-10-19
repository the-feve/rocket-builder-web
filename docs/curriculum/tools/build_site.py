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
    <track>/lesson-NN.html, safety.html, worksheets.html (+ worksheets.pdf and teacher-guide.pdf with --pdf,
                                     also copied to docs/curriculum/<track>/)

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
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagrams  # noqa: E402  (tools/diagrams.py: the labelled line drawings)

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
    out = markdown.markdown(md_fix(text, track), extensions=["tables", "sane_lists", "toc"],
                            extension_configs={"toc": {"permalink": False}})
    # <!-- figure: name --> in the markdown becomes the drawing from diagrams.py.
    out = re.sub(r"<!-- figure: ([\w-]+) -->", lambda m: diagrams.figure(m.group(1)), out)
    # "### 1. Hook (5 minutes)" gets a numbered step badge.
    return re.sub(r'<h3 id="([^"]+)">(\d+)\. (.*?)</h3>', r'<h3 id="\1" class="step"><span class="n">\2</span> \3</h3>', out)


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
    <a class="btn print" href="/learn/{tr}/teacher-guide.pdf" download="rocketry-teacher-guide-{tr}.pdf">Teacher guide (PDF)<small>every lesson, the standards map and safety, ready to print</small></a>
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


# ---------------------------------------------------------------- teacher guides (PDF)
FLETCH = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='24' viewBox='0 0 40 48'%3E"
          "%3Cpath d='M1 4L17 24L1 44H10L26 24L10 4Z' fill='%23F2652B'/%3E%3Cpath d='M15 4L31 24L15 44H24L40 24L24 4Z' fill='%2312203A'/%3E%3C/svg%3E\")")

GUIDE_CSS = r"""
@font-face{font-family:"Inter";src:url(/static/fonts/inter.woff2) format("woff2");font-weight:100 900}
@font-face{font-family:"Space Grotesk";src:url(/static/fonts/space-grotesk.woff2) format("woff2");font-weight:300 700}
:root{--night:#12203A;--paper:#F6F1E7;--white:#FFFDF8;--orange:#F2652B;--sky:#3D8BFD;--red:#E5484D;--green:#2FB67C;--grey:#5E5E63;
 --line:#D9CFBA;--card:#F3EEE3;--sky-100:#E6EFFE;--red-100:#FCE6E6;--green-100:#E3F4EA;--amber-100:#FBF1DC;
 --chamfer:polygon(5px 0,calc(100% - 5px) 0,100% 5px,100% calc(100% - 5px),calc(100% - 5px) 100%,5px 100%,0 calc(100% - 5px),0 5px)}
@page{size:Letter;margin:.6in .62in .7in;
 @bottom-left{content:"Rocket Builder · Rockets & Model Rocketry · TRACKLINE";font:500 7.5pt Inter,sans-serif;color:#5E5E63}
 @bottom-right{content:"Page " counter(page);font:600 7.5pt "Space Grotesk",sans-serif;color:#5E5E63}}
@page cover{margin:0;@bottom-left{content:none}@bottom-right{content:none}}
*{box-sizing:border-box}
html,body{margin:0;background:#fff;color:var(--night)}
body{font:9.6pt/1.45 Inter,system-ui,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
h1,h2,h3,h4,.kicker,.sec{font-family:"Space Grotesk",Inter,sans-serif;letter-spacing:-.01em;line-height:1.15}
h2{font-size:13pt;margin:14pt 0 5pt;padding-bottom:3pt;border-bottom:1.5px solid var(--night);break-after:avoid}
h3{font-size:11pt;margin:10pt 0 4pt;break-after:avoid}
p{margin:0 0 5pt}ul,ol{margin:0 0 6pt;padding-left:1.25em}li{margin:0 0 2pt}
b,strong{font-weight:650}
a{color:inherit;text-decoration:none}
table{border-collapse:collapse;width:100%;font-size:8.6pt;margin:3pt 0 8pt;break-inside:auto}
th,td{text-align:left;vertical-align:top;padding:3pt 5pt;border-bottom:1px solid var(--line)}
th{font:700 7.4pt/1.2 "Space Grotesk",sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--grey);border-bottom:1.5px solid var(--night)}
tr{break-inside:avoid}
/* Cover */
.cover{page:cover;width:8.5in;height:11in;position:relative;overflow:hidden;background:var(--white);display:flex;flex-direction:column}
.cover .band{margin:0;padding:.42in .62in .34in;display:flex;align-items:center;gap:12pt}
.cover .band svg{width:46pt;height:46pt;color:var(--paper)}
.cover .band .lock b{display:block;font:700 21pt/1 "Space Grotesk",sans-serif;color:var(--paper)}
.cover .band .lock small{font:600 7.5pt/1 "Space Grotesk",sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#A9B4C8}
.cover .inner{padding:.45in .62in 0;flex:1;display:flex;flex-direction:column}
.cover .kicker{font:700 10pt/1 "Space Grotesk",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#B8471B}
.cover h1{font-size:40pt;margin:10pt 0 6pt;line-height:1.02}
.cover .sub{font-size:13pt;max-width:5.8in;margin-bottom:12pt}
.cover svg.arc{width:100%;height:1.6in;margin:4pt 0 10pt}
.cover .chips{display:flex;flex-wrap:wrap;gap:5pt;margin:4pt 0 12pt}
.cover .chips span{font:700 8.5pt/1 "Space Grotesk",sans-serif;border:1.5px solid var(--night);padding:4pt 6pt;border-radius:3px}
.cover .inside{display:grid;grid-template-columns:1fr 1fr;gap:2pt 20pt;font-size:9pt;padding-left:1.1em;margin-top:4pt}
.cover .toc{columns:2;column-gap:20pt;font-size:9.4pt;padding:0;list-style:none}
.cover .toc li{break-inside:avoid;margin:0 0 4pt;display:flex;gap:6pt}
.cover .toc .tag{min-width:20pt}
.cover .foot{margin-top:auto;padding:12pt .62in .35in;font-size:8pt;color:var(--grey);border-top:1px solid var(--line)}
.cover .warn{margin-top:8pt}
/* Header band for each part and lesson */
.band{background:var(--night);color:var(--paper);display:flex;align-items:center;gap:10pt;padding:9pt 12pt;margin:0 0 0;border-radius:4px 4px 0 0}
.band svg{width:24pt;height:24pt;color:var(--paper);flex:none}
.band .t{flex:1}
.band .t small{display:block;font:600 7pt/1 "Space Grotesk",sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#A9B4C8;margin-bottom:3pt}
.band .t h1{font-size:17pt;margin:0;color:var(--paper)}
.band .badge{font:700 11pt/1 "Space Grotesk",sans-serif;background:var(--orange);color:var(--night);padding:6pt 9pt;clip-path:var(--chamfer)}
.fletch{height:12px;background:FLETCH repeat-x left center/12px 14px;margin:0 0 10pt}
.part,.lesson{break-before:page}
.meta{font-size:9pt;background:var(--card);border:1px solid var(--line);border-radius:4px;padding:5pt 8pt;margin-bottom:8pt}
/* Steps, callouts, boxes */
h3.step{display:flex;align-items:center;gap:7pt}
h3.step .n{display:inline-grid;place-items:center;width:19pt;height:19pt;background:var(--orange);color:var(--night);font:700 11pt/1 "Space Grotesk",sans-serif;clip-path:var(--chamfer);flex:none}
.tag{display:inline-grid;place-items:center;height:15pt;padding:0 4pt;background:var(--night);color:var(--paper);font:700 8.5pt/1 "Space Grotesk",sans-serif;clip-path:var(--chamfer)}
.stdbox{border:1.5px solid var(--night);border-radius:4px;padding:2pt 8pt 4pt;margin:0 0 8pt;break-inside:avoid}
.stdbox h2{border:0;margin:4pt 0 2pt;font-size:10.5pt;text-transform:uppercase;letter-spacing:.08em}
.stdbox td:first-child{white-space:nowrap;font-weight:650}
.call{border-left:4px solid;padding:5pt 9pt 3pt;border-radius:0 4px 4px 0;margin:4pt 0 8pt;break-inside:avoid}
.call .lab,blockquote .lab{display:block;font:700 7.2pt/1 "Space Grotesk",sans-serif;letter-spacing:.12em;text-transform:uppercase;margin-bottom:3pt}
.call.safety{background:var(--red-100);border-color:var(--red)}.call.safety .lab{color:#C22E33}
.call.tip{background:var(--sky-100);border-color:var(--sky)}.call.tip .lab{color:#1D5BC4}
section.call.notes{background:var(--sky-100);border-color:var(--night);border-left-width:5px;padding-top:2pt;break-inside:auto}
section.call.notes h2{border:0;margin:4pt 0 3pt;font-size:10.5pt;text-transform:uppercase;letter-spacing:.08em}
section.call.rules h2{border:0;margin:4pt 0}
blockquote{margin:3pt 0 8pt;padding:6pt 10pt 2pt;border:1px solid var(--line);border-left:4px solid var(--orange);border-radius:0 4px 4px 0;background:var(--white);font-size:9.8pt;break-inside:avoid}
blockquote .lab{color:#B8471B}
.answers{border:1.5px dashed var(--night);border-radius:4px;padding:3pt 9pt 1pt;margin:2pt 0 8pt;break-inside:avoid}
.answers .lab{display:block;font:700 7.2pt/1 "Space Grotesk",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);margin:3pt 0}
figure.dg{margin:4pt 0 9pt;break-inside:avoid;text-align:center}
figure.dg svg{width:100%;max-width:6.9in;height:auto;display:block;margin:0 auto}
figure.dg figcaption{font-size:8pt;color:var(--grey);text-align:left;margin-top:2pt}
.endnote{margin-top:14pt}
"""


def guide_html(tr: str) -> str:
    """One printable teacher guide: cover, how to use, standards, safety and every lesson."""
    cfg = TRACKS[tr]
    head, s = sections(CUR / tr / "README.md")
    intro = head.split("\n", 1)[1].strip()
    lessons = [read_lesson(tr, n) for n in range(1, cfg["lessons"] + 1)]

    def g(body: str) -> str:
        """polish() for print: answer keys stay open, no app links."""
        body = polish(md(body, tr))
        body = re.sub(r'<details class="answers"><summary>Answer key</summary>(.*?)</details>',
                      r'<div class="answers"><span class="lab">Answer key</span>\1</div>', body, flags=re.S)
        body = body.replace('<div class="tbl">', "<div>")
        return re.sub(r'<a class="app" href="[^"]*">(.*?)</a>', r"\1", body)

    def band(kicker, title, badge=""):
        b = f'<span class="badge">{badge}</span>' if badge else ""
        return (f'<div class="band">{MARK}<div class="t"><small>{kicker}</small><h1>{html.escape(title)}</h1></div>{b}</div>'
                f'<div class="fletch"></div>')

    std = (CUR / "standards.md").read_text(encoding="utf-8")
    key = "### Elementary track (grades 3–5)" if tr == "elementary" else "### Middle-school track (grades 6–8)"
    pe_table = std.split(key, 1)[1].split("\n### ", 1)[0]
    codes = sorted({c for d in lessons for c in d["codes"]}, key=lambda c: (not c[0].isdigit(), c))
    toc = "".join(f'<li><span class="tag">{d["num"]}</span>{html.escape(d["title"])}</li>' for d in lessons)
    use_secs = [k for k in s if k not in ("Standards map",)]
    how = "".join(f"<h2>{k}</h2>{g(s[k])}" for k in use_secs)
    cover = f"""<section class="cover">
<div class="band">{MARK}<div class="lock"><b>Rocket Builder</b><small>by Quiver Design Works</small></div></div>
<div class="fletch" style="margin:0"></div>
<div class="inner">
<p class="kicker">Teacher guide · {cfg['grades']} · {cfg['lessons']} lessons</p>
<h1>Rockets &amp; Model Rocketry</h1>
<p class="sub">{html.escape(cfg['short'])} track. Lesson plans built on the Washington State K–12 Science Learning Standards (NGSS), with standards, "I can…" goals, materials, steps, checks with answers and teacher notes.</p>
<svg class="arc" viewBox="0 0 700 150" aria-hidden="true"><path d="M20 140 Q300 -60 680 120" fill="none" stroke="#12203A" stroke-width="3" stroke-dasharray="10 8"/>
<g transform="translate(250 50) rotate(-6)"><path d="M150 -9 C170 -9 186 -4 196 0 C186 4 170 9 150 9 Z" fill="#F2652B"/><rect x="40" y="-9" width="110" height="18" fill="#12203A"/><path d="M62 -9 L40 -30 L28 -30 L40 -9 Z M62 9 L40 30 L28 30 L40 9 Z" fill="#3D8BFD"/></g></svg>
<div class="chips">{''.join(f'<span>{c}</span>' for c in codes)}</div>
<h2>The lessons</h2>
<ol class="toc">{toc}</ol>
<h2>Inside this guide</h2>
<ul class="inside"><li>How to use this guide: lessons at a glance, materials, Rocket Builder</li><li>Standards map and the full standards text</li>
<li>Safety rules{' for paper rockets' if tr == 'elementary' else ' and the NAR code'}</li><li>{cfg['lessons']} lesson plans with diagrams, answer keys and teacher notes</li></ul>
<div class="call safety warn"><span class="lab">Safety</span><p>{'Paper and air rockets only for students. Model rocket motors and kits are rated 12+ and only adults handle them.' if tr == 'elementary' else 'Model rocket motors and kits are rated 12+. Adults handle all motors and igniters, every time, under the NAR Model Rocket Safety Code.'}</p></div>
</div>
<div class="foot">Free lessons from Rocket Builder by Quiver Design Works · rocket.quiverdesignworks.net/learn/{tr} · Worksheets: a separate PDF at the same address. Free to copy for classrooms, co-ops and home school.</div>
</section>"""
    parts = [cover,
             f'<section class="part">{band("Teacher guide · " + cfg["grades"], "How to use this guide")}{g(intro)}{how}</section>',
             f'<section class="part">{band("Teacher guide · " + cfg["grades"], "Standards")}<h2>Standards map</h2>{g(s["Standards map"])}'
             f'<h2>The performance expectations, in full</h2>{g(pe_table)}'
             f'<p>Sources, the new WA Science 2026 codes and the math and ELA crosswalks: rocket.quiverdesignworks.net/learn/teachers.</p></section>']
    sf = (CUR / tr / "safety.md").read_text(encoding="utf-8").split("\n", 1)[1]
    parts.append(f'<section class="part">{band("Teacher guide · " + cfg["grades"], "Safety")}{g(sf)}</section>')
    for d in lessons:
        meta = md(d["meta"], tr).removeprefix("<p>").removesuffix("</p>")
        parts.append(f'<section class="lesson">{band("Lesson " + str(d["num"]) + " of " + str(cfg["lessons"]) + " · " + cfg["grades"], d["title"], "Lesson " + str(d["num"]))}'
                     f'<p class="meta">{meta}</p>{g(d["body"])}</section>')
    css = (GUIDE_CSS.replace("TRACKLINE", f"Teacher guide, {cfg['grades'].lower()}").replace("FLETCH", FLETCH) + diagrams.DG_CSS)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Rockets and Model Rocketry: teacher guide, {cfg['grades'].lower()}</title>
<style>{css}</style></head>
<body>
<!-- Generated by docs/curriculum/tools/build_site.py from docs/curriculum/{tr}/*.md. -->
{''.join(parts)}
</body></html>
"""


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


def sync_diagram_css():
    """Copy diagrams.DG_CSS into learn.css between its DIAGRAMS markers (the rest is hand-written)."""
    css_path = OUT / "learn.css"
    css = css_path.read_text(encoding="utf-8")
    start, end = "/* DIAGRAMS: from docs/curriculum/tools/diagrams.py (build_site.py rewrites this block) */", "/* END DIAGRAMS */"
    block = f"{start}\n{diagrams.DG_CSS.strip()}\n{end}"
    if start in css:
        css = css[:css.index(start)] + block + css[css.index(end) + len(end):]
    else:
        css = css.rstrip() + "\n\n" + block + "\n"
    css_path.write_text(css, encoding="utf-8")


def main():
    for tr in TRACKS:     # the worksheets first: gen_ws.py writes docs/curriculum/<track>/worksheets.html
        subprocess.run([sys.executable, str(HERE / "gen_ws.py"), tr, str(CUR / tr / "worksheets.html")], check=True)
        (CUR / tr / "teacher-guide.html").write_text(guide_html(tr), encoding="utf-8")
        print("wrote", (CUR / tr / "teacher-guide.html").relative_to(ROOT))
    sync_diagram_css()
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
        # Both PDFs per track go to server/static/learn/<track>/ (served) and docs/curriculum/<track>/ (next to the source).
        for tr in TRACKS:
            for src, name in ((OUT / tr / "worksheets.html", "worksheets.pdf"), (CUR / tr / "teacher-guide.html", "teacher-guide.pdf")):
                pdf = OUT / tr / name
                subprocess.run(["node", str(HERE / "worksheets_pdf.js"), str(src), str(ROOT / "server" / "static"), str(pdf)],
                               check=True, env=os.environ)
                shutil.copyfile(pdf, CUR / tr / name)
                print("wrote", pdf.relative_to(ROOT), "and", (CUR / tr / name).relative_to(ROOT))


if __name__ == "__main__":
    main()
