#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_dedupe.py IN OUT : remove identical duplicate vias/tracks"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); seen = set(); dup = 0
for t in list(b.Tracks()):
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition(); k = ('v', t.GetNetname(), p.x, p.y)
    else:
        a, c = t.GetStart(), t.GetEnd(); e = sorted([(a.x, a.y), (c.x, c.y)]); k = ('t', t.GetNetname(), t.GetLayer(), tuple(e[0]), tuple(e[1]))
    if k in seen: b.Remove(t); dup += 1
    else: seen.add(k)
print('dup', dup); pcbnew.SaveBoard(sys.argv[2], b)
