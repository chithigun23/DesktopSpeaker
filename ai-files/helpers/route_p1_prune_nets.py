#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_prune_nets.py IN NETS.json OUT : delete tracks/vias of the listed nets"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); nets = set(json.load(open(sys.argv[2])))
n = 0
for t in list(b.Tracks()):
    if t.GetNetname() in nets: b.Remove(t); n += 1
print('pruned', n); pcbnew.SaveBoard(sys.argv[3], b)
