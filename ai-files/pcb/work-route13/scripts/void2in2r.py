#!/usr/bin/env python3
"""void2in2.py BOARD GEO OUTPLAN NET [NET...] : via-to-via B.Cu chains of the listed slow nets (rule 11 / 21, In2 allowed) that lie over
In2 void are moved to In2.Cu on the same polyline when the In2 layer is free along it (other-net In2 tracks + 0.3, other-net vias / In2 pads
+ 0.3, non-GND In2 zone fills + 0.4; GND pour refills). Writes an edit.py plan (seg_del + seg_add on In2, width >= 0.25)."""
import sys, math, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep
D = R.load(sys.argv[1]); G = json.load(open(sys.argv[2])); out = sys.argv[3]; nets = sys.argv[4:]
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
def vl(t):
    ln = math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1']); n = max(1, int(ln / 0.4)); s = 0
    for i in range(n):
        u = (i + .5) / n; p = Point(t['x1'] + (t['x2'] - t['x1']) * u, t['y1'] + (t['y2'] - t['y1']) * u)
        if not in2g.contains(p) and not in2o.contains(p): s += ln / n
    return s
def poly(r):
    p = Polygon(r[0], [h for h in r[1:] if len(h) >= 3]); return p if p.is_valid else p.buffer(0)
K = lambda x, y: (round(x, 3), round(y, 3))
P = dict(seg_del=[], seg_add=[]); tot = 0
for net in nets:
    obs = []
    for t in G['tracks']:
        if t['layer'] == 'In2.Cu' and t['net'] != net: obs.append(LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2 + 0.22))
    for v in G['vias']:
        if v['net'] != net: obs.append(Point(v['x'], v['y']).buffer(v['d'] / 2 + 0.22))
    for p in G['pads']:
        if p['net'] != net and 'In2.Cu' in p['poly']:
            for r in p['poly']['In2.Cu']: obs.append(poly(r).buffer(0.22))
        if p['drill'] and p['net'] != net: obs.append(Point(p['x'], p['y']).buffer(max(p['drill']) / 2 + 0.35))
    for z in G['zones']:
        if z['net'] in ('GND', net): continue
        for r in z.get('fills', {}).get('In2.Cu', []):
            if len(r[0]) >= 3: obs.append(poly(r).buffer(0.33))
    O = prep(unary_union(obs))
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
            ids = {c['uuid'] for c in chain}
            Bg = [LineString([(t2['x1'], t2['y1']), (t2['x2'], t2['y2'])]).buffer(t2['w'] / 2) for t2 in T if t2['layer'] == 'B.Cu' and t2['uuid'] not in ids]
            Bg += [poly(r) for p in G['pads'] if p['net'] == net for r in p['poly'].get('B.Cu', [])]
            ends = [Point(*v).buffer(0.35), Point(*cur).buffer(0.35)]
            touch = False
            for c in chain:
                g = LineString([(c['x1'], c['y1']), (c['x2'], c['y2'])]).buffer(c['w'] / 2).difference(ends[0]).difference(ends[1])
                if any(g.intersects(b) for b in Bg): touch = True
            Fg = [LineString([(t2['x1'], t2['y1']), (t2['x2'], t2['y2'])]).buffer(t2['w'] / 2) for t2 in T if t2['layer'] == 'F.Cu']
            Fg += [poly(r) for p in G['pads'] if p['net'] == net for r in p['poly'].get('F.Cu', [])]
            fend = all(any(e.intersects(f) for f in Fg) for e in ends)
            if touch or not fend:
                print('%-28s %s -> %s void %.1f skip (%s)' % (net[-28:], v, cur, vv, 'T-branch' if touch else 'end via has no F link')); continue
            free = all(not O.intersects(LineString([(c['x1'], c['y1']), (c['x2'], c['y2'])]).buffer(max(0.25, c['w']) / 2)) for c in chain)
            print('%-28s %s -> %s void %.1f %s' % (net[-28:], v, cur, vv, 'MOVE' if free else 'blocked'))
            if free:
                tot += vv
                for c in chain:
                    P['seg_del'].append(c['uuid'][:8]); P['seg_add'].append(['In2.Cu', net, max(0.25, c['w']), c['x1'], c['y1'], c['x2'], c['y2']])
json.dump(P, open(out, 'w'), indent=1); print('moved void %.1f mm, %d segments' % (tot, len(P['seg_del'])))
