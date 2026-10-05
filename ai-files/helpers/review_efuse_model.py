"""Review the user-supplied TPS26600 model before linking. No PCB layout."""
from pathlib import Path
import json
import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
corrected='--corrected' in sys.argv
tag='efuse-model-corrected' if corrected else 'efuse-model'
source=Path('DesktopSpeaker-kicad/kicad-library/3d/TPS26600PWPR_datasheet_EP.step') if corrected else Path('ai-files/candidates/TPS26600-vendor/PWP0016H.stp')
r=STEPControl_Reader();r.ReadFile(str(source));r.TransferRoots();shape=r.OneShape()
def bounds(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s,b,False,False)
 return [b.CornerMin().X(),b.CornerMin().Y(),b.CornerMin().Z(),b.CornerMax().X(),b.CornerMax().Y(),b.CornerMax().Z()]
solid_bounds=[];ex=TopExp_Explorer(shape,TopAbs_SOLID)
while ex.More():solid_bounds.append(bounds(ex.Current()));ex.Next()
result={'source':str(source),'bounds':bounds(shape),'solids':solid_bounds}
Path(f'ai-files/reports/{tag}-geometry.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
BRepMesh_IncrementalMesh(shape,.015)
tri=[];ex=TopExp_Explorer(shape,TopAbs_FACE)
while ex.More():
 loc=TopLoc_Location();mesh=BRep_Tool.Triangulation_s(TopoDS.Face(ex.Current()),loc)
 if mesh:
  for i in range(1,mesh.NbTriangles()+1):
   pts=[]
   for j in mesh.Triangle(i).Get():
    p=mesh.Node(j).Transformed(loc.Transformation());pts.append((p.X(),p.Y(),p.Z()))
   tri.append(pts)
 ex.Next()
fig,axs=plt.subplots(1,3,figsize=(12,4))
for ax,axes in zip(axs,[(0,1),(0,2),(1,2)]):
 ax.add_collection(PolyCollection([[(p[axes[0]],p[axes[1]]) for p in t] for t in tri],facecolors='#adc4d0',edgecolors='#637887',linewidths=.10));ax.autoscale();ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('XYZ'[axes[0]]+' mm');ax.set_ylabel('XYZ'[axes[1]]+' mm')
axs[0].set_title('Native XY');axs[1].set_title('Native XZ');axs[2].set_title('Native YZ')
if corrected:
 for i in range(1,17):
  x=-2.9 if i<=8 else 2.9;y=2.275-(i-1)*.65 if i<=8 else -2.275+(i-9)*.65
  axs[0].add_patch(Rectangle((x-.75,y-.225),1.5,.45,fill=False,edgecolor='red',linewidth=1));axs[0].text(x,y,str(i),fontsize=6,ha='center',va='center')
 axs[0].add_patch(Rectangle((-1.65,-1.65),3.3,3.3,fill=False,edgecolor='red',linewidth=1.5))
 axs[0].set_title('Model / footprint lands (red)')
fig.tight_layout();fig.savefig(f'ai-files/reports/{tag}-native.png',dpi=180)
