#!/usr/bin/env python3
"""planplus.py PLAN OUT HRLOG [HRLOG...] [--skip NET:FROM,...] : PLAN plus the copper of every OK job of the hr8 logs."""
import sys, json
a = sys.argv; plan = json.load(open(a[1])); out = a[2]
skip = set(a[a.index('--skip') + 1].split(';')) if '--skip' in a else set()
logs = [x for x in a[3:] if x.endswith('.json')]
n = 0
for lf in logs:
    for e in json.load(open(lf)):
        J = e['job']; key = '%s:%s' % (J['net'], J['from'] if isinstance(J['from'], str) else ','.join(map(str, J['from'])))
        if not e['ok'] or key in skip: continue
        r = e['res']; n += 1
        for s in r['segs']: plan['seg_add'].append([s['layer'], J['net'], s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
        vz = r.get('vsz') or [(0.6, 0.3)] * len(r['vias'])
        for v, z in zip(r['vias'], vz): plan['via_add'].append([J['net'], v[0], v[1], z[0], z[1]])
        for p in e.get('stitch') or []:
            if p: plan['via_add'].append(['GND', p[0], p[1], 0.6, 0.3])
json.dump(plan, open(out, 'w'), indent=1)
print('added jobs', n, '-> segs', len(plan['seg_add']), 'vias', len(plan['via_add']))
