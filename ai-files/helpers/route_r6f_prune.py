"""flatpak: route_r6f_prune.py IN OUT [NET,NET..] : iteratively remove dangling track ends (a track end touching no same-net pad/via/track/zone) and vias touching copper on fewer than two layers; optional net filter"""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); flt = set(sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] else None
def touches(net, pt, layer, skip):
    for f in b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname()) == net and p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(pcbnew.VECTOR2I(pt), 1000): return True
    for t in b.GetTracks():
        if t.m_Uuid.AsString() == skip.m_Uuid.AsString() or str(t.GetNetname()) != net: continue
        if t.GetClass() == 'PCB_VIA':
            if t.GetEffectiveShape(layer).Collide(pcbnew.VECTOR2I(pt), 1000): return True
        elif t.GetLayer() == layer and t.GetEffectiveShape().Collide(pcbnew.VECTOR2I(pt), 1000): return True
    for z in b.Zones():
        if not z.GetIsRuleArea() and str(z.GetNetname()) == net and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer) and z.GetFilledPolysList(layer).Collide(pcbnew.VECTOR2I(pt), 1000): return True
    return False
tot = 0
while True:
    rm = []
    for t in b.GetTracks():
        n = str(t.GetNetname())
        if n in ('', 'GND') or (flt and n not in flt): continue
        if t.GetClass() == 'PCB_VIA':
            ls = [L for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu) if touches(n, t.GetPosition(), L, t)]
            if len(ls) < 2: rm.append(t)
        else:
            if not touches(n, t.GetStart(), t.GetLayer(), t) or not touches(n, t.GetEnd(), t.GetLayer(), t): rm.append(t)
    if not rm: break
    for t in rm: b.RemoveNative(t)
    tot += len(rm)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[2], b); print('pruned', tot)
