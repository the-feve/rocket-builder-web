"""The "Order Supplies" page (/ordersupplies): Amazon affiliate links, in a
Rocket Builder section and, when Trebuchet Builder is mounted in this app
(trebuchet_mount.py), a Trebuchet Builder section read from its own list
(treb_supplies.py / treb_gear.json in that repo), so nothing is copied.

The list is server/gear.json (moved here from the fevergeon.com site on
2026-10-14): categories of items, each with an ASIN, a name, a note and an
optional "pick" (shown as "Start here"). Every link carries the Associates
Store ID ("storeId").

Pictures: Amazon only allows its product images when they're fetched live
through its API (the Creators API, which needs 10 qualifying sales in 30
days), so each item shows a drawn picture of its kind. An item can also have
"photo": "/static/gear/<file>.jpg", the owner's own photo of it, which is
shown instead. No prices on the page for the same reason.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path

import brand

GEAR = Path(__file__).resolve().parent / "gear.json"
ASIN = re.compile(r"^[A-Z0-9]{10}$")
DISCLOSURE = "As an Amazon Associate, I earn from qualifying purchases."


def amazon_url(asin: str, store_id: str) -> str:
    return f"https://www.amazon.com/dp/{asin}/" + (f"?tag={store_id}" if store_id else "")


# Line drawings, one per category (64 x 64, currentColor).
_S = 'fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "launch": f'<path {_S} d="M32 6v40M27 22l5-14 5 14v14h-10zM18 58l14-12 14 12M32 46v12M12 58h40"/>',
    "controllers": f'<rect {_S} x="10" y="18" width="30" height="34" rx="4"/><circle {_S} cx="25" cy="30" r="5"/><path {_S} d="M18 44h14M40 30c10 0 8 14 16 14"/>',
    "igniters": f'<path {_S} d="M8 54c10-2 14-12 22-16s14-4 18-12M48 26l6-6"/><circle cx="56" cy="18" r="4" fill="currentColor"/><path {_S} d="M8 58c10-2 16-10 24-14"/>',
    "motors": f'<rect {_S} x="22" y="8" width="20" height="40" rx="2"/><path {_S} d="M22 16h20M26 48l-2 8h16l-2-8M28 26h8M28 32h8"/>',
    "wadding": f'<path {_S} d="M12 22l20-10 20 10-20 10zM12 32l20 10 20-10M12 42l20 10 20-10"/>',
    "parachutes": f'<path {_S} d="M8 28C10 14 54 14 56 28c-6-4-10-4-16 0-4-4-12-4-16 0-6-4-10-4-16 0zM8 28l24 26 24-26M24 28l8 26 8-26"/>',
    "shock-cords": f'<path {_S} d="M8 32c4-12 10-12 12 0s8 12 12 0 8-12 12 0 8 12 12 0"/><circle {_S} cx="8" cy="32" r="3"/><circle {_S} cx="56" cy="32" r="3"/>',
    "filament": f'<circle {_S} cx="32" cy="32" r="22"/><circle {_S} cx="32" cy="32" r="8"/><path {_S} d="M32 10a22 22 0 0 1 22 22M50 46l10 10"/>',
    "glue": f'<path {_S} d="M24 22h16l4 8v24a4 4 0 0 1-4 4H24a4 4 0 0 1-4-4V30zM28 22V12l4-6 4 6v10M26 38h12"/>',
    "paint": f'<rect {_S} x="18" y="20" width="24" height="38" rx="4"/><path {_S} d="M24 20v-6h12v6M30 14V8h8M46 8h2M50 4h2M50 12h2M18 32h24"/>',
    "stencils": f'<circle {_S} cx="28" cy="34" r="18"/><circle {_S} cx="28" cy="34" r="8"/><path {_S} d="M44 26h14v8H46"/>',
    "letters": f'<rect {_S} x="6" y="16" width="52" height="32" rx="3"/><path {_S} d="M14 40l5-16 5 16M16 35h6M30 24v16h5a4 4 0 0 0 0-8h-5 4a4 4 0 0 0 0-8zM52 26a6 6 0 0 0-10 4v4a6 6 0 0 0 10 4"/>',
}
_FALLBACK = f'<rect {_S} x="12" y="16" width="40" height="34" rx="4"/><path {_S} d="M12 26h40M28 16v10"/>'


@lru_cache(maxsize=1)
def gear() -> dict:
    return json.loads(GEAR.read_text())


def _icon(cat_id: str) -> str:
    return f'<svg viewBox="0 0 64 64" aria-hidden="true">{ICONS.get(cat_id, _FALLBACK)}</svg>'


def _items() -> dict:
    """ASIN -> (category id, item)."""
    return {it["asin"]: (c["id"], it) for c in gear()["categories"] for it in c["items"]}


def motor_links() -> dict[str, list[dict]]:
    """Motor designation (e.g. "B4-4") -> affiliate links to packs that contain it,
    single-motor packs first. Items list theirs under "motors" in gear.json."""
    g, out = gear(), {}
    for c in g["categories"]:
        for it in c["items"]:
            for m in it.get("motors", []):
                out.setdefault(m, []).append({"name": it["name"], "url": amazon_url(it["asin"], g.get("storeId", "")),
                                              "size": len(it["motors"])})
    for links in out.values():
        links.sort(key=lambda x: x["size"])
    return out


def parachute_links() -> dict[int, list[dict]]:
    """Parachute diameter in inches -> affiliate links, read from the item
    names (e.g. 'Estes 18" Parachute') in the parachutes category."""
    g, out = gear(), {}
    for c in g["categories"]:
        if "parachute" not in (c.get("id", "") + c.get("title", "")).lower():
            continue
        for it in c["items"]:
            m = re.search(r'(\d+)\s*(?:"|in\b|inch)', it["name"])
            if m:
                out.setdefault(int(m.group(1)), []).append({"name": it["name"], "url": amazon_url(it["asin"], g.get("storeId", ""))})
    return out


def _starter_kit(store: str) -> str:
    kit = gear().get("starterKit")
    if not kit:
        return ""
    items, rows = _items(), []
    for n, k in enumerate(kit["items"], 1):
        cat, it = items[k["asin"]]
        rows.append(f'<li><a href="{escape(amazon_url(k["asin"], store))}" target="_blank" rel="sponsored noopener">'
                    f'<span class="num rb-step">{n}</span><span class="pic">{_icon(cat)}</span>'
                    f'<span class="txt"><strong>{escape(it["name"])}</strong><span class="note">{escape(k["why"])}</span>'
                    f'<span class="cta">View on Amazon ↗</span></span></a></li>')
    return (f'<section class="kit" id="starter-kit"><h3>{escape(kit["title"])}</h3><p>{escape(kit["intro"])}</p>'
            f'<ol class="kitlist">{"".join(rows)}</ol><p class="kitnote">Then browse the full list below for spares, '
            f'bigger parachutes, filament, glue and paint.</p></section>')


def _treb():
    """Trebuchet Builder's supplies module, when it's mounted here (its server/
    is then on sys.path), else None."""
    try:
        import treb_supplies
        return treb_supplies
    except Exception:
        return None


def _card(url: str, pic: str, it: dict, cta: str) -> str:
    return (f'<li><a href="{escape(url)}" target="_blank" rel="sponsored noopener">'
            f'<span class="pic">{pic}</span><span class="txt">'
            + ('<span class="tag rb-tag">Start here</span>' if it.get("pick") else "")
            + f'<strong>{escape(it["name"])}</strong><span class="note">{escape(it["note"])}</span>'
            f'<span class="cta">{cta}</span></span></a></li>')


def _trebuchet_section() -> str:
    """The trebuchet's categories (ids prefixed "t-": both lists have a filament one)."""
    t = _treb()
    if t is None:
        return ""
    g = t.gear()
    store = g.get("storeId", "")
    toc = "".join(f'<a href="#t-{escape(c["id"])}">{escape(c["title"])}</a>' for c in g["categories"])
    secs = []
    for c in g["categories"]:
        cards = "".join(_card(t.amazon_url(it, store), (f'<img src="{escape(it["photo"])}" alt="" loading="lazy">' if it.get("photo")
                              else t._icon(c["id"])), it, f'{"View" if it.get("asin") else "Find"} on Amazon ↗') for it in c["items"])
        secs.append(f'<section id="t-{escape(c["id"])}"><h3><span class="hicon">{t._icon(c["id"])}</span>{escape(c["title"])}</h3>'
                    f'<p>{escape(c["intro"])}</p><ul class="items">{cards}</ul></section>')
    return (f'<section class="builder" id="trebuchet"><h2>Trebuchet Builder</h2><p class="bl">Bearings, bolts, sling cord, '
            f'counterweight fill and things to throw for a desk trebuchet from '
            f'<a href="https://trebuchet.quiverdesignworks.net/">Trebuchet Builder</a>.</p>'
            f'<nav class="toc rb-chips" aria-label="Trebuchet categories">{toc}</nav>{"".join(secs)}</section>')


