"""flatpak: route_r6a_astar.py IN.kicad_pcb OUT.kicad_pcb NETS(comma)|CLASSES:..  [--lock]
R6a scripted routing of the leftover power connections with the route_p2 raster A* router.
Differences to route_p2_run: no rip-up (hand copper and locked items stay), zone fills of all non-GND nets are
obstacles, layers F.Cu/B.Cu only (In2 is power-island only), SWITCH/SPK_OUT F.Cu only, new items locked."""
import sys, time, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_p2_core import *
from route_r6a_lib import full, refill
import route_p2_core
route_p2_core.lib = ctypes.CDLL('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_r6a_astar.so')
route_p2_core.lib.astar.restype = ctypes.c_int
inp, outp, sel = sys.argv[1:4]
ctx = Ctx(inp, '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6a.kicad_pro')
def add_zone_obstacles():
    for z in ctx.b.Zones():
        if z.GetIsRuleArea(): continue
        n = str(z.GetNetname())
        if n == '': continue
        i = ctx.netid.get(n, 30000); g = ctx.grp_of(ctx.cls.get(n, 'SIGNAL'))
        for li, L in enumerate(LAYS):
            if n == 'GND' and L != pcbnew.F_Cu: continue
            if not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
            for rings in ctx.zone_polys(z, L):
                if rings and len(rings[0]) >= 3: ctx.poly_fill(ctx.R[g][li], rings, i)
