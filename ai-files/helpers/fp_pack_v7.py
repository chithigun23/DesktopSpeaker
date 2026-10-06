"""Randomised rule-aware tile packer for placement v7: python3 fp_pack_v7.py Hmin Hmax trials -> ai-files/pcb/floorplan-v7.json
Pre-placed: rear row BM83|WAKE|JACKS|PDIN and front row AMP6|AMP7|BOOST; the other cells are placed top-left first in random order,
with hard separation rules (content-box distance, square inflation) against the cells already placed."""
import json, math, random, sys, os
import numpy as np
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
sizes = json.load(open(ROOT + 'pcb/cells-v7.json'))['sizes']
MG, MT, HOLE = 0.5, 2.3, 7.6
RS = 4.0          # occupancy raster: 4 cells per mm
STEP = 0.5
sz = {k: list(v) for k, v in sizes.items()}
sz['BM83'][0] -= 8.0
NH = int(os.environ.get('NH', '6'))
HN = ['H%d' % i for i in range(1, NH + 1)]
T = {n: (sz[n][0] + 2 * MG + 0.1, sz[n][1] + MG + MT + 0.1) for n in sz}
for h in HN: T[h] = (HOLE, HOLE); sz[h] = [HOLE - 2 * MG, HOLE - MG - MT]
CH = json.load(open(ROOT + 'pcb/cells-v7.json')).get('cellholes', {})
W = float(sys.argv[4]) if len(sys.argv) > 4 else 115.0
AA = float(os.environ.get('AA', '20.4'))   # class-D to analogue (rules doc: 20 mm, 10 mm absolute minimum with a GND via fence)
ANALOG = ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']
RULE = {}
def addr(a, b, d): RULE.setdefault(a, {})[b] = d; RULE.setdefault(b, {})[a] = d
for a in ANALOG:
    addr('BM83', a, 15.2)
    for b in ('AMP6', 'AMP7', 'BOOST', 'LOG5V'): addr(a, b, AA if b in ('AMP6', 'AMP7') else 20.4)
    addr('CHG', a, 14.0)
    addr('BTSUP', a, 10.0)     # BM83 3V8 buck (L3) kept 10 mm from the analogue cells (ground fence between)
for b in ('CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7'): addr('BM83', b, 25.4)
addr('BM83', 'BTSUP', 12.0)   # BT's own 3V8 supply (U15/L3) may sit close to the BM83
for h in HN: addr('BM83', h, 6.0)
for i_, h_ in enumerate(HN):
    for g_ in HN[i_ + 1:]: addr(h_, g_, 14.0)
