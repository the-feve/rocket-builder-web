"""Convert a line of text to an SVG path with Space Grotesk outlines (GPOS kerning applied)."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

_fonts = {}


def font(path):
    if path not in _fonts:
        t = TTFont(path)
        _fonts[path] = (t, t.getGlyphSet(), t.getBestCmap(), _kern_pairs(t))
    return _fonts[path]


def _kern_pairs(t):
    pairs1, class_tables = {}, []
    gpos = t['GPOS'].table
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag != 'kern':
            continue
        for li in fr.Feature.LookupListIndex:
            lk = gpos.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, 'LookupType', 2) != 2 and lk.LookupType not in (2, 9):
                    continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for i, g in enumerate(cov):
                        for pvr in st.PairSet[i].PairValueRecord:
                            v = getattr(pvr.Value1, 'XAdvance', 0) or 0
                            pairs1.setdefault((g, pvr.SecondGlyph), v)
                elif st.Format == 2:
                    class_tables.append((set(cov), st.ClassDef1.classDefs, st.ClassDef2.classDefs, st.Class1Record))
    return pairs1, class_tables


def kern(k, a, b):
    pairs1, cls = k
    if (a, b) in pairs1:
        return pairs1[(a, b)]
    for cov, c1, c2, recs in cls:
        if a in cov:
            v = recs[c1.get(a, 0)].Class2Record[c2.get(b, 0)].Value1
            x = getattr(v, 'XAdvance', 0) or 0 if v else 0
            if x:
                return x
    return 0


def text_path(fontfile, text, size, x=0.0, y=0.0, tracking=0.0):
    """Return (d, width). y is the baseline. tracking is in em/1000 units."""
    t, gs, cmap, k = font(fontfile)
    upm = t['head'].unitsPerEm
    s = size / upm
    pen = SVGPathPen(gs, ntos=lambda v: ('%.2f' % v).rstrip('0').rstrip('.'))
    adv = 0.0
    prev = None
    for ch in text:
        g = cmap[ord(ch)]
        if prev:
            adv += kern(k, prev, g)
        tp = TransformPen(pen, (s, 0, 0, -s, x + adv * s, y))
        gs[g].draw(tp)
        adv += t['hmtx'][g][0] + tracking
        prev = g
    adv -= tracking
    return pen.getCommands(), adv * s


if __name__ == '__main__':
    d, w = text_path(sys.argv[1], sys.argv[2], float(sys.argv[3]))
    print(w)
