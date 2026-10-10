"""flatpak: route_r6k_why.py BOARD NET LAYER x1 y1 x2 y2 w : route_r6j_smooth.py legality verdict for one straight segment (ok or rule code + the blocking item).
Same-net segments touching either end are ignored."""
import sys, math, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
import route_r6i_bends as RB
a = sys.argv; inp, outp = a[1], a[1]
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

net = a[2]; L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, '2': pcbnew.In2_Cu}[a[3]]; p = (float(a[4]), float(a[5])); q = (float(a[6]), float(a[7])); w = float(a[8])
net = full(net, b)
print(why(net, L, p, q, w, set()))
t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(w * MM))); sh = t.GetEffectiveShape()
for u in b.Tracks():
    if str(u.GetNetname()) == net: continue
    us = u.GetEffectiveShape(L) if u.GetClass() == 'PCB_VIA' else (u.GetEffectiveShape() if u.GetLayer() == L else None)
    if us is None: continue
    r = need(net, str(u.GetNetname()), False, False, sh, L)
    if not gap_ok(us, sh, r): print('  blocks:', u.GetClass(), u.GetNetname(), u.GetPosition().x / MM, u.GetPosition().y / MM, 'need', r)
for f in b.GetFootprints():
    for pd in f.Pads():
        if str(pd.GetNetname()) == net or not pd.IsOnLayer(L): continue
        r = need(net, str(pd.GetNetname()), False, True, sh, L)
        if not gap_ok(pd.GetEffectiveShape(L), sh, r): print('  blocks pad', f.GetReference(), pd.GetNumber(), pd.GetNetname(), 'need', r)
for z in fzones:
    if str(z.GetNetname()) == net or not z.IsOnLayer(L): continue
    if L == pcbnew.In2_Cu and z.Outline().Collide(sh, int(0.3 * MM)): print('  blocks In2 zone outline', z.GetZoneName())
