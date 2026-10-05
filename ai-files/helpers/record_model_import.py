from pathlib import Path
import json,xml.etree.ElementTree as E,shutil
old=Path('ai-files/reports/DesktopSpeaker-netlist.xml');new=Path('ai-files/reports/DesktopSpeaker-model-import-netlist.xml')
def groups(p):
 return sorted(sorted((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')) for net in E.parse(p).findall('.//nets/net'))
assert groups(old)==groups(new),'Physical connectivity changed'
for c in E.parse(new).findall('.//components/comp'):
 if c.attrib['ref'] in ['U15','L3']:print(c.attrib['ref'],c.findtext('footprint'))
shutil.copy2(new,old);new.unlink()
p=Path('DesktopSpeaker-kicad/Bluetooth_Power.kicad_sch');s=p.read_text().replace('U15/L3 footprint and exact STEP pending. EN low disconnects output; default PFM.','EN low disconnects output; default PFM. Local verified package footprints/STEP assigned.');p.write_text(s)
p=Path('ai-files/reports/regulated-power-review.json');d=json.loads(p.read_text());d['open_models']=[];d['model_import_connectivity_preserved']=True
for name in ['TPS63802DLAR','Coilcraft_XFL4015-471MEC']:d['model_links'][name]={'paths':['${KIPRJMOD}/kicad-library/3d/'+name+'.step'],'files_present':True}
p.write_text(json.dumps(d,indent=2)+'\n')
for f in ['plan.md','ai-files/HANDOVER.md']:
 p=Path(f);s=p.read_text()
 if f=='plan.md':
  start=s.index('- U15/L3 exact models are missing.')
  end=s.index('\n',start)
  s=s[:start]+'- [x] U15/L3 exact STEP downloads imported from the user, geometry/orientation reviewed, footprints assigned and project-relative model links resolved. TI land-pattern centers corrected and pad 8 paste split to the manufacturer example. See the model-import evidence in the handover.'+s[end:]
 else:
  s+='''\n## Exact Bluetooth power models resolved (2026-10-04)\n\nUser provided Downloads/ul_TPS63802DLAR/DLA0010A.stp (Ultra Librarian TI package download) and Downloads/XFL4015.STEP (Coilcraft mechanical model download). Imported originals into the flat local 3d folder as TPS63802DLAR.step and Coilcraft_XFL4015-471MEC.step. OpenCascade geometry review: TI bounds 2×3×1mm, underside at z=0, pin 1 square terminal at x<0/y>0 matches footprint upper-left (KiCad drawing y negative). STEP assembly transforms already put TI upright: no extra rotation/offset. Coilcraft native height axis is Y; footprint model rotates X +90°, offsets Z +0.1mm, giving 4.3×4.3×1.6mm with terminal bottoms at board level. Body size is the allowed maximum of 4.0±0.3mm. Alignment image: reports/power-model-alignment.png; exact solid bounds: reports/downloaded-model-geometry.json. Download provenance is user-provided vendor assets, not an independently authenticated download.\n\nCorrected the unfinished TI candidate before activation: left pad centers x=-0.9mm, right four x=+0.75mm, pad8 x=+0.55mm; pitch0.5mm and pad widths0.6/0.9/1.3mm, all heights0.25mm and radius0.05mm, match TI datasheet board-layout example. Pad8 has two 0.55×0.25mm paste apertures at x0.175/0.925mm (83% coverage), per TI stencil example; no fictitious pad11. Coilcraft pads remain0.98×3.4mm at x±1.185mm, matching maker land pattern. U15/L3 active footprints and U15 standalone/cached symbol footprint now assigned, all model links local. These facts supersede the missing-model/blank-footprint status above.\n\nPhysical pin net groups before/after model import are identical. No ERC or physical testing was run; electrical margin, regulator transient/noise qualification, module I/O isolation, unresolved passive/switch selections and BOM reconciliation remain open. Latest six-page preview refreshed using installed KiCad10.0.6/rc2. Temporary CAD environment removed after review to avoid retaining 1.3GB of tools in the project; helpers require cadquery-ocp and matplotlib if rerun.\n'''
 p.write_text(s)
# Remove only the temporary environment installed by this import.
shutil.rmtree('ai-files/cad-tools-venv')
