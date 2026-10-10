"""flatpak: route_r6h_route.py IN.kicad_pcb OUT.kicad_pcb NETS(comma|@file) [--in2] [--prm JSON] [--maxexp N] [--verb]
R6h signal router = route_r6c_route (R6b/R6c rules) plus the R6h In2 exception:
 --in2 : the listed nets may also use In2 (layer index 1), only for SLOW nets (checked against SLOW_OK below),
         outside every non-GND In2 island with >= 0.3 mm (+ margin) clearance to the island outline.
 Vias stay out of In2 islands (as before). AUDIO/I2S/USB/SWITCH-related nets are refused for --in2."""
import sys, time, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import route_r6c_route as RR
from route_r6c_route import *
import numpy as np

# slow nets authorised for In2 corridors (coordinator decision R6h)
SLOW_OK = set(json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_r6h_slow.json')))

_hard0 = RR.Router.hard
_init0 = RR.Router.__init__
def _init(self, inp):
    _init0(self, inp)
    ctx = self.ctx; self.ISL = np.zeros((ctx.H, ctx.W), bool)
    for z in ctx.b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or str(z.GetNetname()) in ('GND', ''): continue
        if z.GetZoneName() in VIAISL.split(','): continue
        ctx.poly_fill(self.ISL, [ring_of(z)], True)
def _hard(self, li, y0, y1, x0, x1, w):
    bl = _hard0(self, li, y0, y1, x0, x1, w)
    if li == 1:
        bl |= self.ctx.dilate(self.ISL[y0:y1, x0:x1], (w / 2 + 0.3 + self.ctx.MARGIN + 0.02) / G)
    return bl
import os
VIAISL = os.environ.get('R6H_VIAISL', '')   # comma list of In2 island zone names that U4-group vias may pass (clearance hole); In2 tracks stay off
_zo0 = RR.Router.zone_obstacles
def _zo(self):
    if not VIAISL: return _zo0(self)
    ctx = self.ctx; skip = set(VIAISL.split(','))
    for z in ctx.b.Zones():
        if z.GetIsRuleArea(): continue
        n = str(z.GetNetname())
        if n == '': continue
        i = ctx.netid.get(n, 30000); g = ctx.grp_of(ctx.cls.get(n, 'SIGNAL'))
        for li, L in enumerate(LAYS):
            if n == 'GND' and L != pcbnew.F_Cu: continue
            if L == pcbnew.In2_Cu and z.GetZoneName() in skip: continue
            if not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
            for rings in ctx.zone_polys(z, L):
                if not rings or len(rings[0]) < 3: continue
                ctx.poly_fill(ctx.R[g][li], rings[:1] if L == pcbnew.In2_Cu else rings, i)
RR.Router.__init__ = _init; RR.Router.hard = _hard; RR.Router.zone_obstacles = _zo
U4NETS = ('/Battery_Charger/CE_N', 'Net-(U4-QON)', '/Battery_Charger/ILIM_HIZ', 'Net-(U4-BATP)', '/CHG_INT', '/CTRL_SCL', '/CTRL_SDA')

if __name__ == '__main__':
    inp, outp, sel = sys.argv[1:4]
    over = json.loads(sys.argv[sys.argv.index('--prm') + 1]) if '--prm' in sys.argv else {}
    R = RR.Router(inp); ctx = R.ctx
    if sel.startswith('@'): sel = ','.join(json.load(open(sel[1:])))
    nets = [full(n, ctx.b) for n in sel.split(',') if n]
    res = {}; log = []
    for n in nets:
        c = ctx.cls.get(n, 'Default'); P = dict(RR.PRM.get(c, RR.PRM['Default'])); P.update(over.get('*', {})); P.update(over.get(n, {})); P['rip'] = None
        P['gndc'] = 0.2
        if '--maxexp' in sys.argv: P['maxexp'] = int(sys.argv[sys.argv.index('--maxexp') + 1])
        if VIAISL and n not in U4NETS: print('REFUSE viaisl', n); continue
        if VIAISL: P['layers'] = [0, 2]
        if '--in2' in sys.argv and not VIAISL:
            if n not in SLOW_OK or c not in ('Default', 'I2C', 'SIGNAL'): print('REFUSE in2', n, c); P['layers'] = [0, 2]
            else: P['layers'] = [0, 1, 2]
        R.cur = {'cls': c, 'crit': n in RR.CRIT, 'bko': c not in RR.BKO_EXEMPT_CLS and n not in ('Net-(U7-BST_B+)', 'Net-(U25-BOOT)') and n not in RR.BKO_EXTRA, 'floor': P['floor'], 'fine': bool(P.get('fine')), 'cme': P['cme']}
        if P.get('fine'): P['dv'], P['drill'] = 0.5, 0.2
        t = time.time()
        try:
            ok, items = route_net(ctx, n, P, log=(print if '--verb' in sys.argv else (lambda *a: None)))
        except Exception:
            import traceback; traceback.print_exc(); ok, items = False, []
        if c in ('AUDIO', 'I2S_CLK'):
            for it in items:
                if it.GetClass() == 'PCB_VIA': RR.gnd_beside(ctx.b, it, log)
        nv = sum(1 for it in items if it.GetClass() == 'PCB_VIA')
        L = sum(it.GetLength() for it in items if it.GetClass() != 'PCB_VIA') / MM
        n2 = sum(it.GetLength() for it in items if it.GetClass() != 'PCB_VIA' and it.GetLayer() == pcbnew.In2_Cu) / MM
        res[n] = (ok, len(items), len(comps_of(ctx, n)) - 1, nv, round(L, 1), round(n2, 1))
        print('%-9s %-34s %s items %d vias %d open %d len %.1f in2 %.1f %.1fs' % (c, n, 'OK' if ok else 'FAIL', len(items), nv, res[n][2], L, n2, time.time() - t), flush=True)
    refill(ctx.b)
    pcbnew.SaveBoard(outp, ctx.b)
    json.dump({'res': res, 'log': log}, open(outp.replace('.kicad_pcb', '.route.json'), 'w'), indent=1)
    print('done', sum(1 for v in res.values() if v[0]), '/', len(res), 'open edges left', sum(v[2] for v in res.values()), 'log', log[:10])
