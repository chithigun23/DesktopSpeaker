#!/usr/bin/env python3
"""Final tidy: vias 0.6/0.4 -> 0.6/0.3 (annular), refill all zones, save. usage (flatpak): route_p0_final.py IN OUT"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA' and abs(t.GetWidth(pcbnew.F_Cu) - 600000) < 1000 and abs(t.GetDrillValue() - 400000) < 1000:
        t.SetDrill(300000); n += 1
print('via drill fixed', n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[2], b)
