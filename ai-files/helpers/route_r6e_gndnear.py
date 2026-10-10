"""flatpak: route_r6e_gndnear.py BOARD X Y [maxr=1.3] : legal GND via spots (0.6/0.3, place_via) within maxr of a point, nearest first, with a legal GND stub to the nearest GND copper being optional (reports whether the via lands on GND F/B pour)"""
import sys, math
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b=pcbnew.LoadBoard(sys.argv[1]); X,Y=float(sys.argv[2]),float(sys.argv[3]); maxr=float(sys.argv[4]) if len(sys.argv)>4 else 1.3
res=[]
for r10 in range(6,int(maxr*20)+1):
    r=r10/20
    for k in range(36):
        a=2*math.pi*k/36; x=X+r*math.cos(a); y=Y+r*math.sin(a)
        v=place_via(b,'GND',x,y,0.6,0.3,lock=False)
        if v is None: continue
        b.Remove(v); res.append((r,round(x,2),round(y,2)))
    if len(res)>=6: break
for q in res[:8]: print('r %.2f via (%.2f,%.2f)'%q)
print('found',len(res))
