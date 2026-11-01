# r7_bench.py BOARD.kicad_pcb [...]  : exact 0/45/90 share of length and signal length / octilinear minimum (needs the pcbparse.py s-expression helper; see r7_metrics.py for a self-contained parser). Used for the benchmark table in the Routing Rulebook.
import sys, math, collections, re
sys.path.insert(0,'/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/an')
from pcbparse import *
def load(path):
    B=parse(path); nm={}
    for n in kids(B,'net'):
        if len(n)>=3: nm[n[1]]=n[2]
    def NN(x):
        if not x or len(x)<2: return ''
        if len(x)>2: return x[2]
        return nm.get(x[1],x[1])
    segs=[]
    for s in kids(B,'segment'):
        a=kid(s,'start');b=kid(s,'end'); segs.append((f(a[1]),f(a[2]),f(b[1]),f(b[2]),f(kid(s,'width')[1]),kid(s,'layer')[1],NN(kid(s,'net'))))
    pads=collections.defaultdict(list)
    for fp in kids(B,'footprint'):
        at=kid(fp,'at'); x,y=f(at[1]),f(at[2]); rot=f(at[3]) if len(at)>3 else 0
        c,s_=math.cos(math.radians(rot)),math.sin(math.radians(rot))
        for p in kids(fp,'pad'):
            pa=kid(p,'at'); px,py=f(pa[1]),f(pa[2]); n=NN(kid(p,'net'))
            if n: pads[n].append((round(x+px*c+py*s_,2),round(y-px*s_+py*c,2)))
    return segs,pads
def octi(a,b):
    dx=abs(a[0]-b[0]);dy=abs(a[1]-b[1]); return max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy)
def mst(pts):
    pts=list(set(pts))
    if len(pts)<2: return 0
    inT={0};d=[octi(pts[0],p) for p in pts];tot=0
    while len(inT)<len(pts):
        j=min((i for i in range(len(pts)) if i not in inT),key=lambda i:d[i]);tot+=d[j];inT.add(j)
        for i in range(len(pts)): d[i]=min(d[i],octi(pts[i],pts[j]))
    return tot
def run(path):
    segs,pads=load(path)
    tot=0;ex=0;tot5=0;ex5=0
    for x1,y1,x2,y2,w,l,n in segs:
        L=math.hypot(x2-x1,y2-y1); a=math.degrees(math.atan2(y2-y1,x2-x1))%180; d=min(abs(a-v) for v in (0,45,90,135,180))
        tot+=L; 
        if d<0.6: ex+=L
        if L>=5:
            tot5+=L
            if d<0.6: ex5+=L
    maxw=collections.defaultdict(float);ln=collections.defaultdict(float)
    for x1,y1,x2,y2,w,l,n in segs: maxw[n]=max(maxw[n],w); ln[n]+=math.hypot(x2-x1,y2-y1)
    R=O=0
    for n,l in ln.items():
        if maxw[n]<=0.35 and not re.search('GND|gnd|VSS|Earth',n) and len(set(pads[n]))>=2: R+=l;O+=mst(pads[n])
    print(f'{path.split("/")[-1][:34]:34s} segs={len(segs):5d} len={tot:7.0f}mm exact-grid(all)={100*ex/max(tot,1):5.1f}% exact(>=5mm)={100*ex5/max(tot5,1):5.1f}% signal routed/octilinear-min={R/max(O,1):.2f} (n={R:.0f}/{O:.0f})')
import glob
for p in sys.argv[1:]: run(p)