def page() -> str:
    g = gear()
    store = g.get("storeId", "")
    toc = "".join(f'<a href="#{escape(c["id"])}">{escape(c["title"])}</a>' for c in g["categories"])
    sections = []
    for c in g["categories"]:
        cards = "".join(_card(amazon_url(it["asin"], store), (f'<img src="{escape(it["photo"])}" alt="" loading="lazy">' if it.get("photo")
                                else _icon(c["id"])), it, "View on Amazon ↗") for it in c["items"])
        sections.append(f'<section id="{escape(c["id"])}"><h3><span class="hicon">{_icon(c["id"])}</span>{escape(c["title"])}</h3>'
                        f'<p>{escape(c["intro"])}</p><ul class="items">{cards}</ul></section>')
    treb = _trebuchet_section()
    builders = ('<nav class="builders" aria-label="Builders"><a href="#rocket">Rocket Builder</a><a href="#trebuchet">Trebuchet Builder</a></nav>'
                if treb else "")
    # No Rocket/Trebuchet toggle in the header (owner, 2026-10-18): the section buttons below jump between them.
    return (_PAGE.replace("{{HEAD}}", brand.HEAD).replace("{{HEADER}}", brand.header("Order supplies"))
            .replace("{{BUILDERS}}", builders).replace("{{KIT}}", _starter_kit(store)).replace("{{TOC}}", toc)
            .replace("{{SECTIONS}}", "".join(sections)).replace("{{TREBUCHET}}", treb).replace("{{DISCLOSURE}}", DISCLOSURE))


