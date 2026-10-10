"""flatpak: route_r6k_arcfix.py IN OUT [--nets A,B] [--kinds corner,jog,acute] [--only x,y;x,y] [--rmin F] [--log FILE]
Corner-rule fixer with true arcs (pcb-layout-best-practices.md sec. 13: 'prefer long gentle bends, arcs where the router allows').
For each route_r6i_bends.py hit:
  corner: the two bends b, c and the short middle are replaced by one tangent arc between the prev and next segments
          (centre on the bisector of the virtual corner P = line(a,b) x line(c,d));
  jog:    each of the two bends becomes a tangent arc (S-curve) using the middle segment;
  acute:  the single bend becomes a tangent arc (removes the acid-trap wedge).
Radius tried from 8 w (max 4 mm) down to rmin x w (default 2.0, never below 0.4 mm); first legal one wins.
Legality: route_r6j_smooth.py rules (class clearances, SWITCH 1.0/2.0, NECK 0.2, foreign pours, In2 island outlines 0.3,
board edge 0.5, NPTH 0.5, BKO on B.Cu) for every new piece. The prev/next segments keep their far ends and widths; the arc
takes the narrower of the two. Writes OUT and a log of applied fixes (net, layer, kind, location, radius)."""
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
def legal_item(net, L, t, pts, ignore):
    sh = t.GetEffectiveShape()
    bb = t.GetBoundingBox(); bb.Inflate(int(2.5 * MM))
    if any(not edge.Collide(V(*p)) for p in pts): return False
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

import route_r6i_bends as RB
kinds = set(a[a.index('--kinds') + 1].split(',')) if '--kinds' in a else {'corner', 'jog', 'acute'}
only = [tuple(map(float, s.split(','))) for s in a[a.index('--only') + 1].split(';')] if '--only' in a else None
rmin = float(a[a.index('--rmin') + 1]) if '--rmin' in a else 2.0
logf = a[a.index('--log') + 1] if '--log' in a else None
skip = [tuple(map(float, s_.split(','))) for s_ in a[a.index('--skip') + 1].split(';')] if '--skip' in a else []
LAYID = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In2.Cu': pcbnew.In2_Cu, 'In1.Cu': pcbnew.In1_Cu}
def P2(v): return (v.x / MM, v.y / MM)
def segs_at(net, L, pt, excl=()):
    out = []
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or str(t.GetNetname()) != net or t.GetLayer() != L or t.m_Uuid.AsString() in excl: continue
        s, e = P2(t.GetStart()), P2(t.GetEnd())
        if math.hypot(s[0] - pt[0], s[1] - pt[1]) < 0.012: out.append((t, e, 'S'))
        elif math.hypot(e[0] - pt[0], e[1] - pt[1]) < 0.012: out.append((t, s, 'E'))
    return out
def unit(v):
    n = math.hypot(*v); return (v[0] / n, v[1] / n)
def line_x(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9: return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])
def arc_geom(P, u1, u2, R):
    """tangent arc at virtual corner P between rays u1 (towards prev far end) and u2 (towards next far end)"""
    cosphi = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])); phi = math.acos(cosphi)   # interior angle
    if phi < 1e-3 or phi > math.pi - 1e-3: return None
    tl = R / math.tan(phi / 2)
    p1 = (P[0] + u1[0] * tl, P[1] + u1[1] * tl); p2 = (P[0] + u2[0] * tl, P[1] + u2[1] * tl)
    bis = unit((u1[0] + u2[0], u1[1] + u2[1])); dc = R / math.sin(phi / 2)
    C = (P[0] + bis[0] * dc, P[1] + bis[1] * dc); M = (C[0] - bis[0] * R, C[1] - bis[1] * R)
    return p1, M, p2, tl
def mk_track(net, L, p, q, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); t.SetNet(b.FindNet(net)); return t
def mk_arc(net, L, p, m, q, w):
    t = pcbnew.PCB_ARC(b); t.SetStart(V(*p)); t.SetMid(V(*m)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); t.SetNet(b.FindNet(net)); return t
def ok_items(net, L, items, ignore):
    for t, pts in items:
        if not legal_item(net, L, t, pts, ignore): return False
    return True
applied = []
def try_bend(net, L, P, prev, nxt, ws, extra_rm, kind, where):
    """P: virtual corner; prev/next: (track, far point, end-flag); ws: candidate arc widths in order. True if an arc was applied."""
    (tp, fp, _), (tn, fn, _) = prev, nxt
    u1, u2 = unit((fp[0] - P[0], fp[1] - P[1])), unit((fn[0] - P[0], fn[1] - P[1]))
    lp, ln = math.hypot(fp[0] - P[0], fp[1] - P[1]), math.hypot(fn[0] - P[0], fn[1] - P[1])
    ign = set([tp.m_Uuid.AsString(), tn.m_Uuid.AsString()] + [x.m_Uuid.AsString() for x in extra_rm])
    for w in ws:
        R = min(8 * w, 4.0)
        while R >= max(rmin * w, 0.4) - 1e-9:
            g = arc_geom(P, u1, u2, R)
            if g is None: return False
            p1, M, p2, tl = g
            if tl <= lp - 0.05 and tl <= ln - 0.05:
                items = [(mk_track(net, L, fp, p1, tp.GetWidth() / MM), [fp, p1]), (mk_arc(net, L, p1, M, p2, w), [p1, M, p2]), (mk_track(net, L, p2, fn, tn.GetWidth() / MM), [p2, fn])]
                if ok_items(net, L, items, ign):
                    for x in [tp, tn] + list(extra_rm): b.Remove(x)
                    for t, _ in items: b.Add(t)
                    applied.append(dict(net=net, layer=b.GetLayerName(L), kind=kind, at=[round(where[0], 3), round(where[1], 3)], R=round(R, 3), w=w))
                    return True
            R = round(R - max(0.05, 0.1 * w), 3) if R > 1.0 else round(R - 0.05, 3)
    return False
