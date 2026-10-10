"""flatpak: route_r6b_route.py IN.kicad_pcb OUT.kicad_pcb NETS(comma) [--prm JSON] [--lock] [--rip]
R6b signal router: route_p2 raster A* (route_r6a_astar.so) on F.Cu + B.Cu only (In2 never used by signals).
Extra obstacles over route_r6a_astar:
 - SWITCH copper (pads, tracks, fills) at 1.0 mm for sensitive classes, SWITCH+BOOT at 2.0 mm for BATP/U25 FB/COMP/ILIM
 - B.Cu keep-outs BKO_* for tracks and vias (signal classes)
 - widths below the class floor only inside NECK_* areas (and near own pads)
 - vias: never inside a non-GND In2 island (fills), 0.5/0.2 fine vias only inside NECK_* areas (P fine=1)
 - straight-shortcut simplification re-checked against these masks
Post: AUDIO/I2S vias get a GND via within 1.2 mm. New items are unlocked unless --lock."""
import sys, time, json, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_p2_core import *
import route_p2_core as RC
from route_r6a_lib import full, refill, place_via
RC.lib = ctypes.CDLL('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_r6a_astar.so')
RC.lib.astar.restype = ctypes.c_int
PRO = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6b.kicad_pro'
SENS = ('Default', 'SIGNAL', 'I2C', 'AUDIO', 'I2S_CLK', 'USB')
CRIT = ('Net-(U4-BATP)', 'Net-(U25-FB)', 'Net-(U25-COMP)', 'Net-(U25-ILIM)')
BKO_EXEMPT_CLS = ('GND', 'PVDD', 'POWER_HI', 'SPK_OUT', 'SWITCH', 'PWR_5V', 'PWR_3V')

def ring_of(z):
    o = z.Outline().Outline(0); return [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]

