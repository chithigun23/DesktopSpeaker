"""flatpak: route_p2_run.py IN.kicad_pcb OUT.kicad_pcb [net1,net2..|ALL] : routes SWITCH/BOOT/SPK_OUT/POWER_HI/PVDD nets with route_p2_core"""
import sys, time, json, os
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_p2_core import *
inp, outp = sys.argv[1], sys.argv[2]
sel = sys.argv[3] if len(sys.argv) > 3 else 'ALL'
ctx = Ctx(inp, inp.replace('.kicad_pcb', '.kicad_pro'))
PRM = {
 'SWITCH': dict(tiers=[1.5, 0.8, 0.4, 0.2], floor=0.4, cme=0.5, dv=0.6, drill=0.3, viacost=8, layers=[0, 2]),
 'BOOT': dict(tiers=[0.3, 0.25, 0.2, 0.2], floor=0.25, cme=0.2, dv=0.6, drill=0.3, viacost=8, layers=[0, 2]),
 'SPK_OUT': dict(tiers=[2.0, 1.0, 0.5, 0.2], floor=0.5, cme=0.3, dv=0.8, drill=0.4, viacost=0, vias=False, layers=[0]),
 'POWER_HI': dict(tiers=[2.0, 1.0, 0.5, 0.2], floor=0.5, cme=0.4, dv=0.8, drill=0.4, viacost=4, layers=[0, 1, 2]),
 'PVDD': dict(tiers=[2.0, 1.0, 0.5, 0.2], floor=0.5, cme=0.3, dv=0.8, drill=0.4, viacost=4, layers=[0, 1, 2]),
}
ORDER = ['SWITCH', 'BOOT', 'SPK_OUT', 'POWER_HI', 'PVDD']
nets = []
for c in ORDER:
    for n in sorted(ctx.netid):
        if ctx.cls[n] == c and (sel == 'ALL' or n in sel.split(',')): nets.append((c, n))
MANAGED = {'SWITCH', 'BOOT', 'SPK_OUT', 'POWER_HI', 'PVDD'}
RPC = {
 'AUDIO': dict(tiers=[0.3, 0.25, 0.25, 0.2], floor=0.25, cme=0.5, dv=0.6, drill=0.3, viacost=8, vias=False, layers=[0]),
 'I2S_CLK': dict(tiers=[0.25, 0.25, 0.2, 0.2], floor=0.25, cme=0.4, dv=0.6, drill=0.3, viacost=8, vias=False, layers=[0]),
 'USB': dict(tiers=[0.25, 0.25, 0.2, 0.2], floor=0.25, cme=0.4, dv=0.6, drill=0.3, viacost=8, vias=False, layers=[0]),
 'I2C': dict(tiers=[0.3, 0.25, 0.2, 0.2], floor=0.25, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 1, 2]),
 'SIGNAL': dict(tiers=[0.25, 0.2, 0.2, 0.2], floor=0.2, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 1, 2]),
 'PWR_LOCAL': dict(tiers=[0.4, 0.3, 0.25, 0.2], floor=0.25, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 1, 2]),
 'PWR_3V': dict(tiers=[0.5, 0.3, 0.25, 0.2], floor=0.3, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 1, 2]),
 'PWR_5V': dict(tiers=[1.0, 0.5, 0.4, 0.2], floor=0.4, cme=0.2, dv=0.6, drill=0.3, viacost=6, layers=[0, 1, 2]),
}
DEF = RPC['SIGNAL']
cur = [None]
RIPPEN = {'SWITCH': 25, 'BOOT': 25, 'SPK_OUT': 25, 'POWER_HI': 25, 'PVDD': 25, 'AUDIO': 40, 'I2S_CLK': 40, 'USB': 40, 'GND': 6}
L = lambda *a: print(*a, flush=True)
queue = []; ripped_all = set(); ok = {}; gnd_pads = []
GRAVE = []
def rippable_ids():
    return {ctx.netid[n]: RIPPEN.get(ctx.cls[n], 10) for n in ctx.netid if n != cur[0] and ((ctx.cls[cur[0]] in MANAGED and not os.environ.get('NOMANRIP')) or ctx.cls[n] not in MANAGED)}
