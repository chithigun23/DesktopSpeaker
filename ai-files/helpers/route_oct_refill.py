#!/usr/bin/env python3
"""route_oct_refill.py IN.kicad_pcb OUT.kicad_pcb  (KiCad AppImage python3.11)
Refill all zones and save. IN must have IN.kicad_pro and IN.kicad_dru beside it (otherwise custom zone clearances are ignored).
Separate process from any edit: pcbnew Remove() followed by a fill segfaults on this board, so edits are text-only."""
import sys, os, pcbnew
stem = os.path.splitext(sys.argv[1])[0]
for ext in ('.kicad_pro', '.kicad_dru'):
    if not os.path.exists(stem + ext):
        print('MISSING', stem + ext, flush=True); os._exit(2)
b = pcbnew.LoadBoard(sys.argv[1]); b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print('refilled', sys.argv[2], flush=True)
os._exit(0)