class Router:
    def __init__(self, inp):
        self.ctx = ctx = Ctx(inp, PRO)
        ctx.cls = {n: self.cl(n) for n in ctx.netid}
        sh = (ctx.H, ctx.W)
        self.NOVIA = np.zeros(sh, bool); self.BKO = np.zeros(sh, bool); self.NECK = np.zeros(sh, bool)
        self.SW = [np.zeros(sh, bool) for _ in LAYS]; self.SWB = [np.zeros(sh, bool) for _ in LAYS]
        self.cur = {'cls': 'SIGNAL', 'crit': False, 'bko': True, 'floor': 0.2, 'fine': False}
        self.build_masks()
        o_obs, o_via, o_reb = ctx.obstacle, ctx.via_obstacle, ctx.rebuild
        R = self
        def obstacle(me, li, y0, y1, x0, x1, w, cme, **k):
            bl = o_obs(me, li, y0, y1, x0, x1, w, cme, **k)
            return bl | R.hard(li, y0, y1, x0, x1, w)
        def via_obstacle(me, y0, y1, x0, x1, dv, cme, **k):
            def one(d):
                bl = np.zeros((y1 - y0, x1 - x0), bool)
                for li in range(3): bl |= obstacle(me, li, y0, y1, x0, x1, d, cme, cpad=0.26, **{a: b for a, b in k.items() if a != 'cpad'})
                return bl | ctx.dilate(R.NOVIA[y0:y1, x0:x1], (d / 2 + 0.05) / G)
            if R.cur['fine']:
                return one(0.6) & (one(0.5) | ~R.NECK[y0:y1, x0:x1])
            return one(dv)
        def rebuild():
            o_reb(); R.fix_edge(); R.zone_obstacles()
        self.fix_edge()
        ctx.obstacle = obstacle; ctx.via_obstacle = via_obstacle; ctx.rebuild = rebuild
        self.zone_obstacles()
        RC.simplify_run = self.simplify_run
        def stub_ok(ctx_, net, nearby, c, e, w, rip, layer=pcbnew.F_Cu):
            cls = ctx.cls.get(net, 'Default'); cme = R.cur.get('cme', 0.2)
            t = pcbnew.PCB_TRACK(ctx.b); t.SetStart(pcbnew.VECTOR2I(int(c[0]*MM), int(c[1]*MM))); t.SetEnd(pcbnew.VECTOR2I(int(e[0]*MM), int(e[1]*MM)))
            t.SetLayer(layer); t.SetWidth(int(w*MM)); sh = t.GetEffectiveShape()
            for kind, o in nearby:
                oc = ctx.cls.get(str(o.GetNetname()), 'Default')
                if kind == 'pad':
                    cl = 1.0 if (oc == 'SWITCH' and cls in SENS) else 0.2
                    if o.IsOnLayer(layer) and o.GetEffectiveShape(layer).Collide(sh, int(cl*MM) - 200): return False
                else:
                    cl = max(0.2, req_clr(cls, oc), cme if oc != 'GND' else 0.2, 1.0 if (oc == 'SWITCH' and cls in SENS) else 0)
                    shp = o.GetEffectiveShape(layer) if kind == 'via' else (o.GetEffectiveShape() if o.GetLayer() == layer else None)
                    if shp is not None and shp.Collide(sh, int(cl*MM) - 200): return False
            return True
        RC.stub_ok = stub_ok
        o_emit = RC.emit
        def emit(ctx_, net, pl, Pp, stubs):
            added = o_emit(ctx_, net, pl, Pp, stubs)
            for v in added:
                if v.GetClass() == 'PCB_VIA' and v.GetWidth(pcbnew.F_Cu) < 0.59 * MM:
                    gy, gx = int(round(ctx.cy(v.GetY() / MM))), int(round(ctx.cx(v.GetX() / MM)))
                    if not R.NECK[gy, gx]:
                        v.SetWidth(int(0.6 * MM)); v.SetDrill(int(0.3 * MM)); ctx.add_track(v)
            return added
        RC.emit = emit

    def cl(self, n):
        import fnmatch
        for p in self.ctx.pats:
            if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
        return 'Default'

    def build_masks(self):
        ctx = self.ctx; b = ctx.b
        for z in b.Zones():
            if not z.GetIsRuleArea(): continue
            nm = z.GetZoneName()
            if nm.startswith('BKO_'): ctx.poly_fill(self.BKO, [ring_of(z)], True)
            elif nm.startswith('NECK_'): ctx.poly_fill(self.NECK, [ring_of(z)], True)
            elif z.GetDoNotAllowVias() and not z.GetDoNotAllowTracks(): ctx.poly_fill(self.NOVIA, [ring_of(z)], True)
        for f in b.GetFootprints():
            for z in f.Zones():
                if z.GetIsRuleArea() and z.GetDoNotAllowVias() and not z.GetDoNotAllowTracks(): ctx.poly_fill(self.NOVIA, [ring_of(z)], True, 0.3)
        swn = set(n for n in ctx.netid if self.cl(n) == 'SWITCH'); bon = set(n for n in ctx.netid if self.cl(n) == 'BOOT')
        for f in b.GetFootprints():
            for p in f.Pads():
                n = str(p.GetNetname())
                if n in swn or n in bon:
                    for li, L in enumerate(LAYS):
                        if p.IsOnLayer(L):
                            for ring in ctx.pad_poly(p, L):
                                if n in swn: ctx.poly_fill(self.SW[li], [ring], True)
                                ctx.poly_fill(self.SWB[li], [ring], True)
        for t in b.Tracks():
            n = str(t.GetNetname())
            if n not in swn and n not in bon: continue
            lis = [0, 1, 2] if t.GetClass() == 'PCB_VIA' else ([LAYS.index(t.GetLayer())] if t.GetLayer() in LAYS else [])
            for li in lis:
                if t.GetClass() == 'PCB_VIA': a = c = (t.GetX() / MM, t.GetY() / MM); w = t.GetWidth(pcbnew.F_Cu) / MM
                else: a = (t.GetStart().x / MM, t.GetStart().y / MM); c = (t.GetEnd().x / MM, t.GetEnd().y / MM); w = t.GetWidth() / MM
                if n in swn: ctx.seg_fill(self.SW[li], a, c, w, True)
                ctx.seg_fill(self.SWB[li], a, c, w, True)
        for z in b.Zones():
            if z.GetIsRuleArea(): continue
            n = str(z.GetNetname())
            if n not in swn and n not in bon: continue
            for li, L in enumerate(LAYS):
                if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L):
                    for rings in ctx.zone_polys(z, L):
                        if n in swn: ctx.poly_fill(self.SW[li], rings, True)
                        ctx.poly_fill(self.SWB[li], rings, True)

    def fix_edge(self):
        """track obstacles = track keep-outs (footprint ones +0.3) + antenna keep-out + board outside; via-only keep-outs go to NOVIA"""
        ctx = self.ctx; ctx.edge[:] = False
        for f in ctx.b.GetFootprints():
            for z in f.Zones():
                if z.GetIsRuleArea() and z.GetDoNotAllowTracks(): ctx.poly_fill(ctx.edge, [ring_of(z)], True, 0.3)
        for z in ctx.b.Zones():
            if z.GetIsRuleArea() and (z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT' or z.GetDoNotAllowTracks()): ctx.poly_fill(ctx.edge, [ring_of(z)], True)
        ps = pcbnew.SHAPE_POLY_SET(); ctx.b.GetBoardPolygonOutlines(ps, True)
        ring = [(ps.Outline(0).CPoint(k).x / MM, ps.Outline(0).CPoint(k).y / MM) for k in range(ps.Outline(0).PointCount())]
        inside = np.zeros((ctx.H, ctx.W), bool); ctx.poly_fill(inside, [ring], True); ctx.edge |= ~inside

    def zone_obstacles(self):
        ctx = self.ctx
        for z in ctx.b.Zones():
            if z.GetIsRuleArea(): continue
            n = str(z.GetNetname())
            if n == '': continue
            i = ctx.netid.get(n, 30000); g = ctx.grp_of(ctx.cls.get(n, 'SIGNAL'))
            for li, L in enumerate(LAYS):
                if n == 'GND' and L != pcbnew.F_Cu: continue
                if not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
                for rings in ctx.zone_polys(z, L):
                    if not rings or len(rings[0]) < 3: continue
                    # In2 islands: outer ring only (no signal via in any island, even in a fill hole)
                    ctx.poly_fill(ctx.R[g][li], rings[:1] if L == pcbnew.In2_Cu else rings, i)
        # footprint/board track keep-outs and the board outside stay in ctx.edge (built by Ctx)

    def hard(self, li, y0, y1, x0, x1, w):
        ctx = self.ctx; s = (slice(y0, y1), slice(x0, x1)); c = self.cur; m = 0.04
        bl = np.zeros((y1 - y0, x1 - x0), bool)
        nk = self.NECK[s]
        bl |= ctx.dilate(self.SW[li][s], (w / 2 + 0.3 + m) / G)
        if c['cls'] in SENS: bl |= ctx.dilate(self.SW[li][s], (w / 2 + 1.0 + m) / G) & ~nk   # neck_ic overrides to 0.2 inside NECK areas: keep 0.3 there
        if c['crit']: bl |= ctx.dilate(self.SWB[li][s], (w / 2 + 2.0 + m) / G) & ~nk | ctx.dilate(self.SWB[li][s], (w / 2 + 0.5 + m) / G)
        if li == 2 and c['bko']: bl |= ctx.dilate(self.BKO[s], (w / 2 + 0.05) / G)
        if w < c['floor'] - 1e-9: bl |= ~self.NECK[s]
        return bl

    def seg_hard(self, l, a, c, w):
        """True if segment a-c (mm) of width w on layer index l touches a hard mask cell"""
        ctx = self.ctx
        xs = (min(a[0], c[0]) - w - 2.5, max(a[0], c[0]) + w + 2.5); ys = (min(a[1], c[1]) - w - 2.5, max(a[1], c[1]) + w + 2.5)
        x0 = max(int(ctx.cx(xs[0])), 0); x1 = min(int(ctx.cx(xs[1])) + 1, ctx.W); y0 = max(int(ctx.cy(ys[0])), 0); y1 = min(int(ctx.cy(ys[1])) + 1, ctx.H)
        hm = self.hard(l, y0, y1, x0, x1, w)
        if not hm.any(): return False
        tmp = np.zeros((ctx.H, ctx.W), bool)
        r = ctx.seg_fill(tmp, a, c, max(w - 0.06, 0.05), True)
        gy0, gy1, gx0, gx1, mk = r
        sub = np.zeros((y1 - y0, x1 - x0), bool)
        ay0, ay1, ax0, ax1 = max(gy0, y0), min(gy1, y1), max(gx0, x0), min(gx1, x1)
        sub[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = mk[ay0 - gy0:ay1 - gy0, ax0 - gx0:ax1 - gx0]
        return bool((sub & hm).any())

    def simplify_run(self, ctx, net, pts):
        if len(pts) < 3: return pts
        b = ctx.b; cls = ctx.cls.get(net, 'SIGNAL'); li = pts[0][0]; L = LAYS[li]
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
        zl = []
        for z in b.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(L) or str(z.GetNetname()) in (net, ''): continue
            if str(z.GetNetname()) == 'GND' and L != pcbnew.F_Cu: continue
            if z.HasFilledPolysForLayer(L): zl.append(z)
        cme = self.cur.get('cme', 0.2)
        def legal(a, c, w):
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * MM)), int(round(a[1] * MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(c[0] * MM)), int(round(c[1] * MM))))
            t.SetLayer(L); t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape()
            for kind, o, cc in near:
                if kind == 'pad':
                    if o.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                        if o.GetEffectiveHoleShape().Collide(sh, int(0.28 * MM)): return False
                    elif o.GetEffectiveShape(L).Collide(sh, int(0.2 * MM) + 5000): return False
                else:
                    cl = int(max(req_clr(cls, cc), cme if cc != 'GND' else 0.2) * MM) + 5000
                    if (o.GetEffectiveShape(L) if kind == 'via' else o.GetEffectiveShape()).Collide(sh, cl): return False
            for z in zl:
                cz = 0.4 if str(z.GetNetname()) == 'GND' else max(0.2, req_clr(cls, ctx.cls.get(str(z.GetNetname()), 'SIGNAL')))
                if z.GetFilledPolysList(L).Collide(sh, int(cz * MM)): return False
            return not self.seg_hard(li, a, c, w)
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

