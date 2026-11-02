#!/usr/bin/env python3
"""voideval.py BOARD.kicad_pcb TAG : RT-10 - for each voidjobs result t/p_TAG_k.json: new B-over-void, length and via count vs the ripped chain."""
import sys, math, json, os
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
brd, tag = sys.argv[1:3]
D = R.load(brd)
g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
def void(x1, y1, x2, y2):
    ln = math.hypot(x2 - x1, y2 - y1); n = max(1, int(ln / 0.2)); v = 0
    for i in range(n):
        t = (i + .5) / n; p = Point(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        if not g.contains(p) and not o.contains(p): v += ln / n
    return v
out = []
for j in json.load(open('t/vj_%s.json' % tag)):
    f = 't/p_%s_%d.json' % (tag, j['k'])
    if not os.path.exists(f): print(j['k'], j['net'], 'FAIL/none'); continue
    p = json.load(open(f))
    if not p.get('seg_add'): print(j['k'], j['net'], 'FAIL'); continue
    v = sum(void(*s[3:7]) for s in p['seg_add'] if s[0] == 'B.Cu')
    L = sum(math.dist(s[3:5], s[5:7]) for s in p['seg_add']); nv = len(p['via_add'])
    gain = j['void'] - v
    ok = gain >= 0.8 and L <= j['len'] * 1.15 + 1.0 and nv == 0
    out.append(dict(k=j['k'], net=j['net'], old_void=j['void'], new_void=round(v, 2), old_len=j['len'], new_len=round(L, 2), vias=nv, ok=ok))
    print(j['k'], j['net'], 'void %.2f -> %.2f  len %.2f -> %.2f  +vias %d  %s' % (j['void'], v, j['len'], L, nv, 'ACCEPT' if ok else ''))
json.dump(out, open('t/ve_%s.json' % tag, 'w'), indent=1)
