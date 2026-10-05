#!/usr/bin/env python3
"""Integrate charger and gauge children without rewriting unrelated root objects."""
from pathlib import Path
import sys, uuid, re, shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from sexpdata import loads, dumps, Symbol
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch'
backup=ROOT/'ai-files/backups/DesktopSpeaker-before-power-subsystems.kicad_sch'
if not backup.exists():shutil.copy2(p,backup)
s=backup.read_text()
def kind(x):return str(x[0]) if isinstance(x,list) and x else ''
def spans(text):
 depth=0; quoted=False; escaped=False; start=0
 for i,c in enumerate(text):
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':
   if depth==1:start=i
   depth+=1
  elif c==')':
   depth-=1
   if depth==1:yield start,i+1
remove=[]
old_ports=set(); old_stubs=set()
for a,b in spans(s):
 e=loads(s[a:b])
 if kind(e)=='sheet':
  for pin in e:
   if kind(pin)=='pin':
    loc=next(v for v in pin if kind(v)=='at');old_ports.add(tuple(loc[1:3]))
  remove.append((a,b))
for a,b in spans(s):
 e=loads(s[a:b])
 if kind(e)=='symbol':
  props={x[1]:x[2] for x in e if kind(x)=='property'}
  if props.get('Reference') in ('U4','U5'):remove.append((a,b))
 if kind(e)=='wire':
  pts=next(x for x in e if kind(x)=='pts')
  if any(tuple(x[1:]) in old_ports for x in pts[1:]):
   old_stubs.update(tuple(x[1:]) for x in pts[1:]);remove.append((a,b))
for a,b in spans(s):
 e=loads(s[a:b])
 if kind(e)=='label':
  at=next(v for v in e if kind(v)=='at')
  if tuple(at[1:3]) in old_stubs:remove.append((a,b))
for a,b in sorted(set(remove),reverse=True):s=s[:a]+s[b:]
# Only move the two unconnected audio blocks that obstruct the new ordered row.
updates=[]
for a,b in spans(s):
 e=loads(s[a:b])
 if kind(e)!='symbol':continue
 props={x[1]:x[2] for x in e if kind(x)=='property'}
 new={'U10':(60.96,160.02),'U6':(353.06,187.96)}.get(props.get('Reference'))
 if new:
  pos=next(v for v in e if kind(v)=='at');dx=new[0]-pos[1];dy=new[1]-pos[2]
  def move(x):
   if isinstance(x,list):
    if kind(x)=='at':x[1]=round(x[1]+dx,4);x[2]=round(x[2]+dy,4)
    else:
     for y in x:move(y)
  move(e);updates.append((a,b,dumps(e)))
