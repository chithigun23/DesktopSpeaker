"""flatpak: route_r6l_splitall.py IN OUT L : copy of IN with every straight track longer than 2 L split into ~L mm collinear pieces (strict DRC oracle: rule areas then apply per piece)."""
import sys,pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); L=float(sys.argv[3]); n=0
for t in list(b.GetTracks()):
    if t.GetClass()!='PCB_TRACK': continue
    Ln=t.GetLength()/1e6
    if Ln<=2*L: continue
    k=int(Ln//L); a=t.GetStart(); e=t.GetEnd()
    pts=[pcbnew.VECTOR2I(int(a.x+(e.x-a.x)*i/k),int(a.y+(e.y-a.y)*i/k)) for i in range(k+1)]
    t.SetEnd(pts[1])
    for i in range(1,k):
        t2=pcbnew.PCB_TRACK(b); t2.SetLayer(t.GetLayer()); t2.SetWidth(t.GetWidth()); t2.SetNet(t.GetNet()); t2.SetStart(pts[i]); t2.SetEnd(pts[i+1]); b.Add(t2)
    n+=k-1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[2],b); print('split',n)
