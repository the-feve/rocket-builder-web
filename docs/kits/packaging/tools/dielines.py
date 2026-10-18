"""Dielines for the Rocket Builder kit packaging (docs/kits/packaging/).

    python docs/kits/packaging/tools/dielines.py

Writes three SVGs next to the artwork, each the size of the sheet it prints on,
so the artwork HTML can lay the dieline over itself (?dieline=1) and a print
shop can use it as the cutting guide:

  tuck-box-starter-dieline.svg  reverse tuck-end box, 2.5 x 2.5 x 8.75 in inside,
                                on an 11 x 17 in sheet (Starter kit, 18 mm)
  header-card-dieline.svg       two 4 x 7 in fold-over header cards (4 x 3.5 in
                                folded) on a US Letter sheet (Mini kit, 13 mm bag)
  tube-wrap-big-dieline.svg     wrap label for a 4 x 12 in kraft mailing tube,
                                on an 11 x 17 in sheet turned sideways (Big kit, 24 mm)

All sizes are inches. Line key (the usual print-shop colours):
  cut   solid magenta     fold  dashed cyan      bleed  dotted green (1/8 in)
  safe  dotted grey (keep text inside)           labels in grey

Box sizes come from the generator's parts for the kit designs (README "Kit
designs"): the Starter's fin can is 53 x 61 x 205 mm, so 2.5 in (63.5 mm)
square fits it, fins and all, with the nose and anchor section lying beside it.
The bleed outline needs shapely (pip install shapely); without it the bleed
line is left out.

The artwork HTML files use the same numbers (CSS variables at their top). If
you change a size here, change it there too.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent

CUT = "#E6007E"
FOLD = "#00A0E3"
BLEED = "#2FB67C"
SAFE = "#9A9AA0"
LABEL = "#6E6E73"
U = 100  # SVG user units per inch

try:
    from shapely.geometry import Polygon
except ImportError:  # bleed line is optional
    Polygon = None


def f(v: float) -> str:
    return f"{v * U:.1f}"


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


class Svg:
    def __init__(self, w: float, h: float, title: str):
        self.w, self.h, self.title, self.body = w, h, title, []

    def poly(self, p, stroke, dash=None, width=1.0, fill="none"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.body.append(f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{d} '
                         f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')

    def path(self, d, stroke, dash=None, width=1.0, fill="none"):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dd} '
                         f'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')

    def line(self, x1, y1, x2, y2, stroke, dash=None, width=1.0):
        self.path(f"M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}", stroke, dash, width)

    def cut(self, p):
        self.poly(p, CUT, width=1.2)

    def fold(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, FOLD, "6 4", 1.0)

    def safe_rect(self, x, y, w, h, m=0.125):
        self.poly([(x + m, y + m), (x + w - m, y + m), (x + w - m, y + h - m), (x + m, y + h - m)], SAFE, "1 3", 0.8)

    def bleed(self, p, d=0.125):
        if Polygon is None:
            return
        b = Polygon(p).buffer(d, join_style=2)
        self.poly(list(b.exterior.coords), BLEED, "2 3", 0.9)

    def text(self, x, y, s, size=0.11, anchor="start", rotate=0, weight=500, fill=LABEL):
        r = f' transform="rotate({rotate} {f(x)} {f(y)})"' if rotate else ""
        self.body.append(f'<text x="{f(x)}" y="{f(y)}" font-size="{size * U:.1f}" text-anchor="{anchor}" '
                         f'font-weight="{weight}" fill="{fill}"{r}>{s}</text>')

    def key(self, x, y):
        items = [(CUT, None, "Cut"), (FOLD, "6 4", "Fold"), (BLEED, "2 3", "Bleed 1/8 in"), (SAFE, "1 3", "Safe area")]
        for i, (c, dash, label) in enumerate(items):
            xx = x + i * 1.35
            self.line(xx, y, xx + 0.4, y, c, dash, 1.4)
            self.text(xx + 0.48, y + 0.04, label, 0.1)

    def save(self, name: str):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}in" height="{self.h}in" '
               f'viewBox="0 0 {f(self.w)} {f(self.h)}">\n<title>{self.title}</title>\n'
               f'<style>text{{font-family:"Space Grotesk","Inter",Arial,sans-serif}}</style>\n'
               + "\n".join(self.body) + "\n</svg>\n")
        (OUT / name).write_text(svg)
        print("wrote", OUT / name)


# ---------------------------------------------------------------------------
# Reverse tuck-end box. Panels left to right: glue flap | front | side 1 |
# back | side 2. Top lid on the back panel, bottom lid on the front panel.
# ---------------------------------------------------------------------------
BOX = dict(W=2.5, D=2.5, L=8.75, T=0.625, HD=0.9, GLUE=0.5, SHEET=(11.0, 17.0))


def tuck_box(name, W, D, L, T, HD, GLUE, SHEET, title):
    sw, sh = SHEET
    tw, th = GLUE + 2 * W + 2 * D, L + 2 * (D + T)
    ox, oy = (sw - tw) / 2, (sh - th) / 2
    i, r = 1 / 16, 0.2  # tuck-flap side inset, corner radius
    xf, x1, xb, x2, xe = GLUE, GLUE + W, GLUE + W + D, GLUE + 2 * W + D, tw
    yt, yb = D + T, D + T + L

    def dust_top(a, b):
        return [(a, yt), (a + 0.06, yt - HD + 0.3), (a + 0.36, yt - HD), (b - 0.36, yt - HD), (b - 0.06, yt - HD + 0.3)]

    def dust_bot(a, b):  # a > b, walking right to left
        return [(a, yb), (a - 0.06, yb + HD - 0.3), (a - 0.36, yb + HD), (b + 0.36, yb + HD), (b + 0.06, yb + HD - 0.3)]

    p = [(xf, yt)]
    p += dust_top(x1, xb)
    p += [(xb, yt), (xb, yt - D), (xb + i, yt - D), (xb + i, yt - D - T + r), (xb + i + r, yt - D - T),
          (x2 - i - r, yt - D - T), (x2 - i, yt - D - T + r), (x2 - i, yt - D), (x2, yt - D)]
    p += dust_top(x2, xe)
    p += [(xe, yt)]
    p += dust_bot(xe, x2)
    p += [(x2, yb), (xb, yb)]
    p += dust_bot(xb, x1)
    p += [(x1, yb), (x1, yb + D), (x1 - i, yb + D), (x1 - i, yb + D + T - r), (x1 - i - r, yb + D + T),
          (xf + i + r, yb + D + T), (xf + i, yb + D + T - r), (xf + i, yb + D), (xf, yb + D), (xf, yb),
          (0, yb - 0.25), (0, yt + 0.25)]
    P = [(x + ox, y + oy) for x, y in p]

    s = Svg(sw, sh, title)
    s.bleed(P)
    s.cut(P)
    for x in (xf, x1, xb, x2):
        s.fold(ox + x, oy + yt, ox + x, oy + yb)
    for a, b in ((x1, xb), (xb, x2), (x2, xe)):
        s.fold(ox + a, oy + yt, ox + b, oy + yt)
    s.fold(ox + xb + i, oy + yt - D, ox + x2 - i, oy + yt - D)
    for a, b in ((xf, x1), (x1, xb), (x2, xe)):
        s.fold(ox + a, oy + yb, ox + b, oy + yb)
    s.fold(ox + xf + i, oy + yb + D, ox + x1 - i, oy + yb + D)
    # Panel names sit outside the printed panels (waste, flaps, tuck flaps), so the
    # overlay doesn't hide the art.
    for x, w in ((xf, W), (x1, D), (xb, W), (x2, D)):
        s.safe_rect(ox + x, oy + yt, w, L)
    s.text(ox + xf + W / 2, oy + yt - 0.2, "FRONT panel below", 0.11, "middle", 0, 600)
    s.text(ox + xb + W / 2, oy + yb + 0.3, "BACK panel above (steps)", 0.11, "middle", 0, 600)
    s.text(ox + xb + W / 2, oy + yt - D - T / 2 + 0.04, "tuck flap · TOP LID below (art upside down)", 0.09, "middle")
    s.text(ox + xf + W / 2, oy + yb + D + T / 2 + 0.04, "tuck flap · BOTTOM LID above", 0.09, "middle")
    s.text(ox + GLUE / 2 + 0.04, oy + yt + L / 2, "GLUE FLAP", 0.11, "middle", -90, 600)
    for x, w, lab in ((x1, D, "SIDE 1 (contents)"), (x2, D, "SIDE 2 (labels)")):
        s.text(ox + x + w / 2, oy + yt - HD / 2, f"dust flap · {lab} below", 0.09, "middle")
        s.text(ox + x + w / 2, oy + yb + HD / 2 + 0.04, "dust flap", 0.09, "middle")
    s.text(0.3, 0.38, f"{title}", 0.16, weight=700, fill="#12203A")
    s.text(0.3, 0.6, f"Inside {W} x {D} x {L} in. Flat {tw:.2f} x {th:.2f} in. Sheet {sw:g} x {sh:g} in. "
                     f"16-18 pt (about 80-100 lb cover) card. Glue the flap inside side 2.", 0.11)
    s.key(0.3, sh - 0.35)
    s.save(name)
    return dict(ox=ox, oy=oy, tw=tw, th=th)


# ---------------------------------------------------------------------------
# Fold-over header card for a 4 in wide poly bag: 4 x 7 in flat, folds to
# 4 x 3.5 in. Front below the fold (upright), back above it (upside down).
# A euro hang slot punched through both layers near the fold. Two per Letter.
# ---------------------------------------------------------------------------
CARD = dict(W=4.0, H=3.5, SHEET=(8.5, 11.0), X0=0.25, Y0=2.0)


def header_cards(name, W, H, SHEET, X0, Y0, title):
    sw, sh = SHEET
    s = Svg(sw, sh, title)
    for k in range(2):
        x, y = X0 + k * W, Y0
        s.cut([(x, y), (x + W, y), (x + W, y + 2 * H), (x, y + 2 * H)])
        s.fold(x, y + H, x + W, y + H)
        # Euro slot: 1.25 x 0.25 in with a 0.4 in round middle, centred 0.3 in from the fold
        for cy in (y + H - 0.3, y + H + 0.3):
            cx, sl, sr, rr = x + W / 2, 0.625, 0.125, 0.2
            d = (f"M{f(cx - sl)} {f(cy - sr)}H{f(cx - rr * 0.6)}A{f(rr)} {f(rr)} 0 0 1 {f(cx + rr * 0.6)} {f(cy - sr)}"
                 f"H{f(cx + sl)}A{f(sr)} {f(sr)} 0 0 1 {f(cx + sl)} {f(cy + sr)}H{f(cx + rr * 0.6)}"
                 f"A{f(rr)} {f(rr)} 0 0 1 {f(cx - rr * 0.6)} {f(cy + sr)}H{f(cx - sl)}A{f(sr)} {f(sr)} 0 0 1 {f(cx - sl)} {f(cy - sr)}Z")
            s.path(d, CUT, width=1.0)
        s.safe_rect(x, y, W, H, 0.12)
        s.safe_rect(x, y + H, W, H, 0.12)
        # staples through both layers and the bag, 0.18 in in from the open edge
        # (the art keeps the bottom 0.3 in clear)
        for sx in (x + 0.7, x + W - 0.7):
            s.line(sx - 0.15, y + 2 * H - 0.18, sx + 0.15, y + 2 * H - 0.18, LABEL, "2 2", 1.0)
            s.line(sx - 0.15, y + 0.18, sx + 0.15, y + 0.18, LABEL, "2 2", 1.0)
    s.text(X0, Y0 - 0.6, "Upper half: BACK, printed upside down. Lower half: FRONT. Fold on the dashed line.", 0.1)
    # crop marks at the sheet edges, so the cards can be cut with a paper trimmer
    for xx in (X0, X0 + W, X0 + 2 * W):
        s.line(xx, Y0 - 0.45, xx, Y0 - 0.2, "#12203A", None, 0.8)
        s.line(xx, Y0 + 2 * H + 0.2, xx, Y0 + 2 * H + 0.45, "#12203A", None, 0.8)
    for yy in (Y0, Y0 + 2 * H):
        s.line(0.02, yy, 0.2, yy, "#12203A", None, 0.8)
        s.line(sw - 0.2, yy, sw - 0.02, yy, "#12203A", None, 0.8)
    s.text(0.3, 0.55, title, 0.16, weight=700, fill="#12203A")
    s.text(0.3, 0.78, "Two cards per US Letter sheet, 65-80 lb cover (ivory if you can). Cut, score and fold, punch the slot "
                      "through both layers, staple over a 4 x 12 in bag.", 0.1)
    s.text(0.3, 0.96, "No bleed: the art stays 1/8 in inside the cut, so home printers and a hand trimmer are fine. "
                      "Dashed grey marks: staple positions.", 0.1)
    s.key(0.3, sh - 0.4)
    s.save(name)


# ---------------------------------------------------------------------------
# Wrap label for a 4 in (inside) x 12 in kraft mailing tube (ULINE S-6242,
# 0.080 in wall, so about 4.16 in outside): circumference 13.07 in plus a
# 0.5 in overlap. 9.5 in tall leaves the end caps and 1.25 in of kraft at
# each end. Sheet: 17 x 11 in (tabloid, landscape).
# ---------------------------------------------------------------------------
TUBE = dict(OD=4.16, OVER=0.5, H=9.5, SHEET=(17.0, 11.0))


def tube_wrap(name, OD, OVER, H, SHEET, title):
    import math
    sw, sh = SHEET
    C = math.pi * OD
    w = C + OVER
    ox, oy = (sw - w) / 2, (sh - H) / 2
    s = Svg(sw, sh, title)
    R = [(ox, oy), (ox + w, oy), (ox + w, oy + H), (ox, oy + H)]
    s.bleed(R)
    s.cut(R)
    # one third of the tube shows at a time: mark the three faces
    third = C / 3
    for k in range(1, 3):
        s.line(ox + k * third, oy + 0.1, ox + k * third, oy + H - 0.1, SAFE, "1 3", 0.8)
    s.poly([(ox + C, oy), (ox + w, oy), (ox + w, oy + H), (ox + C, oy + H)], LABEL, "3 3", 0.8, fill="#6E6E7314")
    for k, lab in enumerate(("FACE 1 · front", "FACE 2 · contents", "FACE 3 · steps + labels")):
        s.text(ox + k * third + third / 2, oy + H + 0.3, lab, 0.13, "middle", 0, 600)
    s.text(ox + C + OVER / 2, oy + H / 2, "OVERLAP · glue, no art", 0.11, "middle", -90, 600)
    s.safe_rect(ox, oy, C, H, 0.25)
    s.text(0.3, 0.38, title, 0.16, weight=700, fill="#12203A")
    s.text(0.3, 0.6, f"Wrap {w:.2f} x {H} in for a 4 in ID x 12 in kraft tube ({OD} in outside, circumference {C:.2f} in). "
                     "Print on 11 x 17 in paper or full-sheet label stock; wrap face 1 first, glue the overlap.", 0.11)
    s.key(0.3, sh - 0.3)
    s.save(name)
    return dict(ox=ox, oy=oy, w=w, C=C)


if __name__ == "__main__":
    g = tuck_box("tuck-box-starter-dieline.svg", **BOX, title="Rocket Builder Starter kit · reverse tuck-end box")
    print("  box offset", g)
    header_cards("header-card-dieline.svg", **CARD, title="Rocket Builder Mini kit · fold-over header card (2-up)")
    t = tube_wrap("tube-wrap-big-dieline.svg", **TUBE, title="Rocket Builder Big kit · mailing-tube wrap label")
    print("  tube offset", t)
