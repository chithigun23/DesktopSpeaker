"""Add a reverse-blocking USB/SYS priority mux to an isolated gauge-power sheet."""
from pathlib import Path
import sys,copy,uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import load,dumps,Symbol as S

def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def one(x,n):return next(a for a in x if k(a)==n)
def prop(x,n):return next(a for a in x if k(a)=='property' and a[1]==n)
def uid():return str(uuid.uuid4())
def at(x,y,a=0):return [S('at'),x,y,a]
def eff(hide=False,justify=None):
 e=[S('effects'),[S('font'),[S('size'),1,1]]]
 if hide:e.append([S('hide'),S('yes')])
 if justify:e.append([S('justify'),S(justify)])
 return e
src=load(open(ROOT/'DesktopSpeaker-kicad/Fuel_Gauge_Power.kicad_sch'))
libs=one(src,'lib_symbols')
instances={prop(a,'Reference')[2]:a for a in src if k(a)=='symbol'}
assert 'U20' not in instances,'Already captured; do not replay source builder'
pathid=one(one(one(instances['U12'],'instances'),'project'),'path')[1]
def wire(*points):
 for a,b in zip(points,points[1:]):
  if a==b:continue
  assert a[0]==b[0] or a[1]==b[1],(a,b)
  src.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
def junction(x,y):src.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
def clone(ref,newref,x,y):
 a=copy.deepcopy(instances[ref]);old=one(a,'at');dx=x-old[1];dy=y-old[2];old[1:3]=[x,y]
 for p in a:
  if k(p)=='property':
   p_at=one(p,'at');p_at[1]+=dx;p_at[2]+=dy
 prop(a,'Reference')[2]=newref
 one(a,'uuid')[1]=uid()
 for pin in [p for p in a if k(p)=='pin']:one(pin,'uuid')[1]=uid()
 one(one(one(a,'instances'),'project'),'path')[1]=pathid
 one(one(one(one(a,'instances'),'project'),'path'),'reference')[1]=newref
 src.append(a);return a
oldpairs={frozenset((a,b)) for a,b in [((35.56,26.67),(81.28,26.67)),((81.28,26.67),(96.52,26.67)),((96.52,26.67),(96.52,33.02)),((96.52,33.02),(111.76,33.02)),((96.52,33.02),(96.52,38.1)),((96.52,38.1),(111.76,38.1)),((81.28,26.67),(81.28,39.37)),((81.28,46.99),(81.28,52.07))]}
removed=0
for a in list(src):
 if k(a)=='wire' and frozenset(tuple(v[1:]) for v in one(a,'pts')[1:]) in oldpairs:src.remove(a);removed+=1
 elif k(a)=='junction' and tuple(one(a,'at')[1:3]) in [(96.52,33.02),(81.28,26.67)]:src.remove(a)
 elif k(a)=='symbol' and prop(a,'Reference')[2]=='#PWR101':src.remove(a)
