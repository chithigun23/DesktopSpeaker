"""One-shot root integration. Do not rerun after manual project edits."""
from pathlib import Path
import copy,sys,uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai-files/vendor'))
from sexpdata import Symbol,load,dumps
S=Symbol
p=ROOT/'DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch'
def k(v):return str(v[0]) if isinstance(v,list) and v else ''
def allof(v,n):return [t for t in v if k(t)==n]
def one(v,n):return allof(v,n)[0]
def uid():return str(uuid.uuid4())
def prop(o,name):return next(t for t in allof(o,'property') if t[1]==name)
def xy(a,b):return [S('xy'),a,b]
def at(a,b,ang=0):return [S('at'),a,b,ang]
def eff(j='left',size=1):return [S('effects'),[S('font'),[S('size'),size,size]],[S('justify'),S(j),S('bottom')]]
def move(o,dx,dy):
 a=one(o,'at');a[1]=round(a[1]+dx,4);a[2]=round(a[2]+dy,4)
 for v in allof(o,'property'):
  a=one(v,'at');a[1]=round(a[1]+dx,4);a[2]=round(a[2]+dy,4)
root=load(p.open())
if any(prop(v,'Sheet name')[2]=='Logic_Audio_Power' for v in allof(root,'sheet')):raise SystemExit('Already integrated; aborting one-shot helper.')
for name in ('Logic_Audio_Power','Bluetooth_Power'):
 if not (p.parent/(name+'.kicad_sch')).is_file():raise SystemExit('Missing child '+name)
(ROOT/'ai-files/backups/DesktopSpeaker-before-regulated-power.kicad_sch').write_bytes(p.read_bytes())
for o in allof(root,'symbol'):
 if prop(o,'Reference')[2]=='U7':move(o,353.06-one(o,'at')[1],132.08-one(o,'at')[2])
# Move USB-C connector with all of its wired stubs, without changing its nets.
for o in root:
 if k(o)=='symbol' and prop(o,'Reference')[2]=='J1':move(o,55.88-one(o,'at')[1],0)
 elif k(o)=='wire':
  pts=one(o,'pts')[1:]
  if all(190<=v[1]<=245 and 225<=v[2]<=283 for v in pts):
   for v in pts:v[1]=round(v[1]-162.69,4)
 elif k(o) in ('label','junction','no_connect'):
  a=one(o,'at')
  if 190<=a[1]<=245 and 225<=a[2]<=283:a[1]=round(a[1]-162.69,4)
def wire(a,b):root.append([S('wire'),[S('pts'),xy(*a),xy(*b)],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
def label(name,x,y,j='left'):root.append([S('label'),name,at(x,y),eff(j),[S('uuid'),uid()]])
def sheet(name,id,x,page,ports):
 y=224.79;w=53.34 if name=='Bluetooth_Power' else 50.8;h=43.18
 o=[S('sheet'),[S('at'),x,y],[S('size'),w,h],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('fill'),[S('color'),255,255,255,0]],[S('uuid'),id],
 [S('property'),'Sheet name',name,at(x,y-1.27),[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('justify'),S('left')]]],
 [S('property'),'Sheet file',name+'.kicad_sch',at(x,y+h),[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('hide'),S('yes')]]]]
 for n,t,side,py in ports:
  o.append([S('pin'),n,S(t),at(x if side=='left' else x+w,py,180 if side=='left' else 0),eff(side),[S('uuid'),uid()]])
 o.append([S('instances'),[S('project'),'DesktopSpeaker',[S('path'),'/feda53ed-537d-4f88-9436-c6075776255b',[S('page'),str(page)]]]])
 root.append(o)
sheet('Bluetooth_Power','f761c113-2c86-429a-8773-5f4b423ef275',166.37,5,[('SYS_RAW','input','left',232.41),('BT_PWR_EN','input','left',243.84),('BT_FORCE_PWM','input','left',254.0),('3V8_BT','output','right',259.08)])
sheet('Logic_Audio_Power','31d56ed5-71f9-4c5a-b590-b5d5119f00f9',240.03,6,[('SYS_RAW','input','left',232.41),('5V_LOGIC_EN','input','left',245.11),('5V_LOGIC','output','right',232.41)])
# Local rail branches above the lower sheets; one label per wired rail section.
wire((228.6,147.32),(228.6,134.62));label('SYS_RAW',228.6,134.62)
root.append([S('junction'),[S('at'),228.6,147.32],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),uid()]])
wire((151.13,214.63),(229.87,214.63));wire((151.13,214.63),(151.13,232.41));wire((151.13,232.41),(166.37,232.41));wire((229.87,214.63),(229.87,232.41));wire((229.87,232.41),(240.03,232.41));label('SYS_RAW',151.13,214.63)
for n,x,y,end,j in [('BT_PWR_EN',166.37,243.84,153.67,'right'),('BT_FORCE_PWM',166.37,254.0,153.67,'right'),('3V8_BT',219.71,259.08,224.79,'left'),('5V_LOGIC_EN',240.03,245.11,227.33,'right'),('5V_LOGIC',290.83,232.41,303.53,'left')]:
 wire((x,y),(end,y));label(n,end,y,j)
p.write_text('(kicad_sch\n'+'\n'.join(dumps(v) for v in root[1:])+'\n)\n')
print('Integrated regulated power children; moved U7/J1 clear.')
