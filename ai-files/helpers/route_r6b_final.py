"""flatpak: route_r6b_final.py IN OUT : remove dangling signal vias, widen sub-floor VMID_HP stub to 0.25, refill."""
import sys
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import refill
MM=1000000
b=pcbnew.LoadBoard(sys.argv[1])
dang=[(155.1,123.35),(184.95,61.35),(170.5,61.9),(182.6,61.85),(132.85,46.6)]
allt=list(b.GetTracks())
for t in allt:
    if t.GetClass()=='PCB_TRACK' and str(t.GetNetname()).endswith('VMID_HP') and t.GetWidth()<0.25*MM and abs(t.GetStart().x/MM-163.35)<1 and abs(t.GetStart().y/MM-78.8)<1: t.SetWidth(int(0.25*MM)); print('widen')
rm=[t for t in allt if t.GetClass()=='PCB_VIA' and any(abs(t.GetX()/MM-x)<0.02 and abs(t.GetY()/MM-y)<0.02 for x,y in dang)]
for t in rm: b.Remove(t); print('rm via')
refill(b); pcbnew.SaveBoard(sys.argv[2],b)
