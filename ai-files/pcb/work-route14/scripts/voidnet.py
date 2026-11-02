#!/usr/bin/env python3
"""voidnet.py A.kicad_pcb B.kicad_pcb : B.Cu signal length over In2 void per net (r7_metrics definition), A vs B, nets that differ"""
import sys, math, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
def per(path):
    D = R.load(path); in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
    out = collections.defaultdict(float); segs = collections.defaultdict(list)
    for s in D['segs']:
        if not R.sig(s) or s['l'] != 'B.Cu': continue
        ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']); n = max(1, int(ln / 0.4))
        for i in range(n):
            t = (i + .5) / n; p = Point(s['x1'] + (s['x2'] - s['x1']) * t, s['y1'] + (s['y2'] - s['y1']) * t)
            if not in2g.contains(p) and not in2o.contains(p): out[s['net']] += ln / n; segs[s['net']].append((round(p.x, 1), round(p.y, 1)))
    return out, segs
a, _ = per(sys.argv[1]); b, sb = per(sys.argv[2])
print('total', round(sum(a.values()), 1), '->', round(sum(b.values()), 1))
for n in sorted(set(a) | set(b), key=lambda n: -(b.get(n, 0) - a.get(n, 0))):
    if abs(a.get(n, 0) - b.get(n, 0)) > 0.05: print('  %-36s %5.1f -> %5.1f  %s' % (n, a.get(n, 0), b.get(n, 0), sb.get(n, [])[:6]))
