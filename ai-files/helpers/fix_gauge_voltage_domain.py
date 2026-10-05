"""One-shot coordinator fix: AO-powered switches, BAT-qualified default-off enable.

Requires the reviewed TPS3839G33DBZR candidate library assets. Does not touch
root hierarchy or unrelated wiring. Snapshot/netlist review is external. Follow-up text/placement refinements
are in the active sheet; do not rerun this one-shot helper.
"""
from pathlib import Path
import sys, copy, uuid
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ai-files/vendor'))
from sexpdata import load, dumps, Symbol as S
def k(x): return str(x[0]) if isinstance(x,list) and x else ''
def one(x,n): return next(a for a in x if k(a)==n)
def allof(x,n): return [a for a in x if k(a)==n]
def uid(): return str(uuid.uuid4())
def at(x,y,a=0): return [S('at'),round(x,4),round(y,4),a]
def xy(p): return [S('xy'),*p]
sheet=ROOT/'DesktopSpeaker-kicad/Fuel_Gauge_Power.kicad_sch'
d=load(open(sheet)); libs=one(d,'lib_symbols')
path='/feda53ed-537d-4f88-9436-c6075776255b/9c37a727-9991-421a-8f6e-77dd39bb53fa'
assert not any(k(a)=='symbol' and one(a,'property')[2]=='U21' for a in d), 'Already applied'
def add(a): d.append(a)
def wire(a,b):
    assert a[0]==b[0] or a[1]==b[1],(a,b)
    if a!=b: add([S('wire'),[S('pts'),xy(a),xy(b)],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
def route(*p):
    for a,b in zip(p,p[1:]): wire(a,b)
def label(name,x,y):add([S('label'),name,at(x,y),[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
def junction(x,y):add([S('junction'),at(x,y)[:3],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
def prop(name,value,x,y,hidden=False,left=False):
    eff=[S('effects'),[S('font'),[S('size'),1,1]]]
    if hidden:eff.append([S('hide'),S('yes')])
    if left:eff.append([S('justify'),S('left')])
    return [S('property'),name,value,at(x,y),eff]
def component(ref,value,libid,x,y,fp,fields=None,ic=False):
    lib=next(a for a in libs if k(a)=='symbol' and a[1]==libid)
    pins=[one(p,'number')[1] for sub in lib if k(sub)=='symbol' for p in sub if k(p)=='pin']
    dx,dy=(0,10.16) if ic else (5.08,-1.27)
    inherited={p[1]:p[2] for p in lib if k(p)=='property' and p[1] not in ['Reference','Value','Footprint']}
    inherited.update(fields or {})
    add([S('symbol'),[S('lib_id'),libid],at(x,y),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()],
         prop('Reference',ref,x+dx,y+dy,left=not ic),prop('Value',value,x+dx,y+dy+2.54,left=not ic),prop('Footprint',fp,x,y,True),
         *[prop(a,b,x,y,True) for a,b in inherited.items()],
         *[[S('pin'),p,[S('uuid'),uid()]] for p in pins],
         [S('instances'),[S('project'),'DesktopSpeaker',[S('path'),path,[S('reference'),ref],[S('unit'),1]]]]])
def gnd(ref,x,y):
    add([S('symbol'),[S('lib_id'),'power:GND'],at(x,y),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('no')],[S('on_board'),S('no')],[S('dnp'),S('no')],[S('uuid'),uid()],prop('Reference',ref,x,y+3.81,True),prop('Value','GND',x,y+5.08),[S('pin'),'1',[S('uuid'),uid()]],[S('instances'),[S('project'),'DesktopSpeaker',[S('path'),path,[S('reference'),ref],[S('unit'),1]]]]])
# Existing switch placement and signal wiring stay intact.
for y in [71.12,106.68,144.78]:
    doomed=[{(229.87,round(y+2.54,4)),(215.9,round(y+2.54,4))},
            {(215.9,round(y+2.54,4)),(215.9,round(y+10.16,4))}]
    for a in d[:]:
        if k(a)=='wire':
            pts={tuple(p[1:]) for p in one(a,'pts')[1:]}
            if pts in doomed:d.remove(a)
    wire((229.87,round(y+2.54,4)),(223.52,round(y+2.54,4)))
    label('GAUGE_ISO_N',223.52,round(y+2.54,4))
switch_supply_labels={(242.57,55.88),(242.57,91.44),(242.57,129.54),
                      (265.43,83.82),(265.43,116.84),(265.43,146.05)}
changed=[]
for a in d:
    if k(a)=='label' and a[1]=='BAT_PACK' and tuple(one(a,'at')[1:3]) in switch_supply_labels:
        a[1]='3V_AO';changed.append(tuple(one(a,'at')[1:3]))
assert len(changed)==6,changed
# Bring reviewed libraries into the sheet cache; active registration is coordinator-owned.
for part in ['TPS3839G33DBZR','2N7002']:
    p=ROOT/f'DesktopSpeaker-kicad/kicad-library/schematic/{part}.kicad_sym'
    lib=copy.deepcopy(one(load(open(p)),'symbol'));lib[1]=f'{part}:{part}'
    if not any(k(a)=='symbol' and a[1]==lib[1] for a in libs): libs.append(lib)
component('U21','TPS3839G33DBZR','TPS3839G33DBZR:TPS3839G33DBZR',68.58,116.84,'DesktopSpeaker:TPS3839G33DBZR',ic=True)
component('Q104','2N7002','2N7002:2N7002',109.22,119.38,'DesktopSpeaker:2N7002',{'MPN':'2N7002,215','LCSC':'C65189','Manufacturer':'Nexperia'})
component('R126','1M','PD_R:PD_R',111.76,99.06,'DesktopSpeaker:PD_R_0603')
component('R127','1M','PD_R:PD_R',96.52,132.08,'DesktopSpeaker:PD_R_0603')
cap=next(a for a in d if k(a)=='symbol' and one(a,'property')[2]=='C120')
capfields={p[1]:p[2] for p in cap if k(p)=='property' and p[1] not in ['Reference','Value','Footprint']}
component('C126','100nF X7R 10V','PD_C:PD_C',45.72,116.84,'DesktopSpeaker:PD_C_0603',capfields)
# U21 functional pins assumed VDD top (0,+7.62), GND bottom(0,-7.62), RESET right(+10.16,0).
route((68.58,109.22),(68.58,104.14),(45.72,104.14),(45.72,113.03))
label('BAT_PACK',45.72,104.14);junction(68.58,104.14)
wire((45.72,120.65),(45.72,124.46));gnd('#PWR224',45.72,124.46)
wire((68.58,124.46),(68.58,134.62));gnd('#PWR225',68.58,134.62)
route((78.74,116.84),(96.52,116.84),(96.52,119.38),(104.14,119.38))
wire((96.52,119.38),(96.52,128.27));junction(96.52,119.38)
wire((96.52,135.89),(96.52,139.7));gnd('#PWR226',96.52,139.7)
wire((111.76,124.46),(111.76,139.7));gnd('#PWR227',111.76,139.7)
wire((111.76,102.87),(111.76,114.3));label('GAUGE_ISO_N',111.76,110.49)
wire((111.76,95.25),(111.76,91.44));label('3V_AO',111.76,91.44)
for a in d:
    if k(a)=='text' and 'Gauge isolation:' in str(a[1]):
        a[1]='Gauge bus: AO-powered switches; default OFF below valid battery.\nU21 3.08 V supervisor enables Q104 after reset recovery.'
sheet.write_text(dumps(d)+'\n')
print('Changed only switch supplies/enables; added U21/Q104/R126/R127/C126')
