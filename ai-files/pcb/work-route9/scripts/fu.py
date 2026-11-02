#!/usr/bin/env python3
"""fu.py BOARD.kicad_pcb NET X0 Y0 X1 Y1 : list segment/arc/via uuids of NET (substring match, '*' = all) with an end
point / centre inside the box (RT-9 helper, plain python3)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import items
b, net = sys.argv[1:3]; x0, y0, x1, y1 = map(float, sys.argv[3:7])
inb = lambda p: p and x0 <= p[0] <= x1 and y0 <= p[1] <= y1
for d in items(b, kinds=('segment', 'arc', 'via')):
    n = d.get('net', '')
    if net != '*' and net not in n: continue
    if d['kind'] == 'via':
        if inb(d['at']): print('via %s %s (%.4f,%.4f) %.2f/%.2f' % (d['uuid'], n, *d['at'], d['size'], d['drill']))
    elif inb(d['start']) or inb(d['end']):
        print('%s %s %s %s w%.3f (%.4f,%.4f)-(%.4f,%.4f)' % (d['kind'][:3], d['uuid'], n, d['layer'], d['width'], *d['start'], *d['end']))