RCOV = float(os.environ.get('RCOV', '40'))
RJ = float(os.environ.get('RJ', '22'))
FAILS = {}
def run(H, rng):
    nx, ny = int(W * RS) + 1, int(H * RS) + 1
    occ = np.zeros((ny, nx), bool)
    P = {}
    def put(n, x, y):
        P[n] = (x, y)
        occ[int(math.floor(y * RS + 1e-6)):int(math.ceil((y + T[n][1]) * RS - 1e-6)), int(math.floor(x * RS + 1e-6)):int(math.ceil((x + T[n][0]) * RS - 1e-6))] = True
    def content(n):
        x, y = P[n]; return (x + MG, y + MT, x + MG + sz[n][0], y + MT + sz[n][1])
    put('BM83', 0, 0); put('WAKE', T['BM83'][0], 0); put('JACKS', T['BM83'][0] + T['WAKE'][0], 0); put('PDIN', W - T['PDIN'][0], 0)
    if T['BM83'][0] + T['WAKE'][0] + T['JACKS'][0] > W - T['PDIN'][0] + 0.01: return None
    x6 = 0.0 if rng.random() < 0.6 else W - T['AMP6'][0] - T['AMP7'][0]
    put('AMP6', x6, H - T['AMP6'][1]); put('AMP7', x6 + T['AMP6'][0], H - T['AMP7'][1])
    if x6 + T['AMP6'][0] + T['AMP7'][0] > W + 0.01: return None
    rest = [n for n in sz if n not in P]
    mode = rng.random()
    rest = ['JACKS', 'WAKE'] + [n for n in rest if n not in ('JACKS', 'WAKE')] if False else rest
    BASE = ['JACKS', 'WAKE', 'BATIO', 'ADC', 'USBAUD', 'MUX', 'CODSUP', 'MCU', 'SWG', 'PD', 'CHGQ', 'CHG', 'BTSUP', 'AO3V', 'BOOST', 'LOG5V'] + HN
    if mode < 0.5:
        sg = rng.uniform(0.0, 4.0)
        rest.sort(key=lambda n: (BASE.index(n) if n in BASE else 40) + rng.gauss(0, sg))
    else:
        rest.sort(key=lambda n: -(T[n][0] * T[n][1] if mode < 0.7 else max(T[n]) * 40 if mode < 0.85 else T[n][1] * 60) * rng.uniform(0.6, 1.4))
    hm = rng.choice([0.3, 0.3, 0.7, 0.7, 0.85, 0.95])
    for n in rest:
        tw, th = T[n]
        xs = np.arange(0, W - tw + 1e-9, STEP)
        if n == 'BATIO': xs = np.array([W - tw])
        ys = np.arange(0, H - th + 1e-9, STEP)
        if n in ('JACKS', 'WAKE'): ys = np.array([0.0])
        X, Y = np.meshgrid(xs, ys)
        ok = np.ones(X.shape, bool)
        # occupancy test by summed-area table
        S = np.zeros((ny + 1, nx + 1)); S[1:, 1:] = occ.cumsum(0).cumsum(1)
        x0, y0 = np.floor(X * RS + 1e-6).astype(int), np.floor(Y * RS + 1e-6).astype(int)
        x1, y1 = np.minimum(np.ceil((X + tw) * RS - 1e-6).astype(int), nx), np.minimum(np.ceil((Y + th) * RS - 1e-6).astype(int), ny)
        ok &= (S[y1, x1] - S[y0, x1] - S[y1, x0] + S[y0, x0]) == 0
        for p, d in RULE.get(n, {}).items():
            if p in P:
                c = content(p)
                gx = np.maximum(np.maximum(c[0] - (X + MG + sz[n][0]), (X + MG) - c[2]), 0)
                gy = np.maximum(np.maximum(c[1] - (Y + MT + sz[n][1]), (Y + MT) - c[3]), 0)
                bad = np.hypot(gx, gy) < d
                ok &= ~bad
        if not ok.any():
            FAILS[n] = FAILS.get(n, 0) + 1; return None
        idx = np.argwhere(ok)
        if n in HN:      # farthest-point heuristic for coverage (plus jitter), bias to the board edges
            pts_ = holes_of(P) + [(-10, -10)] * 0
            ii, jj = idx[:, 0], idx[:, 1]
            cx_, cy_ = X[ii, jj] + HOLE / 2, Y[ii, jj] + HOLE / 2
            dm = np.min([np.hypot(cx_ - a, cy_ - b) for a, b in pts_], axis=0) if pts_ else np.zeros(len(ii))
            k = int(np.argmax(np.minimum(dm, 40) + np.random.default_rng(rng.randrange(1 << 30)).uniform(0, 8, len(ii)) - 0.15 * np.minimum(np.minimum(cx_, W - cx_), np.minimum(cy_, H - cy_))))
            put(n, float(X[tuple(idx[k])]), float(Y[tuple(idx[k])])); continue
        r = hm if rng.random() > 0.12 else rng.random()
        if r < 0.65:     # max-contact heuristic: touching neighbours / board edge, then top-most
            def area_(xa, ya, xb, yb):
                xa, ya, xb, yb = np.clip(xa, 0, nx), np.clip(ya, 0, ny), np.clip(xb, 0, nx), np.clip(yb, 0, ny)
                return S[yb, xb] - S[ya, xb] - S[yb, xa] + S[ya, xa]
            ii, jj = idx[:, 0], idx[:, 1]
            xa, ya = x0[ii, jj], y0[ii, jj]
            xb, yb = x1[ii, jj], y1[ii, jj]
            ring = area_(xa - 1, ya - 1, xb + 1, yb + 1) - area_(xa, ya, xb, yb)
            oob = ((xb + 1 - xa + 2) * (yb + 1 - ya + 2) - (xb - xa) * (yb - ya)) - (np.minimum(xb + 1, nx) - np.maximum(xa - 1, 0)) * (np.minimum(yb + 1, ny) - np.maximum(ya - 1, 0)) + (np.minimum(xb + 1, nx) - np.maximum(xa - 1, 0)) * (np.minimum(yb + 1, ny) - np.maximum(ya - 1, 0)) - (np.minimum(xb + 1, nx) - np.maximum(xa - 1, 0)) * (np.minimum(yb + 1, ny) - np.maximum(ya - 1, 0))
            sc = -(ring + 0.5 * np.maximum(0, (xb + 1 - xa + 2) * (yb + 1 - ya + 2) - (np.minimum(xb + 1, nx) - np.maximum(xa - 1, 0)) * (np.minimum(yb + 1, ny) - np.maximum(ya - 1, 0)))) + rng.uniform(0.0, 3.0) * ya / 10.0
            k = int(np.argmin(sc))
        elif r < 0.8: k = min(range(len(idx)), key=lambda i: (idx[i][0], idx[i][1]))
        elif r < 0.9: k = min(range(len(idx)), key=lambda i: (idx[i][0], -idx[i][1]))
        else: k = min(range(len(idx)), key=lambda i: (idx[i][1], idx[i][0]))
        put(n, float(X[tuple(idx[k])]), float(Y[tuple(idx[k])]))
    pts = holes_of(P)
    FAILS['_done'] = FAILS.get('_done', 0) + 1
    if len(pts) < 3: return None
    gx, gy = np.meshgrid(np.arange(1, W, 2.0), np.arange(1, H, 2.0))
    d = np.min([np.hypot(gx - hx, gy - hy) for hx, hy in pts], axis=0)
    if d.max() > RCOV: FAILS['_cov'] = FAILS.get('_cov', 0) + 1; FAILS['_dmax'] = min(FAILS.get('_dmax', 999), round(float(d.max()), 1)); FAILS['_pts'] = [[round(a), round(b)] for a, b in pts]; return None
    for n in ('PDIN', 'BATIO'):
        cx, cy = P[n][0] + T[n][0] / 2, P[n][1] + T[n][1] / 2
        if min(math.hypot(cx - hx, cy - hy) for hx, hy in pts) > RJ: FAILS['_rj'] = FAILS.get('_rj', 0) + 1; return None
    return P
