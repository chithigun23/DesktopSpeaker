import sys; sys.path.insert(0,'scripts')
from r10lib import *
import time; t=time.time()
B=Board('B9-H0.geo.json','r9.json','B9-H0.nets.txt','base.kicad_dru')
print('load',time.time()-t)
refs=sys.argv[1:]
t=time.time(); bad=B.exits(refs); print('exits',time.time()-t)
for b in bad: print(b)
for r in refs:
    ok,why=B.legal(r); print(r,ok,why[:5])
