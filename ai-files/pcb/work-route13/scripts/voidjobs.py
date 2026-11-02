#!/usr/bin/env python3
"""voidjobs.py BOARD.kicad_pcb GEO.json TAG [--min 1.2] : RT-10 B-over-void repair jobs. For each slow (non-sensitive) signal net,
every B.Cu chain (connected B segments with exactly two open ends) carrying >= MIN mm of B over In2 void (r7 definition) becomes
one hr10 job: rip the chain, re-route end to end on F/B with a high cost for B over In2 void. Writes t/j_TAG_k.json + t/vj_TAG.json."""
import sys, math, json, collections, re
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import r7_metrics as R
from shapely.geometry import Point
from shapely.prepared import prep
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
brd, geo, tag = sys.argv[1:4]; MIN = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 1.2
D = R.load(brd)
g = prep(R.union(D, 'In2.Cu', lambda n: n == 'GND')); o = prep(R.union(D, 'In2.Cu', lambda n: n != 'GND'))
def void(x1, y1, x2, y2):
    ln = math.hypot(x2 - x1, y2 - y1); n = max(1, int(ln / 0.2)); v = 0
    for i in range(n):
        t = (i + .5) / n; p = Point(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        if not g.contains(p) and not o.contains(p): v += ln / n
    return v
SENS = re.compile(r'I2S|AUD_S|BT_AUDIO|HP_OUT|VMID|USB_D|USB_AUDIO|AUX|U24-VIN|XI$|XO$|ADC_INT|TS_SENSE|BATP|ILIM|PROG|FB\)|U14|U15|U25')
segs = [d for d in items(brd, kinds=('segment',)) if d['layer'] == 'B.Cu' and d['net'] != 'GND' and d['width'] <= 0.35]
GJ = json.load(open(geo)); cls = GJ['netclass']
bynet = collections.defaultdict(list)
for d in segs:
    if cls.get(d['net']) in ('Default', 'I2C', 'SIGNAL') and not SENS.search(d['net']): bynet[d['net']].append(d)
r4 = lambda p: (round(p[0], 4), round(p[1], 4))
jobs = []; k = 0
for net, ss in bynet.items():
    adj = collections.defaultdict(list)
    for i, d in enumerate(ss):
        adj[r4(d['start'])].append(i); adj[r4(d['end'])].append(i)
    seen = set()
    for i in range(len(ss)):
        if i in seen: continue
        comp = set(); st = [i]
        while st:
            j = st.pop()
            if j in comp: continue
            comp.add(j)
            for p in (r4(ss[j]['start']), r4(ss[j]['end'])): st += adj[p]
        seen |= comp
        deg = collections.Counter()
        for j in comp: deg[r4(ss[j]['start'])] += 1; deg[r4(ss[j]['end'])] += 1
        ends = [p for p, c in deg.items() if c == 1]
        if len(ends) != 2 or any(c > 2 for c in deg.values()): continue
        v = sum(void(*ss[j]['start'], *ss[j]['end']) for j in comp)
        L = sum(math.dist(ss[j]['start'], ss[j]['end']) for j in comp)
        if v < MIN: continue
        J = dict(net=net, **{'from': [ends[0][0], ends[0][1], 'via', 0.1]}, to=[ends[1][0], ends[1][1], 'via', 0.1], neck_drc=True, layers='FB',
                 margin=2.5, zone_soft=0.2, max_exp=1500000, bcu_cost=1.0, void_cost=12.0, w=ss[next(iter(comp))]['width'])
        base = dict(seg_del=[ss[j]['uuid'][:8] for j in comp])
        json.dump(base, open('t/r_%s_%d.json' % (tag, k), 'w'))
        json.dump(dict(geo=geo, base_plan='t/r_%s_%d.json' % (tag, k), out_plan='t/p_%s_%d.json' % (tag, k), jobs=[J]), open('t/j_%s_%d.json' % (tag, k), 'w'))
        jobs.append(dict(k=k, net=net, void=round(v, 2), len=round(L, 2), n=len(comp), ends=ends)); k += 1
json.dump(jobs, open('t/vj_%s.json' % tag, 'w'), indent=1)
for j in jobs: print(j['k'], j['net'], j['void'], j['len'], j['n'], j['ends'])
