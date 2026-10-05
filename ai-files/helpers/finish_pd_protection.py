from pathlib import Path
import sys,copy,shutil
sys.path.insert(0,'ai-files/vendor');import sexpdata as sx
S=sx.Symbol
root=Path('DesktopSpeaker-kicad'); lib=root/'kicad-library'; sch=root/'USB_PD.kicad_sch';x=sx.loads(sch.read_text())
def key(a):return str(a[0]) if isinstance(a,list) and a else ''
def sub(a,n):return next(z for z in a if key(z)==n)
def props(a):return {q[1]:q for q in a if key(q)=='property'}
# Correct inherited supplier metadata.
for a in x:
 if key(a)=='symbol' and props(a).get('Reference',[0,0,''])[2]=='D6':props(a)['Manufacturer'][2]='Texas Instruments'
# Recognizable unidirectional zener/TVS graphics; exact old pin coordinates stay unchanged.
path=next(Path('/home/chithi/.local/share/flatpak/runtime').glob('org.kicad.KiCad.Library.Symbols/x86_64/beta/*/files/symbols/Device.kicad_sym'))
dev=sx.loads(path.read_text());std=next(a for a in dev[1:] if key(a)=='symbol' and a[1]=='D_Zener');graphics=copy.deepcopy(next(a for a in std if key(a)=='symbol' and a[1].endswith('_0_1'))[2:])
def rotate(a):
 if isinstance(a,list):
  if key(a)=='xy':a[1],a[2]=a[2],-a[1]
  for q in a:rotate(q)
for q in graphics:rotate(q)
for name in ['BZT52C12-7-F','SMA6J10A']:
 p=lib/'schematic'/(name+'.kicad_sym');d=sx.loads(p.read_text());symbol=next(a for a in d if key(a)=='symbol')
 for target in [symbol,next(a for a in sub(x,'lib_symbols')[1:] if a[1]==name+':'+name)]:
  unit=next(a for a in target if key(a)=='symbol' and a[1].endswith('_0_1'));unit[2:]=copy.deepcopy(graphics)
  for k in ['pin_names','pin_numbers']:
   target[:]=[a for a in target if key(a)!=k];target.insert(2,[S(k),[S('hide'),S('yes')]])
 p.write_text(sx.dumps(d).replace(') (',')\n  (')+'\n')
# Hide cramped TVS2200 pin names; numbers remain to show native stacks/pad 7.
name='TVS2200DRVR';p=lib/'schematic'/(name+'.kicad_sym');d=sx.loads(p.read_text());symbol=next(a for a in d if key(a)=='symbol')
for target in [symbol,next(a for a in sub(x,'lib_symbols')[1:] if a[1]==name+':'+name)]:
 target.insert(2,[S('pin_names'),[S('hide'),S('yes')]])
 for unit in target:
  if key(unit)=='symbol':
   for a in unit:
    if key(a)=='pin':sub(sub(sub(a,'number'),'effects'),'font')[1][1:]=[.8,.8]
p.write_text(sx.dumps(d).replace(') (',')\n  (')+'\n')
# Compact overlap cleanup: move R180 upward and local C180 near input rail.
for ref,dy in [('R180',-11.43),('C180',-15.24)]:
 a=next(z for z in x if key(z)=='symbol' and props(z).get('Reference',[0,0,''])[2]==ref);sub(a,'at')[2]+=dy
 for q in props(a).values():sub(q,'at')[2]+=dy
for a in x:
 if key(a)=='wire':
  pts=sub(a,'pts')
  for p in pts[1:]:
   if p[1]==307.34 and p[2] in [66.04,73.66]:p[2]-=11.43
   if p[1]==293.37 and p[2] in [57.15,64.77]:p[2]-=15.24
# Delete isolated dot left by old output routing; actual wire junctions retained.
x[:]=[a for a in x if not(key(a)=='junction' and sub(a,'at')[1:]==[350.52,39.37])]
sch.write_text(sx.dumps(x).replace(') (',')\n  (')+'\n')
# TI PWP0016A land example: 0.65mm pitch, 1.5x0.45 lands, 5.8mm row separation, 3.3mm EP aperture.
p=lib/'footprint'/'TPS26600PWPR.kicad_mod';f=sx.loads(p.read_text());sub(f,'descr')[1]='TI TPS26600 PWP0016A 4.4x5 mm, land pattern per datasheet'
for a in list(f):
 if key(a)=='pad':
  if a[1]=='':f.remove(a)
  elif a[1]=='17':sub(a,'size')[1:]=[3.3,3.3];sub(a,'layers').append('F.Paste')
  else:
   sub(a,'at')[1]= -2.9 if int(a[1])<=8 else 2.9;sub(a,'size')[1:]=[1.5,.45]
# Installed matching body model; its full EP3.4x5mm library variant may have a different exposed metal shape.
model=next(Path('/home/chithi/.local/share/flatpak/runtime').glob('org.kicad.KiCad.Library.Packages3D/x86_64/beta/*/files/3dmodels/Package_SO.3dshapes/HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm.step'))
shutil.copy2(model,lib/'3d'/'TPS26600PWPR.step')
f.append([S('model'),'${KIPRJMOD}/kicad-library/3d/TPS26600PWPR.step',[S('offset'),[S('xyz'),0,0,0]],[S('scale'),[S('xyz'),1,1,1]],[S('rotate'),[S('xyz'),0,0,0]]])
p.write_text(sx.dumps(f).replace(') (',')\n  (')+'\n')
