"""Write the pattern SVGs into docs/brand/patterns/."""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'patterns')
NIGHT, PAPER, ORANGE, SKY, GREY = '#12203A', '#F6F1E7', '#F2652B', '#3D8BFD', '#6E6E73'

# rocket mark geometry (same as logo/rb-mark-*.svg), drawn upright around the origin
BODY = 'M0 -34C4.2 -29.6 6 -23.5 6 -16V12L3.5 16H-3.5L-6 12V-16C-6 -23.5 -4.2 -29.6 0 -34Z'
CHEV = 'M-13 6L0 -9L13 6V11L0 -4L-13 11Z' 'M-13 17L0 2L13 17V22L0 7L-13 22Z'
STAR = 'M0 -7L1.6 -1.6L7 0L1.6 1.6L0 7L-1.6 1.6L-7 0L-1.6 -1.6Z'


def write(name, s):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), 'w') as f:
        f.write(s)
    print('wrote', name)


def head(w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
            f'<title>{title}</title>\n')


# 1. Blueprint grid -------------------------------------------------------------------
def grid_tile(bg, minor, major):
    # 40 px tile: minor line every 8 px, major line on the tile edge. Lines sit on half
    # pixels so they stay crisp at 1x.
    minor_d = ''.join(f'M{x + .5} 0V40M0 {x + .5}H40' for x in (8, 16, 24, 32))
    bgrect = f'<rect width="40" height="40" fill="{bg}"/>\n' if bg else ''
    return (head(40, 40, 'Rocket Builder blueprint grid tile') + bgrect +
            f'<path d="{minor_d}" stroke="{minor}" stroke-width="1"/>\n'
            f'<path d="M.5 0V40M0 .5H40" stroke="{major}" stroke-width="1"/>\n</svg>\n')


write('blueprint-grid-tile-paper.svg', grid_tile(PAPER, 'rgba(61,139,253,.14)', 'rgba(61,139,253,.38)'))
write('blueprint-grid-tile-night.svg', grid_tile(NIGHT, 'rgba(246,241,231,.06)', 'rgba(246,241,231,.16)'))


def grid_panel(bg, minor, major, ink, name):
    w, h = 800, 480
    minor_d = ''.join(f'M{x + .5} 0V40M0 {x + .5}H40' for x in (8, 16, 24, 32))
    # corner registration marks and a small title block, like a drawing sheet
    marks = ''.join(
        f'<path d="M{x - 10} {y}H{x + 10}M{x} {y - 10}V{y + 10}"/><circle cx="{x}" cy="{y}" r="5"/>'
        for x, y in ((40, 40), (760, 40), (40, 440), (760, 440)))
    return (head(w, h, 'Rocket Builder blueprint panel') +
            f'<defs><pattern id="rb-grid-{name}" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="{minor_d}" stroke="{minor}" stroke-width="1"/>'
            f'<path d="M.5 0V40M0 .5H40" stroke="{major}" stroke-width="1"/></pattern></defs>\n'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>\n<rect width="{w}" height="{h}" fill="url(#rb-grid-{name})"/>\n'
            f'<g fill="none" stroke="{ink}" stroke-width="1.5">{marks}</g>\n'
            f'<g fill="none" stroke="{ink}" stroke-width="1.5"><rect x="560" y="380" width="180" height="44"/>'
            f'<path d="M560 402H740M650 402V424"/></g>\n</svg>\n')


write('blueprint-grid-paper.svg', grid_panel(PAPER, 'rgba(61,139,253,.14)', 'rgba(61,139,253,.38)', SKY, 'paper'))
write('blueprint-grid-night.svg', grid_panel(NIGHT, 'rgba(246,241,231,.06)', 'rgba(246,241,231,.16)', '#8BBBFE', 'night'))


