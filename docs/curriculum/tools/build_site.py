#!/usr/bin/env python3
"""Build the curriculum web pages served at /learn from docs/curriculum/*.md.

    pip install markdown            # dev only; the server never imports it
    python3 docs/curriculum/tools/build_site.py          # HTML pages
    python3 docs/curriculum/tools/build_site.py --pdf    # also worksheets.pdf (Playwright)

Writes server/static/learn/: index.html, safety.html, day-01.html … day-10.html,
worksheets.html (a copy of ../worksheets.html with self-hosted fonts) and, with --pdf,
worksheets.pdf. learn.css there is hand-written and not touched. server/app.py serves
them at /learn/, /learn/safety, /learn/day-01 … and /learn/worksheets(.pdf).

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
DAYS = [f"day-{n:02d}" for n in range(1, 11)]

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
def md_fix(text: str) -> str:
    """Rewrite the repo links in the markdown for the web pages."""
    text = text.replace("`worksheets.html`", "[the worksheets](/learn/worksheets)")
    text = re.sub(r"\]\(README\.md#safety\)", "](/learn/safety)", text)
    text = re.sub(r"\]\(#safety\)", "](/learn/safety)", text)
    text = re.sub(r"\]\(README\.md(#[\w-]+)?\)", lambda m: f"](/learn/{m.group(1) or ''})", text)
    text = re.sub(r"\]\((day-\d\d)\.md(#[\w-]+)?\)", lambda m: f"](/learn/{m.group(1)}{m.group(2) or ''})", text)
    # Bare app URLs and nar.org become links.
    text = re.sub(r"(?<!\]\()(?<!<)https://rocket\.quiverdesignworks\.net/?",
                  f"[rocket.quiverdesignworks.net]({APP})", text)
    text = re.sub(r"(?<![\w./])nar\.org\b", "[nar.org](https://www.nar.org/)", text)
    return text


def md(text: str) -> str:
    return markdown.markdown(md_fix(text), extensions=["tables", "sane_lists", "toc"],
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
        # "Rocket Builder" first; a section that only says "the app" links that.
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
                    elif name in ("h1", "h2", "h3", "h4", "summary"):
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
    """Callouts, the answer key, the read-aloud box and scrollable tables."""
    def call(kind, label):
        def f(m):
            return f'<div class="call {kind}"><span class="lab">{label}</span><p>{m.group(1)}</p></div>'
        return f
    body = re.sub(r"<p><strong>Safety:</strong>\s*(.*?)</p>", call("safety", "Safety"), body, flags=re.S)
    body = re.sub(r"<p><strong>Tips?:</strong>\s*(.*?)</p>", call("tip", "Tip"), body, flags=re.S)
    body = re.sub(r"<p><strong>What to expect:</strong>\s*(.*?)</p>", call("tip", "What to expect"), body, flags=re.S)
    body = re.sub(r"<p><strong>Answer key</strong></p>\s*(<ol>.*?</ol>)",
                  r'<details class="answers"><summary>Answer key</summary>\1</details>', body, flags=re.S)
    body = body.replace("<blockquote>", '<blockquote class="aloud"><span class="lab">Read aloud</span>', )
    body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<p><strong>(Paper track \(under 12\)[^<]*)</strong>", r'<p class="trk trk-paper"><strong>\1</strong>', body)
    body = re.sub(r"<p><strong>(Printed-rocket track \(12\+\)[^<]*)</strong>", r'<p class="trk trk-print"><strong>\1</strong>', body)
    # "Launch day rules" is a safety section: frame it.
    body = re.sub(r'(<h2 id="launch-day-rules">.*?)(?=<h2\b)',
                  r'<section class="call safety rules">\1</section>', body, flags=re.S)
    body = body.replace("★", '<span class="star" title="Keep this one in the 1-week version">★</span>')
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
<!-- Generated by docs/curriculum/tools/build_site.py from docs/curriculum/*.md: edit those, then rebuild. -->
<a class="skip" href="#main">Skip to the lesson</a>
<header class="site">
  <a class="brand" href="/learn/" title="Rockets and Model Rocketry: the home-school unit">{MARK}<span>Rocket Builder <small>Learn</small></span></a>
  <nav aria-label="Unit">{nav('/learn/', 'Lessons', 'index')}{nav('/learn/worksheets.pdf', 'Worksheets', 'ws')}{nav('/learn/safety', 'Safety', 'safety')}</nav>
  <a class="btn launch" href="{APP}"><span class="long">Open Rocket Builder</span><span class="short">Open the app</span></a>
  <button id="theme" type="button">Dark mode</button>
</header>
<main id="main">
{main}
</main>
<footer class="site">
  <p><b>Rockets and Model Rocketry</b> is a free home-school unit from <a href="{APP}">Rocket Builder</a> by
  <a href="https://quiverdesignworks.net/">Quiver Design Works</a>. Free to use at home, in co-ops and in classrooms.</p>
  <p><a href="/learn/">All lessons</a> · <a href="/learn/worksheets.pdf">Worksheets (PDF)</a> · <a href="/learn/worksheets">Worksheets (web page)</a> · <a href="/learn/safety">Safety</a> · <a href="/sources">Sources</a></p>
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


# ---------------------------------------------------------------- days
def read_day(slug: str) -> dict:
    text = (CUR / f"{slug}.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    m = re.match(r"# Day (\d+): (.*)", lines[0])
    num, title = int(m.group(1)), m.group(2).strip()
    rest = "\n".join(l for l in lines[1:] if not l.startswith("[← ") and not l.startswith("[Day "))
    # The first paragraph is the time / worksheet line.
    meta, _, body = rest.strip().partition("\n\n")
    return {"slug": slug, "num": num, "title": title, "meta": meta, "body": body}


def day_page(d: dict, prev: dict | None, nxt: dict | None) -> str:
    meta = md(d["meta"]).removeprefix("<p>").removesuffix("</p>")
    body = polish(md(d["body"]))
    body = body.replace('<h2 id="worksheet">Worksheet</h2>',
                        '<h2 id="worksheet">Worksheet</h2>\n<p class="small">In the <a href="/learn/worksheets.pdf">worksheets PDF</a> '
                        '(or <a href="/learn/worksheets">as a web page</a>). Print at 100%.</p>', 1)
    toc = "".join(f'<li><a href="#{i}">{t}</a></li>'
                  for i, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body))

    def card(x, rel, label):
        if not x:
            return f'<a class="pn {rel}" href="/learn/"><span class="lab">{label}</span>Back to the overview</a>'
        return (f'<a class="pn {rel}" href="/learn/{x["slug"]}" rel="{rel}"><span class="lab">{label}</span>'
                f'<span class="tag">Day {x["num"]}</span> {html.escape(x["title"])}</a>')

    main = f"""<article class="lesson">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/learn/">Rockets and Model Rocketry</a> <span aria-hidden="true">›</span> Day {d['num']} of 10</nav>
