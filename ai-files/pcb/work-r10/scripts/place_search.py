"""place_search.py GEO DUMP NETS DRU 'REF:radius:rots:targets' ... [--fix REF=x,y,rot ...]
Greedy local search, one part at a time in the given order (earlier results stay applied):
candidate poses on a 0.05 mm grid within radius (rots: comma list of absolute rotations, '-' = keep), legal (HA8 tiers + AG3,
fixed copper clearance, outline); score = 100 * failing exits (target pads + all signal pads of the part and of parts within 3 mm)
+ MST change of the part's signal nets + 0.2 * displacement. Prints the chosen pose and the before/after exits."""
import sys, math, json
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from r10lib import *
geo, dump, nets, dru = sys.argv[1:5]
B = Board(geo, dump, nets, dru)
args = sys.argv[5:]; fix = [a for a in args if a.startswith('--fix=')]; specs = [a for a in args if not a.startswith('--')]
for f in fix:
    r, v = f[6:].split('='); x, y, ro = map(float, v.split(',')); B.pose[r] = (x, y, ro)
    ok, why = B.legal(r); print('fix', r, B.pose[r], 'legal', ok, why)
out = {}
for sp in specs:
    ref, rad, rots, tg = (sp.split(':') + ['', '', ''])[:4]
    rad = float(rad); x0, y0, r0 = B.pose[ref]
    rots = [r0] if rots in ('', '-') else [float(r) for r in rots.split(',')]
    targets = [t for t in tg.split(',') if t]
    near = [r for r in B.pads if abs(B.pose[r][0] - x0) < 4 and abs(B.pose[r][1] - y0) < 4 and r != ref]
    tref = sorted(set([t.split('-')[0] for t in targets] + near + [ref]))
    sig = {q['net'] for q in B.sigpads(ref)}
    def score():
        bad = B.exits(tref); m = net_mst(B, sig)
        return len(bad), sum(m.values()), bad
    s0 = score(); best = None
    STEP = 0.05 if rad <= 2 else 0.1; n = int(round(rad / STEP))
    for ro in rots:
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                dx, dy = i * STEP, j * STEP
                if math.hypot(dx, dy) > rad + 1e-9: continue
                B.pose[ref] = (round(x0 + dx, 4), round(y0 + dy, 4), ro)
                ok, why = B.legal(ref)
                if not ok: continue
                # cheap prefilter on the part's own exits + targets first
                nb, m, bad = score()
                sc = 100 * nb + (m - s0[1]) + 0.2 * math.hypot(dx, dy) + (0.3 if ro != r0 else 0)
                if best is None or sc < best[0]: best = (sc, B.pose[ref], nb, m, bad)
    if best is None:
        B.pose[ref] = (x0, y0, r0); print(ref, 'NO LEGAL POSE'); continue
    B.pose[ref] = best[1]
    print('%s %s -> %s  exits fail %d -> %d  mst %.2f -> %.2f' % (ref, (x0, y0, r0), best[1], s0[0], best[2], s0[1], best[3]))
    print('   before:', [(b[0], b[1], b[3]) for b in s0[2]]); print('   after: ', [(b[0], b[1], b[3]) for b in best[4]])
    out[ref] = best[1]
print(json.dumps(out))
