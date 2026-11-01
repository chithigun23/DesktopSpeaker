"""metrics.py BEFORE.json AFTER.json OUT.json : R10 gates from two pcbnew dumps (work-r8/scripts/dump.py)
pad nets per (ref, pad) equal; moves; side/rotation; HA8 strict tiers (r8b_ha8) before/after; AG3 (no failing pair tighter);
every pair whose courtyard gap shrank; minimum neighbour gaps; signal-net octilinear MST total; decoupling distances."""
import sys, json, collections, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r8/scripts')
from lib import load, is_sig
from checks import decap
import r8b_ha8 as HA
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from r10lib import mst
A = load(sys.argv[1]); B = load(sys.argv[2]); out = {}
pa = {(f['ref'], p['num'], i): p['net'] for f in A['fps'] for i, p in enumerate(f['pads'])}
pb = {(f['ref'], p['num'], i): p['net'] for f in B['fps'] for i, p in enumerate(f['pads'])}
out['pads_compared'] = len(pa)
out['pad_net_diff'] = [k for k in pa if pa[k] != pb.get(k)] + [k for k in pb if k not in pa]
out['side_diff'] = [f['ref'] for f in A['fps'] if f['side'] != B['F'][f['ref']]['side']]
out['smd_on_bottom'] = [f['ref'] for f in B['fps'] if f['side'] == 'B' and any(p['attr'] == 1 for p in f['pads'])]
out['moved'] = [[f['ref'], round(f['x'], 4), round(f['y'], 4), f['rot'], round(B['F'][f['ref']]['x'], 4), round(B['F'][f['ref']]['y'], 4), B['F'][f['ref']]['rot']]
                for f in A['fps'] if abs(f['x'] - B['F'][f['ref']]['x']) > 1e-4 or abs(f['y'] - B['F'][f['ref']]['y']) > 1e-4 or f['rot'] != B['F'][f['ref']]['rot']]
CA, CB = HA.courtyards(A), HA.courtyards(B)
fa, fb = HA.ha8(A, CA), HA.ha8(B, CB)
out['ha8_before'] = dict(pairs=len(fa), by_tier=dict(collections.Counter('%s %.2f' % (t, rq) for *_, rq, t in fa)))
out['ha8_after'] = dict(pairs=len(fb), by_tier=dict(collections.Counter('%s %.2f' % (t, rq) for *_, rq, t in fb)))
ka = {tuple(sorted(x[:2])): x for x in fa}; kb = {tuple(sorted(x[:2])): x for x in fb}
out['ha8_new_pairs'] = [kb[k] for k in kb if k not in ka]
out['ha8_fixed_pairs'] = [ka[k] for k in ka if k not in kb]
out['ha8_tighter'] = [[*k, ka[k][2], kb[k][2]] for k in kb if k in ka and kb[k][2] < ka[k][2] - 1e-3]
# every pair within 1.6 mm involving a moved part: gap before/after
mv = {m[0] for m in out['moved']}
names = list(CB); shrunk = []; mins = {}
from shapely.strtree import STRtree
tr = STRtree([CB[n][0] for n in names])
for a in mv:
    if a not in CB: continue
    for j in tr.query(CB[a][0].buffer(1.6)):
        b = names[j]
        if b == a: continue
        g1 = CB[a][0].distance(CB[b][0]); g0 = CA[a][0].distance(CA[b][0])
        rq, t = HA.req(B['F'][a], B['F'][b])
        mins[a] = min(mins.get(a, (9, ''))[0], round(g1, 3)), mins.get(a, (9, ''))[1] if g1 >= mins.get(a, (9, ''))[0] else b
        if g1 < g0 - 1e-3: shrunk.append([a, b, round(g0, 3), round(g1, 3), rq, 'ok' if g1 >= rq - 1e-6 else 'FAIL'])
out['pairs_shrunk'] = shrunk
out['min_gap_moved'] = {a: v for a, v in sorted(mins.items())}
def allmin(C):
    n = list(C); t = STRtree([C[x][0] for x in n]); m = (9, None)
    for a in n:
        for j in t.query(C[a][0].buffer(0.5)):
            b = n[j]
            if b <= a: continue
            g = C[a][0].distance(C[b][0])
            if g < m[0]: m = (round(g, 3), (a, b))
    return m
out['min_gap_board'] = [allmin(CA), allmin(CB)]
def sigmst(D):
    t = 0.0; per = {}
    for n, ps in D['netpads'].items():
        if not is_sig(D, n) or len(ps) < 2: continue
        per[n] = mst([(p['x'], p['y']) for _, p in ps]); t += per[n]
    return t, per
ta, pa_ = sigmst(A); tb, pb_ = sigmst(B)
out['signal_mst'] = [round(ta, 2), round(tb, 2), round(100 * (tb - ta) / ta, 3)]
out['signal_mst_changed'] = {n: [round(pa_[n], 2), round(pb_.get(n, 0), 2)] for n in pa_ if abs(pa_[n] - pb_.get(n, 0)) > 0.01}
da, db = decap(A), decap(B)
out['decap_changed'] = [(r, n, da[r][n], db[r].get(n)) for r in da for n in da[r] if db[r].get(n) != da[r][n]]
json.dump(out, open(sys.argv[3], 'w'), indent=1, default=str)
for k in ('pads_compared', 'pad_net_diff', 'side_diff', 'smd_on_bottom', 'ha8_before', 'ha8_after', 'ha8_new_pairs', 'ha8_fixed_pairs', 'ha8_tighter',
          'pairs_shrunk', 'min_gap_moved', 'min_gap_board', 'signal_mst', 'signal_mst_changed', 'decap_changed'):
    print(k, out[k])
print('moved', len(out['moved']))