<p class="daytag"><span class="tag big">Day {d['num']}</span></p>
<h1>{html.escape(d['title'])}</h1>
<p class="meta">{meta}</p>
<p class="tools"><a class="btn ink" href="/learn/worksheets.pdf">Worksheets (PDF)</a> <a class="btn outline" href="{APP}">Open Rocket Builder</a> <button class="btn outline" type="button" onclick="print()">Print this lesson</button></p>
<details class="toc"><summary>On this page</summary><ol>{toc}</ol></details>
{body}
</article>
<nav class="prevnext" aria-label="Lessons">{card(prev, 'prev', '← Previous')}{card(nxt, 'next', 'Next →')}</nav>
<p class="back"><a href="/learn/">← Back to the overview and schedule</a></p>"""
    return page(f"Day {d['num']}: {d['title']} · Rocket Builder Learn",
                f"Day {d['num']} of a free 2-week home-school rocketry unit (grades 3–8): {d['title']}.", main)


# ---------------------------------------------------------------- overview
def readme_sections() -> dict[str, str]:
    text = (CUR / "README.md").read_text(encoding="utf-8")
    secs = {}
    for chunk in re.split(r"\n(?=## )", text)[1:]:
        head, _, body = chunk.partition("\n")
        secs[head[3:].strip()] = body.strip()
    return secs


def index_page(days: list[dict]) -> str:
    s = readme_sections()
    sched = s["Schedule at a glance"]
    table, _, rest = sched.partition("\n### ")
    table = re.sub(r"^\| (\d+) \|", lambda m: f"| [Day {m.group(1)}](/learn/day-{int(m.group(1)):02d}) |",
                   table, flags=re.M)
    sched = table + ("\n### " + rest if rest else "")
    safety = s["Safety"]
    big_rules = safety.split("### The big rules", 1)[1].split("\n### ", 1)[0]

    hands = {}
    main_table = s["Schedule at a glance"].split("\n### ", 1)[0]   # not the 1-week table
    for row in re.findall(r"^\| (\d+) \| [^|]* \| ([^|]*) \|", main_table, flags=re.M):
        hands[int(row[0])] = row[1].strip()
    cards = "".join(
        f'<li><a href="/learn/{d["slug"]}"><span class="tag">Day {d["num"]}</span>'
        f'<b>{html.escape(d["title"])}</b><span class="hands">{md(hands.get(d["num"], ""))[3:-4]}</span></a></li>'
        for d in days)

    sec = lambda key, sid=None, title=None: (
        f'<section id="{sid or re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")}"><h2>{title or key}</h2>'
        f'{polish(md(s[key]))}</section>')

    main = f"""<div class="hero">
  <p class="eyebrow">Free home-school unit · Grades 3–8 · 10 days</p>
  <h1>Rockets and Model Rocketry</h1>
  <p class="lead">A free two-week rocket science unit for grades 3–8. Each day has a short lesson to read aloud,
  hands-on activities, a worksheet, discussion questions and a quick check with answers. It ends with a launch day
  and a mission report.</p>
  <ul class="tracks">
    <li><b>Under 12:</b> paper, straw, balloon and stomp rockets, and Rocket Builder on screen only.</li>
    <li><b>12 and up:</b> all of that, plus a 3D-printed rocket on a real model rocket motor, <b>with an adult handling the motor</b>.</li>
  </ul>
  <div class="ctas">
    <a class="btn print" href="/learn/worksheets.pdf" download="rocketry-worksheets.pdf">Print the worksheets (PDF)<small>22 pages, US Letter, answer keys at the end</small></a>
    <a class="btn outline big" href="/learn/day-01">Start with Day 1 →</a>
  </div>
  <p class="small">You need no account and nothing to install. Most materials are already in your house; see the
  <a href="#materials-and-costs-by-track">materials list</a>. Prefer a web page? <a href="/learn/worksheets">Open the worksheets in the browser</a>.</p>
