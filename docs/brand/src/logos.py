"""Write the Rocket Builder logo SVGs into docs/brand/logo/.

The mark is hand-specified below (local coordinates, rocket upright, then rotated 45 deg
so it flies up-right like the Quiver arrow). Text is converted to paths from Space Grotesk.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from textpath import text_path  # noqa: E402  (src/textpath.py)

HERE = os.path.dirname(os.path.abspath(__file__))
# Space Grotesk TTFs from Google Fonts (OFL), downloaded next to this script; needs `pip install fonttools`.
SG700 = os.path.join(HERE, 'fonts/sg700.ttf')
SG500 = os.path.join(HERE, 'fonts/sg500.ttf')
OUT = os.path.join(HERE, '..', 'logo')

NIGHT, PAPER, ORANGE, GREY = '#12203A', '#F6F1E7', '#F2652B', '#6E6E73'
MIST = '#A9B4C8'   # Night 40% tint on Night: secondary text in dark variants

# --- the mark, upright, origin near the middle --------------------------------------
# Body: ogive nose, straight tube, chamfered tail (the chamfer nods to Quiver's lettering).
BODY = ('M0 -34C4.2 -29.6 6 -23.5 6 -16V12L3.5 16H-3.5L-6 12V-16C-6 -23.5 -4.2 -29.6 0 -34Z')
# Fins as fletching: two nested chevrons, like the feathers on the Quiver arrow.
CHEV = ('M-13 6L0 -9L13 6V11L0 -4L-13 11Z'
        'M-13 17L0 2L13 17V22L0 7L-13 22Z')
# Favicon: same idea, fewer and fatter parts so it holds at 16 px.
FAV_BODY = 'M0 -34C5.4 -29 8 -23 8 -15V2H-8V-15C-8 -23 -5.4 -29 0 -34Z'
FAV_CHEV = 'M-15 6L0 -9L15 6V15.5L0 0.5L-15 15.5Z'
FAV_PTS = [(0, -34), (8, -15), (-8, -15), (15, 6), (-15, 6), (15, 15.5), (-15, 15.5)]

PTS = [(0, -34), (6, -16), (-6, -16), (13, 6), (-13, 6), (13, 22), (-13, 22), (0, -9), (3.5, 16), (-3.5, 16)]


def bbox(pts, ang=45):
    a = math.radians(ang)
    r = [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in pts]
    xs, ys = [p[0] for p in r], [p[1] for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def mark_group(uid, body_fill, chev_fill, cx, cy, scale, gap=1.3, body=BODY, chev=CHEV, seam=True, pts=PTS):
    """Return (defs, group) for the mark centred at (cx, cy)."""
    x0, y0, x1, y1 = bbox(pts)
    ox, oy = -(x0 + x1) / 2, -(y0 + y1) / 2
    seam_line = '<path d="M-8 -16H8" stroke="#000" stroke-width="1.6"/>' if seam else ''
    defs = (f'<mask id="{uid}" maskUnits="userSpaceOnUse" x="-40" y="-40" width="80" height="80">'
            f'<rect x="-40" y="-40" width="80" height="80" fill="#fff"/>'
            f'<path d="{chev}" fill="none" stroke="#000" stroke-width="{gap * 2}" stroke-linejoin="round"/>'
            f'{seam_line}</mask>')
    g = (f'<g transform="translate({cx:.2f} {cy:.2f}) scale({scale:g}) translate({ox:.2f} {oy:.2f}) rotate(45)">'
         f'<path d="{body}" fill="{body_fill}" mask="url(#{uid})"/>'
         f'<path d="{chev}" fill="{chev_fill}"/></g>')
    return defs, g


def svg(w, h, title, defs, body, extra=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}"'
            f' role="img" aria-labelledby="t"{extra}>\n<title id="t">{title}</title>\n'
            f'<defs>{defs}</defs>\n{body}\n</svg>\n')


def mark_size():
    x0, y0, x1, y1 = bbox(PTS)
    return x1 - x0, y1 - y0


def write(name, text):
    with open(os.path.join(OUT, name), 'w') as f:
        f.write(text)
    print('wrote', name)


def main():
    os.makedirs(OUT, exist_ok=True)
    mw, mh = mark_size()
    # 1. primary mark, 64 x 64
    s = 60 / max(mw, mh)
    variants = {
        'light': dict(body=NIGHT, chev=ORANGE, ink=NIGHT, sub=GREY),
        'dark': dict(body=PAPER, chev=ORANGE, ink=PAPER, sub=MIST),
        'mono': dict(body='currentColor', chev='currentColor', ink='currentColor', sub='currentColor'),
    }
    for v, c in variants.items():
        extra = ' color="#12203A"' if v == 'mono' else ''
        d, g = mark_group(f'rb-cut-mark-{v}', c['body'], c['chev'], 32, 32, s)
        write(f'rb-mark-{v}.svg', svg(64, 64, 'Rocket Builder', d, g, extra))

    # 2. horizontal lockup
    H = 64
    title, tw = text_path(SG700, 'Rocket Builder', 34, 0, 0, tracking=-10)
    for v, c in variants.items():
        extra = ' color="#12203A"' if v == 'mono' else ''
        d, g = mark_group(f'rb-cut-h-{v}', c['body'], c['chev'], 32, 32, s)
        tx = 76
        t1, w1 = text_path(SG700, 'Rocket Builder', 34, tx, 35, tracking=-10)
        t2, w2 = text_path(SG500, 'BY QUIVER DESIGN WORKS', 10.2, tx + 1, 53, tracking=150)
        W = tx + max(w1, w2) + 4
        body = (g + f'\n<path fill="{c["ink"]}" d="{t1}"/>\n<path fill="{c["sub"]}" d="{t2}"/>')
        write(f'rb-lockup-horizontal-{v}.svg', svg(round(W), H, 'Rocket Builder by Quiver Design Works', d, body, extra))

    # 3. stacked lockup
    for v, c in variants.items():
        extra = ' color="#12203A"' if v == 'mono' else ''
        _, w1 = text_path(SG700, 'Rocket Builder', 30, 0, 0, tracking=-10)
        _, w2 = text_path(SG500, 'BY QUIVER DESIGN WORKS', 9.6, 0, 0, tracking=150)
        W = round(max(w1, w2) + 8)
        cx = W / 2
        d, g = mark_group(f'rb-cut-s-{v}', c['body'], c['chev'], cx, 38, 72 / max(mw, mh))
        t1, _ = text_path(SG700, 'Rocket Builder', 30, cx - w1 / 2, 110, tracking=-10)
        t2, _ = text_path(SG500, 'BY QUIVER DESIGN WORKS', 9.6, cx - w2 / 2, 128, tracking=150)
        body = g + f'\n<path fill="{c["ink"]}" d="{t1}"/>\n<path fill="{c["sub"]}" d="{t2}"/>'
        write(f'rb-lockup-stacked-{v}.svg', svg(W, 136, 'Rocket Builder by Quiver Design Works', d, body, extra))

    # 4. favicon: Night tile, Paper rocket, orange fletching, no text, no seam
    for v, tile, bodyc in (('', NIGHT, PAPER), ('-light', PAPER, NIGHT)):
        fx0, fy0, fx1, fy1 = bbox(FAV_PTS)
        d, g = mark_group(f'rb-fav{v or "-dark"}', bodyc, ORANGE, 16, 16, 25 / max(fx1 - fx0, fy1 - fy0), gap=1.6,
                          body=FAV_BODY, chev=FAV_CHEV, seam=False, pts=FAV_PTS)
        body = f'<rect width="32" height="32" rx="7" fill="{tile}"/>\n' + g
        write(f'rb-favicon{v}.svg', svg(32, 32, 'Rocket Builder', d, body))


if __name__ == '__main__':
    main()
