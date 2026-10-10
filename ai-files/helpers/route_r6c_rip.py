"""flatpak: route_r6c_rip.py IN OUT : R6c step 0 - unlock all; SW100 pad 1/3 shortened (0.9x1.7, centre y -0.05) to clear the NPTH; rip local R6a power copper at U24/Y200 and U2:
 - all tracks of Net-(U24-AVDD), Net-(U2-VCCP1I), Net-(U2-VCCP2I), Net-(U2-VCCCI)
 - 3V3_AUDIO: F.Cu tracks inside x139.5-151.5 / y72.5-86, via (150.0,81.25), In2 tracks 152.85,77.3->150.15,81.0 and 150.6,81.85->150.0,81.25"""
import sys, pcbnew
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import refill
MM=1e6
b=pcbnew.LoadBoard(sys.argv[1])
for t in b.GetTracks(): t.SetLocked(False)
for z in b.Zones(): z.SetLocked(False)
for f in b.GetFootprints():
    if f.GetReference()=='SW100':
        for p in f.Pads():
            if str(p.GetNumber())=='1':
                p.SetSize(pcbnew.VECTOR2I(int(0.9*MM),int(1.7*MM))); p.SetY(p.GetY()-int(0.05*MM)); print('SW100 pad1 fixed',p.GetX()/MM,p.GetY()/MM)
rm=[]
def inbox(t,x0,x1,y0,y1):
    return all(x0<=q.x/MM<=x1 and y0<=q.y/MM<=y1 for q in (t.GetStart(),t.GetEnd()))
for t in b.GetTracks():
    n=str(t.GetNetname()); v=t.GetClass()=='PCB_VIA'
    if n in ('Net-(U24-AVDD)','Net-(U2-VCCP1I)','Net-(U2-VCCP2I)','Net-(U2-VCCCI)'): rm.append(t)
    elif n=='/3V3_AUDIO':
        if v:
            if abs(t.GetX()/MM-150.0)<.02 and abs(t.GetY()/MM-81.25)<.02: rm.append(t)
        elif t.GetLayer()==pcbnew.F_Cu and inbox(t,139.5,151.5,72.5,86.0): rm.append(t)
        elif t.GetLayer()==pcbnew.In2_Cu and (inbox(t,150.0,153.0,77.0,81.1) or inbox(t,149.9,150.7,81.2,81.9)): rm.append(t)
print('removing',len(rm))
for t in rm: b.Remove(t)
refill(b); pcbnew.SaveBoard(sys.argv[2],b)
