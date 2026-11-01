"""brun.py STEM : contiguous B.Cu runs of sensitive nets; for runs > 5 mm the largest gap along the run to the nearest GND via."""
import json, sys, collections
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, linemerge
G = json.load(open(sys.argv[1] + '.geo.json'))
SENS = {'USB', 'I2S_CLK', 'AUDIO'}; SN = {'/AUD_SDA', '/AUD_SCL'}
gv = [Point(float(v['x']), float(v['y'])) for v in G['vias'] if v['net'] == 'GND']
by = collections.defaultdict(list)
for t in G['tracks']:
    if t['layer'] == 'B.Cu' and not t['arc'] and (t['cls'] in SENS or t['net'] in SN):
        by[t['net']].append(LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]))
rows = []
for n, ls in by.items():
    u = unary_union(ls); m = linemerge(u) if hasattr(u, "geoms") else u; parts = list(m.geoms) if hasattr(m, 'geoms') else [m]
    for p in parts:
        if p.length < 5: rows.append((n, round(p.length, 2), None)); continue
        k = int(p.length / 0.25) + 1
        worst = max(min(q.distance(g) for g in gv) for q in (p.interpolate(i * p.length / k) for i in range(k + 1)))
        rows.append((n, round(p.length, 2), round(worst, 2)))
rows.sort(key=lambda r: -r[1])
print('B.Cu sensitive runs', len(rows), 'longest', rows[:8])
print('runs > 5 mm:', [r for r in rows if r[1] > 5])
