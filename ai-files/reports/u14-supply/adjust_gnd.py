from pathlib import Path
import sys,uuid
sys.path.insert(0,'ai-files/vendor');from sexpdata import loads,dumps,Symbol as S
p=Path('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch');d=loads(p.read_text())
def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,n):return next(q for q in x if k(q)==n)
lab=next(x for x in d if k(x)=='global_label' and x[1]=='GND');sub(lab,'at')[1:3]=[149.86,115.57]
d.append([S('wire'),[S('pts'),[S('xy'),139.7,115.57],[S('xy'),149.86,115.57]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),str(uuid.uuid4())]])
p.write_text(dumps(d)+'\n')
