#!/usr/bin/env python3
"""mkjobs.py DRC GEO BASEPLAN PREFIX : open connections -> hr7 job files by region (W, N, S local; L long), FBI layers."""
import json, sys, re, math, subprocess
drc, geo, base, pre = sys.argv[1:5]
skip = set(sys.argv[sys.argv.index('--skip') + 1].split(',')) if '--skip' in sys.argv else set()
subprocess.run(['python3', 'scripts/gen_jobs.py', drc, geo, pre + '_all.json', pre + '_x.json'], check=True)
J = json.load(open(pre + '_all.json'))
G = json.load(open(geo)); pads = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in G['pads']}
D = json.load(open(drc))
grp = {'W': [], 'N': [], 'S': [], 'L': []}
for j in J['jobs']:
    if j['net'] in skip: continue
    j['layers'] = 'FBI'; j['max_cells'] = 4000000; j['max_exp'] = 2.5e6
    j['margin'] = 4 if j['_d'] < 15 else 6
    j['tgt_radius'] = j['_d'] + 3
    a = pads[j['from']]; b = pads.get(j['to']) if j['to'] != 'NET' else None
    if j['_d'] > 22: grp['L'].append(j); continue
    x, y = a
    g = 'W' if x < 140 else ('N' if y < 100 else 'S')
    grp[g].append(j)
for g, js in grp.items():
    json.dump(dict(geo=geo, out_plan='%s_%s_plan.json' % (pre, g), base_plan=base, jobs=js), open('%s_%s.json' % (pre, g), 'w'), indent=0)
    print(g, len(js), [j['net'].split('/')[-1] for j in js])
