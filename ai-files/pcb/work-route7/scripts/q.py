#!/usr/bin/env python3
"""q.py GEO.json X0 Y0 X1 Y1 [--zones] : list pads, tracks, vias (and zones with fill in the box) inside a box."""
import sys, json
D = json.load(open(sys.argv[1])); X0, Y0, X1, Y1 = map(float, sys.argv[2:6]); Z = '--zones' in sys.argv
inb = lambda x, y: X0 <= x <= X1 and Y0 <= y <= Y1
for p in D['pads']:
    if inb(p['x'], p['y']):
        print('PAD %s-%s %s [%s] (%.3f,%.3f) %.3fx%.3f rot%.0f %s %s' % (p['ref'], p['num'], p['net'], p['cls'], p['x'], p['y'], p['sx'], p['sy'], p['rot'], p['attr'], ','.join(p['layers'])))
for t in D['tracks']:
    if inb(t['x1'], t['y1']) or inb(t['x2'], t['y2']):
        print('TRK %s %s [%s] w%.3f (%.4f,%.4f)-(%.4f,%.4f) %s' % (t['layer'], t['net'], t['cls'], t['w'], t['x1'], t['y1'], t['x2'], t['y2'], t['uuid'][:8]))
for v in D['vias']:
    if inb(v['x'], v['y']):
        print('VIA %s [%s] (%.4f,%.4f) %.2f/%.2f' % (v['net'], v['cls'], v['x'], v['y'], v['d'], v['drill']))
if Z:
    for z in D['zones']:
        for L, pls in z['fills'].items():
            for pl in pls:
                xs = [x for x, y in pl[0]]; ys = [y for x, y in pl[0]]
                if min(xs) <= X1 and max(xs) >= X0 and min(ys) <= Y1 and max(ys) >= Y0:
                    print('ZONE %s %s %s td=%s bbox(%.2f,%.2f,%.2f,%.2f)' % (z['name'], z['net'], L, z['teardrop'], min(xs), min(ys), max(xs), max(ys)))
                    break
