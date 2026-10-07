#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_dedupe.py IN OUT : remove identical duplicate vias/tracks"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); seen = set(); dup = 0
for t in list(b.Tracks()):
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition(); k = ("v", t.GetNetname(), round(p.x / 1e4), round(p.y / 1e4))
    else:
        a, c = t.GetStart(), t.GetEnd(); e = sorted([(round(a.x / 1e4), round(a.y / 1e4)), (round(c.x / 1e4), round(c.y / 1e4))]); k = ('t', t.GetNetname(), t.GetLayer(), tuple(e[0]), tuple(e[1]))
    if k in seen: b.Remove(t); dup += 1
    else: seen.add(k)
print('dup', dup); pcbnew.SaveBoard(sys.argv[2], b)
