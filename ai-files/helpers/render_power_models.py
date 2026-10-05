from OCP.STEPControl import STEPControl_Reader
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from pathlib import Path
fig,axs=plt.subplots(2,2,figsize=(10,8))
for row,name in enumerate(['TPS63802DLAR','Coilcraft_XFL4015-471MEC']):
 r=STEPControl_Reader();r.ReadFile('DesktopSpeaker-kicad/kicad-library/3d/'+name+'.step');r.TransferRoots();s=r.OneShape();BRepMesh_IncrementalMesh(s,.015)
 tri=[];e=TopExp_Explorer(s,TopAbs_FACE)
 while e.More():
  loc=TopLoc_Location();mesh=BRep_Tool.Triangulation_s(TopoDS.Face(e.Current()),loc)
  if mesh:
   for i in range(1,mesh.NbTriangles()+1):
    pts=[]
    for j in mesh.Triangle(i).Get():
     p=mesh.Node(j).Transformed(loc.Transformation());x,y,z=p.X(),p.Y(),p.Z()
     if row: y,z=-z,y+.1
     pts.append((x,y,z))
    tri.append(pts)
  e.Next()
 for col,axes in enumerate([(0,1),(0,2)]):
  ax=axs[row,col];ax.add_collection(PolyCollection([[(p[axes[0]],p[axes[1]]) for p in t] for t in tri],facecolors='#adc4d0',edgecolors='#637887',linewidths=.12));ax.autoscale();ax.set_aspect('equal');ax.set_title(name+(' top' if col==0 else ' side'));ax.set_xlabel('X mm');ax.set_ylabel('Y mm' if col==0 else 'Z mm');ax.grid(alpha=.2)
 if not row:
  for pin in range(1,11):
   x=-.9 if pin<=5 else (.55 if pin==8 else .75);y=1-(pin-1)*.5 if pin<=5 else -1+(pin-6)*.5
   w=.6 if pin<=5 else (1.3 if pin==8 else .9)
   axs[row,0].add_patch(Rectangle((x-w/2,y-.125),w,.25,fill=False,edgecolor='red',linewidth=1.4));axs[row,0].text(x,y,str(pin),fontsize=7,ha='center',va='center')
 else:
  for x in [-1.185,1.185]:axs[row,0].add_patch(Rectangle((x-.49,-1.7),.98,3.4,fill=False,edgecolor='red',linewidth=1.4))
fig.tight_layout();fig.savefig('ai-files/reports/power-model-alignment.png',dpi=180)
