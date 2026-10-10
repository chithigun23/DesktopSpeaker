"""flatpak: route_r6l_netcmp.py REF OUT : items (vias, tracks, arcs, zones) present in both boards (same uuid) whose net differs; pad nets per
footprint; counts of items only in one board. Guards against KiCad's net propagation onto floating vias during scripted edits."""
import sys, pcbnew
def g(f):
    b = pcbnew.LoadBoard(f); d = {}
    for t in b.GetTracks(): d[t.m_Uuid.AsString()] = (t.GetClass(), str(t.GetNetname()), t.GetX() / 1e6, t.GetY() / 1e6)
    for z in b.Zones(): d[z.m_Uuid.AsString()] = ('ZONE ' + z.GetZoneName(), str(z.GetNetname()), 0, 0)
    p = {}
    for f_ in b.GetFootprints():
        for q in f_.Pads(): p[(f_.GetReference(), q.GetNumber())] = str(q.GetNetname())
    return d, p
(a, pa), (b, pb) = g(sys.argv[1]), g(sys.argv[2])
bad = [(u, a[u], b[u][1]) for u in a if u in b and a[u][1] != b[u][1]]
for x in bad: print('NETCHANGE', x)
print('net changes', len(bad), 'pad net changes', sum(1 for k in pa if pb.get(k) != pa[k]), 'only ref', sum(1 for u in a if u not in b), 'only out', sum(1 for u in b if u not in a))
