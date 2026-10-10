"""flatpak: route_r6c_tracks.py BOARD NETSUBSTR... : list tracks/vias/pads of matching nets"""
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); MM=1e6
L={pcbnew.F_Cu:'F',pcbnew.B_Cu:'B',pcbnew.In1_Cu:'1',pcbnew.In2_Cu:'2'}
for n in sys.argv[2:]:
    print('==',n)
    for t in b.GetTracks():
        if str(t.GetNetname())==n:
            if t.GetClass()=='PCB_VIA': print(' via %.2f,%.2f d%.2f/%.2f %s'%(t.GetX()/MM,t.GetY()/MM,t.GetWidth(pcbnew.F_Cu)/MM,t.GetDrillValue()/MM,'L' if t.IsLocked() else ''))
            else: print(' trk %s %.2f,%.2f -> %.2f,%.2f w%.2f %s'%(L[t.GetLayer()],t.GetStart().x/MM,t.GetStart().y/MM,t.GetEnd().x/MM,t.GetEnd().y/MM,t.GetWidth()/MM,'L' if t.IsLocked() else ''))
    for f in b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname())==n: print(' pad',f.GetReference(),p.GetNumber(),round(p.GetX()/MM,2),round(p.GetY()/MM,2))
    for z in b.Zones():
        if str(z.GetNetname())==n and not z.GetIsRuleArea(): print(' zone',z.GetZoneName(),[L[l] for l in z.GetLayerSet().Seq() if l in L], round(z.GetBoundingBox().GetLeft()/MM,1),round(z.GetBoundingBox().GetTop()/MM,1),round(z.GetBoundingBox().GetRight()/MM,1),round(z.GetBoundingBox().GetBottom()/MM,1))
