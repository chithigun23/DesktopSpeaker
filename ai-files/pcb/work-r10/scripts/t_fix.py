import sys; sys.path.insert(0,'scripts')
from r10lib import *
import os; B=Board(os.environ.get('GEO','B9-H0.geo.json'),os.environ.get('DUMP','r9.json'),os.environ.get('NETS','B9-H0.nets.txt'),'base.kicad_dru')
chk=[]
for a in sys.argv[1:]:
    if '=' in a:
        r,v=a.split('='); B.pose[r]=tuple(map(float,v.split(',')))
    else: chk.append(a)
for r in [r for r in B.pose if B.pose[r]!=B.pose0[r]]:
    print(r, B.pose0[r],'->',B.pose[r], B.legal(r))
for b in B.exits(chk): print('  noexit',b)
