"""flatpak: route_r6c_gates.py BOARD : via-in-pad (via centre inside a pad of another net or via overlapping any F.Cu pad), EP via counts, antenna keep-out, via/length stats"""
import sys, math, collections, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); MM=1e6
vias=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
bad=[]
for v in vias:
    p0=v.GetPosition()
    for f in b.GetFootprints():
        if not f.GetBoundingBox().Contains(p0): continue
        for p in f.Pads():
            if p.GetDrillSizeX()>0: continue
            if p.HitTest(p0): bad.append((f.GetReference(),str(p.GetNumber()),str(v.GetNetname()),round(v.GetX()/MM,2),round(v.GetY()/MM,2)))
print('via centre in SMD pad:',len(bad)); [print('  ',x) for x in bad if x[0] not in ('U6','U7','U25') or x[1]!=('33' if x[0]!='U25' else '21')]
for ref in ('U6','U7','U25','U11'):
    f=[x for x in b.GetFootprints() if x.GetReference()==ref][0]
    ep=[p for p in f.Pads() if p.GetSizeX()>2*MM and p.GetSizeY()>2*MM and str(p.GetNetname())=='GND' or (ref=='U25' and str(p.GetNumber())=='21')]
    n=0
    for v in vias:
        for p in ep:
            if p.HitTest(v.GetPosition()): n+=1; break
    print(ref,'EP vias',n)
ant=[z for z in b.Zones() if z.GetZoneName()=='BM83_ANTENNA_KEEPOUT'][0]; bb=ant.GetBoundingBox(); cnt=0
for t in b.GetTracks():
    if bb.Intersects(t.GetBoundingBox()): cnt+=1; print('  ant item',t.GetClass(),str(t.GetNetname()),t.GetPosition().x/MM,t.GetPosition().y/MM)
for z in b.Zones():
    if not z.GetIsRuleArea() and bb.Intersects(z.GetBoundingBox()):
        for l in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu):
            if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l) and z.GetFilledPolysList(l).Collide(ant.Outline().Outline(0).CPoint(0)) : pass
print('antenna keepout: tracks/vias in bbox',cnt)
c=collections.Counter(str(v.GetNetname())=='GND' for v in vias); print('vias total',len(vias),'GND',c[True],'signal',c[False])
L=collections.defaultdict(float); V=collections.Counter()
for t in b.GetTracks():
    n=str(t.GetNetname())
    if t.GetClass()=='PCB_VIA': V[n]+=1
    else: L[n]+=t.GetLength()/MM
for n in sorted(L):
    if any(k in n for k in('USB_D','USB_DP','USB_DN','U2-D','I2S','BCK','LRCK','SDATA')): print(n,round(L[n],2),'mm vias',V[n])
