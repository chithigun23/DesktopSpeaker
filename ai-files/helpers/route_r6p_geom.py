"""flatpak: route_r6p_geom.py BOARD [--json OUT.json] [--nets N1,N2] [--top 40] [--all]
Routing-geometry report per net (user request R6p: no sharp turns, no needless turns over 90 deg, no wandering traces).
 (a) acute turns  : plain vertex (exactly two same-net same-layer track ends, no via or pad there) where the direction changes
                    by more than 90 deg (interior angle < 90 deg). Arcs count by their end tangents.
 (b) zig-zags / U-turns along a chain of plain vertices, within 3 mm of path:
       'uturn'  : the signed direction changes over consecutive bends add up to >= 150 deg (the trace doubles back),
       'zigzag' : >= 3 consecutive bends of alternating sign, each >= 30 deg (a wiggle), or two opposite bends each >= 90 deg.
 (c) two-pin connections: copper graph of tracks, arcs and vias (via = layer hop); pads are terminals (a path never passes
     through another pad). For every pad pair joined that way: routed length (pad centre to pad centre along copper),
     straight-line distance, detour ratio, excess mm and vias on the path. Zones are not part of the graph, so pad pairs
     joined only by pours are not listed.
 (d) net total track length and via count.
Ranking: two-pin connections by excess (ratio > 1.3 and excess > 3 mm), nets by acute/uturn/zigzag count."""
import sys, math, json, collections, heapq, fnmatch
import pcbnew
MM = 1e6
A = sys.argv
b = pcbnew.LoadBoard(A[1])
only = set(A[A.index('--nets') + 1].split(',')) if '--nets' in A else None
top = int(A[A.index('--top') + 1]) if '--top' in A else 40
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6o.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
def P(v): return (v.x / MM, v.y / MM)
def dist(p, q): return math.hypot(p[0] - q[0], p[1] - q[1])
def ang(u, v): return math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
segs = collections.defaultdict(list)   # net -> [(layer, a, c, length, w, tan_a(out of a), tan_c(into c), kind)]
vias = collections.defaultdict(list)
for t in b.GetTracks():
    n = str(t.GetNetname())
    if only and n not in only: continue
    if t.GetClass() == 'PCB_VIA': vias[n].append((P(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) / MM / 2)); continue
    a, c = P(t.GetStart()), P(t.GetEnd())
    if t.GetClass() == 'PCB_ARC':
        m = P(t.GetMid()); L = t.GetLength() / MM
        ctr = P(t.GetCenter())
        def tang(p, q):
            r = (p[0] - ctr[0], p[1] - ctr[1]); v = (-r[1], r[0])
            return v if v[0] * q[0] + v[1] * q[1] >= 0 else (-v[0], -v[1])
        ta, tc = tang(a, (m[0] - a[0], m[1] - a[1])), tang(c, (c[0] - m[0], c[1] - m[1]))
        segs[n].append((t.GetLayer(), a, c, L, t.GetWidth() / MM, ta, tc, 'arc'))
    else:
        L = dist(a, c)
        if L < 1e-6: continue
        d = (c[0] - a[0], c[1] - a[1])
        segs[n].append((t.GetLayer(), a, c, L, t.GetWidth() / MM, d, d, 'seg'))
