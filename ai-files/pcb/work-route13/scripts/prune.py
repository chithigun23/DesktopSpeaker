#!/usr/bin/env python3
"""prune.py BOARD.kicad_pcb DRC.json OUTPLAN : edit.py plan deleting the copper DRC reports as dangling (track_dangling: the
segment whose free end is at the reported position; via_dangling: the via). A dangling item leads nowhere, so removing it
cannot break a connection; repeat until DRC reports none."""
import sys, os, json, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items
board, drc, outp = sys.argv[1:4]
IT = items(board, read(board)); D = json.load(open(drc))
plan = dict(seg_del=[], via_del=[], via_del_xy=[])
for v in D['violations']:
    if v['type'] not in ('track_dangling', 'via_dangling'): continue
    it = v['items'][0]; x, y = it['pos']['x'], it['pos']['y']
    net = re.search(r'\[(.*?)\]', it['description']).group(1)
    if v['type'] == 'via_dangling':
        m = [d for d in IT if d['kind'] == 'via' and d.get('net') == net and math.dist(d['at'], (x, y)) < 0.005]
        if len(m) == 1 and m[0]['uuid'] not in plan['via_del']: plan['via_del'].append(m[0]['uuid']); plan['via_del_xy'].append(list(m[0]['at']))
    else:
        L = re.search(r'on (\S+\.Cu)', it['description']).group(1)
        m = [d for d in IT if d['kind'] == 'segment' and d.get('net') == net and d['layer'] == L and
             (math.dist(d['start'], (x, y)) < 0.005 or math.dist(d['end'], (x, y)) < 0.005)]
        if len(m) == 1 and m[0]['uuid'] not in plan['seg_del']: plan['seg_del'].append(m[0]['uuid'])
        elif len(m) != 1: print('ambiguous', net, x, y, len(m))
json.dump(plan, open(outp, 'w'), indent=1)
print('prune', {k: len(v) for k, v in plan.items()})
