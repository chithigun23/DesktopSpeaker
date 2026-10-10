"""flatpak: route_r6i_route.py IN.kicad_pcb OUT.kicad_pcb PLAN.json [--verb]
R6i plan-driven rip-up/re-route on top of route_r6h_route (R6b/R6c rules + R6h In2 slow-net mask + R6H_VIAISL).
PLAN: list of steps, executed in order:
 {"rip": NET, "keep": [[x0,y0,x1,y1],...], "box": [[...]]}  remove NET copper except items fully inside a keep box;
     with "box": only items with a via/endpoint inside a box (restorable)
 {"route": NET, "layers": [0,1], "alt": [[0,1,2]], "lpen": {"0": 2}, "pen": [[li,x0,y0,x1,y1,val],...],
  "prm": {...}, "restore": true, "viaisl": "BAT_INT_IN2,...", "zfree": [[ZONE, x0, y0, x1, y1]]}
     zfree (U4 nets only): the named F/B pour is not an obstacle inside the box (the R6i BAT_INT_F slot exception)
     layers: 0=F 1=In2 2=B. In2 (1) only for nets in route_r6h_slow.json and never for AUDIO/I2S/USB.
     lpen: per-layer step penalty (uint8 added per cell); pen: box penalties (mm) per layer.
     alt: further layer sets tried in order if the first fails. viaisl: U4-group nets only (route_r6h_route.U4NETS),
     vias may pass the listed In2 islands (clearance hole in the fill).
     restore: on failure remove the partial route and put back the copper this plan ripped for NET.
 {"prune": NET}                                 remove dangling track ends / single-layer vias of NET
 {"save": PATH}                                 refill + save an intermediate board
Prints one line per step; writes OUT.route.json (results)."""
import sys, time, json, os
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import route_r6h_route as H
import route_r6c_route as RR
import route_p2_core as RC
from route_r6c_route import *
import numpy as np

def route_net2(ctx, net, Pp, log=print, maxpairs=10):
    """route_p2_core.route_net, but a failing pair does not end the net: up to maxpairs pairs per round (no 40 mm cut-off),
    failed pairs are remembered; returns (complete, items) and keeps every connection it made"""
    tot = []; bad = set()
    def sig(c): return tuple(sorted(str(it[1].GetParentFootprint().GetReference()) + '.' + str(it[1].GetNumber()) for it in c if it[0] == 'pad')) or (len(c),)
    for it in range(80):
        comps = comps_of(ctx, net)
        if len(comps) <= 1: return True, tot
        refs = [comp_refs(ctx, c) for c in comps]; sg = [sig(c) for c in comps]
        prs = []
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                if (sg[i], sg[j]) in bad: continue
                d = min(math.hypot(a[0] - c[0], a[1] - c[1]) for a in refs[i][:60] for c in refs[j][:60])
                prs.append((d, i, j))
        prs.sort(); res = None
        for d, i, j in prs[:maxpairs]:
            res = route_pair(ctx, net, comps[i], comps[j], Pp)
            if res is not None: break
            bad.add((sg[i], sg[j])); log('  FAIL', net, 'pair', sg[i][:3], sg[j][:3], 'dist %.1f' % d)
        if res is None: return False, tot
        pl, wds, stubs = res
        new = RC.emit(ctx, net, pl, Pp, stubs); tot += new
        if not new: bad.add((sg[i], sg[j])); log('  EMIT-REJECT', net)
    return False, tot

class Pen(dict):
    """truthy, empty 'rip' carrier: routes P['rip'] into ctx.ripmask (penalty map) without ripping anything"""
    def __bool__(self): return True

