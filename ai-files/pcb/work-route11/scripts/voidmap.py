#!/usr/bin/env python3
"""voidmap.py BOARD.kicad_pcb [--top N] : RT-10 helper. B.Cu signal length over In2 void (r7_metrics definition) per net and per
contiguous run, with the In2 copper that makes the void (nearest In2 track / via antipad / island gap)."""
import sys, math, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point, LineString
from shapely.prepared import prep
D = R.load(sys.argv[1]); top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 40
in2g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); in2o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
i2 = [s for s in D['segs'] if s['l'] == 'In2.Cu' and s['net'] != 'GND']
pernet = collections.defaultdict(float); runs = []
for s in D['segs']:
    if not R.sig(s) or s['l'] != 'B.Cu': continue
    ln = math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']); n = max(1, int(ln / 0.4)); cur = None
    for i in range(n):
        t = (i + .5) / n; x = s['x1'] + (s['x2'] - s['x1']) * t; y = s['y1'] + (s['y2'] - s['y1']) * t; p = Point(x, y); d = ln / n
        v = not in2g.contains(p) and not in2o.contains(p)
        if v:
            pernet[s['net']] += d
            if cur is None: cur = [x, y, x, y, 0.0]; runs.append((s['net'], cur))
            cur[2], cur[3] = x, y; cur[4] += d
        else: cur = None
tot = sum(pernet.values()); print('B over In2 void total %.1f' % tot)
for n, v in sorted(pernet.items(), key=lambda kv: -kv[1])[:top]: print('  %-40s %.1f' % (n, v))
def cause(x, y):
    p = Point(x, y); best = None
    for s in i2:
        d = LineString([(s['x1'], s['y1']), (s['x2'], s['y2'])]).distance(p)
        if best is None or d < best[0]: best = (d, s['net'])
    vb = min(((math.hypot(v['x'] - x, v['y'] - y), v['net']) for v in D['vias'] if v['net'] != 'GND'), default=(99, ''))
    return 'In2 %s %.2f | via %s %.2f' % (best[1] if best else '-', best[0] if best else 99, vb[1], vb[0])
print('runs >= 1.5 mm:')
for n, c in sorted(runs, key=lambda r: -r[1][4]):
    if c[4] < 1.5: break
    print('  %-34s %.1f  (%.2f,%.2f)-(%.2f,%.2f)  %s' % (n, c[4], c[0], c[1], c[2], c[3], cause((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)))
