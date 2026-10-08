"""v10 copy of fp_sp_v9.py: python3 fp_sp_v10.py seed iters NH -> ai-files/pcb/work-v10/floorplan-v10-raw<seed>_<NH>.json
v10 additions: key-pin objectives (I2S source->both amps, USB J1->U2, PVDD U25->amps, SYS U4->U25, CC J1->U11, battery J5->Q103) from cells-v10.json 'keypin',
area cap AMAX, BTSUP merged into BM83, initial sequence pair from the v9b floorplan.
Tiles = content + 0.5 mm side/bottom margin + 2.3 mm title strip; abutting tiles share one wall. Initial sequence pair from the v6 tile arrangement.
Separation minima are edge weights of the longest-path compaction (so they hold by construction); wall classes (BM83 left, WAKE/JACKS/PDIN rear,
AMP6/AMP7 front, BATIO right) are slid to the wall after decoding and penalised if blocked; mounting-hole support distances are penalties."""
import json, math, random, sys, os, time
import numpy as np
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
C = json.load(open(ROOT + 'pcb/work-v10/cells-v10.json'))
sizes = {k: list(v) for k, v in C['sizes'].items()}
MG, MT, HOLE = 0.5, 2.3, 7.8
seed, ITERS = int(sys.argv[1]), int(sys.argv[2])
NH = int(sys.argv[3]) if len(sys.argv) > 3 else 8
AA = float(os.environ.get('AA', '20.4'))
HPW = float(os.environ.get('HPW', '1'))
RCOV = float(os.environ.get('RCOV', '35'))
WMAX = float(os.environ.get('WMAX', '140'))
AMAX = float(os.environ.get('AMAX', '18300'))
KP = C.get('keypin', {})
WK = float(os.environ.get('WK', '1.0'))
WI, LI = float(os.environ.get('WI', '60')), float(os.environ.get('LI', '48'))
WP, LP = float(os.environ.get('WP', '40')), float(os.environ.get('LP', '32'))
KPO = [('I2S_SRC', 'I2S_U6', LI, WI * WK), ('I2S_SRC', 'I2S_U7', LI, WI * WK), ('USB_J1', 'USB_U2', 20.0, 30.0), ('PVDD_U25', 'PVDD_U6', LP, WP * WK),
       ('PVDD_U25', 'PVDD_U7', LP, WP * WK), ('SYS_U4', 'SYS_U25', 25.0, 25.0), ('CC_J1', 'CC_U11', 30.0, 8.0), ('BAT_J5', 'BAT_Q103', 25.0, 15.0), ('BATI_Q103', 'BATI_U4', 15.0, 40.0)]
KPO = [k for k in KPO if k[0] in KP and k[1] in KP]
NOTALL = {'CHGQ', 'AO3V', 'SWG', 'CODSUP', 'MUX'}         # tiles without CAD-modelled tall parts
ROCK_X0, ROCK_Y1 = float(os.environ.get('ROCK_X0', '120.0')), float(os.environ.get('ROCK_Y1', '19.5'))
HMAXD = float(os.environ.get('HMAXD', '135'))
sizes['BM83'][0] -= 8.0
names = list(sizes) + ['H%d' % i for i in range(1, NH + 1)]
N = len(names); idx = {n: i for i, n in enumerate(names)}
Wd = [sizes[n][0] + 2 * MG if n in sizes else HOLE for n in names]
Ht = [sizes[n][1] + MG + MT if n in sizes else HOLE for n in names]
cw = [sizes[n][0] if n in sizes else 0 for n in names]; chh = [sizes[n][1] if n in sizes else 0 for n in names]
RULE = {}
def addr(a, b, d):
    k = (idx[a], idx[b]); RULE[k] = RULE[(k[1], k[0])] = max(d, RULE.get(k, 0))
HN = [n for n in names if n.startswith('H')]
for a in ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']:
    addr('BM83', a, 15.2)
    for b in ('AMP6', 'AMP7', 'BOOST', 'LOG5V'): addr(a, b, AA if b in ('AMP6', 'AMP7') else 20.4)
    addr('CHG', a, 14.0)
for b in ('CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7'): addr('BM83', b, 25.4)
for h in HN: addr('BM83', h, 6.0)
for i_, h_ in enumerate(HN):
    for g_ in HN[i_ + 1:]: addr(h_, g_, 10.0)
