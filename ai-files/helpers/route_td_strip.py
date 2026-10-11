"""flatpak: route_td_strip.py IN.kicad_pcb OUT.kicad_pcb [--nofill] : delete every teardrop zone (ZONE.IsTeardropArea()), refill all zones, save.
Prints teardrop count before/after and the number of remaining (non-teardrop) zones."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
td = [z for z in b.Zones() if z.IsTeardropArea()]
print('zones', len(list(b.Zones())), 'teardrops', len(td))
for z in td: b.RemoveNative(z)
if '--nofill' not in sys.argv: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
print('after: zones', len(list(b.Zones())), 'teardrops', sum(1 for z in b.Zones() if z.IsTeardropArea()))
b.Save(sys.argv[2])
