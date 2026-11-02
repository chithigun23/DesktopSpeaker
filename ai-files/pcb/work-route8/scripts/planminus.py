#!/usr/bin/env python3
"""planminus.py PLAN HRLOG OUT NET:FROM [...] : copy of PLAN without the copper added by the listed hr8 jobs (from HRLOG)."""
import sys, json
plan = json.load(open(sys.argv[1])); log = json.load(open(sys.argv[2])); out = sys.argv[3]
kill = set(sys.argv[4:])
rs, rv = [], []
for e in log:
    J = e['job']; key = '%s:%s' % (J['net'], J['from'] if isinstance(J['from'], str) else ','.join(map(str, J['from'])))
    if key not in kill or not e['ok']: continue
    kill.discard(key)
    for s in e['res']['segs']: rs.append([s['layer'], J['net'], s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
    for v in e['res']['vias']: rv.append((J['net'], round(v[0], 4), round(v[1], 4)))
    for p in e.get('stitch') or []:
        if p: rv.append(('GND', round(p[0], 4), round(p[1], 4)))
n0 = len(plan['seg_add']), len(plan['via_add'])
for s in rs:
    m = [k for k, t in enumerate(plan['seg_add']) if t[0] == s[0] and t[1] == s[1] and all(abs(t[i] - s[i]) < 1e-6 for i in range(3, 7))]
    if m: plan['seg_add'].pop(m[0])
for v in rv:
    m = [k for k, t in enumerate(plan['via_add']) if t[0] == v[0] and abs(t[1] - v[1]) < 1e-4 and abs(t[2] - v[2]) < 1e-4]
    if m: plan['via_add'].pop(m[0])
json.dump(plan, open(out, 'w'), indent=1)
print('removed segs %d vias %d; not found jobs %s' % (n0[0] - len(plan['seg_add']), n0[1] - len(plan['via_add']), sorted(kill)))