_PAGE = """<!doctype html>
<html lang="en">
<head>
{{HEAD}}
<title>Order Supplies · Rocket Builder and Trebuchet Builder</title>
<meta name="description" content="Launch pads, motors, igniters, parachutes, filament, glue and paint for 3D-printed model rockets from Rocket Builder.">
<style>
  /* Page styles; the brand (tokens, fonts, header) is in /static/brand.css. */
  html { scroll-behavior:smooth; }
  .rb-main { max-width:1000px; }
  /* Rocket Builder / Trebuchet Builder switch in the header: Night pill for this one. */
  .rb-header nav.apps { display:flex; gap:2px; padding:3px; border-radius:10px; background:var(--card); }
  .rb-header nav.apps a { padding:4px 10px; border-radius:7px; font:600 12.5px/1.3 var(--font-body); color:var(--muted); text-decoration:none; white-space:nowrap; }
  .rb-header nav.apps a:hover { color:var(--ink); }
  .rb-header nav.apps a.cur { background:var(--ink); color:var(--panel); }
  .notice small { display:block; color:var(--muted); margin-top:4px; font-size:.9rem; }
  section { scroll-margin-top:12px; margin-top:30px; }
  h3 { display:flex; align-items:center; gap:10px; font-size:1.25rem; margin:0 0 4px; }
  h3 .hicon svg { width:30px; height:30px; display:block; color:var(--ink); }
  section > p { margin:0 0 12px; color:var(--muted); max-width:70ch; }
  .builders { display:flex; gap:8px; margin:16px 0 0; }
  .builders a { flex:1; max-width:240px; text-align:center; padding:10px 14px; border-radius:10px; border:1.5px solid var(--ink); color:var(--ink);
    font:700 15px/1.2 var(--font-head); text-decoration:none; }
  .builders a:hover { background:var(--ink); color:var(--panel); }
  .builder { margin-top:40px; padding-top:18px; border-top:2px solid var(--ink); }
  .builder > h2 { font-size:clamp(1.4rem, 5vw, 1.75rem); margin:0 0 2px; }
  .builder > .bl { color:var(--muted); margin:0 0 8px; }
  .items { list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%, 300px), 1fr)); gap:12px; }
  .items a { display:grid; grid-template-columns:84px 1fr; gap:14px; align-items:start; height:100%; padding:12px; border:1px solid var(--line);
    border-radius:10px; background:var(--panel); color:var(--ink); text-decoration:none; transition:border-color .15s, transform .15s; }
  .items a:hover { border-color:var(--accent); transform:translateY(-1px); }
  .pic { display:grid; place-items:center; width:84px; height:84px; border-radius:8px; background:var(--card); overflow:hidden; color:var(--ink); }
  .pic svg { width:52px; height:52px; }
  .pic img { width:100%; height:100%; object-fit:cover; }
  .txt { display:flex; flex-direction:column; gap:4px; min-width:0; }
  .txt strong { font:600 1rem/1.3 var(--font-head); }
  .note { color:var(--muted); font-size:.9rem; line-height:1.45; }
  .cta { color:var(--accent); font-size:.88rem; font-weight:600; margin-top:2px; }
  .tag { align-self:flex-start; }
  .kit { margin:22px 0 8px; padding:18px 18px 10px; border:1px solid var(--line); border-radius:12px; background:var(--card); }
  .kit h3 { margin:0 0 2px; }
  .kit > p { margin:0 0 4px; }
  .kitlist { list-style:none; padding:0; margin:12px 0 4px; display:grid; gap:10px; }
  .kitlist a { display:grid; grid-template-columns:28px 64px 1fr; gap:12px; align-items:center; padding:10px; border:1px solid var(--line);
    border-radius:10px; color:var(--ink); text-decoration:none; background:var(--panel); transition:border-color .15s; }
  .kitlist a:hover { border-color:var(--accent); }
  .kitlist .num { width:28px; height:28px; }
  .kitlist .pic { width:64px; height:64px; } .kitlist .pic svg { width:40px; height:40px; }
  .kitnote { color:var(--muted); font-size:.9rem; }
  @media (max-width:480px) { .kitlist a { grid-template-columns:24px 48px 1fr; } .kitlist .num { width:24px; height:24px; font-size:12.5px; }
    .kitlist .pic { width:48px; height:48px; } .kitlist .pic svg { width:32px; height:32px; }
    .items a { grid-template-columns:64px 1fr; } .pic { width:64px; height:64px; } .pic svg { width:40px; height:40px; }
    .rb-header nav.apps { order:3; } }
</style>
</head>
<body>
{{HEADER}}
<main class="rb-main">
  <h1>Order supplies</h1>
  <p class="lede">Everything you need besides the printed parts, for each builder. Items marked <b>Start here</b> are what I'd buy first.</p>
  <div class="notice rb-tip"><b>Ordering through these links supports me and Rocket Builder</b>, at no extra cost to you.
    <small>{{DISCLOSURE}} Links open Amazon, where you'll see the current price. Motors are bought and handled by a grown-up.</small></div>
  {{BUILDERS}}
  <section class="builder" id="rocket"><h2>Rocket Builder</h2>
  <p class="bl">A launch pad, motors, igniters, parachutes, filament, glue and paint for a rocket from Rocket Builder.</p>
  {{KIT}}
  <nav class="toc rb-chips" aria-label="Rocket categories">{{TOC}}</nav>
  {{SECTIONS}}
  </section>
  {{TREBUCHET}}
</main>
<footer class="rb-footer">{{DISCLOSURE}} · <a href="/">Rocket Builder</a> by <a href="https://quiverdesignworks.net">Quiver Design Works</a></footer>
</body>
</html>
"""
