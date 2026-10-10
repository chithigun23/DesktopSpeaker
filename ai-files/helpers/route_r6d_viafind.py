"""flatpak: route_r6d_viafind.py BOARD REF.PAD NET [maxr=2.5] [d=0.6] : legal via spots near a pad for NET (place_via + stub track_legal + not in BKO_* (signal) + not inside a foreign non-GND In2 island outline)"""
import sys, math
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b=pcbnew.LoadBoard(sys.argv[1]); ref,num=sys.argv[2].split('.'); n=full(sys.argv[3],b)
maxr=float(sys.argv[4]) if len(sys.argv)>4 else 2.5; D=float(sys.argv[5]) if len(sys.argv)>5 else 0.6; DR=0.3 if D>=0.6 else 0.2
p=pad(b,ref,num); px,py=p.GetX()/MM,p.GetY()/MM
bko=[z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('BKO_')]
isl=[z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND','',n)]
sig=ncls(n) not in ('GND','PVDD','POWER_HI','SPK_OUT','SWITCH','PWR_5V','PWR_3V')
res=[]
for r10 in range(4,int(maxr*10)+1):
    r=r10/10
    for k in range(48):
        a=2*math.pi*k/48; x=px+r*math.cos(a); y=py+r*math.sin(a)
        if sig and any(z.Outline().Collide(V(x,y),int(D/2*MM)) for z in bko): continue
        if any(z.Outline().Collide(V(x,y),int(D/2*MM)) for z in isl): continue
        v=place_via(b,n,x,y,D,DR,lock=False)
        if v is None: continue
        b.Remove(v)
        for w in (0.25,0.2):
            if track_legal(b,n,(px,py),(x,y),w):
                res.append((r,round(x,2),round(y,2),w)); break
res.sort()
for q in res[:10]: print('r %.1f via (%.2f,%.2f) stub w%.2f'%q)
print('found',len(res))
