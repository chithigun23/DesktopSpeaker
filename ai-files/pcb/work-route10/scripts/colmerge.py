#!/usr/bin/env python3
"""colmerge.py BOARD.kicad_pcb NETFILE OUTPLAN : plan that merges colinear same-net/layer/width segment pairs whose shared end
touches no other copper item (no via, no third segment, no pad). Only nets in NETFILE."""
import sys, json, math, collections
sys.path.insert(0, 'scripts')
from pcbtext import items
from fplib import fps
brd, nf, outp = sys.argv[1:4]
nets = {l.split()[1] for l in open(nf) if l.strip() and not l.startswith('#')}
IT = items(brd)
segs = [d for d in IT if d['kind'] == 'segment' and d['net'] in nets]
vias = [d['at'] for d in IT if d['kind'] == 'via']
pos, pad = fps(brd)[:2]
r = lambda p: (round(p[0], 4), round(p[1], 4))
ends = collections.defaultdict(list)
for s in segs:
    for k in ('start', 'end'): ends[(s['net'], s['layer'], r(s[k]))].append(s)
allends = collections.Counter()
for d in IT:
    if d['kind'] == 'segment':
        for k in ('start', 'end'): allends[(d['layer'], r(d[k]))] += 1
plan = dict(seg_del=[], seg_add=[]); used = set()
for (net, L, p), lst in ends.items():
    if len(lst) != 2 or allends[(L, p)] != 2: continue
    a, b = lst
    if a['uuid'] in used or b['uuid'] in used or abs(a['width'] - b['width']) > 1e-6: continue
    if any(math.dist(v, p) < 0.35 for v in vias): continue
    oa = r(a['end']) if r(a['start']) == p else r(a['start'])
    ob = r(b['end']) if r(b['start']) == p else r(b['start'])
    v1 = (p[0] - oa[0], p[1] - oa[1]); v2 = (ob[0] - p[0], ob[1] - p[1])
    if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 1e-6 or v1[0] * v2[0] + v1[1] * v2[1] <= 0: continue
    used |= {a['uuid'], b['uuid']}
    plan['seg_del'] += [a['uuid'], b['uuid']]; plan['seg_add'].append([L, net, a['width'], *oa, *ob])
    print('merge', net, L, oa, p, ob)
json.dump(plan, open(outp, 'w'), indent=1); print(len(plan['seg_add']), 'merges')
