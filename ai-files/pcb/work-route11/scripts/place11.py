#!/usr/bin/env python3
"""place11.py BOARD.kicad_pcb GEO.json POSES.json OUTPLAN.json : RT-11 placement + local rip-up plan (edit.py format).
POSES = {"box": [x0,y0,x1,y1], "poses": {ref: [x, y, rot]}, "keep_nets": [...], "extra_seg_del": [...], "extra_via_del": [...],
         "neck": {"NECK_U8": "U8", ...}}
Rip (nets of moved parts only): every segment of a moved-part net (GND excluded) with both ends inside the box, every via of such a net
inside the box; GND: segments with an end inside an old moved GND pad and the GND via at the other end of such a stub (when no other
GND track ends there). NECK_<ref> rule areas are translated with their IC."""
import sys, json, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
from shapely.geometry import Point, Polygon
brd, geo, posef, out = sys.argv[1:5]
P = json.load(open(posef)); G = json.load(open(geo))
x0, y0, x1, y1 = P['box']; inb = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
lines = read(brd); IT = items(brd, lines)
pads = [p for p in G['pads'] if p['ref'] in P['poses']]
R = {p['net'] for p in pads if p['net'] and p['net'] != 'GND' and not p['net'].startswith('unconnected')} - set(P.get('keep_nets', []))
gpads = [Polygon(pl[0]).buffer(0.01) for p in pads if p['net'] == 'GND' for L, plist in p['poly'].items() for pl in plist]
plan = dict(fp_move={k: v for k, v in P['poses'].items()}, seg_del=[], via_del=[], zone_pts={}, via_del_xy=[])
segs = [d for d in IT if d['kind'] == 'segment']; vias = [d for d in IT if d['kind'] == 'via']
gstub_ends = []
KL = P.get('keep_layers', {}); KV = set(P.get('keep_vias', []))
for d in segs:
    (a, b), (c, e) = d['start'], d['end']
    if d['net'] in R and inb(a, b) and inb(c, e) and d.get('layer') not in KL.get(d['net'], []): plan['seg_del'].append(d['uuid'])
    elif d['net'] == 'GND' and inb(a, b) and inb(c, e):
        ia = any(g.contains(Point(a, b)) for g in gpads); ie = any(g.contains(Point(c, e)) for g in gpads)
        if ia or ie:
            plan['seg_del'].append(d['uuid']); gstub_ends.append((c, e) if ia else (a, b))
dl = set(plan['seg_del'])
for v in vias:
    x, y = v['at']
    if v['net'] in R and inb(x, y) and v['net'] not in KV: plan['via_del'].append(v['uuid']); plan['via_del_xy'].append([x, y])
    elif v['net'] == 'GND' and inb(x, y) and any(math.hypot(x - q[0], y - q[1]) < 1e-3 for q in gstub_ends):
        other = [d for d in segs if d['net'] == 'GND' and d['uuid'] not in dl and any(math.hypot(x - q[0], y - q[1]) < 1e-3 for q in (d['start'], d['end']))]
        if not other: plan['via_del'].append(v['uuid']); plan['via_del_xy'].append([x, y])
plan['seg_del'] += P.get('extra_seg_del', []); plan['via_del'] += P.get('extra_via_del', [])
# NECK areas follow their IC (translation; the areas are symmetric rectangles around the IC centre)
F = {f['ref']: f for f in json.load(open(P['dump']))['fps']}
for z in [d for d in IT if d['kind'] == 'zone' and d.get('name') in P.get('neck', {})]:
    ref = P['neck'][z['name']]; f = F[ref]; nx, ny = P['poses'][ref][:2]
    plan['zone_pts'][z['uuid']] = [[round(px + nx - f['x'], 4), round(py + ny - f['y'], 4)] for px, py in z['pts']]
json.dump(plan, open(out, 'w'), indent=1)
print('nets ripped', len(R), sorted(n.split('/')[-1] for n in R)); print('seg_del', len(plan['seg_del']), 'via_del', len(plan['via_del']), 'moves', len(plan['fp_move']), 'zones', len(plan['zone_pts']))
