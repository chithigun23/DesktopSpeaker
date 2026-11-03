#!/usr/bin/env python3
"""gen_jobs.py DRC.json GEO.json OUT_JOBS.json OUT_PLAN.json [--skip net,...] : hand-route jobs for the open connections of a board,
in importance order (power-adjacent control, clocks/I2S/CC, analog audio, control). Inherited power items (3V_AO, GND, LDO_3V3)
and pin stacks (same ref and pad number) are skipped."""
import json, sys, re, math
drc, geo, out, plan = sys.argv[1:5]
skip = set(sys.argv[sys.argv.index('--skip') + 1].split(',')) if '--skip' in sys.argv else set()
D = json.load(open(drc)); G = json.load(open(geo))
cls = G['netclass']
PWR = re.compile(r'CHG_|PD_|U11-|Q10|U4-|ILIM|CE_N|TS_SENSE|BATP|U25-|5V_LOGIC_EN|BT_PWR_EN|U15-|U14-|U12-|U20-|AMP_BOOST|BT_FORCE|PROG|QON|R18-|GAUGE')
def rank(net):
    c = cls.get(net, 'Default')
    if PWR.search(net): return 0
    if c in ('I2S_CLK', 'USB') or 'XO' in net or 'CC' in net: return 1
    if c == 'AUDIO' or net in ('/AUD_SDA', '/AUD_SCL'): return 2
    return 3
jobs = []
for u in D['unconnected_items']:
    it = u['items']
    m = [re.search(r'\[(.*?)\]', i['description']).group(1) for i in it]
    net = m[0]
    if net in ('/3V_AO', 'GND', '/USB_PD/LDO_3V3') or net in skip: continue
    ends = []
    for i in it:
        d = i['description']
        mp = re.match(r'(?:PTH )?[Pp]ad (\S+) \[.*\] of (\S+)', d)
        ends.append(('%s-%s' % (mp.group(2), mp.group(1)), (i['pos']['x'], i['pos']['y'])) if mp else (None, (i['pos']['x'], i['pos']['y'])))
    if ends[0][0] and ends[0][0] == ends[1][0]: continue
    dist = math.dist(ends[0][1], ends[1][1])
    pads = [e for e in ends if e[0]]
    if not pads: continue
    a = pads[0][0]
    j = dict(net=net, **{'from': a}, neck_drc=True, margin=3, max_exp=1.5e6, tgt_radius=dist + 3, _rank=rank(net), _d=dist)
    if a.startswith('U11-'): j.update(neck_val=0.15, wn=0.15)
    j['to'] = pads[1][0] if len(pads) == 2 else 'NET'
    if j['to'] != 'NET': j['tgt_keys'] = [j['to']]
    jobs.append(j)
jobs.sort(key=lambda j: (j['_rank'], j['_d']))
json.dump(dict(geo=geo, out_plan=plan, jobs=jobs), open(out, 'w'), indent=0)
print(len(jobs), 'jobs', [sum(1 for j in jobs if j['_rank'] == r) for r in range(4)])
