from pathlib import Path
import sys,copy,uuid,json
sys.path.insert(0,'ai-files/vendor')
import sexpdata as sx
S=sx.Symbol
def k(a):return str(a[0]) if isinstance(a,list) and a else ''
def one(a,n):return next(z for z in a if k(z)==n)
def props(a):return {z[1]:z for z in a if k(z)=='property'}
def uid(a):
 for z in a:
  if k(z)=='uuid':z[1]=str(uuid.uuid4())
  elif isinstance(z,list):uid(z)
def wire(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]]
def move(a,x,y):
 at=one(a,'at');dx=x-at[1];dy=y-at[2];at[1:3]=[x,y]
 for p in props(a).values():
  at=one(p,'at');at[1]+=dx;at[2]+=dy
p=Path('DesktopSpeaker-kicad/USB_PD.kicad_sch');original=p.read_text();s=sx.loads(original)
refs={props(a)['Reference'][2]:a for a in s if k(a)=='symbol'}
assert 'U19' not in refs
Path('ai-files/backups/USB_PD-before-vdd-ldo.kicad_sch').write_text(original)
# Remove the isolated three-capacitor block wiring and its center junction only.
s=[a for a in s if not (k(a)=='wire' and all(219.7<=z[1]<=265.44 and 195.57<=z[2]<=214.64 for z in one(a,'pts')[1:])) and not(k(a)=='junction' and one(a,'at')[1:3]==[242.57,195.58])]
move(refs['C5'],298.45,205.74);move(refs['#PWR12'],298.45,214.63)
move(refs['C6'],231.14,205.74);move(refs['#PWR13'],231.14,214.63)
for a in s:
 if k(a)=='label' and a[1]=='USB_VBUS' and one(a,'at')[1:3]==[181.61,157.48]:a[1]='PD_VDD_5V'
# New functional LDO cache and instance.
lib=sx.loads(Path('DesktopSpeaker-kicad/kicad-library/schematic/TPS7B8450QWDRBRQ1.kicad_sym').read_text())
cache=copy.deepcopy(next(a for a in lib if k(a)=='symbol'));cache[1]='TPS7B8450QWDRBRQ1:TPS7B8450QWDRBRQ1';one(s,'lib_symbols').append(cache)
inst=copy.deepcopy(refs['U18']);uid(inst);one(inst,'lib_id')[1]=cache[1];one(inst,'at')[1:]=[250.19,195.58,0]
inst=[a for a in inst if k(a) not in ['property','pin']]
for f in cache:
 if k(f)=='property':
  f=copy.deepcopy(f);at=one(f,'at');at[1]+=250.19;at[2]=195.58-at[2]
  if f[1]=='Reference':f[2]='U19'
  inst.append(f)
for group in cache:
 if k(group)=='symbol':
  for pin in group:
   if k(pin)=='pin':inst.append([S('pin'),one(pin,'number')[1],[S('uuid'),str(uuid.uuid4())]])
for project in one(inst,'instances')[1:]:
 for path in project[2:]:one(path,'reference')[1]='U19'
ps=props(inst);ps['Reference'][2]='U19'
inst.append([S('property'),'LCSC Part','C3751394',[S('at'),250.19,195.58,0],[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('hide'),S('yes')]]])
s.append(inst)
# Raw input + EN, output/C5, explicit ground. New endpoints on established50milgrid.
segments=[((219.71,201.93),(219.71,195.58)),((219.71,195.58),(231.14,195.58)),((231.14,195.58),(231.14,201.93)),((231.14,195.58),(237.49,195.58)),((237.49,195.58),(237.49,190.5)),((237.49,195.58),(237.49,200.66)),((262.89,187.96),(298.45,187.96)),((298.45,187.96),(298.45,201.93)),((219.71,209.55),(219.71,214.63)),((231.14,209.55),(231.14,214.63)),((298.45,209.55),(298.45,214.63)),((245.11,210.82),(255.27,210.82)),((255.27,210.82),(262.89,210.82)),((262.89,210.82),(262.89,213.36))]
s.extend(wire(a,b) for a,b in segments)
# New grounds cloned from existing proper ground symbol.
g=copy.deepcopy(refs['#PWR13']);uid(g);move(g,262.89,213.36);props(g)['Reference'][2]='#PWR191'
for project in one(g,'instances')[1:]:
 for path in project[2:]:one(path,'reference')[1]='#PWR191'
one(props(g)['Value'],'effects').append([S('hide'),S('yes')]);s.append(g)
for x,y in [(231.14,195.58),(237.49,195.58),(255.27,210.82)]:s.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]])
s.append([S('label'),'PD_VDD_5V',[S('at'),298.45,187.96,0],[S('effects'),[S('font'),[S('size'),1,1]],[S('justify'),S('left'),S('bottom')]],[S('uuid'),str(uuid.uuid4())]])
for a in s:
 if k(a)=='text' and a[1]=='LOCAL REGULATOR AND VDD DECOUPLING':a[1]='RAW-VBUS LDO / PD VDD; C5 EFFECTIVE-CAP REVIEW OPEN';one(a,'at')[1:3]=[200.66,227.33]
p.write_text('('+sx.dumps(s[0])+'\n'+'\n'.join(sx.dumps(a) for a in s[1:])+')\n')
t=Path('DesktopSpeaker-kicad/sym-lib-table');v=t.read_text();assert 'name "TPS7B8450QWDRBRQ1"' not in v;t.write_text(v.rstrip()[:-1]+'  (lib (name "TPS7B8450QWDRBRQ1") (type "KiCad") (uri "${KIPRJMOD}/kicad-library/schematic/TPS7B8450QWDRBRQ1.kicad_sym") (options "") (descr "Raw USB PD VDD LDO"))\n)\n')
print('Added U19 raw USB ->5V PD supply; C5 reused; C2/C6 remain raw.')
