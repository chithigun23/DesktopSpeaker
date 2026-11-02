#!/usr/bin/env python3
"""freevia.py GEO PLAN|- NET X Y R [clr] : candidate via sites (0.6/0.3) for NET within R of (X, Y), clear of every other-net item
on all layers (tracks/vias/pads/zone fills of other nets, + clr), no pad touch (0.06), board edge 0.5. Plan seg_add/via_add included,
plan seg_del removed. Prints the best sites (closest first)."""
import sys, json, math
import numpy as np, shapely
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
geo, planf, net = sys.argv[1:4]; X, Y, R = map(float, sys.argv[4:7]); clr = float(sys.argv[7]) if len(sys.argv) > 7 else 0.2
D = json.load(open(geo)); P = json.load(open(planf)) if planf != '-' else {}
dels = set(P.get('seg_del', []))
win = box(X - R - 3, Y - R - 3, X + R + 3, Y + R + 3)
obs = []; vr = 0.3
def poly(rings):
    p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 3]); return p if p.is_valid else p.buffer(0)
for p in D['pads']:
    for L, pl in p['poly'].items():
        for rings in pl:
            g = poly(rings)
            if not g.intersects(win): continue
            obs.append(g.buffer(vr + (0.06 if p['net'] == net else clr)))
    if p['drill']: obs.append(Point(p['x'], p['y']).buffer(max(p['drill']) / 2 + 0.15 + 0.25))
for t in D['tracks']:
    if t['net'] == net or any(t['uuid'].startswith(u) for u in dels): continue
    g = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])])
    if g.distance(Point(X, Y)) > R + 3: continue
    obs.append(g.buffer(t['w'] / 2 + clr + vr))
for v in D['vias']:
    if math.hypot(v['x'] - X, v['y'] - Y) > R + 3: continue
    obs.append(Point(v['x'], v['y']).buffer((v['d'] / 2 + clr + vr) if v['net'] != net else (0.15 + 0.25 + 0.15)))
for z in D['zones']:
    if z['net'] == net: continue
    for L, fl in z.get('fills', {}).items():
        for rings in fl:
            if len(rings[0]) < 3: continue
            g = poly(rings)
            if g.intersects(win): obs.append(g.buffer(clr + vr))
for a in D['areas']:
    for rings in a['outline']:
        g = poly(rings[0]) if isinstance(rings[0][0][0], list) else poly(rings)
        if a['name'].startswith('BM83') or 'ANTENNA' in a['name']: obs.append(g.buffer(vr))
for a in P.get('seg_add', []):
    if a[1] == net: continue
    obs.append(LineString([(a[3], a[4]), (a[5], a[6])]).buffer(a[2] / 2 + clr + vr))
for v in P.get('via_add', []):
    obs.append(Point(v[1], v[2]).buffer((v[3] / 2 + clr + vr) if v[0] != net else 0.55))
O = unary_union(obs)
edge = Polygon(D['outline'][0][0]).buffer(-0.5 - vr)
res = []
for x in np.arange(X - R, X + R + 1e-9, 0.05):
    for y in np.arange(Y - R, Y + R + 1e-9, 0.05):
        d = math.hypot(x - X, y - Y)
        if d > R: continue
        q = Point(x, y)
        if edge.contains(q) and not O.contains(q): res.append((round(d, 3), round(x, 3), round(y, 3)))
res.sort()
print(len(res), "sites")
import os
if os.environ.get("GRID"):
    cl = {}
    for d, x, y in res: cl.setdefault((round(x * 2) / 2, round(y * 2) / 2), (d, x, y))
    print(' '.join('(%.2f,%.2f)' % (v[1], v[2]) for k, v in sorted(cl.items())))
else: print(' '.join('(%.2f,%.2f)' % (x, y) for d, x, y in res[:int(os.environ.get("NS", 12))]))
