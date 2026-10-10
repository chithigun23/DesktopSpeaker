"""flatpak: route_r6d_gndfind.py BOARD REF.PAD [NET=GND] [maxr=2.0] : legal via spots near a pad (via legal by route_r6a_lib.place_via, stub legal by track_legal), nearest first"""
import sys, math
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b=pcbnew.LoadBoard(sys.argv[1]); ref,num=sys.argv[2].split('.')
n=sys.argv[3] if len(sys.argv)>3 else 'GND'; maxr=float(sys.argv[4]) if len(sys.argv)>4 else 2.0
p=pad(b,ref,num); px,py=p.GetX()/MM,p.GetY()/MM
hw=p.GetBoundingBox().GetWidth()/MM/2; hh=p.GetBoundingBox().GetHeight()/MM/2
res=[]
for r10 in range(5, int(maxr*10)+1):
    r=r10/10
    for k in range(32):
        a=2*math.pi*k/32; x=px+(hw+r)*math.cos(a); y=py+(hh+r)*math.sin(a)
        for d,dr in ((0.6,0.3),):
            v=place_via(b,n,x,y,d,dr,lock=False)
            if v is None: continue
            b.Remove(v)
            # stub from pad edge point toward via
            for w in (0.3,0.25,0.2):
                if track_legal(b,n,(px,py),(x,y),w):
                    res.append((math.hypot(x-px,y-py),round(x,2),round(y,2),d,w)); break
            break
res.sort()
for r in res[:12]: print('dist %.2f via (%.2f,%.2f) d%.1f stub w%.2f'%r)
print('found',len(res))
