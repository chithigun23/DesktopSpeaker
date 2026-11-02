"""Headless renders (FreeCAD tessellation + numpy/matplotlib painter's algorithm).
Run: freecadcmd ai-files/cad/render_cad.py  -> renders/*.png"""
import json, os, math, Part, FreeCAD as App
from FreeCAD import Vector as V
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
CAD=os.environ.get('CAD_OUT','/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v13/').rstrip('/')+'/'; W=CAD+'work/'; OUT=CAD+'renders/'; os.makedirs(OUT,exist_ok=True)
m=json.load(open(W+'meta.json')); P=m['params']
OBJ=[(o,Part.read(W+'brep/'+o['file'])) for o in m['objs']]
TOL=0.35
_tess={}
MAXE=9.0
def refine(vs,tr):
    """split long triangle edges so painter's sorting stays valid for big plates"""
    T=vs[tr]
    for _ in range(12):
        e=np.stack([np.linalg.norm(T[:,1]-T[:,0],axis=1),np.linalg.norm(T[:,2]-T[:,1],axis=1),np.linalg.norm(T[:,0]-T[:,2],axis=1)],1)
        big=e.max(1)>MAXE
        if not big.any(): break
        keep=T[~big]; B=T[big]; eb=e[big]; k=eb.argmax(1)
        a=B[np.arange(len(B)),k]; b=B[np.arange(len(B)),(k+1)%3]; c=B[np.arange(len(B)),(k+2)%3]
        mid=(a+b)/2
        T=np.concatenate([keep,np.stack([a,mid,c],1),np.stack([mid,b,c],1)])
    return T.reshape(-1,3),np.arange(len(T)*3).reshape(-1,3)
def tess(name,shape,key=''):
    k=(name,key)
    if k not in _tess:
        v,f=shape.tessellate(TOL)
        if not f: _tess[k]=(np.zeros((0,3)),np.zeros((0,3),int))
        else:
            _tess[k]=refine(np.array([[p.x,p.y,p.z] for p in v]),np.array(f,dtype=int).reshape(-1,3))
    return _tess[k]
def render(items,az,el,fn,title,section=None,size=(1700,1150),lines=None):
    c=np.array([math.sin(math.radians(az))*math.cos(math.radians(el)),-math.cos(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(el))])
    r=np.cross([0,0,1.0],c)
    if np.linalg.norm(r)<1e-6: r=np.array([1.0,0,0])
    r/=np.linalg.norm(r); u=np.cross(c,r)
    Ld=np.array([0.35,-0.55,0.75]); Ld=Ld[0]*r+Ld[1]*(-c)*0+Ld[2]*u+0.5*c; Ld/=np.linalg.norm(Ld)
    polys=[];cols=[];dep=[]
    for (name,color,verts,tris,off) in items:
        if len(tris)==0: continue
        vv=verts+np.array(off)
        t3=vv[tris]
        n=np.cross(t3[:,1]-t3[:,0],t3[:,2]-t3[:,0]); ln=np.linalg.norm(n,axis=1); ln[ln==0]=1; n/=ln[:,None]
        sgn=np.sign(n@c); sgn[sgn==0]=1; n*=sgn[:,None]
        sh=0.38+0.62*np.clip(n@Ld,0,1)
        base=np.array(color)
        fc=np.clip(base[None,:]*sh[:,None],0,1)
        if section:
            ax_i,val=section
            onp=np.all(np.abs(t3[:,:,ax_i]-val)<1e-3,axis=1)
            fc[onp]=np.array([0.85,0.25,0.2])*(0.8+0.2*sh[onp,None])
        sc=np.stack([t3@r,t3@u],axis=2)
        polys.append(sc); cols.append(fc); dep.append((t3.mean(axis=1))@c)
    polys=np.concatenate(polys);cols=np.concatenate(cols);dep=np.concatenate(dep)
    o=np.argsort(dep)
    fig=plt.figure(figsize=(size[0]/100,size[1]/100),dpi=100)
    ax=fig.add_axes([0,0,1,1]);ax.set_aspect('equal');ax.axis('off')
    ax.add_collection(PolyCollection(polys[o],facecolors=cols[o],edgecolors='none',linewidths=0,antialiaseds=False))
    mn=polys.reshape(-1,2).min(0);mx=polys.reshape(-1,2).max(0);pad=0.04*(mx-mn).max()
    ax.set_xlim(mn[0]-pad,mx[0]+pad);ax.set_ylim(mn[1]-pad-8,mx[1]+pad+10)
    ax.text(0.01,0.985,title,transform=ax.transAxes,va='top',fontsize=13,color='#222')
    fig.savefig(OUT+fn,dpi=100,facecolor='white');plt.close(fig)
    print('wrote',fn,len(polys),'tris')
