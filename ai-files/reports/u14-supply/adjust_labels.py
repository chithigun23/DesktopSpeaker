from pathlib import Path
import sys
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
p=Path('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch');d=loads(p.read_text())
def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,n):return next(q for q in x if k(q)==n)
lab=next(x for x in d if k(x)=='label' and x[1]=='SYS_RAW');sub(lab,'at')[1]=101.6
w=next(x for x in d if k(x)=='wire' and sub(x,'uuid')[1] not in ('9e37d1f1-9561-4344-b8ce-5a7bbc4cd80a',) and tuple((float(v[1]),float(v[2])) for v in sub(x,'pts')[1:])==((114.3,101.6),(124.46,101.6)))
sub(w,'pts')[1][1]=101.6
p.write_text(dumps(d)+'\n')
