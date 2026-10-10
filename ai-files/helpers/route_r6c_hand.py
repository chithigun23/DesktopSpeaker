"""flatpak: route_r6c_hand.py IN OUT SPEC.json : add explicit tracks/vias.
SPEC = list of {"net":N,"layer":"F|B|2","w":0.2,"pts":[[x,y],..]}  or {"net":N,"via":[x,y],"d":0.6,"drill":0.3}  or {"rm":[x,y]} (remove track/via items with an end/centre within 0.05 mm of x,y) """
import sys, json
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import trk, via, refill, full
MM=1e6
b=pcbnew.LoadBoard(sys.argv[1])
for s in json.load(open(sys.argv[3])):
    if 'rm' in s:
        x,y=s['rm']; r=[t for t in b.GetTracks() if (t.GetClass()=='PCB_VIA' and abs(t.GetX()/MM-x)<.05 and abs(t.GetY()/MM-y)<.05) or (t.GetClass()!='PCB_VIA' and any(abs(q.x/MM-x)<.05 and abs(q.y/MM-y)<.05 for q in (t.GetStart(),t.GetEnd())))]
        for t in r: b.RemoveNative(t)
        print('rm',len(r),s['rm'])
    elif 'rmnet' in s:
        r=[t for t in b.GetTracks() if str(t.GetNetname())==s['rmnet']]
        for t in r: b.RemoveNative(t)
        print('rmnet',len(r))
    elif 'via' in s: via(b,s['net'],s['via'][0],s['via'][1],s.get('d',0.6),s.get('drill',0.3),lock=False)
    else: trk(b,s['net'],s['layer'],[tuple(p) for p in s['pts']],s['w'],lock=False)
refill(b); pcbnew.SaveBoard(sys.argv[2],b)
