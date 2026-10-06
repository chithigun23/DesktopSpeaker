"""Randomised rule-aware tile packer for placement v4: python3 fp_pack_v4.py Hmin Hmax trials -> ai-files/pcb/floorplan-v4.json
Pre-placed: rear row BM83|WAKE|JACKS|PDIN and front row AMP6|AMP7|BOOST; the other cells are placed top-left first in random order,
with hard separation rules (content-box distance, square inflation) against the cells already placed."""
import json, math, random, sys
import numpy as np
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
sizes = json.load(open(ROOT + 'pcb/cells-v4.json'))['sizes']
MG, MT, HOLE = 0.9, 2.4, 8.0
sz = {k: list(v) for k, v in sizes.items()}
sz['BM83'][0] -= 8.0
for h in ('H1', 'H2', 'H3', 'H4'): sz[h] = [HOLE - 2 * MG, HOLE - MG - MT]
T = {n: (sz[n][0] + 2 * MG + 0.2, sz[n][1] + MG + MT + 0.3) for n in sz}
W = float(sys.argv[4]) if len(sys.argv) > 4 else 115.0
ANALOG = ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']
RULE = {}
def addr(a, b, d): RULE.setdefault(a, {})[b] = d; RULE.setdefault(b, {})[a] = d
for a in ANALOG:
    addr('BM83', a, 15.2)
    for b in ('AMP6', 'AMP7', 'BOOST', 'LOG5V'): addr(a, b, 20.4)
    addr('CHG', a, 14.0)
for b in ('BTSUP', 'CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7'): addr('BM83', b, 25.4)
for h in ('H1', 'H2', 'H3', 'H4'): addr('BM83', h, 8.0)
FAILS = {}
def run(H, rng):
    nx, ny = int(W) + 1, int(H) + 1
    occ = np.zeros((ny, nx), bool)
    P = {}
    def put(n, x, y):
        P[n] = (x, y)
        occ[int(math.floor(y)):int(math.ceil(y + T[n][1])), int(math.floor(x)):int(math.ceil(x + T[n][0]))] = True
    def content(n):
        x, y = P[n]; return (x + MG, y + MT, x + MG + sz[n][0], y + MT + sz[n][1])
    put('BM83', 0, 0); put('WAKE', T['BM83'][0], 0); put('JACKS', T['BM83'][0] + T['WAKE'][0], 0); put('PDIN', W - T['PDIN'][0], 0)
    if T['BM83'][0] + T['WAKE'][0] + T['JACKS'][0] > W - T['PDIN'][0] + 0.01: return None
    put('AMP6', 0, H - T['AMP6'][1]); put('AMP7', T['AMP6'][0], H - T['AMP7'][1])
    put('H1', 0, H - T['AMP6'][1] - 8); put('H2', W - 8, H - 8); put('H3', W - 8, 25); put('H4', 0, 44)
    rest = [n for n in sz if n not in P]
    rest.sort(key=lambda n: -T[n][0] * T[n][1] * rng.uniform(0.6, 1.4))
    for n in rest:
        tw, th = T[n]
        xs = np.arange(0, int(W - tw) + 1, 1.0)
        if n == 'BATIO': xs = np.array([W - tw])
        elif n[0] == 'H': xs = np.array([0.0, W - tw])
        ys = np.arange(0, H - th + 1, 1.0)
        X, Y = np.meshgrid(xs, ys)
        ok = np.ones(X.shape, bool)
        # occupancy test by summed-area table
        S = np.zeros((ny + 1, nx + 1)); S[1:, 1:] = occ.cumsum(0).cumsum(1)
        x0, y0 = np.floor(X).astype(int), np.floor(Y).astype(int)
        x1, y1 = np.minimum(np.ceil(X + tw).astype(int), nx), np.minimum(np.ceil(Y + th).astype(int), ny)
        ok &= (S[y1, x1] - S[y0, x1] - S[y1, x0] + S[y0, x0]) == 0
        for p, d in RULE.get(n, {}).items():
            if p in P:
                c = content(p)
                bad = (X + MG < c[2] + d) & (X + MG + sz[n][0] > c[0] - d) & (Y + MT < c[3] + d) & (Y + MT + sz[n][1] > c[1] - d)
                ok &= ~bad
        if not ok.any():
            FAILS[n] = FAILS.get(n, 0) + 1; return None
        idx = np.argwhere(ok)
        r = rng.random()
        if r < 0.5: k = min(range(len(idx)), key=lambda i: (idx[i][0], idx[i][1]))
        elif r < 0.8: k = min(range(len(idx)), key=lambda i: (idx[i][0], -idx[i][1]))
        else: k = min(range(len(idx)), key=lambda i: (idx[i][1], idx[i][0]))
        put(n, float(X[tuple(idx[k])]), float(Y[tuple(idx[k])]))
    return P
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
    json.dump(dict(W=W, H=H, abs={n: list(p) for n, p in P.items()}), open(ROOT + 'pcb/floorplan-v4-raw%s.json' % (sys.argv[5] if len(sys.argv) > 5 else ''), 'w'))
