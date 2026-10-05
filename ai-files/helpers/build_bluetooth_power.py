"""One-shot provisional BT rail; exact U15/L3 package models remain open."""
from pathlib import Path
import copy,sys,uuid
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import Symbol,load,dumps
S=Symbol
DEST=ROOT/'DesktopSpeaker-kicad/Bluetooth_Power.kicad_sch'
if DEST.exists():raise SystemExit('Refusing to overwrite existing child')
ID='f761c113-2c86-429a-8773-5f4b423ef275';PATH='/feda53ed-537d-4f88-9436-c6075776255b/'+ID
base=load((ROOT/'DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch').open())
def k(v):return str(v[0]) if isinstance(v,list) and v else ''
def allof(v,n):return [t for t in v if k(t)==n]
def one(v,n):return allof(v,n)[0]
def uid():return str(uuid.uuid4())
def at(x,y,a=0):return [S('at'),x,y,a]
def effects(size=1.27,hide=False,j=None):
 e=[S('effects'),[S('font'),[S('size'),size,size]]]
 if hide:e.append([S('hide'),S('yes')])
 if j:e.append([S('justify'),S(j)])
 return e
u=copy.deepcopy(one(load((ROOT/'DesktopSpeaker-kicad/kicad-library/schematic/TPS63802DLAR.kicad_sym').open()),'symbol'))
# Keep the incomplete package assignment open rather than use a mismatched generic DFN model.
for p in allof(u,'property'):
 if p[1]=='Footprint':p[2]=''
 if p[1]=='Datasheet':p[2]='../ai-files/datasheets/TPS63802.pdf'
libfile=[S('kicad_symbol_lib'),[S('version'),20260306],[S('generator'),'kicad_symbol_editor'],copy.deepcopy(u)]
(ROOT/'DesktopSpeaker-kicad/kicad-library/schematic/TPS63802DLAR.kicad_sym').write_text(dumps(libfile)+'\n')
u[1]='TPS63802DLAR:TPS63802DLAR'
lib=[S('lib_symbols'),u]
for name in ['Device:L','PD_C:PD_C','PD_R:PD_R','power:GND']:
 lib.append(copy.deepcopy(next(v for v in allof(one(base,'lib_symbols'),'symbol') if v[1]==name)))
d=[S('kicad_sch'),[S('version'),20260306],[S('generator'),'eeschema'],[S('generator_version'),'10.0'],[S('uuid'),ID],[S('paper'),'A4'],[S('title_block'),[S('title'),'Switched 3.8 V Bluetooth supply'],[S('rev'),'0.1']],lib]
def wire(*pts):
 for a,b in zip(pts,pts[1:]):
  assert a[0]==b[0] or a[1]==b[1]
  d.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
def dot(x,y):d.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
def port(name,x,y,side='left'):
 d.append([S('hierarchical_label'),name,[S('shape'),S('input' if side=='left' else 'output')],at(x,y,0 if side=='left' else 180),effects(1,j=side),[S('uuid'),uid()]])
def inst(lid,ref,value,x,y,ang=0,fp='',mpn='',lcsc='',ic=False):
 o=[S('symbol'),[S('lib_id'),lid],at(x,y,ang),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('no' if ref.startswith('#') else 'yes')],[S('on_board'),S('no' if ref.startswith('#') else 'yes')],[S('dnp'),S('no')],[S('uuid'),uid()]]
 if ic:rp=(x,y+24.13);vp=(x,y+26.67);j=None
 else:rp=(x+5.08,y-1.27);vp=(x+5.08,y+1.27);j='left'
 o.extend([[S('property'),'Reference',ref,at(*rp,ang),effects(hide=ref.startswith('#'),j=j)],[S('property'),'Value',value,at(*vp,ang),effects(hide=ref.startswith('#'),j=j)],[S('property'),'Footprint',fp,at(x,y),effects(hide=True)]])
 for name,val in [('MPN',mpn),('LCSC Part',lcsc)]:
  if val:o.append([S('property'),name,val,at(x,y),effects(hide=True)])
 definition=next(t for t in lib[1:] if t[1]==lid)
 for sub in allof(definition,'symbol'):
  for p in allof(sub,'pin'):o.append([S('pin'),one(p,'number')[1],[S('uuid'),uid()]])
 o.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),PATH,[S('reference'),ref],[S('unit'),1]]]])
 d.append(o);return o
ng=500
def gnd(x,y):
 global ng
 ng+=1;inst('power:GND','#PWR'+str(ng),'GND',x,y)
