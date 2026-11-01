"""greedy_exits.py GEO DUMP NETS DRU OUT.json [--fix=REF=x,y,rot ...] [--budget MM]
Greedy escape pass (R10 iteration 2): candidates are movable 2-pad passives (R, C) with no copper attached to any pad
(no track end or via inside the pad), not in a hot loop (they carry no copper), not fixed. For each candidate that fails an
exit itself or blocks another pad's exit: try poses within 0.6 mm (0.05 grid) and rotations r0, r0+180, r0+-90; accept the
best legal pose (HA8 tiers + AG3, HA6, fixed copper, silk, outline) only if the number of failing exits in a 4 mm
neighbourhood drops, the MST increase of its nets is <= 1.5 mm, and the running total stays within --budget (default 15 mm)."""
import sys, math, json
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from r10lib import *
geo, dump, nets, dru, outp = sys.argv[1:6]
B = Board(geo, dump, nets, dru)
budget = 15.0
for a in sys.argv[6:]:
    if a.startswith('--fix='):
        r, v = a[6:].split('='); B.pose[r] = tuple(map(float, v.split(',')))
    if a.startswith('--budget='): budget = float(a[9:])
def has_cu(ref):
    for q in B.padgeoms(ref):
        for P in q['P']:
            for t in B.G['tracks']:
                for x, y in ((t['x1'], t['y1']), (t['x2'], t['y2'])):
                    if abs(x - q['x']) < 1.5 and abs(y - q['y']) < 1.5 and P.buffer(0.01).contains(Point(x, y)): return True
            for v in B.G['vias']:
                if abs(v['x'] - q['x']) < 1.5 and abs(v['y'] - q['y']) < 1.5 and P.buffer(v['d'] / 2).contains(Point(v['x'], v['y'])): return True
    return False
cands = [r for r in B.pads if r[0] in 'RC' and r[1].isdigit() and len(B.pads[r]) == 2 and r not in FIXED and not has_cu(r)]
print('copper-free 2-pad passives', len(cands))
allrefs = list(B.pads)
def fails_near(pt, rad=4.0):
    refs = [r for r in allrefs if abs(B.pose[r][0] - pt[0]) < rad and abs(B.pose[r][1] - pt[1]) < rad]
    return B.exits(refs)
bad0 = B.exits(allrefs)
print('failing exits (all signal pads)', len(bad0))
involved = {}
for r, n, net, w in bad0:
    involved[r] = involved.get(r, 0) + 1
    if w: involved[w[1].split('-')[0]] = involved.get(w[1].split('-')[0], 0) + 1
order = [r for r in sorted(involved, key=lambda r: -involved[r]) if r in cands]
print('candidates involved', order)
spent = 0.0; moves = {}
for ref in order:
    x0, y0, r0 = B.pose[ref]; sig = {q['net'] for q in B.padgeoms(ref) if q['net']}
    m0 = sum(net_mst(B, sig).values()); f0 = len(fails_near((x0, y0)))
    best = None
    for ro in (r0, r0 + 180, r0 + 90, r0 - 90):
        ro = (ro + 180) % 360 - 180
        for i in range(-12, 13):
            for j in range(-12, 13):
                dx, dy = i * 0.05, j * 0.05
                if math.hypot(dx, dy) > 0.6 + 1e-9: continue
                B.pose[ref] = (round(x0 + dx, 4), round(y0 + dy, 4), ro)
                if B.pose[ref] == (x0, y0, r0) or not B.legal(ref)[0]: continue
                f1 = len(fails_near((x0, y0)))
                if f1 >= f0: continue
                dm = sum(net_mst(B, sig).values()) - m0
                if dm > 1.5 or spent + max(dm, 0) > budget: continue
                sc = f1 * 10 + dm + 0.5 * math.hypot(dx, dy) + (0.2 if ro != r0 else 0)
                if best is None or sc < best[0]: best = (sc, B.pose[ref], f1, dm)
    if best:
        B.pose[ref] = best[1]; spent += max(best[3], 0); moves[ref] = [best[1], [x0, y0, r0], f0, best[2], round(best[3], 3)]
        print('MOVE %s %s -> %s  local fails %d -> %d  mst %+.2f  (spent %.2f)' % (ref, (x0, y0, r0), best[1], f0, best[2], best[3], spent))
    else:
        B.pose[ref] = (x0, y0, r0)
bad1 = B.exits(allrefs)
print('failing exits after', len(bad1))
json.dump(dict(moves=moves, fails_before=len(bad0), fails_after=len(bad1), after=[(r, n, net, w) for r, n, net, w in bad1]), open(outp, 'w'), indent=1)