pads = collections.defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        n = str(p.GetNetname())
        if n and (not only or n in only): pads[n].append(p)
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
TOL = 0.015
res = {}
for n in sorted(set(segs) | set(vias)):
    if n == '' or n.startswith('unconnected-'): continue
    S = segs[n]; Vs = vias[n]; Ps = pads[n]
    # ---- nodes: endpoint clusters per layer
    nodes = {}; npos = []; nlay = []
    def node(L, p):
        k = (L, round(p[0] / TOL), round(p[1] / TOL))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                kk = (L, k[1] + dx, k[2] + dy)
                if kk in nodes: return nodes[kk]
        nodes[k] = len(npos); npos.append(p); nlay.append(L); return nodes[k]
    E = collections.defaultdict(list)   # node -> [(node, w, seg index or -1, isvia)]
    ends = collections.defaultdict(list)   # node -> [(seg index, which end)]
    for i, (L, a, c, Ln, w, ta, tc, kd) in enumerate(S):
        ia, ic = node(L, a), node(L, c)
        E[ia].append((ic, Ln, i, 0)); E[ic].append((ia, Ln, i, 0)); ends[ia].append((i, 0)); ends[ic].append((i, 1))
    nseg_nodes = len(npos)
    # T-junctions: an endpoint lying on the interior of another straight segment of the same layer
    for k in range(nseg_nodes):
        p = npos[k]; L = nlay[k]
        for i, (L2, a, c, Ln, w, ta, tc, kd) in enumerate(S):
            if L2 != L or kd != 'seg': continue
            if dist(p, a) < 0.03 or dist(p, c) < 0.03: continue
            u = ((p[0] - a[0]) * (c[0] - a[0]) + (p[1] - a[1]) * (c[1] - a[1])) / (Ln * Ln)
            if u <= 0 or u >= 1:   # endpoint overlapping the end of another segment (copper overlap, not an exact joint)
                e = a if u <= 0 else c; ie = node(L, e)
                if ie != k and dist(p, e) < max(w / 2, 0.03) and not any(m == ie for (m, _, _, _) in E[k]):
                    d0 = dist(p, e); E[k].append((ie, d0, -1, 0)); E[ie].append((k, d0, -1, 0)); ends[k].append((-1, -1)); ends[ie].append((-1, -1))
                continue
            if 0 < u < 1:
                q = (a[0] + u * (c[0] - a[0]), a[1] + u * (c[1] - a[1]))
                if dist(p, q) < max(w / 2, 0.03):
                    ia, ic = node(L, a), node(L, c)
                    E[k].append((ia, u * Ln, -1, 0)); E[ia].append((k, u * Ln, -1, 0))
                    E[k].append((ic, (1 - u) * Ln, -1, 0)); E[ic].append((k, (1 - u) * Ln, -1, 0))
                    ends[k].append((-1, -1))
    # vias
    vnode = []
    for (vp, r) in Vs:
        iv = len(npos); npos.append(vp); nlay.append(-1); vnode.append(iv)
        for k in range(nseg_nodes):
            if dist(npos[k], vp) <= r + 0.005:
                d = dist(npos[k], vp); E[k].append((iv, d, -1, 1)); E[iv].append((k, d, -1, 1)); ends[k].append((-2, -2))
    # pads
    pnode = []
    for p in Ps:
        ip = len(npos); npos.append(P(p.GetPosition())); nlay.append(-2); pnode.append(ip)
        for k in range(nseg_nodes):
            L = nlay[k]
            if not p.IsOnLayer(L): continue
            q = npos[k]
            if p.GetEffectiveShape(L).Collide(pcbnew.VECTOR2I(int(q[0] * MM), int(q[1] * MM)), int(0.005 * MM)):
                d = dist(q, npos[ip]); E[k].append((ip, d, -1, 0)); E[ip].append((k, d, -1, 0)); ends[k].append((-3, -3))
        for j, iv in enumerate(vnode):
            vp, r = Vs[j]
            if p.GetEffectiveShape(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu).Collide(pcbnew.VECTOR2I(int(vp[0] * MM), int(vp[1] * MM)), int(r * MM)):
                d = dist(vp, npos[ip]); E[iv].append((ip, d, -1, 0)); E[ip].append((iv, d, -1, 0))
    padset = set(pnode)
    # ---- (a) acute + chains for (b)
    def plain(k):
        e = ends[k]
        return len(e) == 2 and e[0][0] >= 0 and e[1][0] >= 0 and e[0][0] != e[1][0]
    def turn_at(k):
        (i, ei), (j, ej) = ends[k]
        # travel i -> k -> j
        si, sj = S[i], S[j]
        tin = si[6] if ei == 1 else (-si[5][0], -si[5][1])
        tout = sj[5] if ej == 0 else (-sj[6][0], -sj[6][1])
        return ang(tin, tout)
    acute = []; turns = {}
    for k in range(nseg_nodes):
        if plain(k):
            t = turn_at(k); turns[k] = t
            if abs(t) > 90.5: acute.append(dict(at=[round(npos[k][0], 3), round(npos[k][1], 3)], layer=LN[nlay[k]], turn=round(t, 1)))
    # arcs: internal turn
    arcturn = {}
    for i, s in enumerate(S):
        if s[7] == 'arc': arcturn[i] = ang(s[5], s[6])
    # chains: walk from non-plain nodes (or any unvisited) along plain vertices
    seen_seg = set(); chains = []
    def walk(k0, i0):
        seq = []   # list of (pos_along, turn, point)
        pos = 0.0; k = k0; i = i0
        while True:
            seen_seg.add(i); s = S[i]
            other = node(s[0], s[2]) if node(s[0], s[1]) == k else node(s[0], s[1])
            if i in arcturn: seq.append((pos + s[3] / 2, arcturn[i] if node(s[0], s[1]) == k else -arcturn[i], s[1]))
            pos += s[3]
            if not plain(other): break
            (a1, _), (a2, _) = ends[other]; nxt = a2 if a1 == i else a1
            if nxt in seen_seg: break
            # orientation of the turn: entering 'other' from i
            (ii, ei), (jj, ej) = ends[other]
            t = turns[other] if ii == i else -turns[other]
            seq.append((pos, t, npos[other])); k = other; i = nxt
        return seq
    for k in range(nseg_nodes):
        if plain(k): continue
        for (i, e) in ends[k]:
            if i >= 0 and i not in seen_seg: chains.append(walk(k, i))
    for i in range(len(S)):
        if i not in seen_seg: chains.append(walk(node(S[i][0], S[i][1]), i))
    uturns = []; zigs = []
    for seq in chains:
        bends = [x for x in seq if abs(x[1]) >= 5]
        used = -1
        for x in range(len(bends)):
            if x <= used: continue
            cum = 0
            for y in range(x, len(bends)):
                if bends[y][0] - bends[x][0] > 3.0: break
                cum += bends[y][1]
                if abs(cum) >= 150:
                    uturns.append(dict(at=[round(bends[x][2][0], 2), round(bends[x][2][1], 2)], to=[round(bends[y][2][0], 2), round(bends[y][2][1], 2)], turn=round(cum, 1), span=round(bends[y][0] - bends[x][0], 2)))
                    used = y; break
        used = -1
        for x in range(len(bends) - 1):
            if x <= used: continue
            y = x
            while y + 1 < len(bends) and bends[y + 1][0] - bends[y][0] <= 3.0 and bends[y + 1][1] * bends[y][1] < 0 and abs(bends[y + 1][1]) >= 30 and abs(bends[y][1]) >= 30: y += 1
            hard = y == x + 1 and abs(bends[x][1]) >= 90 and abs(bends[y][1]) >= 90
            if y - x + 1 >= 3 or hard:
                zigs.append(dict(at=[round(bends[x][2][0], 2), round(bends[x][2][1], 2)], to=[round(bends[y][2][0], 2), round(bends[y][2][1], 2)], bends=[round(bends[z][1]) for z in range(x, y + 1)], span=round(bends[y][0] - bends[x][0], 2)))
                used = y
    # ---- (c) two-pin connections = ratsnest edges: Euclidean MST over the pads of each copper-connected group,
    #      each edge measured along the copper (shortest path, pads may be passed through)
    DD = {}
    for a_i, ip in enumerate(pnode):
        D = {ip: (0.0, 0)}; h = [(0.0, 0, ip)]
        while h:
            d, nv, k = heapq.heappop(h)
            if D.get(k, (1e18,))[0] < d - 1e-9: continue
            for (m, w, si, isv) in E[k]:
                nd = d + w; nnv = nv + isv
                if nd < D.get(m, (1e18,))[0] - 1e-9: D[m] = (nd, nnv); heapq.heappush(h, (nd, nnv, m))
        DD[a_i] = D
    conns = []; done = set(); mst_len = 0.0
    for a_i in range(len(pnode)):
        if a_i in done: continue
        grp = [b_i for b_i in range(len(pnode)) if pnode[b_i] in DD[a_i]]
        if len(grp) < 2: done.add(a_i); continue
        intree = {grp[0]}; done |= set(grp)
        while len(intree) < len(grp):
            best = None
            for x in intree:
                for y in grp:
                    if y in intree: continue
                    dd = dist(npos[pnode[x]], npos[pnode[y]])
                    if best is None or dd < best[0]: best = (dd, x, y)
            st, x, y = best; intree.add(y); mst_len += st
            rl, nv = DD[x][pnode[y]]; pa, pb = Ps[x], Ps[y]
            conns.append(dict(a='%s.%s' % (pa.GetParentFootprint().GetReference(), pa.GetNumber()), b='%s.%s' % (pb.GetParentFootprint().GetReference(), pb.GetNumber()),
                              pa=[round(npos[pnode[x]][0], 2), round(npos[pnode[x]][1], 2)], pb=[round(npos[pnode[y]][0], 2), round(npos[pnode[y]][1], 2)],
                              routed=round(rl, 2), straight=round(st, 2), ratio=round(rl / st, 2) if st > 0.05 else None, excess=round(rl - st, 2), vias=nv // 2))
    res[n] = dict(cls=cl(n), length=round(sum(s[3] for s in S), 2), mst=round(mst_len, 2), vias=len(Vs), segs=len(S), acute=acute, uturn=uturns, zigzag=zigs, conns=conns)
if '--json' in A: json.dump(res, open(A[A.index('--json') + 1], 'w'), indent=0)
# ---- report
tot = collections.Counter()
for n, r in res.items():
    tot['acute'] += len(r['acute']); tot['uturn'] += len(r['uturn']); tot['zigzag'] += len(r['zigzag'])
print('TOTAL acute %d  uturn %d  zigzag %d  nets %d' % (tot['acute'], tot['uturn'], tot['zigzag'], len(res)))
C = [(n, c) for n, r in res.items() for c in r['conns'] if c['ratio'] and c['ratio'] > 1.3 and c['excess'] > 3]
C.sort(key=lambda x: -x[1]['excess'])
print('two-pin connections with ratio > 1.3 and excess > 3 mm: %d (ratio > 1.6 and excess > 10 mm: %d)' % (len(C), sum(1 for n, c in C if c['ratio'] > 1.6 and c['excess'] > 10)))
for n, c in C[:top]: print('  %-34s %-8s %-10s %-10s routed %7.2f straight %6.2f ratio %5.2f excess %6.2f vias %d' % (n, res[n]['cls'], c['a'], c['b'], c['routed'], c['straight'], c['ratio'], c['excess'], c['vias']))
print('nets with acute / uturn / zigzag:')
for n, r in sorted(res.items(), key=lambda x: -(len(x[1]['acute']) + len(x[1]['uturn']) + len(x[1]['zigzag']))):
    if not (r['acute'] or r['uturn'] or r['zigzag']): break
    print('  %-34s %-8s len %7.2f vias %2d acute %d uturn %d zigzag %d' % (n, r['cls'], r['length'], r['vias'], len(r['acute']), len(r['uturn']), len(r['zigzag'])))
    if '--all' in A:
        for k in ('acute', 'uturn', 'zigzag'):
            for x in r[k]: print('      ', k, x)
print('longest nets (track length / pad MST of the track-connected groups):')
for n, r in sorted(res.items(), key=lambda x: -x[1]['length'])[:top]: print('  %-34s %-8s len %7.2f mst %7.2f vias %2d' % (n, r['cls'], r['length'], r['mst'], r['vias']))
