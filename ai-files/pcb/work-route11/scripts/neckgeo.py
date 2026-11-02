#!/usr/bin/env python3
"""neckgeo.py IN.geo.json OUT.geo.json NAME=mm,... : ROUTER-ONLY model: NECK_<ref> areas grown by mm (approximates the DRC behaviour that
a segment touching a neck area gets the 0.2 mm neck clearance). DRC on the real board stays the gate."""
import sys, json
from shapely.geometry import Polygon
G = json.load(open(sys.argv[1])); grow = {k: float(v) for k, v in (x.split('=') for x in sys.argv[3].split(','))}
for a in G['areas']:
    if a['name'] in grow:
        P = Polygon(a['outline'][0][0]).buffer(grow[a['name']], join_style=2)
        a['outline'] = [[list(map(list, P.exterior.coords))]]
json.dump(G, open(sys.argv[2], 'w'))
