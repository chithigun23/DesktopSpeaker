#!/usr/bin/env python3
"""fix8.py ALLJOBS.json BASEPLAN OUTJOBS OUTPLAN ORDER [--extra JSON] : re-run a subset of U3 jobs (pins in ORDER, comma list of
pin numbers or job keys NET@FROM) on top of BASEPLAN, with exit-lane blocks/no-via boxes of the pins later in ORDER (LB 1.0, EXT 0.8).
--extra: a JSON list of extra hr8 jobs appended at the end."""
import sys, json
a = sys.argv
allj, base, outj, outp, order = a[1:6]
A = json.load(open(allj)); D = json.load(open(A['geo'])); pc = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in D['pads']}
CX, CY, TIP, LB, EXT = 128.0, 76.5, 5.67 + 0.775, 1.0, 0.8
def lane(p):
    x, y = pc[p]; dx, dy = x - CX, y - CY
    if abs(dx) > 5:
        n = 1 if dx > 0 else -1; xa, xb = sorted([CX + n * TIP, CX + n * (TIP + LB)]); return [xa, y - 0.15, xb, y + 0.15]
    n = 1 if dy > 0 else -1; ya, yb = sorted([CY + n * TIP, CY + n * (TIP + LB)]); return [x - 0.15, ya, x + 0.15, yb]
def vbox(p):
    x, y = pc[p]; dx, dy = x - CX, y - CY; L = LB + EXT
    if abs(dx) > 5:
        n = 1 if dx > 0 else -1; xa, xb = sorted([CX + n * TIP, CX + n * (TIP + L)]); return [xa - 0.45, y - 0.6, xb + 0.45, y + 0.6]
    n = 1 if dy > 0 else -1; ya, yb = sorted([CY + n * TIP, CY + n * (TIP + L)]); return [x - 0.6, ya - 0.45, x + 0.6, yb + 0.45]
LONG = ['U3-25', 'U3-29', 'U3-47', 'U3-42', 'U3-38', 'U3-36', 'U3-51', 'U3-24', 'U3-16', 'U3-13']
keys = order.split(',')
sel = []
for k in keys:
    if '@' in k:
        net, fr = k.split('@'); m = [j for j in A['jobs'] if j['net'] == net and str(j['from']) == fr]
    else:
        m = [j for j in A['jobs'] if j['from'] == 'U3-' + k]
    if not m: sys.exit('no job ' + k)
    sel.append(dict(m[0]))
pins = [j['from'] for j in sel if isinstance(j['from'], str) and j['from'].startswith('U3-')]
for k, j in enumerate(sel):
    later = [p for p in pins[pins.index(j['from']) + 1:]] if j['from'] in pins else []
    later = [p for p in later if not any(o['from'] == p and o['net'] == j['net'] for o in sel)]
    if '--long' in a: later += [p for p in LONG if p not in later and p != j['from']]
    j['block'] = [lane(p) + ['F.Cu'] for p in later]; j['noviabox'] = [vbox(p) for p in later]
if '--extra' in a: sel += json.load(open(a[a.index('--extra') + 1]))
json.dump(dict(geo=A['geo'], base_plan=base, out_plan=outp, jobs=sel), open(outj, 'w'), indent=0)
print(len(sel), 'jobs', [j['from'] for j in sel])