def hits_of(added, cme, own=None):
    """foreign non-managed track/via objects that violate clearance to the new items"""
    res = []; addid = {a.m_Uuid.AsString() for a in added}
    for t in ctx.b.Tracks():
        n = str(t.GetNetname())
        if n not in ctx.netid or n == own or t.m_Uuid.AsString() in addid or (ctx.cls[own] not in MANAGED and ctx.cls[n] in MANAGED): continue
        c = 0.2 if ctx.cls[n] == 'GND' else (0.4 if ctx.cls[n] == 'POWER_HI' else 0.3 if ctx.cls[n] in ('PVDD','SPK_OUT') else 0.5 if ctx.cls[n] == 'AUDIO' else (0.4 if ctx.cls[n] in ('I2S_CLK', 'USB') else cme))
        c = int((max(c, 0.2) - 0.001) * MM); hit = False
        for a in added:
            if a.GetClass() == 'PCB_VIA':
                if t.GetClass() == 'PCB_VIA': hit = t.GetEffectiveShape(pcbnew.F_Cu).Collide(a.GetEffectiveShape(pcbnew.F_Cu), c)
                else: hit = t.GetEffectiveShape().Collide(a.GetEffectiveShape(t.GetLayer()), c)
            else:
                if t.GetClass() == 'PCB_VIA': hit = t.GetEffectiveShape(a.GetLayer()).Collide(a.GetEffectiveShape(), c)
                elif t.GetLayer() == a.GetLayer(): hit = t.GetEffectiveShape().Collide(a.GetEffectiveShape(), c)
            if hit: break
        if hit: res.append(t)
    return res
def do_rip(added, cme, own=None):
    hits = hits_of(added, cme, own)
    names = set(str(t.GetNetname()) for t in hits)
    gh = [t for t in hits if str(t.GetNetname()) == 'GND']
    others = names - {'GND'}
    # GND: remove cluster of connected GND track/via
    if gh:
        gall = [t for t in ctx.b.Tracks() if str(t.GetNetname()) == 'GND']
        K = lambda o: o.m_Uuid.AsString()
        cl = set(K(t) for t in gh); objs = {K(t): t for t in gall}; changed = True
        while changed:
            changed = False
            for t in gall:
                if K(t) in cl: continue
                for u in [objs[i] for i in cl]:
                    sh = lambda o, l: o.GetEffectiveShape(l) if o.GetClass() == 'PCB_VIA' else o.GetEffectiveShape()
                    lay = u.GetLayer() if u.GetClass() != 'PCB_VIA' else t.GetLayer()
                    try:
                        if t.GetClass() == 'PCB_VIA' or u.GetClass() == 'PCB_VIA' or t.GetLayer() == u.GetLayer():
                            l = t.GetLayer() if t.GetClass() != 'PCB_VIA' else u.GetLayer()
                            if sh(t, l).Collide(sh(u, l), 0): cl.add(K(t)); changed = True; break
                    except Exception: pass
        for i in cl:
            o = objs[i]
            for f in ctx.b.GetFootprints():
                for p in f.Pads():
                    if str(p.GetNetname()) == 'GND' and p.IsOnLayer(pcbnew.F_Cu) and o.GetClass() != 'PCB_VIA' and p.GetEffectiveShape(pcbnew.F_Cu).Collide(o.GetEffectiveShape(), 0) and o.GetLayer() == pcbnew.F_Cu:
                        gnd_pads.append(padkey(p))
            ctx.b.RemoveNative(o); GRAVE.append(o)
    for x in list(ctx.b.Tracks()):
        if str(x.GetNetname()) in others: ctx.b.RemoveNative(x); GRAVE.append(x)
    ctx.rebuild()
    for nme in others: ripped_all.add(nme); queue.append(nme)
    return others, len(gh)
