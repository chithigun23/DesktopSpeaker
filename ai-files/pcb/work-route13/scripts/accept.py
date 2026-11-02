#!/usr/bin/env python3
"""accept.py GEO OUTPLAN BASEPLAN LOG1.hrlog.json [LOG2 ...] [--drop net,...] : merge hr7 results into one plan by the
RT-7 length policy: sensitive nets (AUDIO, I2S_CLK, USB classes, AUD I2C, FB/COMP/ADC_INT/TS/BATP/ILIM/VIN/XO/INL/INR names)
<= 1.5 x octilinear minimum + 1 mm; slow control/status nets <= 3.5 x. Length = track length + 0 per via; minimum between
the start point and the reached end (pad centres). Prints a table."""
import json, sys, math, re
geo, outp, base = sys.argv[1:4]
logs = [x for x in sys.argv[4:] if x.endswith('.json') and not x.startswith('--')]
drop = set(sys.argv[sys.argv.index('--drop') + 1].split(',')) if '--drop' in sys.argv else set()
G = json.load(open(geo)); cls = G['netclass']; pads = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in G['pads']}
SENS = re.compile(r'FB|COMP|ADC_INT|TS_SENSE|BATP|ILIM|VIN|XO|INL|INR|AUD_S')
def sens(net): return cls.get(net) in ('AUDIO', 'I2S_CLK', 'USB') or bool(SENS.search(net))
def omin(a, b): dx, dy = abs(a[0]-b[0]), abs(a[1]-b[1]); return max(dx, dy) + 0.41421356 * min(dx, dy)
plan = json.load(open(base)) if base != '-' else {}
for k in ('seg_add', 'via_add'): plan.setdefault(k, [])
rows = []
for lf in logs:
    for e in json.load(open(lf)):
        J = e['job']; net = J['net']
        if not e['ok']: rows.append((net, str(J['from']), str(J['to']), 'FAIL', '', '')); continue
        r = e['res']; segs = r['segs']; L = e['length']
        a = pads[J['from']] if isinstance(J['from'], str) else J['from'][:2]
        end = segs[-1]['b']
        b = pads[J['to']] if isinstance(J['to'], str) and J['to'] != 'NET' else end
        m = omin(a, b); ratio = L / m if m > 0 else 1
        lim = (1.5 * m + 1.0) if sens(net) else 3.5 * m
        ok = L <= lim and net not in drop
        rows.append((net, str(J['from']), str(J['to']), 'ACC' if ok else 'REJ', '%.2f/%.2f' % (L, m), '%.2f %s' % (ratio, 'sens' if sens(net) else 'slow')))
        if ok:
            for s in segs: plan['seg_add'].append([s['layer'], net, s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
            vz = r.get('vsz') or [(0.6, 0.3)] * len(r['vias'])
            for (x, y), vs in zip(r['vias'], vz): plan['via_add'].append([net, x, y, vs[0], vs[1]])
            for p in e.get('stitch') or []:
                if p: plan['via_add'].append(['GND', p[0], p[1], 0.6, 0.3])
for r in rows: print('%-34s %-14s %-10s %s %s %s' % r)
json.dump(plan, open(outp, 'w'), indent=1)
print('accepted', sum(1 for r in rows if r[3] == 'ACC'), 'of', len(rows))
