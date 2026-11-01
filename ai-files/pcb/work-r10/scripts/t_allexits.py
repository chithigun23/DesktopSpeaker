import sys, os; sys.path.insert(0,'scripts')
from r10lib import *
B=Board(sys.argv[1],sys.argv[2],sys.argv[3],'base.kicad_dru')
bad=B.exits(list(B.pads)); print(len(bad))
for b in bad: print(b)
