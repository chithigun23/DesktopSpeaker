"""python3: route_r6j_trunkplan.py OBS.json HALFWIDTH [EXTRA_VIAS_JSON] : (R6j) grid A* centreline for the 3V_AO In2 trunk (181.39,77)->(188.4,54.75) around vias/In2 tracks/islands from route_r6j_in2obs.py; prints a simplified polyline"""
import json,math,heapq,sys
import numpy as np
o=json.load(open(sys.argv[1])); hw=float(sys.argv[2]); extra=json.loads(sys.argv[3]) if len(sys.argv)>3 else []
X0,Y0,X1,Y1=176,50,194,82; G=0.05
W=int((X1-X0)/G)+1; H=int((Y1-Y0)/G)+1
xs=X0+np.arange(W)*G; ys=Y0+np.arange(H)*G; XX,YY=np.meshgrid(xs,ys)
bad=np.zeros((H,W),bool)
for x,y,r,n in o['vias']+extra:
    bad|=(XX-x)**2+(YY-y)**2<(r+0.2+hw)**2
for x0,y0,x1,y1,w,n in o['trk']:
    dx,dy=x1-x0,y1-y0;L=dx*dx+dy*dy or 1e-9
    t=np.clip(((XX-x0)*dx+(YY-y0)*dy)/L,0,1); d2=(XX-x0-t*dx)**2+(YY-y0-t*dy)**2
    bad|=d2<(w+0.2+hw)**2
from matplotlib.path import Path
for poly in o['zones']:
    p=Path(poly); ins=p.contains_points(np.c_[XX.ravel(),YY.ravel()]).reshape(H,W); bad|=ins
    # distance to edges
    for i in range(len(poly)):
        x0,y0=poly[i];x1,y1=poly[(i+1)%len(poly)];dx,dy=x1-x0,y1-y0;L=dx*dx+dy*dy or 1e-9
        t=np.clip(((XX-x0)*dx+(YY-y0)*dy)/L,0,1); bad|=(XX-x0-t*dx)**2+(YY-y0-t*dy)**2<(0.2+hw)**2
def cell(x,y): return int(round((y-Y0)/G)),int(round((x-X0)/G))
s=cell(181.39,77.0); e=cell(188.4,54.75)
for c in (s,e):
    i,j=c; bad[max(i-8,0):i+9,max(j-8,0):j+9]=False
D=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
dist={(s,None):0};pq=[(0,s,None)];prev={}
def h(c): return math.hypot(c[0]-e[0],c[1]-e[1])
best=None
while pq:
    f,c,dr=heapq.heappop(pq)
    if c==e: best=(c,dr);break
    g=dist[(c,dr)]
    if f-h(c)>g+1e-9: continue
    for k,(di,dj,cst) in enumerate(D):
        n=(c[0]+di,c[1]+dj)
        if not(0<=n[0]<H and 0<=n[1]<W) or bad[n]: continue
        ng=g+cst+(0 if dr is None or dr==k else 3)
        if ng<dist.get((n,k),1e18):
            dist[(n,k)]=ng;prev[(n,k)]=(c,dr);heapq.heappush(pq,(ng+h(n),n,k))
if not best: print('NOPATH');sys.exit()
pts=[];k=best
while k in prev or k[0]==s:
    pts.append(k[0])
    if k[0]==s and k not in prev: break
    k=prev[k]
pts=pts[::-1]
P=[(X0+j*G,Y0+i*G) for i,j in pts]
# simplify: line of sight on bad
def clear(a,b):
    n=int(math.hypot(b[0]-a[0],b[1]-a[1])/G*2)+2
    for t in range(n+1):
        x=a[0]+(b[0]-a[0])*t/n;y=a[1]+(b[1]-a[1])*t/n;i,j=cell(x,y)
        if bad[i,j]: return False
    return True
out=[P[0]];i=0
while i<len(P)-1:
    j=len(P)-1
    while j>i+1 and not clear(P[i],P[j]): j-=1
    out.append(P[j]);i=j
L=sum(math.hypot(out[k+1][0]-out[k][0],out[k+1][1]-out[k][1]) for k in range(len(out)-1))
print('len %.2f'%L,[(round(x,2),round(y,2)) for x,y in out])
