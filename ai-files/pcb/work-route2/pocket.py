"""pocket.py RUN : for each unrouted 'no path (local pocket)' connection, the routed signal tracks (S1-S3 nets, other nets)
and fixed copper (power/GND tracks, vias, zones of other nets) within 1.0 mm of each end pad's edge on F.Cu."""
import sys, json, collections
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
R = sys.argv[1]
A = json.load(open(R + '.analyze.json')); G = json.load(open(R + '-3.geo.json'))
routed = {l.split('#')[0].split()[1] for l in open('hard-nets.txt') if l.split('#')[0].split() and not l.startswith('S0')}
def poly(p):
    ps = p['poly'].get('F.Cu') or next(iter(p['poly'].values()))
    return unary_union([Polygon(r[0], r[1:]) for r in ps])
pads = {'%s-%s' % (p['ref'], p['num']): p for p in G['pads']}
trk = [(LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2), t['net']) for t in G['tracks'] if t['layer'] == 'F.Cu' and not t['arc']]
res = collections.Counter(); rows = []
for u in A['unrouted']:
    if u['cause'] != 'no path (local pocket)':
        continue
    near_sig = set(); near_fix = set()
    for k in (u['a'], u['b']):
        p = pads[k]
        try:
            g = poly(p)
        except Exception:
            g = Point(p['x'], p['y']).buffer(0.3)
        z = g.buffer(1.0)
        for tg, n in trk:
            if n == u['net'] or n == 'GND':
                continue
            if tg.intersects(z):
                (near_sig if n in routed else near_fix).add(n)
    kind = 'routed signal copper near pad' if near_sig else 'fixed copper only'
    res[(u['stage'], kind)] += 1
    rows.append((u['stage'], u['net'], u['a'], u['b'], kind, sorted(near_sig)[:4], sorted(near_fix)[:3]))
for r in rows: print(*r)
print(dict(res))
