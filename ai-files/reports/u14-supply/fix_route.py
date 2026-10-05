from pathlib import Path
import sys
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
p=Path('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch');d=loads(p.read_text())
def k(x):return str(x[0]) if isinstance(x,list) and x else ''
def sub(x,n):return next(q for q in x if k(q)==n)
def props(x):return {q[1]:q for q in x if k(q)=='property'}
# Place the existing inductor between actual switch pin endpoints.
l=next(x for x in d if k(x)=='symbol' and props(x).get('Reference',[None,None,None])[2]=='L2')
sub(l,'at')[2]=76.2
# Remove the stale SYS_RAW-to-inductor branch, leaving the routed L1 and L2 branches.
remove_pairs={((139.7,43.18),(139.7,66.04)),((139.7,66.04),(135.89,66.04)),((135.89,66.04),(135.89,76.2))}
def pair(w):
 pts=sub(w,'pts');return tuple((float(x[1]),float(x[2])) for x in pts[1:])
d[:]=[x for x in d if not(k(x)=='wire' and pair(x) in remove_pairs)]
# Move SYS_RAW local label away from the MODE pin name; add a short direct lead.
lab=next(x for x in d if k(x)=='label' and x[1]=='SYS_RAW');sub(lab,'at')[1:3]=[114.3,101.6]
# Connect label to MODE pin.
d.append([S('wire'),[S('pts'),[S('xy'),114.3,101.6],[S('xy'),124.46,101.6]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'), __import__('uuid').uuid4().__str__()]])
p.write_text(dumps(d)+'\n')
