#!/usr/bin/env python3
"""net -> netclass map from a project's netclass patterns (first non-SIGNAL match wins). usage (flatpak pcbnew): route_p0_classes.py BOARD PRO OUT.json"""
import sys, json, fnmatch, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pats = json.load(open(sys.argv[2]))['net_settings']['netclass_patterns']
out = {}
for n in b.GetNetsByName().keys():
    n = str(n)
    if not n: continue
    got = 'SIGNAL'
    for p in pats:
        if p['pattern'] != '*' and fnmatch.fnmatchcase(n, p['pattern']): got = p['netclass']; break
    out[n] = got
json.dump(out, open(sys.argv[3], 'w'), indent=0)
import collections; print(collections.Counter(out.values()))
