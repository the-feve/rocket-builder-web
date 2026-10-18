"""Shared page chrome for the server-rendered secondary pages (/ordersupplies,
/terms): the <head> links (fonts, favicons, static/brand.css, the saved theme)
and the branded header. The static pages (sources.html, admin.html) carry the
same markup by hand; keep them in step if this changes.
"""

from __future__ import annotations

from html import escape

# The Rocket Builder mark (same drawing as the app header), Night body in currentColor
# and Launch-orange fletching. {mid} keeps the mask id unique if two are on a page.
MARK = ('<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><defs><mask id="{mid}" maskUnits="userSpaceOnUse" '
        'x="-40" y="-40" width="80" height="80"><rect x="-40" y="-40" width="80" height="80" fill="#fff"/>'
        '<path d="M-13 6L0 -9L13 6V11L0 -4L-13 11ZM-13 17L0 2L13 17V22L0 7L-13 22Z" fill="none" stroke="#000" '
        'stroke-width="2.6" stroke-linejoin="round"/><path d="M-8 -16H8" stroke="#000" stroke-width="1.6"/></mask></defs>'
        '<g transform="translate(32 32) scale(1.23) translate(.35 -.35) rotate(45)"><path d="M0 -34C4.2 -29.6 6 -23.5 6 '
        '-16V12L3.5 16H-3.5L-6 12V-16C-6 -23.5 -4.2 -29.6 0 -34Z" fill="currentColor" mask="url(#{mid})"/>'
        '<path d="M-13 6L0 -9L13 6V11L0 -4L-13 11ZM-13 17L0 2L13 17V22L0 7L-13 22Z" fill="#F2652B"/></g></svg>')

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FFFDF8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12203A" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/static/brand/rb-favicon.svg" type="image/svg+xml">
<link rel="icon" href="/static/brand/rb-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/static/brand/rb-apple-touch-icon-180.png">
<link rel="preload" href="/static/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/static/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/static/brand.css">
<script>try { const t = localStorage.getItem('theme'); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; } catch {}</script>"""


def header(page: str, nav: str = "") -> str:
    """The branded header: the mark and "Rocket Builder" over the page name (links
    home), optional extra nav, then the links back to Rocket Builder and Quiver."""
    return (f'<header class="rb-header"><a class="rb-brand" href="/" title="Rocket Builder: start page">'
            f'{MARK.replace("{mid}", "rb-hdr-cut")}<span>Rocket Builder<small>{escape(page)}</small></span></a>{nav}'
            f'<nav class="rb-nav" aria-label="Site"><a href="/">← Back to Rocket Builder</a>'
            f'<a class="long" href="https://quiverdesignworks.net/">Quiver Design Works</a></nav></header>')
