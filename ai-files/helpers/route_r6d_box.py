"""flatpak: route_r6d_box.py BOARD X0 Y0 X1 Y1 [LAYERS=FB2] [nopads] : list tracks/vias/pads (net, coords, width) intersecting a box"""
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); x0,y0,x1,y1=map(float,sys.argv[2:6]); LS=sys.argv[6] if len(sys.argv)>6 else 'FB2'; MM=1e6
L={pcbnew.F_Cu:'F',pcbnew.B_Cu:'B',pcbnew.In1_Cu:'1',pcbnew.In2_Cu:'2'}
box=pcbnew.BOX2I(pcbnew.VECTOR2I(int(x0*MM),int(y0*MM)),pcbnew.VECTOR2I(int((x1-x0)*MM),int((y1-y0)*MM)))
rows=[]
for t in b.GetTracks():
    if not box.Intersects(t.GetBoundingBox()): continue
    n=str(t.GetNetname())
    if t.GetClass()=='PCB_VIA': rows.append((n,'via %.2f,%.2f d%.2f'%(t.GetX()/MM,t.GetY()/MM,t.GetWidth(pcbnew.F_Cu)/MM)))
    elif L.get(t.GetLayer()) in LS: rows.append((n,'trk %s %.2f,%.2f -> %.2f,%.2f w%.2f'%(L[t.GetLayer()],t.GetStart().x/MM,t.GetStart().y/MM,t.GetEnd().x/MM,t.GetEnd().y/MM,t.GetWidth()/MM)))
if 'nopads' not in sys.argv:
  for f in b.GetFootprints():
    if not box.Intersects(f.GetBoundingBox()): continue
    for p in f.Pads():
        if box.Intersects(p.GetBoundingBox()): rows.append((str(p.GetNetname()),'pad %s.%s %.2f,%.2f %.2fx%.2f%s'%(f.GetReference(),p.GetNumber(),p.GetX()/MM,p.GetY()/MM,p.GetBoundingBox().GetWidth()/MM,p.GetBoundingBox().GetHeight()/MM,' TH' if p.GetDrillSizeX() else '')))
for n,s in sorted(rows): print('%-28s %s'%(n[:28],s))
