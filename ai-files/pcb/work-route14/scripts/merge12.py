#!/usr/bin/env python3
"""merge12.py ROUTED.json POST.json OUT.json BOARD : router plan + hand post edits. POST keys: seg_add, via_add, seg_del, via_del
(VIA:x,y allowed), drop_add [[layer, x1, y1, x2, y2]] (remove router seg_add entries with these end points, 0.002 mm)."""
import sys, json, subprocess, os
r, p, o, b = sys.argv[1:5]
P = json.load(open(r)); Q = json.load(open(p))
def same(a, d): return a[0] == d[0] and abs(a[3] - d[1]) < 2e-3 and abs(a[4] - d[2]) < 2e-3 and abs(a[5] - d[3]) < 2e-3 and abs(a[6] - d[4]) < 2e-3
for d in Q.get('drop_add', []):
    n = len(P['seg_add']); P['seg_add'] = [a for a in P['seg_add'] if not same(a, d)]
    if len(P['seg_add']) != n - 1: sys.exit('ABORT drop_add %s removed %d' % (d, n - len(P['seg_add'])))
for d in Q.get('drop_via', []):
    n = len(P['via_add']); P['via_add'] = [v for v in P['via_add'] if not (abs(v[1] - d[0]) < 2e-3 and abs(v[2] - d[1]) < 2e-3)]
    if len(P['via_add']) != n - 1: sys.exit('ABORT drop_via %s' % d)
P['seg_add'] += Q.get('seg_add', []); P['via_add'] += Q.get('via_add', [])
P['seg_del'] = P.get('seg_del', []) + Q.get('seg_del', []); P['via_del'] = P.get('via_del', []) + Q.get('via_del', [])
P['seg_set'] = dict(P.get('seg_set', {}), **Q.get('seg_set', {})); P['fp_move'] = dict(P.get('fp_move', {}), **Q.get('fp_move', {}))
P['zone_pts'] = dict(P.get('zone_pts', {}), **Q.get('zone_pts', {}))
P.pop('via_del_xy', None); P.pop('via_set_xy', None)
json.dump(P, open(o, 'w'), indent=1)
subprocess.run(['python3', os.path.join(os.path.dirname(__file__), 'resolve.py'), b, o], check=True)
