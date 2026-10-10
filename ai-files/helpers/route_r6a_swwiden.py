"""flatpak: route_r6a_swwiden.py IN OUT : U14/U15 (TPS63802) switch-node tracks: keep a 0.25 mm pin neck of 0.7 mm, widen the rest to the widest legal width"""
import sys, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
NETS = ['Net-(U14-L1)', 'Net-(U14-L2)', 'Net-(U15-L1)', 'Net-(U15-L2)', 'Net-(U6-OUT_A-)', 'Net-(U6-OUT_B-)', 'Net-(U7-OUT_A+)', 'Net-(U7-OUT_B+)', 'Net-(U6-OUT_A+)', 'Net-(U6-OUT_B+)']
ics = [fp(b, r) for r in ('U14', 'U15', 'U6', 'U7')]
def in_ic_pad(pt):
    for f in ics:
        for p in f.Pads():
            if p.GetEffectiveShape(pcbnew.F_Cu).Collide(V(*pt), 0): return True
    return False
log = []
for t in list(b.Tracks()):
    n = str(t.GetNetname())
    if t.GetClass() == 'PCB_VIA' or n not in NETS or t.GetLayer() != pcbnew.F_Cu or t.GetWidth() > 0.45 * MM: continue
    a = (t.GetStart().x / MM, t.GetStart().y / MM); c = (t.GetEnd().x / MM, t.GetEnd().y / MM)
    L = math.hypot(c[0] - a[0], c[1] - a[1])
    if L < 1.2: continue
    if in_ic_pad(c) and not in_ic_pad(a): a, c = c, a
    w0 = t.GetWidth() / MM
    k = 0.7 / L; m = (a[0] + (c[0] - a[0]) * k, a[1] + (c[1] - a[1]) * k) if in_ic_pad(a) else a
    b.Remove(t)
    best = None
    for w in (1.2, 1.0, 0.8, 0.6, 0.5, 0.4):
        if track_legal(b, n, m, c, w): best = w; break
    if best is None: b.Add(t); continue
    if m != a: trk(b, n, 'F', [a, m], w0)
    trk(b, n, 'F', [m, c], best); log.append((n, round(L, 2), w0, best))
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
for x in log: print(x)
