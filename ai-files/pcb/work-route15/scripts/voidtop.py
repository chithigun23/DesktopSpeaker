#!/usr/bin/env python3
"""voidtop.py BOARD [N] : nets with the most B.Cu length over In2 void (r7 definition, 0.4 mm sampling as voidnet.py)"""
import sys, math, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
D = R.load(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
out = collections.defaultdict(float); where = collections.defaultdict(list)
for s in D['segs']:
    if not R.sig(s) or s['l'] != 'B.Cu': continue
    ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']); n = max(1, int(ln / 0.4)); v = 0
    for i in range(n):
        t = (i + .5) / n; p = Point(s['x1'] + (s['x2'] - s['x1']) * t, s['y1'] + (s['y2'] - s['y1']) * t)
        if not in2g.contains(p) and not in2o.contains(p): v += ln / n
    if v > 0.3: where[s['net']].append((round(v, 1), round(s['x1'], 2), round(s['y1'], 2), round(s['x2'], 2), round(s['y2'], 2)))
    out[s['net']] += v
print('total', round(sum(out.values()), 1))
for k, v in sorted(out.items(), key=lambda kv: -kv[1])[:N]: print('%-40s %5.1f %s' % (k, v, sorted(where[k], reverse=True)[:3]))