</div>

<div class="call safety"><span class="lab">Safety first</span><p>Model rocket motors and Rocket Builder kits are
rated <b>12+</b>. Kids under 12 do the whole unit with paper-style rockets. In the 12+ track, <b>adults handle all
rocket motors and igniters</b>, every time, following the NAR Model Rocket Safety Code.
<a href="/learn/safety">Read the safety page</a> before Day 1 and again before Day 10.</p></div>

<section id="days"><h2>The ten lessons</h2>
<ol class="days">{cards}</ol>
<p class="small">★ in a lesson marks the activity to keep if you do the <a href="#short-on-time-a-1-week-version">1-week version</a>.</p>
</section>

<section id="rocket-builder" class="rb"><h2>Use it with Rocket Builder</h2>
<p><a href="{APP}">Rocket Builder</a> is the free web app this unit is built around. It runs in the browser on a computer or tablet.</p>
<div class="two">
  <div class="card"><span class="tag">All ages</span><h3>Design on screen</h3>
  <p>Pick a motor size, the height, the fins and the nose. Read the stability score and find the blue balance point and the red push point. Then press <b>▶ Watch it launch</b> to see the simulated flight: liftoff, coast, parachute and landing.</p></div>
  <div class="card"><span class="tag">12+ with an adult</span><h3>Print it and fly it</h3>
  <p>Download the files and 3D-print the rocket (or order it printed), build it, and fly it on a real model rocket motor on Day 10. An adult buys, loads and launches every motor. Compare the flight with the app's prediction.</p></div>
</div>
<p><a class="btn launch" href="{APP}">Open Rocket Builder</a></p>
</section>

