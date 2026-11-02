#!/usr/bin/env python3
"""mkjobs12.py GEO BASEPLAN OUTJOBS SPEC.py : job file from a python list JOBS = [(net, from, to, layers, {opts})] in SPEC"""
import sys, json
geo, base, out, spec = sys.argv[1:5]
C = dict(neck_drc=True, fine_via=True, via_cost=2.0, max_exp=4e6, max_cells=8000000, margin=3.0, run=0.75, zone_soft=0.2)
ns = {}; exec(open(spec).read(), ns)
J_ = []
for net, a, b, lay, k in ns['JOBS']:
    j = dict(C); j.update(net=net, layers=lay); j['from'] = a
    if isinstance(b, list) and len(b) == 3 and isinstance(b[0], (int, float)):
        j['to'] = 'NET'; j['tgt_near'] = b; j['tgt_radius'] = 300.0
    else: j['to'] = b
    j.update(k); J_.append(j)
json.dump(dict(geo=geo, base_plan=base, out_plan=out.replace('/j', '/p'), jobs=J_), open(out, 'w'), indent=1)
print(len(J_), 'jobs')
