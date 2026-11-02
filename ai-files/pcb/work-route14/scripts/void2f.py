#!/usr/bin/env python3
"""void2f.py BOARD GEO OUTPLAN [NET ...|ALL] : via-to-via B.Cu chains of signal nets over In2 void are moved to F.Cu on the same polyline
when F.Cu is free along it (conservative class clearances, no F under IC packages other than U3, outside the BM83 module).
Writes an edit.py plan (seg_del + seg_add on F.Cu). Net classes AUDIO / I2S_CLK / USB are skipped (keep their reviewed geometry)."""
import sys, math, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep
D = R.load(sys.argv[1]); G = json.load(open(sys.argv[2])); out = sys.argv[3]; nets = sys.argv[4:]
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
NC = G['netclass']
def vl(t):
    ln = math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1']); n = max(1, int(ln / 0.4)); s = 0
    for i in range(n):
        u = (i + .5) / n; p = Point(t['x1'] + (t['x2'] - t['x1']) * u, t['y1'] + (t['y2'] - t['y1']) * u)
        if not in2g.contains(p) and not in2o.contains(p): s += ln / n
    return s
def poly(r):
    p = Polygon(r[0], [h for h in r[1:] if len(h) >= 3]); return p if p.is_valid else p.buffer(0)
CL = {'AUDIO': 0.55, 'I2S_CLK': 0.45, 'USB': 0.3, 'POWER_HI': 0.45, 'PVDD': 0.35, 'SPK_OUT': 0.35, 'SWITCH': 1.05, 'BOOT': 0.35}
icb = [poly(r) for ref, c in G['courtyard'].items() if (ref.startswith('U') and ref != 'U3') for r in c['poly'].get('F', [])]
ICB = prep(unary_union(icb)) if icb else None
K = lambda x, y: (round(x, 3), round(y, 3))
if nets == ['ALL']: nets = sorted({t['net'] for t in G['tracks'] if t['layer'] == 'B.Cu' and NC.get(t['net']) not in ('AUDIO', 'I2S_CLK', 'USB', 'GND', 'POWER_HI', 'PVDD', 'SPK_OUT', 'SWITCH', 'BOOT', 'PWR_5V', 'PWR_3V')})
P = dict(seg_del=[], seg_add=[]); tot = 0
Fobs_all = []
for t in G['tracks']:
    if t['layer'] == 'F.Cu': Fobs_all.append((t['net'], LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2 + CL.get(t['cls'], 0.25))))
for v in G['vias']: Fobs_all.append((v['net'], Point(v['x'], v['y']).buffer(v['d'] / 2 + CL.get(v['cls'], 0.25))))
for p in G['pads']:
    for r in p['poly'].get('F.Cu', []): Fobs_all.append((p['net'], poly(r).buffer(CL.get(NC.get(p['net']), 0.25))))
    if p['drill']: Fobs_all.append((p['net'], Point(p['x'], p['y']).buffer(max(p['drill']) / 2 + 0.3)))
for z in G['zones']:
    if z['net'] == 'GND': continue
    for r in z.get('fills', {}).get('F.Cu', []):
        if len(r[0]) >= 3: Fobs_all.append((z['net'], poly(r).buffer(0.45)))
for a in G['areas']:
    if a['name'].startswith('BM83') or 'ANTENNA' in a['name'] or a['name'] == 'BKO_BM83':
        for rings in a['outline']:
            g = poly(rings[0]) if isinstance(rings[0][0][0], list) else poly(rings); Fobs_all.append(('', g))
for net in nets:
    O = prep(unary_union([g for n, g in Fobs_all if n != net]))
    T = [t for t in G['tracks'] if t['net'] == net]
    vias = {K(v['x'], v['y']) for v in G['vias'] if v['net'] == net}
    adjB = collections.defaultdict(list); other = collections.Counter()
    for t in T:
        a, b = K(t['x1'], t['y1']), K(t['x2'], t['y2'])
        if t['layer'] == 'B.Cu': adjB[a].append((b, t)); adjB[b].append((a, t))
        else: other[a] += 1; other[b] += 1
    for p in G['pads']:
        if p['net'] == net: other[K(p['x'], p['y'])] += 1
    seen = set()
    for v in sorted(vias):
        for (nb, t) in adjB.get(v, []):
            if t['uuid'] in seen: continue
            chain = [t]; seen.add(t['uuid']); cur = nb; ok = True
            while cur not in vias:
                nxt = [(n2, t2) for (n2, t2) in adjB.get(cur, []) if t2['uuid'] not in seen]
                if len(nxt) != 1 or other[cur]: ok = False; break
                cur, t2 = nxt[0]; chain.append(t2); seen.add(t2['uuid'])
            if not ok: continue
            vv = sum(vl(c) for c in chain)
            if vv < 0.3: continue
            geo = [LineString([(c['x1'], c['y1']), (c['x2'], c['y2'])]).buffer(c['w'] / 2) for c in chain]
            free = all(not O.intersects(g) for g in geo) and not (ICB and any(ICB.intersects(g) for g in geo))
            print('%-28s %s -> %s void %.1f %s' % (net[-28:], v, cur, vv, 'MOVE' if free else 'blocked'))
            if free:
                tot += vv
                for c in chain:
                    P['seg_del'].append(c['uuid'][:8]); P['seg_add'].append(['F.Cu', net, c['w'], c['x1'], c['y1'], c['x2'], c['y2']])
json.dump(P, open(out, 'w'), indent=1); print('moved void %.1f mm, %d segments' % (tot, len(P['seg_del'])))
