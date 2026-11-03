#!/usr/bin/env python3
"""segq.py BOARD [--uuid U,..] [--net NET] [--box x0,y0,x1,y1] [--layer L] : list segments/vias (text-level)"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
ap = argparse.ArgumentParser(); ap.add_argument('b'); ap.add_argument('--uuid'); ap.add_argument('--net'); ap.add_argument('--box'); ap.add_argument('--layer'); ap.add_argument('--vias', action='store_true')
a = ap.parse_args()
IT = items(a.b, read(a.b))
bx = list(map(float, a.box.split(','))) if a.box else None
us = a.uuid.split(',') if a.uuid else None
def inb(p): return bx is None or (bx[0] <= p[0] <= bx[2] and bx[1] <= p[1] <= bx[3])
for d in IT:
    if d['kind'] not in ('segment', 'via', 'arc'): continue
    if us and not any(d.get('uuid', '').startswith(u) for u in us): continue
    if a.net and d.get('net') != a.net: continue
    if a.layer and d.get('layer') != a.layer: continue
    if d['kind'] == 'via':
        if not inb(d['at']): continue
        print('via', d['uuid'][:8], d['net'], d['at'], d['size'], d['drill'])
    else:
        if not (inb(d['start']) or inb(d['end'])): continue
        print(d['kind'], d['uuid'][:8], d['net'], d['layer'], d['width'], d['start'], d['end'])
