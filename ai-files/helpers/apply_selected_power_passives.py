"""Apply reviewed sourcing metadata; never move symbols or alter wires."""
from pathlib import Path
import json,sys,shutil,re
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
root=Path('DesktopSpeaker-kicad');report=json.loads(Path('ai-files/reports/power-passives-selected.json').read_text())
records=report['capacitors']+report['resistors']+report['optional_existing_resistors']
pd=json.loads(Path('ai-files/reports/pd-charger-capacitors.json').read_text())
for item in pd['candidates']:
 if item['lcsc'] in ['C1711','C28323','C51205']:
  q=dict(item);q['refs']={'C1711':['C2','C10'],'C28323':['C1','C3','C4','C6','C180'],'C51205':['C5']}[item['lcsc']]
  q['listing']=item['link'];q['datasheet_source']={'C1711':'https://www.lcsc.com/datasheet/C1711.pdf','C28323':'https://www.lcsc.com/datasheet/C28323.pdf','C51205':'https://product.samsungsem.com/mlcc/CL31B475KBHNNN.do'}[item['lcsc']]
  records.append(q)
records.append({'refs':['R4'],'manufacturer':'YAGEO','mpn':'RC1206FR-073K3L','lcsc':'C137292','package':'1206','listing':'https://www.lcsc.com/product-detail/C137292.html','datasheet_source':'https://yageogroup.com/component-documentation/download/specsheet/RC1206FR-073K3L','moq_pcs':50,'order_multiple_pcs':50,'quoted_tier_qty_pcs':50,'unit_price_usd_at_tier':.0104,'stock_snapshot':'264,700 listed'})
byref={r:q for q in records for r in q['refs']}
# Codec divider superseded by reviewed TPS63802 design; historical selections must not overwrite it.
byref.pop('R140',None)
byref.pop('R141',None)
def key(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,k):return next(v for v in x if key(v)==k)
def props(x):return {q[1]:q for q in x if key(q)=='property'}
def meta(x,name,value):
 old=props(x).get(name)
 if old:old[2]=value
 else:x.append([S('property'),name,value,[S('at'),*sub(x,'at')[1:]],[S('effects'),[S('font'),[S('size'),1,1]],[S('hide'),S('yes')]]])
# C5 needs the larger documented package, with local flat assets from installed libraries.
fpdir=root/'kicad-library/footprint';modeldir=root/'kicad-library/3d'
srcfp=next(Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints').rglob('Capacitor_SMD.pretty/C_1206_3216Metric.kicad_mod'))
srcmodel=next(Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Packages3D').rglob('Capacitor_SMD.3dshapes/C_1206_3216Metric.step'))
fptext=srcfp.read_text().replace('"C_1206_3216Metric"','"PD_C_1206"',1)
fptext=fptext.replace('${KICAD10_3DMODEL_DIR}/Capacitor_SMD.3dshapes/C_1206_3216Metric.step','${KIPRJMOD}/kicad-library/3d/PD_C_1206.step')
(fpdir/'PD_C_1206.kicad_mod').write_text(fptext);shutil.copyfile(srcmodel,modeldir/'PD_C_1206.step')
changed={}
for p in root.glob('*.kicad_sch'):
 if p.name=='DesktopSpeaker.kicad_sch':continue
 if p.name=='Battery_Charger.kicad_sch' and '--include-charger' not in sys.argv:continue
 original=p.read_text();d=loads(original);refs=[]
 for n in d:
  if key(n)!='symbol':continue
  pp=props(n);ref=pp.get('Reference',[None,None,None])[2]
  if ref not in byref:continue
  q=byref[ref]
  meta(n,'MPN',q['mpn']);meta(n,'Manufacturer',q['manufacturer']);meta(n,'LCSC',q['lcsc'])
  if 'LCSC Part' in pp:meta(n,'LCSC Part',q['lcsc'])
  ds=q.get('datasheet_source')
  if not ds and q.get('datasheet'):ds='${KIPRJMOD}/../ai-files/'+q['datasheet']
  if ds:meta(n,'Datasheet',ds)
  if ref=='C5':meta(n,'Footprint','DesktopSpeaker:PD_C_1206')
  if ref=='C181':meta(n,'Value','22nF X7R 50V')
  refs.append(ref)
 if refs:
  backup=Path('ai-files/backups')/(p.stem+'-before-passive-selection.kicad_sch')
  if not backup.exists():backup.write_text(original)
  p.write_text(dumps(d)+'\n');changed[p.name]=refs
Path('ai-files/reports/applied-power-passives.json').write_text(json.dumps({'date':'2026-10-05','changed':changed,'selections':records,'note':'C5 footprint enlarged; C181 newly captured dielectric changed to availableX7R. All earlier displayed values/positions/wires preserved.'},indent=2))
all_sources=records+[dict(q,listing=q.get('link')) for q in pd['candidates']]
by_mpn={q['mpn']:q for q in all_sources}
for mpn,group in pd.get('small_cap_group_reuse',{}).items():
 if mpn not in by_mpn:continue
 q=by_mpn[mpn];q['moq_pcs']=group['MOQ'];q['order_multiple_pcs']=group['order_multiple'];q['stock_pcs']=group['snapshot_stock']
 tier=min(int(k.rstrip('+')) for k in group['price_usd']);q['quoted_tier_qty_pcs']=tier;q['unit_price_usd_at_tier']=group['price_usd'][str(tier)+'+']
for q in all_sources:
 if q.get('ordering_stock_snapshot'):
  facts=q['ordering_stock_snapshot'];q['stock_pcs']=facts['stock_units'];q['moq_pcs']=facts['minimum_order_quantity'];q['order_multiple_pcs']=facts['order_multiple']
  tier=min(int(k.rstrip('+')) for k in facts['unit_price_usd_by_tier']);q['quoted_tier_qty_pcs']=tier;q['unit_price_usd_at_tier']=facts['unit_price_usd_by_tier'][str(tier)+'+']
 if 'stock_pcs' not in q:
  match=re.search(r'([0-9][0-9,]*)\s+(?:listed|shown)',q.get('stock_snapshot',q.get('stock_price_snapshot','')))
  if match:q['stock_pcs']=int(match[1].replace(',',''))
 # Explicit numeric facts take precedence; never infer MOQ from a price tier.
 if q.get('moq_pcs') is None and 'MOQ/multiple' in q.get('stock_price_snapshot',''):
  match=re.search(r'MOQ/multiple\s+(\d+)',q['stock_price_snapshot'])
  if match:q['moq_pcs']=q['order_multiple_pcs']=int(match[1])
 if q.get('unit_price_usd_at_tier') is None and q.get('moq_pcs') is not None:
  match=re.search(r'\$([0-9.]+)\s+at\s+(\d+)\+',q.get('stock_price_snapshot',''))
  if match:q['unit_price_usd_at_tier']=float(match[1]);q['quoted_tier_qty_pcs']=int(match[2])
bom_refs={}
for p in root.glob('*.kicad_sch'):
 for n in loads(p.read_text()):
  if key(n)!='symbol':continue
  pp=props(n);ref=pp.get('Reference',[None,None,None])[2];mpn=pp.get('MPN',[None,None,None])[2]
  if mpn in by_mpn:bom_refs[ref]=by_mpn[mpn]
Path('ai-files/reports/bom-passive-input.json').write_text(json.dumps({'date':'2026-10-05','byRef':bom_refs},indent=2))
print(json.dumps(changed))
