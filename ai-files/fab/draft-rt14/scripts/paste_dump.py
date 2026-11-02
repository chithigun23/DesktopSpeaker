#!/usr/bin/env python3
"""paste_dump.py BOARD.kicad_pcb OUT.json  (AppImage python3.11; pcbnew)
Dump everything that makes the F.Paste (stencil) layer: per pad on F.Paste its copper polygon and paste margin (x, y);
footprint graphics on F.Paste as polygons; plus copper polygons of every F.Cu SMD pad (for coverage) and via positions/drills.
Geometry in mm, board coordinates (y down). Analysed by stencil_check.py (shapely)."""
import pcbnew, sys, os, json
b = pcbnew.LoadBoard(sys.argv[1])
ME = pcbnew.FromMM(0.002)
def polys(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i); pts = [(o.CPoint(k).x / 1e6, o.CPoint(k).y / 1e6) for k in range(o.PointCount())]
        holes = []
        for h in range(sps.HoleCount(i)):
            hh = sps.Hole(i, h); holes.append([(hh.CPoint(k).x / 1e6, hh.CPoint(k).y / 1e6) for k in range(hh.PointCount())])
        out.append([pts, holes])
    return out
pads = []; shapes = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        if not p.IsOnLayer(pcbnew.F_Cu) and not p.IsOnLayer(pcbnew.F_Paste): continue
        sps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(sps, pcbnew.F_Cu, 0, ME, pcbnew.ERROR_INSIDE)
        try: m = p.GetSolderPasteMargin(pcbnew.F_Paste)
        except TypeError: m = p.GetSolderPasteMargin()
        pads.append({'ref': ref, 'num': p.GetNumber(), 'attr': int(p.GetAttribute()), 'net': p.GetNetname(),
                     'paste': p.IsOnLayer(pcbnew.F_Paste), 'fcu': p.IsOnLayer(pcbnew.F_Cu), 'margin': [m.x / 1e6, m.y / 1e6],
                     'shape': int(p.GetShape(pcbnew.F_Cu)) if hasattr(p, 'GetShape') else -1,
                     'size': [p.GetSize(pcbnew.F_Cu).x / 1e6, p.GetSize(pcbnew.F_Cu).y / 1e6],
                     'drill': p.GetDrillSize().x / 1e6, 'poly': polys(sps), 'fp_dnp': fp.IsDNP(), 'fp_tht': bool(fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE)})
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_Paste and g.GetClass() in ('PCB_SHAPE', 'FP_SHAPE'):
            sps = pcbnew.SHAPE_POLY_SET(); g.TransformShapeToPolygon(sps, pcbnew.F_Paste, 0, ME, pcbnew.ERROR_INSIDE)
            shapes.append({'ref': ref, 'poly': polys(sps)})
for g in b.GetDrawings():
    if g.GetLayer() == pcbnew.F_Paste:
        sps = pcbnew.SHAPE_POLY_SET(); g.TransformShapeToPolygon(sps, pcbnew.F_Paste, 0, ME, pcbnew.ERROR_INSIDE)
        shapes.append({'ref': '(board)', 'poly': polys(sps)})
vias = [{'x': t.GetPosition().x / 1e6, 'y': t.GetPosition().y / 1e6, 'drill': t.GetDrillValue() / 1e6, 'net': t.GetNetname()}
        for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
ds = b.GetDesignSettings()
json.dump({'pads': pads, 'shapes': shapes, 'vias': vias, 'board_paste_margin': ds.m_SolderPasteMargin / 1e6,
           'board_paste_ratio': ds.m_SolderPasteMarginRatio}, open(sys.argv[2], 'w'))
print('paste_dump pads', len(pads), 'paste pads', sum(p['paste'] for p in pads), 'paste shapes', len(shapes), flush=True)
os._exit(0)
