#!/usr/bin/env python3
"""resolve.py BOARD PLAN.json : replace 'VIA:x,y' keys in via_del / via_set by the via uuid at (x, y) (0.002 mm); checks seg_del keys exist."""
import sys, json, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import read, items
b, pf = sys.argv[1:3]
IT = items(b, read(b)); P = json.load(open(pf))
V = [d for d in IT if d['kind'] == 'via']
def res(k):
    if not k.startswith('VIA:'): return k
    x, y = map(float, k[4:].split(','))
    m = [d for d in V if math.hypot(d['at'][0] - x, d['at'][1] - y) < 0.002]
    if len(m) != 1: sys.exit('ABORT via %s matches %d' % (k, len(m)))
    return m[0]['uuid']
P['via_del'] = [res(k) for k in P.get('via_del', [])]
P['via_set'] = {res(k): v for k, v in P.get('via_set', {}).items()}
S = [d for d in IT if d['kind'] == 'segment']
for k in P.get('seg_del', []) + list(P.get('seg_set', {}).keys()):
    n = sum(1 for d in S if d['uuid'].startswith(k))
    if n != 1: sys.exit('ABORT seg %s matches %d' % (k, n))
json.dump(P, open(pf, 'w'), indent=1); print('resolved', len(P['via_del']), 'via_del', len(P.get('seg_del', [])), 'seg_del')
