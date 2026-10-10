"""flatpak: route_r6b_base.py IN OUT : R6b base = R6a-final + named B.Cu signal keep-out rule areas (BKO_*); the DRC rule bko_* in R6b.kicad_dru enforces them with net exceptions."""
import sys
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
BKO = {
 'BKO_U6':    rect(95.0, 114.0, 125.0, 144.0),   # 900 mm2 GND heat spreader under U6
 'BKO_U7':    rect(177.0, 119.5, 207.0, 148.5),  # 870 mm2 under U7 (BAT_PACK B.Cu band ends at y 119)
 'BKO_BM83':  rect(88.9, 25.4, 111.3, 42.7),     # BM83 module body (antenna keep-out separate)
 'BKO_ADC':   rect(144.0, 78.0, 160.0, 92.0),    # PCM1862 + its decoupling/inputs
 'BKO_CODEC': rect(150.5, 50.0, 162.0, 65.0),    # PCM2902C + Y170
 'BKO_MUX':   rect(169.0, 62.3, 199.5, 69.5),    # TS5A23157 x2 + TPA6132
}
for n, pts in BKO.items(): rule_area(b, n, pts, layers='B')
pcbnew.SaveBoard(sys.argv[2], b); print('added', list(BKO))
