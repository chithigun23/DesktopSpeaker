"""Offline floorplan annealer for placement v4 (cell tiles, hard separation rules, edge constraints, 4 corner holes).
usage: python3 fp_search_v4.py W seed iters -> writes ai-files/pcb/floorplan-v4.json (abs tile positions, y down from the rear edge)."""
import json, random, math, sys
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
W = float(sys.argv[1]); seed = int(sys.argv[2]); ITER = int(sys.argv[3])
sizes = json.load(open(ROOT + 'pcb/cells-v4.json'))['sizes']
MG, MT, HOLE = 0.9, 2.4, 8.0
sz = {k: list(v) for k, v in sizes.items()}
sz['BM83'][0] -= 8.0
for h in ('H1', 'H2', 'H3', 'H4'):
    sz[h] = [HOLE - 2 * MG, HOLE - MG - MT]
N = list(sz)
T = {n: (sz[n][0] + 2 * MG, sz[n][1] + MG + MT) for n in N}
ANALOG = ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']
RULES = []
for a in ANALOG:
    RULES += [('BM83', a, 16.5), ('AMP6', a, 21.5), ('AMP7', a, 21.5), ('BOOST', a, 21.5), ('LOG5V', a, 21.5), ('CHG', a, 15.5)]
for b in ['BTSUP', 'CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7']:
    RULES.append(('BM83', b, 26.0))
for h in ('H1', 'H2', 'H3', 'H4'):
    RULES.append(('BM83', h, 14.0))
rng = random.Random(seed)
P = {}
FIXED = {}
x = 0.0
for n in ['BM83', 'WAKE', 'JACKS', 'PDIN']:
    P[n] = [x, 0.0]; FIXED[n] = 1; x += T[n][0]
x = 0.0; y = max(T[n][1] for n in FIXED); rh = 0.0
for n in sorted([n for n in N if n not in FIXED], key=lambda n: -T[n][1]):          # initial shelf packing
    if x + T[n][0] > W: x, y, rh = 0.0, y + rh, 0.0
    P[n] = [x, y]; x += T[n][0]; rh = max(rh, T[n][1])
def box(n):
    return (P[n][0] + MG, P[n][1] + MT, P[n][0] + MG + sz[n][0], P[n][1] + MT + sz[n][1])
def gap(a, b):
    A, B = box(a), box(b)
    return math.hypot(max(B[0] - A[2], A[0] - B[2], 0), max(B[1] - A[3], A[1] - B[3], 0))
def overlap(a, b):
    ax, ay = P[a]; bx, by = P[b]
    dx = min(ax + T[a][0], bx + T[b][0]) - max(ax, bx); dy = min(ay + T[a][1], by + T[b][1]) - max(ay, by)
    return dx * dy if dx > 0 and dy > 0 else 0.0
REAR = ['BM83', 'JACKS', 'PDIN', 'WAKE']
FIXED = {}
FRONT = ['AMP6', 'AMP7', 'H1', 'H2']
def total(Hc):
    c = 0.0
    for n in N:
        x0, y0 = P[n]
        c += 30 * (max(0, -x0) + max(0, x0 + T[n][0] - W) + max(0, -y0))
        if n in REAR: c += 20 * abs(y0)
        if n in FRONT: c += 20 * abs(y0 + T[n][1] - Hc)
    c += 20 * (abs(P['BM83'][0]) + abs(P['BATIO'][0] + T['BATIO'][0] - W) + abs(P['H1'][0]) + abs(P['H2'][0] + T['H2'][0] - W) + 0.2 * abs(P['MCU'][0]))
    for i, a in enumerate(N):
        for b in N[i + 1:]:
            o = overlap(a, b)
            if o: c += 1.5 * o
    for a, b, d in RULES:
        g = gap(a, b)
        if g < d: c += 25 * (d - g)
    return c
def Hof():
    return max(P[n][1] + T[n][1] for n in N)
Hh = 150.0
hand = {'AMP6': (0, Hh - T['AMP6'][1]), 'AMP7': (T['AMP6'][0], Hh - T['AMP7'][1]), 'BOOST': (T['AMP6'][0] + T['AMP7'][0], Hh - T['BOOST'][1]),
        'MCU': (0, 38.1), 'BTSUP': (0, 62.8), 'H1': (0, Hh - 8), 'H2': (W - 8, Hh - 8), 'BATIO': (W - T['BATIO'][0], 60)}
for k, v in hand.items(): P[k] = [v[0], v[1]]
best = None
cur = None
for it in range(ITER):
    Tmp = 150 * (0.002 ** (it / ITER))
    Hc = Hof()
    if cur is None: cur = total(Hc) + 12 * Hc
    n = rng.choice(N)
    if n in FIXED: continue
    old = list(P[n]); old2 = None
    r = rng.random()
    if r < 0.6:
        s = 8 * (1 - it / ITER) + 0.5
        P[n] = [round((old[0] + rng.gauss(0, s)) * 2) / 2, round((old[1] + rng.gauss(0, s)) * 2) / 2]
    elif r < 0.85:
        m = rng.choice(N)
        if m in FIXED: continue
        old2 = (m, list(P[m])); P[n], P[m] = list(P[m]), list(P[n])
    else:
        P[n] = [round(rng.uniform(0, W - T[n][0]) * 2) / 2, round(rng.uniform(0, Hc) * 2) / 2]
    Hn = Hof(); new = total(Hn) + 12 * Hn
    if new <= cur or rng.random() < math.exp((cur - new) / Tmp): cur = new
    else:
        P[n] = old
        if old2: P[old2[0]] = old2[1]
    if best is None or cur < best[0]: best = (cur, {k: list(v) for k, v in P.items()})
P = best[1]
H = Hof()
v = total(H)
print('cost %.1f penalties %.1f  W %.1f H %.1f area %.0f' % (best[0], v, W, H, W * H))
for n in N: print(n, [round(t, 1) for t in P[n]], [round(t, 1) for t in T[n]])
print('viol', [(a, b, round(gap(a, b), 1), d) for a, b, d in RULES if gap(a, b) < d], 'overlaps', [(a, b) for i, a in enumerate(N) for b in N[i + 1:] if overlap(a, b)])
json.dump(dict(W=W, H=H, abs={n: P[n] for n in N}, score=v), open('/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/48064651-bbac-4d10-bf68-aa2bb3ba73e8/scratchpad/fp_%d.json' % seed, 'w'))
