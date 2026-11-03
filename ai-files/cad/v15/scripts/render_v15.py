"""Headless renders (FreeCAD tessellation + numpy/matplotlib painter's algorithm).
Run: freecadcmd ai-files/cad/render_cad.py  -> renders/*.png"""
import json, os, math, Part, FreeCAD as App
from FreeCAD import Vector as V
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
CAD=os.environ.get('CAD_OUT','/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v15/').rstrip('/')+'/'; W=CAD+'work/'; OUT=CAD+'renders/'; os.makedirs(OUT,exist_ok=True)
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
# ---- v15 views: wiring, crimps/housings, the vendor-built 1S4P brick, countersunk screws (render_cad.py helpers above, unchanged)
ex_open=('Lid_rear','SW101_rocker_D20_standin','SW101_rocker_GRB112B802BR1','Gasket_lid_foam_3mm')
def pick(*pre): return lambda o: o['name'].startswith(pre)
render(cutitems('le',2,H-3.5,exclude=ex_open,filt=lambda o:o['group']!='lid'),-25,55,'v15_wiring_open_top.png','v15: top wall and lid removed: J9/J10 leads over the drivers to the ND65 solder tabs, J11 adapter to the grommet, J5 pack leads down the right side',section=(2,H-3.5))
render(base_items(fn_filter=lambda o:o['name'].startswith(('Wire_J9','Wire_J10','Solder_','Housing_J9','Housing_J10','Crimp_J9','Crimp_J10','Driver_','Washer_','Screw_M3x10CSK_Drv','PCB_J9','PCB_J10','PCB_J11','Housing_J11','Crimp_J11')) or o['group']=='pcb'),-30,38,'v15_wiring_drivers.png','v15: J9 (FRONT_L) and J10 (FRONT_R) 20 AWG leads from the VHR-2N housings to the ND65-4 solder tabs; cup washers + countersunk T10 screws on the flanges')
render(base_items(fn_filter=pick('Wire_J11','Wire_Woofer','Sleeve_','Housing_J11','Crimp_J11','Housing_Woofer','Crimp_Woofer','Grommet_','Woofer_W3','PCB_J11')),60,35,'v15_wiring_woofer.png','v15: J11 adapter (VHR-2N, 20 AWG pair) through the Heyco grommet, staggered splices, PH male + woofer PHR-2, pigtail to the frame rib (insert hidden)')
render(base_items(fn_filter=lambda o:o['name'].startswith(('Wire_J5','Housing_J5','Crimp_J5','PCB_J5','Strap_','Grommet_')) or o['group']=='battery'),40,30,'v15_wiring_pack.png','v15: J5 pack leads (Micro-Fit 43645-0300 + 43030 crimps): down the right side, forward, over to the PCM top edge through the wrap slit')
ys=m['cradle']['strap_y'][0]
render(cutitems('le',1,ys,filt=lambda o:o['group'] in ('shell','battery') or o['name'].startswith('Strap_')),180,8,'v15_pack_section_strap.png','v15: section y = %.1f (strap): wrapped brick in the saddle cradle, strap through both anchor tunnels and the 0.6 mm floor channel' % ys,section=(1,ys))
render(base_items(fn_filter=lambda o:o['group']=='battery' and 'Wrap' not in o['name'] and 'PCM' not in o['name']),160,40,'v15_pack_positive_end.png','v15: 1S4P brick without the wrap and PCM, positive end: fish paper, nickel pads with 1.0 mm fusible links to the bus bar; NTC between cells 2 and 3')
render(base_items(fn_filter=lambda o:o['name'].startswith(('Battery_Cell','Battery_Nickel','Battery_NTC'))),165,35,'v15_pack_nickel_links.png','v15: positive nickel (pads on the buttons, 1.0 x 3.4 mm fusible necks, bus bar) and the negative strip; fish paper, PCM and wrap hidden')
render(base_items(fn_filter=pick('Battery_')),-30,30,'v15_pack_wrapped.png','v15: vendor-built 1S4P brick (heat-shrink, positive end at the rear)')
render(base_items(fn_filter=pick('Lid_rear','Screw_M3x10CSK_Lid','SW101','PCB_J1','PCB_J2','PCB_J3')),180,12,'v15_lid_countersunk.png','v15: rear lid outside: 11 countersunk T10 post-Torx M3x10 flush in 6.0 x 90 deg countersinks')
# close-up section through driver screw L1 (local pieces of the shell and driver only)
sn='DrvScrew_L1'; st=[x for x in m['sites'] if x['name']==sn][0]['p']
lb=Part.makeBox(1.0, 26.0, 16.0, V(st[0]-0.5+0.0, st[1]-14.0, st[2]-8.0))
it=[]
for o,s_ in OBJ:
    nm=o['name']
    if not (nm.endswith(sn) or nm.startswith(('Driver_FrontL','Shell_Box'))): continue
    bb=s_.BoundBox
    loc=Part.makeBox(16.0, 26.0, 16.0, V(st[0]-16.0, st[1]-14.0, st[2]-8.0))
    try: sh=s_.common(loc)
    except Exception: continue
    if sh.isNull() or sh.Volume<1e-6: continue
    v,f=tess(nm,sh,'drvloc'); it.append((nm,o['color'],v,f,(0,0,0)))
render(it,90,0,'v15_driver_screw_section.png','v15: section x = %.1f, driver screw L1: cup washer 8 x 1.6 on the ND65 flange,\ncountersunk T10 M3x10 into the 5.7 mm pad insert (7.65 mm thread below the pad face)' % st[0],section=(0,st[0]))
