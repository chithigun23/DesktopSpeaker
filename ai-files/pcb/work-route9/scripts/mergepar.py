#!/usr/bin/env python3
"""mergepar.py GEO BASEPLAN OUTPLAN LOG1.hrlog.json [LOG2 ...] [--clr 0.25] : merge independent hr8 results (each computed on the
same base) in the given order; a result is accepted only if none of its new copper comes closer than --clr (edge to edge) to new
copper of a different net accepted earlier, and passes the accept.py length policy. Prints accepted / conflicting / rejected."""
import sys, json, math, re
from shapely.geometry import LineString, Point
a = sys.argv
geo, base, outp = a[1:4]
logs = [x for x in a[4:] if x.endswith('.json')]
pre = set(x[1:] for x in logs if x.startswith('+')); logs = [x.lstrip('+') for x in logs]
clr = float(a[a.index('--clr') + 1]) if '--clr' in a else 0.25
G = json.load(open(geo)); cls = G['netclass']; pads = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in G['pads']}
SENS = re.compile(r'FB|COMP|ADC_INT|TS_SENSE|BATP|ILIM|VIN|XO|INL|INR|AUD_S')
def sens(n): return cls.get(n) in ('AUDIO', 'I2S_CLK', 'USB') or bool(SENS.search(n))
def omin(p, q): dx, dy = abs(p[0] - q[0]), abs(p[1] - q[1]); return max(dx, dy) + 0.41421356 * min(dx, dy)
plan = json.load(open(base)); plan.setdefault('seg_add', []); plan.setdefault('via_add', [])
acc = []   # (net, geom)
for lf in logs:
    for e in json.load(open(lf)):
        J = e['job']; net = J['net']
        if not e['ok']: print('FAIL     %-28s %s' % (net, J['from'])); continue
        r = e['res']; L = e['length']
        fa = pads[J['from']] if isinstance(J['from'], str) else J['from'][:2]
        tg = J.get('tgt_near'); end = r['segs'][-1]['b']
        m = omin(fa, end); lim = (1.5 * m + 1.0) if sens(net) else 3.5 * m
        if L > lim + 1e-6: print('REJ-LEN  %-28s %s  %.1f mm vs min %.1f (lim %.1f)' % (net, J['from'], L, m, lim)); continue
        gs = [LineString([s['a'], s['b']]).buffer(s['w'] / 2) for s in r['segs']]
        vz = r.get('vsz') or [(0.6, 0.3)] * len(r['vias'])
        gs += [Point(v).buffer(z[0] / 2) for v, z in zip(r['vias'], vz)]
        st = [p for p in (e.get('stitch') or []) if p]
        hit = [n for n, g in acc if n != net and any(g.distance(x) < clr for x in gs)] + \
              [n for n, g in acc if n != 'GND' and any(g.distance(Point(p).buffer(0.3)) < clr for p in st)]
        if lf in pre: hit = []
        if hit: print('CONFLICT %-28s %s  with %s' % (net, J['from'], sorted(set(hit)))); continue
        for s in r['segs']: plan['seg_add'].append([s['layer'], net, s['w'], s['a'][0], s['a'][1], s['b'][0], s['b'][1]])
        for v, z in zip(r['vias'], vz): plan['via_add'].append([net, v[0], v[1], z[0], z[1]])
        for p in st: plan['via_add'].append(['GND', p[0], p[1], 0.6, 0.3])
        acc += [(net, g) for g in gs] + [('GND', Point(p).buffer(0.3)) for p in st]
        print('ACCEPT   %-28s %s  %.1f mm (min %.1f, x%.2f), %d vias' % (net, J['from'], L, m, L / m if m else 0, len(r['vias'])))
json.dump(plan, open(outp, 'w'), indent=1)
