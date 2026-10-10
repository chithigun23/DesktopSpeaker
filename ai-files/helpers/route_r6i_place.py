"""flatpak: route_r6i_place.py BOARD REF X0 Y0 X1 Y1 [IGNORE_NETS,..] [STEP=0.1] [CLR=0.5] [TARGETS pad=REF.PAD:w,...]
Free-spot finder for a 2-terminal part: tries positions on a grid and rotations 0/90/180/270; legal when its F courtyard
overlaps no other F courtyard and its pads keep CLR from foreign copper (tracks, vias, pads; nets in IGNORE are ignored,
as are the part's own old copper). Prints the 15 best by sum(w * distance(pad, target)) where TARGETS maps 'PADNUM>REF.PAD:w'."""
import sys, math, pcbnew
MM = 1e6
a = sys.argv; b = pcbnew.LoadBoard(a[1]); ref = a[2]; X0, Y0, X1, Y1 = map(float, a[3:7])
ign = set(a[7].split(',')) if len(a) > 7 and a[7] else set(); st = float(a[8]) if len(a) > 8 else 0.1; clr = float(a[9]) if len(a) > 9 else 0.5
tg = []
if len(a) > 10:
    for s in a[10].split(','):
        k, r = s.split('>'); rp, w = r.split(':'); R, P = rp.split('.')
        p = [q for q in b.FindFootprintByReference(R).Pads() if q.GetNumber() == P][0]; tg.append((k, p.GetX() / MM, p.GetY() / MM, float(w)))
f = b.FindFootprintByReference(ref)
others = [g for g in b.GetFootprints() if g.GetReference() != ref and g.GetLayer() == pcbnew.F_Cu]
cys = [(g.GetReference(), g.GetCourtyard(pcbnew.F_CrtYd)) for g in others]
box = pcbnew.BOX2I(pcbnew.VECTOR2I(int((X0 - 3) * MM), int((Y0 - 3) * MM)), pcbnew.VECTOR2I(int((X1 - X0 + 6) * MM), int((Y1 - Y0 + 6) * MM)))
near_t = [t for t in b.GetTracks() if box.Intersects(t.GetBoundingBox()) and str(t.GetNetname()) not in ign and (t.GetClass() == 'PCB_VIA' or t.GetLayer() == pcbnew.F_Cu)]
near_p = [p for g in others if box.Intersects(g.GetBoundingBox()) for p in g.Pads() if p.IsOnLayer(pcbnew.F_Cu) and str(p.GetNetname()) not in ign]
own = set(str(p.GetNetname()) for p in f.Pads())
res = []
x = X0
while x <= X1 + 1e-9:
    y = Y0
    while y <= Y1 + 1e-9:
        for rot in (0, 90, 180, 270):
            f.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))); f.SetOrientationDegrees(rot)
            cy = f.GetCourtyard(pcbnew.F_CrtYd)
            if any(c.Collide(cy) for r, c in cys if c.OutlineCount()): continue
            ok = True
            for p in f.Pads():
                sh = p.GetEffectiveShape(pcbnew.F_Cu); pn = str(p.GetNetname())
                for t in near_t:
                    if str(t.GetNetname()) == pn: continue
                    if t.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, int(clr * MM)): ok = False; break
                if not ok: break
                for q in near_p:
                    if str(q.GetNetname()) == pn: continue
                    if q.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, int(0.25 * MM)): ok = False; break
                if not ok: break
            if not ok: continue
            sc = 0.0
            for k, tx, ty, w in tg:
                p = [q for q in f.Pads() if q.GetNumber() == k][0]; sc += w * math.hypot(p.GetX() / MM - tx, p.GetY() / MM - ty)
            res.append((round(sc, 2), round(x, 2), round(y, 2), rot, [(p.GetNumber(), round(p.GetX() / MM, 2), round(p.GetY() / MM, 2)) for p in f.Pads()]))
        y += st
    x += st
res.sort()
for r in res[:15]: print(r)
print('legal', len(res))