{sec("Pick a track by age")}
<section id="schedule-at-a-glance"><h2>Schedule at a glance</h2>{polish(md(sched))}</section>
{sec("How each day works")}
{sec("Materials and costs by track")}
<section id="safety"><h2>Safety</h2>
<div class="call safety rules"><span class="lab">The big rules</span>{md(big_rules)}</div>
<p>The <a href="/learn/safety">safety page</a> has the rules for each kind of rocket, a plain summary of the NAR Model
Rocket Safety Code and the minimum launch field for each motor class. Day 10 has the <a href="/learn/day-10#launch-day-rules">launch day rules</a>.</p>
</section>
<section id="standards-alignment"><h2>Standards alignment</h2>
<details class="std"><summary>NGSS, Common Core math and literacy: where each standard is covered</summary>{polish(md(s["Standards alignment"]))}</details>
</section>
{sec("A note on the numbers")}"""
    return page("Rockets and Model Rocketry: a free home-school unit · Rocket Builder",
                "A free 2-week rocket science unit for grades 3–8: ten lessons, printable worksheets and answer keys. "
                "Paper rockets for under 12; 3D-printed model rockets for 12+ with an adult.", main, "index")


def safety_page() -> str:
    s = readme_sections()["Safety"].replace("### ", "## ", 1)
    s = re.sub(r"^### ", "## ", s, flags=re.M)
    main = f"""<article class="lesson">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/learn/">Rockets and Model Rocketry</a> <span aria-hidden="true">›</span> Safety</nav>
<p class="daytag"><span class="tag big red">Safety</span></p>
<h1>Safety for the rocketry unit</h1>
{polish(md(s))}
<p class="tools"><a class="btn outline" href="/learn/day-10#launch-day-rules">Launch day rules (Day 10)</a> <a class="btn outline" href="/learn/day-09">Day 9: safety and launch prep</a></p>
</article>
<p class="back"><a href="/learn/">← Back to the overview and schedule</a></p>"""
    return page("Safety · Rockets and Model Rocketry · Rocket Builder",
                "Safety rules for the free home-school rocketry unit: paper rockets, fizzy rockets and the NAR Model Rocket Safety Code for 12+.",
                main, "safety")


# ---------------------------------------------------------------- worksheets
FONT_FACE = ('<style>@font-face{font-family:"Inter";src:url(/static/fonts/inter.woff2) format("woff2");font-weight:100 900;font-display:swap}'
             '@font-face{font-family:"Space Grotesk";src:url(/static/fonts/space-grotesk.woff2) format("woff2");font-weight:300 700;font-display:swap}'
             '.wsbar{font:500 14px/1.3 Inter,system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;'
             'justify-content:center;padding:10px 16px;background:#12203A;color:#F6F1E7}'
             '.wsbar a{color:#F6F1E7}.wsbar a.dl{background:#F2652B;color:#12203A;font-weight:600;text-decoration:none;padding:6px 12px;border-radius:8px}'
             '@media print{.wsbar{display:none}}</style>')


def worksheets_page() -> str:
    src = (CUR / "worksheets.html").read_text(encoding="utf-8")
    src = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", src)
    src = re.sub(r'<link href="https://fonts\.googleapis\.com[^>]*>\s*', "", src)
    src = re.sub(r'<link rel="stylesheet" href="\.\./brand/tokens\.css">', FONT_FACE, src)
    assert not re.search(r'(href|src)="(https?:|\.\./)', src), "worksheets.html links something new: update build_site.py"
    bar = ('<div class="wsbar"><a href="/learn/">← Lessons</a><span>Print at 100% with background graphics on.</span>'
           '<a class="dl" href="/learn/worksheets.pdf">Download the PDF</a></div>')
    src = src.replace("<body>", "<body>\n<!-- Generated by docs/curriculum/tools/build_site.py from docs/curriculum/worksheets.html. -->\n" + bar, 1)
    return src


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    days = [read_day(s) for s in DAYS]
    files = {"index.html": index_page(days), "safety.html": safety_page(), "worksheets.html": worksheets_page()}
    for i, d in enumerate(days):
        files[f"{d['slug']}.html"] = day_page(d, days[i - 1] if i else None, days[i + 1] if i + 1 < len(days) else None)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
        print("wrote", (OUT / name).relative_to(ROOT))
    if "--pdf" in sys.argv:
        pdf = OUT / "worksheets.pdf"
        subprocess.run(["node", str(HERE / "worksheets_pdf.js"), str(OUT / "worksheets.html"),
                        str(ROOT / "server" / "static"), str(pdf)], check=True, env=os.environ)
        print("wrote", pdf.relative_to(ROOT))


if __name__ == "__main__":
    main()