assert removed==8,removed
sysport=next(a for a in src if k(a)=='hierarchical_label' and a[1]=='SYS_RAW');one(sysport,'at')[1:3]=[35.56,58.42]
src.append([S('hierarchical_label'),'USB_AUX_5V',[S('shape'),S('input')],at(35.56,17.78),[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
# Move only the regulator input decoupler to clear the inserted mux.
c=instances['C122'];dx=104.14-one(c,'at')[1];one(c,'at')[1]=104.14
for p in c:
 if k(p)=='property':one(p,'at')[1]+=dx
# Cache reviewed TPS symbol. MODE is on top to keep the divider route clear.
tps=copy.deepcopy(one(load(open(ROOT/'ai-files/candidates/TPS2116DRLR.kicad_sym')),'symbol'))
tps[1]='TPS2116DRLR:TPS2116DRLR';prop(tps,'Datasheet')[2]='${KIPRJMOD}/../ai-files/datasheets/TPS2116.pdf';libs.append(tps)
pins={one(p,'number')[1]:one(p,'at')[1:3] for sub in tps if k(sub)=='symbol' for p in sub if k(p)=='pin'}
assert '[2,7]' in pins and '3' in pins and '6' in pins,pins
assert pins['5']==[0,10.16],pins['5']
a=[S('symbol'),[S('lib_id'),'TPS2116DRLR:TPS2116DRLR'],at(83.82,35.56),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()]]
for name,value,pos,hide in [('Reference','U20',(83.82,49.53),False),('Value','TPS2116DRLR',(83.82,52.07),False),('Footprint','DesktopSpeaker:TPS2116DRLR',(83.82,35.56),True),('Datasheet','${KIPRJMOD}/../ai-files/datasheets/TPS2116.pdf',(83.82,35.56),True),('Manufacturer','Texas Instruments',(83.82,35.56),True),('MPN','TPS2116DRLR',(83.82,35.56),True),('LCSC','C3235557',(83.82,35.56),True)]:
 a.append([S('property'),name,value,at(*pos),eff(hide)])
for number in pins:a.append([S('pin'),number,[S('uuid'),uid()]])
a.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),pathid,[S('reference'),'U20'],[S('unit'),1]]]]);src.append(a)
# Regulator input from mux, with EN directly wired to that input.
wire((93.98,30.48),(101.6,30.48),(101.6,33.02),(104.14,33.02),(109.22,33.02),(111.76,33.02))
wire((109.22,33.02),(109.22,38.1),(111.76,38.1));junction(109.22,33.02)
wire((104.14,33.02),(104.14,39.37));junction(104.14,33.02)
wire((104.14,46.99),(104.14,53.34),(105.41,53.34));junction(105.41,53.34)
wire((83.82,45.72),(93.98,45.72),(93.98,55.88));clone('#PWR102','#PWR220',93.98,55.88)
src.append([S('no_connect'),[S('at'),93.98,40.64],[S('uuid'),uid()]])
# USB preferred input and MODE; SYS is the alternate input.
wire((35.56,17.78),(48.26,17.78),(62.23,17.78),(83.82,17.78),(83.82,25.4))
wire((62.23,17.78),(62.23,30.48),(73.66,30.48));junction(62.23,17.78)
wire((35.56,58.42),(60.96,58.42),(60.96,40.64),(66.04,40.64),(73.66,40.64))
# Local input decoupling; copies retain the selected 1uF/10V capacitor MPN.
clone('C122','C124',35.56,30.48);wire((35.56,17.78),(35.56,26.67));junction(35.56,17.78)
wire((35.56,34.29),(35.56,38.1));clone('#PWR102','#PWR221',35.56,38.1)
clone('C122','C125',66.04,46.99);wire((66.04,40.64),(66.04,43.18));junction(66.04,40.64)
wire((66.04,50.8),(66.04,55.88));clone('#PWR102','#PWR222',66.04,55.88)
# Two standard resistor symbols from the project; selections remain explicitly open.
rdef=copy.deepcopy(one(load(open(ROOT/'DesktopSpeaker-kicad/kicad-library/schematic/PD_R.kicad_sym')),'symbol'));rdef[1]='PD_R:PD_R';libs.append(rdef)
for ref,value,y in [('R124','180k',22.86),('R125','100k',43.18)]:
 a=[S('symbol'),[S('lib_id'),'PD_R:PD_R'],at(48.26,y),[S('unit'),1],[S('exclude_from_sim'),S('no')],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),uid()]]
 for name,val,pos,hide in [('Reference',ref,(53.34,y-1.27),False),('Value',value,(53.34,y+1.27),False),('Footprint','DesktopSpeaker:PD_R_0603',(48.26,y),True)]:a.append([S('property'),name,val,at(*pos),eff(hide,'left')])
 for n in ['1','2']:a.append([S('pin'),n,[S('uuid'),uid()]])
 a.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),pathid,[S('reference'),ref],[S('unit'),1]]]]);src.append(a)
wire((48.26,17.78),(48.26,19.05));junction(48.26,17.78)
wire((48.26,26.67),(48.26,33.02),(48.26,39.37));wire((48.26,33.02),(73.66,33.02));junction(48.26,33.02)
wire((48.26,46.99),(48.26,49.53));clone('#PWR102','#PWR223',48.26,49.53)
for a in src:
 if k(a)=='symbol' and prop(a,'Reference')[2].startswith('#PWR'):
  e=one(prop(a,'Reference'),'effects')
  if not any(k(v)=='hide' for v in e):e.append([S('hide'),S('yes')])
src.append([S('text'),'USB-priority logic supply; PR1 nominal 2.8 V.\nSwitchover/BOR and effective capacitance need qualification.',at(35.56,180.34),[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),uid()]])
out=ROOT/'ai-files/candidates/Fuel_Gauge_Power.kicad_sch';out.write_text('('+dumps(src[0])+'\n'+'\n'.join(dumps(a) for a in src[1:])+')\n');print(out)