reqx = [[0.0] * N for _ in range(N)]; reqy = [[0.0] * N for _ in range(N)]
for (i, j), d in RULE.items():
    reqx[i][j] = max(0.0, d - 2 * MG); reqy[i][j] = max(0.0, d - MG - MT)
    # vertical gap between content boxes = tile gap + MG (bottom margin of upper) + MT (top strip of lower); symmetric use both orders
    reqy[j][i] = max(0.0, d - MG - MT)
HV = []
for r, (cn, du, dv) in C['heavy'].items():
    if r in ('U1', 'SW101', 'J2', 'J3'): continue
    HV.append((r, idx[cn], MG + du, MT + dv, 12.0 if r.startswith('L20') else 15.0))
CELLH = [(idx[cn], MG + du, MT + dv) for cn, lst in C['cellholes'].items() for du, dv in lst]
REAR = [idx[n] for n in ('JACKS', 'PDIN', 'WAKE')]
FRONT = [idx[n] for n in ('AMP6', 'AMP7')]
LEFT = [idx['BM83']]; RIGHT = [idx['BATIO']]
rng = random.Random(seed)

def decode(p1, p2):
    pos2 = [0] * N
    for k, m in enumerate(p2): pos2[m] = k
    X = [0.0] * N; Y = [0.0] * N
    for k, b in enumerate(p1):
        xb = 0.0; yb = 0.0; pb = pos2[b]
        for a in p1[:k]:
            if pos2[a] < pb:
                v = X[a] + Wd[a] + reqx[a][b]
                if v > xb: xb = v
            else:
                v = Y[a] + Ht[a] + reqy[a][b]
                if v > yb: yb = v
        X[b] = xb; Y[b] = yb
    return X, Y

def evaluate(p1, p2, detail=False):
    X, Y = decode(p1, p2)
    W = max(X[i] + Wd[i] for i in range(N)); H = max(Y[i] + Ht[i] for i in range(N))
    pen = 0.0
    for i in FRONT:       # slide to the front wall
        lim = H - Y[i] - Ht[i]
        for b in range(N):
            if b != i and X[b] < X[i] + Wd[i] - 1e-6 and X[b] + Wd[b] > X[i] + 1e-6 and Y[b] >= Y[i] + Ht[i] - 1e-6:
                lim = min(lim, Y[b] - Y[i] - Ht[i] - reqy[i][b])
        Y[i] += max(lim, 0.0); pen += H - Y[i] - Ht[i]
    for i in RIGHT:
        lim = W - X[i] - Wd[i]
        for b in range(N):
            if b != i and Y[b] < Y[i] + Ht[i] - 1e-6 and Y[b] + Ht[b] > Y[i] + 1e-6 and X[b] >= X[i] + Wd[i] - 1e-6:
                lim = min(lim, X[b] - X[i] - Wd[i] - reqx[i][b])
        X[i] += max(lim, 0.0); pen += W - X[i] - Wd[i]
    for i in REAR: pen += Y[i]
    for i in LEFT: pen += X[i]
    hx = [X[i] + HOLE / 2 for i in range(N) if names[i].startswith('H')] + [X[i] + a for i, a, c in CELLH]
    hy = [Y[i] + HOLE / 2 for i in range(N) if names[i].startswith('H')] + [Y[i] + c for i, a, c in CELLH]
    hp = 0.0
    for r, ti, dx, dy, lim in HV:
        d = min(math.hypot(X[ti] + dx - a, Y[ti] + dy - b) for a, b in zip(hx, hy))
        if d > lim: hp += d - lim
    cov = 0.0; dm = 0.0
    if HPW > 0:
        gxs, gys = np.meshgrid(np.arange(3, W, 6.0), np.arange(3, H, 6.0))
        dm = float(np.min(np.hypot(gxs[..., None] - np.array(hx), gys[..., None] - np.array(hy)), axis=-1).max())
        cov = max(dm - RCOV, 0)
    kpp = 0.0
    kd = {}
    # v10: CAD rear-lid rocker SW101 stand-in (CAD x 66, r 9.8, 22 mm deep from the lid; PCB rear edge 3.5 mm in front of the lid face):
    # board x >= 120.7 (from the left edge, ul = -61, pcb_cx = -3.5) and y <= 19 from the rear edge must hold no modelled tall part or hole
    rk = 0.0
    for i in range(N):
        if names[i] in NOTALL:
            continue
        ox = X[i] + Wd[i] - ROCK_X0
        oy = ROCK_Y1 - Y[i]
        if ox > 0 and oy > 0:
            rk += min(ox, Wd[i]) * min(oy, Ht[i])
    kpp += 200.0 * rk
    kd['rocker'] = round(rk, 1)
    for a_, b_, lim_, w_ in KPO:
        ca, cb = KP[a_], KP[b_]
        ia, ib = idx[ca[0]], idx[cb[0]]
        ax_, ay_ = X[ia] + MG + ca[1], Y[ia] + MT + ca[2]
        bx_, by_ = X[ib] + MG + cb[1], Y[ib] + MT + cb[2]
        dx_, dy_ = abs(ax_ - bx_), abs(ay_ - by_)
        d_ = max(dx_, dy_) + 0.4142 * min(dx_, dy_)
        kd[a_ + '-' + b_] = round(d_, 1)
        if d_ > lim_: kpp += w_ * (d_ - lim_)
    tot = W * H + 40 * pen + HPW * (25 * hp + 40 * cov) + 40 * max(H - HMAXD, 0) + 40 * max(W - WMAX, 0) + kpp + 60 * max(W * H - AMAX, 0)
    if detail: return tot, dict(W=W, H=H, area=W * H, pins=pen, hp=hp, cov=dm, kp=kpp, **kd), X, Y
    return tot

