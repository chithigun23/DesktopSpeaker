"""flatpak: route_r6i_smooth.py IN.kicad_pcb OUT.kicad_pcb [--nets N1,N2] [--skip-class USB,...] [--passes 3]
Corner-radius fixer for route_r6i_bends.py hits (corner / jog): for a short middle segment b-c between prev a-b and next c-d
(same net/layer, plain bends), tries in order
  1. shortcut a-d (both bends removed), or a longer shortcut over up to two more plain joints on each side,
  2. widened chamfer: b moved back along b->a and c forward along c->d so the middle reaches max(3w, 0.4 mm),
keeping the narrower width of the three. A candidate is applied only when every new segment passes a clearance check
against foreign copper (route_r6h_chk rules: class clearances, SWITCH 1.0/2.0, NECK 0.2, foreign pours 0.3, NPTH/edge 0.5,
BKO on B.Cu) and the number of bend hits on that net does not grow. Final acceptance is by DRC + open edges outside."""
import sys, math, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
import route_r6i_bends as RB
a = sys.argv; inp, outp = a[1], a[2]
nets_only = set(a[a.index('--nets') + 1].split(',')) if '--nets' in a else None
skipc = set(a[a.index('--skip-class') + 1].split(',')) if '--skip-class' in a else {'USB'}
passes = int(a[a.index('--passes') + 1]) if '--passes' in a else 3
b = pcbnew.LoadBoard(inp)
necks = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('NECK')]
bkos = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('BKO')]
ant = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT']
fzones = [z for z in b.Zones() if not z.GetIsRuleArea() and str(z.GetNetname()) not in ('', 'GND')]
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True); edge = ps.Outline(0)
CRITN = ('Net-(U4-BATP)', 'Net-(U25-FB)', 'Net-(U25-COMP)', 'Net-(U25-ILIM)')
BKO_OK = ('GND', 'PVDD', 'POWER_HI', 'SPK_OUT', 'SWITCH', 'PWR_5V', 'PWR_3V')
def inneck(sh, L): return any(z.IsOnLayer(L) and z.Outline().Collide(sh) for z in necks)
def need(na, nb, apad, bpad, sh, L):
    ca, cb = ncls(na), (ncls(nb) if nb else 'Default')
    r = req(ca, cb, apad, bpad)
    if ca == 'SWITCH' or cb == 'SWITCH':
        other = cb if ca == 'SWITCH' else ca
        if other in ('Default', 'SIGNAL', 'I2C', 'AUDIO', 'I2S_CLK', 'USB') and not (apad and bpad): r = max(r, 1.0)
    if not (apad and bpad):
        if (na in CRITN and cb in ('SWITCH', 'BOOT')) or (nb in CRITN and ca in ('SWITCH', 'BOOT')): r = max(r, 2.0)
    if inneck(sh, L): r = 0.2
    return r
def gap_ok(s1, s2, r): return not s1.Collide(s2, int(r * MM) - 1500)
def legal(net, L, p, q, w, ignore):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape()
    bb = t.GetBoundingBox(); bb.Inflate(int(2.5 * MM))
    if not edge.Collide(V(*p)) or not edge.Collide(V(*q)): return False
    for k in range(edge.SegmentCount()):
        if sh.Collide(edge.CSegment(k), int(0.5 * MM)): return False
    for z in ant:
        if z.Outline().Collide(sh): return False
    if L == pcbnew.B_Cu and ncls(net) not in BKO_OK:
        for z in bkos:
            if z.Outline().Collide(sh): return False
    for u in b.Tracks():
        if u.m_Uuid.AsString() in ignore or str(u.GetNetname()) == net or not bb.Intersects(u.GetBoundingBox()): continue
        if u.GetClass() == 'PCB_VIA': us = u.GetEffectiveShape(L)
        elif u.GetLayer() == L: us = u.GetEffectiveShape()
        else: continue
        if not gap_ok(us, sh, need(net, str(u.GetNetname()), False, False, sh, L)): return False
    for f in b.GetFootprints():
        if not bb.Intersects(f.GetBoundingBox()): continue
        for pd in f.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                if not gap_ok(pd.GetEffectiveHoleShape(), sh, 0.5): return False
                continue
            if str(pd.GetNetname()) == net or not pd.IsOnLayer(L): continue
            if not gap_ok(pd.GetEffectiveShape(L), sh, need(net, str(pd.GetNetname()), False, True, sh, L)): return False
        for z in f.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.IsOnLayer(L) and z.Outline().Collide(sh): return False
    for z in fzones:
        if str(z.GetNetname()) == net or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
        if L == pcbnew.In2_Cu:
            if z.Outline().Collide(sh, int(0.3 * MM)): return False
            continue
        if z.GetFilledPolysList(L).Collide(sh, int(max(0.3, req(ncls(net), ncls(str(z.GetNetname())), False, False)) * MM)): return False
    return True
