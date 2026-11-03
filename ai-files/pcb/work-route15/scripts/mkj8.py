#!/usr/bin/env python3
"""mkj8.py GEO OUT_JOBS OUT_PLAN BASE_PLAN|- SPEC... : hr7 job file. SPEC = NET:FROM[:RADIUS[:key=val,...]]  (FROM = REF-NUM or x,y,L)
Defaults (RT-8): to NET, neck_drc, fine_via, island_via, layers FBI, via_cost 1.2, max_exp 3e6, max_cells 4e6."""
import sys, json
geo, outj, outp, base = sys.argv[1:5]
jobs = []
for s in sys.argv[5:]:
    f = s.split(':')
    net = f[0]; fr = f[1]
    if ',' in fr:
        a = fr.split(','); fr = [float(a[0]), float(a[1]), a[2]]
    J = dict(net=net, **{'from': fr}, to='NET', tgt_radius=float(f[2]) if len(f) > 2 and f[2] else 30.0, neck_drc=True, fine_via=True,
             island_via=True, layers='FBI', via_cost=1.2, max_exp=3e6, max_cells=4000000, margin=4)
    if len(f) > 3:
        for kv in f[3].split(','):
            k, v = kv.split('=')
            try: v = json.loads(v)
            except Exception: pass
            J[k] = v
    jobs.append(J)
d = dict(geo=geo, out_plan=outp, jobs=jobs)
if base != '-': d['base_plan'] = base
json.dump(d, open(outj, 'w'), indent=0)
print(len(jobs), 'jobs ->', outj)
