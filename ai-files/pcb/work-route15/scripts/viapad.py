#!/usr/bin/env python3
"""viapad.py GEO.json [BASEGEO.json] : vias (new vs BASE if given) whose land touches or overlaps any pad (via-in-pad check, hand assembly)"""
import sys, json
from shapely.geometry import Polygon, Point
G = json.load(open(sys.argv[1]))
old = set()
if len(sys.argv) > 2:
    old = {(round(v['x'], 3), round(v['y'], 3)) for v in json.load(open(sys.argv[2]))['vias']}
pads = []
for p in G['pads']:
    for L, pl in p['poly'].items():
        for r in pl:
            if len(r[0]) >= 3: pads.append((p['ref'] + '-' + p['num'], p['net'], Polygon(r[0]).buffer(0)))
n = 0
for v in G['vias']:
    if (round(v['x'], 3), round(v['y'], 3)) in old: continue
    c = Point(v['x'], v['y'])
    for k, net, g in pads:
        d = g.distance(c) - v['d'] / 2
        if d < 0.05:
            print('via %s (%.3f,%.3f) d%.2f touches pad %s [%s] gap %.3f' % (v['net'], v['x'], v['y'], v['d'], k, net, d)); n += 1
print('vias touching pads:', n)
