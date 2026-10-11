"""flatpak: route_r6o_gvcand.py BOARD X Y [R=1.15] [STEP=0.05] [IGNORE=layer:net] : candidate 0.6/0.3 GND via spots within R of (X,Y).
For each grid point reports the worst margin (clearance - required) over all four layers to non-GND copper
(tracks, vias, pads, non-GND zone fills; POWER_HI 0.4, PVDD/SPK_OUT 0.3, else 0.2; +0.25 hole-to-hole, never in a pad)
and which item limits it. Prints the 12 best points and, for the best blocked point, the blocking items."""
import sys, math, pcbnew, fnmatch, json
MM=1e6; b=pcbnew.LoadBoard(sys.argv[1]); X,Y=float(sys.argv[2]),float(sys.argv[3])
R=float(sys.argv[4]) if len(sys.argv)>4 else 1.15; ST=float(sys.argv[5]) if len(sys.argv)>5 else 0.05
L=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]; LN=['F','In1','In2','B']
def req(nc): return 0.4 if nc=='POWER_HI' else 0.3 if nc in ('PVDD','SPK_OUT') else 0.2
def V(x,y): return pcbnew.VECTOR2I(int(round(x*MM)),int(round(y*MM)))
items=[]
box=pcbnew.BOX2I(V(X-R-3,Y-R-3),V(2*R+6,2*R+6))
for t in b.GetTracks():
    if t.GetNetname()=='GND' or not t.GetBoundingBox().Intersects(box): continue
    for i,l in enumerate(L):
        if t.IsOnLayer(l): items.append((LN[i],t.GetEffectiveShape(l),req(t.GetNetClassName()),'%s %s'%('via' if t.GetClass()=='PCB_VIA' else 'trk',t.GetNetname())))
    if t.GetClass()=='PCB_VIA': items.append(('hole',t.GetEffectiveHoleShape(),0.25,'hole '+t.GetNetname()))
for f in b.GetFootprints():
    for p in f.Pads():
        if not p.GetBoundingBox().Intersects(box): continue
        nm='%s.%s %s'%(f.GetReference(),p.GetNumber(),p.GetNetname())
        for i,l in enumerate(L):
            if p.IsOnLayer(l):
                rq=-0.3 if p.GetNetname()=='GND' else req(p.GetNetClassName())  # GND pads: just never in/over the pad
                if p.GetNetname()=='GND': rq=0.0
                items.append((LN[i],p.GetEffectiveShape(l),rq,nm))
        if p.HasHole(): items.append(('hole',p.GetEffectiveHoleShape(),0.25,'hole '+nm))
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() in ('GND','') or not z.GetBoundingBox().Intersects(box): continue
    for i,l in enumerate(L):
        if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):
            items.append((LN[i],z.GetFilledPolysList(l),req(z.GetNetClassName()),'zone %s %s'%(z.GetZoneName(),z.GetNetname())))
IGN=sys.argv[6] if len(sys.argv)>6 else ''   # e.g. 'In2:/3V3_AUDIO' : ignore that net on that layer (reported separately)
def ign(ly,nm): return bool(IGN) and ly==IGN.split(':')[0] and nm.endswith(' '+IGN.split(':')[1])
def margin(x,y,ig=False):
    P=V(x,y); worst=(9,None)
    for ly,sh,rq,nm in items:
        if ign(ly,nm)!=ig: continue
        # distance from via ring (r 0.3) / hole (r 0.15) to shape
        rr=0.15 if ly=='hole' else 0.3
        lo,hi=0.0,3.0
        if sh.Collide(P,int(rr*MM)) if hasattr(sh,'Collide') else False: d=-1
        else:
            for _ in range(14):
                m=(lo+hi)/2
                if sh.Collide(P,int((rr+m)*MM)): hi=m
                else: lo=m
            d=lo
        mg=d-rq
        if mg<worst[0]: worst=(mg,ly+' '+nm)
    return worst
res=[]
n=int(R/ST)
for i in range(-n,n+1):
    for j in range(-n,n+1):
        x,y=X+i*ST,Y+j*ST
        if math.hypot(x-X,y-Y)>R: continue
        m,w=margin(x,y); res.append((m,round(x,3),round(y,3),w,margin(x,y,True) if IGN else None))
res.sort(key=lambda r:-r[0])
for r in res[:12]: print('  margin %.3f at (%.3f, %.3f) dist %.2f  limit %s'%(r[0],r[1],r[2],math.hypot(r[1]-X,r[2]-Y),r[3]), ('| ignored-set margin %.3f %s'%r[4]) if r[4] else '')
