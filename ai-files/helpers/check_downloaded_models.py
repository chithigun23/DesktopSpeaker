from OCP.STEPControl import STEPControl_Reader
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import json
from pathlib import Path
out={}
for name,path in [('TPS63802','/home/chithi/Downloads/ul_TPS63802DLAR/DLA0010A.stp'),('XFL4015','/home/chithi/Downloads/XFL4015.STEP')]:
 r=STEPControl_Reader(); r.ReadFile(path); r.TransferRoots(); s=r.OneShape(); b=Bnd_Box(); BRepBndLib.AddOptimal_s(s,b,False,False)
 solids=[]; it=TopExp_Explorer(s,TopAbs_SOLID)
 while it.More():
  a=it.Current(); bb=Bnd_Box(); BRepBndLib.AddOptimal_s(a,bb,False,False); g=GProp_GProps(); BRepGProp.VolumeProperties_s(a,g)
  solids.append({'bounds':tuple([bb.CornerMin().X(),bb.CornerMin().Y(),bb.CornerMin().Z(),bb.CornerMax().X(),bb.CornerMax().Y(),bb.CornerMax().Z()]),'volume':g.Mass()}); it.Next()
 out[name]={'source':path,'bounds':tuple([b.CornerMin().X(),b.CornerMin().Y(),b.CornerMin().Z(),b.CornerMax().X(),b.CornerMax().Y(),b.CornerMax().Z()]),'solids':solids}
Path('ai-files/reports/downloaded-model-geometry.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
