import sys, math; sys.path.insert(0,'scripts')
from r10lib import *
B=Board('B9-H0.geo.json','r9.json','B9-H0.nets.txt','base.kicad_dru')
for r,v in {'R206':(149.095,91.9,-90),'R207':(147.745,91.9,-90),'R208':(146.395,91.9,-90),'TP13':(147,101.6,0),'TP14':(147,95.4,0)}.items(): B.pose[r]=v
segs=[((151.55,92.1),(151.95,92.1)),((151.1,92.55),(151.55,92.1))]; via=(151.95,92.1)
x0,y0,r0=B.pose0['R211']; res=[]
allv=[v for v in B.G['vias'] if abs(v['x']-via[0])>1e-3 or abs(v['y']-via[1])>1e-3]
for i in range(-30,31):
  for j in range(-10,41):
    dx,dy=i*0.05,j*0.05
    B.pose['R211']=(x0+dx,y0+dy,r0)
    ok,why=B.legal('R211')
    if not ok: continue
    nv=(via[0]+dx,via[1]+dy)
    po=B.all_pad_obs(nv,3)
    bad=False
    for g,net,cls,typ,name in po:
        if name.startswith('R211'): continue
        if g.distance(Point(nv).buffer(0.3))<0.5-1e-6 and net!='GND': bad=True;break
        for a,b in segs:
            s=LineString([(a[0]+dx,a[1]+dy),(b[0]+dx,b[1]+dy)]).buffer(0.15)
            if net!='GND' and g.distance(s)<0.2: bad=True;break
        if bad: break
    if bad: continue
    for v in allv:
        if math.hypot(v['x']-nv[0],v['y']-nv[1])<0.6+0.3: bad=True;break
    for t in B.G['tracks']:
        if t['net']=='GND' or t['layer'] not in ('F.Cu','B.Cu','In1.Cu','In2.Cu'): continue
        d=LineString([(t['x1'],t['y1']),(t['x2'],t['y2'])]).distance(Point(nv))-t['w']/2-0.3
        if d<0.25: bad=True;break
    if bad: continue
    if not B.legal('R206')[0]: continue
    res.append((math.hypot(dx,dy),dx,dy))
res.sort(); print(res[:10])
