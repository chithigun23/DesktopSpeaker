#!/usr/bin/env python3
"""in2map.py GEO X0 Y0 X1 Y1 STEP [layer] : ASCII map of zone fills on a layer: G=GND, letter=other net (legend), .=no fill; In2 tracks '#'"""
import sys, json
import numpy as np, shapely
from shapely.geometry import Polygon, LineString
D = json.load(open(sys.argv[1])); x0, y0, x1, y1, st = map(float, sys.argv[2:7]); L = sys.argv[7] if len(sys.argv) > 7 else 'In2.Cu'
xs = np.arange(x0, x1 + 1e-9, st); ys = np.arange(y0, y1 + 1e-9, st)
X, Y = np.meshgrid(xs, ys)
M = np.full(X.shape, '.', dtype='<U1'); leg = {}
for z in D['zones']:
    for r in z.get('fills', {}).get(L, []):
        if len(r[0]) < 3: continue
        p = Polygon(r[0], [h for h in r[1:] if len(h) >= 3]).buffer(0)
        if p.bounds[2] < x0 or p.bounds[0] > x1 or p.bounds[3] < y0 or p.bounds[1] > y1: continue
        c = 'G' if z['net'] == 'GND' else leg.setdefault(z['net'], 'abcdefghijklmnopqrstuvwxyz'[len(leg)])
        M[shapely.contains_xy(p, X, Y)] = c
for t in D['tracks']:
    if t['layer'] != L: continue
    g = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2)
    if g.bounds[2] < x0 or g.bounds[0] > x1 or g.bounds[3] < y0 or g.bounds[1] > y1: continue
    M[shapely.contains_xy(g, X, Y)] = '#'
print('     ' + ''.join(('%d' % (x % 10)) if abs(x - round(x)) < 1e-6 else ' ' for x in xs))
for j, y in enumerate(ys): print('%5.1f %s' % (y, ''.join(M[j])))
print(leg)
