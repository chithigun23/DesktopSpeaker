# Resistive solver for one net: rasterises copper per layer, vias/PTH barrels as resistors, fixed-potential source/sink pad sets.
# Prints path resistance, drop/loss at I0, per-layer loss, max sheet current (A/mm) and hotspots; writes map_TAG_LAYER.png
# (grey < 0.5 A/mm, blue >= 0.5, green >= 1, yellow >= 2, red >= 4, magenta >= 8 A/mm at I0).
# Usage: python (with numpy + shapely) copper_path_solve.py GEO.json NET "REF:PAD,..." "REF:PAD,..." x0,y0,x1,y1 cell_mm I0_A temp_C [TAG]
# Assumptions: copper thickness from the board stackup (35 / 15.2 / 15.2 / 35 um), barrel plating 20 um, rho(Cu) 1.72e-8 at 20 C.
# Written 2026-11-02 for reports/charge-policy-2026-11-02.md.
# Resistive solver for one net: rasterise copper per layer, vias/PTH as barrels, Dirichlet source/sink pad sets.
import json, sys, numpy as np, shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
D=json.load(open(sys.argv[1])); net=sys.argv[2]
src=[tuple(s.split(":")) for s in sys.argv[3].split(",")]   # ref:pad
snk=[tuple(s.split(":")) for s in sys.argv[4].split(",")]
bbox=[float(v) for v in sys.argv[5].split(",")]   # x0,y0,x1,y1
h=float(sys.argv[6]); I0=float(sys.argv[7]); TC=float(sys.argv[8]) if len(sys.argv)>8 else 20.0
rho=1.72e-8*(1+0.00393*(TC-20))  # ohm m
TH={"F.Cu":35e-6,"In1.Cu":15.2e-6,"In2.Cu":15.2e-6,"B.Cu":35e-6}
Z={"F.Cu":0.0,"In1.Cu":0.2454,"In2.Cu":1.3256,"B.Cu":1.571}  # mm, approx copper mid-plane depth
TPLATE=20e-6   # ASSUMPTION barrel plating thickness
d=D[net]; LAY=["F.Cu","In1.Cu","In2.Cu","B.Cu"]
def mk(p):
    ring,holes=p
    try: return Polygon(ring,holes).buffer(0)
    except Exception: return None
geo={L:[] for L in LAY}
for z in d["zones"]:
    for p in z["polys"]:
        g=mk(p); 
        if g: geo[z["layer"]].append(g)
for t in d["tracks"]:
    for p in t["polys"]:
        g=mk(p)
        if g and t["layer"] in geo: geo[t["layer"]].append(g)
padgeo={}
for p in d["pads"]:
    for q in p["polys"]:
        g=mk(q)
        if g: geo[p["layer"]].append(g); padgeo.setdefault((p["ref"],p["num"]),[]).append((p["layer"],g))
x0,y0,x1,y1=bbox
nx=int((x1-x0)/h); ny=int((y1-y0)/h)
xs=x0+(np.arange(nx)+0.5)*h; ys=y0+(np.arange(ny)+0.5)*h
XX,YY=np.meshgrid(xs,ys)
mask={}
for L in LAY:
    if not geo[L]: mask[L]=np.zeros((ny,nx),bool); continue
    u=unary_union(geo[L]); shapely.prepare(u)
    mask[L]=shapely.contains_xy(u,XX,YY)
idx={}; n=0
for L in LAY:
    a=-np.ones((ny,nx),int); m=mask[L]; c=int(m.sum()); a[m]=np.arange(n,n+c); n+=c; idx[L]=a
ei=[];ej=[];eg=[]; elay=[]
for li,L in enumerate(LAY):
    a=idx[L]; gs=TH[L]/rho  # siemens per square
    for (A,Bb) in [(a[:,:-1],a[:,1:]),(a[:-1,:],a[1:,:])]:
        m=(A>=0)&(Bb>=0); ei.append(A[m]); ej.append(Bb[m]); eg.append(np.full(m.sum(),gs)); elay.append(np.full(m.sum(),li))
