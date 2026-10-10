"""flatpak: route_r6c_zones.py BOARD [substr] : list zones/rule areas with bbox"""
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); MM=1e6
for z in b.Zones():
    nm=z.GetZoneName(); n=str(z.GetNetname())
    if len(sys.argv)>2 and sys.argv[2] not in nm+n: continue
    bb=z.GetBoundingBox(); print(('RULE ' if z.GetIsRuleArea() else 'ZONE '),nm,n,[pcbnew.BOARD.GetStandardLayerName(l) for l in z.GetLayerSet().Seq()],'%.1f %.1f %.1f %.1f'%(bb.GetLeft()/MM,bb.GetTop()/MM,bb.GetRight()/MM,bb.GetBottom()/MM),'tracks' if z.GetDoNotAllowTracks() else '','vias' if z.GetDoNotAllowVias() else '')
