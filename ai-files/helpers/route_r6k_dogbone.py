"""flatpak: route_r6k_dogbone.py IN OUT X Y [maxd] : move the via at (X,Y), whose centre lies in a same-net SMD pad, beside the pad (dogbone).
Candidates on rings around the via (0.1 mm steps up to maxd, 15 deg steps), kept only if the ring clears every pad by >= 0.05 mm,
the via is legal (route_r6a_lib.place_via, R6a clearances), the F stub pad-centre -> via and every re-pointed In2/B track end
(old via -> new via) are legal (route_r6a_lib.track_legal, F pours of GND ignored). Picks the shortest. Prints the move."""
import sys, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import place_via, track_legal, trk, refill, V, LAY
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); X, Y = float(sys.argv[3]), float(sys.argv[4]); maxd = float(sys.argv[5]) if len(sys.argv) > 5 else 1.6
v0 = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and abs(t.GetX() / MM - X) < 0.02 and abs(t.GetY() / MM - Y) < 0.02][0]
n = str(v0.GetNetname()); d = v0.GetWidth(pcbnew.F_Cu) / MM; dr = v0.GetDrillValue() / MM; r = d / 2
pad = [p for f in b.GetFootprints() for p in f.Pads() if str(p.GetNetname()) == n and p.IsOnLayer(pcbnew.F_Cu) and p.GetEffectivePolygon(pcbnew.F_Cu).Contains(v0.GetPosition())][0]
pc = (pad.GetX() / MM, pad.GetY() / MM)
attach = []   # (track, which end) on In2/B ending inside the via ring
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA' or str(t.GetNetname()) != n or t.GetLayer() == pcbnew.F_Cu: continue
    for e, q in (('s', t.GetStart()), ('e', t.GetEnd())):
        if math.hypot(q.x / MM - X, q.y / MM - Y) <= r + t.GetWidth() / MM / 2: attach.append((t, e, (q.x / MM, q.y / MM), t.GetLayer(), t.GetWidth() / MM))
b.Remove(v0)
pads = [p for f in b.GetFootprints() for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu) and abs(p.GetX() / MM - X) < 5 and abs(p.GetY() / MM - Y) < 5]
LN = {pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B', pcbnew.In1_Cu: '1'}
# GND F zones are ignored by the stub check: temporarily hide them from track_legal by netname test
best = None; REJ = {'ext': 0, 'stub': 0, 'via': 0}
for k in range(1, int(maxd / 0.05) + 1):
    dist = k * 0.05
    for a in range(0, 360, 10):
        qx, qy = X + dist * math.cos(math.radians(a)), Y + dist * math.sin(math.radians(a))
        if any(p.GetEffectivePolygon(pcbnew.F_Cu).Collide(V(qx, qy), int((r + 0.05) * MM)) for p in pads): continue
        ok = True
        for t, e, q, L, w in attach:
            if not track_legal(b, n, q, (qx, qy), w, LN[L]): ok = False; break
        if not ok: REJ['ext'] += 1; continue
        # F stub from the pad edge region (pad centre) to the via
        sw = min(0.25, pad.GetSizeX() / MM, pad.GetSizeY() / MM)
        gz = [z for z in b.Zones() if not z.GetIsRuleArea() and str(z.GetNetname()) == 'GND' and z.IsOnLayer(pcbnew.F_Cu)]
        for z in gz: z.SetNet(b.FindNet(n))   # treat GND F pours as own-net for the check only
        okf = track_legal(b, n, pc, (qx, qy), sw, 'F')
        for z in gz: z.SetNet(b.FindNet('GND'))
        if not okf: REJ['stub'] += 1; continue
        vv = place_via(b, n, qx, qy, d, dr, lock=False)
        if vv is None: REJ['via'] += 1; continue
        best = (dist, qx, qy, sw, vv); break
    if best: break
if best is None:
    print('NO dogbone for', n, X, Y, REJ, 'attach', [(LN[a[3]], a[2]) for a in attach]); b.Add(v0); sys.exit(1)
dist, qx, qy, sw, vv = best
for t, e, q, L, w in attach: trk(b, n, LN[L], [q, (qx, qy)], w, lock=False)
trk(b, n, 'F', [pc, (qx, qy)], sw, lock=False)
print('dogbone', n, (X, Y), '->', (round(qx, 3), round(qy, 3)), 'dist %.2f' % dist, 'pad', pad.GetParentFootprint().GetReference() + '.' + str(pad.GetNumber()), 'stub w', sw, 'reattached', len(attach))
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
