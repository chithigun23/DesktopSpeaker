"""flatpak: route_r6p_cucmp.py A.kicad_pcb B.kicad_pcb : compare copper: tracks/arcs/vias (geometry, width, layer, net), non-teardrop zones
(outline, layers, net, priority, clearance, filled area per layer), footprints (ref, pos, rot, layer, pad nets/positions), board-text/graphics count.
Footprint field differences are reported separately (count of footprints with changed fields)."""
import sys, pcbnew
MM = 1e6
def key(b):
    T = set(); V = set(); Z = {}; F = {}; FLD = {}
    for t in b.GetTracks():
        n = str(t.GetNetname())
        if t.GetClass() == 'PCB_VIA': V.add((t.GetX(), t.GetY(), t.GetWidth(pcbnew.F_Cu), t.GetDrill(), n))
        else:
            a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            T.add((min(a, c), max(a, c), t.GetWidth(), t.GetLayer(), n, t.GetClass()))
    for z in b.Zones():
        if z.IsTeardropArea(): continue
        o = z.Outline(); pts = tuple((o.CVertex(i).x, o.CVertex(i).y) for i in range(o.TotalVertices()))
        ar = tuple(round(z.GetFilledPolysList(l).Area() / MM / MM, 2) if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l) else 0 for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu))
        Z[(z.GetZoneName(), str(z.GetNetname()), pts)] = (z.GetAssignedPriority(), z.GetLocalClearance(), z.GetIsRuleArea(), ar)
    for f in b.GetFootprints():
        r = f.GetReference() + '@%d,%d' % (f.GetX(), f.GetY())
        F[r] = (f.GetOrientationDegrees(), f.GetLayer(), f.GetFPIDAsString(), tuple(sorted((p.GetNumber(), p.GetX(), p.GetY(), str(p.GetNetname())) for p in f.Pads())))
        FLD[r] = tuple(sorted((fl.GetName(), fl.GetText()) for fl in f.GetFields()))
    return T, V, Z, F, FLD
a = pcbnew.LoadBoard(sys.argv[1]); c = pcbnew.LoadBoard(sys.argv[2])
A, B = key(a), key(c)
for nm, i in (('tracks', 0), ('vias', 1)):
    print(nm, len(A[i]), len(B[i]), 'only A', len(A[i] - B[i]), 'only B', len(B[i] - A[i]))
    for x in list(A[i] - B[i])[:5]: print('  -', x)
    for x in list(B[i] - A[i])[:5]: print('  +', x)
za, zb = A[2], B[2]
print('zones', len(za), len(zb), 'outline/net diff', len(set(za) ^ set(zb)))
dz = 0
for k in set(za) & set(zb):
    if za[k][:3] != zb[k][:3]: dz += 1; print('  zone prop', k[0], k[1], za[k][:3], zb[k][:3])
    elif any(abs(p - q) > 0.05 for p, q in zip(za[k][3], zb[k][3])): dz += 1; print('  zone fill area', k[0], k[1], za[k][3], zb[k][3])
print('zone differences', dz)
fa, fb = A[3], B[3]
print('footprints', len(fa), len(fb), 'set diff', len(set(fa) ^ set(fb)), 'geom/pad diff', sum(1 for k in set(fa) & set(fb) if fa[k] != fb[k]))
for k in list(set(fa) ^ set(fb))[:5]: print('  ', k)
for k in [k for k in set(fa) & set(fb) if fa[k] != fb[k]][:5]: print('  geom', k, fa[k][:3], fb[k][:3])
print('footprints with changed fields', sum(1 for k in set(A[4]) & set(B[4]) if A[4][k] != B[4][k]))
