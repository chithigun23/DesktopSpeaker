#!/usr/bin/env python3
"""fillsig.py BOARD.kicad_pcb OUT.json  (AppImage python3.11; pcbnew)
Zone-fill signature: per copper zone (teardrop zones summed per layer) the filled area per layer in mm2,
plus counts (zones, teardrop zones, filled polygons, vias, tracks). Two boards with the same copper and the
same fill give the same signature; compare with fillsig_cmp in regen_final.sh (tolerance 0.01 mm2 per zone layer)."""
import pcbnew, sys, os, json
b = pcbnew.LoadBoard(sys.argv[1])
sig = {}; td = 0; zones = 0; polys = 0
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    zones += 1
    is_td = z.IsTeardropArea(); td += is_td
    for L in z.GetLayerSet().Seq():
        if not pcbnew.IsCopperLayer(L): continue
        a = 0.0
        if z.HasFilledPolysForLayer(L):
            sp = z.GetFilledPolysList(L); polys += sp.OutlineCount(); a = sp.Area() / 1e12
        if is_td:
            k = 'TEARDROPS|%s' % b.GetLayerName(L)
        else:
            bb = z.GetBoundingBox()
            k = '%s|%s|%d|%.3f,%.3f,%.3f,%.3f' % (z.GetNetname(), b.GetLayerName(L), z.GetAssignedPriority(),
                bb.GetX()/1e6, bb.GetY()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
        sig[k] = round(sig.get(k, 0.0) + a, 4)
vias = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
json.dump({'zones': zones, 'teardrop_zones': td, 'filled_polys': polys, 'vias': vias,
           'tracks': sum(1 for t in b.GetTracks()) - vias, 'area': sig}, open(sys.argv[2], 'w'), indent=0, sort_keys=True)
print('fillsig zones %d teardrops %d polys %d vias %d' % (zones, td, polys, vias), flush=True)
os._exit(0)
