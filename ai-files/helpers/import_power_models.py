from pathlib import Path
import shutil,sys,re
sys.path.insert(0,'ai-files/vendor'); import sexpdata as sx
root=Path('DesktopSpeaker-kicad'); lib=root/'kicad-library'
for src,name in [('/home/chithi/Downloads/ul_TPS63802DLAR/DLA0010A.stp','TPS63802DLAR.step'),('/home/chithi/Downloads/XFL4015.STEP','Coilcraft_XFL4015-471MEC.step')]: shutil.copy2(src,lib/'3d'/name)
for name,rotate,offset in [('TPS63802DLAR',0,0),('Coilcraft_XFL4015-471MEC',90,.1)]:
 s=(Path('ai-files/candidates')/(name+'.kicad_mod')).read_text()
 if name=='TPS63802DLAR':
  s=s.replace('(at -1.2 ', '(at -0.9 ').replace('(at 1.2 ', '(at 0.75 ').replace('(at 0.95 0)', '(at 0.55 0)').replace('(roundrect_rratio 0.2)', '(roundrect_rratio 0.2)')
  # Pad 8 uses TI's two 0.55 x 0.25 mm stencil windows, 83% coverage.
  s=s.replace('(pad "8" smd roundrect (at 0.55 0) (size 1.3 0.25) (layers "F.Cu" "F.Paste" "F.Mask")', '(pad "8" smd roundrect (at 0.55 0) (size 1.3 0.25) (layers "F.Cu" "F.Mask")')
  s=s.rstrip()[:-1]+'\n  (pad "" smd roundrect (at 0.175 0) (size 0.55 0.25) (layers "F.Paste") (roundrect_rratio 0.2))\n  (pad "" smd roundrect (at 0.925 0) (size 0.55 0.25) (layers "F.Paste") (roundrect_rratio 0.2))\n)\n'
  # 0.05 mm corner radius throughout.
  s=s.replace('(roundrect_rratio 0.15)', '(roundrect_rratio 0.2)').replace('(roundrect_rratio 0.1)', '(roundrect_rratio 0.2)')
 s=s.rstrip()[:-1]+f'  (model "${{KIPRJMOD}}/kicad-library/3d/{name}.step"\n    (offset (xyz 0 0 {offset}))\n    (scale (xyz 1 1 1))\n    (rotate (xyz {rotate} 0 0)))\n)\n'
 (lib/'footprint'/(name+'.kicad_mod')).write_text(s)
def walk(x):
 if isinstance(x,list):
  if len(x)>2 and str(x[0])=='property' and x[1]=='Footprint' and x[2]=='':
   return
  for y in x: yield from walk(y)
def props(x): return {a[1]:a for a in x if isinstance(a,list) and len(a)>2 and str(a[0])=='property'}
def update(x):
 if not isinstance(x,list):return
 if x and str(x[0])=='symbol':
  p=props(x)
  ref=p.get('Reference',[None,None,''])[2]; val=p.get('Value',[None,None,''])[2]
  if val=='TPS63802DLAR' or ref=='U15': p['Footprint'][2]='DesktopSpeaker:TPS63802DLAR'
  elif ref=='L3': p['Footprint'][2]='DesktopSpeaker:Coilcraft_XFL4015-471MEC'
 for a in x:update(a)
for path in [root/'Bluetooth_Power.kicad_sch',lib/'schematic'/'TPS63802DLAR.kicad_sym']:
 data=sx.loads(path.read_text());update(data)
 path.write_text(sx.dumps(data).replace(') (', ')\n  (')+'\n')
