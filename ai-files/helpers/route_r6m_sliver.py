"""flatpak: route_r6m_sliver.py BOARD [OUT.json] [OUTER_W=0.15] [INNER_W=0.12] [MIN_AREA=0.003]
Narrow-copper scan of every zone fill on every copper layer (R6m, reviewer B1).  Per net and layer the copper union
T = (all zone fills of the net) + (its tracks, pads, vias) is opened morphologically (deflate by W/2, inflate by W/2, round
corners); D = T - opening holds every feature narrower than W.  D pieces that overlap a zone fill by >= MIN_AREA mm2 are
reported with the zone(s) they belong to, size and an estimated width (2 * area / perimeter).  Pad/track-only residue
(sharp pad corners) is ignored because it does not touch a fill.  The same opening test is also run on each zone fill on
its own ('alone'; finds tongues lying flush against a same-net zone).  Also prints a zone table (name, net, layer, priority,
min thickness, fill pieces, area)."""
import sys, json, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
out = sys.argv[2] if len(sys.argv) > 2 else None
WO = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
WI = float(sys.argv[4]) if len(sys.argv) > 4 else 0.12
AMIN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.003
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: '1', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
RC = pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS; ERR = 2000
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
print('ZONES')
for z in sorted(zones, key=lambda z: (str(z.GetNetname()), z.GetZoneName())):
    for L in LN:
        if z.IsOnLayer(L):
            fp = z.GetFilledPolysList(L) if z.HasFilledPolysForLayer(L) else pcbnew.SHAPE_POLY_SET()
            print('  %-22s %-28s %s prio %2d minw %.3f clr %.3f pieces %3d area %8.2f' % (z.GetZoneName() or '-', str(z.GetNetname())[-28:], LN[L],
                  z.GetAssignedPriority(), z.GetMinThickness() / MM, z.GetLocalClearance().value_or(0) / MM if hasattr(z.GetLocalClearance(), 'value_or') else 0,
                  fp.OutlineCount(), fp.Area() / MM / MM))
res = []; alone = []
for L in LN:
    W = WO if L in (pcbnew.F_Cu, pcbnew.B_Cu) else WI; r = int(W / 2 * MM)
    nets = sorted(set(str(z.GetNetname()) for z in zones if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L)))
    for n in nets:
        zf = [(z.GetZoneName() or '-', z.GetFilledPolysList(L)) for z in zones if str(z.GetNetname()) == n and z.IsOnLayer(L) and z.HasFilledPolysForLayer(L)]
        T = pcbnew.SHAPE_POLY_SET()
        for _, p in zf: T.Append(p)
        for t in b.GetTracks():
            if str(t.GetNetname()) == n and t.IsOnLayer(L): t.TransformShapeToPolygon(T, L, 0, ERR, pcbnew.ERROR_INSIDE)
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) == n and p.IsOnLayer(L): p.TransformShapeToPolygon(T, L, 0, ERR, pcbnew.ERROR_INSIDE)
        T.Simplify()
        O = pcbnew.SHAPE_POLY_SET(T); O.Deflate(r, RC, ERR); O.Inflate(r, RC, ERR); O.Simplify()
        D = pcbnew.SHAPE_POLY_SET(T); D.BooleanSubtract(O); D.Simplify()
        for k in range(D.OutlineCount()):
            pc = pcbnew.SHAPE_POLY_SET(); pc.AddOutline(D.Outline(k))
            a = pc.Area() / MM / MM
            if a < AMIN: continue
            hit = []
            for nm, p in zf:
                q = pcbnew.SHAPE_POLY_SET(pc); q.BooleanIntersection(p)
                qa = q.Area() / MM / MM
                if qa >= AMIN: hit.append((nm, round(qa, 4)))
            if not hit: continue
            bb = pc.BBox(); per = D.Outline(k).Length() / MM
            res.append({'layer': LN[L], 'net': n, 'zones': hit, 'area': round(a, 4), 'est_w': round(2 * a / per, 3) if per else 0,
                        'bbox': [round(bb.GetX() / MM, 2), round(bb.GetY() / MM, 2), round(bb.GetRight() / MM, 2), round(bb.GetBottom() / MM, 2)]})
        # zone-alone test (each zone fill on its own, as a reviewer reading one zone's fill sees it; flush tongues on a
        # same-net neighbour show up here but merge into wider copper in the union above)
        for nm, p in zf:
            P = pcbnew.SHAPE_POLY_SET(p); P.Simplify()
            O = pcbnew.SHAPE_POLY_SET(P); O.Deflate(r, RC, ERR); O.Inflate(r, RC, ERR); O.Simplify()
            D = pcbnew.SHAPE_POLY_SET(P); D.BooleanSubtract(O); D.Simplify()
            for k in range(D.OutlineCount()):
                pc = pcbnew.SHAPE_POLY_SET(); pc.AddOutline(D.Outline(k)); a = pc.Area() / MM / MM
                if a < AMIN: continue
                bb = pc.BBox(); per = D.Outline(k).Length() / MM
                alone.append({'layer': LN[L], 'net': n, 'zone': nm, 'area': round(a, 4), 'est_w': round(2 * a / per, 3) if per else 0,
                              'bbox': [round(bb.GetX() / MM, 2), round(bb.GetY() / MM, 2), round(bb.GetRight() / MM, 2), round(bb.GetBottom() / MM, 2)]})
print('NARROW in net copper union (W outer %.2f inner %.2f, area >= %.3f mm2): %d' % (WO, WI, AMIN, len(res)))
for x in sorted(res, key=lambda x: (x['layer'], x['net'], x['bbox'])):
    print('  %s %-26s area %.4f est_w %.3f bbox %s zones %s' % (x['layer'], x['net'][-26:], x['area'], x['est_w'], x['bbox'], x['zones']))
print('NARROW in a zone fill on its own: %d' % len(alone))
for x in sorted(alone, key=lambda x: (x['layer'], x['zone'], x['bbox'])):
    print('  %s %-20s %-22s area %.4f est_w %.3f bbox %s' % (x['layer'], x['zone'], x['net'][-22:], x['area'], x['est_w'], x['bbox']))
if out: json.dump({'union': res, 'alone': alone}, open(out, 'w'), indent=0)
