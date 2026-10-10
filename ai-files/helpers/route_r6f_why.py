"""flatpak: route_r6f_why.py BOARD NET LAYER W X1 Y1 X2 Y2 | BOARD NET via D X Y : list items that make a track segment (or via) illegal under route_r6a_lib rules (req clearance, actual gap)"""
import sys, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
a = sys.argv; b = pcbnew.LoadBoard(a[1]); n = full(a[2], b); cn = ncls(n)
if a[3] == 'via':
    D = float(a[4]); x, y = float(a[5]), float(a[6])
    t = pcbnew.PCB_VIA(b); t.SetPosition(V(x, y)); t.SetWidth(int(D * MM)); t.SetDrill(int((0.3 if D >= 0.6 else 0.2) * MM)); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    layers = [pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu]
    def shp(L): return t.GetEffectiveShape(L)
else:
    L0 = LAY[a[3]]; w = float(a[4]); p1 = (float(a[5]), float(a[6])); p2 = (float(a[7]), float(a[8]))
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p1)); t.SetEnd(V(*p2)); t.SetLayer(L0); t.SetWidth(int(w * MM)); layers = [L0]
    def shp(L): return t.GetEffectiveShape()
bb = t.GetBoundingBox(); bb.Inflate(int(2 * MM))
def gap(s1, s2):
    for c in range(0, 3000, 5):
        if s1.Collide(s2, int(c / 1000 * MM)): return c / 1000
    return 9
for f in b.GetFootprints():
    if not bb.Intersects(f.GetBoundingBox()): continue
    for p in f.Pads():
        pn = str(p.GetNetname())
        if pn == n and pn: continue
        for L in layers:
            if not p.IsOnLayer(L): continue
            r = req(cn, ncls(pn) if pn else 'Default', False, True); g = gap(p.GetEffectiveShape(L), shp(L))
            if g < r: print('pad %s.%s %s L%d gap %.3f req %.2f' % (f.GetReference(), p.GetNumber(), pn, L, g, r))
for u in b.Tracks():
    if not bb.Intersects(u.GetBoundingBox()): continue
    un = str(u.GetNetname())
    if un == n: continue
    r = req(cn, ncls(un), False, False)
    for L in layers:
        if u.GetClass() == 'PCB_VIA': s = u.GetEffectiveShape(L)
        elif u.GetLayer() == L: s = u.GetEffectiveShape()
        else: continue
        g = gap(s, shp(L))
        if g < r: print('%s %s L%d (%.2f,%.2f)-(%.2f,%.2f) gap %.3f req %.2f' % ('via' if u.GetClass() == 'PCB_VIA' else 'trk', un, L, u.GetStart().x / MM, u.GetStart().y / MM, u.GetEnd().x / MM, u.GetEnd().y / MM, g, r))
for z in b.Zones():
    zn = str(z.GetNetname())
    for L in layers:
        if not z.IsOnLayer(L): continue
        if z.GetIsRuleArea():
            if z.Outline().Collide(shp(L)) and (z.GetDoNotAllowTracks() or z.GetZoneName().startswith('BKO')): print('rulearea', z.GetZoneName(), L)
            continue
        if zn in (n, '', 'GND'): continue
        if z.Outline().Collide(shp(L), int(0.3 * MM)): print('zone', z.GetZoneName(), zn, 'L%d' % L)
print('done')
