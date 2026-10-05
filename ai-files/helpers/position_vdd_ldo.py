from pathlib import Path
import sys,uuid
sys.path.insert(0,'ai-files/vendor');import sexpdata as sx
S=sx.Symbol
def k(a):return str(a[0]) if isinstance(a,list) and a else ''
def one(a,n):return next(z for z in a if k(z)==n)
def props(a):return {z[1]:z for z in a if k(z)=='property'}
def move(a,x,y):
 at=one(a,'at');dx=x-at[1];dy=y-at[2];at[1:3]=[x,y]
 for p in props(a).values():
  t=one(p,'at');t[1]+=dx;t[2]+=dy
p=Path('DesktopSpeaker-kicad/USB_PD.kicad_sch');s=sx.loads(p.read_text())
u19=next(a for a in s if k(a)=='symbol' and props(a)['Reference'][2]=='U19')
assert one(u19,'at')[1:3]==[250.19,195.58], 'One-shot placement already applied or user moved U19'
old=[((219.71,201.93),(219.71,195.58)),((219.71,195.58),(231.14,195.58)),((231.14,195.58),(231.14,201.93)),((231.14,195.58),(237.49,195.58)),((237.49,195.58),(237.49,190.5)),((237.49,195.58),(237.49,200.66)),((262.89,187.96),(298.45,187.96)),((298.45,187.96),(298.45,201.93)),((219.71,209.55),(219.71,214.63)),((231.14,209.55),(231.14,214.63)),((298.45,209.55),(298.45,214.63)),((245.11,210.82),(255.27,210.82)),((255.27,210.82),(262.89,210.82)),((262.89,210.82),(262.89,213.36))]
s=[a for a in s if not(k(a)=='wire' and tuple(tuple(z[1:]) for z in one(a,'pts')[1:]) in old) and not(k(a)=='junction' and tuple(one(a,'at')[1:3]) in [(231.14,195.58),(237.49,195.58),(255.27,210.82)])]
positions={'C2':(88.9,226.06),'C6':(119.38,226.06),'C5':(199.39,226.06),'#PWR11':(88.9,234.95),'#PWR13':(119.38,234.95),'#PWR12':(199.39,234.95),'U19':(151.13,226.06),'#PWR191':(163.83,243.84)}
for a in s:
 if k(a)=='symbol':
  ref=props(a)['Reference'][2]
  if ref in positions:move(a,*positions[ref])
 elif k(a)=='label':
  if one(a,'at')[1:3]==[219.71,195.58]:one(a,'at')[1:3]=[88.9,215.9]
  if one(a,'at')[1:3]==[298.45,187.96]:one(a,'at')[1:3]=[199.39,218.44]
 elif k(a)=='text':
  if a[1].startswith('RAW-VBUS LDO'):one(a,'at')[1:3]=[88.9,257.81]
  if a[1].startswith('Program and read'):one(a,'at')[2]=264.16
  if a[1].startswith('Hardware cutoff'):one(a,'at')[2]=271.78
new=[((88.9,222.25),(88.9,215.9)),((88.9,215.9),(119.38,215.9)),((119.38,215.9),(119.38,222.25)),((119.38,215.9),(135.89,215.9)),((135.89,215.9),(135.89,220.98)),((135.89,220.98),(138.43,220.98)),((135.89,220.98),(135.89,231.14)),((135.89,231.14),(138.43,231.14)),((163.83,218.44),(199.39,218.44)),((199.39,218.44),(199.39,222.25)),((88.9,229.87),(88.9,234.95)),((119.38,229.87),(119.38,234.95)),((199.39,229.87),(199.39,234.95)),((146.05,241.3),(156.21,241.3)),((156.21,241.3),(163.83,241.3)),((163.83,241.3),(163.83,243.84))]
for a,b in new:s.append([S('wire'),[S('pts'),[S('xy'),*a],[S('xy'),*b]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]])
for x,y in [(119.38,215.9),(135.89,220.98),(156.21,241.3)]:s.append([S('junction'),[S('at'),x,y],[S('diameter'),0],[S('color'),0,0,0,0],[S('uuid'),str(uuid.uuid4())]])
p.write_text('('+sx.dumps(s[0])+'\n'+'\n'.join(sx.dumps(a) for a in s[1:])+')\n')