def main():
    inp, outp, plan = sys.argv[1:4]
    verb = '--verb' in sys.argv
    R = RR.Router(inp); ctx = R.ctx; b = ctx.b
    cur = {'lpen': {}, 'pen': []}
    def ripmask(me, li, y0, y1, x0, x1, w, c, rip):
        p = np.zeros((y1 - y0, x1 - x0), np.uint8)
        v = int(cur['lpen'].get(str(li), 0))
        if v: p[:] = v
        for l, a0, b0, a1, b1, val in cur['pen']:
            if l != li: continue
            gx0 = max(int(ctx.cx(a0)) - x0, 0); gx1 = min(int(ctx.cx(a1)) - x0, x1 - x0); gy0 = max(int(ctx.cy(b0)) - y0, 0); gy1 = min(int(ctx.cy(b1)) - y0, y1 - y0)
            if gx1 > gx0 and gy1 > gy0: p[gy0:gy1, gx0:gx1] = np.maximum(p[gy0:gy1, gx0:gx1], val)
        return p
    ctx.ripmask = ripmask
    # R6i: no via centre inside any SMD pad (keeps the via-in-pad gate list), NPTH holes keep 0.5 mm (edge_hole rule) on every layer
    PADM = np.zeros((ctx.H, ctx.W), bool)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetDrillSizeX() > 0: continue
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(L):
                    for ring in ctx.pad_poly(p, L):
                        if len(ring) >= 3: ctx.poly_fill(PADM, [ring], True)
    o_vo = ctx.via_obstacle
    ISL_ALL = R.ISL.copy(); isl_v = {'': ISL_ALL}   # In2 tracks: every island; vias: islands not listed in R6H_VIAISL
    def islv():
        k = H.VIAISL
        if k not in isl_v:
            m = np.zeros((ctx.H, ctx.W), bool)
            for z in b.Zones():
                if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or str(z.GetNetname()) in ('GND', ''): continue
                if z.GetZoneName() in k.split(','): continue
                ctx.poly_fill(m, [H.ring_of(z)], True)
            isl_v[k] = m
        return isl_v[k]
    def via_obstacle(me, y0, y1, x0, x1, dv, cme, **k):
        R.ISL = islv()
        try: r = o_vo(me, y0, y1, x0, x1, dv, cme, **k)
        finally: R.ISL = ISL_ALL
        return r | PADM[y0:y1, x0:x1] if 'NO_PADM' not in os.environ else r
    ctx.via_obstacle = via_obstacle
    o_fe = R.fix_edge
    def fix_edge():
        o_fe()
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and p.GetDrillSizeX() > 0:
                    ctx.circ_fill(ctx.edge, (p.GetX() / MM, p.GetY() / MM), p.GetDrillSizeX() / MM / 2, True)
    if 'NO_NPTH' not in os.environ:
        R.fix_edge = fix_edge; fix_edge()
    o_hard = R.hard
    def padded(fn, y0, y1, x0, x1, extra):
        # evaluate a windowed mask function on a window grown by 'extra' cells (copper/edge just outside the A* window still counts), then crop
        Y0, Y1, X0, X1 = max(y0 - extra, 0), min(y1 + extra, ctx.H), max(x0 - extra, 0), min(x1 + extra, ctx.W)
        return fn(Y0, Y1, X0, X1)[y0 - Y0:y0 - Y0 + (y1 - y0), x0 - X0:x0 - X0 + (x1 - x0)]
    def hard(li, y0, y1, x0, x1, w):   # edge/NPTH also in the hard mask, so the straight-shortcut pass (seg_hard) keeps 0.5 mm too
        ex = int((w / 2 + 1.2 + ctx.MARGIN) / G) + 2
        return padded(lambda a, b_, c, d: o_hard(li, a, b_, c, d, w) | ctx.dilate(ctx.edge[a:b_, c:d], (w / 2 + 0.5 + ctx.MARGIN) / G), y0, y1, x0, x1, ex)
    if 'NO_HARD' not in os.environ:
        R.hard = hard
    o_obs = ctx.obstacle
    def obstacle(me, li, y0, y1, x0, x1, w, cme, **k):
        ex = int((w / 2 + 2.2) / G) + 2
        return padded(lambda a, b_, c, d: o_obs(me, li, a, b_, c, d, w, cme, **k), y0, y1, x0, x1, ex)
    if 'NO_OBS' not in os.environ:
        ctx.obstacle = obstacle
    saved = {}; pre_open = {}
    res = {}
    def snap(t):
        try: t.GetStart()
        except Exception as e: print('SNAPFAIL', type(t), t.GetClass(), repr(e)); raise
        if t.GetClass() == 'PCB_VIA': return ('v', str(t.GetNetname()), t.GetX(), t.GetY(), t.GetWidth(pcbnew.F_Cu), t.GetDrillValue())
        return ('t', str(t.GetNetname()), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth())
    def unsnap(s):
        nobj = b.FindNet(s[1])
        if s[0] == 'v':
            t = pcbnew.PCB_VIA(b); t.SetPosition(pcbnew.VECTOR2I(s[2], s[3])); t.SetWidth(s[4]); t.SetDrill(s[5]); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); t.SetViaType(pcbnew.VIATYPE_THROUGH)
        else:
            t = pcbnew.PCB_TRACK(b); t.SetLayer(s[2]); t.SetStart(pcbnew.VECTOR2I(s[3], s[4])); t.SetEnd(pcbnew.VECTOR2I(s[5], s[6])); t.SetWidth(s[7])
        t.SetNet(nobj); b.Add(t); ctx.add_track(t); return t
    def touches(net, pt, layer, skip):
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) == net and p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(pcbnew.VECTOR2I(pt), 1000): return True
        for t in b.GetTracks():
            if t.m_Uuid.AsString() == skip.m_Uuid.AsString() or str(t.GetNetname()) != net: continue
            if t.GetClass() == 'PCB_VIA':   # geometric (padstack flashing needs connectivity data that this session does not build)
                if math.hypot(t.GetX() - pt.x, t.GetY() - pt.y) <= t.GetWidth(pcbnew.F_Cu) / 2 + 1000: return True
            elif t.GetLayer() == layer and t.GetEffectiveShape().Collide(pcbnew.VECTOR2I(pt), 1000): return True
        for z in b.Zones():
            if not z.GetIsRuleArea() and str(z.GetNetname()) == net and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Collide(pcbnew.VECTOR2I(pt), 1000): return True
        return False
    def via_touch(net, v, layer):
        c = v.GetPosition(); r = v.GetWidth(pcbnew.F_Cu) / 2
        circ = pcbnew.SHAPE_CIRCLE(c, int(r))
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) == net and p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(circ, 1000): return True
        for t in b.GetTracks():
            if t.m_Uuid.AsString() == v.m_Uuid.AsString() or str(t.GetNetname()) != net: continue
            if t.GetClass() == 'PCB_VIA': continue
            if t.GetLayer() == layer and t.GetEffectiveShape().Collide(circ, 1000): return True
        for z in b.Zones():
            if not z.GetIsRuleArea() and str(z.GetNetname()) == net and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Collide(c, int(r)): return True
        return False
    from route_r6a_lib import req as _req
    def collides(n, items):
        cn = ctx.cls.get(n, 'Default')
        for t in items:
            bb = t.GetBoundingBox(); bb.Inflate(int(0.6 * MM))
            lays = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu] if t.GetClass() == 'PCB_VIA' else [t.GetLayer()]
            for L in lays:
                sh = t.GetEffectiveShape(L) if t.GetClass() == 'PCB_VIA' else t.GetEffectiveShape()
                for u in b.GetTracks():
                    un = str(u.GetNetname())
                    if un == n or not bb.Intersects(u.GetBoundingBox()): continue
                    if u.GetClass() != 'PCB_VIA' and u.GetLayer() != L: continue
                    c = max(0.2, _req(cn, ctx.cls.get(un, 'Default'), False, False)) if un != 'GND' else 0.2
                    if (u.GetEffectiveShape(L) if u.GetClass() == 'PCB_VIA' else u.GetEffectiveShape()).Collide(sh, int(c * MM) - 2000): return True
                for f in b.GetFootprints():
                    if not bb.Intersects(f.GetBoundingBox()): continue
                    for q in f.Pads():
                        if str(q.GetNetname()) != n and q.IsOnLayer(L) and q.GetEffectiveShape(L).Collide(sh, int(0.2 * MM) - 2000): return True
        return False
    def prune(n):
        tot = 0
        while True:
            rm = []
            for t in b.GetTracks():
                if str(t.GetNetname()) != n: continue
                if t.GetClass() == 'PCB_VIA':
                    if len([L for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu) if via_touch(n, t, L)]) < 2: rm.append(t)
                elif not touches(n, t.GetStart(), t.GetLayer(), t) or not touches(n, t.GetEnd(), t.GetLayer(), t): rm.append(t)
            if not rm: break
            if verb:
                for t in rm: print('   prune', t.GetClass(), (t.GetPosition().x / MM, t.GetPosition().y / MM) if t.GetClass() == 'PCB_VIA' else (t.GetLayer(), t.GetStart().x / MM, t.GetStart().y / MM, t.GetEnd().x / MM, t.GetEnd().y / MM))
            for t in rm: b.RemoveNative(t)
            tot += len(rm)
        if tot: ctx.rebuild()
        return tot
    curviaisl = ['']
    for st in json.load(open(plan)):
        if 'rip' in st:
            n = full(st['rip'], b); K = st.get('keep', [])
            def kin(q): return any(k[0] <= q.x / MM <= k[2] and k[1] <= q.y / MM <= k[3] for k in K)
            r = [t for t in b.GetTracks() if str(t.GetNetname()) == n and not ((kin(t.GetPosition()) if t.GetClass() == 'PCB_VIA' else (kin(t.GetStart()) and kin(t.GetEnd()))))]
            if 'box' in st:   # rip only items with a via/endpoint inside one of the boxes
                Bx = st['box']
                def bin_(q): return any(k[0] <= q.x / MM <= k[2] and k[1] <= q.y / MM <= k[3] for k in Bx)
                r = [t for t in r if (bin_(t.GetPosition()) if t.GetClass() == 'PCB_VIA' else (bin_(t.GetStart()) or bin_(t.GetEnd())))]
            if n not in saved: pre_open[n] = len(comps_of(ctx, n)) - 1
            saved.setdefault(n, []).extend(snap(t) for t in r)
            for t in r: b.RemoveNative(t)
            ctx.rebuild(); print('rip', n, len(r), flush=True)
        elif 'prune' in st:
            n = full(st['prune'], b); print('prune', n, prune(n), flush=True)
        elif 'save' in st:
            refill(b); pcbnew.SaveBoard(st['save'], b); ctx.rebuild(); print('saved', st['save'], flush=True)
        elif 'route' in st:
            n = full(st['route'], b); c = ctx.cls.get(n, 'Default')
            vi = st.get('viaisl', '')
            if vi and n not in H.U4NETS: print('REFUSE viaisl', n); vi = ''
            if vi != curviaisl[0]:
                H.VIAISL = vi; curviaisl[0] = vi; ctx.rebuild()
            zf = st.get('zfree', [])
            if zf:   # R6i slot exception: this net may cross the named pour inside the box (refill re-cuts the pour; continuity checked by route_r6h_isl.py)
                if n not in H.U4NETS: print('REFUSE zfree', n); zf = []
                for zn, a0, b0, a1, b1 in zf:
                    z = [z for z in b.Zones() if z.GetZoneName() == zn][0]; zid = ctx.netid[str(z.GetNetname())]; g = ctx.grp_of(ctx.cls.get(str(z.GetNetname()), 'SIGNAL'))
                    li = LAYS.index(pcbnew.F_Cu if z.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
                    gx0, gx1, gy0, gy1 = int(ctx.cx(a0)), int(ctx.cx(a1)), int(ctx.cy(b0)), int(ctx.cy(b1))
                    sub = ctx.R[g][li][gy0:gy1, gx0:gx1]; sub[sub == zid] = 0
                    print('  zfree', zn, 'box', a0, b0, a1, b1)
            sets = [st.get('layers', [0, 2])] + st.get('alt', [])
            cur['lpen'] = st.get('lpen', {}); cur['pen'] = st.get('pen', [])
            t0 = time.time(); ok = False; items = []
            open0 = pre_open.get(n, len(comps_of(ctx, n)) - 1); ripped = n in pre_open
            for lays in sets:
                if 1 in lays and c not in ('PWR_5V', 'PWR_3V', 'POWER_HI', 'PVDD') and (n not in H.SLOW_OK or c not in ('Default', 'I2C', 'SIGNAL')):   # rule 11: power classes may use In2
                    print('REFUSE in2', n, c); lays = [x for x in lays if x != 1]
                P = dict(RR.PRM.get(c, RR.PRM['Default'])); P.update(st.get('prm', {}))
                P['gndc'] = 0.2; P['layers'] = lays
                P['rip'] = Pen() if (cur['lpen'] or cur['pen']) else None
                R.cur = {'cls': c, 'crit': n in RR.CRIT, 'bko': c not in RR.BKO_EXEMPT_CLS and n not in ('Net-(U7-BST_B+)', 'Net-(U25-BOOT)') and n not in RR.BKO_EXTRA, 'floor': P['floor'], 'fine': bool(P.get('fine')), 'cme': P['cme']}
                if P.get('fine'): P['dv'], P['drill'] = 0.5, 0.2
                log = []
                pre = set(t.m_Uuid.AsString() for t in b.GetTracks() if str(t.GetNetname()) == n)
                try:
                    ok, items = route_net2(ctx, n, P, log=(print if verb else (lambda *a: log.append(a))))
                except Exception:
                    import traceback; traceback.print_exc(); ok, items = False, []
                if ok: break
                oc = len(comps_of(ctx, n)) - 1
                if lays is sets[-1] and ((ripped and oc <= open0) or (not ripped and oc < open0)) and st.get('partial', True):
                    print('  partial accepted (open %d, %d before)' % (oc, open0)); ok = 'partial'; break
                part = [t for t in b.GetTracks() if str(t.GetNetname()) == n and t.m_Uuid.AsString() not in pre]
                if part:   # remove the partial attempt before the next layer set
                    for t in part: b.RemoveNative(t)
                    ctx.rebuild()
                items = []
            if ok and c in ('AUDIO', 'I2S_CLK'):
                lg = []
                for it in items:
                    if it.GetClass() == 'PCB_VIA': RR.gnd_beside(b, it, lg)
                if lg: print('  gnd_beside', lg)
                ctx.rebuild()
            if zf: ctx.rebuild()
            if ok and not st.get('noprune'):
                pr = prune(n)
                if pr: print('  pruned dangling', pr)
            rest = 0
            if not ok and st.get('restore', True) and n in saved:
                back = [unsnap(s) for s in saved.pop(n)]; rest = len(back)
                pre_open.pop(n, None)
                if collides(n, back):   # space was taken by later routes: leave the net ripped (reported as LOST)
                    for t in back: b.RemoveNative(t)
                    ctx.rebuild(); rest = -rest; print('  LOST', n, 'old copper collides; left unrouted')
            nv = sum(1 for it in items if it.GetClass() == 'PCB_VIA')
            L = sum(it.GetLength() for it in items if it.GetClass() != 'PCB_VIA') / MM
            n2 = sum(it.GetLength() for it in items if it.GetClass() != 'PCB_VIA' and it.GetLayer() == pcbnew.In2_Cu) / MM
            nb = sum(it.GetLength() for it in items if it.GetClass() != 'PCB_VIA' and it.GetLayer() == pcbnew.B_Cu) / MM
            op = len(comps_of(ctx, n)) - 1
            res[n] = dict(ok=ok, lays=lays, vias=nv, len=round(L, 1), in2=round(n2, 1), b=round(nb, 1), open=op, restored=rest)
            if ok: saved.pop(n, None); pre_open.pop(n, None)
            print('%-8s %-32s %s lay %s vias %d len %.1f in2 %.1f B %.1f open %d restored %d %.0fs' % (c, n, ('OK  ' if ok is True else 'PART') if ok else 'FAIL', lays, nv, L, n2, nb, op, rest, time.time() - t0), flush=True)
    for n in saved: print('WARNING ripped and not re-routed:', n, len(saved[n]))
    refill(b); pcbnew.SaveBoard(outp, b)
    json.dump(res, open(outp.replace('.kicad_pcb', '.route.json'), 'w'), indent=1)
    print('done', sum(1 for v in res.values() if v['ok']), '/', len(res))

if __name__ == '__main__':
    main()
