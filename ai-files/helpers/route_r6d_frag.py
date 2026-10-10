"""flatpak: route_r6d_frag.py BOARD NET [x0 y0 x1 y1] : fragments of NET (pads, #items, has zone) - only fragments with a pad inside the box; largest fragment marked MAIN"""
import sys
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_p2_core import comps_of
class C: pass
c=C(); c.b=pcbnew.LoadBoard(sys.argv[1]); n=sys.argv[2]
box=list(map(float,sys.argv[3:7])) if len(sys.argv)>6 else None
cs=comps_of(c,n); big=max(range(len(cs)),key=lambda i:len(cs[i]))
MM=1e6
for i,g in enumerate(cs):
    pads=[x[1] for x in g if x[0]=='pad']
    if box and not any(box[0]<=p.GetX()/MM<=box[2] and box[1]<=p.GetY()/MM<=box[3] for p in pads): continue
    print('MAIN' if i==big else 'frag', len(g), 'zones' if any(x[0]=='zone' for x in g) else '', [ '%s.%s(%.2f,%.2f)'%(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetX()/MM,p.GetY()/MM) for p in pads][:14])