for a,b,new in reversed(updates):s=s[:a]+new+s[b:]
def uid():return str(uuid.uuid4())
objects=[]; pins={}
def sheet(name,id,x,y,w,h,page,left,right):
 rows=[f'(sheet (at {x} {y}) (size {w} {h}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{id}")', f'(property "Sheet name" "{name}" (at {x} {y-1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))', f'(property "Sheet file" "{name}.kicad_sch" (at {x} {y+h} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
 for side,ps in [('left',left),('right',right)]:
  for n,typ,dy in ps:
   px=x if side=='left' else x+w; py=round(y+dy,4); angle=180 if side=='left' else 0
   pins[(name,n)]=(px,py)
   rows.append(f'(pin "{n}" {typ} (at {px} {py} {angle}) (effects (font (size 1 1)) (justify {side} bottom)) (uuid "{uid()}"))')
 rows.append(f'(instances (project "DesktopSpeaker" (path "/feda53ed-537d-4f88-9436-c6075776255b" (page "{page}")))) )')
 objects.append('\n'.join(rows))
sheet('USB_PD','f38b7023-3d53-43ea-b3db-e2c826d87b35',100.33,139.7,45.72,48.26,2,[('USB_VBUS','input',7.62),('USB_CC1','input',15.24),('USB_CC2','input',22.86),('GND','input',30.48)],[('VBUS_PD','output',7.62)])
sheet('Battery_Charger','a7066d55-4393-49f1-9dcb-c2e9f1db9549',166.37,139.7,53.34,66.04,3,[('VBUS_PD','input',7.62),('CHG_ENABLE','input',25.4),('CHG_VIO_3V0','input',55.88)],[('SYS_RAW','output',7.62),('BAT_PACK','bidirectional',17.78),('CHG_SCL','bidirectional',30.48),('CHG_SDA','bidirectional',40.64),('CHG_INT','output',55.88)])
sheet('Fuel_Gauge_Power','9c37a727-9991-421a-8f6e-77dd39bb53fa',240.03,139.7,50.8,66.04,4,[('SYS_RAW','input',7.62),('BAT_PACK','input',17.78),('GAUGE_SCL','input',30.48),('GAUGE_SDA','bidirectional',40.64)],[('3V_AO','output',7.62),('GAUGE_ALRT_N','output',55.88)])
def wire(a,b):objects.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{uid()}"))')
def route(*pts):
 for a,b in zip(pts,pts[1:]):wire(a,b)
def label(n,p,align='left'):objects.append(f'(label "{n}" (at {p[0]} {p[1]} 0) (effects (font (size 1 1)) (justify {align} bottom)) (uuid "{uid()}"))')
def stub(n,sheetname,port,side):
 p=pins[(sheetname,port)];q=(round(p[0]+(-5.08 if side=='left' else 5.08),4),p[1]);wire(p,q);label(n,q,'right' if side=='left' else 'left')
# The port order follows the power path and the shared control bus.
for sa,pa,sb,pb in [('USB_PD','VBUS_PD','Battery_Charger','VBUS_PD'),('Battery_Charger','SYS_RAW','Fuel_Gauge_Power','SYS_RAW'),('Battery_Charger','BAT_PACK','Fuel_Gauge_Power','BAT_PACK'),('Battery_Charger','CHG_SCL','Fuel_Gauge_Power','GAUGE_SCL'),('Battery_Charger','CHG_SDA','Fuel_Gauge_Power','GAUGE_SDA')]:
 wire(pins[(sa,pa)],pins[(sb,pb)])
label('CTRL_SCL',(229.87,170.18),'right')
label('CTRL_SDA',(229.87,180.34),'right')
for port in ('USB_VBUS','USB_CC1','USB_CC2'):stub(port,'USB_PD',port,'left')
for port,n in [('CHG_ENABLE','CHG_ENABLE'),('CHG_VIO_3V0','3V_AO')]:stub(n,'Battery_Charger',port,'left')
stub('CHG_INT','Battery_Charger','CHG_INT','right')
for port,n in [('3V_AO','3V_AO'),('GAUGE_ALRT_N','GAUGE_ALRT_N')]:stub(n,'Fuel_Gauge_Power',port,'right')
# Explicit root ground symbol; retain the same global GND connectivity.
pd=loads((ROOT/'DesktopSpeaker-kicad/USB_PD.kicad_sch').read_text())
def child(x,name):return next(v for v in x if kind(v)==name)
glib=next(v for v in child(pd,'lib_symbols') if kind(v)=='symbol' and v[1]=='power:GND')
for a,b in spans(s):
 e=loads(s[a:b])
 if kind(e)=='lib_symbols':
  if not any(kind(v)=='symbol' and v[1]=='power:GND' for v in e):e.append(glib);s=s[:a]+dumps(e)+s[b:]
  break
gp=pins[('USB_PD','GND')];wire(gp,(95.25,170.18));wire((95.25,170.18),(95.25,175.26))
objects.append(f'(symbol (lib_id "power:GND") (at 95.25 175.26 0) (unit 1) (in_bom no) (on_board no) (uuid "{uid()}") (property "Reference" "#PWR301" (at 95.25 179.07 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" "GND" (at 95.25 180.34 0) (effects (font (size 1.27 1.27)))) (pin "1" (uuid "{uid()}")) (instances (project "DesktopSpeaker" (path "/feda53ed-537d-4f88-9436-c6075776255b" (reference "#PWR301") (unit 1)))))')
s=s.replace('USB PD connected; remaining blocks pending','USB PD, charger and gauge draft; MCU/audio pending')
s=s.rstrip();assert s.endswith(')');p.write_text(s[:-1]+'\n'+'\n'.join(objects)+'\n)\n')
print('Integrated charger/gauge hierarchy; unrelated root objects preserved.')