def wl(*ts):
    v = [t.GetWidth() / MM for t in ts]; out = []
    for x in (max(v), v[len(v) // 2] if len(v) == 3 else max(v), min(v)):
        if x not in out: out.append(x)
    return out
for pas in range(3):
    _, SEGS, VIAS, PADS = RB.loadb(b)
    H = [h for h in RB.hits_core(b, SEGS, VIAS, PADS) if h['kind'] in kinds and (nets_only is None or h['net'] in nets_only)]
    if only is not None: H = [h for h in H if any(math.hypot((h.get('at') or h['a'])[0] - x, (h.get('at') or h['a'])[1] - y) < 0.6 or ('b' in h and math.hypot(h['b'][0] - x, h['b'][1] - y) < 0.6) for x, y in only)]
    H = [h for h in H if not any(math.hypot((h.get('at') or h['a'])[0] - x, (h.get('at') or h['a'])[1] - y) < 0.3 or ('b' in h and math.hypot(h['b'][0] - x, h['b'][1] - y) < 0.3) for x, y in skip)]
    n0 = len(applied)
    for h in H:
        net = h['net']; L = LAYID[h['layer']]
        if h['kind'] == 'acute':
            at = tuple(h['at']); ss = segs_at(net, L, at)
            if len(ss) != 2: continue
            if try_bend(net, L, at, ss[0], ss[1], wl(ss[0][0], ss[1][0]), [], 'acute', at): continue
            # fallback: merge the short stub into the junction: cut the long segment at A' (distance d from the bend) and run A' -> stub end
            (t1, f1, _), (t2, f2, _) = sorted(ss, key=lambda x: -x[0].GetLength())
            if t2.GetLength() / MM <= 2.5:
                L1 = t1.GetLength() / MM; u = unit((f1[0] - at[0], f1[1] - at[1])); w1 = t1.GetWidth() / MM
                def nh(): 
                    _, S2, V2, P2_ = RB.loadb(b); return len([x for x in RB.hits_core(b, S2, V2, P2_, only=net) if x['layer'] == h['layer']])
                base = nh()
                for dd in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, L1):
                    if dd > L1 + 1e-6: break
                    Ap = (at[0] + u[0] * dd, at[1] + u[1] * dd) if dd < L1 - 1e-6 else f1
                    items = [(mk_track(net, L, Ap, f2, w1), [Ap, f2])] + ([(mk_track(net, L, f1, Ap, w1), [f1, Ap])] if dd < L1 - 1e-6 else [])
                    if not ok_items(net, L, items, set([t1.m_Uuid.AsString(), t2.m_Uuid.AsString()])): continue
                    b.Remove(t1); b.Remove(t2)
                    for t, _ in items: b.Add(t)
                    if nh() < base:
                        applied.append(dict(net=net, layer=b.GetLayerName(L), kind='acute-merge', at=[round(at[0], 3), round(at[1], 3)], R=0, d=dd, w=w1)); break
                    for t, _ in items: b.Remove(t)
                    b.Add(t1); b.Add(t2)
            continue
        pb, pc = tuple(h['a']), tuple(h['b'])
        mid = [t for t, _, _ in segs_at(net, L, pb) if t in [x for x, _, _ in segs_at(net, L, pc)]]
        if not mid: continue
        tm = mid[0]; ex = (tm.m_Uuid.AsString(),)
        sb, sc = segs_at(net, L, pb, ex), segs_at(net, L, pc, ex)
        if len(sb) != 1 or len(sc) != 1: continue
        if h['kind'] == 'corner':
            fa, fd = sb[0][1], sc[0][1]
            P = line_x(pb, unit((pb[0] - fa[0], pb[1] - fa[1])), pc, unit((pc[0] - fd[0], pc[1] - fd[1])))
            if P is None: continue
            # P must lie beyond b along a->b and beyond c along d->c (true outside corner)
            try_bend(net, L, P, sb[0], sc[0], wl(sb[0][0], tm, sc[0][0]), [tm], 'corner', pb)
        else:
            # jog: arc at b using half the middle, then arc at c using the rest (middle split at its midpoint)
            mpt = ((pb[0] + pc[0]) / 2, (pb[1] + pc[1]) / 2)
            b.Remove(tm); h1 = mk_track(net, L, pb, mpt, tm.GetWidth() / MM); h2 = mk_track(net, L, mpt, pc, tm.GetWidth() / MM); b.Add(h1); b.Add(h2)
            o1 = try_bend(net, L, pb, sb[0], (h1, mpt, 'E'), wl(sb[0][0], h1), [], 'jog', pb)
            s2 = segs_at(net, L, pc); 
            o2 = False
            if len(s2) == 2:
                hh = [x for x in s2 if x[0].m_Uuid.AsString() == h2.m_Uuid.AsString()]
                oth = [x for x in s2 if x[0].m_Uuid.AsString() != h2.m_Uuid.AsString()]
                if hh and oth: o2 = try_bend(net, L, pc, (hh[0][0], hh[0][1], 'S'), oth[0], wl(hh[0][0], oth[0][0]), [], 'jog', pc)
            if not o1 and not o2:
                b.Remove(h1); b.Remove(h2); b.Add(tm)
    if len(applied) == n0: break
refill(b); pcbnew.SaveBoard(outp, b)
print('arcs applied', len(applied))
for x in applied: print(' ', x)
if logf: json.dump(applied, open(logf, 'w'), indent=0)
