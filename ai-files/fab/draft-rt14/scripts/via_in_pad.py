#!/usr/bin/env python3
"""via_in_pad.py PASTE.json OUT.json  (venv python with shapely, -I): vias whose drill hole touches an F.Cu SMD pad
(copper outline) or comes within 0.15 mm of it; exposed pads (pad numbers of thermal pads with >= 4 vias) are listed apart."""
import json, sys, collections
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
d = json.load(open(sys.argv[1]))
pads = []
for p in d['pads']:
    if p['attr'] != 1 or not p.get('fcu', True): continue
    gs = [Polygon(o, h).buffer(0) for o, h in p['poly'] if len(o) >= 3]
    if gs: pads.append((unary_union(gs), p))
rows = []
for v in d['vias']:
    hole = Point(v['x'], v['y']).buffer(v['drill'] / 2, 24)
    for g, p in pads:
        dist = g.distance(hole)
        if dist <= 0.15:
            rows.append({'via': [v['x'], v['y']], 'drill': v['drill'], 'via_net': v['net'], 'pad': '%s.%s' % (p['ref'], p['num']),
                         'pad_net': p['net'], 'centre_in_pad': g.contains(Point(v['x'], v['y'])), 'hole_to_pad_mm': round(dist, 3)})
cnt = collections.Counter(r['pad'] for r in rows)
ep = {k for k, n in cnt.items() if n >= 4}
inpad = [r for r in rows if r['pad'] not in ep and r['centre_in_pad']]
edge = [r for r in rows if r['pad'] not in ep and not r['centre_in_pad']]
json.dump({'exposed_pad_vias': {k: cnt[k] for k in sorted(ep)}, 'via_in_pad': inpad, 'via_at_pad_edge': sorted(edge, key=lambda r: r['hole_to_pad_mm'])},
          open(sys.argv[2], 'w'), indent=1)
print('VIAPAD exposed-pad vias', sum(cnt[k] for k in ep), dict((k, cnt[k]) for k in sorted(ep)), '| via centre in a non-EP pad', len(inpad),
      sorted(r['pad'] for r in inpad), '| hole within 0.15 mm of a pad', len(edge))