PRM = {
 'AUDIO':   dict(tiers=[0.25, 0.2], floor=0.25, cme=0.5, dv=0.6, drill=0.3, viacost=15, layers=[0, 2]),
 'I2S_CLK': dict(tiers=[0.25, 0.2], floor=0.25, cme=0.4, dv=0.6, drill=0.3, viacost=15, layers=[0, 2]),
 'USB':     dict(tiers=[0.25, 0.2], floor=0.25, cme=0.4, dv=0.6, drill=0.3, viacost=0, vias=False, layers=[0]),
 'I2C':     dict(tiers=[0.25, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=3, layers=[0, 2]),
 'Default': dict(tiers=[0.25, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=3, layers=[0, 2]),
 'SIGNAL':  dict(tiers=[0.25, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=3, layers=[0, 2]),
 'PWR_LOCAL': dict(tiers=[0.4, 0.3, 0.25, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=4, layers=[0, 2]),
 'GND':     dict(tiers=[0.3, 0.25, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=1, layers=[0, 2]),
}

def gnd_beside(b, v, log):
    x, y = v.GetX() / MM, v.GetY() / MM
    for r in (0.75, 0.85, 1.0, 1.2):
        for k in range(16):
            a = 2 * math.pi * k / 16
            if place_via(b, 'GND', x + r * math.cos(a), y + r * math.sin(a), lock=False) is not None: return True
    log.append(('nognd', str(v.GetNetname()), round(x, 2), round(y, 2))); return False

if __name__ == '__main__':
    inp, outp, sel = sys.argv[1:4]
    over = json.loads(sys.argv[sys.argv.index('--prm') + 1]) if '--prm' in sys.argv else {}
    R = Router(inp); ctx = R.ctx
    if sel.startswith('@'): sel = ','.join(json.load(open(sel[1:])))
    nets = [full(n, ctx.b) for n in sel.split(',') if n]
    if '--sort' in sys.argv:
        def span(n):
            ps = [(p.GetX() / MM, p.GetY() / MM) for f in ctx.b.GetFootprints() for p in f.Pads() if str(p.GetNetname()) == n]
            return (max(x for x, y in ps) - min(x for x, y in ps)) + (max(y for x, y in ps) - min(y for x, y in ps)) if ps else 0
        nets.sort(key=span)
    res = {}; log = []
    for n in nets:
        c = ctx.cls.get(n, 'Default'); P = dict(PRM.get(c, PRM['Default'])); P.update(over.get('*', {})); P.update(over.get(n, {})); P['rip'] = None
        P['gndc'] = 0.2
        R.cur = {'cls': c, 'crit': n in CRIT, 'bko': c not in BKO_EXEMPT_CLS and n not in ('Net-(U7-BST_B+)', 'Net-(U25-BOOT)'), 'floor': P['floor'], 'fine': bool(P.get('fine')), 'cme': P['cme']}
        if P.get('fine'): P['dv'], P['drill'] = 0.5, 0.2
        t = time.time()
        try:
            ok, items = route_net(ctx, n, P, log=lambda *a: None)
        except Exception:
            import traceback; traceback.print_exc(); ok, items = False, []
        if c in ('AUDIO', 'I2S_CLK'):
            for it in items:
                if it.GetClass() == 'PCB_VIA': gnd_beside(ctx.b, it, log)
        if '--lock' in sys.argv:
            for it in items: it.SetLocked(True)
        nv = sum(1 for it in items if it.GetClass() == 'PCB_VIA')
        res[n] = (ok, len(items), len(comps_of(ctx, n)) - 1, nv)
        print('%-9s %-34s %s items %d vias %d open %d %.1fs' % (c, n, 'OK' if ok else 'FAIL', len(items), nv, res[n][2], time.time() - t), flush=True)
    refill(ctx.b)
    pcbnew.SaveBoard(outp, ctx.b)
    json.dump({'res': res, 'log': log}, open(outp.replace('.kicad_pcb', '.route.json'), 'w'), indent=1)
    print('done', sum(1 for v in res.values() if v[0]), '/', len(res), 'open edges left', sum(v[2] for v in res.values()), 'log', log[:10])
