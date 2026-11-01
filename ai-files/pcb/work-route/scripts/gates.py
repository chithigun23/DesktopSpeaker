"""gates.py : AG15 gates RT-0 -> RT-1 (plain python3 + json). Pad nets, copper lock manifest, new-copper exactness, zone outlines."""
import json, sys, hashlib, math, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route'
out = {}
# 1. pad nets
A = json.load(open(f'{W}/RT-0.dump.json')); B = json.load(open(f'{W}/RT-1.dump.json'))
pa = {(f['ref'], p['num'], i): p['net'] for f in A['fps'] for i, p in enumerate(f['pads'])}
pb = {(f['ref'], p['num'], i): p['net'] for f in B['fps'] for i, p in enumerate(f['pads'])}
pos = lambda D: {f['ref']: (round(f['x'], 4), round(f['y'], 4), f['rot'], f['side']) for f in D['fps']}
out['pads_compared'] = len(pa); out['pad_net_diff'] = [k for k in pa if pa[k] != pb.get(k)] + [k for k in pb if k not in pa]
out['footprint_pose_diff'] = [r for r, v in pos(A).items() if pos(B).get(r) != v]
# 2. copper items canonical
def canon(d):
    r = lambda v: tuple(round(x, 4) for x in v)
    if d['kind'] in ('segment', 'arc'):
        return (d['kind'], d['net'], d['layer'], round(d['width'], 4), r(d['start']), r(d['end']), r(d.get('mid', (0, 0))))
    if d['kind'] == 'via':
        return ('via', d['net'], r(d['at']), round(d['size'], 4), round(d['drill'], 4))
    return ('zone', d.get('uuid'), d.get('net', ''), str(d.get('layer', d.get('layers'))), tuple(r(p) for p in d.get('pts', [])))
I0 = [d for d in items(f'{W}/RT-0.kicad_pcb') if not (d['kind'] == 'zone' and d.get('teardrop'))]
I1 = [d for d in items(f'{W}/RT-1.kicad_pcb') if not (d['kind'] == 'zone' and d.get('teardrop'))]
C0 = collections.Counter(canon(d) for d in I0); C1 = collections.Counter(canon(d) for d in I1)
kept = C0 & C1; removed = C0 - C1; added = C1 - C0
h = hashlib.sha256('\n'.join(sorted(repr(k) for k in kept.elements())).encode()).hexdigest()
out['copper_items_RT0'] = sum(C0.values()); out['copper_items_RT1'] = sum(C1.values())
out['untouched_items'] = sum(kept.values()); out['untouched_sha256'] = h
out['removed_or_changed'] = sorted([list(map(str, k)) for k in removed.elements()])
out['added_or_changed'] = sorted([list(map(str, k)) for k in added.elements()])
# 3. exactness of every added track (power edits and USB/XTO)
bad = []; n = 0; L = 0.0
for k in added.elements():
    if k[0] != 'segment': continue
    (x1, y1), (x2, y2) = k[4], k[5]; dx, dy = abs(x2 - x1), abs(y2 - y1); n += 1; L += math.hypot(dx, dy)
    if not (dx < 1e-4 or dy < 1e-4 or abs(dx - dy) < 1e-4): bad.append(k)
out['new_segments'] = n; out['new_length_mm'] = round(L, 3); out['new_segments_not_exact'] = [list(map(str, b)) for b in bad]
# acute joints among new segments (two endpoints meeting, any net)
segs = [k for k in C1.elements() if k[0] == 'segment']
ep = collections.defaultdict(list)
for i, k in enumerate(segs):
    ep[(k[1], k[2], k[4])].append((i, 0)); ep[(k[1], k[2], k[5])].append((i, 1))
acute = []
newset = set(added)
for key, v in ep.items():
    if len(v) != 2: continue
    (i, e), (j, f) = v; a, b = segs[i], segs[j]
    if a not in newset and b not in newset: continue
    d1 = (a[5][0] - a[4][0], a[5][1] - a[4][1]) if e == 0 else (a[4][0] - a[5][0], a[4][1] - a[5][1])
    d2 = (b[5][0] - b[4][0], b[5][1] - b[4][1]) if f == 0 else (b[4][0] - b[5][0], b[4][1] - b[5][1])
    n1, n2 = math.hypot(*d1), math.hypot(*d2)
    if n1 < 1e-6 or n2 < 1e-6: continue
    ang = math.degrees(math.acos(max(-1, min(1, (d1[0] * d2[0] + d1[1] * d2[1]) / (n1 * n2)))))
    if ang < 91: acute.append([key[0], key[1], key[2], round(ang, 1)])
out['joints_le90_on_new_copper'] = acute
json.dump(out, open(f'{W}/RT-1.gates.json', 'w'), indent=1)
for k in ('pads_compared', 'pad_net_diff', 'footprint_pose_diff', 'copper_items_RT0', 'copper_items_RT1', 'untouched_items', 'untouched_sha256',
          'new_segments', 'new_length_mm', 'new_segments_not_exact', 'joints_le90_on_new_copper'):
    print(k, out[k])
print('removed/changed', len(out['removed_or_changed']), 'added/changed', len(out['added_or_changed']))
