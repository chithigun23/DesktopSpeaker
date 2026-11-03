#!/usr/bin/env python3
"""inbox.py GEO X0 Y0 X1 Y1 [layers] : tracks / vias / pads in a box (text)"""
import sys, json
D = json.load(open(sys.argv[1])); x0, y0, x1, y1 = map(float, sys.argv[2:6]); lay = sys.argv[6].split(',') if len(sys.argv) > 6 else ['F', 'B', 'In2']
def ib(x, y): return x0 <= x <= x1 and y0 <= y <= y1
for t in D['tracks']:
    seg_in = ib(t['x1'], t['y1']) or ib(t['x2'], t['y2']) or any(ib(t['x1'] + (t['x2'] - t['x1']) * k / 40, t['y1'] + (t['y2'] - t['y1']) * k / 40) for k in range(41))
    if t['layer'].split('.')[0] in lay and seg_in:
        print('T %-5s w%.2f (%.3f,%.3f)-(%.3f,%.3f) %s %s' % (t['layer'][:3], t['w'], t['x1'], t['y1'], t['x2'], t['y2'], t['net'][-22:], t['uuid'][:8]))
for v in D['vias']:
    if ib(v['x'], v['y']): print('V       d%.2f (%.3f,%.3f) %s' % (v['d'], v['x'], v['y'], v['net'][-22:]))
for p in D['pads']:
    if ib(p['x'], p['y']): print('P %s-%s (%.3f,%.3f) %s %s' % (p['ref'], p['num'], p['x'], p['y'], p['net'][-22:], ','.join(p['poly'].keys())))
