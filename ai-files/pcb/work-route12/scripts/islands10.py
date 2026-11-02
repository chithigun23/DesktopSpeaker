#!/usr/bin/env python3
"""islands10.py A.kicad_pcb B.kicad_pcb : RT-10 pour check per zone on every copper layer: number of filled islands and filled area,
A vs B (zones matched by name+net+layer, teardrops ignored). Flags zones whose island count rose or whose area dropped by > 2 %."""
import sys, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Polygon
def load(p):
    B = R.parse(p); out = collections.defaultdict(lambda: [0, 0.0])
    for z in R.kids(B, 'zone'):
        td = R.kid(z, 'attr')
        if td and R.kid(td, 'teardrop'): continue
        nm = R.kid(z, 'name'); nn = R.kid(z, 'net_name') or R.kid(z, 'net')
        name = nm[1] if nm else '?'; net = R.NN(nn) if nn else ''
        for fp in R.kids(z, 'filled_polygon'):
            pts = [(float(q[1]), float(q[2])) for q in R.kid(fp, 'pts') if isinstance(q, list) and q[0] == 'xy']
            k = (name, net, R.kid(fp, 'layer')[1]); out[k][0] += 1
            g = Polygon(pts); out[k][1] += (g if g.is_valid else g.buffer(0)).area
    return out
a, b = load(sys.argv[1]), load(sys.argv[2]); bad = 0
print('%-24s %-30s %-7s %9s %9s %10s %10s' % ('zone', 'net', 'layer', 'isl A', 'isl B', 'area A', 'area B'))
for k in sorted(set(a) | set(b)):
    ia, aa = a.get(k, [0, 0]); ib, ab = b.get(k, [0, 0])
    flag = ib > ia or ab < aa * 0.98
    if flag or k[2] == 'In2.Cu':
        print('%-24s %-30s %-7s %9d %9d %10.1f %10.1f %s' % (k[0][:24], k[1][-30:], k[2], ia, ib, aa, ab, 'CHECK' if flag else ''))
    bad += flag
print('zones flagged:', bad)
