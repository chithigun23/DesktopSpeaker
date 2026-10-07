"""route_p2_core.py : component finder and net router (needs route_p2_lib)."""
import math, numpy as np, ctypes, pcbnew
from route_p2_lib import *

def padkey(p): return (p.GetParentFootprint().GetReference(), str(p.GetNumber()))

def stub_ok(ctx, net, nearby, c, e, w, rip, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(ctx.b); t.SetStart(pcbnew.VECTOR2I(int(c[0]*MM), int(c[1]*MM))); t.SetEnd(pcbnew.VECTOR2I(int(e[0]*MM), int(e[1]*MM)))
    t.SetLayer(layer); t.SetWidth(int(w*MM)); sh = t.GetEffectiveShape()
    clr = int(0.2*MM) - 200
    for kind, o in nearby:
        if kind == 'pad':
            if o.IsOnLayer(layer) and o.GetEffectiveShape(layer).Collide(sh, clr): return False
        elif kind == 'trk':
            if o.GetLayer() == layer and o.GetEffectiveShape().Collide(sh, clr): return False
        else:
            if o.GetEffectiveShape(layer).Collide(sh, clr): return False
    return True

def find_stubs(ctx, net, pad, win, code0, rip, wst=0.2):
    """candidate exit points (exact mm) along the pad axes whose straight stub is exact-legal and whose cell is routable"""
    y0, y1, x0, x1 = win
    cx, cy = pad.GetX() / MM, pad.GetY() / MM
    bbx = pad.GetBoundingBox(); hw, hh = bbx.GetWidth() / MM / 2, bbx.GetHeight() / MM / 2
    near = []
    r = 3.0 * MM; bb = pcbnew.BOX2I(pcbnew.VECTOR2I(int(cx*MM - r), int(cy*MM - r)), pcbnew.VECTOR2I(int(2*r), int(2*r)))
    ripn = set(ctx.netname[i] for i in (rip or []))
    for f in ctx.b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname()) != net and bb.Intersects(p.GetBoundingBox()): near.append(('pad', p))
    for t in ctx.b.Tracks():
        n = str(t.GetNetname())
        if n == net or n in ripn or not bb.Intersects(t.GetBoundingBox()): continue
        near.append(('via' if t.GetClass() == 'PCB_VIA' else 'trk', t))
    dirs = [(1, 0, hw), (-1, 0, hw), (0, 1, hh), (0, -1, hh)]
    dirs.sort(key=lambda d: -d[2])
    out = []
    for dx, dy, half in dirs:
        if half < max(hw, hh) - 1e-6 and out: continue  # prefer long axis only
        for j in range(0, 60):
            d = half + 0.05 * j
            e = (cx + dx * d, cy + dy * d)
            gy = int(round(ctx.cy(e[1]))) - y0; gx = int(round(ctx.cx(e[0]))) - x0
            if gy < 0 or gx < 0 or gy >= y1 - y0 or gx >= x1 - x0: break
            if code0[gy, gx] == 0: continue
            if stub_ok(ctx, net, near, (cx, cy), e, wst, rip): out.append((e, (dx, dy))); break
    return out

def _outline_polys(z, ly):
    fp = z.GetFilledPolysList(ly); res = []
    for i in range(fp.OutlineCount()):
        ps = pcbnew.SHAPE_POLY_SET(); ps.AddOutline(fp.Outline(i))
        for h in range(fp.HoleCount(i)): ps.AddHole(fp.Hole(i, h))
        res.append(ps)
    return res

