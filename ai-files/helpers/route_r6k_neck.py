"""flatpak: route_r6k_neck.py BOARD [CASES.json] : widest-path (max-min width) through power zone fills, grid 0.1 mm.
Each case: [zone_name, layer(F|2|B), [ax,ay], [bx,by], label]. The width is 2 x the distance-to-edge along the best path,
so it is the widest track that could pass from a to b inside the fill. Prints width and where the narrowest point is."""
import sys, json, math, heapq
import pcbnew, numpy as np
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
LY = {'F': pcbnew.F_Cu, '2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
def V(x, y): return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
DEF = [
 ['SYS_IN2', '2', [161.9, 117.1], [148.3, 135.4], 'SYS In2: U4 cap field -> boost'],
 ['SYS_IN2', '2', [159.3, 128.6], [148.3, 135.4], 'SYS In2: SYS field 2 -> boost'],
 ['SYS_BOOST_F', 'F', [159.3, 128.6], [148.3, 135.4], 'SYS F: field 2 -> boost'],
 ['BAT_INT_IN2', '2', [168.0, 122.0], [168.6, 111.2], 'BAT In2: U4 side -> Q103'],
 ['BAT_INT_F', 'F', [162.0, 122.5], [168.6, 111.2], 'BAT F: U4 side -> Q103'],
 ['PVDD_IN2', '2', [159.7, 154.1], [110.0, 128.0], 'PVDD In2: boost -> U6'],
 ['PVDD_IN2', '2', [159.7, 154.1], [199.6, 132.3], 'PVDD In2: boost -> U7'],
 ['VBUS_PD_IN2', '2', [143.3, 58.8], [148.2, 126.2], 'VBUS In2: U11 -> U4 VBUS 8/9 field'],
 ['VBUS_PD_IN2', '2', [143.3, 58.8], [148.4, 120.3], 'VBUS In2: U11 -> U4 VBUS 2/3 field'],
]
cases = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else DEF
def fills(name, L):
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetZoneName() not in name.split('+'): continue
        if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L): out.append(z.GetFilledPolysList(L))
    return out
