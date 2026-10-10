"""flatpak: route_r6i_bends.py BOARD [REF_BOARD] [--json OUT.json] [--all]
Corner-radius check (user rule 2026-10-09, pcb-layout-best-practices.md sec. 13): a track segment whose two ends are both
plain bends (each end joins exactly one other same-net, same-layer, same-width-or-not segment, no via/pad/third track there)
and whose turn angles are both >= 10 deg, with length < max(3 x width, 0.4 mm). 'corner' = both bends turn the same way
(acts like one sharp corner); 'jog' = opposite turns (short S-offset). Also lists single bends sharper than 90 deg ('acute').
With REF_BOARD, each hit is tagged 'inherited' when the same middle segment (endpoints within 0.02 mm) exists there."""
import sys, math, json, collections
import pcbnew
MM = 1e6
def load(path): return loadb(pcbnew.LoadBoard(path))
def loadb(b):
    segs = []
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetClass() == 'PCB_ARC': continue
        segs.append((str(t.GetNetname()), t.GetLayer(), (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM), t.GetWidth() / MM))
    vias = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA': vias[str(t.GetNetname())].append((t.GetX() / MM, t.GetY() / MM, t.GetWidth(pcbnew.F_Cu) / MM / 2))
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            pads[str(p.GetNetname())].append(p)
    return b, segs, vias, pads
def key(p): return (round(p[0] / 0.01), round(p[1] / 0.01))
def hits(path): return hits_from(pcbnew.LoadBoard(path))
def hits_from(bd):
    b, segs, vias, pads = loadb(bd); return hits_core(b, segs, vias, pads)
def hits_core(b, segs, vias, pads, only=None):
    by = collections.defaultdict(list)
    for i, s in enumerate(segs):
        if only is None or s[0] == only: by[(s[0], s[1])].append(i)
    out = []
    for (net, L), idx in by.items():
        if net in ('', 'GND'): pass
        ends = collections.defaultdict(list)
        for i in idx:
            ends[key(segs[i][2])].append((i, 0)); ends[key(segs[i][3])].append((i, 1))
        def plain(pt, k):
            lst = ends[k]
            if len(lst) != 2: return None
            for vx, vy, r in vias[net]:
                if math.hypot(vx - pt[0], vy - pt[1]) <= r: return None
            v = pcbnew.VECTOR2I(int(pt[0] * MM), int(pt[1] * MM))
            for p in pads[net]:
                if p.IsOnLayer(L) and p.HitTest(v): return None
            return lst
        def other(i, k):
            for j, e in ends[k]:
                if j != i: return j, e
        def ang(u, v):
            a = math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]); return math.degrees(a)
        for i in idx:
            n_, l_, a, c, w = segs[i]
            Ln = math.hypot(c[0] - a[0], c[1] - a[1])
            if Ln < 1e-6: continue
            lim = max(3 * w, 0.4)
            ka, kc = key(a), key(c)
            pa, pc = plain(a, ka), plain(c, kc)
            d = (c[0] - a[0], c[1] - a[1])
            turns = []
            for pt, k, pl, sgn in ((a, ka, pa, -1), (c, kc, pc, 1)):
                if not pl: turns.append(None); continue
                j, e = other(i, k); s2 = segs[j]
                far = s2[3] if e == 0 else s2[2]
                v = (far[0] - pt[0], far[1] - pt[1])
                if math.hypot(*v) < 1e-6: turns.append(None); continue
                # direction of travel: through a towards c; at a the incoming is from far to a
                if sgn < 0: t_ = ang((pt[0] - far[0], pt[1] - far[1]), d)
                else: t_ = ang(d, v)
                turns.append(t_)
                if abs(t_) > 90.5: out.append(dict(kind='acute', net=net, layer=b.GetLayerName(L), at=[round(pt[0], 2), round(pt[1], 2)], turn=round(t_, 1), w=w))
            if Ln < lim and turns[0] is not None and turns[1] is not None and abs(turns[0]) >= 10 and abs(turns[1]) >= 10:
                kind = 'corner' if turns[0] * turns[1] > 0 else 'jog'
                out.append(dict(kind=kind, net=net, layer=b.GetLayerName(L), a=[round(a[0], 3), round(a[1], 3)], b=[round(c[0], 3), round(c[1], 3)], len=round(Ln, 3), lim=round(lim, 2), turns=[round(turns[0], 1), round(turns[1], 1)], w=w))
    # de-duplicate acute (reported from both segments)
    seen = set(); res = []
    for h in out:
        k = (h['kind'], h['net'], h['layer'], tuple(h.get('at', h.get('a'))), tuple(h.get('b', ())))
        if k in seen: continue
        seen.add(k); res.append(h)
    return res
if __name__ == '__main__':
    H = hits(sys.argv[1])
    ref = None
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        R = hits(sys.argv[2]); ref = set()
        for h in R:
            if 'a' in h: ref.add((h['net'], h['layer'], key(h['a']), key(h['b']))); ref.add((h['net'], h['layer'], key(h['b']), key(h['a'])))
            else: ref.add((h['net'], h['layer'], key(h['at'])))
    for h in H:
        if ref is not None:
            k = (h['net'], h['layer'], key(h['a']), key(h['b'])) if 'a' in h else (h['net'], h['layer'], key(h['at']))
            h['inherited'] = k in ref
    c = collections.Counter((h['kind'], h.get('inherited', False)) for h in H)
    print('bend hits', len(H), dict(c))
    if '--all' in sys.argv:
        for h in sorted(H, key=lambda h: (h.get('inherited', False), h['kind'], h['net'])): print(' ', h)
    if '--json' in sys.argv: json.dump(H, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=0)
