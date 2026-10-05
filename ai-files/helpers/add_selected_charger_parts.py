from pathlib import Path
import copy,sys,uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from sexpdata import load,dumps,Symbol
S=Symbol
p=Path(__file__).resolve().parents[2]/'DesktopSpeaker-kicad/Battery_Charger.kicad_sch'
d=load(p.open())
def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def allof(x,n):return [t for t in x if k(t)==n]
def one(x,n):return allof(x,n)[0]
def ref(x):return next(t[2] for t in allof(x,'property') if t[1]=='Reference')
def meta(o,name,value):
 old=next((t for t in allof(o,'property') if t[1]==name),None)
 if old:old[2]=value
 else:o.append([S('property'),name,value,[S('at'),*one(o,'at')[1:3],0],[S('effects'),[S('font'),[S('size'),1,1]],[S('hide'),S('yes')]]])
def clone(o,newref,dx):
 o=copy.deepcopy(o);one(o,'uuid')[1]=str(uuid.uuid4());one(o,'at')[1]=round(one(o,'at')[1]+dx,4)
 for t in allof(o,'property'):
  one(t,'at')[1]=round(one(t,'at')[1]+dx,4)
  if t[1]=='Reference':t[2]=newref
 for t in allof(o,'pin'):one(t,'uuid')[1]=str(uuid.uuid4())
 for proj in one(o,'instances')[1:]:
  for path in allof(proj,'path'):one(path,'reference')[1]=newref
 d.append(o);return o
objs={ref(t):t for t in allof(d,'symbol')}
for t in allof(objs['L1'],'property'):
 if t[1]=='Footprint':t[2]='DesktopSpeaker:Bourns_SRN6045TA-2R2Y'
meta(objs['L1'],'MPN','SRN6045TA-2R2Y');meta(objs['L1'],'Manufacturer','Bourns');meta(objs['L1'],'LCSC Part','C1332316')
if 'C107' not in objs:
 objs['C107']=clone(objs['C105'],'C107',25.4)
 def wire(a,b):d.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]])
 wire((360.68,121.92),(360.68,139.7));wire((360.68,147.32),(360.68,154.94))
 d.append([S('junction'),[S('at'),360.68,121.92],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]])
 clone(next(t for t in allof(d,'symbol') if one(t,'lib_id')[1]=='power:GND' and one(t,'at')[1:3]==[335.28,154.94]),'#PWR299',25.4)
for r in ('C104','C105','C107'):
 meta(objs[r],'Manufacturer','Murata');meta(objs[r],'MPN','GRM21BZ71A226ME15L');meta(objs[r],'LCSC Part','C907991')
p.write_text(dumps(d)+'\n')
print('L1 selected; C107 added; SYS capacitor MPNs assigned.')
