#!/usr/bin/env python3
"""zonecut.py BOARD OUT_PLAN.json UUID:x0,y0,x1,y1[;x0,y0,x1,y1] ... : zone_pts plan entries = zone outline minus boxes (venv python, shapely).
The result must stay one polygon without holes (KiCad zone outline); aborts otherwise."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
B, outp = sys.argv[1:3]
IT = items(B, read(B))
plan = json.load(open(outp)) if os.path.exists(outp) else {}
plan.setdefault('zone_pts', {})
for arg in sys.argv[3:]:
    u, bs = arg.split(':')
    z = [d for d in IT if d['kind'] == 'zone' and d.get('uuid', '').startswith(u)]
    assert len(z) == 1, (u, len(z))
    P = Polygon(z[0]['pts'])
    cut = unary_union([box(*map(float, b.split(','))) for b in bs.split(';')])
    R = P.difference(cut)
    if R.geom_type != 'Polygon' or len(R.interiors):
        sys.exit('ABORT: %s -> %s with %d holes' % (u, R.geom_type, len(getattr(R, 'interiors', []))))
    pts = [(round(x, 6), round(y, 6)) for x, y in list(R.exterior.coords)[:-1]]
    plan['zone_pts'][z[0]['uuid']] = pts
    print(u, z[0].get('name'), 'area %.1f -> %.1f' % (P.area, R.area), len(z[0]['pts']), '->', len(pts))
json.dump(plan, open(outp, 'w'), indent=1)
