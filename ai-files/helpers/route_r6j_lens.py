"""flatpak: route_r6j_lens.py BOARD [NETSUFFIX,..] : (R6j) per-net track length, vias, B and In2 length; no filter = nets >= 100 mm"""
import sys,pcbnew,collections
b=pcbnew.LoadBoard(sys.argv[1]);MM=1e6
L=collections.defaultdict(float);V=collections.Counter();Lb=collections.defaultdict(float);L2=collections.defaultdict(float)
for t in b.GetTracks():
    n=str(t.GetNetname())
    if t.GetClass()=='PCB_VIA': V[n]+=1
    else:
        L[n]+=t.GetLength()/MM
        if t.GetLayer()==pcbnew.B_Cu: Lb[n]+=t.GetLength()/MM
        if t.GetLayer()==pcbnew.In2_Cu: L2[n]+=t.GetLength()/MM
nets=sys.argv[2].split(',') if len(sys.argv)>2 and sys.argv[2] else None
for n in sorted(L,key=lambda k:-L[k]):
    if nets and not any(n.endswith(x) for x in nets): continue
    if not nets and L[n]<100: continue
    print('%-36s %7.1f mm  vias %2d  B %6.1f  In2 %6.1f'%(n,L[n],V[n],Lb[n],L2[n]))
