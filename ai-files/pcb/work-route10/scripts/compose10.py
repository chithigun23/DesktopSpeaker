#!/usr/bin/env python3
"""compose10.py BASEPLAN GEO TAG OUT_JOBS k1,k2,... : RT-10 - one sequential hr10 job file: base plan (adds) + the rips of the
voidjobs results t/r_TAG_k.json, then the jobs t/j_TAG_k.json in the given order (each later job sees the earlier routes)."""
import sys, json
bp, geo, tag, out, ks = sys.argv[1:6]
P = json.load(open(bp)); P.setdefault('seg_del', [])
jobs = []
for k in ks.split(','):
    P['seg_del'] += json.load(open('t/r_%s_%s.json' % (tag, k)))['seg_del']
    jobs += json.load(open('t/j_%s_%s.json' % (tag, k)))['jobs']
json.dump(P, open(out.replace('.json', '_base.json'), 'w'), indent=1)
json.dump(dict(geo=geo, base_plan=out.replace('.json', '_base.json'), out_plan=out.replace('/j', '/p'), jobs=jobs), open(out, 'w'))
print(len(jobs), 'jobs,', len(P['seg_del']), 'rips')
