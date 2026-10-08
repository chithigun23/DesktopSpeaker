# -*- coding: utf-8 -*-
"""Sandbox check of a hand-placed cluster (KiCad python): v10_cellcheck.py spec.json [out.png]
spec: {"parts": [[ref, u, v, rot], ...]} in the board frame (u right, v rear), origin anywhere. Prints courtyard overlaps (gap < 0.2 mm,
0.5 mm to tall parts) and, for every pad, the distance to the nearest other-part pad on the same net."""
import sys, json, math, re
import xml.etree.ElementTree as ET
import pcbnew
ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
LIB = ROOT + 'DesktopSpeaker-kicad/kicad-library/footprint'
root = ET.parse(ROOT + 'ai-files/pcb/work-v10/ds_net.xml').getroot()
fpn, pins = {}, {}
for c in root.find('components'):
    fpn[c.get('ref')] = (c.findtext('footprint') or '').split(':')[-1]
for n in root.find('nets'):
    for nd in n:
        pins.setdefault(nd.get('ref'), {})[nd.get('pin')] = n.get('name')
spec = json.load(open(sys.argv[1]))
MM = 1e6
P = []
for ref, u, v, rot in spec['parts']:
    f = pcbnew.FootprintLoad(LIB, fpn[ref])
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.VECTOR2I(int(u * MM), int(-v * MM)))
    cb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
    cr = [cb.GetX() / MM, -cb.GetBottom() / MM, cb.GetRight() / MM, -cb.GetY() / MM]
    pads = []
    for p in f.Pads():
        b = p.GetBoundingBox()
        pr = (b.GetX() / MM, -b.GetBottom() / MM, b.GetRight() / MM, -b.GetY() / MM)
        cr = [min(cr[0], pr[0]), min(cr[1], pr[1]), max(cr[2], pr[2]), max(cr[3], pr[3])]
        pads.append((p.GetNumber(), pins.get(ref, {}).get(p.GetNumber(), ''), pr))
    P.append((ref, cr, pads))


def gap(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0))


def ov(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


for r_, c_, p_ in P: print("CRT", r_, [round(x, 2) for x in c_])
tall = re.compile(r'^(L\d+|C275|J\d+|SW\d+|H)')
for i, (ra, ca, pa) in enumerate(P):
    for rb, cb_, pb in P[i + 1:]:
        need = 0.5 if (tall.match(ra) or tall.match(rb)) else 0.15
        g = gap(ca, cb_)
        if ov(ca, cb_) or g < need:
            print('CLASH %-5s %-5s gap %.2f' % (ra, rb, -1 if ov(ca, cb_) else g))
for ref, cr, pads in P:
    out = []
    for num, net, pr in pads:
        if not net or net == 'GND' or net.startswith('unconnected'):
            continue
        best = None
        for r2, c2, p2 in P:
            if r2 == ref:
                continue
            for n2, nt2, q in p2:
                if nt2 == net:
                    d = gap(pr, q)
                    if best is None or d < best[0]:
                        best = (d, r2 + '.' + n2)
        if best:
            out.append('%s:%s %.2f' % (num, best[1], best[0]))
    print('%-5s' % ref, ' '.join(out))
