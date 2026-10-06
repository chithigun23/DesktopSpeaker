"""Slide-compaction annealer for placement v8: python3 fp_anneal_v8.py seed iters [NH] -> ai-files/pcb/floorplan-v8-raw<seed>.json
Starts from the v6 tile arrangement (floorplan-v6.json), tiles shrunk to content + 0.5 mm margin + 2.3 mm title strip, abutting tiles share one wall.
Moves: shift, gravity slide (to wall / neighbour), swap, teleport next to a neighbour. Edge classes: BM83 left wall; WAKE/JACKS/PDIN rear wall; AMP6/AMP7 front wall;
BATIO right wall. Hard-ish constraints as penalties (overlap, separations, hole support distances); a final legalisation + greedy gravity pass; output only if clean."""
import json, math, random, sys, os
import numpy as np
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
C = json.load(open(ROOT + 'pcb/cells-v8.json'))
sizes = {k: list(v) for k, v in C['sizes'].items()}
MG, MT, HOLE = 0.5, 2.3, 7.8
seed, ITERS = int(sys.argv[1]), int(sys.argv[2])
NH = int(sys.argv[3]) if len(sys.argv) > 3 else 8
AA = float(os.environ.get('AA', '20.4'))
sizes['BM83'][0] -= 8.0
OVH = {'BM83': 8.0}
names = list(sizes) + ['H%d' % i for i in range(1, NH + 1)]
N = len(names); idx = {n: i for i, n in enumerate(names)}
isH = np.array([n.startswith('H') for n in names])
Wd = np.array([sizes[n][0] + 2 * MG if n in sizes else HOLE for n in names])
Ht = np.array([sizes[n][1] + MG + MT if n in sizes else HOLE for n in names])
cw = np.array([sizes[n][0] if n in sizes else 0 for n in names]); ch = np.array([sizes[n][1] if n in sizes else 0 for n in names])
# content rect offsets inside the tile
RULE = {}
def addr(a, b, d): RULE[(min(idx[a], idx[b]), max(idx[a], idx[b]))] = max(d, RULE.get((min(idx[a], idx[b]), max(idx[a], idx[b])), 0))
HN = [n for n in names if n.startswith('H')]
for a in ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']:
    addr('BM83', a, 15.2)
    for b in ('AMP6', 'AMP7', 'BOOST', 'LOG5V'): addr(a, b, AA if b in ('AMP6', 'AMP7') else 20.4)
    addr('CHG', a, 14.0); addr('BTSUP', a, 10.0)
for b in ('CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7'): addr('BM83', b, 25.4)
addr('BM83', 'BTSUP', 12.0)
for h in HN: addr('BM83', h, 6.0)
for i_, h_ in enumerate(HN):
    for g_ in HN[i_ + 1:]: addr(h_, g_, 12.0)
RI = np.array([k[0] for k in RULE]); RJ = np.array([k[1] for k in RULE]); RD = np.array(list(RULE.values()))
# heavy parts: (tile idx, dx, dy, limit, weight)
HV = []
for r, (cn, du, dv) in C['heavy'].items():
    if r in ('U1', 'SW101', 'J2', 'J3'): continue
    lim = 12.0 if r.startswith('L20') else 15.0
    HV.append((r, idx[cn], MG + du, MT + dv, lim))
HVi = np.array([h[1] for h in HV]); HVx = np.array([h[2] for h in HV]); HVy = np.array([h[3] for h in HV]); HVl = np.array([h[4] for h in HV])
CELLH = [(idx[cn], MG + du, MT + dv) for cn, lst in C['cellholes'].items() for du, dv in lst]
REAR = [idx[n] for n in ('JACKS', 'PDIN', 'WAKE')]
FRONT = [idx[n] for n in ('AMP6', 'AMP7')]
LEFT = [idx['BM83']]; RIGHT = [idx['BATIO']]
RCOV = float(os.environ.get('RCOV', '32'))
HMAXD = float(os.environ.get('HMAXD', '132'))
rng = random.Random(seed)
HPW = float(os.environ.get('HPW', '1'))

