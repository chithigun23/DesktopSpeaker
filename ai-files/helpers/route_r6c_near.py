"""flatpak: route_r6c_near.py BOARD X Y R : pads, tracks, vias within R mm of x,y"""
import sys, pcbnew, math
b=pcbnew.LoadBoard(sys.argv[1]); X,Y,R=map(float,sys.argv[2:5]); MM=1e6
L={pcbnew.F_Cu:'F',pcbnew.B_Cu:'B',pcbnew.In1_Cu:'1',pcbnew.In2_Cu:'2'}
for f in b.GetFootprints():
    for p in f.Pads():
        if math.hypot(p.GetX()/MM-X,p.GetY()/MM-Y)<R: print('pad',f.GetReference(),p.GetNumber(),round(p.GetX()/MM,2),round(p.GetY()/MM,2),'%.2fx%.2f'%(p.GetSizeX()/MM,p.GetSizeY()/MM),str(p.GetNetname()), 'hole %.2f'%(p.GetDrillSizeX()/MM) if p.GetDrillSizeX() else '')
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        if math.hypot(t.GetX()/MM-X,t.GetY()/MM-Y)<R: print('via',round(t.GetX()/MM,2),round(t.GetY()/MM,2),str(t.GetNetname()))
    else:
        s,e=t.GetStart(),t.GetEnd()
        if min(math.hypot(q.x/MM-X,q.y/MM-Y) for q in (s,e))<R: print('trk',L[t.GetLayer()],round(s.x/MM,2),round(s.y/MM,2),round(e.x/MM,2),round(e.y/MM,2),'w%.2f'%(t.GetWidth()/MM),str(t.GetNetname()))