# footprint keep-outs that only forbid vias (J7 TC2030) must not block tracks: rebuild the edge mask, keep a separate no-via mask
NOVIA = np.zeros((ctx.H, ctx.W), bool)
def fix_edge():
    ctx.edge[:] = False
    for f in ctx.b.GetFootprints():
        for z in f.Zones():
            if not z.GetIsRuleArea(): continue
            o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
            if z.GetDoNotAllowTracks(): ctx.poly_fill(ctx.edge, [ring], True, 0.3)
            elif z.GetDoNotAllowVias(): ctx.poly_fill(NOVIA, [ring], True, 0.3)
    for z in ctx.b.Zones():
        if z.GetIsRuleArea() and (z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT' or z.GetDoNotAllowTracks()):
            o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
            ctx.poly_fill(ctx.edge, [ring], True)
        elif z.GetIsRuleArea() and z.GetDoNotAllowVias():
            o = z.Outline().Outline(0); ring = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
            ctx.poly_fill(NOVIA, [ring], True)
    ps = pcbnew.SHAPE_POLY_SET(); ctx.b.GetBoardPolygonOutlines(ps, True)
    ring = [(ps.Outline(0).CPoint(k).x / MM, ps.Outline(0).CPoint(k).y / MM) for k in range(ps.Outline(0).PointCount())]
    inside = np.zeros((ctx.H, ctx.W), bool); ctx.poly_fill(inside, [ring], True); ctx.edge |= ~inside
fix_edge()
_orig_vo = ctx.via_obstacle
def via_obstacle(me, y0, y1, x0, x1, dv, cme, **k):
    return _orig_vo(me, y0, y1, x0, x1, dv, cme, **k) | ctx.dilate(NOVIA[y0:y1, x0:x1], (dv / 2 + 0.05) / G)
ctx.via_obstacle = via_obstacle
_orig_rebuild = ctx.rebuild
def rebuild():
    _orig_rebuild(); fix_edge(); add_zone_obstacles()
ctx.rebuild = rebuild
add_zone_obstacles()
# optional layer penalty: on penalised layers only the narrowest tier is offered (cost x2.2 in the A*), so long runs prefer In2
LAYPEN = {'on': False, 'layers': (), 'wmin': 0.5}
_orig_obstacle = ctx.obstacle
def obstacle(me, li, y0, y1, x0, x1, w, cme, **k):
    if LAYPEN['on'] and li in LAYPEN['layers'] and w > LAYPEN['wmin'] + 1e-9 and k.get('cpad') != 0.26:
        return np.ones((y1 - y0, x1 - x0), bool)
    return _orig_obstacle(me, li, y0, y1, x0, x1, w, cme, **k)
ctx.obstacle = obstacle
PRM = {
 'SWITCH': dict(tiers=[1.5, 1.0, 0.6, 0.4], floor=0.4, cme=0.3, dv=0.6, drill=0.3, viacost=0, vias=False, layers=[0]),
 'SPK_OUT': dict(tiers=[2.0, 1.5, 1.0, 0.5], floor=0.5, cme=0.3, dv=0.8, drill=0.4, viacost=0, vias=False, layers=[0]),
 'POWER_HI': dict(tiers=[1.0, 0.8, 0.6, 0.5], floor=0.5, cme=0.4, dv=0.6, drill=0.3, viacost=6, layers=[0, 2]),
 'PVDD': dict(tiers=[2.0, 1.0, 0.6, 0.5], floor=0.5, cme=0.3, dv=0.6, drill=0.3, viacost=6, layers=[0, 2]),
 'BOOT': dict(tiers=[0.3, 0.25, 0.2, 0.2], floor=0.2, cme=0.3, dv=0.6, drill=0.3, viacost=8, layers=[0, 2]),
 'SIGNAL': dict(tiers=[0.25, 0.2, 0.2, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=4, layers=[0, 2]),
 'PWR_5V': dict(tiers=[1.0, 0.6, 0.5, 0.4], floor=0.4, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 2]),
 'PWR_3V': dict(tiers=[0.8, 0.5, 0.4, 0.3], floor=0.3, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 2]),
}
# --seeds x,y;x,y : copper groups containing a via at one of these points count as components (pre-placed jumpers)
SEEDS = []
if '--seeds' in sys.argv:
    SEEDS = [tuple(map(float, q.split(','))) for q in sys.argv[sys.argv.index('--seeds') + 1].split(';')]
    import route_p2_core as _rc
    _src = open('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_p2_core.py').read()
    _i = _src.index('def comps_of'); _j = _src.index('def comp_refs')
    _code = _src[_i:_j].replace("comps = [g for g in groups.values() if any(x[0] == 'pad' for x in g)]",
        "comps = [g for g in groups.values() if any(x[0] == 'pad' for x in g) or any(x[0] == 'via' and any(abs(x[1].GetX() / MM - sx) < 0.01 and abs(x[1].GetY() / MM - sy) < 0.01 for sx, sy in SEEDS) for x in g)]")
    _ns = dict(vars(_rc)); _ns['SEEDS'] = SEEDS; exec(_code, _ns)
    _rc.comps_of = _ns['comps_of']; comps_of = _ns['comps_of']
over = json.loads(sys.argv[sys.argv.index('--prm') + 1]) if '--prm' in sys.argv else {}
nets = [full(n, ctx.b) for n in sel.split(',') if n]
res = {}
for n in nets:
    c = ctx.cls.get(n, 'SIGNAL'); P = dict(PRM.get(c, PRM['SIGNAL'])); P.update(over.get(n, {})); P['rip'] = None
    P['gndc'] = {'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3}.get(c, 0.2)
    LAYPEN['on'] = bool(P.get('inner_pref')); LAYPEN['layers'] = (0, 2); LAYPEN['wmin'] = P['tiers'][-1]
    t = time.time()
    try:
        ok, items = route_net(ctx, n, P, log=lambda *a: print(*a, flush=True))
    except Exception as e:
        import traceback; traceback.print_exc(); ok, items = False, []
    for it in items: it.SetLocked(True)
    res[n] = (ok, len(items), len(comps_of(ctx, n)) - 1)
    print('%-8s %-34s %s items %d open %d %.1fs' % (c, n, 'OK' if ok else 'FAIL', len(items), res[n][2], time.time() - t), flush=True)
refill(ctx.b)
pcbnew.SaveBoard(outp, ctx.b)
json.dump(res, open(outp.replace('.kicad_pcb', '.astar.json'), 'w'), indent=1)