# barrels: vias + PTH pads
barrels=[(v["x"],v["y"],v["drill"],v["layers"]) for v in d["vias"]]
seen=set()
for p in d["pads"]:
    if p["drill"]>0 and (p["ref"],p["num"]) not in seen:
        seen.add((p["ref"],p["num"])); barrels.append((p["x"],p["y"],p["drill"],LAY))
nb=0
for (x,y,dr,ls) in barrels:
    ix=int((x-x0)/h); iy=int((y-y0)/h)
    if not(0<=ix<nx and 0<=iy<ny): continue
    # find copper cell near centre on each layer (search small window, drill hole itself may be void)
    cells=[]
    r=max(1,int(np.ceil((dr/2+0.15)/h)))
    for L in LAY:
        if L not in ls: continue
        w=idx[L][max(0,iy-r):iy+r+1,max(0,ix-r):ix+r+1]
        ids=w[w>=0]
        if len(ids): cells.append((L,ids))
    for k in range(len(cells)-1):
        (La,ia),(Lb,ib)=cells[k],cells[k+1]
        Rb=rho*abs(Z[Lb]-Z[La])*1e-3/(np.pi*dr*1e-3*TPLATE)
        # distribute barrel conductance over ring cells (star from first cell of each set)
        ga=1/Rb
        ei.append(np.array([ia[len(ia)//2]])); ej.append(np.array([ib[len(ib)//2]])); eg.append(np.array([ga])); elay.append(np.array([-1]))
        nb+=1
    # tie ring cells on each layer to their centre cell (annulus, near-zero resistance)
    for (L,ids) in cells:
        c=ids[len(ids)//2]; o=ids[ids!=c]
        ei.append(o); ej.append(np.full(len(o),c)); eg.append(np.full(len(o),1e4)); elay.append(np.full(len(o),-2))
ei=np.concatenate(ei); ej=np.concatenate(ej); eg=np.concatenate(eg); elay=np.concatenate(elay)
def cellset(lst):
    s=[]
    for (r,num) in lst:
        for (L,g) in padgeo.get((r,num),[]):
            shapely.prepare(g); m=shapely.contains_xy(g,XX,YY)&(idx[L]>=0); s.append(idx[L][m])
    return np.unique(np.concatenate(s)) if s else np.array([],int)
S=cellset(src); K=cellset(snk)
print(net,"cells",n,"barrels",nb,"src cells",len(S),"snk cells",len(K))
V=np.zeros(n); fixed=np.zeros(n,bool); fixed[S]=True; fixed[K]=True; V[S]=1.0
free=~fixed
diag=np.zeros(n); np.add.at(diag,ei,eg); np.add.at(diag,ej,eg)
def Aop(x):
    y=diag*x; np.add.at(y,ei,-eg*x[ej]); np.add.at(y,ej,-eg*x[ei]); return y
# rhs = -A*V_fixed restricted to free
b=-Aop(V); b[fixed]=0
x=np.zeros(n); r=b.copy(); r[fixed]=0; Minv=np.where(free,1/np.maximum(diag,1e-30),0); z=Minv*r; p=z.copy(); rz=r@z
for it in range(20000):
    Ap=Aop(p); Ap[fixed]=0
    al=rz/(p@Ap); x+=al*p; r-=al*Ap
    if np.sqrt(r@r)<1e-10*np.sqrt(b@b): break
    z=Minv*r; rzn=r@z; p=z+(rzn/rz)*p; rz=rzn
V=V+x
cur=eg*(V[ei]-V[ej])
Iin=0.0
inS=np.zeros(n,bool); inS[S]=True
Iin=cur[inS[ei]&~inS[ej]].sum()-cur[inS[ej]&~inS[ei]].sum()
R=1/Iin
print("iters",it,"R_total = %.3f mOhm  at %.0f C"%(R*1e3,TC))
sc=I0*R   # volts per unit V
print("at I=%.1f A: drop %.1f mV, loss %.1f mW"%(I0,I0*R*1e3,I0*I0*R*1e3))
# sheet current density per cell (A/mm) on each layer
for li,L in enumerate(LAY):
    a=idx[L]; 
    if (a>=0).sum()==0: continue
    Vg=np.full((ny,nx),np.nan); m=a>=0; Vg[m]=V[a[m]]*sc
    gs=TH[L]/rho
    jx=np.zeros((ny,nx)); jy=np.zeros((ny,nx))
    dvx=(Vg[:,:-1]-Vg[:,1:]); dvx=np.nan_to_num(dvx); jx[:,:-1]+=dvx*gs/h/2; jx[:,1:]+=dvx*gs/h/2
    dvy=(Vg[:-1,:]-Vg[1:,:]); dvy=np.nan_to_num(dvy); jy[:-1,:]+=dvy*gs/h/2; jy[1:,:]+=dvy*gs/h/2
    K_=np.hypot(jx,jy); K_[~m]=0
    # layer current share: loss on layer
    sel=elay==li; P=(cur[sel]*sc)**2/eg[sel] if False else (eg[sel]*((V[ei[sel]]-V[ej[sel]])*sc)**2)
    print(" %s: copper %.1f mm2 in bbox, loss %.1f mW, max sheet current %.2f A/mm (equiv. width at I0 %.2f mm)"%(L,m.sum()*h*h,P.sum()*1e3,K_.max(),I0/max(K_.max(),1e-9)))
    # hot spots: top cells, clustered 0.5 mm
    order=np.argsort(K_.ravel())[::-1]; picked=[]
    for o in order[:20000]:
        yy,xx=divmod(o,nx); X=xs[xx]; Y=ys[yy]
        if K_.ravel()[o]<0.3*K_.max(): break
        if all((X-px)**2+(Y-py)**2>1.0 for px,py,_ in picked): picked.append((X,Y,K_.ravel()[o]))
        if len(picked)>=6: break
    for X,Y,k in picked: print("    hotspot (%.2f, %.2f) %.2f A/mm -> equiv width %.2f mm"%(X,Y,k,I0/k))
sel=elay==-1
Pv=(eg[sel]*((V[ei[sel]]-V[ej[sel]])*sc)**2); Iv=np.abs(eg[sel]*(V[ei[sel]]-V[ej[sel]])*sc)
print(" barrels: loss %.1f mW, max barrel-segment current %.2f A, n segments carrying >0.5 A: %d"%(Pv.sum()*1e3,Iv.max() if len(Iv) else 0,(Iv>0.5).sum()))
np.save("V_%s.npy"%net.split("/")[-1],V)
# ---- PNG heat maps (sheet current density, A/mm, at I0) ----
import zlib, struct
def png(fn,rgb):
    h_,w_,_=rgb.shape; raw=b"".join(b"\x00"+rgb[i].astype(np.uint8).tobytes() for i in range(h_))
    def ch(t,d): c=struct.pack(">I",len(d))+t+d; return c+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    open(fn,"wb").write(b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",w_,h_,8,2,0,0,0))+ch(b"IDAT",zlib.compress(raw,9))+ch(b"IEND",b""))
tag=sys.argv[9] if len(sys.argv)>9 else net.split("/")[-1]
for li,L in enumerate(LAY):
    a=idx[L]; m=a>=0
    if m.sum()==0: continue
    Vg=np.full((ny,nx),np.nan); Vg[m]=V[a[m]]*sc; gs=TH[L]/rho
    jx=np.zeros((ny,nx)); jy=np.zeros((ny,nx))
    dvx=np.nan_to_num(Vg[:,:-1]-Vg[:,1:]); jx[:,:-1]+=dvx*gs/h/2; jx[:,1:]+=dvx*gs/h/2
    dvy=np.nan_to_num(Vg[:-1,:]-Vg[1:,:]); jy[:-1,:]+=dvy*gs/h/2; jy[1:,:]+=dvy*gs/h/2
    Kk=np.hypot(jx,jy); Kk[~m]=0
    # colour: grey copper, then blue(0.5 A/mm)->green(1)->yellow(2)->red(4+) A/mm
    rgb=np.zeros((ny,nx,3)); rgb[m]=(90,90,90)
    lv=[(0.5,(0,90,255)),(1.0,(0,200,0)),(2.0,(255,220,0)),(4.0,(255,0,0)),(8.0,(255,0,255))]
    for th,c in lv: rgb[m&(Kk>=th)]=c
    s=max(1,int(round(0.1/h)))  # keep ~0.1 mm per px at most
    png("map_%s_%s.png"%(tag,L.replace(".","")),rgb[::1,::1])
