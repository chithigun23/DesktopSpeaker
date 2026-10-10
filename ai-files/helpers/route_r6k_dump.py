"""flatpak: route_r6k_dump.py BOARD x0 y0 x1 y1 [netfilter] : list pads, tracks, vias, zones (outline bbox + fill outline count) in a box"""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6]); nf = sys.argv[6] if len(sys.argv) > 6 else ''
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: '1', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
def inb(x, y, m=0): return x0 - m <= x <= x1 + m and y0 - m <= y <= y1 + m
eb = b.GetBoardEdgesBoundingBox(); print('board bbox', eb.GetLeft() / MM, eb.GetTop() / MM, eb.GetRight() / MM, eb.GetBottom() / MM)
for f in b.GetFootprints():
    for p in f.Pads():
        x, y = p.GetX() / MM, p.GetY() / MM
        if inb(x, y) and nf in str(p.GetNetname()):
            print('PAD %s.%s %s (%.3f,%.3f) %.2fx%.2f rot%.0f %s' % (f.GetReference(), p.GetNumber(), p.GetNetname(), x, y, p.GetSizeX() / MM, p.GetSizeY() / MM, p.GetOrientationDegrees(), 'TH' if p.GetDrillSizeX() > 0 else ''))
for t in b.GetTracks():
    n = str(t.GetNetname())
    if nf not in n: continue
    if t.GetClass() == 'PCB_VIA':
        if inb(t.GetX() / MM, t.GetY() / MM): print('VIA %s (%.3f,%.3f) %.2f/%.2f' % (n, t.GetX() / MM, t.GetY() / MM, t.GetWidth(pcbnew.F_Cu) / MM, t.GetDrillValue() / MM))
    else:
        a, c = t.GetStart(), t.GetEnd()
        if inb(a.x / MM, a.y / MM) or inb(c.x / MM, c.y / MM):
            print('TRK %s %s (%.3f,%.3f)-(%.3f,%.3f) w%.2f' % (n, LN.get(t.GetLayer(), '?'), a.x / MM, a.y / MM, c.x / MM, c.y / MM, t.GetWidth() / MM))
for z in b.Zones():
    bb = z.GetBoundingBox()
    if bb.GetRight() / MM < x0 or bb.GetLeft() / MM > x1 or bb.GetBottom() / MM < y0 or bb.GetTop() / MM > y1: continue
    if nf not in str(z.GetNetname()) and nf not in z.GetZoneName(): continue
    ls = ''.join(LN[l] for l in LN if z.IsOnLayer(l))
    fc = ''
    for l in LN:
        if z.IsOnLayer(l) and not z.GetIsRuleArea() and z.HasFilledPolysForLayer(l): fc += '%s:%d/%.1f ' % (LN[l], z.GetFilledPolysList(l).OutlineCount(), z.GetFilledPolysList(l).Area() / MM / MM)
    o = z.Outline(); pts = [(round(o.CVertex(i).x / MM, 2), round(o.CVertex(i).y / MM, 2)) for i in range(o.TotalVertices())]
    print('ZONE %s net=%s L=%s prio=%d clr=%.2f %s rule=%s fill=%s pts=%s' % (z.GetZoneName(), z.GetNetname(), ls, z.GetAssignedPriority(), z.GetLocalClearance().value_or(0) / MM if hasattr(z.GetLocalClearance(), 'value_or') else 0, '', z.GetIsRuleArea(), fc, pts if len(pts) < 40 else str(pts[:40]) + '...'))
