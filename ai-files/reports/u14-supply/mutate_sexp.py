from pathlib import Path
import sys,copy,uuid
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
P=Path('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch'); B=Path('DesktopSpeaker-kicad/Bluetooth_Power.kicad_sch')
d=loads(P.read_text()); bd=loads(B.read_text())
def key(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,k):return next(v for v in x if key(v)==k)
def props(x):return {q[1]:q for q in x if key(q)=='property'}
def ref(x):return props(x).get('Reference',[None,None,None])[2]
def uid():return str(uuid.uuid4())
# cache symbol directly from normalized existing sibling sheet
lib=sub(d,'lib_symbols'); blib=sub(bd,'lib_symbols')
cache=copy.deepcopy(next(x for x in blib if key(x)=='symbol' and str(x[1])=='TPS63802DLAR:TPS63802DLAR'))
lib[:]=[x for x in lib if not(key(x)=='symbol' and str(x[1])=='TPS61023DRLT:TPS61023DRLT')]+[cache]
u=next(x for x in d if key(x)=='symbol' and ref(x)=='U14')
sub(u,'lib_id')[1]='TPS63802DLAR:TPS63802DLAR'
props(u)['Value'][2]='TPS63802DLAR';props(u)['Footprint'][2]='DesktopSpeaker:TPS63802DLAR';props(u)['Datasheet'][2]='../ai-files/datasheets/TPS63802.pdf'
# Metadata is left for coordinator normalization; replace stale pin UUID records only.
u[:]=[x for x in u if key(x)!='pin']+[[S('pin'),str(i),[S('uuid'),uid()]] for i in range(1,11)]
props(u)['Reference'][3][1:3]=[139.7,126.0];props(u)['Value'][3][1:3]=[139.7,128.54]
# Keep instance transform and UUID. Update existing passive values; placements retained.
l=next(x for x in d if key(x)=='symbol' and ref(x)=='L2');sub(l,'at')[3]=90;props(l)['Value'][2]='0.47uH'
next(x for x in d if key(x)=='symbol' and ref(x)=='R140');props(next(x for x in d if key(x)=='symbol' and ref(x)=='R140'))['Value'][2]='787k 1%'
next(x for x in d if key(x)=='symbol' and ref(x)=='R141');props(next(x for x in d if key(x)=='symbol' and ref(x)=='R141'))['Value'][2]='91k 1%'
# Remove former boost switch/gnd/output/feedback connections; retain rails and divider.
remove={'9e37d1f1-9561-4344-b8ce-5a7bbc4cd80a','f0564805-d238-4620-89fe-cb9d3eeb7dca','78fd7653-cd68-4d26-9c14-e8e0c57e8c89'}
d[:]=[x for x in d if not(key(x)=='wire' and sub(x,'uuid')[1] in remove)]
oldg=next(x for x in d if key(x)=='symbol' and ref(x)=='#PWR143');d.remove(oldg)
def wire(a,b):return [S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]]
def ground(ref,x,y):
 g=copy.deepcopy(oldg);sub(g,'at')[1:]=[x,y,0];props(g)['Reference'][2]=ref;props(g)['Reference'][3][1:3]=[x,y+3.81];props(g)['Value'][3][1:3]=[x,y+5.08];sub(g,'uuid')[1]=uid();sub(g,'pin')[2][1]=uid();sub(sub(g,'instances')[1][2],'reference')[1]=ref;return g
# L2 is now horizontal; converter inductor connects L1/L2 switch nodes.
wires=[
wire((101.6,88.9),(124.46,88.9)),wire((124.46,88.9),(124.46,91.44)),
wire((124.46,83.82),(127,83.82)),wire((127,83.82),(127,76.2)),wire((127,76.2),(135.89,76.2)),
wire((139.7,66.04),(135.89,66.04)),wire((135.89,66.04),(135.89,76.2)),
wire((143.51,76.2),(160.02,76.2)),wire((160.02,76.2),(160.02,83.82)),wire((160.02,83.82),(154.94,83.82)),
wire((154.94,91.44),(165.1,91.44)),wire((165.1,91.44),(165.1,88.9)),wire((165.1,88.9),(168.91,88.9)),
wire((124.46,96.52),(121.92,96.52)),wire((121.92,96.52),(121.92,99.06)),wire((121.92,99.06),(88.9,99.06)),
wire((154.94,96.52),(160.02,96.52)),wire((160.02,96.52),(160.02,99.06)),wire((160.02,99.06),(165.1,99.06)),
wire((137.16,111.76),(137.16,115.57)),wire((142.24,111.76),(142.24,115.57)),wire((137.16,115.57),(142.24,115.57)),wire((139.7,115.57),(139.7,118.11))]
d.extend(wires)
d.append([S('no_connect'),[S('at'),154.94,101.6],[S('uuid'),uid()]])
d.append([S('label'),'SYS_RAW',[S('at'),124.46,101.6,0],[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S('left')]],[S('uuid'),uid()]])
d.append(ground('#PWR143',139.7,118.11))
for t in d:
 if key(t)=='text':
  if 'R140/R141' in t[1]:t[1]='U14 forced PWM while enabled; feedback-divider DC bounds remain within PCM2902C supply limits. Ripple and startup transient require qualification.'
  elif 'EN low' in t[1]:t[1]='EN low = true input/output disconnect; MODE tied to SYS_RAW selects forced PWM while enabled.'
P.write_text(dumps(d)+'\n')
