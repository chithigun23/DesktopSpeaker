"""fref.py STEM : F.Cu length of routed signal nets over In1 non-GND (void), split antipad zone (within TH/via pad + 0.6 mm) / elsewhere, top nets."""
import json, sys, collections
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
G = json.load(open(sys.argv[1] + '.geo.json'))
nets = {l.split('#')[0].split()[1] for l in open('hard-nets.txt') if l.split('#')[0].split()}
gnd = unary_union([Polygon(p[0], p[1:]) for z in G['zones'] if z['net'] == 'GND' for p in z.get('fills', {}).get('In1.Cu', [])])
holes = unary_union([Point(float(v['x']), float(v['y'])).buffer(float(v['d']) / 2 + 0.6) for v in G['vias']] +
                    [Point(p['x'], p['y']).buffer(max(float(p['sx']), float(p['sy'])) / 2 + 0.6) for p in G['pads'] if p.get('drill')])
ap = 0; el = collections.Counter(); tot = 0
for t in G['tracks']:
    if t['layer'] != 'F.Cu' or t['arc'] or t['net'] not in nets:
        continue
    L = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]); tot += L.length
    off = L.difference(gnd); a = off.intersection(holes).length; ap += a; el[t['net']] += off.length - a
print('F.Cu routed %.1f mm; over In1 non-GND: antipad zone %.1f mm, elsewhere %.1f mm' % (tot, ap, sum(el.values())))
print('elsewhere by net', [(n, round(v, 2)) for n, v in el.most_common(12) if v > 0.05])
