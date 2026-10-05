import re,uuid,copy
P='DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch'; Q='DesktopSpeaker-kicad/Bluetooth_Power.kicad_sch'
class A(str):
 def __new__(cls,v,q=False):o=str.__new__(cls,v);o.q=q;return o
def parsefile(p):
 s=open(p).read(); toks=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s);i=0
 def parse():
  nonlocal i
  t=toks[i];i+=1
  if t=='(':
   a=[]
   while toks[i]!=')':a.append(parse())
   i+=1;return a
  if t.startswith('"'):return A(t[1:-1].replace('\\"','"').replace('\\\\','\\'),True)
  return A(t,False)
 return s,parse()
def h(x):return x[0] if isinstance(x,list) and x else None
def sx(x):
 if isinstance(x,list):return '('+' '.join(map(sx,x))+')'
 if isinstance(x,A):
  if not x.q:return str(x)
  return '"'+str(x).replace('\\','\\\\').replace('"','\\"')+'"'
 if isinstance(x,str) and re.fullmatch(r'[-+]?\d+(?:\.\d+)?',str(x)):return str(x)
 return '"'+str(x).replace('\\','\\\\').replace('"','\\"')+'"'
def a(x):return A(str(x),False)
def uid():return str(uuid.uuid4())
s,root=parsefile(P); _,bt=parsefile(Q)
lib=next(x for x in root if h(x)=='lib_symbols'); blib=next(x for x in bt if h(x)=='lib_symbols')
newlib=copy.deepcopy(next(x for x in blib if h(x)=='symbol' and x[1]=='TPS63802DLAR:TPS63802DLAR'))
lib[:]=[x for x in lib if not(h(x)=='symbol' and x[1]=='TPS61023DRLT:TPS61023DRLT')]+[newlib]
path='/feda53ed-537d-4f88-9436-c6075776255b/31d56ed5-71f9-4c5a-b590-b5d5119f00f9'
def prop(sym,n):return next(x for x in sym if h(x)=='property' and x[1]==n)
def setprop(sym,n,val):prop(sym,n)[2]=val
u=next(x for x in root if h(x)=='symbol' and prop(x,'Reference')[2]=='U14')
next(x for x in u if h(x)=='lib_id')[1]='TPS63802DLAR:TPS63802DLAR'
setprop(u,'Value','TPS63802DLAR'); setprop(u,'Footprint','DesktopSpeaker:TPS63802DLAR')
# Keep legacy hidden purchase fields for parent metadata normalization; replace datasheet with correct official file.
setprop(u,'Datasheet','../ai-files/datasheets/TPS63802.pdf')
for x in u:
 if h(x)=='pin':x[2][1]=uid()
