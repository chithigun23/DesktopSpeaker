#!/usr/bin/env python3
"""bchains.py BOARD.kicad_pcb GEO NET [NET...] : B.Cu segment chains of each net whose two ends are vias (via-to-via B runs),
with their length over In2 void (r7 definition). Prints chain uuids, end vias, void mm."""
import sys, math, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
D = R.load(sys.argv[1]); G = json.load(open(sys.argv[2]))
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
def vl(t):
    ln = math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1']); n = max(1, int(ln / 0.4)); s = 0
    for i in range(n):
        u = (i + .5) / n; p = Point(t['x1'] + (t['x2'] - t['x1']) * u, t['y1'] + (t['y2'] - t['y1']) * u)
        if not in2g.contains(p) and not in2o.contains(p): s += ln / n
    return s
K = lambda x, y: (round(x, 3), round(y, 3))
for net in sys.argv[3:]:
    T = [t for t in G['tracks'] if t['net'] == net]
    vias = {K(v['x'], v['y']) for v in G['vias'] if v['net'] == net}
    padpts = [(p['x'], p['y']) for p in G['pads'] if p['net'] == net]
    deg = collections.Counter(); adjB = collections.defaultdict(list); other = collections.Counter()
    for t in T:
        a, b = K(t['x1'], t['y1']), K(t['x2'], t['y2'])
        if t['layer'] == 'B.Cu': adjB[a].append((b, t)); adjB[b].append((a, t))
        else: other[a] += 1; other[b] += 1
    seen = set()
    for v in vias:
        for (nb, t) in adjB.get(v, []):
            if t['uuid'] in seen: continue
            chain = [t]; seen.add(t['uuid']); cur = nb; ok = True
            while cur not in vias:
                nxt = [(n2, t2) for (n2, t2) in adjB.get(cur, []) if t2['uuid'] not in seen]
                if len(nxt) != 1 or other[cur]: ok = False; break
                cur, t2 = nxt[0]; chain.append(t2); seen.add(t2['uuid'])
            if not ok: continue
            L = sum(math.hypot(c['x2'] - c['x1'], c['y2'] - c['y1']) for c in chain); vv = sum(vl(c) for c in chain)
            if vv > 0.3: print('%-30s %s -> %s  len %.1f void %.1f  %s' % (net[-30:], v, cur, L, vv, ','.join(c['uuid'][:8] for c in chain)))