def _item_pts(it, ly):
    k, o = it[0], it[1]
    if k == 'via': return [o.GetPosition()]
    if k == 'trk':
        s_, e_ = o.GetStart(), o.GetEnd()
        return [s_, e_, pcbnew.VECTOR2I((s_.x + e_.x) // 2, (s_.y + e_.y) // 2)]
    pts = [o.GetPosition()]
    try:
        ps = o.GetEffectivePolygon(ly)
        for i in range(ps.OutlineCount()):
            oo = ps.Outline(i)
            pts += [oo.CPoint(k2) for k2 in range(0, oo.PointCount(), max(1, oo.PointCount() // 8))]
    except Exception: pass
    return pts

def comps_of(ctx, net):
    b = ctx.b
    its = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname()) == net: its.append(('pad', p, [l for l in ALL4 if p.IsOnLayer(l)]))
    for t in b.Tracks():
        if str(t.GetNetname()) != net: continue
        if t.GetClass() == 'PCB_VIA': its.append(('via', t, ALL4))
        else: its.append(('trk', t, [t.GetLayer()]))
    zn = []   # (zone, layer, idx, polyset)
    for z in b.Zones():
        if z.GetIsRuleArea() or str(z.GetNetname()) != net: continue
        for ly in ALL4:
            if z.IsOnLayer(ly):
                for idx, ps in enumerate(_outline_polys(z, ly)): zn.append((z, ly, idx, ps))
    n = len(its); par = list(range(n + len(zn)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def uni(a, c): par[find(a)] = find(c)
    def shp(it, ly):
        return it[1].GetEffectiveShape(ly) if it[0] == 'pad' else it[1].GetEffectiveShape()
    for i in range(n):
        for j in range(i + 1, n):
            if its[i][0] == 'pad' and its[j][0] == 'pad': continue
            for ly in set(its[i][2]) & set(its[j][2]):
                try:
                    if shp(its[i], ly).Collide(shp(its[j], ly), 0): uni(i, j); break
                except Exception: pass
    for k, (z, ly, idx, ps) in enumerate(zn):
        bb = ps.BBox()
        for i, it in enumerate(its):
            if ly not in it[2]: continue
            for pt in _item_pts(it, ly):
                if bb.Contains(pt) and ps.Collide(pt, 0): uni(i, n + k); break
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(its[i])
    for k, (z, ly, idx, ps) in enumerate(zn):
        r = find(n + k)
        if r in groups: groups[r].append(('zone', z, ly, idx))
    comps = [g for g in groups.values() if any(x[0] == 'pad' for x in g)]
    return comps

def comp_refs(ctx, comp):
    pts = []
    for it in comp:
        if it[0] in ('pad', 'via'): pts.append((it[1].GetPosition().x / MM, it[1].GetPosition().y / MM))
        elif it[0] == 'trk': pts += [(it[1].GetStart().x / MM, it[1].GetStart().y / MM), (it[1].GetEnd().x / MM, it[1].GetEnd().y / MM)]
        elif it[0] == 'zone':
            fp = it[1].GetFilledPolysList(it[2])
            if it[3] < fp.OutlineCount():
                o = fp.Outline(it[3])
                for k in range(0, o.PointCount(), 6): pts.append((o.CPoint(k).x / MM, o.CPoint(k).y / MM))
    return pts

def raster_comp(ctx, comp, win, skip=()):
    y0, y1, x0, x1 = win
    arr = np.zeros((3, y1 - y0, x1 - x0), np.uint8)
    tmp = np.zeros((ctx.H, ctx.W), np.uint8) if False else None
    def mark(li, res):
        if res is None: return
        gy0, gy1, gx0, gx1, m = res
        # intersect with window
        ay0 = max(gy0, y0); ay1 = min(gy1, y1); ax0 = max(gx0, x0); ax1 = min(gx1, x1)
        if ay1 <= ay0 or ax1 <= ax0: return
        arr[li, ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] |= m[ay0 - gy0:ay1 - gy0, ax0 - gx0:ax1 - gx0]
    scratch = np.zeros((ctx.H, ctx.W), np.int8)  # fill target (unused values)
    dummy = np.zeros((ctx.H, ctx.W), np.int8)
    for it in comp:
        if it[0] == 'pad':
            if padkey(it[1]) in skip: continue
            for li, L in enumerate(LAYS):
                if it[1].IsOnLayer(L):
                    for ring in ctx.pad_poly(it[1], L):
                        if len(ring) >= 3: mark(li, ctx.poly_fill(dummy, [ring], 0))
        elif it[0] == 'via':
            c = (it[1].GetPosition().x / MM, it[1].GetPosition().y / MM)
            for li in range(3): mark(li, ctx.circ_fill(dummy, c, it[1].GetWidth(pcbnew.F_Cu) / MM / 2, 0))
        elif it[0] == 'trk':
            if it[1].GetLayer() in LAYS:
                t = it[1]; mark(LAYS.index(t.GetLayer()), ctx.seg_fill(dummy, (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM), t.GetWidth() / MM, 0))
        elif it[0] == 'zone':
            if it[2] in LAYS:
                zp = ctx.zone_polys(it[1], it[2])
                if it[3] < len(zp): mark(LAYS.index(it[2]), ctx.poly_fill(dummy, zp[it[3]], 0))
    return arr

def route_pair(ctx, net, A, B, P):
    """P: dict layers(list idx), tiers(list widths desc), floor, cme, dv, drill, viacost. returns list of items added or None"""
    me = ctx.netid[net]
    ra = comp_refs(ctx, A); rb = comp_refs(ctx, B)
    allp = ra + rb
    for margin in P.get('margins', (8, 20)):
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        x0 = max(int(ctx.cx(min(xs) - margin)), 0); x1 = min(int(ctx.cx(max(xs) + margin)), ctx.W)
        y0 = max(int(ctx.cy(min(ys) - margin)), 0); y1 = min(int(ctx.cy(max(ys) + margin)), ctx.H)
        win = (y0, y1, x0, x1)
        res = _search(ctx, net, me, A, B, ra, rb, win, P)
        if res is not None: return res
    return None

def _search(ctx, net, me, A, B, ra, rb, win, P):
    y0, y1, x0, x1 = win; h = y1 - y0; w = x1 - x0
    tiers = P['tiers']
    wds = []
    for t in tiers:
        if t not in wds: wds.append(t)
    wds = wds[:4]
    nl = 3
    rip = P.get('rip')
    pen = np.zeros((nl, h, w), np.uint8)
    if rip:
        for li in range(nl): pen[li] = ctx.ripmask(me, li, y0, y1, x0, x1, wds[0], P['cme'], rip)
    code = np.zeros((nl, h, w), np.uint8)
    # own-net pad cells (this net) for neck permission
    ownpad = np.zeros((h, w), bool)
    for f in ctx.b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname()) == net:
                cxp = ctx.cx(p.GetX() / MM) - x0; cyp = ctx.cy(p.GetY() / MM) - y0
                R = 3.0 / G
                ownpad[max(int(cyp - R), 0):max(int(cyp + R), 0), max(int(cxp - R), 0):max(int(cxp + R), 0)] = True
    for li in range(nl):
        for ti, wd in enumerate(wds):
            bl = ctx.obstacle(me, li, y0, y1, x0, x1, wd, P['cme'], rip=rip, gndc=P.get('gndc', 0.2))
            ok = ~bl
            if wd < P['floor'] - 1e-9: ok &= ownpad
            sel = ok & (code[li] == 0)
            code[li][sel] = ti + 1
    # fine pads: replaced by exact stubs
    fine = set(); stubs = {}
    for comp in (A, B):
        has_other = any(it[0] in ('trk', 'zone', 'via') for it in comp)
        for it in comp:
            if it[0] != 'pad' or has_other: continue
            p = it[1]
            if not p.IsOnLayer(pcbnew.F_Cu) or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            gy = int(ctx.cy(p.GetY() / MM)) - y0; gx = int(ctx.cx(p.GetX() / MM)) - x0
            if not (0 <= gy < h and 0 <= gx < w): continue
            if code[0, gy, gx] not in (1, 2) and 0 in P['layers']:
                fine.add(padkey(p))
    srcA = raster_comp(ctx, A, win, fine); tgtB = raster_comp(ctx, B, win, fine)
    code0 = code[0].copy()
    for comp, arrx in ((A, srcA), (B, tgtB)):
        for it in comp:
            if it[0] == 'pad' and padkey(it[1]) in fine:
                for e, d in find_stubs(ctx, net, it[1], win, code0, P.get('rip')):
                    gy = int(round(ctx.cy(e[1]))) - y0; gx = int(round(ctx.cx(e[0]))) - x0
                    arrx[0, gy, gx] = 1; stubs[(0, gy + y0, gx + x0)] = ((it[1].GetX() / MM, it[1].GetY() / MM), e)
    ownmask = srcA | tgtB
    for li in range(nl):
        zc = (code[li] == 0) & (ownmask[li] > 0)
        code[li][zc] = len(wds)  # narrowest
    # via ok
    dv = P['dv']
    vb = ctx.via_obstacle(me, y0, y1, x0, x1, dv, P['cme'], rip=rip, gndc=P.get('gndc', 0.2))
    viaok = (~vb).astype(np.uint8)
    # layers
    lay_ok = np.zeros(nl, np.uint8)
    for l in P['layers']: lay_ok[l] = 1
    if not P.get('vias', True): viaok[:] = 0
    for l in range(nl):
        if not lay_ok[l]: code[l][:] = 0
    src = (srcA > 0).astype(np.uint8); tgt = (tgtB > 0).astype(np.uint8)
    for l in range(nl):
        if not lay_ok[l]: src[l][:] = 0; tgt[l][:] = 0
    if not src.any() or not tgt.any(): return None
    # target heuristic point: target cell nearest source centroid
    sy, sx = np.nonzero(src.any(axis=0)); cy_, cx_ = sy.mean(), sx.mean()
    ty_, tx_ = np.nonzero(tgt.any(axis=0)); k = np.argmin((ty_ - cy_) ** 2 + (tx_ - cx_) ** 2)
    ty, tx = int(ty_[k]), int(tx_[k])
    sc = (ctypes.c_float * 5)(0, 1.0, 1.15, 1.6, 2.2)
    path = np.zeros((400000, 3), np.int32)
    code = np.ascontiguousarray(code); src = np.ascontiguousarray(src); tgt = np.ascontiguousarray(tgt)
    n = lib.astar(nl, h, w, code.ctypes.data_as(P_), src.ctypes.data_as(P_), tgt.ctypes.data_as(P_), viaok.ctypes.data_as(P_), lay_ok.ctypes.data_as(P_),
                  pen.ctypes.data_as(P_), sc, ctypes.c_float(P['viacost'] / G), ctypes.c_float(P.get('turn', 1.5)), ctypes.c_float(P.get('hw', 1.0)), ty, tx,
                  path.ctypes.data_as(P_), 400000, ctypes.c_int64(P.get('maxexp', 30_000_000)))
    if n <= 0: return None
    pts = [(int(path[i, 0]), int(path[i, 1]), int(path[i, 2])) for i in range(n)]  # target -> source
    pts = pts[::-1]  # source -> target
    # per-cell widths
    def cw(li, y, x):
        c = code[li, y, x]; return wds[c - 1] if c else wds[-1]
    # in-pad snapping at both ends
    items = []
    ends = [0, 1]
    pl = [(l, y + y0, x + x0, cw(l, y, x), (srcA[l, y, x] > 0) or (tgtB[l, y, x] > 0)) for (l, y, x) in pts]
    return pl, wds, stubs
P_ = ctypes.c_void_p

RULE_CL = {'AUDIO': 0.5, 'I2S_CLK': 0.4, 'USB': 0.2, 'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3, 'SWITCH': 0.3}
def req_clr(ca, cb):
    c = 0.2
    for x, y in ((ca, cb), (cb, ca)):
        r = RULE_CL.get(x, 0.2)
        if r > 0.2:
            if y == 'GND' and x in ('AUDIO', 'I2S_CLK', 'SWITCH'): continue
            if x == 'SWITCH' and y == 'SWITCH': continue
            if x == 'AUDIO' and y == 'AUDIO': continue
            c = max(c, r)
    return c

def fit_width(ctx, t, net, widths):
    """largest width (from widths, descending) with exact legal clearance for new track t; returns True if legal"""
    b = ctx.b; cls = ctx.cls.get(net, 'SIGNAL')
    bb = t.GetBoundingBox(); bb.Inflate(int(1.5 * MM)); sh0 = t
    near = []
    for f in b.GetFootprints():
        if not bb.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if (str(p.GetNetname()) != net or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH) and bb.Intersects(p.GetBoundingBox()): near.append(('pad', p, 'x'))
    for u in b.Tracks():
        n = str(u.GetNetname())
        if n == net or u.m_Uuid.AsString() == t.m_Uuid.AsString() or not bb.Intersects(u.GetBoundingBox()): continue
        near.append(('via' if u.GetClass() == 'PCB_VIA' else 'trk', u, ctx.cls.get(n, 'SIGNAL')))
    L = t.GetLayer()
    for w in widths:
        t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape(); ok = True
        for kind, o, c in near:
            if kind == 'pad':
                if o.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    if o.GetEffectiveHoleShape().Collide(sh, int(0.27 * MM)): ok = False; break
                elif o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(sh, int(0.2 * MM) - 150): ok = False; break
            else:
                cc = int((req_clr(cls, c)) * MM) - 150
                if kind == 'via':
                    if o.GetEffectiveShape(L).Collide(sh, cc): ok = False; break
                elif o.GetLayer() == L and o.GetEffectiveShape().Collide(sh, cc): ok = False; break
        if ok: return True
    return False

def simplify_run(ctx, net, pts):
    """greedy straight shortcuts over one same-layer run [(l,x,y,w)...] keeping exact legality"""
    if len(pts) < 3: return pts
    b = ctx.b; cls = ctx.cls.get(net, 'SIGNAL'); L = LAYS[pts[0][0]]
    xs = [p[1] for p in pts]; ys = [p[2] for p in pts]
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(int((min(xs) - 2.5) * MM), int((min(ys) - 2.5) * MM)), pcbnew.VECTOR2I(int((max(xs) - min(xs) + 5) * MM), int((max(ys) - min(ys) + 5) * MM)))
    near = []
    for f in b.GetFootprints():
        if not box.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if ((str(p.GetNetname()) != net and p.IsOnLayer(L)) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH) and box.Intersects(p.GetBoundingBox()): near.append(('pad', p, 'x'))
    for u in b.Tracks():
        n = str(u.GetNetname())
        if n == net or not box.Intersects(u.GetBoundingBox()): continue
        if u.GetClass() != 'PCB_VIA' and u.GetLayer() != L: continue
        near.append(('via' if u.GetClass() == 'PCB_VIA' else 'trk', u, ctx.cls.get(n, 'SIGNAL')))
    def legal(a, c, w):
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * MM)), int(round(a[1] * MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(c[0] * MM)), int(round(c[1] * MM))))
        t.SetLayer(L); t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape()
        for kind, o, cc in near:
            if kind == 'pad':
                if o.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    if o.GetEffectiveHoleShape().Collide(sh, int(0.28 * MM)): return False
                elif o.GetEffectiveShape(L).Collide(sh, int(0.2 * MM) + 5000): return False
            else:
                cl = int(req_clr(cls, cc) * MM) + 5000
                if (o.GetEffectiveShape(L) if kind == 'via' else o.GetEffectiveShape()).Collide(sh, cl): return False
        return True
    out = [pts[0]]; i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1; done = False
        while j > i + 1:
            w = min(p[3] for p in pts[i:j + 1])
            if legal((pts[i][1], pts[i][2]), (pts[j][1], pts[j][2]), w):
                out.append((pts[j][0], pts[j][1], pts[j][2], w)); i = j; done = True; break
            j -= 1
        if not done: out.append(pts[i + 1]); i += 1
    return out

def emit(ctx, net, pl, Pp, stubs):
    """convert cell path to tracks/vias on the board; returns number of new items"""
    b = ctx.b; ni = b.FindNet(net)
    pts = [(l, ctx.x0 + x * G, ctx.y0 + y * G, wd) for (l, y, x, wd, own) in pl]
    own = [o for *_, o in pl]
    if len(pl) == 1:
        l, x, y = pl[0][0], pts[0][1], pts[0][2]; pt = pcbnew.VECTOR2I(int(x * MM), int(y * MM)); added = []
        kk = (pl[0][0], pl[0][1], pl[0][2])
        if kk in stubs:
            c, e = stubs[kk]
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(round(c[0] * MM)), int(round(c[1] * MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(e[0] * MM)), int(round(e[1] * MM))))
            t.SetLayer(pcbnew.F_Cu); t.SetWidth(200000); t.SetNet(ni); b.Add(t); ctx.add_track(t); return [t]
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) == net and p.IsOnLayer(LAYS[l]) and p.HitTest(pt):
                    c = (p.GetX() / MM, p.GetY() / MM)
                    if abs(c[0] - x) + abs(c[1] - y) > 1e-6:
                        t = pcbnew.PCB_TRACK(b); t.SetStart(p.GetPosition()); t.SetEnd(pt); t.SetLayer(LAYS[l]); t.SetWidth(int(max(Pp['tiers'][-1], 0.2) * MM)); t.SetNet(ni); b.Add(t); ctx.add_track(t); added.append(t)
                    return added
        return added
    pre = []; post = []
    k0 = (pl[0][0], pl[0][1], pl[0][2]); k1 = (pl[-1][0], pl[-1][1], pl[-1][2])
    if k0 in stubs:
        c, e = stubs[k0]; pre = [(0, c[0], c[1], 0.2), (0, e[0], e[1], 0.2)]; pts = pts[1:]
    if k1 in stubs:
        c, e = stubs[k1]; post = [(0, e[0], e[1], 0.2), (0, c[0], c[1], 0.2)]; pts = pts[:-1]
    # snap: if first/last cell inside an own-net pad, replace leading in-own cells by pad center
    def snap_end(rev):
        if not pts: return pts
        seq = pts[::-1] if rev else pts
        if not seq: return seq
        ow = own[::-1] if rev else own
        l0 = seq[0][0]
        # find the pad that contains first point
        pad = None
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) == net and p.IsOnLayer(LAYS[l0]) and p.HitTest(pcbnew.VECTOR2I(int(seq[0][1] * MM), int(seq[0][2] * MM))): pad = p
        if pad is None: return seq
        k = 0
        while k + 1 < len(seq) and seq[k + 1][0] == l0 and pad.HitTest(pcbnew.VECTOR2I(int(seq[k + 1][1] * MM), int(seq[k + 1][2] * MM))): k += 1
        # exit cell = seq[k+1] if exists
        wmin = min(s[3] for s in seq[:k + 2]) if k + 1 < len(seq) else seq[0][3]
        c = (pad.GetX() / MM, pad.GetY() / MM)
        # exit width: narrowest of in-pad region, also treat lateral: pads small -> use width of in-pad cells computed with override=narrowest
        new = [(l0, c[0], c[1], wmin)] + seq[k + 1:] if k + 1 < len(seq) else [(l0, c[0], c[1], wmin)]
        return new
    if not pre: pts = snap_end(False)
    if not post: pts = snap_end(True)[::-1]
    pts = pre + pts + post
    # simplify per same-layer run (first/last points are exact pad/stub positions and are kept)
    sp = []; k = 0
    while k < len(pts):
        m = k
        while m + 1 < len(pts) and pts[m + 1][0] == pts[k][0]: m += 1
        run = simplify_run(ctx, net, pts[k:m + 1])
        sp += run if not sp else run
        k = m + 1
    pts = sp
    # build segments
    segs = []; vias = []
    for i in range(len(pts) - 1):
        a, c = pts[i], pts[i + 1]
        if a[0] != c[0]:
            vias.append((a[1], a[2])); continue
        if abs(a[1] - c[1]) < 1e-9 and abs(a[2] - c[2]) < 1e-9: continue
        wd = min(a[3], c[3])
        segs.append([a[0], a[1], a[2], c[1], c[2], wd])
    # merge collinear same width same layer
    mg = []
    for s in segs:
        if mg:
            m = mg[-1]
            if m[0] == s[0] and abs(m[5] - s[5]) < 1e-9 and abs(m[3] - s[1]) < 1e-9 and abs(m[4] - s[2]) < 1e-9:
                d1 = (m[3] - m[1], m[4] - m[2]); d2 = (s[3] - s[1], s[4] - s[2])
                if abs(d1[0] * d2[1] - d1[1] * d2[0]) < 1e-6 * max(1, abs(d1[0] * d2[0] + d1[1] * d2[1])) and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                    m[3], m[4] = s[3], s[4]; continue
        mg.append(s)
    added = []
    for l, xa, ya, xb, yb, wd in mg:
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(round(xa * MM)), int(round(ya * MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(xb * MM)), int(round(yb * MM))))
        t.SetLayer(LAYS[l]); t.SetWidth(int(round(wd * MM))); t.SetNet(ni); b.Add(t)
        ws = [w for w in (2.0, 1.5, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2) if w <= wd + 1e-9]
        fit_width(ctx, t, net, ws)
        ctx.add_track(t); added.append(t)
    for (x, y) in vias:
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(int(round(Pp['dv'] * MM))); v.SetDrill(int(round(Pp['drill'] * MM)))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); b.Add(v); ctx.add_track(v); added.append(v)
    # exact via legality on all layers (snap to pad centres can move a via onto foreign In2/B.Cu copper)
    bad = False
    for v in [a for a in added if a.GetClass() == 'PCB_VIA']:
        bb = v.GetBoundingBox(); bb.Inflate(int(0.6 * MM))
        for u in b.Tracks():
            if str(u.GetNetname()) == net or u is v or not bb.Intersects(u.GetBoundingBox()): continue
            cc = int(req_clr(cls_ := ctx.cls.get(net, 'SIGNAL'), ctx.cls.get(str(u.GetNetname()), 'SIGNAL')) * MM) - 20000
            for L in LAYS:
                if u.GetClass() != 'PCB_VIA' and u.GetLayer() != L: continue
                if u.GetEffectiveShape(L).Collide(v.GetEffectiveShape(L), cc): bad = True; break
            if bad: break
        if bad: break
    if bad:
        for a in added: b.RemoveNative(a)
        ctx.rebuild(); return []
    return added

def route_net(ctx, net, Pp, log=print):
    tot = []
    for it in range(80):
        comps = comps_of(ctx, net)
        if len(comps) <= 1: return True, tot
        refs = [comp_refs(ctx, c) for c in comps]
        prs = []
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                d = min(math.hypot(a[0] - c[0], a[1] - c[1]) for a in refs[i][:60] for c in refs[j][:60])
                prs.append((d, i, j))
        prs.sort()
        res = None; tried = 0
        for d, i, j in prs:
            if tried >= 6 or (tried > 0 and d > 40): break
            res = route_pair(ctx, net, comps[i], comps[j], Pp); tried += 1
            if res is not None: break
            log('  FAIL', net, 'pair', i, j, 'dist %.1f' % d)
        if res is None: return False, tot
        pl, wds, stubs = res
        new = emit(ctx, net, pl, Pp, stubs); tot += new
        if not new and it > 0 and len(comps_of(ctx, net)) >= len(comps): log('  NOPROGRESS', net); return False, tot
    return False, tot
