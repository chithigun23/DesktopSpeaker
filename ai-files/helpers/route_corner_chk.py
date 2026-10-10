"""flatpak: route_corner_chk.py BOARD [OUT.json] : read-only; lists short middle segments between two bends (min(3*width, ...) rule)"""
import sys, json, math, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
segs = [t for t in b.Tracks() if t.GetClass() == 'PCB_TRACK']
pts = collections.defaultdict(list)  # (layer,net,x,y)->segments
others = set()  # via/pad positions
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA': others.add((round(mm(t.GetPosition().x), 3), round(mm(t.GetPosition().y), 3)))
for f in b.GetFootprints():
    for p in f.Pads(): others.add((round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)))
def key(t, p): return (t.GetLayer(), t.GetNetname(), round(mm(p.x), 3), round(mm(p.y), 3))
for t in segs:
    pts[key(t, t.GetStart())].append(t); pts[key(t, t.GetEnd())].append(t)
def ang(t, p):
    o = t.GetEnd() if (t.GetStart().x == p.x and t.GetStart().y == p.y) else t.GetStart()
    return math.atan2(mm(o.y - p.y), mm(o.x - p.x))
def bend(t, p, k):
    l = pts[k]
    if len(l) != 2 or (k[2], k[3]) in others: return False
    a1, a2 = ang(l[0], p), ang(l[1], p)
    d = abs((a1 - a2 + math.pi) % (2 * math.pi) - math.pi)
    return d < math.pi - 0.05  # not collinear
hits = []
for t in segs:
    w = mm(t.GetWidth()); thr = max(3 * w, 0.4); L = mm(t.GetLength())
    if L >= thr: continue
    s, e = t.GetStart(), t.GetEnd()
    if bend(t, s, key(t, s)) and bend(t, e, key(t, e)):
        hits.append(dict(net=t.GetNetname(), layer=b.GetLayerName(t.GetLayer()), x=round(mm(s.x), 2), y=round(mm(s.y), 2), len=round(L, 3), w=round(w, 3)))
cnt = collections.Counter(h['net'] for h in hits)
print('hits', len(hits), 'nets', len(cnt)); print(cnt.most_common(15))
print(collections.Counter(h['layer'] for h in hits))
if len(sys.argv) > 2: json.dump(hits, open(sys.argv[2], 'w'), indent=0)
