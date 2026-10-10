"""flatpak: route_r6c_comps.py BOARD NET... : print pads of each unconnected fragment"""
import sys
sys.path.insert(0,'/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_p2_core import comps_of
class C: pass
c=C(); c.b=pcbnew.LoadBoard(sys.argv[1])
for n in sys.argv[2:]:
    cs=comps_of(c,n); print(n,len(cs))
    for g in cs: print('  ',[ (x[1].GetParentFootprint().GetReference()+'.'+str(x[1].GetNumber())) for x in g if x[0]=='pad'][:12], 'items',len(g))
