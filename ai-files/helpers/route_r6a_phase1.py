"""flatpak: route_r6a_phase1.py IN.kicad_pcb OUT.kicad_pcb
R6a phase 1/2 base: NECK_<ref> rule areas, lock the reservation vias, EP thermal arrays (U6/U7 4x4, U25 >= 6),
GND planes In1 (solid) + B.Cu + In2 GND background (power islands come in phase 2 with higher priority)."""
import sys, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
inp, outp = sys.argv[1:3]
b = pcbnew.LoadBoard(inp)
log = {}
# --- neck areas: courtyard bbox + 1.5 mm (U6/U7: bottom extended to the bootstrap cap stack, documented)
NECK = ['U4', 'U6', 'U7', 'U8', 'U9', 'U11', 'U14', 'U15', 'U19', 'U24', 'U25',
        'U3', 'U5', 'U10', 'U20', 'J1']   # second row: 0.5 mm pitch parts named in pcb-routing-plan-review sec. 4 (U3/U10/J1) plus U5/U20 (0.5 mm pitch)
EXTRA = {'U6': (0, 0, 0, 3.8), 'U7': (0, 0, 0, 3.8)}   # extra (left, top, right, bottom) mm
for r in NECK:
    f = fp(b, r); c = f.GetCourtyard(pcbnew.F_CrtYd); bb = c.BBox()
    x0, y0, x1, y1 = bb.GetLeft() / MM - 1.5, bb.GetTop() / MM - 1.5, bb.GetRight() / MM + 1.5, bb.GetBottom() / MM + 1.5
    e = EXTRA.get(r, (0, 0, 0, 0)); x0 -= e[0]; y0 -= e[1]; x1 += e[2]; y1 += e[3]
    rule_area(b, 'NECK_' + r, rect(x0, y0, x1, y1))
    log['NECK_' + r] = [round(v, 2) for v in (x0, y0, x1, y1)]
# --- lock reservation vias
nl = 0
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA': t.SetLocked(True); nl += 1
log['locked_reservation_vias'] = nl
# --- EP arrays
def ep_array(ref, num, pitch, nx, ny, cx=None, cy=None, r=0.3, py=None):
    py = pitch if py is None else py
    p = pad(b, ref, num); cx = p.GetX() / MM if cx is None else cx; cy = p.GetY() / MM if cy is None else cy
    out = []
    for i in range(nx):
        for j in range(ny):
            x = cx + (i - (nx - 1) / 2) * pitch; y = cy + (j - (ny - 1) / 2) * py
            if via_in_pad(p, x, y, r): via(b, 'GND', x, y, 0.6, 0.3); out.append((round(x, 3), round(y, 3)))
    return out
log['EP_U6'] = ep_array('U6', 33, 0.9, 4, 4)
log['EP_U7'] = ep_array('U7', 33, 0.9, 4, 4)
p21 = pad(b, 'U25', 21)
log['EP_U25'] = ep_array('U25', 21, 0.9, 2, 4, cx=153.185, cy=147.195, py=0.8)
for p in (pad(b, 'U6', 33), pad(b, 'U7', 33), p21): p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
# --- GND planes
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True)
o = ps.Outline(0); outline = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
zone(b, 'GND', '1', outline, prio=0, clr=0.3, minw=0.25, name='GND_IN1')
zone(b, 'GND', 'B', outline, prio=0, clr=0.3, minw=0.25, name='GND_BCU')
zone(b, 'GND', '2', outline, prio=0, clr=0.4, minw=0.3, name='GND_IN2_BG')
refill(b)
pcbnew.SaveBoard(outp, b)
json.dump(log, open(outp.replace('.kicad_pcb', '.phase1.json'), 'w'), indent=1)
print({k: (len(v) if isinstance(v, list) and k.startswith('EP') else v) for k, v in log.items()})