def derive(S):
    X, Y = S[:, 0].copy(), S[:, 1].copy()
    for i in REAR: Y[i] = 0.0
    for i in LEFT: X[i] = 0.0
    oth = [i for i in range(N) if i not in RIGHT and i not in FRONT]
    H = max(np.max((Y + Ht)[oth]), max(Ht[i] for i in FRONT))
    for i in FRONT: Y[i] = H - Ht[i]
    H = max(H, np.max((Y + Ht)))
    W = np.max((X + Wd)[[i for i in range(N) if i not in RIGHT]])
    for i in RIGHT: X[i] = W - Wd[i]; W = max(W, Wd[i])
    return X, Y, W, H

GX = GY = None
def cost(S, lam, detail=False):
    X, Y, W, H = derive(S)
    ov = np.maximum(np.minimum((X + Wd)[:, None], (X + Wd)[None]) - np.maximum(X[:, None], X[None]), 0)
    oy = np.maximum(np.minimum((Y + Ht)[:, None], (Y + Ht)[None]) - np.maximum(Y[:, None], Y[None]), 0)
    ovl = np.triu(ov * oy, 1)
    ovsum = ovl.sum()
    # separations (content rects)
    l, t = X + MG, Y + MT; r, b = l + cw, t + ch
    gx = np.maximum(np.maximum(l[RJ] - r[RI], l[RI] - r[RJ]), 0); gy = np.maximum(np.maximum(t[RJ] - b[RI], t[RI] - b[RJ]), 0)
    sep = np.maximum(RD - np.hypot(gx, gy), 0).sum()
    # hole supports
    hx = [X[i] + HOLE / 2 for i in range(N) if isH[i]] + [X[i] + a for i, a, c in CELLH]
    hy = [Y[i] + HOLE / 2 for i in range(N) if isH[i]] + [Y[i] + c for i, a, c in CELLH]
    hx, hy = np.array(hx), np.array(hy)
    px, py = X[HVi] + HVx, Y[HVi] + HVy
    dh = np.min(np.hypot(px[:, None] - hx[None], py[:, None] - hy[None]), axis=1)
    hp = np.maximum(dh - HVl, 0).sum()
    gxs, gys = np.meshgrid(np.arange(2, W, 4.0), np.arange(2, H, 4.0))
    dm = np.min(np.hypot(gxs[..., None] - hx, gys[..., None] - hy), axis=-1).max()
    cov = max(dm - RCOV, 0)
    # hole inside the board (centre >= 3.9 mm from walls is ensured by the tile)
    HPW = float(os.environ.get('HPW', '1'))
    tot = W * H + lam * (30 * ovsum + 120 * sep + HPW * (25 * hp + 40 * cov) + 30 * max(H - HMAXD, 0))
    if detail: return dict(W=W, H=H, area=W * H, ov=ovsum, sep=sep, hp=hp, cov=dm, cost=tot)
    return tot

def free_axes(i):
    if i in REAR: return (1, 0)
    if i in FRONT: return (1, 0)
    if i in LEFT or i in RIGHT: return (0, 1)
    return (1, 1)

def slide(S, i, d):
    X, Y, W, H = derive(S)
    fx, fy = free_axes(i)
    if (d in (0, 1) and not fx) or (d in (2, 3) and not fy): return None
    x0, y0, x1, y1 = X[i], Y[i], X[i] + Wd[i], Y[i] + Ht[i]
    best = 80.0
    for j in range(N):
        if j == i: continue
        xa, ya, xb, yb = X[j], Y[j], X[j] + Wd[j], Y[j] + Ht[j]
        if d == 0 and ya < y1 - 1e-6 and yb > y0 + 1e-6 and xb <= x0 + 1e-6: best = min(best, x0 - xb)
        if d == 1 and ya < y1 - 1e-6 and yb > y0 + 1e-6 and xa >= x1 - 1e-6: best = min(best, xa - x1)
        if d == 2 and xa < x1 - 1e-6 and xb > x0 + 1e-6 and yb <= y0 + 1e-6: best = min(best, y0 - yb)
        if d == 3 and xa < x1 - 1e-6 and xb > x0 + 1e-6 and ya >= y1 - 1e-6: best = min(best, ya - y1)
    if d == 0: best = min(best, x0)
    if d == 2: best = min(best, y0)
    if d in (1, 3): best = min(best, 40.0)
    S2 = S.copy()
    k = [(-1, 0), (1, 0), (0, -1), (0, 1)][d]
    S2[i, 0] += k[0] * best; S2[i, 1] += k[1] * best
    return S2

