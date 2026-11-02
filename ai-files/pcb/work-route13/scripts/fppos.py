#!/usr/bin/env python3
"""fppos.py BOARD [REF ...] : footprint positions (x, y, rot, layer) from the board text"""
import re, sys, json
s = open(sys.argv[1]).read()
pos = {}
for m in re.finditer(r'\n\t\(footprint "([^"]+)"\n(.*?)\n\t\)', s, re.S):
    b = m.group(2)
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
    ref = re.search(r'\(property "Reference" "([^"]+)"', b)
    lay = re.search(r'\n\t\t\(layer "([^"]+)"\)', b)
    if not (at and ref): continue
    pos[ref.group(1)] = (float(at.group(1)), float(at.group(2)), float(at.group(3) or 0), lay.group(1) if lay else '?', m.group(1).split(':')[-1][:28])
if len(sys.argv) > 2:
    for r in sys.argv[2:]: print(r, pos.get(r))
else: print(json.dumps(pos))
