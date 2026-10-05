"""Preserve downloaded body/leads; replace the mismatched EP with a nominal PWP0016A pad."""
from pathlib import Path
import json, hashlib
from OCP.STEPControl import STEPControl_Reader, STEPControl_AsIs
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.gp import gp_Pnt
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
source=Path('ai-files/candidates/TPS26600-vendor/PWP0016H.stp')
target=Path('DesktopSpeaker-kicad/kicad-library/3d/TPS26600PWPR_datasheet_EP.step')
r=STEPControl_Reader();r.ReadFile(str(source));r.TransferRoots();solids=[];ex=TopExp_Explorer(r.OneShape(),TopAbs_SOLID)
while ex.More():solids.append(ex.Current());ex.Next()
if len(solids)!=18:raise ValueError('Unexpected original solid count')
solids[-1]=BRepPrimAPI_MakeBox(gp_Pnt(-1.5,-1.5,0),3,3,.28).Shape()
doc=TDocStd_Document(TCollection_ExtendedString('efuse-datasheet-corrected'))
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
for i,shape in enumerate(solids):
 label=st.AddShape(shape,False)
 color=Quantity_Color(.13,.13,.15,Quantity_TOC_RGB) if i==0 else Quantity_Color(.72,.73,.75,Quantity_TOC_RGB)
 ct.SetColor(label,color,XCAFDoc_ColorGen)
writer=STEPCAFControl_Writer();writer.SetColorMode(True);writer.Transfer(doc,STEPControl_AsIs);writer.Write(str(target))
fp=Path('DesktopSpeaker-kicad/kicad-library/footprint/TPS26600PWPR.kicad_mod')
text=fp.read_text()
if '(model ' in text:raise ValueError('Footprint already has model; review rather than append')
pos=text.rfind('(embedded_fonts no)')
text=text[:pos]+'(model "${KIPRJMOD}/kicad-library/3d/TPS26600PWPR_datasheet_EP.step"\n (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n  '+text[pos:]
fp.write_text(text)
Path('ai-files/reports/efuse-model-provenance.json').write_text(json.dumps({
 'origin':'User download ul_TPS26600PWPR.zip via requested DigiKey/Ultra Librarian listing',
 'sourceFile':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'activeFile':str(target),'activeSha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'derivedModel':True,'changes':'Original molded body and 16 lead solids retained. Original EP 2.509x2.91mm at z0.13 replaced by nominal 3x3mm EP, underside z0, height0.28mm. Body/lead coloring assigned.',
 'datasheet':'https://www.ti.com/lit/ds/symlink/tps2660.pdf',
 'orientation':'No rotation, scale or offset; pin1 molded marker at native x<0/y>0 aligns footprint upper-left; leads underside z0.',
 'qualification':'Mechanical visualization, not manufacturer-authenticated exact CAD. EP copper remains3.3x3.3 per land pattern.'},indent=2))
print(target)
