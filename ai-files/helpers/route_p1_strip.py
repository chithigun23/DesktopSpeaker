#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_strip.py IN OUT : remove every track and via (zones kept), save"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for t in list(b.Tracks()): b.Remove(t); n += 1
print('removed', n); pcbnew.SaveBoard(sys.argv[2], b)
