#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_netinfo.py BOARD OUT.json : {net: {"pads":[[x,y,ref,num],...]}} in mm (excluding GND)"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); out = {}
for f in b.GetFootprints():
    for p in f.Pads():
        n = p.GetNetname()
        if not n: continue
        q = p.GetPosition(); out.setdefault(n, []).append([q.x/1e6, q.y/1e6, f.GetReference(), str(p.GetNumber())])
json.dump(out, open(sys.argv[2], 'w'))
