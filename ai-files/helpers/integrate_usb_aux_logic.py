"""Integrate reviewed auxiliary logic mux without changing PD voltage limits."""
from pathlib import Path
import sys, shutil, uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import load,dumps,Symbol as S
def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def one(x,n):return next(a for a in x if k(a)==n)
def prop(x,n):return next(a for a in x if k(a)=='property' and a[1]==n)
def uid():return str(uuid.uuid4())
def save(p,x):p.write_text('('+dumps(x[0])+'\n'+'\n'.join(dumps(a) for a in x[1:])+')\n')
def wire(doc,*pts):
 for a,b in zip(pts,pts[1:]):
  assert a[0]==b[0] or a[1]==b[1]
  doc.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
prj=ROOT/'DesktopSpeaker-kicad';candidate=ROOT/'ai-files/candidates'
fg=load(open(candidate/'Fuel_Gauge_Power.kicad_sch'))
assert any(k(a)=='symbol' and prop(a,'Reference')[2]=='U20' for a in fg)
assert not any(k(a)=='symbol' and prop(a,'Reference')[2]=='U20' for a in load(open(prj/'Fuel_Gauge_Power.kicad_sch')))
for a in fg:
 if k(a)!='symbol':continue
 ref=prop(a,'Reference')[2]
 if ref not in ['R124','R125']:continue
 mpn,lcsc=('RC0603FR-07180KL','C123419') if ref=='R124' else ('RC0603FR-07100KL','C14675')
 for name,val in [('Manufacturer','Yageo'),('MPN',mpn),('LCSC',lcsc),('LCSC Part',lcsc)]:
  a.append([S('property'),name,val,one(a,'at').copy(),[S('effects'),[S('font'),[S('size'),1,1]],[S('hide'),S('yes')]]])
for kind,ext in [('schematic','kicad_sym'),('footprint','kicad_mod'),('3d','step')]:
 shutil.copy2(candidate/f'TPS2116DRLR.{ext}',prj/f'kicad-library/{kind}/TPS2116DRLR.{ext}')
table=load(open(prj/'sym-lib-table'))
if not any(k(a)=='lib' and one(a,'name')[1]=='TPS2116DRLR' for a in table):
 table.append([S('lib'),[S('name'),'TPS2116DRLR'],[S('type'),'KiCad'],[S('uri'),'${KIPRJMOD}/kicad-library/schematic/TPS2116DRLR.kicad_sym'],[S('options'),''],[S('descr'),'USB and battery logic priority mux']])
save(prj/'sym-lib-table',table)
pd=load(open(prj/'USB_PD.kicad_sch'))
for a in pd:
 if k(a)=='label' and a[1]=='PD_VDD_5V':a[1]='USB_AUX_5V'
assert not any(k(a)=='hierarchical_label' and a[1]=='USB_AUX_5V' for a in pd)
# Extend the existing U19 output/C5 branch to a right-facing output port.
wire(pd,(199.39,218.44),(226.06,218.44))
pd.append([S('junction'),[S('at'),199.39,218.44],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
pd.append([S('hierarchical_label'),'USB_AUX_5V',[S('shape'),S('output')],[S('at'),226.06,218.44,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
# Hierarchy label names this local wired output; remove the duplicate local label.
pd[:]=[a for a in pd if not (k(a)=='label' and a[1]=='USB_AUX_5V' and one(a,'at')[1:3]==[199.39,218.44])]
root=load(open(prj/'DesktopSpeaker.kicad_sch'))
for a in root:
 if k(a)!='sheet':continue
 name=prop(a,'Sheet name')[2]
 if name not in ['USB_PD','Fuel_Gauge_Power']:continue
 x,ang,typ,just=(146.05,0,'output','right') if name=='USB_PD' else (240.03,180,'input','left')
 a.append([S('pin'),'USB_AUX_5V',S(typ),[S('at'),x,144.78,ang],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S(just),S('bottom')]],[S('uuid'),uid()]])
# Move the existing SYS branch below its direct link to clear the AUX wire.
for item in root:
 if k(item)=='label' and item[1]=='SYS_RAW' and one(item,'at')[1:3]==[228.6,134.62]:one(item,'at')[2]=152.4
 if k(item)=='wire':
  for point in one(item,'pts')[1:]:
   if point[1:]==[228.6,134.62]:point[2]=152.4
wire(root,(146.05,144.78),(153.67,144.78),(153.67,134.62),(234.95,134.62),(234.95,144.78),(240.03,144.78))
save(prj/'Fuel_Gauge_Power.kicad_sch',fg)
save(prj/'USB_PD.kicad_sch',pd)
save(prj/'DesktopSpeaker.kicad_sch',root)
print('Integrated auxiliary logic mux; active PD remains 5/9 V only.')