def why(net, L, p, q, w, ignore):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape()
    bb = t.GetBoundingBox(); bb.Inflate(int(2.5 * MM))
    if not edge.Collide(V(*p)) or not edge.Collide(V(*q)): return 'R3'
    for k in range(edge.SegmentCount()):
        if sh.Collide(edge.CSegment(k), int(0.5 * MM)): return 'R5'
    for z in ant:
        if z.Outline().Collide(sh): return 'R7'
    if L == pcbnew.B_Cu and ncls(net) not in BKO_OK:
        for z in bkos:
            if z.Outline().Collide(sh): return 'R10'
    for u in b.Tracks():
        if u.m_Uuid.AsString() in ignore or str(u.GetNetname()) == net or not bb.Intersects(u.GetBoundingBox()): continue
        if u.GetClass() == 'PCB_VIA': us = u.GetEffectiveShape(L)
        elif u.GetLayer() == L: us = u.GetEffectiveShape()
        else: continue
        if not gap_ok(us, sh, need(net, str(u.GetNetname()), False, False, sh, L)): return 'R16'
    for f in b.GetFootprints():
        if not bb.Intersects(f.GetBoundingBox()): continue
        for pd in f.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                if not gap_ok(pd.GetEffectiveHoleShape(), sh, 0.5): return 'R21'
                continue
            if str(pd.GetNetname()) == net or not pd.IsOnLayer(L): continue
            if not gap_ok(pd.GetEffectiveShape(L), sh, need(net, str(pd.GetNetname()), False, True, sh, L)): return 'R24'
        for z in f.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.IsOnLayer(L) and z.Outline().Collide(sh): return 'R26'
    for z in fzones:
        if str(z.GetNetname()) == net or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
        if L == pcbnew.In2_Cu:
            if z.Outline().Collide(sh, int(0.3 * MM)): return 'R30'
            continue
        if z.GetFilledPolysList(L).Collide(sh, int(max(0.3, req(ncls(net), ncls(str(z.GetNetname())), False, False)) * MM)): return 'R32'
    return 'ok'
def find_seg(net, L, p, q):
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' or str(t.GetNetname()) != net or t.GetLayer() != L: continue
        s, e = (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM)
        if (math.hypot(s[0] - p[0], s[1] - p[1]) < 0.012 and math.hypot(e[0] - q[0], e[1] - q[1]) < 0.012) or (math.hypot(s[0] - q[0], s[1] - q[1]) < 0.012 and math.hypot(e[0] - p[0], e[1] - p[1]) < 0.012): return t
def neighbour(net, L, pt, exclude):
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' or str(t.GetNetname()) != net or t.GetLayer() != L or t.m_Uuid.AsString() in exclude: continue
        s, e = (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM)
        if math.hypot(s[0] - pt[0], s[1] - pt[1]) < 0.012: return t, e
        if math.hypot(e[0] - pt[0], e[1] - pt[1]) < 0.012: return t, s
    return None, None