def base_items(exclude=(),offsets=None,fn_filter=None):
    it=[]
    for o,s in OBJ:
        if o['name'] in exclude: continue
        if fn_filter and not fn_filter(o): continue
        v,f=tess(o['name'],s)
        it.append((o['name'],o['color'],v,f,(offsets or (lambda o:(0,0,0)))(o)))
    return it
H=P['H'];D=P['D']
# assembled
render(base_items(),-35,25,'assembled_front_right.png','DesktopSpeaker internal CAD - assembled, front/right/top view (grille on front, feet below)')
render(base_items(),145,22,'assembled_rear_left.png','Assembled, rear/left view: USB-C, two 3.5 mm jacks, tact button and rocker in the rear lid')
render(base_items(),-30,-35,'assembled_underside.png','Assembled, underside: woofer grille (dia %g), four outside woofer insert bosses (%.1f mm) and four 15 mm feet' % (P['w_grille_d'], m['woofer_ring']['boss_below_floor']))
# open views: remove top wall region + lid via sections (keep z<=93 handled by cutting)
def cutitems(keep,axis,val,exclude=(),filt=None):
    """keep half-space: axis index, 'le' keeps coord<=val"""
    box_dims=[1000.0,1000.0,1000.0]; org=[-500.0,-500.0,-500.0]
    box_dims[axis]=val+500.0
    hb=Part.makeBox(*box_dims,V(*org))
    it=[]
    for o,s in OBJ:
        if o['name'] in exclude: continue
        if filt and not filt(o): continue
        bb=s.BoundBox
        lo=[bb.XMin,bb.YMin,bb.ZMin][axis]; hi=[bb.XMax,bb.YMax,bb.ZMax][axis]
        if lo>=val: continue
        if hi<=val:
            v,f=tess(o['name'],s)
        else:
            try: sh=s.common(hb)
            except Exception: continue
            if sh.isNull() or not sh.Solids and not sh.Faces: continue
            v,f=tess(o['name'],sh,'cut%d_%s'%(axis,val))
        it.append((o['name'],o['color'],v,f,(0,0,0)))
    return it
# ---- v13p4 battery study views (render_cad.py helpers above, unchanged)
ex_open=('Lid_rear','SW101_rocker_D20_standin','SW101_rocker_GRB112B802BR1','Gasket_lid_foam_3mm')
VAR=os.path.basename(CAD.rstrip('/'))
SX=float(os.environ.get('SEC_X','0'))
render(cutitems('le',2,15.0,exclude=ex_open),0,90,'batt_section_z15_top.png','%s: section z = 15 (cell axis height), view from above; front baffle at the bottom, woofer-chamber partition above the pack'%VAR,section=(2,15.0))
render(cutitems('le',0,SX),90,0,'batt_section_x%g_side.png'%SX,'%s: section x = %g, view from +X; front baffle at left, partition and woofer chamber at right, PCB above'%(VAR,SX),section=(0,SX))
render(cutitems('le',1,40.0,exclude=ex_open),180,0,'batt_section_y40_front.png','%s: section y = 40 (through the drivers and the pack), viewed from the rear (+X to the left)'%VAR,section=(1,40.0))
render(cutitems('le',1,72.0,exclude=ex_open),180,0,'batt_section_y72_front.png','%s: section y = 72 (behind the drivers, under the PCB shelf), viewed from the rear (+X to the left)'%VAR,section=(1,72.0))
render(cutitems('le',2,H-3.5,exclude=ex_open,filt=lambda o:o['group'] not in ('lid','pcb','pcb_parts') and 'PcbScrew' not in o['name'] and o['group']!='insert'),-25,55,'batt_open_view.png','%s: top wall, lid, PCB and woofer-chamber insert hidden: pack, cradle, drivers, harness'%VAR,section=(2,H-3.5))