def do_net(c, n, depth=0):
    cur[0] = n
    t = time.time(); items = []; r = False
    base = dict(PRM.get(c) or RPC.get(c, DEF))
    atts = [(None, base['cme'])]
    if c == 'SWITCH': atts += [(None, 0.3)]
    if c in ('POWER_HI', 'PVDD'): atts += [(None, base['cme'], 0.6)]
    if depth < 3: atts += [('rip', base['cme'])] + ([('rip', 0.3)] if c == 'SWITCH' else [])
    for att in atts:
        P_ = dict(base); P_['cme'] = att[1]
        P_['gndc'] = {'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3}.get(c, 0.2)
        if len(att) > 2: P_['dv'] = att[2]; P_['drill'] = 0.3
        P_['rip'] = rippable_ids() if att[0] == 'rip' else None
        if att[0] == 'rip': P_['margins'] = (10, 25)
        r, i2 = route_net(ctx, n, P_, log=L); items += i2
        if att[0] == 'rip' and i2:
            h, g = do_rip(i2, att[1], n)
            L('   rip', sorted(h), 'gnd clusters', g)
        if r: break
    L('%-8s %-32s %s items %d %.1fs' % (c, n, 'OK' if r else 'FAIL', len(items), time.time() - t))
    ok[n] = r
CLEAR = [('U4', 5.5), ('U6', 5.0), ('U7', 5.0), ('U25', 4.5), ('U14', 3.5), ('U15', 3.5)]
def clear_regions():
    names = set(); gcl = []
    for ref, r in CLEAR:
        f = [x for x in ctx.b.GetFootprints() if x.GetReference() == ref][0]
        c = f.GetPosition(); box = pcbnew.BOX2I(pcbnew.VECTOR2I(c.x - int(r * MM), c.y - int(r * MM)), pcbnew.VECTOR2I(int(2 * r * MM), int(2 * r * MM)))
        for t in ctx.b.Tracks():
            n = str(t.GetNetname())
            if n not in ctx.netid or ctx.cls[n] in MANAGED or not box.Intersects(t.GetBoundingBox()): continue
            if n == 'GND': gcl.append(t)
            else: names.add(n)
    # GND: remove only the touched tracks/vias (+ pads recorded)
    for t in gcl:
        pass
    L('clearing nets', len(names), 'gnd items', len(gcl))
    if gcl:
        gh = gcl
        for t in gh:
            for f in ctx.b.GetFootprints():
                for p in f.Pads():
                    if str(p.GetNetname()) == 'GND' and p.IsOnLayer(pcbnew.F_Cu) and p.GetEffectiveShape(pcbnew.F_Cu).Collide(t.GetEffectiveShape(pcbnew.F_Cu) if t.GetClass() == 'PCB_VIA' else t.GetEffectiveShape(), 0): gnd_pads.append(padkey(p))
    for x in list(ctx.b.Tracks()):
        n = str(x.GetNetname())
        if n in names or any(x.m_Uuid.AsString() == g.m_Uuid.AsString() for g in gcl): ctx.b.RemoveNative(x); GRAVE.append(x)
    ctx.rebuild()
    for n in names: ripped_all.add(n); queue.append(n)
import traceback
only = None
if '--only' in sys.argv:
    only = json.load(open(sys.argv[sys.argv.index('--only') + 1]))
    nets = sorted([(ctx.cls[n], n) for n in only if n in ctx.netid], key=lambda x: (ORDER.index(x[0]) if x[0] in ORDER else 99))
if '--noclear' not in sys.argv and only is None: clear_regions()
def safe(c, n, d=0):
    try: do_net(c, n, d)
    except Exception: traceback.print_exc(); ok[n] = False
for c, n in nets:
    if len(comps_of(ctx, n)) <= 1: continue
    safe(c, n)
    pcbnew.SaveBoard(outp, ctx.b)
for rnd in range(4):
    q = [x for x in dict.fromkeys(queue)]; queue.clear()
    if not q: break
    L('--- reroute round', rnd, len(q))
    for n in q:
        if len(comps_of(ctx, n)) <= 1: continue
        safe(ctx.cls[n], n, 1 + rnd)
pcbnew.SaveBoard(outp, ctx.b)
json.dump({'gnd_pads': gnd_pads, 'ripped': sorted(ripped_all), 'ok': ok}, open(outp.replace('.kicad_pcb', '.run.json'), 'w'))
print('saved', outp, sum(ok.values()), '/', len(ok), 'ripped', len(ripped_all), 'gnd pads', len(gnd_pads))
