"""flatpak: route_r6c_setw.py IN OUT W NET x0 y0 x1 y1 : set width W (mm) of tracks of NET (or '*') fully inside box"""
import sys, pcbnew
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import refill
MM=1e6; b=pcbnew.LoadBoard(sys.argv[1]); W=float(sys.argv[3]); N=sys.argv[4]; x0,y0,x1,y1=map(float,sys.argv[5:9]); k=0
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA' or (N!='*' and str(t.GetNetname())!=N): continue
    if all(x0<=q.x/MM<=x1 and y0<=q.y/MM<=y1 for q in (t.GetStart(),t.GetEnd())): t.SetWidth(int(W*MM)); k+=1
print('set',k); refill(b); pcbnew.SaveBoard(sys.argv[2],b)
