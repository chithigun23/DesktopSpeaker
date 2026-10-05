"""One-shot authorized USB power update; preserve existing physical connectivity."""
from pathlib import Path
import copy,sys,uuid
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
p=Path('DesktopSpeaker-kicad/USB_PD.kicad_sch');original=p.read_text();d=loads(original)
def key(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,k):return next(v for v in x if key(v)==k)
def props(x):return {v[1]:v for v in x if key(v)=='property'}
def ref(x):return props(x).get('Reference',[None,None,None])[2]
def move(x,xy):
 a=sub(x,'at');dx,dy=xy[0]-a[1],xy[1]-a[2];a[1:3]=xy
 for q in x:
  if key(q)=='property':b=sub(q,'at');b[1]=round(b[1]+dx,6);b[2]=round(b[2]+dy,6)
def wire(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]]
if any(key(n)=='symbol' and ref(n)=='C181' for n in d):raise RuntimeError('Already applied; do not rerun')
Path('ai-files/backups').mkdir(exist_ok=True)
Path('ai-files/backups/USB_PD-before-ramp.kicad_sch').write_text(original)
c=copy.deepcopy(next(n for n in d if key(n)=='symbol' and ref(n)=='C180'));move(c,[365.76,105.41]);sub(c,'uuid')[1]=str(uuid.uuid4())
for q in c:
 if key(q)=='pin':sub(q,'uuid')[1]=str(uuid.uuid4())
pr=props(c);pr['Reference'][2]='C181';pr['Value'][2]='22nF C0G 50V';pr['Footprint'][2]='DesktopSpeaker:PD_C_0603';pr['MPN'][2]='TBD'
if 'Datasheet' in pr:pr['Datasheet'][2]=''
inst=sub(c,'instances')[1][2];sub(inst,'reference')[1]='C181';d.append(c)
d[:]=[n for n in d if not (key(n)=='no_connect' and sub(n,'at')[1:3]==[359.41,88.9])]
d.extend([wire((359.41,88.9),(365.76,88.9)),wire((365.76,88.9),(365.76,101.6)),wire((365.76,109.22),(365.76,114.3))])
# Shorten the ILIM ground tail to keep the new capacitor text clear.
g=next(n for n in d if key(n)=='symbol' and str(sub(n,'lib_id')[1])=='power:GND' and sub(n,'at')[1:3]==[381.0,101.6]);move(g,[381.0,92.71])
for n in d:
 if key(n)=='wire' and sub(n,'pts')[1][1:]==[381.0,88.9] and sub(n,'pts')[2][1:]==[381.0,101.6]:sub(n,'pts')[2][1:]=[381.0,92.71]
ground=copy.deepcopy(g);move(ground,[365.76,114.3]);sub(ground,'uuid')[1]=str(uuid.uuid4());props(ground)['Reference'][2]='#PWR181';sub(sub(ground,'instances')[1][2],'reference')[1]='#PWR181'
for q in ground:
 if key(q)=='pin':sub(q,'uuid')[1]=str(uuid.uuid4())
d.append(ground)
# Preserve displayed R4 value and physical footprint; add hidden sourcing data.
r4=next(n for n in d if key(n)=='symbol' and ref(n)=='R4');rp=props(r4)
data={'MPN':'RC1206FR-073K3L','Manufacturer':'YAGEO','LCSC':'C137292','Datasheet':'https://yageogroup.com/component-documentation/download/specsheet/RC1206FR-073K3L'}
for name,value in data.items():
 if name in rp:rp[name][2]=value
 else:r4.append([S('property'),name,value,[S('at'),*sub(r4,'at')[1:]],[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('hide'),S('yes')]]])
p.write_text(dumps(d)+'\n');print('Added C181; R4 metadata selected; R182 ground tail compacted.')