v6 = json.load(open(os.environ.get('INIT', ROOT + 'pcb/floorplan-v9.json')))['abs']      # v10: INIT=raw floorplan to refine
cx = []; cy = []
for n in names:
    if n in v6: cx.append(v6[n][0] + Wd[idx[n]] / 2); cy.append(v6[n][1] + Ht[idx[n]] / 2)
    else: cx.append(rng.uniform(0, 110)); cy.append(rng.uniform(0, 130))
p1 = sorted(range(N), key=lambda i: cx[i] + cy[i] + rng.gauss(0, 3)); p2 = sorted(range(N), key=lambda i: cx[i] - cy[i] + rng.gauss(0, 3))
cur = evaluate(p1, p2); best = (cur, p1[:], p2[:])
T0, T1 = float(os.environ.get('T0', '300')), 2.0
t0 = time.time()
for it in range(ITERS):
    T = T0 * (T1 / T0) ** (it / ITERS)
    q1, q2 = p1[:], p2[:]
    m = rng.random()
    a, b = rng.sample(range(N), 2)
    if m < 0.4: q1[q1.index(a)], q1[q1.index(b)] = b, a
    elif m < 0.7: q2[q2.index(a)], q2[q2.index(b)] = b, a
    elif m < 0.85:
        q1[q1.index(a)], q1[q1.index(b)] = b, a; q2[q2.index(a)], q2[q2.index(b)] = b, a
    else:       # relocate one module in one sequence
        s = q1 if rng.random() < 0.5 else q2
        s.remove(a); s.insert(rng.randrange(N), a)
    c2 = evaluate(q1, q2)
    if c2 <= cur or rng.random() < math.exp((cur - c2) / T):
        p1, p2, cur = q1, q2, c2
        if cur < best[0]: best = (cur, p1[:], p2[:])
tot, d, X, Y = evaluate(best[1], best[2], True)
print('seed', seed, {k: round(float(v), 1) for k, v in d.items()}, 'cost', round(tot), '%ds' % (time.time() - t0), flush=True)
d = {k: (float(v) if not isinstance(v, str) else v) for k, v in d.items()}
if d['pins'] < 1e-6:
    json.dump(dict(W=round(d['W'], 2), H=round(d['H'], 2), area=d['area'], abs={n: [round(X[idx[n]], 2), round(Y[idx[n]], 2)] for n in names}, cov=d['cov'], hp=d['hp'], metrics=d),
              open(ROOT + 'pcb/work-v10/floorplan-v10-raw%d_%d%s.json' % (seed, NH, os.environ.get('TAG', '')), 'w'))
