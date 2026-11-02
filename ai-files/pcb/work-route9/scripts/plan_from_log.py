"""plan_from_log.py HRLOG.json OUT_PLAN.json [--drop net:from,...] : rebuild an edit plan from hr.py results, dropping listed jobs"""
import json, sys
log = json.load(open(sys.argv[1])); drop = set(sys.argv[sys.argv.index('--drop') + 1].split(',')) if '--drop' in sys.argv else set()
plan = dict(seg_add=[], via_add=[]); kept = 0
for e in log:
    if not e['ok']: continue
    J = e['job']
    if '%s:%s' % (J['net'], J['from']) in drop: continue
    kept += 1
    for s in e['res']['segs']: plan['seg_add'].append([s['layer'], J['net'], s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
    vs = (0.45, 0.2) if J.get('fine_via') else (0.6, 0.3)
    for x, y in e['res']['vias']: plan['via_add'].append([J['net'], x, y, vs[0], vs[1]])
    for p in e.get('stitch') or []:
        if p: plan['via_add'].append(['GND', float(p[0]), float(p[1]), 0.6, 0.3])
json.dump(plan, open(sys.argv[2], 'w'), indent=1); print('kept', kept, {k: len(v) for k, v in plan.items()})
