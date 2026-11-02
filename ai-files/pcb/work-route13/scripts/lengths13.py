#!/usr/bin/env python3
"""lengths13.py CHECK.json NET... : whole-net length / vias / octilinear ratio from route_oct_check JSON"""
import sys, json
d = json.load(open(sys.argv[1]))['nets']
print('| net | mm | ratio | vias |'); print('|---|---|---|---|')
for n in sys.argv[2:]:
    x = d.get(n)
    if x: print('| %s | %.1f | %s | %d |' % (n, x['len'], ('%.2f' % x['ratio']) if x.get('ratio') else '-', x['vias']))
