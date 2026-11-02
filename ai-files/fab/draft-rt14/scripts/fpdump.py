#!/usr/bin/env python3
"""fpdump.py BOARD.kicad_pcb OUT.json  (AppImage python3.11): footprints with ref, value, lib id, side, position, rotation,
attributes (SMD/THT, DNP, exclude from pos/BOM, board-only), pad counts and courtyard bbox."""
import pcbnew, sys, os, json
b = pcbnew.LoadBoard(sys.argv[1]); out = []
for fp in b.GetFootprints():
    p = fp.GetPosition(); a = fp.GetAttributes()
    cy = fp.GetCourtyard(pcbnew.F_CrtYd); bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    out.append({'ref': fp.GetReference(), 'value': fp.GetValue(), 'lib': fp.GetFPIDAsString(),
        'side': 'B' if fp.IsFlipped() else 'F', 'x': p.x/1e6, 'y': p.y/1e6, 'rot': fp.GetOrientationDegrees(),
        'smd': bool(a & pcbnew.FP_SMD), 'tht': bool(a & pcbnew.FP_THROUGH_HOLE), 'dnp': fp.IsDNP(),
        'no_pos': fp.IsExcludedFromPosFiles(), 'no_bom': fp.IsExcludedFromBOM(), 'board_only': fp.IsBoardOnly(),
        'pads': len(fp.Pads()), 'pth': sum(1 for q in fp.Pads() if q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH),
        'crtyd': [bb.GetX()/1e6, bb.GetY()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6]})
json.dump(out, open(sys.argv[2], 'w'), indent=0)
print('footprints', len(out), flush=True); os._exit(0)
