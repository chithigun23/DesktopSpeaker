"""flatpak: route_r6m_gndfloat.py BOARD : every GND zone fill piece on every copper layer must hold a GND via, a GND pad or touch a
GND track on its layer; prints piece counts per layer and any floating piece (bbox, area)."""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: '1', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
for L, ln in LN.items():
    pts = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == 'GND']
    pads = [p for f in b.GetFootprints() for p in f.Pads() if str(p.GetNetname()) == 'GND' and p.IsOnLayer(L)]
    trks = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == 'GND' and t.GetLayer() == L]
    n = fl = 0
    for z in b.Zones():
        if z.GetIsRuleArea() or str(z.GetNetname()) != 'GND' or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
        fp = z.GetFilledPolysList(L)
        for k in range(fp.OutlineCount()):
            n += 1; pc = pcbnew.SHAPE_POLY_SET(); pc.AddOutline(fp.Outline(k))
            for h in range(fp.HoleCount(k)): pc.AddHole(fp.Hole(k, h))
            ok = any(pc.Contains(p) for p in pts) or any(pc.Contains(p.GetPosition()) or pc.Collide(p.GetPosition(), int(min(p.GetSizeX(), p.GetSizeY()) / 2)) for p in pads) \
                or any(pc.Collide(t.GetStart(), int(t.GetWidth() / 2)) or pc.Collide(t.GetEnd(), int(t.GetWidth() / 2)) for t in trks)
            if not ok:
                fl += 1; bb = pc.BBox()
                print('  FLOATING %s %s bbox %.2f %.2f %.2f %.2f area %.3f' % (ln, z.GetZoneName(), bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM, pc.Area() / MM / MM))
    print('GND layer %s fill pieces %d floating %d' % (ln, n, fl))