# Existing passives
l=next(x for x in root if h(x)=='symbol' and prop(x,'Reference')[2]=='L2')
next(x for x in l if h(x)=='at')[3]=a('90'); prop(l,'Value')[2]='0.47uH'
r140=next(x for x in root if h(x)=='symbol' and prop(x,'Reference')[2]=='R140');prop(r140,'Value')[2]='787k 1%'
r141=next(x for x in root if h(x)=='symbol' and prop(x,'Reference')[2]=='R141');prop(r141,'Value')[2]='91k 1%'
# Center U14 identifiers below expanded package.
prop(u,'Reference')[3][1:3]=[A('139.7',False),A('120.65',False)];prop(u,'Value')[3][1:3]=[A('139.7',False),A('123.19',False)]
# Wire helper
def wire(a,b):return ['wire',['pts',['xy',a.__class__ and A(str(a[0]),False),A(str(a[1]),False)],['xy',A(str(b[0]),False),A(str(b[1]),False)]],['stroke',['width','0'],['type','default']],['uuid',uid()]]
def junc(at):return ['junction',['at',str(at[0]),str(at[1])],['diameter','0'],['color','0','0','0','0'],['uuid',uid()]]
# Delete old converter-specific wiring and old converter ground; retain input rail and output/divider rails.
remove={'9e37d1f1-9561-4344-b8ce-5a7bbc4cd80a','f0564805-d238-4620-89fe-cb9d3eeb7dca','78fd7653-cd68-4d26-9c14-e8e0c57e8c89'}
root[:]=[x for x in root if not (h(x)=='wire' and any(h(q)=='uuid' and q[1] in remove for q in x))]
# Replace old ground symbol #PWR143 with two downward GND symbols for AGND/GND.
oldg=next(x for x in root if h(x)=='symbol' and prop(x,'Reference')[2]=='#PWR143')
def ground(ref,x,y):
 g=copy.deepcopy(oldg); at=next(q for q in g if h(q)=='at');at[1:]=[A(str(x),False),A(str(y),False),A('0',False)];prop(g,'Reference')[2]=ref;prop(g,'Reference')[3][1:3]=[A(str(x),False),A(str(y+3.81),False)];prop(g,'Value')[3][1:3]=[A(str(x),False),A(str(y+5.08),False)];next(q for q in g if h(q)=='uuid')[1]=uid();next(q for q in g if h(q)=='pin')[2][1]=uid(); inst=next(q for q in g if h(q)=='instances');inst[1][2][2][1]=ref;return g
# TPS63802 pins at original IC origin: VIN(124.46,91.44), EN(124.46,96.52), MODE(124.46,101.6), L1(124.46,83.82), VOUT(154.94,91.44), FB(154.94,96.52), PG(154.94,101.6), L2(154.94,83.82), AGND/GND bottom(142.24/137.16,111.76).
# Input rail to VIN; preserve SYS_RAW hierarchical label on common input rail.
neww=[wire((101.6,88.9),(124.46,88.9)),wire((124.46,88.9),(124.46,91.44)),
      wire((124.46,83.82),(124.46,76.2)),wire((124.46,76.2),(135.89,76.2)),
      wire((143.51,76.2),(160.02,76.2)),wire((160.02,76.2),(160.02,83.82)),wire((160.02,83.82),(154.94,83.82)),
      wire((154.94,91.44),(165.1,91.44)),wire((165.1,91.44),(165.1,88.9)),wire((165.1,88.9),(168.91,88.9)),
      wire((124.46,96.52),(121.92,96.52)),wire((121.92,96.52),(121.92,99.06)),wire((121.92,99.06),(88.9,99.06)),
      wire((154.94,96.52),(160.02,96.52)),wire((160.02,96.52),(160.02,99.06)),wire((160.02,99.06),(165.1,99.06)),
      wire((137.16,111.76),(137.16,115.57)),wire((142.24,111.76),(142.24,115.57))]
# Existing divider branch y99.06 ends at165.1; our extension joins there.
root.extend(neww)
# replace pin5 with intentional NC
root.append(['no_connect',['at',A('154.94',False),A('101.6',False)],['uuid',uid()]])
# MODE SYS_RAW tie via local label; input rail already has hierarchical SYS_RAW.
root.append(['label','SYS_RAW',['at',A('124.46',False),A('101.6',False),A('0',False)],['effects',['font',['size',A('1',False),A('1',False)]],['justify','left']],['uuid',uid()]])
root.extend([ground('#PWR143',137.16,115.57),ground('#PWR147',142.24,115.57)])
# Update old explanatory text to current topology and qualifications.
for t in root:
 if h(t)=='text':
  if 'R140/R141' in t[1]:t[1]='U14 forced PWM when enabled; resistor-ratio DC bound is within PCM2902C range. Ripple and startup transient need qualification.'
  elif 'EN low' in t[1]:t[1]='EN low = true input/output disconnect; MODE tied to SYS_RAW selects forced PWM while enabled.'
# Save with original expression ordering but normalized spacing.
open(P,'w').write(sx(root)+'\n')