def widest(polys, a, c, step=0.1):
    L_ = min(p.BBox().GetLeft() for p in polys) / MM; R_ = max(p.BBox().GetRight() for p in polys) / MM
    T_ = min(p.BBox().GetTop() for p in polys) / MM; B_ = max(p.BBox().GetBottom() for p in polys) / MM
    x0, y0 = L_ - step, T_ - step
    W = int((R_ - L_) / step) + 3; H = int((B_ - T_) / step) + 3
    ins = np.zeros((H, W), dtype=bool)
    for p in polys:
        for k in range(p.OutlineCount()):
            sub = pcbnew.SHAPE_POLY_SET(); sub.AddOutline(p.Outline(k))
            for h in range(p.HoleCount(k)): sub.AddHole(p.Hole(k, h))
            sb = sub.BBox(); i0 = max(0, int((sb.GetLeft() / MM - x0) / step)); i1 = min(W, int((sb.GetRight() / MM - x0) / step) + 2)
            j0 = max(0, int((sb.GetTop() / MM - y0) / step)); j1 = min(H, int((sb.GetBottom() / MM - y0) / step) + 2)
            for j in range(j0, j1):
                for i in range(i0, i1):
                    if not ins[j, i] and sub.Contains(V(x0 + i * step, y0 + j * step)): ins[j, i] = True
    # pads of the net inside the bbox count as copper (zone joins pads); optional via '@NET' suffix handled by caller
    for pp in PADS:
        sh = pp.GetEffectivePolygon(LCUR[0]); pb = sh.BBox()
        i0 = max(0, int((pb.GetLeft() / MM - x0) / step)); i1 = min(W, int((pb.GetRight() / MM - x0) / step) + 2)
        j0 = max(0, int((pb.GetTop() / MM - y0) / step)); j1 = min(H, int((pb.GetBottom() / MM - y0) / step) + 2)
        for j in range(j0, j1):
            for i in range(i0, i1):
                if not ins[j, i] and sh.Contains(V(x0 + i * step, y0 + j * step)): ins[j, i] = True
    # exact euclidean distance transform (brute force over boundary cells, fine for these sizes)
    from collections import deque
    bnd = np.argwhere(~ins)
    d = np.full((H, W), 0.0)
    idx = np.argwhere(ins)
    if len(idx) == 0: return None
    # two-pass 8-neighbour chamfer approximates euclid within 4 %
    INF = 1e9; D = np.where(ins, INF, 0.0)
    s2 = math.sqrt(2)
    for j in range(H):
        for i in range(W):
            if not ins[j, i]: continue
            v = D[j, i]
            if j: v = min(v, D[j-1, i] + 1, D[j-1, i-1] + s2 if i else INF, D[j-1, i+1] + s2 if i < W-1 else INF)
            if i: v = min(v, D[j, i-1] + 1)
            D[j, i] = v
    for j in range(H-1, -1, -1):
        for i in range(W-1, -1, -1):
            if not ins[j, i]: continue
            v = D[j, i]
            if j < H-1: v = min(v, D[j+1, i] + 1, D[j+1, i+1] + s2 if i < W-1 else INF, D[j+1, i-1] + s2 if i else INF)
            if i < W-1: v = min(v, D[j, i+1] + 1)
            D[j, i] = v
    def cell(p): return (int(round((p[1] - y0) / step)), int(round((p[0] - x0) / step)))
    def near(p, r=1.0):
        cj, ci = cell(p); rr = int(r / step); out = []
        for j in range(cj - rr, cj + rr + 1):
            for i in range(ci - rr, ci + rr + 1):
                if 0 <= j < H and 0 <= i < W and ins[j, i] and (j - cj) ** 2 + (i - ci) ** 2 <= rr * rr: out.append((j, i))
        return out
    S = near(a); T = set(near(c))
    if not S or not T: return ('endpoint not in fill', len(S), len(T))
    best = np.full((H, W), -1.0); pred = {}; pq = []
    for s in S: best[s] = D[s]; heapq.heappush(pq, (-D[s], s))
    while pq:
        nd, (j, i) = heapq.heappop(pq); nd = -nd
        if nd < best[j, i]: continue
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                jj, ii = j + dj, i + di
                if 0 <= jj < H and 0 <= ii < W and ins[jj, ii]:
                    v = min(nd, D[jj, ii])
                    if v > best[jj, ii]: best[jj, ii] = v; pred[(jj, ii)] = (j, i); heapq.heappush(pq, (-v, (jj, ii)))
    tb = max(T, key=lambda q: best[q])
    if best[tb] < 0: return ('no path',)
    # the bottleneck is where 'best' drops to its final value walking from S to T (walk back from tb)
    q = tb; nar = (D[tb], tb); seen = set()
    while q is not None and q not in seen:
        seen.add(q)
        if best[q] <= best[tb] + 1e-9: nar = (D[q], q)
        else: break
        q = pred.get(q)
    loc = (round(x0 + nar[1][1] * step, 2), round(y0 + nar[1][0] * step, 2)) if nar[1] else None
    return (round(2 * (best[tb] - 0.5) * step, 2), loc)
PADS = []; LCUR = [None]
for zn, ly, a, c, lab in cases:
    p = fills(zn, LY[ly]); LCUR[0] = LY[ly]
    nets = set(str(z.GetNetname()) for z in b.Zones() if z.GetZoneName() in zn.split('+'))
    PADS = [pp for f in b.GetFootprints() for pp in f.Pads() if str(pp.GetNetname()) in nets and pp.IsOnLayer(LY[ly])]
    if not p: print('%-40s %s: no fill' % (lab, zn)); continue
    print('%-40s %-12s %s widest %s' % (lab, zn, ly, widest(p, a, c)))
