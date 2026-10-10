import sys, math; sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b=pcbnew.LoadBoard(sys.argv[1]); n='/5V_LOGIC'
v=[t for t in b.Tracks() if t.GetClass()=='PCB_VIA' and str(t.GetNetname())==n and abs(t.GetX()/MM-94.35)<0.01 and abs(t.GetY()/MM-102.25)<0.01][0]
bt=[t for t in b.Tracks() if t.GetClass()!='PCB_VIA' and str(t.GetNetname())==n and t.GetLayer()==pcbnew.B_Cu and t.GetEffectiveShape().Collide(v.GetEffectiveShape(pcbnew.B_Cu),0)]
far=[(t.GetEnd() if math.hypot(t.GetStart().x-v.GetX(),t.GetStart().y-v.GetY())<1000 else t.GetStart()) for t in bt]
b.Remove(v); [b.Remove(t) for t in bt]
pad=(94.9075,104.97)  # C141.1 centre
done=False
for r in (0.8,1.0,1.2,1.5,1.8,2.2):
    for k in range(32):
        a=2*math.pi*k/32; Q=(pad[0]+r*math.cos(a), pad[1]+r*math.sin(a))
        if not track_legal(b,n,pad,Q,0.5,'F'): continue
        if not all(track_legal(b,n,(e.x/MM,e.y/MM),Q,0.4,'B') for e in far): continue
        nv=place_via(b,n,Q[0],Q[1])
        if nv is None: continue
        trk(b,n,'F',[pad,Q],0.5); [trk(b,n,'B',[(e.x/MM,e.y/MM),Q],0.4) for e in far]; print('moved to',Q); done=True; break
    if done: break
if not done: print('FAILED')
refill(b); pcbnew.SaveBoard(sys.argv[2],b)
