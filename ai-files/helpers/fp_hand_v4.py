"""Hand floorplan for placement v4 (absolute tile positions, y down from the rear edge). python3 fp_hand_v4.py -> checks + writes ai-files/pcb/floorplan-v4.json"""
import json, math, sys
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
sizes = json.load(open(ROOT + 'pcb/cells-v4.json'))['sizes']
MG, MT, HOLE = 0.9, 2.4, 8.0
sz = {k: list(v) for k, v in sizes.items()}
OVH = 8.0
sz['BM83'][0] -= OVH
T = {n: (sz[n][0] + 2 * MG, sz[n][1] + MG + MT) for n in sz}
W = 115.0
H = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
exec(open(ROOT + 'pcb/fp_pos_v4.py').read())      # defines POS: name -> (x, y) or ('B', x) bottom-aligned; HOLES list
def pos(n):
    p = POS[n]
    x = p[0]; y = p[1]
    if y == 'B': y = H - T[n][1]
    if x == 'R': x = W - T[n][0]
    return x, y
def box(n):
    x, y = pos(n); return (x + MG, y + MT, x + MG + sz[n][0], y + MT + sz[n][1])
def gap(a, b):
    A, B = box(a), box(b)
    return math.hypot(max(B[0] - A[2], A[0] - B[2], 0), max(B[1] - A[3], A[1] - B[3], 0))
ANALOG = ['JACKS', 'MUX', 'ADC', 'USBAUD', 'CODSUP']
bad = []
names = list(POS)
for i, a in enumerate(names):
    ax, ay = pos(a)
    if ax < -0.01 or ax + T[a][0] > W + 0.01 or ay < -0.01 or ay + T[a][1] > H + 0.01: bad.append(('outside', a, round(ax, 1), round(ay, 1)))
    for b in names[i + 1:]:
        bx, by = pos(b)
        dx = min(ax + T[a][0], bx + T[b][0]) - max(ax, bx); dy = min(ay + T[a][1], by + T[b][1]) - max(ay, by)
        if dx > 0.01 and dy > 0.01: bad.append(('overlap', a, b, round(dx, 1), round(dy, 1)))
rep = {}
for a in ANALOG:
    for b, d in (('BM83', 15), ('AMP6', 20), ('AMP7', 20), ('BOOST', 20), ('LOG5V', 20), ('CHG', 15)):
        g = gap(a, b); rep[(a, b)] = round(g, 1)
        if g < d - 0.05: bad.append(('rule', a, b, round(g, 1), d))
for b in ('BTSUP', 'CHG', 'LOG5V', 'BOOST', 'AMP6', 'AMP7'):
    g = gap('BM83', b); rep[('BM83', b)] = round(g, 1)
    if g < 25: bad.append(('rule', 'BM83', b, round(g, 1), 25))
missing = [n for n in sz if n not in POS]
print('W', W, 'H', H, 'area', W * H, 'tiles', round(sum(t[0] * t[1] for t in T.values())), 'missing', missing)
for x in bad: print('BAD', x)
print({'%s-%s' % k: v for k, v in rep.items() if k[0] != 'BM83' or True})
if not bad and not missing:
    abs_ = {n: list(pos(n)) for n in POS}
    json.dump(dict(W=W, H=H, abs=abs_, holes=HOLES, ul=-61.0, title=[0, 0], edge=EDGE, titles_bottom=TB), open(ROOT + 'pcb/floorplan-v4.json', 'w'), indent=1)
    print('WROTE')
