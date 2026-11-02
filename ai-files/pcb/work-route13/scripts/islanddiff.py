#!/usr/bin/env python3
"""islanddiff.py A.geo B.geo : GND fill islands per layer that are new in B (centroid match 0.15 mm), with GND vias / plated GND pads inside"""
import sys, json
from shapely.geometry import Polygon, Point
def isl(f):
    D = json.load(open(f)); out = []
    for z in D['zones']:
        if z['net'] != 'GND': continue
        for L, fl in z.get('fills', {}).items():
            for r in fl:
                if len(r[0]) < 3: continue
                p = Polygon(r[0], [h for h in r[1:] if len(h) >= 3]).buffer(0)
                out.append((L, z.get('name'), p))
    return D, out
_, a = isl(sys.argv[1]); D, b = isl(sys.argv[2])
ka = {(L, round(p.centroid.x, 1), round(p.centroid.y, 1)) for L, n, p in a}
for L, n, p in b:
    if (L, round(p.centroid.x, 1), round(p.centroid.y, 1)) in ka: continue
    g = p.buffer(0.01)
    vs = [(v['x'], v['y']) for v in D['vias'] if v['net'] == 'GND' and g.contains(Point(v['x'], v['y']))]
    ps = [q['ref'] + '-' + q['num'] for q in D['pads'] if q['net'] == 'GND' and (q['drill'] or L == 'F.Cu' or L == 'B.Cu') and g.intersects(Point(q['x'], q['y']).buffer(0.1))]
    print(L, n, 'centroid (%.1f, %.1f)' % (p.centroid.x, p.centroid.y), 'area %.1f' % p.area, 'GND vias', len(vs), 'GND pads', ps[:4])