# 2. Flight arc --------------------------------------------------------------------------
def flight_arc(bg, ink, body, sub, name):
    w, h = 1200, 400
    # climb: quadratic from the pad to apogee; the rocket rides where it runs at 45 degrees
    p0, c, p1 = (120, 340), (320, 80), (520, 80)
    t = 1 - 200 / 260  # where dy/dx = -1 on this curve
    lerp = lambda u, v, k: (u[0] + k * (v[0] - u[0]), u[1] + k * (v[1] - u[1]))
    a, b = lerp(p0, c, t), lerp(c, p1, t)
    rx, ry = lerp(a, b, t)
    apex = p1
    bgrect = f'<rect width="{w}" height="{h}" fill="{bg}"/>\n' if bg else ''
    stars = ''.join(f'<path transform="translate({x} {y}) scale({s})" d="{STAR}"/>'
                    for x, y, s in ((250, 90, 1), (640, 40, .7), (820, 170, 1.1), (1080, 70, .8), (150, 170, .6), (1140, 230, .6), (420, 180, .5)))
    # launch puffs at the pad: three overlapping outlined circles
    puffs = (f'<g fill="{bg or "none"}" stroke="{ink}" stroke-width="2.5">'
             '<circle cx="160" cy="364" r="8"/><circle cx="84" cy="362" r="10"/><circle cx="140" cy="358" r="13"/><circle cx="106" cy="354" r="16"/></g>')
    pad = f'<path d="M50 372H190" stroke="{ink}" stroke-width="3" stroke-linecap="round"/>'
    # parachute on the way down (simple canopy + shroud lines)
    chute = (f'<g transform="translate(1000 250)" fill="none" stroke="{ink}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">'
             '<path d="M-26 0C-26 -18 -12 -28 0 -28C12 -28 26 -18 26 0C20 -5 13 -5 8.6 0C4 -5 -4 -5 -8.6 0C-13 -5 -20 -5 -26 0Z" fill="' + ORANGE + '"/>'
             '<path d="M-26 0L0 34L26 0M-8.6 0L0 34L8.6 0"/><path d="M-3 34H3V48H-3Z" fill="' + ink + '"/></g>')
    return (head(w, h, 'Rocket Builder flight arc') + bgrect +
            f'<g fill="none" stroke-linecap="round">'
            f'<path d="M{p0[0]} {p0[1]}Q{a[0]:.1f} {a[1]:.1f} {rx:.1f} {ry:.1f}" stroke="{ORANGE}" stroke-width="4" stroke-dasharray="2 10"/>'
            f'<path d="M{rx:.1f} {ry:.1f}Q{b[0]:.1f} {b[1]:.1f} {p1[0]} {p1[1]}" stroke="{ink}" stroke-width="3" stroke-dasharray="14 12"/>'
            f'<path d="M{p1[0]} {p1[1]}C720 80 930 120 1000 214" stroke="{ink}" stroke-width="3" stroke-dasharray="1 10"/>'
            f'</g>\n'
            f'<g fill="{sub}">{stars}</g>\n'
            f'<g fill="none" stroke="{ink}" stroke-width="2"><path d="M{apex[0]} {apex[1] - 22}V{apex[1] - 10}"/></g>\n'
            f'<text x="{apex[0]}" y="{apex[1] - 30}" fill="{ink}" font-family="Space Grotesk, sans-serif" font-size="14" font-weight="700" letter-spacing="2" text-anchor="middle">APOGEE</text>\n'
            + puffs + '\n' + pad + '\n' + chute + '\n' +
            f'<g transform="translate({rx + 18:.1f} {ry - 18:.1f}) rotate(45) scale(1.6)">'
            f'<path d="{BODY}" fill="{body}"/><path d="{CHEV}" fill="{ORANGE}" stroke="{bg or PAPER}" stroke-width="2.4" paint-order="stroke"/></g>\n'
            '</svg>\n')


write('flight-arc-paper.svg', flight_arc(PAPER, NIGHT, NIGHT, '#3D8BFD', 'paper'))
write('flight-arc-night.svg', flight_arc(NIGHT, PAPER, PAPER, '#8BBBFE', 'night'))


# 3. Fletching stripe band -----------------------------------------------------------------
def band(bg, a, b, name, w=960):
    # 48 px tall tile, 40 px repeat: an orange and a second-colour chevron, pointing in the
    # direction of flight (right), like the cresting and feathers on an arrow shaft.
    chev = lambda x: f'M{x} 4L{x + 16} 24L{x} 44H{x + 9}L{x + 25} 24L{x + 9} 4Z'  # 25 wide
    return (head(w, 48, 'Rocket Builder fletching band') +
            f'<defs><pattern id="rb-fletch-{name}" width="40" height="48" patternUnits="userSpaceOnUse">'
            f'<path d="{chev(1)}" fill="{a}"/><path d="{chev(15)}" fill="{b}"/></pattern></defs>\n'
            f'<rect width="{w}" height="48" fill="{bg}"/>\n'
            f'<rect width="{w}" height="48" fill="url(#rb-fletch-{name})"/>\n</svg>\n')


write('fletching-band-paper.svg', band(PAPER, ORANGE, NIGHT, 'paper'))
write('fletching-band-night.svg', band(NIGHT, ORANGE, PAPER, 'night'))