def holes_of(P):
    pts = []
    for h in HN:
        if h in P: pts.append((P[h][0] + HOLE / 2, P[h][1] + HOLE / 2))
    for cn, lst in CH.items():
        x, y = P[cn]
        for du, dvt in lst: pts.append((x + (T[cn][0] - sz[cn][0] - 2 * MG) / 2 + MG + du, y + MT + dvt))
    return pts
Hmin, Hmax, trials = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
rng = random.Random(int(sys.argv[5]) if len(sys.argv) > 5 else 5)
found = None
for H in np.arange(Hmin, Hmax + 0.1, 2.0):
    for t in range(trials):
        P = run(float(H), rng)
        if P: found = (float(H), P); break
    print('H', H, 'ok' if found else 'no', flush=True)
    if found: break
print("fails", FAILS)
if found:
    H, P = found
    print('W', W, 'H', H, 'area', W * H)
    for n, p in sorted(P.items(), key=lambda kv: (kv[1][1], kv[1][0])): print(n, p, [round(v, 1) for v in T[n]])
    json.dump(dict(W=W, H=H, abs={n: list(p) for n, p in P.items()}), open(ROOT + 'pcb/floorplan-v7-raw%d_%s.json' % (int(W), sys.argv[5] if len(sys.argv) > 5 else ''), 'w'))
