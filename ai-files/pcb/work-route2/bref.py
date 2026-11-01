"""bref.py STEM : B.Cu length of sensitive nets (classes USB, I2S_CLK, AUDIO + AUD_SDA/SCL) over In2 GND fill vs not,
split into 'within 1.0 mm of a via or TH pad' (antipad zone) and 'elsewhere'; plus GND-via distance of every B.Cu run > 5 mm."""
import json, sys
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
G = json.load(open(sys.argv[1] + '.geo.json'))
SENS = {'USB', 'I2S_CLK', 'AUDIO'}; SN = {'/AUD_SDA', '/AUD_SCL'}
gnd = unary_union([Polygon(p[0], p[1:]) for z in G['zones'] if z['net'] == 'GND' for p in z.get('fills', {}).get('In2.Cu', [])])
holes = unary_union([Point(float(v['x']), float(v['y'])).buffer(1.0) for v in G['vias']] +
                    [Point(p["x"], p["y"]).buffer(max(1.0, max(p["sx"], p["sy"]) / 2 + 0.6)) for p in G["pads"] if p.get("drill")])
tot = dict(gnd=0, off_antipad=0, off_elsewhere=0); per = {}
for t in G['tracks']:
    if t['layer'] != 'B.Cu' or t['arc'] or not (t['cls'] in SENS or t['net'] in SN):
        continue
    L = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])])
    on = L.intersection(gnd).length; off = L.length - on
    offL = L.difference(gnd); a = offL.intersection(holes).length; e = offL.length - a
    tot['gnd'] += on; tot['off_antipad'] += a; tot['off_elsewhere'] += e
    if e > 0.05:
        per[t['net']] = per.get(t['net'], 0) + e
print({k: round(v, 2) for k, v in tot.items()}); print('elsewhere by net', {k: round(v, 2) for k, v in per.items()})
