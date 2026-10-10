"""flatpak: route_r6a_dogbone.py IN OUT : move router vias whose drill sits inside an SMD pad (not EP, not the v10d reservation vias) to a legal dogbone spot.
Inner/B.Cu tracks ending at the old via are extended to the new via; an F.Cu stub joins pad and via."""
import sys, math, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
base = pcbnew.LoadBoard('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6a-base.kicad_pcb')
keep = {(round(t.GetX() / MM, 3), round(t.GetY() / MM, 3)) for t in base.Tracks() if t.GetClass() == 'PCB_VIA'}
EP = {('U6', '33'), ('U7', '33'), ('U25', '21')}
LN = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
def pad_hit(v):
    for f in b.GetFootprints():
        if not f.GetBoundingBox().Contains(v.GetPosition()): continue
        for p in f.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.IsOnLayer(pcbnew.F_Cu) or (f.GetReference(), str(p.GetNumber())) in EP: continue
            if p.GetEffectiveShape(pcbnew.F_Cu).Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), int(v.GetDrill() / 2)), 0): return p
    return None
moved, failed = [], []
for v in list(b.Tracks()):
    if v.GetClass() != 'PCB_VIA': continue
    P = (round(v.GetX() / MM, 3), round(v.GetY() / MM, 3))
    if P in keep: continue
    p = pad_hit(v)
    if p is None: continue
    n = str(v.GetNetname()); d, dr = v.GetWidth(pcbnew.F_Cu) / MM, v.GetDrill() / MM
    R = v.GetWidth(pcbnew.F_Cu) / 2
    def near(pt): return math.hypot(pt.x - v.GetX(), pt.y - v.GetY()) <= R + 1000
    inner = [t for t in b.Tracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and t.GetLayer() != pcbnew.F_Cu
             and t.GetEffectiveShape().Collide(v.GetEffectiveShape(t.GetLayer()), 0)]
    ends = {}
    for t in inner:
        e = t.GetStart() if math.hypot(t.GetStart().x - v.GetX(), t.GetStart().y - v.GetY()) < math.hypot(t.GetEnd().x - v.GetX(), t.GetEnd().y - v.GetY()) else t.GetEnd()
        ends.setdefault(LN[t.GetLayer()], []).append(((e.x / MM, e.y / MM), t.GetWidth() / MM))
    b.Remove(v)
    done = False
    for r in (0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0):
        for k in range(24):
            a = 2 * math.pi * k / 24; Q = (P[0] + r * math.cos(a), P[1] + r * math.sin(a))
            lays = {LN[t.GetLayer()] for t in inner}
            if not all(track_legal(b, n, e, Q, w, L) for L in ends for e, w in ends[L]): continue
            wst = {'POWER_HI': 0.5, 'PVDD': 0.5, 'PWR_5V': 0.4}.get(ncls(n), 0.3)
            if not track_legal(b, n, (p.GetX() / MM, p.GetY() / MM), Q, wst, 'F'): continue
            nv = place_via(b, n, Q[0], Q[1], d, dr)
            if nv is None: continue
            for L in ends:
                for e, w in ends[L]: trk(b, n, L, [e, Q], w)
            trk(b, n, 'F', [(p.GetX() / MM, p.GetY() / MM), Q], wst)
            moved.append((n, P, (round(Q[0], 2), round(Q[1], 2)))); done = True; break
        if done: break
    if not done:
        b.Add(v); failed.append((n, P, p.GetParentFootprint().GetReference() + '.' + str(p.GetNumber())))
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
print('moved', len(moved), 'failed', len(failed)); [print(' FAIL', x) for x in failed]
