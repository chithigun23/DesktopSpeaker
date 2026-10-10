"""flatpak: route_r6j_in2obs.py BOARD X0 Y0 X1 Y1 SKIPNET OUT.json : (R6j) export vias, In2 tracks and non-GND In2 zones in a box (for route_r6j_trunkplan.py)"""
import sys,pcbnew,json
b=pcbnew.LoadBoard(sys.argv[1]);MM=1e6;x0,y0,x1,y1=map(float,sys.argv[2:6]);skip=sys.argv[6]
out={'vias':[],'trk':[],'zones':[]}
for t in b.GetTracks():
    n=str(t.GetNetname())
    if n==skip: continue
    if t.GetClass()=='PCB_VIA':
        x,y=t.GetX()/MM,t.GetY()/MM
        if x0<=x<=x1 and y0<=y<=y1: out['vias'].append([x,y,t.GetWidth(pcbnew.F_Cu)/MM/2,n])
    elif t.GetLayer()==pcbnew.In2_Cu:
        a,c=t.GetStart(),t.GetEnd()
        if min(a.x,c.x)/MM<=x1 and max(a.x,c.x)/MM>=x0 and min(a.y,c.y)/MM<=y1 and max(a.y,c.y)/MM>=y0: out['trk'].append([a.x/MM,a.y/MM,c.x/MM,c.y/MM,t.GetWidth()/MM/2,n])
for z in b.Zones():
    if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or str(z.GetNetname()) in ('GND',skip): continue
    o=z.Outline().Outline(0); out['zones'].append([[o.CPoint(i).x/MM,o.CPoint(i).y/MM] for i in range(o.PointCount())])
json.dump(out,open(sys.argv[7],'w'))
print(len(out['vias']),len(out['trk']),len(out['zones']))