def add(net, L, p, q, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); t.SetNet(b.FindNet(net)); b.Add(t); return t
LAYN = {pcbnew.F_Cu: 'F.Cu', pcbnew.B_Cu: 'B.Cu', pcbnew.In2_Cu: 'In2.Cu'}
LAYID = {v: k for k, v in LAYN.items()}
stats = collections.Counter()
def segkey(t): return (str(t.GetNetname()), t.GetLayer(), (t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM), t.GetWidth() / MM)
for ps_ in range(passes):
    _, SEGS, VIAS, PADS = RB.loadb(b)
    H = [h for h in RB.hits_core(b, SEGS, VIAS, PADS) if h['kind'] in ('corner', 'jog') and (nets_only is None or h['net'] in nets_only) and ncls(h['net']) not in skipc]
    if not H: break
    changed = 0
    for h in H:
        net = h['net']; L = LAYID[h['layer']]; pb, pc = tuple(h['a']), tuple(h['b'])
        mid = find_seg(net, L, pb, pc)
        if mid is None: continue
        prev, pa = neighbour(net, L, pb, {mid.m_Uuid.AsString()})
        nxt, pd_ = neighbour(net, L, pc, {mid.m_Uuid.AsString()})
        if prev is None or nxt is None or prev.m_Uuid.AsString() == nxt.m_Uuid.AsString(): continue
        trio = {prev.m_Uuid.AsString(), mid.m_Uuid.AsString(), nxt.m_Uuid.AsString()}
        base = [segkey(t) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and str(t.GetNetname()) == net and t.m_Uuid.AsString() not in trio]
        allt = [segkey(t) for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and str(t.GetNetname()) == net]
        before = sum(1 for x in RB.hits_core(b, allt, VIAS, PADS, only=net) if x['kind'] in ('corner', 'jog'))
        wp, wm, wn = prev.GetWidth() / MM, mid.GetWidth() / MM, nxt.GetWidth() / MM; w = min(wp, wm, wn)
        lim = max(3 * w, 0.4)
        cands = [([pa, pd_], [w])]
        # longer shortcuts: extend the chain by up to two plain joints on each side (no via, pad or T at the joint)
        def plain_pt(pt):
            k = 0
            for t in b.GetTracks():
                if str(t.GetNetname()) != net: continue
                if t.GetClass() == 'PCB_VIA':
                    if math.hypot(t.GetX() / MM - pt[0], t.GetY() / MM - pt[1]) <= t.GetWidth(pcbnew.F_Cu) / MM / 2 + 0.01: return False
                    continue
                if t.GetLayer() != L: continue
                for q in ((t.GetStart().x / MM, t.GetStart().y / MM), (t.GetEnd().x / MM, t.GetEnd().y / MM)):
                    if math.hypot(q[0] - pt[0], q[1] - pt[1]) < 0.012: k += 1
            if k != 2: return False
            v = pcbnew.VECTOR2I(int(pt[0] * MM), int(pt[1] * MM))
            for f in b.GetFootprints():
                for pd in f.Pads():
                    if str(pd.GetNetname()) == net and pd.IsOnLayer(L) and pd.HitTest(v): return False
            return True
        left = [(pa, prev)]; right = [(pd_, nxt)]
        for side, chain in ((0, left), (1, right)):
            for _ in range(2):
                pt, seg = chain[-1]
                if not plain_pt(pt): break
                t2, far = neighbour(net, L, pt, {x.m_Uuid.AsString() for _, x in chain} | {mid.m_Uuid.AsString()})
                if t2 is None: break
                chain.append((far, t2))
        for i in range(len(left)):
            for j in range(len(right)):
                if i == 0 and j == 0: continue
                if i > 0 and not plain_pt(left[i - 1][0]): continue
                if j > 0 and not plain_pt(right[j - 1][0]): continue
                segsx = [x for _, x in left[1:i + 1]] + [x for _, x in right[1:j + 1]]
                wx = min([w] + [x.GetWidth() / MM for x in segsx])
                cands.append(([left[i][0], right[j][0]], [wx], segsx))
        lab = math.hypot(pb[0] - pa[0], pb[1] - pa[1]); lcd = math.hypot(pd_[0] - pc[0], pd_[1] - pc[1]); lm = math.hypot(pc[0] - pb[0], pc[1] - pb[1])
        for extra in (0.0, 0.1, 0.25, 0.5):
            t = (lim - lm) / 1.5 + extra
            if t <= 0 or t > lab - 0.05 or t > lcd - 0.05: continue
            nb = (pb[0] + (pa[0] - pb[0]) / lab * t, pb[1] + (pa[1] - pb[1]) / lab * t)
            nc = (pc[0] + (pd_[0] - pc[0]) / lcd * t, pc[1] + (pd_[1] - pc[1]) / lcd * t)
            cands.append(([pa, nb, nc, pd_], [wp, wm, wn]))
        done = False
        if '--verb' in a: print('  orig-mid legal', net, legal(net, L, pb, pc, wm, trio), 'why', why(net, L, pb, pc, wm, trio))
        for cand in cands:
            pts, ws = cand[0], cand[1]; extra_rm = cand[2] if len(cand) > 2 else []
            ign = trio | {x.m_Uuid.AsString() for x in extra_rm}
            base2 = [s_ for s_ in base if not any(abs(s_[2][0] - x.GetStart().x / MM) < 1e-4 and abs(s_[2][1] - x.GetStart().y / MM) < 1e-4 and abs(s_[3][0] - x.GetEnd().x / MM) < 1e-4 and abs(s_[3][1] - x.GetEnd().y / MM) < 1e-4 for x in extra_rm)]
            segsn = [(net, L, p, q, ws[k]) for k, (p, q) in enumerate(zip(pts[:-1], pts[1:]))]
            after = sum(1 for x in RB.hits_core(b, base2 + segsn, VIAS, PADS, only=net) if x['kind'] in ('corner', 'jog'))
            if '--verb' in a: print('  cand', net, [tuple(round(c, 2) for c in p_) for p_ in pts], 'hits', before, '->', after, 'why', [why(net, L, p, q, ws[k], ign) for k, (p, q) in enumerate(zip(pts[:-1], pts[1:]))])
            if after >= before: continue
            if not all(legal(net, L, p, q, ws[k], ign) for k, (p, q) in enumerate(zip(pts[:-1], pts[1:]))): continue
            for x in list(extra_rm) + [prev, mid, nxt]: b.RemoveNative(x)
            for s_ in segsn: add(net, L, s_[2], s_[3], s_[4])
            stats['shortcut' if (len(pts) == 2 and not extra_rm) else ('long-shortcut' if len(pts) == 2 else 'widen')] += 1; done = True; changed += 1
            break
        if not done: stats['kept'] += 1
    print('pass', ps_, 'changed', changed, dict(stats), flush=True)
    if not changed: break
refill(b); pcbnew.SaveBoard(outp, b)
print('smooth', dict(stats))
