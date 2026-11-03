#!/usr/bin/env python3
"""whyblk.py GEO NET LAYER x y [w] : RT-10 debug - which items block a track centre of NET at (x, y) (strict and neck clearances)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hr10 as H
from shapely.geometry import Point
geo, net, L, x, y = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]); w = float(sys.argv[6]) if len(sys.argv) > 6 else 0.25
B = H.Board(geo); cls = B.netcls.get(net, 'Default'); p = Point(x, y)
print('in neck', B.neck.contains(p), 'icbody', B.icbody.contains(p) if B.icbody else None, 'modko', B.modko.contains(p))
for it in B.query(L, p.buffer(3)):
    if it.net == net: continue
    if it.typ == 'Zone' and it.net == 'GND': continue
    cs = H.RU.clr_strict(cls, net, it.cls, it.typ); d = it.geom.distance(p)
    if d < cs + w / 2 + 0.05: print('  %-6s %-28s %-8s d %.3f need %.3f %s' % (it.typ, it.net[-28:], it.cls, d, cs + w / 2, it.name))
for a in B.areas:
    g = H.mk(a['outline'])
    if L in a['layers'] and g.buffer(w / 2).contains(p): print('  area', a['name'], a['no_tracks'])
