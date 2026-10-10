"""flatpak: route_r6l_union.py BOARD [NAME_SUBSTR] : per net and layer, the union of all same-net zone fills (incl. the R6l *_G companion pours)
with the net's tracks/pads/vias: number of separate copper pieces and the zone-only piece count. Island continuity check when a pour is
split over several zone objects."""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); flt = sys.argv[2] if len(sys.argv) > 2 else '_G'
LN = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
want = set()
for z in b.Zones():
    if not z.GetIsRuleArea() and flt in z.GetZoneName():
        for L in LN:
            if z.IsOnLayer(L): want.add((str(z.GetNetname()), L))
for n, L in sorted(want):
    zs = pcbnew.SHAPE_POLY_SET(); names = []
    for z in b.Zones():
        if not z.GetIsRuleArea() and str(z.GetNetname()) == n and z.IsOnLayer(L) and z.HasFilledPolysForLayer(L): zs.Append(z.GetFilledPolysList(L)); names.append(z.GetZoneName())
    zs.Simplify()
    al = pcbnew.SHAPE_POLY_SET(zs)
    for t in b.GetTracks():
        if str(t.GetNetname()) == n and t.IsOnLayer(L): t.TransformShapeToPolygon(al, L, 0, 5000, pcbnew.ERROR_INSIDE)
    for f in b.GetFootprints():
        for p in f.Pads():
            if str(p.GetNetname()) == n and p.IsOnLayer(L): p.TransformShapeToPolygon(al, L, 0, 5000, pcbnew.ERROR_INSIDE)
    al.Simplify()
    print('%-30s %s zones %-60s zone-union pieces %d  copper pieces %d  area %.1f' % (n[-30:], LN[L], ','.join(sorted(names))[:60], zs.OutlineCount(), al.OutlineCount(), zs.Area() / MM / MM))
