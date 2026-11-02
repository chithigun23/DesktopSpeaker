#!/usr/bin/env python3
"""planvoid.py BOARD.kicad_pcb PLAN.json : B.Cu length over In2 void of the plan's added B segments (before refill effects)"""
import sys, math, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
D = R.load(sys.argv[1]); P = json.load(open(sys.argv[2]))
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
tot = {}
for a in P['seg_add']:
    if a[0] != 'B.Cu': continue
    x1, y1, x2, y2 = a[3:7]; ln = math.hypot(x2 - x1, y2 - y1); n = max(1, int(ln / 0.4))
    for i in range(n):
        u = (i + .5) / n; p = Point(x1 + (x2 - x1) * u, y1 + (y2 - y1) * u)
        if not in2g.contains(p) and not in2o.contains(p): tot[a[1]] = tot.get(a[1], 0) + ln / n
print({k: round(v, 1) for k, v in tot.items()}, 'B total', round(sum(math.hypot(a[5]-a[3], a[6]-a[4]) for a in P['seg_add'] if a[0]=='B.Cu'), 1))