def propose(S):
    S2 = S.copy()
    i = rng.randrange(N)
    fx, fy = free_axes(i)
    m = rng.random()
    if m < 0.35:
        sg = rng.choice([0.4, 1.5, 5.0])
        if fx: S2[i, 0] = max(0.0, S2[i, 0] + rng.gauss(0, sg))
        if fy: S2[i, 1] = max(0.0, S2[i, 1] + rng.gauss(0, sg))
    elif m < 0.65:
        r = slide(S, i, rng.randrange(4))
        if r is None: return None
        S2 = r
    elif m < 0.8:
        j = rng.randrange(N)
        if j == i or (free_axes(j) != (1, 1)) or (free_axes(i) != (1, 1)): return None
        X, Y, W, H = derive(S)
        S2[i] = (X[j], Y[j]); S2[j] = (X[i], Y[i])
    else:
        j = rng.randrange(N)
        if j == i: return None
        X, Y, W, H = derive(S)
        side = rng.randrange(4)
        if side == 0: nx, ny = X[j] - Wd[i], Y[j] + rng.uniform(-Ht[i] * 0.8, Ht[j] * 0.8)
        elif side == 1: nx, ny = X[j] + Wd[j], Y[j] + rng.uniform(-Ht[i] * 0.8, Ht[j] * 0.8)
        elif side == 2: nx, ny = X[j] + rng.uniform(-Wd[i] * 0.8, Wd[j] * 0.8), Y[j] - Ht[i]
        else: nx, ny = X[j] + rng.uniform(-Wd[i] * 0.8, Wd[j] * 0.8), Y[j] + Ht[j]
        if fx: S2[i, 0] = max(0.0, nx)
        if fy: S2[i, 1] = max(0.0, ny)
    S2 = np.round(S2 * 20) / 20
    return S2

# start: v6 arrangement
v6 = json.load(open(ROOT + 'pcb/floorplan-v6.json'))['abs']
S = np.zeros((N, 2))
hi = 0
for n in names:
    if n in v6: S[idx[n]] = v6[n]
    else: S[idx[n]] = [rng.uniform(0, 100), rng.uniform(0, 120)]
S *= rng.uniform(1.0, 1.08)
cur = cost(S, 1.0); best_ok = None
T0, T1 = float(os.environ.get('T0','60')), 1.0
for it in range(ITERS):
    f = it / ITERS
    T = T0 * (T1 / T0) ** f
    lam = 1.0 + 3.0 * f
    S2 = propose(S)
    if S2 is None: continue
    c2 = cost(S2, lam); c1 = cost(S, lam)
    if c2 <= c1 or rng.random() < math.exp((c1 - c2) / T):
        S = S2
    if it % 200 == 0 or it == ITERS - 1:
        d = cost(S, 1.0, True)
        if d['ov'] < 1e-6 and d['sep'] < 1e-6 and (d['hp'] < 1e-6 or HPW == 0) and (d['cov'] <= RCOV + 1e-6 or HPW == 0) and d['H'] <= HMAXD:
            if best_ok is None or d['area'] < best_ok[0]: best_ok = (d['area'], S.copy())
# final greedy gravity compaction on the best-clean (or the final) state
S = best_ok[1] if best_ok else S
def valid(S):
    d = cost(S, 1.0, True); return d['ov'] < 1e-6 and d['sep'] < 1e-6 and (d['hp'] < 1e-6 or HPW == 0) and (d['cov'] <= RCOV + 1e-6 or HPW == 0), d
for sweep in range(8):
    imp = False
    for i in rng.sample(range(N), N):
        for d_ in rng.sample(range(4), 4):
            S2 = slide(S, i, d_)
            if S2 is None: continue
            S2 = np.round(S2 * 20) / 20
            ok, d2 = valid(S2)
            if ok and d2['area'] <= cost(S, 1.0, True)['area'] + 1e-6 and not np.allclose(S2, S):
                S = S2; imp = True
    if not imp: break
ok, d = valid(S)
X, Y, W, H = derive(S)
print('seed', seed, 'valid', ok, {k: round(float(v), 1) for k, v in d.items()}, flush=True)
if ok:
    json.dump(dict(W=round(float(W), 2), H=round(float(H), 2), area=float(W * H), abs={n: [round(float(X[idx[n]]), 2), round(float(Y[idx[n]]), 2)] for n in names}),
              open(ROOT + 'pcb/floorplan-v8-raw%d.json' % seed, 'w'))
