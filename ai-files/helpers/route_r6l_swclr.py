"""flatpak: route_r6l_swclr.py BOARD NET[,NET..] [x0 y0 x1 y1] : minimum copper clearance from each listed net (F/B: zone fills, tracks, pads, vias)
to every other net on the same layer, reported per other net with location, inside the optional box (default: whole net)."""
import sys, math, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); nets = sys.argv[2].split(',')
box = list(map(float, sys.argv[3:7])) if len(sys.argv) > 6 else None
LY = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, '2': pcbnew.In2_Cu}
def items_poly(L, pred):
    ps = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.IsOnLayer(L) and pred(str(z.GetNetname())) and z.HasFilledPolysForLayer(L): ps.Append(z.GetFilledPolysList(L))
    for t in b.GetTracks():
        if pred(str(t.GetNetname())) and t.IsOnLayer(L): t.TransformShapeToPolygon(ps, L, 0, 2000, pcbnew.ERROR_INSIDE)
    for f in b.GetFootprints():
        for p in f.Pads():
            if pred(str(p.GetNetname())) and p.IsOnLayer(L): p.TransformShapeToPolygon(ps, L, 0, 2000, pcbnew.ERROR_INSIDE)
    ps.Simplify(); return ps
for nn in nets:
    full = [str(k) for k in b.GetNetsByName().keys() if str(k) == nn or str(k).endswith('/' + nn)][0]
    for ln, L in LY.items():
        me = items_poly(L, lambda n: n == full)
        if me.OutlineCount() == 0: continue
        pts = []
        for k in range(me.OutlineCount()):
            for c in [me.Outline(k)] + [me.Hole(k, h) for h in range(me.HoleCount(k))]:
                for i in range(c.PointCount()):
                    a = c.CPoint(i); q = c.CPoint((i + 1) % c.PointCount()); L_ = math.hypot(q.x - a.x, q.y - a.y) / MM; n = max(1, int(L_ / 0.02))
                    for s in range(n): pts.append(((a.x + (q.x - a.x) * s / n) / MM, (a.y + (q.y - a.y) * s / n) / MM))
        if box: pts = [p for p in pts if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]]
        others = set()
        for t in b.GetTracks():
            if t.IsOnLayer(L): others.add(str(t.GetNetname()))
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.IsOnLayer(L): others.add(str(z.GetNetname()))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.IsOnLayer(L): others.add(str(p.GetNetname()))
        others.discard(full); others.discard('')
        res = []
        for o in others:
            op = items_poly(L, lambda n, o=o: n == o)
            if op.OutlineCount() == 0: continue
            bb = op.BBox(); best = (9e9, None)
            for x, y in pts:
                if x < bb.GetLeft() / MM - 1.2 or x > bb.GetRight() / MM + 1.2 or y < bb.GetTop() / MM - 1.2 or y > bb.GetBottom() / MM + 1.2: continue
                d = math.sqrt(op.SquaredDistance(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))) / MM
                if d < best[0]: best = (d, (round(x, 2), round(y, 2)))
            if best[0] < 1.2: res.append((round(best[0], 3), o, best[1]))
        for r in sorted(res): print(nn, ln, '%.3f' % r[0], r[1], r[2])
