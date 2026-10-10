"""flatpak: route_r6d_chk.py BOARD SPEC.json : pre-check hand spec items (tracks via track_legal, vias via place_via + BKO/In2-island) without DRC; prints failing items"""
import sys, json, math
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b=pcbnew.LoadBoard(sys.argv[1])
bko=[z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('BKO_')]
for s in json.load(open(sys.argv[2])):
    if 'via' in s:
        n=full(s['net'],b); x,y=s['via']; D=s.get('d',0.6); DR=s.get('drill',0.3)
        sig=ncls(n) not in ('GND','PVDD','POWER_HI','SPK_OUT','SWITCH','PWR_5V','PWR_3V')
        why=[]
        if sig and any(z.Outline().Collide(V(x,y),int(D/2*MM)) for z in bko): why.append('BKO')
        isl=[z.GetZoneName() for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND','',n) and z.Outline().Collide(V(x,y),int(D/2*MM))]
        if isl and ncls(n) not in ('GND',): why.append('island '+','.join(isl))
        v=place_via(b,n,x,y,D,DR,lock=False)
        if v is None: why.append('place')
        print('via',n,x,y,'OK' if not why else why)
    elif 'pts' in s:
        n=full(s['net'],b); L=s['layer']; w=s['w']; P=s['pts']
        bad=[i for i in range(len(P)-1) if not track_legal(b,n,tuple(P[i]),tuple(P[i+1]),w,L)]
        print('trk',n,L,'OK' if not bad else ['seg %d %s-%s'%(i,P[i],P[i+1]) for i in bad])
        trk(b,n,L,[tuple(p) for p in P],w,lock=False)
