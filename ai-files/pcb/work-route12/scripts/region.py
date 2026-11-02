#!/usr/bin/env python3
"""region.py GEO X0 Y0 X1 Y1 : copper per net inside a box; ports = endpoints of segments that cross the box edge"""
import sys, json, collections
G = json.load(open(sys.argv[1])); x0, y0, x1, y1 = map(float, sys.argv[2:6])
inb = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
N = collections.defaultdict(lambda: dict(segs_in=0, len_in=0.0, cross=[], vias=0))
for t in G['tracks']:
    a, b = inb(t['x1'], t['y1']), inb(t['x2'], t['y2'])
    if a or b:
        n = N[t['net']]
        if a and b: n['segs_in'] += 1; n['len_in'] += ((t['x1']-t['x2'])**2+(t['y1']-t['y2'])**2)**.5
        else: n['cross'].append((t['layer'][0], t['w'], (t['x1'], t['y1']) if a else (t['x2'], t['y2']), (t['x2'], t['y2']) if a else (t['x1'], t['y1']), t['uuid'][:8]))
for v in G['vias']:
    if inb(v['x'], v['y']): N[v['net']]['vias'] += 1
for k, n in sorted(N.items()):
    print('%-28s in %2d segs %6.1f mm  vias %2d  cross %s' % (k.split('/')[-1], n['segs_in'], n['len_in'], n['vias'], ['%s w%.2f in(%.2f,%.2f) out(%.2f,%.2f) %s' % (c[0], c[1], *c[2], *c[3], c[4]) for c in n['cross']]))