def cap(ref,x,y,value='22uF 10V X7R'):
 inst('PD_C:PD_C',ref,value,x,y,fp='DesktopSpeaker:PD_C_0805' if value.startswith('22') else 'DesktopSpeaker:PD_C_0603',mpn='GRM21BZ71A226ME15L' if value.startswith('22') else 'TBD',lcsc='C907991' if value.startswith('22') else 'TBD')
def res(ref,value,x,y):inst('PD_R:PD_R',ref,value,x,y,fp='DesktopSpeaker:PD_R_0603',mpn='TBD')
inst('TPS63802DLAR:TPS63802DLAR','U15','TPS63802DLAR',139.7,93.98,mpn='TPS63802DLAR',lcsc='C2845237',ic=True)
l=inst('Device:L','L3','0.47uH',139.7,60.96,90,mpn='XFL4015-471MEC',lcsc='C18221164')
for p in allof(l,'property'):
 if p[1]=='Reference':one(p,'at')[1:]=[148.59,66.04,90]
 if p[1]=='Value':one(p,'at')[1:]=[148.59,68.58,90]
cap('C150',76.2,55.88);cap('C151',50.8,55.88,'100nF 10V X7R')
for ref,x in [('C152',218.44),('C153',241.3),('C154',264.16)]:cap(ref,x,93.98)
res('R150','604k 1%',187.96,91.44);res('R151','91k 1%',187.96,115.57)
res('R152','100k',69.85,137.16);res('R153','100k',48.26,175.26);res('R154','100k',203.2,134.62)
port('SYS_RAW',25.4,40.64);wire((25.4,40.64),(50.8,40.64),(76.2,40.64),(101.6,40.64),(101.6,91.44),(124.46,91.44))
for x in [50.8,76.2]:wire((x,40.64),(x,52.07));dot(x,40.64);wire((x,59.69),(x,64.77));gnd(x,64.77)
wire((124.46,83.82),(124.46,60.96),(135.89,60.96));wire((143.51,60.96),(154.94,60.96),(154.94,83.82))
wire((154.94,91.44),(168.91,91.44),(168.91,76.2),(187.96,76.2),(203.2,76.2),(218.44,76.2),(241.3,76.2),(264.16,76.2),(279.4,76.2));port('3V8_BT',279.4,76.2,'right')
for x in [218.44,241.3,264.16]:wire((x,76.2),(x,90.17));dot(x,76.2);wire((x,97.79),(x,102.87));gnd(x,102.87)
wire((187.96,76.2),(187.96,87.63));dot(187.96,76.2);wire((187.96,95.25),(187.96,102.87),(187.96,111.76));dot(187.96,102.87)
wire((154.94,96.52),(165.1,96.52),(165.1,102.87),(187.96,102.87));wire((187.96,119.38),(187.96,124.46));gnd(187.96,124.46)
wire((203.2,76.2),(203.2,130.81));dot(203.2,76.2);wire((203.2,138.43),(203.2,143.51));gnd(203.2,143.51)
port('BT_PWR_EN',25.4,124.46);wire((25.4,124.46),(69.85,124.46),(88.9,124.46),(88.9,96.52),(124.46,96.52));wire((69.85,124.46),(69.85,133.35));dot(69.85,124.46);wire((69.85,140.97),(69.85,146.05));gnd(69.85,146.05)
port('BT_FORCE_PWM',25.4,162.56);wire((25.4,162.56),(48.26,162.56),(114.3,162.56),(114.3,101.6),(124.46,101.6));wire((48.26,162.56),(48.26,171.45));dot(48.26,162.56);wire((48.26,179.07),(48.26,184.15));gnd(48.26,184.15)
gnd(137.16,111.76);gnd(142.24,111.76)
d.append([S('no_connect'),[S('at'),154.94,101.6],[S('uuid'),uid()]])
for text,y in [('SYS to switched 3.8 V for BM83; reserve 500 mA. Module wiring follows later.',25.4),('U15/L3 footprint and exact STEP pending. EN low disconnects output; default PFM.',30.48),('Switch OFF after BM83 power-off ACK; validate >640 us supply decay and signal isolation.',35.56)]:
 d.append([S('text'),text,at(25.4,y),effects(1,j='left'),[S('uuid'),uid()]])
DEST.write_text('(kicad_sch\n'+'\n'.join(dumps(v) for v in d[1:])+'\n)\n')
print('Bluetooth regulator circuit captured; exact U15/L3 footprint/model assignments pending.')
